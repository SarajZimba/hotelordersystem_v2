# """
# POST /express-checkin  (put it in app_file402 next to /create-reservation)
 
# One call, one transaction: create the reservation, guest reservation and FIT rates,
# then check the rooms in and save the in-house guests (with meal + rate snapshots).
# Nothing is saved unless everything succeeds.
 
# Payload:
# {
#   "tblReservation": {
#       "outlet": "Thamel Hotel", "Emp_ID": 1, "Pay_Mode": "...", "Market_Seg": "...",
#       "business_Src": "Walk-in", "Advance_Payment": 1000, "Advance_Payment_Currency": "NPR",
#       "Advance_Payment_Local": 1000,
#       "Guest_ID": 15,              # existing customer ... or send "guest" below
#       "company_id": null
#   },
#   "guest": {"name": "Ram", "phone": "...", "country": "..."},   # optional, creates the customer
#   "tblGuestReservation": {"No_of_adults": 2, "No_of_children": 0, "start_date": "2026-10-15",
#                           "end_date": "2026-10-17"},
#   "tblFITRate": [{"rateID": 7, "mealID": 3, "quantity": 2}],
#   "rooms": [
#       {"room_no": 5, "meal_id": 3, "rate_id": 7,
#        "guests": [{"name": "Ram", "is_primary": true, "identity_type": "Passport",
#                    "identity_no": "X1", "nationality": "Nepal"},
#                   {"name": "Sita"}]}
#   ]
# }
# """
 
# # ---------------------------------------------------------------------------
# # Shared helpers (create_reservation can call these too, so the logic lives once)
# # ---------------------------------------------------------------------------
# from decimal import Decimal, InvalidOperation

# def _to_int_or_none(value):
#     """None or '' -> None, otherwise int. Raises ValueError if not a number."""
#     if value in (None, ""):
#         return None
#     return int(value)
 
 
# def _normalize_advance(reservation_data):
#     """
#     Validates Advance_Payment / currency / local amount and writes the cleaned
#     values back into reservation_data. Returns an error string, or None if fine.
#     """
#     raw_advance = reservation_data.get("Advance_Payment")
#     if raw_advance in (None, ""):
#         amount = None
#     else:
#         try:
#             amount = Decimal(str(raw_advance))
#         except InvalidOperation:
#             return "Advance_Payment must be a number."
#         if amount < 0:
#             return "Advance_Payment cannot be negative."
 
#     currency = (reservation_data.get("Advance_Payment_Currency") or "").strip().upper() or None
#     if amount and not currency:
#         currency = "NPR"
#     if not amount:
#         currency = None
 
#     raw_local = reservation_data.get("Advance_Payment_Local")
#     if raw_local in (None, ""):
#         local = None
#     else:
#         try:
#             local = Decimal(str(raw_local))
#         except InvalidOperation:
#             return "Advance_Payment_Local must be a number."
#         if local < 0:
#             return "Advance_Payment_Local cannot be negative."
 
#     if not amount:
#         local = None
#     elif local is None:
#         return "Advance_Payment_Local is required when Advance_Payment is sent."
 
#     reservation_data["Advance_Payment"] = amount
#     reservation_data["Advance_Payment_Currency"] = currency
#     reservation_data["Advance_Payment_Local"] = local
#     return None
 
 
# def _fetch_by_ids(cursor, select_sql, ids):
#     """select_sql must end with a WHERE clause, e.g. '... WHERE is_active = 1'."""
#     if not ids:
#         return {}
#     placeholders = ",".join(["%s"] * len(ids))
#     cursor.execute(f"{select_sql} AND id IN ({placeholders})", list(ids))
#     return {r["id"]: r for r in cursor.fetchall()}
 
 
# RESERVATION_FIELDS = (
#     "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
#     "Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local",
#     "Guest_ID", "company_id",
#     "Reservation_Date", "Market_Seg", "business_Src",
#     "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id",
# )
 
 
# def _insert_reservation(cursor, reservation_data, now):
#     values = []
#     for field in RESERVATION_FIELDS:
#         value = reservation_data.get(field)
#         if field == "Reservation_Date":
#             value = value or now.date()
#         elif field == "Check_In":
#             value = value or now
#         values.append(value)
 
