# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# from root.auth.check import token_auth
# from datetime import datetime, date
# from dateutil.relativedelta import relativedelta

# app_file482 = Blueprint('app_file482', __name__)

# import calendar
# from datetime import date, datetime, timedelta
# import requests

# def _same_day_last_month(target_date):
#     year, month = target_date.year, target_date.month - 1
#     if month == 0:
#         month, year = 12, year - 1
#     last_day = calendar.monthrange(year, month)[1]
#     return date(year, month, min(target_date.day, last_day))

# def _same_day_last_year(target_date):
#     try:
#         return target_date.replace(year=target_date.year - 1)
#     except ValueError:
#         # Feb 29 -> Feb 28 fallback
#         return date(target_date.year - 1, 2, 28)

# # def _get_front_office_block(cursor, outlet, target_date):
# #     # -------- BASE AGGREGATES --------
# #     cursor.execute("""
# #         SELECT
# #             COALESCE(SUM(b.subTotal), 0) AS total_sale,
# #             COALESCE(SUM(b.subTotal - b.DiscountAmt), 0) AS total_net_sale,
# #             COALESCE(SUM(b.VAT), 0) AS vat,
# #             COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
# #             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
# #             COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #     """, (target_date, outlet))
# #     base = cursor.fetchone()

# #     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
# #     cursor.execute("""
# #         SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #           AND LOWER(TRIM(b.PaymentMode)) != 'split'
# #         GROUP BY LOWER(TRIM(b.PaymentMode))
# #     """, (target_date, outlet))
# #     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

# #     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
# #     cursor.execute("""
# #         SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
# #         FROM hotel_tblbillpayments p
# #         JOIN hotel_tblhotelbills b ON p.bill_id = b.id
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #           AND LOWER(TRIM(b.PaymentMode)) = 'split'
# #         GROUP BY LOWER(TRIM(p.PaymentMode))
# #     """, (target_date, outlet))
# #     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

# #     def mode_total(*names):
# #         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

# #     return {
# #         "Total Sale": float(base["total_sale"]),
# #         "Total Net Sale": float(base["total_net_sale"]),
# #         "Service Charge": 0,
# #         "VAT": float(base["vat"]),
# #         "Room Revenue": float(base["room_revenue"]),
# #         "Cash": mode_total("cash"),
# #         "Credit Card": mode_total("card"),
# #         "Mobile Payment": mode_total("mobile"),
# #         "Credit": mode_total("credit"),
# #         "Discount": float(base["discount"]),
# #         "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
# #     }

# # def _get_front_office_block(cursor, outlet, target_date):
# #     # -------- BASE AGGREGATES --------
# #     cursor.execute("""
# #         SELECT
# #             COALESCE(SUM(b.subTotal), 0) AS total_sale,
# #             COALESCE(SUM(b.subTotal - b.DiscountAmt - b.VAT), 0) AS total_net_sale,
# #             COALESCE(SUM(b.VAT), 0) AS vat,
# #             COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
# #             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
# #             COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #     """, (target_date, outlet))
# #     base = cursor.fetchone()

# #     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
# #     cursor.execute("""
# #         SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #           AND LOWER(TRIM(b.PaymentMode)) != 'split'
# #         GROUP BY LOWER(TRIM(b.PaymentMode))
# #     """, (target_date, outlet))
# #     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

# #     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
# #     cursor.execute("""
# #         SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
# #         FROM hotel_tblbillpayments p
# #         JOIN hotel_tblhotelbills b ON p.bill_id = b.id
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #           AND LOWER(TRIM(b.PaymentMode)) = 'split'
# #         GROUP BY LOWER(TRIM(p.PaymentMode))
# #     """, (target_date, outlet))
# #     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

# #     def mode_total(*names):
# #         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

# #     # -------- GUEST COUNT (for revenue-per-guest) --------
# #     cursor.execute("""
# #         SELECT COALESCE(SUM(gr.No_of_adults + gr.No_of_children), 0) AS total_guests
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         JOIN hotel_tblguestreservation gr ON gr.Reservation_ID = r.id AND gr.is_active = 1
# #         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
# #     """, (target_date, outlet))
# #     guest_row = cursor.fetchone()
# #     total_guests = int(guest_row["total_guests"] or 0)

# #     total_sale = float(base["total_sale"])
# #     revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

