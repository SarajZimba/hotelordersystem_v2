# from flask import Blueprint, request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# from datetime import datetime, timedelta
# import re

# load_dotenv()
# app_file65 = Blueprint('app_file65', __name__)
# from root.auth.check import token_auth

# from collections import defaultdict

# from decimal import Decimal
# def valid_date(datestring):
#     try:
#         regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
#         match = re.match(regex, datestring)
#         if match:
#             return True
#     except ValueError:
#         return False
#     return False


# @app_file65.route("/dailyreport", methods=["POST"])
# @cross_origin()
# def dailyreport():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         json = request.get_json()
#         if "token" not in json or not json["token"]:
#             return {"error": "No token provided."}, 400
        
#         token = json["token"]
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
        
#         if "outlet" not in json or "dateStart" not in json or "dateEnd" not in json:
#             return {"error": "Some fields are missing"}, 400
        
#         outletName = json["outlet"]
#         start_Date = json["dateStart"]
#         end_Date = json["dateEnd"]

#         if not valid_date(start_Date) or not valid_date(end_Date):
#             return {"error": "Invalid date supplied."}, 400
        
#         # Convert dates to Python date objects
#         start_date_obj = datetime.strptime(start_Date, "%Y-%m-%d")
#         end_date_obj = datetime.strptime(end_Date, "%Y-%m-%d")

#         # List to store daily reports
#         daily_reports = []

#         # Iterate through each date
#         current_date = start_date_obj
#         while current_date <= end_date_obj:
#             date_str = current_date.strftime("%Y-%m-%d")

#             # Query to fetch sales data for the current day
#             statsSql = f"""
#             SELECT 
#                 (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TOTALSALES,
#                 (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Dine-In') AS DineInSALES,
#                 (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Tab') AS TabSALES,
#                 (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS netTOTALSALES,
#                 (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Dine-In') AS netDineInSALES,
#                 (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Tab') AS netTabSALES,
#                 (SELECT SUM(b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalVat,
#                 (SELECT SUM(b.serviceCharge) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalServiceCharge,
#                 (SELECT SUM(b.NoOfGuests) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalGuests,
#                 (SELECT MIN(CAST(bill_no AS UNSIGNED)) FROM tblorderhistory WHERE bill_no != '' AND Date = %s AND Outlet_Name = %s) AS StartBill,
#                 (SELECT MAX(CAST(bill_no AS UNSIGNED)) FROM tblorderhistory WHERE bill_no != '' AND Date = %s AND Outlet_Name = %s) AS EndBill,
#                 (SELECT SUM(b.DiscountAmt) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS DiscountAmt,
#                 (SELECT SUM(od.Total) FROM tblorder_detailshistory od
#                 WHERE od.ItemType = 'Food'
#                 AND od.order_ID IN (
#                     SELECT idtblorderHistory 
#                     FROM tblorderhistory 
#                     WHERE Date = %s 
#                     AND Outlet_Name = %s 
#                     AND bill_no != ''
#                 )) AS Food_Sales,
#                 (SELECT SUM(od.Total) FROM tblorder_detailshistory od
#                 WHERE od.ItemType = 'Beverage'
#                 AND od.order_ID IN (
#                     SELECT idtblorderHistory 
#                     FROM tblorderhistory 
#                     WHERE Date = %s 
#                     AND Outlet_Name = %s 
#                     AND bill_no != ''
#                 )) AS Beverage_Sales,
#                 (SELECT SUM(od.Total) FROM tblorder_detailshistory od
#                 WHERE od.ItemType = 'Other'
#                 AND od.order_ID IN (
#                     SELECT idtblorderHistory 
#                     FROM tblorderhistory 
#                     WHERE Date = %s 
#                     AND Outlet_Name = %s 
#                     AND bill_no != ''
#                 )) AS Others_Sales
#             """
#             cursor.execute(statsSql, (date_str, outletName) * 15)
#             statsResult = cursor.fetchall()

#             if not statsResult or not statsResult[0][0]:
#                 # current_date += timedelta(days=1)
#                 dummy_data_for_notavailable_data = {
#                     "Beverage_Sales": "0.0",
#                     "Date": date_str,
#                     "DineInSALES": "0.0",
#                     "DiscountAmt": "0.00",
#                     "EndBill": 0,
#                     "StartBill": None,
#                     "Food_Sales": "0.0",
#                     "Others_Sales": None,
#                     "StartBill": 0,
#                     "TOTALSALES": "0.0",
#                     "TabSALES": None,
#                     "TotalGuests": "0",
#                     "TotalServiceCharge": "0.00",
#                     "TotalVat": "0.0",
#                     "netDineInSALES": "0.0",
#                     "netTOTALSALES": "0.0",
#                     "netTabSALES": None,
#                     "paymentStats": {
#                         "Cash": "0.00",
#                         "Complimentary": "0",
#                         "Credit": "0",
#                         "CreditCard": "0.0",
#                         "MobilePayment": "0.0",
#                         "NonChargeable": "0",
#                         "Split": "0"
#                     }
#                 }
#                 daily_reports.append(dummy_data_for_notavailable_data)
#                 current_date += timedelta(days=1)

#                 continue  # Skip if no data

#             row_headers = [x[0] for x in cursor.description]
#             daily_data = dict(zip(row_headers, statsResult[0]))
#             daily_data["Date"] = date_str  # Add date to response
            
#             # Fetch payment stats
#             paymentStats_Sql = """
#             SELECT CONVERT(SUM(Total), CHAR) AS Total, PaymentMode 
#             FROM tblorderhistory 
#             WHERE Date = %s AND Outlet_Name = %s 
#             GROUP BY PaymentMode
#             """
#             cursor.execute(paymentStats_Sql, (date_str, outletName))
#             paymentStatsResult = cursor.fetchall()

