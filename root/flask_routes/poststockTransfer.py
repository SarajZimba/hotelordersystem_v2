# # from flask import Flask, Blueprint, request, jsonify
# # import mysql.connector
# # from flask_cors import cross_origin

# # import os

# # from dotenv import load_dotenv
# # from datetime import datetime

# # load_dotenv()


# # app_file57 = Blueprint('appfile_57', __name__)


# # @app_file57.route('/poststockTransfer', methods = ["POST"])

# # @cross_origin()
# # def postStock():
# #     try:
# #         mydb = mysql.connector.connect(user=os.getenv('user'), password = os.getenv('password'), host= os.getenv('host'))

# #         cursor = mydb.cursor(buffered=True)

# #         database_sql = "USE {};".format(os.getenv('database'))

# #         cursor.execute(database_sql)

# #         json = request.get_json()

# #         store_itemdetails = json.pop("ItemDetailsList", None)

# #         store_requisition = json

# #         # Convert the date to MySQL compatible format
# #         try:
# #             date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
# #             formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
# #         except Exception as e:
# #             return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400

# #         insert_storerequisitionSql = """ Insert into intblstorerequisition (`Date`, `CostCenter`, `Outlet`, `OutletREQID`) values (%s,%s,%s,%s)"""

# #         cursor.execute(insert_storerequisitionSql, (formatted_date,store_requisition["CostCenter"], store_requisition["OutletName"],store_requisition["Outlet_Req_ID"],))

# #         # Get the id of the last inserted record in intblstorerequisition
# #         store_req_id = cursor.lastrowid

# #         costcenter = store_requisition["CostCenter"]

# #         item_type = "Food"
# #         if costcenter == "Kitchen":
# #             item_type = "Food"

# #         else:
# #             item_type = "Beverage"

# #         for item in store_itemdetails:

# #             insert_storerequisitiondetailsSql = """ Insert into intblstorereqdetails (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) values (%s,%s,%s,%s,%s,%s,%s,%s)"""


# #             cursor.execute(insert_storerequisitiondetailsSql, (item["ItemName"], item["GroupName"], item["BrandName"], item["Amount"], item["UOM"], item["Rate"], store_req_id,item_type))


# #             # Always insert new entry into item_current_level (sequential entry)
# #             cursor.execute("""
# #                 INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
# #                 VALUES (%s, %s, %s, %s)
# #             """, (
# #                 item['item_name'],
# #                 float(item['quantity']),
# #                 float(item['price']),
# #                 store_requisition["OutletName"],
# #                 costcenter                
# #             ))

# #         # Commit the transaction to save changes
# #         mydb.commit()

# #         # Return a success response
# #         return jsonify({"status": "success", "message": "Stock transfer request added successfully!"})
    
# #     except Exception as e:

# #         data = {"error": str(e)}
# #         return data, 400
    
# #     finally:
# #         mydb.close()


# from flask import Flask, Blueprint, request, jsonify
# import mysql.connector
# from flask_cors import cross_origin

# import os

# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()


# app_file57 = Blueprint('appfile_57', __name__)


# @app_file57.route('/poststockTransfer', methods = ["POST"])

# @cross_origin()
# def postStock():
#     try:
#         mydb = mysql.connector.connect(user=os.getenv('user'), password = os.getenv('password'), host= os.getenv('host'))

#         cursor = mydb.cursor(buffered=True)

#         database_sql = "USE {};".format(os.getenv('database'))

#         cursor.execute(database_sql)

#         json = request.get_json()

#         store_itemdetails = json.pop("ItemDetailsList", None)

#         store_requisition = json

#         # Convert the date to MySQL compatible format
#         try:
#             date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
#             formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#         except Exception as e:
#             return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400
        
#         purchase_from = store_requisition.get("purchase_from", "c_app")

#         purchase_id = store_requisition.get("purchase_id", None)


#         # Generate OutletREQID based on purchase_from
#         if purchase_from == "web":
#             cursor.execute("""
#                 SELECT MAX(CAST(OutletREQID AS UNSIGNED)) 
#                 FROM intblstorerequisition
#                 WHERE Outlet = %s
#             """, (store_requisition["OutletName"],))
            
#             max_id = cursor.fetchone()[0]
            
#             if max_id is None:
#                 outlet_req_id = 1
#             else:
#                 outlet_req_id = int(max_id) + 1
#         else:
#             outlet_req_id = store_requisition["Outlet_Req_ID"]

#         insert_storerequisitionSql = """ Insert into intblstorerequisition (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) values (%s,%s,%s,%s,%s,%s)"""

#         cursor.execute(insert_storerequisitionSql, (formatted_date,store_requisition["CostCenter"], store_requisition["OutletName"],outlet_req_id, purchase_from, purchase_id))

#         # Get the id of the last inserted record in intblstorerequisition
#         store_req_id = cursor.lastrowid

#         costcenter = store_requisition["CostCenter"]

#         item_type = "Food"
#         if costcenter == "Kitchen":
#             item_type = "Food"

#         elif costcenter == "Bar":
#             item_type = "Beverage"

#         else:
#             item_type = costcenter

#         for item in store_itemdetails:
#             # DEDUCT FROM stock_current_level TABLE USING FIFO (EARLIEST EXPIRY FIRST)
#             item_name = item["ItemName"]
#             requested_qty = float(item["Amount"])

#             # stocktype = item.get("stocktype")

#             # if stocktype == "Stockable":
            
#             # # Check if sufficient stock is available
#             # cursor.execute("""
#             #         SELECT SUM(qty) as total_available 
#             #         FROM stock_current_level 
#             #         WHERE name = %s 
#             #         AND qty > 0
#             #         AND (expiry_date IS NULL OR expiry_date > CURDATE())
#             #     """, (item_name,))
                
#             # result = cursor.fetchone()
#             # total_available = result[0] if result[0] else 0
                
#             # if total_available < requested_qty:
#             #     raise Exception(f"Insufficient stock for {item_name}. Available: {total_available}, Requested: {requested_qty}")
                
#             # # Get stock batches ordered by expiry date (earliest first)
#             # cursor.execute("""
#             #         SELECT id, qty, total, rate, expiry_date
#             #         FROM stock_current_level 
#             #         WHERE name = %s 
#             #         AND qty > 0
#             #         AND (expiry_date IS NULL OR expiry_date > CURDATE())
#             #         ORDER BY expiry_date ASC, id ASC
#             #     """, (item_name,))
                
#             # stock_batches = cursor.fetchall()
#             # remaining_to_deduct = requested_qty
                
#             # # Deduct from batches
#             # for batch in stock_batches:
#             #     if remaining_to_deduct <= 0:
#             #         break
                        
#             #     batch_id = batch[0]
#             #     current_qty = float(batch[1])
#             #     current_total = float(batch[2])
#             #     current_rate = float(batch[3])
                    
#             #     if current_qty <= remaining_to_deduct:
#             #         # Remove entire batch
#             #         new_qty = 0
#             #         new_total = 0
#             #         remaining_to_deduct -= current_qty
#             #     else:
#             #         # Partially deduct from this batch
#             #         new_qty = current_qty - remaining_to_deduct
#             #         new_total = new_qty * current_rate
#             #         remaining_to_deduct = 0
                    
#             #     # Update the stock_current_level
#             #     cursor.execute("""
#             #         UPDATE stock_current_level 
#             #         SET qty = %s, total = %s 
#             #         WHERE id = %s
#             #     """, (new_qty, new_total, batch_id))


#             # SUBTRACT FROM stock_statement (aggregated stock)
#             cursor.execute("""
#                 SELECT CurrentLevel, Total 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item["ItemName"], item["UOM"], store_requisition["OutletName"]))

#             existing = cursor.fetchone()

#             if existing:
#                 current_level = float(existing[0])
#                 current_total = float(existing[1]) if existing[1] else 0

#                 new_level = current_level - requested_qty
#                 deduction_total = requested_qty * float(item["Rate"])
#                 new_total = current_total - deduction_total

#                 # if new_level <= 0:
#                 #     # Optional: delete row if stock becomes zero
#                 #     # cursor.execute(""" 
#                 #     #     DELETE FROM stock_statement
#                 #     #     WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#                 #     # """, (item["ItemName"], item["UOM"], store_requisition["OutletName"]))
#                 #     new_level = 0
#                 #     deduction_total = 0
#                 #     new_total = 0
#                 cursor.execute("""
#                         UPDATE stock_statement
#                         SET CurrentLevel = %s,
#                             Total = %s
#                         WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#                     """, (
#                         new_level,
#                         new_total,
#                         item["ItemName"],
#                         item["UOM"],
#                         store_requisition["OutletName"]
#                     ))
#             else:
#                 # This should not happen ideally
#                 raise Exception(f"Stock statement missing for {item['ItemName']}")

#             # Insert into intblstorereqdetails (original code - unchanged)
#             insert_storerequisitiondetailsSql = """ Insert into intblstorereqdetails (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) values (%s,%s,%s,%s,%s,%s,%s,%s)"""

#             cursor.execute(insert_storerequisitiondetailsSql, (item["ItemName"], item["GroupName"], item["BrandName"], item["Amount"], item["UOM"], item["Rate"], store_req_id,item_type))

#             # Insert into item_current_level (original code - unchanged except using negative quantity)
#             cursor.execute("""
#                 INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (
#                 item['ItemName'],
#                 float(item['Amount']),  # Keep as positive as in your original
#                 float(item['Rate']),
#                 store_requisition["OutletName"],
#                 costcenter                
#             ))

#         # Commit the transaction to save changes
#         mydb.commit()

#         # Return a success response
#         return jsonify({"status": "success", "message": "Stock transfer request added successfully!"})
    
#     except Exception as e:
#         mydb.rollback()
#         data = {"error": str(e)}
#         return data, 400
    
#     finally:
#         mydb.close()


# @app_file57.route('/getStorereqsByPurchaseId', methods=["POST"])
# @cross_origin()
# def getStorereqsByPurchaseId():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Select DB
#         cursor.execute(f"USE {os.getenv('database')}")

#         # Get request data
#         data = request.get_json()

#         purchase_id = data.get('purchase_id')
#         outlet_name = data.get('outlet_name')

#         # ✅ Validation
#         if not purchase_id:
#             return jsonify({"error": "purchase_id is required"}), 400

#         if not outlet_name:
#             return jsonify({"error": "outlet_name is required"}), 400

#         # Convert purchase_id to int (safer)
#         try:
#             purchase_id = int(purchase_id)
#         except:
#             return jsonify({"error": "purchase_id must be an integer"}), 400

#         # ✅ Main Query (NO DATE_FORMAT here)
#         sql = """
#         SELECT 
#             idintblStoreRequisition,
#             OutletREQID,
#             Date,
#             CostCenter,
#             Outlet,
#             purchase_from,
#             purchase_id
#         FROM intblstorerequisition 
#         WHERE purchase_id = %s AND Outlet = %s
#         ORDER BY Date DESC
#         """

#         cursor.execute(sql, (purchase_id, outlet_name))
#         store_requisitions = cursor.fetchall()

#         # ✅ Add formatted date + fetch items
#         for requisition in store_requisitions:
#             # Format date safely
#             if requisition.get("Date"):
#                 requisition["formatted_date"] = requisition["Date"].strftime('%Y-%m-%d %H:%M:%S')
#             else:
#                 requisition["formatted_date"] = None

#             # Fetch item details
#             items_sql = """
#             SELECT 
#                 ItemName,
#                 GroupName,
#                 BrandName,
#                 Amount,
#                 UOM,
#                 Rate,
#                 itemtype
#             FROM intblstorereqdetails 
#             WHERE StoreReqID = %s
#             """

#             cursor.execute(items_sql, (requisition['idintblStoreRequisition'],))
#             requisition['items'] = cursor.fetchall()

#         mydb.close()

#         return jsonify({
#             "success": True,
#             "purchase_id": purchase_id,
#             "outlet_name": outlet_name,
#             "count": len(store_requisitions),
#             "data": store_requisitions
#         }), 200

#     except Exception as e:
#         print("Error details:", str(e))
#         return jsonify({"error": str(e)}), 400
    

# @app_file57.route('/getDistinctCostCenters', methods=["POST"])
# @cross_origin()
# def get_distinct_cost_centers():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Select DB
#         cursor.execute(f"USE {os.getenv('database')}")

#         # Get request data
#         data = request.get_json()
#         outlet_name = data.get('outlet_name')

#         # Validation
#         if not outlet_name:
#             return jsonify({"error": "outlet_name is required"}), 400

#         # Query to get distinct cost centers
#         sql = """
#         SELECT DISTINCT CostCenter
#         FROM intblstorerequisition 
#         WHERE Outlet = %s AND CostCenter IS NOT NULL AND CostCenter != ''
#         ORDER BY CostCenter ASC
#         """

#         cursor.execute(sql, (outlet_name,))
#         cost_centers = cursor.fetchall()

#         mydb.close()

#         # Extract just the cost center names into a list
#         cost_center_list = [center['CostCenter'] for center in cost_centers]

#         return jsonify({
#             "success": True,
#             "outlet_name": outlet_name,
#             "count": len(cost_center_list),
#             "cost_centers": cost_center_list
#         }), 200

#     except Exception as e:
#         print("Error details:", str(e))
#         return jsonify({"error": str(e)}), 400
    
