# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from root.auth.check import token_auth

# from root.flask_routes.hotel.journal_utils.utils import post_hotelbill_and_create_journal, post_hotelbill_and_create_journal_for_creditbills

# load_dotenv()

# app_file412 = Blueprint('app_file412', __name__)


# @app_file412.route("/bill", methods=["POST"])
# @cross_origin()
# def create_bills():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True)

#         bill_data = request.get_json() or {}

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

#         # -------- INPUT --------
#         outlet_reservationID = bill_data.get("outlet_reservationID")
#         bill_details = bill_data.get("bill_details", [])
#         split_payments = bill_data.get("SplitPaymentDetailsList", [])

#         if not outlet_reservationID:
#             return {"error": "outlet_reservationID is required"}, 400

#         # -------- STEP 1: FETCH reservationID + outlet + employee --------
#         cursor.execute("""
#             SELECT r.id, r.outlet, r.Emp_ID, e.userName AS employee_name
#             FROM hotel_tblreservation r
#             LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#             WHERE r.reservation_outlet_id = %s
#         """, (outlet_reservationID,))
#         reservation = cursor.fetchone()

#         if not reservation:
#             return {"error": "Reservation not found"}, 404

#         reservationID = reservation["id"]
#         outlet_name = reservation["outlet"]
#         employee_name = reservation["employee_name"] or str(reservation["Emp_ID"])

#         # -------- CHECK EXISTING BILL --------
#         cursor.execute("""
#             SELECT id FROM hotel_tblhotelbills 
#             WHERE reservationID = %s
#         """, (reservationID,))
#         existing = cursor.fetchone()

#         if existing:
#             return {"error": "Bill already exists for this reservation"}, 400

#         # -------- VALIDATE SPLIT PAYMENTS UP FRONT --------
#         if bill_data.get("PaymentMode") == "Split" and not split_payments:
#             return {"error": "PaymentMode is 'Split' but SplitPaymentDetailsList is empty"}, 400

#         # # -------- START TRANSACTION --------
#         # mydb.start_transaction()

#         # -------- INSERT MASTER BILL --------
#         cursor.execute("""
#             INSERT INTO hotel_tblhotelbills (
#                 reservationID,
#                 outlet_reservationID,
#                 fiscalYear,
#                 BillNo,
#                 subTotal,
#                 DiscountAmt,
#                 VAT,
#                 Total,
#                 PaymentMode,
#                 PartyName,
#                 PartyPAN,
#                 Date,
#                 NoOfNights,
#                 MealplanRevenue,
#                 RoomRevenue,
#                 ExtraChargeSettlement,
#                 created_at,
#                 updated_at,
#                 time
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
#         """, (
#             reservationID,
#             outlet_reservationID,
#             bill_data.get("fiscalYear"),
#             bill_data.get("BillNo"),
#             bill_data.get("subTotal", 0),
#             bill_data.get("DiscountAmt", 0),
#             bill_data.get("VAT", 0),
#             bill_data.get("Total", 0),
#             bill_data.get("PaymentMode"),
#             bill_data.get("PartyName"),
#             bill_data.get("PartyPAN"),
#             bill_data.get("Date"),
#             bill_data.get("NoOfNights"),
#             bill_data.get("MealplanRevenue", 0),
#             bill_data.get("RoomRevenue", 0),
#             bill_data.get("ExtraChargeSettlement", 0),
#             bill_data.get("time", "")
#         ))

#         bill_id = cursor.lastrowid

#         # -------- INSERT SPLIT PAYMENTS --------
#         if bill_data.get("PaymentMode") == "Split" and split_payments:
#             payment_query = """
#                 INSERT INTO hotel_tblbillpayments (
#                     bill_id, PaymentMode, PaymentAmount, fiscalYear, created_at, updated_at
#                 ) VALUES (%s, %s, %s, %s, NOW(), NOW())
#             """
#             payment_values = [
#                 (
#                     bill_id,
#                     p.get("paymentMode"),
#                     p.get("paymentAmount", 0),
#                     bill_data.get("fiscalYear"),
#                 )
#                 for p in split_payments
#             ]
#             cursor.executemany(payment_query, payment_values)

#         # -------- INSERT BILL DETAILS --------
#         if bill_details:
#             detail_query = """
#                 INSERT INTO hotel_tblbilldetails (
#                     bill_id,
#                     Date,
#                     RoomNumber,
#                     RoomType,
#                     RoomRate,
#                     RoomRateName,
#                     RateAmt,
#                     MealPlan,
#                     MealPlanAmt,
#                     Amount,
#                     Currency,
#                     ExeRate,
#                     AmountInclCurr,
#                     created_at,
#                     updated_at
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#             """

#             detail_values = []
#             for d in bill_details:
#                 detail_values.append((
#                     bill_id,
#                     d.get("Date"),
#                     d.get("RoomNumber"),
#                     d.get("RoomType"),
#                     d.get("RoomRate", 0),
#                     d.get("RoomRateName"),
#                     d.get("RateAmt", 0),
#                     d.get("MealPlan"),
#                     d.get("MealPlanAmt", 0),
#                     d.get("Amount", 0),
#                     d.get("Currency"),
#                     d.get("ExeRate", 0),
#                     d.get("AmountInclCurr", 0)
#                 ))

#             cursor.executemany(detail_query, detail_values)

#         update_query = """
#             UPDATE hotel_tblreservation
#             SET Current_Status = %s
#             WHERE id = %s
#         """

#         cursor.execute(update_query, ("Checked Out", reservationID))

#         # -------- COMMIT --------
#         mydb.commit()
#         mydb.close()

#         # -------- JOURNAL ENTRY (best-effort, after commit) --------
#         bill_data["Outlet_Name"] = outlet_name
#         bill_data["Employee"] = employee_name
#         bill_data["billPrintTime"] = ""

#         if bill_data.get("PaymentMode") == "Credit":
#             post_hotelbill_and_create_journal_for_creditbills(bill_data, bill_id)
#         else:
#             post_hotelbill_and_create_journal(bill_data, bill_id)

#         return jsonify({
#             "message": "Bill + details created successfully",
#             "bill_id": bill_id,
#             "total_details": len(bill_details),
#             "total_split_payments": len(split_payments) if bill_data.get("PaymentMode") == "Split" else 0
#         }), 201

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500


# from root.flask_routes.hotel.journal_utils.utils import get_next_hotel_bill_no, get_next_hotel_bill_info   # adjust to your utils module path

# import os
# from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# import mysql.connector
# from mysql.connector import errors as mysql_errors
# from flask import request, jsonify, current_app
# from flask_cors import cross_origin


# def _safe_rollback(mydb):
#     try:
#         mydb.rollback()
#     except Exception:
#         pass


# from root.flask_routes.hotel.journal_utils.utils import JournalOutcomeUnknown


# def _parse_forex_receipts(items, bill_payment_mode):
#     """
#     Validate ForexReceiptsList from the frontend.

#     Each item: {"currency": "USD", "amountReceived": 100, "exeRate": 150, "paymentMode": "Cash"}

#     - AmountLocal is always computed here (amountReceived * exeRate), never trusted from the frontend.
#     - paymentMode falls back to the bill's PaymentMode, except for Split bills,
#       where each item must say how it was paid.

#     Returns (rows, error). rows are tuples of
#     (Currency, AmountReceived, ExeRate, AmountLocal, PaymentMode).
#     """
#     rows = []
#     for i, f in enumerate(items, start=1):
#         if not isinstance(f, dict):
#             return None, f"ForexReceiptsList item {i} must be an object."

#         currency = str(f.get("currency") or f.get("Currency") or "").strip().upper()
#         if not currency:
#             return None, f"ForexReceiptsList item {i}: currency is required."

#         mode = str(f.get("paymentMode") or f.get("PaymentMode") or "").strip()
#         if not mode and bill_payment_mode != "Split":
#             mode = bill_payment_mode or ""
#         if not mode:
#             return None, f"ForexReceiptsList item {i}: paymentMode is required."

#         try:
#             amount = Decimal(str(f.get("amountReceived")))
#             rate = Decimal(str(f.get("exeRate")))
#         except (InvalidOperation, TypeError, ValueError):
#             return None, f"ForexReceiptsList item {i}: amountReceived and exeRate must be numbers."

#         if not amount.is_finite() or not rate.is_finite() or amount <= 0 or rate <= 0:
#             return None, f"ForexReceiptsList item {i}: amountReceived and exeRate must be greater than 0."

#         local = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#         rows.append((currency, amount, rate, local, mode))

#     return rows, None


# @app_file412.route("/bill-by-id", methods=["POST"])
# @cross_origin()
# def create_bills_by_reservation_id():
#     mydb = None
#     cursor = None
#     committed = False
#     try:
#         bill_data = request.get_json() or {}

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT (validated before any DB work) --------
#         reservationID = bill_data.get("reservationID") or bill_data.get("Reservation_ID")
#         bill_details = bill_data.get("bill_details") or []
#         split_payments = bill_data.get("SplitPaymentDetailsList") or []
#         forex_items = bill_data.get("ForexReceiptsList") or []
#         payment_mode = bill_data.get("PaymentMode")
#         fiscal_year = bill_data.get("fiscalYear")
#         guest_id = str(bill_data.get("guestID") or "").strip()

#         if not fiscal_year:
#             return {"error": "fiscalYear is required"}, 400
#         if payment_mode == "Credit":
#             if not guest_id:
#                 return {"error": "guestID is required for credit bills."}, 400
#             if not (bill_data.get("PartyName") or "").strip():
#                 return {"error": "PartyName is required for credit bills."}, 400
#         if not reservationID:
#             return {"error": "reservationID is required"}, 400
#         if (
#             not isinstance(bill_details, list)
#             or not isinstance(split_payments, list)
#             or not isinstance(forex_items, list)
#         ):
#             return {"error": "bill_details, SplitPaymentDetailsList and ForexReceiptsList must be lists."}, 400
#         if payment_mode == "Split" and not split_payments:
#             return {"error": "PaymentMode is 'Split' but SplitPaymentDetailsList is empty"}, 400
#         if payment_mode == "Credit" and forex_items:
#             return {"error": "ForexReceiptsList cannot be sent for credit bills (no money is received)."}, 400

#         forex_rows, forex_err = _parse_forex_receipts(forex_items, payment_mode)
#         if forex_err:
#             return {"error": forex_err}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- RESERVATION + EMPLOYEE + EXISTING BILL (one query, row locked) --------
#         cursor.execute("""
#             SELECT r.id, r.outlet, r.Emp_ID, r.reservation_outlet_id, r.Current_Status,
#                    e.userName AS employee_name,
#                    (SELECT b.id FROM hotel_tblhotelbills b
#                     WHERE b.reservationID = r.id LIMIT 1) AS existing_bill_id
#             FROM hotel_tblreservation r
#             LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#             WHERE r.id = %s AND r.is_active = 1
#             FOR UPDATE
#         """, (reservationID,))
#         reservation = cursor.fetchone()

#         if not reservation:
#             return {"error": "Reservation not found"}, 404
#         if reservation["existing_bill_id"]:
#             return {"error": "Bill already exists for this reservation"}, 400
#         if reservation["Current_Status"] != "Registered":
#             return {"error": f"Reservation is {reservation['Current_Status']}; only Registered reservations can be billed."}, 400

