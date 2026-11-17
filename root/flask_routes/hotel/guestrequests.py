import os
from datetime import datetime

import mysql.connector
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from root.auth.check import token_auth

# Assumes app_file496 and token_auth already exist in your module.

REQUEST_TYPES = ("Housekeeping", "Maintenance", "Amenity", "Laundry",
                 "Room Service", "Wake-up Call", "Other")
PRIORITIES = ("Low", "Medium", "High", "Urgent")
STATUSES = ("Open", "In Progress", "Completed", "Cancelled")
DT_FIELDS = ("requested_at", "due_at", "completed_at", "created_at", "updated_at")

SELECT_REQUEST = """
    SELECT g.*, r.room_no, r.floor, r.room_type
    FROM hotel_tblguest_requests g
    JOIN hotel_tblrooms r ON r.id = g.room_id
    WHERE g.is_active = 1
"""


# ---------------- helpers ----------------
def _gr_conn():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database"),
    )


def _gr_token_error():
    """Returns an error response tuple, or None if the token is valid."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400
    return None


def _gr_parse_dt(value):
    """Accepts 'YYYY-MM-DD HH:MM[:SS]' (or with a 'T'). Empty -> None."""
    if value in (None, ""):
        return None
    s = str(value).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError("Date/time must look like YYYY-MM-DD HH:MM")


def _gr_clean(value):
    """Trim a string; empty becomes None."""
    if value is None:
        return None
    return str(value).strip() or None


def _gr_serialize(row):
    for k in DT_FIELDS:
        if row.get(k):
            row[k] = str(row[k])
    return row

app_file496 = Blueprint('app_file496', __name__)
from root.auth.check import token_auth


# ---------------- LIST ----------------
@app_file496.route("/guest-requests", methods=["GET"])
@cross_origin()
def list_guest_requests():
    outlet = request.args.get("outlet")
    room_id = request.args.get("room_id")
    reservation_id = request.args.get("reservation_id")
    req_type = request.args.get("type")
    priority = request.args.get("priority")
    status = request.args.get("status")          # one or comma separated: Open,In Progress
    date_arg = request.args.get("date")          # requests logged on this date
    try:
        limit = min(max(int(request.args.get("limit", 200)), 1), 500)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"error": "limit and offset must be numbers"}), 400

    sql = SELECT_REQUEST
    params = []

    if outlet:
        sql += " AND g.outlet = %s"
        params.append(outlet)
    if room_id:
        sql += " AND g.room_id = %s"
        params.append(room_id)
    if reservation_id:
        sql += " AND g.reservation_id = %s"
        params.append(reservation_id)
    if req_type:
        sql += " AND g.request_type = %s"
        params.append(req_type)
    if priority:
        if priority not in PRIORITIES:
            return jsonify({"error": f"priority must be one of {list(PRIORITIES)}"}), 400
        sql += " AND g.priority = %s"
        params.append(priority)
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if any(s not in STATUSES for s in statuses):
            return jsonify({"error": f"status must be from {list(STATUSES)}"}), 400
        sql += " AND g.status IN (" + ",".join(["%s"] * len(statuses)) + ")"
        params.extend(statuses)
    if date_arg:
        try:
            datetime.strptime(date_arg, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        sql += " AND DATE(g.requested_at) = %s"
        params.append(date_arg)

    # open work first, then by priority, oldest first
    sql += """
        ORDER BY (g.status IN ('Completed','Cancelled')) ASC,
                 FIELD(g.priority, 'Urgent', 'High', 'Medium', 'Low'),
                 g.requested_at ASC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    mydb = None
    try:
        mydb = _gr_conn()
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(sql, params)
        rows = [_gr_serialize(r) for r in cursor.fetchall()]
        mydb.close()
        return jsonify(rows), 200
    except Exception as e:
        if mydb:
            mydb.close()
        return jsonify({"error": str(e)}), 500


# ---------------- READ ONE ----------------
@app_file496.route("/guest-requests/<int:req_id>", methods=["GET"])
@cross_origin()
def get_guest_request(req_id):
    mydb = None
    try:
        mydb = _gr_conn()
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(SELECT_REQUEST + " AND g.id = %s", (req_id,))
        row = cursor.fetchone()
        mydb.close()
        if not row:
            return jsonify({"error": f"Request {req_id} not found."}), 404
        return jsonify(_gr_serialize(row)), 200
    except Exception as e:
        if mydb:
            mydb.close()
        return jsonify({"error": str(e)}), 500