# from .production.utils import adjust_production_item_after_sale

# @app_file57.route('/poststockTransfer_web', methods = ["POST"])
# @cross_origin()
# def postStock_web():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'), 
#             password=os.getenv('password'), 
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(buffered=True, dictionary=True)

#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         json_data = request.get_json()

#         store_itemdetails = json_data.pop("ItemDetailsList", None)
#         store_requisition = json_data

#         # Convert the date to MySQL compatible format
#         try:
#             date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
#             formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#         except Exception as e:
#             return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400
        
#         purchase_from = store_requisition.get("purchase_from", "c_app")
#         purchase_id = store_requisition.get("purchase_id", None)

#         # Generate OutletREQID based on purchase_from
#         if purchase_from == "web":
#             cursor.execute("""
#                 SELECT MAX(CAST(OutletREQID AS UNSIGNED)) as max_id
#                 FROM intblstorerequisition
#                 WHERE Outlet = %s and purchase_from = 'web'
#             """, (store_requisition["OutletName"],))
            
#             result = cursor.fetchone()
#             max_id = result['max_id'] if result else None
            
#             if max_id is None:
#                 outlet_req_id = 1
#             else:
#                 outlet_req_id = int(max_id) + 1
#         else:
#             outlet_req_id = store_requisition["Outlet_Req_ID"]

#         # VALIDATION: Get current stock levels for all items
#         stock_info = []
#         stock_validation_errors = []
        
#         for item in store_itemdetails:
#             requested_qty = float(item["Amount"])
#             item_name = item["ItemName"]
#             uom = item["UOM"]
#             outlet_name = store_requisition["OutletName"]
            
#             cursor.execute("""
#                 SELECT CurrentLevel, Total, Rate 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item_name, uom, outlet_name))
            
#             existing = cursor.fetchone()
            
#             if not existing:
#                 stock_validation_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "requested": requested_qty,
#                     "available": 0,
#                     "error": "Item not found in stock statement"
#                 })
#             else:
#                 current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
#                 current_total = float(existing['Total']) if existing['Total'] else 0
#                 unit_price = float(existing['Rate']) if existing.get('Rate') else item.get("Rate", 0)
                
#                 stock_info.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "requested": requested_qty,
#                     "available": current_level,
#                     "unit_price": unit_price,
#                     "current_total": current_total,
#                     "will_remain": current_level - requested_qty,
#                     "will_total": current_total - (requested_qty * unit_price)
#                 })
                
#                 if requested_qty > current_level:
#                     stock_validation_errors.append({
#                         "item": item_name,
#                         "uom": uom,
#                         "requested": requested_qty,
#                         "available": current_level,
#                         "shortage": requested_qty - current_level,
#                         "error": f"Insufficient stock. Shortage: {requested_qty - current_level} units"
#                     })
        
#         # If any validation errors, return them without proceeding
#         if stock_validation_errors:
#             mydb.rollback()
#             return jsonify({
#                 "status": "error",
#                 "message": "Stock validation failed. Some items have insufficient stock.",
#                 "stock_summary": stock_info,
#                 "errors": stock_validation_errors
#             }), 400

#         # Proceed with insertion
#         insert_storerequisitionSql = """ INSERT INTO intblstorerequisition 
#             (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) 
#             VALUES (%s, %s, %s, %s, %s, %s)"""

#         cursor.execute(insert_storerequisitionSql, (
#             formatted_date,
#             store_requisition["CostCenter"], 
#             store_requisition["OutletName"],
#             outlet_req_id, 
#             purchase_from, 
#             purchase_id
#         ))

#         store_req_id = cursor.lastrowid

#         costcenter = store_requisition["CostCenter"]

#         if costcenter == "Kitchen":
#             item_type = "Food"
#         elif costcenter == "Bar":
#             item_type = "Beverage"
#         else:
#             item_type = costcenter

#         # Process each item
#         for item, stock in zip(store_itemdetails, stock_info):
#             requested_qty = float(item["Amount"])
#             requested_rate = float(item["Rate"])
#             item_name = item["ItemName"]
#             uom = item["UOM"]
#             outlet_name = store_requisition["OutletName"]

#             # Update stock_statement
#             cursor.execute("""
#                 UPDATE stock_statement
#                 SET CurrentLevel = %s,
#                     Total = %s
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (
#                 stock['will_remain'],
#                 stock['will_total'],
#                 item_name,
#                 uom,
#                 outlet_name
#             ))

#             # Insert into intblstorereqdetails
#             cursor.execute("""
#                 INSERT INTO intblstorereqdetails 
#                 (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) 
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """, (
#                 item["ItemName"], 
#                 item["GroupName"], 
#                 item["BrandName"], 
#                 item["Amount"], 
#                 item["UOM"], 
#                 item["Rate"], 
#                 store_req_id,
#                 item_type
#             ))

#             # # Insert into item_current_level
#             # cursor.execute("""
#             #     INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
#             #     VALUES (%s, %s, %s, %s, %s)
#             # """, (
#             #     item['ItemName'],
#             #     float(item['Amount']),
#             #     float(item['Rate']),
#             #     outlet_name,
#             #     costcenter                
#             # ))


#             if costcenter == "Central Kitchen":
#                 # Insert into item_current_level
#                 cursor.execute("""
#                     INSERT INTO production_item_current_level (itemname, quantity, rate, outlet, costcenter)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """, (
#                     item['ItemName'],
#                     float(item['Amount']),
#                     float(item['Rate']),
#                     outlet_name,
#                     costcenter                
#                 ))
#             else:
#                 # Insert into item_current_level
#                 cursor.execute("""
#                     INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """, (
#                     item['ItemName'],
#                     float(item['Amount']),
#                     float(item['Rate']),
#                     outlet_name,
#                     costcenter                
#                 ))

#                 if item['GroupName'] == "Finished Goods":

#                   # CALL YOUR FUNCTION HERE!
#                     adjust_production_item_after_sale(
#                         production_item_name=item_name,
#                         sold_qty=requested_qty,
#                         outlet=outlet_name,
#                         cursor=cursor,
#                         mydb=mydb,
#                         order_date=date_obj.date()  # Use the date from the requisition
#                     )

#         mydb.commit()

#         return jsonify({
#             "status": "success", 
#             "message": "Stock transfer request added successfully!",
#             "outlet_req_id": outlet_req_id,
#             "store_req_id": store_req_id,
#             "stock_summary": stock_info
#         }), 200
    
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return jsonify({"error": str(e)}), 400
    
#     finally:
#         if mydb and mydb.is_connected():
#             mydb.close()


# # from datetime import datetime, timedelta

# # @app_file57.route('/getStorereqs', methods=["POST"])
# # @cross_origin()
# # def getStorereqs():
# #     try:
# #         mydb = mysql.connector.connect(
# #             user=os.getenv('user'),
# #             password=os.getenv('password'),
# #             host=os.getenv('host')
# #         )
# #         cursor = mydb.cursor(dictionary=True, buffered=True)

# #         # Select DB
# #         cursor.execute(f"USE {os.getenv('database')}")

# #         # Get request data
# #         data = request.get_json()
# #         outlet_name = data.get('outlet_name')
# #         from_date = data.get('from_date')
# #         to_date = data.get('to_date')

# #         if not outlet_name:
# #             return jsonify({"error": "outlet_name is required"}), 400

# #         # ✅ Build dynamic query
# #         sql = """
# #         SELECT 
# #             idintblStoreRequisition,
# #             OutletREQID,
# #             Date,
# #             CostCenter,
# #             Outlet,
# #             purchase_from,
# #             purchase_id
# #         FROM intblstorerequisition 
# #         WHERE Outlet = %s and purchase_from = 'web' and Date between %s and %s
# #         """

# #         # params = [outlet_name]

# #         # # ✅ Apply date filter if provided
# #         # if from_date and to_date:
# #         #     start = datetime.strptime(from_date, "%Y-%m-%d")
# #         #     end = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)

# #         #     sql += " AND Date >= %s AND Date < %s"
# #         #     params.extend([start, end])

# #         # sql += " ORDER BY Date DESC"

# #         cursor.execute(sql, (outlet_name, from_date, to_date,))
# #         store_requisitions = cursor.fetchall()

# #         # ✅ Add formatted date + fetch items
# #         for requisition in store_requisitions:
# #             if requisition.get("Date"):
# #                 requisition["formatted_date"] = requisition["Date"].strftime('%Y-%m-%d %H:%M:%S')
# #             else:
# #                 requisition["formatted_date"] = None

# #             items_sql = """
# #             SELECT 
# #                 ItemName,
# #                 GroupName,
# #                 BrandName,
# #                 Amount,
# #                 UOM,
# #                 Rate,
# #                 itemtype
# #             FROM intblstorereqdetails 
# #             WHERE StoreReqID = %s
# #             """

# #             cursor.execute(items_sql, (requisition['idintblStoreRequisition'],))
# #             requisition['items'] = cursor.fetchall()

# #         mydb.close()

# #         return jsonify({
# #             "success": True,
# #             "outlet_name": outlet_name,
# #             "count": len(store_requisitions),
# #             "data": store_requisitions
# #         }), 200

# #     except Exception as e:
# #         print("Error details:", str(e))
# #         return jsonify({"error": str(e)}), 400


# from datetime import datetime, timedelta

# @app_file57.route('/getStorereqs', methods=["POST"])
# @cross_origin()
# def getStorereqs():
#     mydb = None
#     cursor = None
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Select DB - safer way
#         cursor.execute(f"USE `{os.getenv('database')}`")

#         # Get request data
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "Request body is required"}), 400
            
#         outlet_name = data.get('outlet_name')
#         from_date = data.get('from_date')
#         to_date = data.get('to_date')
#         page = data.get('page', 1)
#         limit = data.get('limit', 50)
#         cost_center = data.get('cost_center')  # Optional filter
#         store_req_id = data.get('storereqID')

#         if not outlet_name:
#             return jsonify({"error": "outlet_name is required"}), 400
    

#         # ✅ Validate date formats if provided
#         start_date = None
#         end_date = None
        
#         if from_date:
#             try:
#                 start_date = datetime.strptime(from_date, "%Y-%m-%d")
#             except ValueError:
#                 return jsonify({"error": "Invalid from_date format. Use YYYY-MM-DD"}), 400
                
#         if to_date:
#             try:
#                 # Add 1 day to include the end date fully
#                 end_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
#             except ValueError:
#                 return jsonify({"error": "Invalid to_date format. Use YYYY-MM-DD"}), 400

#         # ✅ Build dynamic query
#         sql = """
#         SELECT 
#             idintblStoreRequisition,
#             OutletREQID,
#             Date,
#             CostCenter,
#             Outlet,
#             purchase_from,
#             purchase_id
#         FROM intblstorerequisition 
#         WHERE Outlet = %s 
#         AND purchase_from = 'web'
#         """
        
#         params = [outlet_name]

#         # ✅ Apply date filter if both provided
#         if start_date and end_date:
#             sql += " AND Date >= %s AND Date < %s"
#             params.extend([start_date, end_date])
#         elif start_date:
#             sql += " AND Date >= %s"
#             params.append(start_date)
#         elif end_date:
#             sql += " AND Date < %s"
#             params.append(end_date)

#         # ✅ Optional cost center filter
#         if cost_center:
#             sql += " AND CostCenter = %s"
#             params.append(cost_center)

#         # ✅ Filter by requisition ID
#         if store_req_id:
#             sql += " AND idintblStoreRequisition = %s"
#             params.append(store_req_id)

#         # ✅ Add pagination
#         sql += " ORDER BY Date DESC LIMIT %s OFFSET %s"
#         offset = (page - 1) * limit
#         params.extend([limit, offset])
        
#         cursor.execute(sql, params)
#         store_requisitions = cursor.fetchall()

#         # ✅ Get total count for pagination
#         count_sql = """
#         SELECT COUNT(*) as total 
#         FROM intblstorerequisition 
#         WHERE Outlet = %s 
#         AND purchase_from = 'web'
#         """
#         count_params = [outlet_name]
        
#         if start_date and end_date:
#             count_sql += " AND Date >= %s AND Date < %s"
#             count_params.extend([start_date, end_date])
#         elif start_date:
#             count_sql += " AND Date >= %s"
#             count_params.append(start_date)
#         elif end_date:
#             count_sql += " AND Date < %s"
#             count_params.append(end_date)
            
#         if cost_center:
#             count_sql += " AND CostCenter = %s"
#             count_params.append(cost_center)
            
#         cursor.execute(count_sql, count_params)
#         total_count = cursor.fetchone()['total']

#         # ✅ Add formatted date + fetch items
#         for requisition in store_requisitions:
#             if requisition.get("Date"):
#                 requisition["formatted_date"] = requisition["Date"].strftime('%Y-%m-%d %H:%M:%S')
#             else:
#                 requisition["formatted_date"] = None

#             # Fetch items for this requisition
#             items_sql = """
#             SELECT 
#                 ItemName,
#                 GroupName,
#                 BrandName,
#                 Amount,
#                 UOM,
#                 Rate,
#                 itemtype
#             FROM intblstorereqdetails 
#             WHERE StoreReqID = %s
#             """
            
#             cursor.execute(items_sql, (requisition['idintblStoreRequisition'],))
#             requisition['items'] = cursor.fetchall()

