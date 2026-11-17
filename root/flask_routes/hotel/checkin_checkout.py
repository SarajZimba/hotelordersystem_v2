# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()
# from root.auth.check import token_auth

# app_file404 = Blueprint('app_file404', __name__)

# @app_file404.route("/GuestCheckIN", methods=["POST"])
# @cross_origin()
# def guest_checkin():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         checkin_list = json_data.get("checkin_list", [])

#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400

#         created_records = []

#         for item in checkin_list:
#             reservation_id = item.get("Reservation_ID")
#             room_id = item.get("room_no")

#             if not reservation_id or not room_id:
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

#             # Check for existing reservation detail
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             existing = cursor.fetchone()
#             if existing:
#                 return {"error": f"Reservation details already exist for Reservation_ID={reservation_id} and room_id={room_id}"}, 400

#             # Update reservation Current_Status and Check_In
#             now = datetime.now()
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room state
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))

#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))

#             created_records.append({
#                 "Reservation_ID": reservation_id,
#                 "room_id": room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S")
#             })

#         mydb.commit()
#         mydb.close()

#         return jsonify(created_records), 201

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file404.route("/GuestCheckIN-v2/", methods=["POST"])
# @cross_origin()
# def guest_checkin_v2():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         checkin_list = json_data.get("checkin_list", [])

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400

#         created_records = []

#         for item in checkin_list:
#             outlet_reservation_id = item.get("Reservation_ID")
#             outlet_room_id = item.get("room_id")

#             if not outlet_reservation_id or not outlet_room_id:
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

#             # Fetch internal reservation ID
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation
#                 WHERE reservation_outlet_id=%s
#             """, (outlet_reservation_id,))
#             reservation_row = cursor.fetchone()
#             if not reservation_row:
#                 return {"error": f"Reservation not found for outlet ID {outlet_reservation_id}"}, 404
#             reservation_id = reservation_row["id"]

#             # Fetch internal room ID
#             cursor.execute("""
#                 SELECT id FROM hotel_tblrooms
#                 WHERE outlet_room_id=%s
#             """, (outlet_room_id,))
#             room_row = cursor.fetchone()
#             if not room_row:
#                 return {"error": f"Room not found for outlet ID {outlet_room_id}"}, 404
#             room_id = room_row["id"]

#             # Check if reservation detail already exists
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             existing = cursor.fetchone()
#             if existing:
#                 return {"error": f"Reservation detail already exists for Reservation_ID={outlet_reservation_id} and room_id={outlet_room_id}"}, 400

#             now = datetime.now()

#             # Update reservation
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))

#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))

#             created_records.append({
#                 "Reservation_ID": outlet_reservation_id,
#                 "room_id": outlet_room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S")
#             })

#         mydb.commit()
#         mydb.close()

#         return jsonify(created_records), 201

#     except Exception as e:
#         return {"error": str(e)}, 400


# @app_file404.route("/GuestCheckOUT-v2", methods=["POST"])
# @cross_origin()
# def guest_checkout_v2():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         checkout_list = json_data.get("checkout_list", [])

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
#         if not isinstance(checkout_list, list) or not checkout_list:
#             return {"error": "Expected a non-empty list 'checkout_list'."}, 400

#         for item in checkout_list:
#             outlet_reservation_id = item.get("Reservation_ID")
#             outlet_room_id = item.get("room_id")

#             if not outlet_reservation_id or not outlet_room_id:
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

#             # Fetch internal reservation ID
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation
#                 WHERE reservation_outlet_id=%s
#             """, (outlet_reservation_id,))
#             reservation_row = cursor.fetchone()
#             if not reservation_row:
#                 return {"error": f"Reservation not found for outlet ID {outlet_reservation_id}"}, 404
#             reservation_id = reservation_row["id"]

#             # Fetch internal room ID
#             cursor.execute("""
#                 SELECT id FROM hotel_tblrooms
#                 WHERE outlet_room_id=%s
#             """, (outlet_room_id,))
#             room_row = cursor.fetchone()
#             if not room_row:
#                 return {"error": f"Room not found for outlet ID {outlet_room_id}"}, 404
#             room_id = room_row["id"]

#             now = datetime.now()

#             # Update reservation details
#             cursor.execute("""
#                 UPDATE hotel_tblreservation_details
#                 SET is_current=0
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))

#             # Update reservation
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Checked Out', Check_Out=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Vacant'
#                 WHERE id=%s
#             """, (room_id,))

#         mydb.commit()
#         mydb.close()

#         return jsonify({"message": "Reservations checked out successfully"}), 201

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file404.route("/GuestCheckOut", methods=["POST"])
# @cross_origin()
# def guest_checkout():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         checkout_list = json_data.get("checkout_list", [])

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
#         if not isinstance(checkout_list, list) or not checkout_list:
#             return {"error": "Expected a non-empty list 'checkout_list'."}, 400

#         for item in checkout_list:
#             reservation_id = item.get("Reservation_ID")
#             room_id = item.get("room_id")

#             if not reservation_id or not room_id:
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

#             now = datetime.now()

#             # Update reservation details
#             cursor.execute("""
#                 UPDATE hotel_tblreservation_details
#                 SET is_current=0
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))

#             # Update reservation
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Checked Out', Check_Out=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Vacant'
#                 WHERE id=%s
#             """, (room_id,))

#         mydb.commit()
#         mydb.close()

#         return jsonify({"message": "Reservations checked out successfully"}), 201

#     except Exception as e:
#         return {"error": str(e)}, 400


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
from root.auth.check import token_auth

app_file404 = Blueprint('app_file404', __name__)


# @app_file404.route("/GuestCheckIN", methods=["POST"])
# @cross_origin()
# def guest_checkin():
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

#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- PAYLOAD VALIDATION (before any DB work) --------
#         json_data = request.get_json() or {}
#         checkin_list = json_data.get("checkin_list", [])

#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400

#         primaries_by_reservation = {}   # reservation -> primary guests sent in this request

#         for item in checkin_list:
#             if not item.get("Reservation_ID") or not item.get("room_no"):
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_no'."}, 400

#             room_ref = item.get("room_no")
#             guests = item.get("guests")

#             if not isinstance(guests, list) or not guests:
#                 return {"error": f"At least one guest is required for room {room_ref}."}, 400

#             for g in guests:
#                 if not (g.get("name") or "").strip():
#                     return {"error": f"Every guest needs a name (room {room_ref})."}, 400

#             key = str(item["Reservation_ID"])
#             primaries_by_reservation[key] = (
#                 primaries_by_reservation.get(key, 0)
#                 + sum(1 for g in guests if g.get("is_primary"))
#             )

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- PRIMARY GUEST RULE: one per reservation --------
#         for res_key, primaries_in_request in primaries_by_reservation.items():
#             # lock the reservation so two simultaneous check-ins can't both add a primary
#             cursor.execute("SELECT id FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (res_key,))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": f"Reservation {res_key} not found."}, 404

#             cursor.execute("""
#                 SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
#                 WHERE reservation_id=%s AND is_primary=1 AND is_active=1
#             """, (res_key,))
#             existing_primary = cursor.fetchone()["n"]

#             if existing_primary == 0 and primaries_in_request != 1:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} needs exactly one primary guest "
#                              f"across all its rooms (received {primaries_in_request})."
#                 }, 400

#             if existing_primary > 0 and primaries_in_request > 0:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} already has a primary guest in-house. "
#                              f"Guests added to new rooms must not be primary."
#                 }, 400

#         created_records = []

#         for item in checkin_list:
#             reservation_id = item["Reservation_ID"]
#             room_id = item["room_no"]
#             guests = item["guests"]

#             # Check for existing reservation detail
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation details already exist for "
#                              f"Reservation_ID={reservation_id} and room_id={room_id}"
#                 }, 400

#             now = datetime.now()

#             # Update reservation Current_Status and Check_In
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room state
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))

#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))

#             # Insert in-house guests for this room
#             guest_rows = [
#                 (
#                     reservation_id,
#                     room_id,
#                     g["name"].strip(),
#                     g.get("identity_type"),
#                     g.get("identity_no"),
#                     g.get("nationality"),
#                     1 if g.get("is_primary") else 0,
#                     now,
#                 )
#                 for g in guests
#             ]
#             cursor.executemany("""
#                 INSERT INTO hotel_tblinhouse_guests
#                     (reservation_id, room_id, name, identity_type, identity_no,
#                      nationality, is_primary, is_active, checked_in_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
#             """, guest_rows)

#             created_records.append({
#                 "Reservation_ID": reservation_id,
#                 "room_id": room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#                 "guests_saved": len(guest_rows)
#             })

#         mydb.commit()
#         return jsonify(created_records), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


# def _parse_meal_id(value):
#     """None or '' -> None, otherwise int. Raises ValueError if not a number."""
#     if value in (None, ""):
#         return None
#     return int(value)

# @app_file404.route("/GuestCheckIN", methods=["POST"])
# @cross_origin()
# def guest_checkin():
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
 
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
 