# ---------------- CREATE ----------------
@app_file496.route("/guest-requests", methods=["POST"])
@cross_origin()
def create_guest_request():
    err = _gr_token_error()
    if err:
        return err

    d = request.get_json() or {}
    room_id = d.get("room_id")
    request_type = d.get("request_type")
    description = _gr_clean(d.get("description"))
    priority = d.get("priority") or "Medium"

    if not room_id:
        return jsonify({"error": "room_id is required"}), 400
    if request_type not in REQUEST_TYPES:
        return jsonify({"error": f"request_type must be one of {list(REQUEST_TYPES)}"}), 400
    if not description:
        return jsonify({"error": "description is required"}), 400
    if priority not in PRIORITIES:
        return jsonify({"error": f"priority must be one of {list(PRIORITIES)}"}), 400
    try:
        due_at = _gr_parse_dt(d.get("due_at"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    mark_dirty = d.get("mark_room_dirty") in (True, "true", "True", "1", 1)

    mydb = None
    try:
        mydb = _gr_conn()
        cursor = mydb.cursor(dictionary=True, buffered=True)

        cursor.execute(
            "SELECT id, outlet FROM hotel_tblrooms WHERE id=%s AND is_active=1", (room_id,)
        )
        room = cursor.fetchone()
        if not room:
            mydb.close()
            return jsonify({"error": f"Room {room_id} not found."}), 404

        # Link to the guest currently in the room, unless a reservation was given
        reservation_id = d.get("reservation_id")
        if not reservation_id:
            cursor.execute("""
                SELECT res.id
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblreservation res
                    ON rd.Reservation_ID = res.id AND res.is_active = 1
                WHERE rd.room_id = %s AND rd.is_active = 1 AND rd.is_current = 1
                  AND res.Current_Status = 'Registered'
                LIMIT 1
            """, (room_id,))
            row = cursor.fetchone()
            reservation_id = row["id"] if row else None

        cursor.execute("""
            INSERT INTO hotel_tblguest_requests
                (outlet, room_id, reservation_id, request_type, description, priority,
                 requested_by, assigned_to, requested_at, due_at, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (room["outlet"], room_id, reservation_id, request_type, description, priority,
              _gr_clean(d.get("requested_by")), _gr_clean(d.get("assigned_to")),
              datetime.now(), due_at, _gr_clean(d.get("remarks"))))
        new_id = cursor.lastrowid

        # Optional: send the room back to housekeeping's dirty list for today
        if mark_dirty:
            cursor.execute("""
                INSERT INTO hotel_tblhousekeeping (room_id, hk_date, hk_status, remarks)
                VALUES (%s, CURDATE(), 'Dirty', %s)
                ON DUPLICATE KEY UPDATE
                    hk_status = 'Dirty', cleaned_at = NULL, cleaned_by = NULL,
                    remarks = VALUES(remarks)
            """, (room_id, f"Guest request: {request_type}"[:255]))

        mydb.commit()
        mydb.close()
        return jsonify({
            "message": "Request created",
            "id": new_id,
            "reservation_id": reservation_id,
            "room_marked_dirty": mark_dirty,
        }), 201

    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
                mydb.close()
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500


# ---------------- UPDATE ----------------
@app_file496.route("/guest-requests/<int:req_id>", methods=["PUT"])
@cross_origin()
def update_guest_request(req_id):
    err = _gr_token_error()
    if err:
        return err

    d = request.get_json() or {}
    updates = {}

    if "request_type" in d:
        if d["request_type"] not in REQUEST_TYPES:
            return jsonify({"error": f"request_type must be one of {list(REQUEST_TYPES)}"}), 400
        updates["request_type"] = d["request_type"]
    if "description" in d:
        desc = _gr_clean(d["description"])
        if not desc:
            return jsonify({"error": "description cannot be empty"}), 400
        updates["description"] = desc
    if "priority" in d:
        if d["priority"] not in PRIORITIES:
            return jsonify({"error": f"priority must be one of {list(PRIORITIES)}"}), 400
        updates["priority"] = d["priority"]
    if "status" in d:
        if d["status"] not in STATUSES:
            return jsonify({"error": f"status must be one of {list(STATUSES)}"}), 400
        updates["status"] = d["status"]
    for field in ("assigned_to", "remarks"):
        if field in d:
            updates[field] = _gr_clean(d[field])
    if "due_at" in d:
        try:
            updates["due_at"] = _gr_parse_dt(d["due_at"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    mydb = None
    try:
        mydb = _gr_conn()
        cursor = mydb.cursor(dictionary=True, buffered=True)

        cursor.execute(
            "SELECT * FROM hotel_tblguest_requests WHERE id=%s AND is_active=1 FOR UPDATE",
            (req_id,),
        )
        current = cursor.fetchone()
        if not current:
            mydb.close()
            return jsonify({"error": f"Request {req_id} not found."}), 404

        # Completion bookkeeping follows the status change
        if "status" in updates:
            new_status = updates["status"]
            if new_status == "Completed" and current["status"] != "Completed":
                updates["completed_at"] = datetime.now()
                updates["completed_by"] = _gr_clean(d.get("completed_by"))
            elif new_status != "Completed" and current["status"] == "Completed":
                updates["completed_at"] = None      # reopened or cancelled
                updates["completed_by"] = None

        # Drop values that didn't actually change
        updates = {k: v for k, v in updates.items() if v != current.get(k)}

        if not updates:
            mydb.close()
            return jsonify({"message": "No changes.", "id": req_id}), 200

        set_clause = ", ".join(f"{col}=%s" for col in updates)
        cursor.execute(
            f"UPDATE hotel_tblguest_requests SET {set_clause} WHERE id=%s",
            list(updates.values()) + [req_id],
        )
        mydb.commit()
        mydb.close()
        return jsonify({
            "message": "Request updated",
            "id": req_id,
            "updated_fields": list(updates.keys()),
        }), 200

    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
                mydb.close()
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500


# ---------------- DELETE (soft) ----------------
@app_file496.route("/guest-requests/<int:req_id>", methods=["DELETE"])
@cross_origin()
def delete_guest_request(req_id):
    err = _gr_token_error()
    if err:
        return err

    mydb = None
    try:
        mydb = _gr_conn()
        cursor = mydb.cursor()
        cursor.execute(
            "UPDATE hotel_tblguest_requests SET is_active = 0 WHERE id=%s AND is_active=1",
            (req_id,),
        )
        if cursor.rowcount == 0:
            mydb.close()
            return jsonify({"error": f"Request {req_id} not found."}), 404
        mydb.commit()
        mydb.close()
        return jsonify({"message": "Request deleted", "id": req_id}), 200
    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
                mydb.close()
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500
