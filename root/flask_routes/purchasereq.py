from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file12 = Blueprint('app_file12', __name__)

from datetime import datetime

from .utils import post_purchases_and_create_journal


@app_file12.route("/req", methods=["POST"])
@cross_origin()
def purchasereqPost():
    try:
        today_str = datetime.today().strftime('%Y-%m-%d')
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute("USE {};".format(os.getenv('database')))

        data = request.get_json()
        posted_data = data
        purchase_from = data.get("purchase_from", "c_app")
        outlet_name = data.get("Outlet_Name")

        if purchase_from == "web":
            cursor.execute("""
                SELECT MAX(Outlet_PurchaseReqID) FROM intbl_purchaserequisition 
                WHERE Outlet_Name = %s AND purchase_from = 'web'
            """, (outlet_name,))
            max_purchase_id = cursor.fetchone()[0]
            purchase_requisition_id = (max_purchase_id + 1) if max_purchase_id else 1

            cursor.execute("""
                SELECT MAX(GRN) FROM intbl_purchaserequisition 
                WHERE Outlet_Name = %s AND purchase_from = 'web'
            """, (outlet_name,))
            max_grn = cursor.fetchone()[0]
            grn = (max_grn + 1) if max_grn else 1
        else:
            purchase_requisition_id = data["PurchaseRequistionID"]
            grn = data["GRN"]

        sql = """
        INSERT INTO `intbl_purchaserequisition` 
        (Outlet_PurchaseReqID, RequisitionType, Date, TotalAmount, TaxAmount, Company_Name, 
         State, ReceivedDate, ServerReceivedDate, purchaseBillNumber, DiscountAmount, 
         Outlet_Name, GRN, purchase_id_ocular, purchase_from, company_pan, payment_mode)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        sql2 = """
        INSERT INTO `intbl_purchaserequisition_contract`    
        (ItemID, UnitsOrdered, PurchaseReqID, Rate, Name, BrandName, Code, UOM, 
         StockType, Department, GroupName, ExpDate, Status, Taxable) 
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            purchase_requisition_id,
            data["RequisitionType"],
            data["Date"],
            data["TotalAmount"],
            data["TaxAmount"],
            data.get("Company_Name", None),
            data["State"],
            data["ReceivedDate"],
            today_str,
            data["purchaseBillNumber"],
            data["DiscountAmount"],
            data["Outlet_Name"],
            grn,
            data.get("purchase_id_ocular", None),
            purchase_from,
            data.get("company_pan", None),
            data.get("payment_mode", None)
        ))

        purchase_req_id = cursor.lastrowid
        state = data.get("State", "")
        current_level_entries = []

        for item in data["RequisitionDetailsList"]:
            try:
                cursor.execute(sql2, (
                    item["ItemID"],
                    item["UnitsOrdered"],
                    purchase_req_id,
                    item["Rate"],
                    item["Name"],
                    item["BrandName"],
                    item["Code"],
                    item["UOM"],
                    item["StockType"],
                    item["Department"],
                    item["GroupName"],
                    item["ExpDate"],
                    item["Status"],
                    item["Taxable"],
                ))

                if state == "Received":
                    qty   = float(item["UnitsOrdered"])
                    rate  = float(item["Rate"])
                    total = round(qty * rate, 4)

                    # ── stock_current_level (batch insert after loop) ──────────
                    current_level_entries.append((
                        item["Name"],
                        data["Outlet_Name"],
                        item["UOM"],
                        qty,
                        item.get("ExpDate") if item.get("ExpDate") else None,
                        rate,
                        total,
                        purchase_req_id
                    ))

                    # ── stock_statement: update or insert, capture id ──────────
                    cursor.execute("""
                        SELECT id, CurrentLevel 
                        FROM stock_statement 
                        WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                    """, (item["Name"], item["UOM"], data["Outlet_Name"]))

                    existing = cursor.fetchone()

                    if existing:
                        ss_id = existing[0]  # actual row id

                        new_level = existing[1] + qty
                        cursor.execute("""
                            UPDATE stock_statement
                            SET CurrentLevel = CurrentLevel + %s, Rate = %s, Total = %s
                            WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                        """, (qty, rate,new_level*rate, item["Name"], item["UOM"], data["Outlet_Name"]))


                        print("new_level", new_level)

                        print("level is updated")
                    else:
                        cursor.execute("""
                            INSERT INTO stock_statement 
                            (GroupName, ItemName, BrandName, UOM, CurrentLevel, Rate, OutletName)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            item["GroupName"],
                            item["Name"],
                            item["BrandName"],
                            item["UOM"],
                            qty,
                            rate,
                            data["Outlet_Name"]
                        ))
                        ss_id = cursor.lastrowid

                    # ── stock_statement_lots: always APPEND, never wipe ────────
                    cursor.execute("""
                        INSERT INTO stock_statement_lots 
                            (stock_statement_id, item_name, outlet_name, qty, rate, total, posted_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (ss_id, item["Name"], data["Outlet_Name"], qty, rate, total, today_str))

                

            except Exception as e:
                return {"error": str(e)}, 400
            
        if state == "Received":
            data["purchase_id"] = purchase_req_id
            post_purchases_and_create_journal(posted_data)

        mydb.commit()
        mydb.close()

        if purchase_from == "web":
            return {
                "success": "Data posted successfully.",
                "purchase_requisition_id": purchase_req_id,
                "grn": grn
            }, 200
        else:
            return {"success": "Data posted successfully."}, 200

    except Exception as error:
        return {'error': str(error)}, 400

@app_file12.route("/getOrderedPurchases", methods=["POST"])
@cross_origin()
def get_ordered_purchases():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True)
        
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        
        # Get data from request body
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Get filter parameters from body
        outlet_name = data.get('outlet_name')
        company_name = data.get('company_name')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        grn = data.get('grn')
        bill_number = data.get('bill_number')
        purchase_id = data.get('purchase_id')
        state = data.get('state')  # Allow filtering by specific state (Ordered/Received)
        purchase_from = data.get('purchase_from')  # New filter: 'web' or 'all'
        page = data.get('page', 1)
        limit = data.get('limit', 10)
        
        if not outlet_name:
            return jsonify({"error": "outlet_name is required"}), 400
        
        # Calculate offset for pagination
        offset = (int(page) - 1) * int(limit)
        
        # Base conditions
        conditions = ["State IN ('Ordered','Received')", "Outlet_Name = %s"]
        params = [outlet_name]
        
        # Override state filter if specific state is provided
        if state and state in ['Ordered', 'Received']:
            conditions = [f"State = %s", "Outlet_Name = %s"]
            params = [state, outlet_name]
        
        # Add purchase_from filter
        if purchase_from and purchase_from.lower() == 'web':
            conditions.append("purchase_from = 'web'")
        # If purchase_from is 'all' or not provided, don't add the filter (get all purchases)
        
        # Add optional filters
        if company_name:
            conditions.append("Company_Name = %s")
            params.append(company_name)
        
        if from_date:
            conditions.append("Date >= %s")
            params.append(from_date)
        
        if to_date:
            conditions.append("Date <= %s")
            params.append(to_date)
        
        if grn:
            conditions.append("GRN = %s")
            params.append(grn)
        
        if bill_number:
            conditions.append("purchaseBillNumber = %s")
            params.append(bill_number)
        
        if purchase_id:
            conditions.append("id = %s")
            params.append(purchase_id)
        
        # Build WHERE clause
        where_clause = " AND ".join(conditions)
        
        # Query for total count
        count_sql = f"""
        SELECT COUNT(*) as total 
        FROM intbl_purchaserequisition 
        WHERE {where_clause}
        """
        
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()['total']
        
        # Build main query with same conditions
        sql = f"""
        SELECT *
        FROM intbl_purchaserequisition 
        WHERE {where_clause}
        ORDER BY Date DESC 
        LIMIT %s OFFSET %s
        """
        
        query_params = params + [int(limit), offset]
        
        cursor.execute(sql, query_params)
        purchases = cursor.fetchall()
        
        # Convert date objects to string for JSON serialization
        for purchase in purchases:
            if 'Date' in purchase and purchase['Date']:
                purchase['Date'] = purchase['Date'].strftime('%Y-%m-%d')
        
        # Get purchase details (items) for each purchase
        for purchase in purchases:
            items_sql = """
            SELECT 
                *
            FROM intbl_purchaserequisition_contract
            WHERE PurchaseReqID = %s
            """
            cursor.execute(items_sql, (purchase['IDIntbl_PurchaseRequisition'],))
            items = cursor.fetchall()
            
            # Convert any decimal/float values and date fields in items
            for item in items:
                if 'ItemPrice' in item and item['ItemPrice']:
                    item['ItemPrice'] = float(item['ItemPrice'])
                if 'UnitsOrdered' in item and item['UnitsOrdered']:
                    item['UnitsOrdered'] = float(item['UnitsOrdered'])
                if 'UnitsReceived' in item and item['UnitsReceived']:
                    item['UnitsReceived'] = float(item['UnitsReceived'])
            
            purchase['items'] = items
            
            # Add summary calculations
            purchase['total_items_count'] = len(items)
            purchase['total_units_ordered'] = sum(float(item.get('UnitsOrdered', 0)) for item in items) if items else 0
            purchase['total_units_received'] = sum(float(item.get('UnitsReceived', 0)) for item in items) if items else 0
        
        mydb.close()
        
        # Prepare response with applied filters
        applied_filters = {
            "state": state if state else "Ordered/Received",
            "purchase_from": purchase_from if purchase_from else "all",
            "company_name": company_name,
            "from_date": from_date,
            "to_date": to_date,
            "grn": grn,
            "bill_number": bill_number,
            "purchase_id": purchase_id
        }
        
        # Remove None values from applied_filters
        applied_filters = {k: v for k, v in applied_filters.items() if v is not None}
        
        return jsonify({
            "success": True,
            "outlet_name": outlet_name,
            "filters_applied": applied_filters,
            "pagination": {
                "current_page": int(page),
                "limit": int(limit),
                "total_count": total_count,
                "total_pages": (total_count + int(limit) - 1) // int(limit) if total_count > 0 else 0
            },
            "count": len(purchases),
            "purchases": purchases
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400