#         reservationID = reservation["id"]
#         outlet_name = reservation["outlet"]
#         outlet_reservationID = reservation["reservation_outlet_id"]
#         employee_name = reservation["employee_name"] or str(reservation["Emp_ID"])

#         # -------- BILL NUMBER --------
#         bill_no = str(bill_data.get("BillNo") or "").strip()

#         if not bill_no:
#             # frontend didn't reserve one: get it here
#             try:
#                 bill_no = get_next_hotel_bill_no()
#             except Exception as e:
#                 return {"error": f"Could not get a bill number from accounting: {e}"}, 502
#         else:
#             # a number sent by the frontend must not already be used
#             cursor.execute("""
#                 SELECT id FROM hotel_tblhotelbills
#                 WHERE BillNo = %s AND fiscalYear = %s
#                 LIMIT 1
#             """, (bill_no, fiscal_year))
#             if cursor.fetchone():
#                 return {
#                     "error": f"Bill number {bill_no} is already used. Fetch a new bill number and retry.",
#                     "code": "BILL_NO_TAKEN",
#                 }, 409

#         bill_data["BillNo"] = bill_no

#         # -------- MASTER BILL --------
#         cursor.execute("""
#             INSERT INTO hotel_tblhotelbills (
#                 reservationID, outlet_reservationID, fiscalYear, BillNo,
#                 subTotal, DiscountAmt, VAT, Total, PaymentMode,
#                 PartyName, PartyPAN, Date, NoOfNights,
#                 MealplanRevenue, RoomRevenue, ExtraChargeSettlement,
#                 created_at, updated_at, time, Guest_ID
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)
#         """, (
#             reservationID,
#             outlet_reservationID,
#             fiscal_year,
#             bill_no,
#             bill_data.get("subTotal", 0),
#             bill_data.get("DiscountAmt", 0),
#             bill_data.get("VAT", 0),
#             bill_data.get("Total", 0),
#             payment_mode,
#             bill_data.get("PartyName"),
#             bill_data.get("PartyPAN"),
#             bill_data.get("Date"),
#             bill_data.get("NoOfNights"),
#             bill_data.get("MealplanRevenue", 0),
#             bill_data.get("RoomRevenue", 0),
#             bill_data.get("ExtraChargeSettlement", 0),
#             bill_data.get("time", ""),
#             guest_id or None,
#         ))
#         bill_id = cursor.lastrowid

#         # -------- SPLIT PAYMENTS --------
#         if payment_mode == "Split":
#             cursor.executemany("""
#                 INSERT INTO hotel_tblbillpayments
#                     (bill_id, PaymentMode, PaymentAmount, fiscalYear, created_at, updated_at)
#                 VALUES (%s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (bill_id, p.get("paymentMode"), p.get("paymentAmount", 0), fiscal_year)
#                 for p in split_payments
#             ])

#         # -------- FOREX RECEIPTS (international currency actually received) --------
#         if forex_rows:
#             cursor.executemany("""
#                 INSERT INTO hotel_tblbillforexreceipts
#                     (bill_id, Currency, AmountReceived, ExeRate, AmountLocal,
#                      PaymentMode, fiscalYear, created_at, updated_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (bill_id, *row, fiscal_year)
#                 for row in forex_rows
#             ])

