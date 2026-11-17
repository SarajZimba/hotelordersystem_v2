from flask import  Blueprint,request
import mysql.connector
from flask_cors import CORS, cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file9= Blueprint('app_file9',__name__)

import datetime
from .ird.postvoidbillintoird import post_credit_note_to_ird

# @app_file9.route("/deletedata", methods=['PUT'])
# @cross_origin()
# def delete_bill():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password')
#         )
#         cursor = mydb.cursor(buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         data = request.get_json()
        
#         # 1️⃣ Fetch the bill details to be deleted
#         cursor.execute(
#             "SELECT * FROM tblorderhistory WHERE Outlet_OrderID=%s AND Date=%s AND Outlet_Name= %s",
#             (data["outlet_orderID"], data["date"], data["Outlet_Name"])
#         )
#         bill = cursor.fetchone()
#         if not bill:
#             return {"error": "Bill not found"}, 400

#         # 2️⃣ Prepare Credit Note payload
#         # Convert AD to BS for IRD
#         ad_date = bill[10]  # assuming Date is 11th column, adjust index if needed
#         if isinstance(ad_date, str):
#             ad_date = datetime.datetime.strptime(ad_date, "%Y-%m-%d").date()
#         from nepali_datetime import date as nepali_date
#         bs_date = nepali_date.from_datetime_date(ad_date)
#         bs_date_str = f"{bs_date.year}.{bs_date.month:02d}.{bs_date.day:02d}"

#         # # Fetch IRD credentials
#         # cursor.execute("SELECT username, password, seller_pan FROM ird_credentials LIMIT 1")
#         # ird_creds = cursor.fetchone()
#         # if not ird_creds:
#         #     return {"error": "IRD credentials not found"}, 400
#         # ird_username, ird_password, ird_seller_pan = ird_creds

#         # # Fetch outlet prefix
#         # cursor.execute(
#         #     "SELECT bill_prefix, postingToIRD FROM outetNames WHERE Outlet=%s LIMIT 1",
#         #     (data["Outlet_Name"],)
#         # )
#         # prefix_row = cursor.fetchone()
#         # bill_prefix = prefix_row[0] if prefix_row else ""
#         # postingToIRD = prefix_row[1] 

#         # credit_note_payload = {
#         #     "username": ird_username,
#         #     "password": ird_password,
#         #     "seller_pan": ird_seller_pan,
#         #     "buyer_pan": "0",  # adjust index for guest PAN
#         #     "fiscal_year": bill[17],
#         #     "buyer_name": bill[18],
#         #     "ref_invoice_number": f"{bill_prefix}-{bill[11]}",  # original bill_no
#         #     "credit_note_number": f"{bill_prefix}-VOID-{bill[11]}",  # generate unique credit note number
#         #     "credit_note_date": bs_date_str,
#         #     "reason_for_return": data.get("reason", "Voided bill"),
#         #     "total_sales": float(bill[12]),
#         #     "taxable_sales_vat": float(bill[12]) - float(bill[14]),
#         #     "vat": float(bill[14]),
#         #     "excisable_amount": 0,
#         #     "excise": 0,
#         #     "taxable_sales_hst": 0,
#         #     "hst": 0,
#         #     "amount_for_esf": 0,
#         #     "esf": 0,
#         #     "export_sales": 0,
#         #     "tax_exempted_sales": 0,
#         #     "isrealtime": True,
#         #     "datetimeClient": datetime.datetime.now().isoformat()
#         # }

#         # if postingToIRD:
#         #     success, response_text = post_credit_note_to_ird(credit_note_payload)
#         #     if not success:
#         #         return {"error": "Failed to post credit note to IRD", "details": response_text}, 400

#         cursor.execute("DELETE FROM tblorder_detailshistory WHERE order_ID=%s", (bill[0],))
#         cursor.execute("delete from `payment_history` WHERE orderHistoryid =%s;", (bill[0],))
#         cursor.execute("DELETE FROM tblorderhistory WHERE idtblorderhistory=%s", (bill[0],))

