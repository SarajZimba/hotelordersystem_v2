from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()

app_file220 = Blueprint('app_file220', __name__)
from root.auth.check import token_auth

@app_file220.route("/employee_outlets", methods=["POST"])
@cross_origin()
def employee_outlets():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        json_data = request.get_json()

        # Validate token
        if "token" not in json_data or not json_data["token"].strip():
            return {"error": "No token provided."}, 400
        token = json_data["token"]
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Validate employee_id
        if "employee_id" not in json_data or not json_data["employee_id"]:
            return {"error": "No employee_id provided."}, 400
        employee_id = json_data["employee_id"]

        # Get all outlets assigned to this employee including status
        cursor.execute("""
            SELECT eo.id AS employee_outlet_id, eo.status, 
                   o.id AS outlet_id, o.Outlet, o.Company_name, o.address, o.logo
            FROM employeeoutlets eo
            JOIN outetNames o ON eo.outlet_id = o.id
            WHERE eo.employee_id = %s
        """, (employee_id,))
        result = cursor.fetchall()

        if not result:
            return {"error": "No outlets assigned to this employee."}, 400

        # Build JSON response
        row_headers = [x[0] for x in cursor.description]
        response_json = []
        for row in result:
            outlet = dict(zip(row_headers, row))
            outlet_json = {
                "employee_outlet_id": outlet["employee_outlet_id"],
                "status": bool(outlet["status"]),  # convert 0/1 to boolean
                "id": outlet["outlet_id"],
                "name": outlet["Outlet"],
                "company": outlet["Company_name"],
                "address": outlet["address"],
                "logo": outlet["logo"],
            }
            response_json.append(outlet_json)

        mydb.close()
        return {"outlets": response_json}, 200

    except Exception as e:
        return {"error": str(e)}, 400


@app_file220.route("/assign_employee_outlet", methods=["POST"])
@cross_origin()
def assign_employee_outlet():
    try:
        json_data = request.get_json()

        # -------- TOKEN --------
        if "token" not in json_data or not json_data["token"].strip():
            return {"error": "No token provided."}, 400
        token = json_data["token"]
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        employee_id = json_data.get("employee_id")
        outlet_id = json_data.get("outlet_id")

        if not employee_id:
            return {"error": "No employee_id provided."}, 400
        if not outlet_id:
            return {"error": "No outlet_id provided."}, 400

        # -------- CONNECT --------
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # -------- VALIDATE EMPLOYEE EXISTS --------
        cursor.execute("SELECT id FROM EmployeeLogin WHERE id = %s", (employee_id,))
        if not cursor.fetchone():
            mydb.close()
            return {"error": "No employee found with that employee_id"}, 400

        # -------- VALIDATE OUTLET EXISTS --------
        cursor.execute("SELECT id FROM outetNames WHERE id = %s", (outlet_id,))
        if not cursor.fetchone():
            mydb.close()
            return {"error": "No outlet found with that outlet_id"}, 400

        # -------- CHECK ALREADY ASSIGNED --------
        cursor.execute(
            "SELECT id FROM employeeoutlets WHERE employee_id = %s AND outlet_id = %s",
            (employee_id, outlet_id)
        )
        existing = cursor.fetchone()
        if existing:
            mydb.close()
            return {"error": "Employee already has access to this outlet", "id": existing["id"]}, 400

        # -------- INSERT --------
        cursor.execute(
            "INSERT INTO employeeoutlets (employee_id, outlet_id) VALUES (%s, %s)",
            (employee_id, outlet_id)
        )
        mydb.commit()
        new_id = cursor.lastrowid
        mydb.close()

        return {
            "message": "Employee outlet access granted successfully",
            "id": new_id,
            "employee_id": employee_id,
            "outlet_id": outlet_id
        }, 201

    except Exception as e:
        return {"error": str(e)}, 400