#             paymentStats_json_data = {}
#             row_headers = [x[0] for x in cursor.description]
#             for res in paymentStatsResult:
#                 paymentkey = dict(zip(row_headers, res))["PaymentMode"]
#                 paymentkey = paymentkey.replace(" ", "")
#                 paymentStats_json_data[paymentkey] = dict(zip(row_headers, res))["Total"]

#             # Ensure all keys exist
#             required_keys = ["Cash", "Complimentary", "CreditCard", "MobilePayment", "NonChargeable", "Split", "Credit"]
#             for key in required_keys:
#                 if key not in paymentStats_json_data:
#                     paymentStats_json_data[key] = "0"

#             # # Merge Complimentary and NonChargeable
#             # if "NonChargeable" in paymentStats_json_data and "Complimentary" in paymentStats_json_data:
#             #     paymentStats_json_data["Complimentary"] = str(float(paymentStats_json_data["NonChargeable"]) + float(paymentStats_json_data["Complimentary"]))

#             # if "NonChargeable" in paymentStats_json_data and "Complimentary" not in paymentStats_json_data:
#             #     paymentStats_json_data["Complimentary"] = paymentStats_json_data["NonChargeable"]

#             daily_data["paymentStats"] = paymentStats_json_data



#             # Append to list
#             daily_reports.append(daily_data)

#             # Move to next day
#             current_date += timedelta(days=1)

#         mydb.close()

#         response_dict = {
#             "daily_data" : [],
#             "total_data": {}
#         }

#         response_dict["daily_data"] = daily_reports

#         total_data = defaultdict(Decimal)

#         min_startbill = None
#         max_endbill = None
#         for report in daily_reports:
#             start_bill = Decimal(report.get("StartBill"))  # Convert None/null to 0
#             end_bill = Decimal(report.get("EndBill") or 0)


#             print("The start bills", start_bill)
#             print("The min start bills", min_startbill)
#             # Update min_startbill
#             if start_bill != 0:
#                 if min_startbill is None or start_bill < min_startbill:
#                     min_startbill = start_bill

#             # Update max_endbill
#             if max_endbill is None or end_bill > max_endbill:
#                 max_endbill = end_bill
#             for key, value in report.items():
#                 if key in ["Date", "StartBill", "EndBill", "paymentStats"]:

#                     continue

#                 # if key in ["StartBill"]:
#                 #     min_startbill = min(min_startbill, Decimal(value))
                

#                 # if key in ["StartBill"]:
#                 #     max_endbill = max(max_endbill, Decimal(value))


#                 if isinstance(value, str ) or value is None:
#                     value = Decimal(value) if value not in (None, "null") else Decimal(0.0)
#                 total_data[key] += value

#             for key, value in report["paymentStats"].items():
#                 if isinstance(value, str) or value is None:
#                     value = Decimal(value) if value not in (None, "null") else Decimal(0.0)
#                 total_data[key] += value

            
#         total_data = dict(total_data)

#         total_data["min_startbill"] = int(min_startbill) if min_startbill else None
#         total_data["max_endbill"] = int(max_endbill) if max_endbill else None
#         response_dict["total_data"] = total_data
        


#         return response_dict

#     except Exception as error:
#         return {'error': str(error)}, 400



# import calendar
# from datetime import date, datetime

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
#         return date(target_date.year - 1, 2, 28)


# def _get_restaurant_sales_block(cursor, outlet, target_date):
#     date_str = target_date.strftime("%Y-%m-%d")

#     # -------- BASE AGGREGATES (incl. item-type breakdown) --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.Total), 0) AS total_sale,
#             COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
#             COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Food'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS food_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Beverage'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS beverage_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Other'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS others_sales
#         FROM tblorderhistory b
#         WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
#     """, (date_str, outlet, date_str, outlet, date_str, outlet, date_str, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
#         FROM tblorderhistory b
#         WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
#     """, (date_str, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
#         FROM payment_history p
#         JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
#         WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
#     """, (date_str, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     return {
#         "Total Sale": float(base["total_sale"]),
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": float(base["service_charge"]),
#         "VAT": float(base["vat"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("creditcard"),
#         "Mobile Payment": mode_total("mobilepayment"),
#         "Credit": mode_total("credit"),
#         "Room Charge": mode_total("roomcharge"),
#         "Discount": float(base["discount"]),
#         "Food Sale": float(base["food_sales"]),
#         "Beverage Sale": float(base["beverage_sales"]),
#         "Other Sale": float(base["others_sales"]),
#     }


# @app_file65.route("/restaurant_sales_summary", methods=["POST"])
# @cross_origin()
# def restaurant_sales_summary():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         body = request.get_json() or {}

#         # -------- TOKEN --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         outlet = body.get("outlet")

#         # -------- RESOLVE OUTLET LIST --------
#         if outlet:
#             outlets = [outlet]
#         else:
#             cursor.execute("SELECT DISTINCT Outlet FROM outetNames")
#             outlets = [row["Outlet"] for row in cursor.fetchall() if row["Outlet"]]

#         date_param = body.get("date")
#         if date_param:
#             if not valid_date(date_param):
#                 return {"error": "Invalid date supplied."}, 400
#             today = datetime.strptime(date_param, "%Y-%m-%d").date()
#         else:
#             today = date.today()

#         last_year_date = _same_day_last_year(today)
#         last_month_date = _same_day_last_month(today)