#         return jsonify({
#             "success": True,
#             "outlet_name": outlet_name,
#             "count": len(store_requisitions),
#             "total_count": total_count,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_count + limit - 1) // limit,
#             "data": store_requisitions
#         }), 200

#     except mysql.connector.Error as db_error:
#         print("Database error:", str(db_error))
#         return jsonify({"error": f"Database error: {str(db_error)}"}), 500
#     except Exception as e:
#         print("Error details:", str(e))
#         return jsonify({"error": str(e)}), 400
#     finally:
#         if cursor:
#             cursor.close()
#         if mydb and mydb.is_connected():
#             mydb.close()
    

# # @app_file57.route('/deletestockTransfer_web', methods = ["DELETE"])
# # @cross_origin()
# # def deleteStockTransfer_web():
# #     try:
# #         mydb = mysql.connector.connect(
# #             user=os.getenv('user'), 
# #             password=os.getenv('password'), 
# #             host=os.getenv('host')
# #         )
# #         cursor = mydb.cursor(buffered=True, dictionary=True)

# #         database_sql = "USE {};".format(os.getenv('database'))
# #         cursor.execute(database_sql)

# #         # Get the store_req_id from request
# #         json_data = request.get_json()
# #         store_req_id = json_data.get("store_req_id")
        
# #         if not store_req_id:
# #             return jsonify({"error": "store_req_id is required"}), 400

# #         # First, get the requisition details to know which items to restore/remove
# #         cursor.execute("""
# #             SELECT sr.Outlet, sr.CostCenter, srd.ItemName, srd.UOM, srd.Amount, srd.Rate
# #             FROM intblstorerequisition sr
# #             JOIN intblstorereqdetails srd ON sr.idintblStoreRequisition = srd.StoreReqID
# #             WHERE sr.idintblStoreRequisition = %s
# #         """, (store_req_id,))
        
# #         requisition_items = cursor.fetchall()
        
# #         if not requisition_items:
# #             return jsonify({"error": "Store requisition not found"}), 404

# #         # Restore stock to stock_statement and remove from item_current_level
# #         restoration_details = []
# #         restoration_errors = []
        
# #         for item in requisition_items:
# #             item_name = item['ItemName']
# #             uom = item['UOM']
# #             outlet_name = item['Outlet']
# #             costcenter = item['CostCenter']
# #             amount_to_restore = float(item['Amount'])
# #             rate = float(item['Rate'])
            
# #             # 1. RESTORE stock_statement (add back the quantity)
# #             cursor.execute("""
# #                 SELECT CurrentLevel, Total, Rate 
# #                 FROM stock_statement 
# #                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
# #             """, (item_name, uom, outlet_name))
            
# #             existing = cursor.fetchone()
            
# #             if not existing:
# #                 restoration_errors.append({
# #                     "item": item_name,
# #                     "uom": uom,
# #                     "error": "Item not found in stock_statement"
# #                 })
# #                 continue
            
# #             current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
# #             current_total = float(existing['Total']) if existing['Total'] else 0
# #             unit_price = float(existing['Rate']) if existing.get('Rate') else rate
            
# #             # Calculate restored values (adding back)
# #             restored_level = current_level + amount_to_restore
# #             restored_total = restored_level * unit_price
            
# #             # Update stock_statement with restored levels
# #             cursor.execute("""
# #                 UPDATE stock_statement
# #                 SET CurrentLevel = %s,
# #                     Total = %s
# #                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
# #             """, (
# #                 restored_level,
# #                 restored_total,
# #                 item_name,
# #                 uom,
# #                 outlet_name
# #             ))
            
# #             # 2. REMOVE from item_current_level (subtract the quantity)
# #             # First, get the current item_current_level entry for this item
# #             cursor.execute("""
# #                 SELECT id, quantity, rate 
# #                 FROM item_current_level 
# #                 WHERE itemname = %s 
# #                 AND outlet = %s 
# #                 AND costcenter = %s
# #                 ORDER BY id DESC 
# #                 LIMIT 1
# #             """, (item_name, outlet_name, costcenter))
            
# #             current_item = cursor.fetchone()
            
# #             if not current_item:
# #                 restoration_errors.append({
# #                     "item": item_name,
# #                     "uom": uom,
# #                     "error": "Item not found in item_current_level"
# #                 })
# #                 continue
            
# #             current_item_qty = float(current_item['quantity'])
            
# #             if current_item_qty < amount_to_restore:
# #                 restoration_errors.append({
# #                     "item": item_name,
# #                     "uom": uom,
# #                     "error": f"Insufficient quantity in item_current_level to remove. Available: {current_item_qty}, Requested to remove: {amount_to_restore}"
# #                 })
# #                 continue
            
# #             new_item_qty = current_item_qty - amount_to_restore
            
# #             restoration_details.append({
# #                 "item": item_name,
# #                 "uom": uom,
# #                 "amount_restored_to_stock": amount_to_restore,
# #                 "stock_statement": {
# #                     "previous_level": current_level,
# #                     "new_level": restored_level,
# #                     "previous_total": current_total,
# #                     "new_total": restored_total
# #                 },
# #                 "item_current_level": {
# #                     "previous_quantity": current_item_qty,
# #                     "new_quantity": new_item_qty,
# #                     "rate": float(current_item['rate'])
# #                 }
# #             })
            
# #             # Update or delete from item_current_level based on new quantity
# #             if new_item_qty <= 0:
# #                 # If quantity becomes zero or negative, delete the record
# #                 cursor.execute("""
# #                     DELETE FROM item_current_level 
# #                     WHERE id = %s
# #                 """, (current_item['id'],))
# #                 restoration_details[-1]["item_current_level"]["action"] = "Deleted (quantity became 0)"
# #             else:
# #                 # Otherwise, update with new quantity
# #                 cursor.execute("""
# #                     UPDATE item_current_level 
# #                     SET quantity = %s
# #                     WHERE id = %s
# #                 """, (new_item_qty, current_item['id']))
# #                 restoration_details[-1]["item_current_level"]["action"] = "Updated"
        
# #         # If there were errors, rollback and don't delete
# #         if restoration_errors:
# #             mydb.rollback()
# #             return jsonify({
# #                 "status": "error",
# #                 "message": "Failed to restore stock/remove from current level. Deletion cancelled.",
# #                 "errors": restoration_errors,
# #                 "restoration_details": restoration_details
# #             }), 400
        
# #         # Delete from intblstorereqdetails first (due to foreign key constraint)
# #         cursor.execute("""
# #             DELETE FROM intblstorereqdetails 
# #             WHERE StoreReqID = %s
# #         """, (store_req_id,))
        
# #         # Finally delete the main requisition record
# #         cursor.execute("""
# #             DELETE FROM intblstorerequisition 
# #             WHERE idintblStoreRequisition = %s
# #         """, (store_req_id,))
        
# #         mydb.commit()
        
# #         return jsonify({
# #             "status": "success",
# #             "message": f"Store requisition {store_req_id} deleted successfully. Stock restored and current level updated.",
# #             "restoration_details": restoration_details
# #         }), 200
    
# #     except Exception as e:
# #         if mydb:
# #             mydb.rollback()
# #         return jsonify({"error": str(e)}), 400
    
# #     finally:
# #         if mydb and mydb.is_connected():
# #             mydb.close()


# @app_file57.route('/deletestockTransfer_web', methods = ["DELETE"])
# @cross_origin()
# def deleteStockTransfer_web():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'), 
#             password=os.getenv('password'), 
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(buffered=True, dictionary=True)

#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         # Get the store_req_id from request
#         json_data = request.get_json()
#         store_req_id = json_data.get("store_req_id")
        
#         if not store_req_id:
#             return jsonify({"error": "store_req_id is required"}), 400

#         # First, get the requisition details to know which items to restore/remove
#         cursor.execute("""
#             SELECT sr.Outlet, sr.CostCenter, srd.ItemName, srd.UOM, srd.Amount, srd.Rate
#             FROM intblstorerequisition sr
#             JOIN intblstorereqdetails srd ON sr.idintblStoreRequisition = srd.StoreReqID
#             WHERE sr.idintblStoreRequisition = %s
#         """, (store_req_id,))
        
#         requisition_items = cursor.fetchall()
        
#         if not requisition_items:
#             return jsonify({"error": "Store requisition not found"}), 404

#         # Restore stock to stock_statement and remove from item_current_level
#         restoration_details = []
#         restoration_errors = []
        
#         for item in requisition_items:
#             item_name = item['ItemName']
#             uom = item['UOM']
#             outlet_name = item['Outlet']
#             costcenter = item['CostCenter']
#             amount_to_restore = float(item['Amount'])
#             rate = float(item['Rate'])
            
#             # 1. RESTORE stock_statement (add back the quantity)
#             cursor.execute("""
#                 SELECT CurrentLevel, Total, Rate 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item_name, uom, outlet_name))
            
#             existing = cursor.fetchone()
            
#             if not existing:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": "Item not found in stock_statement"
#                 })
#                 continue
            
#             current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
#             current_total = float(existing['Total']) if existing['Total'] else 0
#             unit_price = float(existing['Rate']) if existing.get('Rate') else rate
            
#             # Calculate restored values (adding back)
#             restored_level = current_level + amount_to_restore
#             restored_total = restored_level * unit_price
            
