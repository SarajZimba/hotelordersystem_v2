from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

from root.auth.check import token_auth
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# app_file504 = Blueprint('app_file504', __name__)

# @app_file504.route("/noshowwalkincount", methods=["POST"])
# @cross_origin()
# def no_show_walk_in_count():
#     mydb = None
#     cursor = None
#     try:
#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token or not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- PAYLOAD --------
#         data = request.get_json() or {}
#         outlet = data.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required."}, 400

#         today = datetime.now().date()
#         try:
#             from_date = datetime.strptime(data["from_date"], "%Y-%m-%d").date() if data.get("from_date") else today
#             to_date = datetime.strptime(data["to_date"], "%Y-%m-%d").date() if data.get("to_date") else today
#         except ValueError:
#             return {"error": "Dates must be in YYYY-MM-DD format."}, 400
#         if from_date > to_date:
#             return {"error": "from_date cannot be after to_date."}, 400

#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- NO SHOWS: still Reserved, arrival date already passed --------
#         cursor.execute("""
#             SELECT COUNT(DISTINCT r.id) AS n
#             FROM hotel_tblreservation r
#             JOIN hotel_tblguestreservation gr
#               ON gr.Reservation_ID = r.id AND gr.is_active = 1
#             WHERE r.outlet = %s
#               AND r.is_active = 1
#               AND r.Current_Status = 'Reserved'
#               AND gr.start_date < %s
#               AND gr.start_date BETWEEN %s AND %s
#         """, (outlet, today, from_date, to_date))
#         no_shows = int(cursor.fetchone()["n"] or 0)

#         # -------- WALK-INS: booked and checked in on the same day --------
#         cursor.execute("""
#             SELECT COUNT(*) AS n
#             FROM hotel_tblreservation r
#             WHERE r.outlet = %s
#               AND r.is_active = 1
#               AND r.Check_In IS NOT NULL
#               AND DATE(r.Check_In) = r.Reservation_Date
#               AND DATE(r.Check_In) BETWEEN %s AND %s
#         """, (outlet, from_date, to_date))
#         walk_ins = int(cursor.fetchone()["n"] or 0)

#         return jsonify({
#             "outlet": outlet,
#             "from_date": str(from_date),
#             "to_date": str(to_date),
#             "no_show_reservations": no_shows,
#             "walk_in_reservations": walk_ins,
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400
#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()

app_file504 = Blueprint('app_file504', __name__)

@app_file504.route("/noshowwalkincount", methods=["POST"])
@cross_origin()
def no_show_walk_in_count():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- PAYLOAD --------
        data = request.get_json() or {}
        outlet = data.get("outlet")
        if not outlet:
            return {"error": "outlet is required."}, 400

        today = datetime.now().date()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- NO SHOWS: still Reserved, arrival date before today --------
        cursor.execute("""
            SELECT COUNT(DISTINCT r.id) AS n
            FROM hotel_tblreservation r
            JOIN hotel_tblguestreservation gr
              ON gr.Reservation_ID = r.id AND gr.is_active = 1
            WHERE r.outlet = %s
              AND r.is_active = 1
              AND r.Current_Status = 'Reserved'
              AND gr.start_date < %s
              AND (r.business_Src IS NULL OR LOWER(TRIM(r.business_Src)) NOT IN ('walk-in', 'walk in', 'walkin'))
        """, (outlet, today))
        no_shows = int(cursor.fetchone()["n"] or 0)

        # -------- WALK-INS: business source is Walk-in, checked in today --------
        cursor.execute("""
            SELECT COUNT(*) AS n
            FROM hotel_tblreservation r
            WHERE r.outlet = %s
              AND r.is_active = 1
              AND LOWER(TRIM(r.business_Src)) IN ('walk-in', 'walk in', 'walkin')
              AND r.Check_In IS NOT NULL
              AND DATE(r.Check_In) = %s
        """, (outlet, today))
        walk_ins = int(cursor.fetchone()["n"] or 0)

        return jsonify({
            "outlet": outlet,
            "date": str(today),
            "no_show_reservations": no_shows,
            "walk_in_reservations": walk_ins,
        }), 200

    except Exception as e:
        return {"error": str(e)}, 400
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()