#     placeholders = ", ".join(["%s"] * len(RESERVATION_FIELDS))
#     cursor.execute(
#         f"INSERT INTO hotel_tblreservation ({', '.join(RESERVATION_FIELDS)}) "
#         f"VALUES ({placeholders})",
#         tuple(values),
#     )
#     return cursor.lastrowid
 
 
# def _insert_guest_reservation(cursor, reservation_id, data):
#     cursor.execute("""
#         INSERT INTO hotel_tblguestreservation
#             (Reservation_ID, No_of_children, No_of_adults, Likes, Dislikes,
#              Guest_Notes, start_date, end_date)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#     """, (
#         reservation_id,
#         data.get("No_of_children"),
#         data.get("No_of_adults"),
#         data.get("Likes"),
#         data.get("Dislikes"),
#         data.get("Guest_Notes"),
#         data.get("start_date"),
#         data.get("end_date"),
#     ))
 
 
# def _insert_fitrates(cursor, reservation_id, fit_items):
#     """
#     New reservation = no existing rows, so no SELECT per item. Duplicate
#     (rateID, mealID) lines in the payload are merged in Python, then one executemany.
#     """
#     merged = {}
#     for item in fit_items:
#         rate_id = item.get("rateID")
#         if rate_id is None:
#             raise ValueError("Each tblFITRate item needs 'rateID'.")
#         key = (rate_id, item.get("mealID"))
#         merged[key] = merged.get(key, 0) + (item.get("quantity") or 0)
 
#     cursor.executemany("""
#         INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
#         VALUES (%s, %s, %s, %s, 1)
#     """, [(r, m, reservation_id, q) for (r, m), q in merged.items()])
 
 
# def _insert_inhouse_guests(cursor, reservation_id, room_id, guests, meal_info, rate_info, now):
#     rows = []
#     for g in guests:
#         meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
#         rate = rate_info.get(g["rate_id"]) if g["rate_id"] is not None else None
#         rows.append((
#             reservation_id, room_id, g["name"].strip(),
#             g.get("identity_type"), g.get("identity_no"), g.get("nationality"),
#             1 if g.get("is_primary") else 0,
#             g["meal_id"],
#             meal["mp"] if meal else None,
#             meal["rate"] if meal else None,
#             meal["currency"] if meal else None,
#             g["rate_id"],
#             rate["room_name"] if rate else None,
#             rate["rate"] if rate else None,
#             rate["currency"] if rate else None,
#             now,
#         ))
#     cursor.executemany("""
#         INSERT INTO hotel_tblinhouse_guests
#             (reservation_id, room_id, name, identity_type, identity_no, nationality,
#              is_primary, meal_id, meal_mp, meal_rate, meal_currency,
#              rate_id, rate_name, rate_amount, rate_currency,
#              is_active, checked_in_at)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
#     """, rows)
#     return len(rows)
 
# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()
# from root.auth.check import token_auth
# from root.flask_routes.hotel.updateguestreservation import CompanyUpdate, CustomerUpdate

# app_file499 = Blueprint('app_file499', __name__)
# # ---------------------------------------------------------------------------
# # Endpoint
# # ---------------------------------------------------------------------------
 
# # @app_file499.route("/express-checkin", methods=["POST"])
# @app_file499.route("/express-checkin", methods=["POST"])
# @cross_origin()
# def express_checkin():
#     # -------- TOKEN --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token or not token_auth(token):
#         return {"error": "Invalid token."}, 400
 