#         response_list = []
#         for outlet_name in outlets:
#             response_list.append({
#                 "outlet": outlet_name,
#                 "today": {
#                     "date": today.strftime("%Y-%m-%d"),
#                     **_get_restaurant_sales_block(cursor, outlet_name, today)
#                 },
#                 "same_day_last_year": {
#                     "date": last_year_date.strftime("%Y-%m-%d"),
#                     **_get_restaurant_sales_block(cursor, outlet_name, last_year_date)
#                 },
#                 "same_day_last_month": {
#                     "date": last_month_date.strftime("%Y-%m-%d"),
#                     **_get_restaurant_sales_block(cursor, outlet_name, last_month_date)
#                 },
#             })

#         mydb.close()
#         return {"outlets": response_list}, 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
#         return {"error": str(e)}, 500

# def _get_restaurant_sales_block_range(cursor, outlet, start_date, end_date):
#     start_str = start_date.strftime("%Y-%m-%d")
#     end_str = end_date.strftime("%Y-%m-%d")

#     # -------- BASE AGGREGATES (incl. item-type breakdown) --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.Total), 0) AS total_sale,
#             COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
#             COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Food'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS food_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Beverage'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS beverage_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Other'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS others_sales
#         FROM tblorderhistory b
#         WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
#     """, (start_str, end_str, outlet, start_str, end_str, outlet, start_str, end_str, outlet, start_str, end_str, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
#         FROM tblorderhistory b
#         WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
#     """, (start_str, end_str, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
#         FROM payment_history p
#         JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
#         WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
#     """, (start_str, end_str, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     return {
#         "Total Sale": float(base["total_sale"]),
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": float(base["service_charge"]),
#         "VAT": float(base["vat"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("creditcard"),
#         "Mobile Payment": mode_total("mobilepayment"),
#         "Credit": mode_total("credit"),
#         "Room Charge": mode_total("roomcharge"),
#         "Discount": float(base["discount"]),
#         "Food Sale": float(base["food_sales"]),
#         "Beverage Sale": float(base["beverage_sales"]),
#         "Other Sale": float(base["others_sales"]),
#     }


# @app_file65.route("/restaurant_sales_summary_range", methods=["POST"])
# @cross_origin()
# def restaurant_sales_summary_range():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         body = request.get_json() or {}

#         # -------- TOKEN --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         outlet = body.get("outlet")
#         per_day = bool(body.get("per_day", False))

#         # -------- RESOLVE OUTLET LIST --------
#         if outlet:
#             outlets = [outlet]
#         else:
#             cursor.execute("SELECT DISTINCT Outlet FROM outetNames")
#             outlets = [row["Outlet"] for row in cursor.fetchall() if row["Outlet"]]

#         # -------- INPUT DATES --------
#         start_date_str = body.get("start_date")
#         end_date_str = body.get("end_date")

#         if not start_date_str or not end_date_str:
#             return {"error": "start_date and end_date are required"}, 400

#         if not valid_date(start_date_str) or not valid_date(end_date_str):
#             return {"error": "Invalid date supplied."}, 400

#         start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

#         if start_date > end_date:
#             return {"error": "start_date must be before or equal to end_date"}, 400

#         response_list = []

#         if per_day:
#             # -------- BUILD LIST OF DATES IN RANGE --------
#             all_dates = []
#             current_day = start_date
#             while current_day <= end_date:
#                 all_dates.append(current_day)
#                 current_day += timedelta(days=1)

#             for outlet_name in outlets:
#                 daily_data = [
#                     {
#                         "date": day.strftime("%Y-%m-%d"),
#                         **_get_restaurant_sales_block(cursor, outlet_name, day)
#                     }
#                     for day in all_dates
#                 ]

#                 response_list.append({
#                     "outlet": outlet_name,
#                     "start_date": start_date_str,
#                     "end_date": end_date_str,
#                     "daily_data": daily_data
#                 })
#         else:
#             for outlet_name in outlets:
#                 response_list.append({
#                     "outlet": outlet_name,
#                     "start_date": start_date_str,
#                     "end_date": end_date_str,
#                     **_get_restaurant_sales_block_range(cursor, outlet_name, start_date, end_date)
#                 })

#         mydb.close()
#         return {"outlets": response_list}, 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
#         return {"error": str(e)}, 500


# from flask import Blueprint, request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# from datetime import datetime, timedelta
# import re

# load_dotenv()
# app_file65 = Blueprint('app_file65', __name__)
# from root.auth.check import token_auth

# from collections import defaultdict

# from decimal import Decimal
# def valid_date(datestring):
#     try:
#         regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
#         match = re.match(regex, datestring)
#         if match:
#             return True
#     except ValueError:
#         return False
#     return False


# @app_file65.route("/dailyreport", methods=["POST"])
# @cross_origin()
# def dailyreport():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         json = request.get_json()
#         if "token" not in json or not json["token"]:
#             return {"error": "No token provided."}, 400
        
#         token = json["token"]
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400
        
#         if "outlet" not in json or "dateStart" not in json or "dateEnd" not in json:
#             return {"error": "Some fields are missing"}, 400
        
#         outletName = json["outlet"]
#         start_Date = json["dateStart"]
#         end_Date = json["dateEnd"]

#         if not valid_date(start_Date) or not valid_date(end_Date):
#             return {"error": "Invalid date supplied."}, 400
        
#         # Convert dates to Python date objects
#         start_date_obj = datetime.strptime(start_Date, "%Y-%m-%d")
#         end_date_obj = datetime.strptime(end_Date, "%Y-%m-%d")

#         # List to store daily reports
#         daily_reports = []

#         # Iterate through each date
#         current_date = start_date_obj
#         while current_date <= end_date_obj:
#             date_str = current_date.strftime("%Y-%m-%d")

