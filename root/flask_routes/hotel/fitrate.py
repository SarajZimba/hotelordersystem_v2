from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
from root.auth.check import token_auth

app_file407 = Blueprint('app_file407', __name__)

@app_file407.route("/fitrate-create", methods=["POST"])
@cross_origin()
def create_fitrate():
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

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        rateID = json_data.get("rateID")
        mealID = json_data.get("mealID")
        reservationID = json_data.get("reservationID")
        quantity = json_data.get("quantity", 1)

        if not rateID or not reservationID:
            return {"error": "rateID and reservationID are required"}, 400

        # Optional mealID validation
        if mealID:
            cursor.execute(
                "SELECT id FROM hotel_tblmeal_price WHERE id=%s",
                (mealID,)
            )
            if not cursor.fetchone():
                return {"error": "Invalid mealID"}, 404

        # Validate rate
        cursor.execute(
            "SELECT id FROM hotel_tblrates WHERE id=%s",
            (rateID,)
        )
        if not cursor.fetchone():
            return {"error": "Invalid rateID"}, 404

        # Validate reservation
        cursor.execute(
            "SELECT id FROM hotel_tblreservation WHERE id=%s",
            (reservationID,)
        )
        if not cursor.fetchone():
            return {"error": "Invalid reservationID"}, 404

        insert_sql = """
            INSERT INTO hotel_tblfitrate
            (rateID, mealID, reservationID, quantity, is_active)
            VALUES (%s, %s, %s, %s, 1)
        """

        cursor.execute(insert_sql, (
            rateID,
            mealID,
            reservationID,
            quantity
        ))

        # ✅ CHECK reservation_outlet_id FIRST
        cursor.execute(
                """
                SELECT reservation_outlet_id 
                FROM hotel_tblreservation 
                WHERE id = %s
                """,
            (reservationID,)
        )
        result = cursor.fetchone()

        if result and result['reservation_outlet_id']:
            # ✅ Only update if reservation_outlet_id has value (synced)
            cursor.execute(
                    """
                    UPDATE hotel_tblreservation
                    SET is_updated = TRUE, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (reservationID,)
            )

        mydb.commit()

        created_id = cursor.lastrowid

        mydb.close()

        return jsonify({
            "message": "FIT Rate created successfully",
            "id": created_id
        }), 201

    except Exception as e:
        return {"error": str(e)}, 400
    

@app_file407.route("/fitrate-delete", methods=["POST"])
@cross_origin()
def delete_fitrate():
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

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        rateID = json_data.get("rateID")
        reservationID = json_data.get("reservationID")
        mealID = json_data.get("mealID")

        if not rateID or not reservationID or not mealID:
            return {"error": "rateID, reservationID and mealID are required"}, 400

        # Check if record exists
        cursor.execute(
            """
            SELECT id FROM hotel_tblfitrate
            WHERE rateID=%s AND reservationID=%s AND mealID=%s
            """,
            (rateID, reservationID, mealID)
        )

        fitrate = cursor.fetchone()

        if not fitrate:
            return {"message": "FITrate not found"}, 404

        # Delete record
        cursor.execute(
            """
            DELETE FROM hotel_tblfitrate
            WHERE rateID=%s AND reservationID=%s AND mealID=%s
            """,
            (rateID, reservationID, mealID)
        )

        # ✅ CHECK reservation_outlet_id FIRST
        cursor.execute(
                """
                SELECT reservation_outlet_id 
                FROM hotel_tblreservation 
                WHERE id = %s
                """,
            (reservationID,)
        )
        result = cursor.fetchone()

        if result and result['reservation_outlet_id']:
            # ✅ Only update if reservation_outlet_id has value (synced)
            cursor.execute(
                    """
                    UPDATE hotel_tblreservation
                    SET is_updated = TRUE, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (reservationID,)
            )

        mydb.commit()
        mydb.close()

        return {"message": "FITrate deleted successfully"}, 200

    except Exception as e:
        return {"message": str(e)}, 500

@app_file407.route("/fitrate-delete-by-id", methods=["POST"])
@cross_origin()
def delete_fitrate_by_id():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        json_data = request.get_json() or {}
        fitrate_id = json_data.get("fitrate_id") or json_data.get("id")

        if not fitrate_id:
            return {"error": "fitrate_id is required"}, 400
        try:
            fitrate_id = int(fitrate_id)
        except (TypeError, ValueError):
            return {"error": "fitrate_id must be a number"}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- FIND THE RECORD (locked) --------
        cursor.execute(
            "SELECT id, reservationID FROM hotel_tblfitrate WHERE id = %s FOR UPDATE",
            (fitrate_id,)
        )
        fitrate = cursor.fetchone()

        if not fitrate:
            return {"message": "FITrate not found"}, 404

        reservationID = fitrate["reservationID"]

        # optional safety check: if the caller also sends reservationID, it must match
        sent_reservation = json_data.get("reservationID")
        if sent_reservation and str(sent_reservation) != str(reservationID):
            return {"error": "This FITrate does not belong to that reservation."}, 400

        # -------- DELETE --------
        cursor.execute("DELETE FROM hotel_tblfitrate WHERE id = %s", (fitrate_id,))

        # -------- MARK THE RESERVATION AS UPDATED (only if it is synced) --------
        cursor.execute(
            "SELECT reservation_outlet_id FROM hotel_tblreservation WHERE id = %s",
            (reservationID,)
        )
        result = cursor.fetchone()

        if result and result["reservation_outlet_id"]:
            cursor.execute(
                """
                UPDATE hotel_tblreservation
                SET is_updated = TRUE, updated_at = NOW()
                WHERE id = %s
                """,
                (reservationID,)
            )

        mydb.commit()

        return {
            "message": "FITrate deleted successfully",
            "fitrate_id": fitrate_id,
            "reservationID": reservationID
        }, 200

    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
            except Exception:
                pass
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass