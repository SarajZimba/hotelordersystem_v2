from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

load_dotenv()

app_file492 = Blueprint('app_file492', __name__)

BILL_TYPES = {"LA", "SPA", "MB", "TR"}
PAYMENT_MODES = {"Cash", "Credit Card", "Online", "Room Charge", "Credit", "Mobile Payment"}
TWO = Decimal("0.01")


def _dec(value, field):
    try:
        return Decimal(str(value)).quantize(TWO, ROUND_HALF_UP)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid number for '{field}'")

def _check_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400
    return None

def next_generalbill_number(cursor, bill_type):
    cursor.execute("""
        SELECT fiscal_year, last_number
        FROM hotel_generalbill_sequences
        WHERE type_code = %s
        FOR UPDATE
    """, (bill_type,))
    row = cursor.fetchone()
    if not row:
        return None

    seq = int(row["last_number"]) + 1
    cursor.execute("""
        UPDATE hotel_generalbill_sequences
        SET last_number = %s
        WHERE type_code = %s
    """, (seq, bill_type))

    return row["fiscal_year"], seq, f"{bill_type}-{seq}"

from root.flask_routes.hotel.journal_utils.generalbill_utils import (
    post_generalbill_and_create_journal,
    post_generalbill_and_create_journal_for_creditbills,
)

CREDIT_PAYMENT_MODES = {"Room Charge", "Credit"}


from datetime import date   # at the top of the file

# CREDIT_PAYMENT_MODES = {"Room Charge", "Credit"}



# @app_file492.route("/generalbill", methods=["POST"])
# @cross_origin()
# def create_general_bill():
#     mydb = None
#     try:
#         bill_data = request.get_json(silent=True) or {}

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT VALIDATION --------
#         bill_type = (bill_data.get("bill_type") or "").upper()
#         if bill_type not in BILL_TYPES:
#             return {"error": "Invalid bill_type. Use LA, SPA, MB or TR."}, 400

#         bill_number = str(bill_data.get("BillNo") or "").strip()
#         if not bill_number:
#             return {"error": "BillNo is required"}, 400

#         fiscal_year = (bill_data.get("fiscalYear") or "").strip()
#         if not fiscal_year:
#             return {"error": "fiscalYear is required"}, 400

#         prefix, _, num = bill_number.rpartition("-")
#         if prefix != bill_type or not num.isdigit() or int(num) < 1:
#             return {"error": f"BillNo must look like {bill_type}-<number>"}, 400
#         seq = int(num)

#         outlet = (bill_data.get("outlet") or "").strip()
#         if not outlet:
#             return {"error": "outlet is required"}, 400

#         customer_name = (bill_data.get("customer_name") or "").strip()
#         if not customer_name:
#             return {"error": "customer_name is required"}, 400

#         payment_mode = bill_data.get("payment_mode", "Cash")
#         if payment_mode not in PAYMENT_MODES:
#             return {"error": f"payment_mode must be one of {sorted(PAYMENT_MODES)}"}, 400

#         customer_id = str(bill_data.get("customer_id") or "").strip()
#         if len(customer_id) > 50:
#             return {"error": "customer_id is too long (max 50 characters)"}, 400
#         if payment_mode in CREDIT_PAYMENT_MODES and not customer_id:
#             return {"error": f"customer_id is required for payment mode '{payment_mode}'"}, 400

#         raw_items = bill_data.get("items") or []
#         if not raw_items:
#             return {"error": "At least one item is required"}, 400

#         # -------- TOTALS, ITEMS & FOREX RECEIPTS: as sent by frontend --------
#         try:
#             sub_total = _dec(bill_data["sub_total"], "sub_total")
#             discount = _dec(bill_data.get("discount_amount") or 0, "discount_amount")
#             taxable_amount = _dec(bill_data["taxable_amount"], "taxable_amount")
#             tax_amount = _dec(bill_data["tax_amount"], "tax_amount")
#             grand_total = _dec(bill_data["grand_total"], "grand_total")

