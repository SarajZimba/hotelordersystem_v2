from flask import Blueprint, jsonify, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime

from decimal import Decimal

from root.auth.check import token_auth

from .utils import get_sales_data_for_central_kitchen

from datetime import date

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )

load_dotenv()

app_file233 = Blueprint('app_file233', __name__)

@app_file233.route("/save-inventory-snapshot-production", methods=["POST"])
@cross_origin()
def save_inventory_snapshot_production():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        items = data.get("items")
        outlet = data.get("outlet")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        total_items = data.get("total_items")
        accuracy = data.get("accuracy")
        missing_items = data.get("missing_items")

        is_opening = data.get("is_opening", False)  # Default to False if not provided
        physical_added = data.get("physical_added", False)  # Default to False if not provided

        if not all([items, outlet, start_date, end_date]):
            return jsonify({"error": "Missing required fields."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = datetime.now().date()

         # Check if opening snapshot already exists for this outlet
        if is_opening:
            # Check for existing opening snapshot
            cursor.execute("""
                SELECT id FROM production_inventorycalculation
                WHERE outlet_name = %s AND is_opening = 1
            """, (outlet,))
            
            existing_opening = cursor.fetchone()
            
            if existing_opening:
                # Delete existing opening snapshot and its items
                opening_id = existing_opening["id"]
                
                # Delete items first (foreign key constraint)
                cursor.execute("""
                    DELETE FROM production_inventorycalculation_items
                    WHERE calculation_id = %s
                """, (opening_id,))
                
                # Delete the master record
                cursor.execute("""
                    DELETE FROM production_inventorycalculation
                    WHERE id = %s
                """, (opening_id,))
                
                print(f"Deleted existing opening snapshot (ID: {opening_id}) for outlet: {outlet}")
        else:
            # For non-opening snapshots, check if a snapshot was already saved today
            cursor.execute("""
                SELECT id FROM production_inventorycalculation
                WHERE outlet_name = %s AND DATE(created_at) = %s AND is_opening = 0
            """, (outlet, today))
            
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": f"Inventory snapshot for beverage has already been saved for {outlet} today."}), 400

        # Insert master record
        cursor.execute("""
            INSERT INTO production_inventorycalculation (
                outlet_name, start_date, end_date, created_at,
                total_items,
                accuracy,
                missing_items,
                is_opening,
                physical_added
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            outlet, start_date, end_date, datetime.now(),
            total_items, 
            accuracy,
            missing_items,
            is_opening,
            physical_added
        ))

        calculation_id = cursor.lastrowid

        # Track totals for FNB Costing
        total_opening_cost = 0.0
        total_purchase_cost = 0.0
        total_closing_cost = 0.0
        total_consumption_cost = 0.0
        total_wastage_cost = 0.0

        insert_item_sql = """
            INSERT INTO production_inventorycalculation_items (
                calculation_id, item_name, item_type, group_name,
                uom, new_uom, total_consumed, total_received,
                closing_balance, closing_count, opening_count,
                wastage_count, physical_count, discrepancy_count,
                received_cost, consumption_cost, wastage_cost, rate,actual_consumption_cost,opening_cost, physical_cost, discrepancy_cost
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for item in items:
            item_name = item.get("name")

            # Get consumption cost
            cursor.execute("""
                SELECT SUM(consumed_quantity * rate) AS total_consumption_cost
                FROM production_consumption_tracker
                WHERE item_name = %s AND outlet = %s AND order_date BETWEEN %s AND %s
            """, (item_name, outlet, start_date, end_date))
            consumption_cost_from_consumption_tracker = float(cursor.fetchone()["total_consumption_cost"] or 0)


            # Get unit definition for the item
            cursor.execute("""
                SELECT unit, uom, rate
                FROM tblunitdefinition
                WHERE name = %s AND outlet = %s
            """, (item_name, outlet))
            
            unit_definition = cursor.fetchone()
            
            # Calculate real consumption cost based on unit
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

            # # Get received cost
            # cursor.execute("""
            #     SELECT SUM(quantity * price) AS total_received_cost
            #     FROM received_items
            #     WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s
            # """, (item_name, outlet, start_date, end_date))

            # Get received cost from store requisition tables
            cursor.execute("""
                SELECT SUM(d.Amount * d.Rate) AS total_received_cost
                FROM intblstorereqdetails d
                JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE d.ItemName = %s 
                    AND r.Outlet = %s 
                    AND DATE(r.Date) BETWEEN %s AND %s and CostCenter = 'Central Kitchen'
            """, (item_name, outlet, start_date, end_date))

            received_cost = float(cursor.fetchone()["total_received_cost"] or 0)

            # Get wastage cost
            cursor.execute("""
                SELECT SUM(price) AS total_wastage_cost
                FROM production_wastage_items
                WHERE item_name = %s AND outlet_name = %s AND received_date BETWEEN %s AND %s and costcenter = 'Central Kitchen'
            """, (item_name, outlet, start_date, end_date))
            wastage_cost = float(cursor.fetchone()["total_wastage_cost"] or 0)

            # Get closing quantity (from frontend input)
            closing_count = float(Decimal(item.get("closing_balance", 0)))

            # Get previous closing balance to calculate opening cost
            cursor.execute("""
                SELECT isi.rate, isi.closing_balance
                FROM production_inventorycalculation_items isi
                JOIN production_inventorycalculation ism ON isi.calculation_id = ism.id
                WHERE ism.outlet_name = %s AND isi.item_name = %s AND ism.end_date < %s
                ORDER BY ism.end_date DESC LIMIT 1
            """, (outlet, item_name, start_date))
            prev = cursor.fetchone()
            opening_cost = 0
            if prev:
                opening_cost = float(prev["closing_balance"] or 0)
            else:
                # cursor.execute("""
                #     SELECT Rate FROM stock_statement
                #     WHERE ItemName = %s AND OutletName = %s
                # """, (item_name, outlet))

                cursor.execute("""
                    SELECT d.Rate
                    FROM intblstorereqdetails d
                    JOIN intblstorerequisition r 
                        ON d.StoreReqID = r.idintblStoreRequisition
                    WHERE d.ItemName = %s 
                        AND r.Outlet = %s
                        AND r.CostCenter = 'Central Kitchen'
                    ORDER BY r.Date DESC 
                    LIMIT 1
                """, (item_name, outlet))
                opening_rate_result = cursor.fetchone()
                if not opening_rate_result:
                    print(f"{item_name} didnt have store requisition")
                    # continue
                    opening_cost = 0
                else:
                    opening_rate = float(opening_rate_result["Rate"])
                    opening_cost = opening_rate * float(item.get("opening_count", 0))

            # Total cost = opening + received - wastage - consumption
            total_cost = opening_cost + received_cost - wastage_cost - consumption_cost

            # Step 1: Get physical_count from frontend
            physical_count = float(Decimal(item.get("physical_count", 0)))
            remaining_physical_qty = physical_count
            physical_cost = 0.0

            # Step 2: Fetch from item_current_level in **LIFO** order
            cursor.execute("""
                SELECT quantity, rate FROM production_item_current_level
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


            # Step 5: Get discrepancy_count from frontend
            discrepancy_count = abs(float(Decimal(item.get("discrepancy_count", 0))))
            remaining_discrepancy_qty = discrepancy_count
            discrepancy_cost = 0.0

            # Step 2: Fetch from item_current_level in **LIFO** order
            cursor.execute("""
                SELECT quantity, rate FROM production_item_current_level
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

                if remaining_discrepancy_qty <= 0:
                    break

                used_qty = min(available_qty, remaining_discrepancy_qty)
                discrepancy_cost += used_qty * rate
                remaining_discrepancy_qty -= used_qty

            # Step 4: If there's still remaining quantity, use the last known rate
            if remaining_discrepancy_qty > 0 and last_rate > 0:
                discrepancy_cost += remaining_discrepancy_qty * last_rate


            actual_consumption_cost = opening_cost + received_cost + wastage_cost - physical_cost


            print("actual_consumption_cost", actual_consumption_cost)
            if is_opening == False:

                rate = round(total_cost / physical_count, 4) if physical_count > 0 else 0
                closing_balance = physical_count * rate
            
            else:
                # cursor.execute("""
                #     SELECT Rate FROM stock_statement
                #     WHERE ItemName = %s AND OutletName = %s
                # """, (item_name, outlet))

                cursor.execute("""
                    SELECT d.Rate
                    FROM intblstorereqdetails d
                    JOIN intblstorerequisition r 
                        ON d.StoreReqID = r.idintblStoreRequisition
                    WHERE d.ItemName = %s 
                        AND r.Outlet = %s
                        AND r.CostCenter = 'Central Kitchen'
                    ORDER BY r.Date DESC 
                    LIMIT 1
                """, (item_name, outlet))
                noopening_rate_result = cursor.fetchone()
                if not opening_rate_result:
                    print(f"{item_name} didnt have store requisition")
                else:
                    noopening_rate = float(noopening_rate_result["Rate"])
                    closing_cost = noopening_rate * physical_count
                    closing_balance = closing_cost
                    rate = noopening_rate


            print("I got upto here")
            # Accumulate totals for FNB Costing
            total_opening_cost += opening_cost
            total_purchase_cost += received_cost 
            total_closing_cost += physical_cost 
            total_consumption_cost += actual_consumption_cost 
            total_wastage_cost += wastage_cost 

            # Insert record
            cursor.execute(insert_item_sql, (
                calculation_id,
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

            # Opening stock insert (if first snapshot)
            if is_opening:
                # cursor.execute("""
                #     SELECT Rate FROM stock_statement
                #     WHERE ItemName = %s AND OutletName = %s
                # """, (item_name, outlet))

                cursor.execute("""
                    SELECT d.Rate
                    FROM intblstorereqdetails d
                    JOIN intblstorerequisition r 
                        ON d.StoreReqID = r.idintblStoreRequisition
                    WHERE d.ItemName = %s 
                        AND r.Outlet = %s
                        AND r.CostCenter = 'Central Kitchen'
                    ORDER BY r.Date DESC 
                    LIMIT 1
                """, (item_name, outlet))
                rate_result = cursor.fetchone()
                if not rate_result:
                    continue
                opening_rate = float(rate_result["Rate"])
                print("got upto here")
                # Always insert a new row for opening stock (sequentially)
                cursor.execute("""
                    INSERT INTO item_current_level (itemname, quantity, rate, outlet)
                    VALUES (%s, %s, %s, %s)
                """, (item_name, closing_count, opening_rate, outlet))

        print("and got upto here")
        # ============ CALCULATE AND SAVE FNB COSTING ============

        # Get sales data for the period
        sales_data = get_sales_data_for_central_kitchen(cursor, outlet, start_date, end_date)
        
        # Calculate employee meal cost from Staff Consumption
        # employee_meal = calculate_employee_meal_cost(outlet, start_date, end_date, "Beverage")
        
        # # Calculate complimentary cost
        # complimentary = calculate_complimentary_cost_for_snapshot(cursor, outlet, start_date, end_date)
        
        # Get total discount from sales data
        # total_discount = sales_data['discounts_sales']

        gross_sales = sales_data['gross_sales']
        gross_cost = sales_data['gross_cost']
        gross_cost_percent = sales_data['gross_cost_percent']
        
        # Calculate net sale for beverage
        net_sale = sales_data['sales'] 
        

        employee_meal = 0
        complimentary = 0
        # Calculate net cost
        net_cost = total_opening_cost + total_purchase_cost - total_closing_cost - employee_meal - complimentary
        total_discount = 0
        # Calculate cost percent
        net_cost_percent = (net_cost / net_sale * 100) if net_sale > 0 else 0
        if is_opening != True:        
            # Insert into FNB Costing table
            fnb_insert_query = """
                INSERT INTO production_tblfnbcostingdetails 
                (outlet_name, report_for, opening, purchase, closing, employee_meal, 
                complimentary, net_cost, total_discount, cost_of_goods_sold, net_sale, 
                net_cost_percent, from_date, to_date, date, gross_cost, gross_sales, gross_cost_percent, wastage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(fnb_insert_query, (
                outlet,
                'Beverage',  # report_for
                total_opening_cost,
                total_purchase_cost,
                total_closing_cost,
                employee_meal,
                complimentary,
                net_cost,
                total_discount,
                total_consumption_cost,  # cost_of_goods_sold
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

        return jsonify({"status": "success", "calculation_id": calculation_id}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500