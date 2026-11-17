from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

app_file500 = Blueprint('app_file500', __name__)
from root.auth.check import token_auth

@app_file500.route("/frontoffice/activity_log", methods=["GET"])
@cross_origin()
def hotel_activity_log():

    # ... same token check as your other GET endpoints ...

    # -------- TOKEN FROM HEADER --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400

    try:
        token = auth_header.split(" ")[1]  # Remove "Bearer"
    except Exception:
        return {"error": "Invalid Authorization header format."}, 400

    if not token:
        return {"error": "No token provided."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- DB --------
    mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
    )
    cursor = mydb.cursor(dictionary=True, buffered=True)
    outlet = request.args.get("outlet")
    if not outlet:
        return {"error": "outlet is required"}, 400

    where, params = ["outlet = %s"], [outlet]
    if request.args.get("from_date"):
        where.append("created_at >= %s"); params.append(request.args["from_date"])
    if request.args.get("to_date"):
        where.append("created_at < DATE_ADD(%s, INTERVAL 1 DAY)"); params.append(request.args["to_date"])
    if request.args.get("reservation_id"):
        where.append("reservation_id = %s"); params.append(request.args["reservation_id"])
    if request.args.get("action"):
        where.append("action = %s"); params.append(request.args["action"].upper())

    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))

    cursor.execute(f"""
        SELECT id, reservation_id, action, description, employee_id, employee_name,
               details, created_at
        FROM hotel_activity_log
        WHERE {' AND '.join(where)}
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, params + [limit, offset])
    return jsonify({"logs": cursor.fetchall()}), 200