#             # Query to fetch sales data for the current day
#             statsSql = f"""
#             SELECT 
#                 (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TOTALSALES,
#                 (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Dine-In') AS DineInSALES,
#                 (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Tab') AS TabSALES,
#                 (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS netTOTALSALES,
#                 (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Dine-In') AS netDineInSALES,
#                 (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Tab') AS netTabSALES,
#                 (SELECT SUM(b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalVat,
#                 (SELECT SUM(b.serviceCharge) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalServiceCharge,
#                 (SELECT SUM(b.NoOfGuests) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalGuests,
#                 (SELECT MIN(CAST(bill_no AS UNSIGNED)) FROM tblorderhistory WHERE bill_no != '' AND Date = %s AND Outlet_Name = %s) AS StartBill,
#                 (SELECT MAX(CAST(bill_no AS UNSIGNED)) FROM tblorderhistory WHERE bill_no != '' AND Date = %s AND Outlet_Name = %s) AS EndBill;
#             """
#             cursor.execute(statsSql, (date_str, outletName) * 11)
#             statsResult = cursor.fetchall()

#             if not statsResult or not statsResult[0][0]:
#                 current_date += timedelta(days=1)
#                 continue  # Skip if no data

#             row_headers = [x[0] for x in cursor.description]
#             daily_data = dict(zip(row_headers, statsResult[0]))
#             daily_data["Date"] = date_str  # Add date to response
            
#             # Fetch payment stats
#             paymentStats_Sql = """
#             SELECT CONVERT(SUM(Total), CHAR) AS Total, PaymentMode 
#             FROM tblorderhistory 
#             WHERE Date = %s AND Outlet_Name = %s 
#             GROUP BY PaymentMode
#             """
#             cursor.execute(paymentStats_Sql, (date_str, outletName))
#             paymentStatsResult = cursor.fetchall()

#             paymentStats_json_data = {}
#             row_headers = [x[0] for x in cursor.description]
#             for res in paymentStatsResult:
#                 paymentkey = dict(zip(row_headers, res))["PaymentMode"]
#                 paymentkey = paymentkey.replace(" ", "")
#                 paymentStats_json_data[paymentkey] = dict(zip(row_headers, res))["Total"]

#             # Ensure all keys exist
#             required_keys = ["Cash", "Complimentary", "CreditCard", "MobilePayment", "NonChargeable", "Split", "Credit"]
#             for key in required_keys:
#                 if key not in paymentStats_json_data:
#                     paymentStats_json_data[key] = "0"

#             # Merge Complimentary and NonChargeable
#             if "NonChargeable" in paymentStats_json_data and "Complimentary" in paymentStats_json_data:
#                 paymentStats_json_data["Complimentary"] = str(float(paymentStats_json_data["NonChargeable"]) + float(paymentStats_json_data["Complimentary"]))

#             if "NonChargeable" in paymentStats_json_data and "Complimentary" not in paymentStats_json_data:
#                 paymentStats_json_data["Complimentary"] = paymentStats_json_data["NonChargeable"]

#             daily_data["paymentStats"] = paymentStats_json_data

#             # Append to list
#             daily_reports.append(daily_data)

#             # Move to next day
#             current_date += timedelta(days=1)

#         mydb.close()

#         response_dict = {
#             "daily_data" : [],
#             "total_data": {}
#         }

#         response_dict["daily_data"] = daily_reports

#         total_data = defaultdict(Decimal)

#         for report in daily_reports:
#             for key, value in report.items():
#                 if key in ["Date", "StartBill", "EndBill", "paymentStats"]:
#                     continue

#                 if isinstance(value, str ) or value is None:
#                     value = Decimal(value) if value not in (None, "null") else Decimal(0.0)
#                 total_data[key] += value

#             for key, value in report["paymentStats"].items():
#                 if isinstance(value, str) or value is None:
#                     value = Decimal(value) if value not in (None, "null") else Decimal(0.0)
#                 total_data[key] += value

            
#         total_data = dict(total_data)


#         response_dict["total_data"] = total_data
        


#         return response_dict

#     except Exception as error:
#         return {'error': str(error)}, 400


from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

load_dotenv()
app_file65 = Blueprint('app_file65', __name__)
from root.auth.check import token_auth

from collections import defaultdict

from decimal import Decimal
def valid_date(datestring):
    try:
        regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
        match = re.match(regex, datestring)
        if match:
            return True
    except ValueError:
        return False
    return False


