# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# app_file413 = Blueprint('app_file413', __name__)
# from root.auth.check import token_auth
# from datetime import datetime, timedelta, date
# from dateutil.relativedelta import relativedelta

# @app_file413.route("/room-occupancy", methods=["GET"])
# @cross_origin()
# def room_occupancy():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- TARGET DATE (from query param, default today) --------
#         date_param = request.args.get("date")
#         if date_param:
#             try:
#                 today = datetime.strptime(date_param, "%Y-%m-%d").date()
#             except ValueError:
#                 return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
#         else:
#             today = date.today()

#         yesterday = today - timedelta(days=1)

#         # -------- TOTAL ROOMS --------
#         cursor.execute("SELECT COUNT(*) as total FROM hotel_tblrooms")
#         total_rooms = cursor.fetchone()["total"]

#         # -------- ACTIVE RESERVATIONS ON TARGET DATE --------
#         active_res_query = """
#             SELECT gr.Reservation_ID
#             FROM hotel_tblguestreservation gr
#             JOIN hotel_tblreservation r ON gr.Reservation_ID = r.id
#             WHERE gr.start_date <= %s
#               AND gr.end_date >= %s
#               AND r.Current_Status IN ('Reserved', 'Registered')
#         """
#         cursor.execute(active_res_query, (today, today))
#         active_reservations = cursor.fetchall()
#         reservation_ids = [row["Reservation_ID"] for row in active_reservations]

#         # -------- OCCUPIED ROOMS --------
#         occupied_rooms = 0
#         if reservation_ids:
#             format_strings = ','.join(['%s'] * len(reservation_ids))
#             occupied_query = f"""
#                 SELECT COUNT(DISTINCT room_id) as occupied
#                 FROM hotel_tblreservation_details
#                 WHERE Reservation_ID IN ({format_strings})
#                 AND is_current = TRUE
#             """
#             cursor.execute(occupied_query, tuple(reservation_ids))
#             occupied_rooms = cursor.fetchone()["occupied"]

#         # -------- VACANT ROOMS --------
#         vacant_rooms = total_rooms - occupied_rooms

#         # -------- OCCUPANCY RATE --------
#         occupancy_rate = 0
#         if total_rooms > 0:
#             occupancy_rate = round((occupied_rooms / total_rooms) * 100, 2)

#         # -------- RESERVATIONS MADE ON TARGET DATE --------
#         today_res_query = """
#             SELECT COUNT(*) as total
#             FROM hotel_tblreservation
#             WHERE Current_Status IN ('Reserved', 'Registered')
#             AND Reservation_Date = %s
#         """
#         cursor.execute(today_res_query, (today,))
#         today_reservations = cursor.fetchone()["total"]

#         # -------- REVENUE STATS (relative to target date) --------
#         # Target date's month revenue
#         current_month_query = """
#             SELECT SUM(Total) as total
#             FROM hotel_tblhotelbills
#             WHERE YEAR(Date) = %s AND MONTH(Date) = %s
#         """
#         cursor.execute(current_month_query, (today.year, today.month))
#         current_month_revenue = cursor.fetchone()["total"] or 0

#         # Month before target date's month
#         last_month = today - relativedelta(months=1)
#         last_month_query = """
#             SELECT SUM(Total) as total
#             FROM hotel_tblhotelbills
#             WHERE YEAR(Date) = %s AND MONTH(Date) = %s
#         """
#         cursor.execute(last_month_query, (last_month.year, last_month.month))
#         last_month_revenue = cursor.fetchone()["total"] or 0

#         # -------- TARGET DATE REVENUE --------
#         today_revenue_query = """
#             SELECT SUM(Total) as total
#             FROM hotel_tblhotelbills
#             WHERE Date = %s
#         """
#         cursor.execute(today_revenue_query, (today,))
#         today_revenue = cursor.fetchone()["total"] or 0

#         # -------- DAY BEFORE TARGET DATE REVENUE --------
#         yesterday_revenue_query = """
#             SELECT SUM(Total) as total
#             FROM hotel_tblhotelbills
#             WHERE Date = %s
#         """
#         cursor.execute(yesterday_revenue_query, (yesterday,))
#         yesterday_revenue = cursor.fetchone()["total"] or 0

#         mydb.close()