# #     return {
# #         "Total Sale": total_sale,
# #         "Total Net Sale": float(base["total_net_sale"]),
# #         "Service Charge": 0,
# #         "VAT": float(base["vat"]),
# #         "Room Revenue": float(base["room_revenue"]),
# #         "Cash": mode_total("cash"),
# #         "Credit Card": mode_total("card"),
# #         "Mobile Payment": mode_total("mobile"),
# #         "Credit": mode_total("credit"),
# #         "Discount": float(base["discount"]),
# #         "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
# #         "Total Guests": total_guests,
# #         "Revenue Per Guest": revenue_per_guest,
# #     }


# def _get_front_office_block(cursor, outlet, target_date):
#     # -------- BASE AGGREGATES --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.subTotal + b.DiscountAmt + b.VAT), 0) AS total_sale,
#             COALESCE(SUM(b.subTotal - b.DiscountAmt - b.VAT), 0) AS total_net_sale,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
#             COALESCE(SUM(b.MealplanRevenue), 0) AS mealplan_revenue,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#     """, (target_date, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(b.PaymentMode))
#     """, (target_date, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
#         FROM hotel_tblbillpayments p
#         JOIN hotel_tblhotelbills b ON p.bill_id = b.id
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(p.PaymentMode))
#     """, (target_date, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     # -------- GUEST COUNT (for revenue-per-guest) --------
#     cursor.execute("""
#         SELECT COALESCE(SUM(gr.No_of_adults + gr.No_of_children), 0) AS total_guests
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         JOIN hotel_tblguestreservation gr ON gr.Reservation_ID = r.id AND gr.is_active = 1
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#     """, (target_date, outlet))
#     guest_row = cursor.fetchone()
#     total_guests = int(guest_row["total_guests"] or 0)

#     total_sale = float(base["total_sale"])
#     revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

#     return {
#         "Total Sale": total_sale,
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": 0,
#         "VAT": float(base["vat"]),
#         "Room Revenue": float(base["room_revenue"]),
#         "Mealplan Revenue": float(base["mealplan_revenue"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("card"),
#         "Mobile Payment": mode_total("mobile"),
#         "Credit": mode_total("credit"),
#         "Discount": float(base["discount"]),
#         "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
#         "Total Guests": total_guests,
#         "Revenue Per Guest": revenue_per_guest,
#     }

# from datetime import datetime, date, timedelta
# @app_file482.route("/front_office_sales", methods=["POST"])
# @cross_origin()
# def front_office_sales():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # -------- INPUT (from body) --------
#         body = request.get_json() or {}

#         # -------- TOKEN (from body) --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         outlet = body.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required"}, 400

#         date_param = body.get("date")
#         if date_param:
#             today = datetime.strptime(date_param, "%Y-%m-%d").date()
#         else:
#             today = date.today()

#         last_year_date = _same_day_last_year(today)
#         last_month_date = _same_day_last_month(today)

#         result = {
#             "today": {
#                 "date": today.strftime("%Y-%m-%d"),
#                 **_get_front_office_block(cursor, outlet, today)
#             },
#             "same_day_last_year": {
#                 "date": last_year_date.strftime("%Y-%m-%d"),
#                 **_get_front_office_block(cursor, outlet, last_year_date)
#             },
#             "same_day_last_month": {
#                 "date": last_month_date.strftime("%Y-%m-%d"),
#                 **_get_front_office_block(cursor, outlet, last_month_date)
#             },
#         }

#         mydb.close()
#         return jsonify({"outlet": outlet, **result}), 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
#         return {"error": str(e)}, 500


# # def _get_front_office_block_range(cursor, outlet, start_date, end_date):
# #     # -------- BASE AGGREGATES --------
# #     cursor.execute("""
# #         SELECT
# #             COALESCE(SUM(b.subTotal), 0) AS total_sale,
# #             COALESCE(SUM(b.subTotal - b.DiscountAmt), 0) AS total_net_sale,
# #             COALESCE(SUM(b.VAT), 0) AS vat,
# #             COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
# #             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
# #             COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
# #     """, (start_date, end_date, outlet))
# #     base = cursor.fetchone()

# #     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
# #     cursor.execute("""
# #         SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
# #         FROM hotel_tblhotelbills b
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
# #           AND LOWER(TRIM(b.PaymentMode)) != 'split'
# #         GROUP BY LOWER(TRIM(b.PaymentMode))
# #     """, (start_date, end_date, outlet))
# #     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

# #     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
# #     cursor.execute("""
# #         SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
# #         FROM hotel_tblbillpayments p
# #         JOIN hotel_tblhotelbills b ON p.bill_id = b.id
# #         JOIN hotel_tblreservation r ON b.reservationID = r.id
# #         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
# #           AND LOWER(TRIM(b.PaymentMode)) = 'split'
# #         GROUP BY LOWER(TRIM(p.PaymentMode))
# #     """, (start_date, end_date, outlet))
# #     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