#         cursor.execute("DELETE FROM CreditHistory WHERE Outlet_OrderID=%s and outetName=%s and Date=%s", (data["outlet_orderID"], data["Outlet_Name"], data["date"],))
#         mydb.commit()
#         mydb.close()

#         return {"success": "Bill voided and credit note posted to IRD"}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400


from root.flask_routes.hotel.journal_utils.utils import AccountingEntryNotFound, JournalOutcomeUnknown, void_hotelbill

from root.flask_routes.postsales import get_outlet_sales_entry_info
@app_file9.route("/deletedata", methods=['PUT'])
@cross_origin()
def delete_bill():
    mydb = None
    try:
        data = request.get_json(silent=True) or {}
        for k in ("outlet_orderID", "date", "Outlet_Name"):
            if not data.get(k):
                return {"error": f"{k} is required"}, 400
        reason = (data.get("reason") or "").strip() or "Voided Bill"

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- FIND THE BILL --------
        cursor.execute("""
            SELECT idtblorderHistory AS id, bill_no, fiscal_year, Date, PaymentMode
            FROM tblorderhistory
            WHERE Outlet_OrderID = %s AND Date = %s AND Outlet_Name = %s
        """, (data["outlet_orderID"], data["date"], data["Outlet_Name"]))
        bill = cursor.fetchone()
        if not bill:
            return {"error": "Bill not found"}, 400

        # -------- WORK OUT THE SALES BILL NO USED AT POSTING (same rule as /postsales) --------
        info_cursor = mydb.cursor(buffered=True)   # get_outlet_sales_entry_info reads rows by index
        try:
            sales_info = get_outlet_sales_entry_info(info_cursor, {
                "paymentMode": bill["PaymentMode"],
                "Outlet_Name": data["Outlet_Name"],
                "bill_No": bill["bill_no"],
            })
        except Exception as e:
            return {"error": f"Could not work out the accounting bill number: {e}"}, 400
        finally:
            info_cursor.close()

        # -------- VOID IN ACCOUNTING (reverses journal + posts IRD credit note) --------
        accounting_voided = True
        if sales_info.get("skip"):
            # no sales entry was created for this bill (Complimentary / Non Chargeable,
            # or an outlet that doesn't post to IRD), so the void API has nothing to find
            accounting_voided = False
        else:
            try:
                void_hotelbill({
                    "bill_no": sales_info["sales_bill_no"],   # e.g. "ALG-12", as posted
                    "bill_date": str(bill["Date"])[:10],
                    "fiscal_year": bill["fiscal_year"],
                    "reason": reason,
                })
            except AccountingEntryNotFound as e:
                if not data.get("allow_unposted"):
                    return {"error": f"Accounting has no entry for this bill: {e}. Not deleted. "
                                     f"Send allow_unposted=true if it was never posted."}, 409
                accounting_voided = False
            except JournalOutcomeUnknown as e:
                return {"error": f"Accounting did not confirm the void: {e}. Retrying is safe."}, 502
            except Exception as e:
                return {"error": f"Accounting could not void the bill: {e}"}, 400

        # -------- DELETE LOCAL ROWS (one transaction) --------
        try:
            cursor.execute("DELETE FROM tblorder_detailshistory WHERE order_ID = %s", (bill["id"],))
            cursor.execute("DELETE FROM payment_history WHERE orderHistoryid = %s", (bill["id"],))
            cursor.execute("DELETE FROM tblorderhistory WHERE idtblorderHistory = %s", (bill["id"],))
            cursor.execute(
                "DELETE FROM CreditHistory WHERE Outlet_OrderID = %s AND outetName = %s AND Date = %s",
                (data["outlet_orderID"], data["Outlet_Name"], data["date"]),
            )
            mydb.commit()
        except Exception as e:
            mydb.rollback()
            return {"error": f"Voided in accounting but could not delete the bill: {e}. "
                             f"Retry to finish."}, 500

        return {"success": "Bill voided and deleted", "accounting_voided": accounting_voided}, 200

    except Exception as e:
        return {"error": str(e)}, 400

    finally:
        if mydb:
            mydb.close()