@app_file65.route("/dailyreport", methods=["POST"])
@cross_origin()
def dailyreport():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')};")

        json = request.get_json()
        if "token" not in json or not json["token"]:
            return {"error": "No token provided."}, 400
        
        token = json["token"]
        if not token_auth(token):
            return {"error": "Invalid token."}, 400
        
        if "outlet" not in json or "dateStart" not in json or "dateEnd" not in json:
            return {"error": "Some fields are missing"}, 400
        
        outletName = json["outlet"]
        start_Date = json["dateStart"]
        end_Date = json["dateEnd"]

        if not valid_date(start_Date) or not valid_date(end_Date):
            return {"error": "Invalid date supplied."}, 400
        
        # Convert dates to Python date objects
        start_date_obj = datetime.strptime(start_Date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_Date, "%Y-%m-%d")

        # List to store daily reports
        daily_reports = []

        # Iterate through each date
        current_date = start_date_obj
        while current_date <= end_date_obj:
            date_str = current_date.strftime("%Y-%m-%d")

            # Query to fetch sales data for the current day
            statsSql = f"""
            SELECT 
                (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TOTALSALES,
                (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Dine-In') AS DineInSALES,
                (SELECT SUM(b.total) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Tab') AS TabSALES,
                (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS netTOTALSALES,
                (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Dine-In') AS netDineInSALES,
                (SELECT SUM(b.Total - b.serviceCharge - b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s AND b.Type='Tab') AS netTabSALES,
                (SELECT SUM(b.VAT) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalVat,
                (SELECT SUM(b.serviceCharge) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalServiceCharge,
                (SELECT SUM(b.NoOfGuests) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS TotalGuests,
                (SELECT MIN(CAST(bill_no AS UNSIGNED)) FROM tblorderhistory WHERE bill_no != '' AND Date = %s AND Outlet_Name = %s) AS StartBill,
                (SELECT MAX(CAST(bill_no AS UNSIGNED)) FROM tblorderhistory WHERE bill_no != '' AND Date = %s AND Outlet_Name = %s) AS EndBill,
                (SELECT SUM(b.DiscountAmt) FROM tblorderhistory b WHERE b.bill_no != '' AND b.Date = %s AND b.Outlet_Name = %s) AS DiscountAmt,
                (SELECT SUM(od.Total) FROM tblorder_detailshistory od
                WHERE od.ItemType = 'Food'
                AND od.order_ID IN (
                    SELECT idtblorderHistory 
                    FROM tblorderhistory 
                    WHERE Date = %s 
                    AND Outlet_Name = %s 
                    AND bill_no != ''
                )) AS Food_Sales,
                (SELECT SUM(od.Total) FROM tblorder_detailshistory od
                WHERE od.ItemType = 'Beverage'
                AND od.order_ID IN (
                    SELECT idtblorderHistory 
                    FROM tblorderhistory 
                    WHERE Date = %s 
                    AND Outlet_Name = %s 
                    AND bill_no != ''
                )) AS Beverage_Sales,
                (SELECT SUM(od.Total) FROM tblorder_detailshistory od
                WHERE od.ItemType = 'Other'
                AND od.order_ID IN (
                    SELECT idtblorderHistory 
                    FROM tblorderhistory 
                    WHERE Date = %s 
                    AND Outlet_Name = %s 
                    AND bill_no != ''
                )) AS Others_Sales
            """
            cursor.execute(statsSql, (date_str, outletName) * 15)
            statsResult = cursor.fetchall()

            if not statsResult or not statsResult[0][0]:
                # current_date += timedelta(days=1)
                dummy_data_for_notavailable_data = {
                    "Beverage_Sales": "0.0",
                    "Date": date_str,
                    "DineInSALES": "0.0",
                    "DiscountAmt": "0.00",
                    "EndBill": 0,
                    "StartBill": None,
                    "Food_Sales": "0.0",
                    "Others_Sales": None,
                    "StartBill": 0,
                    "TOTALSALES": "0.0",
                    "TabSALES": None,
                    "TotalGuests": "0",
                    "TotalServiceCharge": "0.00",
                    "TotalVat": "0.0",
                    "netDineInSALES": "0.0",
                    "netTOTALSALES": "0.0",
                    "netTabSALES": None,
                    "paymentStats": {
                        "Cash": "0.00",
                        "Complimentary": "0",
                        "Credit": "0",
                        "CreditCard": "0.0",
                        "MobilePayment": "0.0",
                        "NonChargeable": "0",
                        "Split": "0"
                    }
                }
                daily_reports.append(dummy_data_for_notavailable_data)
                current_date += timedelta(days=1)

                continue  # Skip if no data

            row_headers = [x[0] for x in cursor.description]
            daily_data = dict(zip(row_headers, statsResult[0]))
            daily_data["Date"] = date_str  # Add date to response
            
            # Fetch payment stats
            paymentStats_Sql = """
            SELECT CONVERT(SUM(Total), CHAR) AS Total, PaymentMode 
            FROM tblorderhistory 
            WHERE Date = %s AND Outlet_Name = %s 
            GROUP BY PaymentMode
            """
            cursor.execute(paymentStats_Sql, (date_str, outletName))
            paymentStatsResult = cursor.fetchall()

            paymentStats_json_data = {}
            row_headers = [x[0] for x in cursor.description]
            for res in paymentStatsResult:
                paymentkey = dict(zip(row_headers, res))["PaymentMode"]
                paymentkey = paymentkey.replace(" ", "")
                paymentStats_json_data[paymentkey] = dict(zip(row_headers, res))["Total"]

            # Ensure all keys exist
            required_keys = ["Cash", "Complimentary", "CreditCard", "MobilePayment", "NonChargeable", "Split", "Credit"]
            for key in required_keys:
                if key not in paymentStats_json_data:
                    paymentStats_json_data[key] = "0"

            # # Merge Complimentary and NonChargeable
            # if "NonChargeable" in paymentStats_json_data and "Complimentary" in paymentStats_json_data:
            #     paymentStats_json_data["Complimentary"] = str(float(paymentStats_json_data["NonChargeable"]) + float(paymentStats_json_data["Complimentary"]))

            # if "NonChargeable" in paymentStats_json_data and "Complimentary" not in paymentStats_json_data:
            #     paymentStats_json_data["Complimentary"] = paymentStats_json_data["NonChargeable"]

            daily_data["paymentStats"] = paymentStats_json_data



            # Append to list
            daily_reports.append(daily_data)

            # Move to next day
            current_date += timedelta(days=1)

        mydb.close()

        response_dict = {
            "daily_data" : [],
            "total_data": {}
        }

        response_dict["daily_data"] = daily_reports

        total_data = defaultdict(Decimal)

        min_startbill = None
        max_endbill = None
        for report in daily_reports:
            start_bill = Decimal(report.get("StartBill"))  # Convert None/null to 0
            end_bill = Decimal(report.get("EndBill") or 0)


            print("The start bills", start_bill)
            print("The min start bills", min_startbill)
            # Update min_startbill
            if start_bill != 0:
                if min_startbill is None or start_bill < min_startbill:
                    min_startbill = start_bill

            # Update max_endbill
            if max_endbill is None or end_bill > max_endbill:
                max_endbill = end_bill
            for key, value in report.items():
                if key in ["Date", "StartBill", "EndBill", "paymentStats"]:

                    continue

                # if key in ["StartBill"]:
                #     min_startbill = min(min_startbill, Decimal(value))
                

                # if key in ["StartBill"]:
                #     max_endbill = max(max_endbill, Decimal(value))


                if isinstance(value, str ) or value is None:
                    value = Decimal(value) if value not in (None, "null") else Decimal(0.0)
                total_data[key] += value

            for key, value in report["paymentStats"].items():
                if isinstance(value, str) or value is None:
                    value = Decimal(value) if value not in (None, "null") else Decimal(0.0)
                total_data[key] += value

            
        total_data = dict(total_data)

        total_data["min_startbill"] = int(min_startbill) if min_startbill else None
        total_data["max_endbill"] = int(max_endbill) if max_endbill else None
        response_dict["total_data"] = total_data
        


        return response_dict

    except Exception as error:
        return {'error': str(error)}, 400