#         # -------- PAYLOAD VALIDATION (before any DB work) --------
#         json_data = request.get_json() or {}
#         checkin_list = json_data.get("checkin_list", [])
 
#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400
 
#         primaries_by_reservation = {}   # reservation -> primary guests sent in this request
 
#         for item in checkin_list:
#             if not item.get("Reservation_ID") or not item.get("room_no"):
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_no'."}, 400
 
#             room_ref = item.get("room_no")
#             guests = item.get("guests")
 
#             if not isinstance(guests, list) or not guests:
#                 return {"error": f"At least one guest is required for room {room_ref}."}, 400
 
#             for g in guests:
#                 if not (g.get("name") or "").strip():
#                     return {"error": f"Every guest needs a name (room {room_ref})."}, 400
 
#             # meal_id can be sent per guest, or once per room as a default for its guests
#             try:
#                 room_meal = _parse_meal_id(item.get("meal_id"))
#                 for g in guests:
#                     guest_meal = _parse_meal_id(g.get("meal_id"))
#                     g["meal_id"] = guest_meal if guest_meal is not None else room_meal
#             except (TypeError, ValueError):
#                 return {"error": f"meal_id must be a number (room {room_ref})."}, 400
 
#             key = str(item["Reservation_ID"])
#             primaries_by_reservation[key] = (
#                 primaries_by_reservation.get(key, 0)
#                 + sum(1 for g in guests if g.get("is_primary"))
#             )
 
#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)
 
#         # -------- MEAL PLAN LOOKUP --------
#         # The name, rate and currency are read from the meal price table here and
#         # saved on each guest, so they stay as they were at check-in.
#         meal_ids = {
#             g["meal_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["meal_id"] is not None
#         }
#         meal_info = {}
#         if meal_ids:
#             placeholders = ",".join(["%s"] * len(meal_ids))
#             cursor.execute(
#                 f"SELECT id, mp, rate, currency FROM hotel_tblmeal_price "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(meal_ids),
#             )
#             meal_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(meal_ids - set(meal_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Meal plan(s) not found or inactive: {missing}."}, 400
 
#         # -------- PRIMARY GUEST RULE: one per reservation --------
#         for res_key, primaries_in_request in primaries_by_reservation.items():
#             # lock the reservation so two simultaneous check-ins can't both add a primary
#             cursor.execute("SELECT id FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (res_key,))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": f"Reservation {res_key} not found."}, 404
 
#             cursor.execute("""
#                 SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
#                 WHERE reservation_id=%s AND is_primary=1 AND is_active=1
#             """, (res_key,))
#             existing_primary = cursor.fetchone()["n"]
 
#             if existing_primary == 0 and primaries_in_request != 1:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} needs exactly one primary guest "
#                              f"across all its rooms (received {primaries_in_request})."
#                 }, 400
 
#             if existing_primary > 0 and primaries_in_request > 0:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} already has a primary guest in-house. "
#                              f"Guests added to new rooms must not be primary."
#                 }, 400
 
#         created_records = []
 
#         for item in checkin_list:
#             reservation_id = item["Reservation_ID"]
#             room_id = item["room_no"]
#             guests = item["guests"]
 
#             # Check for existing reservation detail
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation details already exist for "
#                              f"Reservation_ID={reservation_id} and room_id={room_id}"
#                 }, 400
 
#             now = datetime.now()
 
#             # Update reservation Current_Status and Check_In
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))
 
#             # Update room state
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))
 
#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))
 
#             # Insert in-house guests for this room (with their meal plan snapshot)
#             guest_rows = []
#             for g in guests:
#                 meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
#                 guest_rows.append((
#                     reservation_id,
#                     room_id,
#                     g["name"].strip(),
#                     g.get("identity_type"),
#                     g.get("identity_no"),
#                     g.get("nationality"),
#                     1 if g.get("is_primary") else 0,
#                     g["meal_id"],
#                     meal["mp"] if meal else None,
#                     meal["rate"] if meal else None,
#                     meal["currency"] if meal else None,
#                     now,
#                 ))
#             cursor.executemany("""
#                 INSERT INTO hotel_tblinhouse_guests
#                     (reservation_id, room_id, name, identity_type, identity_no,
#                      nationality, is_primary, meal_id, meal_mp, meal_rate, meal_currency,
#                      is_active, checked_in_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
#             """, guest_rows)
 
#             created_records.append({
#                 "Reservation_ID": reservation_id,
#                 "room_id": room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#                 "guests_saved": len(guest_rows)
#             })
 
#         mydb.commit()
#         return jsonify(created_records), 201
 
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400
 
#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


# def _parse_int_id(value):
#     """None or '' -> None, otherwise int. Raises ValueError if not a number."""
#     if value in (None, ""):
#         return None
#     return int(value)
 
 
# @app_file404.route("/GuestCheckIN", methods=["POST"])
# @cross_origin()
# def guest_checkin():
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
 
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
 
#         # -------- PAYLOAD VALIDATION (before any DB work) --------
#         json_data = request.get_json() or {}
#         checkin_list = json_data.get("checkin_list", [])
 
#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400
 
#         primaries_by_reservation = {}   # reservation -> primary guests sent in this request
 
#         for item in checkin_list:
#             if not item.get("Reservation_ID") or not item.get("room_no"):
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_no'."}, 400
 
#             room_ref = item.get("room_no")
#             guests = item.get("guests")
 
#             if not isinstance(guests, list) or not guests:
#                 return {"error": f"At least one guest is required for room {room_ref}."}, 400
 
#             for g in guests:
#                 if not (g.get("name") or "").strip():
#                     return {"error": f"Every guest needs a name (room {room_ref})."}, 400
 
#             # meal_id / rate_id can be sent per guest, or once per room as a default for its guests
#             try:
#                 room_meal = _parse_int_id(item.get("meal_id"))
#                 room_rate = _parse_int_id(item.get("rate_id"))
#                 for g in guests:
#                     guest_meal = _parse_int_id(g.get("meal_id"))
#                     g["meal_id"] = guest_meal if guest_meal is not None else room_meal
 
#                     guest_rate = _parse_int_id(g.get("rate_id"))
#                     g["rate_id"] = guest_rate if guest_rate is not None else room_rate
#             except (TypeError, ValueError):
#                 return {"error": f"meal_id and rate_id must be numbers (room {room_ref})."}, 400
 
#             key = str(item["Reservation_ID"])
#             primaries_by_reservation[key] = (
#                 primaries_by_reservation.get(key, 0)
#                 + sum(1 for g in guests if g.get("is_primary"))
#             )
 
#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)
 
#         # -------- MEAL PLAN LOOKUP --------
#         # The name, rate and currency are read from the meal price table here and
#         # saved on each guest, so they stay as they were at check-in.
#         meal_ids = {
#             g["meal_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["meal_id"] is not None
#         }
#         meal_info = {}
#         if meal_ids:
#             placeholders = ",".join(["%s"] * len(meal_ids))
#             cursor.execute(
#                 f"SELECT id, mp, rate, currency FROM hotel_tblmeal_price "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(meal_ids),
#             )
#             meal_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(meal_ids - set(meal_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Meal plan(s) not found or inactive: {missing}."}, 400
 
#         # -------- RATE LOOKUP --------
#         # Same idea as meals: the rate name, amount and currency are copied onto
#         # each guest at check-in so later edits to hotel_tblrates don't change them.
#         rate_ids = {
#             g["rate_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["rate_id"] is not None
#         }
#         rate_info = {}
#         if rate_ids:
#             placeholders = ",".join(["%s"] * len(rate_ids))
#             cursor.execute(
#                 f"SELECT id, room_name, rate, currency FROM hotel_tblrates "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(rate_ids),
#             )
#             rate_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(rate_ids - set(rate_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Rate(s) not found or inactive: {missing}."}, 400
 
#         # -------- PRIMARY GUEST RULE: one per reservation --------
#         for res_key, primaries_in_request in primaries_by_reservation.items():
#             # lock the reservation so two simultaneous check-ins can't both add a primary
#             cursor.execute("SELECT id FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (res_key,))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": f"Reservation {res_key} not found."}, 404
 
#             cursor.execute("""
#                 SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
#                 WHERE reservation_id=%s AND is_primary=1 AND is_active=1
#             """, (res_key,))
#             existing_primary = cursor.fetchone()["n"]
 
#             if existing_primary == 0 and primaries_in_request != 1:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} needs exactly one primary guest "
#                              f"across all its rooms (received {primaries_in_request})."
#                 }, 400
 
#             if existing_primary > 0 and primaries_in_request > 0:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} already has a primary guest in-house. "
#                              f"Guests added to new rooms must not be primary."
#                 }, 400
 
#         created_records = []
 
#         for item in checkin_list:
#             reservation_id = item["Reservation_ID"]
#             room_id = item["room_no"]
#             guests = item["guests"]
 