#         return jsonify({
#             "date": today.strftime("%Y-%m-%d"),
#             "room_stats": {
#                 "total_rooms": total_rooms,
#                 "occupied_rooms": occupied_rooms,
#                 "vacant_rooms": vacant_rooms,
#                 "occupancy_rate_percent": occupancy_rate
#             },
#             "reservation_stats": {
#                 "today_reservations": today_reservations
#             },
#             "revenue_stats": {
#                 "today": round(float(today_revenue), 2),
#                 "yesterday": round(float(yesterday_revenue), 2),
#                 "current_month": round(float(current_month_revenue), 2),
#                 "last_month": round(float(last_month_revenue), 2)
#             }
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500


# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# app_file413 = Blueprint('app_file413', __name__)
# from root.auth.check import token_auth
# from datetime import datetime, timedelta, date
# from dateutil.relativedelta import relativedelta

# @app_file413.route("/analytics/room-occupancy", methods=["POST"])
# @cross_origin()
# def room_occupancy():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True)

#         today = date.today()
#         now = datetime.now()

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

#         # -------- TOTAL ROOMS --------
#         cursor.execute("SELECT COUNT(*) as total FROM hotel_tblrooms")
#         total_rooms = cursor.fetchone()["total"]

#         # -------- ACTIVE RESERVATIONS TODAY --------
#         active_res_query = """
#             SELECT gr.Reservation_ID
#             FROM hotel_tblguestreservation gr
#             JOIN hotel_tblreservation r ON gr.Reservation_ID = r.id
#             WHERE gr.start_date <= %s
#               AND gr.end_date >= %s
#               AND r.Current_Status IN ('Reserved', 'Registered')
#         """
#         cursor.execute(active_res_query, (today, today))
#         active_reservations = cursor.fetchall()

#         reservation_ids = [row["Reservation_ID"] for row in active_reservations]

#         # -------- OCCUPIED ROOMS --------
#         occupied_rooms = 0

#         if reservation_ids:
#             format_strings = ','.join(['%s'] * len(reservation_ids))

#             occupied_query = f"""
#                 SELECT COUNT(DISTINCT room_id) as occupied
#                 FROM hotel_tblreservation_details
#                 WHERE Reservation_ID IN ({format_strings})
#                 AND is_current = TRUE
#             """
#             cursor.execute(occupied_query, tuple(reservation_ids))
#             occupied_rooms = cursor.fetchone()["occupied"]

#         # -------- VACANT ROOMS --------
#         vacant_rooms = total_rooms - occupied_rooms

#         # -------- OCCUPANCY RATE --------
#         occupancy_rate = 0
#         if total_rooms > 0:
#             occupancy_rate = round((occupied_rooms / total_rooms) * 100, 2)

#         # -------- TODAY RESERVATIONS --------
#         today_res_query = """
#             SELECT COUNT(*) as total
#             FROM hotel_tblreservation
#             WHERE Current_Status IN ('Reserved', 'Registered')
#             AND Reservation_Date = %s
#         """
#         cursor.execute(today_res_query, (today,))
#         today_reservations = cursor.fetchone()["total"]

#         # -------- REVENUE STATS --------
#         # Assuming your bill table = hotel_tblhotelbills
#         # and Date column is used for billing date

#         # Current month
#         current_month_query = """
#             SELECT SUM(Total) as total
#             FROM hotel_tblhotelbills
#             WHERE YEAR(Date) = %s AND MONTH(Date) = %s
#         """
#         cursor.execute(current_month_query, (now.year, now.month))
#         current_month_revenue = cursor.fetchone()["total"] or 0

#         # Last month
#         last_month = now - relativedelta(months=1)

#         last_month_query = """
#             SELECT SUM(Total) as total
#             FROM hotel_tblhotelbills
#             WHERE YEAR(Date) = %s AND MONTH(Date) = %s
#         """
#         cursor.execute(last_month_query, (last_month.year, last_month.month))
#         last_month_revenue = cursor.fetchone()["total"] or 0

#         mydb.close()

#         return jsonify({
#             "room_stats": {
#                 "total_rooms": total_rooms,
#                 "occupied_rooms": occupied_rooms,
#                 "vacant_rooms": vacant_rooms,
#                 "occupancy_rate_percent": occupancy_rate
#             },
#             "reservation_stats": {
#                 "today_reservations": today_reservations
#             },
#             "revenue_stats": {
#                 "current_month": round(float(current_month_revenue), 2),
#                 "last_month": round(float(last_month_revenue), 2)
#             }
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

app_file413 = Blueprint('app_file413', __name__)
from root.auth.check import token_auth
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

