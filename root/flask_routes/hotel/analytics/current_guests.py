# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# app_file411 = Blueprint('app_file411', __name__)
# from root.auth.check import token_auth
# from datetime import datetime, timedelta, date

# @app_file411.route("/analytics/current-guests", methods=["POST"])
# @cross_origin()
# def current_guests():
#     try:
#         # Connect to database
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Get input date from JSON payload
#         json_data = request.get_json() or {}
#         input_date = json_data.get("date", None)
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
#         if input_date:
#             try:
#                 filter_date = datetime.strptime(input_date, "%Y-%m-%d").date()
#             except ValueError:
#                 return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
#         else:
#             filter_date = datetime.today().date()

#         # Step 1️⃣: Get active guest reservations for that date
#         cursor.execute("""
#             SELECT gr.id as guest_reservation_id,
#                    gr.Reservation_ID,
#                    gr.No_of_children,
#                    gr.No_of_adults,
#                    gr.Likes,
#                    gr.Dislikes,
#                    gr.Guest_Notes,
#                    gr.start_date,
#                    gr.end_date,
#                    r.Current_Status,
#                    r.Guest_ID
#             FROM hotel_tblguestreservation gr
#             JOIN hotel_tblreservation r
#             ON gr.Reservation_ID = r.id
#             WHERE gr.start_date <= %s AND gr.end_date >= %s
#         """, (filter_date, filter_date))

#         guest_reservations = cursor.fetchall()
#         print("guest reservations", guest_reservations)
#         result = []

#         for guest in guest_reservations:
#             reservation_id = guest["Reservation_ID"]
#             guest_id = guest["Guest_ID"]


#             print("this is guest id", guest_id)
#             # Step 2️⃣: Fetch customer details
#             cursor.execute("""
#                 SELECT id, name, phone, email, address, customer_type
#                 FROM customers
#                 WHERE id = %s
#             """, (guest_id,))
#             customer = cursor.fetchone()

#             # Step 3️⃣: Fetch room numbers
#             cursor.execute("""
#                 SELECT rd.room_id, rm.room_no
#                 FROM hotel_tblreservation_details rd
#                 JOIN hotel_tblrooms rm
#                 ON rd.room_id = rm.id
#                 WHERE rd.Reservation_ID = %s AND rd.is_current = TRUE
#             """, (reservation_id,))
#             rooms = cursor.fetchall()
#             room_numbers = [r["room_no"] for r in rooms]

#             # Step 4️⃣: Calculate nights
#             nights = (guest["end_date"] - guest["start_date"]).days

#             result.append({
#                 "reservation_id": reservation_id,
#                 "guest_name": customer["name"] if customer else None,
#                 "contact_number": customer["phone"] if customer else None,
#                 "reservation_status": guest["Current_Status"],
#                 "arrival_date": guest["start_date"].strftime("%Y-%m-%d"),
#                 "departure_date": guest["end_date"].strftime("%Y-%m-%d"),
#                 "no_of_nights": nights,
#                 "room_numbers": room_numbers,
#                 "guest_notes": guest["Guest_Notes"]
#             })

#         mydb.close()

#         return jsonify({
#             "date": str(filter_date),
#             "current_guests_count": len(result),
#             "current_guests": result
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

app_file411 = Blueprint('app_file411', __name__)
from root.auth.check import token_auth
from datetime import datetime, timedelta, date

@app_file411.route("/analytics/current-guests", methods=["POST"])
@cross_origin()
def current_guests():
    try:
        # Connect to database
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Get input date/outlet from JSON payload
        json_data = request.get_json() or {}
        input_date = json_data.get("date", None)
        outlet = json_data.get("outlet", None)

        if not outlet:
            return jsonify({"error": "outlet is required."}), 400

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400
        if input_date:
            try:
                filter_date = datetime.strptime(input_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            filter_date = datetime.today().date()

        # Step 1️⃣: Get active guest reservations for that date, filtered by outlet
        cursor.execute("""
            SELECT gr.id as guest_reservation_id,
                   gr.Reservation_ID,
                   gr.No_of_children,
                   gr.No_of_adults,
                   gr.Likes,
                   gr.Dislikes,
                   gr.Guest_Notes,
                   gr.start_date,
                   gr.end_date,
                   r.Current_Status,
                   r.Guest_ID,
                   r.outlet
            FROM hotel_tblguestreservation gr
            JOIN hotel_tblreservation r
            ON gr.Reservation_ID = r.id
            WHERE gr.start_date <= %s AND gr.end_date >= %s
            AND r.outlet = %s
        """, (filter_date, filter_date, outlet))

        guest_reservations = cursor.fetchall()
        print("guest reservations", guest_reservations)
        result = []

        for guest in guest_reservations:
            reservation_id = guest["Reservation_ID"]
            guest_id = guest["Guest_ID"]

            print("this is guest id", guest_id)
            # Step 2️⃣: Fetch customer details
            cursor.execute("""
                SELECT id, name, phone, email, address, customer_type
                FROM customers
                WHERE id = %s
            """, (guest_id,))
            customer = cursor.fetchone()

            # Step 3️⃣: Fetch room numbers
            cursor.execute("""
                SELECT rd.room_id, rm.room_no
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblrooms rm
                ON rd.room_id = rm.id
                WHERE rd.Reservation_ID = %s AND rd.is_current = TRUE
            """, (reservation_id,))
            rooms = cursor.fetchall()
            room_numbers = [r["room_no"] for r in rooms]

            # Step 4️⃣: Calculate nights
            nights = (guest["end_date"] - guest["start_date"]).days

            result.append({
                "reservation_id": reservation_id,
                "guest_name": customer["name"] if customer else None,
                "contact_number": customer["phone"] if customer else None,
                "reservation_status": guest["Current_Status"],
                "outlet": guest["outlet"],
                "arrival_date": guest["start_date"].strftime("%Y-%m-%d"),
                "departure_date": guest["end_date"].strftime("%Y-%m-%d"),
                "no_of_nights": nights,
                "room_numbers": room_numbers,
                "guest_notes": guest["Guest_Notes"]
            })

        mydb.close()

        return jsonify({
            "date": str(filter_date),
            "outlet": outlet,
            "current_guests_count": len(result),
            "current_guests": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500