#             # Check for existing reservation detail
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation details already exist for "
#                              f"Reservation_ID={reservation_id} and room_id={room_id}"
#                 }, 400
 
#             now = datetime.now()
 
#             # Update reservation Current_Status and Check_In
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))
 
#             # Update room state
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))
 
#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))
 
#             # Insert in-house guests for this room (with meal plan and rate snapshots)
#             guest_rows = []
#             for g in guests:
#                 meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
#                 rate = rate_info.get(g["rate_id"]) if g["rate_id"] is not None else None
#                 guest_rows.append((
#                     reservation_id,
#                     room_id,
#                     g["name"].strip(),
#                     g.get("identity_type"),
#                     g.get("identity_no"),
#                     g.get("nationality"),
#                     1 if g.get("is_primary") else 0,
#                     g["meal_id"],
#                     meal["mp"] if meal else None,
#                     meal["rate"] if meal else None,
#                     meal["currency"] if meal else None,
#                     g["rate_id"],
#                     rate["room_name"] if rate else None,
#                     rate["rate"] if rate else None,
#                     rate["currency"] if rate else None,
#                     now,
#                 ))
#             cursor.executemany("""
#                 INSERT INTO hotel_tblinhouse_guests
#                     (reservation_id, room_id, name, identity_type, identity_no,
#                      nationality, is_primary, meal_id, meal_mp, meal_rate, meal_currency,
#                      rate_id, rate_name, rate_amount, rate_currency,
#                      is_active, checked_in_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#                         %s, %s, %s, %s, 1, %s)
#             """, guest_rows)
 
#             created_records.append({
#                 "Reservation_ID": reservation_id,
#                 "room_id": room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#                 "guests_saved": len(guest_rows)
#             })
 
#         mydb.commit()
#         return jsonify(created_records), 201
 
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400
 
#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


def _parse_int_id(value):
    """None or '' -> None, otherwise int. Raises ValueError if not a number."""
    if value in (None, ""):
        return None
    return int(value)

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
 
 
# @app_file404.route("/GuestCheckIN", methods=["POST"])
# @cross_origin()
# def guest_checkin():
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
 
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
 
#         # -------- PAYLOAD VALIDATION (before any DB work) --------
#         json_data = request.get_json() or {}
#         checkin_list = json_data.get("checkin_list", [])
 
#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400
 
#         primaries_by_reservation = {}   # reservation -> primary guests sent in this request
 
#         for item in checkin_list:
#             if not item.get("Reservation_ID") or not item.get("room_no"):
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_no'."}, 400
 
#             room_ref = item.get("room_no")
#             guests = item.get("guests")
 
#             if not isinstance(guests, list) or not guests:
#                 return {"error": f"At least one guest is required for room {room_ref}."}, 400
 
#             for g in guests:
#                 if not (g.get("name") or "").strip():
#                     return {"error": f"Every guest needs a name (room {room_ref})."}, 400
#             # is_complimentary can be sent once per room (default for its guests)
#             # or per guest (overrides the room value)
#             try:
#                 room_comp = _parse_bool_flag(item.get("is_complimentary"))
#                 for g in guests:
#                     g["is_complimentary"] = _parse_bool_flag(
#                         g.get("is_complimentary"), default=room_comp
#                     )
#             except ValueError:
#                 return {"error": f"is_complimentary must be true or false (room {room_ref})."}, 400
 
#             # meal_id / rate_id can be sent per guest, or once per room as a default for its guests
#             try:
#                 room_meal = _parse_int_id(item.get("meal_id"))
#                 room_rate = _parse_int_id(item.get("rate_id"))
#                 for g in guests:
#                     guest_meal = _parse_int_id(g.get("meal_id"))
#                     g["meal_id"] = guest_meal if guest_meal is not None else room_meal
 
#                     guest_rate = _parse_int_id(g.get("rate_id"))
#                     g["rate_id"] = guest_rate if guest_rate is not None else room_rate
#             except (TypeError, ValueError):
#                 return {"error": f"meal_id and rate_id must be numbers (room {room_ref})."}, 400
 
#             key = str(item["Reservation_ID"])
#             primaries_by_reservation[key] = (
#                 primaries_by_reservation.get(key, 0)
#                 + sum(1 for g in guests if g.get("is_primary"))
#             )
 
#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)
 
#         # -------- MEAL PLAN LOOKUP --------
#         # The name, rate and currency are read from the meal price table here and
#         # saved on each guest, so they stay as they were at check-in.
#         meal_ids = {
#             g["meal_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["meal_id"] is not None
#         }
#         meal_info = {}
#         if meal_ids:
#             placeholders = ",".join(["%s"] * len(meal_ids))
#             cursor.execute(
#                 f"SELECT id, mp, rate, currency FROM hotel_tblmeal_price "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(meal_ids),
#             )
#             meal_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(meal_ids - set(meal_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Meal plan(s) not found or inactive: {missing}."}, 400
 
#         # -------- RATE LOOKUP --------
#         # Same idea as meals: the rate name, amount and currency are copied onto
#         # each guest at check-in so later edits to hotel_tblrates don't change them.
#         rate_ids = {
#             g["rate_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["rate_id"] is not None
#         }
#         rate_info = {}
#         if rate_ids:
#             placeholders = ",".join(["%s"] * len(rate_ids))
#             cursor.execute(
#                 f"SELECT id, room_name, rate, currency FROM hotel_tblrates "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(rate_ids),
#             )
#             rate_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(rate_ids - set(rate_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Rate(s) not found or inactive: {missing}."}, 400
 
#         # -------- PRIMARY GUEST RULE: one per reservation --------
#         for res_key, primaries_in_request in primaries_by_reservation.items():
#             # lock the reservation so two simultaneous check-ins can't both add a primary
#             cursor.execute("SELECT id FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (res_key,))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": f"Reservation {res_key} not found."}, 404
 
#             cursor.execute("""
#                 SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
#                 WHERE reservation_id=%s AND is_primary=1 AND is_active=1
#             """, (res_key,))
#             existing_primary = cursor.fetchone()["n"]
 
#             if existing_primary == 0 and primaries_in_request != 1:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} needs exactly one primary guest "
#                              f"across all its rooms (received {primaries_in_request})."
#                 }, 400
 
#             if existing_primary > 0 and primaries_in_request > 0:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} already has a primary guest in-house. "
#                              f"Guests added to new rooms must not be primary."
#                 }, 400
 
#         created_records = []
 
#         for item in checkin_list:
#             reservation_id = item["Reservation_ID"]
#             room_id = item["room_no"]
#             guests = item["guests"]
 
#             # Check for existing reservation detail
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation details already exist for "
#                              f"Reservation_ID={reservation_id} and room_id={room_id}"
#                 }, 400
 
#             now = datetime.now()
 
#             # Update reservation Current_Status and Check_In
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))
 
#             # Update room state
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))
 
#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))
 
#             # Insert in-house guests for this room (with meal plan and rate snapshots)
#             guest_rows = []
#             for g in guests:
#                 meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
#                 rate = rate_info.get(g["rate_id"]) if g["rate_id"] is not None else None
#                 guest_rows.append((
#                     reservation_id,
#                     room_id,
#                     g["name"].strip(),
#                     g.get("identity_type"),
#                     g.get("identity_no"),
#                     g.get("nationality"),
#                     1 if g.get("is_primary") else 0,
#                     1 if g["is_complimentary"] else 0,   # <-- new
#                     g["meal_id"],
#                     meal["mp"] if meal else None,
#                     meal["rate"] if meal else None,
#                     meal["currency"] if meal else None,
#                     g["rate_id"],
#                     rate["room_name"] if rate else None,
#                     rate["rate"] if rate else None,
#                     rate["currency"] if rate else None,
#                     now,
#                 ))
#             cursor.executemany("""
#                 INSERT INTO hotel_tblinhouse_guests
#                     (reservation_id, room_id, name, identity_type, identity_no,
#                      nationality, is_primary, is_complimentary, meal_id, meal_mp, meal_rate, meal_currency,
#                      rate_id, rate_name, rate_amount, rate_currency,
#                      is_active, checked_in_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
#                         %s, %s, %s, %s, 1, %s)
#             """, guest_rows)
 
#             created_records.append({
#                 "Reservation_ID": reservation_id,
#                 "room_id": room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#                 "guests_saved": len(guest_rows),
#                 "is_complimentary": any(g["is_complimentary"] for g in guests)
#             })
 
#         mydb.commit()
#         return jsonify(created_records), 201
 
#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400
 
#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()

# latest
# @app_file404.route("/GuestCheckIN", methods=["POST"])
# @cross_origin()
# def guest_checkin():
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

#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- PAYLOAD VALIDATION (before any DB work) --------
#         json_data = request.get_json() or {}
#         checkin_list = json_data.get("checkin_list", [])

#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400

#         primaries_by_reservation = {}   # reservation -> primary guests sent in this request

#         for item in checkin_list:
#             if not item.get("Reservation_ID") or not item.get("room_no"):
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_no'."}, 400