#     # -------- PAYLOAD VALIDATION (no DB work yet) --------
#     json_data = request.get_json() or {}
#     reservation_data = json_data.get("tblReservation") or {}
#     guest_reservation_data = json_data.get("tblGuestReservation") or {}
#     fit_rate_data = json_data.get("tblFITRate") or []
#     new_guest_data = json_data.get("guest") or {}
#     rooms = json_data.get("rooms") or []
 
#     if not reservation_data:
#         return {"error": "Missing 'tblReservation' data"}, 400
#     if not guest_reservation_data:
#         return {"error": "Missing 'tblGuestReservation' data"}, 400
#     if not fit_rate_data:
#         return {"error": "Missing 'tblFITRate' data"}, 400
#     if not isinstance(rooms, list) or not rooms:
#         return {"error": "Expected a non-empty list 'rooms'."}, 400
 
#     new_company_data = json_data.get("company")
#     if new_company_data is not None and not isinstance(new_company_data, dict):
#         return {"error": "'company' must be an object."}, 400
 
#     if not (reservation_data.get("Guest_ID") or reservation_data.get("company_id")
#             or new_guest_data or new_company_data):
#         return {"error": "Send Guest_ID, company_id, a 'guest' object or a 'company' object."}, 400
#     if new_guest_data and not (new_guest_data.get("name") or "").strip():
#         return {"error": "'guest' needs a name."}, 400
 
#     advance_error = _normalize_advance(reservation_data)
#     if advance_error:
#         return {"error": advance_error}, 400
 
#     seen_rooms = set()
#     primaries = 0
#     for item in rooms:
#         room_ref = item.get("room_no")
#         if not room_ref:
#             return {"error": "Each room needs 'room_no'."}, 400
#         if room_ref in seen_rooms:
#             return {"error": f"Room {room_ref} appears more than once."}, 400
#         seen_rooms.add(room_ref)
 
#         guests = item.get("guests")
#         if not isinstance(guests, list) or not guests:
#             return {"error": f"At least one guest is required for room {room_ref}."}, 400
#         for g in guests:
#             if not (g.get("name") or "").strip():
#                 return {"error": f"Every guest needs a name (room {room_ref})."}, 400
 
#         try:
#             room_meal = _to_int_or_none(item.get("meal_id"))
#             room_rate = _to_int_or_none(item.get("rate_id"))
#             for g in guests:
#                 gm = _to_int_or_none(g.get("meal_id"))
#                 gr = _to_int_or_none(g.get("rate_id"))
#                 g["meal_id"] = gm if gm is not None else room_meal
#                 g["rate_id"] = gr if gr is not None else room_rate
#         except (TypeError, ValueError):
#             return {"error": f"meal_id and rate_id must be numbers (room {room_ref})."}, 400
 
#         primaries += sum(1 for g in guests if g.get("is_primary"))
 
#     # one primary guest per reservation, across all rooms
#     if primaries != 1:
#         return {"error": f"Exactly one primary guest is needed across all rooms (received {primaries})."}, 400
 
#     # -------- DB (single transaction) --------
#     mydb = None
#     cursor = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         now = datetime.now()
 
#         # ---- rooms: lock them, make sure they exist and are free ----
#         room_ids = [r["room_no"] for r in rooms]
#         ph = ",".join(["%s"] * len(room_ids))
 
#         # FOR UPDATE makes two simultaneous walk-ins queue up instead of
#         # both taking the same room.
#         cursor.execute(f"SELECT id FROM hotel_tblrooms WHERE id IN ({ph}) FOR UPDATE", room_ids)
#         found = {r["id"] for r in cursor.fetchall()}
#         missing = sorted(set(room_ids) - found)
#         if missing:
#             mydb.rollback()
#             return {"error": f"Room(s) not found: {missing}."}, 404
 
#         cursor.execute(f"""
#             SELECT DISTINCT d.room_id
#             FROM hotel_tblreservation_details d
#             JOIN hotel_tblreservation r ON r.id = d.Reservation_ID
#             WHERE d.is_current = 1 AND d.is_active = 1
#               AND r.Current_Status = 'Registered'
#               AND d.room_id IN ({ph})
#         """, room_ids)
#         occupied = sorted(r["room_id"] for r in cursor.fetchall())
#         if occupied:
#             mydb.rollback()
#             return {"error": f"Room(s) already occupied: {occupied}."}, 400
 