@app_file413.route("/room-occupancy", methods=["GET"])
@cross_origin()
def room_occupancy():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

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

        # -------- OUTLET (required, from query param) --------
        outlet = request.args.get("outlet")
        if not outlet:
            return {"error": "outlet is required"}, 400

        # -------- TARGET DATE (from query param, default today) --------
        date_param = request.args.get("date")
        if date_param:
            try:
                today = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
        else:
            today = date.today()

        yesterday = today - timedelta(days=1)

        # -------- TOTAL ROOMS (for this outlet) --------
        cursor.execute("SELECT COUNT(*) as total FROM hotel_tblrooms WHERE outlet = %s", (outlet,))
        total_rooms = cursor.fetchone()["total"]

        # -------- ACTIVE RESERVATIONS ON TARGET DATE (for this outlet) --------
        active_res_query = """
            SELECT gr.Reservation_ID
            FROM hotel_tblguestreservation gr
            JOIN hotel_tblreservation r ON gr.Reservation_ID = r.id
            WHERE gr.start_date <= %s
              AND gr.end_date >= %s
              AND r.Current_Status IN ('Reserved', 'Registered')
              AND r.outlet = %s
        """
        cursor.execute(active_res_query, (today, today, outlet))
        active_reservations = cursor.fetchall()
        reservation_ids = [row["Reservation_ID"] for row in active_reservations]

        # -------- OCCUPIED ROOMS --------
        occupied_rooms = 0
        if reservation_ids:
            format_strings = ','.join(['%s'] * len(reservation_ids))
            occupied_query = f"""
                SELECT COUNT(DISTINCT room_id) as occupied
                FROM hotel_tblreservation_details
                WHERE Reservation_ID IN ({format_strings})
                AND is_current = TRUE
            """
            cursor.execute(occupied_query, tuple(reservation_ids))
            occupied_rooms = cursor.fetchone()["occupied"]

        # -------- VACANT ROOMS --------
        vacant_rooms = total_rooms - occupied_rooms

        # -------- OCCUPANCY RATE --------
        occupancy_rate = 0
        if total_rooms > 0:
            occupancy_rate = round((occupied_rooms / total_rooms) * 100, 2)

        # -------- RESERVATIONS MADE ON TARGET DATE (for this outlet) --------
        today_res_query = """
            SELECT COUNT(*) as total
            FROM hotel_tblreservation
            WHERE Current_Status IN ('Reserved', 'Registered')
            AND Reservation_Date = %s
            AND outlet = %s
        """
        cursor.execute(today_res_query, (today, outlet))
        today_reservations = cursor.fetchone()["total"]

        # -------- REVENUE STATS (relative to target date, for this outlet) --------
        # Target date's month revenue
        current_month_query = """
            SELECT SUM(b.Total) as total
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE YEAR(b.Date) = %s AND MONTH(b.Date) = %s AND r.outlet = %s
        """
        cursor.execute(current_month_query, (today.year, today.month, outlet))
        current_month_revenue = cursor.fetchone()["total"] or 0

        # Month before target date's month
        last_month = today - relativedelta(months=1)
        last_month_query = """
            SELECT SUM(b.Total) as total
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE YEAR(b.Date) = %s AND MONTH(b.Date) = %s AND r.outlet = %s
        """
        cursor.execute(last_month_query, (last_month.year, last_month.month, outlet))
        last_month_revenue = cursor.fetchone()["total"] or 0

        # -------- TARGET DATE REVENUE --------
        today_revenue_query = """
            SELECT SUM(b.Total) as total
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE b.Date = %s AND r.outlet = %s
        """
        cursor.execute(today_revenue_query, (today, outlet))
        today_revenue = cursor.fetchone()["total"] or 0

        # -------- DAY BEFORE TARGET DATE REVENUE --------
        yesterday_revenue_query = """
            SELECT SUM(b.Total) as total
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE b.Date = %s AND r.outlet = %s
        """
        cursor.execute(yesterday_revenue_query, (yesterday, outlet))
        yesterday_revenue = cursor.fetchone()["total"] or 0

        mydb.close()

        return jsonify({
            "outlet": outlet,
            "date": today.strftime("%Y-%m-%d"),
            "room_stats": {
                "total_rooms": total_rooms,
                "occupied_rooms": occupied_rooms,
                "vacant_rooms": vacant_rooms,
                "occupancy_rate_percent": occupancy_rate
            },
            "reservation_stats": {
                "today_reservations": today_reservations
            },
            "revenue_stats": {
                "today": round(float(today_revenue), 2),
                "yesterday": round(float(yesterday_revenue), 2),
                "current_month": round(float(current_month_revenue), 2),
                "last_month": round(float(last_month_revenue), 2)
            }
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500