#             room_ref = item.get("room_no")
#             guests = item.get("guests")

#             if not isinstance(guests, list) or not guests:
#                 return {"error": f"At least one guest is required for room {room_ref}."}, 400

#             for g in guests:
#                 if not (g.get("name") or "").strip():
#                     return {"error": f"Every guest needs a name (room {room_ref})."}, 400

#             # is_complimentary: per guest overrides per room; if neither is sent it stays
#             # None here and is filled from the reservation's flag after the DB lookup below
#             try:
#                 room_comp = _parse_bool_flag(item.get("is_complimentary"), default=None)
#                 for g in guests:
#                     g["is_complimentary"] = _parse_bool_flag(
#                         g.get("is_complimentary"), default=room_comp
#                     )
#             except ValueError:
#                 return {"error": f"is_complimentary must be true or false (room {room_ref})."}, 400

#             # meal_id / rate_id can be sent per guest, or once per room as a default for its guests
#             try:
#                 room_meal = _parse_int_id(item.get("meal_id"))
#                 room_rate = _parse_int_id(item.get("rate_id"))
#                 for g in guests:
#                     guest_meal = _parse_int_id(g.get("meal_id"))
#                     g["meal_id"] = guest_meal if guest_meal is not None else room_meal

#                     guest_rate = _parse_int_id(g.get("rate_id"))
#                     g["rate_id"] = guest_rate if guest_rate is not None else room_rate
#             except (TypeError, ValueError):
#                 return {"error": f"meal_id and rate_id must be numbers (room {room_ref})."}, 400

#             key = str(item["Reservation_ID"])
#             primaries_by_reservation[key] = (
#                 primaries_by_reservation.get(key, 0)
#                 + sum(1 for g in guests if g.get("is_primary"))
#             )

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- MEAL PLAN LOOKUP --------
#         # The name, rate and currency are read from the meal price table here and
#         # saved on each guest, so they stay as they were at check-in.
#         meal_ids = {
#             g["meal_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["meal_id"] is not None
#         }
#         meal_info = {}
#         if meal_ids:
#             placeholders = ",".join(["%s"] * len(meal_ids))
#             cursor.execute(
#                 f"SELECT id, mp, rate, currency FROM hotel_tblmeal_price "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(meal_ids),
#             )
#             meal_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(meal_ids - set(meal_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Meal plan(s) not found or inactive: {missing}."}, 400

#         # -------- RATE LOOKUP --------
#         # Same idea as meals: the rate name, amount and currency are copied onto
#         # each guest at check-in so later edits to hotel_tblrates don't change them.
#         rate_ids = {
#             g["rate_id"]
#             for item in checkin_list
#             for g in item["guests"]
#             if g["rate_id"] is not None
#         }
#         rate_info = {}
#         if rate_ids:
#             placeholders = ",".join(["%s"] * len(rate_ids))
#             cursor.execute(
#                 f"SELECT id, room_name, rate, currency FROM hotel_tblrates "
#                 f"WHERE is_active = 1 AND id IN ({placeholders})",
#                 list(rate_ids),
#             )
#             rate_info = {r["id"]: r for r in cursor.fetchall()}
#             missing = sorted(rate_ids - set(rate_info))
#             if missing:
#                 mydb.rollback()
#                 return {"error": f"Rate(s) not found or inactive: {missing}."}, 400

#         # -------- PRIMARY GUEST RULE: one per reservation --------
#         reservation_comp = {}   # reservation -> is_complimentary flag on the reservation

#         for res_key, primaries_in_request in primaries_by_reservation.items():
#             # lock the reservation so two simultaneous check-ins can't both add a primary
#             cursor.execute(
#                 "SELECT id, is_complimentary FROM hotel_tblreservation WHERE id=%s FOR UPDATE",
#                 (res_key,)
#             )
#             res_row = cursor.fetchone()
#             if not res_row:
#                 mydb.rollback()
#                 return {"error": f"Reservation {res_key} not found."}, 404
#             reservation_comp[res_key] = bool(res_row["is_complimentary"])

#             cursor.execute("""
#                 SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
#                 WHERE reservation_id=%s AND is_primary=1 AND is_active=1
#             """, (res_key,))
#             existing_primary = cursor.fetchone()["n"]

#             if existing_primary == 0 and primaries_in_request != 1:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} needs exactly one primary guest "
#                              f"across all its rooms (received {primaries_in_request})."
#                 }, 400

#             if existing_primary > 0 and primaries_in_request > 0:
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation {res_key} already has a primary guest in-house. "
#                              f"Guests added to new rooms must not be primary."
#                 }, 400

#         # -------- COMPLIMENTARY DEFAULT FROM THE RESERVATION --------
#         # guests with no flag from the frontend (guest or room level) inherit the reservation's flag
#         for item in checkin_list:
#             res_comp = reservation_comp[str(item["Reservation_ID"])]
#             for g in item["guests"]:
#                 if g["is_complimentary"] is None:
#                     g["is_complimentary"] = res_comp

#         created_records = []

#         for item in checkin_list:
#             reservation_id = item["Reservation_ID"]
#             room_id = item["room_no"]
#             guests = item["guests"]

#             # Check for existing reservation detail
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation details already exist for "
#                              f"Reservation_ID={reservation_id} and room_id={room_id}"
#                 }, 400

#             now = datetime.now()

#             # Update reservation Current_Status and Check_In
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room state
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))

#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))

#             # Insert in-house guests for this room (with meal plan and rate snapshots)
#             guest_rows = []
#             for g in guests:
#                 meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
#                 rate = rate_info.get(g["rate_id"]) if g["rate_id"] is not None else None
#                 guest_rows.append((
#                     reservation_id,
#                     room_id,
#                     g["name"].strip(),
#                     g.get("identity_type"),
#                     g.get("identity_no"),
#                     g.get("nationality"),
#                     1 if g.get("is_primary") else 0,
#                     1 if g["is_complimentary"] else 0,
#                     g["meal_id"],
#                     meal["mp"] if meal else None,
#                     meal["rate"] if meal else None,
#                     meal["currency"] if meal else None,
#                     g["rate_id"],
#                     rate["room_name"] if rate else None,
#                     rate["rate"] if rate else None,
#                     rate["currency"] if rate else None,
#                     now,
#                 ))
#             cursor.executemany("""
#                 INSERT INTO hotel_tblinhouse_guests
#                     (reservation_id, room_id, name, identity_type, identity_no,
#                      nationality, is_primary, is_complimentary,
#                      meal_id, meal_mp, meal_rate, meal_currency,
#                      rate_id, rate_name, rate_amount, rate_currency,
#                      is_active, checked_in_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
#                         %s, %s, %s, %s,
#                         %s, %s, %s, %s, 1, %s)
#             """, guest_rows)

#             created_records.append({
#                 "Reservation_ID": reservation_id,
#                 "room_id": room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#                 "guests_saved": len(guest_rows),
#                 "is_complimentary": any(g["is_complimentary"] for g in guests)
#             })

#         mydb.commit()
#         return jsonify(created_records), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()



from root.flask_routes.hotel.hotel_utils.utils import log_hotel_activity, get_employee_name   # <-- new (same import as create-reservation)

