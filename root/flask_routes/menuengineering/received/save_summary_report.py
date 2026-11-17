# from flask import Blueprint, jsonify, request
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from flask_cors import cross_origin
# from root.auth.check import token_auth
# from decimal import Decimal, ROUND_HALF_UP
# from datetime import datetime

# load_dotenv()

# app_file116 = Blueprint('app_file116', __name__)

# def get_db_connection():
#     return mysql.connector.connect(
#         host=os.getenv("host"),
#         user=os.getenv("user"),
#         password=os.getenv("password"),
#         database=os.getenv("database")
#     )

# @app_file116.route("/save-inventory-snapshot", methods=["POST"])
# @cross_origin()
# def save_inventory_snapshot():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         items = data.get("items")
#         outlet = data.get("outlet")
#         start_date = data.get("start_date")
#         end_date = data.get("end_date")
#         food_total_items = data.get("food_total_items")
#         beverage_total_items = data.get("beverage_total_items")
#         food_accuracy = data.get("food_accuracy")
#         beverage_accuracy = data.get("beverage_accuracy")

#         if not all([items, outlet, start_date, end_date]):
#             return jsonify({"error": "Missing required fields."}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         today = datetime.now().date()
#         cursor.execute("""
#             SELECT id FROM inventory_snapshot_master
#             WHERE outlet_name = %s AND DATE(created_at) = %s
#         """, (outlet, today))

#         is_opening = False
#         if cursor.fetchone():
#             cursor.close()
#             conn.close()
#             return jsonify({"error": f"Inventory snapshot has already been saved for {outlet} today."}), 400

#         cursor.execute("""
#             SELECT COUNT(*) AS count FROM inventory_snapshot_master
#             WHERE outlet_name = %s
#         """, (outlet,))
#         if cursor.fetchone()["count"] == 0:
#             is_opening = True

#         # Insert master record
#         cursor.execute("""
#             INSERT INTO inventory_snapshot_master (
#                 outlet_name, start_date, end_date, created_at,
#                 food_total_items, beverage_total_items,
#                 food_accuracy, beverage_accuracy
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             outlet, start_date, end_date, datetime.now(),
#             food_total_items, beverage_total_items,
#             food_accuracy, beverage_accuracy
#         ))

#         snapshot_id = cursor.lastrowid

#         insert_item_sql = """
#             INSERT INTO inventory_snapshot_items (
#                 snapshot_id, item_name, item_type, group_name,
#                 uom, new_uom, total_consumed, total_received,
#                 closing_balance, closing_count, opening_count,
#                 wastage_count, physical_count, discrepancy_count,
#                 received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """

#         for item in items:
#             item_name = item.get("name")

#             # Get consumption cost
#             cursor.execute("""
#                 SELECT SUM(consumed_quantity * rate) AS total_consumption_cost
#                 FROM consumption_tracker
#                 WHERE item_name = %s AND outlet = %s AND order_date BETWEEN %s AND %s
#             """, (item_name, outlet, start_date, end_date))
#             consumption_cost = float(cursor.fetchone()["total_consumption_cost"] or 0)

#             # Get received cost from store requisition tables
#             cursor.execute("""
#                 SELECT SUM(d.Amount * d.Rate) AS total_received_cost
#                 FROM intblstorereqdetails d
#                 JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
#                 WHERE d.ItemName = %s 
#                     AND r.Outlet = %s 
#                     AND DATE(r.Date) BETWEEN %s AND %s
#             """, (item_name, outlet, start_date, end_date))

#             received_cost = float(cursor.fetchone()["total_received_cost"] or 0)

#             # Get wastage cost
#             cursor.execute("""
#                 SELECT SUM(price) AS total_wastage_cost
#                 FROM wastage_items
#                 WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s
#             """, (item_name, outlet, start_date, end_date))
#             wastage_cost = float(cursor.fetchone()["total_wastage_cost"] or 0)

#             # Get closing quantity (from frontend input)
#             closing_count = float(Decimal(item.get("closing_balance", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP))

#             # Get previous closing balance to calculate opening cost
#             cursor.execute("""
#                 SELECT isi.rate, isi.closing_balance
#                 FROM inventory_snapshot_items isi
#                 JOIN inventory_snapshot_master ism ON isi.snapshot_id = ism.id
#                 WHERE ism.outlet_name = %s AND isi.item_name = %s AND ism.end_date < %s
#                 ORDER BY ism.end_date DESC LIMIT 1
#             """, (outlet, item_name, start_date))
#             prev = cursor.fetchone()
#             opening_cost = 0
#             if prev:
#                 opening_cost = float(prev["closing_balance"] or 0)
#             else:
#                 cursor.execute("""
#                     SELECT Rate FROM stock_statement
#                     WHERE ItemName = %s AND OutletName = %s
#                 """, (item_name, outlet))
#                 opening_rate_result = cursor.fetchone()
#                 if not opening_rate_result:
#                     print(f"{item_name} didnt have stockstatement")
#                     # continue
#                     opening_cost = 0
#                 else:
#                     opening_rate = float(opening_rate_result["Rate"])
#                     opening_cost = opening_rate * float(item.get("opening_count", 0))

#             # Total cost = opening + received - wastage - consumption
#             total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

#             # Step 1: Get physical_count from frontend
#             physical_count = float(Decimal(item.get("physical_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP))
#             remaining_physical_qty = physical_count
#             physical_cost = 0.0

#             # Step 2: Fetch from item_current_level in **LIFO** order
#             cursor.execute("""
#                 SELECT quantity, rate FROM item_current_level
#                 WHERE itemname = %s AND outlet = %s AND quantity > 0
#                 ORDER BY id DESC
#             """, (item_name, outlet))
#             stock_rows = cursor.fetchall()

#             last_rate = 0.0

#             # Step 3: LIFO calculation
#             for row in stock_rows:
#                 available_qty = float(row["quantity"])
#                 rate = float(row["rate"])
#                 last_rate = rate  # update last seen rate

#                 if remaining_physical_qty <= 0:
#                     break

#                 used_qty = min(available_qty, remaining_physical_qty)
#                 physical_cost += used_qty * rate
#                 remaining_physical_qty -= used_qty

#             # Step 4: If there's still remaining quantity, use the last known rate
#             if remaining_physical_qty > 0 and last_rate > 0:
#                 physical_cost += remaining_physical_qty * last_rate



#             actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost

#             if is_opening == False:

#                 rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
#                 closing_balance = round(physical_count * rate, 2)
            
#             else:
#                 cursor.execute("""
#                     SELECT Rate FROM stock_statement
#                     WHERE ItemName = %s AND OutletName = %s
#                 """, (item_name, outlet))
#                 noopening_rate_result = cursor.fetchone()
#                 if not opening_rate_result:
#                     print(f"{item_name} didnt have stockstatement")
#                 else:
#                     noopening_rate = float(noopening_rate_result["Rate"])
#                     closing_cost = noopening_rate * physical_count
#                     closing_balance = closing_cost
#                     rate = noopening_rate

#             # Insert record
#             cursor.execute(insert_item_sql, (
#                 snapshot_id,
#                 item_name,
#                 item.get("type"),
#                 item.get("group_name"),
#                 item.get("uom"),
#                 item.get("new_uom"),
#                 float(Decimal(item.get("total_consumed", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
#                 float(Decimal(item.get("total_received", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
#                 closing_balance,
#                 closing_count,
#                 float(Decimal(item.get("opening_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
#                 float(Decimal(item.get("total_wastage", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
#                 float(Decimal(item.get("physical_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
#                 float(Decimal(item.get("discrepancy_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
#                 round(received_cost, 2),
#                 round(consumption_cost, 2),
#                 round(wastage_cost, 2),
#                 rate,
#                 round(actual_consumption_cost, 2),
#                 round(opening_cost, 2),
#                 round(physical_cost, 2)
#             ))

#             # Opening stock insert (if first snapshot)
#             if is_opening:
#                 cursor.execute("""
#                     SELECT Rate FROM stock_statement
#                     WHERE ItemName = %s AND OutletName = %s
#                 """, (item_name, outlet))
#                 rate_result = cursor.fetchone()
#                 if not rate_result:
#                     continue
#                 opening_rate = float(rate_result["Rate"])

#                 # Always insert a new row for opening stock (sequentially)
#                 cursor.execute("""
#                     INSERT INTO item_current_level (itemname, quantity, rate, outlet)
#                     VALUES (%s, %s, %s, %s)
#                 """, (item_name, closing_count, opening_rate, outlet))


#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"status": "success", "snapshot_id": snapshot_id}), 200

#     except Exception as e:
#         if 'conn' in locals():
#             conn.rollback()
#             conn.close()
#         return jsonify({"error": str(e)}), 500


# from .utils_fnb import get_sales_data_for_snapshot, calculate_employee_meal_cost, calculate_complimentary_cost_for_snapshot
# from datetime import date
# @app_file116.route("/save-inventory-snapshot-food", methods=["POST"])
# @cross_origin()
# def save_inventory_snapshot_food():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         items = data.get("items")
#         outlet = data.get("outlet")
#         start_date = data.get("start_date")
#         end_date = data.get("end_date")
#         food_total_items = data.get("food_total_items")
#         food_accuracy = data.get("food_accuracy")
#         food_missing_items = data.get("food_missing_items")

#         is_opening = data.get("is_opening", False)  # Default to False if not provided
#         physical_added = data.get("physical_added", False)  # Default to False if not provided

#         if not all([items, outlet, start_date, end_date]):
#             return jsonify({"error": "Missing required fields."}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True, buffered=True)

#         today = datetime.now().date()

#          # Check if opening snapshot already exists for this outlet
#         if is_opening:
#             # Check for existing opening snapshot
#             cursor.execute("""
#                 SELECT id FROM inventory_snapshot_master_food
#                 WHERE outlet_name = %s AND is_opening = 1
#             """, (outlet,))
            
