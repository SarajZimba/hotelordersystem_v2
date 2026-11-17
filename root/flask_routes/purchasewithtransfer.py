# new one





from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file228 = Blueprint('app_file228', __name__)

from datetime import datetime

@app_file228.route("/purchase_with_transfer", methods=["POST"])
@cross_origin()
def create_purchase_and_transfer():
    mydb = None
    cursor = None
    
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
        
        stock_transfers_data = data.pop("stocktransfers", None)
        purchase_id_to_delete = data.pop("purchase_id_to_delete", None)
        outlet_name = data.get("Outlet_Name")
        
        # Backward compatibility: singular "stocktransfer" → array
        if stock_transfers_data is None and "stocktransfer" in data:
            single_transfer = data.pop("stocktransfer", None)
            if single_transfer:
                stock_transfers_data = [single_transfer]
        
        # ==================== VALIDATION: purchase_id_to_delete ====================
        if purchase_id_to_delete:
            cursor.execute("""
                SELECT State, Outlet_PurchaseReqID 
                FROM ordered_purchase 
                WHERE IDOrdered_Purchase = %s
            """, (purchase_id_to_delete,))
            
            existing_purchase = cursor.fetchone()
            
            if not existing_purchase:
                raise Exception(f"Purchase with ID {purchase_id_to_delete} not found")
            if existing_purchase[0] != "Ordered":
                raise Exception(
                    f"Purchase with ID {purchase_id_to_delete} is in '{existing_purchase[0]}' state, "
                    f"not 'Ordered'. Cannot delete."
                )
            print(f"Will delete purchase ID {purchase_id_to_delete} (State: {existing_purchase[0]}) after successful creation")
        
        # ==================== PART 1: CREATE PURCHASE REQUISITION ====================
        purchase_from = data.get("purchase_from", "c_app")
        
        if purchase_from == "web":
            cursor.execute("SELECT MAX(Outlet_PurchaseReqID) FROM intbl_purchaserequisition where Outlet_Name = %s", (outlet_name,))
            max_purchase_id = cursor.fetchone()[0]
            purchase_requisition_id = (max_purchase_id + 1) if max_purchase_id else 1
            
            cursor.execute("SELECT MAX(GRN) FROM intbl_purchaserequisition where Outlet_Name = %s", (outlet_name,))
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
        
        sql2 = """
        INSERT INTO `intbl_purchaserequisition_contract`    
        (ItemID, UnitsOrdered, PurchaseReqID, Rate, Name, BrandName, Code, UOM, 
         StockType, Department, GroupName, ExpDate, Status, Taxable) 
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for item in data["RequisitionDetailsList"]:
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

                # ── stock_current_level (batch insert after loop) ─────────────
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
                
                # ── stock_statement: update or insert, capture id ─────────────
                cursor.execute("""
                    SELECT id, CurrentLevel 
                    FROM stock_statement 
                    WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                """, (item["Name"], item["UOM"], data["Outlet_Name"]))
                
                existing = cursor.fetchone()
                
                if existing:
                    ss_id = existing[0]   # actual row id, not CurrentLevel
                    new_level = (existing[1] + qty)
                    cursor.execute("""
                        UPDATE stock_statement
                        SET CurrentLevel = CurrentLevel + %s, Rate = %s, Total = %s
                        WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                    """, (qty, rate, new_level*rate, item["Name"], item["UOM"], data["Outlet_Name"]))
                else:
                    cursor.execute("""
                        INSERT INTO stock_statement 
                        (GroupName, ItemName, BrandName, UOM, CurrentLevel, Rate, OutletName, Total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item["GroupName"],
                        item["Name"],
                        item["BrandName"],
                        item["UOM"],
                        qty,
                        rate,
                        data["Outlet_Name"],
                        new_level*rate
                    ))
                    ss_id = cursor.lastrowid

                # ── stock_statement_lots: always APPEND, never wipe ───────────
                cursor.execute("""
                    INSERT INTO stock_statement_lots 
                        (stock_statement_id, item_name, outlet_name, qty, rate, total, posted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (ss_id, item["Name"], data["Outlet_Name"], qty, rate, total, today_str))
        
        # Batch insert stock_current_level entries
        if current_level_entries:
            cursor.executemany("""
                INSERT INTO stock_current_level (name, outlet, units, qty, expiry_date, rate, total, purchase_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, current_level_entries)
        
        # ==================== PART 2: HANDLE MULTIPLE STOCK TRANSFERS ====================
        transfer_results = []
        
        if stock_transfers_data and isinstance(stock_transfers_data, list):

            # ── FIRST PASS: validate stock availability across ALL transfers ──
            validation_errors = []
            cumulative_deductions = {}  # key: (item_name, uom)
            
            for transfer_index, transfer in enumerate(stock_transfers_data):
                for item in transfer["ItemDetailsList"]:
                    key = (item["ItemName"], item["UOM"])
                    requested_qty = float(item["Amount"])
                    
                    if key not in cumulative_deductions:
                        cumulative_deductions[key] = {
                            "total_requested": 0,
                            "transfer_indices": []
                        }
                    cumulative_deductions[key]["total_requested"] += requested_qty
                    cumulative_deductions[key]["transfer_indices"].append(transfer_index)
            
            for (item_name, uom), deduction_info in cumulative_deductions.items():
                total_requested = deduction_info["total_requested"]
                
                # # Check stock_current_level
                # cursor.execute("""
                #     SELECT SUM(qty) 
                #     FROM stock_current_level 
                #     WHERE name = %s 
                #     AND qty > 0
                #     AND (expiry_date IS NULL OR expiry_date > CURDATE())
                # """, (item_name,))
                # result = cursor.fetchone()
                # total_available = float(result[0]) if result[0] else 0
                
                # if total_available < total_requested - 0.001:
                #     validation_errors.append(
                #         f"Insufficient stock for {item_name} in stock_current_level. "
                #         f"Available: {total_available:.2f}, Requested: {total_requested:.2f}"
                #     )
                
                # Check stock_statement (with UOM for precision)
                cursor.execute("""
                    SELECT CurrentLevel 
                    FROM stock_statement 
                    WHERE ItemName = %s AND UOM = %s AND OutletName = %s
                """, (item_name, uom, data["Outlet_Name"]))
                existing = cursor.fetchone()
                
                if not existing:
                    validation_errors.append(f"Stock statement missing for {item_name} ({uom})")
                elif float(existing[0]) < total_requested - 0.001:
                    validation_errors.append(
                        f"Insufficient stock in stock_statement for {item_name} ({uom}). "
                        f"Available: {float(existing[0]):.2f}, Requested: {total_requested:.2f}"
                    )
                
                # Check stock_statement_lots
                cursor.execute("""
                    SELECT SUM(qty)
                    FROM stock_statement_lots
                    WHERE item_name = %s AND outlet_name = %s AND qty > 0
                """, (item_name, data["Outlet_Name"]))
                lots_result = cursor.fetchone()
                lots_available = float(lots_result[0]) if lots_result[0] else 0
                
                if lots_available < total_requested - 0.001:
                    validation_errors.append(
                        f"Insufficient lots in stock_statement_lots for {item_name}. "
                        f"Available: {lots_available:.2f}, Requested: {total_requested:.2f}"
                    )
            
            if validation_errors:
                raise Exception("Stock validation failed: " + "; ".join(validation_errors))
            
            # ── SECOND PASS: all validations passed, process each transfer ────
            for transfer_idx, transfer in enumerate(stock_transfers_data):
                try:
                    transfer_result = process_single_transfer(
                        cursor, transfer, data, purchase_from, purchase_req_id
                    )
                    transfer_results.append(transfer_result)
                except Exception as transfer_error:
                    raise Exception(f"Stock transfer #{transfer_idx + 1} failed: {str(transfer_error)}")
        
        # ==================== PART 3: DELETE PREVIOUS ORDER-STATE PURCHASE ====================
        deleted_purchase_info = None
        
        if purchase_id_to_delete:
            try:
                cursor.execute("""
                    SELECT Outlet_PurchaseReqID, Outlet_Name, State 
                    FROM ordered_purchase 
                    WHERE IDOrdered_Purchase = %s
                """, (purchase_id_to_delete,))
                purchase_to_delete = cursor.fetchone()
                
                cursor.execute("""
                    DELETE FROM ordered_purchaseitems 
                    WHERE OrderedPurchaseID = %s
                """, (purchase_id_to_delete,))
                
                cursor.execute("""
                    DELETE FROM ordered_purchase 
                    WHERE IDOrdered_Purchase = %s AND State = 'Ordered'
                """, (purchase_id_to_delete,))
                
                if cursor.rowcount > 0:
                    deleted_purchase_info = {
                        "purchase_id": purchase_id_to_delete,
                        "outlet_purchase_req_id": purchase_to_delete[0] if purchase_to_delete else None,
                        "outlet_name": purchase_to_delete[1] if purchase_to_delete else None,
                        "state": "Ordered",
                        "status": "deleted"
                    }
                    print(f"Successfully deleted purchase ID {purchase_id_to_delete}")
                else:
                    raise Exception(
                        f"Failed to delete purchase ID {purchase_id_to_delete}. It may have been modified."
                    )
            except Exception as delete_error:
                raise Exception(f"Failed to delete previous purchase: {str(delete_error)}")
        
        # ==================== COMMIT EVERYTHING ====================
        mydb.commit()
        
        # ==================== RETURN RESPONSE ====================
        response_data = {
            "success": True,
            "purchase": {
                "purchase_requisition_id": purchase_req_id,
                "grn": grn if purchase_from == "web" else None,
                "outlet_purchase_req_id": purchase_requisition_id,
                "items_added": len(data["RequisitionDetailsList"])
            }
        }
        if transfer_results:
            response_data["stock_transfers"] = transfer_results
        if deleted_purchase_info:
            response_data["deleted_purchase"] = deleted_purchase_info
        
        return jsonify(response_data), 200
        
    except Exception as error:
        if mydb:
            mydb.rollback()
        return jsonify({'error': str(error)}), 400
        
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


def process_single_transfer(cursor, transfer, parent_data, purchase_from, purchase_req_id):
    """
    Process a single stock transfer transaction with FIFO deduction from stock_statement_lots.
    Transfer line items are split per lot (same item may appear multiple times with different rates).
    """
    try:
        date_obj = datetime.strptime(transfer['Date'], '%Y-%m-%dT%H:%M:%S')
        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        raise Exception(f"Invalid date format in stocktransfer: {str(e)}")

    outlet_name = parent_data["Outlet_Name"]

    if purchase_from == "web":
        cursor.execute("""
            SELECT MAX(CAST(OutletREQID AS UNSIGNED)) 
            FROM intblstorerequisition
            WHERE Outlet = %s
        """, (outlet_name,))
        max_id = cursor.fetchone()[0]
        outlet_req_id = int(max_id) + 1 if max_id else 1
    else:
        outlet_req_id = transfer["Outlet_Req_ID"]

    insert_storerequisitionSql = """
    INSERT INTO intblstorerequisition 
    (`Date`, `CostCenter`, `Outlet`, `OutletREQID`, `purchase_from`, `purchase_id`) 
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_storerequisitionSql, (
        formatted_date,
        transfer["CostCenter"],
        outlet_name,
        outlet_req_id,
        purchase_from,
        purchase_req_id
    ))

    store_req_id = cursor.lastrowid
    costcenter = transfer["CostCenter"]

    if costcenter == "Kitchen":
        item_type = "Food"
    elif costcenter == "Bar":
        item_type = "Beverage"
    else:
        item_type = costcenter

    for item in transfer["ItemDetailsList"]:
        item_name    = item["ItemName"]
        requested_qty = float(item["Amount"])

        # # ── 1. FIFO deduction from stock_current_level (expiry-first) ────────
        # cursor.execute("""
        #     SELECT id, qty, total, rate, expiry_date
        #     FROM stock_current_level 
        #     WHERE name = %s 
        #     AND qty > 0
        #     AND (expiry_date IS NULL OR expiry_date > CURDATE())
        #     ORDER BY expiry_date ASC, id ASC
        # """, (item_name,))
        # stock_batches = cursor.fetchall()

        # remaining_to_deduct = requested_qty

        # for batch in stock_batches:
        #     if remaining_to_deduct <= 0.001:
        #         break

        #     batch_id      = batch[0]
        #     current_qty   = float(batch[1])
        #     current_rate  = float(batch[3])

        #     if current_qty <= remaining_to_deduct + 0.001:
        #         deducted_qty       = current_qty
        #         new_qty            = 0
        #         new_total          = 0
        #         remaining_to_deduct -= current_qty
        #     else:
        #         deducted_qty       = remaining_to_deduct
        #         new_qty            = current_qty - remaining_to_deduct
        #         new_total          = round(new_qty * current_rate, 4)
        #         remaining_to_deduct = 0

        #     cursor.execute("""
        #         UPDATE stock_current_level 
        #         SET qty = %s, total = %s 
        #         WHERE id = %s AND qty >= %s
        #     """, (new_qty, new_total, batch_id, current_qty))

        #     if cursor.rowcount == 0:
        #         raise Exception(f"Concurrent update detected for batch {batch_id}")

        # ── 2. FIFO deduction from stock_statement_lots (posted_at-first) ────
        #    Fetch lots ordered oldest first for FIFO
        cursor.execute("""
            SELECT id, qty, rate
            FROM stock_statement_lots
            WHERE item_name = %s AND outlet_name = %s AND qty > 0
            ORDER BY id ASC
        """, (item_name, outlet_name))
        lots = cursor.fetchall()

        fifo_lines = []          # will hold (deducted_qty, lot_rate) per lot consumed
        remaining_lots = requested_qty

        for lot in lots:
            if remaining_lots <= 0.001:
                break

            lot_id       = lot[0]
            lot_qty      = float(lot[1])
            lot_rate     = float(lot[2])

            if lot_qty <= remaining_lots + 0.001:
                deducted_from_lot  = lot_qty
                new_lot_qty        = 0
                new_lot_total      = 0
                remaining_lots    -= lot_qty
            else:
                deducted_from_lot  = remaining_lots
                new_lot_qty        = lot_qty - remaining_lots
                new_lot_total      = round(new_lot_qty * lot_rate, 4)
                remaining_lots     = 0

            cursor.execute("""
                UPDATE stock_statement_lots
                SET qty = %s, total = %s
                WHERE id = %s AND qty >= %s
            """, (new_lot_qty, new_lot_total, lot_id, lot_qty))

            if cursor.rowcount == 0:
                raise Exception(f"Concurrent update detected for stock_statement_lots id {lot_id}")

            fifo_lines.append((deducted_from_lot, lot_rate))

        if remaining_lots > 0.001:
            raise Exception(
                f"Insufficient lots in stock_statement_lots for {item_name}. "
                f"Still undeducted: {remaining_lots:.4f}"
            )

        # ── 3. Update stock_statement CurrentLevel ────────────────────────────
        cursor.execute("""
            SELECT CurrentLevel, Total 
            FROM stock_statement 
            WHERE ItemName = %s AND UOM = %s AND OutletName = %s
        """, (item["ItemName"], item["UOM"], outlet_name))

        existing = cursor.fetchone()

        if not existing:
            raise Exception(f"Stock statement missing for {item['ItemName']}")

        current_level = float(existing[0])
        current_total = float(existing[1]) if existing[1] else 0

        # Recompute deduction total using FIFO rates (not frontend rate)
        fifo_deduction_total = round(sum(qty * rate for qty, rate in fifo_lines), 4)

        new_level = current_level - requested_qty
        new_total = current_total - fifo_deduction_total

        if new_level < -0.001:
            raise Exception(f"Stock level would become negative for {item['ItemName']}")

        if abs(new_level) < 0.001:
            new_level = 0
            new_total = 0

        cursor.execute("""
            UPDATE stock_statement
            SET CurrentLevel = %s, Total = %s
            WHERE ItemName = %s AND UOM = %s AND OutletName = %s
            AND CurrentLevel >= %s
        """, (
            new_level,
            new_total,
            item["ItemName"],
            item["UOM"],
            outlet_name,
            requested_qty
        ))

        if cursor.rowcount == 0:
            raise Exception(f"Concurrent update detected for stock_statement of {item['ItemName']}")

        # ── 4. Insert into intblstorereqdetails — one row per FIFO lot ────────
        #    Same item may appear multiple times with different rates
        insert_detailsSql = """
        INSERT INTO intblstorereqdetails 
        (`ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`, `StoreReqID`, `itemtype`) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for deducted_qty, lot_rate in fifo_lines:
            cursor.execute(insert_detailsSql, (
                item["ItemName"],
                item["GroupName"],
                item["BrandName"],
                deducted_qty,           # qty consumed from this lot
                item["UOM"],
                lot_rate,               # rate from the lot, NOT from frontend
                store_req_id,
                item_type
            ))

        # ── 5. Insert into item_current_level — one row per FIFO lot ─────────
        for deducted_qty, lot_rate in fifo_lines:
            cursor.execute("""
                INSERT INTO item_current_level (itemname, quantity, rate, outlet, costcenter)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                item['ItemName'],
                deducted_qty,           # qty consumed from this lot
                lot_rate,               # rate from the lot, NOT from frontend
                outlet_name,
                costcenter
            ))

    return {
        "store_req_id": store_req_id,
        "outlet_req_id": outlet_req_id,
        "cost_center": costcenter,
        "items_transferred": len(transfer["ItemDetailsList"]),
        "status": "success"
    }