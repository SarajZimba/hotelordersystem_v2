from flask import Blueprint, request, jsonify, current_app, url_for
import uuid
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()
from root.auth.check import token_auth

app_file403 = Blueprint('app_file403', __name__)

def _as_date(value):
    """Normalize a DB value (date, datetime or 'YYYY-MM-DD' string) to a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    return value
OCCUPIED_STATES = ("Check-In", "Overdue", "Departing Today")


def hk_after_checkout(hk, last_out):
    """Status for a room that is vacant, or whose guest arrived today.
    Dirty if a guest checked out after the room's last cleaning."""
    if hk is None:
        return "Dirty" if last_out else "Clean"
    if hk["hk_status"] == "Dirty":
        return "Dirty"
    if last_out and (hk["cleaned_at"] is None or hk["cleaned_at"] < last_out):
        return "Dirty"
    return hk["hk_status"]


def housekeeping_counts(rooms):
    c = {
        "total_rooms": len(rooms),
        "out_of_order": 0,
        "occupied": 0,
        "vacant": 0,
        "dirty": 0,
        "clean": 0,
        "inspected": 0,
        "occupied_dirty": 0,
        "occupied_clean": 0,
        "vacant_dirty": 0,
        "vacant_clean": 0,
    }
    for r in rooms:
        if r["is_out_of_order"]:
            c["out_of_order"] += 1
            continue
        side = "occupied" if r["occupancy_state"] in OCCUPIED_STATES else "vacant"
        hk = r["hk_status"]  # Dirty | Clean | Inspected
        c[side] += 1
        c[hk.lower()] += 1
        c[f"{side}_{'dirty' if hk == 'Dirty' else 'clean'}"] += 1

    serviceable = c["total_rooms"] - c["out_of_order"]
    ready = c["clean"] + c["inspected"]
    c["serviceable_rooms"] = serviceable
    c["cleaned"] = ready
    c["cleaned_pct"] = round(ready * 100 / serviceable, 1) if serviceable else 0.0
    c["dirty_pct"] = round(c["dirty"] * 100 / serviceable, 1) if serviceable else 0.0
    return c
    return c