#             existing_opening = cursor.fetchone()
            
#             if existing_opening:
#                 # Delete existing opening snapshot and its items
#                 opening_id = existing_opening["id"]
                
#                 # Delete items first (foreign key constraint)
#                 cursor.execute("""
#                     DELETE FROM inventory_snapshot_items_food
#                     WHERE snapshot_id = %s
#                 """, (opening_id,))
                
#                 # Delete the master record
#                 cursor.execute("""
#                     DELETE FROM inventory_snapshot_master_food
#                     WHERE id = %s
#                 """, (opening_id,))
                
#                 print(f"Deleted existing opening snapshot (ID: {opening_id}) for outlet: {outlet}")
#         else:
#             # For non-opening snapshots, check if a snapshot was already saved today
#             cursor.execute("""
#                 SELECT id FROM inventory_snapshot_master_food
#                 WHERE outlet_name = %s AND DATE(created_at) = %s AND is_opening = 0
#             """, (outlet, today))
            
#             if cursor.fetchone():
#                 cursor.close()
#                 conn.close()
#                 return jsonify({"error": f"Inventory snapshot for food has already been saved for {outlet} today."}), 400

#         # Insert master record
#         cursor.execute("""
#             INSERT INTO inventory_snapshot_master_food (
#                 outlet_name, start_date, end_date, created_at,
#                 food_total_items,
#                 food_accuracy,
#                 food_missing_items,
#                 is_opening,
#                 physical_added
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             outlet, start_date, end_date, datetime.now(),
#             food_total_items, 
#             food_accuracy,
#             food_missing_items,
#             is_opening,
#             physical_added
#         ))

#         snapshot_id = cursor.lastrowid

#         # Track totals for FNB Costing
#         total_opening_cost = 0.0
#         total_purchase_cost = 0.0
#         total_closing_cost = 0.0
#         total_consumption_cost = 0.0
#         total_wastage_cost = 0.0

#         insert_item_sql = """
#             INSERT INTO inventory_snapshot_items_food (
#                 snapshot_id, item_name, item_type, group_name,
#                 uom, new_uom, total_consumed, total_received,
#                 closing_balance, closing_count, opening_count,
#                 wastage_count, physical_count, discrepancy_count,
#                 received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost, discrepancy_cost
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """

#         for item in items:
#             item_name = item.get("name")

#             # Get consumption cost
#             cursor.execute("""
#                 SELECT SUM(consumed_quantity * rate) AS total_consumption_cost
#                 FROM consumption_tracker
#                 WHERE item_name = %s AND outlet = %s AND order_date BETWEEN %s AND %s
#             """, (item_name, outlet, start_date, end_date))
#             consumption_cost_from_consumption_tracker = float(cursor.fetchone()["total_consumption_cost"] or 0)


#             # Get unit definition for the item
#             cursor.execute("""
#                 SELECT unit, uom, rate
#                 FROM tblunitdefinition
#                 WHERE name = %s AND outlet = %s
#             """, (item_name, outlet))
            
#             unit_definition = cursor.fetchone()
            
#             # Calculate real consumption cost based on unit
#             if unit_definition and unit_definition["unit"] and unit_definition["unit"] > 0:
#                 unit = float(unit_definition["unit"])
#                 consumption_cost = consumption_cost_from_consumption_tracker / unit
#                 uom = unit_definition["uom"]
#                 unit_rate = float(unit_definition["rate"] or 0) if unit_definition["rate"] else 0
#             else:
#                 consumption_cost = consumption_cost_from_consumption_tracker
#                 unit = 1
#                 uom = "unit"
#                 unit_rate = 0

#             # # Get received cost
#             # cursor.execute("""
#             #     SELECT SUM(quantity * price) AS total_received_cost
#             #     FROM received_items
#             #     WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s
#             # """, (item_name, outlet, start_date, end_date))

#             # Get received cost from store requisition tables
#             cursor.execute("""
#                 SELECT SUM(d.Amount * d.Rate) AS total_received_cost
#                 FROM intblstorereqdetails d
#                 JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
#                 WHERE d.ItemName = %s 
#                     AND r.Outlet = %s 
#                     AND DATE(r.Date) BETWEEN %s AND %s and r.CostCenter = 'Kitchen'
#             """, (item_name, outlet, start_date, end_date))

#             received_cost = float(cursor.fetchone()["total_received_cost"] or 0)

#             # Get wastage cost
#             cursor.execute("""
#                 SELECT SUM(price) AS total_wastage_cost
#                 FROM wastage_items
#                 WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s and costcenter = 'Kitchen'
#             """, (item_name, outlet, start_date, end_date))
#             wastage_cost = float(cursor.fetchone()["total_wastage_cost"] or 0)

#             # Get closing quantity (from frontend input)
#             closing_count = float(Decimal(item.get("closing_balance", 0)))

#             # Get previous closing balance to calculate opening cost
#             cursor.execute("""
#                 SELECT isi.rate, isi.closing_balance
#                 FROM inventory_snapshot_items_food isi
#                 JOIN inventory_snapshot_master_food ism ON isi.snapshot_id = ism.id
#                 WHERE ism.outlet_name = %s AND isi.item_name = %s AND ism.end_date < %s
#                 ORDER BY ism.end_date DESC LIMIT 1
#             """, (outlet, item_name, start_date))
#             prev = cursor.fetchone()
#             opening_cost = 0
#             if prev:
#                 opening_cost = float(prev["closing_balance"] or 0)
#             else:
#                 # cursor.execute("""
#                 #     SELECT Rate FROM stock_statement
#                 #     WHERE ItemName = %s AND OutletName = %s
#                 # """, (item_name, outlet))

#                 cursor.execute("""
#                     SELECT d.Rate
#                     FROM intblstorereqdetails d
#                     JOIN intblstorerequisition r 
#                         ON d.StoreReqID = r.idintblStoreRequisition
#                     WHERE d.ItemName = %s 
#                         AND r.Outlet = %s
#                         AND r.CostCenter = 'Kitchen'
#                     ORDER BY r.Date DESC 
#                     LIMIT 1
#                 """, (item_name, outlet))
#                 opening_rate_result = cursor.fetchone()
#                 if not opening_rate_result:
#                     print(f"{item_name} didnt have store requisition")
#                     # continue
#                     opening_cost = 0
#                 else:
#                     opening_rate = float(opening_rate_result["Rate"])
#                     opening_cost = opening_rate * float(item.get("opening_count", 0))

#             # Total cost = opening + received - wastage - consumption
#             total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

#             # Step 1: Get physical_count from frontend
#             physical_count = float(Decimal(item.get("physical_count", 0)))
#             remaining_physical_qty = physical_count
#             physical_cost = 0.0

#             # Step 2: Fetch from item_current_level in **LIFO** order
#             cursor.execute("""
#                 SELECT quantity, rate FROM item_current_level
#                 WHERE itemname = %s AND outlet = %s AND quantity > 0
#                 ORDER BY id DESC
#             """, (item_name, outlet))
#             stock_rows = cursor.fetchall()

#             last_rate = 0.0

#             # Step 3: LIFO calculation
#             for row in stock_rows:
#                 available_qty = float(row["quantity"])
#                 rate = float(row["rate"])
#                 last_rate = rate  # update last seen rate

#                 if remaining_physical_qty <= 0:
#                     break

#                 used_qty = min(available_qty, remaining_physical_qty)
#                 physical_cost += used_qty * rate
#                 remaining_physical_qty -= used_qty

#             # Step 4: If there's still remaining quantity, use the last known rate
#             if remaining_physical_qty > 0 and last_rate > 0:
#                 physical_cost += remaining_physical_qty * last_rate



#             # Step 5: Get discrepancy_count from frontend
#             discrepancy_count = float(Decimal(item.get("discrepancy_count", 0)))
#             remaining_discrepancy_qty = discrepancy_count
#             discrepancy_cost = 0.0

#             # Step 2: Fetch from item_current_level in **LIFO** order
#             cursor.execute("""
#                 SELECT quantity, rate FROM item_current_level
#                 WHERE itemname = %s AND outlet = %s AND quantity > 0
#                 ORDER BY id DESC
#             """, (item_name, outlet))
#             stock_rows = cursor.fetchall()

#             last_rate = 0.0

#             # Step 3: LIFO calculation
#             for row in stock_rows:
#                 available_qty = float(row["quantity"])
#                 rate = float(row["rate"])
#                 last_rate = rate  # update last seen rate

#                 if remaining_discrepancy_qty <= 0:
#                     break

#                 used_qty = min(available_qty, remaining_discrepancy_qty)
#                 discrepancy_cost += used_qty * rate
#                 remaining_discrepancy_qty -= used_qty

#             # Step 4: If there's still remaining quantity, use the last known rate
#             if remaining_discrepancy_qty > 0 and last_rate > 0:
#                 discrepancy_cost += remaining_discrepancy_qty * last_rate



#             actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost


#             print("actual_consumption_cost", actual_consumption_cost)
#             if is_opening == False:

#                 rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
#                 closing_balance = physical_count * rate
            
#             else:
#                 # cursor.execute("""
#                 #     SELECT Rate FROM stock_statement
#                 #     WHERE ItemName = %s AND OutletName = %s
#                 # """, (item_name, outlet))

#                 cursor.execute("""
#                     SELECT d.Rate
#                     FROM intblstorereqdetails d
#                     JOIN intblstorerequisition r 
#                         ON d.StoreReqID = r.idintblStoreRequisition
#                     WHERE d.ItemName = %s 
#                         AND r.Outlet = %s
#                         AND r.CostCenter = 'Kitchen'
#                     ORDER BY r.Date DESC 
#                     LIMIT 1
#                 """, (item_name, outlet))
#                 noopening_rate_result = cursor.fetchone()
#                 if not opening_rate_result:
#                     print(f"{item_name} didnt have store requisition")
#                 else:
#                     noopening_rate = float(noopening_rate_result["Rate"])
#                     closing_cost = noopening_rate * physical_count
#                     closing_balance = closing_cost
#                     rate = noopening_rate


