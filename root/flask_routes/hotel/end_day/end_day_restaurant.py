from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()

app_file485 = Blueprint('app_file485', __name__)
from root.auth.check import token_auth
from datetime import datetime, timedelta, date
@app_file485.route("/outlet/endday", methods=["POST"])
@cross_origin()
def close_outlet_day():
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        data = request.get_json() or {}
        outlet_name = data.get("outlet")
        closed_by = data.get("closed_by")  # optional: employee_id

        if not outlet_name:
            return {"error": "outlet is required"}, 400

        outlet_name = outlet_name.strip()

        # -------- VALIDATE OUTLET, RESOLVE TO ID --------
        cursor.execute("SELECT id FROM outetNames WHERE Outlet = %s", (outlet_name,))
        outlet_row = cursor.fetchone()

        if not outlet_row:
            return {"error": f"No outlet found with name '{outlet_name}'"}, 404

        outlet_id = outlet_row["id"]

        # -------- FIND THE LAST CLOSED ENTRY FOR THIS OUTLET --------
        cursor.execute("""
            SELECT business_date, end_bill_id
            FROM hotel_outlet_endday
            WHERE outlet_id = %s
            ORDER BY business_date DESC
            LIMIT 1
        """, (outlet_id,))
        last_entry = cursor.fetchone()

        # -------- DETERMINE start_bill_id --------
        if last_entry is None or last_entry["end_bill_id"] is None:
            # No prior close for this outlet -- start from its very first bill
            cursor.execute("""
                SELECT MIN(idtblorderHistory) AS first_bill
                FROM tblorderhistory
                WHERE Outlet_Name = %s
            """, (outlet_name,))
            first_bill_row = cursor.fetchone()
            start_bill_id = first_bill_row["first_bill"]
        else:
            # Continue right after the last closed window
            start_bill_id = last_entry["end_bill_id"] + 1

        # -------- DETERMINE end_bill_id: latest bill currently in the system --------
        cursor.execute("""
            SELECT MAX(idtblorderHistory) AS last_bill
            FROM tblorderhistory
            WHERE Outlet_Name = %s
        """, (outlet_name,))
        last_bill_row = cursor.fetchone()
        end_bill_id = last_bill_row["last_bill"]

        # if start_bill_id is None or end_bill_id is None:
        #     return {"error": "No bills found for this outlet -- nothing to close"}, 400

        # if end_bill_id < start_bill_id:
        #     return {"error": "No new bills since the last close for this outlet"}, 400

        # -------- DETERMINE business_date --------
        cursor.execute("""
            SELECT MAX(business_date) AS last_closed
            FROM hotel_outlet_endday
            WHERE outlet_id = %s
        """, (outlet_id,))
        row = cursor.fetchone()
        last_closed = row["last_closed"]

        if last_closed is None:
            business_date = date.today()
        else:
            business_date = last_closed + timedelta(days=1)

        # -------- INSERT --------
        cursor.execute("""
            INSERT INTO hotel_outlet_endday (outlet_id, business_date, start_bill_id, end_bill_id, closed_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (outlet_id, business_date, start_bill_id, end_bill_id, closed_by))

        mydb.commit()

        return jsonify({
            "message": "Day closed successfully",
            "outlet": outlet_name,
            "outlet_id": outlet_id,
            "business_date": str(business_date),
            "start_bill_id": start_bill_id,
            "end_bill_id": end_bill_id
        }), 201

    except mysql.connector.IntegrityError:
        return {"error": "This business date has already been closed for this outlet"}, 400

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()