import calendar
from datetime import date, datetime

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
        return date(target_date.year - 1, 2, 28)


# def _get_restaurant_sales_block(cursor, outlet, target_date):
#     date_str = target_date.strftime("%Y-%m-%d")

#     # -------- BASE AGGREGATES (incl. item-type breakdown) --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.Total), 0) AS total_sale,
#             COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
#             COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Food'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS food_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Beverage'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS beverage_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Other'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS others_sales
#         FROM tblorderhistory b
#         WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
#     """, (date_str, outlet, date_str, outlet, date_str, outlet, date_str, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
#         FROM tblorderhistory b
#         WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
#     """, (date_str, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
#         FROM payment_history p
#         JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
#         WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
#     """, (date_str, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     return {
#         "Total Sale": float(base["total_sale"]),
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": float(base["service_charge"]),
#         "VAT": float(base["vat"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("creditcard"),
#         "Mobile Payment": mode_total("mobilepayment"),
#         "Credit": mode_total("credit"),
#         "Room Charge": mode_total("roomcharge"),
#         "Discount": float(base["discount"]),
#         "Food Sale": float(base["food_sales"]),
#         "Beverage Sale": float(base["beverage_sales"]),
#         "Other Sale": float(base["others_sales"]),
#     }


# @app_file65.route("/restaurant_sales_summary", methods=["POST"])
# @cross_origin()
# def restaurant_sales_summary():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         body = request.get_json() or {}

#         # -------- TOKEN --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         outlet = body.get("outlet")

#         # -------- RESOLVE OUTLET LIST --------
#         if outlet:
#             outlets = [outlet]
#         else:
#             cursor.execute("SELECT DISTINCT Outlet FROM outetNames")
#             outlets = [row["Outlet"] for row in cursor.fetchall() if row["Outlet"]]

#         date_param = body.get("date")
#         if date_param:
#             if not valid_date(date_param):
#                 return {"error": "Invalid date supplied."}, 400
#             today = datetime.strptime(date_param, "%Y-%m-%d").date()
#         else:
#             today = date.today()

#         last_year_date = _same_day_last_year(today)
#         last_month_date = _same_day_last_month(today)

#         response_list = []
#         for outlet_name in outlets:
#             response_list.append({
#                 "outlet": outlet_name,
#                 "today": {
#                     "date": today.strftime("%Y-%m-%d"),
#                     **_get_restaurant_sales_block(cursor, outlet_name, today)
#                 },
#                 "same_day_last_year": {
#                     "date": last_year_date.strftime("%Y-%m-%d"),
#                     **_get_restaurant_sales_block(cursor, outlet_name, last_year_date)
#                 },
#                 "same_day_last_month": {
#                     "date": last_month_date.strftime("%Y-%m-%d"),
#                     **_get_restaurant_sales_block(cursor, outlet_name, last_month_date)
#                 },
#             })

#         mydb.close()
#         return {"outlets": response_list}, 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
#         return {"error": str(e)}, 500

def _get_restaurant_sales_block(cursor, outlet, target_date):
    date_str = target_date.strftime("%Y-%m-%d")

    # -------- BASE AGGREGATES (incl. item-type breakdown + guest count) --------
    cursor.execute("""
        SELECT
            COALESCE(SUM(b.Total), 0) AS total_sale,
            COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
            COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
            COALESCE(SUM(b.VAT), 0) AS vat,
            COALESCE(SUM(b.DiscountAmt), 0) AS discount,
            COALESCE(SUM(b.NoOfGuests), 0) AS total_guests,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Food'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
             )) AS food_sales,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Beverage'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
             )) AS beverage_sales,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Other'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE Date = %s AND Outlet_Name = %s AND bill_no != ''
             )) AS others_sales
        FROM tblorderhistory b
        WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
    """, (date_str, outlet, date_str, outlet, date_str, outlet, date_str, outlet))
    base = cursor.fetchone()

    # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
        FROM tblorderhistory b
        WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
          AND LOWER(TRIM(b.PaymentMode)) != 'split'
        GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
    """, (date_str, outlet))
    direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
        FROM payment_history p
        JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
        WHERE b.Date = %s AND b.Outlet_Name = %s AND b.bill_no != ''
          AND LOWER(TRIM(b.PaymentMode)) = 'split'
        GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
    """, (date_str, outlet))
    split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    def mode_total(*names):
        return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

    total_sale = float(base["total_sale"])
    total_guests = int(base["total_guests"] or 0)
    revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

    return {
        "Total Sale": total_sale,
        "Total Net Sale": float(base["total_net_sale"]),
        "Service Charge": float(base["service_charge"]),
        "VAT": float(base["vat"]),
        "Cash": mode_total("cash"),
        "Credit Card": mode_total("creditcard"),
        "Mobile Payment": mode_total("mobilepayment"),
        "Credit": mode_total("credit"),
        "Room Charge": mode_total("roomcharge"),
        "Discount": float(base["discount"]),
        "Food Sale": float(base["food_sales"]),
        "Beverage Sale": float(base["beverage_sales"]),
        "Other Sale": float(base["others_sales"]),
        "Total Guests": total_guests,
        "Revenue Per Guest": revenue_per_guest,
    }