#             print("I got upto here")
#             # Accumulate totals for FNB Costing
#             total_opening_cost += opening_cost 
#             total_purchase_cost += received_cost 
#             total_closing_cost += physical_cost 
#             total_consumption_cost += actual_consumption_cost 
#             total_wastage_cost += wastage_cost

#             # Insert record
#             cursor.execute(insert_item_sql, (
#                 snapshot_id,
#                 item_name,
#                 item.get("type"),
#                 item.get("group_name"),
#                 item.get("uom"),
#                 item.get("new_uom"),
#                 float(Decimal(item.get("total_consumed", 0))),
#                 float(Decimal(item.get("total_received", 0))),
#                 closing_balance,
#                 closing_count,
#                 float(Decimal(item.get("opening_count", 0))),
#                 float(Decimal(item.get("total_wastage", 0))),
#                 float(Decimal(item.get("physical_count", 0))),
#                 float(Decimal(item.get("discrepancy_count", 0))),
#                 received_cost,
#                 consumption_cost,
#                 wastage_cost,
#                 rate,
#                 actual_consumption_cost,
#                 opening_cost,
#                 physical_cost,
#                 discrepancy_cost,
#             ))

#             # Opening stock insert (if first snapshot)
#             if is_opening:
#                 # cursor.execute("""
#                 #     SELECT Rate FROM stock_statement
#                 #     WHERE ItemName = %s AND OutletName = %s
#                 # """, (item_name, outlet))

#                 cursor.execute("""
#                     SELECT d.Rate
#                     FROM intblstorereqdetails d
#                     JOIN intblstorerequisition r 
#                         ON d.StoreReqID = r.idintblStoreRequisition
#                     WHERE d.ItemName = %s 
#                         AND r.Outlet = %s
#                         AND r.CostCenter = 'Kitchen'
#                     ORDER BY r.Date DESC 
#                     LIMIT 1
#                 """, (item_name, outlet))
#                 rate_result = cursor.fetchone()
#                 if not rate_result:
#                     continue
#                 opening_rate = float(rate_result["Rate"])
#                 print("got upto here")
#                 # Always insert a new row for opening stock (sequentially)
#                 cursor.execute("""
#                     INSERT INTO item_current_level (itemname, quantity, rate, outlet)
#                     VALUES (%s, %s, %s, %s)
#                 """, (item_name, closing_count, opening_rate, outlet))

#         print("and got upto here")
#         # ============ CALCULATE AND SAVE FNB COSTING ============

#         # Get sales data for the period
#         sales_data = get_sales_data_for_snapshot(cursor, outlet, start_date, end_date)
        
#         # Calculate employee meal cost from Staff Consumption
#         employee_meal = calculate_employee_meal_cost(outlet, start_date, end_date, "Food")
        
#         # Calculate complimentary cost
#         complimentary = calculate_complimentary_cost_for_snapshot(cursor, outlet, start_date, end_date)
        
#         # Get total discount from sales data
#         total_discount = sales_data['discounts_sales']

#         gross_sales = sales_data['gross_sales']
#         gross_cost = sales_data['gross_cost']
#         gross_cost_percent = sales_data['gross_cost_percent']
        
#         # Calculate net sale for Food
#         net_sale = sales_data['food_sales'] - total_discount
        
#         # Calculate net cost
#         net_cost = total_opening_cost + total_purchase_cost - total_closing_cost - employee_meal - complimentary
        
#         # Calculate cost percent
#         net_cost_percent = (net_cost / net_sale * 100) if net_sale > 0 else 0
#         if is_opening != True:        
#             # Insert into FNB Costing table
#             fnb_insert_query = """
#                 INSERT INTO tblfnbcostingdetails 
#                 (outlet_name, report_for, opening, purchase, closing, employee_meal, 
#                 complimentary, net_cost, total_discount, cost_of_goods_sold, net_sale, 
#                 net_cost_percent, from_date, to_date, date, gross_cost, gross_sales, gross_cost_percent, wastage)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """
            
#             cursor.execute(fnb_insert_query, (
#                 outlet,
#                 'Food',  # report_for
#                 total_opening_cost,
#                 total_purchase_cost,
#                 total_closing_cost,
#                 employee_meal,
#                 complimentary,
#                 net_cost,
#                 total_discount,
#                 total_consumption_cost,  # cost_of_goods_sold
#                 net_sale,
#                 net_cost_percent,
#                 start_date,
#                 end_date,
#                 date.today(),
#                 gross_cost,
#                 gross_sales,
#                 gross_cost_percent,
#                 total_wastage_cost

#             ))


#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"status": "success", "snapshot_id": snapshot_id}), 200

#     except Exception as e:
#         if 'conn' in locals():
#             conn.rollback()
#             conn.close()
#         return jsonify({"error": str(e)}), 500
    


# @app_file116.route("/save-inventory-snapshot-beverage", methods=["POST"])
# @cross_origin()
# def save_inventory_snapshot_beverage():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         items = data.get("items")
#         outlet = data.get("outlet")
#         start_date = data.get("start_date")
#         end_date = data.get("end_date")
#         beverage_total_items = data.get("beverage_total_items")
#         beverage_accuracy = data.get("beverage_accuracy")
#         beverage_missing_items = data.get("beverage_missing_items")

#         is_opening = data.get("is_opening", False)  # Default to False if not provided
#         physical_added = data.get("physical_added", False)  # Default to False if not provided

#         if not all([items, outlet, start_date, end_date]):
#             return jsonify({"error": "Missing required fields."}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True, buffered=True)

#         today = datetime.now().date()

#          # Check if opening snapshot already exists for this outlet
#         if is_opening:
#             # Check for existing opening snapshot
#             cursor.execute("""
#                 SELECT id FROM inventory_snapshot_master_beverage
#                 WHERE outlet_name = %s AND is_opening = 1
#             """, (outlet,))
            
#             existing_opening = cursor.fetchone()
            
#             if existing_opening:
#                 # Delete existing opening snapshot and its items
#                 opening_id = existing_opening["id"]
                
#                 # Delete items first (foreign key constraint)
#                 cursor.execute("""
#                     DELETE FROM inventory_snapshot_items_beverage
#                     WHERE snapshot_id = %s
#                 """, (opening_id,))
                
#                 # Delete the master record
#                 cursor.execute("""
#                     DELETE FROM inventory_snapshot_master_beverage
#                     WHERE id = %s
#                 """, (opening_id,))
                
#                 print(f"Deleted existing opening snapshot (ID: {opening_id}) for outlet: {outlet}")
#         else:
#             # For non-opening snapshots, check if a snapshot was already saved today
#             cursor.execute("""
#                 SELECT id FROM inventory_snapshot_master_beverage
#                 WHERE outlet_name = %s AND DATE(created_at) = %s AND is_opening = 0
#             """, (outlet, today))
            
#             if cursor.fetchone():
#                 cursor.close()
#                 conn.close()
#                 return jsonify({"error": f"Inventory snapshot for beverage has already been saved for {outlet} today."}), 400

#         # Insert master record
#         cursor.execute("""
#             INSERT INTO inventory_snapshot_master_beverage (
#                 outlet_name, start_date, end_date, created_at,
#                 beverage_total_items,
#                 beverage_accuracy,
#                 beverage_missing_items,
#                 is_opening,
#                 physical_added
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             outlet, start_date, end_date, datetime.now(),
#             beverage_total_items, 
#             beverage_accuracy,
#             beverage_missing_items,
#             is_opening,
#             physical_added
#         ))

#         snapshot_id = cursor.lastrowid

#         # Track totals for FNB Costing
#         total_opening_cost = 0.0
#         total_purchase_cost = 0.0
#         total_closing_cost = 0.0
#         total_consumption_cost = 0.0
#         total_wastage_cost = 0.0

#         insert_item_sql = """
#             INSERT INTO inventory_snapshot_items_beverage (
#                 snapshot_id, item_name, item_type, group_name,
#                 uom, new_uom, total_consumed, total_received,
#                 closing_balance, closing_count, opening_count,
#                 wastage_count, physical_count, discrepancy_count,
#                 received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost, discrepancy_cost
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """

#         for item in items:
#             item_name = item.get("name")

#             # Get consumption cost
#             cursor.execute("""
#                 SELECT SUM(consumed_quantity * rate) AS total_consumption_cost
#                 FROM consumption_tracker
#                 WHERE item_name = %s AND outlet = %s AND order_date BETWEEN %s AND %s
#             """, (item_name, outlet, start_date, end_date))
#             consumption_cost_from_consumption_tracker = float(cursor.fetchone()["total_consumption_cost"] or 0)


#             # Get unit definition for the item
#             cursor.execute("""
#                 SELECT unit, uom, rate
#                 FROM tblunitdefinition
#                 WHERE name = %s AND outlet = %s
#             """, (item_name, outlet))
            
#             unit_definition = cursor.fetchone()
            
#             # Calculate real consumption cost based on unit
#             if unit_definition and unit_definition["unit"] and unit_definition["unit"] > 0:
#                 unit = float(unit_definition["unit"])
#                 consumption_cost = consumption_cost_from_consumption_tracker / unit
#                 uom = unit_definition["uom"]
#                 unit_rate = float(unit_definition["rate"] or 0) if unit_definition["rate"] else 0
#             else:
#                 consumption_cost = consumption_cost_from_consumption_tracker
#                 unit = 1
#                 uom = "unit"
#                 unit_rate = 0