#         # ---- meal + rate lookups: one query each for the whole request ----
#         meal_ids = {g["meal_id"] for r in rooms for g in r["guests"] if g["meal_id"] is not None}
#         rate_ids = {g["rate_id"] for r in rooms for g in r["guests"] if g["rate_id"] is not None}
 
#         meal_info = _fetch_by_ids(
#             cursor,
#             "SELECT id, mp, rate, currency FROM hotel_tblmeal_price WHERE is_active = 1",
#             meal_ids,
#         )
#         if meal_ids - set(meal_info):
#             mydb.rollback()
#             return {"error": f"Meal plan(s) not found or inactive: {sorted(meal_ids - set(meal_info))}."}, 400
 
#         rate_info = _fetch_by_ids(
#             cursor,
#             "SELECT id, room_name, rate, currency FROM hotel_tblrates WHERE is_active = 1",
#             rate_ids,
#         )
#         if rate_ids - set(rate_info):
#             mydb.rollback()
#             return {"error": f"Rate(s) not found or inactive: {sorted(rate_ids - set(rate_info))}."}, 400
 
#         # ---- booker: existing customer, or create one ----
#         if reservation_data.get("company_id"):
#             cursor.execute("SELECT id FROM companies WHERE id = %s", (reservation_data["company_id"],))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": "Invalid company_id"}, 400
#         elif new_company_data:
#             # creates the company (needs company_name + phone, phone must be unique),
#             # or links an existing one when {"new_id": ...} is sent
#             new_company_data.setdefault("outlet", reservation_data.get("outlet"))
#             reservation_data["company_id"] = CompanyUpdate.resolve(cursor, new_company_data)
 
#         if reservation_data.get("Guest_ID"):
#             cursor.execute("SELECT id FROM customers WHERE id = %s", (reservation_data["Guest_ID"],))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": "Invalid guest_id"}, 400
#         elif new_guest_data:
#             reservation_data["Guest_ID"] = CustomerUpdate.update_or_create(cursor, new_guest_data)
 
#         # ---- reservation: Registered + Check_In = now ----
#         reservation_data["Current_Status"] = "Registered"
#         reservation_data["Check_In"] = now
#         reservation_id = _insert_reservation(cursor, reservation_data, now)
 
#         guest_reservation_data.setdefault("start_date", now.date())
#         _insert_guest_reservation(cursor, reservation_id, guest_reservation_data)
#         _insert_fitrates(cursor, reservation_id, fit_rate_data)
 
#         # ---- check the rooms in ----
#         cursor.executemany("""
#             INSERT INTO hotel_tblreservation_details
#                 (Reservation_ID, room_id, is_current, created_at, is_active)
#             VALUES (%s, %s, 1, %s, 1)
#         """, [(reservation_id, rid, now) for rid in room_ids])
 
#         cursor.execute(
#             f"UPDATE hotel_tblrooms SET room_state='Check-In' WHERE id IN ({ph})", room_ids
#         )
 
#         checked_in = []
#         for item in rooms:
#             saved = _insert_inhouse_guests(
#                 cursor, reservation_id, item["room_no"], item["guests"],
#                 meal_info, rate_info, now,
#             )
#             checked_in.append({"room_id": item["room_no"], "guests_saved": saved})
 
#         mydb.commit()
 
#         return jsonify({
#             "message": f"Checked in. Reservation ID is {reservation_id}",
#             "reservation_id": reservation_id,
#             "Guest_ID": reservation_data.get("Guest_ID"),
#             "company_id": reservation_data.get("company_id"),
#             "Current_Status": "Registered",
#             "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#             "rooms": checked_in,
#         }), 201
 
#     except ValueError as ve:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(ve)}, 400
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400
#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()