#         # -------- BILL DETAILS --------
#         if bill_details:
#             cursor.executemany("""
#                 INSERT INTO hotel_tblbilldetails (
#                     bill_id, Date, RoomNumber, RoomType, RoomRate, RoomRateName,
#                     RateAmt, MealPlan, MealPlanAmt, Amount, Currency, ExeRate,
#                     AmountInclCurr, created_at, updated_at
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (
#                     bill_id,
#                     d.get("Date"),
#                     d.get("RoomNumber"),
#                     d.get("RoomType"),
#                     d.get("RoomRate", 0),
#                     d.get("RoomRateName"),
#                     d.get("RateAmt", 0),
#                     d.get("MealPlan"),
#                     d.get("MealPlanAmt", 0),
#                     d.get("Amount", 0),
#                     d.get("Currency"),
#                     d.get("ExeRate", 0),
#                     d.get("AmountInclCurr", 0),
#                 )
#                 for d in bill_details
#             ])

#         # -------- CHECKOUT (same transaction) --------
#         cursor.execute("""
#             UPDATE hotel_tblreservation
#             SET Current_Status = 'Checked Out', Check_Out = NOW()
#             WHERE id = %s
#         """, (reservationID,))


#         cursor.execute("""
#             UPDATE hotel_tblinhouse_guests
#             SET is_active = 0, checked_out_at = NOW()
#             WHERE reservation_id = %s AND is_active = 1
#         """, (reservationID,))

#         # -------- JOURNAL (must succeed, otherwise the bill is rolled back) --------
#         bill_data["outlet_reservationID"] = outlet_reservationID
#         bill_data["Outlet_Name"] = outlet_name
#         bill_data["Employee"] = employee_name
#         bill_data["billPrintTime"] = ""
#         bill_data["guestID"] = guest_id

#         # try:
#         #     if payment_mode == "Credit":
#         #         post_hotelbill_and_create_journal_for_creditbills(bill_data, bill_id)
#         #     else:
#         #         post_hotelbill_and_create_journal(bill_data, bill_id)

#         # except JournalOutcomeUnknown as ue:
#         #     # Accounting MAY have committed. Roll back Flask; the retry with the
#         #     # same BillNo is idempotent on the Django side.
#         #     _safe_rollback(mydb)
#         #     current_app.logger.error(
#         #         f"JOURNAL OUTCOME UNKNOWN reservationID={reservationID} "
#         #         f"BillNo={bill_no} fy={fiscal_year}: {ue}"
#         #     )
#         #     return {
#         #         "error": "Accounting did not respond in time. The bill may or may not have been "
#         #                  "posted. Retry with the same BillNo; it is safe.",
#         #         "code": "JOURNAL_OUTCOME_UNKNOWN",
#         #         "BillNo": bill_no,
#         #         "reservationID": reservationID,
#         #         "retry_with_same_bill_no": True,
#         #     }, 504

#         # except Exception as je:
#         #     # Definite failure: accounting did not commit.
#         #     _safe_rollback(mydb)
#         #     current_app.logger.error(
#         #         f"Journal rejected reservationID={reservationID} BillNo={bill_no}: {je}"
#         #     )
#         #     return {"error": f"Journal posting failed, so the bill was not created: {je}"}, 502

#         # -------- COMMIT (only after the journal is confirmed) --------
#         mydb.commit()
#         committed = True

#         return jsonify({
#             "message": "Bill + details created successfully",
#             "bill_id": bill_id,
#             "BillNo": bill_no,
#             "total_details": len(bill_details),
#             "total_split_payments": len(split_payments) if payment_mode == "Split" else 0,
#             "total_forex_receipts": len(forex_rows),
#             "journal_posted": True,
#         }), 201

#     except mysql_errors.IntegrityError as e:
#         if mydb and not committed:
#             _safe_rollback(mydb)
#         if e.errno == 1062 and "uniq_billno_fy" in str(e):
#             return {
#                 "error": "This bill number was already used by another bill. Fetch a new bill number and retry.",
#                 "code": "BILL_NO_TAKEN",
#             }, 409
#         current_app.logger.exception("Integrity error in /bill-by-id")
#         return {"error": str(e)}, 500

#     except Exception as e:
#         if mydb and not committed:
#             _safe_rollback(mydb)
#         current_app.logger.exception("Unhandled error in /bill-by-id")
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             try:
#                 cursor.close()
#             except Exception:
#                 pass
#         if mydb:
#             try:
#                 mydb.close()
#             except Exception:
#                 pass

# import re
# from datetime import datetime, date, time as dtime
# from decimal import Decimal

# # tblorderhistory.Date is a varchar stored as YYYY-MM-DD; LEFT(...,10) also
# # tolerates a value with a time appended.
# OUTLET_DATE_SQL = "LEFT(o.Date, 10)"
# OUTLET_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y")
# TIME_FORMATS = ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M")


# def valid_date(datestring):
#     try:
#         regex = re.compile(r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
#         if re.match(regex, datestring):
#             return True
#     except (ValueError, TypeError):
#         return False
#     return False


# def _norm_date(value):
#     """'2026-9-4' -> '2026-09-04'. Returns None if value is empty."""
#     if not value:
#         return None
#     return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")


# def _parse_time(value):
#     """'11:34 AM' / '11:34:00' -> datetime.time, or None if unparseable."""
#     if not value:
#         return None
#     value = str(value).strip().upper()
#     for fmt in TIME_FORMATS:
#         try:
#             return datetime.strptime(value, fmt).time()
#         except ValueError:
#             continue
#     return None


# def _parse_date(value):
#     """date object or string -> date, or None."""
#     if value is None:
#         return None
#     if hasattr(value, "year"):  # already a date/datetime
#         return value.date() if isinstance(value, datetime) else value
#     value = str(value).strip()[:10]
#     for fmt in OUTLET_DATE_FORMATS:
#         try:
#             return datetime.strptime(value, fmt).date()
#         except ValueError:
#             continue
#     return None


# def _sort_datetime(date_value, time_value):
#     d = _parse_date(date_value)
#     if d is None:
#         return datetime.min
#     return datetime.combine(d, _parse_time(time_value) or dtime(0, 0))


# def _date_conditions(column, specific_date, start_date, end_date):
#     if specific_date:
#         return [f"{column} = %s"], [specific_date]
#     conds, params = [], []
#     if start_date:
#         conds.append(f"{column} >= %s")
#         params.append(start_date)
#     if end_date:
#         conds.append(f"{column} <= %s")
#         params.append(end_date)
#     return conds, params


# def _in(n):
#     return ",".join(["%s"] * n)


# def _like(value):
#     """Escape LIKE wildcards in user input, then wrap for a 'contains' match."""
#     escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
#     return f"%{escaped}%"

# @app_file412.route("/bills", methods=["GET"])
# @cross_origin()
# def get_all_bills():
#     # -------- TOKEN --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     # -------- PARAMS --------
#     hotel_name = request.args.get("outlet")  # hotel_company_property.name
#     start_date = request.args.get("start_date")
#     end_date = request.args.get("end_date")
#     specific_date = request.args.get("date")
#     sort_order = request.args.get("order", "desc").lower()

#     if not hotel_name:
#         return {"error": "outlet (hotel name) is required."}, 400
#     for d in (start_date, end_date, specific_date):
#         if d and not valid_date(d):
#             return {"error": "Invalid date supplied."}, 400
#     from datetime import date

#     if not (specific_date or start_date or end_date):
#         specific_date = date.today().strftime("%Y-%m-%d")

#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # -------- RESOLVE HOTEL + ITS OUTLETS --------
#         cursor.execute(
#             "SELECT id FROM hotel_company_property WHERE name = %s LIMIT 1",
#             (hotel_name,),
#         )
#         prop = cursor.fetchone()
#         if not prop:
#             return {"error": "Hotel not found."}, 404

#         cursor.execute(
#             "SELECT DISTINCT Outlet FROM outetNames WHERE company_property_id = %s",
#             (prop["id"],),
#         )
#         outlet_names = [r["Outlet"] for r in cursor.fetchall() if r["Outlet"]]

#         # =====================================================
#         # HOTEL BILLS
#         # =====================================================
#         conds, params = _date_conditions("b.Date", specific_date, start_date, end_date)
#         where = " AND ".join(["r.outlet = %s"] + conds)

#         cursor.execute(
#             f"""
#             SELECT b.*, r.outlet, r.Reservation_Date, r.Current_Status
#             FROM hotel_tblhotelbills b
#             JOIN hotel_tblreservation r ON b.reservationID = r.id
#             WHERE {where}
#             """,
#             tuple([hotel_name] + params),
#         )
#         hotel_bills = cursor.fetchall()

#         if hotel_bills:
#             reservation_ids = [b["reservationID"] for b in hotel_bills]
#             bill_ids = [b["id"] for b in hotel_bills]

#             cursor.execute(
#                 f"""
#                 SELECT rd.Reservation_ID, r.id as room_id, r.room_no, r.room_type, r.outlet, rd.is_current,
#                        tr.rate as room_rate, tr.currency as room_currency,
#                        mp.mp as meal_plan, mp.rate as meal_rate, mp.currency as meal_currency
#                 FROM hotel_tblreservation_details rd
#                 JOIN hotel_tblrooms r ON rd.room_id = r.id
#                 LEFT JOIN hotel_tblrates tr ON tr.room_name = r.room_no AND tr.room_type = r.room_type
#                 LEFT JOIN hotel_tblmeal_price mp ON tr.meal_price_id = mp.id
#                 WHERE rd.Reservation_ID IN ({_in(len(reservation_ids))})
#                 """,
#                 tuple(reservation_ids),
#             )
#             rooms_map = {}
#             for row in cursor.fetchall():
#                 rooms_map.setdefault(row["Reservation_ID"], []).append(row)

#             cursor.execute(
#                 f"""
#                 SELECT * FROM hotel_tblbilldetails
#                 WHERE bill_id IN ({_in(len(bill_ids))})
#                 ORDER BY Date ASC
#                 """,
#                 tuple(bill_ids),
#             )
#             details_map = {}
#             for row in cursor.fetchall():
#                 details_map.setdefault(row["bill_id"], []).append(row)

#             cursor.execute(
#                 f"SELECT * FROM hotel_tblbillpayments WHERE bill_id IN ({_in(len(bill_ids))})",
#                 tuple(bill_ids),
#             )
#             payments_map = {}
#             for row in cursor.fetchall():
#                 payments_map.setdefault(row["bill_id"], []).append(row)

#             for b in hotel_bills:
#                 b["bill_type"] = "hotel"
#                 b["rooms"] = rooms_map.get(b["reservationID"], [])
#                 b["bill_details"] = details_map.get(b["id"], [])
#                 b["split_payments"] = payments_map.get(b["id"], [])
#                 b["_sort_dt"] = _sort_datetime(b.get("Date"), b.get("time"))

#         # =====================================================
#         # OUTLET (RESTAURANT) BILLS
#         # =====================================================
#         outlet_bills = []
#         if outlet_names:
#             conds, params = _date_conditions(
#                 OUTLET_DATE_SQL, specific_date, start_date, end_date
#             )
#             where = " AND ".join([f"o.Outlet_Name IN ({_in(len(outlet_names))})"] + conds)

#             cursor.execute(
#                 f"SELECT o.* FROM tblorderhistory o WHERE {where}",
#                 tuple(outlet_names + params),
#             )
#             outlet_bills = cursor.fetchall()

#         if outlet_bills:
#             order_ids = [o["idtblorderHistory"] for o in outlet_bills]

#             cursor.execute(
#                 f"""
#                 SELECT * FROM tblorder_detailshistory
#                 WHERE order_ID IN ({_in(len(order_ids))})
#                 """,
#                 tuple(order_ids),
#             )
#             items_map = {}
#             for row in cursor.fetchall():
#                 items_map.setdefault(row["order_ID"], []).append(row)

#             cursor.execute(
#                 f"""
#                 SELECT * FROM payment_history
#                 WHERE orderHistoryid IN ({_in(len(order_ids))})
#                 """,
#                 tuple(order_ids),
#             )
#             opay_map = {}
#             for row in cursor.fetchall():
#                 opay_map.setdefault(row["orderHistoryid"], []).append(row)

#             for o in outlet_bills:
#                 oid = o["idtblorderHistory"]
#                 o["bill_type"] = "outlet"
#                 o["items"] = items_map.get(oid, [])
#                 o["split_payments"] = opay_map.get(oid, [])
#                 o["_sort_dt"] = _sort_datetime(o.get("Date"), o.get("billPrintTime"))

#         # =====================================================
#         # GENERAL BILLS (laundry, spa, minibar, transport)
#         # =====================================================
#         conds, params = _date_conditions(
#             "DATE(g.created_at)", specific_date, start_date, end_date
#         )
#         where = " AND ".join(["g.outlet = %s"] + conds)

#         cursor.execute(
#             f"SELECT g.* FROM hotel_generalbills g WHERE {where}",
#             tuple([hotel_name] + params),
#         )
#         general_bills = cursor.fetchall()

#         if general_bills:
#             general_ids = [g["id"] for g in general_bills]

#             cursor.execute(
#                 f"""
#                 SELECT * FROM hotel_generalbill_items
#                 WHERE bill_id IN ({_in(len(general_ids))})
#                 """,
#                 tuple(general_ids),
#             )
#             gitems_map = {}
#             for row in cursor.fetchall():
#                 gitems_map.setdefault(row["bill_id"], []).append(row)

#             for g in general_bills:
#                 g["general_bill_type"] = g["bill_type"]  # LA / SPA / MB / TR
#                 g["bill_type"] = "general"
#                 g["items"] = gitems_map.get(g["id"], [])
#                 g["_sort_dt"] = g["created_at"] or datetime.min

#         # =====================================================
#         # MERGE + SORT
#         # =====================================================
#         all_bills = hotel_bills + outlet_bills + general_bills
#         if not all_bills:
#             return {"message": "No bills found"}, 200

#         all_bills.sort(key=lambda x: x["_sort_dt"], reverse=(sort_order != "asc"))
#         for bill in all_bills:
#             dt = bill.pop("_sort_dt")
#             bill["bill_datetime"] = None if dt == datetime.min else dt.isoformat()

#         return jsonify({
#             "hotel": hotel_name,
#             "total_bills": len(all_bills),
#             "hotel_bill_count": len(hotel_bills),
#             "outlet_bill_count": len(outlet_bills),
#             "general_bill_count": len(general_bills),
#             "bills": all_bills,
#             "filters": {
#                 "start_date": start_date,
#                 "end_date": end_date,
#                 "specific_date": specific_date,
#             },
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()

# @app_file412.route("/void-bill", methods=["POST"])
# @cross_origin()
# def void_bill():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

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

#         # -------- INPUT --------
#         data = request.get_json()
#         bill_id = data.get("bill_id")

#         if not bill_id:
#             return {"error": "bill_id is required"}, 400

#         # -------- CHECK IF BILL EXISTS --------
#         cursor.execute(
#             "SELECT id, status FROM hotel_tblhotelbills WHERE id = %s",
#             (bill_id,)
#         )
#         bill = cursor.fetchone()

#         if not bill:
#             return {"error": "Bill not found"}, 404

#         # -------- OPTIONAL: CHECK IF ALREADY VOID --------
#         if bill["status"] == 0:
#             return {"message": "Bill already voided"}, 200

#         # -------- VOID BILL --------
#         cursor.execute(
#             "UPDATE hotel_tblhotelbills SET status = 0 WHERE id = %s",
#             (bill_id,)
#         )
#         mydb.commit()

#         mydb.close()

#         return {
#             "message": "Bill voided successfully",
#             "bill_id": bill_id
#         }, 200

#     except Exception as e:
#         return {"error": str(e)}, 500



# import requests
# from root.flask_routes.hotel.journal_utils.utils import get_next_hotel_bill_no   # adjust to your utils module path
# @app_file412.route("/hotel-bill-no", methods=["GET"])
# @cross_origin()
# def reserve_hotel_bill_no():
#     # -------- TOKEN --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]
#     except Exception:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     property_id = request.args.get("property_id", type=int)
#     if not property_id:
#         return {"error": "property_id is required."}, 400

#     mydb = None
#     cursor = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         info = get_next_hotel_bill_info(cursor, property_id)
#         mydb.commit()

#         return jsonify({
#             "BillNo": info["bill_no"],
#             "fiscalYear": info["fiscal_year"],
#         }), 201

#     except ValueError as e:
#         # property not found / fiscal year not configured
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

from root.flask_routes.hotel.journal_utils.utils import post_hotelbill_and_create_journal, post_hotelbill_and_create_journal_for_creditbills, void_hotelbill

load_dotenv()

app_file412 = Blueprint('app_file412', __name__)

@app_file412.route("/bill", methods=["POST"])
@cross_origin()
def create_bills():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True)

        bill_data = request.get_json() or {}

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
        outlet_reservationID = bill_data.get("outlet_reservationID")
        bill_details = bill_data.get("bill_details", [])
        split_payments = bill_data.get("SplitPaymentDetailsList", [])

        if not outlet_reservationID:
            return {"error": "outlet_reservationID is required"}, 400

        # -------- STEP 1: FETCH reservationID + outlet + employee --------
        cursor.execute("""
            SELECT r.id, r.outlet, r.Emp_ID, e.userName AS employee_name
            FROM hotel_tblreservation r
            LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
            WHERE r.reservation_outlet_id = %s
        """, (outlet_reservationID,))
        reservation = cursor.fetchone()

        if not reservation:
            return {"error": "Reservation not found"}, 404

        reservationID = reservation["id"]
        outlet_name = reservation["outlet"]
        employee_name = reservation["employee_name"] or str(reservation["Emp_ID"])

        # -------- CHECK EXISTING BILL --------
        cursor.execute("""
            SELECT id FROM hotel_tblhotelbills 
            WHERE reservationID = %s
        """, (reservationID,))
        existing = cursor.fetchone()

        if existing:
            return {"error": "Bill already exists for this reservation"}, 400

        # -------- VALIDATE SPLIT PAYMENTS UP FRONT --------
        if bill_data.get("PaymentMode") == "Split" and not split_payments:
            return {"error": "PaymentMode is 'Split' but SplitPaymentDetailsList is empty"}, 400

        # # -------- START TRANSACTION --------
        # mydb.start_transaction()

        # -------- INSERT MASTER BILL --------
        cursor.execute("""
            INSERT INTO hotel_tblhotelbills (
                reservationID,
                outlet_reservationID,
                fiscalYear,
                BillNo,
                subTotal,
                DiscountAmt,
                VAT,
                Total,
                PaymentMode,
                PartyName,
                PartyPAN,
                Date,
                NoOfNights,
                MealplanRevenue,
                RoomRevenue,
                ExtraChargeSettlement,
                created_at,
                updated_at,
                time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
        """, (
            reservationID,
            outlet_reservationID,
            bill_data.get("fiscalYear"),
            bill_data.get("BillNo"),
            bill_data.get("subTotal", 0),
            bill_data.get("DiscountAmt", 0),
            bill_data.get("VAT", 0),
            bill_data.get("Total", 0),
            bill_data.get("PaymentMode"),
            bill_data.get("PartyName"),
            bill_data.get("PartyPAN"),
            bill_data.get("Date"),
            bill_data.get("NoOfNights"),
            bill_data.get("MealplanRevenue", 0),
            bill_data.get("RoomRevenue", 0),
            bill_data.get("ExtraChargeSettlement", 0),
            bill_data.get("time", "")
        ))

        bill_id = cursor.lastrowid

        # -------- INSERT SPLIT PAYMENTS --------
        if bill_data.get("PaymentMode") == "Split" and split_payments:
            payment_query = """
                INSERT INTO hotel_tblbillpayments (
                    bill_id, PaymentMode, PaymentAmount, fiscalYear, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            payment_values = [
                (
                    bill_id,
                    p.get("paymentMode"),
                    p.get("paymentAmount", 0),
                    bill_data.get("fiscalYear"),
                )
                for p in split_payments
            ]
            cursor.executemany(payment_query, payment_values)

        # -------- INSERT BILL DETAILS --------
        if bill_details:
            detail_query = """
                INSERT INTO hotel_tblbilldetails (
                    bill_id,
                    Date,
                    RoomNumber,
                    RoomType,
                    RoomRate,
                    RoomRateName,
                    RateAmt,
                    MealPlan,
                    MealPlanAmt,
                    Amount,
                    Currency,
                    ExeRate,
                    AmountInclCurr,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """

            detail_values = []
            for d in bill_details:
                detail_values.append((
                    bill_id,
                    d.get("Date"),
                    d.get("RoomNumber"),
                    d.get("RoomType"),
                    d.get("RoomRate", 0),
                    d.get("RoomRateName"),
                    d.get("RateAmt", 0),
                    d.get("MealPlan"),
                    d.get("MealPlanAmt", 0),
                    d.get("Amount", 0),
                    d.get("Currency"),
                    d.get("ExeRate", 0),
                    d.get("AmountInclCurr", 0)
                ))

            cursor.executemany(detail_query, detail_values)

        update_query = """
            UPDATE hotel_tblreservation
            SET Current_Status = %s
            WHERE id = %s
        """

        cursor.execute(update_query, ("Checked Out", reservationID))

        # -------- COMMIT --------
        mydb.commit()
        mydb.close()

        # -------- JOURNAL ENTRY (best-effort, after commit) --------
        bill_data["Outlet_Name"] = outlet_name
        bill_data["Employee"] = employee_name
        bill_data["billPrintTime"] = ""

        if bill_data.get("PaymentMode") == "Credit":
            post_hotelbill_and_create_journal_for_creditbills(bill_data, bill_id)
        else:
            post_hotelbill_and_create_journal(bill_data, bill_id)

        return jsonify({
            "message": "Bill + details created successfully",
            "bill_id": bill_id,
            "total_details": len(bill_details),
            "total_split_payments": len(split_payments) if bill_data.get("PaymentMode") == "Split" else 0
        }), 201

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500



from root.flask_routes.hotel.journal_utils.utils import get_next_hotel_bill_no, get_next_hotel_bill_info   # adjust to your utils module path

import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import mysql.connector
from mysql.connector import errors as mysql_errors
from flask import request, jsonify, current_app
from flask_cors import cross_origin


def _safe_rollback(mydb):
    try:
        mydb.rollback()
    except Exception:
        pass


from root.flask_routes.hotel.journal_utils.utils import JournalOutcomeUnknown, PAYMENT_MODE_LEDGERS, post_party_payment_journal


def _parse_forex_receipts(items, bill_payment_mode):
    """
    Validate ForexReceiptsList from the frontend.

    Each item: {"currency": "USD", "amountReceived": 100, "exeRate": 150, "paymentMode": "Cash"}

    - AmountLocal is always computed here (amountReceived * exeRate), never trusted from the frontend.
    - paymentMode falls back to the bill's PaymentMode, except for Split bills,
      where each item must say how it was paid.

    Returns (rows, error). rows are tuples of
    (Currency, AmountReceived, ExeRate, AmountLocal, PaymentMode).
    """
    rows = []
    for i, f in enumerate(items, start=1):
        if not isinstance(f, dict):
            return None, f"ForexReceiptsList item {i} must be an object."

        currency = str(f.get("currency") or f.get("Currency") or "").strip().upper()
        if not currency:
            return None, f"ForexReceiptsList item {i}: currency is required."

        mode = str(f.get("paymentMode") or f.get("PaymentMode") or "").strip()
        if not mode and bill_payment_mode != "Split":
            mode = bill_payment_mode or ""
        if not mode:
            return None, f"ForexReceiptsList item {i}: paymentMode is required."

        try:
            amount = Decimal(str(f.get("amountReceived")))
            rate = Decimal(str(f.get("exeRate")))
        except (InvalidOperation, TypeError, ValueError):
            return None, f"ForexReceiptsList item {i}: amountReceived and exeRate must be numbers."

        if not amount.is_finite() or not rate.is_finite() or amount <= 0 or rate <= 0:
            return None, f"ForexReceiptsList item {i}: amountReceived and exeRate must be greater than 0."

        local = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rows.append((currency, amount, rate, local, mode))

    return rows, None


# def _parse_settlement_payments(items):
#     cleaned = []
#     for i, p in enumerate(items, 1):
#         if not isinstance(p, dict):
#             return None, f"GuestSettlementList[{i}] must be an object."
#         mode = p.get("paymentMode")
#         if mode not in PAYMENT_MODE_LEDGERS:
#             return None, f"GuestSettlementList[{i}]: unsupported paymentMode '{mode}'."
#         try:
#             amt = round(Decimal(str(p.get("paymentAmount"))), 2)
#         except Exception:
#             return None, f"GuestSettlementList[{i}]: invalid paymentAmount."
#         if amt <= 0:
#             return None, f"GuestSettlementList[{i}]: paymentAmount must be greater than 0."
#         cleaned.append({
#             "paymentMode": mode,
#             "paymentAmount": amt,
#             "billNo": str(p.get("billNo") or "").strip(),
#         })
#     return cleaned, None

from datetime import date

def _parse_settlement_payments(items):
    cleaned = []
    for i, p in enumerate(items, 1):
        if not isinstance(p, dict):
            return None, f"GuestSettlementList[{i}] must be an object."
        mode = p.get("paymentMode")
        if mode not in PAYMENT_MODE_LEDGERS:
            return None, f"GuestSettlementList[{i}]: unsupported paymentMode '{mode}'."
        try:
            amt = round(Decimal(str(p.get("paymentAmount"))), 2)
        except Exception:
            return None, f"GuestSettlementList[{i}]: invalid paymentAmount."
        if amt <= 0:
            return None, f"GuestSettlementList[{i}]: paymentAmount must be greater than 0."
        cleaned.append({"paymentMode": mode, "paymentAmount": amt})
    return cleaned, None


#latest 
# @app_file412.route("/bill-by-id", methods=["POST"])
# @cross_origin()
# def create_bills_by_reservation_id():
#     mydb = None
#     cursor = None
#     committed = False
#     try:
#         bill_data = request.get_json() or {}

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT (validated before any DB work) --------
#         reservationID = bill_data.get("reservationID") or bill_data.get("Reservation_ID")
#         bill_details = bill_data.get("bill_details") or []
#         split_payments = bill_data.get("SplitPaymentDetailsList") or []
#         forex_items = bill_data.get("ForexReceiptsList") or []
#         payment_mode = bill_data.get("PaymentMode")
#         fiscal_year = bill_data.get("fiscalYear")
#         guest_id = str(bill_data.get("guestID") or "").strip()

#         if not fiscal_year:
#             return {"error": "fiscalYear is required"}, 400
#         if payment_mode == "Credit":
#             if not guest_id:
#                 return {"error": "guestID is required for credit bills."}, 400
#             if not (bill_data.get("PartyName") or "").strip():
#                 return {"error": "PartyName is required for credit bills."}, 400
#         if not reservationID:
#             return {"error": "reservationID is required"}, 400
#         if (
#             not isinstance(bill_details, list)
#             or not isinstance(split_payments, list)
#             or not isinstance(forex_items, list)
#         ):
#             return {"error": "bill_details, SplitPaymentDetailsList and ForexReceiptsList must be lists."}, 400
#         if payment_mode == "Split" and not split_payments:
#             return {"error": "PaymentMode is 'Split' but SplitPaymentDetailsList is empty"}, 400
#         if payment_mode == "Credit" and forex_items:
#             return {"error": "ForexReceiptsList cannot be sent for credit bills (no money is received)."}, 400

#         forex_rows, forex_err = _parse_forex_receipts(forex_items, payment_mode)
#         if forex_err:
#             return {"error": forex_err}, 400


#         settlement_items = bill_data.get("GuestSettlementList") or []

#         if not isinstance(settlement_items, list):
#             return {"error": "GuestSettlementList must be a list."}, 400
#         if settlement_items:
#             if payment_mode in ("Credit", "Complimentary", "Non Chargeable"):
#                 return {"error": f"GuestSettlementList is not allowed for {payment_mode} bills."}, 400
#             if not guest_id:
#                 return {"error": "guestID is required to settle a guest ledger."}, 400

#         settlement_payments, st_err = _parse_settlement_payments(settlement_items)
#         if st_err:
#             return {"error": st_err}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- RESERVATION + EMPLOYEE + EXISTING BILL (one query, row locked) --------
#         cursor.execute("""
#             SELECT r.id, r.outlet, r.Emp_ID, r.reservation_outlet_id, r.Current_Status,
#                    e.userName AS employee_name,
#                    (SELECT b.id FROM hotel_tblhotelbills b
#                     WHERE b.reservationID = r.id LIMIT 1) AS existing_bill_id
#             FROM hotel_tblreservation r
#             LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#             WHERE r.id = %s AND r.is_active = 1
#             FOR UPDATE
#         """, (reservationID,))
#         reservation = cursor.fetchone()

#         if not reservation:
#             return {"error": "Reservation not found"}, 404
#         if reservation["existing_bill_id"]:
#             return {"error": "Bill already exists for this reservation"}, 400
#         if reservation["Current_Status"] != "Registered":
#             return {"error": f"Reservation is {reservation['Current_Status']}; only Registered reservations can be billed."}, 400

#         reservationID = reservation["id"]
#         outlet_name = reservation["outlet"]
#         outlet_reservationID = reservation["reservation_outlet_id"]
#         employee_name = reservation["employee_name"] or str(reservation["Emp_ID"])

#         # -------- BILL NUMBER --------
#         bill_no = str(bill_data.get("BillNo") or "").strip()

#         if not bill_no:
#             # frontend didn't reserve one: get it here
#             try:
#                 bill_no = get_next_hotel_bill_no()
#             except Exception as e:
#                 return {"error": f"Could not get a bill number from accounting: {e}"}, 502
#         else:
#             # a number sent by the frontend must not already be used
#             cursor.execute("""
#                 SELECT id FROM hotel_tblhotelbills
#                 WHERE BillNo = %s AND fiscalYear = %s
#                 LIMIT 1
#             """, (bill_no, fiscal_year))
#             if cursor.fetchone():
#                 return {
#                     "error": f"Bill number {bill_no} is already used. Fetch a new bill number and retry.",
#                     "code": "BILL_NO_TAKEN",
#                 }, 409

#         bill_data["BillNo"] = bill_no

#         # -------- MASTER BILL --------
#         cursor.execute("""
#             INSERT INTO hotel_tblhotelbills (
#                 reservationID, outlet_reservationID, fiscalYear, BillNo,
#                 subTotal, DiscountAmt, VAT, Total, PaymentMode,
#                 PartyName, PartyPAN, Date, NoOfNights,
#                 MealplanRevenue, RoomRevenue, ExtraChargeSettlement,
#                 created_at, updated_at, time, Guest_ID
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)
#         """, (
#             reservationID,
#             outlet_reservationID,
#             fiscal_year,
#             bill_no,
#             bill_data.get("subTotal", 0),
#             bill_data.get("DiscountAmt", 0),
#             bill_data.get("VAT", 0),
#             bill_data.get("Total", 0),
#             payment_mode,
#             bill_data.get("PartyName"),
#             bill_data.get("PartyPAN"),
#             bill_data.get("Date"),
#             bill_data.get("NoOfNights"),
#             bill_data.get("MealplanRevenue", 0),
#             bill_data.get("RoomRevenue", 0),
#             bill_data.get("ExtraChargeSettlement", 0),
#             bill_data.get("time", ""),
#             guest_id or None,
#         ))
#         bill_id = cursor.lastrowid