#             # Update stock_statement with restored levels
#             cursor.execute("""
#                 UPDATE stock_statement
#                 SET CurrentLevel = %s,
#                     Total = %s
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (
#                 restored_level,
#                 restored_total,
#                 item_name,
#                 uom,
#                 outlet_name
#             ))
            
#             # 2. REMOVE from item_current_level (subtract the quantity from multiple records using FIFO/LIFO)
#             # First, get ALL current item_current_level entries for this item
#             cursor.execute("""
#                 SELECT id, quantity, rate
#                 FROM item_current_level 
#                 WHERE itemname = %s 
#                 AND outlet = %s 
#                 AND costcenter = %s
#                 AND quantity > 0
#                 ORDER BY id ASC  -- Change to DESC for LIFO (Last In First Out)
#             """, (item_name, outlet_name, costcenter))
            
#             current_items = cursor.fetchall()
            
#             if not current_items:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": "Item not found in item_current_level"
#                 })
#                 continue
            
#             # Calculate total available quantity
#             total_available_qty = sum(float(item['quantity']) for item in current_items)
            
#             if total_available_qty < amount_to_restore:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": f"Insufficient quantity in item_current_level to remove. Available: {total_available_qty}, Requested to remove: {amount_to_restore}"
#                 })
#                 continue
            
#             # Track removal from multiple records
#             remaining_to_remove = amount_to_restore
#             removal_details = []
            
#             for current_item in current_items:
#                 if remaining_to_remove <= 0:
#                     break
                    
#                 current_item_id = current_item['id']
#                 current_item_qty = float(current_item['quantity'])
#                 current_item_rate = float(current_item['rate'])
                
#                 # Determine how much to remove from this record
#                 remove_qty = min(remaining_to_remove, current_item_qty)
#                 new_item_qty = current_item_qty - remove_qty
#                 remaining_to_remove -= remove_qty
                
#                 item_removal_detail = {
#                     "record_id": current_item_id,
#                     "original_quantity": current_item_qty,
#                     "original_rate": current_item_rate,
#                     "quantity_removed": remove_qty,
#                     "new_quantity": new_item_qty
#                 }
                
#                 # Update or delete from item_current_level based on new quantity
#                 if new_item_qty <= 0:
#                     # If quantity becomes zero, delete the record
#                     cursor.execute("""
#                         DELETE FROM item_current_level 
#                         WHERE id = %s
#                     """, (current_item_id,))
#                     item_removal_detail["action"] = "Deleted (quantity became 0)"
#                 else:
#                     # Otherwise, update with new quantity
#                     cursor.execute("""
#                         UPDATE item_current_level 
#                         SET quantity = %s
#                         WHERE id = %s
#                     """, (new_item_qty, current_item_id))
#                     item_removal_detail["action"] = "Updated"
                
#                 removal_details.append(item_removal_detail)
            
#             # Verify we removed everything
#             if remaining_to_remove > 0:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": f"Failed to remove all quantity. {remaining_to_remove} remaining after processing all records"
#                 })
#                 continue
            
#             restoration_details.append({
#                 "item": item_name,
#                 "uom": uom,
#                 "amount_restored_to_stock": amount_to_restore,
#                 "stock_statement": {
#                     "previous_level": current_level,
#                     "new_level": restored_level,
#                     "previous_total": current_total,
#                     "new_total": restored_total
#                 },
#                 "item_current_level_removals": removal_details
#             })
        
#         # If there were errors, rollback and don't delete
#         if restoration_errors:
#             mydb.rollback()
#             return jsonify({
#                 "status": "error",
#                 "message": "Failed to restore stock/remove from current level. Deletion cancelled.",
#                 "errors": restoration_errors,
#                 "restoration_details": restoration_details
#             }), 400
        
#         # Delete from intblstorereqdetails first (due to foreign key constraint)
#         cursor.execute("""
#             DELETE FROM intblstorereqdetails 
#             WHERE StoreReqID = %s
#         """, (store_req_id,))
        
#         # Finally delete the main requisition record
#         cursor.execute("""
#             DELETE FROM intblstorerequisition 
#             WHERE idintblStoreRequisition = %s
#         """, (store_req_id,))
        
#         mydb.commit()
        
#         return jsonify({
#             "status": "success",
#             "message": f"Store requisition {store_req_id} deleted successfully. Stock restored and current level updated.",
#             "restoration_details": restoration_details
#         }), 200
    
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return jsonify({"error": str(e)}), 400
    
#     finally:
#         if mydb and mydb.is_connected():
#             mydb.close()


# from flask import Flask, Blueprint, request, jsonify
# import mysql.connector
# from flask_cors import cross_origin

# import os

# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()


# app_file57 = Blueprint('appfile_57', __name__)


# @app_file57.route('/poststockTransfer', methods = ["POST"])

# @cross_origin()
# def postStock():
#     try:
#         mydb = mysql.connector.connect(user=os.getenv('user'), password = os.getenv('password'), host= os.getenv('host'))

#         cursor = mydb.cursor(buffered=True)

#         database_sql = "USE {};".format(os.getenv('database'))

#         cursor.execute(database_sql)

#         json = request.get_json()

#         store_itemdetails = json.pop("ItemDetailsList", None)

#         store_requisition = json

#         # Convert the date to MySQL compatible format
#         try:
#             date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
#             formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#         except Exception as e:
#             return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400

#         insert_storerequisitionSql = """ Insert into intblstorerequisition (`Date`, `CostCenter`, `Outlet`, `OutletREQID`) values (%s,%s,%s,%s)"""

#         cursor.execute(insert_storerequisitionSql, (formatted_date,store_requisition["CostCenter"], store_requisition["OutletName"],store_requisition["Outlet_Req_ID"],))

#         # Get the id of the last inserted record in intblstorerequisition
#         store_req_id = cursor.lastrowid

#         costcenter = formatted_date,store_requisition["CostCenter"]

#         item_type = "Food"
#         if costcenter == "Kitchen":
#             item_type = "Food"

#         else:
#             item_type = "Beverage"

#         for item in store_itemdetails:

#             insert_storerequisitiondetailsSql = """ Insert into intblstorereqdetails (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) values (%s,%s,%s,%s,%s,%s,%s,%s)"""


#             cursor.execute(insert_storerequisitiondetailsSql, (item["ItemName"], item["GroupName"], item["BrandName"], item["Amount"], item["UOM"], item["Rate"], store_req_id,item_type))


#             # Always insert new entry into item_current_level (sequential entry)
#             cursor.execute("""
#                 INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
#                 VALUES (%s, %s, %s, %s)
#             """, (
#                 item['item_name'],
#                 float(item['quantity']),
#                 float(item['price']),
#                 store_requisition["OutletName"],
#                 costcenter                
#             ))

#         # Commit the transaction to save changes
#         mydb.commit()

#         # Return a success response
#         return jsonify({"status": "success", "message": "Stock transfer request added successfully!"})
    
#     except Exception as e:

#         data = {"error": str(e)}
#         return data, 400
    
#     finally:
#         mydb.close()


from flask import Flask, Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin

import os

from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


app_file57 = Blueprint('appfile_57', __name__)


# @app_file57.route('/poststockTransfer', methods = ["POST"])

# @cross_origin()
# def postStock():
#     try:
#         mydb = mysql.connector.connect(user=os.getenv('user'), password = os.getenv('password'), host= os.getenv('host'))

#         cursor = mydb.cursor(buffered=True)

#         database_sql = "USE {};".format(os.getenv('database'))

#         cursor.execute(database_sql)

#         json = request.get_json()

#         store_itemdetails = json.pop("ItemDetailsList", None)

#         store_requisition = json

#         # Convert the date to MySQL compatible format
#         try:
#             date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
#             formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#         except Exception as e:
#             return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400
        
#         purchase_from = store_requisition.get("purchase_from", "c_app")

#         purchase_id = store_requisition.get("purchase_id", None)


#         # Generate OutletREQID based on purchase_from
#         if purchase_from == "web":
#             cursor.execute("""
#                 SELECT MAX(CAST(OutletREQID AS UNSIGNED)) 
#                 FROM intblstorerequisition
#                 WHERE Outlet = %s and purchase_from = 'web'
#             """, (store_requisition["OutletName"],))
            
#             max_id = cursor.fetchone()[0]
            
#             if max_id is None:
#                 outlet_req_id = 1
#             else:
#                 outlet_req_id = int(max_id) + 1
#         else:
#             outlet_req_id = store_requisition["Outlet_Req_ID"]

#         insert_storerequisitionSql = """ Insert into intblstorerequisition (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) values (%s,%s,%s,%s,%s,%s)"""

#         cursor.execute(insert_storerequisitionSql, (formatted_date,store_requisition["CostCenter"], store_requisition["OutletName"],outlet_req_id, purchase_from, purchase_id))

#         # Get the id of the last inserted record in intblstorerequisition
#         store_req_id = cursor.lastrowid

#         costcenter = store_requisition["CostCenter"]

#         item_type = "Food"
#         if costcenter == "Kitchen":
#             item_type = "Food"

#         elif costcenter == "Bar":
#             item_type = "Beverage"

#         else:
#             item_type = costcenter

#         for item in store_itemdetails:
#             # DEDUCT FROM stock_current_level TABLE USING FIFO (EARLIEST EXPIRY FIRST)
#             item_name = item["ItemName"]
#             requested_qty = float(item["Amount"])
            
#             # Check if sufficient stock is available
#             # cursor.execute("""
#             #         SELECT SUM(qty) as total_available 
#             #         FROM stock_current_level 
#             #         WHERE name = %s 
#             #         AND qty > 0
#             #         AND (expiry_date IS NULL OR expiry_date > CURDATE())
#             #     """, (item_name,))
                
#             # result = cursor.fetchone()
#             # total_available = result[0] if result[0] else 0
                
#             # if total_available < requested_qty:
#             #     raise Exception(f"Insufficient stock for {item_name}. Available: {total_available}, Requested: {requested_qty}")
                
#             # # Get stock batches ordered by expiry date (earliest first)
#             # cursor.execute("""
#             #         SELECT id, qty, total, rate, expiry_date
#             #         FROM stock_current_level 
#             #         WHERE name = %s 
#             #         AND qty > 0
#             #         AND (expiry_date IS NULL OR expiry_date > CURDATE())
#             #         ORDER BY expiry_date ASC, id ASC
#             #     """, (item_name,))
                
#             # stock_batches = cursor.fetchall()
#             # remaining_to_deduct = requested_qty
                
#             # # Deduct from batches
#             # for batch in stock_batches:
#             #     if remaining_to_deduct <= 0:
#             #         break
                        
#             #     batch_id = batch[0]
#             #     current_qty = float(batch[1])
#             #     current_total = float(batch[2])
#             #     current_rate = float(batch[3])
                    
#             #     if current_qty <= remaining_to_deduct:
#             #         # Remove entire batch
#             #         new_qty = 0
#             #         new_total = 0
#             #         remaining_to_deduct -= current_qty
#             #     else:
#             #         # Partially deduct from this batch
#             #         new_qty = current_qty - remaining_to_deduct
#             #         new_total = new_qty * current_rate
#             #         remaining_to_deduct = 0
                    
#             #     # Update the stock_current_level
#             #     cursor.execute("""
#             #         UPDATE stock_current_level 
#             #         SET qty = %s, total = %s 
#             #         WHERE id = %s
#             #     """, (new_qty, new_total, batch_id))


#             # SUBTRACT FROM stock_statement (aggregated stock)
#             cursor.execute("""
#                 SELECT CurrentLevel, Total 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item["ItemName"], item["UOM"], store_requisition["OutletName"]))

#             existing = cursor.fetchone()

#             if existing:
#                 current_level = float(existing[0])
#                 current_total = float(existing[1]) if existing[1] else 0

#                 new_level = current_level - requested_qty
#                 deduction_total = requested_qty * float(item["Rate"])
#                 new_total = current_total - deduction_total

#                 # if new_level <= 0:
#                 #     # Optional: delete row if stock becomes zero
#                 #     # cursor.execute(""" 
#                 #     #     DELETE FROM stock_statement
#                 #     #     WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#                 #     # """, (item["ItemName"], item["UOM"], store_requisition["OutletName"]))
#                 #     new_level = 0
#                 #     deduction_total = 0
#                 #     new_total = 0
#                 cursor.execute("""
#                         UPDATE stock_statement
#                         SET CurrentLevel = %s,
#                             Total = %s
#                         WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#                     """, (
#                         new_level,
#                         new_total,
#                         item["ItemName"],
#                         item["UOM"],
#                         store_requisition["OutletName"]
#                     ))
#             else:
#                 # This should not happen ideally
#                 raise Exception(f"Stock statement missing for {item['ItemName']}")

#             # Insert into intblstorereqdetails (original code - unchanged)
#             insert_storerequisitiondetailsSql = """ Insert into intblstorereqdetails (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) values (%s,%s,%s,%s,%s,%s,%s,%s)"""

#             cursor.execute(insert_storerequisitiondetailsSql, (item["ItemName"], item["GroupName"], item["BrandName"], item["Amount"], item["UOM"], item["Rate"], store_req_id,item_type))

#             # Insert into item_current_level (original code - unchanged except using negative quantity)
#             cursor.execute("""
#                 INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (
#                 item['ItemName'],
#                 float(item['Amount']),  # Keep as positive as in your original
#                 float(item['Rate']),
#                 store_requisition["OutletName"],
#                 costcenter                
#             ))

#         # Commit the transaction to save changes
#         mydb.commit()

#         # Return a success response
#         return jsonify({"status": "success", "message": "Stock transfer request added successfully!"})
    
#     except Exception as e:
#         mydb.rollback()
#         data = {"error": str(e)}
#         return data, 400
    
#     finally:
#         mydb.close()

@app_file57.route('/poststockTransfer', methods=["POST"])
@cross_origin()
def postStock():
    try:
        mydb = mysql.connector.connect(
            user=os.getenv('user'),
            password=os.getenv('password'),
            host=os.getenv('host')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute("USE {};".format(os.getenv('database')))

        json_data = request.get_json()
        store_itemdetails = json_data.pop("ItemDetailsList", None)
        store_requisition = json_data

        try:
            date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400

        purchase_from = store_requisition.get("purchase_from", "c_app")
        purchase_id   = store_requisition.get("purchase_id", None)
        outlet_name   = store_requisition["OutletName"]

        # Generate OutletREQID
        if purchase_from == "web":
            cursor.execute("""
                SELECT MAX(CAST(OutletREQID AS UNSIGNED)) 
                FROM intblstorerequisition
                WHERE Outlet = %s AND purchase_from = 'web'
            """, (outlet_name,))
            max_id = cursor.fetchone()[0]
            outlet_req_id = (int(max_id) + 1) if max_id else 1
        else:
            outlet_req_id = store_requisition["Outlet_Req_ID"]

        # ==================== VALIDATION ====================
        validation_errors = []

        for item in store_itemdetails:
            item_name     = item["ItemName"]
            uom           = item["UOM"]
            requested_qty = float(item["Amount"])

            # Check stock_statement
            cursor.execute("""
                SELECT CurrentLevel 
                FROM stock_statement 
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
            """, (item_name, uom, outlet_name))
            existing = cursor.fetchone()

            if not existing:
                validation_errors.append(f"Stock statement missing for {item_name} ({uom})")
            elif float(existing[0]) < requested_qty - 0.001:
                validation_errors.append(
                    f"Insufficient stock in stock_statement for {item_name}. "
                    f"Available: {float(existing[0]):.2f}, Requested: {requested_qty:.2f}"
                )

            # # Check stock_current_level
            # cursor.execute("""
            #     SELECT SUM(qty)
            #     FROM stock_current_level
            #     WHERE name = %s AND qty > 0
            #     AND (expiry_date IS NULL OR expiry_date > CURDATE())
            # """, (item_name,))
            # scl_result    = cursor.fetchone()
            # scl_available = float(scl_result[0]) if scl_result[0] else 0

            # if scl_available < requested_qty - 0.001:
            #     validation_errors.append(
            #         f"Insufficient stock in stock_current_level for {item_name}. "
            #         f"Available: {scl_available:.2f}, Requested: {requested_qty:.2f}"
            #     )

            # Check stock_statement_lots
            cursor.execute("""
                SELECT SUM(qty)
                FROM stock_statement_lots
                WHERE item_name = %s AND outlet_name = %s AND qty > 0
            """, (item_name, outlet_name))
            lots_result   = cursor.fetchone()
            lots_available = float(lots_result[0]) if lots_result[0] else 0

            if lots_available < requested_qty - 0.001:
                validation_errors.append(
                    f"Insufficient lots in stock_statement_lots for {item_name}. "
                    f"Available: {lots_available:.2f}, Requested: {requested_qty:.2f}"
                )

        if validation_errors:
            return jsonify({
                "status": "error",
                "message": "Stock validation failed.",
                "errors": validation_errors
            }), 400

        # ==================== INSERT REQUISITION HEADER ====================
        cursor.execute("""
            INSERT INTO intblstorerequisition 
            (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (formatted_date, store_requisition["CostCenter"], outlet_name, outlet_req_id, purchase_from, purchase_id))

        store_req_id = cursor.lastrowid
        costcenter   = store_requisition["CostCenter"]

        if costcenter == "Kitchen":
            item_type = "Food"
        elif costcenter == "Bar":
            item_type = "Beverage"
        else:
            item_type = costcenter

        # ==================== PROCESS EACH ITEM ====================
        for item in store_itemdetails:
            item_name     = item["ItemName"]
            uom           = item["UOM"]
            requested_qty = float(item["Amount"])

            # # ── 1. FIFO deduction from stock_current_level ────────────────────
            # cursor.execute("""
            #     SELECT id, qty, rate, total
            #     FROM stock_current_level
            #     WHERE name = %s AND qty > 0
            #     AND (expiry_date IS NULL OR expiry_date > CURDATE())
            #     ORDER BY expiry_date ASC, id ASC
            # """, (item_name,))
            # scl_batches   = cursor.fetchall()
            # remaining_scl = requested_qty

            # for batch in scl_batches:
            #     if remaining_scl <= 0.001:
            #         break

            #     batch_id   = batch[0]
            #     batch_qty  = float(batch[1])
            #     batch_rate = float(batch[2])

            #     if batch_qty <= remaining_scl + 0.001:
            #         new_qty   = 0
            #         new_total = 0
            #         remaining_scl -= batch_qty
            #     else:
            #         new_qty   = batch_qty - remaining_scl
            #         new_total = round(new_qty * batch_rate, 4)
            #         remaining_scl = 0

            #     cursor.execute("""
            #         UPDATE stock_current_level
            #         SET qty = %s, total = %s
            #         WHERE id = %s AND qty >= %s
            #     """, (new_qty, new_total, batch_id, batch_qty))

            #     if cursor.rowcount == 0:
            #         raise Exception(f"Concurrent update detected for stock_current_level batch {batch_id}")

            # ── 2. FIFO deduction from stock_statement_lots ───────────────────
            cursor.execute("""
                SELECT id, qty, rate
                FROM stock_statement_lots
                WHERE item_name = %s AND outlet_name = %s AND qty > 0
                ORDER BY id ASC
            """, (item_name, outlet_name))
            lots           = cursor.fetchall()
            fifo_lines     = []   # [(deducted_qty, lot_rate), ...]
            remaining_lots = requested_qty

            for lot in lots:
                if remaining_lots <= 0.001:
                    break

                lot_id   = lot[0]
                lot_qty  = float(lot[1])
                lot_rate = float(lot[2])

                if lot_qty <= remaining_lots + 0.001:
                    deducted      = lot_qty
                    new_lot_qty   = 0
                    new_lot_total = 0
                    remaining_lots -= lot_qty
                else:
                    deducted      = remaining_lots
                    new_lot_qty   = lot_qty - remaining_lots
                    new_lot_total = round(new_lot_qty * lot_rate, 4)
                    remaining_lots = 0

                cursor.execute("""
                    UPDATE stock_statement_lots
                    SET qty = %s, total = %s
                    WHERE id = %s AND qty >= %s
                """, (new_lot_qty, new_lot_total, lot_id, lot_qty))

                if cursor.rowcount == 0:
                    raise Exception(f"Concurrent update detected for stock_statement_lots id {lot_id}")

                fifo_lines.append((deducted, lot_rate))

            if remaining_lots > 0.001:
                raise Exception(
                    f"Insufficient lots in stock_statement_lots for {item_name}. "
                    f"Still undeducted: {remaining_lots:.4f}"
                )

            # ── 3. Update stock_statement using FIFO total ────────────────────
            cursor.execute("""
                SELECT CurrentLevel, Total, Rate
                FROM stock_statement
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
            """, (item_name, uom, outlet_name))
            existing = cursor.fetchone()

            current_level        = float(existing[0])
            current_total        = float(existing[1]) if existing[1] else 0
            fifo_deduction_total = round(sum(q * r for q, r in fifo_lines), 4)
            new_level            = current_level - requested_qty
            new_total            = new_level * float(existing[2])

            if abs(new_level) < 0.001:
                new_level = 0
                new_total = 0

            cursor.execute("""
                UPDATE stock_statement
                SET CurrentLevel = %s, Total = %s
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                AND CurrentLevel >= %s
            """, (new_level, new_total, item_name, uom, outlet_name, requested_qty))

            if cursor.rowcount == 0:
                raise Exception(f"Concurrent update detected for stock_statement of {item_name}")

            # ── 4. Insert into intblstorereqdetails — one row per FIFO lot ────
            for deducted_qty, lot_rate in fifo_lines:
                cursor.execute("""
                    INSERT INTO intblstorereqdetails 
                    (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["ItemName"],
                    item["GroupName"],
                    item["BrandName"],
                    deducted_qty,    # qty from this lot
                    item["UOM"],
                    lot_rate,        # rate from the lot, NOT frontend
                    store_req_id,
                    item_type
                ))

            # ── 5. Insert into item_current_level — one row per FIFO lot ─────
            for deducted_qty, lot_rate in fifo_lines:
                cursor.execute("""
                    INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    item['ItemName'],
                    deducted_qty,
                    lot_rate,        # rate from the lot, NOT frontend
                    outlet_name,
                    costcenter
                ))

        mydb.commit()

        return jsonify({
            "status": "success",
            "message": "Stock transfer request added successfully!",
            "outlet_req_id": outlet_req_id,
            "store_req_id": store_req_id
        }), 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        if mydb and mydb.is_connected():
            mydb.close()


from .production.utils import adjust_production_item_after_sale
# @app_file57.route('/poststockTransfer_web', methods = ["POST"])
# @cross_origin()
# def postStock_web():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'), 
#             password=os.getenv('password'), 
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(buffered=True, dictionary=True)

#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         json_data = request.get_json()

#         store_itemdetails = json_data.pop("ItemDetailsList", None)
#         store_requisition = json_data

#         # Convert the date to MySQL compatible format
#         try:
#             date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
#             formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#         except Exception as e:
#             return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400
        
#         purchase_from = store_requisition.get("purchase_from", "c_app")
#         purchase_id = store_requisition.get("purchase_id", None)

#         # Generate OutletREQID based on purchase_from
#         if purchase_from == "web":
#             cursor.execute("""
#                 SELECT MAX(CAST(OutletREQID AS UNSIGNED)) as max_id
#                 FROM intblstorerequisition
#                 WHERE Outlet = %s and purchase_from = 'web'
#             """, (store_requisition["OutletName"],))
            
#             result = cursor.fetchone()
#             max_id = result['max_id'] if result else None
            
#             if max_id is None:
#                 outlet_req_id = 1
#             else:
#                 outlet_req_id = int(max_id) + 1
#         else:
#             outlet_req_id = store_requisition["Outlet_Req_ID"]

#         # VALIDATION: Get current stock levels for all items
#         stock_info = []
#         stock_validation_errors = []
        
#         for item in store_itemdetails:
#             requested_qty = float(item["Amount"])
#             item_name = item["ItemName"]
#             uom = item["UOM"]
#             outlet_name = store_requisition["OutletName"]
            
#             cursor.execute("""
#                 SELECT CurrentLevel, Total, Rate 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item_name, uom, outlet_name))
            
#             existing = cursor.fetchone()
            
#             if not existing:
#                 stock_validation_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "requested": requested_qty,
#                     "available": 0,
#                     "error": "Item not found in stock statement"
#                 })
#             else:
#                 current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
#                 current_total = float(existing['Total']) if existing['Total'] else 0
#                 unit_price = float(existing['Rate']) if existing.get('Rate') else item.get("Rate", 0)
                
#                 stock_info.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "requested": requested_qty,
#                     "available": current_level,
#                     "unit_price": unit_price,
#                     "current_total": current_total,
#                     "will_remain": current_level - requested_qty,
#                     "will_total": current_total - (requested_qty * unit_price)
#                 })
                
#                 if requested_qty > current_level:
#                     stock_validation_errors.append({
#                         "item": item_name,
#                         "uom": uom,
#                         "requested": requested_qty,
#                         "available": current_level,
#                         "shortage": requested_qty - current_level,
#                         "error": f"Insufficient stock. Shortage: {requested_qty - current_level} units"
#                     })
        
#         # If any validation errors, return them without proceeding
#         if stock_validation_errors:
#             mydb.rollback()
#             return jsonify({
#                 "status": "error",
#                 "message": "Stock validation failed. Some items have insufficient stock.",
#                 "stock_summary": stock_info,
#                 "errors": stock_validation_errors
#             }), 400

#         # Proceed with insertion
#         insert_storerequisitionSql = """ INSERT INTO intblstorerequisition 
#             (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) 
#             VALUES (%s, %s, %s, %s, %s, %s)"""

#         cursor.execute(insert_storerequisitionSql, (
#             formatted_date,
#             store_requisition["CostCenter"], 
#             store_requisition["OutletName"],
#             outlet_req_id, 
#             purchase_from, 
#             purchase_id
#         ))

#         store_req_id = cursor.lastrowid

#         costcenter = store_requisition["CostCenter"]

#         if costcenter == "Kitchen":
#             item_type = "Food"
#         elif costcenter == "Bar":
#             item_type = "Beverage"
#         else:
#             item_type = costcenter

#         # Process each item
#         for item, stock in zip(store_itemdetails, stock_info):
#             requested_qty = float(item["Amount"])
#             requested_rate = float(item["Rate"])
#             item_name = item["ItemName"]
#             uom = item["UOM"]
#             outlet_name = store_requisition["OutletName"]

#             # Update stock_statement
#             cursor.execute("""
#                 UPDATE stock_statement
#                 SET CurrentLevel = %s,
#                     Total = %s
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (
#                 stock['will_remain'],
#                 stock['will_total'],
#                 item_name,
#                 uom,
#                 outlet_name
#             ))

#             # Insert into intblstorereqdetails
#             cursor.execute("""
#                 INSERT INTO intblstorereqdetails 
#                 (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) 
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """, (
#                 item["ItemName"], 
#                 item["GroupName"], 
#                 item["BrandName"], 
#                 item["Amount"], 
#                 item["UOM"], 
#                 item["Rate"], 
#                 store_req_id,
#                 item_type
#             ))


#             if costcenter == "Central Kitchen":
#                 # Insert into item_current_level
#                 cursor.execute("""
#                     INSERT INTO production_item_current_level (itemname, quantity, rate, outlet, costcenter)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """, (
#                     item['ItemName'],
#                     float(item['Amount']),
#                     float(item['Rate']),
#                     outlet_name,
#                     costcenter                
#                 ))
#             else:
#                 # Insert into item_current_level
#                 cursor.execute("""
#                     INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """, (
#                     item['ItemName'],
#                     float(item['Amount']),
#                     float(item['Rate']),
#                     outlet_name,
#                     costcenter                
#                 ))

#                 if item['GroupName'] == "Finished Goods":

#                   # CALL YOUR FUNCTION HERE!
#                     adjust_production_item_after_sale(
#                         production_item_name=item_name,
#                         sold_qty=requested_qty,
#                         outlet=outlet_name,
#                         cursor=cursor,
#                         mydb=mydb,
#                         order_date=date_obj.date()  # Use the date from the requisition
#                     )


#         mydb.commit()

#         return jsonify({
#             "status": "success", 
#             "message": "Stock transfer request added successfully!",
#             "outlet_req_id": outlet_req_id,
#             "store_req_id": store_req_id,
#             "stock_summary": stock_info
#         }), 200
    
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return jsonify({"error": str(e)}), 400
    
#     finally:
#         if mydb and mydb.is_connected():
#             mydb.close()


@app_file57.route('/poststockTransfer_web', methods=["POST"])
@cross_origin()
def postStock_web():
    try:
        mydb = mysql.connector.connect(
            user=os.getenv('user'), 
            password=os.getenv('password'), 
            host=os.getenv('host')
        )
        cursor = mydb.cursor(buffered=True, dictionary=True)
        cursor.execute("USE {};".format(os.getenv('database')))

        json_data = request.get_json()
        store_itemdetails = json_data.pop("ItemDetailsList", None)
        store_requisition = json_data

        try:
            date_obj = datetime.strptime(store_requisition['Date'], '%Y-%m-%dT%H:%M:%S')
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return jsonify({"error": "Invalid date format, expected 'YYYY-MM-DDTHH:MM:SS'"}), 400

        purchase_from = store_requisition.get("purchase_from", "c_app")
        purchase_id   = store_requisition.get("purchase_id", None)
        outlet_name   = store_requisition["OutletName"]

        # Generate OutletREQID
        if purchase_from == "web":
            cursor.execute("""
                SELECT MAX(CAST(OutletREQID AS UNSIGNED)) as max_id
                FROM intblstorerequisition
                WHERE Outlet = %s AND purchase_from = 'web'
            """, (outlet_name,))
            result = cursor.fetchone()
            max_id = result['max_id'] if result else None
            outlet_req_id = (int(max_id) + 1) if max_id else 1
        else:
            outlet_req_id = store_requisition["Outlet_Req_ID"]

        # ==================== VALIDATION ====================
        stock_info = []
        stock_validation_errors = []

        for item in store_itemdetails:
            requested_qty = float(item["Amount"])
            item_name     = item["ItemName"]
            uom           = item["UOM"]

            # Check stock_statement
            cursor.execute("""
                SELECT CurrentLevel, Total, Rate 
                FROM stock_statement 
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
            """, (item_name, uom, outlet_name))
            existing = cursor.fetchone()

            if not existing:
                stock_validation_errors.append({
                    "item": item_name, "uom": uom,
                    "requested": requested_qty, "available": 0,
                    "error": "Item not found in stock statement"
                })
                continue

            current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
            current_total = float(existing['Total']) if existing['Total'] else 0
            unit_price    = float(existing['Rate']) if existing.get('Rate') else item.get("Rate", 0)

            if requested_qty > current_level:
                stock_validation_errors.append({
                    "item": item_name, "uom": uom,
                    "requested": requested_qty, "available": current_level,
                    "shortage": requested_qty - current_level,
                    "error": f"Insufficient stock. Shortage: {requested_qty - current_level} units"
                })

            # Check stock_statement_lots
            cursor.execute("""
                SELECT SUM(qty)
                FROM stock_statement_lots
                WHERE item_name = %s AND outlet_name = %s AND qty > 0
            """, (item_name, outlet_name))
            lots_result   = cursor.fetchone()
            # dictionary cursor returns dict, get first value
            lots_available = float(list(lots_result.values())[0]) if list(lots_result.values())[0] else 0

            if lots_available < requested_qty - 0.001:
                stock_validation_errors.append({
                    "item": item_name, "uom": uom,
                    "requested": requested_qty, "available": lots_available,
                    "error": f"Insufficient lots in stock_statement_lots. Available: {lots_available:.2f}"
                })

            stock_info.append({
                "item": item_name,
                "uom": uom,
                "requested": requested_qty,
                "available": current_level,
                "unit_price": unit_price,
                "current_total": current_total,
                "will_remain": current_level - requested_qty,
                "will_total": current_total - (requested_qty * unit_price)
            })

        if stock_validation_errors:
            return jsonify({
                "status": "error",
                "message": "Stock validation failed. Some items have insufficient stock.",
                "stock_summary": stock_info,
                "errors": stock_validation_errors
            }), 400

        # ==================== INSERT REQUISITION HEADER ====================
        cursor.execute("""
            INSERT INTO intblstorerequisition 
            (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            formatted_date,
            store_requisition["CostCenter"],
            outlet_name,
            outlet_req_id,
            purchase_from,
            purchase_id
        ))

        store_req_id = cursor.lastrowid
        costcenter   = store_requisition["CostCenter"]

        if costcenter == "Kitchen":
            item_type = "Food"
        elif costcenter == "Bar":
            item_type = "Beverage"
        else:
            item_type = costcenter

        # ==================== PROCESS EACH ITEM ====================
        for item, stock in zip(store_itemdetails, stock_info):
            requested_qty = float(item["Amount"])
            item_name     = item["ItemName"]
            uom           = item["UOM"]

            rate = item["Rate"]

            # # ── 1. FIFO deduction from stock_current_level ────────────────────
            # cursor.execute("""
            #     SELECT id, qty, rate, total, expiry_date
            #     FROM stock_current_level
            #     WHERE name = %s
            #     AND qty > 0
            #     AND (expiry_date IS NULL OR expiry_date > CURDATE())
            #     ORDER BY expiry_date ASC, id ASC
            # """, (item_name,))
            # # dictionary cursor — convert to list of dicts
            # scl_batches = cursor.fetchall()

            # remaining_scl = requested_qty
            # for batch in scl_batches:
            #     if remaining_scl <= 0.001:
            #         break
            #     batch_id     = batch['id']
            #     batch_qty    = float(batch['qty'])
            #     batch_rate   = float(batch['rate'])

            #     if batch_qty <= remaining_scl + 0.001:
            #         new_qty   = 0
            #         new_total = 0
            #         remaining_scl -= batch_qty
            #     else:
            #         new_qty   = batch_qty - remaining_scl
            #         new_total = round(new_qty * batch_rate, 4)
            #         remaining_scl = 0

            #     cursor.execute("""
            #         UPDATE stock_current_level
            #         SET qty = %s, total = %s
            #         WHERE id = %s AND qty >= %s
            #     """, (new_qty, new_total, batch_id, batch_qty))

            #     if cursor.rowcount == 0:
            #         raise Exception(f"Concurrent update detected for stock_current_level batch {batch_id}")

            # ── 2. FIFO deduction from stock_statement_lots ───────────────────
            cursor.execute("""
                SELECT id, qty, rate
                FROM stock_statement_lots
                WHERE item_name = %s AND outlet_name = %s AND qty > 0
                ORDER BY id ASC
            """, (item_name, outlet_name))
            lots = cursor.fetchall()

            fifo_lines     = []   # [(deducted_qty, lot_rate), ...]
            remaining_lots = requested_qty

            for lot in lots:
                if remaining_lots <= 0.001:
                    break

                lot_id   = lot['id']
                lot_qty  = float(lot['qty'])
                lot_rate = float(lot['rate'])

                if lot_qty <= remaining_lots + 0.001:
                    deducted      = lot_qty
                    new_lot_qty   = 0
                    new_lot_total = 0
                    remaining_lots -= lot_qty
                else:
                    deducted      = remaining_lots
                    new_lot_qty   = lot_qty - remaining_lots
                    new_lot_total = round(new_lot_qty * lot_rate, 4)
                    remaining_lots = 0

                cursor.execute("""
                    UPDATE stock_statement_lots
                    SET qty = %s, total = %s
                    WHERE id = %s AND qty >= %s
                """, (new_lot_qty, new_lot_total, lot_id, lot_qty))

                if cursor.rowcount == 0:
                    raise Exception(f"Concurrent update detected for stock_statement_lots id {lot_id}")

                fifo_lines.append((deducted, lot_rate))

            if remaining_lots > 0.001:
                raise Exception(
                    f"Insufficient lots in stock_statement_lots for {item_name}. "
                    f"Still undeducted: {remaining_lots:.4f}"
                )

            # ── 3. Update stock_statement using FIFO total ────────────────────
            fifo_deduction_total = round(sum(qty * rate for qty, rate in fifo_lines), 4)
            new_level = stock['will_remain']
            # new_total = round(stock['current_total'] - fifo_deduction_total, 4)
            new_total = new_level * rate

            if abs(new_level) < 0.001:
                new_level = 0
                new_total = 0

            cursor.execute("""
                UPDATE stock_statement
                SET CurrentLevel = %s, Total = %s
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                AND CurrentLevel >= %s
            """, (new_level, new_total, item_name, uom, outlet_name, requested_qty))

            if cursor.rowcount == 0:
                raise Exception(f"Concurrent update detected for stock_statement of {item_name}")

            # ── 4. Insert into intblstorereqdetails — one row per FIFO lot ────
            for deducted_qty, lot_rate in fifo_lines:
                cursor.execute("""
                    INSERT INTO intblstorereqdetails 
                    (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["ItemName"],
                    item["GroupName"],
                    item["BrandName"],
                    deducted_qty,    # qty from this lot
                    item["UOM"],
                    lot_rate,        # rate from the lot, NOT frontend
                    store_req_id,
                    item_type
                ))

            # ── 5. Insert into item_current_level — one row per FIFO lot ─────
            if costcenter == "Central Kitchen":
                for deducted_qty, lot_rate in fifo_lines:
                    cursor.execute("""
                        INSERT INTO production_item_current_level 
                        (itemname, quantity, rate, outlet, costcenter)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (item['ItemName'], deducted_qty, lot_rate, outlet_name, costcenter))
            else:
                for deducted_qty, lot_rate in fifo_lines:
                    cursor.execute("""
                        INSERT INTO item_current_level 
                        (itemname, quantity, rate, outlet, costcenter)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (item['ItemName'], deducted_qty, lot_rate, outlet_name, costcenter))

                if item['GroupName'] == "Finished Goods":
                    adjust_production_item_after_sale(
                        production_item_name=item_name,
                        sold_qty=requested_qty,
                        outlet=outlet_name,
                        cursor=cursor,
                        mydb=mydb,
                        order_date=date_obj.date()
                    )

        mydb.commit()

        return jsonify({
            "status": "success",
            "message": "Stock transfer request added successfully!",
            "outlet_req_id": outlet_req_id,
            "store_req_id": store_req_id,
            "stock_summary": stock_info
        }), 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        if mydb and mydb.is_connected():
            mydb.close()


@app_file57.route('/getStorereqsByPurchaseId', methods=["POST"])
@cross_origin()
def getStorereqsByPurchaseId():
    try:
        mydb = mysql.connector.connect(
            user=os.getenv('user'),
            password=os.getenv('password'),
            host=os.getenv('host')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Select DB
        cursor.execute(f"USE {os.getenv('database')}")

        # Get request data
        data = request.get_json()

        purchase_id = data.get('purchase_id')
        outlet_name = data.get('outlet_name')

        # ✅ Validation
        if not purchase_id:
            return jsonify({"error": "purchase_id is required"}), 400

        if not outlet_name:
            return jsonify({"error": "outlet_name is required"}), 400

        # Convert purchase_id to int (safer)
        try:
            purchase_id = int(purchase_id)
        except:
            return jsonify({"error": "purchase_id must be an integer"}), 400

        # ✅ Main Query (NO DATE_FORMAT here)
        sql = """
        SELECT 
            idintblStoreRequisition,
            OutletREQID,
            Date,
            CostCenter,
            Outlet,
            purchase_from,
            purchase_id
        FROM intblstorerequisition 
        WHERE purchase_id = %s AND Outlet = %s
        ORDER BY Date DESC
        """

        cursor.execute(sql, (purchase_id, outlet_name))
        store_requisitions = cursor.fetchall()

        # ✅ Add formatted date + fetch items
        for requisition in store_requisitions:
            # Format date safely
            if requisition.get("Date"):
                requisition["formatted_date"] = requisition["Date"].strftime('%Y-%m-%d %H:%M:%S')
            else:
                requisition["formatted_date"] = None

            # Fetch item details
            items_sql = """
            SELECT 
                ItemName,
                GroupName,
                BrandName,
                Amount,
                UOM,
                Rate,
                itemtype
            FROM intblstorereqdetails 
            WHERE StoreReqID = %s
            """

            cursor.execute(items_sql, (requisition['idintblStoreRequisition'],))
            requisition['items'] = cursor.fetchall()

        mydb.close()

        return jsonify({
            "success": True,
            "purchase_id": purchase_id,
            "outlet_name": outlet_name,
            "count": len(store_requisitions),
            "data": store_requisitions
        }), 200

    except Exception as e:
        print("Error details:", str(e))
        return jsonify({"error": str(e)}), 400
    

@app_file57.route('/getDistinctCostCenters', methods=["POST"])
@cross_origin()
def get_distinct_cost_centers():
    try:
        mydb = mysql.connector.connect(
            user=os.getenv('user'),
            password=os.getenv('password'),
            host=os.getenv('host')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Select DB
        cursor.execute(f"USE {os.getenv('database')}")

        # Get request data
        data = request.get_json()
        outlet_name = data.get('outlet_name')

        # Validation
        if not outlet_name:
            return jsonify({"error": "outlet_name is required"}), 400

        # Query to get distinct cost centers
        sql = """
        SELECT DISTINCT CostCenter
        FROM intblstorerequisition 
        WHERE Outlet = %s AND CostCenter IS NOT NULL AND CostCenter != ''
        ORDER BY CostCenter ASC
        """

        cursor.execute(sql, (outlet_name,))
        cost_centers = cursor.fetchall()

        mydb.close()

        # Extract just the cost center names into a list
        cost_center_list = [center['CostCenter'] for center in cost_centers]

        return jsonify({
            "success": True,
            "outlet_name": outlet_name,
            "count": len(cost_center_list),
            "cost_centers": cost_center_list
        }), 200

    except Exception as e:
        print("Error details:", str(e))
        return jsonify({"error": str(e)}), 400
    


from datetime import datetime, timedelta

@app_file57.route('/getStorereqs', methods=["POST"])
@cross_origin()
def getStorereqs():
    try:
        mydb = mysql.connector.connect(
            user=os.getenv('user'),
            password=os.getenv('password'),
            host=os.getenv('host')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Select DB
        cursor.execute(f"USE {os.getenv('database')}")

        # Get request data
        data = request.get_json()
        outlet_name = data.get('outlet_name')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        store_req_id = data.get('storereqID')
        if not outlet_name:
            return jsonify({"error": "outlet_name is required"}), 400

        # ✅ Build dynamic query
        sql = """
        SELECT 
            idintblStoreRequisition,
            OutletREQID,
            Date,
            CostCenter,
            Outlet,
            purchase_from,
            purchase_id
        FROM intblstorerequisition 
        WHERE Outlet = %s and purchase_from = 'web'
        """

        params = [outlet_name]

        # ✅ Filter by requisition ID
        if store_req_id:
            sql += " AND idintblStoreRequisition = %s"
            params.append(store_req_id)


        # ✅ Apply date filter if provided
        if from_date and to_date:
            start = datetime.strptime(from_date, "%Y-%m-%d")
            end = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)

            sql += " AND Date >= %s AND Date < %s"
            params.extend([start, end])

        sql += " ORDER BY Date DESC"

        cursor.execute(sql, tuple(params))
        store_requisitions = cursor.fetchall()

        # ✅ Add formatted date + fetch items
        for requisition in store_requisitions:
            if requisition.get("Date"):
                requisition["formatted_date"] = requisition["Date"].strftime('%Y-%m-%d %H:%M:%S')
            else:
                requisition["formatted_date"] = None

            items_sql = """
            SELECT 
                ItemName,
                GroupName,
                BrandName,
                Amount,
                UOM,
                Rate,
                itemtype
            FROM intblstorereqdetails 
            WHERE StoreReqID = %s
            """

            cursor.execute(items_sql, (requisition['idintblStoreRequisition'],))
            requisition['items'] = cursor.fetchall()

        mydb.close()

        return jsonify({
            "success": True,
            "outlet_name": outlet_name,
            "count": len(store_requisitions),
            "data": store_requisitions
        }), 200

    except Exception as e:
        print("Error details:", str(e))
        return jsonify({"error": str(e)}), 400
    

# @app_file57.route('/deletestockTransfer_web', methods = ["DELETE"])
# @cross_origin()
# def deleteStockTransfer_web():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'), 
#             password=os.getenv('password'), 
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(buffered=True, dictionary=True)

#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         # Get the store_req_id from request
#         json_data = request.get_json()
#         store_req_id = json_data.get("store_req_id")
        
#         if not store_req_id:
#             return jsonify({"error": "store_req_id is required"}), 400

#         # First, get the requisition details to know which items to restore/remove
#         cursor.execute("""
#             SELECT sr.Outlet, sr.CostCenter, srd.ItemName, srd.UOM, srd.Amount, srd.Rate
#             FROM intblstorerequisition sr
#             JOIN intblstorereqdetails srd ON sr.StoreReqID = srd.StoreReqID
#             WHERE sr.StoreReqID = %s
#         """, (store_req_id,))
        
#         requisition_items = cursor.fetchall()
        
#         if not requisition_items:
#             return jsonify({"error": "Store requisition not found"}), 404

#         # Restore stock to stock_statement and remove from item_current_level
#         restoration_details = []
#         restoration_errors = []
        
#         for item in requisition_items:
#             item_name = item['ItemName']
#             uom = item['UOM']
#             outlet_name = item['Outlet']
#             costcenter = item['CostCenter']
#             amount_to_restore = float(item['Amount'])
#             rate = float(item['Rate'])
            
#             # 1. RESTORE stock_statement (add back the quantity)
#             cursor.execute("""
#                 SELECT CurrentLevel, Total, Rate 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item_name, uom, outlet_name))
            
#             existing = cursor.fetchone()
            
#             if not existing:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": "Item not found in stock_statement"
#                 })
#                 continue
            
#             current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
#             current_total = float(existing['Total']) if existing['Total'] else 0
#             unit_price = float(existing['Rate']) if existing.get('Rate') else rate
            
#             # Calculate restored values (adding back)
#             restored_level = current_level + amount_to_restore
#             restored_total = current_total + (amount_to_restore * unit_price)
            
#             # Update stock_statement with restored levels
#             cursor.execute("""
#                 UPDATE stock_statement
#                 SET CurrentLevel = %s,
#                     Total = %s
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (
#                 restored_level,
#                 restored_total,
#                 item_name,
#                 uom,
#                 outlet_name
#             ))
            
#             # 2. REMOVE from item_current_level (subtract the quantity)
#             # First, get the current item_current_level entry for this item
#             cursor.execute("""
#                 SELECT id, quantity, rate 
#                 FROM item_current_level 
#                 WHERE itemname = %s 
#                 AND outlet = %s 
#                 AND costcenter = %s
#                 ORDER BY id DESC 
#                 LIMIT 1
#             """, (item_name, outlet_name, costcenter))
            
#             current_item = cursor.fetchone()
            
#             if not current_item:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": "Item not found in item_current_level"
#                 })
#                 continue
            
#             current_item_qty = float(current_item['quantity'])
            
#             if current_item_qty < amount_to_restore:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": f"Insufficient quantity in item_current_level to remove. Available: {current_item_qty}, Requested to remove: {amount_to_restore}"
#                 })
#                 continue
            
#             new_item_qty = current_item_qty - amount_to_restore
            
#             restoration_details.append({
#                 "item": item_name,
#                 "uom": uom,
#                 "amount_restored_to_stock": amount_to_restore,
#                 "stock_statement": {
#                     "previous_level": current_level,
#                     "new_level": restored_level,
#                     "previous_total": current_total,
#                     "new_total": restored_total
#                 },
#                 "item_current_level": {
#                     "previous_quantity": current_item_qty,
#                     "new_quantity": new_item_qty,
#                     "rate": float(current_item['rate'])
#                 }
#             })
            
#             # Update or delete from item_current_level based on new quantity
#             if new_item_qty <= 0:
#                 # If quantity becomes zero or negative, delete the record
#                 cursor.execute("""
#                     DELETE FROM item_current_level 
#                     WHERE id = %s
#                 """, (current_item['id'],))
#                 restoration_details[-1]["item_current_level"]["action"] = "Deleted (quantity became 0)"
#             else:
#                 # Otherwise, update with new quantity
#                 cursor.execute("""
#                     UPDATE item_current_level 
#                     SET quantity = %s
#                     WHERE id = %s
#                 """, (new_item_qty, current_item['id']))
#                 restoration_details[-1]["item_current_level"]["action"] = "Updated"
        
#         # If there were errors, rollback and don't delete
#         if restoration_errors:
#             mydb.rollback()
#             return jsonify({
#                 "status": "error",
#                 "message": "Failed to restore stock/remove from current level. Deletion cancelled.",
#                 "errors": restoration_errors,
#                 "restoration_details": restoration_details
#             }), 400
        
#         # Delete from intblstorereqdetails first (due to foreign key constraint)
#         cursor.execute("""
#             DELETE FROM intblstorereqdetails 
#             WHERE StoreReqID = %s
#         """, (store_req_id,))
        
#         # Finally delete the main requisition record
#         cursor.execute("""
#             DELETE FROM intblstorerequisition 
#             WHERE StoreReqID = %s
#         """, (store_req_id,))
        
#         mydb.commit()
        
#         return jsonify({
#             "status": "success",
#             "message": f"Store requisition {store_req_id} deleted successfully. Stock restored and current level updated.",
#             "restoration_details": restoration_details
#         }), 200
    
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return jsonify({"error": str(e)}), 400
    
#     finally:
#         if mydb and mydb.is_connected():
#             mydb.close()


# @app_file57.route('/deletestockTransfer_web', methods=["DELETE"])
# @cross_origin()
# def deleteStockTransfer_web():
#     try:
#         mydb = mysql.connector.connect(
#             user=os.getenv('user'), 
#             password=os.getenv('password'), 
#             host=os.getenv('host')
#         )
#         cursor = mydb.cursor(buffered=True, dictionary=True)

#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         # Get the store_req_id from request
#         json_data = request.get_json()
#         store_req_id = json_data.get("store_req_id")
        
#         if not store_req_id:
#             return jsonify({"error": "store_req_id is required"}), 400

#         # Get the requisition header details first
#         cursor.execute("""
#             SELECT sr.Outlet, sr.CostCenter, sr.Date, sr.purchase_from, sr.purchase_id
#             FROM intblstorerequisition sr
#             WHERE sr.StoreReqID = %s
#         """, (store_req_id,))
        
#         requisition_header = cursor.fetchone()
#         if not requisition_header:
#             return jsonify({"error": "Store requisition not found"}), 404
        
#         outlet_name = requisition_header['Outlet']
#         costcenter = requisition_header['CostCenter']
#         order_date = requisition_header['Date']
        
#         # Get all items in this requisition with their details
#         cursor.execute("""
#             SELECT srd.ItemName, srd.GroupName, srd.BrandName, srd.UOM, 
#                    srd.Amount, srd.Rate, srd.itemtype,
#                    srd.id as detail_id
#             FROM intblstorereqdetails srd
#             WHERE srd.StoreReqID = %s
#         """, (store_req_id,))
        
#         requisition_items = cursor.fetchall()
        
#         if not requisition_items:
#             return jsonify({"error": "No items found in this requisition"}), 404

#         # Track restoration details
#         restoration_details = []
#         restoration_errors = []
        
#         # Group items by item_name for lot restoration
#         items_by_name = {}
#         for item in requisition_items:
#             item_name = item['ItemName']
#             if item_name not in items_by_name:
#                 items_by_name[item_name] = []
#             items_by_name[item_name].append(item)
        
#         for item_name, items in items_by_name.items():
#             total_amount_to_restore = sum(float(item['Amount']) for item in items)
#             uom = items[0]['UOM']
#             group_name = items[0]['GroupName']
            
#             # Step 1: RESTORE stock_statement (add back the quantity)
#             cursor.execute("""
#                 SELECT CurrentLevel, Total, Rate 
#                 FROM stock_statement 
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (item_name, uom, outlet_name))
            
#             existing = cursor.fetchone()
            
#             if not existing:
#                 restoration_errors.append({
#                     "item": item_name,
#                     "uom": uom,
#                     "error": "Item not found in stock_statement"
#                 })
#                 continue
            
#             current_level = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
#             current_total = float(existing['Total']) if existing['Total'] else 0
#             unit_price = float(existing['Rate']) if existing.get('Rate') else items[0]['Rate']
            
#             # Calculate restored values (adding back)
#             restored_level = current_level + total_amount_to_restore
#             restored_total = current_total + (total_amount_to_restore * unit_price)
            
#             # Update stock_statement with restored levels
#             cursor.execute("""
#                 UPDATE stock_statement
#                 SET CurrentLevel = %s,
#                     Total = %s
#                 WHERE ItemName = %s AND UOM = %s AND OutletName = %s
#             """, (
#                 restored_level,
#                 restored_total,
#                 item_name,
#                 uom,
#                 outlet_name
#             ))
            
#             # Step 2: RESTORE stock_statement_lots (add back the lots that were consumed)
#             # We need to reverse the FIFO deduction from stock_statement_lots
#             for item in items:
#                 amount_to_restore = float(item['Amount'])
#                 rate = float(item['Rate'])
                
#                 # Instead of trying to match exact lots, we'll add back as a new lot
#                 # This is simpler and more reliable
#                 cursor.execute("""
#                     INSERT INTO stock_statement_lots 
#                     (item_name, uom, qty, rate, total, outlet_name, posted_at)
#                     VALUES (%s, %s, %s, %s, %s, %s, NOW())
#                 """, (
#                     item_name, 
#                     uom, 
#                     amount_to_restore,
#                     rate,
#                     amount_to_restore * rate,
#                     outlet_name
#                 ))
            
#             # Step 3: REVERSE production_item_current_level and production_consumption_tracker for Finished Goods
#             if group_name == "Finished Goods":
#                 # For Finished Goods, we need to reverse the production consumption
#                 for item in items:
#                     amount_to_restore = float(item['Amount'])
#                     rate = float(item['Rate'])
                    
#                     # Get conversion factor for this production item
#                     cursor.execute("""
#                         SELECT ss.id as production_item_id, cf.factor, cf.production_recipe_id
#                         FROM stock_statement ss
#                         LEFT JOIN conversionfactor cf ON cf.production_item_id = ss.id AND cf.outlet = %s
#                         WHERE ss.ItemName = %s AND ss.OutletName = %s
#                     """, (outlet_name, item_name, outlet_name))
                    
#                     conversion_info = cursor.fetchone()
                    
#                     if conversion_info and conversion_info['factor']:
#                         factor = float(conversion_info['factor'])
#                         actual_production_quantity = amount_to_restore / factor if factor > 0 else 0
                        
#                         # Get the consumption records from production_consumption_tracker
#                         cursor.execute("""
#                             SELECT id, item_name, consumed_quantity, rate, outlet, recipe_name, ItemType
#                             FROM production_consumption_tracker
#                             WHERE recipe_name = %s 
#                             AND outlet = %s 
#                             AND DATE(order_date) = DATE(%s)
#                             ORDER BY id DESC
#                         """, (item_name, outlet_name, order_date))
                        
#                         consumption_records = cursor.fetchall()
                        
#                         if consumption_records:
#                             # We need to reverse these consumptions - add back to production_item_current_level
#                             for record in consumption_records:
#                                 ingredient_name = record['item_name']
#                                 consumed_qty = float(record['consumed_quantity'])
#                                 consumed_rate = float(record['rate'])
#                                 recipe_item_type = record['ItemType']
                                
#                                 # Add back to production_item_current_level
#                                 cursor.execute("""
#                                     SELECT id, quantity, rate, costcenter
#                                     FROM production_item_current_level
#                                     WHERE itemname = %s 
#                                     AND outlet = %s 
#                                     AND costcenter = 'Central Kitchen'
#                                     ORDER BY id DESC
#                                     LIMIT 1
#                                 """, (ingredient_name, outlet_name))
                                
#                                 existing_prod_item = cursor.fetchone()
                                
#                                 if existing_prod_item:
#                                     # Update existing record
#                                     new_qty = float(existing_prod_item['quantity']) + consumed_qty
#                                     cursor.execute("""
#                                         UPDATE production_item_current_level
#                                         SET quantity = %s
#                                         WHERE id = %s
#                                     """, (new_qty, existing_prod_item['id']))
#                                 else:
#                                     # Create new record
#                                     cursor.execute("""
#                                         INSERT INTO production_item_current_level
#                                         (itemname, quantity, rate, outlet, costcenter, ItemType)
#                                         VALUES (%s, %s, %s, %s, %s, %s)
#                                     """, (
#                                         ingredient_name,
#                                         consumed_qty,
#                                         consumed_rate,
#                                         outlet_name,
#                                         'Central Kitchen',
#                                         recipe_item_type
#                                     ))
                                
#                                 # Delete the consumption record
#                                 cursor.execute("""
#                                     DELETE FROM production_consumption_tracker
#                                     WHERE id = %s
#                                 """, (record['id'],))
#                     else:
#                         # No conversion factor, just handle as regular item
#                         # For Finished Goods without conversion factor, they might not have triggered production consumption
#                         pass
                    
#                     # Also remove from production_item_current_level (the finished good itself)
#                     cursor.execute("""
#                         DELETE FROM production_item_current_level
#                         WHERE itemname = %s 
#                         AND outlet = %s 
#                         AND costcenter = %s
#                         AND id IN (
#                             SELECT id FROM (
#                                 SELECT id FROM production_item_current_level
#                                 WHERE itemname = %s AND outlet = %s AND costcenter = %s
#                                 ORDER BY id ASC
#                                 LIMIT %s
#                             ) AS tmp
#                         )
#                     """, (item_name, outlet_name, costcenter, item_name, outlet_name, costcenter, len(items)))
            
#             # Step 4: REVERSE regular item_current_level (non-Finished Goods)
#             else:
#                 # Remove the items from item_current_level that were added during transfer
#                 for item in items:
#                     amount_to_remove = float(item['Amount'])
                    
#                     # Get the oldest entries first (FIFO removal)
#                     cursor.execute("""
#                         SELECT id, quantity, rate
#                         FROM item_current_level
#                         WHERE itemname = %s 
#                         AND outlet = %s 
#                         AND costcenter = %s
#                         AND quantity > 0
#                         ORDER BY id ASC
#                     """, (item_name, outlet_name, costcenter))
                    
#                     current_level_items = cursor.fetchall()
                    
#                     remaining_to_remove = amount_to_remove
#                     for level_item in current_level_items:
#                         if remaining_to_remove <= 0:
#                             break
                        
#                         current_qty = float(level_item['quantity'])
#                         item_id = level_item['id']
                        
#                         if current_qty <= remaining_to_remove:
#                             # Remove entire record
#                             cursor.execute("DELETE FROM item_current_level WHERE id = %s", (item_id,))
#                             remaining_to_remove -= current_qty
#                         else:
#                             # Update quantity
#                             new_qty = current_qty - remaining_to_remove
#                             cursor.execute("""
#                                 UPDATE item_current_level 
#                                 SET quantity = %s 
#                                 WHERE id = %s
#                             """, (new_qty, item_id))
#                             remaining_to_remove = 0
                    
#                     if remaining_to_remove > 0:
#                         restoration_errors.append({
#                             "item": item_name,
#                             "uom": uom,
#                             "error": f"Could not find enough quantity in item_current_level to remove. Missing: {remaining_to_remove}"
#                         })
            
#             restoration_details.append({
#                 "item": item_name,
#                 "uom": uom,
#                 "group_name": group_name,
#                 "amount_restored_to_stock": total_amount_to_restore,
#                 "action": "Restored stock and removed from current levels"
#             })
        
#         # If there were errors, rollback and don't delete
#         if restoration_errors:
#             mydb.rollback()
#             return jsonify({
#                 "status": "error",
#                 "message": "Failed to reverse the stock transfer. Deletion cancelled.",
#                 "errors": restoration_errors,
#                 "restoration_details": restoration_details
#             }), 400
        
#         # Delete from intblstorereqdetails first (due to foreign key constraint)
#         cursor.execute("""
#             DELETE FROM intblstorereqdetails 
#             WHERE StoreReqID = %s
#         """, (store_req_id,))
        
#         # Finally delete the main requisition record
#         cursor.execute("""
#             DELETE FROM intblstorerequisition 
#             WHERE StoreReqID = %s
#         """, (store_req_id,))
        
#         mydb.commit()
        
#         return jsonify({
#             "status": "success",
#             "message": f"Store requisition {store_req_id} deleted successfully. Stock and inventory levels have been reversed.",
#             "restoration_details": restoration_details
#         }), 200
    
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return jsonify({"error": str(e)}), 400
    
#     finally:
#         if mydb and mydb.is_connected():
#             mydb.close()


@app_file57.route('/deletestockTransfer_web', methods=["DELETE"])
@cross_origin()
def deleteStockTransfer_web():
    try:
        mydb = mysql.connector.connect(
            user=os.getenv('user'), 
            password=os.getenv('password'), 
            host=os.getenv('host')
        )
        cursor = mydb.cursor(buffered=True, dictionary=True)
        cursor.execute("USE {};".format(os.getenv('database')))

        json_data = request.get_json()
        store_req_id = json_data.get("store_req_id")
        
        if not store_req_id:
            return jsonify({"error": "store_req_id is required"}), 400

        # ── Get requisition header ────────────────────────────────────────────
        cursor.execute("""
            SELECT Outlet, CostCenter
            FROM intblstorerequisition
            WHERE StoreReqID = %s
        """, (store_req_id,))
        header = cursor.fetchone()

        if not header:
            return jsonify({"error": "Store requisition not found"}), 404

        outlet_name = header['Outlet']
        costcenter  = header['CostCenter']

        # ── Get all detail rows (one row per FIFO lot per item) ───────────────
        cursor.execute("""
            SELECT ItemName, UOM, Amount, Rate
            FROM intblstorereqdetails
            WHERE StoreReqID = %s
            ORDER BY id ASC
        """, (store_req_id,))
        detail_rows = cursor.fetchall()

        if not detail_rows:
            return jsonify({"error": "Store requisition details not found"}), 404

        # ── Group detail rows by item ─────────────────────────────────────────
        from collections import defaultdict
        item_lots = defaultdict(list)   # item_name -> [(qty, rate), ...]
        item_uom  = {}

        for row in detail_rows:
            item_name = row['ItemName']
            item_lots[item_name].append((float(row['Amount']), float(row['Rate'])))
            item_uom[item_name] = row['UOM']

        restoration_errors  = []
        restoration_details = []

        for item_name, lots in item_lots.items():
            uom        = item_uom[item_name]
            total_qty  = sum(qty for qty, _ in lots)
            fifo_total = round(sum(qty * rate for qty, rate in lots), 4)

            # ── 1. Restore stock_statement ────────────────────────────────────
            cursor.execute("""
                SELECT CurrentLevel, Total
                FROM stock_statement
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
            """, (item_name, uom, outlet_name))
            existing = cursor.fetchone()

            if not existing:
                restoration_errors.append({
                    "item": item_name,
                    "error": "Item not found in stock_statement"
                })
                continue

            current_level  = float(existing['CurrentLevel']) if existing['CurrentLevel'] else 0
            current_total  = float(existing['Total']) if existing['Total'] else 0
            restored_level = round(current_level + total_qty, 4)
            restored_total = round(current_total + fifo_total, 4)

            cursor.execute("""
                UPDATE stock_statement
                SET CurrentLevel = %s, Total = %s
                WHERE ItemName = %s AND UOM = %s AND OutletName = %s
            """, (restored_level, restored_total, item_name, uom, outlet_name))

            # ── 2. Restore stock_statement_lots ───────────────────────────────
            # Go LIFO (newest lot first) and match by rate to restore qty
            cursor.execute("""
                SELECT id, qty, rate, total
                FROM stock_statement_lots
                WHERE item_name = %s AND outlet_name = %s
                ORDER BY posted_at DESC, id DESC
            """, (item_name, outlet_name))
            existing_lots = cursor.fetchall()

            remaining_to_restore = total_qty

            for lot in existing_lots:
                if remaining_to_restore <= 0.001:
                    break

                lot_id   = lot['id']
                lot_qty  = float(lot['qty'])
                lot_rate = float(lot['rate'])

                # Find matching lot slice from detail rows by rate
                matched_restore_qty = 0
                for dqty, drate in lots:
                    if abs(drate - lot_rate) < 0.0001:
                        matched_restore_qty += dqty

                if matched_restore_qty <= 0:
                    continue

                restore_qty   = min(matched_restore_qty, remaining_to_restore)
                new_lot_qty   = round(lot_qty + restore_qty, 4)
                new_lot_total = round(new_lot_qty * lot_rate, 4)

                cursor.execute("""
                    UPDATE stock_statement_lots
                    SET qty = %s, total = %s
                    WHERE id = %s
                """, (new_lot_qty, new_lot_total, lot_id))

                remaining_to_restore -= restore_qty

            # If lot was fully consumed and no matching row exists, re-insert
            if remaining_to_restore > 0.001:
                cursor.execute("""
                    SELECT id FROM stock_statement
                    WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                """, (item_name, uom, outlet_name))
                ss_row = cursor.fetchone()
                ss_id  = ss_row['id'] if ss_row else None

                if ss_id:
                    restore_rate  = lots[-1][1]
                    restore_total = round(remaining_to_restore * restore_rate, 4)
                    cursor.execute("""
                        INSERT INTO stock_statement_lots
                            (stock_statement_id, item_name, outlet_name, qty, rate, total, posted_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (ss_id, item_name, outlet_name, remaining_to_restore, restore_rate, restore_total))

            # ── 3. Remove from item_current_level or production_item_current_level
            if costcenter == "Central Kitchen":
                for deducted_qty, lot_rate in reversed(lots):
                    cursor.execute("""
                        SELECT id, quantity
                        FROM production_item_current_level
                        WHERE itemname = %s AND outlet = %s AND costcenter = %s
                        AND ABS(rate - %s) < 0.0001
                        ORDER BY id DESC
                        LIMIT 1
                    """, (item_name, outlet_name, costcenter, lot_rate))
                    picl_row = cursor.fetchone()

                    if not picl_row:
                        restoration_errors.append({
                            "item": item_name,
                            "rate": lot_rate,
                            "error": "Matching row not found in production_item_current_level"
                        })
                        continue

                    picl_id      = picl_row['id']
                    picl_qty     = float(picl_row['quantity'])
                    new_picl_qty = round(picl_qty - deducted_qty, 4)

                    if new_picl_qty <= 0:
                        cursor.execute("""
                            DELETE FROM production_item_current_level WHERE id = %s
                        """, (picl_id,))
                    else:
                        cursor.execute("""
                            UPDATE production_item_current_level 
                            SET quantity = %s WHERE id = %s
                        """, (new_picl_qty, picl_id))

            else:
                for deducted_qty, lot_rate in reversed(lots):
                    cursor.execute("""
                        SELECT id, quantity
                        FROM item_current_level
                        WHERE itemname = %s AND outlet = %s AND costcenter = %s
                        AND ABS(rate - %s) < 0.0001
                        ORDER BY id DESC
                        LIMIT 1
                    """, (item_name, outlet_name, costcenter, lot_rate))
                    icl_row = cursor.fetchone()

                    if not icl_row:
                        restoration_errors.append({
                            "item": item_name,
                            "rate": lot_rate,
                            "error": "Matching row not found in item_current_level"
                        })
                        continue

                    icl_id      = icl_row['id']
                    icl_qty     = float(icl_row['quantity'])
                    new_icl_qty = round(icl_qty - deducted_qty, 4)

                    if new_icl_qty <= 0:
                        cursor.execute("DELETE FROM item_current_level WHERE id = %s", (icl_id,))
                    else:
                        cursor.execute("""
                            UPDATE item_current_level SET quantity = %s WHERE id = %s
                        """, (new_icl_qty, icl_id))

                # Reverse production_consumption_tracker for Finished Goods
                cursor.execute("""
                    SELECT GroupName FROM stock_statement
                    WHERE ItemName = %s AND OutletName = %s
""", (item_name, outlet_name))
                ss_group = cursor.fetchone()

                if ss_group and ss_group['GroupName'] == 'Finished Goods':
                    cursor.execute("""
                        DELETE FROM production_consumption_tracker
                        WHERE recipe_name = %s AND outlet = %s
                        ORDER BY id DESC
                        LIMIT 1
                    """, (item_name, outlet_name))

            restoration_details.append({
                "item": item_name,
                "uom": uom,
                "total_qty_restored": total_qty,
                "fifo_total_restored": fifo_total,
                "lots_restored": [{"qty": q, "rate": r} for q, r in lots],
                "stock_statement": {
                    "previous_level": current_level,
                    "new_level": restored_level,
                    "previous_total": current_total,
                    "new_total": restored_total
                }
            })

        if restoration_errors:
            mydb.rollback()
            return jsonify({
                "status": "error",
                "message": "Failed to fully reverse the stock transfer. Deletion cancelled.",
                "errors": restoration_errors,
                "restoration_details": restoration_details
            }), 400

        # ── 4. Delete detail and header rows ──────────────────────────────────
        cursor.execute("DELETE FROM intblstorereqdetails WHERE StoreReqID = %s", (store_req_id,))
        cursor.execute("DELETE FROM intblstorerequisition WHERE StoreReqID = %s", (store_req_id,))

        mydb.commit()

        return jsonify({
            "status": "success",
            "message": f"Store requisition {store_req_id} deleted and all stock reversed successfully.",
            "restoration_details": restoration_details
        }), 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        if mydb and mydb.is_connected():
            mydb.close()