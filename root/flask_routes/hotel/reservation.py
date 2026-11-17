from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
load_dotenv()

app_file402 = Blueprint('app_file402', __name__)
from root.auth.check import token_auth

from datetime import datetime
from decimal import Decimal, InvalidOperation
from root.flask_routes.hotel.hotel_utils.utils import log_hotel_activity, get_employee_name   

# # accepted statuses, matched case-insensitively; "hold" is treated as "On Hold"
# STATUS_MAP = {
#     "reserved": "Reserved",
#     "registered": "Registered",
#     "checked out": "Checked Out",
#     "cancelled": "Cancelled",
#     "on hold": "On Hold",
#     "hold": "On Hold",
# }

# accepted statuses, matched case-insensitively; "wait list" is treated as "Wait Listed"
STATUS_MAP = {
    "reserved": "Reserved",
    "registered": "Registered",
    "checked out": "Checked Out",
    "cancelled": "Cancelled",
    "wait listed": "Wait Listed",
    "wait list": "Wait Listed",
    "waitlisted": "Wait Listed",
    "waitlist": "Wait Listed",
}


# @app_file402.route("/create-reservation", methods=["POST"])
# @cross_origin()
# def create_reservation():
#     # -------- TOKEN FROM HEADER --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]  # Remove "Bearer"
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     # -------- PAYLOAD VALIDATION --------
#     json_data = request.get_json() or {}

#     reservation_data = json_data.get("tblReservation") or {}
#     guest_reservation_data = json_data.get("tblGuestReservation") or {}
#     fit_rate_data = json_data.get("tblFITRate") or []

#     if not reservation_data:
#         return {"error": "Missing 'tblReservation' data"}, 400
#     if not guest_reservation_data:
#         return {"error": "Missing 'tblGuestReservation' data"}, 400
#     if not fit_rate_data:
#         return {"error": "Missing 'tblFITRate' data"}, 400

#     guest_id = reservation_data.get("Guest_ID")
#     company_id = reservation_data.get("company_id")
#     if not guest_id and not company_id:
#         return {"error": "Either Guest_ID or company_id is required"}, 400

#     # ---- Current_Status: from frontend, default 'Reserved' ----
#     raw_status = (reservation_data.get("Current_Status") or "").strip()
#     if raw_status:
#         status = STATUS_MAP.get(raw_status.lower())
#         if not status:
#             return {
#                 "error": f"Invalid Current_Status '{raw_status}'. "
#                          f"Allowed: {', '.join(sorted(set(STATUS_MAP.values())))}."
#             }, 400
#     else:
#         status = "Reserved"
#     reservation_data["Current_Status"] = status

#     # ---- Advance payment: amount + currency ----
#     raw_advance = reservation_data.get("Advance_Payment")
#     if raw_advance in (None, ""):
#         advance_amount = None
#     else:
#         try:
#             advance_amount = Decimal(str(raw_advance))
#         except InvalidOperation:
#             return {"error": "Advance_Payment must be a number."}, 400
#         if advance_amount < 0:
#             return {"error": "Advance_Payment cannot be negative."}, 400


#     advance_currency = (reservation_data.get("Advance_Payment_Currency") or "").strip().upper() or None
#     if advance_amount and not advance_currency:
#         advance_currency = "NPR"   # default when an amount is sent without a currency
#     if not advance_amount:
#         advance_currency = None    # no advance -> no currency

#     reservation_data["Advance_Payment"] = advance_amount
#     reservation_data["Advance_Payment_Currency"] = advance_currency

#     # ---- Advance payment in local currency (NPR), sent by the frontend ----
#     raw_local = reservation_data.get("Advance_Payment_Local")
#     if raw_local in (None, ""):
#         advance_local = None
#     else:
#         try:
#             advance_local = Decimal(str(raw_local))
#         except InvalidOperation:
#             return {"error": "Advance_Payment_Local must be a number."}, 400
#         if advance_local < 0:
#             return {"error": "Advance_Payment_Local cannot be negative."}, 400

#     if not advance_amount:
#         advance_local = None                      # no advance -> no local amount
#     elif advance_local is None:
#         return {"error": "Advance_Payment_Local is required when Advance_Payment is sent."}, 400

#     reservation_data["Advance_Payment_Local"] = advance_local

#     # -------- DB --------
#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         if company_id:
#             cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
#             if not cursor.fetchone():
#                 return {"error": "Invalid company_id"}, 400

#         if guest_id:
#             cursor.execute("SELECT id FROM customers WHERE id = %s", (guest_id,))
#             if not cursor.fetchone():
#                 return {"error": "Invalid guest_id"}, 400

#         # -----------------------
#         # 1) Insert reservation
#         # -----------------------
#         now_datetime = datetime.now()
#         now_date = now_datetime.date()

#         reservation_fields = (
#             "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
#             "Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local",
#             "Guest_ID", "company_id",
#             "Reservation_Date", "Market_Seg", "business_Src",
#             "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id"
#         )

#         def _value(field):
#             value = reservation_data.get(field)
#             if field == "Reservation_Date":
#                 return value or now_date
#             if field == "Check_In":
#                 return value or now_datetime
#             return value

#         reservation_values = tuple(_value(f) for f in reservation_fields)

#         placeholders = ", ".join(["%s"] * len(reservation_fields))
#         cursor.execute(f"""
#             INSERT INTO hotel_tblreservation ({', '.join(reservation_fields)})
#             VALUES ({placeholders})
#         """, reservation_values)
#         reservation_id = cursor.lastrowid

#         # -----------------------
#         # 2) Insert guest reservation
#         # -----------------------
#         guest_fields = (
#             "Reservation_ID", "No_of_children", "No_of_adults", "Likes", "Dislikes",
#             "Guest_Notes", "start_date", "end_date"
#         )
#         guest_values = (
#             reservation_id,
#             guest_reservation_data.get("No_of_children"),
#             guest_reservation_data.get("No_of_adults"),
#             guest_reservation_data.get("Likes"),
#             guest_reservation_data.get("Dislikes"),
#             guest_reservation_data.get("Guest_Notes"),
#             guest_reservation_data.get("start_date"),
#             guest_reservation_data.get("end_date")
#         )
#         placeholders = ", ".join(["%s"] * len(guest_fields))
#         cursor.execute(f"""
#             INSERT INTO hotel_tblguestreservation ({', '.join(guest_fields)})
#             VALUES ({placeholders})
#         """, guest_values)

#         # -----------------------
#         # 3) Insert FITRate data
#         # -----------------------
#         for fit_item in fit_rate_data:
#             rateID = fit_item.get("rateID")
#             mealID = fit_item.get("mealID")
#             quantity = fit_item.get("quantity", 0)

#             cursor.execute("""
#                 SELECT id, quantity FROM hotel_tblfitrate
#                 WHERE rateID=%s AND (mealID=%s OR (mealID IS NULL AND %s IS NULL)) AND reservationID=%s
#                 LIMIT 1
#             """, (rateID, mealID, mealID, reservation_id))
#             existing = cursor.fetchone()

#             if existing:
#                 new_quantity = (existing["quantity"] or 0) + quantity
#                 cursor.execute(
#                     "UPDATE hotel_tblfitrate SET quantity=%s WHERE id=%s",
#                     (new_quantity, existing["id"])
#                 )
#             else:
#                 cursor.execute("""
#                     INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
#                     VALUES (%s, %s, %s, %s, 1)
#                 """, (rateID, mealID, reservation_id, quantity))

#         mydb.commit()

#         return {
#             "message": f"Congrats, Your reservation ID is {reservation_id}",
#             "reservation_id": reservation_id,
#             "Current_Status": status,
#             "Advance_Payment": float(advance_amount) if advance_amount is not None else None,
#             "Advance_Payment_Currency": advance_currency,
#             "Advance_Payment_Currency": advance_currency,
#             "Advance_Payment_Local": float(advance_local) if advance_local is not None else None
#         }, 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400

#     finally:
#         if mydb:
#             mydb.close()

def _parse_bool_flag(value, default=False):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "y"):
            return True
        if v in ("0", "false", "no", "n"):
            return False
    raise ValueError("invalid boolean")

# @app_file402.route("/create-reservation", methods=["POST"])
# @cross_origin()
# def create_reservation():
#     # -------- TOKEN FROM HEADER --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]  # Remove "Bearer"
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     # -------- PAYLOAD VALIDATION --------
#     json_data = request.get_json() or {}

#     reservation_data = json_data.get("tblReservation") or {}
#     guest_reservation_data = json_data.get("tblGuestReservation") or {}
#     fit_rate_data = json_data.get("tblFITRate") or []

#     if not reservation_data:
#         return {"error": "Missing 'tblReservation' data"}, 400
#     if not guest_reservation_data:
#         return {"error": "Missing 'tblGuestReservation' data"}, 400
#     if not fit_rate_data:
#         return {"error": "Missing 'tblFITRate' data"}, 400

#     guest_id = reservation_data.get("Guest_ID")
#     company_id = reservation_data.get("company_id")
#     if not guest_id and not company_id:
#         return {"error": "Either Guest_ID or company_id is required"}, 400

#     # ---- Current_Status: from frontend, default 'Reserved' ----
#     raw_status = (reservation_data.get("Current_Status") or "").strip()
#     if raw_status:
#         status = STATUS_MAP.get(raw_status.lower())
#         if not status:
#             return {
#                 "error": f"Invalid Current_Status '{raw_status}'. "
#                          f"Allowed: {', '.join(sorted(set(STATUS_MAP.values())))}."
#             }, 400
#     else:
#         status = "Reserved"
#     reservation_data["Current_Status"] = status

#     # ---- is_complimentary: from frontend, default false ----
#     try:
#         is_complimentary = _parse_bool_flag(reservation_data.get("is_complimentary"))
#     except ValueError:
#         return {"error": "is_complimentary must be true or false."}, 400
#     reservation_data["is_complimentary"] = 1 if is_complimentary else 0

#     # ---- Advance payment: amount + currency ----
#     raw_advance = reservation_data.get("Advance_Payment")
#     if raw_advance in (None, ""):
#         advance_amount = None
#     else:
#         try:
#             advance_amount = Decimal(str(raw_advance))
#         except InvalidOperation:
#             return {"error": "Advance_Payment must be a number."}, 400
#         if advance_amount < 0:
#             return {"error": "Advance_Payment cannot be negative."}, 400


#     advance_currency = (reservation_data.get("Advance_Payment_Currency") or "").strip().upper() or None
#     if advance_amount and not advance_currency:
#         advance_currency = "NPR"   # default when an amount is sent without a currency
#     if not advance_amount:
#         advance_currency = None    # no advance -> no currency

#     reservation_data["Advance_Payment"] = advance_amount
#     reservation_data["Advance_Payment_Currency"] = advance_currency

#     # ---- Advance payment in local currency (NPR), sent by the frontend ----
#     raw_local = reservation_data.get("Advance_Payment_Local")
#     if raw_local in (None, ""):
#         advance_local = None
#     else:
#         try:
#             advance_local = Decimal(str(raw_local))
#         except InvalidOperation:
#             return {"error": "Advance_Payment_Local must be a number."}, 400
#         if advance_local < 0:
#             return {"error": "Advance_Payment_Local cannot be negative."}, 400

#     if not advance_amount:
#         advance_local = None                      # no advance -> no local amount
#     elif advance_local is None:
#         return {"error": "Advance_Payment_Local is required when Advance_Payment is sent."}, 400

#     reservation_data["Advance_Payment_Local"] = advance_local

#     # -------- DB --------
#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         if company_id:
#             cursor.execute("SELECT id FROM companies WHERE id = %s", (company_id,))
#             if not cursor.fetchone():
#                 return {"error": "Invalid company_id"}, 400

#         if guest_id:
#             cursor.execute("SELECT id FROM customers WHERE id = %s", (guest_id,))
#             if not cursor.fetchone():
#                 return {"error": "Invalid guest_id"}, 400

#         # -----------------------
#         # 1) Insert reservation
#         # -----------------------
#         now_datetime = datetime.now()
#         now_date = now_datetime.date()

#         reservation_fields = (
#             "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
#             "Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local",
#             "Guest_ID", "company_id",
#             "Reservation_Date", "Market_Seg", "business_Src",
#             "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id",
#             "is_complimentary"
#         )

#         def _value(field):
#             value = reservation_data.get(field)
#             if field == "Reservation_Date":
#                 return value or now_date
#             if field == "Check_In":
#                 return value or now_datetime
#             return value

#         reservation_values = tuple(_value(f) for f in reservation_fields)

#         placeholders = ", ".join(["%s"] * len(reservation_fields))
#         cursor.execute(f"""
#             INSERT INTO hotel_tblreservation ({', '.join(reservation_fields)})
#             VALUES ({placeholders})
#         """, reservation_values)
#         reservation_id = cursor.lastrowid

#         # -----------------------
#         # 2) Insert guest reservation
#         # -----------------------
#         guest_fields = (
#             "Reservation_ID", "No_of_children", "No_of_adults", "Likes", "Dislikes",
#             "Guest_Notes", "start_date", "end_date"
#         )
#         guest_values = (
#             reservation_id,
#             guest_reservation_data.get("No_of_children"),
#             guest_reservation_data.get("No_of_adults"),
#             guest_reservation_data.get("Likes"),
#             guest_reservation_data.get("Dislikes"),
#             guest_reservation_data.get("Guest_Notes"),
#             guest_reservation_data.get("start_date"),
#             guest_reservation_data.get("end_date")
#         )
#         placeholders = ", ".join(["%s"] * len(guest_fields))
#         cursor.execute(f"""
#             INSERT INTO hotel_tblguestreservation ({', '.join(guest_fields)})
#             VALUES ({placeholders})
#         """, guest_values)

#         # -----------------------
#         # 3) Insert FITRate data
#         # -----------------------
#         for fit_item in fit_rate_data:
#             rateID = fit_item.get("rateID")
#             mealID = fit_item.get("mealID")
#             quantity = fit_item.get("quantity", 0)

#             cursor.execute("""
#                 SELECT id, quantity FROM hotel_tblfitrate
#                 WHERE rateID=%s AND (mealID=%s OR (mealID IS NULL AND %s IS NULL)) AND reservationID=%s
#                 LIMIT 1
#             """, (rateID, mealID, mealID, reservation_id))
#             existing = cursor.fetchone()

#             if existing:
#                 new_quantity = (existing["quantity"] or 0) + quantity
#                 cursor.execute(
#                     "UPDATE hotel_tblfitrate SET quantity=%s WHERE id=%s",
#                     (new_quantity, existing["id"])
#                 )
#             else:
#                 cursor.execute("""
#                     INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
#                     VALUES (%s, %s, %s, %s, 1)
#                 """, (rateID, mealID, reservation_id, quantity))

#         mydb.commit()

#         return {
#             "message": f"Congrats, Your reservation ID is {reservation_id}",
#             "reservation_id": reservation_id,
#             "Current_Status": status,
#             "Advance_Payment": float(advance_amount) if advance_amount is not None else None,
#             "Advance_Payment_Currency": advance_currency,
#             "Advance_Payment_Currency": advance_currency,
#             "Advance_Payment_Local": float(advance_local) if advance_local is not None else None,
#             "is_complimentary": bool(is_complimentary)
#         }, 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400

