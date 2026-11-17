from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()

app_file40 = Blueprint('app_file40', __name__)
from root.auth.check import token_auth

@app_file40.route('/userlists', methods=['POST'])

@cross_origin()
def userslist():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json =request.get_json()

        if "token" not in json or not any([json["token"]]) or json["token"] == "":
            data = {"error": "No token provided"}
            return data, 400 
        if "username" not in json or not any([json["username"]]) or json["username"] == "":
            data = {"error": "No username provided"}
            return data, 400 
        token = json["token"]
        username = json["username"]
        if not token_auth(token):
            data = {"error": "Invalid token"}
            return data, 400
        getUserlist_query = """select * from EmployeeLogin where userName != %s"""
        cursor.execute(getUserlist_query, (username,))
        result = cursor.fetchall()
        if result == []:
            data = {"error":"Temporary Unavailable"}
            return data, 400
        
        users_list = []

        for row in result:
            data  = {
                "id": row[0],
                "username" : row[1],
                "password" : row[2],
                "type": row[5]
            }
            users_list.append(data)

        return {"users":users_list}, 200
        
    except Exception as e:
        data = {'error': str(e)}

        return data, 400 

@app_file40.route('/hotel-userlists', methods=['POST'])
@cross_origin()
def hoteluserslist():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(dictionary=True, buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

        json_data = request.get_json() or {}

        # -------- TOKEN --------
        token = json_data.get("token")
        if not token:
            return {"error": "No token provided"}, 400
        if not token_auth(token):
            return {"error": "Invalid token"}, 400

        # -------- INPUT --------
        user_id = json_data.get("user_id")
        if not user_id:
            return {"error": "No user_id provided"}, 400

        # -------- GET REQUESTING USER --------
        cursor.execute("SELECT id, userName, type FROM EmployeeLogin WHERE id = %s", (user_id,))
        requesting_user = cursor.fetchone()

        if not requesting_user:
            return {"error": "User not found"}, 400

        user_type = requesting_user["type"]

        # -------- RESTAURANT AGENT: no user list --------
        if user_type == "restaurantagent":
            return {"users": []}, 200

        # -------- ADMIN: all users --------
        if user_type == "admin":
            cursor.execute("""
                SELECT id, userName, type, password
                FROM EmployeeLogin
                WHERE id != %s
            """, (user_id,))
            result = cursor.fetchall()

            users_list = [
                {"id": row["id"], "username": row["userName"], "type": row["type"], "password": row["password"]}
                for row in result
            ]
            return {"users": users_list}, 200

        # -------- HOTEL AGENT: restaurant agents of restaurants under their hotels --------
        if user_type == "hotelagent":
            # 1. Hotels this hotelagent has access to
            cursor.execute("""
                SELECT property_id
                FROM hotel_employee_property_access
                WHERE employee_id = %s
            """, (user_id,))
            property_ids = [row["property_id"] for row in cursor.fetchall()]

            if not property_ids:
                return {"users": []}, 200

            # 2. Restaurants (outlets) under those hotels
            format_strings = ','.join(['%s'] * len(property_ids))
            cursor.execute(f"""
                SELECT id
                FROM outetNames
                WHERE company_property_id IN ({format_strings})
            """, tuple(property_ids))
            outlet_ids = [row["id"] for row in cursor.fetchall()]

            if not outlet_ids:
                return {"users": []}, 200

            # 3. Restaurant agents who have access to those restaurants
            format_strings = ','.join(['%s'] * len(outlet_ids))
            cursor.execute(f"""
                SELECT DISTINCT e.id, e.userName, e.type, e.password
                FROM employeeoutlets eo
                JOIN EmployeeLogin e ON eo.employee_id = e.id
                WHERE eo.outlet_id IN ({format_strings})
                AND e.type = 'restaurantagent'
                AND e.id != %s
            """, tuple(outlet_ids) + (user_id,))
            result = cursor.fetchall()

            users_list = [
                {"id": row["id"], "username": row["userName"], "type": row["type"], "password": row["password"]}
                for row in result
            ]
            return {"users": users_list}, 200

        # -------- UNKNOWN TYPE --------
        return {"error": f"Unrecognized user type: {user_type}"}, 400

    except Exception as e:
        return {"error": str(e)}, 400