#         # -------- SPLIT PAYMENTS --------
#         if payment_mode == "Split":
#             cursor.executemany("""
#                 INSERT INTO hotel_tblbillpayments
#                     (bill_id, PaymentMode, PaymentAmount, fiscalYear, created_at, updated_at)
#                 VALUES (%s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (bill_id, p.get("paymentMode"), p.get("paymentAmount", 0), fiscal_year)
#                 for p in split_payments
#             ])

#         # -------- FOREX RECEIPTS (international currency actually received) --------
#         if forex_rows:
#             cursor.executemany("""
#                 INSERT INTO hotel_tblbillforexreceipts
#                     (bill_id, Currency, AmountReceived, ExeRate, AmountLocal,
#                      PaymentMode, fiscalYear, created_at, updated_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (bill_id, *row, fiscal_year)
#                 for row in forex_rows
#             ])

#         # -------- BILL DETAILS --------
#         if bill_details:
#             cursor.executemany("""
#                 INSERT INTO hotel_tblbilldetails (
#                     bill_id, Date, RoomNumber, RoomType, RoomRate, RoomRateName,
#                     RateAmt, MealPlan, MealPlanAmt, Amount, Currency, ExeRate,
#                     AmountInclCurr, created_at, updated_at
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#             """, [
#                 (
#                     bill_id,
#                     d.get("Date"),
#                     d.get("RoomNumber"),
#                     d.get("RoomType"),
#                     d.get("RoomRate", 0),
#                     d.get("RoomRateName"),
#                     d.get("RateAmt", 0),
#                     d.get("MealPlan"),
#                     d.get("MealPlanAmt", 0),
#                     d.get("Amount", 0),
#                     d.get("Currency"),
#                     d.get("ExeRate", 0),
#                     d.get("AmountInclCurr", 0),
#                 )
#                 for d in bill_details
#             ])

