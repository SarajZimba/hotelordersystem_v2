
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
from root.auth.check import token_auth

app_file408 = Blueprint('app_file408', __name__)
@app_file408.route("/unique-outlets", methods=["POST"])
@cross_origin()
def unique_reservation_outlets():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)

        json_data = request.get_json() or {}
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        query = """
            SELECT DISTINCT outlet
            FROM hotel_tblreservation
            WHERE outlet IS NOT NULL
            AND outlet != ''
            ORDER BY outlet
        """

        cursor.execute(query)
        results = cursor.fetchall()

        outlets = [row["outlet"] for row in results]

        mydb.close()

        return jsonify({
            "count": len(outlets),
            "outlets": outlets
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500