# #     def mode_total(*names):
# #         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

# #     return {
# #         "Total Sale": float(base["total_sale"]),
# #         "Total Net Sale": float(base["total_net_sale"]),
# #         "Service Charge": 0,
# #         "VAT": float(base["vat"]),
# #         "Room Revenue": float(base["room_revenue"]),
# #         "Cash": mode_total("cash"),
# #         "Credit Card": mode_total("card"),
# #         "Mobile Payment": mode_total("mobile"),
# #         "Credit": mode_total("credit"),
# #         "Discount": float(base["discount"]),
# #         "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
# #     }


# def _get_front_office_block_range(cursor, outlet, start_date, end_date):
#     # -------- BASE AGGREGATES --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.subTotal), 0) AS total_sale,
#             COALESCE(SUM(b.subTotal - b.DiscountAmt), 0) AS total_net_sale,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
#             COALESCE(SUM(b.MealplanRevenue), 0) AS mealplan_revenue,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
#     """, (start_date, end_date, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(b.PaymentMode))
#     """, (start_date, end_date, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
#         FROM hotel_tblbillpayments p
#         JOIN hotel_tblhotelbills b ON p.bill_id = b.id
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(p.PaymentMode))
#     """, (start_date, end_date, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     # -------- GUEST COUNT (for revenue-per-guest) --------
#     cursor.execute("""
#         SELECT COALESCE(SUM(gr.No_of_adults + gr.No_of_children), 0) AS total_guests
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         JOIN hotel_tblguestreservation gr ON gr.Reservation_ID = r.id AND gr.is_active = 1
#         WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
#     """, (start_date, end_date, outlet))
#     guest_row = cursor.fetchone()
#     total_guests = int(guest_row["total_guests"] or 0)

#     room_revenue = float(base["room_revenue"])
#     total_sale = float(base["total_sale"])
#     revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

#     return {
#         "Total Sale": total_sale,
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": 0,
#         "VAT": float(base["vat"]),
#         "Room Revenue": room_revenue,
#         "Mealplan Revenue": float(base["mealplan_revenue"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("card"),
#         "Mobile Payment": mode_total("mobile"),
#         "Credit": mode_total("credit"),
#         "Discount": float(base["discount"]),
#         "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
#         "Total Guests": total_guests,
#         "Revenue Per Guest": revenue_per_guest,
#     }

# @app_file482.route("/front_office_sales_range", methods=["POST"])
# @cross_origin()
# def front_office_sales_range():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         body = request.get_json() or {}

#         # -------- TOKEN (from body) --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         outlet = body.get("outlet", "Thamel")
#         per_day = bool(body.get("per_day", False))

#         start_date_str = body.get("start_date")
#         end_date_str = body.get("end_date")

#         if not start_date_str or not end_date_str:
#             return {"error": "start_date and end_date are required"}, 400

#         try:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

#         if start_date > end_date:
#             return {"error": "start_date must be before or equal to end_date"}, 400

#         if per_day:
#             all_dates = []
#             current_day = start_date
#             while current_day <= end_date:
#                 all_dates.append(current_day)
#                 current_day += timedelta(days=1)

#             daily_data = []
#             for day in all_dates:
#                 last_year_date = _same_day_last_year(day)
#                 last_month_date = _same_day_last_month(day)

#                 daily_data.append({
#                     "date": day.strftime("%Y-%m-%d"),
#                     "today": _get_front_office_block(cursor, outlet, day),
#                     "same_day_last_year": {
#                         "date": last_year_date.strftime("%Y-%m-%d"),
#                         **_get_front_office_block(cursor, outlet, last_year_date)
#                     },
#                     "same_day_last_month": {
#                         "date": last_month_date.strftime("%Y-%m-%d"),
#                         **_get_front_office_block(cursor, outlet, last_month_date)
#                     },
#                 })

#             mydb.close()
#             return jsonify({
#                 "outlet": outlet,
#                 "start_date": start_date_str,
#                 "end_date": end_date_str,
#                 "daily_data": daily_data
#             }), 200
#         else:
#             result = _get_front_office_block_range(cursor, outlet, start_date_str, end_date_str)

#             mydb.close()
#             return jsonify({
#                 "outlet": outlet,
#                 "start_date": start_date_str,
#                 "end_date": end_date_str,
#                 **result
#             }), 200

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

app_file482 = Blueprint('app_file482', __name__)

import calendar
from datetime import date, datetime, timedelta
import requests

def _same_day_last_month(target_date):
    year, month = target_date.year, target_date.month - 1
    if month == 0:
        month, year = 12, year - 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(target_date.day, last_day))

