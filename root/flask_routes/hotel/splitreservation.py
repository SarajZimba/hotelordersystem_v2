from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
from root.auth.check import token_auth

app_file491 = Blueprint('app_file491', __name__)
@cross_origin()
@app_file491.route("/splitreservation/v1", methods=["POST"])
@cross_origin()
def split_reservation():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- PAYLOAD VALIDATION (before any DB work) --------
        data = request.get_json() or {}
        original_id = data.get("reservation_id")
        splits = data.get("splits")

        if not original_id:
            return {"error": "reservation_id is required."}, 400
        if not isinstance(splits, list) or len(splits) < 2:
            return {"error": "At least 2 splits are required."}, 400

        assigned_ids = []
        room_ids = []
        payload_total = 0

        for n, s in enumerate(splits, start=1):
            if not s.get("room_id"):
                return {"error": f"Split {n}: room_id is required."}, 400
            room_ids.append(s["room_id"])

            gr = s.get("guest_reservation") or {}
            try:
                adults = int(gr.get("No_of_adults") or 0)
                children = int(gr.get("No_of_children") or 0)
            except (TypeError, ValueError):
                return {"error": f"Split {n}: guest counts must be numbers."}, 400
            if adults < 0 or children < 0 or adults + children < 1:
                return {"error": f"Split {n}: needs at least one guest."}, 400
            payload_total += adults + children

            if not s.get("fit_rates"):
                return {"error": f"Split {n}: fit_rates is required."}, 400

            guests = s.get("guests")
            if not isinstance(guests, list) or not guests:
                return {"error": f"Split {n}: at least one in-house guest is required."}, 400

            primaries = 0
            for g in guests:
                if not g.get("idguest"):
                    return {"error": f"Split {n}: every guest needs idguest."}, 400
                assigned_ids.append(int(g["idguest"]))
                if g.get("is_primary"):
                    primaries += 1
            if primaries != 1:
                return {"error": f"Split {n}: needs exactly one primary guest (received {primaries})."}, 400

        if len(room_ids) != len(set(room_ids)):
            return {"error": "Each split must have its own room. Guests in the same room "
                             "belong to the same reservation."}, 400
        if len(assigned_ids) != len(set(assigned_ids)):
            return {"error": "A guest is assigned to more than one split."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # lock the original so two splits / check-ins can't run at once
        cursor.execute("SELECT * FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (original_id,))
        orig = cursor.fetchone()
        if not orig or orig.get("is_active") == 0:
            mydb.rollback()
            return {"error": f"Reservation {original_id} not found."}, 404
        if orig["Current_Status"] != "Registered":
            mydb.rollback()
            return {"error": "Only a Registered reservation can be split."}, 400

        # billed reservations can't be split
        # NOTE: adjust table/column to however your bills reference the reservation
        cursor.execute("SELECT COUNT(*) AS n FROM hotel_tblhotelbills WHERE ReservationID=%s", (original_id,))
        if cursor.fetchone()["n"] > 0:
            mydb.rollback()
            return {"error": "Billed reservations cannot be split."}, 400

        # original guest reservation row
        cursor.execute("""
            SELECT * FROM hotel_tblguestreservation
            WHERE Reservation_ID=%s AND is_active=1 ORDER BY id LIMIT 1
        """, (original_id,))
        orig_gr = cursor.fetchone()
        if not orig_gr:
            mydb.rollback()
            return {"error": "Original reservation has no guest reservation row."}, 400

        orig_total = (orig_gr["No_of_adults"] or 0) + (orig_gr["No_of_children"] or 0)
        if payload_total != orig_total:
            mydb.rollback()
            return {"error": f"Guest total across splits ({payload_total}) must equal the "
                             f"original total ({orig_total})."}, 400

        # every active in-house guest must be assigned exactly once
        cursor.execute("""
            SELECT idguest FROM hotel_tblinhouse_guests
            WHERE reservation_id=%s AND is_active=1
        """, (original_id,))
        inhouse_ids = {r["idguest"] for r in cursor.fetchall()}
        if inhouse_ids != set(assigned_ids):
            mydb.rollback()
            return {"error": "Splits must include every in-house guest of the reservation exactly once.",
                    "in_house_guest_ids": sorted(inhouse_ids)}, 400

        # room validation: exists, and not occupied by another reservation
        for n, s in enumerate(splits, start=1):
            room_id = s["room_id"]
            cursor.execute("SELECT id FROM hotel_tblrooms WHERE id=%s", (room_id,))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": f"Split {n}: invalid room_id {room_id}."}, 400

            cursor.execute("""
                SELECT d.id FROM hotel_tblreservation_details d
                JOIN hotel_tblreservation r ON r.id = d.Reservation_ID
                WHERE d.room_id=%s AND d.is_current=1 AND d.is_active=1
                  AND r.Current_Status='Registered' AND d.Reservation_ID <> %s
                LIMIT 1
            """, (room_id, original_id))
            if cursor.fetchone():
                mydb.rollback()
                return {"error": f"Split {n}: room {room_id} is occupied by another reservation."}, 400

        now = datetime.now()
        results = []

        # helper: insert fitrate rows (merging duplicate rate/meal pairs)
        def save_fitrates(reservation_id, fit_items):
            merged = {}
            for f in fit_items:
                key = (f.get("rateID"), f.get("mealID"))
                merged[key] = merged.get(key, 0) + int(f.get("quantity") or 0)
            for (rate_id, meal_id), qty in merged.items():
                cursor.execute("""
                    INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                """, (rate_id, meal_id, reservation_id, qty))

        # helper: point the reservation's current room assignment at room_id
        def set_room(reservation_id, room_id):
            cursor.execute("""
                SELECT id FROM hotel_tblreservation_details
                WHERE Reservation_ID=%s AND is_current=1 AND is_active=1 ORDER BY id
            """, (reservation_id,))
            rows = cursor.fetchall()
            if rows:
                cursor.execute("UPDATE hotel_tblreservation_details SET room_id=%s WHERE id=%s",
                               (room_id, rows[0]["id"]))
                for extra in rows[1:]:
                    cursor.execute("DELETE FROM hotel_tblreservation_details WHERE id=%s", (extra["id"],))
            else:
                cursor.execute("""
                    INSERT INTO hotel_tblreservation_details
                        (Reservation_ID, room_id, is_current, created_at, is_active)
                    VALUES (%s, %s, 1, %s, 1)
                """, (reservation_id, room_id, now))

        # helper: move in-house guests to a reservation / room
        def move_guests(reservation_id, room_id, guests):
            for g in guests:
                cursor.execute("""
                    UPDATE hotel_tblinhouse_guests
                    SET reservation_id=%s, room_id=%s, is_primary=%s
                    WHERE idguest=%s AND reservation_id=%s AND is_active=1
                """, (reservation_id, room_id, 1 if g.get("is_primary") else 0,
                      int(g["idguest"]), original_id))

        # -----------------------
        # Split 1 = original reservation (updated in place)
        # -----------------------
        first = splits[0]
        first_gr = first["guest_reservation"]

        cursor.execute("""
            UPDATE hotel_tblguestreservation
            SET No_of_adults=%s, No_of_children=%s,
                Likes=COALESCE(%s, Likes), Dislikes=COALESCE(%s, Dislikes),
                Guest_Notes=COALESCE(%s, Guest_Notes)
            WHERE id=%s
        """, (int(first_gr.get("No_of_adults") or 0), int(first_gr.get("No_of_children") or 0),
              first_gr.get("Likes"), first_gr.get("Dislikes"), first_gr.get("Guest_Notes"),
              orig_gr["id"]))

        cursor.execute("DELETE FROM hotel_tblfitrate WHERE reservationID=%s", (original_id,))
        save_fitrates(original_id, first["fit_rates"])
        set_room(original_id, first["room_id"])
        move_guests(original_id, first["room_id"], first["guests"])

        results.append({"reservation_id": original_id, "room_id": first["room_id"], "is_original": True})

        # -----------------------
        # Splits 2..N = new Registered reservations
        # -----------------------
        for n, s in enumerate(splits[1:], start=2):
            gid, cid = s.get("Guest_ID"), s.get("company_id")
            if not gid and not cid:
                gid, cid = orig["Guest_ID"], orig["company_id"]
            else:
                gid, cid = gid or None, cid or None

            if cid:
                cursor.execute("SELECT id FROM companies WHERE id=%s", (cid,))
                if not cursor.fetchone():
                    mydb.rollback()
                    return {"error": f"Split {n}: invalid company_id."}, 400
            if gid:
                cursor.execute("SELECT id FROM customers WHERE id=%s", (gid,))
                if not cursor.fetchone():
                    mydb.rollback()
                    return {"error": f"Split {n}: invalid Guest_ID."}, 400

            cursor.execute("""
                INSERT INTO hotel_tblreservation (
                    outlet, Emp_ID, Pay_Mode, Billing_Inst, Reservation_type, designation,
                    Advance_Payment, Advance_Payment_Currency, Advance_Payment_Local,
                    Guest_ID, company_id, Reservation_Date, Market_Seg, business_Src,
                    Current_Status, Check_In, Check_Out
                ) VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL,
                          %s, %s, %s, %s, %s, 'Registered', %s, NULL)
            """, (orig["outlet"], orig["Emp_ID"], orig["Pay_Mode"], orig["Billing_Inst"],
                  orig["Reservation_type"], orig["designation"],
                  gid, cid, orig["Reservation_Date"], orig["Market_Seg"], orig["business_Src"],
                  orig["Check_In"]))
            new_id = cursor.lastrowid

            gr = s["guest_reservation"]
            cursor.execute("""
                INSERT INTO hotel_tblguestreservation
                    (Reservation_ID, No_of_children, No_of_adults, Likes, Dislikes,
                     Guest_Notes, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_id, int(gr.get("No_of_children") or 0), int(gr.get("No_of_adults") or 0),
                  gr.get("Likes"), gr.get("Dislikes"), gr.get("Guest_Notes"),
                  gr.get("start_date") or orig_gr["start_date"],
                  gr.get("end_date") or orig_gr["end_date"]))

            save_fitrates(new_id, s["fit_rates"])
            set_room(new_id, s["room_id"])
            move_guests(new_id, s["room_id"], s["guests"])

            results.append({"reservation_id": new_id, "room_id": s["room_id"], "is_original": False})

        mydb.commit()
        return jsonify({"original_reservation_id": original_id, "reservations": results}), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


@app_file491.route("/splitreservationrecreate/v2", methods=["POST"])
@cross_origin()
def split_reservation_recreate():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- PAYLOAD VALIDATION (before any DB work) --------
        data = request.get_json() or {}
        original_id = data.get("reservation_id")
        splits = data.get("splits")

        if not original_id:
            return {"error": "reservation_id is required."}, 400
        if not isinstance(splits, list) or len(splits) < 2:
            return {"error": "At least 2 splits are required."}, 400

        assigned_ids = []
        room_ids = []
        payload_total = 0

        for n, s in enumerate(splits, start=1):
            if not s.get("room_id"):
                return {"error": f"Split {n}: room_id is required."}, 400
            room_ids.append(s["room_id"])

            gr = s.get("guest_reservation") or {}
            try:
                adults = int(gr.get("No_of_adults") or 0)
                children = int(gr.get("No_of_children") or 0)
            except (TypeError, ValueError):
                return {"error": f"Split {n}: guest counts must be numbers."}, 400
            if adults < 0 or children < 0 or adults + children < 1:
                return {"error": f"Split {n}: needs at least one guest."}, 400
            payload_total += adults + children

            if not s.get("fit_rates"):
                return {"error": f"Split {n}: fit_rates is required."}, 400

            guests = s.get("guests")
            if not isinstance(guests, list) or not guests:
                return {"error": f"Split {n}: at least one in-house guest is required."}, 400

            primaries = 0
            for g in guests:
                if not g.get("idguest"):
                    return {"error": f"Split {n}: every guest needs idguest."}, 400
                assigned_ids.append(int(g["idguest"]))
                if g.get("is_primary"):
                    primaries += 1
            if primaries != 1:
                return {"error": f"Split {n}: needs exactly one primary guest (received {primaries})."}, 400

        if len(room_ids) != len(set(room_ids)):
            return {"error": "Each split must have its own room. Guests in the same room "
                             "belong to the same reservation."}, 400
        if len(assigned_ids) != len(set(assigned_ids)):
            return {"error": "A guest is assigned to more than one split."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- READ EVERYTHING FROM THE OLD RESERVATION --------
        cursor.execute("SELECT * FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (original_id,))
        orig = cursor.fetchone()
        if not orig or orig.get("is_active") == 0:
            mydb.rollback()
            return {"error": f"Reservation {original_id} not found."}, 404
        if orig["Current_Status"] != "Registered":
            mydb.rollback()
            return {"error": "Only a Registered reservation can be split."}, 400

        # billed reservations can't be split
        # NOTE: adjust table/column to however your bills reference the reservation
        cursor.execute("SELECT COUNT(*) AS n FROM hotel_tblhotelbills WHERE ReservationID=%s", (original_id,))
        if cursor.fetchone()["n"] > 0:
            mydb.rollback()
            return {"error": "Billed reservations cannot be split."}, 400

        cursor.execute("""
            SELECT * FROM hotel_tblguestreservation
            WHERE Reservation_ID=%s AND is_active=1 ORDER BY id LIMIT 1
        """, (original_id,))
        orig_gr = cursor.fetchone()
        if not orig_gr:
            mydb.rollback()
            return {"error": "Original reservation has no guest reservation row."}, 400

        orig_total = (orig_gr["No_of_adults"] or 0) + (orig_gr["No_of_children"] or 0)
        if payload_total != orig_total:
            mydb.rollback()
            return {"error": f"Guest total across splits ({payload_total}) must equal the "
                             f"original total ({orig_total})."}, 400

        # old in-house guests (full rows, so identity details and checked_in_at are carried over)
        cursor.execute("""
            SELECT * FROM hotel_tblinhouse_guests
            WHERE reservation_id=%s AND is_active=1
        """, (original_id,))
        old_guests = {r["idguest"]: r for r in cursor.fetchall()}
        if set(old_guests) != set(assigned_ids):
            mydb.rollback()
            return {"error": "Splits must include every in-house guest of the reservation exactly once.",
                    "in_house_guest_ids": sorted(old_guests)}, 400

        # room validation: exists, and not occupied by another reservation
        for n, s in enumerate(splits, start=1):
            room_id = s["room_id"]
            cursor.execute("SELECT id FROM hotel_tblrooms WHERE id=%s", (room_id,))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": f"Split {n}: invalid room_id {room_id}."}, 400

            cursor.execute("""
                SELECT d.id FROM hotel_tblreservation_details d
                JOIN hotel_tblreservation r ON r.id = d.Reservation_ID
                WHERE d.room_id=%s AND d.is_current=1 AND d.is_active=1
                  AND r.Current_Status='Registered' AND d.Reservation_ID <> %s
                LIMIT 1
            """, (room_id, original_id))
            if cursor.fetchone():
                mydb.rollback()
                return {"error": f"Split {n}: room {room_id} is occupied by another reservation."}, 400

        # validate bookers up front
        for n, s in enumerate(splits, start=1):
            gid, cid = s.get("Guest_ID"), s.get("company_id")
            if cid:
                cursor.execute("SELECT id FROM companies WHERE id=%s", (cid,))
                if not cursor.fetchone():
                    mydb.rollback()
                    return {"error": f"Split {n}: invalid company_id."}, 400
            if gid:
                cursor.execute("SELECT id FROM customers WHERE id=%s", (gid,))
                if not cursor.fetchone():
                    mydb.rollback()
                    return {"error": f"Split {n}: invalid Guest_ID."}, 400

        # -------- DELETE THE OLD RESERVATION --------
        # in-house guests have no cascade, so remove them first
        cursor.execute("DELETE FROM hotel_tblinhouse_guests WHERE reservation_id=%s", (original_id,))
        # cascades: guestreservation, reservation_details, fitrate
        cursor.execute("DELETE FROM hotel_tblreservation WHERE id=%s", (original_id,))

        # -------- CREATE THE NEW RESERVATIONS --------
        now = datetime.now()
        results = []

        for n, s in enumerate(splits, start=1):
            gid, cid = s.get("Guest_ID"), s.get("company_id")
            if not gid and not cid:
                gid, cid = orig["Guest_ID"], orig["company_id"]
            else:
                gid, cid = gid or None, cid or None

            # advance payment goes to the first split only
            if n == 1:
                adv, adv_cur, adv_local = (orig["Advance_Payment"],
                                           orig["Advance_Payment_Currency"],
                                           orig["Advance_Payment_Local"])
            else:
                adv = adv_cur = adv_local = None

            cursor.execute("""
                INSERT INTO hotel_tblreservation (
                    outlet, Emp_ID, Pay_Mode, Billing_Inst, Reservation_type, designation,
                    Advance_Payment, Advance_Payment_Currency, Advance_Payment_Local,
                    Guest_ID, company_id, Reservation_Date, Market_Seg, business_Src,
                    Current_Status, Check_In, Check_Out
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, 'Registered', %s, NULL)
            """, (orig["outlet"], orig["Emp_ID"], orig["Pay_Mode"], orig["Billing_Inst"],
                  orig["Reservation_type"], orig["designation"],
                  adv, adv_cur, adv_local,
                  gid, cid, orig["Reservation_Date"], orig["Market_Seg"], orig["business_Src"],
                  orig["Check_In"]))
            new_id = cursor.lastrowid

            # guest reservation (falls back to the old values when not sent)
            gr = s["guest_reservation"]
            cursor.execute("""
                INSERT INTO hotel_tblguestreservation
                    (Reservation_ID, No_of_children, No_of_adults, Likes, Dislikes,
                     Guest_Notes, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_id,
                  int(gr.get("No_of_children") or 0), int(gr.get("No_of_adults") or 0),
                  gr.get("Likes") if gr.get("Likes") is not None else orig_gr["Likes"],
                  gr.get("Dislikes") if gr.get("Dislikes") is not None else orig_gr["Dislikes"],
                  gr.get("Guest_Notes") if gr.get("Guest_Notes") is not None else orig_gr["Guest_Notes"],
                  gr.get("start_date") or orig_gr["start_date"],
                  gr.get("end_date") or orig_gr["end_date"]))

            # fit rates (merge duplicate rate/meal pairs)
            merged = {}
            for f in s["fit_rates"]:
                key = (f.get("rateID"), f.get("mealID"))
                merged[key] = merged.get(key, 0) + int(f.get("quantity") or 0)
            for (rate_id, meal_id), qty in merged.items():
                cursor.execute("""
                    INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                """, (rate_id, meal_id, new_id, qty))

            # room assignment
            cursor.execute("""
                INSERT INTO hotel_tblreservation_details
                    (Reservation_ID, room_id, is_current, created_at, is_active)
                VALUES (%s, %s, 1, %s, 1)
            """, (new_id, s["room_id"], now))

            # in-house guests: copy identity + checked_in_at from the old rows
            guest_rows = []
            for g in s["guests"]:
                old = old_guests[int(g["idguest"])]
                guest_rows.append((
                    new_id, s["room_id"], old["name"], old["identity_type"],
                    old["identity_no"], old["nationality"],
                    1 if g.get("is_primary") else 0,
                    old["checked_in_at"],
                ))
            cursor.executemany("""
                INSERT INTO hotel_tblinhouse_guests
                    (reservation_id, room_id, name, identity_type, identity_no,
                     nationality, is_primary, is_active, checked_in_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
            """, guest_rows)

            results.append({
                "reservation_id": new_id,
                "room_id": s["room_id"],
                "guests_saved": len(guest_rows),
            })

        mydb.commit()
        return jsonify({
            "old_reservation_id": original_id,
            "new_reservations": results
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


@app_file491.route("/splitreservation/v4", methods=["POST"])
@cross_origin()
def split_reservation_v4():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- PAYLOAD VALIDATION (before any DB work) --------
        data = request.get_json() or {}
        original_id = data.get("reservation_id")
        moves = data.get("moves")

        if not original_id:
            return {"error": "reservation_id is required."}, 400
        if not isinstance(moves, list) or not moves:
            return {"error": "At least one move is required."}, 400

        room_ids = []
        moved_ids = []

        for n, m in enumerate(moves, start=1):
            if not m.get("room_id"):
                return {"error": f"Move {n}: room_id is required."}, 400
            room_ids.append(m["room_id"])

            gids = m.get("guest_ids")
            if not isinstance(gids, list) or not gids:
                return {"error": f"Move {n}: guest_ids is required."}, 400
            try:
                gids = [int(x) for x in gids]
            except (TypeError, ValueError):
                return {"error": f"Move {n}: guest_ids must be numbers."}, 400
            m["guest_ids"] = gids
            moved_ids.extend(gids)

        if len(room_ids) != len(set(room_ids)):
            return {"error": "Each move must have its own room. Guests in the same room "
                             "belong to the same reservation."}, 400
        if len(moved_ids) != len(set(moved_ids)):
            return {"error": "A guest is assigned to more than one move."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        cursor.execute("SELECT * FROM hotel_tblreservation WHERE id=%s FOR UPDATE", (original_id,))
        orig = cursor.fetchone()
        if not orig or orig.get("is_active") == 0:
            mydb.rollback()
            return {"error": f"Reservation {original_id} not found."}, 404
        if orig["Current_Status"] != "Registered":
            mydb.rollback()
            return {"error": "Only a Registered reservation can be split."}, 400

        # billed reservations can't be split
        # NOTE: adjust table/column to however your bills reference the reservation
        cursor.execute("SELECT COUNT(*) AS n FROM hotel_tblhotelbills WHERE ReservationID=%s", (original_id,))
        if cursor.fetchone()["n"] > 0:
            mydb.rollback()
            return {"error": "Billed reservations cannot be split."}, 400

        # in-house guests of the original
        cursor.execute("""
            SELECT * FROM hotel_tblinhouse_guests
            WHERE reservation_id=%s AND is_active=1
        """, (original_id,))
        guests = {r["idguest"]: r for r in cursor.fetchall()}

        unknown = [g for g in moved_ids if g not in guests]
        if unknown:
            mydb.rollback()
            return {"error": "These guests are not active in-house guests of this reservation.",
                    "guest_ids": unknown}, 400

        remaining = [g for gid, g in guests.items() if gid not in set(moved_ids)]
        if not remaining:
            mydb.rollback()
            return {"error": "At least one guest must stay on the original reservation."}, 400
        remaining_rooms = {g["room_id"] for g in remaining}

        # room validation
        for n, m in enumerate(moves, start=1):
            room_id = m["room_id"]
            cursor.execute("SELECT id FROM hotel_tblrooms WHERE id=%s", (room_id,))
            if not cursor.fetchone():
                mydb.rollback()
                return {"error": f"Move {n}: invalid room_id {room_id}."}, 400

            if room_id in remaining_rooms:
                mydb.rollback()
                return {"error": f"Move {n}: room {room_id} still has guests of the original "
                                 f"reservation. Guests in the same room stay in the same reservation."}, 400

            cursor.execute("""
                SELECT d.id FROM hotel_tblreservation_details d
                JOIN hotel_tblreservation r ON r.id = d.Reservation_ID
                WHERE d.room_id=%s AND d.is_current=1 AND d.is_active=1
                  AND r.Current_Status='Registered' AND d.Reservation_ID <> %s
                LIMIT 1
            """, (room_id, original_id))
            if cursor.fetchone():
                mydb.rollback()
                return {"error": f"Move {n}: room {room_id} is occupied by another reservation."}, 400

        now = datetime.now()
        results = []

        for n, m in enumerate(moves, start=1):
            room_id = m["room_id"]
            primary_guest = guests[m["guest_ids"][0]]   # first guest = primary / booker

            # -------- 1) create customer from the primary guest --------
            cursor.execute("""
                INSERT INTO customers (name, country)
                VALUES (%s, %s)
            """, (primary_guest["name"], primary_guest["nationality"]))
            customer_id = cursor.lastrowid

            # -------- 2) copy the reservation --------
            # advance payment is NOT copied, so it isn't counted twice
            cursor.execute("""
                INSERT INTO hotel_tblreservation (
                    outlet, Emp_ID, Pay_Mode, Billing_Inst, Reservation_type, designation,
                    Advance_Payment, Advance_Payment_Currency, Advance_Payment_Local,
                    Guest_ID, company_id, Reservation_Date, Market_Seg, business_Src,
                    Current_Status, Check_In, Check_Out
                ) VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL,
                          %s, %s, %s, %s, %s, 'Registered', %s, NULL)
            """, (orig["outlet"], orig["Emp_ID"], orig["Pay_Mode"], orig["Billing_Inst"],
                  orig["Reservation_type"], orig["designation"],
                  customer_id, orig["company_id"], orig["Reservation_Date"],
                  orig["Market_Seg"], orig["business_Src"], orig["Check_In"]))
            new_id = cursor.lastrowid

            # -------- 3) copy guest reservation + fit rates exactly --------
            cursor.execute("""
                INSERT INTO hotel_tblguestreservation
                    (Reservation_ID, No_of_children, No_of_adults, Likes, Dislikes,
                     Guest_Notes, start_date, end_date)
                SELECT %s, No_of_children, No_of_adults, Likes, Dislikes,
                       Guest_Notes, start_date, end_date
                FROM hotel_tblguestreservation
                WHERE Reservation_ID=%s AND is_active=1
            """, (new_id, original_id))

            cursor.execute("""
                INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active)
                SELECT rateID, mealID, %s, quantity, 1
                FROM hotel_tblfitrate
                WHERE reservationID=%s AND is_active=1
            """, (new_id, original_id))

            # -------- 4) room assignment for the new reservation --------
            cursor.execute("""
                INSERT INTO hotel_tblreservation_details
                    (Reservation_ID, room_id, is_current, created_at, is_active)
                VALUES (%s, %s, 1, %s, 1)
            """, (new_id, room_id, now))

            # -------- 5) move the in-house guests --------
            for gid in m["guest_ids"]:
                cursor.execute("""
                    UPDATE hotel_tblinhouse_guests
                    SET reservation_id=%s, room_id=%s, is_primary=%s
                    WHERE idguest=%s AND reservation_id=%s AND is_active=1
                """, (new_id, room_id, 1 if gid == primary_guest["idguest"] else 0,
                      gid, original_id))

            results.append({
                "reservation_id": new_id,
                "room_id": room_id,
                "Guest_ID": customer_id,
                "guests_moved": len(m["guest_ids"]),
            })

        # -------- 6) clean up the original --------
        # drop room assignments of rooms that no longer have any of its guests
        placeholders = ", ".join(["%s"] * len(remaining_rooms))
        cursor.execute(f"""
            DELETE FROM hotel_tblreservation_details
            WHERE Reservation_ID=%s AND is_current=1 AND is_active=1
              AND room_id NOT IN ({placeholders})
        """, (original_id, *remaining_rooms))

        # make sure the original still has a primary guest
        cursor.execute("""
            SELECT COUNT(*) AS n FROM hotel_tblinhouse_guests
            WHERE reservation_id=%s AND is_primary=1 AND is_active=1
        """, (original_id,))
        if cursor.fetchone()["n"] == 0:
            cursor.execute("""
                UPDATE hotel_tblinhouse_guests SET is_primary=1
                WHERE reservation_id=%s AND is_active=1
                ORDER BY idguest LIMIT 1
            """, (original_id,))

        mydb.commit()
        return jsonify({
            "original_reservation_id": original_id,
            "new_reservations": results
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()