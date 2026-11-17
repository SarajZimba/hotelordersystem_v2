from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date


from collections import defaultdict
load_dotenv()

app_file409 = Blueprint('app_file409', __name__)
from root.auth.check import token_auth


# @app_file409.route("/room-availability", methods=["POST"])
# @cross_origin()
# def room_availability():
#     mydb = None
#     try:
#         json_data = request.get_json() or {}

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT VALIDATION --------
#         outlet = (json_data.get("outlet") or "").strip()
#         if not outlet:
#             return {"error": "outlet is required."}, 400

#         from_date = json_data.get("from_date")
#         # accept both "end_date" (old) and "to_date" (same as analytics API)
#         to_date = json_data.get("to_date") or json_data.get("end_date")

#         if not from_date or not to_date:
#             return {"error": "Both from_date and to_date are required (format: YYYY-MM-DD)"}, 400

#         try:
#             start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
#             end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

#         if end_date < start_date:
#             return {"error": "to_date must be on or after from_date."}, 400

#         requested_rooms = json_data.get("rooms")
#         total_days = (end_date - start_date).days + 1
#         today = date.today()

#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- 1. ROOM INVENTORY (scoped to outlet) --------
#         cursor.execute("""
#             SELECT room_type, COUNT(*) AS total
#             FROM hotel_tblrooms
#             WHERE is_active = 1
#             AND outlet = %s
#             GROUP BY room_type
#         """, (outlet,))

#         room_type_totals = {row["room_type"]: int(row["total"]) for row in cursor.fetchall()}

#         if not room_type_totals:
#             return jsonify([]), 200

#         # -------- 2. BOOKINGS (scoped to outlet) --------
#         # One row per reservation stay (MIN/MAX over guest rows) so multiple
#         # guests never multiply the room quantity.
#         cursor.execute("""
#             SELECT
#                 rt.room_type,
#                 f.quantity,
#                 res.Current_Status,
#                 st.s AS start_date,
#                 st.e AS end_date
#             FROM hotel_tblfitrate f
#             JOIN hotel_tblrates rt
#                 ON f.rateID = rt.id AND rt.is_active = 1
#             JOIN hotel_tblreservation res
#                 ON f.reservationID = res.id AND res.is_active = 1
#             JOIN (
#                 SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
#                 FROM hotel_tblguestreservation
#                 WHERE is_active = 1
#                 GROUP BY Reservation_ID
#             ) st ON st.Reservation_ID = res.id
#             WHERE f.is_active = 1
#               AND res.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
#               AND res.outlet = %s
#               AND st.s <= %s
#               AND st.e >= %s
#         """, (outlet, end_date, start_date))

#         bookings = cursor.fetchall()
#         bookings_by_day = defaultdict(lambda: defaultdict(int))

#         for booking in bookings:
#             start = booking["start_date"]
#             end = booking["end_date"]

#             if isinstance(start, str):
#                 start = datetime.strptime(start, "%Y-%m-%d").date()
#             if isinstance(end, str):
#                 end = datetime.strptime(end, "%Y-%m-%d").date()

#             room_type = booking["room_type"]
#             quantity = int(booking["quantity"] or 0)
#             status = booking["Current_Status"]

#             # Occupied nights: start <= night < end.
#             # A same-day stay (start == end) occupies its start day only.
#             same_day = start == end
#             last_night = end if same_day else end - timedelta(days=1)

#             # Checked Out reservations only occupied the room up to today.
#             # Future nights of an early checkout are free again.
#             if status == "Checked Out":
#                 checkout_cap = today if same_day else today - timedelta(days=1)
#                 last_night = min(last_night, checkout_cap)

#             current = max(start, start_date)
#             last = min(last_night, end_date)

#             while current <= last:
#                 bookings_by_day[current][room_type] += quantity
#                 current += timedelta(days=1)

#         # -------- 3. BUILD DAILY RESPONSE --------
#         response_data = []

#         for day_offset in range(total_days):
#             current_date = start_date + timedelta(days=day_offset)

#             booked_rooms = {}
#             available_rooms = {}

#             for room_type, total in room_type_totals.items():
#                 booked = bookings_by_day[current_date].get(room_type, 0)
#                 booked_rooms[room_type] = booked
#                 available_rooms[room_type] = max(total - booked, 0)