#             # # Get received cost
#             # cursor.execute("""
#             #     SELECT SUM(quantity * price) AS total_received_cost
#             #     FROM received_items
#             #     WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s
#             # """, (item_name, outlet, start_date, end_date))

#             # Get received cost from store requisition tables
#             cursor.execute("""
#                 SELECT SUM(d.Amount * d.Rate) AS total_received_cost
#                 FROM intblstorereqdetails d
#                 JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
#                 WHERE d.ItemName = %s 
#                     AND r.Outlet = %s 
#                     AND DATE(r.Date) BETWEEN %s AND %s and CostCenter = 'Bar'
#             """, (item_name, outlet, start_date, end_date))

#             received_cost = float(cursor.fetchone()["total_received_cost"] or 0)

#             # Get wastage cost
#             cursor.execute("""
#                 SELECT SUM(price) AS total_wastage_cost
#                 FROM wastage_items
#                 WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s and costcenter = 'Bar'
#             """, (item_name, outlet, start_date, end_date))
#             wastage_cost = float(cursor.fetchone()["total_wastage_cost"] or 0)

#             # Get closing quantity (from frontend input)
#             closing_count = float(Decimal(item.get("closing_balance", 0)))

#             # Get previous closing balance to calculate opening cost
#             cursor.execute("""
#                 SELECT isi.rate, isi.closing_balance
#                 FROM inventory_snapshot_items_beverage isi
#                 JOIN inventory_snapshot_master_beverage ism ON isi.snapshot_id = ism.id
#                 WHERE ism.outlet_name = %s AND isi.item_name = %s AND ism.end_date < %s
#                 ORDER BY ism.end_date DESC LIMIT 1
#             """, (outlet, item_name, start_date))
#             prev = cursor.fetchone()
#             opening_cost = 0
#             if prev:
#                 opening_cost = float(prev["closing_balance"] or 0)
#             else:
#                 # cursor.execute("""
#                 #     SELECT Rate FROM stock_statement
#                 #     WHERE ItemName = %s AND OutletName = %s
#                 # """, (item_name, outlet))

#                 cursor.execute("""
#                     SELECT d.Rate
#                     FROM intblstorereqdetails d
#                     JOIN intblstorerequisition r 
#                         ON d.StoreReqID = r.idintblStoreRequisition
#                     WHERE d.ItemName = %s 
#                         AND r.Outlet = %s
#                         AND r.CostCenter = 'Bar'
#                     ORDER BY r.Date DESC 
#                     LIMIT 1
#                 """, (item_name, outlet))
#                 opening_rate_result = cursor.fetchone()
#                 if not opening_rate_result:
#                     print(f"{item_name} didnt have store requisition")
#                     # continue
#                     opening_cost = 0
#                 else:
#                     opening_rate = float(opening_rate_result["Rate"])
#                     opening_cost = opening_rate * float(item.get("opening_count", 0))

#             # Total cost = opening + received - wastage - consumption
#             total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

#             # Step 1: Get physical_count from frontend
#             physical_count = float(Decimal(item.get("physical_count", 0)))
#             remaining_physical_qty = physical_count
#             physical_cost = 0.0

#             # Step 2: Fetch from item_current_level in **LIFO** order
#             cursor.execute("""
#                 SELECT quantity, rate FROM item_current_level
#                 WHERE itemname = %s AND outlet = %s AND quantity > 0
#                 ORDER BY id DESC
#             """, (item_name, outlet))
#             stock_rows = cursor.fetchall()

#             last_rate = 0.0

#             # Step 3: LIFO calculation
#             for row in stock_rows:
#                 available_qty = float(row["quantity"])
#                 rate = float(row["rate"])
#                 last_rate = rate  # update last seen rate

#                 if remaining_physical_qty <= 0:
#                     break

#                 used_qty = min(available_qty, remaining_physical_qty)
#                 physical_cost += used_qty * rate
#                 remaining_physical_qty -= used_qty

#             # Step 4: If there's still remaining quantity, use the last known rate
#             if remaining_physical_qty > 0 and last_rate > 0:
#                 physical_cost += remaining_physical_qty * last_rate


#             # Step 5: Get discrepancy_count from frontend
#             discrepancy_count = abs(float(Decimal(item.get("discrepancy_count", 0))))
#             remaining_discrepancy_qty = discrepancy_count
#             discrepancy_cost = 0.0

#             # Step 2: Fetch from item_current_level in **LIFO** order
#             cursor.execute("""
#                 SELECT quantity, rate FROM item_current_level
#                 WHERE itemname = %s AND outlet = %s AND quantity > 0
#                 ORDER BY id DESC
#             """, (item_name, outlet))
#             stock_rows = cursor.fetchall()

#             last_rate = 0.0

#             # Step 3: LIFO calculation
#             for row in stock_rows:
#                 available_qty = float(row["quantity"])
#                 rate = float(row["rate"])
#                 last_rate = rate  # update last seen rate

#                 if remaining_discrepancy_qty <= 0:
#                     break

#                 used_qty = min(available_qty, remaining_discrepancy_qty)
#                 discrepancy_cost += used_qty * rate
#                 remaining_discrepancy_qty -= used_qty

#             # Step 4: If there's still remaining quantity, use the last known rate
#             if remaining_discrepancy_qty > 0 and last_rate > 0:
#                 discrepancy_cost += remaining_discrepancy_qty * last_rate


#             actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost


#             print("actual_consumption_cost", actual_consumption_cost)
#             if is_opening == False:

#                 rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
#                 closing_balance = physical_count * rate
            
#             else:
#                 # cursor.execute("""
#                 #     SELECT Rate FROM stock_statement
#                 #     WHERE ItemName = %s AND OutletName = %s
#                 # """, (item_name, outlet))

#                 cursor.execute("""
#                     SELECT d.Rate
#                     FROM intblstorereqdetails d
#                     JOIN intblstorerequisition r 
#                         ON d.StoreReqID = r.idintblStoreRequisition
#                     WHERE d.ItemName = %s 
#                         AND r.Outlet = %s
#                         AND r.CostCenter = 'Bar'
#                     ORDER BY r.Date DESC 
#                     LIMIT 1
#                 """, (item_name, outlet))
#                 noopening_rate_result = cursor.fetchone()
#                 if not opening_rate_result:
#                     print(f"{item_name} didnt have store requisition")
#                 else:
#                     noopening_rate = float(noopening_rate_result["Rate"])
#                     closing_cost = noopening_rate * physical_count
#                     closing_balance = closing_cost
#                     rate = noopening_rate


#             print("I got upto here")
#             # Accumulate totals for FNB Costing
#             total_opening_cost += opening_cost
#             total_purchase_cost += received_cost 
#             total_closing_cost += physical_cost 
#             total_consumption_cost += actual_consumption_cost 
#             total_wastage_cost += wastage_cost
#             # Insert record
#             cursor.execute(insert_item_sql, (
#                 snapshot_id,
#                 item_name,
#                 item.get("type"),
#                 item.get("group_name"),
#                 item.get("uom"),
#                 item.get("new_uom"),
#                 float(Decimal(item.get("total_consumed", 0))),
#                 float(Decimal(item.get("total_received", 0))),
#                 closing_balance,
#                 closing_count,
#                 float(Decimal(item.get("opening_count", 0))),
#                 float(Decimal(item.get("total_wastage", 0))),
#                 float(Decimal(item.get("physical_count", 0))),
#                 float(Decimal(item.get("discrepancy_count", 0))),
#                 received_cost,
#                 consumption_cost,
#                 wastage_cost,
#                 rate,
#                 actual_consumption_cost,
#                 opening_cost,
#                 physical_cost,
#                 discrepancy_cost,
#             ))

#             # Opening stock insert (if first snapshot)
#             if is_opening:
#                 # cursor.execute("""
#                 #     SELECT Rate FROM stock_statement
#                 #     WHERE ItemName = %s AND OutletName = %s
#                 # """, (item_name, outlet))

#                 cursor.execute("""
#                     SELECT d.Rate
#                     FROM intblstorereqdetails d
#                     JOIN intblstorerequisition r 
#                         ON d.StoreReqID = r.idintblStoreRequisition
#                     WHERE d.ItemName = %s 
#                         AND r.Outlet = %s
#                         AND r.CostCenter = 'Bar'
#                     ORDER BY r.Date DESC 
#                     LIMIT 1
#                 """, (item_name, outlet))
#                 rate_result = cursor.fetchone()
#                 if not rate_result:
#                     continue
#                 opening_rate = float(rate_result["Rate"])
#                 print("got upto here")
#                 # Always insert a new row for opening stock (sequentially)
#                 cursor.execute("""
#                     INSERT INTO item_current_level (itemname, quantity, rate, outlet)
#                     VALUES (%s, %s, %s, %s)
#                 """, (item_name, closing_count, opening_rate, outlet))

#         print("and got upto here")
#         # ============ CALCULATE AND SAVE FNB COSTING ============

#         # Get sales data for the period
#         sales_data = get_sales_data_for_snapshot(cursor, outlet, start_date, end_date)
        
#         # Calculate employee meal cost from Staff Consumption
#         employee_meal = calculate_employee_meal_cost(outlet, start_date, end_date, "Beverage")
        
#         # Calculate complimentary cost
#         complimentary = calculate_complimentary_cost_for_snapshot(cursor, outlet, start_date, end_date)
        
#         # Get total discount from sales data
#         total_discount = sales_data['discounts_sales']

#         gross_sales = sales_data['gross_sales']
#         gross_cost = sales_data['gross_cost']
#         gross_cost_percent = sales_data['gross_cost_percent']
        
#         # Calculate net sale for beverage
#         net_sale = sales_data['beverage_sales'] - total_discount
        
#         # Calculate net cost
#         net_cost = total_opening_cost + total_purchase_cost - total_closing_cost - employee_meal - complimentary
        