#             items = []
#             for i in raw_items:
#                 name = (i.get("item_name") or "").strip()
#                 if not name:
#                     raise ValueError("item_name is required for every item")
#                 items.append({
#                     "item_name": name,
#                     "quantity": _dec(i.get("quantity", 1), "quantity"),
#                     "rate": _dec(i["rate"], "rate"),
#                     "is_taxable": 1 if i.get("is_taxable", True) else 0,
#                     "subtotal": _dec(i["subtotal"], "subtotal"),
#                     "vat_amount": _dec(i["vat_amount"], "vat_amount"),
#                     "total": _dec(i["total"], "total"),
#                 })

#             forex_receipts = []
#             for f in (bill_data.get("forex_receipts") or []):
#                 currency = (f.get("Currency") or "").strip().upper()
#                 if not currency:
#                     raise ValueError("Currency is required for every forex receipt")
#                 amount_received = _dec(f["AmountReceived"], "AmountReceived")
#                 exe_rate = _dec(f["ExeRate"], "ExeRate")
#                 amount_local = _dec(f["AmountLocal"], "AmountLocal")
#                 # if amount_received <= 0 or exe_rate <= 0:
#                 #     raise ValueError("AmountReceived and ExeRate must be greater than 0")
#                 # if abs((amount_received * exe_rate).quantize(Decimal("0.01")) - amount_local) > Decimal("0.01"):
#                 #     raise ValueError("AmountLocal must equal AmountReceived x ExeRate")
#                 forex_receipts.append({
#                     "Currency": currency,
#                     "AmountReceived": amount_received,
#                     "ExeRate": exe_rate,
#                     "AmountLocal": amount_local,
#                     "PaymentMode": (f.get("PaymentMode") or "Cash").strip(),
#                 })

#             if forex_receipts and payment_mode in CREDIT_PAYMENT_MODES:
#                 raise ValueError("Forex receipts are not allowed for Room Charge / Credit bills")
#             if sum(f["AmountLocal"] for f in forex_receipts) > grand_total:
#                 raise ValueError("Forex receipts exceed the bill total")
#         except KeyError as e:
#             return {"error": f"Missing field: {e.args[0]}"}, 400
#         except ValueError as e:
#             return {"error": str(e)}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # type name (used as the accounting subledger name)
#         cursor.execute(
#             "SELECT name FROM hotel_generalbill_types WHERE code = %s AND is_active = 1",
#             (bill_type,)
#         )
#         type_row = cursor.fetchone()
#         if not type_row:
#             mydb.rollback()
#             return {"error": f"Bill type {bill_type} not found or inactive"}, 400
#         type_name = type_row["name"]

#         # the number must have been issued by the reserve endpoint, for the current fiscal year
#         cursor.execute("""
#             SELECT fiscal_year, last_number
#             FROM hotel_generalbill_sequences
#             WHERE type_code = %s
#             FOR UPDATE
#         """, (bill_type,))
#         seq_row = cursor.fetchone()
#         if not seq_row:
#             mydb.rollback()
#             return {"error": f"No sequence row found for bill type {bill_type}"}, 400
#         if seq_row["fiscal_year"] != fiscal_year:
#             mydb.rollback()
#             return {"error": "Fiscal year has changed. Please get a new bill number."}, 409
#         if seq > int(seq_row["last_number"]):
#             mydb.rollback()
#             return {"error": "This bill number has not been issued. Please get a new bill number."}, 400

#         created_by = bill_data.get("created_by") or "system"
#         bill_date = date.today().strftime("%Y-%m-%d")   # the date accounting posts under; void needs the same one

