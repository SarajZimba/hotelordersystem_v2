# from flask import  Blueprint,request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# load_dotenv()
# app_file4 = Blueprint('app_file4',__name__)


# @app_file4.route("/login", methods=["POST"])
# @cross_origin()
# def login():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(buffered=True)
#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)
#         json = request.get_json()
#         if "username" not in json or "password" not in json or not any([json["username"],json["password"]]) or json["username"] =="" or json["password"]=="":
#             data = {"error":"Some fields missing."}
#             return data,400
#         uname = json["username"]
#         upass = json["password"]
#         get_outlet_sql =f"""select Token, type, id from EmployeeLogin where userName=%s and Password=%s"""
#         cursor.execute(get_outlet_sql,(uname,upass,),)
#         result = cursor.fetchall()
#         if result == []:
#             data = {"error":"No data available."}
#             return data,400
#         token = {"token":str(result[0][0]), "type": result[0][1], "id": result[0][2]}
#         mydb.close()
#         return token,200
#     except Exception as error:
#         data ={'error':str(error)}
#         return data,400


# from flask import  Blueprint,request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# load_dotenv()
# app_file4 = Blueprint('app_file4',__name__)

# import os
# import requests
# import mysql.connector
# from flask import Blueprint, request
# from flask_cors import cross_origin
# from dotenv import load_dotenv

# load_dotenv()

# ACCOUNTING_LOGIN_URL = os.getenv("accounting_url") + "api/login/"

# app_file4 = Blueprint("app_file4", __name__)


# @app_file4.route("/login", methods=["POST"])
# @cross_origin()
# def login():
#     mydb = None
#     cursor = None

#     try:
#         json_data = request.get_json()

#         if (
#             "username" not in json_data
#             or "password" not in json_data
#             or not json_data["username"]
#             or not json_data["password"]
#         ):
#             return {"error": "Some fields missing."}, 400

#         uname = json_data["username"]
#         upass = json_data["password"]

#         # -----------------------------
#         # Check restaurant/POS user
#         # -----------------------------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(buffered=True)

#         get_user_sql = """
#             SELECT Token, type, id
#             FROM EmployeeLogin
#             WHERE userName = %s AND Password = %s
#         """

#         cursor.execute(get_user_sql, (uname, upass))
#         result = cursor.fetchone()

#         if not result:
#             return {"error": "No data available."}, 400

#         restaurant_token = str(result[0])
#         user_type = result[1]
#         employee_id = result[2]

#         # -----------------------------
#         # Login to accounting system
#         # -----------------------------
#         accounting_token = None
#         accounting_response = None

#         try:
#             accounting_resp = requests.post(
#                 ACCOUNTING_LOGIN_URL,
#                 json={
#                     "username": uname,
#                     "password": upass
#                 },
#                 timeout=15
#             )

#             accounting_response = accounting_resp.json()

#             if accounting_resp.status_code == 200:
#                 accounting_token = accounting_response.get("access")

#         except requests.RequestException as e:
#             print("Accounting login failed:", str(e))

#         # -----------------------------
#         # Response to frontend
#         # -----------------------------
#         return {
#             "token": restaurant_token,
#             "type": user_type,
#             "id": employee_id,
#             "accounting_token": accounting_token
#         }, 200

#     except Exception as error:
#         return {
#             "error": str(error)
#         }, 400

#     finally:
#         if cursor:
#             cursor.close()

#         if mydb:
#             mydb.close()




import os
import requests
import mysql.connector
from flask import Blueprint, request
from flask_cors import cross_origin
from dotenv import load_dotenv

load_dotenv()

ACCOUNTING_LOGIN_URL = os.getenv("accounting_url") + "api/login/"

app_file4 = Blueprint("app_file4", __name__)

import base64
import json

def get_user_id_from_token(token):
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # fix base64 padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("user_id")
    except Exception as e:
        print("Failed to decode accounting token:", str(e))
        return None


@app_file4.route("/login", methods=["POST"])
@cross_origin()
def login():
    mydb = None
    cursor = None

    try:
        json_data = request.get_json()

        if (
            "username" not in json_data
            or "password" not in json_data
            or not json_data["username"]
            or not json_data["password"]
        ):
            return {"error": "Some fields missing."}, 400

        uname = json_data["username"]
        upass = json_data["password"]

        # -----------------------------
        # Check restaurant/POS user
        # -----------------------------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(buffered=True)

        get_user_sql = """
            SELECT Token, type, id
            FROM EmployeeLogin
            WHERE userName = %s AND Password = %s
        """

        cursor.execute(get_user_sql, (uname, upass))
        result = cursor.fetchone()

        if not result:
            return {"error": "No data available."}, 400

        restaurant_token = str(result[0])
        user_type = result[1]
        employee_id = result[2]

        # -----------------------------
        # Login to accounting system
        # -----------------------------
        accounting_token = None
        accounting_response = None

        try:
            accounting_resp = requests.post(
                ACCOUNTING_LOGIN_URL,
                json={
                    "username": uname,
                    "password": upass
                },
                timeout=15
            )

            accounting_response = accounting_resp.json()

            if accounting_resp.status_code == 200:
                accounting_token = accounting_response.get("access")
                accounting_branch = accounting_response.get("branch")

                if accounting_token:
                    accounting_user_id = get_user_id_from_token(accounting_token)

        except requests.RequestException as e:
            print("Accounting login failed:", str(e))

        # -----------------------------
        # Response to frontend
        # -----------------------------
        return {
            "token": restaurant_token,
            "type": user_type,
            "id": employee_id,
            "accounting_token": accounting_token,
            "accounting_user_id": accounting_user_id,
            "accounting_branch": accounting_branch

        }, 200

    except Exception as error:
        return {
            "error": str(error)
        }, 400

    finally:
        if cursor:
            cursor.close()

        if mydb:
            mydb.close()