#     finally:
#         if mydb:
#             mydb.close()


@app_file402.route("/create-reservation", methods=["POST"])
@cross_origin()
def create_reservation():
    # -------- TOKEN FROM HEADER --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]  # Remove "Bearer"
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- PAYLOAD VALIDATION --------
    json_data = request.get_json() or {}

    reservation_data = json_data.get("tblReservation") or {}
    guest_reservation_data = json_data.get("tblGuestReservation") or {}
    fit_rate_data = json_data.get("tblFITRate") or []

    if not reservation_data:
        return {"error": "Missing 'tblReservation' data"}, 400
    if not guest_reservation_data:
        return {"error": "Missing 'tblGuestReservation' data"}, 400
    if not fit_rate_data:
        return {"error": "Missing 'tblFITRate' data"}, 400

    guest_id = reservation_data.get("Guest_ID")
    company_id = reservation_data.get("company_id")
    if not guest_id and not company_id:
        return {"error": "Either Guest_ID or company_id is required"}, 400

    # ---- Current_Status: from frontend, default 'Reserved' ----
    raw_status = (reservation_data.get("Current_Status") or "").strip()
    if raw_status:
        status = STATUS_MAP.get(raw_status.lower())
        if not status:
            return {
                "error": f"Invalid Current_Status '{raw_status}'. "
                         f"Allowed: {', '.join(sorted(set(STATUS_MAP.values())))}."
            }, 400
    else:
        status = "Reserved"
    reservation_data["Current_Status"] = status

    # ---- is_complimentary: from frontend, default false ----
    try:
        is_complimentary = _parse_bool_flag(reservation_data.get("is_complimentary"))
    except ValueError:
        return {"error": "is_complimentary must be true or false."}, 400
    reservation_data["is_complimentary"] = 1 if is_complimentary else 0

    # ---- Advance payment: amount + currency ----
    raw_advance = reservation_data.get("Advance_Payment")
    if raw_advance in (None, ""):
        advance_amount = None
    else:
        try:
            advance_amount = Decimal(str(raw_advance))
        except InvalidOperation:
            return {"error": "Advance_Payment must be a number."}, 400
        if advance_amount < 0:
            return {"error": "Advance_Payment cannot be negative."}, 400

    advance_currency = (reservation_data.get("Advance_Payment_Currency") or "").strip().upper() or None
    if advance_amount and not advance_currency:
        advance_currency = "NPR"   # default when an amount is sent without a currency
    if not advance_amount:
        advance_currency = None    # no advance -> no currency

    reservation_data["Advance_Payment"] = advance_amount
    reservation_data["Advance_Payment_Currency"] = advance_currency

    # ---- Advance payment in local currency (NPR), sent by the frontend ----
    raw_local = reservation_data.get("Advance_Payment_Local")
    if raw_local in (None, ""):
        advance_local = None
    else:
        try:
            advance_local = Decimal(str(raw_local))
        except InvalidOperation:
            return {"error": "Advance_Payment_Local must be a number."}, 400
        if advance_local < 0:
            return {"error": "Advance_Payment_Local cannot be negative."}, 400

    if not advance_amount:
        advance_local = None                      # no advance -> no local amount
    elif advance_local is None:
        return {"error": "Advance_Payment_Local is required when Advance_Payment is sent."}, 400

    reservation_data["Advance_Payment_Local"] = advance_local

    # -------- DB --------
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        company_name = None   # <-- new
        guest_name = None     # <-- new

        if company_id:
            cursor.execute("SELECT id, company_name FROM companies WHERE id = %s", (company_id,))   # <-- new: also name
            company_row = cursor.fetchone()
            if not company_row:
                return {"error": "Invalid company_id"}, 400
            company_name = company_row["company_name"]   # <-- new

        if guest_id:
            cursor.execute("SELECT id, name FROM customers WHERE id = %s", (guest_id,))   # <-- new: also name
            guest_row = cursor.fetchone()
            if not guest_row:
                return {"error": "Invalid guest_id"}, 400
            guest_name = guest_row["name"]   # <-- new

        # -----------------------
        # 1) Insert reservation
        # -----------------------
        now_datetime = datetime.now()
        now_date = now_datetime.date()

        reservation_fields = (
            "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
            "Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local",
            "Guest_ID", "company_id",
            "Reservation_Date", "Market_Seg", "business_Src",
            "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id",
            "is_complimentary"
        )

        def _value(field):
            value = reservation_data.get(field)
            if field == "Reservation_Date":
                return value or now_date
            # if field == "Check_In":
            #     return value or now_datetime
            return value

        reservation_values = tuple(_value(f) for f in reservation_fields)

        placeholders = ", ".join(["%s"] * len(reservation_fields))
        cursor.execute(f"""
            INSERT INTO hotel_tblreservation ({', '.join(reservation_fields)})
            VALUES ({placeholders})
        """, reservation_values)
        reservation_id = cursor.lastrowid

        # -----------------------
        # 2) Insert guest reservation
        # -----------------------
        guest_fields = (
            "Reservation_ID", "No_of_children", "No_of_adults", "Likes", "Dislikes",
            "Guest_Notes", "start_date", "end_date"
        )
        guest_values = (
            reservation_id,
            guest_reservation_data.get("No_of_children"),
            guest_reservation_data.get("No_of_adults"),
            guest_reservation_data.get("Likes"),
            guest_reservation_data.get("Dislikes"),
            guest_reservation_data.get("Guest_Notes"),
            guest_reservation_data.get("start_date"),
            guest_reservation_data.get("end_date")
        )
        placeholders = ", ".join(["%s"] * len(guest_fields))
        cursor.execute(f"""
            INSERT INTO hotel_tblguestreservation ({', '.join(guest_fields)})
            VALUES ({placeholders})
        """, guest_values)

        # -----------------------
        # 3) Insert FITRate data
        # -----------------------
        for fit_item in fit_rate_data:
            rateID = fit_item.get("rateID")
            mealID = fit_item.get("mealID")
            quantity = fit_item.get("quantity", 0)

            cursor.execute("""
                SELECT id, quantity FROM hotel_tblfitrate
                WHERE rateID=%s AND (mealID=%s OR (mealID IS NULL AND %s IS NULL)) AND reservationID=%s
                LIMIT 1
            """, (rateID, mealID, mealID, reservation_id))
            existing = cursor.fetchone()

            if existing:
                new_quantity = (existing["quantity"] or 0) + quantity
                cursor.execute(
                    "UPDATE hotel_tblfitrate SET quantity=%s WHERE id=%s",
                    (new_quantity, existing["id"])
                )
            else:
                cursor.execute("""
                    INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                """, (rateID, mealID, reservation_id, quantity))

        # -----------------------
        # 4) Activity log (same transaction as the reservation)   # <-- new
        # -----------------------
        emp_id = reservation_data.get("Emp_ID")
        emp_name = get_employee_name(cursor, emp_id)
        total_rooms = sum(int(f.get("quantity") or 0) for f in fit_rate_data)
        party = guest_name or company_name or "unknown guest"

        description = (
            f"{emp_name or 'Employee'} created reservation #{reservation_id} "
            f"({status}) for {party}, "
            f"{guest_reservation_data.get('start_date')} to {guest_reservation_data.get('end_date')}, "
            f"{total_rooms} room(s)"
        )
        if is_complimentary:
            description += ", complimentary"
        if advance_amount:
            description += f", advance {advance_amount} {advance_currency}"

        log_hotel_activity(
            cursor,
            outlet=reservation_data.get("outlet"),
            action="CREATED",
            reservation_id=reservation_id,
            description=description,
            employee_id=emp_id,
            employee_name=emp_name,
            details={
                "guest_id": guest_id,
                "company_id": company_id,
                "status": status,
                "start_date": guest_reservation_data.get("start_date"),
                "end_date": guest_reservation_data.get("end_date"),
                "rooms": total_rooms,
                "is_complimentary": bool(is_complimentary),
                "advance_payment": advance_amount,
                "advance_currency": advance_currency,
            },
            endpoint="/create-reservation",
        )

        mydb.commit()

        return {
            "message": f"Congrats, Your reservation ID is {reservation_id}",
            "reservation_id": reservation_id,
            "Current_Status": status,
            "Advance_Payment": float(advance_amount) if advance_amount is not None else None,
            "Advance_Payment_Currency": advance_currency,
            "Advance_Payment_Local": float(advance_local) if advance_local is not None else None,
            "is_complimentary": bool(is_complimentary)
        }, 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if mydb:
            mydb.close()


def _find_by_outlet_rate_id(cursor, table, outlet_rate_id, outlet):
    """
    Find a row in `table` by outlet_rate_id, scoped to the outlet.
    Prefers an exact outlet match; falls back to a legacy row with outlet NULL
    and backfills its outlet.
    """
    cursor.execute(
        f"""
        SELECT id, outlet FROM {table}
        WHERE outlet_rate_id=%s AND (outlet=%s OR outlet IS NULL)
        ORDER BY (outlet IS NULL)
        LIMIT 1
        """,
        (outlet_rate_id, outlet),
    )
    row = cursor.fetchone()
    if not row:
        return None
    if row["outlet"] is None and outlet:
        cursor.execute(f"UPDATE {table} SET outlet=%s WHERE id=%s", (outlet, row["id"]))
    return row["id"]
    
from datetime import datetime