"""
POST /express-checkin

One call, one transaction: create the reservation, guest reservation and FIT rates,
then check the rooms in and save the in-house guests (with meal + rate snapshots).
Nothing is saved unless everything succeeds.

Payload:
{
  "tblReservation": {
      "outlet": "Thamel Hotel", "Emp_ID": 1, "Pay_Mode": "...", "Market_Seg": "...",
      "business_Src": "Walk-in", "Advance_Payment": 1000, "Advance_Payment_Currency": "NPR",
      "Advance_Payment_Local": 1000,
      "is_complimentary": false,   # optional, default false; default for every in-house guest
      "Guest_ID": 15,              # existing customer ... or send "guest" below
      "company_id": null
  },
  "guest": {"name": "Ram", "phone": "...", "country": "..."},   # optional, creates the customer
  "tblGuestReservation": {"No_of_adults": 2, "No_of_children": 0, "start_date": "2026-10-15",
                          "end_date": "2026-10-17"},
  "tblFITRate": [{"rateID": 7, "mealID": 3, "quantity": 2}],
  "rooms": [
      {"room_no": 5, "meal_id": 3, "rate_id": 7,
       "is_complimentary": true,    # optional, applies to every guest in this room
       "guests": [{"name": "Ram", "is_primary": true, "identity_type": "Passport",
                   "identity_no": "X1", "nationality": "Nepal"},
                  {"name": "Sita", "is_complimentary": false}]}   # guest level overrides room level
  ]
}

is_complimentary on an in-house guest: guest flag > room flag > reservation flag.
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime
import os

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
from root.auth.check import token_auth
from root.flask_routes.hotel.updateguestreservation import CompanyUpdate, CustomerUpdate

app_file499 = Blueprint('app_file499', __name__)


# ---------------------------------------------------------------------------
# Shared helpers (create_reservation can call these too, so the logic lives once)
# ---------------------------------------------------------------------------
def _to_int_or_none(value):
    """None or '' -> None, otherwise int. Raises ValueError if not a number."""
    if value in (None, ""):
        return None
    return int(value)


def _parse_bool_flag(value, default=False):
    """None or '' -> default. Raises ValueError if the value is not a boolean-like."""
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


def _normalize_advance(reservation_data):
    """
    Validates Advance_Payment / currency / local amount and writes the cleaned
    values back into reservation_data. Returns an error string, or None if fine.
    """
    raw_advance = reservation_data.get("Advance_Payment")
    if raw_advance in (None, ""):
        amount = None
    else:
        try:
            amount = Decimal(str(raw_advance))
        except InvalidOperation:
            return "Advance_Payment must be a number."
        if amount < 0:
            return "Advance_Payment cannot be negative."

    currency = (reservation_data.get("Advance_Payment_Currency") or "").strip().upper() or None
    if amount and not currency:
        currency = "NPR"
    if not amount:
        currency = None

    raw_local = reservation_data.get("Advance_Payment_Local")
    if raw_local in (None, ""):
        local = None
    else:
        try:
            local = Decimal(str(raw_local))
        except InvalidOperation:
            return "Advance_Payment_Local must be a number."
        if local < 0:
            return "Advance_Payment_Local cannot be negative."

    if not amount:
        local = None
    elif local is None:
        return "Advance_Payment_Local is required when Advance_Payment is sent."

    reservation_data["Advance_Payment"] = amount
    reservation_data["Advance_Payment_Currency"] = currency
    reservation_data["Advance_Payment_Local"] = local
    return None


def _fetch_by_ids(cursor, select_sql, ids):
    """select_sql must end with a WHERE clause, e.g. '... WHERE is_active = 1'."""
    if not ids:
        return {}
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(f"{select_sql} AND id IN ({placeholders})", list(ids))
    return {r["id"]: r for r in cursor.fetchall()}


RESERVATION_FIELDS = (
    "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
    "Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local",
    "Guest_ID", "company_id",
    "Reservation_Date", "Market_Seg", "business_Src",
    "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id",
    "is_complimentary",
)


def _insert_reservation(cursor, reservation_data, now):
    values = []
    for field in RESERVATION_FIELDS:
        value = reservation_data.get(field)
        if field == "Reservation_Date":
            value = value or now.date()
        elif field == "Check_In":
            value = value or now
        values.append(value)

    placeholders = ", ".join(["%s"] * len(RESERVATION_FIELDS))
    cursor.execute(
        f"INSERT INTO hotel_tblreservation ({', '.join(RESERVATION_FIELDS)}) "
        f"VALUES ({placeholders})",
        tuple(values),
    )
    return cursor.lastrowid


def _insert_guest_reservation(cursor, reservation_id, data):
    cursor.execute("""
        INSERT INTO hotel_tblguestreservation
            (Reservation_ID, No_of_children, No_of_adults, Likes, Dislikes,
             Guest_Notes, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        reservation_id,
        data.get("No_of_children"),
        data.get("No_of_adults"),
        data.get("Likes"),
        data.get("Dislikes"),
        data.get("Guest_Notes"),
        data.get("start_date"),
        data.get("end_date"),
    ))