#         # Calculate cost percent
#         net_cost_percent = (net_cost / net_sale * 100) if net_sale > 0 else 0
#         if is_opening != True:        
#             # Insert into FNB Costing table
#             fnb_insert_query = """
#                 INSERT INTO tblfnbcostingdetails 
#                 (outlet_name, report_for, opening, purchase, closing, employee_meal, 
#                 complimentary, net_cost, total_discount, cost_of_goods_sold, net_sale, 
#                 net_cost_percent, from_date, to_date, date, gross_cost, gross_sales, gross_cost_percent, wastage)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """
            
#             cursor.execute(fnb_insert_query, (
#                 outlet,
#                 'Beverage',  # report_for
#                 total_opening_cost,
#                 total_purchase_cost,
#                 total_closing_cost,
#                 employee_meal,
#                 complimentary,
#                 net_cost,
#                 total_discount,
#                 total_consumption_cost,  # cost_of_goods_sold
#                 net_sale,
#                 net_cost_percent,
#                 start_date,
#                 end_date,
#                 date.today(),
#                 gross_cost,
#                 gross_sales,
#                 gross_cost_percent,
#                 total_wastage_cost

#             ))


#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"status": "success", "snapshot_id": snapshot_id}), 200

#     except Exception as e:
#         if 'conn' in locals():
#             conn.rollback()
#             conn.close()
#         return jsonify({"error": str(e)}), 500


from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

load_dotenv()

app_file116 = Blueprint('app_file116', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )

