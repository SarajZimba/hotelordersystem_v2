# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# from root.auth.check import token_auth
# from datetime import datetime, date
# from dateutil.relativedelta import relativedelta

# app_file414 = Blueprint('app_file414', __name__)

# @app_file414.route("/revenue/seven-month", methods=["GET"])
# @cross_origin()
# def last_7_months_analytics():
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

#         now = datetime.now()
#         data = []

#         for i in range(6, -1, -1):  # last 7 months, old → current
#             month_date = now - relativedelta(months=i)
#             year = month_date.year
#             month = month_date.month

#             # -------- TOTAL REVENUE --------
#             revenue_query = """
#                 SELECT SUM(Total) AS total
#                 FROM hotel_tblhotelbills
#                 WHERE YEAR(Date) = %s AND MONTH(Date) = %s
#             """
#             cursor.execute(revenue_query, (year, month))
#             revenue = cursor.fetchone()["total"] or 0

#             # -------- TOTAL BOOKINGS --------
#             bookings_query = """
#                 SELECT COUNT(*) AS total
#                 FROM hotel_tblreservation
#                 WHERE YEAR(Reservation_Date) = %s AND MONTH(Reservation_Date) = %s
#             """
#             cursor.execute(bookings_query, (year, month))
#             bookings = cursor.fetchone()["total"]

#             data.append({
#                 "year": year,
#                 "month": month_date.strftime("%B"),
#                 "month_number": month,
#                 "total_revenue": round(float(revenue), 2),
#                 "total_bookings": bookings
#             })

#         mydb.close()

#         return jsonify({
#             "last_7_months": data
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

from root.auth.check import token_auth
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

app_file414 = Blueprint('app_file414', __name__)

@app_file414.route("/revenue/seven-month", methods=["GET"])
@cross_origin()
def last_7_months_analytics():
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

        now = datetime.now()
        data = []

        for i in range(6, -1, -1):  # last 7 months, old → current
            month_date = now - relativedelta(months=i)
            year = month_date.year
            month = month_date.month

            # -------- TOTAL REVENUE (for this outlet) --------
            revenue_query = """
                SELECT SUM(b.Total) AS total
                FROM hotel_tblhotelbills b
                JOIN hotel_tblreservation r ON b.reservationID = r.id
                WHERE YEAR(b.Date) = %s AND MONTH(b.Date) = %s AND r.outlet = %s
            """
            cursor.execute(revenue_query, (year, month, outlet))
            revenue = cursor.fetchone()["total"] or 0

            # -------- TOTAL BOOKINGS (for this outlet) --------
            bookings_query = """
                SELECT COUNT(*) AS total
                FROM hotel_tblreservation
                WHERE YEAR(Reservation_Date) = %s AND MONTH(Reservation_Date) = %s AND outlet = %s
            """
            cursor.execute(bookings_query, (year, month, outlet))
            bookings = cursor.fetchone()["total"]

            data.append({
                "year": year,
                "month": month_date.strftime("%B"),
                "month_number": month,
                "total_revenue": round(float(revenue), 2),
                "total_bookings": bookings
            })

        mydb.close()

        return jsonify({
            "outlet": outlet,
            "last_7_months": data
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500