def _insert_fitrates(cursor, reservation_id, fit_items):
    """
    New reservation = no existing rows, so no SELECT per item. Duplicate
    (rateID, mealID) lines in the payload are merged in Python, then one executemany.
    """
    merged = {}
    for item in fit_items:
        rate_id = item.get("rateID")
        if rate_id is None:
            raise ValueError("Each tblFITRate item needs 'rateID'.")
        key = (rate_id, item.get("mealID"))
        merged[key] = merged.get(key, 0) + (item.get("quantity") or 0)

    cursor.executemany("""
        INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
        VALUES (%s, %s, %s, %s, 1)
    """, [(r, m, reservation_id, q) for (r, m), q in merged.items()])


def _insert_inhouse_guests(cursor, reservation_id, room_id, guests, meal_info, rate_info, now):
    rows = []
    for g in guests:
        meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
        rate = rate_info.get(g["rate_id"]) if g["rate_id"] is not None else None
        rows.append((
            reservation_id, room_id, g["name"].strip(),
            g.get("identity_type"), g.get("identity_no"), g.get("nationality"),
            1 if g.get("is_primary") else 0,
            1 if g["is_complimentary"] else 0,
            g["meal_id"],
            meal["mp"] if meal else None,
            meal["rate"] if meal else None,
            meal["currency"] if meal else None,
            g["rate_id"],
            rate["room_name"] if rate else None,
            rate["rate"] if rate else None,
            rate["currency"] if rate else None,
            now,
        ))
    cursor.executemany("""
        INSERT INTO hotel_tblinhouse_guests
            (reservation_id, room_id, name, identity_type, identity_no, nationality,
             is_primary, is_complimentary, meal_id, meal_mp, meal_rate, meal_currency,
             rate_id, rate_name, rate_amount, rate_currency,
             is_active, checked_in_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
    """, rows)
    return len(rows)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@app_file499.route("/express-checkin", methods=["POST"])
