from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

load_dotenv()
app_file487 = Blueprint('app_file487', __name__)
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

def _get_restaurant_sales_block_by_bill_range(cursor, outlet, start_bill_id, end_bill_id):
    # -------- BASE AGGREGATES (incl. item-type breakdown + guest count) --------
    cursor.execute("""
        SELECT
            COALESCE(SUM(b.Total), 0) AS total_sale,
            COALESCE(SUM(b.Total - b.serviceCharge - b.VAT), 0) AS total_net_sale,
            COALESCE(SUM(b.serviceCharge), 0) AS service_charge,
            COALESCE(SUM(b.VAT), 0) AS vat,
            COALESCE(SUM(b.DiscountAmt), 0) AS discount,
            COALESCE(SUM(b.NoOfGuests), 0) AS total_guests,
            COUNT(*) AS total_bills,
            COALESCE(SUM(b.DiscountAmt <> 0), 0) AS discounted_bills,
            MIN(b.Date) AS earliest_date,
            MAX(b.Date) AS latest_date,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Food'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE idtblorderhistory BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
             )) AS food_sales,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Beverage'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE idtblorderhistory BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
             )) AS beverage_sales,
            (SELECT COALESCE(SUM(od.Total), 0) FROM tblorder_detailshistory od
             WHERE od.ItemType = 'Other'
             AND od.order_ID IN (
                 SELECT idtblorderhistory FROM tblorderhistory
                 WHERE idtblorderhistory BETWEEN %s AND %s AND Outlet_Name = %s AND bill_no != ''
             )) AS others_sales
        FROM tblorderhistory b
        WHERE b.idtblorderhistory BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
    """, (start_bill_id, end_bill_id, outlet, start_bill_id, end_bill_id, outlet,
          start_bill_id, end_bill_id, outlet, start_bill_id, end_bill_id, outlet))
    base = cursor.fetchone()

    # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(REPLACE(b.PaymentMode, ' ', ''))) AS mode, SUM(b.Total) AS amt
        FROM tblorderhistory b
        WHERE b.idtblorderhistory BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
          AND LOWER(TRIM(b.PaymentMode)) != 'split'
        GROUP BY LOWER(TRIM(REPLACE(b.PaymentMode, ' ', '')))
    """, (start_bill_id, end_bill_id, outlet))
    direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(REPLACE(p.paymentMode, ' ', ''))) AS mode, SUM(p.paymentAmount) AS amt
        FROM payment_history p
        JOIN tblorderhistory b ON p.orderHistoryid = b.idtblorderhistory
        WHERE b.idtblorderhistory BETWEEN %s AND %s AND b.Outlet_Name = %s AND b.bill_no != ''
          AND LOWER(TRIM(b.PaymentMode)) = 'split'
        GROUP BY LOWER(TRIM(REPLACE(p.paymentMode, ' ', '')))
    """, (start_bill_id, end_bill_id, outlet))
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
        "Total Bills": int(base["total_bills"] or 0),
        "Discounted Bills": int(base["discounted_bills"] or 0),
        "Beverage Sale": float(base["beverage_sales"]),
        "Other Sale": float(base["others_sales"]),
        "Total Guests": total_guests,
        "Revenue Per Guest": revenue_per_guest,
        "earliest_bill_date": str(base["earliest_date"]) if base["earliest_date"] else None,
        "latest_bill_date": str(base["latest_date"]) if base["latest_date"] else None,
    }


