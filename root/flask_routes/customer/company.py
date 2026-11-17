# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from root.auth.check import token_auth

# load_dotenv()

# app_file471 = Blueprint('app_file471', __name__)

# # =========================
# # GET COMPANIES
# # =========================
# @app_file471.route("/companies", methods=["GET"])
# @cross_origin()
# def get_companies():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True)

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- FETCH COMPANIES --------
#         query = """
#             SELECT 
#                 id,
#                 company_name,
#                 contact_person,
#                 address,
#                 phone,
#                 email,
#                 pan_number,
#                 company_type,
#                 status,
#                 source,
#                 outlet_company_id,
#                 created_at
#             FROM companies
#             ORDER BY id DESC
#         """

#         cursor.execute(query)
#         companies = cursor.fetchall()

#         mydb.close()

#         return jsonify({
#             "total_companies": len(companies),
#             "companies": companies
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500


# # =========================
# # CREATE COMPANY
# # =========================
# @app_file471.route("/companies", methods=["POST"])
# @cross_origin()
# def create_company():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True)

#         data = request.get_json() or {}

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         company_name = data.get("company_name")
#         contact_person = data.get("contact_person")
#         email = data.get("email")
#         address = data.get("address")
#         phone = data.get("phone")
#         company_type = data.get("company_type")
#         source = data.get("source")
#         pan_number = data.get("pan_number")

#         if not company_name or not phone:
#             return {"error": "company_name and phone are required"}, 400

#         # -------- CHECK EXISTING --------
#         cursor.execute("""
#             SELECT id FROM companies
#             WHERE email = %s OR phone = %s
#         """, (email, phone))

#         existing = cursor.fetchone()
#         if existing:
#             return {"error": "Company with this email or phone already exists"}, 400

#         # -------- INSERT --------
#         insert_query = """
#             INSERT INTO companies (
#                 company_name,
#                 contact_person,
#                 email,
#                 address,
#                 phone,
#                 company_type,
#                 source,
#                 pan_number,
#                 outlet_company_id
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """

#         values = (
#             company_name,
#             contact_person,
#             email,
#             address,
#             phone,
#             company_type,
#             source,
#             pan_number,
#             None  # outlet_company_id
#         )

#         cursor.execute(insert_query, values)
#         mydb.commit()

#         company_id = cursor.lastrowid
#         mydb.close()

#         return jsonify({
#             "message": "Company created successfully",
#             "company_id": company_id
#         }), 201

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

load_dotenv()

app_file471 = Blueprint('app_file471', __name__)

# =========================
# GET COMPANIES
# =========================
@app_file471.route("/companies", methods=["GET"])
@cross_origin()
def get_companies():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True)

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

        # -------- OUTLET FILTER (from query param) --------
        outlet = request.args.get("outlet")

        # -------- FETCH COMPANIES --------
        query = """
            SELECT 
                id,
                company_name,
                outlet,
                contact_person,
                address,
                phone,
                email,
                pan_number,
                company_type,
                status,
                source,
                outlet_company_id,
                created_at
            FROM companies
        """
        params = []

        if outlet:
            query += " WHERE outlet = %s"
            params.append(outlet)

        query += " ORDER BY id DESC"

        cursor.execute(query, tuple(params))
        companies = cursor.fetchall()

        mydb.close()

        return jsonify({
            "total_companies": len(companies),
            "companies": companies
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500


# =========================
# CREATE COMPANY
# =========================
# =========================
# CREATE COMPANY
# =========================
@app_file471.route("/companies", methods=["POST"])
@cross_origin()
def create_company():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True)

        data = request.get_json() or {}

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
        company_name = data.get("company_name")
        outlet = data.get("outlet")
        contact_person = data.get("contact_person")
        email = data.get("email")
        address = data.get("address")
        phone = data.get("phone")
        company_type = data.get("company_type")
        source = data.get("source")
        pan_number = data.get("pan_number")

        if not company_name or not phone:
            return {"error": "company_name and phone are required"}, 400

        # -------- CHECK EXISTING --------
        cursor.execute("""
            SELECT id FROM companies
            WHERE phone = %s
        """, (phone,))

        existing = cursor.fetchone()
        if existing:
            return {"error": "Company with this email or phone already exists"}, 400

        # -------- INSERT --------
        insert_query = """
            INSERT INTO companies (
                company_name,
                outlet,
                contact_person,
                email,
                address,
                phone,
                company_type,
                source,
                pan_number,
                outlet_company_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            company_name,
            outlet,
            contact_person,
            email,
            address,
            phone,
            company_type,
            source,
            pan_number,
            None  # outlet_company_id
        )

        cursor.execute(insert_query, values)
        mydb.commit()

        company_id = cursor.lastrowid
        mydb.close()

        return jsonify({
            "message": "Company created successfully",
            "company_id": company_id
        }), 201

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500