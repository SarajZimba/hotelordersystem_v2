from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

load_dotenv()

app_file470 = Blueprint('app_file470', __name__)

@app_file470.route("/customers", methods=["GET"])
@cross_origin()
def get_customers():
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

        # -------- FETCH CUSTOMERS --------
        query = """
            SELECT 
                id,
                name,
                address,
                phone,
                email,
                status,
                source,
                guestPan,
                outlet_guest_id,
                customer_type, 
                country
            FROM customers
            ORDER BY id DESC
        """

        cursor.execute(query)
        customers = cursor.fetchall()

        mydb.close()

        return jsonify({
            "total_customers": len(customers),
            "customers": customers
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500


@app_file470.route("/customers", methods=["POST"])
@cross_origin()
def create_customer():
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

        # -------- INPUT VALIDATION --------
        name = data.get("name")
        email = data.get("email")
        address = data.get("address")
        contact_number = data.get("contact_number")
        customer_type = data.get("customer_type")
        created_by = data.get("created_by")
        tax_number = data.get("tax_number")
        country = data.get("country")

        if not name or not contact_number:
            return {"error": "Name and contact_number are required"}, 400

        if email != '':
            # -------- OPTIONAL: Check if email or phone exists --------
            cursor.execute("""
                SELECT id FROM customers
                WHERE email = %s OR phone = %s
            """, (email, contact_number))
            existing = cursor.fetchone()
            if existing:
                return {"error": "Customer with this email or phone already exists"}, 400

        # -------- INSERT CUSTOMER --------
        insert_query = """
            INSERT INTO customers (
                name,
                email,
                address,
                phone,
                customer_type,
                source,
                guestPan,
                outlet_guest_id, 
                country
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            email,
            address,
            contact_number,
            customer_type,
            created_by,
            tax_number,
            None,  # outlet_guest_id,
            country
        )

        cursor.execute(insert_query, values)
        mydb.commit()

        customer_id = cursor.lastrowid
        mydb.close()

        return jsonify({
            "message": "Customer created successfully",
            "customer_id": customer_id
        }), 201

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500