@app_file487.route("/restaurant_sales_summary_since_last_close", methods=["POST"])
@cross_origin()
def restaurant_sales_summary_since_last_close():
    body = request.get_json() or {}

    # -------- VALIDATION (no DB needed) --------
    token = body.get("token")
    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    company_property_name = body.get("outlet")  # optional: filter to one hotel property's outlets

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESOLVE OUTLET LIST (with their outlet_id, needed for hotel_outlet_endday) --------
        if company_property_name:
            cursor.execute(
                "SELECT id FROM hotel_company_property WHERE name = %s",
                (company_property_name,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": "Company property not found."}, 404

            cursor.execute(
                "SELECT id, Outlet FROM outetNames WHERE company_property_id = %s",
                (row["id"],)
            )
        else:
            cursor.execute("SELECT id, Outlet FROM outetNames")

        outlets = cursor.fetchall()

        response_list = []

        for outlet_row in outlets:
            outlet_id = outlet_row["id"]
            outlet_name = outlet_row["Outlet"]

            if not outlet_name:
                continue

            # -------- FIND THIS OUTLET'S LAST CLOSED end_bill_id --------
            cursor.execute("""
                SELECT end_bill_id
                FROM hotel_outlet_endday
                WHERE outlet_id = %s
                ORDER BY business_date DESC
                LIMIT 1
            """, (outlet_id,))
            last_entry = cursor.fetchone()

            if last_entry is None or last_entry["end_bill_id"] is None:
                # Never closed before -- start from this outlet's very first bill
                cursor.execute("""
                    SELECT MIN(idtblorderhistory) AS first_bill
                    FROM tblorderhistory
                    WHERE Outlet_Name = %s
                """, (outlet_name,))
                first_bill_row = cursor.fetchone()
                start_bill_id = first_bill_row["first_bill"]
            else:
                start_bill_id = last_entry["end_bill_id"] + 1

            # -------- CURRENT LATEST BILL FOR THIS OUTLET --------
            cursor.execute("""
                SELECT MAX(idtblorderhistory) AS last_bill
                FROM tblorderhistory
                WHERE Outlet_Name = %s
            """, (outlet_name,))
            last_bill_row = cursor.fetchone()
            end_bill_id = last_bill_row["last_bill"]

            if start_bill_id is None or end_bill_id is None or end_bill_id < start_bill_id:
                # Nothing new since last close (or no bills at all) -- return an empty block
                response_list.append({
                    "outlet": outlet_name,
                    "start_bill_id": start_bill_id,
                    "end_bill_id": end_bill_id,
                    "has_new_bills": False
                })
                continue

            sales_block = _get_restaurant_sales_block_by_bill_range(cursor, outlet_name, start_bill_id, end_bill_id)

            response_list.append({
                "outlet": outlet_name,
                "start_bill_id": start_bill_id,
                "end_bill_id": end_bill_id,
                "has_new_bills": True,
                **sales_block
            })

        return {"outlets": response_list}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()


# ---------------------------------------------------------------
# 1) CLOSED DAYS: sales for a saved start/end bill range
# ---------------------------------------------------------------
@app_file487.route("/restaurant_sales_summary_by_bill_range", methods=["POST"])
@cross_origin()
def restaurant_sales_summary_by_bill_range():
    body = request.get_json(silent=True) or {}

    # -------- VALIDATION (no DB needed) --------
    token = body.get("token")
    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    outlet_id = body.get("outlet_id")
    start_bill_id = body.get("start_bill_id")
    end_bill_id = body.get("end_bill_id")

    if outlet_id is None or start_bill_id is None or end_bill_id is None:
        return {"error": "outlet_id, start_bill_id and end_bill_id are required"}, 400

    try:
        outlet_id = int(outlet_id)
        start_bill_id = int(start_bill_id)
        end_bill_id = int(end_bill_id)
    except (TypeError, ValueError):
        return {"error": "outlet_id, start_bill_id and end_bill_id must be integers"}, 400

    if start_bill_id > end_bill_id:
        return {"error": "start_bill_id cannot be greater than end_bill_id"}, 400

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESOLVE OUTLET NAME --------
        cursor.execute("SELECT Outlet FROM outetNames WHERE id = %s", (outlet_id,))
        outlet_row = cursor.fetchone()
        if not outlet_row or not outlet_row["Outlet"]:
            return {"error": "Outlet not found."}, 404
        outlet_name = outlet_row["Outlet"]

        # -------- RANGE MUST MATCH A CLOSED DAY FOR THIS OUTLET --------
        cursor.execute("""
            SELECT business_date
            FROM hotel_outlet_endday
            WHERE outlet_id = %s AND start_bill_id = %s AND end_bill_id = %s
            LIMIT 1
        """, (outlet_id, start_bill_id, end_bill_id))
        closed_row = cursor.fetchone()
        if not closed_row:
            return {"error": "This bill range does not match a closed day for this outlet."}, 404

        sales_block = _get_restaurant_sales_block_by_bill_range(
            cursor, outlet_name, start_bill_id, end_bill_id
        )

        return jsonify({
            "outlet_id": outlet_id,
            "outlet": outlet_name,
            "business_date": str(closed_row["business_date"]),
            "start_bill_id": start_bill_id,
            "end_bill_id": end_bill_id,
            **sales_block
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()

# ---------------------------------------------------------------
# 2) CLOSED DAYS: sales for every restaurant of a property, by business date
# ---------------------------------------------------------------
@app_file487.route("/restaurant_sales_summary_by_business_date", methods=["POST"])
@cross_origin()
def restaurant_sales_summary_by_business_date():
    body = request.get_json(silent=True) or {}

    # -------- VALIDATION (no DB needed) --------
    token = body.get("token")
    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    property_name = body.get("outlet")        # hotel property name, as in restaurant_sales_summary
    business_date = body.get("business_date")
    if not property_name or not business_date:
        return {"error": "outlet (property name) and business_date are required"}, 400
    if not valid_date(business_date):
        return {"error": "Invalid date supplied. Use YYYY-MM-DD"}, 400
    parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- PROPERTY --------
        cursor.execute(
            "SELECT id FROM hotel_company_property WHERE name = %s",
            (property_name,)
        )
        prop = cursor.fetchone()
        if not prop:
            return {"error": "Company property not found."}, 404

        # -------- RESTAURANTS OF THIS PROPERTY --------
        cursor.execute(
            "SELECT id, Outlet FROM outetNames WHERE company_property_id = %s AND Outlet IS NOT NULL",
            (prop["id"],)
        )
        restaurants = cursor.fetchall()
        if not restaurants:
            return {"error": "No restaurants found for this property."}, 404

        response_list = []
        for rest in restaurants:
            outlet_id = rest["id"]
            outlet_name = rest["Outlet"]

            # -------- CLOSED DAY FOR THIS RESTAURANT + DATE --------
            cursor.execute("""
                SELECT business_date, start_bill_id, end_bill_id
                FROM hotel_outlet_endday
                WHERE outlet_id = %s AND business_date = %s
                LIMIT 1
            """, (outlet_id, parsed_date))
            closed = cursor.fetchone()

            item = {
                "outlet_id": outlet_id,
                "outlet": outlet_name,
                "business_date": str(parsed_date),
            }

            if not closed:
                # day was not closed for this restaurant
                response_list.append({**item, "closed": False})
                continue

            start_bill_id = closed["start_bill_id"]
            end_bill_id = closed["end_bill_id"]

            if start_bill_id is None or end_bill_id is None:
                # closed, but there were no bills in that session
                response_list.append({
                    **item,
                    "closed": True,
                    "has_bills": False,
                    "start_bill_id": None,
                    "end_bill_id": None,
                })
                continue

            sales_block = _get_restaurant_sales_block_by_bill_range(
                cursor, outlet_name, start_bill_id, end_bill_id
            )
            response_list.append({
                **item,
                "closed": True,
                "has_bills": True,
                "start_bill_id": start_bill_id,
                "end_bill_id": end_bill_id,
                **sales_block,
            })

        return jsonify({
            "property": property_name,
            "business_date": str(parsed_date),
            "outlets": response_list,
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()