@app_file403.route("/rooms", methods=["GET", "POST"])
@cross_origin()
def rooms_list_create():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        if request.method == "GET":
            outlet = request.args.get("outlet")
            want_summary = request.args.get("summary") in ("1", "true", "True")
            hk_filter = request.args.get("hk")                # Dirty | Clean | Inspected | Out of Order
            occupancy_filter = request.args.get("occupancy")  # Occupied | Vacant
            today = date.today()

            date_arg = request.args.get("date")
            if date_arg:
                try:
                    target_date = datetime.strptime(date_arg, "%Y-%m-%d").date()
                except ValueError:
                    mydb.close()
                    return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            else:
                target_date = today

            # 1) rooms
            room_sql = "SELECT * FROM hotel_tblrooms WHERE is_active = 1"
            room_params = []
            if outlet:
                room_sql += " AND outlet = %s"
                room_params.append(outlet)
            room_sql += " ORDER BY created_at DESC"

            cursor.execute(room_sql, room_params)
            rooms = cursor.fetchall()

            # 2) registered stays that have started, one row per reservation
            stay_sq = """
                SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
                FROM hotel_tblguestreservation
                WHERE is_active = 1
                GROUP BY Reservation_ID
            """

            cursor.execute(f"""
                SELECT rd.room_id, res.id AS reservation_id, res.Check_In,
                       st.s AS start_date, st.e AS end_date
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblreservation res
                    ON rd.Reservation_ID = res.id AND res.is_active = 1
                JOIN ({stay_sq}) st ON st.Reservation_ID = res.id
                WHERE rd.is_active = 1
                  AND rd.is_current = 1
                  AND res.Current_Status = 'Registered'
                  AND st.s <= %s
            """, (today,))

            PRIORITY = {"Overdue": 3, "Check-In": 2, "Departing Today": 1}
            state_by_room = {}
            arrived_today_by_room = {}
            overdue_info = {}

            for stay in cursor.fetchall():
                start = _as_date(stay["start_date"])
                end = _as_date(stay["end_date"])
                room_id = stay["room_id"]
                check_in = stay["Check_In"]
                # arrived today: planned start is today, or actually registered today
                arrived_today = start == today or (
                    check_in is not None and _as_date(check_in) == today
                )

                if end < today:
                    state = "Overdue"
                    current = overdue_info.get(room_id)
                    if current is None or end < current["due_out"]:
                        overdue_info[room_id] = {
                            "reservation_id": stay["reservation_id"],
                            "due_out": end,
                            "days_overdue": (today - end).days,
                        }
                elif end > today or start == end:
                    state = "Check-In"
                else:
                    state = "Departing Today"

                if PRIORITY[state] > PRIORITY.get(state_by_room.get(room_id), 0):
                    state_by_room[room_id] = state
                    arrived_today_by_room[room_id] = arrived_today

            # 3) out-of-order blocks touching today and/or the target date
            range_start = min(today, target_date)
            range_end = max(today, target_date)
            cursor.execute("""
                SELECT id, room_id, block_type, reason, start_date, end_date
                FROM hotel_tblroom_blocks
                WHERE is_active = 1
                  AND released_at IS NULL
                  AND start_date <= %s
                  AND end_date >= %s
            """, (range_end, range_start))

            block_today = {}
            ooo_on_target = set()
            for b in cursor.fetchall():
                b_start = _as_date(b["start_date"])
                b_end = _as_date(b["end_date"])
                if b_start <= today <= b_end:
                    block_today.setdefault(b["room_id"], b)
                if b_start <= target_date <= b_end:
                    ooo_on_target.add(b["room_id"])

            # 4) latest housekeeping row on or before today, per room
            #    (checkout and room change both write a Dirty row)
            cursor.execute("""
                SELECT h.room_id, h.hk_status, h.hk_date, h.cleaned_at, h.cleaned_by, h.remarks
                FROM hotel_tblhousekeeping h
                JOIN (
                    SELECT room_id, MAX(hk_date) AS d
                    FROM hotel_tblhousekeeping
                    WHERE hk_date <= %s
                    GROUP BY room_id
                ) m ON m.room_id = h.room_id AND m.d = h.hk_date
            """, (today,))
            hk_latest = {r["room_id"]: r for r in cursor.fetchall()}

            # 5) build the room payload
            for room in rooms:
                rid = room["id"]
                state = state_by_room.get(rid, "Vacant")
                info = overdue_info.get(rid)
                block = block_today.get(rid)
                hk = hk_latest.get(rid)

                occupied = state in OCCUPIED_STATES
                if occupied:
                    if hk and hk["hk_date"] == today:
                        # service recorded today (or room dirtied today)
                        hk_status = hk["hk_status"]
                    elif arrived_today_by_room.get(rid):
                        # arrival day: room keeps its last recorded status
                        hk_status = hk["hk_status"] if hk else "Clean"
                    else:
                        # stayover with no service recorded today
                        hk_status = "Dirty"
                else:
                    # vacant: last recorded status, Clean if never recorded
                    hk_status = hk["hk_status"] if hk else "Clean"

                room["occupancy_state"] = state
                room["room_state"] = "Out of Order" if block else state
                room["departing_today"] = state == "Departing Today"
                room["overdue"] = state == "Overdue"
                room["overdue_reservation_id"] = info["reservation_id"] if info else None
                room["overdue_since"] = str(info["due_out"]) if info else None
                room["days_overdue"] = info["days_overdue"] if info else 0
                room["room_image_url"] = _upload_url(room.get("room_image"))

                room["is_out_of_order"] = block is not None
                room["ooo_block_id"] = block["id"] if block else None
                room["ooo_type"] = block["block_type"] if block else None
                room["ooo_reason"] = block["reason"] if block else None
                room["ooo_until"] = str(block["end_date"]) if block else None
                room["hk_status"] = "Out of Order" if block else hk_status
                room["hk_cleaned_at"] = str(hk["cleaned_at"]) if hk and hk["cleaned_at"] else None
                room["hk_cleaned_by"] = hk["cleaned_by"] if hk else None
                room["hk_remarks"] = hk["remarks"] if hk else None
                room["display_state"] = (
                    "Out of Order" if block
                    else f"{'Occupied' if occupied else 'Vacant'} {hk_status}"
                )

            # housekeeping counts cover all rooms, before any filter
            hk_counts = housekeeping_counts(rooms)

            # type-wise bookings / arrivals summary
            summary_payload = None
            if want_summary:
                summary = {}
                for room in rooms:
                    t = room["room_type"]
                    if t not in summary:
                        summary[t] = {
                            "room_type": t,
                            "total_rooms": 0,
                            "checked_in_now": 0,
                            "overdue": 0,
                            "out_of_order": 0,
                            "booked": 0,
                            "available": 0,
                            "arrivals": 0,
                            "stayovers": 0,
                            "departures": 0,
                            "expected_arrivals": 0
                        }
                    summary[t]["total_rooms"] += 1
                    if room["id"] in ooo_on_target:
                        summary[t]["out_of_order"] += 1
                    if room["occupancy_state"] == "Check-In":
                        summary[t]["checked_in_now"] += 1
                    if room["occupancy_state"] == "Overdue" and room["id"] not in ooo_on_target:
                        summary[t]["overdue"] += 1

                booking_query = f"""
                    SELECT
                        rt.room_type,
                        f.quantity,
                        res.Current_Status,
                        st.s AS start_date,
                        st.e AS end_date
                    FROM hotel_tblfitrate f
                    JOIN hotel_tblrates rt ON f.rateID = rt.id AND rt.is_active = 1
                    JOIN hotel_tblreservation res
                        ON f.reservationID = res.id AND res.is_active = 1
                    JOIN ({stay_sq}) st ON st.Reservation_ID = res.id
                    WHERE f.is_active = 1
                      AND res.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
                      AND st.s <= %s
                      AND st.e >= %s
                """
                b_params = [target_date, target_date]
                if outlet:
                    booking_query += " AND res.outlet = %s"
                    b_params.append(outlet)

                cursor.execute(booking_query, b_params)

                for b in cursor.fetchall():
                    t = b["room_type"]
                    if t not in summary:
                        continue

                    start = _as_date(b["start_date"])
                    end = _as_date(b["end_date"])
                    qty = int(b["quantity"] or 0)
                    status = b["Current_Status"]
                    same_day = start == end

                    night_ok = True
                    if status == "Checked Out":
                        night_ok = target_date <= today if same_day else target_date < today

                    if start == target_date and night_ok:
                        summary[t]["arrivals"] += qty
                        summary[t]["booked"] += qty
                        if status == "Reserved":
                            summary[t]["expected_arrivals"] += qty
                    elif not same_day and start < target_date < end and night_ok:
                        summary[t]["stayovers"] += qty
                        summary[t]["booked"] += qty
                    elif not same_day and end == target_date and status in ("Registered", "Checked Out"):
                        summary[t]["departures"] += qty

                for t in summary:
                    blocked = summary[t]["overdue"] if target_date == today else 0
                    summary[t]["available"] = max(
                        summary[t]["total_rooms"]
                        - summary[t]["booked"]
                        - blocked
                        - summary[t]["out_of_order"],
                        0
                    )
                summary_payload = list(summary.values())

            # 6) optional housekeeping-board filters (list only)
            if hk_filter:
                rooms = [r for r in rooms if r["hk_status"] == hk_filter]
            if occupancy_filter:
                want_occupied = occupancy_filter.lower() == "occupied"
                rooms = [
                    r for r in rooms
                    if (r["occupancy_state"] in OCCUPIED_STATES) == want_occupied
                    and not r["is_out_of_order"]
                ]

            mydb.close()

            if want_summary:
                return jsonify({
                    "date": str(target_date),
                    "rooms": rooms,
                    "summary_by_type": summary_payload,
                    "housekeeping_counts": hk_counts
                }), 200

            return jsonify(rooms), 200

        # -----------------------
        # POST: create rooms
        # -----------------------
        elif request.method == "POST":

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
            # -----------------------------------

            json_data = request.get_json() or {}
            rooms_data = json_data.get("rooms", [])

            if not isinstance(rooms_data, list):
                return {"error": "Expected a list of rooms."}, 400

            # Fetch existing outlet_room_ids
            cursor.execute(
                "SELECT outlet_room_id FROM hotel_tblrooms WHERE outlet_room_id IS NOT NULL"
            )
            existing_ids = set(row["outlet_room_id"] for row in cursor.fetchall())

            rooms_to_insert = []
            skipped_ids = []
            created_rooms = []

            for item in rooms_data:
                outlet_room_id = item.get("outlet_room_id")

                if outlet_room_id and outlet_room_id in existing_ids:
                    skipped_ids.append(outlet_room_id)
                else:
                    rooms_to_insert.append(item)

            # Insert rooms
            for r in rooms_to_insert:
                insert_sql = """
                    INSERT INTO hotel_tblrooms (
                        outlet, room_no, floor, room_state, phone_no, preference,
                        room_view, room_type, room_notes, outlet_room_id,
                        created_at, is_active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """

                floor = r.get("floor")
                floor = str(floor).strip() if floor not in (None, "") else None

                cursor.execute(
                    insert_sql,
                    (
                        r.get("outlet"),
                        r.get("room_no"),
                        floor,
                        "Vacant",  # Always set to Vacant on creation
                        r.get("phone_no"),
                        r.get("preference"),
                        r.get("room_view"),
                        r.get("room_type"),
                        r.get("room_notes"),
                        r.get("outlet_room_id"),
                        datetime.now(),
                    ),
                )

                created_rooms.append(cursor.lastrowid)

            mydb.commit()
            mydb.close()

            return {
                "created_count": len(created_rooms),
                "skipped_count": len(skipped_ids),
                "skipped_ids": skipped_ids,
                "created_rooms": created_rooms,
            }, 201

    except Exception as e:
        return {"error": str(e)}, 400