@cross_origin()
def express_checkin():
    # -------- TOKEN --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token or not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- PAYLOAD VALIDATION (no DB work yet) --------
    json_data = request.get_json() or {}
    reservation_data = json_data.get("tblReservation") or {}
    guest_reservation_data = json_data.get("tblGuestReservation") or {}
    fit_rate_data = json_data.get("tblFITRate") or []
    new_guest_data = json_data.get("guest") or {}
    rooms = json_data.get("rooms") or []

    if not reservation_data:
        return {"error": "Missing 'tblReservation' data"}, 400
    if not guest_reservation_data:
        return {"error": "Missing 'tblGuestReservation' data"}, 400
    if not fit_rate_data:
        return {"error": "Missing 'tblFITRate' data"}, 400
    if not isinstance(rooms, list) or not rooms:
        return {"error": "Expected a non-empty list 'rooms'."}, 400

    new_company_data = json_data.get("company")
    if new_company_data is not None and not isinstance(new_company_data, dict):
        return {"error": "'company' must be an object."}, 400

    if not (reservation_data.get("Guest_ID") or reservation_data.get("company_id")
            or new_guest_data or new_company_data):
        return {"error": "Send Guest_ID, company_id, a 'guest' object or a 'company' object."}, 400
    if new_guest_data and not (new_guest_data.get("name") or "").strip():
        return {"error": "'guest' needs a name."}, 400

    advance_error = _normalize_advance(reservation_data)
    if advance_error:
        return {"error": advance_error}, 400

    # ---- is_complimentary (reservation level): from frontend, default false ----
    try:
        is_complimentary = _parse_bool_flag(reservation_data.get("is_complimentary"))
    except ValueError:
        return {"error": "is_complimentary must be true or false."}, 400
    reservation_data["is_complimentary"] = 1 if is_complimentary else 0

    seen_rooms = set()
    primaries = 0
    for item in rooms:
        room_ref = item.get("room_no")
        if not room_ref:
            return {"error": "Each room needs 'room_no'."}, 400
        if room_ref in seen_rooms:
            return {"error": f"Room {room_ref} appears more than once."}, 400
        seen_rooms.add(room_ref)

        guests = item.get("guests")
        if not isinstance(guests, list) or not guests:
            return {"error": f"At least one guest is required for room {room_ref}."}, 400
        for g in guests:
            if not (g.get("name") or "").strip():
                return {"error": f"Every guest needs a name (room {room_ref})."}, 400

        try:
            room_meal = _to_int_or_none(item.get("meal_id"))
            room_rate = _to_int_or_none(item.get("rate_id"))
            for g in guests:
                gm = _to_int_or_none(g.get("meal_id"))
                gr = _to_int_or_none(g.get("rate_id"))
                g["meal_id"] = gm if gm is not None else room_meal
                g["rate_id"] = gr if gr is not None else room_rate
        except (TypeError, ValueError):
            return {"error": f"meal_id and rate_id must be numbers (room {room_ref})."}, 400

        # is_complimentary: per guest overrides per room; if neither is sent,
        # the guest inherits the reservation's flag
        try:
            room_comp = _parse_bool_flag(item.get("is_complimentary"), default=None)
            for g in guests:
                g["is_complimentary"] = _parse_bool_flag(
                    g.get("is_complimentary"), default=room_comp
                )
        except ValueError:
            return {"error": f"is_complimentary must be true or false (room {room_ref})."}, 400

        for g in guests:
            if g["is_complimentary"] is None:
                g["is_complimentary"] = is_complimentary

        primaries += sum(1 for g in guests if g.get("is_primary"))

    # one primary guest per reservation, across all rooms
    if primaries != 1:
        return {"error": f"Exactly one primary guest is needed across all rooms (received {primaries})."}, 400

    # -------- DB (single transaction) --------
    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        now = datetime.now()

        # ---- rooms: lock them, make sure they exist and are free ----
        room_ids = [r["room_no"] for r in rooms]
        ph = ",".join(["%s"] * len(room_ids))

        # FOR UPDATE makes two simultaneous walk-ins queue up instead of
        # both taking the same room.
        cursor.execute(f"SELECT id FROM hotel_tblrooms WHERE id IN ({ph}) FOR UPDATE", room_ids)
        found = {r["id"] for r in cursor.fetchall()}
        missing = sorted(set(room_ids) - found)
        if missing:
            mydb.rollback()
            return {"error": f"Room(s) not found: {missing}."}, 404

        cursor.execute(f"""
            SELECT DISTINCT d.room_id
            FROM hotel_tblreservation_details d
            JOIN hotel_tblreservation r ON r.id = d.Reservation_ID
            WHERE d.is_current = 1 AND d.is_active = 1
              AND r.Current_Status = 'Registered'
              AND d.room_id IN ({ph})
        """, room_ids)
        occupied = sorted(r["room_id"] for r in cursor.fetchall())
        if occupied:
            mydb.rollback()
            return {"error": f"Room(s) already occupied: {occupied}."}, 400

        # ---- meal + rate lookups: one query each for the whole request ----
        meal_ids = {g["meal_id"] for r in rooms for g in r["guests"] if g["meal_id"] is not None}
        rate_ids = {g["rate_id"] for r in rooms for g in r["guests"] if g["rate_id"] is not None}

        meal_info = _fetch_by_ids(
            cursor,
            "SELECT id, mp, rate, currency FROM hotel_tblmeal_price WHERE is_active = 1",
            meal_ids,
        )
        if meal_ids - set(meal_info):
            mydb.rollback()
            return {"error": f"Meal plan(s) not found or inactive: {sorted(meal_ids - set(meal_info))}."}, 400

        rate_info = _fetch_by_ids(
            cursor,
            "SELECT id, room_name, rate, currency FROM hotel_tblrates WHERE is_active = 1",
            rate_ids,
        )
        if rate_ids - set(rate_info):
            mydb.rollback()
            return {"error": f"Rate(s) not found or inactive: {sorted(rate_ids - set(rate_info))}."}, 400

        # ---- booker: existing customer, or create one ----
        if reservation_data.get("company_id"):
            cursor.execute("SELECT id FROM companies WHERE id = %s", (reservation_data["company_id"],))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": "Invalid company_id"}, 400
        elif new_company_data:
            # creates the company (needs company_name + phone, phone must be unique),
            # or links an existing one when {"new_id": ...} is sent
            new_company_data.setdefault("outlet", reservation_data.get("outlet"))
            reservation_data["company_id"] = CompanyUpdate.resolve(cursor, new_company_data)

        if reservation_data.get("Guest_ID"):
            cursor.execute("SELECT id FROM customers WHERE id = %s", (reservation_data["Guest_ID"],))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": "Invalid guest_id"}, 400
        elif new_guest_data:
            reservation_data["Guest_ID"] = CustomerUpdate.update_or_create(cursor, new_guest_data)

        # ---- reservation: Registered + Check_In = now ----
        reservation_data["Current_Status"] = "Registered"
        reservation_data["Check_In"] = now
        reservation_id = _insert_reservation(cursor, reservation_data, now)

        guest_reservation_data.setdefault("start_date", now.date())
        _insert_guest_reservation(cursor, reservation_id, guest_reservation_data)
        _insert_fitrates(cursor, reservation_id, fit_rate_data)

        # ---- check the rooms in ----
        cursor.executemany("""
            INSERT INTO hotel_tblreservation_details
                (Reservation_ID, room_id, is_current, created_at, is_active)
            VALUES (%s, %s, 1, %s, 1)
        """, [(reservation_id, rid, now) for rid in room_ids])

        cursor.execute(
            f"UPDATE hotel_tblrooms SET room_state='Check-In' WHERE id IN ({ph})", room_ids
        )

        checked_in = []
        for item in rooms:
            saved = _insert_inhouse_guests(
                cursor, reservation_id, item["room_no"], item["guests"],
                meal_info, rate_info, now,
            )
            checked_in.append({
                "room_id": item["room_no"],
                "guests_saved": saved,
                "is_complimentary": any(g["is_complimentary"] for g in item["guests"]),
            })

        mydb.commit()

        return jsonify({
            "message": f"Checked in. Reservation ID is {reservation_id}",
            "reservation_id": reservation_id,
            "Guest_ID": reservation_data.get("Guest_ID"),
            "company_id": reservation_data.get("company_id"),
            "Current_Status": "Registered",
            "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
            "is_complimentary": bool(is_complimentary),
            "rooms": checked_in,
        }), 201

    except ValueError as ve:
        if mydb:
            mydb.rollback()
        return {"error": str(ve)}, 400
    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()