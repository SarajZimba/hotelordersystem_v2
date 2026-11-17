# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# from root.auth.check import token_auth
# from datetime import datetime, date
# from dateutil.relativedelta import relativedelta

# app_file484 = Blueprint('app_file484', __name__)

# @app_file484.route("/bill_details_summary", methods=["POST"])
# @cross_origin()
# def bill_details_summary():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         body = request.get_json() or {}

#         # -------- TOKEN --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         start_date = body.get("start_date")
#         end_date = body.get("end_date")
#         outlet = body.get("outlet")

#         if not start_date or not end_date:
#             return {"error": "start_date and end_date are required"}, 400

#         # -------- FETCH BILL DETAILS FOR BILLS IN RANGE --------
#         query = """
#             SELECT
#                 bd.id AS bill_detail_id,
#                 bd.bill_id,
#                 bd.Date,
#                 bd.RoomNumber,
#                 bd.RoomType,
#                 bd.RoomRate,
#                 bd.RoomRateName,
#                 bd.RateAmt,
#                 bd.MealPlan,
#                 bd.MealPlanAmt,
#                 bd.Amount,
#                 bd.Currency,
#                 bd.ExeRate,
#                 bd.AmountInclCurr,
#                 b.BillNo,
#                 b.Date AS BillDate,
#                 b.PaymentMode,
#                 b.DiscountAmt,
#                 r.outlet
#             FROM hotel_tblbilldetails bd
#             INNER JOIN hotel_tblhotelbills b ON bd.bill_id = b.id
#             INNER JOIN hotel_tblreservation r ON b.reservationID = r.id
#             WHERE DATE(b.Date) BETWEEN %s AND %s
#               AND b.status = 1
#         """
#         params = [start_date, end_date]

#         if outlet:
#             query += " AND r.outlet = %s"
#             params.append(outlet)

#         query += " ORDER BY b.Date ASC"

#         cursor.execute(query, tuple(params))
#         bill_details = cursor.fetchall()

#         # -------- ATTACH PARENT BILL'S DISCOUNT TO EACH ROW --------
#         for row in bill_details:
#             row["DiscountAmt"] = float(row["DiscountAmt"] or 0)

#         # -------- TOTALS --------
#         room_revenue_total = sum(float(row["RoomRate"] or 0) for row in bill_details)
#         meal_revenue_total = sum(float(row["MealPlanAmt"] or 0) for row in bill_details)

#         mydb.close()

#         return jsonify({
#             "outlet": outlet if outlet else "All",
#             "start_date": start_date,
#             "end_date": end_date,
#             "bill_details": bill_details,
#             "totals": {
#                 "Room Revenue": room_revenue_total,
#                 "Meal Plan Revenue": meal_revenue_total
#             }
#         }), 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
#         return {"error": str(e)}, 500

# @app_file484.route("/top_room_types", methods=["POST"])
# @cross_origin()
# def top_room_types():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         body = request.get_json() or {}

#         # -------- TOKEN --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         start_date = body.get("start_date")
#         end_date = body.get("end_date")
#         outlet = body.get("outlet")
#         limit = body.get("limit")

#         if not start_date or not end_date:
#             return {"error": "start_date and end_date are required"}, 400

#         # -------- AGGREGATE ROOM TYPE REVENUE FOR BILLS IN RANGE --------
#         query = """
#             SELECT
#                 bd.RoomType,
#                 SUM(bd.RoomRate) AS total_revenue,
#                 COUNT(*) AS room_nights_sold
#             FROM hotel_tblbilldetails bd
#             INNER JOIN hotel_tblhotelbills b ON bd.bill_id = b.id
#             INNER JOIN hotel_tblreservation r ON b.reservationID = r.id
#             WHERE DATE(b.Date) BETWEEN %s AND %s
#               AND b.status = 1
#         """
#         params = [start_date, end_date]

#         if outlet:
#             query += " AND r.outlet = %s"
#             params.append(outlet)

#         query += " GROUP BY bd.RoomType ORDER BY total_revenue DESC"

#         if limit:
#             query += " LIMIT %s"
#             params.append(int(limit))

#         cursor.execute(query, tuple(params))
#         room_types = cursor.fetchall()

#         for row in room_types:
#             row["total_revenue"] = float(row["total_revenue"] or 0)

