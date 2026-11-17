# from flask import Blueprint, request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# load_dotenv()

# app_file43 = Blueprint('app_file43', __name__)
# from root.auth.check import token_auth

# from .postintosalesproportal import updateuserinsalesproportal



# @app_file43.route('/edituser', methods=['POST'])
# @cross_origin()
# def edit_user():
#     cursor = None
#     mydb = None
#     try:
#         # Connect to the database
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Get JSON data from the request
#         json = request.get_json()

#         # Validate input fields
#         if "token" not in json or not json["token"]:
#             return {"error": "No token provided"}, 400

#         if "username" not in json or not json["username"]:
#             return {"error": "No username provided"}, 400

#         # if "restaurantURL" not in json or not json["restaurantURL"] or "baseURL" not in json:
#         #     return {"error": "Some urls not provided"}, 400

#         if not token_auth(json["token"]):
#             return {"error": "Invalid token"}, 400

#         if "new_username" not in json and "new_password" not in json and "new_type" not in json:
#             return {"error": "No fields to update provided"}, 400
#         if json.get("new_username") == "":
#             return {"error": "Username cannot be empty"}, 400
#         if json.get("new_password") == "":
#             return {"error": "Password cannot be empty"}, 400
#         if json.get("new_type") == "":
#             return {"error": "Type cannot be empty"}, 400

#         # Prepare variables
#         username = json["username"]
#         new_username = json.get("new_username", None)
#         new_password = json.get("new_password", None)
#         new_type = json.get("new_type", None)
#         # restaurantURL = json["restaurantURL"]
#         # baseURL = json["baseURL"]

#         get_sql = """SELECT * FROM EmployeeLogin WHERE userName = %s"""
#         cursor.execute(get_sql, (username,))
#         existing_user = cursor.fetchone()

#         if not existing_user:
#             data = {'error': 'No User found of that username'}
#             return data, 400

#         # Capture the employee's id and previous type before updating
#         employee_id = existing_user["id"]
#         previous_type = existing_user["type"]

#         # Create the SQL query to update fields dynamically
#         update_fields = []
#         values = []

#         if new_username:
#             update_fields.append("userName = %s")
#             values.append(new_username)
#         if new_password:
#             update_fields.append("Password = %s")
#             values.append(new_password)
#         if new_type:
#             update_fields.append("type = %s")
#             values.append(new_type)

#         if not update_fields:
#             return {"error": "No valid fields to update"}, 400

#         # Add the username condition to the query
#         update_query = f"UPDATE EmployeeLogin SET {', '.join(update_fields)} WHERE userName = %s"
#         values.append(username)

#         # Execute the query
#         cursor.execute(update_query, tuple(values))
#         mydb.commit()

#         # -------- IF PROMOTED TO ADMIN, GRANT FULL OUTLET + PROPERTY ACCESS --------
#         if new_type == "admin" and previous_type != "admin":
#             cursor.execute("SELECT id FROM outetNames")
#             outlet_ids = [row["id"] for row in cursor.fetchall()]

#             for outlet_id in outlet_ids:
#                 cursor.execute(
#                     "INSERT IGNORE INTO employeeoutlets (employee_id, outlet_id) VALUES (%s, %s)",
#                     (employee_id, outlet_id)
#                 )

#             cursor.execute("SELECT id FROM hotel_company_property")
#             property_ids = [row["id"] for row in cursor.fetchall()]

#             for property_id in property_ids:
#                 cursor.execute(
#                     "INSERT IGNORE INTO hotel_employee_property_access (employee_id, property_id) VALUES (%s, %s)",
#                     (employee_id, property_id)
#                 )

#             mydb.commit()

#         if new_type == "admin":
#             updateAccountingsalespro_data = {
#                 "old_username": username,
#                 "username": new_username,
#                 "password": new_password,
#                 # "restaurantURL": restaurantURL,
#                 # "baseURL": baseURL
#             }

#             # updateuserinsalesproportal(updateAccountingsalespro_data)

#         return {"success": "User details updated successfully"}, 200

#     except Exception as e:
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()

app_file43 = Blueprint('app_file43', __name__)
from root.auth.check import token_auth

from .postintosalesproportal import updateuserinsalesproportal