#         # -------- CHECKOUT (same transaction) --------
#         cursor.execute("""
#             UPDATE hotel_tblreservation
#             SET Current_Status = 'Checked Out', Check_Out = NOW()
#             WHERE id = %s
#         """, (reservationID,))

#         # cursor.execute("""
#         #     UPDATE hotel_tblreservation_details
#         #     SET is_current = 0
#         #     WHERE Reservation_ID = %s AND is_current = 1
#         # """, (reservationID,))

#         cursor.execute("""
#             UPDATE hotel_tblinhouse_guests
#             SET is_active = 0, checked_out_at = NOW()
#             WHERE reservation_id = %s AND is_active = 1
#         """, (reservationID,))

#         # -------- MARK CHECKED-OUT ROOMS DIRTY (same transaction) --------
#         cursor.execute("""
#             INSERT INTO hotel_tblhousekeeping
#                 (room_id, hk_date, hk_status, cleaned_at, cleaned_by, remarks)
#             SELECT rd.room_id, %s, 'Dirty', NULL, NULL, 'Checkout'
#             FROM hotel_tblreservation_details rd
#             WHERE rd.Reservation_ID = %s AND rd.is_current = 1 AND rd.is_active = 1
#             ON DUPLICATE KEY UPDATE
#                 hk_status = 'Dirty', cleaned_at = NULL,
#                 cleaned_by = NULL, remarks = VALUES(remarks)
#         """, (date.today(), reservationID))

#         # -------- JOURNAL (must succeed, otherwise the bill is rolled back) --------
#         bill_data["outlet_reservationID"] = outlet_reservationID
#         bill_data["Outlet_Name"] = outlet_name
#         bill_data["Employee"] = employee_name
#         bill_data["billPrintTime"] = ""
#         bill_data["guestID"] = guest_id

#         try:
#             if payment_mode == "Credit":
#                 post_hotelbill_and_create_journal_for_creditbills(bill_data, bill_id)
#             else:
#                 post_hotelbill_and_create_journal(bill_data, bill_id)

#         except JournalOutcomeUnknown as ue:
#             # Accounting MAY have committed. Roll back Flask; the retry with the
#             # same BillNo is idempotent on the Django side.
#             _safe_rollback(mydb)
#             current_app.logger.error(
#                 f"JOURNAL OUTCOME UNKNOWN reservationID={reservationID} "
#                 f"BillNo={bill_no} fy={fiscal_year}: {ue}"
#             )
#             return {
#                 "error": "Accounting did not respond in time. The bill may or may not have been "
#                          "posted. Retry with the same BillNo; it is safe.",
#                 "code": "JOURNAL_OUTCOME_UNKNOWN",
#                 "BillNo": bill_no,
#                 "reservationID": reservationID,
#                 "retry_with_same_bill_no": True,
#             }, 504

#         except Exception as je:
#             # Definite failure: accounting did not commit.
#             _safe_rollback(mydb)
#             current_app.logger.error(
#                 f"Journal rejected reservationID={reservationID} BillNo={bill_no}: {je}"
#             )
#             return {"error": f"Journal posting failed, so the bill was not created: {je}"}, 502

#         # # -------- GUEST LEDGER SETTLEMENT (room charges etc. paid at billing) --------
#         # if settlement_payments:
#         #     ok, pay_result = post_party_payment_journal({
#         #         "customer_ledger_id": guest_id,
#         #         "payments": settlement_payments,
#         #         "Employee": employee_name,
#         #         "date": bill_data.get("Date"),
#         #         "bill_no": bill_no,
#         #         # "particular": f"Settlement received with bill no: {bill_no}",
#         #         "particular": f"Settlement received with bill no: {bill_no}",
#         #         "reference": f"SETTLE-{bill_no}",
#         #     })
#         #     if not ok:
#         #         _safe_rollback(mydb)
#         #         current_app.logger.error(
#         #             f"Settlement failed reservationID={reservationID} BillNo={bill_no}: {pay_result}"
#         #         )
#         #         return {
#         #             "error": f"Guest settlement failed, so the bill was not created: {pay_result}",
#         #             "code": "SETTLEMENT_POST_FAILED",
#         #             "BillNo": bill_no,
#         #             "retry_with_same_bill_no": True,
#         #         }, 502

#         # -------- GUEST LEDGER SETTLEMENT (room charges etc. paid at billing) --------
#         if settlement_payments:
#             ok, pay_result = post_party_payment_journal({
#                 "customer_ledger_id": guest_id,
#                 "payments": settlement_payments,
#                 "Employee": employee_name,
#                 "date": bill_data.get("Date"),
#                 "bill_no": bill_no,
#                 "particular": f"Settlement received",
#                 "reference": f"SETTLE-{bill_no}",
#             })
#             if not ok:
#                 _safe_rollback(mydb)
#                 current_app.logger.error(
#                     f"Settlement failed reservationID={reservationID} BillNo={bill_no}: {pay_result}"
#                 )
#                 return {
#                     "error": f"Guest settlement failed, so the bill was not created: {pay_result}",
#                     "code": "SETTLEMENT_POST_FAILED",
#                     "BillNo": bill_no,
#                     "retry_with_same_bill_no": True,
#                 }, 502

#         # -------- COMMIT (only after the journal is confirmed) --------
#         mydb.commit()
#         committed = True

#         return jsonify({
#             "message": "Bill + details created successfully",
#             "bill_id": bill_id,
#             "BillNo": bill_no,
#             "total_details": len(bill_details),
#             "total_split_payments": len(split_payments) if payment_mode == "Split" else 0,
#             "total_forex_receipts": len(forex_rows),
#             "total_settlements": len(settlement_payments),
#             "journal_posted": True,
#         }), 201

#     except mysql_errors.IntegrityError as e:
#         if mydb and not committed:
#             _safe_rollback(mydb)
#         if e.errno == 1062 and "uniq_billno_fy" in str(e):
#             return {
#                 "error": "This bill number was already used by another bill. Fetch a new bill number and retry.",
#                 "code": "BILL_NO_TAKEN",
#             }, 409
#         current_app.logger.exception("Integrity error in /bill-by-id")
#         return {"error": str(e)}, 500

#     except Exception as e:
#         if mydb and not committed:
#             _safe_rollback(mydb)
#         current_app.logger.exception("Unhandled error in /bill-by-id")
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             try:
#                 cursor.close()
#             except Exception:
#                 pass
#         if mydb:
#             try:
#                 mydb.close()
#             except Exception:
#                 pass


from root.flask_routes.hotel.hotel_utils.utils import log_hotel_activity, get_employee_name   # <-- new

