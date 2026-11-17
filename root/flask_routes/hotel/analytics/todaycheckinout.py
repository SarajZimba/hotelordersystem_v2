# def get_db_connection():
#     return mysql.connector.connect(
#         host=os.getenv("host"),
#         user=os.getenv("user"),
#         password=os.getenv("password"),
#         database=os.getenv("database")
#     )

# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from datetime import datetime, timedelta, date


# from collections import defaultdict
# load_dotenv()

# app_file410 = Blueprint('app_file410', __name__)
# from root.auth.check import token_auth
# @app_file410.route("/analytics/today-checkin-checkout-details", methods=["GET"])
# @cross_origin()
# def today_checkin_checkout_details():
#     try:
#         mydb = get_db_connection()
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

#         today_str = datetime.now().strftime("%Y-%m-%d")
#         start_of_day = f"{today_str} 00:00:00"
#         end_of_day = f"{today_str} 23:59:59"

#         # -------- CHECK-INS --------
#         checkin_query = """
#             SELECT r.*, c.id AS cust_id, c.name, c.phone, c.email, c.address, c.customer_type
#             FROM hotel_tblreservation r
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.Current_Status = 'Registered'
#             AND r.Check_In BETWEEN %s AND %s
#         """
#         cursor.execute(checkin_query, (start_of_day, end_of_day))
#         checkins = cursor.fetchall()

#         checkins_data = []
#         for obj in checkins:
#             checkins_data.append({
#                 "reservation_id": obj["id"],
#                 "customer": {
#                     "id": obj["cust_id"],
#                     "name": obj["name"],
#                     "contact_number": obj["phone"],
#                     "email": obj["email"],
#                     "address": obj["address"],
#                     "customer_type": obj["customer_type"],
#                 },
#                 "pay_mode": obj["Pay_Mode"],
#                 "reservation_type": obj["Reservation_type"],
#                 "market_segment": obj["Market_Seg"],
#                 "business_source": obj["business_Src"],
#                 "advance_payment": float(obj["Advance_Payment"]) if obj["Advance_Payment"] else None,
#                 "check_in_time": obj["Check_In"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_In"] else None,
#                 "check_out_time": obj["Check_Out"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_Out"] else None
#             })

#         # -------- Checked OutS --------
#         checkout_query = """
#             SELECT r.*, c.id AS cust_id, c.name, c.phone, c.email, c.address, c.customer_type
#             FROM hotel_tblreservation r
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.Current_Status = 'Checked Out'
#             AND r.Check_Out BETWEEN %s AND %s
#         """
#         cursor.execute(checkout_query, (start_of_day, end_of_day))
#         checkouts = cursor.fetchall()

#         checkouts_data = []
#         for obj in checkouts:
#             checkouts_data.append({
#                 "reservation_id": obj["id"],
#                 "customer": {
#                     "id": obj["cust_id"],
#                     "name": obj["name"],
#                     "contact_number": obj["contact_number"],
#                     "email": obj["email"],
#                     "address": obj["address"],
#                     "customer_type": obj["customer_type"],
#                 },
#                 "pay_mode": obj["Pay_Mode"],
#                 "reservation_type": obj["Reservation_type"],
#                 "market_segment": obj["Market_Seg"],
#                 "business_source": obj["business_Src"],
#                 "advance_payment": float(obj["Advance_Payment"]) if obj["Advance_Payment"] else None,
#                 "check_in_time": obj["Check_In"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_In"] else None,
#                 "check_out_time": obj["Check_Out"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_Out"] else None
#             })
 
#         mydb.close()

#         return jsonify({
#             "date": today_str,
#             "checkin": {
#                 "count": len(checkins),
#                 "data": checkins_data
#             },
#             "checkout": {
#                 "count": len(checkouts),
#                 "data": checkouts_data
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date


from collections import defaultdict
load_dotenv()

app_file410 = Blueprint('app_file410', __name__)
from root.auth.check import token_auth
# @app_file410.route("/analytics/today-checkin-checkout-details", methods=["GET"])
# @cross_origin()
# def today_checkin_checkout_details():
#     try:
#         mydb = get_db_connection()
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

#         today_str = datetime.now().strftime("%Y-%m-%d")
#         start_of_day = f"{today_str} 00:00:00"
#         end_of_day = f"{today_str} 23:59:59"

#         # -------- CHECK-INS --------
#         checkin_query = """
#             SELECT r.*, c.id AS cust_id, c.name, c.phone, c.email, c.address, c.customer_type
#             FROM hotel_tblreservation r
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.Current_Status = 'Registered'
#             AND r.Check_In BETWEEN %s AND %s
#         """
#         cursor.execute(checkin_query, (start_of_day, end_of_day))
#         checkins = cursor.fetchall()

#         checkins_data = []
#         for obj in checkins:
#             checkins_data.append({
#                 "reservation_id": obj["id"],
#                 "customer": {
#                     "id": obj["cust_id"],
#                     "name": obj["name"],
#                     "contact_number": obj["phone"],
#                     "email": obj["email"],
#                     "address": obj["address"],
#                     "customer_type": obj["customer_type"],
#                 },
#                 "pay_mode": obj["Pay_Mode"],
#                 "reservation_type": obj["Reservation_type"],
#                 "market_segment": obj["Market_Seg"],
#                 "business_source": obj["business_Src"],
#                 "advance_payment": float(obj["Advance_Payment"]) if obj["Advance_Payment"] else None,
#                 "check_in_time": obj["Check_In"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_In"] else None,
#                 "check_out_time": obj["Check_Out"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_Out"] else None
#             })