#         mydb.close()

#         return jsonify({
#             "outlet": outlet if outlet else "All",
#             "start_date": start_date,
#             "end_date": end_date,
#             "top_room_types": room_types
#         }), 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
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

app_file484 = Blueprint('app_file484', __name__)

@app_file484.route("/bill_details_summary", methods=["POST"])
@cross_origin()
def bill_details_summary():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        body = request.get_json() or {}

        # -------- TOKEN --------
        token = body.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        start_date = body.get("start_date")
        end_date = body.get("end_date")
        outlet = body.get("outlet")

        if not start_date or not end_date:
            return {"error": "start_date and end_date are required"}, 400

        # -------- FETCH BILL DETAILS FOR BILLS IN RANGE --------
        query = """
            SELECT
                bd.id AS bill_detail_id,
                bd.bill_id,
                bd.Date,
                bd.RoomNumber,
                bd.RoomType,
                bd.RoomRate,
                bd.RoomRateName,
                bd.RateAmt,
                bd.MealPlan,
                bd.MealPlanAmt,
                bd.Amount,
                bd.Currency,
                bd.ExeRate,
                bd.AmountInclCurr,
                b.BillNo,
                b.Date AS BillDate,
                b.PaymentMode,
                b.DiscountAmt,
                r.outlet
            FROM hotel_tblbilldetails bd
            INNER JOIN hotel_tblhotelbills b ON bd.bill_id = b.id
            INNER JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE DATE(b.Date) BETWEEN %s AND %s
              AND b.status = 1
        """
        params = [start_date, end_date]

        if outlet:
            query += " AND r.outlet = %s"
            params.append(outlet)

        query += " ORDER BY b.Date ASC"

        cursor.execute(query, tuple(params))
        bill_details = cursor.fetchall()

        # -------- ATTACH PARENT BILL'S DISCOUNT TO EACH ROW --------
        for row in bill_details:
            row["DiscountAmt"] = float(row["DiscountAmt"] or 0)

        # -------- TOTALS --------
        room_revenue_total = sum(float(row["RoomRate"] or 0) for row in bill_details)
        meal_revenue_total = sum(float(row["MealPlanAmt"] or 0) for row in bill_details)

        mydb.close()

        return jsonify({
            "outlet": outlet if outlet else "All",
            "start_date": start_date,
            "end_date": end_date,
            "bill_details": bill_details,
            "totals": {
                "Room Revenue": room_revenue_total,
                "Meal Plan Revenue": meal_revenue_total
            }
        }), 200

    except Exception as e:
        try:
            mydb.close()
        except:
            pass
        return {"error": str(e)}, 500

@app_file484.route("/top_room_types", methods=["POST"])
@cross_origin()
def top_room_types():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        body = request.get_json() or {}

        # -------- TOKEN --------
        token = body.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        start_date = body.get("start_date")
        end_date = body.get("end_date")
        outlet = body.get("outlet")
        limit = body.get("limit")

        if not start_date or not end_date:
            return {"error": "start_date and end_date are required"}, 400

        # -------- AGGREGATE ROOM TYPE REVENUE FOR BILLS IN RANGE --------
        query = """
            SELECT
                bd.RoomType,
                SUM(bd.RoomRate) AS total_revenue,
                COUNT(*) AS room_nights_sold
            FROM hotel_tblbilldetails bd
            INNER JOIN hotel_tblhotelbills b ON bd.bill_id = b.id
            INNER JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE DATE(b.Date) BETWEEN %s AND %s
              AND b.status = 1
        """
        params = [start_date, end_date]

        if outlet:
            query += " AND r.outlet = %s"
            params.append(outlet)

        query += " GROUP BY bd.RoomType ORDER BY total_revenue DESC"

        if limit:
            query += " LIMIT %s"
            params.append(int(limit))

        cursor.execute(query, tuple(params))
        room_types = cursor.fetchall()

        for row in room_types:
            row["total_revenue"] = float(row["total_revenue"] or 0)

        mydb.close()

        return jsonify({
            "outlet": outlet if outlet else "All",
            "start_date": start_date,
            "end_date": end_date,
            "top_room_types": room_types
        }), 200

    except Exception as e:
        try:
            mydb.close()
        except:
            pass
        return {"error": str(e)}, 500