def _same_day_last_year(target_date):
    try:
        return target_date.replace(year=target_date.year - 1)
    except ValueError:
        # Feb 29 -> Feb 28 fallback
        return date(target_date.year - 1, 2, 28)

# def _get_front_office_block(cursor, outlet, target_date):
#     # -------- BASE AGGREGATES --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.subTotal), 0) AS total_sale,
#             COALESCE(SUM(b.subTotal - b.DiscountAmt), 0) AS total_net_sale,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#     """, (target_date, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
#         FROM hotel_tblhotelbills b
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(b.PaymentMode))
#     """, (target_date, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
#         FROM hotel_tblbillpayments p
#         JOIN hotel_tblhotelbills b ON p.bill_id = b.id
#         JOIN hotel_tblreservation r ON b.reservationID = r.id
#         WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(p.PaymentMode))
#     """, (target_date, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     return {
#         "Total Sale": float(base["total_sale"]),
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": 0,
#         "VAT": float(base["vat"]),
#         "Room Revenue": float(base["room_revenue"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("card"),
#         "Mobile Payment": mode_total("mobile"),
#         "Credit": mode_total("credit"),
#         "Discount": float(base["discount"]),
#         "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
#     }

def _get_front_office_block(cursor, outlet, target_date):
    # -------- BASE AGGREGATES --------
    cursor.execute("""
        SELECT
            COALESCE(SUM(b.subTotal + b.DiscountAmt + b.VAT), 0) AS total_sale,
            COALESCE(SUM(b.subTotal - b.DiscountAmt - b.VAT), 0) AS total_net_sale,
            COALESCE(SUM(b.VAT), 0) AS vat,
            COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
            COALESCE(SUM(b.MealplanRevenue), 0) AS mealplan_revenue,
            COALESCE(SUM(b.DiscountAmt), 0) AS discount,
            COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
    """, (target_date, outlet))
    base = cursor.fetchone()

    # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
          AND LOWER(TRIM(b.PaymentMode)) != 'split'
        GROUP BY LOWER(TRIM(b.PaymentMode))
    """, (target_date, outlet))
    direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
        FROM hotel_tblbillpayments p
        JOIN hotel_tblhotelbills b ON p.bill_id = b.id
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
          AND LOWER(TRIM(b.PaymentMode)) = 'split'
        GROUP BY LOWER(TRIM(p.PaymentMode))
    """, (target_date, outlet))
    split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    def mode_total(*names):
        return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

    # -------- GUEST COUNT (for revenue-per-guest) --------
    cursor.execute("""
        SELECT COALESCE(SUM(gr.No_of_adults + gr.No_of_children), 0) AS total_guests
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        JOIN hotel_tblguestreservation gr ON gr.Reservation_ID = r.id AND gr.is_active = 1
        WHERE DATE(b.Date) = %s AND r.outlet = %s AND b.status = 1
    """, (target_date, outlet))
    guest_row = cursor.fetchone()
    total_guests = int(guest_row["total_guests"] or 0)

    total_sale = float(base["total_sale"])
    revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

    return {
        "Total Sale": total_sale,
        "Total Net Sale": float(base["total_net_sale"]),
        "Service Charge": 0,
        "VAT": float(base["vat"]),
        "Room Revenue": float(base["room_revenue"]),
        "Mealplan Revenue": float(base["mealplan_revenue"]),
        "Cash": mode_total("cash"),
        "Credit Card": mode_total("card"),
        "Mobile Payment": mode_total("mobile"),
        "Credit": mode_total("credit"),
        "Discount": float(base["discount"]),
        "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
        "Total Guests": total_guests,
        "Revenue Per Guest": revenue_per_guest,
    }

from datetime import datetime, date, timedelta
@app_file482.route("/front_office_sales", methods=["POST"])
@cross_origin()
def front_office_sales():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        # -------- INPUT (from body) --------
        body = request.get_json() or {}

        # -------- TOKEN (from body) --------
        token = body.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        outlet = body.get("outlet")
        if not outlet:
            return {"error": "outlet is required"}, 400

        date_param = body.get("date")
        if date_param:
            today = datetime.strptime(date_param, "%Y-%m-%d").date()
        else:
            today = date.today()

        last_year_date = _same_day_last_year(today)
        last_month_date = _same_day_last_month(today)

        result = {
            "today": {
                "date": today.strftime("%Y-%m-%d"),
                **_get_front_office_block(cursor, outlet, today)
            },
            "same_day_last_year": {
                "date": last_year_date.strftime("%Y-%m-%d"),
                **_get_front_office_block(cursor, outlet, last_year_date)
            },
            "same_day_last_month": {
                "date": last_month_date.strftime("%Y-%m-%d"),
                **_get_front_office_block(cursor, outlet, last_month_date)
            },
        }

        mydb.close()
        return jsonify({"outlet": outlet, **result}), 200

    except Exception as e:
        try:
            mydb.close()
        except:
            pass
        return {"error": str(e)}, 500