#             day_data = {
#                 "date": str(current_date),
#                 "total_rooms": dict(room_type_totals),
#                 "booked_rooms": booked_rooms,
#                 "available_rooms": available_rooms
#             }

#             if requested_rooms:
#                 overall_status = "available"
#                 for req in requested_rooms:
#                     req_type = req.get("room_type")
#                     req_qty = int(req.get("quantity", 0) or 0)
#                     if req_qty > available_rooms.get(req_type, 0):
#                         overall_status = "not_available"
#                         break
#                 day_data["status"] = overall_status

#             response_data.append(day_data)

#         return jsonify({
#             "outlet": outlet,
#             "start_date": str(start_date),
#             "end_date": str(end_date),
#             "data": response_data
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

#     finally:
#         if mydb is not None:
#             try:
#                 mydb.close()
#             except Exception:
#                 pass


@app_file409.route("/room-availability", methods=["POST"])
@cross_origin()
def room_availability():
    mydb = None
    try:
        json_data = request.get_json() or {}

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT VALIDATION --------
        outlet = (json_data.get("outlet") or "").strip()
        if not outlet:
            return {"error": "outlet is required."}, 400

        from_date = json_data.get("from_date")
        to_date = json_data.get("to_date") or json_data.get("end_date")

        if not from_date or not to_date:
            return {"error": "Both from_date and to_date are required (format: YYYY-MM-DD)"}, 400

        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        if end_date < start_date:
            return {"error": "to_date must be on or after from_date."}, 400

        requested_rooms = json_data.get("rooms")
        total_days = (end_date - start_date).days + 1
        today = date.today()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- 1. ROOM INVENTORY (scoped to outlet) --------
        cursor.execute("""
            SELECT room_type, COUNT(*) AS total
            FROM hotel_tblrooms
            WHERE is_active = 1
            AND outlet = %s
            GROUP BY room_type
        """, (outlet,))

        room_type_totals = {row["room_type"]: int(row["total"]) for row in cursor.fetchall()}

        if not room_type_totals:
            return jsonify([]), 200

        # -------- 2. BOOKINGS (scoped to outlet) --------
        cursor.execute("""
            SELECT
                rt.room_type,
                f.quantity,
                res.Current_Status,
                st.s AS start_date,
                st.e AS end_date
            FROM hotel_tblfitrate f
            JOIN hotel_tblrates rt
                ON f.rateID = rt.id AND rt.is_active = 1
            JOIN hotel_tblreservation res
                ON f.reservationID = res.id AND res.is_active = 1
            JOIN (
                SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
                FROM hotel_tblguestreservation
                WHERE is_active = 1
                GROUP BY Reservation_ID
            ) st ON st.Reservation_ID = res.id
            WHERE f.is_active = 1
              AND res.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
              AND res.outlet = %s
              AND st.s <= %s
              AND st.e >= %s
        """, (outlet, end_date, start_date))

        bookings = cursor.fetchall()
        bookings_by_day = defaultdict(lambda: defaultdict(int))

        for booking in bookings:
            start = booking["start_date"]
            end = booking["end_date"]

            if isinstance(start, str):
                start = datetime.strptime(start, "%Y-%m-%d").date()
            if isinstance(end, str):
                end = datetime.strptime(end, "%Y-%m-%d").date()

            room_type = booking["room_type"]
            quantity = int(booking["quantity"] or 0)
            status = booking["Current_Status"]

            same_day = start == end
            last_night = end if same_day else end - timedelta(days=1)

            if status == "Checked Out":
                checkout_cap = today if same_day else today - timedelta(days=1)
                last_night = min(last_night, checkout_cap)

            current = max(start, start_date)
            last = min(last_night, end_date)

            while current <= last:
                bookings_by_day[current][room_type] += quantity
                current += timedelta(days=1)

        # -------- 2b. BLOCKED ROOMS (Out of Order / Out of Service) --------
        # Each blocked room is deducted from its type, inclusive of start/end date.
        # Early-released blocks stop applying from the release date.
        cursor.execute("""
            SELECT
                b.room_id,
                r.room_type,
                b.start_date,
                b.end_date,
                b.released_at
            FROM hotel_tblroom_blocks b
            JOIN hotel_tblrooms r
                ON r.id = b.room_id AND r.is_active = 1 AND r.outlet = %s
            WHERE b.is_active = 1
              AND b.start_date <= %s
              AND b.end_date >= %s
        """, (outlet, end_date, start_date))

        # set of room_ids per day/type so overlapping blocks never double-deduct
        blocked_by_day = defaultdict(lambda: defaultdict(set))

        for blk in cursor.fetchall():
            b_start = blk["start_date"]
            b_end = blk["end_date"]

            if isinstance(b_start, str):
                b_start = datetime.strptime(b_start, "%Y-%m-%d").date()
            if isinstance(b_end, str):
                b_end = datetime.strptime(b_end, "%Y-%m-%d").date()

            released_at = blk["released_at"]
            if released_at:
                released_day = released_at.date() if hasattr(released_at, "date") else released_at
                b_end = min(b_end, released_day - timedelta(days=1))

            current = max(b_start, start_date)
            last = min(b_end, end_date)

            while current <= last:
                blocked_by_day[current][blk["room_type"]].add(blk["room_id"])
                current += timedelta(days=1)

        # -------- 3. BUILD DAILY RESPONSE --------
        response_data = []

        for day_offset in range(total_days):
            current_date = start_date + timedelta(days=day_offset)

            booked_rooms = {}
            blocked_rooms = {}
            available_rooms = {}

            for room_type, total in room_type_totals.items():
                booked = bookings_by_day[current_date].get(room_type, 0)
                blocked = len(blocked_by_day[current_date].get(room_type, ()))
                booked_rooms[room_type] = booked
                blocked_rooms[room_type] = blocked
                available_rooms[room_type] = max(total - booked - blocked, 0)

            day_data = {
                "date": str(current_date),
                "total_rooms": dict(room_type_totals),
                "booked_rooms": booked_rooms,
                "blocked_rooms": blocked_rooms,
                "available_rooms": available_rooms
            }

            if requested_rooms:
                overall_status = "available"
                for req in requested_rooms:
                    req_type = req.get("room_type")
                    req_qty = int(req.get("quantity", 0) or 0)
                    if req_qty > available_rooms.get(req_type, 0):
                        overall_status = "not_available"
                        break
                day_data["status"] = overall_status

            response_data.append(day_data)

        return jsonify({
            "outlet": outlet,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "data": response_data
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb is not None:
            try:
                mydb.close()
            except Exception:
                pass

@app_file409.route("/room-bookings-by-customer-detailed", methods=["POST"])
@cross_origin()
def room_bookings_by_customer_detailed():
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
            token = auth_header.split(" ")[1]
        except IndexError:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get outlet from request
        outlet = json_data.get("outlet")

        if not outlet:
            return {"error": "outlet is required."}, 400

        outlet = outlet.strip()

        # Get date range from request
        from_date = json_data.get("from_date")
        to_date = json_data.get("to_date")

        today = date.today()

        if from_date:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        else:
            start_date = today

        if to_date:
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        else:
            end_date = start_date + timedelta(days=14)

        # Validate date range
        if start_date > end_date:
            return {"error": "Start date cannot be after end date"}, 400

        # 1. Get all active room types with their total counts, scoped to outlet
        cursor.execute("""
            SELECT 
                room_type,
                COUNT(*) as total_rooms
            FROM hotel_tblrooms
            WHERE is_active = 1
            AND outlet = %s
            GROUP BY room_type
            ORDER BY room_type
        """, (outlet,))

        room_type_counts = cursor.fetchall()
        room_type_info = {}
        room_type_list = []

        for rt in room_type_counts:
            room_type_info[rt['room_type']] = rt['total_rooms']
            room_type_list.append(rt['room_type'])

        # 2. Get bookings with customer and room details, scoped to outlet
        cursor.execute("""
            SELECT
                r.room_type,
                f.quantity,
                g.start_date,
                g.end_date,
                res.id as reservation_id,
                res.Reservation_Date,
                res.Current_Status,
                res.Check_In,
                res.Check_Out,
                res.Advance_Payment,
                res.Reservation_type,
                res.outlet,
                c.id as customer_id,
                c.name as customer_name,
                c.email as customer_email,
                c.phone as customer_phone,
                c.address as customer_address,
                c.customer_type,
                c.source as customer_source,
                c.guestPan as customer_pan,
                rd.room_id,
                rm.room_no,
                rm.room_state,
                rm.phone_no as room_phone,
                rm.preference as room_preference,
                rm.room_view,
                rm.room_notes
            FROM hotel_tblfitrate f
            JOIN hotel_tblrates r ON f.rateID = r.id
            JOIN hotel_tblreservation res ON f.reservationID = res.id
            JOIN hotel_tblguestreservation g ON g.Reservation_ID = res.id
            LEFT JOIN customers c ON res.Guest_ID = c.id
            LEFT JOIN hotel_tblreservation_details rd ON res.id = rd.Reservation_ID AND rd.is_current = 1 AND rd.is_active = 1
            LEFT JOIN hotel_tblrooms rm ON rd.room_id = rm.id AND rm.is_active = 1
            WHERE res.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
            AND g.start_date <= %s
            AND g.end_date >= %s
            AND res.outlet = %s
            ORDER BY g.start_date, r.room_type, c.name, rm.room_no
        """, (end_date, start_date, outlet))

        bookings = cursor.fetchall()

        # Structure: day -> room_type -> customer -> list of booking details
        bookings_by_day = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # Track customer summary across the entire period
        customer_summary = defaultdict(lambda: {
            "total_nights": 0,
            "total_rooms": 0,
            "room_types": defaultdict(int),
            "reservations": set(),
            "customer_details": {}
        })

        # Process bookings
        for booking in bookings:
            start = booking["start_date"]
            end = booking["end_date"]
            room_type = booking["room_type"]
            quantity = booking["quantity"] or 0

            # Skip invalid quantities
            if quantity <= 0:
                continue

            customer_id = booking.get("customer_id")

            # Create unique customer key
            if customer_id:
                customer_key = str(customer_id)
                customer_name = booking.get("customer_name", "Unknown")
            else:
                customer_key = f"walkin_{booking['reservation_id']}"
                customer_name = f"Walk-in Guest"

            # Calculate effective date range within query period
            effective_start = max(start, start_date)
            effective_end = min(end, end_date)

            current = effective_start
            nights_count = 0

            # Loop through each night of stay
            while current < effective_end:
                # Create room assignment details
                room_assignment = None
                if booking.get("room_id"):
                    room_assignment = {
                        "room_id": booking["room_id"],
                        "room_no": booking["room_no"],
                        "room_state": booking["room_state"],
                        "room_phone": booking["room_phone"],
                        "room_preference": booking["room_preference"],
                        "room_view": booking["room_view"],
                        "room_notes": booking["room_notes"]
                    }

                # Create booking entry with all details
                booking_entry = {
                    "reservation_id": booking["reservation_id"],
                    "room_type": room_type,
                    "quantity": quantity,
                    "start_date": str(start),
                    "end_date": str(end),
                    "reservation_date": str(booking["Reservation_Date"]),
                    "status": booking["Current_Status"],
                    "check_in": str(booking["Check_In"]) if booking["Check_In"] else None,
                    "check_out": str(booking["Check_Out"]) if booking["Check_Out"] else None,
                    "advance_payment": float(booking["Advance_Payment"]) if booking["Advance_Payment"] else 0,
                    "reservation_type": booking["Reservation_type"],
                    "outlet": booking.get("outlet"),
                    # Customer details
                    "customer_id": booking.get("customer_id"),
                    "customer_name": booking.get("customer_name"),
                    "customer_email": booking.get("customer_email"),
                    "customer_phone": booking.get("customer_phone"),
                    "customer_address": booking.get("customer_address"),
                    "customer_type": booking.get("customer_type"),
                    "customer_source": booking.get("customer_source"),
                    "customer_pan": booking.get("customer_pan"),
                    # Room assignment details (if registered)
                    "room_assignment": room_assignment
                }

                # Store in structure: day -> room_type -> customer -> bookings
                bookings_by_day[current][room_type][customer_key].append(booking_entry)
                nights_count += 1
                current += timedelta(days=1)

            # Update customer summary for customers with ID
            if customer_id:
                summary_key = str(customer_id)
                customer_summary[summary_key]["total_nights"] += nights_count
                customer_summary[summary_key]["total_rooms"] += quantity * nights_count
                customer_summary[summary_key]["room_types"][room_type] += quantity * nights_count
                customer_summary[summary_key]["reservations"].add(booking["reservation_id"])
                # Store customer details (only once)
                if not customer_summary[summary_key]["customer_details"]:
                    customer_summary[summary_key]["customer_details"] = {
                        "customer_id": booking.get("customer_id"),
                        "customer_name": booking.get("customer_name", "Unknown"),
                        "customer_email": booking.get("customer_email"),
                        "customer_phone": booking.get("customer_phone"),
                        "customer_address": booking.get("customer_address"),
                        "customer_type": booking.get("customer_type"),
                        "customer_source": booking.get("customer_source"),
                        "customer_pan": booking.get("customer_pan")
                    }

        # Build the response structure with all room types
        response_data = []

        current_date = start_date
        while current_date <= end_date:
            date_str = str(current_date)
            day_data = {
                "date": date_str,
                "room_types": []
            }

            # For each room type, show customers who have bookings
            for room_type in room_type_list:
                total_available = room_type_info.get(room_type, 0)
                total_booked = 0
                customers_data = []

                if current_date in bookings_by_day and room_type in bookings_by_day[current_date]:
                    customers_data_dict = bookings_by_day[current_date][room_type]

                    # Sort customers by name
                    for customer_key in sorted(customers_data_dict.keys()):
                        bookings_list = customers_data_dict[customer_key]
                        total_quantity = sum(b["quantity"] for b in bookings_list)
                        total_booked += total_quantity

                        # Group rooms by assignment
                        rooms_with_details = []
                        for booking_entry in bookings_list:
                            room_info = {
                                "quantity": booking_entry["quantity"],
                                "room_assignment": booking_entry.get("room_assignment"),
                                "booking_details": booking_entry
                            }
                            rooms_with_details.append(room_info)

                        # Get customer details from first booking
                        first_booking = bookings_list[0] if bookings_list else None

                        if first_booking and first_booking.get("customer_id"):
                            customer_details = {
                                "customer_id": first_booking.get("customer_id"),
                                "customer_name": first_booking.get("customer_name"),
                                "customer_email": first_booking.get("customer_email"),
                                "customer_phone": first_booking.get("customer_phone"),
                                "customer_type": first_booking.get("customer_type")
                            }
                        elif first_booking and "walkin" in customer_key:
                            customer_details = {
                                "customer_id": None,
                                "customer_name": f"Walk-in Guest",
                                "customer_email": None,
                                "customer_phone": None,
                                "customer_type": "Walk-in"
                            }
                        else:
                            customer_details = {
                                "customer_id": None,
                                "customer_name": "Unknown",
                                "customer_email": None,
                                "customer_phone": None,
                                "customer_type": None
                            }

                        customers_data.append({
                            "customer": customer_details,
                            "total_rooms": total_quantity,
                            "rooms": rooms_with_details
                        })

                # Calculate available rooms
                total_available_rooms = total_available
                total_rooms_booked = total_booked
                available_rooms = max(total_available_rooms - total_rooms_booked, 0)

                room_type_data = {
                    "room_type": room_type,
                    "total_available": total_available_rooms,
                    "total_booked": total_rooms_booked,
                    "available": available_rooms,
                    "customers": customers_data
                }

                day_data["room_types"].append(room_type_data)

            response_data.append(day_data)
            current_date += timedelta(days=1)

        # Convert customer summary sets to lists for JSON serialization
        for customer_key, customer_data in customer_summary.items():
            customer_data["reservations"] = list(customer_data["reservations"])
            customer_data["room_types"] = dict(customer_data["room_types"])

        mydb.close()

        return jsonify({
            "outlet": outlet,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_days": (end_date - start_date).days + 1,
            "room_types_summary": room_type_info,
            "daily_breakdown": response_data,
            "customer_summary": dict(customer_summary)
        }), 200

    except mysql.connector.Error as db_error:
        return {"error": f"Database error: {str(db_error)}"}, 500
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        # Ensure database connection is closed
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'mydb' in locals() and mydb.is_connected():
            mydb.close()