@app_file404.route("/GuestCheckIN", methods=["POST"])
@cross_origin()
def guest_checkin():
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

        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- PAYLOAD VALIDATION (before any DB work) --------
        json_data = request.get_json() or {}
        checkin_list = json_data.get("checkin_list", [])
        emp_id = json_data.get("Emp_ID")   # <-- new: who is checking the guest in (sent by the frontend)

        if not isinstance(checkin_list, list) or not checkin_list:
            return {"error": "Expected a non-empty list 'checkin_list'."}, 400

        primaries_by_reservation = {}   # reservation -> primary guests sent in this request

        for item in checkin_list:
            if not item.get("Reservation_ID") or not item.get("room_no"):
                return {"error": "Each item must have 'Reservation_ID' and 'room_no'."}, 400

            room_ref = item.get("room_no")
            guests = item.get("guests")

            if not isinstance(guests, list) or not guests:
                return {"error": f"At least one guest is required for room {room_ref}."}, 400

            for g in guests:
                if not (g.get("name") or "").strip():
                    return {"error": f"Every guest needs a name (room {room_ref})."}, 400

            # is_complimentary: per guest overrides per room; if neither is sent it stays
            # None here and is filled from the reservation's flag after the DB lookup below
            try:
                room_comp = _parse_bool_flag(item.get("is_complimentary"), default=None)
                for g in guests:
                    g["is_complimentary"] = _parse_bool_flag(
                        g.get("is_complimentary"), default=room_comp
                    )
            except ValueError:
                return {"error": f"is_complimentary must be true or false (room {room_ref})."}, 400

            # meal_id / rate_id can be sent per guest, or once per room as a default for its guests
            try:
                room_meal = _parse_int_id(item.get("meal_id"))
                room_rate = _parse_int_id(item.get("rate_id"))
                for g in guests:
                    guest_meal = _parse_int_id(g.get("meal_id"))
                    g["meal_id"] = guest_meal if guest_meal is not None else room_meal

                    guest_rate = _parse_int_id(g.get("rate_id"))
                    g["rate_id"] = guest_rate if guest_rate is not None else room_rate
            except (TypeError, ValueError):
                return {"error": f"meal_id and rate_id must be numbers (room {room_ref})."}, 400

            key = str(item["Reservation_ID"])
            primaries_by_reservation[key] = (
                primaries_by_reservation.get(key, 0)
                + sum(1 for g in guests if g.get("is_primary"))
            )

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- MEAL PLAN LOOKUP --------
        # The name, rate and currency are read from the meal price table here and
        # saved on each guest, so they stay as they were at check-in.
        meal_ids = {
            g["meal_id"]
            for item in checkin_list
            for g in item["guests"]
            if g["meal_id"] is not None
        }
        meal_info = {}
        if meal_ids:
            placeholders = ",".join(["%s"] * len(meal_ids))
            cursor.execute(
                f"SELECT id, mp, rate, currency FROM hotel_tblmeal_price "
                f"WHERE is_active = 1 AND id IN ({placeholders})",
                list(meal_ids),
            )
            meal_info = {r["id"]: r for r in cursor.fetchall()}
            missing = sorted(meal_ids - set(meal_info))
            if missing:
                mydb.rollback()
                return {"error": f"Meal plan(s) not found or inactive: {missing}."}, 400

        # -------- RATE LOOKUP --------
        # Same idea as meals: the rate name, amount and currency are copied onto
        # each guest at check-in so later edits to hotel_tblrates don't change them.
        rate_ids = {
            g["rate_id"]
            for item in checkin_list
            for g in item["guests"]
            if g["rate_id"] is not None
        }
        rate_info = {}
        if rate_ids:
            placeholders = ",".join(["%s"] * len(rate_ids))
            cursor.execute(
                f"SELECT id, room_name, rate, currency FROM hotel_tblrates "
                f"WHERE is_active = 1 AND id IN ({placeholders})",
                list(rate_ids),
            )
            rate_info = {r["id"]: r for r in cursor.fetchall()}
            missing = sorted(rate_ids - set(rate_info))
            if missing:
                mydb.rollback()
                return {"error": f"Rate(s) not found or inactive: {missing}."}, 400

        # -------- PRIMARY GUEST RULE: one per reservation --------
        reservation_comp = {}     # reservation -> is_complimentary flag on the reservation
        reservation_outlet = {}   # <-- new: reservation -> outlet (for the log)

        for res_key, primaries_in_request in primaries_by_reservation.items():
            # lock the reservation so two simultaneous check-ins can't both add a primary
            cursor.execute(
                "SELECT id, is_complimentary, outlet FROM hotel_tblreservation WHERE id=%s FOR UPDATE",   # <-- new: outlet
                (res_key,)
            )
            res_row = cursor.fetchone()
            if not res_row:
                mydb.rollback()
                return {"error": f"Reservation {res_key} not found."}, 404
            reservation_comp[res_key] = bool(res_row["is_complimentary"])
            reservation_outlet[res_key] = res_row["outlet"]   # <-- new

            cursor.execute("""
                SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
                WHERE reservation_id=%s AND is_primary=1 AND is_active=1
            """, (res_key,))
            existing_primary = cursor.fetchone()["n"]

            if existing_primary == 0 and primaries_in_request != 1:
                mydb.rollback()
                return {
                    "error": f"Reservation {res_key} needs exactly one primary guest "
                             f"across all its rooms (received {primaries_in_request})."
                }, 400

            if existing_primary > 0 and primaries_in_request > 0:
                mydb.rollback()
                return {
                    "error": f"Reservation {res_key} already has a primary guest in-house. "
                             f"Guests added to new rooms must not be primary."
                }, 400

        # -------- COMPLIMENTARY DEFAULT FROM THE RESERVATION --------
        # guests with no flag from the frontend (guest or room level) inherit the reservation's flag
        for item in checkin_list:
            res_comp = reservation_comp[str(item["Reservation_ID"])]
            for g in item["guests"]:
                if g["is_complimentary"] is None:
                    g["is_complimentary"] = res_comp

        emp_name = get_employee_name(cursor, emp_id)   # <-- new: looked up once for the whole request

        created_records = []

        for item in checkin_list:
            reservation_id = item["Reservation_ID"]
            room_id = item["room_no"]
            guests = item["guests"]

            # Check for existing reservation detail
            cursor.execute("""
                SELECT id FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND room_id=%s
            """, (reservation_id, room_id))
            if cursor.fetchone():
                mydb.rollback()
                return {
                    "error": f"Reservation details already exist for "
                             f"Reservation_ID={reservation_id} and room_id={room_id}"
                }, 400

            now = datetime.now()

            # Update reservation Current_Status and Check_In
            cursor.execute("""
                UPDATE hotel_tblreservation
                SET Current_Status='Registered', Check_In=%s
                WHERE id=%s
            """, (now, reservation_id))

            # Update room state
            cursor.execute("""
                UPDATE hotel_tblrooms
                SET room_state='Check-In'
                WHERE id=%s
            """, (room_id,))

            # Insert reservation detail
            cursor.execute("""
                INSERT INTO hotel_tblreservation_details (
                    Reservation_ID, room_id, is_current, created_at, is_active
                ) VALUES (%s, %s, 1, %s, 1)
            """, (reservation_id, room_id, now))

            # Insert in-house guests for this room (with meal plan and rate snapshots)
            guest_rows = []
            for g in guests:
                meal = meal_info.get(g["meal_id"]) if g["meal_id"] is not None else None
                rate = rate_info.get(g["rate_id"]) if g["rate_id"] is not None else None
                guest_rows.append((
                    reservation_id,
                    room_id,
                    g["name"].strip(),
                    g.get("identity_type"),
                    g.get("identity_no"),
                    g.get("nationality"),
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
                    (reservation_id, room_id, name, identity_type, identity_no,
                     nationality, is_primary, is_complimentary,
                     meal_id, meal_mp, meal_rate, meal_currency,
                     rate_id, rate_name, rate_amount, rate_currency,
                     is_active, checked_in_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, 1, %s)
            """, guest_rows)

            # ---- Activity log: one row per room checked in ----   # <-- new
            cursor.execute("SELECT room_no FROM hotel_tblrooms WHERE id = %s", (room_id,))
            room_row = cursor.fetchone()
            room_no = room_row["room_no"] if room_row else room_id

            primary_name = next(
                (g["name"].strip() for g in guests if g.get("is_primary")),
                guests[0]["name"].strip()
            )
            room_is_comp = any(g["is_complimentary"] for g in guests)

            description = (
                f"{emp_name or 'Employee'} checked in reservation #{reservation_id} "
                f"({primary_name}, {len(guests)} guest(s)) to room {room_no}"
            )
            if room_is_comp:
                description += ", complimentary"

            log_hotel_activity(
                cursor,
                outlet=reservation_outlet.get(str(reservation_id)),
                action="CHECKED_IN",
                reservation_id=reservation_id,
                description=description,
                employee_id=emp_id,
                employee_name=emp_name,
                details={
                    "room_id": room_id,
                    "room_no": room_no,
                    "guests": [g["name"].strip() for g in guests],
                    "is_complimentary": room_is_comp,
                    "check_in": now.strftime("%Y-%m-%d %H:%M:%S"),
                },
                endpoint="/GuestCheckIN",
            )

            created_records.append({
                "Reservation_ID": reservation_id,
                "room_id": room_id,
                "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
                "guests_saved": len(guest_rows),
                "is_complimentary": any(g["is_complimentary"] for g in guests)
            })

        mydb.commit()
        return jsonify(created_records), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()

from datetime import datetime
import os
import mysql.connector
from flask import request, jsonify
from flask_cors import cross_origin


# @app_file404.route("/GuestCheckIN-v2/", methods=["POST"])
# @cross_origin()
# def guest_checkin_v2():
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

#         # -------- PAYLOAD VALIDATION (before any DB work) --------
#         json_data = request.get_json() or {}
#         checkin_list = json_data.get("checkin_list", [])

#         if not isinstance(checkin_list, list) or not checkin_list:
#             return {"error": "Expected a non-empty list 'checkin_list'."}, 400

#         for item in checkin_list:
#             if not item.get("Reservation_ID") or not item.get("room_id"):
#                 return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

#             room_ref = item.get("room_id")
#             guests = item.get("guests")

#             if not isinstance(guests, list) or not guests:
#                 return {"error": f"At least one guest is required for room {room_ref}."}, 400

#             if sum(1 for g in guests if g.get("is_primary")) != 1:
#                 return {"error": f"Exactly one primary guest is required for room {room_ref}."}, 400

#             for g in guests:
#                 if not (g.get("name") or "").strip():
#                     return {"error": f"Every guest needs a name (room {room_ref})."}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         created_records = []

#         for item in checkin_list:
#             outlet_reservation_id = item["Reservation_ID"]
#             outlet_room_id = item["room_id"]
#             guests = item["guests"]

#             # Fetch internal reservation ID
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation
#                 WHERE reservation_outlet_id=%s
#             """, (outlet_reservation_id,))
#             reservation_row = cursor.fetchone()
#             if not reservation_row:
#                 mydb.rollback()
#                 return {"error": f"Reservation not found for outlet ID {outlet_reservation_id}"}, 404
#             reservation_id = reservation_row["id"]

#             # Fetch internal room ID
#             cursor.execute("""
#                 SELECT id FROM hotel_tblrooms
#                 WHERE outlet_room_id=%s
#             """, (outlet_room_id,))
#             room_row = cursor.fetchone()
#             if not room_row:
#                 mydb.rollback()
#                 return {"error": f"Room not found for outlet ID {outlet_room_id}"}, 404
#             room_id = room_row["id"]

#             # Check if reservation detail already exists
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, room_id))
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {
#                     "error": f"Reservation detail already exists for "
#                              f"Reservation_ID={outlet_reservation_id} and room_id={outlet_room_id}"
#                 }, 400

#             now = datetime.now()

#             # Update reservation
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET Current_Status='Registered', Check_In=%s
#                 WHERE id=%s
#             """, (now, reservation_id))

#             # Update room
#             cursor.execute("""
#                 UPDATE hotel_tblrooms
#                 SET room_state='Check-In'
#                 WHERE id=%s
#             """, (room_id,))

#             # Insert reservation detail
#             cursor.execute("""
#                 INSERT INTO hotel_tblreservation_details (
#                     Reservation_ID, room_id, is_current, created_at, is_active
#                 ) VALUES (%s, %s, 1, %s, 1)
#             """, (reservation_id, room_id, now))

#             # Insert in-house guests for this room
#             guest_rows = [
#                 (
#                     reservation_id,
#                     room_id,
#                     g["name"].strip(),
#                     g.get("identity_type"),
#                     g.get("identity_no"),
#                     g.get("nationality"),
#                     1 if g.get("is_primary") else 0,
#                     now,
#                 )
#                 for g in guests
#             ]
#             cursor.executemany("""
#                 INSERT INTO hotel_tblinhouse_guests
#                     (reservation_id, room_id, name, identity_type, identity_no,
#                      nationality, is_primary, is_active, checked_in_at)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
#             """, guest_rows)

#             created_records.append({
#                 "Reservation_ID": outlet_reservation_id,
#                 "room_id": outlet_room_id,
#                 "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
#                 "guests_saved": len(guest_rows)
#             })

#         mydb.commit()
#         return jsonify(created_records), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


@app_file404.route("/GuestCheckIN-v2/", methods=["POST"])
@cross_origin()
def guest_checkin_v2():
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

        # -------- PAYLOAD VALIDATION (before any DB work) --------
        json_data = request.get_json() or {}
        checkin_list = json_data.get("checkin_list", [])

        if not isinstance(checkin_list, list) or not checkin_list:
            return {"error": "Expected a non-empty list 'checkin_list'."}, 400

        primaries_by_reservation = {}   # outlet reservation id -> primary guests sent in this request

        for item in checkin_list:
            if not item.get("Reservation_ID") or not item.get("room_id"):
                return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

            room_ref = item.get("room_id")
            guests = item.get("guests")

            if not isinstance(guests, list) or not guests:
                return {"error": f"At least one guest is required for room {room_ref}."}, 400

            for g in guests:
                if not (g.get("name") or "").strip():
                    return {"error": f"Every guest needs a name (room {room_ref})."}, 400

            key = str(item["Reservation_ID"])
            primaries_by_reservation[key] = (
                primaries_by_reservation.get(key, 0)
                + sum(1 for g in guests if g.get("is_primary"))
            )

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESOLVE RESERVATIONS + PRIMARY GUEST RULE (one per reservation) --------
        internal_reservation_ids = {}   # outlet reservation id -> internal id

        for outlet_res_key, primaries_in_request in primaries_by_reservation.items():
            # lock the reservation so two simultaneous check-ins can't both add a primary
            cursor.execute("""
                SELECT id FROM hotel_tblreservation
                WHERE reservation_outlet_id=%s
                FOR UPDATE
            """, (outlet_res_key,))
            reservation_row = cursor.fetchone()
            if not reservation_row:
                mydb.rollback()
                return {"error": f"Reservation not found for outlet ID {outlet_res_key}"}, 404

            internal_id = reservation_row["id"]
            internal_reservation_ids[outlet_res_key] = internal_id

            cursor.execute("""
                SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
                WHERE reservation_id=%s AND is_primary=1 AND is_active=1
            """, (internal_id,))
            existing_primary = cursor.fetchone()["n"]

            if existing_primary == 0 and primaries_in_request != 1:
                mydb.rollback()
                return {
                    "error": f"Reservation {outlet_res_key} needs exactly one primary guest "
                             f"across all its rooms (received {primaries_in_request})."
                }, 400

            if existing_primary > 0 and primaries_in_request > 0:
                mydb.rollback()
                return {
                    "error": f"Reservation {outlet_res_key} already has a primary guest in-house. "
                             f"Guests added to new rooms must not be primary."
                }, 400

        created_records = []

        for item in checkin_list:
            outlet_reservation_id = item["Reservation_ID"]
            outlet_room_id = item["room_id"]
            guests = item["guests"]

            reservation_id = internal_reservation_ids[str(outlet_reservation_id)]

            # Fetch internal room ID
            cursor.execute("""
                SELECT id FROM hotel_tblrooms
                WHERE outlet_room_id=%s
            """, (outlet_room_id,))
            room_row = cursor.fetchone()
            if not room_row:
                mydb.rollback()
                return {"error": f"Room not found for outlet ID {outlet_room_id}"}, 404
            room_id = room_row["id"]

            # Check if reservation detail already exists
            cursor.execute("""
                SELECT id FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND room_id=%s
            """, (reservation_id, room_id))
            if cursor.fetchone():
                mydb.rollback()
                return {
                    "error": f"Reservation detail already exists for "
                             f"Reservation_ID={outlet_reservation_id} and room_id={outlet_room_id}"
                }, 400

            now = datetime.now()

            # Update reservation
            cursor.execute("""
                UPDATE hotel_tblreservation
                SET Current_Status='Registered', Check_In=%s
                WHERE id=%s
            """, (now, reservation_id))

            # Update room
            cursor.execute("""
                UPDATE hotel_tblrooms
                SET room_state='Check-In'
                WHERE id=%s
            """, (room_id,))

            # Insert reservation detail
            cursor.execute("""
                INSERT INTO hotel_tblreservation_details (
                    Reservation_ID, room_id, is_current, created_at, is_active
                ) VALUES (%s, %s, 1, %s, 1)
            """, (reservation_id, room_id, now))

            # Insert in-house guests for this room
            guest_rows = [
                (
                    reservation_id,
                    room_id,
                    g["name"].strip(),
                    g.get("identity_type"),
                    g.get("identity_no"),
                    g.get("nationality"),
                    1 if g.get("is_primary") else 0,
                    now,
                )
                for g in guests
            ]
            cursor.executemany("""
                INSERT INTO hotel_tblinhouse_guests
                    (reservation_id, room_id, name, identity_type, identity_no,
                     nationality, is_primary, is_active, checked_in_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
            """, guest_rows)

            created_records.append({
                "Reservation_ID": outlet_reservation_id,
                "room_id": outlet_room_id,
                "Check_In": now.strftime("%Y-%m-%d %H:%M:%S"),
                "guests_saved": len(guest_rows)
            })

        mydb.commit()
        return jsonify(created_records), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


from datetime import datetime
import os
import mysql.connector
from flask import request, jsonify
from flask_cors import cross_origin


@app_file404.route("/GuestCheckOUT-v2", methods=["POST"])
@cross_origin()
def guest_checkout_v2():
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

        # -------- PAYLOAD VALIDATION --------
        json_data = request.get_json() or {}
        checkout_list = json_data.get("checkout_list", [])

        if not isinstance(checkout_list, list) or not checkout_list:
            return {"error": "Expected a non-empty list 'checkout_list'."}, 400

        for item in checkout_list:
            if not item.get("Reservation_ID") or not item.get("room_id"):
                return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        results = []

        for item in checkout_list:
            outlet_reservation_id = item["Reservation_ID"]
            outlet_room_id = item["room_id"]

            # Fetch internal reservation ID
            cursor.execute("""
                SELECT id FROM hotel_tblreservation
                WHERE reservation_outlet_id=%s
            """, (outlet_reservation_id,))
            reservation_row = cursor.fetchone()
            if not reservation_row:
                mydb.rollback()
                return {"error": f"Reservation not found for outlet ID {outlet_reservation_id}"}, 404
            reservation_id = reservation_row["id"]

            # Fetch internal room ID
            cursor.execute("""
                SELECT id FROM hotel_tblrooms
                WHERE outlet_room_id=%s
            """, (outlet_room_id,))
            room_row = cursor.fetchone()
            if not room_row:
                mydb.rollback()
                return {"error": f"Room not found for outlet ID {outlet_room_id}"}, 404
            room_id = room_row["id"]

            now = datetime.now()

            # Close reservation detail for this room
            cursor.execute("""
                UPDATE hotel_tblreservation_details
                SET is_current=0
                WHERE Reservation_ID=%s AND room_id=%s
            """, (reservation_id, room_id))

            # Close in-house guests of this room
            cursor.execute("""
                UPDATE hotel_tblinhouse_guests
                SET is_active=0, checked_out_at=%s
                WHERE reservation_id=%s AND room_id=%s AND is_active=1
            """, (now, reservation_id, room_id))
            guests_checked_out = cursor.rowcount

            # Vacate the room
            cursor.execute("""
                UPDATE hotel_tblrooms
                SET room_state='Vacant'
                WHERE id=%s
            """, (room_id,))

            # Mark the reservation Checked Out only when no other room is still in-house
            cursor.execute("""
                SELECT COUNT(*) AS remaining
                FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND is_current=1
            """, (reservation_id,))
            remaining = cursor.fetchone()["remaining"]

            if remaining == 0:
                cursor.execute("""
                    UPDATE hotel_tblreservation
                    SET Current_Status='Checked Out', Check_Out=%s
                    WHERE id=%s
                """, (now, reservation_id))

            results.append({
                "Reservation_ID": outlet_reservation_id,
                "room_id": outlet_room_id,
                "guests_checked_out": guests_checked_out,
                "reservation_closed": remaining == 0
            })

        mydb.commit()
        return jsonify({
            "message": "Reservations checked out successfully",
            "results": results
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


from datetime import datetime
import os
import mysql.connector
from flask import request, jsonify
from flask_cors import cross_origin


@app_file404.route("/GuestCheckOut", methods=["POST"])
@cross_origin()
def guest_checkout():
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

        # -------- PAYLOAD VALIDATION --------
        json_data = request.get_json() or {}
        checkout_list = json_data.get("checkout_list", [])

        if not isinstance(checkout_list, list) or not checkout_list:
            return {"error": "Expected a non-empty list 'checkout_list'."}, 400

        for item in checkout_list:
            if not item.get("Reservation_ID") or not item.get("room_id"):
                return {"error": "Each item must have 'Reservation_ID' and 'room_id'."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        results = []

        for item in checkout_list:
            reservation_id = item["Reservation_ID"]
            room_id = item["room_id"]
            now = datetime.now()

            # Close reservation detail for this room
            cursor.execute("""
                UPDATE hotel_tblreservation_details
                SET is_current=0
                WHERE Reservation_ID=%s AND room_id=%s
            """, (reservation_id, room_id))

            # Close in-house guests of this room
            cursor.execute("""
                UPDATE hotel_tblinhouse_guests
                SET is_active=0, checked_out_at=%s
                WHERE reservation_id=%s AND room_id=%s AND is_active=1
            """, (now, reservation_id, room_id))
            guests_checked_out = cursor.rowcount

            # Vacate the room
            cursor.execute("""
                UPDATE hotel_tblrooms
                SET room_state='Vacant'
                WHERE id=%s
            """, (room_id,))

            # Mark the reservation Checked Out only when no other room is still in-house
            cursor.execute("""
                SELECT COUNT(*) AS remaining
                FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND is_current=1
            """, (reservation_id,))
            remaining = cursor.fetchone()["remaining"]

            if remaining == 0:
                cursor.execute("""
                    UPDATE hotel_tblreservation
                    SET Current_Status='Checked Out', Check_Out=%s
                    WHERE id=%s
                """, (now, reservation_id))

            results.append({
                "Reservation_ID": reservation_id,
                "room_id": room_id,
                "guests_checked_out": guests_checked_out,
                "reservation_closed": remaining == 0
            })

        mydb.commit()
        return jsonify({
            "message": "Reservations checked out successfully",
            "results": results
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()



from datetime import date, datetime, timedelta

STAY_SQ = """
    SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
    FROM hotel_tblguestreservation
    WHERE is_active = 1
    GROUP BY Reservation_ID
"""


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    return value


def find_room_conflict(cursor, room_id, reservation_id, window_start, window_end, today):
    """
    Return the first other stay that blocks `room_id` during [window_start, window_end), or None.
    Same rules as /rooms for today, plus later dates:
      - another reservation holds the room (Registered or Reserved, current assignment)
      - a same-day stay occupies its own day
      - a Registered stay that ends today still holds the room today (Departing Today)
    """
    cursor.execute(f"""
        SELECT res.id AS reservation_id, res.Current_Status,
               st.s AS start_date, st.e AS end_date
        FROM hotel_tblreservation_details rd
        JOIN hotel_tblreservation res
            ON res.id = rd.Reservation_ID AND res.is_active = 1
        JOIN ({STAY_SQ}) st ON st.Reservation_ID = res.id
        WHERE rd.room_id = %s
          AND rd.is_active = 1
          AND rd.is_current = 1
          AND rd.Reservation_ID <> %s
          AND res.Current_Status IN ('Registered', 'Reserved')
    """, (room_id, reservation_id))

    one_day = timedelta(days=1)
    for stay in cursor.fetchall():
        start = _to_date(stay["start_date"])
        end = _to_date(stay["end_date"])

        occupied_until = max(end, start + one_day)            # exclusive end
        if stay["Current_Status"] == "Registered" and end == today:
            occupied_until = max(occupied_until, today + one_day)   # not billed yet, still in the room

        if start < window_end and occupied_until > window_start:
            return {
                "reservation_id": stay["reservation_id"],
                "status": stay["Current_Status"],
                "start": start,
                "end": end,
            }
    return None


# @app_file404.route("/GuestRoomChange", methods=["POST"])
# @cross_origin()
# def guest_room_change():
#     mydb = None
#     cursor = None
#     try:
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- PAYLOAD VALIDATION --------
#         json_data = request.get_json() or {}
#         room_changes = json_data.get("room_changes", [])

#         if not isinstance(room_changes, list) or not room_changes:
#             return {"error": "Expected a non-empty list 'room_changes'."}, 400

#         for item in room_changes:
#             if not item.get("Reservation_ID") or not item.get("from_room_id") or not item.get("to_room_id"):
#                 return {"error": "Each item needs 'Reservation_ID', 'from_room_id' and 'to_room_id'."}, 400
#             if str(item["from_room_id"]) == str(item["to_room_id"]):
#                 return {"error": "from_room_id and to_room_id cannot be the same."}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         today = date.today()
#         results = []

#         for item in room_changes:
#             reservation_id = item["Reservation_ID"]   # internal hotel_tblreservation.id
#             from_room_id = item["from_room_id"]       # internal hotel_tblrooms.id
#             to_room_id = item["to_room_id"]           # internal hotel_tblrooms.id
#             reason = item.get("reason")

#             # Reservation must exist, be active, have stay dates and still hold a room
#             cursor.execute(f"""
#                 SELECT res.id, res.Current_Status, st.s AS start_date, st.e AS end_date
#                 FROM hotel_tblreservation res
#                 JOIN ({STAY_SQ}) st ON st.Reservation_ID = res.id
#                 WHERE res.id = %s AND res.is_active = 1
#             """, (reservation_id,))
#             res = cursor.fetchone()
#             if not res:
#                 mydb.rollback()
#                 return {"error": f"Reservation not found: {reservation_id}"}, 404
#             if res["Current_Status"] not in ("Registered", "Reserved"):
#                 mydb.rollback()
#                 return {"error": f"Reservation {reservation_id} is {res['Current_Status']} and cannot change rooms."}, 400

#             # Old room must exist
#             cursor.execute("SELECT id FROM hotel_tblrooms WHERE id=%s", (from_room_id,))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": f"Room not found: {from_room_id}"}, 404

#             # New room: locked so two simultaneous changes can't both take it
#             cursor.execute("""
#                 SELECT id, room_no FROM hotel_tblrooms
#                 WHERE id=%s AND is_active=1
#                 FOR UPDATE
#             """, (to_room_id,))
#             to_row = cursor.fetchone()
#             if not to_row:
#                 mydb.rollback()
#                 return {"error": f"Room not found: {to_room_id}"}, 404

#             # The guest must currently be in the old room under this reservation
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s AND is_current=1 AND is_active=1
#             """, (reservation_id, from_room_id))
#             if not cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": f"Reservation {reservation_id} is not currently in room {from_room_id}."}, 400

#             # -------- AVAILABILITY OF THE NEW ROOM FOR THE REST OF THE STAY --------
#             stay_start = _to_date(res["start_date"])
#             stay_end = _to_date(res["end_date"])
#             window_start = max(stay_start, today)
#             window_end = max(stay_end, window_start + timedelta(days=1))   # covers today at least

#             conflict = find_room_conflict(
#                 cursor, to_room_id, reservation_id, window_start, window_end, today
#             )
#             if conflict:
#                 mydb.rollback()
#                 return {
#                     "error": (
#                         f"Room {to_row['room_no']} is not available from {window_start} to {stay_end}: "
#                         f"reservation {conflict['reservation_id']} ({conflict['status']}) holds it "
#                         f"from {conflict['start']} to {conflict['end']}."
#                     )
#                 }, 409

#             now = datetime.now()

#             # 1. Close the old room's detail row
#             cursor.execute("""
#                 UPDATE hotel_tblreservation_details
#                 SET is_current=0
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, from_room_id))

#             # 2. Open the new room's detail row (reuse it if the guest moved back to an earlier room)
#             cursor.execute("""
#                 SELECT id FROM hotel_tblreservation_details
#                 WHERE Reservation_ID=%s AND room_id=%s
#             """, (reservation_id, to_room_id))
#             if cursor.fetchone():
#                 cursor.execute("""
#                     UPDATE hotel_tblreservation_details
#                     SET is_current=1, is_active=1
#                     WHERE Reservation_ID=%s AND room_id=%s
#                 """, (reservation_id, to_room_id))
#             else:
#                 cursor.execute("""
#                     INSERT INTO hotel_tblreservation_details
#                         (Reservation_ID, room_id, is_current, created_at, is_active)
#                     VALUES (%s, %s, 1, %s, 1)
#                 """, (reservation_id, to_room_id, now))

#             # 3. Move the in-house guests to the new room
#             cursor.execute("""
#                 UPDATE hotel_tblinhouse_guests
#                 SET room_id=%s
#                 WHERE reservation_id=%s AND room_id=%s AND is_active=1
#             """, (to_room_id, reservation_id, from_room_id))
#             guests_moved = cursor.rowcount

#             # 4. Audit log
#             cursor.execute("""
#                 INSERT INTO hotel_tblroom_changes
#                     (reservation_id, from_room_id, to_room_id, reason, changed_at)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (reservation_id, from_room_id, to_room_id, reason, now))

#             results.append({
#                 "Reservation_ID": reservation_id,
#                 "from_room_id": from_room_id,
#                 "to_room_id": to_room_id,
#                 "guests_moved": guests_moved,
#                 "changed_at": now.strftime("%Y-%m-%d %H:%M:%S")
#             })

#         mydb.commit()
#         return jsonify({"message": "Room changed successfully", "results": results}), 200

#     except Exception as e:
#         if mydb:
#             try:
#                 mydb.rollback()
#             except Exception:
#                 pass
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


@app_file404.route("/GuestRoomChange", methods=["POST"])
@cross_origin()
def guest_room_change():
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

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- PAYLOAD VALIDATION --------
        json_data = request.get_json() or {}
        room_changes = json_data.get("room_changes", [])

        if not isinstance(room_changes, list) or not room_changes:
            return {"error": "Expected a non-empty list 'room_changes'."}, 400

        for item in room_changes:
            if not item.get("Reservation_ID") or not item.get("from_room_id") or not item.get("to_room_id"):
                return {"error": "Each item needs 'Reservation_ID', 'from_room_id' and 'to_room_id'."}, 400
            if str(item["from_room_id"]) == str(item["to_room_id"]):
                return {"error": "from_room_id and to_room_id cannot be the same."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        today = date.today()
        results = []

        for item in room_changes:
            reservation_id = item["Reservation_ID"]   # internal hotel_tblreservation.id
            from_room_id = item["from_room_id"]       # internal hotel_tblrooms.id
            to_room_id = item["to_room_id"]           # internal hotel_tblrooms.id
            reason = item.get("reason")

            # Reservation must exist, be active, have stay dates and still hold a room
            cursor.execute(f"""
                SELECT res.id, res.Current_Status, st.s AS start_date, st.e AS end_date,
                       (SELECT g.id
                        FROM hotel_tblguestreservation g
                        WHERE g.Reservation_ID = res.id AND g.is_active = 1
                        ORDER BY g.start_date DESC, g.id DESC
                        LIMIT 1) AS guest_reservation_id
                FROM hotel_tblreservation res
                JOIN ({STAY_SQ}) st ON st.Reservation_ID = res.id
                WHERE res.id = %s AND res.is_active = 1
            """, (reservation_id,))
            res = cursor.fetchone()
            if not res:
                mydb.rollback()
                return {"error": f"Reservation not found: {reservation_id}"}, 404
            if res["Current_Status"] not in ("Registered", "Reserved"):
                mydb.rollback()
                return {"error": f"Reservation {reservation_id} is {res['Current_Status']} and cannot change rooms."}, 400

            # Old room must exist
            cursor.execute("SELECT id FROM hotel_tblrooms WHERE id=%s", (from_room_id,))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": f"Room not found: {from_room_id}"}, 404

            # New room: locked so two simultaneous changes can't both take it
            cursor.execute("""
                SELECT id, room_no FROM hotel_tblrooms
                WHERE id=%s AND is_active=1
                FOR UPDATE
            """, (to_room_id,))
            to_row = cursor.fetchone()
            if not to_row:
                mydb.rollback()
                return {"error": f"Room not found: {to_room_id}"}, 404

            # The guest must currently be in the old room under this reservation
            cursor.execute("""
                SELECT id FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND room_id=%s AND is_current=1 AND is_active=1
            """, (reservation_id, from_room_id))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": f"Reservation {reservation_id} is not currently in room {from_room_id}."}, 400

            # -------- AVAILABILITY OF THE NEW ROOM FOR THE REST OF THE STAY --------
            stay_start = _to_date(res["start_date"])
            stay_end = _to_date(res["end_date"])
            window_start = max(stay_start, today)
            window_end = max(stay_end, window_start + timedelta(days=1))   # covers today at least

            conflict = find_room_conflict(
                cursor, to_room_id, reservation_id, window_start, window_end, today
            )
            if conflict:
                mydb.rollback()
                return {
                    "error": (
                        f"Room {to_row['room_no']} is not available from {window_start} to {stay_end}: "
                        f"reservation {conflict['reservation_id']} ({conflict['status']}) holds it "
                        f"from {conflict['start']} to {conflict['end']}."
                    )
                }, 409

            now = datetime.now()

            # 1. Close the old room's detail row
            cursor.execute("""
                UPDATE hotel_tblreservation_details
                SET is_current=0
                WHERE Reservation_ID=%s AND room_id=%s
            """, (reservation_id, from_room_id))

            # 2. Open the new room's detail row (reuse it if the guest moved back to an earlier room)
            cursor.execute("""
                SELECT id FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND room_id=%s
            """, (reservation_id, to_room_id))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE hotel_tblreservation_details
                    SET is_current=1, is_active=1
                    WHERE Reservation_ID=%s AND room_id=%s
                """, (reservation_id, to_room_id))
            else:
                cursor.execute("""
                    INSERT INTO hotel_tblreservation_details
                        (Reservation_ID, room_id, is_current, created_at, is_active)
                    VALUES (%s, %s, 1, %s, 1)
                """, (reservation_id, to_room_id, now))

            # 3. Move the in-house guests to the new room
            cursor.execute("""
                UPDATE hotel_tblinhouse_guests
                SET room_id=%s
                WHERE reservation_id=%s AND room_id=%s AND is_active=1
            """, (to_room_id, reservation_id, from_room_id))
            guests_moved = cursor.rowcount

            # 4. Audit log
            cursor.execute("""
                INSERT INTO hotel_tblroom_changes
                    (reservation_id, from_room_id, to_room_id, reason, changed_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (reservation_id, from_room_id, to_room_id, reason, now))

            # 5. Old room becomes Vacant Dirty (only if the guest was actually in it)
            old_room_dirty = False
            if res["Current_Status"] == "Registered":
                cursor.execute("""
                    INSERT INTO hotel_tblhousekeeping
                        (room_id, hk_date, hk_status, cleaned_at, cleaned_by, remarks)
                    VALUES (%s, %s, 'Dirty', NULL, NULL, %s)
                    ON DUPLICATE KEY UPDATE
                        hk_status = 'Dirty', cleaned_at = NULL,
                        cleaned_by = NULL, remarks = VALUES(remarks)
                """, (from_room_id, today, "Room change"))
                old_room_dirty = True

            results.append({
                "Reservation_ID": reservation_id,
                "GuestReservation_ID": res["guest_reservation_id"],
                "from_room_id": from_room_id,
                "to_room_id": to_room_id,
                "guests_moved": guests_moved,
                "old_room_marked_dirty": old_room_dirty,
                "changed_at": now.strftime("%Y-%m-%d %H:%M:%S")
            })

        mydb.commit()
        return jsonify({"message": "Room changed successfully", "results": results}), 200

    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
            except Exception:
                pass
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()