@app_file65.route("/restaurant_sales_summary", methods=["POST"])
@cross_origin()
def restaurant_sales_summary():
    body = request.get_json() or {}

    # -------- VALIDATION (no DB needed) --------
    token = body.get("token")
    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    date_param = body.get("date")
    if date_param:
        if not valid_date(date_param):
            return {"error": "Invalid date supplied."}, 400
        today = datetime.strptime(date_param, "%Y-%m-%d").date()
    else:
        today = date.today()

    company_property_name = body.get("outlet")
    last_year_date = _same_day_last_year(today)
    last_month_date = _same_day_last_month(today)

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        if company_property_name:
            cursor.execute(
                "SELECT id FROM hotel_company_property WHERE name = %s",
                (company_property_name,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": "Company property not found."}, 404

            cursor.execute(
                "SELECT DISTINCT Outlet FROM outetNames WHERE company_property_id = %s",
                (row["id"],)
            )
        else:
            cursor.execute("SELECT DISTINCT Outlet FROM outetNames")

        outlets = [r["Outlet"] for r in cursor.fetchall() if r["Outlet"]]

        response_list = []
        for outlet_name in outlets:
            response_list.append({
                "outlet": outlet_name,
                "today": {
                    "date": today.strftime("%Y-%m-%d"),
                    **_get_restaurant_sales_block(cursor, outlet_name, today)
                },
                "same_day_last_year": {
                    "date": last_year_date.strftime("%Y-%m-%d"),
                    **_get_restaurant_sales_block(cursor, outlet_name, last_year_date)
                },
                "same_day_last_month": {
                    "date": last_month_date.strftime("%Y-%m-%d"),
                    **_get_restaurant_sales_block(cursor, outlet_name, last_month_date)
                },
            })

        return {"outlets": response_list}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()

# def _get_restaurant_sales_block_range(cursor, outlet, start_date, end_date):
#     start_str = start_date.strftime("%Y-%m-%d")
#     end_str = end_date.strftime("%Y-%m-%d")

#     # -------- BASE AGGREGATES (incl. item-type breakdown) --------
#     cursor.execute("""
#         SELECT
#             COALESCE(SUM(b.Total), 0) AS total_sale,
#             COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
#             COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
#             COALESCE(SUM(b.VAT), 0) AS vat,
#             COALESCE(SUM(b.DiscountAmt), 0) AS discount,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Food'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS food_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Beverage'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS beverage_sales,
#             (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
#              WHERE od.ItemType = 'Other'
#              AND od.order_ID IN (
#                  SELECT idtblorderhistory FROM tblorderhistory
#                  WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
#              )) AS others_sales
#         FROM tblorderhistory b
#         WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
#     """, (start_str, end_str, outlet, start_str, end_str, outlet, start_str, end_str, outlet, start_str, end_str, outlet))
#     base = cursor.fetchone()

#     # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
#         FROM tblorderhistory b
#         WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) != 'split'
#         GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
#     """, (start_str, end_str, outlet))
#     direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
#     cursor.execute("""
#         SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
#         FROM payment_history p
#         JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
#         WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
#           AND LOWER(TRIM(b.PaymentMode)) = 'split'
#         GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
#     """, (start_str, end_str, outlet))
#     split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

#     def mode_total(*names):
#         return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

#     return {
#         "Total Sale": float(base["total_sale"]),
#         "Total Net Sale": float(base["total_net_sale"]),
#         "Service Charge": float(base["service_charge"]),
#         "VAT": float(base["vat"]),
#         "Cash": mode_total("cash"),
#         "Credit Card": mode_total("creditcard"),
#         "Mobile Payment": mode_total("mobilepayment"),
#         "Credit": mode_total("credit"),
#         "Room Charge": mode_total("roomcharge"),
#         "Discount": float(base["discount"]),
#         "Food Sale": float(base["food_sales"]),
#         "Beverage Sale": float(base["beverage_sales"]),
#         "Other Sale": float(base["others_sales"]),
#     }


# @app_file65.route("/restaurant_sales_summary_range", methods=["POST"])
# @cross_origin()
# def restaurant_sales_summary_range():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         cursor.execute(f"USE {os.getenv('database')};")

#         body = request.get_json() or {}

#         # -------- TOKEN --------
#         token = body.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         outlet = body.get("outlet")
#         per_day = bool(body.get("per_day", False))

#         # -------- RESOLVE OUTLET LIST --------
#         if outlet:
#             outlets = [outlet]
#         else:
#             cursor.execute("SELECT DISTINCT Outlet FROM outetNames")
#             outlets = [row["Outlet"] for row in cursor.fetchall() if row["Outlet"]]

#         # -------- INPUT DATES --------
#         start_date_str = body.get("start_date")
#         end_date_str = body.get("end_date")

#         if not start_date_str or not end_date_str:
#             return {"error": "start_date and end_date are required"}, 400

#         if not valid_date(start_date_str) or not valid_date(end_date_str):
#             return {"error": "Invalid date supplied."}, 400

#         start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

#         if start_date > end_date:
#             return {"error": "start_date must be before or equal to end_date"}, 400

#         response_list = []

#         if per_day:
#             # -------- BUILD LIST OF DATES IN RANGE --------
#             all_dates = []
#             current_day = start_date
#             while current_day <= end_date:
#                 all_dates.append(current_day)
#                 current_day += timedelta(days=1)

#             for outlet_name in outlets:
#                 daily_data = [
#                     {
#                         "date": day.strftime("%Y-%m-%d"),
#                         **_get_restaurant_sales_block(cursor, outlet_name, day)
#                     }
#                     for day in all_dates
#                 ]

#                 response_list.append({
#                     "outlet": outlet_name,
#                     "start_date": start_date_str,
#                     "end_date": end_date_str,
#                     "daily_data": daily_data
#                 })
#         else:
#             for outlet_name in outlets:
#                 response_list.append({
#                     "outlet": outlet_name,
#                     "start_date": start_date_str,
#                     "end_date": end_date_str,
#                     **_get_restaurant_sales_block_range(cursor, outlet_name, start_date, end_date)
#                 })

#         mydb.close()
#         return {"outlets": response_list}, 200

#     except Exception as e:
#         try:
#             mydb.close()
#         except:
#             pass
#         return {"error": str(e)}, 500

def _get_restaurant_sales_block_range(cursor, outlet, start_date, end_date):
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # -------- BASE AGGREGATES (incl. item-type breakdown + guest count) --------
    cursor.execute("""
        SELECT
            COALESCE(SUM(b.Total), 0) AS total_sale,
            COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
            COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
            COALESCE(SUM(b.VAT), 0) AS vat,
            COALESCE(SUM(b.DiscountAmt), 0) AS discount,
            COALESCE(SUM(b.NoOfGuests), 0) AS total_guests,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Food'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
             )) AS food_sales,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Beverage'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
             )) AS beverage_sales,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Other'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
             )) AS others_sales
        FROM tblorderhistory b
        WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
    """, (start_str, end_str, outlet, start_str, end_str, outlet, start_str, end_str, outlet, start_str, end_str, outlet))
    base = cursor.fetchone()

    # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
        FROM tblorderhistory b
        WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
          AND LOWER(TRIM(b.PaymentMode)) != 'split'
        GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
    """, (start_str, end_str, outlet))
    direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
        FROM payment_history p
        JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
        WHERE b.Date BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
          AND LOWER(TRIM(b.PaymentMode)) = 'split'
        GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
    """, (start_str, end_str, outlet))
    split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    def mode_total(*names):
        return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

    total_sale = float(base["total_sale"])
    total_guests = int(base["total_guests"] or 0)
    revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0

    return {
        "Total Sale": total_sale,
        "Total Net Sale": float(base["total_net_sale"]),
        "Service Charge": float(base["service_charge"]),
        "VAT": float(base["vat"]),
        "Cash": mode_total("cash"),
        "Credit Card": mode_total("creditcard"),
        "Mobile Payment": mode_total("mobilepayment"),
        "Credit": mode_total("credit"),
        "Room Charge": mode_total("roomcharge"),
        "Discount": float(base["discount"]),
        "Food Sale": float(base["food_sales"]),
        "Beverage Sale": float(base["beverage_sales"]),
        "Other Sale": float(base["others_sales"]),
        "Total Guests": total_guests,
        "Revenue Per Guest": revenue_per_guest,
    }


@app_file65.route("/restaurant_sales_summary_range", methods=["POST"])
@cross_origin()
def restaurant_sales_summary_range():
    body = request.get_json() or {}

    # -------- VALIDATION (no DB needed) --------
    token = body.get("token")
    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    start_date_str = body.get("start_date")
    end_date_str = body.get("end_date")

    if not start_date_str or not end_date_str:
        return {"error": "start_date and end_date are required"}, 400

    if not valid_date(start_date_str) or not valid_date(end_date_str):
        return {"error": "Invalid date supplied."}, 400

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    if start_date > end_date:
        return {"error": "start_date must be before or equal to end_date"}, 400

    company_property_name = body.get("outlet")
    per_day = bool(body.get("per_day", False))

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESOLVE OUTLET LIST --------
        if company_property_name:
            cursor.execute(
                "SELECT id FROM hotel_company_property WHERE name = %s",
                (company_property_name,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": "Company property not found."}, 404

            cursor.execute(
                "SELECT DISTINCT Outlet FROM outetNames WHERE company_property_id = %s",
                (row["id"],)
            )
        else:
            cursor.execute("SELECT DISTINCT Outlet FROM outetNames")

        outlets = [r["Outlet"] for r in cursor.fetchall() if r["Outlet"]]

        response_list = []

        if per_day:
            all_dates = []
            current_day = start_date
            while current_day <= end_date:
                all_dates.append(current_day)
                current_day += timedelta(days=1)

            for outlet_name in outlets:
                daily_data = [
                    {
                        "date": day.strftime("%Y-%m-%d"),
                        **_get_restaurant_sales_block(cursor, outlet_name, day)
                    }
                    for day in all_dates
                ]

                response_list.append({
                    "outlet": outlet_name,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "daily_data": daily_data
                })
        else:
            for outlet_name in outlets:
                response_list.append({
                    "outlet": outlet_name,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    **_get_restaurant_sales_block_range(cursor, outlet_name, start_date, end_date)
                })

        return {"outlets": response_list}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()