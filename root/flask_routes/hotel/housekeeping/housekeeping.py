from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

load_dotenv()
app_file495 = Blueprint('app_file495', __name__)
from root.auth.check import token_auth
from datetime import date, datetime

# @app_file495.route("/rooms/<int:room_id>/housekeeping", methods=["POST"])
# @cross_origin()
# def update_housekeeping(room_id):
#     data = request.get_json() or {}
#     status = data.get("hk_status")                       # Dirty | Clean | Inspected
#     hk_date = data.get("date") or str(date.today())
#     if status not in ("Dirty", "Clean", "Inspected"):
#         return jsonify({"error": "Invalid hk_status"}), 400
#     mydb = mysql.connector.connect(host=os.getenv("host"), user=os.getenv("user"),
#                                    password=os.getenv("password"), database=os.getenv("database"))
#     cursor = mydb.cursor()
#     cleaned = status in ("Clean", "Inspected")
#     cursor.execute("""
#         INSERT INTO hotel_tblhousekeeping
#             (room_id, hk_date, hk_status, cleaned_at, cleaned_by, remarks)
#         VALUES (%s, %s, %s, IF(%s, NOW(), NULL), %s, %s)
#         ON DUPLICATE KEY UPDATE
#             hk_status = VALUES(hk_status), cleaned_at = VALUES(cleaned_at),
#             cleaned_by = VALUES(cleaned_by), remarks = VALUES(remarks)
#     """, (room_id, hk_date, status, cleaned, data.get("cleaned_by"), data.get("remarks")))
#     mydb.commit(); mydb.close()
#     return jsonify({"message": "Updated"}), 200