#         # -------- Checked OutS --------
#         checkout_query = """
#             SELECT r.*, c.id AS cust_id, c.name, c.phone, c.email, c.address, c.customer_type
#             FROM hotel_tblreservation r
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.Current_Status = 'Checked Out'
#             AND r.Check_Out BETWEEN %s AND %s
#         """
#         cursor.execute(checkout_query, (start_of_day, end_of_day))
#         checkouts = cursor.fetchall()

#         checkouts_data = []
#         for obj in checkouts:
#             checkouts_data.append({
#                 "reservation_id": obj["id"],
#                 "customer": {
#                     "id": obj["cust_id"],
#                     "name": obj["name"],
#                     "contact_number": obj["contact_number"],
#                     "email": obj["email"],
#                     "address": obj["address"],
#                     "customer_type": obj["customer_type"],
#                 },
#                 "pay_mode": obj["Pay_Mode"],
#                 "reservation_type": obj["Reservation_type"],
#                 "market_segment": obj["Market_Seg"],
#                 "business_source": obj["business_Src"],
#                 "advance_payment": float(obj["Advance_Payment"]) if obj["Advance_Payment"] else None,
#                 "check_in_time": obj["Check_In"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_In"] else None,
#                 "check_out_time": obj["Check_Out"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_Out"] else None
#             })
 
#         mydb.close()

#         return jsonify({
#             "date": today_str,
#             "checkin": {
#                 "count": len(checkins),
#                 "data": checkins_data
#             },
#             "checkout": {
#                 "count": len(checkouts),
#                 "data": checkouts_data
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app_file410.route("/analytics/today-checkin-checkout-details", methods=["GET"])
@cross_origin()
def today_checkin_checkout_details():
    try:
        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True, buffered=True)

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

        # -------- OUTLET (required, from query param) --------
        outlet = request.args.get("outlet")
        if not outlet:
            return {"error": "outlet is required"}, 400

        today_str = datetime.now().strftime("%Y-%m-%d")
        start_of_day = f"{today_str} 00:00:00"
        end_of_day = f"{today_str} 23:59:59"

        # -------- CHECK-INS --------
        checkin_query = """
            SELECT r.*, c.id AS cust_id, c.name, c.phone, c.email, c.address, c.customer_type
            FROM hotel_tblreservation r
            LEFT JOIN customers c ON r.Guest_ID = c.id
            WHERE r.Current_Status = 'Registered'
            AND r.Check_In BETWEEN %s AND %s
            AND r.outlet = %s
        """
        cursor.execute(checkin_query, (start_of_day, end_of_day, outlet))
        checkins = cursor.fetchall()

        checkins_data = []
        for obj in checkins:
            checkins_data.append({
                "reservation_id": obj["id"],
                "customer": {
                    "id": obj["cust_id"],
                    "name": obj["name"],
                    "contact_number": obj["phone"],
                    "email": obj["email"],
                    "address": obj["address"],
                    "customer_type": obj["customer_type"],
                },
                "pay_mode": obj["Pay_Mode"],
                "reservation_type": obj["Reservation_type"],
                "market_segment": obj["Market_Seg"],
                "business_source": obj["business_Src"],
                "advance_payment": float(obj["Advance_Payment"]) if obj["Advance_Payment"] else None,
                "check_in_time": obj["Check_In"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_In"] else None,
                "check_out_time": obj["Check_Out"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_Out"] else None
            })

        # -------- Checked OutS --------
        checkout_query = """
            SELECT r.*, c.id AS cust_id, c.name, c.phone, c.email, c.address, c.customer_type
            FROM hotel_tblreservation r
            LEFT JOIN customers c ON r.Guest_ID = c.id
            WHERE r.Current_Status = 'Checked Out'
            AND r.Check_Out BETWEEN %s AND %s
            AND r.outlet = %s
        """
        cursor.execute(checkout_query, (start_of_day, end_of_day, outlet))
        checkouts = cursor.fetchall()

        checkouts_data = []
        for obj in checkouts:
            checkouts_data.append({
                "reservation_id": obj["id"],
                "customer": {
                    "id": obj["cust_id"],
                    "name": obj["name"],
                    "contact_number": obj["phone"],
                    "email": obj["email"],
                    "address": obj["address"],
                    "customer_type": obj["customer_type"],
                },
                "pay_mode": obj["Pay_Mode"],
                "reservation_type": obj["Reservation_type"],
                "market_segment": obj["Market_Seg"],
                "business_source": obj["business_Src"],
                "advance_payment": float(obj["Advance_Payment"]) if obj["Advance_Payment"] else None,
                "check_in_time": obj["Check_In"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_In"] else None,
                "check_out_time": obj["Check_Out"].strftime("%d-%m-%Y %I:%M %p") if obj["Check_Out"] else None
            })
 
        mydb.close()

        return jsonify({
            "outlet": outlet,
            "date": today_str,
            "checkin": {
                "count": len(checkins),
                "data": checkins_data
            },
            "checkout": {
                "count": len(checkouts),
                "data": checkouts_data
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500