from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()
from root.auth.check import token_auth

app_file405 = Blueprint('app_file405', __name__)

@app_file405.route("/get_today_room_nos", methods=["POST"])
@cross_origin()
def get_today_room_nos():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        today_date = date.today()

        # Get guest reservations ending today
        cursor.execute("""
            SELECT Reservation_ID FROM hotel_tblguestreservation
            WHERE end_date = %s
        """, (today_date,))
        reservations_today = cursor.fetchall()

        room_numbers = []

        for res in reservations_today:
            reservation_id = res["Reservation_ID"]

            # Get reservation details for each reservation
            cursor.execute("""
                SELECT rd.room_id, r.room_no, r.room_state
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblrooms r ON rd.room_id = r.id
                WHERE rd.Reservation_ID = %s
            """, (reservation_id,))
            reservation_details = cursor.fetchall()

            for rd in reservation_details:
                if rd["room_state"] != "Vacant":
                    room_numbers.append(rd["room_no"])

        mydb.close()

        return jsonify({"room_numbers": room_numbers}), 200

    except Exception as e:
        return {"error": str(e)}, 400