@app_file116.route("/save-inventory-snapshot", methods=["POST"])
@cross_origin()
def save_inventory_snapshot():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        items = data.get("items")
        outlet = data.get("outlet")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        food_total_items = data.get("food_total_items")
        beverage_total_items = data.get("beverage_total_items")
        food_accuracy = data.get("food_accuracy")
        beverage_accuracy = data.get("beverage_accuracy")

        if not all([items, outlet, start_date, end_date]):
            return jsonify({"error": "Missing required fields."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = datetime.now().date()
        cursor.execute("""
            SELECT id FROM inventory_snapshot_master
            WHERE outlet_name = %s AND DATE(created_at) = %s
        """, (outlet, today))

        is_opening = False
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": f"Inventory snapshot has already been saved for {outlet} today."}), 400

        cursor.execute("""
            SELECT COUNT(*) AS count FROM inventory_snapshot_master
            WHERE outlet_name = %s
        """, (outlet,))
        if cursor.fetchone()["count"] == 0:
            is_opening = True

        # Insert master record
        cursor.execute("""
            INSERT INTO inventory_snapshot_master (
                outlet_name, start_date, end_date, created_at,
                food_total_items, beverage_total_items,
                food_accuracy, beverage_accuracy
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            outlet, start_date, end_date, datetime.now(),
            food_total_items, beverage_total_items,
            food_accuracy, beverage_accuracy
        ))

        snapshot_id = cursor.lastrowid

        insert_item_sql = """
            INSERT INTO inventory_snapshot_items (
                snapshot_id, item_name, item_type, group_name,
                uom, new_uom, total_consumed, total_received,
                closing_balance, closing_count, opening_count,
                wastage_count, physical_count, discrepancy_count,
                received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for item in items:
            item_name = item.get("name")

            # Get consumption cost
            cursor.execute("""
                SELECT SUM(consumed_quantity * rate) AS total_consumption_cost
                FROM consumption_tracker
                WHERE item_name = %s AND outlet = %s AND order_date BETWEEN %s AND %s
            """, (item_name, outlet, start_date, end_date))
            consumption_cost = float(cursor.fetchone()["total_consumption_cost"] or 0)

            # Get received cost from store requisition tables
            cursor.execute("""
                SELECT SUM(d.Amount * d.Rate) AS total_received_cost
                FROM intblstorereqdetails d
                JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE d.ItemName = %s 
                    AND r.Outlet = %s 
                    AND DATE(r.Date) BETWEEN %s AND %s
            """, (item_name, outlet, start_date, end_date))

            received_cost = float(cursor.fetchone()["total_received_cost"] or 0)

            # Get wastage cost
            cursor.execute("""
                SELECT SUM(price) AS total_wastage_cost
                FROM wastage_items
                WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s
            """, (item_name, outlet, start_date, end_date))
            wastage_cost = float(cursor.fetchone()["total_wastage_cost"] or 0)

            # Get closing quantity (from frontend input)
            closing_count = float(Decimal(item.get("closing_balance", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP))

            # Get previous closing balance to calculate opening cost
            cursor.execute("""
                SELECT isi.rate, isi.closing_balance
                FROM inventory_snapshot_items isi
                JOIN inventory_snapshot_master ism ON isi.snapshot_id = ism.id
                WHERE ism.outlet_name = %s AND isi.item_name = %s AND ism.end_date < %s
                ORDER BY ism.end_date DESC LIMIT 1
            """, (outlet, item_name, start_date))
            prev = cursor.fetchone()
            opening_cost = 0
            if prev:
                opening_cost = float(prev["closing_balance"] or 0)
            else:
                cursor.execute("""
                    SELECT Rate FROM stock_statement
                    WHERE ItemName = %s AND OutletName = %s
                """, (item_name, outlet))
                opening_rate_result = cursor.fetchone()
                if not opening_rate_result:
                    print(f"{item_name} didnt have stockstatement")
                    # continue
                    opening_cost = 0
                else:
                    opening_rate = float(opening_rate_result["Rate"])
                    opening_cost = opening_rate * float(item.get("opening_count", 0))

            # Total cost = opening + received - wastage - consumption
            total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

            # Step 1: Get physical_count from frontend
            physical_count = float(Decimal(item.get("physical_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP))
            remaining_physical_qty = physical_count
            physical_cost = 0.0

            # Step 2: Fetch from item_current_level in **LIFO** order
            cursor.execute("""
                SELECT quantity, rate FROM item_current_level
                WHERE itemname = %s AND outlet = %s AND quantity > 0
                ORDER BY id DESC
            """, (item_name, outlet))
            stock_rows = cursor.fetchall()

            last_rate = 0.0

            # Step 3: LIFO calculation
            for row in stock_rows:
                available_qty = float(row["quantity"])
                rate = float(row["rate"])
                last_rate = rate  # update last seen rate

                if remaining_physical_qty <= 0:
                    break

                used_qty = min(available_qty, remaining_physical_qty)
                physical_cost += used_qty * rate
                remaining_physical_qty -= used_qty

            # Step 4: If there's still remaining quantity, use the last known rate
            if remaining_physical_qty > 0 and last_rate > 0:
                physical_cost += remaining_physical_qty * last_rate



            actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost

            if is_opening == False:

                rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
                closing_balance = round(physical_count * rate, 2)
            
            else:
                cursor.execute("""
                    SELECT Rate FROM stock_statement
                    WHERE ItemName = %s AND OutletName = %s
                """, (item_name, outlet))
                noopening_rate_result = cursor.fetchone()
                if not opening_rate_result:
                    print(f"{item_name} didnt have stockstatement")
                else:
                    noopening_rate = float(noopening_rate_result["Rate"])
                    closing_cost = noopening_rate * physical_count
                    closing_balance = closing_cost
                    rate = noopening_rate

            # Insert record
            cursor.execute(insert_item_sql, (
                snapshot_id,
                item_name,
                item.get("type"),
                item.get("group_name"),
                item.get("uom"),
                item.get("new_uom"),
                float(Decimal(item.get("total_consumed", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
                float(Decimal(item.get("total_received", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
                closing_balance,
                closing_count,
                float(Decimal(item.get("opening_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
                float(Decimal(item.get("total_wastage", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
                float(Decimal(item.get("physical_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
                float(Decimal(item.get("discrepancy_count", 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
                round(received_cost, 2),
                round(consumption_cost, 2),
                round(wastage_cost, 2),
                rate,
                round(actual_consumption_cost, 2),
                round(opening_cost, 2),
                round(physical_cost, 2)
            ))

            # Opening stock insert (if first snapshot)
            if is_opening:
                cursor.execute("""
                    SELECT Rate FROM stock_statement
                    WHERE ItemName = %s AND OutletName = %s
                """, (item_name, outlet))
                rate_result = cursor.fetchone()
                if not rate_result:
                    continue
                opening_rate = float(rate_result["Rate"])

                # Always insert a new row for opening stock (sequentially)
                cursor.execute("""
                    INSERT INTO item_current_level (itemname, quantity, rate, outlet)
                    VALUES (%s, %s, %s, %s)
                """, (item_name, closing_count, opening_rate, outlet))


        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "snapshot_id": snapshot_id}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500

from .utils_fnb import get_sales_data_for_snapshot, calculate_employee_meal_cost, calculate_complimentary_cost_for_snapshot
from datetime import date

def _key(name):
    """Normalize item names for dict lookups so batched results match
    the same way MySQL's default collation tolerated trailing spaces /
    case differences in the old per-item queries."""
    return (name or "").strip().lower()


@app_file116.route("/save-inventory-snapshot-food", methods=["POST"])
@cross_origin()
def save_inventory_snapshot_food():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        items = data.get("items")
        outlet = data.get("outlet")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        food_total_items = data.get("food_total_items")
        food_accuracy = data.get("food_accuracy")
        food_missing_items = data.get("food_missing_items")

        is_opening = data.get("is_opening", False)
        physical_added = data.get("physical_added", False)

        if not all([items, outlet, start_date, end_date]):
            return jsonify({"error": "Missing required fields."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        today = datetime.now().date()

        if is_opening:
            cursor.execute("""
                SELECT id FROM inventory_snapshot_master_food
                WHERE outlet_name = %s AND is_opening = 1
            """, (outlet,))
            existing_opening = cursor.fetchone()
            if existing_opening:
                opening_id = existing_opening["id"]
                cursor.execute("""
                    DELETE FROM inventory_snapshot_items_food
                    WHERE snapshot_id = %s
                """, (opening_id,))
                cursor.execute("""
                    DELETE FROM inventory_snapshot_master_food
                    WHERE id = %s
                """, (opening_id,))
                print(f"Deleted existing opening snapshot (ID: {opening_id}) for outlet: {outlet}")
        else:
            cursor.execute("""
                SELECT id FROM inventory_snapshot_master_food
                WHERE outlet_name = %s AND DATE(created_at) = %s AND is_opening = 0
            """, (outlet, today))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": f"Inventory snapshot for food has already been saved for {outlet} today."}), 400

        cursor.execute("""
            INSERT INTO inventory_snapshot_master_food (
                outlet_name, start_date, end_date, created_at,
                food_total_items,
                food_accuracy,
                food_missing_items,
                is_opening,
                physical_added
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            outlet, start_date, end_date, datetime.now(),
            food_total_items,
            food_accuracy,
            food_missing_items,
            is_opening,
            physical_added
        ))

        snapshot_id = cursor.lastrowid

        total_opening_cost = 0.0
        total_purchase_cost = 0.0
        total_closing_cost = 0.0
        total_consumption_cost = 0.0
        total_wastage_cost = 0.0

        insert_item_sql = """
            INSERT INTO inventory_snapshot_items_food (
                snapshot_id, item_name, item_type, group_name,
                uom, new_uom, total_consumed, total_received,
                closing_balance, closing_count, opening_count,
                wastage_count, physical_count, discrepancy_count,
                received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost, discrepancy_cost
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # =====================================================================
        # BATCH PREFETCH -- replaces the ~9 per-item SELECTs that used to run
        # inside the loop. Same filters/joins/where-clauses as the originals,
        # run once for all items instead of once per item. All map keys are
        # normalized with _key() so lookups tolerate the same trailing-space /
        # case differences that MySQL's default collation absorbed in the
        # old per-item `WHERE ItemName = %s` queries.
        # =====================================================================
        item_names = [item.get("name") for item in items]
        placeholders = ','.join(['%s'] * len(item_names)) if item_names else ''

        consumption_map = {}
        unit_def_map = {}
        received_map = {}
        wastage_map = {}
        prev_snapshot_map = {}
        storereq_rate_map = {}
        stock_statement_map = {}
        stock_rows_map = {}

        if item_names:
            # 1) consumption cost
            cursor.execute(f"""
                SELECT item_name, SUM(consumed_quantity * rate) AS total_consumption_cost
                FROM consumption_tracker
                WHERE item_name IN ({placeholders}) AND outlet = %s AND order_date BETWEEN %s AND %s
                GROUP BY item_name
            """, (*item_names, outlet, start_date, end_date))
            for row in cursor.fetchall():
                consumption_map[_key(row["item_name"])] = row

            # 2) unit definitions
            cursor.execute(f"""
                SELECT name, unit, uom, rate
                FROM tblunitdefinition
                WHERE name IN ({placeholders}) AND outlet = %s
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                unit_def_map[_key(row["name"])] = row

            # 3) received cost
            cursor.execute(f"""
                SELECT d.ItemName AS item_name, SUM(d.Amount * d.Rate) AS total_received_cost
                FROM intblstorereqdetails d
                JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE d.ItemName IN ({placeholders})
                    AND r.Outlet = %s
                    AND DATE(r.Date) BETWEEN %s AND %s AND r.CostCenter = 'Kitchen'
                GROUP BY d.ItemName
            """, (*item_names, outlet, start_date, end_date))
            for row in cursor.fetchall():
                received_map[_key(row["item_name"])] = row

            # 4) wastage cost
            cursor.execute(f"""
                SELECT item_name, SUM(price) AS total_wastage_cost
                FROM wastage_items
                WHERE item_name IN ({placeholders}) AND outlet_name = %s AND received_date BETWEEN %s AND %s AND costcenter = 'Kitchen'
                GROUP BY item_name
            """, (*item_names, outlet, start_date, end_date))
            for row in cursor.fetchall():
                wastage_map[_key(row["item_name"])] = row

            # 5) previous snapshot per item, latest end_date < start_date
            #    (fetched ordered DESC, keep only the FIRST row seen per item --
            #    identical semantics to the old per-item ORDER BY ... LIMIT 1)
            cursor.execute(f"""
                SELECT isi.item_name, isi.rate, isi.closing_balance, ism.end_date
                FROM inventory_snapshot_items_food isi
                JOIN inventory_snapshot_master_food ism ON isi.snapshot_id = ism.id
                WHERE ism.outlet_name = %s AND isi.item_name IN ({placeholders}) AND ism.end_date < %s
                ORDER BY ism.end_date DESC
            """, (outlet, *item_names, start_date))
            for row in cursor.fetchall():
                k = _key(row["item_name"])
                if k not in prev_snapshot_map:
                    prev_snapshot_map[k] = row

            # 6) latest store-requisition rate per item
            #    (was 3 identical per-item queries reused for opening_rate_result,
            #    noopening_rate_result, and rate_result -- now fetched once)
            cursor.execute(f"""
                SELECT d.ItemName AS item_name, d.Rate AS Rate, r.Date AS req_date
                FROM intblstorereqdetails d
                JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE d.ItemName IN ({placeholders})
                    AND r.Outlet = %s
                    AND r.CostCenter = 'Kitchen'
                ORDER BY r.Date DESC
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                k = _key(row["item_name"])
                if k not in storereq_rate_map:
                    storereq_rate_map[k] = row

            # 7) stock_statement fallback rate per item
            cursor.execute(f"""
                SELECT ItemName, Rate
                FROM stock_statement
                WHERE ItemName IN ({placeholders}) AND OutletName = %s
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                stock_statement_map[_key(row["ItemName"])] = row

            # 8) item_current_level LIFO rows per item, ORDER BY id DESC preserved
            #    (was fetched TWICE per item in the original -- once for
            #    physical_count, once for discrepancy_count. Now fetched once
            #    and reused for both, same as the identical query it replaced.)
            cursor.execute(f"""
                SELECT itemname, quantity, rate
                FROM item_current_level
                WHERE itemname IN ({placeholders}) AND outlet = %s AND quantity > 0
                ORDER BY id DESC
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                stock_rows_map.setdefault(_key(row["itemname"]), []).append(row)
        # =====================================================================
        # END BATCH PREFETCH
        # =====================================================================

        for item in items:
            item_name = item.get("name")
            k = _key(item_name)

            consumption_row = consumption_map.get(k)
            consumption_cost_from_consumption_tracker = float(consumption_row["total_consumption_cost"]) if consumption_row and consumption_row["total_consumption_cost"] is not None else 0

            unit_definition = unit_def_map.get(k)

            if unit_definition and unit_definition["unit"] and unit_definition["unit"] > 0:
                unit = float(unit_definition["unit"])
                consumption_cost = consumption_cost_from_consumption_tracker / unit
                uom = unit_definition["uom"]
                unit_rate = float(unit_definition["rate"] or 0) if unit_definition["rate"] else 0
            else:
                consumption_cost = consumption_cost_from_consumption_tracker
                unit = 1
                uom = "unit"
                unit_rate = 0

            received_row = received_map.get(k)
            received_cost = float(received_row["total_received_cost"]) if received_row and received_row["total_received_cost"] is not None else 0

            wastage_row = wastage_map.get(k)
            wastage_cost = float(wastage_row["total_wastage_cost"]) if wastage_row and wastage_row["total_wastage_cost"] is not None else 0

            closing_count = float(Decimal(item.get("closing_balance", 0)))

            prev = prev_snapshot_map.get(k)
            opening_cost = 0
            if prev:
                opening_cost = float(prev["closing_balance"] or 0)
            else:
                opening_rate_result = storereq_rate_map.get(k)
                if not opening_rate_result:
                    opening_rate_result_stockstatement = stock_statement_map.get(k)
                    if not opening_rate_result_stockstatement:
                        opening_rate = 0
                        opening_cost = 0
                    else:
                        opening_rate = float(opening_rate_result_stockstatement["Rate"])
                        opening_cost = opening_rate * float(item.get("opening_count", 0))
                else:
                    opening_rate = float(opening_rate_result["Rate"])
                    opening_cost = opening_rate * float(item.get("opening_count", 0))

            total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

            physical_count = float(Decimal(item.get("physical_count", 0)))
            remaining_physical_qty = physical_count
            physical_cost = 0.0

            stock_rows = stock_rows_map.get(k, [])

            last_rate = 0.0
            for row in stock_rows:
                available_qty = float(row["quantity"])
                rate = float(row["rate"])
                last_rate = rate

                if remaining_physical_qty <= 0:
                    break

                used_qty = min(available_qty, remaining_physical_qty)
                physical_cost += used_qty * rate
                remaining_physical_qty -= used_qty

            if remaining_physical_qty > 0 and last_rate > 0:
                physical_cost += remaining_physical_qty * last_rate

            discrepancy_count = float(Decimal(item.get("discrepancy_count", 0)))
            remaining_discrepancy_qty = discrepancy_count
            discrepancy_cost = 0.0

            # reuses the SAME stock_rows fetched above -- identical result to
            # the original code's second (duplicate) query for this item
            last_rate = 0.0
            for row in stock_rows:
                available_qty = float(row["quantity"])
                rate = float(row["rate"])
                last_rate = rate

                if remaining_discrepancy_qty <= 0:
                    break

                used_qty = min(available_qty, remaining_discrepancy_qty)
                discrepancy_cost += used_qty * rate
                remaining_discrepancy_qty -= used_qty

            if remaining_discrepancy_qty > 0 and last_rate > 0:
                discrepancy_cost += remaining_discrepancy_qty * last_rate

            actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost

            print("actual_consumption_cost", actual_consumption_cost)
            if is_opening == False:
                rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
                closing_balance = physical_count * rate
            else:
                noopening_rate_result = storereq_rate_map.get(k)
                if not noopening_rate_result:
                    rate_from_stockstatement = stock_statement_map.get(k)
                    if not rate_from_stockstatement:
                        print(f"{item_name} has no rate in store requisition or stock_statement")
                        closing_balance = 0
                        rate = 0
                    else:
                        noopening_rate = float(rate_from_stockstatement["Rate"])
                        closing_cost = noopening_rate * physical_count
                        closing_balance = closing_cost
                        rate = noopening_rate
                else:
                    noopening_rate = float(noopening_rate_result["Rate"])
                    closing_cost = noopening_rate * physical_count
                    closing_balance = closing_cost
                    rate = noopening_rate

            print("I got upto here")
            total_opening_cost += opening_cost
            total_purchase_cost += received_cost
            total_closing_cost += physical_cost
            total_consumption_cost += actual_consumption_cost
            total_wastage_cost += wastage_cost

            cursor.execute(insert_item_sql, (
                snapshot_id,
                item_name,
                item.get("type"),
                item.get("group_name"),
                item.get("uom"),
                item.get("new_uom"),
                float(Decimal(item.get("total_consumed", 0))),
                float(Decimal(item.get("total_received", 0))),
                closing_balance,
                closing_count,
                float(Decimal(item.get("opening_count", 0))),
                float(Decimal(item.get("total_wastage", 0))),
                float(Decimal(item.get("physical_count", 0))),
                float(Decimal(item.get("discrepancy_count", 0))),
                received_cost,
                consumption_cost,
                wastage_cost,
                rate,
                actual_consumption_cost,
                opening_cost,
                physical_cost,
                discrepancy_cost,
            ))

            if is_opening:
                rate_result = storereq_rate_map.get(k)
                if not rate_result:
                    rate_result = stock_statement_map.get(k)
                    if not rate_result:
                        print(f"{item_name} has no rate for opening stock insertion")
                        continue
                opening_rate = float(rate_result["Rate"])
                print("got upto here")
                cursor.execute("""
                    INSERT INTO item_current_level (itemname, quantity, rate, outlet)
                    VALUES (%s, %s, %s, %s)
                """, (item_name, closing_count, opening_rate, outlet))

        print("and got upto here")

        sales_data = get_sales_data_for_snapshot(cursor, outlet, start_date, end_date)
        employee_meal = calculate_employee_meal_cost(outlet, start_date, end_date, "Food")
        complimentary_cost = calculate_complimentary_cost_for_snapshot(cursor, outlet, start_date, end_date)
        complimentary = complimentary_cost.get('Food', 0.0)

        total_discount = sales_data['food_discount']

        gross_sales = sales_data['food_sales']
        gross_cost = sales_data['food_cost']
        gross_cost_percent = round((float(gross_cost) / float(gross_sales) * 100), 2) if gross_sales else 0
        total_complementary = sales_data['food_complimentary']

        net_sale = sales_data['food_sales'] - total_discount - total_complementary
        net_cost = float(total_opening_cost) + float(total_purchase_cost) - float(total_closing_cost) - float(employee_meal) - float(complimentary)
        net_cost_percent = (float(gross_cost) / float(net_sale) * 100) if net_sale > 0 else 0

        if is_opening != True:
            fnb_insert_query = """
                INSERT INTO tblfnbcostingdetails 
                (outlet_name, report_for, opening, purchase, closing, employee_meal, 
                complimentary, net_cost, total_discount, cost_of_goods_sold, net_sale, 
                net_cost_percent, from_date, to_date, date, gross_cost, gross_sales, gross_cost_percent, wastage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(fnb_insert_query, (
                outlet,
                'Food',
                total_opening_cost,
                total_purchase_cost,
                total_closing_cost,
                employee_meal,
                complimentary,
                net_cost,
                total_discount,
                total_consumption_cost,
                net_sale,
                net_cost_percent,
                start_date,
                end_date,
                date.today(),
                gross_cost,
                gross_sales,
                gross_cost_percent,
                total_wastage_cost
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "snapshot_id": snapshot_id}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500

from datetime import date

def _key(name):
    """Normalize item names for dict lookups so batched results match
    the same way MySQL's default collation tolerated trailing spaces /
    case differences in the old per-item queries."""
    return (name or "").strip().lower()


@app_file116.route("/save-inventory-snapshot-beverage", methods=["POST"])
@cross_origin()
def save_inventory_snapshot_beverage():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        items = data.get("items")
        outlet = data.get("outlet")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        beverage_total_items = data.get("beverage_total_items")
        beverage_accuracy = data.get("beverage_accuracy")
        beverage_missing_items = data.get("beverage_missing_items")

        is_opening = data.get("is_opening", False)
        physical_added = data.get("physical_added", False)

        if not all([items, outlet, start_date, end_date]):
            return jsonify({"error": "Missing required fields."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        today = datetime.now().date()

        if is_opening:
            cursor.execute("""
                SELECT id FROM inventory_snapshot_master_beverage
                WHERE outlet_name = %s AND is_opening = 1
            """, (outlet,))
            existing_opening = cursor.fetchone()
            if existing_opening:
                opening_id = existing_opening["id"]
                cursor.execute("""
                    DELETE FROM inventory_snapshot_items_beverage
                    WHERE snapshot_id = %s
                """, (opening_id,))
                cursor.execute("""
                    DELETE FROM inventory_snapshot_master_beverage
                    WHERE id = %s
                """, (opening_id,))
                print(f"Deleted existing opening snapshot (ID: {opening_id}) for outlet: {outlet}")
        else:
            cursor.execute("""
                SELECT id FROM inventory_snapshot_master_beverage
                WHERE outlet_name = %s AND DATE(created_at) = %s AND is_opening = 0
            """, (outlet, today))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": f"Inventory snapshot for beverage has already been saved for {outlet} today."}), 400

        cursor.execute("""
            INSERT INTO inventory_snapshot_master_beverage (
                outlet_name, start_date, end_date, created_at,
                beverage_total_items,
                beverage_accuracy,
                beverage_missing_items,
                is_opening,
                physical_added
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            outlet, start_date, end_date, datetime.now(),
            beverage_total_items,
            beverage_accuracy,
            beverage_missing_items,
            is_opening,
            physical_added
        ))

        snapshot_id = cursor.lastrowid

        total_opening_cost = 0.0
        total_purchase_cost = 0.0
        total_closing_cost = 0.0
        total_consumption_cost = 0.0
        total_wastage_cost = 0.0

        insert_item_sql = """
            INSERT INTO inventory_snapshot_items_beverage (
                snapshot_id, item_name, item_type, group_name,
                uom, new_uom, total_consumed, total_received,
                closing_balance, closing_count, opening_count,
                wastage_count, physical_count, discrepancy_count,
                received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost, discrepancy_cost
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # =====================================================================
        # BATCH PREFETCH -- replaces the per-item SELECTs that used to run
        # inside the loop. Same filters/joins/where-clauses as the originals
        # (CostCenter = 'Bar' preserved throughout), run once for all items
        # instead of once per item. All map keys are normalized with _key()
        # so lookups tolerate the same trailing-space / case differences that
        # MySQL's default collation absorbed in the old `WHERE ItemName = %s`
        # per-item queries.
        # =====================================================================
        item_names = [item.get("name") for item in items]
        placeholders = ','.join(['%s'] * len(item_names)) if item_names else ''

        consumption_map = {}
        unit_def_map = {}
        received_map = {}
        wastage_map = {}
        prev_snapshot_map = {}
        storereq_rate_map = {}
        stock_statement_map = {}
        stock_rows_map = {}

        if item_names:
            # 1) consumption cost
            cursor.execute(f"""
                SELECT item_name, SUM(consumed_quantity * rate) AS total_consumption_cost
                FROM consumption_tracker
                WHERE item_name IN ({placeholders}) AND outlet = %s AND order_date BETWEEN %s AND %s
                GROUP BY item_name
            """, (*item_names, outlet, start_date, end_date))
            for row in cursor.fetchall():
                consumption_map[_key(row["item_name"])] = row

            # 2) unit definitions
            cursor.execute(f"""
                SELECT name, unit, uom, rate
                FROM tblunitdefinition
                WHERE name IN ({placeholders}) AND outlet = %s
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                unit_def_map[_key(row["name"])] = row

            # 3) received cost -- CostCenter = 'Bar' (original had "and CostCenter = 'Bar'"
            #    unqualified with a table alias -- kept exactly as-is)
            cursor.execute(f"""
                SELECT d.ItemName AS item_name, SUM(d.Amount * d.Rate) AS total_received_cost
                FROM intblstorereqdetails d
                JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE d.ItemName IN ({placeholders})
                    AND r.Outlet = %s
                    AND DATE(r.Date) BETWEEN %s AND %s and CostCenter = 'Bar'
                GROUP BY d.ItemName
            """, (*item_names, outlet, start_date, end_date))
            for row in cursor.fetchall():
                received_map[_key(row["item_name"])] = row

            # 4) wastage cost -- costcenter = 'Bar'
            cursor.execute(f"""
                SELECT item_name, SUM(price) AS total_wastage_cost
                FROM wastage_items
                WHERE item_name IN ({placeholders}) AND outlet_name = %s AND received_date BETWEEN %s AND %s and costcenter = 'Bar'
                GROUP BY item_name
            """, (*item_names, outlet, start_date, end_date))
            for row in cursor.fetchall():
                wastage_map[_key(row["item_name"])] = row

            # 5) previous snapshot per item, latest end_date < start_date
            #    (fetched ordered DESC, keep only the FIRST row seen per item --
            #    identical semantics to the old per-item ORDER BY ... LIMIT 1)
            cursor.execute(f"""
                SELECT isi.item_name, isi.rate, isi.closing_balance, ism.end_date
                FROM inventory_snapshot_items_beverage isi
                JOIN inventory_snapshot_master_beverage ism ON isi.snapshot_id = ism.id
                WHERE ism.outlet_name = %s AND isi.item_name IN ({placeholders}) AND ism.end_date < %s
                ORDER BY ism.end_date DESC
            """, (outlet, *item_names, start_date))
            for row in cursor.fetchall():
                k = _key(row["item_name"])
                if k not in prev_snapshot_map:
                    prev_snapshot_map[k] = row

            # 6) latest store-requisition rate per item, CostCenter = 'Bar'
            #    (was 3 identical per-item queries reused for opening_rate_result,
            #    noopening_rate_result, and rate_result -- now fetched once)
            cursor.execute(f"""
                SELECT d.ItemName AS item_name, d.Rate AS Rate, r.Date AS req_date
                FROM intblstorereqdetails d
                JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE d.ItemName IN ({placeholders})
                    AND r.Outlet = %s
                    AND r.CostCenter = 'Bar'
                ORDER BY r.Date DESC
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                k = _key(row["item_name"])
                if k not in storereq_rate_map:
                    storereq_rate_map[k] = row

            # 7) stock_statement fallback rate per item
            cursor.execute(f"""
                SELECT ItemName, Rate
                FROM stock_statement
                WHERE ItemName IN ({placeholders}) AND OutletName = %s
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                stock_statement_map[_key(row["ItemName"])] = row

            # 8) item_current_level LIFO rows per item, ORDER BY id DESC preserved
            #    (was fetched TWICE per item in the original -- once for
            #    physical_count, once for discrepancy_count. Now fetched once
            #    and reused for both, same as the identical query it replaced.)
            cursor.execute(f"""
                SELECT itemname, quantity, rate
                FROM item_current_level
                WHERE itemname IN ({placeholders}) AND outlet = %s AND quantity > 0
                ORDER BY id DESC
            """, (*item_names, outlet))
            for row in cursor.fetchall():
                stock_rows_map.setdefault(_key(row["itemname"]), []).append(row)
        # =====================================================================
        # END BATCH PREFETCH
        # =====================================================================

        for item in items:
            item_name = item.get("name")
            k = _key(item_name)

            consumption_row = consumption_map.get(k)
            consumption_cost_from_consumption_tracker = float(consumption_row["total_consumption_cost"]) if consumption_row and consumption_row["total_consumption_cost"] is not None else 0

            unit_definition = unit_def_map.get(k)

            if unit_definition and unit_definition["unit"] and unit_definition["unit"] > 0:
                unit = float(unit_definition["unit"])
                consumption_cost = consumption_cost_from_consumption_tracker / unit
                uom = unit_definition["uom"]
                unit_rate = float(unit_definition["rate"] or 0) if unit_definition["rate"] else 0
            else:
                consumption_cost = consumption_cost_from_consumption_tracker
                unit = 1
                uom = "unit"
                unit_rate = 0

            received_row = received_map.get(k)
            received_cost = float(received_row["total_received_cost"]) if received_row and received_row["total_received_cost"] is not None else 0

            wastage_row = wastage_map.get(k)
            wastage_cost = float(wastage_row["total_wastage_cost"]) if wastage_row and wastage_row["total_wastage_cost"] is not None else 0

            closing_count = float(Decimal(item.get("closing_balance", 0)))

            prev = prev_snapshot_map.get(k)
            opening_cost = 0
            if prev:
                opening_cost = float(prev["closing_balance"] or 0)
            else:
                opening_rate_result = storereq_rate_map.get(k)
                if not opening_rate_result:
                    print(f"{item_name} didnt have store requisition")
                    opening_rate_result_stockstatement = stock_statement_map.get(k)
                    if not opening_rate_result_stockstatement:
                        opening_rate = 0
                        opening_cost = 0
                    else:
                        opening_rate = float(opening_rate_result_stockstatement["Rate"])
                        opening_cost = opening_rate * float(item.get("opening_count", 0))
                else:
                    opening_rate = float(opening_rate_result["Rate"])
                    opening_cost = opening_rate * float(item.get("opening_count", 0))

            total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

            physical_count = float(Decimal(item.get("physical_count", 0)))
            remaining_physical_qty = physical_count
            physical_cost = 0.0

            stock_rows = stock_rows_map.get(k, [])

            last_rate = 0.0
            for row in stock_rows:
                available_qty = float(row["quantity"])
                rate = float(row["rate"])
                last_rate = rate

                if remaining_physical_qty <= 0:
                    break

                used_qty = min(available_qty, remaining_physical_qty)
                physical_cost += used_qty * rate
                remaining_physical_qty -= used_qty

            if remaining_physical_qty > 0 and last_rate > 0:
                physical_cost += remaining_physical_qty * last_rate

            discrepancy_count = float(Decimal(item.get("discrepancy_count", 0)))
            remaining_discrepancy_qty = discrepancy_count
            discrepancy_cost = 0.0

            # reuses the SAME stock_rows fetched above -- identical result to
            # the original code's second (duplicate) query for this item
            last_rate = 0.0
            for row in stock_rows:
                available_qty = float(row["quantity"])
                rate = float(row["rate"])
                last_rate = rate

                if remaining_discrepancy_qty <= 0:
                    break

                used_qty = min(available_qty, remaining_discrepancy_qty)
                discrepancy_cost += used_qty * rate
                remaining_discrepancy_qty -= used_qty

            if remaining_discrepancy_qty > 0 and last_rate > 0:
                discrepancy_cost += remaining_discrepancy_qty * last_rate

            actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost

            print("actual_consumption_cost", actual_consumption_cost)
            if is_opening == False:
                rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
                closing_balance = physical_count * rate
            else:
                noopening_rate_result = storereq_rate_map.get(k)
                if not noopening_rate_result:
                    rate_from_stockstatement = stock_statement_map.get(k)
                    if not rate_from_stockstatement:
                        print(f"{item_name} has no rate in store requisition or stock_statement")
                        closing_balance = 0
                        rate = 0
                    else:
                        noopening_rate = float(rate_from_stockstatement["Rate"])
                        closing_cost = noopening_rate * physical_count
                        closing_balance = closing_cost
                        rate = noopening_rate
                else:
                    noopening_rate = float(noopening_rate_result["Rate"])
                    closing_cost = noopening_rate * physical_count
                    closing_balance = closing_cost
                    rate = noopening_rate

            print("I got upto here")
            total_opening_cost += opening_cost
            total_purchase_cost += received_cost
            total_closing_cost += physical_cost
            total_consumption_cost += actual_consumption_cost
            total_wastage_cost += wastage_cost

            cursor.execute(insert_item_sql, (
                snapshot_id,
                item_name,
                item.get("type"),
                item.get("group_name"),
                item.get("uom"),
                item.get("new_uom"),
                float(Decimal(item.get("total_consumed", 0))),
                float(Decimal(item.get("total_received", 0))),
                closing_balance,
                closing_count,
                float(Decimal(item.get("opening_count", 0))),
                float(Decimal(item.get("total_wastage", 0))),
                float(Decimal(item.get("physical_count", 0))),
                float(Decimal(item.get("discrepancy_count", 0))),
                received_cost,
                consumption_cost,
                wastage_cost,
                rate,
                actual_consumption_cost,
                opening_cost,
                physical_cost,
                discrepancy_cost,
            ))

            if is_opening:
                rate_result = storereq_rate_map.get(k)
                if not rate_result:
                    rate_result = stock_statement_map.get(k)
                    if not rate_result:
                        print(f"{item_name} has no rate for opening stock insertion")
                        continue
                opening_rate = float(rate_result["Rate"])
                print("got upto here")
                cursor.execute("""
                    INSERT INTO item_current_level (itemname, quantity, rate, outlet)
                    VALUES (%s, %s, %s, %s)
                """, (item_name, closing_count, opening_rate, outlet))

        print("and got upto here")

        sales_data = get_sales_data_for_snapshot(cursor, outlet, start_date, end_date)
        employee_meal = calculate_employee_meal_cost(outlet, start_date, end_date, "Beverage")
        complimentary_cost = calculate_complimentary_cost_for_snapshot(cursor, outlet, start_date, end_date)
        complimentary = complimentary_cost.get('Beverage', 0.0)

        total_discount = sales_data['beverage_discount']

        gross_sales = sales_data['beverage_sales']
        gross_cost = sales_data['beverage_cost']
        gross_cost_percent = round((float(gross_cost) / float(gross_sales) * float(100)), 2) if gross_sales else 0

        total_complementary = sales_data['beverage_complimentary']
        net_sale = sales_data['beverage_sales'] - total_discount - total_complementary

        net_cost = float(total_opening_cost) + float(total_purchase_cost) - float(total_closing_cost) - float(employee_meal) - float(complimentary)
        net_cost_percent = (float(gross_cost) / float(net_sale) * 100) if net_sale > 0 else 0

        if is_opening != True:
            fnb_insert_query = """
                INSERT INTO tblfnbcostingdetails 
                (outlet_name, report_for, opening, purchase, closing, employee_meal, 
                complimentary, net_cost, total_discount, cost_of_goods_sold, net_sale, 
                net_cost_percent, from_date, to_date, date, gross_cost, gross_sales, gross_cost_percent, wastage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(fnb_insert_query, (
                outlet,
                'Beverage',
                total_opening_cost,
                total_purchase_cost,
                total_closing_cost,
                employee_meal,
                complimentary,
                net_cost,
                total_discount,
                total_consumption_cost,
                net_sale,
                net_cost_percent,
                start_date,
                end_date,
                date.today(),
                gross_cost,
                gross_sales,
                gross_cost_percent,
                total_wastage_cost
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "snapshot_id": snapshot_id}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500