# -----------------------
# Image helpers
# -----------------------
# Same uploads folder as the logos: root/uploads
basedir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(basedir, '../..'))
UPLOAD_FOLDER = os.path.join(root_dir, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_ROOM_IMAGE_BYTES = 5 * 1024 * 1024      # 5 MB
UPLOADS_URL_PREFIX = "/static/uploads"      # how the uploads folder is exposed


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_url(filename):
    """Public URL for a stored filename (None if there is no image)."""
    if not filename:
        return None
    base = os.getenv("IMAGE_BASE_URL") or request.host_url   # optional override
    return f"{base.rstrip('/')}{UPLOADS_URL_PREFIX}/{os.path.basename(filename)}"


def _remove_upload(filename):
    if not filename:
        return
    path = os.path.join(UPLOAD_FOLDER, os.path.basename(filename))
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass

@app_file403.route("/rooms/<int:room_id>/image", methods=["POST", "PUT"])
@cross_origin()
def update_room_image(room_id):
    # -------- TOKEN (Authorization: Bearer <token>) --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- INPUT (multipart/form-data, field "image") --------
    file = request.files.get("image")
    if not file or not file.filename or not _allowed_file(file.filename):
        return {"error": "Invalid or missing image file (png, jpg, jpeg, gif)."}, 400
    if not (file.mimetype or "").startswith("image/"):
        return {"error": "File is not an image."}, 400

    # size check without loading the file into memory
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size == 0:
        return {"error": "Empty file."}, 400
    if size > MAX_ROOM_IMAGE_BYTES:
        return {"error": f"Image must be {MAX_ROOM_IMAGE_BYTES // (1024 * 1024)} MB or smaller."}, 400

    mydb = None
    new_path = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- FIND THE ROOM --------
        cursor.execute(
            "SELECT id, room_image FROM hotel_tblrooms WHERE id = %s AND is_active = 1",
            (room_id,),
        )
        room = cursor.fetchone()
        if not room:
            return {"error": f"Room {room_id} not found."}, 404

        old_image = room["room_image"]

        # -------- SAVE FILE (unique name, only after the room exists) --------
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"room_{room_id}_{uuid.uuid4().hex}.{ext}"
        new_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(new_path)

        # -------- UPDATE DB (filename only, like the logos) --------
        cursor.execute(
            "UPDATE hotel_tblrooms SET room_image = %s WHERE id = %s",
            (filename, room_id),
        )
        mydb.commit()
        new_path = None    # committed, so don't clean it up below

        # -------- REMOVE OLD IMAGE FILE --------
        _remove_upload(old_image)

        return {
            "message": "Room image uploaded successfully",
            "room_id": room_id,
            "room_image": filename,
            "room_image_url": _upload_url(filename),
        }, 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        if new_path and os.path.isfile(new_path):
            try:
                os.remove(new_path)
            except OSError:
                pass
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()


@app_file403.route("/rooms/<int:room_id>/image", methods=["DELETE"])
@cross_origin()
def delete_room_image(room_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        cursor.execute(
            "SELECT id, room_image FROM hotel_tblrooms WHERE id = %s AND is_active = 1",
            (room_id,),
        )
        room = cursor.fetchone()
        if not room:
            return {"error": f"Room {room_id} not found."}, 404

        cursor.execute("UPDATE hotel_tblrooms SET room_image = NULL WHERE id = %s", (room_id,))
        mydb.commit()
        _remove_upload(room["room_image"])

        return {"message": "Room image removed", "room_id": room_id}, 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()


@app_file403.route("/rooms/with-image", methods=["POST"])
@cross_origin()
def create_room_with_image():
    # -------- TOKEN (Authorization: Bearer <token>) --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- FORM FIELDS (multipart/form-data) --------
    form = request.form
    outlet = (form.get("outlet") or "").strip()
    room_no = (form.get("room_no") or "").strip()
    room_type = (form.get("room_type") or "").strip()
    outlet_room_id = (form.get("outlet_room_id") or "").strip() or None

    if not outlet:
        return {"error": "outlet is required."}, 400
    if not room_no:
        return {"error": "room_no is required."}, 400
    try:
        room_no = int(room_no)
    except ValueError:
        return {"error": "room_no must be a number."}, 400
    if not room_type:
        return {"error": "room_type is required."}, 400

    # -------- OPTIONAL IMAGE (field "image") --------
    file = request.files.get("image")
    has_image = bool(file and file.filename)

    if has_image:
        if not _allowed_file(file.filename):
            return {"error": "Invalid image file (png, jpg, jpeg, gif)."}, 400
        if not (file.mimetype or "").startswith("image/"):
            return {"error": "File is not an image."}, 400

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size == 0:
            return {"error": "Empty file."}, 400
        if size > MAX_ROOM_IMAGE_BYTES:
            return {"error": f"Image must be {MAX_ROOM_IMAGE_BYTES // (1024 * 1024)} MB or smaller."}, 400

    mydb = None
    cursor = None
    saved_path = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- DUPLICATE CHECKS --------
        if outlet_room_id:
            cursor.execute(
                "SELECT id FROM hotel_tblrooms WHERE outlet_room_id=%s",
                (outlet_room_id,),
            )
            if cursor.fetchone():
                return {"error": f"Room with outlet_room_id '{outlet_room_id}' already exists."}, 409

        cursor.execute(
            "SELECT id FROM hotel_tblrooms WHERE outlet=%s AND room_no=%s AND is_active=1",
            (outlet, room_no),
        )
        if cursor.fetchone():
            return {"error": f"Room {room_no} already exists in outlet '{outlet}'."}, 409

        # -------- INSERT ROOM --------
        filename = None
        if has_image:
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"room_{uuid.uuid4().hex}.{ext}"

        cursor.execute("""
            INSERT INTO hotel_tblrooms (
                outlet, room_no, room_state, phone_no, preference,
                room_view, room_type, room_notes, outlet_room_id,
                room_image, created_at, is_active
            )
            VALUES (%s, %s, 'Vacant', %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (
            outlet,
            room_no,
            form.get("phone_no"),
            form.get("preference"),
            form.get("room_view"),
            room_type,
            form.get("room_notes"),
            outlet_room_id,
            filename,
            datetime.now(),
        ))
        new_room_id = cursor.lastrowid

        # -------- SAVE FILE, THEN COMMIT --------
        if has_image:
            saved_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(saved_path)

        mydb.commit()
        saved_path = None   # committed, so don't clean it up below

        return {
            "message": "Room created successfully",
            "room_id": new_room_id,
            "room_no": room_no,
            "room_image": filename,
            "room_image_url": _upload_url(filename),
        }, 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        if saved_path and os.path.isfile(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                pass
        return {"error": str(e)}, 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


# @app_file403.route("/rooms/<int:room_id>/with-image", methods=["PUT"])
# @cross_origin()
# def update_room_with_image(room_id):
#     # -------- TOKEN (Authorization: Bearer <token>) --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     form = request.form

#     # -------- OPTIONAL IMAGE (field "image") --------
#     file = request.files.get("image")
#     has_image = bool(file and file.filename)
#     remove_image = (form.get("remove_image") or "").lower() in ("1", "true", "yes")

#     if has_image:
#         if not _allowed_file(file.filename):
#             return {"error": "Invalid image file (png, jpg, jpeg, gif)."}, 400
#         if not (file.mimetype or "").startswith("image/"):
#             return {"error": "File is not an image."}, 400

#         file.seek(0, os.SEEK_END)
#         size = file.tell()
#         file.seek(0)
#         if size == 0:
#             return {"error": "Empty file."}, 400
#         if size > MAX_ROOM_IMAGE_BYTES:
#             return {"error": f"Image must be {MAX_ROOM_IMAGE_BYTES // (1024 * 1024)} MB or smaller."}, 400

#     mydb = None
#     cursor = None
#     saved_path = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- FIND THE ROOM (locked) --------
#         cursor.execute("""
#             SELECT id, outlet, room_no, room_type, outlet_room_id, room_image,
#                    phone_no, preference, room_view, room_notes
#             FROM hotel_tblrooms
#             WHERE id=%s AND is_active=1
#             FOR UPDATE
#         """, (room_id,))
#         room = cursor.fetchone()
#         if not room:
#             return {"error": f"Room {room_id} not found."}, 404

#         updates = {}

#         # -------- REQUIRED FIELDS (only validated if sent) --------
#         if "outlet" in form:
#             v = form.get("outlet").strip()
#             if not v:
#                 return {"error": "outlet cannot be empty."}, 400
#             updates["outlet"] = v

#         if "room_no" in form:
#             v = form.get("room_no").strip()
#             try:
#                 updates["room_no"] = int(v)
#             except ValueError:
#                 return {"error": "room_no must be a number."}, 400

#         if "room_type" in form:
#             v = form.get("room_type").strip()
#             if not v:
#                 return {"error": "room_type cannot be empty."}, 400
#             updates["room_type"] = v

#         # -------- OPTIONAL FIELDS (empty string clears to NULL) --------
#         for field in ("phone_no", "preference", "room_view", "room_notes", "outlet_room_id"):
#             if field in form:
#                 updates[field] = form.get(field).strip() or None

#         # Drop values that didn't actually change
#         updates = {k: v for k, v in updates.items() if v != room.get(k)}

#         # -------- GUARD: no identity/type change while a guest is in the room --------
#         if {"outlet", "room_no", "room_type"} & set(updates):
#             cursor.execute("""
#                 SELECT 1
#                 FROM hotel_tblreservation_details rd
#                 JOIN hotel_tblreservation res
#                     ON rd.Reservation_ID = res.id AND res.is_active = 1
#                 WHERE rd.room_id=%s AND rd.is_active=1 AND rd.is_current=1
#                   AND res.Current_Status='Registered'
#                 LIMIT 1
#             """, (room_id,))
#             if cursor.fetchone():
#                 return {"error": "Outlet, room number and room type cannot be changed while a guest is checked into this room."}, 409

#         # -------- DUPLICATE CHECKS (excluding this room) --------
#         new_outlet = updates.get("outlet", room["outlet"])
#         new_room_no = updates.get("room_no", room["room_no"])

#         if updates.get("outlet_room_id"):
#             cursor.execute(
#                 "SELECT id FROM hotel_tblrooms WHERE outlet_room_id=%s AND id<>%s",
#                 (updates["outlet_room_id"], room_id),
#             )
#             if cursor.fetchone():
#                 return {"error": f"Room with outlet_room_id '{updates['outlet_room_id']}' already exists."}, 409

#         if "outlet" in updates or "room_no" in updates:
#             cursor.execute("""
#                 SELECT id FROM hotel_tblrooms
#                 WHERE outlet=%s AND room_no=%s AND is_active=1 AND id<>%s
#             """, (new_outlet, new_room_no, room_id))
#             if cursor.fetchone():
#                 return {"error": f"Room {new_room_no} already exists in outlet '{new_outlet}'."}, 409

#         # -------- IMAGE HANDLING --------
#         old_image = room["room_image"]
#         remove_old_after_commit = False

#         if has_image:
#             ext = file.filename.rsplit(".", 1)[1].lower()
#             filename = f"room_{room_id}_{uuid.uuid4().hex}.{ext}"
#             saved_path = os.path.join(UPLOAD_FOLDER, filename)
#             file.save(saved_path)
#             updates["room_image"] = filename
#             remove_old_after_commit = bool(old_image)
#         elif remove_image and old_image:
#             updates["room_image"] = None
#             remove_old_after_commit = True

#         # -------- NOTHING TO UPDATE --------
#         if not updates:
#             return {
#                 "message": "No changes.",
#                 "room_id": room_id,
#                 "room_image": old_image,
#                 "room_image_url": _upload_url(old_image),
#             }, 200

#         # -------- UPDATE --------
#         set_clause = ", ".join(f"{col}=%s" for col in updates)
#         cursor.execute(
#             f"UPDATE hotel_tblrooms SET {set_clause}, updated_at=%s WHERE id=%s",
#             list(updates.values()) + [datetime.now(), room_id],
#         )

#         mydb.commit()
#         saved_path = None   # committed, so don't clean it up below

#         # -------- REMOVE OLD IMAGE FILE (only after commit) --------
#         if remove_old_after_commit:
#             _remove_upload(old_image)

#         final_image = updates["room_image"] if "room_image" in updates else old_image

#         return {
#             "message": "Room updated successfully",
#             "room_id": room_id,
#             "updated_fields": list(updates.keys()),
#             "room_image": final_image,
#             "room_image_url": _upload_url(final_image),
#         }, 200

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         if saved_path and os.path.isfile(saved_path):
#             try:
#                 os.remove(saved_path)
#             except OSError:
#                 pass
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             cursor.close()
#         if mydb:
#             mydb.close()


@app_file403.route("/rooms/<int:room_id>/with-image", methods=["PUT"])
@cross_origin()
def update_room_with_image(room_id):
    # -------- TOKEN (Authorization: Bearer <token>) --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    form = request.form

    # -------- OPTIONAL IMAGE (field "image") --------
    file = request.files.get("image")
    has_image = bool(file and file.filename)
    remove_image = (form.get("remove_image") or "").lower() in ("1", "true", "yes")

    if has_image:
        if not _allowed_file(file.filename):
            return {"error": "Invalid image file (png, jpg, jpeg, gif)."}, 400
        if not (file.mimetype or "").startswith("image/"):
            return {"error": "File is not an image."}, 400

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size == 0:
            return {"error": "Empty file."}, 400
        if size > MAX_ROOM_IMAGE_BYTES:
            return {"error": f"Image must be {MAX_ROOM_IMAGE_BYTES // (1024 * 1024)} MB or smaller."}, 400

    mydb = None
    cursor = None
    saved_path = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- FIND THE ROOM (locked) --------
        cursor.execute("""
            SELECT id, outlet, room_no, floor, room_type, outlet_room_id, room_image,
                   phone_no, preference, room_view, room_notes
            FROM hotel_tblrooms
            WHERE id=%s AND is_active=1
            FOR UPDATE
        """, (room_id,))
        room = cursor.fetchone()
        if not room:
            return {"error": f"Room {room_id} not found."}, 404

        updates = {}

        # -------- REQUIRED FIELDS (only validated if sent) --------
        if "outlet" in form:
            v = form.get("outlet").strip()
            if not v:
                return {"error": "outlet cannot be empty."}, 400
            updates["outlet"] = v

        if "room_no" in form:
            v = form.get("room_no").strip()
            try:
                updates["room_no"] = int(v)
            except ValueError:
                return {"error": "room_no must be a number."}, 400

        if "room_type" in form:
            v = form.get("room_type").strip()
            if not v:
                return {"error": "room_type cannot be empty."}, 400
            updates["room_type"] = v

        # -------- OPTIONAL FIELDS (empty string clears to NULL) --------
        for field in ("floor", "phone_no", "preference", "room_view", "room_notes", "outlet_room_id"):
            if field in form:
                updates[field] = form.get(field).strip() or None

        # Drop values that didn't actually change
        updates = {k: v for k, v in updates.items() if v != room.get(k)}

        # -------- GUARD: no identity/type change while a guest is in the room --------
        if {"outlet", "room_no", "room_type"} & set(updates):
            cursor.execute("""
                SELECT 1
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblreservation res
                    ON rd.Reservation_ID = res.id AND res.is_active = 1
                WHERE rd.room_id=%s AND rd.is_active=1 AND rd.is_current=1
                  AND res.Current_Status='Registered'
                LIMIT 1
            """, (room_id,))
            if cursor.fetchone():
                return {"error": "Outlet, room number and room type cannot be changed while a guest is checked into this room."}, 409

        # -------- DUPLICATE CHECKS (excluding this room) --------
        new_outlet = updates.get("outlet", room["outlet"])
        new_room_no = updates.get("room_no", room["room_no"])

        if updates.get("outlet_room_id"):
            cursor.execute(
                "SELECT id FROM hotel_tblrooms WHERE outlet_room_id=%s AND id<>%s",
                (updates["outlet_room_id"], room_id),
            )
            if cursor.fetchone():
                return {"error": f"Room with outlet_room_id '{updates['outlet_room_id']}' already exists."}, 409

        if "outlet" in updates or "room_no" in updates:
            cursor.execute("""
                SELECT id FROM hotel_tblrooms
                WHERE outlet=%s AND room_no=%s AND is_active=1 AND id<>%s
            """, (new_outlet, new_room_no, room_id))
            if cursor.fetchone():
                return {"error": f"Room {new_room_no} already exists in outlet '{new_outlet}'."}, 409

        # -------- IMAGE HANDLING --------
        old_image = room["room_image"]
        remove_old_after_commit = False

        if has_image:
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"room_{room_id}_{uuid.uuid4().hex}.{ext}"
            saved_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(saved_path)
            updates["room_image"] = filename
            remove_old_after_commit = bool(old_image)
        elif remove_image and old_image:
            updates["room_image"] = None
            remove_old_after_commit = True

        # -------- NOTHING TO UPDATE --------
        if not updates:
            return {
                "message": "No changes.",
                "room_id": room_id,
                "room_image": old_image,
                "room_image_url": _upload_url(old_image),
            }, 200

        # -------- UPDATE --------
        set_clause = ", ".join(f"{col}=%s" for col in updates)
        cursor.execute(
            f"UPDATE hotel_tblrooms SET {set_clause}, updated_at=%s WHERE id=%s",
            list(updates.values()) + [datetime.now(), room_id],
        )

        mydb.commit()
        saved_path = None   # committed, so don't clean it up below

        # -------- REMOVE OLD IMAGE FILE (only after commit) --------
        if remove_old_after_commit:
            _remove_upload(old_image)

        final_image = updates["room_image"] if "room_image" in updates else old_image

        return {
            "message": "Room updated successfully",
            "room_id": room_id,
            "updated_fields": list(updates.keys()),
            "room_image": final_image,
            "room_image_url": _upload_url(final_image),
        }, 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        if saved_path and os.path.isfile(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                pass
        return {"error": str(e)}, 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()