@app_file402.route("/create-reservation-v2", methods=["POST"])
@cross_origin()
def create_reservation_v2():
    # =====================================================
    # VALIDATION (no DB needed)
    # =====================================================
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    json_data = request.get_json() or {}

    reservation_data = json_data.get("tblReservation") or {}
    guest_reservation_data = json_data.get("tblGuestReservation") or {}
    fit_rate_data = json_data.get("tblFITRate") or []
    checkin_list = json_data.get("checkin_list") or []
    bill_data = json_data.get("HotelBills") or {}

    guest_info = reservation_data.pop("guest_info", None)
    company_info = reservation_data.pop("company_info", None)

    if not reservation_data:
        return {"error": "Missing 'tblReservation' data"}, 400
    if not guest_reservation_data:
        return {"error": "Missing 'tblGuestReservation' data"}, 400
    if not fit_rate_data:
        return {"error": "Missing 'tblFITRate' data"}, 400
    if not guest_info or not guest_info.get("outlet_guest_id"):
        return {"error": "guest_info with outlet_guest_id is required"}, 400

    # -------- CHECK-IN / CHECK-OUT FROM GUEST RESERVATION --------
    start_date_str = guest_reservation_data.get("start_date")
    end_date_str = guest_reservation_data.get("end_date")

    if not start_date_str or not end_date_str:
        return {"error": "start_date and end_date are required in tblGuestReservation"}, 400

    try:
        check_in_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "start_date and end_date must be in YYYY-MM-DD format"}, 400

    if check_out_date < check_in_date:
        return {"error": "end_date must be on or after start_date"}, 400

    reservation_data["Check_In"] = check_in_date
    reservation_data["Check_Out"] = check_out_date

    # accept both spellings for the reservation date
    if not reservation_data.get("Reservation_Date"):
        reservation_data["Reservation_Date"] = reservation_data.get("ReservationDate")

    # ---- Current_Status: from frontend, default 'Reserved' ----
    raw_status = (reservation_data.get("Current_Status") or "").strip()
    if raw_status:
        status = STATUS_MAP.get(raw_status.lower())
        if not status:
            return {
                "error": f"Invalid Current_Status '{raw_status}'. "
                         f"Allowed: {', '.join(sorted(set(STATUS_MAP.values())))}."
            }, 400
    else:
        status = "Reserved"
    reservation_data["Current_Status"] = status
    is_checked_out = status == "Checked Out"

    # # A held or cancelled booking must not occupy rooms
    # if status in ("On Hold", "Cancelled") and any(r.get("room_id") for r in checkin_list):
    #     return {"error": f"A reservation with status '{status}' cannot have rooms in checkin_list."}, 400

    # A wait-listed or cancelled booking must not occupy rooms
    if status in ("Wait Listed", "Cancelled") and any(r.get("room_id") for r in checkin_list):
        return {"error": f"A reservation with status '{status}' cannot have rooms in checkin_list."}, 400

    # ---- Advance payment: amount + currency ----
    raw_advance = reservation_data.get("Advance_Payment")
    if raw_advance in (None, ""):
        advance_amount = None
    else:
        try:
            advance_amount = Decimal(str(raw_advance))
        except InvalidOperation:
            return {"error": "Advance_Payment must be a number."}, 400
        if advance_amount < 0:
            return {"error": "Advance_Payment cannot be negative."}, 400

    advance_currency = (reservation_data.get("Advance_Payment_Currency") or "").strip().upper() or None
    if advance_amount and not advance_currency:
        advance_currency = "NPR"   # default when an amount is sent without a currency
    if not advance_amount:
        advance_currency = None    # no advance -> no currency

    reservation_data["Advance_Payment"] = advance_amount
    reservation_data["Advance_Payment_Currency"] = advance_currency

    # ---- Advance payment in local currency (NPR), sent by the frontend ----
    raw_local = reservation_data.get("Advance_Payment_Local")
    if raw_local in (None, ""):
        advance_local = None
    else:
        try:
            advance_local = Decimal(str(raw_local))
        except InvalidOperation:
            return {"error": "Advance_Payment_Local must be a number."}, 400
        if advance_local < 0:
            return {"error": "Advance_Payment_Local cannot be negative."}, 400

    if not advance_amount:
        advance_local = None                      # no advance -> no local amount
    elif advance_local is None:
        return {"error": "Advance_Payment_Local is required when Advance_Payment is sent."}, 400

    reservation_data["Advance_Payment_Local"] = advance_local

    outlet_guest_id = guest_info.get("outlet_guest_id")
    no_of_nights = (check_out_date - check_in_date).days

    now_datetime = datetime.now()
    now_date = now_datetime.date()

    # # -------- GUESTS PER CHECKED-IN ROOM --------
    # for room_assignment in checkin_list:
    #     room_ref = room_assignment.get("room_id")
    #     if not room_ref:
    #         continue

    #     room_guests = room_assignment.get("guests")

    #     if is_checked_out and not room_guests:
    #         continue  # history-only stay: guests are optional

    #     if not isinstance(room_guests, list) or not room_guests:
    #         return {"error": f"At least one guest is required for room {room_ref}."}, 400

    #     if sum(1 for g in room_guests if g.get("is_primary")) != 1:
    #         return {"error": f"Exactly one primary guest is required for room {room_ref}."}, 400

    #     for g in room_guests:
    #         if not (g.get("name") or "").strip():
    #             return {"error": f"Every guest needs a name (room {room_ref})."}, 400


    # -------- GUESTS PER CHECKED-IN ROOM --------
    # Each room needs at least one named guest; the reservation as a whole
    # needs exactly one primary guest across all its rooms.
    total_primaries = 0
    any_guests = False

    for room_assignment in checkin_list:
        room_ref = room_assignment.get("room_id")
        if not room_ref:
            continue

        room_guests = room_assignment.get("guests")

        if is_checked_out and not room_guests:
            continue  # history-only stay: guests are optional

        if not isinstance(room_guests, list) or not room_guests:
            return {"error": f"At least one guest is required for room {room_ref}."}, 400

        for g in room_guests:
            if not (g.get("name") or "").strip():
                return {"error": f"Every guest needs a name (room {room_ref})."}, 400

        any_guests = True
        total_primaries += sum(1 for g in room_guests if g.get("is_primary"))

    if any_guests and total_primaries != 1:
        return {
            "error": f"Exactly one primary guest is required across all rooms of the reservation "
                     f"(received {total_primaries})."
        }, 400

    # =====================================================
    # DATABASE WORK
    # =====================================================
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -----------------------
        # 1) Customer
        # -----------------------
        cursor.execute(
            "SELECT * FROM customers WHERE outlet_guest_id=%s LIMIT 1",
            (outlet_guest_id,),
        )
        customer = cursor.fetchone()

        if not customer:
            cursor.execute(
                """
                INSERT INTO customers (name, phone, email, address, outlet_guest_id, customer_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    guest_info.get("name"),
                    guest_info.get("contact_number"),
                    guest_info.get("email"),
                    guest_info.get("address"),
                    outlet_guest_id,
                    guest_info.get("type"),
                ),
            )
            customer_id = cursor.lastrowid
        else:
            customer_id = customer["id"]

        reservation_data["Guest_ID"] = customer_id

        # -----------------------
        # 1b) Company (optional)
        # -----------------------
        if company_info and company_info.get("outlet_company_id"):
            outlet_company_id = company_info.get("outlet_company_id")

            cursor.execute(
                "SELECT * FROM companies WHERE outlet_company_id=%s LIMIT 1",
                (outlet_company_id,),
            )
            company = cursor.fetchone()

            if not company:
                cursor.execute(
                    """
                    INSERT INTO companies
                        (company_name, phone, email, address, pan_number, outlet_company_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        company_info.get("company_name"),
                        company_info.get("phone"),
                        company_info.get("email"),
                        company_info.get("address"),
                        company_info.get("pan_number"),
                        outlet_company_id,
                    ),
                )
                company_id = cursor.lastrowid
            else:
                company_id = company["id"]

            reservation_data["company_id"] = company_id

        # -----------------------
        # 2) Reservation
        # -----------------------
        reservation_fields = (
            "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
            "Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local",
            "Guest_ID", "company_id",
            "Reservation_Date", "Market_Seg", "business_Src",
            "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id"
        )

        def _reservation_value(field):
            value = reservation_data.get(field)
            if field == "Emp_ID" and value == "":
                return None  # "" -> NULL
            if field == "Reservation_Date":
                return value or now_date
            return value

        reservation_values = tuple(_reservation_value(f) for f in reservation_fields)

        placeholders = ", ".join(["%s"] * len(reservation_fields))
        cursor.execute(
            f"""
            INSERT INTO hotel_tblreservation ({', '.join(reservation_fields)})
            VALUES ({placeholders})
            """,
            reservation_values,
        )
        reservation_id = cursor.lastrowid

        # -----------------------
        # 3) Guest reservation
        # -----------------------
        guest_fields = (
            "Reservation_ID", "No_of_children", "No_of_adults", "Likes", "Dislikes",
            "Guest_Notes", "start_date", "end_date",
        )
        guest_values = (
            reservation_id,
            guest_reservation_data.get("No_of_children"),
            guest_reservation_data.get("No_of_adults"),
            guest_reservation_data.get("Likes"),
            guest_reservation_data.get("Dislikes"),
            guest_reservation_data.get("Guest_Notes"),
            start_date_str,
            end_date_str,
        )
        placeholders = ", ".join(["%s"] * len(guest_fields))
        cursor.execute(
            f"""
            INSERT INTO hotel_tblguestreservation ({', '.join(guest_fields)})
            VALUES ({placeholders})
            """,
            guest_values,
        )

        # -----------------------
        # 4) Room assignments (hotel_tblreservation_details) + in-house guests
        # -----------------------
        # A checked-out stay keeps its room link for history, but the
        # assignment is not current and the room is not marked occupied.
        assignment_is_current = 0 if is_checked_out else 1
        guests_saved = 0

        for room_assignment in checkin_list:
            outlet_room_id = room_assignment.get("room_id")
            if not outlet_room_id:
                continue

            cursor.execute(
                """
                SELECT id, room_no, room_type
                FROM hotel_tblrooms
                WHERE outlet_room_id = %s AND is_active = 1
                LIMIT 1
                """,
                (outlet_room_id,),
            )
            room = cursor.fetchone()

            if not room:
                # fallback: match on local id
                cursor.execute(
                    """
                    SELECT id, room_no, room_type
                    FROM hotel_tblrooms
                    WHERE id = %s AND is_active = 1
                    LIMIT 1
                    """,
                    (outlet_room_id,),
                )
                room = cursor.fetchone()

            if not room:
                mydb.rollback()
                return {"error": f"Room with outlet_room_id or id '{outlet_room_id}' not found"}, 400

            room_id = room["id"]

            cursor.execute(
                """
                SELECT id FROM hotel_tblreservation_details
                WHERE Reservation_ID = %s AND room_id = %s AND is_current = %s
                """,
                (reservation_id, room_id, assignment_is_current),
            )
            existing_assignment = cursor.fetchone()

            if existing_assignment:
                cursor.execute(
                    """
                    UPDATE hotel_tblreservation_details
                    SET updated_at = %s, is_active = 1
                    WHERE id = %s
                    """,
                    (now_datetime, existing_assignment["id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO hotel_tblreservation_details
                        (Reservation_ID, room_id, is_current, created_at, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                    """,
                    (reservation_id, room_id, assignment_is_current, now_datetime),
                )

                if not is_checked_out:
                    cursor.execute(
                        "UPDATE hotel_tblrooms SET room_state='Check-In' WHERE id=%s",
                        (room_id,),
                    )

            # In-house guests for this room
            room_guests = room_assignment.get("guests") or []
            if room_guests:
                if is_checked_out:
                    # history only: not active, dated to the stay
                    guest_in = datetime.combine(check_in_date, datetime.min.time())
                    guest_out = datetime.combine(check_out_date, datetime.min.time())
                    guest_active = 0
                else:
                    guest_in = now_datetime
                    guest_out = None
                    guest_active = 1

                guest_rows = [
                    (
                        reservation_id,
                        room_id,
                        g["name"].strip(),
                        g.get("identity_type"),
                        g.get("identity_no"),
                        g.get("nationality"),
                        1 if g.get("is_primary") else 0,
                        guest_active,
                        guest_in,
                        guest_out,
                    )
                    for g in room_guests
                ]
                cursor.executemany(
                    """
                    INSERT INTO hotel_tblinhouse_guests
                        (reservation_id, room_id, name, identity_type, identity_no,
                         nationality, is_primary, is_active, checked_in_at, checked_out_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    guest_rows,
                )
                guests_saved += len(guest_rows)

        # -----------------------
        # 5) FIT rates (with automatic rate/meal creation)
        # -----------------------
        outlet = reservation_data.get("outlet")

        for item in fit_rate_data:
            outlet_rate_id = item.get("rateID")
            outlet_meal_id = item.get("mealID")
            quantity = item.get("quantity", 0)

            rate_details = item.get("rate_details") or {}
            meal_details = item.get("meal_details") or {}

            # ---------- Handle Meal (first, so the rate can link to it) ----------
            meal_id = None

            if outlet_meal_id:
                meal_id = _find_by_outlet_rate_id(cursor, "hotel_tblmeal_price", outlet_meal_id, outlet)

            if not meal_id and meal_details:
                meal_field_mapping = {
                    "mp": meal_details.get("mp"),
                    "outlet": outlet,
                    "rate": meal_details.get("rate"),
                    "currency": meal_details.get("currency"),
                    "outlet_rate_id": outlet_meal_id,
                }
                meal_fields = []
                meal_values = []
                for field, value in meal_field_mapping.items():
                    if value is not None:
                        meal_fields.append(field)
                        meal_values.append(value)

                meal_fields += ["created_at", "is_active"]
                meal_values += [now_datetime, True]

                placeholders = ", ".join(["%s"] * len(meal_fields))
                cursor.execute(
                    f"""
                    INSERT INTO hotel_tblmeal_price ({', '.join(meal_fields)})
                    VALUES ({placeholders})
                    """,
                    meal_values,
                )
                meal_id = cursor.lastrowid

            # ---------- Handle Rate ----------
            rate_id = None

            if outlet_rate_id:
                rate_id = _find_by_outlet_rate_id(cursor, "hotel_tblrates", outlet_rate_id, outlet)

            if not rate_id and rate_details:
                # rate_details["meal_price_id"] is the meal's outlet_rate_id, NOT the real id.
                # Resolve it to hotel_tblmeal_price.id before it goes into hotel_tblrates.
                rate_meal_outlet_id = rate_details.get("meal_price_id")
                rate_meal_price_id = None

                if rate_meal_outlet_id:
                    if meal_id and outlet_meal_id and str(rate_meal_outlet_id) == str(outlet_meal_id):
                        # same meal plan we just looked up / created above
                        rate_meal_price_id = meal_id
                    else:
                        rate_meal_price_id = _find_by_outlet_rate_id(
                            cursor, "hotel_tblmeal_price", rate_meal_outlet_id, outlet
                        )
                        if not rate_meal_price_id:
                            mydb.rollback()
                            return {
                                "error": f"Meal plan with outlet_rate_id {rate_meal_outlet_id} "
                                         f"not found for rate {outlet_rate_id}"
                            }, 400

                field_mapping = {
                    "room_name": rate_details.get("room_name"),
                    "room_type": rate_details.get("room_type"),
                    "outlet": outlet,
                    "rate": rate_details.get("rate"),
                    "currency": rate_details.get("currency"),
                    "outlet_rate_id": outlet_rate_id,
                    "meal_price_id": rate_meal_price_id,  # real id, or None (omitted below)
                }

                rate_fields = []
                rate_values = []
                for field, value in field_mapping.items():
                    if value is not None:
                        rate_fields.append(field)
                        rate_values.append(value)

                rate_fields += ["created_at", "is_active"]
                rate_values += [now_datetime, True]

                placeholders = ", ".join(["%s"] * len(rate_fields))
                cursor.execute(
                    f"""
                    INSERT INTO hotel_tblrates ({', '.join(rate_fields)})
                    VALUES ({placeholders})
                    """,
                    rate_values,
                )
                rate_id = cursor.lastrowid

            if not rate_id:
                mydb.rollback()
                return {"error": f"Rate not found and no rate details provided for outlet_rate_id {outlet_rate_id}"}, 400

            # ---------- Handle FIT Rate ----------
            cursor.execute(
                """
                SELECT id, quantity FROM hotel_tblfitrate
                WHERE rateID=%s AND (mealID=%s OR (mealID IS NULL AND %s IS NULL)) AND reservationID=%s
                LIMIT 1
                """,
                (rate_id, meal_id, meal_id, reservation_id),
            )
            existing = cursor.fetchone()

            if existing:
                new_quantity = (existing["quantity"] or 0) + quantity
                cursor.execute(
                    "UPDATE hotel_tblfitrate SET quantity=%s WHERE id=%s",
                    (new_quantity, existing["id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active, created_at)
                    VALUES (%s, %s, %s, %s, 1, %s)
                    """,
                    (rate_id, meal_id, reservation_id, quantity, now_datetime),
                )

        # -----------------------
        # 6) Bill
        # -----------------------
        bill_id = None

        if bill_data:
            bill_details_list = bill_data.get("bill_details") or []

            bill_fields = [
                "reservationID", "outlet_reservationID", "fiscalYear", "BillNo",
                "subTotal", "DiscountAmt", "VAT", "Total", "PaymentMode",
                "PartyName", "PartyPAN", "Date", "time", "NoOfNights",
                "MealplanRevenue", "RoomRevenue", "created_at",
            ]
            bill_values = [
                reservation_id,
                bill_data.get("outlet_reservationID"),
                bill_data.get("fiscalYear"),
                bill_data.get("BillNo"),
                bill_data.get("subTotal", 0),
                bill_data.get("DiscountAmt", 0),
                bill_data.get("VAT", 0),
                bill_data.get("Total", 0),
                bill_data.get("PaymentMode"),
                bill_data.get("PartyName"),
                bill_data.get("PartyPAN"),
                bill_data.get("Date") or now_date,
                bill_data.get("time") or now_datetime.strftime("%H:%M:%S"),
                no_of_nights,
                bill_data.get("MealplanRevenue", 0),
                bill_data.get("RoomRevenue", 0),
                now_datetime,
            ]

            placeholders = ", ".join(["%s"] * len(bill_fields))
            cursor.execute(
                f"""
                INSERT INTO hotel_tblhotelbills ({', '.join(bill_fields)})
                VALUES ({placeholders})
                """,
                bill_values,
            )
            bill_id = cursor.lastrowid

            # -----------------------
            # 7) Bill details (includes RoomRateName)
            # -----------------------
            detail_fields = [
                "bill_id", "Date", "RoomNumber", "RoomType", "RoomRateName",
                "RoomRate", "RateAmt", "MealPlan", "MealPlanAmt", "Amount",
                "Currency", "ExeRate", "AmountInclCurr", "created_at",
            ]
            detail_placeholders = ", ".join(["%s"] * len(detail_fields))
            detail_sql = f"""
                INSERT INTO hotel_tblbilldetails ({', '.join(detail_fields)})
                VALUES ({detail_placeholders})
            """

            for bill_detail in bill_details_list:
                detail_values = [
                    bill_id,
                    bill_detail.get("Date") or now_date,
                    bill_detail.get("RoomNumber"),
                    bill_detail.get("RoomType"),
                    bill_detail.get("RoomRateName"),
                    bill_detail.get("RoomRate", 0),
                    bill_detail.get("RateAmt", 0),
                    bill_detail.get("MealPlan"),
                    bill_detail.get("MealPlanAmt", 0),
                    bill_detail.get("Amount", 0),
                    bill_detail.get("Currency", bill_data.get("Currency", "NPR")),
                    bill_detail.get("ExeRate", 1.0),
                    bill_detail.get("AmountInclCurr", bill_detail.get("Amount", 0)),
                    now_datetime,
                ]
                cursor.execute(detail_sql, detail_values)

        mydb.commit()

        return {
            "message": f"Reservation created successfully. ID: {reservation_id}",
            "reservation_id": reservation_id,
            "bill_id": bill_id,
            "guests_saved": guests_saved,
            "Current_Status": status,
            "Advance_Payment": float(advance_amount) if advance_amount is not None else None,
            "Advance_Payment_Currency": advance_currency,
            "Advance_Payment_Local": float(advance_local) if advance_local is not None else None
        }, 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if mydb:
            mydb.close()

# @app_file402.route("/tblguestreservations", methods=["GET"])
# @cross_origin()
# def tbl_guest_reservation_list():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

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

#         # -------- OUTLET (required, from query param) --------
#         outlet = request.args.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required"}, 400

#         # -------- Fetch guest reservations --------
#         guest_res_query = """
#             SELECT g.*, r.Guest_ID, r.Reservation_type, r.Current_Status, r.Market_Seg, r.business_Src, r.Pay_Mode, r.Billing_Inst, r.designation, r.Check_In, r.Check_Out, r.Emp_ID, r.outlet, r.designation, r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local, r.reservation_outlet_id
#             FROM hotel_tblguestreservation g
#             JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
#             WHERE r.Current_Status IN ('Reserved', 'Registered', "Wait Listed")
#             AND r.outlet = %s
#             ORDER BY r.created_at DESC
#         """
#         cursor.execute(guest_res_query, (outlet,))
#         guest_reservations = cursor.fetchall()

#         if not guest_reservations:
#             mydb.close()
#             return {"message": "No guest reservations found"}, 200

#         # -------- Fetch guest IDs and reservation IDs --------
#         guest_ids = [res["Guest_ID"] for res in guest_reservations if res["Guest_ID"]]
#         reservation_ids = [res["Reservation_ID"] for res in guest_reservations]

#         # -------- Fetch guest details --------
#         guests_map = {}
#         if guest_ids:
#             format_strings = ','.join(['%s'] * len(guest_ids))
#             guest_query = f"""
#                 SELECT *
#                 FROM customers
#                 WHERE id IN ({format_strings})
#             """
#             cursor.execute(guest_query, tuple(guest_ids))
#             guests = cursor.fetchall()
#             for guest in guests:
#                 guests_map[guest["id"]] = {
#                     "name": guest.get("name"),
#                     "phone": guest.get("phone"),
#                     "email": guest.get("email"),
#                     "address": guest.get("address"),
#                     "customer_type": guest.get("customer_type"),
#                     "tax_number": guest.get("tax_number"),
#                     "country": guest.get("country"),
#                 }

#         # -------- Fetch room details (including room ID) for reservations --------
#         rooms_map = {}
#         if reservation_ids:
#             format_strings = ','.join(['%s'] * len(reservation_ids))
#             rooms_query = f"""
#                 SELECT 
#                     rd.Reservation_ID, 
#                     r.id as room_id,
#                     r.room_no,
#                     r.room_type,
#                     r.room_state,
#                     r.room_view,
#                     r.preference as room_preference
#                 FROM hotel_tblreservation_details rd
#                 JOIN hotel_tblrooms r ON rd.room_id = r.id
#                 WHERE rd.Reservation_ID IN ({format_strings})
#                 AND rd.is_current = 1
#                 AND rd.is_active = 1
#                 ORDER BY r.room_no
#             """
#             cursor.execute(rooms_query, tuple(reservation_ids))
#             rooms = cursor.fetchall()
#             for room in rooms:
#                 rid = room["Reservation_ID"]
#                 if rid not in rooms_map:
#                     rooms_map[rid] = []
                
#                 # Create room details object
#                 room_details = {
#                     "room_id": room["room_id"],
#                     "room_no": room["room_no"],
#                     "room_type": room.get("room_type"),
#                     "room_state": room.get("room_state"),
#                     "room_view": room.get("room_view"),
#                     "room_preference": room.get("room_preference")
#                 }
#                 rooms_map[rid].append(room_details)

#         # -------- Fetch fitrate data for all reservations --------
#         fitrates_map = {}
#         if reservation_ids:
#             format_strings = ','.join(['%s'] * len(reservation_ids))
#             fitrate_query = f"""
#                 SELECT 
#                     fr.*,
#                     rt.room_name,
#                     rt.room_type,
#                     rt.rate as room_rate,
#                     rt.currency as room_currency,
#                     mp.mp as meal_plan,
#                     mp.rate as meal_rate,
#                     mp.currency as meal_currency
#                 FROM hotel_tblfitrate fr
#                 LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
#                 LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#                 WHERE fr.reservationID IN ({format_strings})
#                 AND fr.is_active = 1
#                 ORDER BY fr.id DESC
#             """
#             cursor.execute(fitrate_query, tuple(reservation_ids))
#             fitrates = cursor.fetchall()
            
#             for fr in fitrates:
#                 rid = fr["reservationID"]
#                 if rid not in fitrates_map:
#                     fitrates_map[rid] = []
                
#                 # Format fitrate data
#                 formatted_fitrate = {
#                     "id": fr["id"],
#                     "quantity": fr["quantity"],
#                     "rate_details": {
#                         "id": fr["rateID"],
#                         "room_name": fr.get("room_name"),
#                         "room_type": fr.get("room_type"),
#                         "rate": float(fr["room_rate"]) if fr.get("room_rate") else 0,
#                         "currency": fr.get("room_currency")
#                     } if fr["rateID"] else None,
#                     "meal_details": {
#                         "id": fr["mealID"],
#                         "mp": fr.get("meal_plan"),
#                         "rate": float(fr["meal_rate"]) if fr.get("meal_rate") else 0,
#                         "currency": fr.get("meal_currency")
#                     } if fr["mealID"] else None,
#                     "created_at": fr["created_at"].strftime('%Y-%m-%d %H:%M:%S') if fr.get("created_at") else None
#                 }
#                 fitrates_map[rid].append(formatted_fitrate)

#         # -------- Build final formatted response --------
#         formatted_reservations = []
#         for res in guest_reservations:
#             # Calculate total amount from fitrates
#             fitrates_for_res = fitrates_map.get(res["Reservation_ID"], [])
#             total_amount = 0
#             for fr in fitrates_for_res:
#                 if fr["rate_details"]:
#                     total_amount += fr["quantity"] * fr["rate_details"]["rate"]
            
#             formatted_reservations.append({
#                 "id": res["id"],
#                 "Reservation_ID": {
#                     "id": res["Reservation_ID"],
#                     "Guest_ID": guests_map.get(res["Guest_ID"], {}),
#                     "Reservation_type": res.get("Reservation_type"),
#                     "Current_Status": res.get("Current_Status"),
#                     "Market_Seg": res.get("Market_Seg"),
#                     "business_Src": res.get("business_Src"),
#                     "Pay_Mode": res.get("Pay_Mode"),
#                     "Billing_Inst": res.get("Billing_Inst"),
#                     "designation": res.get("designation"),
#                     "Check_In": res.get("Check_In"),
#                     "Emp_ID": res.get("Emp_ID"),
#                     "outlet": res.get("outlet"),
#                 },
#                 "room_details": rooms_map.get(res["Reservation_ID"], []),  # Now returns list of room objects with IDs
#                 "start_date": res.get("start_date").strftime('%Y-%m-%d') if res.get("start_date") else None,
#                 "end_date": res.get("end_date").strftime('%Y-%m-%d') if res.get("end_date") else None,
#                 "No_of_adults": res.get("No_of_adults"),
#                 "No_of_children": res.get("No_of_children"),
#                 "Likes": res.get("Likes"),
#                 "Dislikes": res.get("Dislikes"),
#                 "Guest_Notes": res.get("Guest_Notes"),
#                 "designation": res.get("designation"),
#                 "Advance_Payment": res.get("Advance_Payment"),
#                 "Advance_Payment_Currency": res.get("Advance_Payment_Currency"),
#                 "Advance_Payment_Local": res.get("Advance_Payment_Local"),
#                 "reservation_outlet_id": res.get("reservation_outlet_id"),
#                 "Guest_Notes": res.get("Guest_Notes"),
#                 "fit_rates": fitrates_map.get(res["Reservation_ID"], []),
#                 "total_amount": total_amount,
#                 "fitrate_count": len(fitrates_map.get(res["Reservation_ID"], []))
#             })

#         mydb.close()

#         return jsonify({
#             "total_reservations": len(formatted_reservations),
#             "guest_reservations": formatted_reservations
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

@app_file402.route("/tblguestreservations", methods=["GET"])
@cross_origin()
def tbl_guest_reservation_list():
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

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

        # -------- OUTLET (required, from query param) --------
        outlet = request.args.get("outlet")
        if not outlet:
            return {"error": "outlet is required"}, 400

        # # -------- Fetch guest reservations --------
        # guest_res_query = """
        #     SELECT g.*, r.Guest_ID, r.Reservation_type, r.Current_Status, r.Market_Seg, r.business_Src, r.Pay_Mode, r.Billing_Inst, r.designation, r.Check_In, r.Check_Out, r.Emp_ID, r.outlet, r.designation, r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local, r.reservation_outlet_id
        #     FROM hotel_tblguestreservation g
        #     JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
        #     WHERE r.Current_Status IN ('Reserved', 'Registered', "Wait Listed")
        #     AND r.outlet = %s
        #     ORDER BY r.created_at DESC
        # """

        guest_res_query = """
            SELECT g.*, r.Guest_ID, r.company_id, r.Reservation_type, r.Current_Status, r.Market_Seg, r.business_Src, r.Pay_Mode, r.Billing_Inst, r.designation, r.Check_In, r.Check_Out, r.Emp_ID, r.outlet, r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local, r.reservation_outlet_id, r.is_complimentary
            FROM hotel_tblguestreservation g
            JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
            WHERE r.Current_Status IN ('Reserved', 'Registered', "Wait Listed")
            AND r.outlet = %s
            ORDER BY r.created_at DESC
        """

        cursor.execute(guest_res_query, (outlet,))
        guest_reservations = cursor.fetchall()

        if not guest_reservations:
            mydb.close()
            return {"message": "No guest reservations found"}, 200

        # -------- Fetch guest IDs and reservation IDs --------
        guest_ids = [res["Guest_ID"] for res in guest_reservations if res["Guest_ID"]]
        reservation_ids = [res["Reservation_ID"] for res in guest_reservations]

        # -------- Fetch guest details --------
        guests_map = {}
        if guest_ids:
            format_strings = ','.join(['%s'] * len(guest_ids))
            guest_query = f"""
                SELECT *
                FROM customers
                WHERE id IN ({format_strings})
            """
            cursor.execute(guest_query, tuple(guest_ids))
            guests = cursor.fetchall()
            for guest in guests:
                guests_map[guest["id"]] = {
                    "name": guest.get("name"),
                    "phone": guest.get("phone"),
                    "email": guest.get("email"),
                    "address": guest.get("address"),
                    "customer_type": guest.get("customer_type"),
                    "tax_number": guest.get("tax_number"),
                    "country": guest.get("country"),
                }
        # -------- Fetch company details --------
        company_ids = list({res["company_id"] for res in guest_reservations if res.get("company_id")})
        companies_map = {}
        if company_ids:
            format_strings = ','.join(['%s'] * len(company_ids))
            cursor.execute(f"""
                SELECT id, company_name, contact_person, address, phone, email,
                    pan_number, company_type, status, source
                FROM companies
                WHERE id IN ({format_strings})
            """, tuple(company_ids))
            for comp in cursor.fetchall():
                companies_map[comp["id"]] = {
                    "id": comp["id"],
                    "company_name": comp["company_name"],
                    "contact_person": comp["contact_person"],
                    "address": comp["address"],
                    "phone": comp["phone"],
                    "email": comp["email"],
                    "pan_number": comp["pan_number"],
                    "company_type": comp["company_type"],
                    "status": comp["status"],
                    "source": comp["source"],
                }

        # -------- Fetch room details (including room ID) for reservations --------
        rooms_map = {}
        if reservation_ids:
            format_strings = ','.join(['%s'] * len(reservation_ids))
            rooms_query = f"""
                SELECT 
                    rd.Reservation_ID, 
                    r.id as room_id,
                    r.room_no,
                    r.room_type,
                    r.room_state,
                    r.room_view,
                    r.preference as room_preference
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblrooms r ON rd.room_id = r.id
                WHERE rd.Reservation_ID IN ({format_strings})
                AND rd.is_current = 1
                AND rd.is_active = 1
                ORDER BY r.room_no
            """
            cursor.execute(rooms_query, tuple(reservation_ids))
            rooms = cursor.fetchall()
            for room in rooms:
                rid = room["Reservation_ID"]
                if rid not in rooms_map:
                    rooms_map[rid] = []
                
                # Create room details object
                room_details = {
                    "room_id": room["room_id"],
                    "room_no": room["room_no"],
                    "room_type": room.get("room_type"),
                    "room_state": room.get("room_state"),
                    "room_view": room.get("room_view"),
                    "room_preference": room.get("room_preference")
                }
                rooms_map[rid].append(room_details)

        # -------- Fetch fitrate data for all reservations --------
        fitrates_map = {}
        if reservation_ids:
            format_strings = ','.join(['%s'] * len(reservation_ids))
            fitrate_query = f"""
                SELECT 
                    fr.*,
                    rt.room_name,
                    rt.room_type,
                    rt.rate as room_rate,
                    rt.currency as room_currency,
                    mp.mp as meal_plan,
                    mp.rate as meal_rate,
                    mp.currency as meal_currency
                FROM hotel_tblfitrate fr
                LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
                LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
                WHERE fr.reservationID IN ({format_strings})
                AND fr.is_active = 1
                ORDER BY fr.id DESC
            """
            cursor.execute(fitrate_query, tuple(reservation_ids))
            fitrates = cursor.fetchall()
            
            for fr in fitrates:
                rid = fr["reservationID"]
                if rid not in fitrates_map:
                    fitrates_map[rid] = []
                
                # Format fitrate data
                formatted_fitrate = {
                    "id": fr["id"],
                    "quantity": fr["quantity"],
                    "rate_details": {
                        "id": fr["rateID"],
                        "room_name": fr.get("room_name"),
                        "room_type": fr.get("room_type"),
                        "rate": float(fr["room_rate"]) if fr.get("room_rate") else 0,
                        "currency": fr.get("room_currency")
                    } if fr["rateID"] else None,
                    "meal_details": {
                        "id": fr["mealID"],
                        "mp": fr.get("meal_plan"),
                        "rate": float(fr["meal_rate"]) if fr.get("meal_rate") else 0,
                        "currency": fr.get("meal_currency")
                    } if fr["mealID"] else None,
                    "created_at": fr["created_at"].strftime('%Y-%m-%d %H:%M:%S') if fr.get("created_at") else None
                }
                fitrates_map[rid].append(formatted_fitrate)


        # -------- Build final formatted response --------
        formatted_reservations = []
        for res in guest_reservations:
            # Calculate total amount from fitrates
            fitrates_for_res = fitrates_map.get(res["Reservation_ID"], [])
            total_amount = 0
            for fr in fitrates_for_res:
                if fr["rate_details"]:
                    total_amount += fr["quantity"] * fr["rate_details"]["rate"]
            
            formatted_reservations.append({
                "id": res["id"],
                "Reservation_ID": {
                    "id": res["Reservation_ID"],
                    "Guest_ID": guests_map.get(res["Guest_ID"], {}),
                    "company": companies_map.get(res.get("company_id")),   # None when there is no company
                    "Reservation_type": res.get("Reservation_type"),
                    "Current_Status": res.get("Current_Status"),
                    "Market_Seg": res.get("Market_Seg"),
                    "business_Src": res.get("business_Src"),
                    "Pay_Mode": res.get("Pay_Mode"),
                    "Billing_Inst": res.get("Billing_Inst"),
                    "designation": res.get("designation"),
                    "Check_In": res.get("Check_In"),
                    "Emp_ID": res.get("Emp_ID"),
                    "outlet": res.get("outlet"),
                    "is_complimentary": res.get("is_complimentary"),
                },
                "room_details": rooms_map.get(res["Reservation_ID"], []),  # Now returns list of room objects with IDs
                "start_date": res.get("start_date").strftime('%Y-%m-%d') if res.get("start_date") else None,
                "end_date": res.get("end_date").strftime('%Y-%m-%d') if res.get("end_date") else None,
                "No_of_adults": res.get("No_of_adults"),
                "No_of_children": res.get("No_of_children"),
                "Likes": res.get("Likes"),
                "Dislikes": res.get("Dislikes"),
                "Guest_Notes": res.get("Guest_Notes"),
                "designation": res.get("designation"),
                "Advance_Payment": res.get("Advance_Payment"),
                "Advance_Payment_Currency": res.get("Advance_Payment_Currency"),
                "Advance_Payment_Local": res.get("Advance_Payment_Local"),
                "reservation_outlet_id": res.get("reservation_outlet_id"),
                "Guest_Notes": res.get("Guest_Notes"),
                "fit_rates": fitrates_map.get(res["Reservation_ID"], []),
                "total_amount": total_amount,
                "fitrate_count": len(fitrates_map.get(res["Reservation_ID"], []))
            })

        mydb.close()

        return jsonify({
            "total_reservations": len(formatted_reservations),
            "guest_reservations": formatted_reservations
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500


@app_file402.route("/search-guestreservations/", methods=["POST"])
@cross_origin()
def search_guest_reservations():
    try:
        # -------- DB Connection --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

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
        json_data = request.get_json() or {}
        start_date_str = json_data.get("start_date", "")
        end_date_str = json_data.get("end_date", "")
        guest_name = json_data.get("guest_name", "")
        outlet = json_data.get("outlet", None)

        # Outlet is now required
        if not outlet:
            return jsonify({"error": "outlet is required."}), 400

        if not start_date_str or not end_date_str:
            return jsonify([]), 200

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)

        # -------- MAIN QUERY --------
        query = """
            SELECT g.*, r.Guest_ID, r.Reservation_type, r.Current_Status, r.Market_Seg, r.business_Src, r.Pay_Mode, r.Billing_Inst, r.designation, r.Check_In, r.Check_Out, r.Emp_ID, r.outlet
            FROM hotel_tblguestreservation g
            JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
            JOIN customers c ON r.Guest_ID = c.id
            WHERE g.start_date >= %s 
              AND g.start_date < %s
              AND r.Current_Status IN ('Reserved', 'Registered')
              AND r.outlet = %s
        """
        params = [start_date, end_date, outlet]

        if guest_name and guest_name.lower() != "null":
            query += " AND c.name LIKE %s"
            params.append(f"%{guest_name}%")

        query += " ORDER BY r.created_at DESC"

        cursor.execute(query, params)
        guest_reservations = cursor.fetchall()

        if not guest_reservations:
            mydb.close()
            return jsonify({
                "total_reservations": 0,
                "guest_reservations": []
            }), 200

        # -------- COLLECT IDS --------
        guest_ids = list(set([res["Guest_ID"] for res in guest_reservations if res["Guest_ID"]]))
        reservation_ids = list(set([res["Reservation_ID"] for res in guest_reservations]))

        # -------- FETCH GUEST DETAILS --------
        guests_map = {}
        if guest_ids:
            format_strings = ','.join(['%s'] * len(guest_ids))
            guest_query = f"""
                SELECT id, name, phone, email, address, guestPan, customer_type
                FROM customers
                WHERE id IN ({format_strings})
            """
            cursor.execute(guest_query, tuple(guest_ids))
            guests = cursor.fetchall()

            for g in guests:
                guests_map[g["id"]] = {
                    "name": g.get("name"),
                    "phone": g.get("phone"),
                    "email": g.get("email"),
                    "address": g.get("address"),
                    "customer_type": g.get("customer_type"),
                    "tax_number": g.get("guestPan")
                }

        # -------- FETCH ROOM DETAILS --------
        rooms_map = {}
        if reservation_ids:
            format_strings = ','.join(['%s'] * len(reservation_ids))
            rooms_query = f"""
                SELECT rd.Reservation_ID, r.room_no, r.room_type, r.id as room_id
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblrooms r ON rd.room_id = r.id
                WHERE rd.Reservation_ID IN ({format_strings})
            """
            cursor.execute(rooms_query, tuple(reservation_ids))
            rooms = cursor.fetchall()

            for room in rooms:
                rid = room["Reservation_ID"]
                if rid not in rooms_map:
                    rooms_map[rid] = []
                rooms_map[rid].append({
                    "room_id": room["room_id"],
                    "room_no": f"Room {room['room_no']}",
                    "room_type": room.get("room_type")
                })

        # -------- FETCH FITRATE DATA --------
        fitrates_map = {}
        if reservation_ids:
            format_strings = ','.join(['%s'] * len(reservation_ids))
            fitrate_query = f"""
                SELECT 
                    fr.*,
                    rt.room_name,
                    rt.room_type as rate_room_type,
                    rt.rate as room_rate,
                    rt.currency as room_currency,
                    mp.mp as meal_plan,
                    mp.rate as meal_rate,
                    mp.currency as meal_currency
                FROM hotel_tblfitrate fr
                LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
                LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id AND mp.is_active = 1
                WHERE fr.reservationID IN ({format_strings})
                AND fr.is_active = 1
                ORDER BY fr.id DESC
            """
            cursor.execute(fitrate_query, tuple(reservation_ids))
            fitrates = cursor.fetchall()

            for fr in fitrates:
                rid = fr["reservationID"]
                if rid not in fitrates_map:
                    fitrates_map[rid] = []

                # Format fitrate data
                formatted_fitrate = {
                    "id": fr["id"],
                    "quantity": fr["quantity"],
                    "rate_details": {
                        "id": fr["rateID"],
                        "room_name": fr.get("room_name"),
                        "room_type": fr.get("rate_room_type"),
                        "rate": float(fr["room_rate"]) if fr.get("room_rate") else 0,
                        "currency": fr.get("room_currency")
                    } if fr["rateID"] else None,
                    "meal_details": {
                        "id": fr["mealID"],
                        "mp": fr.get("meal_plan"),
                        "rate": float(fr["meal_rate"]) if fr.get("meal_rate") else 0,
                        "currency": fr.get("meal_currency")
                    } if fr["mealID"] else None,
                    "created_at": fr["created_at"].strftime('%Y-%m-%d %H:%M:%S') if fr.get("created_at") else None
                }
                fitrates_map[rid].append(formatted_fitrate)

        # -------- FINAL RESPONSE --------
        formatted_reservations = []

        for res in guest_reservations:
            # Calculate total amount from fitrates
            fitrates_for_res = fitrates_map.get(res["Reservation_ID"], [])
            total_amount = 0
            for fr in fitrates_for_res:
                if fr["rate_details"]:
                    total_amount += fr["quantity"] * fr["rate_details"]["rate"]

            formatted_reservations.append({
                "id": res["id"],
                "Reservation_ID": {
                    "id": res["Reservation_ID"],
                    "Guest_ID": guests_map.get(res["Guest_ID"], {}),
                    "Reservation_type": res.get("Reservation_type"),
                    "Current_Status": res.get("Current_Status") or "Reserved",
                    "Market_Seg": res.get("Market_Seg"),
                    "business_Src": res.get("business_Src"),
                    "Pay_Mode": res.get("Pay_Mode"),
                    "Billing_Inst": res.get("Billing_Inst"),
                    "designation": res.get("designation"),
                    "Check_In": res.get("Check_In"),
                    "Emp_ID": res.get("Emp_ID"),
                    "outlet": res.get("outlet"),
                },
                "room_details": rooms_map.get(res["Reservation_ID"], []),
                "start_date": res.get("start_date").strftime('%Y-%m-%d') if res.get("start_date") else None,
                "end_date": res.get("end_date").strftime('%Y-%m-%d') if res.get("end_date") else None,
                "No_of_adults": res.get("No_of_adults"),
                "No_of_children": res.get("No_of_children"),
                "Likes": res.get("Likes"),
                "Dislikes": res.get("Dislikes"),
                "Guest_Notes": res.get("Guest_Notes"),
                "fit_rates": fitrates_map.get(res["Reservation_ID"], []),
                "total_amount": total_amount,
                "fitrate_count": len(fitrates_map.get(res["Reservation_ID"], []))
            })

        mydb.close()

        return jsonify({
            "total_reservations": len(formatted_reservations),
            "guest_reservations": formatted_reservations
        }), 200

    except Exception as e:
        return {"error": str(e)}, 400


# @app_file402.route("/reservation_details/<int:room_id>", methods=["GET"])
# @cross_origin()
# def reservation_details_by_room(room_id):
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)
        
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # First, get the reservation details for the room
#         cursor.execute("""
#             SELECT rd.*, 
#                    r.id as room_table_id, r.room_no, r.room_type, r.outlet as room_outlet,
#                    res.id as reservation_id, res.Guest_ID, res.Current_Status, res.company_id,
#                    c.name as guest_name, c.address as guest_address, c.guestPan as guest_tax_number, 
#                    c.customer_type ,c.phone,
#                    gr.id as guest_reservation_id, gr.start_date, gr.end_date, 
#                    gr.No_of_children, gr.No_of_adults, gr.Likes, gr.Dislikes, gr.Guest_Notes, 
#                    res.Market_Seg, res.business_Src, res.Pay_Mode, res.Billing_Inst, 
#                    res.designation, res.Check_In, res.Check_Out, res.Emp_ID,
#                    comp.id as company_id, comp.company_name, comp.contact_person, 
#                    comp.address as company_address, comp.phone as company_phone, 
#                    comp.email as company_email, comp.pan_number as company_pan_number,
#                    comp.company_type, comp.status as company_status, comp.source as company_source

#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             INNER JOIN hotel_tblreservation res ON rd.Reservation_ID = res.id
#             INNER JOIN hotel_tblguestreservation gr ON res.id = gr.Reservation_ID
#             INNER JOIN customers c ON res.Guest_ID = c.id
#             LEFT JOIN companies comp ON res.company_id = comp.id
#             WHERE rd.room_id = %s
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#             AND res.is_active = 1
#             AND gr.is_active = 1
#             ORDER BY gr.start_date DESC
#             LIMIT 1
#         """, (room_id,))

#         reservation_detail = cursor.fetchone()

#         if not reservation_detail:
#             mydb.close()
#             return {"message": "Reservation details not found for this room"}, 404

#         # Get all rooms associated with this reservation (if any)
#         cursor.execute("""
#             SELECT r.id, r.room_no, r.room_type
#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             WHERE rd.Reservation_ID = %s 
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#         """, (reservation_detail['Reservation_ID'],))
        
#         rooms_data = cursor.fetchall()
        
#         # Format rooms data
#         rooms = []
#         for room in rooms_data:
#             rooms.append({
#                 "Reservation_ID": reservation_detail['Reservation_ID'],
#                 "room_id": {
#                     "id": room['id'],
#                     "room_no": str(room['room_no']),
#                     "room_type": room['room_type']
#                 }
#             })

#         # Get Fit rates for this reservation
#         cursor.execute("""
#             SELECT fr.id, fr.quantity, fr.rateID, fr.mealID,
#                    rt.rate as room_rate, rt.room_type as rate_room_type, 
#                    rt.room_name, rt.currency as rate_currency,
#                    mp.mp, mp.rate as meal_rate, mp.currency as meal_currency
#             FROM hotel_tblfitrate fr
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#             WHERE fr.reservationID = %s
#             AND fr.is_active = 1
#         """, (reservation_detail['Reservation_ID'],))
        
#         fit_rates_data = cursor.fetchall()
        
#         # Format fit rates data
#         fit_rates = []
#         for fr in fit_rates_data:
#             fit_rate_item = {
#                 "quantity": fr['quantity'],
#                 "rateID": {
#                     "rate": str(fr['room_rate']),
#                     "room_type": fr['rate_room_type'],
#                     "room_name": fr['room_name'],
#                     "currency": fr['rate_currency']
#                 }
#             }
            
#             # Add meal info if exists
#             if fr['mealID']:
#                 fit_rate_item["mealID"] = {
#                     "mp": fr['mp'],
#                     "rate": str(fr['meal_rate'])
#                 }
            
#             fit_rates.append(fit_rate_item)

#         # Build company data if exists
#         company_data = None
#         if reservation_detail.get('company_id'):
#             company_data = {
#                 "id": reservation_detail['company_id'],
#                 "company_name": reservation_detail['company_name'],
#                 "contact_person": reservation_detail['contact_person'],
#                 "address": reservation_detail['company_address'],
#                 "phone": reservation_detail['company_phone'],
#                 "email": reservation_detail['company_email'],
#                 "pan_number": reservation_detail['company_pan_number'],
#                 "company_type": reservation_detail['company_type'],
#                 "status": reservation_detail['company_status'],
#                 "source": reservation_detail['company_source']
#             }

#         # Construct the response in the required format
#         response = {
#             "rooms": rooms,
#             "GuestReservation_ID": {
#                 "id": reservation_detail['guest_reservation_id'],
#                 "start_date": reservation_detail['start_date'].strftime('%Y-%m-%d') if reservation_detail['start_date'] else None,
#                 "end_date": reservation_detail['end_date'].strftime('%Y-%m-%d') if reservation_detail['end_date'] else None,
#                 "No_of_children": reservation_detail['No_of_children'],
#                 "No_of_adults": reservation_detail['No_of_adults'],
#                 "Likes": reservation_detail['Likes'],
#                 "Dislikes": reservation_detail['Dislikes'],
#                 "Guest_Notes": reservation_detail['Guest_Notes'],
#                 "Reservation_ID": {
#                     "id": reservation_detail['reservation_id'],
#                     "Guest_ID": {
#                         "id": reservation_detail['Guest_ID'],
#                         "name": reservation_detail['guest_name'],
#                         "address": reservation_detail['guest_address'],
#                         "tax_number": reservation_detail['guest_tax_number'],
#                         "customer_type": reservation_detail.get("customer_type"),
#                         "phone": reservation_detail.get("phone"),
#                     },
#                     "Current_Status": reservation_detail['Current_Status'],
#                     "Market_Seg": reservation_detail.get("Market_Seg"),
#                     "business_Src": reservation_detail.get("business_Src"),
#                     "Pay_Mode": reservation_detail.get("Pay_Mode"),
#                     "Billing_Inst": reservation_detail.get("Billing_Inst"),
#                     "designation": reservation_detail.get("designation"),
#                     "Check_In": reservation_detail.get("Check_In"),
#                     "Emp_ID": reservation_detail.get("Emp_ID"),
#                     "company": company_data  # Add company data here
#                 },
#                 "Fit_rate": fit_rates
#             }
#         }

#         mydb.close()
#         return jsonify(response), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400


# @app_file402.route("/reservation_details/<int:room_id>", methods=["GET"])
# @cross_origin()
# def reservation_details_by_room(room_id):
#     mydb = None
#     cursor = None
#     try:
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # First, get the reservation details for the room
#         cursor.execute("""
#             SELECT rd.*, 
#                    r.id as room_table_id, r.room_no, r.room_type, r.outlet as room_outlet,
#                    res.id as reservation_id, res.Guest_ID, res.Current_Status, res.company_id,
#                    c.name as guest_name, c.address as guest_address, c.guestPan as guest_tax_number, 
#                    c.customer_type, c.phone, c.country as guest_country,
#                    gr.id as guest_reservation_id, gr.start_date, gr.end_date, 
#                    gr.No_of_children, gr.No_of_adults, gr.Likes, gr.Dislikes, gr.Guest_Notes, 
#                    res.Market_Seg, res.business_Src, res.Pay_Mode, res.Billing_Inst, 
#                    res.designation, res.Check_In, res.Check_Out, res.Emp_ID,
#                    res.Advance_Payment, res.Advance_Payment_Currency, res.Advance_Payment_Local,
#                    comp.id as company_id, comp.company_name, comp.contact_person, 
#                    comp.address as company_address, comp.phone as company_phone, 
#                    comp.email as company_email, comp.pan_number as company_pan_number,
#                    comp.company_type, comp.status as company_status, comp.source as company_source

#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             INNER JOIN hotel_tblreservation res ON rd.Reservation_ID = res.id
#             INNER JOIN hotel_tblguestreservation gr ON res.id = gr.Reservation_ID
#             INNER JOIN customers c ON res.Guest_ID = c.id
#             LEFT JOIN companies comp ON res.company_id = comp.id
#             WHERE rd.room_id = %s
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#             AND res.is_active = 1
#             AND gr.is_active = 1
#             ORDER BY gr.start_date DESC
#             LIMIT 1
#         """, (room_id,))

#         reservation_detail = cursor.fetchone()

#         if not reservation_detail:
#             return {"message": "Reservation details not found for this room"}, 404

#         # Get all rooms associated with this reservation (if any)
#         cursor.execute("""
#             SELECT r.id, r.room_no, r.room_type
#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             WHERE rd.Reservation_ID = %s 
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#         """, (reservation_detail['Reservation_ID'],))

#         rooms_data = cursor.fetchall()

#         # Format rooms data
#         rooms = []
#         for room in rooms_data:
#             rooms.append({
#                 "Reservation_ID": reservation_detail['Reservation_ID'],
#                 "room_id": {
#                     "id": room['id'],
#                     "room_no": str(room['room_no']),
#                     "room_type": room['room_type']
#                 }
#             })

#         # Get Fit rates for this reservation
#         cursor.execute("""
#             SELECT fr.id, fr.quantity, fr.rateID, fr.mealID,
#                    rt.rate as room_rate, rt.room_type as rate_room_type, 
#                    rt.room_name, rt.currency as rate_currency,
#                    mp.mp, mp.rate as meal_rate, mp.currency as meal_currency
#             FROM hotel_tblfitrate fr
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#             WHERE fr.reservationID = %s
#             AND fr.is_active = 1
#         """, (reservation_detail['Reservation_ID'],))

#         fit_rates_data = cursor.fetchall()

#         # Format fit rates data
#         fit_rates = []
#         for fr in fit_rates_data:
#             fit_rate_item = {
#                 "fitrate_id": fr["id"],
#                 "quantity": fr['quantity'],
#                 "rateID": {
#                     "rate": str(fr['room_rate']),
#                     "room_type": fr['rate_room_type'],
#                     "room_name": fr['room_name'],
#                     "currency": fr['rate_currency']
#                 }
#             }

#             # Add meal info if exists
#             if fr['mealID']:
#                 fit_rate_item["mealID"] = {
#                     "mp": fr['mp'],
#                     "rate": str(fr['meal_rate'])
#                 }

#             fit_rates.append(fit_rate_item)

#         # Build company data if exists
#         company_data = None
#         if reservation_detail.get('company_id'):
#             company_data = {
#                 "id": reservation_detail['company_id'],
#                 "company_name": reservation_detail['company_name'],
#                 "contact_person": reservation_detail['contact_person'],
#                 "address": reservation_detail['company_address'],
#                 "phone": reservation_detail['company_phone'],
#                 "email": reservation_detail['company_email'],
#                 "pan_number": reservation_detail['company_pan_number'],
#                 "company_type": reservation_detail['company_type'],
#                 "status": reservation_detail['company_status'],
#                 "source": reservation_detail['company_source']
#             }

#         # Money helper: Decimal -> float, NULL -> 0
#         def _money(value):
#             return float(value) if value is not None else 0

#         # Construct the response in the required format
#         response = {
#             "rooms": rooms,
#             "GuestReservation_ID": {
#                 "id": reservation_detail['guest_reservation_id'],
#                 "start_date": reservation_detail['start_date'].strftime('%Y-%m-%d') if reservation_detail['start_date'] else None,
#                 "end_date": reservation_detail['end_date'].strftime('%Y-%m-%d') if reservation_detail['end_date'] else None,
#                 "No_of_children": reservation_detail['No_of_children'],
#                 "No_of_adults": reservation_detail['No_of_adults'],
#                 "Likes": reservation_detail['Likes'],
#                 "Dislikes": reservation_detail['Dislikes'],
#                 "Guest_Notes": reservation_detail['Guest_Notes'],
#                 "Reservation_ID": {
#                     "id": reservation_detail['reservation_id'],
#                     "Guest_ID": {
#                         "id": reservation_detail['Guest_ID'],
#                         "name": reservation_detail['guest_name'],
#                         "address": reservation_detail['guest_address'],
#                         "tax_number": reservation_detail['guest_tax_number'],
#                         "customer_type": reservation_detail.get("customer_type"),
#                         "phone": reservation_detail.get("phone"),
#                         "country": reservation_detail.get("guest_country"),
#                     },
#                     "Current_Status": reservation_detail['Current_Status'],
#                     "Market_Seg": reservation_detail.get("Market_Seg"),
#                     "business_Src": reservation_detail.get("business_Src"),
#                     "Pay_Mode": reservation_detail.get("Pay_Mode"),
#                     "Billing_Inst": reservation_detail.get("Billing_Inst"),
#                     "Advance_Payment": _money(reservation_detail.get("Advance_Payment")),
#                     "Advance_Payment_Currency": reservation_detail.get("Advance_Payment_Currency"),
#                     "Advance_Payment_Local": _money(reservation_detail.get("Advance_Payment_Local")),
#                     "designation": reservation_detail.get("designation"),
#                     "Check_In": reservation_detail.get("Check_In"),
#                     "Emp_ID": reservation_detail.get("Emp_ID"),
#                     "company": company_data
#                 },
#                 "Fit_rate": fit_rates
#             }
#         }

#         return jsonify(response), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()

# @app_file402.route("/reservation_details/<int:room_id>", methods=["GET"])
# @cross_origin()
# def reservation_details_by_room(room_id):
#     mydb = None
#     cursor = None
#     try:
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Reservation currently holding this room.
#         # Status filter: checked-out / cancelled reservations may still carry
#         # is_current = 1 on their last room, so they must never be returned here.
#         # ORDER BY: an in-house (Registered) guest always wins over a future booking.
#         cursor.execute("""
#             SELECT rd.*, 
#                    r.id as room_table_id, r.room_no, r.room_type, r.outlet as room_outlet,
#                    res.id as reservation_id, res.Guest_ID, res.Current_Status, res.company_id,
#                    c.name as guest_name, c.address as guest_address, c.guestPan as guest_tax_number, 
#                    c.customer_type, c.phone, c.country as guest_country,
#                    gr.id as guest_reservation_id, gr.start_date, gr.end_date, 
#                    gr.No_of_children, gr.No_of_adults, gr.Likes, gr.Dislikes, gr.Guest_Notes, 
#                    res.Market_Seg, res.business_Src, res.Pay_Mode, res.Billing_Inst, 
#                    res.designation, res.Check_In, res.Check_Out, res.Emp_ID,
#                    res.Advance_Payment, res.Advance_Payment_Currency, res.Advance_Payment_Local,
#                    comp.id as company_id, comp.company_name, comp.contact_person, 
#                    comp.address as company_address, comp.phone as company_phone, 
#                    comp.email as company_email, comp.pan_number as company_pan_number,
#                    comp.company_type, comp.status as company_status, comp.source as company_source

#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             INNER JOIN hotel_tblreservation res ON rd.Reservation_ID = res.id
#             INNER JOIN hotel_tblguestreservation gr ON res.id = gr.Reservation_ID
#             INNER JOIN customers c ON res.Guest_ID = c.id
#             LEFT JOIN companies comp ON res.company_id = comp.id
#             WHERE rd.room_id = %s
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#             AND res.is_active = 1
#             AND res.Current_Status IN ('Registered', 'Reserved')
#             AND gr.is_active = 1
#             ORDER BY (res.Current_Status = 'Registered') DESC,
#                      gr.start_date DESC
#             LIMIT 1
#         """, (room_id,))

#         reservation_detail = cursor.fetchone()

#         if not reservation_detail:
#             return {"message": "Reservation details not found for this room"}, 404

#         # Get all rooms associated with this reservation (if any)
#         cursor.execute("""
#             SELECT r.id, r.room_no, r.room_type
#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             WHERE rd.Reservation_ID = %s 
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#         """, (reservation_detail['Reservation_ID'],))

#         rooms_data = cursor.fetchall()

#         # Format rooms data
#         rooms = []
#         for room in rooms_data:
#             rooms.append({
#                 "Reservation_ID": reservation_detail['Reservation_ID'],
#                 "room_id": {
#                     "id": room['id'],
#                     "room_no": str(room['room_no']),
#                     "room_type": room['room_type']
#                 }
#             })

#         # Get Fit rates for this reservation
#         cursor.execute("""
#             SELECT fr.id, fr.quantity, fr.rateID, fr.mealID,
#                    rt.rate as room_rate, rt.room_type as rate_room_type, 
#                    rt.room_name, rt.currency as rate_currency,
#                    mp.mp, mp.rate as meal_rate, mp.currency as meal_currency
#             FROM hotel_tblfitrate fr
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#             WHERE fr.reservationID = %s
#             AND fr.is_active = 1
#         """, (reservation_detail['Reservation_ID'],))

#         fit_rates_data = cursor.fetchall()

#         # Format fit rates data
#         fit_rates = []
#         for fr in fit_rates_data:
#             fit_rate_item = {
#                 "fitrate_id": fr["id"],
#                 "quantity": fr['quantity'],
#                 "rateID": {
#                     "rate": str(fr['room_rate']),
#                     "room_type": fr['rate_room_type'],
#                     "room_name": fr['room_name'],
#                     "currency": fr['rate_currency']
#                 }
#             }

#             # Add meal info if exists
#             if fr['mealID']:
#                 fit_rate_item["mealID"] = {
#                     "mp": fr['mp'],
#                     "rate": str(fr['meal_rate'])
#                 }

#             fit_rates.append(fit_rate_item)

#         # Build company data if exists
#         company_data = None
#         if reservation_detail.get('company_id'):
#             company_data = {
#                 "id": reservation_detail['company_id'],
#                 "company_name": reservation_detail['company_name'],
#                 "contact_person": reservation_detail['contact_person'],
#                 "address": reservation_detail['company_address'],
#                 "phone": reservation_detail['company_phone'],
#                 "email": reservation_detail['company_email'],
#                 "pan_number": reservation_detail['company_pan_number'],
#                 "company_type": reservation_detail['company_type'],
#                 "status": reservation_detail['company_status'],
#                 "source": reservation_detail['company_source']
#             }

#         # Money helper: Decimal -> float, NULL -> 0
#         def _money(value):
#             return float(value) if value is not None else 0

#         # General bills posted to the room / on credit.
#         # These are settled at checkout of the whole reservation, so they are
#         # returned for the reservation no matter which room was requested.
#         cursor.execute("""
#             SELECT id, bill_number, bill_type, fiscal_year, bill_date, outlet,
#                    room_no, customer_id, customer_name, payment_mode, narration,
#                    sub_total, discount_amount, taxable_amount, tax_amount,
#                    grand_total, created_by
#             FROM hotel_generalbills
#             WHERE reservation_id = %s
#             AND payment_mode IN ('Room Charge', 'Credit')
#             ORDER BY bill_date, id
#         """, (reservation_detail['Reservation_ID'],))
#         general_bills_data = cursor.fetchall()

#         # Items for all those bills in one query
#         items_by_bill = {}
#         if general_bills_data:
#             bill_ids = [b['id'] for b in general_bills_data]
#             placeholders = ", ".join(["%s"] * len(bill_ids))
#             cursor.execute(f"""
#                 SELECT bill_id, item_name, quantity, rate, is_taxable,
#                        subtotal, vat_amount, total
#                 FROM hotel_generalbill_items
#                 WHERE bill_id IN ({placeholders})
#                 ORDER BY id
#             """, tuple(bill_ids))
#             for it in cursor.fetchall():
#                 items_by_bill.setdefault(it['bill_id'], []).append({
#                     "item_name": it['item_name'],
#                     "quantity": _money(it['quantity']),
#                     "rate": _money(it['rate']),
#                     "is_taxable": bool(it['is_taxable']),
#                     "subtotal": _money(it['subtotal']),
#                     "vat_amount": _money(it['vat_amount']),
#                     "total": _money(it['total']),
#                 })

#         general_bills = []
#         for b in general_bills_data:
#             general_bills.append({
#                 "bill_id": b['id'],
#                 "bill_number": b['bill_number'],
#                 "bill_type": b['bill_type'],
#                 "fiscal_year": b['fiscal_year'],
#                 "bill_date": b['bill_date'].strftime('%Y-%m-%d') if b['bill_date'] else None,
#                 "outlet": b['outlet'],
#                 "room_no": b['room_no'],
#                 "customer_id": b['customer_id'],
#                 "customer_name": b['customer_name'],
#                 "payment_mode": b['payment_mode'],
#                 "narration": b['narration'],
#                 "sub_total": _money(b['sub_total']),
#                 "discount_amount": _money(b['discount_amount']),
#                 "taxable_amount": _money(b['taxable_amount']),
#                 "tax_amount": _money(b['tax_amount']),
#                 "grand_total": _money(b['grand_total']),
#                 "created_by": b['created_by'],
#                 "items": items_by_bill.get(b['id'], []),
#             })

#         general_bills_total = sum(b["grand_total"] for b in general_bills)

#         # Construct the response in the required format
#         response = {
#             "rooms": rooms,
#             "general_bills": general_bills,
#             "general_bills_total": general_bills_total,
#             "GuestReservation_ID": {
#                 "id": reservation_detail['guest_reservation_id'],
#                 "start_date": reservation_detail['start_date'].strftime('%Y-%m-%d') if reservation_detail['start_date'] else None,
#                 "end_date": reservation_detail['end_date'].strftime('%Y-%m-%d') if reservation_detail['end_date'] else None,
#                 "No_of_children": reservation_detail['No_of_children'],
#                 "No_of_adults": reservation_detail['No_of_adults'],
#                 "Likes": reservation_detail['Likes'],
#                 "Dislikes": reservation_detail['Dislikes'],
#                 "Guest_Notes": reservation_detail['Guest_Notes'],
#                 "Reservation_ID": {
#                     "id": reservation_detail['reservation_id'],
#                     "Guest_ID": {
#                         "id": reservation_detail['Guest_ID'],
#                         "name": reservation_detail['guest_name'],
#                         "address": reservation_detail['guest_address'],
#                         "tax_number": reservation_detail['guest_tax_number'],
#                         "customer_type": reservation_detail.get("customer_type"),
#                         "phone": reservation_detail.get("phone"),
#                         "country": reservation_detail.get("guest_country"),
#                     },
#                     "Current_Status": reservation_detail['Current_Status'],
#                     "Market_Seg": reservation_detail.get("Market_Seg"),
#                     "business_Src": reservation_detail.get("business_Src"),
#                     "Pay_Mode": reservation_detail.get("Pay_Mode"),
#                     "Billing_Inst": reservation_detail.get("Billing_Inst"),
#                     "Advance_Payment": _money(reservation_detail.get("Advance_Payment")),
#                     "Advance_Payment_Currency": reservation_detail.get("Advance_Payment_Currency"),
#                     "Advance_Payment_Local": _money(reservation_detail.get("Advance_Payment_Local")),
#                     "designation": reservation_detail.get("designation"),
#                     "Check_In": reservation_detail.get("Check_In"),
#                     "Check_Out": reservation_detail.get("Check_Out"),
#                     "Emp_ID": reservation_detail.get("Emp_ID"),
#                     "company": company_data
#                 },
#                 "Fit_rate": fit_rates
#             }
#         }

#         return jsonify(response), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()




@app_file402.route("/reservation_details/<int:room_id>", methods=["GET"])
@cross_origin()
def reservation_details_by_room(room_id):
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Reservation currently holding this room.
        # Status filter: checked-out / cancelled reservations may still carry
        # is_current = 1 on their last room, so they must never be returned here.
        # ORDER BY: an in-house (Registered) guest always wins over a future booking.
        cursor.execute("""
            SELECT rd.*, 
                   r.id as room_table_id, r.room_no, r.room_type, r.outlet as room_outlet,
                   res.id as reservation_id, res.Guest_ID, res.Current_Status, res.company_id,
                   c.name as guest_name, c.address as guest_address, c.guestPan as guest_tax_number, 
                   c.customer_type, c.phone, c.country as guest_country,
                   gr.id as guest_reservation_id, gr.start_date, gr.end_date, 
                   gr.No_of_children, gr.No_of_adults, gr.Likes, gr.Dislikes, gr.Guest_Notes, 
                   res.Market_Seg, res.business_Src, res.Pay_Mode, res.Billing_Inst, 
                   res.designation, res.Check_In, res.Check_Out, res.Emp_ID,
                   res.Advance_Payment, res.Advance_Payment_Currency, res.Advance_Payment_Local,
                   comp.id as company_id, comp.company_name, comp.contact_person, 
                   comp.address as company_address, comp.phone as company_phone, 
                   comp.email as company_email, comp.pan_number as company_pan_number,
                   comp.company_type, comp.status as company_status, comp.source as company_source, res.is_complimentary

            FROM hotel_tblreservation_details rd
            INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
            INNER JOIN hotel_tblreservation res ON rd.Reservation_ID = res.id
            INNER JOIN hotel_tblguestreservation gr ON res.id = gr.Reservation_ID
            INNER JOIN customers c ON res.Guest_ID = c.id
            LEFT JOIN companies comp ON res.company_id = comp.id
            WHERE rd.room_id = %s
            AND rd.is_current = TRUE
            AND rd.is_active = 1
            AND r.is_active = 1
            AND res.is_active = 1
            AND res.Current_Status IN ('Registered', 'Reserved')
            AND gr.is_active = 1
            ORDER BY (res.Current_Status = 'Registered') DESC,
                     gr.start_date DESC
            LIMIT 1
        """, (room_id,))

        reservation_detail = cursor.fetchone()

        if not reservation_detail:
            return {"message": "Reservation details not found for this room"}, 404

        # Get all rooms associated with this reservation (if any)
        cursor.execute("""
            SELECT r.id, r.room_no, r.room_type
            FROM hotel_tblreservation_details rd
            INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
            WHERE rd.Reservation_ID = %s 
            AND rd.is_current = TRUE
            AND rd.is_active = 1
            AND r.is_active = 1
        """, (reservation_detail['Reservation_ID'],))

        rooms_data = cursor.fetchall()

        # Format rooms data
        rooms = []
        for room in rooms_data:
            rooms.append({
                "Reservation_ID": reservation_detail['Reservation_ID'],
                "room_id": {
                    "id": room['id'],
                    "room_no": str(room['room_no']),
                    "room_type": room['room_type']
                }
            })

        # Get Fit rates for this reservation
        cursor.execute("""
            SELECT fr.id, fr.quantity, fr.rateID, fr.mealID,
                   rt.rate as room_rate, rt.room_type as rate_room_type, 
                   rt.room_name, rt.currency as rate_currency, rt.occupancy as rate_occupancy,
                   mp.mp, mp.rate as meal_rate, mp.currency as meal_currency
            FROM hotel_tblfitrate fr
            INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
            LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
            WHERE fr.reservationID = %s
            AND fr.is_active = 1
        """, (reservation_detail['Reservation_ID'],))

        fit_rates_data = cursor.fetchall()

        # Format fit rates data
        fit_rates = []
        for fr in fit_rates_data:
            fit_rate_item = {
                "fitrate_id": fr["id"],
                "quantity": fr['quantity'],
                "rateID": {
                    "rate": str(fr['room_rate']),
                    "room_type": fr['rate_room_type'],
                    "room_name": fr['room_name'],
                    "currency": fr['rate_currency'],
                    "occupancy": fr['rate_occupancy']
                }
            }

            # Add meal info if exists
            if fr['mealID']:
                fit_rate_item["mealID"] = {
                    "mp": fr['mp'],
                    "rate": str(fr['meal_rate'])
                }

            fit_rates.append(fit_rate_item)

        # Build company data if exists
        company_data = None
        if reservation_detail.get('company_id'):
            company_data = {
                "id": reservation_detail['company_id'],
                "company_name": reservation_detail['company_name'],
                "contact_person": reservation_detail['contact_person'],
                "address": reservation_detail['company_address'],
                "phone": reservation_detail['company_phone'],
                "email": reservation_detail['company_email'],
                "pan_number": reservation_detail['company_pan_number'],
                "company_type": reservation_detail['company_type'],
                "status": reservation_detail['company_status'],
                "source": reservation_detail['company_source']
            }

        # Money helper: Decimal -> float, NULL -> 0
        def _money(value):
            return float(value) if value is not None else 0


        # General bills posted to the room / on credit.
        # These are settled at checkout of the whole reservation, so they are
        # returned for the reservation no matter which room was requested.
        cursor.execute("""
            SELECT id, bill_number, bill_type, fiscal_year, bill_date, outlet,
                   room_no, customer_id, customer_name, payment_mode, narration,
                   sub_total, discount_amount, taxable_amount, tax_amount,
                   grand_total, created_by
            FROM hotel_generalbills
            WHERE reservation_id = %s
            AND payment_mode IN ('Room Charge', 'Credit')
            ORDER BY bill_date, id
        """, (reservation_detail['Reservation_ID'],))
        general_bills_data = cursor.fetchall()

        # Items for all those bills in one query
        items_by_bill = {}
        if general_bills_data:
            bill_ids = [b['id'] for b in general_bills_data]
            placeholders = ", ".join(["%s"] * len(bill_ids))
            cursor.execute(f"""
                SELECT bill_id, item_name, quantity, rate, is_taxable,
                       subtotal, vat_amount, total
                FROM hotel_generalbill_items
                WHERE bill_id IN ({placeholders})
                ORDER BY id
            """, tuple(bill_ids))
            for it in cursor.fetchall():
                items_by_bill.setdefault(it['bill_id'], []).append({
                    "item_name": it['item_name'],
                    "quantity": _money(it['quantity']),
                    "rate": _money(it['rate']),
                    "is_taxable": bool(it['is_taxable']),
                    "subtotal": _money(it['subtotal']),
                    "vat_amount": _money(it['vat_amount']),
                    "total": _money(it['total']),
                })

        general_bills = []
        for b in general_bills_data:
            general_bills.append({
                "bill_id": b['id'],
                "bill_number": b['bill_number'],
                "bill_type": b['bill_type'],
                "fiscal_year": b['fiscal_year'],
                "bill_date": b['bill_date'].strftime('%Y-%m-%d') if b['bill_date'] else None,
                "outlet": b['outlet'],
                "room_no": b['room_no'],
                "customer_id": b['customer_id'],
                "customer_name": b['customer_name'],
                "payment_mode": b['payment_mode'],
                "narration": b['narration'],
                "sub_total": _money(b['sub_total']),
                "discount_amount": _money(b['discount_amount']),
                "taxable_amount": _money(b['taxable_amount']),
                "tax_amount": _money(b['tax_amount']),
                "grand_total": _money(b['grand_total']),
                "created_by": b['created_by'],
                "items": items_by_bill.get(b['id'], []),
            })

        general_bills_total = sum(b["grand_total"] for b in general_bills)

        # Restaurant orders charged to this reservation's room.
        # Settled at hotel checkout, so returned for the whole reservation.
        cursor.execute("""
            SELECT idtblorderHistory, Outlet_OrderID, bill_no, fiscal_year,
                   Outlet_Name, Table_No, Employee, Date, State, Type,
                   Total, serviceCharge, VAT, DiscountAmt, PaymentMode,
                   GuestName, hotel_room_no
            FROM tblorderhistory
            WHERE hotel_reservation_id = %s
            AND PaymentMode = 'Room Charge'
            ORDER BY idtblorderHistory
        """, (reservation_detail['Reservation_ID'],))
        restaurant_orders_data = cursor.fetchall()

        # Items for all those orders in one query
        order_items = {}
        if restaurant_orders_data:
            order_ids = [o['idtblorderHistory'] for o in restaurant_orders_data]
            placeholders = ", ".join(["%s"] * len(order_ids))
            cursor.execute(f"""
                SELECT order_ID, ItemName, itemRate, Total, ItemType,
                       Description, discountExempt, count
                FROM tblorder_detailshistory
                WHERE order_ID IN ({placeholders})
                ORDER BY 1
            """, tuple(order_ids))
            for it in cursor.fetchall():
                order_items.setdefault(it['order_ID'], []).append({
                    "item_name": it['ItemName'],
                    "rate": _money(it['itemRate']),
                    "count": it['count'],
                    "total": _money(it['Total']),
                    "item_type": it['ItemType'],
                    "description": it['Description'],
                    "discount_exempt": it['discountExempt'],
                })

        restaurant_orders = []
        for o in restaurant_orders_data:
            restaurant_orders.append({
                "order_history_id": o['idtblorderHistory'],
                "outlet_order_id": o['Outlet_OrderID'],
                "bill_no": o['bill_no'],
                "fiscal_year": o['fiscal_year'],
                "outlet": o['Outlet_Name'],
                "room_no": o['hotel_room_no'],
                "table_no": o['Table_No'],
                "employee": o['Employee'],
                "date": o['Date'],
                "state": o['State'],
                "type": o['Type'],
                "total": _money(o['Total']),
                "service_charge": _money(o['serviceCharge']),
                "vat": _money(o['VAT']),
                "discount_amount": _money(o['DiscountAmt']),
                "payment_mode": o['PaymentMode'],
                "guest_name": o['GuestName'],
                "items": order_items.get(o['idtblorderHistory'], []),
            })

        restaurant_orders_total = sum(o["total"] for o in restaurant_orders)

        # Construct the response in the required format
        response = {
            "rooms": rooms,
            "general_bills": general_bills,
            "general_bills_total": general_bills_total,
            "restaurant_orders": restaurant_orders,
            "restaurant_orders_total": restaurant_orders_total,
            "GuestReservation_ID": {
                "id": reservation_detail['guest_reservation_id'],
                "start_date": reservation_detail['start_date'].strftime('%Y-%m-%d') if reservation_detail['start_date'] else None,
                "end_date": reservation_detail['end_date'].strftime('%Y-%m-%d') if reservation_detail['end_date'] else None,
                "No_of_children": reservation_detail['No_of_children'],
                "No_of_adults": reservation_detail['No_of_adults'],
                "Likes": reservation_detail['Likes'],
                "Dislikes": reservation_detail['Dislikes'],
                "Guest_Notes": reservation_detail['Guest_Notes'],
                "Reservation_ID": {
                    "id": reservation_detail['reservation_id'],
                    "Guest_ID": {
                        "id": reservation_detail['Guest_ID'],
                        "name": reservation_detail['guest_name'],
                        "address": reservation_detail['guest_address'],
                        "tax_number": reservation_detail['guest_tax_number'],
                        "customer_type": reservation_detail.get("customer_type"),
                        "phone": reservation_detail.get("phone"),
                        "country": reservation_detail.get("guest_country"),
                    },
                    "Current_Status": reservation_detail['Current_Status'],
                    "Market_Seg": reservation_detail.get("Market_Seg"),
                    "business_Src": reservation_detail.get("business_Src"),
                    "Pay_Mode": reservation_detail.get("Pay_Mode"),
                    "Billing_Inst": reservation_detail.get("Billing_Inst"),
                    "Advance_Payment": _money(reservation_detail.get("Advance_Payment")),
                    "Advance_Payment_Currency": reservation_detail.get("Advance_Payment_Currency"),
                    "Advance_Payment_Local": _money(reservation_detail.get("Advance_Payment_Local")),
                    "designation": reservation_detail.get("designation"),
                    "Check_In": reservation_detail.get("Check_In"),
                    "Check_Out": reservation_detail.get("Check_Out"),
                    "is_complimentary": reservation_detail.get("is_complimentary"),
                    "Emp_ID": reservation_detail.get("Emp_ID"),
                    "company": company_data
                },
                "Fit_rate": fit_rates
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


# Alternative endpoint to get reservation details by reservation ID instead of room ID
@app_file402.route("/reservation_details_by_reservation/<int:reservation_id>", methods=["GET"])
@cross_origin()
def reservation_details_by_reservation(reservation_id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)
        
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get all rooms for this reservation
        cursor.execute("""
            SELECT r.id, r.room_no, r.room_type, r.outlet
            FROM hotel_tblreservation_details rd
            INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
            WHERE rd.Reservation_ID = %s
            AND rd.is_current = TRUE
            AND rd.is_active = 1
            AND r.is_active = 1
        """, (reservation_id,))
        
        rooms_data = cursor.fetchall()
        
        # Format rooms data
        rooms = []
        for room in rooms_data:
            rooms.append({
                "Reservation_ID": reservation_id,
                "room_id": {
                    "id": room['id'],
                    "room_no": str(room['room_no']),
                    "room_type": room['room_type']
                }
            })

        # Get reservation and guest details
        cursor.execute("""
            SELECT res.id, res.Guest_ID, res.Current_Status, res.outlet,
                   c.name as guest_name, c.address as guest_address, c.tax_number as guest_tax_number,
                   gr.id as guest_reservation_id, gr.start_date, gr.end_date,
                   gr.No_of_children, gr.No_of_adults, gr.Likes, gr.Dislikes, gr.Guest_Notes
            FROM hotel_tblreservation res
            INNER JOIN hotel_tblguestreservation gr ON res.id = gr.Reservation_ID
            INNER JOIN customers c ON res.Guest_ID = c.id
            WHERE res.id = %s
            AND res.is_active = 1
            AND gr.is_active = 1
        """, (reservation_id,))
        
        reservation_data = cursor.fetchone()

        if not reservation_data:
            mydb.close()
            return {"message": "Reservation not found"}, 404

        # Get Fit rates for this reservation
        cursor.execute("""
            SELECT fr.id, fr.quantity, fr.rateID, fr.mealID,
                   rt.rate as room_rate, rt.room_type as rate_room_type, 
                   rt.room_name, rt.currency as rate_currency,
                   mp.mp, mp.rate as meal_rate, mp.currency as meal_currency
            FROM hotel_tblfitrate fr
            INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
            LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
            WHERE fr.reservationID = %s
            AND fr.is_active = 1
        """, (reservation_id,))
        
        fit_rates_data = cursor.fetchall()
        
        # Format fit rates data
        fit_rates = []
        for fr in fit_rates_data:
            fit_rate_item = {
                "quantity": fr['quantity'],
                "rateID": {
                    "rate": str(fr['room_rate']),
                    "room_type": fr['rate_room_type'],
                    "room_name": fr['room_name'],
                    "currency": fr['rate_currency']
                }
            }
            
            if fr['mealID']:
                fit_rate_item["mealID"] = {
                    "mp": fr['mp'],
                    "rate": str(fr['meal_rate'])
                }
            
            fit_rates.append(fit_rate_item)

        # Construct the response
        response = {
            "rooms": rooms,
            "GuestReservation_ID": {
                "id": reservation_data['guest_reservation_id'],
                "start_date": reservation_data['start_date'].strftime('%Y-%m-%d') if reservation_data['start_date'] else None,
                "end_date": reservation_data['end_date'].strftime('%Y-%m-%d') if reservation_data['end_date'] else None,
                "No_of_children": reservation_data['No_of_children'],
                "No_of_adults": reservation_data['No_of_adults'],
                "Likes": reservation_data['Likes'],
                "Dislikes": reservation_data['Dislikes'],
                "Guest_Notes": reservation_data['Guest_Notes'],
                "Reservation_ID": {
                    "id": reservation_data['id'],
                    "Guest_ID": {
                        "id": reservation_data['Guest_ID'],
                        "name": reservation_data['guest_name'],
                        "address": reservation_data['guest_address'],
                        "tax_number": reservation_data['guest_tax_number']
                    },
                    "Current_Status": reservation_data['Current_Status'],
                    "outlet": reservation_data['outlet']
                },
                "Fit_rate": fit_rates
            }
        }

        mydb.close()
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

from datetime import datetime, date

@app_file402.route("/frontoffice/opening_reservations", methods=["GET"])
@cross_origin()
def opening_reservations():
    mydb = None
    try:
        # -------- TOKEN (header) --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(parts[1]):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        outlet = request.args.get("outlet")  # hotel property name (matches hotel_tblreservation.outlet)
        date_param = request.args.get("date")  # optional, defaults to today
        include_details = request.args.get("details", "false").lower() == "true"

        if not outlet:
            return {"error": "outlet is required"}, 400

        if date_param:
            try:
                biz_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
        else:
            biz_date = date.today()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- VALIDATE PROPERTY --------
        cursor.execute("SELECT id FROM hotel_company_property WHERE name = %s", (outlet,))
        if not cursor.fetchone():
            return {"error": "Property not found"}, 404

        # -------- RESERVED + REGISTERED BOOKED BEFORE THE BUSINESS DATE --------
        # One row per reservation (guest rows collapsed with MIN/MAX) so room
        # counts are never multiplied by the number of guest rows.
        cursor.execute("""
            SELECT
                r.id AS reservation_id,
                r.Current_Status AS status,
                MIN(gr.start_date) AS start_date,
                MAX(gr.end_date)   AS end_date,
                (SELECT COALESCE(SUM(fr.quantity), 0)
                   FROM hotel_tblfitrate fr
                  WHERE fr.reservationID = r.id AND fr.is_active = 1) AS rooms
            FROM hotel_tblreservation r
            JOIN hotel_tblguestreservation gr
              ON gr.Reservation_ID = r.id AND gr.is_active = 1
            WHERE r.is_active = 1
              AND r.outlet = %s
              AND r.Current_Status IN ('Reserved', 'Registered')
              AND r.Reservation_Date < %s
            GROUP BY r.id, r.Current_Status
            ORDER BY start_date, r.id
        """, (outlet, biz_date))
        rows = cursor.fetchall()

        # -------- CLASSIFY --------
        awaiting_res = awaiting_rooms = 0
        inhouse_res = inhouse_rooms = 0
        noshow_res = noshow_rooms = 0
        details = []

        for row in rows:
            status = row["status"]
            start_date = row["start_date"]
            end_date = row["end_date"]
            rooms = int(row["rooms"] or 0) or 1  # a reservation always holds at least one room

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if status == "Reserved":
                if start_date >= biz_date:
                    bucket = "awaiting_arrival"
                    awaiting_res += 1
                    awaiting_rooms += rooms
                else:
                    # arrival date passed, guest never registered -> no-show, not opening
                    noshow_res += 1
                    noshow_rooms += rooms
                    continue
            else:  # Registered
                if end_date < biz_date:
                    continue  # already due out before the business date
                if start_date >= biz_date:
                    bucket = "awaiting_arrival"  # registered early on the arrival day
                    awaiting_res += 1
                    awaiting_rooms += rooms
                else:
                    bucket = "in_house_carryover"
                    inhouse_res += 1
                    inhouse_rooms += rooms

            if include_details:
                details.append({
                    "reservation_id": row["reservation_id"],
                    "status": status,
                    "bucket": bucket,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "rooms": rooms
                })

        response = {
            "outlet": outlet,
            "business_date": biz_date.strftime("%Y-%m-%d"),
            "opening_reservations": awaiting_res + inhouse_res,
            "opening_rooms": awaiting_rooms + inhouse_rooms,
            "awaiting_arrival": {"reservations": awaiting_res, "rooms": awaiting_rooms},
            "in_house_carryover": {"reservations": inhouse_res, "rooms": inhouse_rooms},
            "no_show_excluded": {"reservations": noshow_res, "rooms": noshow_rooms}
        }

        if biz_date != date.today():
            response["note"] = ("Figures use current reservation statuses, so they are only "
                                "exact for today. For past dates use a close-time snapshot.")

        if include_details:
            response["reservations"] = details

        return jsonify(response), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()

    

@app_file402.route("/delete-reservation/<int:reservation_id>", methods=["DELETE"])
@cross_origin()
def delete_reservation(reservation_id):
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # lock the reservation so nothing else changes it mid-delete
        cursor.execute("""
            SELECT id, Current_Status, Advance_Payment
            FROM hotel_tblreservation
            WHERE id=%s FOR UPDATE
        """, (reservation_id,))
        res = cursor.fetchone()
        if not res:
            mydb.rollback()
            return {"error": f"Reservation {reservation_id} not found."}, 404

        # billed reservations can't be deleted
        # NOTE: adjust table/column to however your bills reference the reservation
        cursor.execute("SELECT COUNT(*) AS n FROM hotel_tblhotelbills WHERE ReservationID=%s", (reservation_id,))
        if cursor.fetchone()["n"] > 0:
            mydb.rollback()
            return {"error": "Billed reservations cannot be deleted."}, 400

        # in-house guests have no cascade, so remove them first
        cursor.execute("DELETE FROM hotel_tblinhouse_guests WHERE reservation_id=%s", (reservation_id,))
        guests_deleted = cursor.rowcount

        # cascades: hotel_tblguestreservation, hotel_tblreservation_details, hotel_tblfitrate
        cursor.execute("DELETE FROM hotel_tblreservation WHERE id=%s", (reservation_id,))

        mydb.commit()
        return {
            "message": f"Reservation {reservation_id} deleted.",
            "reservation_id": reservation_id,
            "Current_Status": res["Current_Status"],
            "in_house_guests_deleted": guests_deleted
        }, 200

    except mysql.connector.errors.IntegrityError as e:
        # some other table still points at this reservation
        if mydb:
            mydb.rollback()
        return {"error": "Reservation is referenced by other records and cannot be deleted.",
                "detail": str(e)}, 409

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()

# @app_file402.route("/registered_reservations", methods=["GET"])
# @cross_origin()
# def registered_reservations():
#     mydb = None
#     cursor = None
#     try:
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 401

#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 401

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 401

#         # Optional search: matches room number, guest name or guest phone
#         q = (request.args.get("q") or "").strip()

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         sql = """
#             SELECT res.id AS reservation_id, res.Current_Status, res.Check_In,
#                    c.id AS guest_id, c.name AS guest_name, c.phone AS guest_phone,
#                    comp.company_name,
#                    gr.start_date, gr.end_date, gr.No_of_adults, gr.No_of_children,
#                    r.id AS room_id, r.room_no, r.room_type, r.outlet AS room_outlet
#             FROM hotel_tblreservation res
#             INNER JOIN hotel_tblreservation_details rd ON rd.Reservation_ID = res.id
#             INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#             INNER JOIN customers c ON res.Guest_ID = c.id
#             LEFT JOIN hotel_tblguestreservation gr
#                    ON gr.Reservation_ID = res.id AND gr.is_active = 1
#             LEFT JOIN companies comp ON res.company_id = comp.id
#             WHERE res.Current_Status = 'Registered'
#             AND res.is_active = 1
#             AND rd.is_current = TRUE
#             AND rd.is_active = 1
#             AND r.is_active = 1
#         """
#         params = []

#         if q:
#             sql += " AND (r.room_no LIKE %s OR c.name LIKE %s OR c.phone LIKE %s)"
#             like = f"%{q}%"
#             params.extend([like, like, like])

#         sql += " ORDER BY r.room_no, res.id"

#         cursor.execute(sql, tuple(params))
#         rows = cursor.fetchall()
#         # Dedupe on room_id in case the guest-reservation join returns extra rows.
#         rooms = []
#         seen_rooms = set()
#         for row in rows:
#             if row["room_id"] in seen_rooms:
#                 continue
#             seen_rooms.add(row["room_id"])
#             rooms.append({
#                 "room_id": row["room_id"],
#                 "room_no": str(row["room_no"]),
#                 "room_type": row["room_type"],
#                 "outlet": row["room_outlet"],
#                 "reservation_id": row["reservation_id"],
#                 "status": row["Current_Status"],
#                 "check_in": str(row["Check_In"]) if row["Check_In"] else None,
#                 "guest_id": row["guest_id"],
#                 "guest_name": row["guest_name"],
#                 "guest_phone": row["guest_phone"],
#                 "company_name": row["company_name"],
#                 "start_date": row["start_date"].strftime("%Y-%m-%d") if row["start_date"] else None,
#                 "end_date": row["end_date"].strftime("%Y-%m-%d") if row["end_date"] else None
#             })

#         return jsonify({"count": len(rooms), "rooms": rooms}), 200

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


    
@app_file402.route("/registered_reservations", methods=["GET"])
@cross_origin()
def registered_reservations():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 401

        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 401

        if not token_auth(token):
            return {"error": "Invalid token."}, 401

        # Optional search: matches room number, guest name or guest phone
        q = (request.args.get("q") or "").strip()

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        sql = """
            SELECT res.id AS reservation_id, res.Check_In,
                   c.id AS guest_id, c.name AS guest_name, c.phone AS guest_phone,
                   comp.company_name,
                   gr.start_date, gr.end_date, gr.No_of_adults, gr.No_of_children,
                   r.id AS room_id, r.room_no, r.room_type, r.outlet AS room_outlet
            FROM hotel_tblreservation res
            INNER JOIN hotel_tblreservation_details rd ON rd.Reservation_ID = res.id
            INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
            INNER JOIN customers c ON res.Guest_ID = c.id
            LEFT JOIN hotel_tblguestreservation gr
                   ON gr.Reservation_ID = res.id AND gr.is_active = 1
            LEFT JOIN companies comp ON res.company_id = comp.id
            WHERE res.Current_Status = 'Registered'
            AND res.is_active = 1
            AND rd.is_current = TRUE
            AND rd.is_active = 1
            AND r.is_active = 1
        """
        params = []

        if q:
            sql += " AND (r.room_no LIKE %s OR c.name LIKE %s OR c.phone LIKE %s)"
            like = f"%{q}%"
            params.extend([like, like, like])

        sql += " ORDER BY r.room_no, res.id"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        # -------- Meal plan (from fit rate) for these reservations --------
        reservation_ids = list({row["reservation_id"] for row in rows})
        meal_plan_map = {}
        if reservation_ids:
            placeholders = ",".join(["%s"] * len(reservation_ids))
            cursor.execute(f"""
                SELECT fr.reservationID, mp.mp AS meal_plan
                FROM hotel_tblfitrate fr
                INNER JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
                WHERE fr.reservationID IN ({placeholders})
                AND fr.is_active = 1
                ORDER BY fr.id
            """, tuple(reservation_ids))

            for fr in cursor.fetchall():
                plans = meal_plan_map.setdefault(fr["reservationID"], [])
                if fr["meal_plan"] and fr["meal_plan"] not in plans:
                    plans.append(fr["meal_plan"])

        # -------- One entry per room --------
        # Dedupe on room_id in case the guest-reservation join returns extra rows.
        rooms = []
        seen_rooms = set()
        for row in rows:
            if row["room_id"] in seen_rooms:
                continue
            seen_rooms.add(row["room_id"])

            adults = row["No_of_adults"] or 0
            children = row["No_of_children"] or 0
            plans = meal_plan_map.get(row["reservation_id"], [])

            rooms.append({
                "room_id": row["room_id"],
                "room_no": str(row["room_no"]),
                "room_type": row["room_type"],
                "outlet": row["room_outlet"],
                "reservation_id": row["reservation_id"],
                "check_in": str(row["Check_In"]) if row["Check_In"] else None,
                "guest_id": row["guest_id"],
                "guest_name": row["guest_name"],
                "guest_phone": row["guest_phone"],
                "company_name": row["company_name"],
                "start_date": row["start_date"].strftime("%Y-%m-%d") if row["start_date"] else None,
                "end_date": row["end_date"].strftime("%Y-%m-%d") if row["end_date"] else None,
                "no_of_pax": adults + children,
                "meal_plan": ", ".join(plans) if plans else None,
            })

        return jsonify({"count": len(rooms), "rooms": rooms}), 200

    except Exception as e:
        print(f"registered_reservations error: {e}")
        return jsonify({"error": "Failed to fetch registered reservations"}), 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()