from .postintosalesproportal import updateuserinsalesproportal


ACCOUNTING_ADMIN_UPDATE_URL = os.getenv("accounting_url") + "api/admin/update/"

ACCOUNTING_API_TOKEN = os.getenv("accounting_token")
import requests
@app_file43.route('/edituser', methods=['POST'])
@cross_origin()
def edit_user():
    cursor = None
    mydb = None
    try:
        # Connect to the database
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Get JSON data from the request
        json = request.get_json()

        # Validate input fields
        if "token" not in json or not json["token"]:
            return {"error": "No token provided"}, 400

        if "username" not in json or not json["username"]:
            return {"error": "No username provided"}, 400

        # if "restaurantURL" not in json or not json["restaurantURL"] or "baseURL" not in json:
        #     return {"error": "Some urls not provided"}, 400

        if not token_auth(json["token"]):
            return {"error": "Invalid token"}, 400

        if "new_username" not in json and "new_password" not in json and "new_type" not in json:
            return {"error": "No fields to update provided"}, 400
        if json.get("new_username") == "":
            return {"error": "Username cannot be empty"}, 400
        if json.get("new_password") == "":
            return {"error": "Password cannot be empty"}, 400
        if json.get("new_type") == "":
            return {"error": "Type cannot be empty"}, 400

        # Prepare variables
        username = json["username"]
        new_username = json.get("new_username", None)
        new_password = json.get("new_password", None)
        new_type = json.get("new_type", None)
        restaurantURL = json["restaurantURL"]
        baseURL = json["baseURL"]

        get_sql = """SELECT * FROM EmployeeLogin WHERE userName = %s"""
        cursor.execute(get_sql, (username,))
        existing_user = cursor.fetchone()

        if not existing_user:
            data = {'error': 'No User found of that username'}
            return data, 400

        # Capture the employee's id and previous type before updating
        employee_id = existing_user["id"]
        previous_type = existing_user["type"]

        # Create the SQL query to update fields dynamically
        update_fields = []
        values = []

        if new_username:
            update_fields.append("userName = %s")
            values.append(new_username)
        if new_password:
            update_fields.append("Password = %s")
            values.append(new_password)
        if new_type:
            update_fields.append("type = %s")
            values.append(new_type)

        if not update_fields:
            return {"error": "No valid fields to update"}, 400

        # Add the username condition to the query
        update_query = f"UPDATE EmployeeLogin SET {', '.join(update_fields)} WHERE userName = %s"
        values.append(username)

        # Execute the query
        cursor.execute(update_query, tuple(values))
        mydb.commit()

        # -------- IF PROMOTED TO ADMIN, GRANT FULL OUTLET + PROPERTY ACCESS --------
        if new_type == "admin" and previous_type != "admin":
            cursor.execute("SELECT id FROM outetNames")
            outlet_ids = [row["id"] for row in cursor.fetchall()]

            for outlet_id in outlet_ids:
                cursor.execute(
                    "INSERT IGNORE INTO employeeoutlets (employee_id, outlet_id) VALUES (%s, %s)",
                    (employee_id, outlet_id)
                )

            cursor.execute("SELECT id FROM hotel_company_property")
            property_ids = [row["id"] for row in cursor.fetchall()]

            for property_id in property_ids:
                cursor.execute(
                    "INSERT IGNORE INTO hotel_employee_property_access (employee_id, property_id) VALUES (%s, %s)",
                    (employee_id, property_id)
                )

            mydb.commit()

        # --- Update on the accounting backend ---
        accounting_payload = {
                "username": username,
                **({"new_username": new_username} if new_username else {}),
                **({"password": new_password} if new_password else {}),
        }
        try:
            accounting_resp = requests.post(
                    ACCOUNTING_ADMIN_UPDATE_URL,
                    json=accounting_payload,
                    headers={"Authorization": f"Bearer {ACCOUNTING_API_TOKEN}"},
                    timeout=15,
                )
            accounting_resp.raise_for_status()
        except requests.RequestException as e:
            cursor.close()
            mydb.close()
            body = getattr(e.response, "text", str(e))
            return {
                    "error": "Accounting agent update failed, no update was made.",
                    "detail": body,
                }, 502

        return {"success": "User details updated successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()