def _get_front_office_block_range(cursor, outlet, start_date, end_date):
    # -------- BASE AGGREGATES --------
    cursor.execute("""
        SELECT
            COALESCE(SUM(b.subTotal), 0) AS total_sale,
            COALESCE(SUM(b.subTotal - b.DiscountAmt), 0) AS total_net_sale,
            COALESCE(SUM(b.VAT), 0) AS vat,
            COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
            COALESCE(SUM(b.MealplanRevenue), 0) AS mealplan_revenue,
            COALESCE(SUM(b.DiscountAmt), 0) AS discount,
            COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
    """, (start_date, end_date, outlet))
    base = cursor.fetchone()

    # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
          AND LOWER(TRIM(b.PaymentMode)) != 'split'
        GROUP BY LOWER(TRIM(b.PaymentMode))
    """, (start_date, end_date, outlet))
    direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
        FROM hotel_tblbillpayments p
        JOIN hotel_tblhotelbills b ON p.bill_id = b.id
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
          AND LOWER(TRIM(b.PaymentMode)) = 'split'
        GROUP BY LOWER(TRIM(p.PaymentMode))
    """, (start_date, end_date, outlet))
    split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    def mode_total(*names):
        return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

    # -------- GUEST COUNT (for revenue-per-guest) --------
    cursor.execute("""
        SELECT COALESCE(SUM(gr.No_of_adults + gr.No_of_children), 0) AS total_guests
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        JOIN hotel_tblguestreservation gr ON gr.Reservation_ID = r.id AND gr.is_active = 1
        WHERE DATE(b.Date) BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
    """, (start_date, end_date, outlet))
    guest_row = cursor.fetchone()
    total_guests = int(guest_row["total_guests"] or 0)

    room_revenue = float(base["room_revenue"])
    total_sale = float(base["total_sale"])
    revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

    return {
        "Total Sale": total_sale,
        "Total Net Sale": float(base["total_net_sale"]),
        "Service Charge": 0,
        "VAT": float(base["vat"]),
        "Room Revenue": room_revenue,
        "Mealplan Revenue": float(base["mealplan_revenue"]),
        "Cash": mode_total("cash"),
        "Credit Card": mode_total("card"),
        "Mobile Payment": mode_total("mobile"),
        "Credit": mode_total("credit"),
        "Discount": float(base["discount"]),
        "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
        "Total Guests": total_guests,
        "Revenue Per Guest": revenue_per_guest,
    }

@app_file482.route("/front_office_sales_range", methods=["POST"])
@cross_origin()
def front_office_sales_range():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        body = request.get_json() or {}

        # -------- TOKEN (from body) --------
        token = body.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        outlet = body.get("outlet", "Thamel")
        per_day = bool(body.get("per_day", False))

        start_date_str = body.get("start_date")
        end_date_str = body.get("end_date")

        if not start_date_str or not end_date_str:
            return {"error": "start_date and end_date are required"}, 400

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        if start_date > end_date:
            return {"error": "start_date must be before or equal to end_date"}, 400

        if per_day:
            all_dates = []
            current_day = start_date
            while current_day <= end_date:
                all_dates.append(current_day)
                current_day += timedelta(days=1)

            daily_data = []
            for day in all_dates:
                last_year_date = _same_day_last_year(day)
                last_month_date = _same_day_last_month(day)

                daily_data.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "today": _get_front_office_block(cursor, outlet, day),
                    "same_day_last_year": {
                        "date": last_year_date.strftime("%Y-%m-%d"),
                        **_get_front_office_block(cursor, outlet, last_year_date)
                    },
                    "same_day_last_month": {
                        "date": last_month_date.strftime("%Y-%m-%d"),
                        **_get_front_office_block(cursor, outlet, last_month_date)
                    },
                })

            mydb.close()
            return jsonify({
                "outlet": outlet,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "daily_data": daily_data
            }), 200
        else:
            result = _get_front_office_block_range(cursor, outlet, start_date_str, end_date_str)

            mydb.close()
            return jsonify({
                "outlet": outlet,
                "start_date": start_date_str,
                "end_date": end_date_str,
                **result
            }), 200

    except Exception as e:
        try:
            mydb.close()
        except:
            pass
        return {"error": str(e)}, 500