#         cursor.execute("""
#             INSERT INTO hotel_generalbills (
#                 bill_type, fiscal_year, bill_date, seq_no, bill_number,
#                 reservation_id, room_no, outlet,
#                 customer_id, customer_name, customer_tax_number,
#                 payment_mode, narration,
#                 sub_total, discount_amount, taxable_amount, tax_amount, grand_total,
#                 created_by
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             bill_type, fiscal_year, bill_date, seq, bill_number,
#             bill_data.get("reservation_id"), bill_data.get("room_no"), outlet,
#             customer_id or None, customer_name, bill_data.get("customer_tax_number"),
#             payment_mode, bill_data.get("narration"),
#             sub_total, discount, taxable_amount, tax_amount, grand_total,
#             created_by
#         ))
#         bill_id = cursor.lastrowid

#         cursor.executemany("""
#             INSERT INTO hotel_generalbill_items (
#                 bill_id, item_name, quantity, rate, is_taxable,
#                 subtotal, vat_amount, total
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#         """, [
#             (bill_id, it["item_name"], it["quantity"], it["rate"], it["is_taxable"],
#              it["subtotal"], it["vat_amount"], it["total"])
#             for it in items
#         ])

#         if forex_receipts:
#             cursor.executemany("""
#                 INSERT INTO hotel_generalbill_forex_receipts (
#                     bill_id, Currency, AmountReceived, ExeRate, AmountLocal,
#                     PaymentMode, fiscalYear, created_at, updated_at
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (bill_id, f["Currency"], f["AmountReceived"], f["ExeRate"],
#                  f["AmountLocal"], f["PaymentMode"], fiscal_year)
#                 for f in forex_receipts
#             ])

#         mydb.commit()

#         # -------- ACCOUNTING (best-effort, after commit) --------
#         journal_posted, journal_error = True, None
#         try:
#             journal_bill = {
#                 "bill_number": bill_number,
#                 "bill_type": bill_type,
#                 "type_name": type_name,
#                 "fiscal_year": fiscal_year,
#                 "bill_date": bill_date,
#                 "outlet": outlet,
#                 "customer_name": customer_name,
#                 "customer_tax_number": bill_data.get("customer_tax_number"),
#                 "guest_id": customer_id,   # debtor ledger id for credit / room charge bills
#                 "payment_mode": payment_mode,
#                 "grand_total": grand_total,
#                 "tax_amount": tax_amount,
#                 "taxable_amount": taxable_amount,
#                 "discount_amount": discount,
#                 "created_by": created_by,
#             }
#             if payment_mode in CREDIT_PAYMENT_MODES:
#                 post_generalbill_and_create_journal_for_creditbills(journal_bill)
#             else:
#                 post_generalbill_and_create_journal(journal_bill)
#         except Exception as e:
#             journal_posted, journal_error = False, str(e)

#         try:
#             cursor.execute("""
#                 UPDATE hotel_generalbills
#                 SET journal_posted = %s, journal_error = %s
#                 WHERE id = %s
#             """, (1 if journal_posted else 0, (journal_error or "")[:255] or None, bill_id))
#             mydb.commit()
#         except Exception:
#             pass

#         return jsonify({
#             "message": "General bill created successfully",
#             "bill": {
#                 "bill_id": bill_id,
#                 "bill_number": bill_number,
#                 "bill_type": bill_type,
#                 "bill_type_name": type_name,
#                 "fiscal_year": fiscal_year,
#                 "bill_date": bill_date,
#                 "outlet": outlet,
#                 "customer_id": customer_id or None,
#                 "customer_name": customer_name,
#                 "payment_mode": payment_mode,
#                 "sub_total": str(sub_total),
#                 "discount_amount": str(discount),
#                 "taxable_amount": str(taxable_amount),
#                 "tax_amount": str(tax_amount),
#                 "non_taxable_amount": str(sub_total - taxable_amount),
#                 "grand_total": str(grand_total),
#                 "journal_posted": journal_posted,
#                 "journal_error": journal_error,
#                 "items": [
#                     {k: (str(v) if isinstance(v, Decimal) else v) for k, v in it.items()}
#                     for it in items
#                 ],
#                 "forex_receipts": [
#                     {k: (str(v) if isinstance(v, Decimal) else v) for k, v in f.items()}
#                     for f in forex_receipts
#                 ],
#             }
#         }), 201

#     except mysql.connector.errors.IntegrityError as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         if e.errno == 1062:
#             return {"error": "This bill number has already been used"}, 409
#         return {"error": str(e)}, 500

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500

#     finally:
#         try:
#             mydb.close()
#         except:
#             pass


from datetime import date   # at the top of the file
from flask import current_app   # <-- new (skip if this file already imports it)
from root.flask_routes.hotel.hotel_utils.utils import log_hotel_activity, get_employee_name   # <-- new

CREDIT_PAYMENT_MODES = {"Room Charge", "Credit"}


@app_file492.route("/generalbill", methods=["POST"])
@cross_origin()
def create_general_bill():
    mydb = None
    try:
        bill_data = request.get_json(silent=True) or {}

        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT VALIDATION --------
        bill_type = (bill_data.get("bill_type") or "").upper()
        if bill_type not in BILL_TYPES:
            return {"error": "Invalid bill_type. Use LA, SPA, MB or TR."}, 400

        bill_number = str(bill_data.get("BillNo") or "").strip()
        if not bill_number:
            return {"error": "BillNo is required"}, 400

        fiscal_year = (bill_data.get("fiscalYear") or "").strip()
        if not fiscal_year:
            return {"error": "fiscalYear is required"}, 400

        prefix, _, num = bill_number.rpartition("-")
        if prefix != bill_type or not num.isdigit() or int(num) < 1:
            return {"error": f"BillNo must look like {bill_type}-<number>"}, 400
        seq = int(num)

        outlet = (bill_data.get("outlet") or "").strip()
        if not outlet:
            return {"error": "outlet is required"}, 400

        customer_name = (bill_data.get("customer_name") or "").strip()
        if not customer_name:
            return {"error": "customer_name is required"}, 400

        payment_mode = bill_data.get("payment_mode", "Cash")
        if payment_mode not in PAYMENT_MODES:
            return {"error": f"payment_mode must be one of {sorted(PAYMENT_MODES)}"}, 400

        customer_id = str(bill_data.get("customer_id") or "").strip()
        if len(customer_id) > 50:
            return {"error": "customer_id is too long (max 50 characters)"}, 400
        if payment_mode in CREDIT_PAYMENT_MODES and not customer_id:
            return {"error": f"customer_id is required for payment mode '{payment_mode}'"}, 400

        raw_items = bill_data.get("items") or []
        if not raw_items:
            return {"error": "At least one item is required"}, 400

        # -------- TOTALS, ITEMS & FOREX RECEIPTS: as sent by frontend --------
        try:
            sub_total = _dec(bill_data["sub_total"], "sub_total")
            discount = _dec(bill_data.get("discount_amount") or 0, "discount_amount")
            taxable_amount = _dec(bill_data["taxable_amount"], "taxable_amount")
            tax_amount = _dec(bill_data["tax_amount"], "tax_amount")
            grand_total = _dec(bill_data["grand_total"], "grand_total")

            items = []
            for i in raw_items:
                name = (i.get("item_name") or "").strip()
                if not name:
                    raise ValueError("item_name is required for every item")
                items.append({
                    "item_name": name,
                    "quantity": _dec(i.get("quantity", 1), "quantity"),
                    "rate": _dec(i["rate"], "rate"),
                    "is_taxable": 1 if i.get("is_taxable", True) else 0,
                    "subtotal": _dec(i["subtotal"], "subtotal"),
                    "vat_amount": _dec(i["vat_amount"], "vat_amount"),
                    "total": _dec(i["total"], "total"),
                })

            forex_receipts = []
            for f in (bill_data.get("forex_receipts") or []):
                currency = (f.get("Currency") or "").strip().upper()
                if not currency:
                    raise ValueError("Currency is required for every forex receipt")
                amount_received = _dec(f["AmountReceived"], "AmountReceived")
                exe_rate = _dec(f["ExeRate"], "ExeRate")
                amount_local = _dec(f["AmountLocal"], "AmountLocal")
                # if amount_received <= 0 or exe_rate <= 0:
                #     raise ValueError("AmountReceived and ExeRate must be greater than 0")
                # if abs((amount_received * exe_rate).quantize(Decimal("0.01")) - amount_local) > Decimal("0.01"):
                #     raise ValueError("AmountLocal must equal AmountReceived x ExeRate")
                forex_receipts.append({
                    "Currency": currency,
                    "AmountReceived": amount_received,
                    "ExeRate": exe_rate,
                    "AmountLocal": amount_local,
                    "PaymentMode": (f.get("PaymentMode") or "Cash").strip(),
                })

            if forex_receipts and payment_mode in CREDIT_PAYMENT_MODES:
                raise ValueError("Forex receipts are not allowed for Room Charge / Credit bills")
            if sum(f["AmountLocal"] for f in forex_receipts) > grand_total:
                raise ValueError("Forex receipts exceed the bill total")
        except KeyError as e:
            return {"error": f"Missing field: {e.args[0]}"}, 400
        except ValueError as e:
            return {"error": str(e)}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        # type name (used as the accounting subledger name)
        cursor.execute(
            "SELECT name FROM hotel_generalbill_types WHERE code = %s AND is_active = 1",
            (bill_type,)
        )
        type_row = cursor.fetchone()
        if not type_row:
            mydb.rollback()
            return {"error": f"Bill type {bill_type} not found or inactive"}, 400
        type_name = type_row["name"]

        # the number must have been issued by the reserve endpoint, for the current fiscal year
        cursor.execute("""
            SELECT fiscal_year, last_number
            FROM hotel_generalbill_sequences
            WHERE type_code = %s
            FOR UPDATE
        """, (bill_type,))
        seq_row = cursor.fetchone()
        if not seq_row:
            mydb.rollback()
            return {"error": f"No sequence row found for bill type {bill_type}"}, 400
        if seq_row["fiscal_year"] != fiscal_year:
            mydb.rollback()
            return {"error": "Fiscal year has changed. Please get a new bill number."}, 409
        if seq > int(seq_row["last_number"]):
            mydb.rollback()
            return {"error": "This bill number has not been issued. Please get a new bill number."}, 400

        created_by = bill_data.get("created_by") or "system"
        bill_date = date.today().strftime("%Y-%m-%d")   # the date accounting posts under; void needs the same one

        cursor.execute("""
            INSERT INTO hotel_generalbills (
                bill_type, fiscal_year, bill_date, seq_no, bill_number,
                reservation_id, room_no, outlet,
                customer_id, customer_name, customer_tax_number,
                payment_mode, narration,
                sub_total, discount_amount, taxable_amount, tax_amount, grand_total,
                created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            bill_type, fiscal_year, bill_date, seq, bill_number,
            bill_data.get("reservation_id"), bill_data.get("room_no"), outlet,
            customer_id or None, customer_name, bill_data.get("customer_tax_number"),
            payment_mode, bill_data.get("narration"),
            sub_total, discount, taxable_amount, tax_amount, grand_total,
            created_by
        ))
        bill_id = cursor.lastrowid

        cursor.executemany("""
            INSERT INTO hotel_generalbill_items (
                bill_id, item_name, quantity, rate, is_taxable,
                subtotal, vat_amount, total
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            (bill_id, it["item_name"], it["quantity"], it["rate"], it["is_taxable"],
             it["subtotal"], it["vat_amount"], it["total"])
            for it in items
        ])

        if forex_receipts:
            cursor.executemany("""
                INSERT INTO hotel_generalbill_forex_receipts (
                    bill_id, Currency, AmountReceived, ExeRate, AmountLocal,
                    PaymentMode, fiscalYear, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, [
                (bill_id, f["Currency"], f["AmountReceived"], f["ExeRate"],
                 f["AmountLocal"], f["PaymentMode"], fiscal_year)
                for f in forex_receipts
            ])

        # -------- ACTIVITY LOG (same transaction as the bill; never blocks the bill) --------   # <-- new
        try:
            # created_by is the employee's user id (it falls back to the text "system" when not sent)
            log_emp_id = int(created_by) if str(created_by).isdigit() else None
            log_emp_name = get_employee_name(cursor, log_emp_id)

            where = []
            if bill_data.get("reservation_id"):
                where.append(f"reservation #{bill_data.get('reservation_id')}")
            if bill_data.get("room_no"):
                where.append(f"room {bill_data.get('room_no')}")

            description = (
                f"{log_emp_name or 'Employee'} created {type_name} bill {bill_number} "
                f"for {customer_name}"
                + (f" ({', '.join(where)})" if where else "")
                + f". {payment_mode}, total {grand_total}"
            )

            log_hotel_activity(
                cursor,
                outlet=outlet,
                action="GENERAL_BILL_CREATED",
                reservation_id=bill_data.get("reservation_id"),
                description=description,
                employee_id=log_emp_id,
                employee_name=log_emp_name,
                details={
                    "bill_id": bill_id,
                    "bill_number": bill_number,
                    "bill_type": bill_type,
                    "type_name": type_name,
                    "fiscal_year": fiscal_year,
                    "customer_id": customer_id or None,
                    "customer_name": customer_name,
                    "payment_mode": payment_mode,
                    "grand_total": grand_total,
                    "room_no": bill_data.get("room_no"),
                    "items": len(items),
                },
                endpoint="/generalbill",
            )
        except Exception as e:
            current_app.logger.exception(f"Activity log failed for general bill {bill_number}: {e}")

        mydb.commit()

        # -------- ACCOUNTING (best-effort, after commit) --------
        journal_posted, journal_error = True, None
        try:
            journal_bill = {
                "bill_number": bill_number,
                "bill_type": bill_type,
                "type_name": type_name,
                "fiscal_year": fiscal_year,
                "bill_date": bill_date,
                "outlet": outlet,
                "customer_name": customer_name,
                "customer_tax_number": bill_data.get("customer_tax_number"),
                "guest_id": customer_id,   # debtor ledger id for credit / room charge bills
                "payment_mode": payment_mode,
                "grand_total": grand_total,
                "tax_amount": tax_amount,
                "taxable_amount": taxable_amount,
                "discount_amount": discount,
                "created_by": created_by,
            }
            if payment_mode in CREDIT_PAYMENT_MODES:
                post_generalbill_and_create_journal_for_creditbills(journal_bill)
            else:
                post_generalbill_and_create_journal(journal_bill)
        except Exception as e:
            journal_posted, journal_error = False, str(e)

        try:
            cursor.execute("""
                UPDATE hotel_generalbills
                SET journal_posted = %s, journal_error = %s
                WHERE id = %s
            """, (1 if journal_posted else 0, (journal_error or "")[:255] or None, bill_id))
            mydb.commit()
        except Exception:
            pass

        return jsonify({
            "message": "General bill created successfully",
            "bill": {
                "bill_id": bill_id,
                "bill_number": bill_number,
                "bill_type": bill_type,
                "bill_type_name": type_name,
                "fiscal_year": fiscal_year,
                "bill_date": bill_date,
                "outlet": outlet,
                "customer_id": customer_id or None,
                "customer_name": customer_name,
                "payment_mode": payment_mode,
                "sub_total": str(sub_total),
                "discount_amount": str(discount),
                "taxable_amount": str(taxable_amount),
                "tax_amount": str(tax_amount),
                "non_taxable_amount": str(sub_total - taxable_amount),
                "grand_total": str(grand_total),
                "journal_posted": journal_posted,
                "journal_error": journal_error,
                "items": [
                    {k: (str(v) if isinstance(v, Decimal) else v) for k, v in it.items()}
                    for it in items
                ],
                "forex_receipts": [
                    {k: (str(v) if isinstance(v, Decimal) else v) for k, v in f.items()}
                    for f in forex_receipts
                ],
            }
        }), 201

    except mysql.connector.errors.IntegrityError as e:
        try:
            mydb.rollback()
        except:
            pass
        if e.errno == 1062:
            return {"error": "This bill number has already been used"}, 409
        return {"error": str(e)}, 500

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass

@app_file492.route("/generalbill/sequences/next-fiscal-year", methods=["POST"])
@cross_origin()
def rollover_generalbill_fiscal_year():
    mydb = None
    try:
        data = request.get_json(silent=True) or {}

        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        new_fy = (data.get("fiscalYear") or "").strip()
        if not new_fy:
            return {"error": "fiscalYear is required"}, 400

        bill_type = (data.get("bill_type") or "").upper()
        if bill_type and bill_type not in BILL_TYPES:
            return {"error": "Invalid bill_type. Use LA, SPA, MB or TR."}, 400

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        if bill_type:
            cursor.execute("""
                SELECT type_code, fiscal_year FROM hotel_generalbill_sequences
                WHERE type_code = %s FOR UPDATE
            """, (bill_type,))
        else:
            cursor.execute("""
                SELECT type_code, fiscal_year FROM hotel_generalbill_sequences
                FOR UPDATE
            """)
        rows = cursor.fetchall()

        if not rows:
            mydb.rollback()
            return {"error": "No sequence rows found"}, 404

        already = [r["type_code"] for r in rows if r["fiscal_year"] == new_fy]
        if already:
            mydb.rollback()
            return {"error": f"Already on fiscal year {new_fy} for: {', '.join(already)}"}, 400

        cursor.executemany("""
            UPDATE hotel_generalbill_sequences
            SET fiscal_year = %s, last_number = 0
            WHERE type_code = %s
        """, [(new_fy, r["type_code"]) for r in rows])

        mydb.commit()

        return jsonify({
            "message": "Fiscal year updated and numbering reset",
            "fiscal_year": new_fy,
            "types_updated": [r["type_code"] for r in rows]
        }), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass

@app_file492.route("/generalbill/bill-no", methods=["GET"])
@cross_origin()
def reserve_generalbill_no():
    # -------- TOKEN --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except Exception:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    bill_type = (request.args.get("bill_type") or "").upper()
    if bill_type not in BILL_TYPES:
        return {"error": "Invalid bill_type. Use LA, SPA, MB or TR."}, 400

    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        numbering = next_generalbill_number(cursor, bill_type)
        if not numbering:
            mydb.rollback()
            return {"error": f"No sequence row found for bill type {bill_type}"}, 400
        fiscal_year, seq, bill_number = numbering
        mydb.commit()

        return jsonify({
            "BillNo": bill_number,
            "fiscalYear": fiscal_year,
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


# # ---------------- VOID BILL ----------------
# @app_file492.route("/generalbill/<int:bill_id>/void", methods=["POST"])
# @cross_origin()
# def void_general_bill(bill_id):
#     mydb = None
#     try:
#         err = _check_token()
#         if err:
#             return err

#         data = request.get_json(silent=True) or {}

#         void_reason = (data.get("void_reason") or "").strip()
#         if not void_reason:
#             return {"error": "void_reason is required"}, 400

#         voided_by = (data.get("voided_by") or "").strip() or "system"

#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         cursor.execute("""
#             SELECT id, bill_number, fiscal_year, status
#             FROM hotel_generalbills
#             WHERE id = %s
#             FOR UPDATE
#         """, (bill_id,))
#         bill = cursor.fetchone()

#         if not bill:
#             mydb.rollback()
#             return {"error": "Bill not found"}, 404

#         if bill["status"] == 0:
#             mydb.rollback()
#             return {"error": "Bill is already void"}, 400

#         cursor.execute("""
#             UPDATE hotel_generalbills
#             SET status = 0,
#                 void_reason = %s,
#                 voided_by = %s,
#                 voided_at = NOW()
#             WHERE id = %s AND status = 1
#         """, (void_reason, voided_by, bill_id))

#         mydb.commit()

#         return jsonify({
#             "message": "Bill voided successfully",
#             "bill_id": bill["id"],
#             "bill_number": bill["bill_number"],
#             "fiscal_year": bill["fiscal_year"],
#             "status": 0,
#             "void_reason": void_reason,
#             "voided_by": voided_by
#         }), 200

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500

#     finally:
#         try:
#             mydb.close()
#         except:
#             pass


from root.flask_routes.hotel.journal_utils.utils import (
    void_hotelbill,
    JournalOutcomeUnknown,
    AccountingEntryNotFound,
)


@app_file492.route("/generalbill/<int:bill_id>/void", methods=["POST"])
@cross_origin()
def void_general_bill(bill_id):
    mydb = None
    try:
        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        data = request.get_json(silent=True) or {}

        void_reason = (data.get("void_reason") or "").strip()
        if not void_reason:
            return {"error": "void_reason is required"}, 400

        voided_by = (data.get("voided_by") or "").strip() or "system"

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        # -------- CHECK BILL --------
        cursor.execute("""
            SELECT id, bill_number, fiscal_year, status, journal_posted,
                   COALESCE(bill_date, DATE(created_at)) AS bill_date
            FROM hotel_generalbills
            WHERE id = %s
        """, (bill_id,))
        bill = cursor.fetchone()

        if not bill:
            return {"error": "Bill not found"}, 404

        if bill["status"] == 0:
            return {"message": "Bill already voided"}, 200

        bill_date = bill["bill_date"]
        bill_date = bill_date.strftime("%Y-%m-%d") if hasattr(bill_date, "strftime") else str(bill_date)[:10]

        # -------- VOID IN ACCOUNTING (reverses journal + posts IRD credit note) --------
        accounting_voided = True
        try:
            void_hotelbill({
                "bill_no": bill["bill_number"],
                "bill_date": bill_date,
                "fiscal_year": bill["fiscal_year"],
                "reason": void_reason,
            })
        except AccountingEntryNotFound as e:
            if bill["journal_posted"]:
                return {
                    "error": f"Bill is marked as posted but accounting has no entry for it: {e}. Not voided."
                }, 409
            accounting_voided = False   # never reached accounting, nothing to reverse
        except JournalOutcomeUnknown as e:
            return {"error": f"Accounting did not confirm the void: {e}. Retrying is safe."}, 502
        except Exception as e:
            return {"error": f"Accounting could not void the bill: {e}"}, 400

        # -------- VOID BILL --------
        try:
            cursor.execute("""
                UPDATE hotel_generalbills
                SET status = 0, void_reason = %s, voided_by = %s, voided_at = NOW()
                WHERE id = %s AND status = 1
            """, (void_reason, voided_by, bill_id))
            changed = cursor.rowcount
            mydb.commit()
        except Exception as e:
            mydb.rollback()
            return {
                "error": f"Voided in accounting but could not update the bill status: {e}. "
                         f"Retry the void to finish."
            }, 500

        if changed == 0:
            return {"message": "Bill already voided"}, 200

        return {
            "message": "Bill voided successfully",
            "bill_id": bill_id,
            "bill_number": bill["bill_number"],
            "status": 0,
            "accounting_voided": accounting_voided,
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass