
from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth

load_dotenv()

app_file241 = Blueprint('app_file241', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )

from root.flask_routes.menuengineering.received.utils_fnb import calculate_other_cost

@app_file241.route("/fnb-costing-reports-production", methods=["POST"])
@cross_origin()
def get_fnb_costing_reports_production():
    try:
        data = request.get_json()
        token = data.get("token")
        outlet = data.get("outlet")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        if not outlet:
            return jsonify({"error": "Missing required parameter: outlet"}), 400
        if not start_date or not end_date:
            return jsonify({"error": "Missing required parameters: start_date or end_date"}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True)

        # Query for fnb costing details
        query = """
            SELECT *
            FROM production_tblfnbcostingdetails
            WHERE outlet_name = %s
              AND from_date = %s
              AND to_date = %s
            ORDER BY from_date DESC, to_date DESC
        """
        cursor.execute(query, (outlet, start_date, end_date))
        fnb_results = cursor.fetchall()

        # # Process sales data once for Food and once for Beverage
        # sales_data = {}
        
        # for report_type in ["Food", "Beverage"]:
        #     # Get all orders with their discount percentages and complimentary status
        #     cursor.execute("""
        #         SELECT 
        #             idtblorderHistory as order_id,
        #             Total,
        #             VAT,
        #             DiscountAmt,
        #             bill_no,
        #             PaymentMode,
        #             CASE 
        #                 WHEN (Total - VAT) > 0 THEN (DiscountAmt / (Total - VAT)) * 100 
        #                 ELSE 0 
        #             END AS discount_percent
        #         FROM tblorderhistory
        #         WHERE Outlet_Name = %s 
        #             AND Date BETWEEN %s AND %s
        #             AND Total > 0
        #     """, (outlet, start_date, end_date))
            
        #     orders = cursor.fetchall()
            
        #     # Initialize sales tracking variables
        #     gross_sale = 0.0
        #     gross_cost = 0.0
        #     total_discount = 0.0
        #     total_complementary = 0.0
        #     items_sold_dict = {}
            
        #     # Process each order
        #     for order in orders:
        #         order_id = order['order_id']
        #         discount_percent = float(order['discount_percent'] or 0)
        #         is_complimentary = order['bill_no'] == '' and order['PaymentMode'] in ['Complimentary', 'Non Chargeable']
                
        #         # Get order details (items)
        #         cursor.execute("""
        #             SELECT 
        #                 ItemName,
        #                 ItemType,
        #                 Total,
        #                 count,
        #                 discountExempt
        #             FROM tblorder_detailshistory
        #             WHERE order_ID = %s
        #         """, (order_id,))
                
        #         items = cursor.fetchall()
                
        #         for item in items:
        #             item_type = item['ItemType']
                    
        #             # Only process items matching the report_type
        #             if item_type != report_type:
        #                 continue
                    
        #             item_name = item['ItemName']
        #             # Convert to float to handle Decimal and other numeric types
        #             item_total = float(item['Total'] or 0)
        #             item_count = float(item['count'] or 1)
                    
        #             # Get recipe cost
        #             cursor.execute("""
        #                 SELECT costprice
        #                 FROM recipe
        #                 WHERE name = %s AND outlet = %s
        #                 LIMIT 1
        #             """, (item_name, outlet))
                    
        #             recipe = cursor.fetchone()
        #             # Convert costprice to float and multiply with item_count
        #             recipe_cost = float(recipe['costprice'] or 0) if recipe else 0
        #             item_cost = recipe_cost * item_count
                    
        #             # Add to gross totals
        #             gross_sale += item_total
        #             gross_cost += item_cost
                    
        #             # Handle complimentary
        #             if is_complimentary:
        #                 total_complementary += item_total
                    
        #             # Handle discount (if not discount exempt)
        #             if discount_percent > 0 and item.get('discountExempt') != 'Yes':
        #                 discount_amount = item_total * (discount_percent / 100)
        #                 total_discount += discount_amount
                    
        #             # Aggregate items sold
        #             if item_name not in items_sold_dict:
        #                 items_sold_dict[item_name] = {
        #                     "item_name": item_name,
        #                     "quantity": 0,
        #                     "total_sale": 0,
        #                     "total_cost": 0,
        #                     "unit_cost": recipe_cost
        #                 }
                    
        #             items_sold_dict[item_name]["quantity"] += item_count
        #             items_sold_dict[item_name]["total_sale"] += item_total
        #             items_sold_dict[item_name]["total_cost"] += item_cost
            
        #     # Calculate percentages
        #     gross_cost_percent = round((gross_cost / gross_sale) * 100, 2) if gross_sale > 0 else 0
        #     net_sale = gross_sale - total_discount - total_complementary
        #     net_cost_percent = round((gross_cost / net_sale) * 100, 2) if net_sale > 0 else 0
            
        #     # Put items_sold inside sales_summary
        #     sales_data[report_type] = {
        #         "sales_summary": {
        #             "gross_sale": round(gross_sale, 2),
        #             "gross_cost": round(gross_cost, 2),
        #             "gross_cost_percent": gross_cost_percent,
        #             "discount": round(total_discount, 2),
        #             "complementary": round(total_complementary, 2),
        #             "net_sale": round(net_sale, 2),
        #             "net_cost_percent": net_cost_percent,
        #             "items_sold": list(items_sold_dict.values())
        #         }
        #     }

        # Process store requisition items (deployed items) for Food and Beverage
        store_requisition_data = {}
        
        for report_type in ["Food", "Beverage"]:
            # Query to get items deployed from store requisition
            cursor.execute("""
                SELECT 
                    d.ItemName,
                    d.GroupName,
                    d.BrandName,
                    d.UOM,
                    d.Rate,
                    d.Amount,
                    d.itemtype,
                    (d.Amount * d.Rate) AS total_amount
                FROM intblstorereqdetails d
                INNER JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
                WHERE r.Outlet = %s
                    AND DATE(r.Date) BETWEEN %s AND %s
                    AND d.itemtype = %s
                ORDER BY d.ItemName
            """, (outlet, start_date, end_date, report_type))
            
            requisition_items = cursor.fetchall()
            
            # Group by item name and calculate average rate
            items_dict = {}
            
            for item in requisition_items:
                item_name = item['ItemName']
                
                if item_name not in items_dict:
                    items_dict[item_name] = {
                        "item_name": item_name,
                        "group_name": item['GroupName'],
                        "brand_name": item['BrandName'],
                        "uom": item['UOM'],
                        "item_type": item['itemtype'],
                        "total_quantity": 0.0,
                        "total_amount": 0.0,
                        "entries": []  # Store individual entries for average calculation
                    }
                
                # Convert to float to handle Decimal
                quantity = float(item['Amount'] or 0)
                total_amount = float(item['total_amount'] or 0)
                
                # Add to totals
                items_dict[item_name]["total_quantity"] += quantity
                items_dict[item_name]["total_amount"] += total_amount
                items_dict[item_name]["entries"].append({
                    "quantity": quantity,
                    "rate": float(item['Rate'] or 0),
                    "total": total_amount
                })
            
            # Calculate average rate and prepare final list
            deployed_items_list = []
            for item_name, item_data in items_dict.items():
                avg_rate = item_data["total_amount"] / item_data["total_quantity"] if item_data["total_quantity"] > 0 else 0
                
                deployed_items_list.append({
                    "item_name": item_data["item_name"],
                    "group_name": item_data["group_name"],
                    "brand_name": item_data["brand_name"],
                    "uom": item_data["uom"],
                    "item_type": item_data["item_type"],
                    "total_quantity": round(item_data["total_quantity"], 3),
                    "average_rate": round(avg_rate, 2),
                    "total_amount": round(item_data["total_amount"], 2),
                    "transaction_count": len(item_data["entries"])
                })
            
            store_requisition_data[report_type] = {
                "deployed_items": deployed_items_list,
                "summary": {
                    "total_items_deployed": len(deployed_items_list),
                    "total_quantity": round(sum(item["total_quantity"] for item in deployed_items_list), 3),
                    "total_value": round(sum(item["total_amount"] for item in deployed_items_list), 2)
                }
            }

        # For each fnb record, fetch the corresponding inventory snapshot data
        for fnb_record in fnb_results:
            report_for = fnb_record.get("report_for")
            fnb_from_date = fnb_record.get("from_date")
            fnb_to_date = fnb_record.get("to_date")
            
            # Initialize inventory snapshot fields
            fnb_record["inventory_snapshot"] = None
            fnb_record["items_actual_costing"] = []
            fnb_record["sales_summary"] = {}
            fnb_record["purchase_items"] = {}  # New field for deployed items
            
            # if report_for == "Food":
            #     master_table = "inventory_snapshot_master_food"
            #     items_table = "production_inventorycalculation_items_food"
            # elif report_for == "Beverage":
            #     master_table = "inventory_snapshot_master_beverage"
            #     items_table = "production_inventorycalculation_items_beverage"
            # else:
            #     continue

            master_table = "production_inventorycalculation"
            items_table = "production_inventorycalculation_items"

            # # Add sales data from pre-processed data
            # if report_for in sales_data:
            #     fnb_record["sales_summary"] = sales_data[report_for]["sales_summary"]
            
            # Add deployed items data from store requisition
            if report_for in store_requisition_data:
                fnb_record["purchase_items"] = store_requisition_data[report_for]
            
            # Query the master snapshot table
            master_query = f"""
                SELECT *
                FROM {master_table}
                WHERE outlet_name = %s
                  AND start_date = %s
                  AND end_date = %s AND is_opening = False
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(master_query, (outlet, fnb_from_date, fnb_to_date))
            master_result = cursor.fetchone()
            
            if master_result:
                # Convert Decimal fields to float for JSON serialization
                for key, value in master_result.items():
                    if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                        master_result[key] = float(value)
                
                fnb_record["inventory_snapshot"] = master_result
                calculation_id = master_result.get("id")
                
                # Query the items table for this snapshot
                items_query = f"""
                    SELECT *
                    FROM {items_table}
                    WHERE calculation_id = %s
                    ORDER BY item_name
                """
                cursor.execute(items_query, (calculation_id,))
                items_results = cursor.fetchall()
                
                # Convert Decimal fields to float for each item
                for item in items_results:
                    for key, value in item.items():
                        if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                            item[key] = float(value)
                
                fnb_record["items_actual_costing"] = items_results

        other_cost_food = calculate_other_cost(outlet, start_date, end_date, "Food")
        other_cost_beverage = calculate_other_cost(outlet, start_date, end_date, "Beverage")


        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "outlet": outlet,
            "start_date": start_date,
            "end_date": end_date,
            "fnb_costing_reports": fnb_results,
            "other_cost_food" : other_cost_food,
            "other_cost_beverage" : other_cost_beverage


        }), 200

    except Exception as e:
        if 'mydb' in locals():
            mydb.rollback()
            mydb.close()
        return jsonify({"error": str(e)}), 400
    



@app_file241.route("/food-and-costing-analysis-production", methods=["POST"])
@cross_origin()
def receive_snapshot_details_production():
    try:
        data = request.get_json()
        token = data.get("token")
        calculation_id = data.get("calculation_id")

        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        if not calculation_id:
            return jsonify({"error": "Missing required parameter: calculation_id"}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True)

        # Snapshot info
        cursor.execute("""
            SELECT outlet_name, start_date, end_date 
            FROM production_inventorycalculation 
            WHERE id = %s
        """, (calculation_id,))
        snapshot = cursor.fetchone()
        if not snapshot:
            return jsonify({"error": "Snapshot not found"}), 404

        outlet_name = snapshot['outlet_name']
        start_date = snapshot['start_date']
        end_date = snapshot['end_date']

        # Get all inventory items
        cursor.execute("""
            SELECT 
                item_name, item_type, group_name, uom, new_uom,
                opening_count, total_received, total_consumed,
                closing_balance, wastage_count, physical_count, discrepancy_count,
                rate, received_cost, consumption_cost, wastage_cost, actual_consumption_cost,
                opening_cost, physical_cost,
                (closing_balance * rate) AS closing_value, discrepancy_cost
            FROM production_inventorycalculation_items
            WHERE calculation_id = %s
            ORDER BY item_name ASC
        """, (calculation_id,))
        inventory_items = cursor.fetchall()

        # Summary of cost fields
        cursor.execute("""
            SELECT 
                SUM(opening_cost) AS total_opening_cost,
                SUM(physical_cost) AS total_physical_cost,
                SUM(wastage_cost) AS total_wastage_cost,
                SUM(actual_consumption_cost) AS total_actual_consumption_cost
            FROM production_inventorycalculation_items
            WHERE calculation_id = %s
        """, (calculation_id,))
        summary = cursor.fetchone()

        # STEP 1: Get sales data from store requisition for Finished Goods
        def to_float(value):
            if value is None:
                return 0.0
            return float(value)
        
        # # Get detailed sales items with their costs using conversion factor
        # sales_items_query = """
        #     SELECT 
        #         srd.ItemName,
        #         srd.GroupName,
        #         COALESCE(SUM(srd.Amount), 0) AS quantity,
        #         COALESCE(SUM(srd.Amount * srd.Rate), 0) AS total_sale,
        #         COALESCE(
        #             SUM(
        #                 CASE 
        #                     WHEN r.costprice IS NOT NULL AND cf.factor IS NOT NULL AND cf.factor > 0 
        #                     THEN (r.costprice / cf.factor) * srd.Amount
        #                     ELSE 0
        #                 END
        #             ), 0
        #         ) AS total_cost,
        #         CASE 
        #             WHEN r.costprice IS NOT NULL AND cf.factor IS NOT NULL AND cf.factor > 0 
        #             THEN r.costprice / cf.factor
        #             ELSE 0
        #         END AS unit_cost
        #     FROM intblstorereqdetails srd
        #     JOIN intblstorerequisition sr 
        #         ON srd.StoreReqID = sr.idintblStoreRequisition
        #     LEFT JOIN stock_statement ss 
        #         ON ss.ItemName = srd.ItemName 
        #         AND ss.OutletName = sr.Outlet
        #     LEFT JOIN conversionfactor cf 
        #         ON cf.production_item_id = ss.id 
        #         AND cf.outlet = sr.Outlet
        #     LEFT JOIN recipe r 
        #         ON r.id = cf.production_recipe_id 
        #         AND r.outlet = sr.Outlet
        #     WHERE sr.Outlet = %s
        #         AND DATE(sr.Date) BETWEEN %s AND %s
        #         AND srd.GroupName = 'Finished Goods'
        #     GROUP BY srd.ItemName, srd.GroupName, unit_cost
        # """

        # Get detailed sales items with their costs using conversion factor
        sales_items_query = """
            SELECT 
                pi.itemname AS ItemName,
                ss.GroupName,
                COALESCE(SUM(pi.quantity), 0) AS quantity,
                COALESCE(SUM(pi.quantity * pi.rate), 0) AS total_sale,
                COALESCE(
                    SUM(
                        CASE 
                            WHEN r.costprice IS NOT NULL AND cf.factor IS NOT NULL AND cf.factor > 0 
                            THEN (r.costprice / cf.factor) * pi.quantity
                            ELSE 0
                        END
                    ), 0
                ) AS total_cost,
                CASE 
                    WHEN r.costprice IS NOT NULL AND cf.factor IS NOT NULL AND cf.factor > 0 
                    THEN r.costprice / cf.factor
                    ELSE 0
                END AS unit_cost
            FROM centralkitchen_productionitems pi
            JOIN centralkitchen_production p 
                ON p.id = pi.production_id
            LEFT JOIN stock_statement ss 
                ON ss.ItemName = pi.itemname COLLATE utf8mb4_general_ci
                AND ss.OutletName = p.outlet COLLATE utf8mb4_general_ci
                AND ss.GroupName = 'Finished Goods'
            LEFT JOIN conversionfactor cf 
                ON cf.production_item_id = ss.id 
                AND cf.outlet = p.outlet COLLATE utf8mb4_general_ci
            LEFT JOIN recipe r 
                ON r.id = cf.production_recipe_id 
                AND r.outlet = p.outlet COLLATE utf8mb4_general_ci
            WHERE p.outlet = %s
                AND DATE(p.production_date) BETWEEN %s AND %s
                AND ss.GroupName = 'Finished Goods'
            GROUP BY pi.itemname, ss.GroupName, unit_cost
        """
        
        cursor.execute(sales_items_query, (outlet_name, start_date, end_date))
        sales_items = cursor.fetchall()
        
        # Format sales items for response
        formatted_sales_items = []
        total_gross_sale = 0.0
        total_gross_cost = 0.0
        
        for item in sales_items:
            quantity = to_float(item['quantity'])
            total_sale = to_float(item['total_sale'])
            total_cost = to_float(item['total_cost'])
            unit_cost = to_float(item['unit_cost'])
            
            formatted_sales_items.append({
                "item_name": item['ItemName'],
                "quantity": round(quantity, 2),
                "total_sale": round(total_sale, 2),
                "total_cost": round(total_cost, 2),
                "unit_cost": round(unit_cost, 2)
            })
            
            total_gross_sale += total_sale
            total_gross_cost += total_cost
        
        # STEP 2: Get discount and complementary data from orders
        cursor.execute("""
            SELECT 
                idtblorderHistory as order_id,
                Total,
                VAT,
                DiscountAmt,
                bill_no,
                PaymentMode,
                (DiscountAmt / (Total - VAT)) * 100 AS discount_percent
            FROM tblorderhistory
            WHERE Outlet_Name = %s 
                AND Date BETWEEN %s AND %s
                AND Total > 0
                AND (Total - VAT) > 0
        """, (outlet_name, start_date, end_date))
        
        orders = cursor.fetchall()
        
        total_discount = 0.0
        total_complementary = 0.0
        
        # Process each order for discount and complementary
        for order in orders:
            order_id = order['order_id']
            discount_percent = order['discount_percent'] if order['discount_percent'] else 0
            is_complimentary = order['bill_no'] == '' and order['PaymentMode'] in ['Complimentary', 'Non Chargeable']
            
            # Get order details (items)
            cursor.execute("""
                SELECT 
                    ItemName,
                    Total,
                    discountExempt
                FROM tblorder_detailshistory
                WHERE order_ID = %s
            """, (order_id,))
            
            items = cursor.fetchall()
            
            for item in items:
                item_total = float(item['Total'] or 0)
                
                # Handle complimentary
                if is_complimentary:
                    total_complementary += item_total
                
                # Handle discount (if not discount exempt)
                if discount_percent > 0 and item.get('discountExempt') != 'Yes':
                    discount_amount = float(item_total) * (float(discount_percent) / 100)
                    total_discount += discount_amount
        
        # Calculate percentages
        gross_cost_percent = round((total_gross_cost / total_gross_sale) * 100, 2) if total_gross_sale else 0
        net_sale = total_gross_sale - total_discount - total_complementary
        net_cost_percent = round((total_gross_cost / net_sale) * 100, 2) if net_sale else 0

        # STEP 3: Get purchase/received items from store requisition for Central Kitchen
        purchase_items_query = """
            SELECT 
                d.ItemName AS item_name,
                COALESCE(SUM(d.Amount), 0) AS quantity,
                d.UOM AS uom,
                AVG(d.Rate) AS avg_rate,
                COALESCE(SUM(d.Amount * d.Rate), 0) AS total
            FROM intblstorereqdetails d
            JOIN intblstorerequisition r ON d.StoreReqID = r.idintblStoreRequisition
            WHERE r.Outlet = %s 
                AND r.CostCenter = 'Central Kitchen'
                AND DATE(r.Date) BETWEEN %s AND %s
            GROUP BY d.ItemName, d.UOM
            ORDER BY d.ItemName ASC
        """
        
        cursor.execute(purchase_items_query, (outlet_name, start_date, end_date))
        purchase_items = cursor.fetchall()
        
        # Format purchase items for response
        formatted_purchase_items = []
        total_purchase = 0.0
        
        for item in purchase_items:
            quantity = to_float(item['quantity'])
            total = to_float(item['total'])
            avg_rate = to_float(item['avg_rate'])
            
            formatted_purchase_items.append({
                "item_name": item['item_name'],
                "quantity": round(quantity, 2),
                "uom": item['uom'],
                "rate": round(avg_rate, 2),
                "total": round(total, 2)
            })
            
            total_purchase += total

        cursor.close()
        mydb.close()

        # Return single group of data without item type separation
        return jsonify({
            "status": "success",
            "calculation_id": calculation_id,
            "outlet_name": outlet_name,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "summary": summary,
            "items_actual_food_costing": inventory_items,
            "sales_summary": {
                "gross_sale": round(total_gross_sale, 2),
                "gross_cost": round(total_gross_cost, 2),
                "gross_cost_percent": gross_cost_percent,
                "discount": round(total_discount, 2),
                "complementary": round(total_complementary, 2),
                "net_sale": round(net_sale, 2),
                "net_cost_percent": net_cost_percent,
                "items_sold": formatted_sales_items
            },
            "purchase_summary": {
                "total_purchase": round(total_purchase, 2),
                "items": formatted_purchase_items
            }
        }), 200

    except Exception as e:
        if 'mydb' in locals():
            mydb.rollback()
            mydb.close()
        return jsonify({"error": str(e)}), 400