@app_file495.route("/rooms/housekeeping", methods=["POST"])               # bulk
@app_file495.route("/rooms/<int:room_id>/housekeeping", methods=["POST"]) # single (still works)
@cross_origin()
def update_housekeeping(room_id=None):
    data = request.get_json() or {}
    status = data.get("hk_status")                       # Dirty | Clean | Inspected
    if status not in ("Dirty", "Clean", "Inspected"):
        return jsonify({"error": "Invalid hk_status"}), 400

    # Collect room ids: from the URL, or from "room_ids" in the body
    if room_id is not None:
        room_ids = [room_id]
    else:
        room_ids = data.get("room_ids")
        if not isinstance(room_ids, list) or not room_ids:
            return jsonify({"error": "room_ids must be a non-empty list"}), 400
        try:
            room_ids = list({int(r) for r in room_ids})   # ints, de-duplicated
        except (TypeError, ValueError):
            return jsonify({"error": "room_ids must contain only integers"}), 400

    hk_date = data.get("date") or str(date.today())
    try:
        datetime.strptime(hk_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    cleaned_at = datetime.now() if status in ("Clean", "Inspected") else None
    cleaned_by = data.get("cleaned_by")
    remarks = data.get("remarks")

    mydb = None
    try:
        mydb = mysql.connector.connect(host=os.getenv("host"), user=os.getenv("user"),
                                       password=os.getenv("password"), database=os.getenv("database"))
        cursor = mydb.cursor(dictionary=True)

        # Only update rooms that exist and are active; report the rest
        placeholders = ",".join(["%s"] * len(room_ids))
        cursor.execute(
            f"SELECT id FROM hotel_tblrooms WHERE is_active = 1 AND id IN ({placeholders})",
            room_ids
        )
        valid_ids = [r["id"] for r in cursor.fetchall()]
        not_found = [r for r in room_ids if r not in valid_ids]

        if not valid_ids:
            mydb.close()
            return jsonify({"error": "No valid rooms found", "not_found": not_found}), 404

        cursor.executemany("""
            INSERT INTO hotel_tblhousekeeping
                (room_id, hk_date, hk_status, cleaned_at, cleaned_by, remarks)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                hk_status = VALUES(hk_status), cleaned_at = VALUES(cleaned_at),
                cleaned_by = VALUES(cleaned_by), remarks = VALUES(remarks)
        """, [(rid, hk_date, status, cleaned_at, cleaned_by, remarks) for rid in valid_ids])

        mydb.commit()
        mydb.close()
        return jsonify({
            "message": "Updated",
            "updated": valid_ids,
            "not_found": not_found
        }), 200

    except Exception as e:
        if mydb is not None:
            try:
                mydb.rollback()
                mydb.close()
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500


@app_file495.route("/rooms/<int:room_id>/out-of-order", methods=["POST", "DELETE"])
@cross_origin()
def room_out_of_order(room_id):
    mydb = mysql.connector.connect(host=os.getenv("host"), user=os.getenv("user"),
                                   password=os.getenv("password"), database=os.getenv("database"))
    cursor = mydb.cursor(dictionary=True)
    if request.method == "POST":
        d = request.get_json() or {}
        start, end = d.get("start_date"), d.get("end_date")
        if not start or not end or end < start:
            mydb.close()
            return jsonify({"error": "start_date and end_date (YYYY-MM-DD) required"}), 400

        # Reject if a guest is in the room, or a booking overlaps the block
        cursor.execute("""
            SELECT 1
            FROM hotel_tblreservation_details rd
            JOIN hotel_tblreservation res
                ON rd.Reservation_ID = res.id AND res.is_active = 1
            JOIN (SELECT Reservation_ID, MIN(start_date) s, MAX(end_date) e
                  FROM hotel_tblguestreservation WHERE is_active = 1
                  GROUP BY Reservation_ID) st ON st.Reservation_ID = res.id
            WHERE rd.room_id = %s AND rd.is_active = 1 AND rd.is_current = 1
              AND (
                    (res.Current_Status = 'Registered'
                     AND (st.e >= %s OR st.e < CURDATE()))   -- in-house, or overdue
                 OR (res.Current_Status = 'Reserved'
                     AND st.s <= %s AND st.e >= %s)          -- future booking overlaps
              )
            LIMIT 1
        """, (room_id, start, end, start))
        if cursor.fetchone():
            mydb.close()
            return jsonify({"error": "Room has a guest in it or a reservation in these dates"}), 409

        cursor.execute("""
            INSERT INTO hotel_tblroom_blocks
                (room_id, block_type, start_date, end_date, reason, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (room_id, d.get("block_type", "Out of Order"), start, end,
              d.get("reason"), d.get("created_by")))

    else:  # DELETE = release the room early (fixed)
        cursor.execute("""
            UPDATE hotel_tblroom_blocks SET released_at = NOW()
            WHERE room_id = %s AND is_active = 1 AND released_at IS NULL
              AND start_date <= CURDATE() AND end_date >= CURDATE()
        """, (room_id,))
        if cursor.rowcount == 0:
            mydb.close()
            return jsonify({"error": "No active out-of-order block for this room"}), 404

    mydb.commit()
    mydb.close()
    return jsonify({"message": "OK"}), 200


@app_file495.route("/rooms/room-blocks", methods=["GET"])
@cross_origin()
def list_out_of_order():
    outlet = request.args.get("outlet")

    mydb = mysql.connector.connect(host=os.getenv("host"), user=os.getenv("user"),
                                   password=os.getenv("password"), database=os.getenv("database"))
    cursor = mydb.cursor(dictionary=True)

    sql = """
        SELECT b.id AS block_id, b.room_id, r.room_no, r.room_type, r.outlet,
               b.block_type, b.start_date, b.end_date, b.reason, b.created_by,
               b.released_at, b.created_at
        FROM hotel_tblroom_blocks b
        JOIN hotel_tblrooms r ON r.id = b.room_id
        WHERE b.is_active = 1
    """
    params = []
    if outlet:
        sql += " AND r.outlet = %s"
        params.append(outlet)
    sql += " ORDER BY b.start_date DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    mydb.close()

    for r in rows:
        for k in ("start_date", "end_date", "released_at", "created_at"):
            r[k] = str(r[k]) if r[k] else None
    return jsonify(rows), 200


# @app_file495.route("/rooms/out-of-order", methods=["GET"])
# @cross_origin()
# def list_out_of_order():
#     outlet = request.args.get("outlet")
#     status = request.args.get("status", "active")    # active | upcoming | completed | released | all

#     mydb = mysql.connector.connect(host=os.getenv("host"), user=os.getenv("user"),
#                                    password=os.getenv("password"), database=os.getenv("database"))
#     cursor = mydb.cursor(dictionary=True)

#     sql = """
#         SELECT b.id AS block_id, b.room_id, r.room_no, r.room_type, r.outlet,
#                b.block_type, b.start_date, b.end_date, b.reason, b.created_by,
#                b.released_at, b.created_at,
#                CASE
#                  WHEN b.released_at IS NOT NULL THEN 'released'
#                  WHEN b.start_date <= CURDATE() AND b.end_date >= CURDATE() THEN 'active'
#                  WHEN b.start_date > CURDATE() THEN 'upcoming'
#                  ELSE 'completed'
#                END AS block_status
#         FROM hotel_tblroom_blocks b
#         JOIN hotel_tblrooms r ON r.id = b.room_id
#         WHERE b.is_active = 1
#     """
#     params = []
#     if outlet:
#         sql += " AND r.outlet = %s"
#         params.append(outlet)
#     sql += " ORDER BY b.start_date DESC"

#     cursor.execute(sql, params)
#     rows = cursor.fetchall()
#     mydb.close()

#     if status != "all":
#         rows = [r for r in rows if r["block_status"] == status]
#     for r in rows:
#         for k in ("start_date", "end_date", "released_at", "created_at"):
#             r[k] = str(r[k]) if r[k] else None
#     return jsonify(rows), 200