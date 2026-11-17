from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from collections import OrderedDict

load_dotenv()

app_file490 = Blueprint('app_file490', __name__)
from root.auth.check import token_auth


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )


def _fmt_dt(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def _is_national(nationality):
    return (nationality or "").strip().lower() == "nepal"


# @app_file490.route("/frontoffice/inhouse_guests", methods=["GET"])
# @cross_origin()
# def get_inhouse_guests():
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

#         # -------- PARAMS --------
#         outlet = request.args.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required."}, 400

#         room_no = request.args.get("room_no")          # optional exact room filter
#         search = (request.args.get("search") or "").strip()  # optional name / identity search
#         nationality = (request.args.get("nationality") or "").strip()  # optional
#         primary_only = request.args.get("primary_only") in ("1", "true", "True")

#         # -------- QUERY --------
#         query = """
#             SELECT
#                 g.idguest,
#                 g.reservation_id,
#                 r.reservation_outlet_id,
#                 g.room_id,
#                 rm.room_no,
#                 g.name,
#                 g.identity_type,
#                 g.identity_no,
#                 g.nationality,
#                 g.is_primary,
#                 g.checked_in_at
#             FROM hotel_tblinhouse_guests g
#             JOIN hotel_tblreservation r ON r.id = g.reservation_id
#             JOIN hotel_tblrooms rm      ON rm.id = g.room_id
#             WHERE g.is_active = 1
#               AND r.outlet = %s
#         """
#         params = [outlet]

#         if room_no:
#             query += " AND rm.room_no = %s"
#             params.append(room_no)

#         if search:
#             query += " AND (g.name LIKE %s OR g.identity_no LIKE %s)"
#             like = f"%{search}%"
#             params.extend([like, like])

#         if nationality:
#             query += " AND g.nationality = %s"
#             params.append(nationality)

#         if primary_only:
#             query += " AND g.is_primary = 1"

#         query += " ORDER BY rm.room_no, g.is_primary DESC, g.idguest"

#         mydb = get_db_connection()
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(query, params)
#         rows = cursor.fetchall()

#         # -------- BUILD RESPONSE --------
#         guests = []
#         rooms = OrderedDict()
#         national = 0
#         international = 0
#         primary_count = 0
#         reservation_ids = set()

#         for row in rows:
#             guest = {
#                 "idguest": row["idguest"],
#                 "name": row["name"],
#                 "identity_type": row["identity_type"],
#                 "identity_no": row["identity_no"],
#                 "nationality": row["nationality"],
#                 "is_primary": bool(row["is_primary"]),
#                 "reservation_id": row["reservation_id"],
#                 "reservation_outlet_id": row["reservation_outlet_id"],
#                 "room_id": row["room_id"],
#                 "room_no": row["room_no"],
#                 "checked_in_at": _fmt_dt(row["checked_in_at"]),
#             }
#             guests.append(guest)

#             key = row["room_id"]
#             if key not in rooms:
#                 rooms[key] = {
#                     "room_id": row["room_id"],
#                     "room_no": row["room_no"],
#                     "reservation_id": row["reservation_id"],
#                     "reservation_outlet_id": row["reservation_outlet_id"],
#                     "guests": [],
#                 }
#             rooms[key]["guests"].append(guest)

#             if _is_national(row["nationality"]):
#                 national += 1
#             else:
#                 international += 1
#             if row["is_primary"]:
#                 primary_count += 1
#             reservation_ids.add(row["reservation_id"])

#         return jsonify({
#             "outlet": outlet,
#             "summary": {
#                 "total_guests": len(guests),
#                 "occupied_rooms": len(rooms),
#                 "reservations": len(reservation_ids),
#                 "primary_guests": primary_count,
#                 "national_guests": national,
#                 "international_guests": international,
#             },
#             "rooms": list(rooms.values()),
#             "guests": guests,
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


# @app_file490.route("/frontoffice/inhouse_guests", methods=["GET"])
# @cross_origin()
# def get_inhouse_guests():
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

#         # -------- PARAMS --------
#         outlet = request.args.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required."}, 400

#         room_no = request.args.get("room_no")                          # optional exact room filter
#         search = (request.args.get("search") or "").strip()            # optional name / identity search
#         nationality = (request.args.get("nationality") or "").strip()  # optional
#         primary_only = request.args.get("primary_only") in ("1", "true", "True")

#         reservation_id = request.args.get("reservation_id")            # optional reservation filter
#         if reservation_id:
#             try:
#                 reservation_id = int(reservation_id)
#             except ValueError:
#                 return {"error": "reservation_id must be a number."}, 400

#         # -------- QUERY --------
#         query = """
#             SELECT
#                 g.idguest,
#                 g.reservation_id,
#                 r.reservation_outlet_id,
#                 g.room_id,
#                 rm.room_no,
#                 rm.room_type,
#                 rm.room_view,
#                 rm.preference,
#                 rm.phone_no,
#                 rm.room_notes,
#                 rm.room_image,
#                 rm.outlet_room_id,
#                 g.name,
#                 g.identity_type,
#                 g.identity_no,
#                 g.nationality,
#                 g.is_primary,
#                 g.checked_in_at
#             FROM hotel_tblinhouse_guests g
#             JOIN hotel_tblreservation r ON r.id = g.reservation_id
#             JOIN hotel_tblrooms rm      ON rm.id = g.room_id
#             WHERE g.is_active = 1
#               AND r.outlet = %s
#         """
#         params = [outlet]

#         if reservation_id:
#             query += " AND g.reservation_id = %s"
#             params.append(reservation_id)

#         if room_no:
#             query += " AND rm.room_no = %s"
#             params.append(room_no)

#         if search:
#             query += " AND (g.name LIKE %s OR g.identity_no LIKE %s)"
#             like = f"%{search}%"
#             params.extend([like, like])

#         if nationality:
#             query += " AND g.nationality = %s"
#             params.append(nationality)

#         if primary_only:
#             query += " AND g.is_primary = 1"

#         query += " ORDER BY rm.room_no, g.is_primary DESC, g.idguest"

#         mydb = get_db_connection()
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(query, params)
#         rows = cursor.fetchall()

#         # -------- BUILD RESPONSE --------
#         guests = []
#         rooms = OrderedDict()
#         room_details_by_id = {}
#         national = 0
#         international = 0
#         primary_count = 0
#         reservation_ids = set()

#         for row in rows:
#             room_id = row["room_id"]

#             # build each room's details once and share it
#             if room_id not in room_details_by_id:
#                 room_details_by_id[room_id] = {
#                     "room_id": room_id,
#                     "room_no": row["room_no"],
#                     "room_type": row["room_type"],
#                     "room_view": row["room_view"],
#                     "preference": row["preference"],
#                     "phone_no": row["phone_no"],
#                     "room_notes": row["room_notes"],
#                     "room_image": row["room_image"],
#                     "outlet_room_id": row["outlet_room_id"],
#                 }
#             room_details = room_details_by_id[room_id]

#             guest = {
#                 "idguest": row["idguest"],
#                 "name": row["name"],
#                 "identity_type": row["identity_type"],
#                 "identity_no": row["identity_no"],
#                 "nationality": row["nationality"],
#                 "is_primary": bool(row["is_primary"]),
#                 "reservation_id": row["reservation_id"],
#                 "reservation_outlet_id": row["reservation_outlet_id"],
#                 "room_id": room_id,
#                 "room_no": row["room_no"],
#                 "room": room_details,
#                 "checked_in_at": _fmt_dt(row["checked_in_at"]),
#             }
#             guests.append(guest)

#             if room_id not in rooms:
#                 rooms[room_id] = {
#                     "room_id": room_id,
#                     "room_no": row["room_no"],
#                     "room": room_details,
#                     "reservation_id": row["reservation_id"],
#                     "reservation_outlet_id": row["reservation_outlet_id"],
#                     "guests": [],
#                 }
#             rooms[room_id]["guests"].append(guest)

#             if _is_national(row["nationality"]):
#                 national += 1
#             else:
#                 international += 1
#             if row["is_primary"]:
#                 primary_count += 1
#             reservation_ids.add(row["reservation_id"])

#         return jsonify({
#             "outlet": outlet,
#             "summary": {
#                 "total_guests": len(guests),
#                 "occupied_rooms": len(rooms),
#                 "reservations": len(reservation_ids),
#                 "primary_guests": primary_count,
#                 "national_guests": national,
#                 "international_guests": international,
#             },
#             "rooms": list(rooms.values()),
#             "guests": guests,
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


# from collections import OrderedDict

# from flask import request, jsonify
# from flask_cors import cross_origin

# # Assumes app_file490, token_auth, get_db_connection, _fmt_dt and _is_national
# # already exist in your module.
# #
# # Needs these columns on hotel_tblinhouse_guests (added in the check-in change):
# #   meal_id, meal_mp, meal_rate, meal_currency


# @app_file490.route("/frontoffice/inhouse_guests", methods=["GET"])
# @cross_origin()
# def get_inhouse_guests():
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

#         # -------- PARAMS --------
#         outlet = request.args.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required."}, 400

#         room_no = request.args.get("room_no")                          # optional exact room filter
#         search = (request.args.get("search") or "").strip()            # optional name / identity search
#         nationality = (request.args.get("nationality") or "").strip()  # optional
#         primary_only = request.args.get("primary_only") in ("1", "true", "True")

#         reservation_id = request.args.get("reservation_id")            # optional reservation filter
#         if reservation_id:
#             try:
#                 reservation_id = int(reservation_id)
#             except ValueError:
#                 return {"error": "reservation_id must be a number."}, 400

#         # -------- QUERY --------
#         query = """
#             SELECT
#                 g.idguest,
#                 g.reservation_id,
#                 r.reservation_outlet_id,
#                 g.room_id,
#                 rm.room_no,
#                 rm.room_type,
#                 rm.room_view,
#                 rm.preference,
#                 rm.phone_no,
#                 rm.room_notes,
#                 rm.room_image,
#                 rm.outlet_room_id,
#                 g.name,
#                 g.identity_type,
#                 g.identity_no,
#                 g.nationality,
#                 g.is_primary,
#                 g.meal_id,
#                 g.meal_mp,
#                 g.meal_rate,
#                 g.meal_currency,
#                 g.checked_in_at
#             FROM hotel_tblinhouse_guests g
#             JOIN hotel_tblreservation r ON r.id = g.reservation_id
#             JOIN hotel_tblrooms rm      ON rm.id = g.room_id
#             WHERE g.is_active = 1
#               AND r.outlet = %s
#         """
#         params = [outlet]

#         if reservation_id:
#             query += " AND g.reservation_id = %s"
#             params.append(reservation_id)

#         if room_no:
#             query += " AND rm.room_no = %s"
#             params.append(room_no)

#         if search:
#             query += " AND (g.name LIKE %s OR g.identity_no LIKE %s)"
#             like = f"%{search}%"
#             params.extend([like, like])

#         if nationality:
#             query += " AND g.nationality = %s"
#             params.append(nationality)

#         if primary_only:
#             query += " AND g.is_primary = 1"

#         query += " ORDER BY rm.room_no, g.is_primary DESC, g.idguest"

#         mydb = get_db_connection()
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(query, params)
#         rows = cursor.fetchall()

#         # -------- BUILD RESPONSE --------
#         guests = []
#         rooms = OrderedDict()
#         room_details_by_id = {}
#         national = 0
#         international = 0
#         primary_count = 0
#         reservation_ids = set()

#         for row in rows:
#             room_id = row["room_id"]

#             # build each room's details once and share it
#             if room_id not in room_details_by_id:
#                 room_details_by_id[room_id] = {
#                     "room_id": room_id,
#                     "room_no": row["room_no"],
#                     "room_type": row["room_type"],
#                     "room_view": row["room_view"],
#                     "preference": row["preference"],
#                     "phone_no": row["phone_no"],
#                     "room_notes": row["room_notes"],
#                     "room_image": row["room_image"],
#                     "outlet_room_id": row["outlet_room_id"],
#                 }
#             room_details = room_details_by_id[room_id]

#             # meal plan chosen at check-in (null when none was selected)
#             meal_plan = None
#             if row["meal_id"] is not None:
#                 meal_plan = {
#                     "meal_id": row["meal_id"],
#                     "meal_plan": row["meal_mp"],
#                     "rate": float(row["meal_rate"]) if row["meal_rate"] is not None else None,
#                     "currency": row["meal_currency"],
#                 }

#             guest = {
#                 "idguest": row["idguest"],
#                 "name": row["name"],
#                 "identity_type": row["identity_type"],
#                 "identity_no": row["identity_no"],
#                 "nationality": row["nationality"],
#                 "is_primary": bool(row["is_primary"]),
#                 "reservation_id": row["reservation_id"],
#                 "reservation_outlet_id": row["reservation_outlet_id"],
#                 "room_id": room_id,
#                 "room_no": row["room_no"],
#                 "room": room_details,
#                 "meal_plan": meal_plan,
#                 "checked_in_at": _fmt_dt(row["checked_in_at"]),
#             }
#             guests.append(guest)

#             if room_id not in rooms:
#                 rooms[room_id] = {
#                     "room_id": room_id,
#                     "room_no": row["room_no"],
#                     "room": room_details,
#                     "reservation_id": row["reservation_id"],
#                     "reservation_outlet_id": row["reservation_outlet_id"],
#                     "guests": [],
#                 }
#             rooms[room_id]["guests"].append(guest)

#             if _is_national(row["nationality"]):
#                 national += 1
#             else:
#                 international += 1
#             if row["is_primary"]:
#                 primary_count += 1
#             reservation_ids.add(row["reservation_id"])

#         return jsonify({
#             "outlet": outlet,
#             "summary": {
#                 "total_guests": len(guests),
#                 "occupied_rooms": len(rooms),
#                 "reservations": len(reservation_ids),
#                 "primary_guests": primary_count,
#                 "national_guests": national,
#                 "international_guests": international,
#             },
#             "rooms": list(rooms.values()),
#             "guests": guests,
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


@app_file490.route("/frontoffice/inhouse_guests", methods=["GET"])
@cross_origin()
def get_inhouse_guests():
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

        # -------- PARAMS --------
        outlet = request.args.get("outlet")
        if not outlet:
            return {"error": "outlet is required."}, 400

        room_no = request.args.get("room_no")                          # optional exact room filter
        search = (request.args.get("search") or "").strip()            # optional name / identity search
        nationality = (request.args.get("nationality") or "").strip()  # optional
        primary_only = request.args.get("primary_only") in ("1", "true", "True")

        reservation_id = request.args.get("reservation_id")            # optional reservation filter
        if reservation_id:
            try:
                reservation_id = int(reservation_id)
            except ValueError:
                return {"error": "reservation_id must be a number."}, 400

        # -------- QUERY --------
        query = """
            SELECT
                g.idguest,
                g.reservation_id,
                r.reservation_outlet_id,
                st.s AS start_date,
                st.e AS end_date,
                g.room_id,
                rm.room_no,
                rm.room_type,
                rm.room_view,
                rm.preference,
                rm.phone_no,
                rm.room_notes,
                rm.room_image,
                rm.outlet_room_id,
                g.name,
                g.identity_type,
                g.identity_no,
                g.nationality,
                g.is_primary,
                g.meal_id,
                g.meal_mp,
                g.meal_rate,
                g.meal_currency,
                g.checked_in_at
            FROM hotel_tblinhouse_guests g
            JOIN hotel_tblreservation r ON r.id = g.reservation_id
            JOIN hotel_tblrooms rm      ON rm.id = g.room_id
            LEFT JOIN (
                SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
                FROM hotel_tblguestreservation
                WHERE is_active = 1
                GROUP BY Reservation_ID
            ) st ON st.Reservation_ID = r.id
            WHERE g.is_active = 1
              AND r.outlet = %s
        """
        params = [outlet]

        if reservation_id:
            query += " AND g.reservation_id = %s"
            params.append(reservation_id)

        if room_no:
            query += " AND rm.room_no = %s"
            params.append(room_no)

        if search:
            query += " AND (g.name LIKE %s OR g.identity_no LIKE %s)"
            like = f"%{search}%"
            params.extend([like, like])

        if nationality:
            query += " AND g.nationality = %s"
            params.append(nationality)

        if primary_only:
            query += " AND g.is_primary = 1"

        query += " ORDER BY rm.room_no, g.is_primary DESC, g.idguest"

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # -------- BUILD RESPONSE --------
        guests = []
        rooms = OrderedDict()
        room_details_by_id = {}
        national = 0
        international = 0
        primary_count = 0
        reservation_ids = set()

        for row in rows:
            room_id = row["room_id"]
            start_date = str(row["start_date"]) if row["start_date"] else None
            end_date = str(row["end_date"]) if row["end_date"] else None

            # build each room's details once and share it
            if room_id not in room_details_by_id:
                room_details_by_id[room_id] = {
                    "room_id": room_id,
                    "room_no": row["room_no"],
                    "room_type": row["room_type"],
                    "room_view": row["room_view"],
                    "preference": row["preference"],
                    "phone_no": row["phone_no"],
                    "room_notes": row["room_notes"],
                    "room_image": row["room_image"],
                    "outlet_room_id": row["outlet_room_id"],
                }
            room_details = room_details_by_id[room_id]

            # meal plan chosen at check-in (null when none was selected)
            meal_plan = None
            if row["meal_id"] is not None:
                meal_plan = {
                    "meal_id": row["meal_id"],
                    "meal_plan": row["meal_mp"],
                    "rate": float(row["meal_rate"]) if row["meal_rate"] is not None else None,
                    "currency": row["meal_currency"],
                }

            guest = {
                "idguest": row["idguest"],
                "name": row["name"],
                "identity_type": row["identity_type"],
                "identity_no": row["identity_no"],
                "nationality": row["nationality"],
                "is_primary": bool(row["is_primary"]),
                "reservation_id": row["reservation_id"],
                "reservation_outlet_id": row["reservation_outlet_id"],
                "start_date": start_date,
                "end_date": end_date,
                "room_id": room_id,
                "room_no": row["room_no"],
                "room": room_details,
                "meal_plan": meal_plan,
                "checked_in_at": _fmt_dt(row["checked_in_at"]),
            }
            guests.append(guest)

            if room_id not in rooms:
                rooms[room_id] = {
                    "room_id": room_id,
                    "room_no": row["room_no"],
                    "room": room_details,
                    "reservation_id": row["reservation_id"],
                    "reservation_outlet_id": row["reservation_outlet_id"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "guests": [],
                }
            rooms[room_id]["guests"].append(guest)

            if _is_national(row["nationality"]):
                national += 1
            else:
                international += 1
            if row["is_primary"]:
                primary_count += 1
            reservation_ids.add(row["reservation_id"])

        return jsonify({
            "outlet": outlet,
            "summary": {
                "total_guests": len(guests),
                "occupied_rooms": len(rooms),
                "reservations": len(reservation_ids),
                "primary_guests": primary_count,
                "national_guests": national,
                "international_guests": international,
            },
            "rooms": list(rooms.values()),
            "guests": guests,
        }), 200

    except Exception as e:
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()