@app_file412.route("/bill-by-id", methods=["POST"])
@cross_origin()
def create_bills_by_reservation_id():
    mydb = None
    cursor = None
    committed = False
    try:
        bill_data = request.get_json() or {}

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

        # -------- INPUT (validated before any DB work) --------
        reservationID = bill_data.get("reservationID") or bill_data.get("Reservation_ID")
        bill_details = bill_data.get("bill_details") or []
        split_payments = bill_data.get("SplitPaymentDetailsList") or []
        forex_items = bill_data.get("ForexReceiptsList") or []
        payment_mode = bill_data.get("PaymentMode")
        fiscal_year = bill_data.get("fiscalYear")
        guest_id = str(bill_data.get("guestID") or "").strip()
        log_emp_id = bill_data.get("Emp_ID")   # <-- new: employee doing the checkout (for the activity log)

        if not fiscal_year:
            return {"error": "fiscalYear is required"}, 400
        if payment_mode == "Credit":
            if not guest_id:
                return {"error": "guestID is required for credit bills."}, 400
            if not (bill_data.get("PartyName") or "").strip():
                return {"error": "PartyName is required for credit bills."}, 400
        if not reservationID:
            return {"error": "reservationID is required"}, 400
        if (
            not isinstance(bill_details, list)
            or not isinstance(split_payments, list)
            or not isinstance(forex_items, list)
        ):
            return {"error": "bill_details, SplitPaymentDetailsList and ForexReceiptsList must be lists."}, 400
        if payment_mode == "Split" and not split_payments:
            return {"error": "PaymentMode is 'Split' but SplitPaymentDetailsList is empty"}, 400
        if payment_mode == "Credit" and forex_items:
            return {"error": "ForexReceiptsList cannot be sent for credit bills (no money is received)."}, 400

        forex_rows, forex_err = _parse_forex_receipts(forex_items, payment_mode)
        if forex_err:
            return {"error": forex_err}, 400


        settlement_items = bill_data.get("GuestSettlementList") or []

        if not isinstance(settlement_items, list):
            return {"error": "GuestSettlementList must be a list."}, 400
        if settlement_items:
            if payment_mode in ("Credit", "Complimentary", "Non Chargeable"):
                return {"error": f"GuestSettlementList is not allowed for {payment_mode} bills."}, 400
            if not guest_id:
                return {"error": "guestID is required to settle a guest ledger."}, 400

        settlement_payments, st_err = _parse_settlement_payments(settlement_items)
        if st_err:
            return {"error": st_err}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESERVATION + EMPLOYEE + EXISTING BILL (one query, row locked) --------
        cursor.execute("""
            SELECT r.id, r.outlet, r.Emp_ID, r.reservation_outlet_id, r.Current_Status,
                   e.userName AS employee_name,
                   (SELECT b.id FROM hotel_tblhotelbills b
                    WHERE b.reservationID = r.id LIMIT 1) AS existing_bill_id
            FROM hotel_tblreservation r
            LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
            WHERE r.id = %s AND r.is_active = 1
            FOR UPDATE
        """, (reservationID,))
        reservation = cursor.fetchone()

        if not reservation:
            return {"error": "Reservation not found"}, 404
        if reservation["existing_bill_id"]:
            return {"error": "Bill already exists for this reservation"}, 400
        if reservation["Current_Status"] != "Registered":
            return {"error": f"Reservation is {reservation['Current_Status']}; only Registered reservations can be billed."}, 400

        reservationID = reservation["id"]
        outlet_name = reservation["outlet"]
        outlet_reservationID = reservation["reservation_outlet_id"]
        employee_name = reservation["employee_name"] or str(reservation["Emp_ID"])

        # -------- BILL NUMBER --------
        bill_no = str(bill_data.get("BillNo") or "").strip()

        if not bill_no:
            # frontend didn't reserve one: get it here
            try:
                bill_no = get_next_hotel_bill_no()
            except Exception as e:
                return {"error": f"Could not get a bill number from accounting: {e}"}, 502
        else:
            # a number sent by the frontend must not already be used
            cursor.execute("""
                SELECT id FROM hotel_tblhotelbills
                WHERE BillNo = %s AND fiscalYear = %s
                LIMIT 1
            """, (bill_no, fiscal_year))
            if cursor.fetchone():
                return {
                    "error": f"Bill number {bill_no} is already used. Fetch a new bill number and retry.",
                    "code": "BILL_NO_TAKEN",
                }, 409

        bill_data["BillNo"] = bill_no

        # -------- MASTER BILL --------
        cursor.execute("""
            INSERT INTO hotel_tblhotelbills (
                reservationID, outlet_reservationID, fiscalYear, BillNo,
                subTotal, DiscountAmt, VAT, Total, PaymentMode,
                PartyName, PartyPAN, Date, NoOfNights,
                MealplanRevenue, RoomRevenue, ExtraChargeSettlement,
                created_at, updated_at, time, Guest_ID
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)
        """, (
            reservationID,
            outlet_reservationID,
            fiscal_year,
            bill_no,
            bill_data.get("subTotal", 0),
            bill_data.get("DiscountAmt", 0),
            bill_data.get("VAT", 0),
            bill_data.get("Total", 0),
            payment_mode,
            bill_data.get("PartyName"),
            bill_data.get("PartyPAN"),
            bill_data.get("Date"),
            bill_data.get("NoOfNights"),
            bill_data.get("MealplanRevenue", 0),
            bill_data.get("RoomRevenue", 0),
            bill_data.get("ExtraChargeSettlement", 0),
            bill_data.get("time", ""),
            guest_id or None,
        ))
        bill_id = cursor.lastrowid

        # -------- SPLIT PAYMENTS --------
        if payment_mode == "Split":
            cursor.executemany("""
                INSERT INTO hotel_tblbillpayments
                    (bill_id, PaymentMode, PaymentAmount, fiscalYear, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, [
                (bill_id, p.get("paymentMode"), p.get("paymentAmount", 0), fiscal_year)
                for p in split_payments
            ])

        # -------- FOREX RECEIPTS (international currency actually received) --------
        if forex_rows:
            cursor.executemany("""
                INSERT INTO hotel_tblbillforexreceipts
                    (bill_id, Currency, AmountReceived, ExeRate, AmountLocal,
                     PaymentMode, fiscalYear, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, [
                (bill_id, *row, fiscal_year)
                for row in forex_rows
            ])

        # -------- BILL DETAILS --------
        if bill_details:
            cursor.executemany("""
                INSERT INTO hotel_tblbilldetails (
                    bill_id, Date, RoomNumber, RoomType, RoomRate, RoomRateName,
                    RateAmt, MealPlan, MealPlanAmt, Amount, Currency, ExeRate,
                    AmountInclCurr, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, [
                (
                    bill_id,
                    d.get("Date"),
                    d.get("RoomNumber"),
                    d.get("RoomType"),
                    d.get("RoomRate", 0),
                    d.get("RoomRateName"),
                    d.get("RateAmt", 0),
                    d.get("MealPlan"),
                    d.get("MealPlanAmt", 0),
                    d.get("Amount", 0),
                    d.get("Currency"),
                    d.get("ExeRate", 0),
                    d.get("AmountInclCurr", 0),
                )
                for d in bill_details
            ])

        # -------- CHECKOUT (same transaction) --------
        cursor.execute("""
            UPDATE hotel_tblreservation
            SET Current_Status = 'Checked Out', Check_Out = NOW()
            WHERE id = %s
        """, (reservationID,))

        # cursor.execute("""
        #     UPDATE hotel_tblreservation_details
        #     SET is_current = 0
        #     WHERE Reservation_ID = %s AND is_current = 1
        # """, (reservationID,))

        cursor.execute("""
            UPDATE hotel_tblinhouse_guests
            SET is_active = 0, checked_out_at = NOW()
            WHERE reservation_id = %s AND is_active = 1
        """, (reservationID,))

        # -------- MARK CHECKED-OUT ROOMS DIRTY (same transaction) --------
        cursor.execute("""
            INSERT INTO hotel_tblhousekeeping
                (room_id, hk_date, hk_status, cleaned_at, cleaned_by, remarks)
            SELECT rd.room_id, %s, 'Dirty', NULL, NULL, 'Checkout'
            FROM hotel_tblreservation_details rd
            WHERE rd.Reservation_ID = %s AND rd.is_current = 1 AND rd.is_active = 1
            ON DUPLICATE KEY UPDATE
                hk_status = 'Dirty', cleaned_at = NULL,
                cleaned_by = NULL, remarks = VALUES(remarks)
        """, (date.today(), reservationID))

        # -------- JOURNAL (must succeed, otherwise the bill is rolled back) --------
        bill_data["outlet_reservationID"] = outlet_reservationID
        bill_data["Outlet_Name"] = outlet_name
        bill_data["Employee"] = employee_name
        bill_data["billPrintTime"] = ""
        bill_data["guestID"] = guest_id

        try:
            if payment_mode == "Credit":
                post_hotelbill_and_create_journal_for_creditbills(bill_data, bill_id)
            else:
                post_hotelbill_and_create_journal(bill_data, bill_id)

        except JournalOutcomeUnknown as ue:
            # Accounting MAY have committed. Roll back Flask; the retry with the
            # same BillNo is idempotent on the Django side.
            _safe_rollback(mydb)
            current_app.logger.error(
                f"JOURNAL OUTCOME UNKNOWN reservationID={reservationID} "
                f"BillNo={bill_no} fy={fiscal_year}: {ue}"
            )
            return {
                "error": "Accounting did not respond in time. The bill may or may not have been "
                         "posted. Retry with the same BillNo; it is safe.",
                "code": "JOURNAL_OUTCOME_UNKNOWN",
                "BillNo": bill_no,
                "reservationID": reservationID,
                "retry_with_same_bill_no": True,
            }, 504

        except Exception as je:
            # Definite failure: accounting did not commit.
            _safe_rollback(mydb)
            current_app.logger.error(
                f"Journal rejected reservationID={reservationID} BillNo={bill_no}: {je}"
            )
            return {"error": f"Journal posting failed, so the bill was not created: {je}"}, 502

        # # -------- GUEST LEDGER SETTLEMENT (room charges etc. paid at billing) --------
        # if settlement_payments:
        #     ok, pay_result = post_party_payment_journal({
        #         "customer_ledger_id": guest_id,
        #         "payments": settlement_payments,
        #         "Employee": employee_name,
        #         "date": bill_data.get("Date"),
        #         "bill_no": bill_no,
        #         # "particular": f"Settlement received with bill no: {bill_no}",
        #         "particular": f"Settlement received with bill no: {bill_no}",
        #         "reference": f"SETTLE-{bill_no}",
        #     })
        #     if not ok:
        #         _safe_rollback(mydb)
        #         current_app.logger.error(
        #             f"Settlement failed reservationID={reservationID} BillNo={bill_no}: {pay_result}"
        #         )
        #         return {
        #             "error": f"Guest settlement failed, so the bill was not created: {pay_result}",
        #             "code": "SETTLEMENT_POST_FAILED",
        #             "BillNo": bill_no,
        #             "retry_with_same_bill_no": True,
        #         }, 502

        # -------- GUEST LEDGER SETTLEMENT (room charges etc. paid at billing) --------
        if settlement_payments:
            ok, pay_result = post_party_payment_journal({
                "customer_ledger_id": guest_id,
                "payments": settlement_payments,
                "Employee": employee_name,
                "date": bill_data.get("Date"),
                "bill_no": bill_no,
                "particular": f"Settlement received",
                "reference": f"SETTLE-{bill_no}",
            })
            if not ok:
                _safe_rollback(mydb)
                current_app.logger.error(
                    f"Settlement failed reservationID={reservationID} BillNo={bill_no}: {pay_result}"
                )
                return {
                    "error": f"Guest settlement failed, so the bill was not created: {pay_result}",
                    "code": "SETTLEMENT_POST_FAILED",
                    "BillNo": bill_no,
                    "retry_with_same_bill_no": True,
                }, 502

        # -------- ACTIVITY LOG (same transaction; logging problems never block the checkout) --------   # <-- new
        try:
            log_emp_name = get_employee_name(cursor, log_emp_id)

            cursor.execute("""
                SELECT rm.room_no
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblrooms rm ON rm.id = rd.room_id
                WHERE rd.Reservation_ID = %s AND rd.is_current = 1 AND rd.is_active = 1
                ORDER BY rm.room_no
            """, (reservationID,))
            room_nos = [str(r["room_no"]) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT name FROM hotel_tblinhouse_guests
                WHERE reservation_id = %s AND is_primary = 1
                ORDER BY idguest DESC LIMIT 1
            """, (reservationID,))
            primary_row = cursor.fetchone()
            guest_label = primary_row["name"] if primary_row else None

            description = (
                f"{log_emp_name or 'Employee'} checked out reservation #{reservationID}"
                + (f" ({guest_label})" if guest_label else "")
                + (f" from room {', '.join(room_nos)}" if room_nos else "")
                + f". Bill {bill_no}, {payment_mode}, total {bill_data.get('Total', 0)}"
            )

            log_hotel_activity(
                cursor,
                outlet=outlet_name,
                action="CHECKED_OUT",
                reservation_id=reservationID,
                description=description,
                employee_id=log_emp_id,
                employee_name=log_emp_name,
                details={
                    "bill_id": bill_id,
                    "bill_no": bill_no,
                    "fiscal_year": fiscal_year,
                    "payment_mode": payment_mode,
                    "total": bill_data.get("Total", 0),
                    "rooms": room_nos,
                },
                endpoint="/bill-by-id",
            )
        except Exception as e :
            current_app.logger.warning(f"Activity log failed for reservationID={reservationID}")
            current_app.logger.warning(f"{e}")
        # -------- COMMIT (only after the journal is confirmed) --------
        mydb.commit()
        committed = True

        return jsonify({
            "message": "Bill + details created successfully",
            "bill_id": bill_id,
            "BillNo": bill_no,
            "total_details": len(bill_details),
            "total_split_payments": len(split_payments) if payment_mode == "Split" else 0,
            "total_forex_receipts": len(forex_rows),
            "total_settlements": len(settlement_payments),
            "journal_posted": True,
        }), 201

    except mysql_errors.IntegrityError as e:
        if mydb and not committed:
            _safe_rollback(mydb)
        if e.errno == 1062 and "uniq_billno_fy" in str(e):
            return {
                "error": "This bill number was already used by another bill. Fetch a new bill number and retry.",
                "code": "BILL_NO_TAKEN",
            }, 409
        current_app.logger.exception("Integrity error in /bill-by-id")
        return {"error": str(e)}, 500

    except Exception as e:
        if mydb and not committed:
            _safe_rollback(mydb)
        current_app.logger.exception("Unhandled error in /bill-by-id")
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass

from datetime import datetime, time as dtime

# Adjust if tblorderhistory.Date isn't stored as YYYY-MM-DD.
# (%% is required because the driver does % substitution when params are passed.)
OUTLET_DATE_SQL = "STR_TO_DATE(o.Date, '%Y-%m-%d')"
OUTLET_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y")
TIME_FORMATS = ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M")


def _parse_time(value):
    """'11:34 AM' / '11:34:00' -> datetime.time, or None if unparseable."""
    if not value:
        return None
    value = str(value).strip().upper()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def _parse_date(value):
    """date object or string -> date, or None."""
    if value is None:
        return None
    if hasattr(value, "year"):  # already a date/datetime
        return value.date() if isinstance(value, datetime) else value
    value = str(value).strip()
    for fmt in OUTLET_DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _sort_datetime(date_value, time_value):
    d = _parse_date(date_value)
    if d is None:
        return datetime.min
    return datetime.combine(d, _parse_time(time_value) or dtime(0, 0))


def _date_conditions(column, specific_date, start_date, end_date):
    if specific_date:
        return [f"{column} = %s"], [specific_date]
    conds, params = [], []
    if start_date:
        conds.append(f"{column} >= %s")
        params.append(start_date)
    if end_date:
        conds.append(f"{column} <= %s")
        params.append(end_date)
    return conds, params


def _in(n):
    return ",".join(["%s"] * n)

import re
from decimal import Decimal
def valid_date(datestring):
    try:
        regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
        match = re.match(regex, datestring)
        if match:
            return True
    except ValueError:
        return False
    return False


# @app_file412.route("/bills", methods=["GET"])
# @cross_origin()
# def get_all_bills():
#     # -------- TOKEN --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     # -------- PARAMS --------
#     hotel_name = request.args.get("outlet")  # hotel_company_property.name
#     start_date = request.args.get("start_date")
#     end_date = request.args.get("end_date")
#     specific_date = request.args.get("date")
#     sort_order = request.args.get("order", "desc").lower()

#     if not hotel_name:
#         return {"error": "outlet (hotel name) is required."}, 400
#     for d in (start_date, end_date, specific_date):
#         if d and not valid_date(d):
#             return {"error": "Invalid date supplied."}, 400
#     from datetime import date

#     if not (specific_date or start_date or end_date):
#         specific_date = date.today().strftime("%Y-%m-%d")

#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # -------- RESOLVE HOTEL + ITS OUTLETS --------
#         cursor.execute(
#             "SELECT id FROM hotel_company_property WHERE name = %s LIMIT 1",
#             (hotel_name,),
#         )
#         prop = cursor.fetchone()
#         if not prop:
#             return {"error": "Hotel not found."}, 404

#         cursor.execute(
#             "SELECT DISTINCT Outlet FROM outetNames WHERE company_property_id = %s",
#             (prop["id"],),
#         )
#         outlet_names = [r["Outlet"] for r in cursor.fetchall() if r["Outlet"]]

#         # =====================================================
#         # HOTEL BILLS
#         # =====================================================
#         conds, params = _date_conditions("b.Date", specific_date, start_date, end_date)
#         where = " AND ".join(["r.outlet = %s"] + conds)

#         cursor.execute(
#             f"""
#             SELECT b.*, r.outlet, r.Reservation_Date, r.Current_Status
#             FROM hotel_tblhotelbills b
#             JOIN hotel_tblreservation r ON b.reservationID = r.id
#             WHERE {where}
#             """,
#             tuple([hotel_name] + params),
#         )
#         hotel_bills = cursor.fetchall()

#         if hotel_bills:
#             reservation_ids = [b["reservationID"] for b in hotel_bills]
#             bill_ids = [b["id"] for b in hotel_bills]

#             cursor.execute(
#                 f"""
#                 SELECT rd.Reservation_ID, r.id as room_id, r.room_no, r.room_type, r.outlet, rd.is_current,
#                        tr.rate as room_rate, tr.currency as room_currency,
#                        mp.mp as meal_plan, mp.rate as meal_rate, mp.currency as meal_currency
#                 FROM hotel_tblreservation_details rd
#                 JOIN hotel_tblrooms r ON rd.room_id = r.id
#                 LEFT JOIN hotel_tblrates tr ON tr.room_name = r.room_no AND tr.room_type = r.room_type
#                 LEFT JOIN hotel_tblmeal_price mp ON tr.meal_price_id = mp.id
#                 WHERE rd.Reservation_ID IN ({_in(len(reservation_ids))})
#                 """,
#                 tuple(reservation_ids),
#             )
#             rooms_map = {}
#             for row in cursor.fetchall():
#                 rooms_map.setdefault(row["Reservation_ID"], []).append(row)

#             cursor.execute(
#                 f"""
#                 SELECT * FROM hotel_tblbilldetails
#                 WHERE bill_id IN ({_in(len(bill_ids))})
#                 ORDER BY Date ASC
#                 """,
#                 tuple(bill_ids),
#             )
#             details_map = {}
#             for row in cursor.fetchall():
#                 details_map.setdefault(row["bill_id"], []).append(row)

#             cursor.execute(
#                 f"SELECT * FROM hotel_tblbillpayments WHERE bill_id IN ({_in(len(bill_ids))})",
#                 tuple(bill_ids),
#             )
#             payments_map = {}
#             for row in cursor.fetchall():
#                 payments_map.setdefault(row["bill_id"], []).append(row)

#             for b in hotel_bills:
#                 b["bill_type"] = "hotel"
#                 b["rooms"] = rooms_map.get(b["reservationID"], [])
#                 b["bill_details"] = details_map.get(b["id"], [])
#                 b["split_payments"] = payments_map.get(b["id"], [])
#                 b["_sort_dt"] = _sort_datetime(b.get("Date"), b.get("time"))

#         # =====================================================
#         # OUTLET (RESTAURANT) BILLS
#         # =====================================================
#         outlet_bills = []
#         if outlet_names:
#             conds, params = _date_conditions(
#                 OUTLET_DATE_SQL, specific_date, start_date, end_date
#             )
#             where = " AND ".join([f"o.Outlet_Name IN ({_in(len(outlet_names))})"] + conds)

#             cursor.execute(
#                 f"SELECT o.* FROM tblorderhistory o WHERE {where}",
#                 tuple(outlet_names + params),
#             )
#             outlet_bills = cursor.fetchall()

#         if outlet_bills:
#             order_ids = [o["idtblorderHistory"] for o in outlet_bills]

#             cursor.execute(
#                 f"""
#                 SELECT * FROM tblorder_detailshistory
#                 WHERE order_ID IN ({_in(len(order_ids))})
#                 """,
#                 tuple(order_ids),
#             )
#             items_map = {}
#             for row in cursor.fetchall():
#                 items_map.setdefault(row["order_ID"], []).append(row)

#             cursor.execute(
#                 f"""
#                 SELECT * FROM payment_history
#                 WHERE orderHistoryid IN ({_in(len(order_ids))})
#                 """,
#                 tuple(order_ids),
#             )
#             opay_map = {}
#             for row in cursor.fetchall():
#                 opay_map.setdefault(row["orderHistoryid"], []).append(row)

#             for o in outlet_bills:
#                 oid = o["idtblorderHistory"]
#                 o["bill_type"] = "outlet"
#                 o["items"] = items_map.get(oid, [])
#                 o["split_payments"] = opay_map.get(oid, [])
#                 o["_sort_dt"] = _sort_datetime(o.get("Date"), o.get("billPrintTime"))

#         # =====================================================
#         # MERGE + SORT
#         # =====================================================
#         all_bills = hotel_bills + outlet_bills
#         if not all_bills:
#             return {"message": "No bills found"}, 200

#         all_bills.sort(key=lambda x: x["_sort_dt"], reverse=(sort_order != "asc"))
#         for bill in all_bills:
#             dt = bill.pop("_sort_dt")
#             bill["bill_datetime"] = None if dt == datetime.min else dt.isoformat()

#         return jsonify({
#             "hotel": hotel_name,
#             "total_bills": len(all_bills),
#             "hotel_bill_count": len(hotel_bills),
#             "outlet_bill_count": len(outlet_bills),
#             "bills": all_bills,
#             "filters": {
#                 "start_date": start_date,
#                 "end_date": end_date,
#                 "specific_date": specific_date,
#             },
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()


@app_file412.route("/bills", methods=["GET"])
@cross_origin()
def get_all_bills():
    # -------- TOKEN --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- PARAMS --------
    hotel_name = request.args.get("outlet")  # hotel_company_property.name
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    specific_date = request.args.get("date")
    sort_order = request.args.get("order", "desc").lower()

    if not hotel_name:
        return {"error": "outlet (hotel name) is required."}, 400
    for d in (start_date, end_date, specific_date):
        if d and not valid_date(d):
            return {"error": "Invalid date supplied."}, 400
    from datetime import date

    if not (specific_date or start_date or end_date):
        specific_date = date.today().strftime("%Y-%m-%d")

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True)

        # -------- RESOLVE HOTEL + ITS OUTLETS --------
        cursor.execute(
            "SELECT id FROM hotel_company_property WHERE name = %s LIMIT 1",
            (hotel_name,),
        )
        prop = cursor.fetchone()
        if not prop:
            return {"error": "Hotel not found."}, 404

        cursor.execute(
            "SELECT DISTINCT Outlet FROM outetNames WHERE company_property_id = %s",
            (prop["id"],),
        )
        outlet_names = [r["Outlet"] for r in cursor.fetchall() if r["Outlet"]]

        # =====================================================
        # HOTEL BILLS
        # =====================================================
        conds, params = _date_conditions("b.Date", specific_date, start_date, end_date)
        where = " AND ".join(["r.outlet = %s"] + conds)

        # cursor.execute(
        #     f"""
        #     SELECT b.*, r.outlet, r.Reservation_Date, r.Current_Status
        #     FROM hotel_tblhotelbills b
        #     JOIN hotel_tblreservation r ON b.reservationID = r.id
        #     WHERE {where}
        #     """,
        #     tuple([hotel_name] + params),
        # )
        # hotel_bills = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT b.*, r.outlet, r.Reservation_Date, r.Current_Status, r.Advance_Payment_Local AS reservation_advance_local
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE {where}
            """,
            tuple([hotel_name] + params),
        )
        hotel_bills = cursor.fetchall()

        if hotel_bills:
            reservation_ids = [b["reservationID"] for b in hotel_bills]
            bill_ids = [b["id"] for b in hotel_bills]

            cursor.execute(
                f"""
                SELECT rd.Reservation_ID, r.id as room_id, r.room_no, r.room_type, r.outlet, rd.is_current,
                       tr.rate as room_rate, tr.currency as room_currency,
                       mp.mp as meal_plan, mp.rate as meal_rate, mp.currency as meal_currency
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblrooms r ON rd.room_id = r.id
                LEFT JOIN hotel_tblrates tr ON tr.room_name = r.room_no AND tr.room_type = r.room_type
                LEFT JOIN hotel_tblmeal_price mp ON tr.meal_price_id = mp.id
                WHERE rd.Reservation_ID IN ({_in(len(reservation_ids))})
                """,
                tuple(reservation_ids),
            )
            rooms_map = {}
            for row in cursor.fetchall():
                rooms_map.setdefault(row["Reservation_ID"], []).append(row)

            cursor.execute(
                f"""
                SELECT * FROM hotel_tblbilldetails
                WHERE bill_id IN ({_in(len(bill_ids))})
                ORDER BY Date ASC
                """,
                tuple(bill_ids),
            )
            details_map = {}
            for row in cursor.fetchall():
                details_map.setdefault(row["bill_id"], []).append(row)

            cursor.execute(
                f"SELECT * FROM hotel_tblbillpayments WHERE bill_id IN ({_in(len(bill_ids))})",
                tuple(bill_ids),
            )
            payments_map = {}
            for row in cursor.fetchall():
                payments_map.setdefault(row["bill_id"], []).append(row)

            for b in hotel_bills:
                b["bill_type"] = "hotel"
                b["rooms"] = rooms_map.get(b["reservationID"], [])
                b["bill_details"] = details_map.get(b["id"], [])
                b["split_payments"] = payments_map.get(b["id"], [])
                b["_sort_dt"] = _sort_datetime(b.get("Date"), b.get("time"))
                adv = b.pop("reservation_advance_local", None)
                b["AdvancePaid"] = float(adv) if adv is not None else 0
        # =====================================================
        # OUTLET (RESTAURANT) BILLS
        # =====================================================
        outlet_bills = []
        if outlet_names:
            conds, params = _date_conditions(
                OUTLET_DATE_SQL, specific_date, start_date, end_date
            )
            where = " AND ".join([f"o.Outlet_Name IN ({_in(len(outlet_names))})"] + conds)

            cursor.execute(
                f"SELECT o.* FROM tblorderhistory o WHERE {where}",
                tuple(outlet_names + params),
            )
            outlet_bills = cursor.fetchall()

        if outlet_bills:
            order_ids = [o["idtblorderHistory"] for o in outlet_bills]

            cursor.execute(
                f"""
                SELECT * FROM tblorder_detailshistory
                WHERE order_ID IN ({_in(len(order_ids))})
                """,
                tuple(order_ids),
            )
            items_map = {}
            for row in cursor.fetchall():
                items_map.setdefault(row["order_ID"], []).append(row)

            cursor.execute(
                f"""
                SELECT * FROM payment_history
                WHERE orderHistoryid IN ({_in(len(order_ids))})
                """,
                tuple(order_ids),
            )
            opay_map = {}
            for row in cursor.fetchall():
                opay_map.setdefault(row["orderHistoryid"], []).append(row)

            for o in outlet_bills:
                oid = o["idtblorderHistory"]
                o["bill_type"] = "outlet"
                o["items"] = items_map.get(oid, [])
                o["split_payments"] = opay_map.get(oid, [])
                o["_sort_dt"] = _sort_datetime(o.get("Date"), o.get("billPrintTime"))

        # =====================================================
        # GENERAL BILLS (laundry, spa, minibar, transport)
        # =====================================================
        conds, params = _date_conditions(
            "DATE(g.created_at)", specific_date, start_date, end_date
        )
        where = " AND ".join(["g.outlet = %s"] + conds)

        cursor.execute(
            f"SELECT g.* FROM hotel_generalbills g WHERE {where}",
            tuple([hotel_name] + params),
        )
        general_bills = cursor.fetchall()

        if general_bills:
            general_ids = [g["id"] for g in general_bills]

            cursor.execute(
                f"""
                SELECT * FROM hotel_generalbill_items
                WHERE bill_id IN ({_in(len(general_ids))})
                """,
                tuple(general_ids),
            )
            gitems_map = {}
            for row in cursor.fetchall():
                gitems_map.setdefault(row["bill_id"], []).append(row)

            for g in general_bills:
                g["general_bill_type"] = g["bill_type"]  # LA / SPA / MB / TR
                g["bill_type"] = "general"
                g["items"] = gitems_map.get(g["id"], [])
                g["_sort_dt"] = g["created_at"] or datetime.min

        # =====================================================
        # MERGE + SORT
        # =====================================================
        all_bills = hotel_bills + outlet_bills + general_bills
        if not all_bills:
            return {"message": "No bills found"}, 200

        all_bills.sort(key=lambda x: x["_sort_dt"], reverse=(sort_order != "asc"))
        for bill in all_bills:
            dt = bill.pop("_sort_dt")
            bill["bill_datetime"] = None if dt == datetime.min else dt.isoformat()

        return jsonify({
            "hotel": hotel_name,
            "total_bills": len(all_bills),
            "hotel_bill_count": len(hotel_bills),
            "outlet_bill_count": len(outlet_bills),
            "general_bill_count": len(general_bills),
            "bills": all_bills,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "specific_date": specific_date,
            },
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()

    

@app_file412.route("/bills/<int:reservation_id>", methods=["GET"])
@cross_origin()
def get_reservation_bills(reservation_id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

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

        # -------- FETCH BILLS --------
        bills_query = """
            SELECT *
            FROM hotel_tblhotelbills
            WHERE reservationID = %s
        """
        cursor.execute(bills_query, (reservation_id,))
        bills = cursor.fetchall()

        if not bills:
            return {"error": "No bills found for this reservation"}, 404

        # -------- FETCH ROOMS FOR RESERVATION --------
        rooms_query = """
            SELECT r.id as room_id, r.room_no, r.room_type, r.outlet, rd.is_current,
                   tr.rate as room_rate, tr.currency as room_currency,
                   mp.mp as meal_plan, mp.rate as meal_rate, mp.currency as meal_currency
            FROM hotel_tblreservation_details rd
            JOIN hotel_tblrooms r ON rd.room_id = r.id
            LEFT JOIN hotel_tblrates tr ON tr.room_name = r.room_no AND tr.room_type = r.room_type
            LEFT JOIN hotel_tblmeal_price mp ON tr.meal_price_id = mp.id
            WHERE rd.Reservation_ID = %s
        """
        cursor.execute(rooms_query, (reservation_id,))
        rooms = cursor.fetchall()

        mydb.close()

        return jsonify({
            "reservation_id": reservation_id,
            "bills": bills,
            "rooms": rooms
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

# # from 
# @app_file412.route("/void-bill", methods=["POST"])
# @cross_origin()
# def void_bill():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

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

#         # -------- INPUT --------
#         data = request.get_json()
#         bill_id = data.get("bill_id")

#         print(data)

#         if not bill_id:
#             return {"error": "bill_id is required"}, 400

#         # -------- CHECK IF BILL EXISTS --------
#         cursor.execute(
#             "SELECT id, status, BillNo, fiscalYear, Date FROM hotel_tblhotelbills WHERE id = %s",
#             (bill_id,)
#         )
#         bill = cursor.fetchone()

#         print("bill", bill)
#         void_data = {
#             "bill_no": bill["BillNo"],
#             "bill_date":  bill["Date"].strftime("%Y-%m-%d"),
#             "fiscal_year":  bill["fiscalYear"],
#             "reason":  data.get('reason')
#         }            
#         try:
#             void_hotelbill(void_data)
#         except Exception as e :
#              return {"error": "error in voiding bill in accounting"}, 400           

#         if not bill:
#             return {"error": "Bill not found"}, 404

#         # -------- OPTIONAL: CHECK IF ALREADY VOID --------
#         if bill["status"] == 0:
#             return {"message": "Bill already voided"}, 200

#         # -------- VOID BILL --------
#         cursor.execute(
#             "UPDATE hotel_tblhotelbills SET status = 0 WHERE id = %s",
#             (bill_id,)
#         )
#         mydb.commit()

#         mydb.close()

#         return {
#             "message": "Bill voided successfully",
#             "bill_id": bill_id
#         }, 200

#     except Exception as e:
#         return {"error": str(e)}, 500


from root.flask_routes.hotel.journal_utils.utils import void_hotelbill, JournalOutcomeUnknown


@app_file412.route("/void-bill", methods=["POST"])
@cross_origin()
def void_bill():
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
        bill_id = data.get("bill_id")
        if not bill_id:
            return {"error": "bill_id is required"}, 400
        reason = (data.get("reason") or "").strip() or "Voided Bill"

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        # -------- CHECK BILL --------
        cursor.execute(
            "SELECT id, status, BillNo, fiscalYear, Date FROM hotel_tblhotelbills WHERE id = %s",
            (bill_id,)
        )
        bill = cursor.fetchone()

        if not bill:
            return {"error": "Bill not found"}, 404

        if bill["status"] == 0:
            return {"message": "Bill already voided"}, 200

        bill_date = bill["Date"]
        if not bill_date:
            return {"error": "Bill has no date, cannot void"}, 400
        bill_date = bill_date.strftime("%Y-%m-%d") if hasattr(bill_date, "strftime") else str(bill_date)[:10]

        # -------- VOID IN ACCOUNTING (also posts the IRD credit note) --------
        try:
            void_hotelbill({
                "bill_no": bill["BillNo"],
                "bill_date": bill_date,
                "fiscal_year": bill["fiscalYear"],
                "reason": reason,
            })
        except JournalOutcomeUnknown as e:
            return {"error": f"Accounting did not confirm the void: {e}. Retrying is safe."}, 502
        except Exception as e:
            return {"error": f"Accounting could not void the bill: {e}"}, 400

        # -------- VOID BILL --------
        try:
            cursor.execute(
                "UPDATE hotel_tblhotelbills SET status = 0 WHERE id = %s",
                (bill_id,)
            )
            mydb.commit()
        except Exception as e:
            mydb.rollback()
            return {
                "error": f"Voided in accounting but could not update the bill status: {e}. "
                         f"Retry the void to finish."
            }, 500

        return {
            "message": "Bill voided successfully",
            "bill_id": bill_id
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass

import requests
from root.flask_routes.hotel.journal_utils.utils import get_next_hotel_bill_no   # adjust to your utils module path


@app_file412.route("/hotel-bill-no", methods=["GET"])
@cross_origin()
def reserve_hotel_bill_no():
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

    property_id = request.args.get("property_id", type=int)
    if not property_id:
        return {"error": "property_id is required."}, 400

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

        info = get_next_hotel_bill_info(cursor, property_id)
        mydb.commit()

        return jsonify({
            "BillNo": info["bill_no"],
            "fiscalYear": info["fiscal_year"],
        }), 201

    except ValueError as e:
        # property not found / fiscal year not configured
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()