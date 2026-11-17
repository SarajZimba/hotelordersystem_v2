from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()

app_file486 = Blueprint('app_file486', __name__)
from root.auth.check import token_auth
from datetime import datetime, timedelta, date


@app_file486.route("/frontoffice/closeday/next-date", methods=["GET"])
@cross_origin()
def get_next_close_date():
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

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

        # -------- INPUT --------
        property_id = request.args.get("property_id")

        if not property_id:
            return {"error": "property_id is required"}, 400

        # -------- VALIDATE PROPERTY --------
        cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (property_id,))
        if not cursor.fetchone():
            return {"error": "Property not found"}, 404

        # -------- FIND THE LAST CLOSED DATE FOR THIS PROPERTY --------
        cursor.execute("""
            SELECT MAX(business_date) AS last_closed
            FROM hotel_close_day
            WHERE property_id = %s
        """, (property_id,))
        row = cursor.fetchone()
        last_closed = row["last_closed"]

        if last_closed is None:
            next_date = date.today()
        else:
            next_date = last_closed + timedelta(days=1)

        return jsonify({
            "property_id": property_id,
            "next_close_date": str(next_date)
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()


# @app_file486.route("/frontoffice/closeday", methods=["POST"])
# @cross_origin()
# def close_hotel_day():
#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         data = request.get_json() or {}
#         property_id = data.get("property_id")
#         business_date = data.get("business_date")
#         closed_by = data.get("closed_by")  # optional: employee_id

#         if not property_id or not business_date:
#             return {"error": "property_id and business_date are required"}, 400

#         try:
#             parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

#         # -------- VALIDATE PROPERTY --------
#         cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (property_id,))
#         if not cursor.fetchone():
#             return {"error": "Property not found"}, 404

#         # -------- INSERT --------
#         try:
#             cursor.execute("""
#                 INSERT INTO hotel_close_day (property_id, business_date, closed_by)
#                 VALUES (%s, %s, %s)
#             """, (property_id, parsed_date, closed_by))

#             mydb.commit()

#         except mysql.connector.IntegrityError:
#             return {"error": "This business date has already been closed for this property"}, 400

#         return jsonify({
#             "message": "Day closed successfully",
#             "property_id": property_id,
#             "business_date": str(parsed_date)
#         }), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()


# @app_file486.route("/frontoffice/closeday", methods=["POST"])
# @cross_origin()
# def close_hotel_day():
#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         data = request.get_json() or {}
#         property_id = data.get("property_id")
#         business_date = data.get("business_date")
#         closed_by = data.get("closed_by")  # optional: employee_id

#         if not property_id or not business_date:
#             return {"error": "property_id and business_date are required"}, 400

#         try:
#             parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

#         # -------- VALIDATE PROPERTY, GET ITS NAME --------
#         cursor.execute("SELECT id, name FROM hotel_company_property WHERE id = %s", (property_id,))
#         property_row = cursor.fetchone()
#         if not property_row:
#             return {"error": "Property not found"}, 404

#         property_name = property_row["name"]

#         # -------- FIND THE LAST CLOSED ENTRY FOR THIS PROPERTY --------
#         cursor.execute("""
#             SELECT end_bill_id
#             FROM hotel_close_day
#             WHERE property_id = %s
#             ORDER BY business_date DESC
#             LIMIT 1
#         """, (property_id,))
#         last_entry = cursor.fetchone()

#         # -------- DETERMINE start_bill_id --------
#         if last_entry is None or last_entry["end_bill_id"] is None:
#             # No prior close -- start from this property's very first hotel bill
#             cursor.execute("""
#                 SELECT MIN(b.id) AS first_bill
#                 FROM hotel_tblhotelbills b
#                 JOIN hotel_tblreservation r ON b.reservationID = r.id
#                 WHERE r.outlet = %s
#             """, (property_name,))
#             first_bill_row = cursor.fetchone()
#             start_bill_id = first_bill_row["first_bill"]
#         else:
#             start_bill_id = last_entry["end_bill_id"] + 1

#         # -------- DETERMINE end_bill_id: latest hotel bill currently in the system --------
#         cursor.execute("""
#             SELECT MAX(b.id) AS last_bill
#             FROM hotel_tblhotelbills b
#             JOIN hotel_tblreservation r ON b.reservationID = r.id
#             WHERE r.outlet = %s
#         """, (property_name,))
#         last_bill_row = cursor.fetchone()
#         end_bill_id = last_bill_row["last_bill"]

#         if start_bill_id is None or end_bill_id is None:
#             return {"error": "No hotel bills found for this property -- nothing to close"}, 400

#         if end_bill_id < start_bill_id:
#             return {"error": "No new hotel bills since the last close for this property"}, 400

#         # -------- INSERT --------
#         try:
#             cursor.execute("""
#                 INSERT INTO hotel_close_day (property_id, business_date, start_bill_id, end_bill_id, closed_by)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (property_id, parsed_date, start_bill_id, end_bill_id, closed_by))

#             mydb.commit()

#         except mysql.connector.IntegrityError:
#             return {"error": "This business date has already been closed for this property"}, 400

#         return jsonify({
#             "message": "Day closed successfully",
#             "property_id": property_id,
#             "business_date": str(parsed_date),
#             "start_bill_id": start_bill_id,
#             "end_bill_id": end_bill_id
#         }), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()

# @app_file486.route("/frontoffice/closeday", methods=["POST"])
# @cross_origin()
# def close_hotel_day():
#     mydb = None
#     try:
#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         parts = auth_header.split(" ")
#         if len(parts) != 2:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(parts[1]):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         data = request.get_json(silent=True) or {}
#         property_id = data.get("property_id")
#         business_date = data.get("business_date")
#         closed_by = data.get("closed_by")  # optional: employee_id

#         if not property_id or not business_date:
#             return {"error": "property_id and business_date are required"}, 400

#         try:
#             parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- VALIDATE PROPERTY + LOCK IT --------
#         # FOR UPDATE serializes concurrent closes for the same property,
#         # so two requests can't compute overlapping ranges.
#         cursor.execute(
#             "SELECT name FROM hotel_company_property WHERE id = %s FOR UPDATE",
#             (property_id,)
#         )
#         property_row = cursor.fetchone()
#         if not property_row:
#             return {"error": "Property not found"}, 404
#         property_name = property_row["name"]

#         # -------- LAST CLOSED POSITIONS (one query) --------
#         # Independent lookups so a day with NULL reservation IDs
#         # doesn't reset the reservation range on the next close.
#         cursor.execute("""
#             SELECT
#               (SELECT end_bill_id FROM hotel_close_day
#                 WHERE property_id = %s AND end_bill_id IS NOT NULL
#                 ORDER BY id DESC LIMIT 1) AS last_bill,
#               (SELECT end_reservation_id FROM hotel_close_day
#                 WHERE property_id = %s AND end_reservation_id IS NOT NULL
#                 ORDER BY id DESC LIMIT 1) AS last_res
#         """, (property_id, property_id))
#         last = cursor.fetchone()
#         last_bill = last["last_bill"] or 0
#         last_res = last["last_res"] or 0

#         # -------- NEW BILL RANGE --------
#         cursor.execute("""
#             SELECT MIN(b.id) AS start_id, MAX(b.id) AS end_id
#             FROM hotel_tblhotelbills b
#             JOIN hotel_tblreservation r ON b.reservationID = r.id
#             WHERE r.outlet = %s AND b.id > %s
#         """, (property_name, last_bill))
#         bills = cursor.fetchone()
#         start_bill_id, end_bill_id = bills["start_id"], bills["end_id"]

#         # -------- NEW RESERVATION RANGE --------
#         cursor.execute("""
#             SELECT MIN(id) AS start_id, MAX(id) AS end_id
#             FROM hotel_tblreservation
#             WHERE outlet = %s AND id > %s
#         """, (property_name, last_res))
#         res = cursor.fetchone()
#         start_reservation_id, end_reservation_id = res["start_id"], res["end_id"]

#         # nothing at all to close: no bills AND no reservations
#         if start_bill_id is None and start_reservation_id is None:
#             return {"error": "No new bills or reservations since the last close for this property"}, 400

#         # -------- INSERT --------
#         try:
#             cursor.execute("""
#                 INSERT INTO hotel_close_day
#                     (property_id, business_date, start_bill_id, end_bill_id,
#                      start_reservation_id, end_reservation_id, closed_by)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s)
#             """, (property_id, parsed_date, start_bill_id, end_bill_id,
#                   start_reservation_id, end_reservation_id, closed_by))
#             mydb.commit()
#         except mysql.connector.IntegrityError:
#             mydb.rollback()
#             return {"error": "This business date has already been closed for this property"}, 400

#         return jsonify({
#             "message": "Day closed successfully",
#             "property_id": property_id,
#             "business_date": str(parsed_date),
#             "start_bill_id": start_bill_id,
#             "end_bill_id": end_bill_id,
#             "start_reservation_id": start_reservation_id,
#             "end_reservation_id": end_reservation_id
#         }), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()


from root.flask_routes.hotel.generalbills.generalbill import BILL_TYPES
@app_file486.route("/frontoffice/closeday", methods=["POST"])
@cross_origin()
def close_hotel_day():
    mydb = None
    try:
        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(parts[1]):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        data = request.get_json(silent=True) or {}
        property_id = data.get("property_id")
        business_date = data.get("business_date")
        closed_by = data.get("closed_by")  # optional: employee_id

        if not property_id or not business_date:
            return {"error": "property_id and business_date are required"}, 400

        try:
            parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- VALIDATE PROPERTY + LOCK IT --------
        # FOR UPDATE serializes concurrent closes for the same property,
        # so two requests can't compute overlapping ranges.
        cursor.execute(
            "SELECT name FROM hotel_company_property WHERE id = %s FOR UPDATE",
            (property_id,)
        )
        property_row = cursor.fetchone()
        if not property_row:
            return {"error": "Property not found"}, 404
        property_name = property_row["name"]

        # -------- LAST CLOSED POSITIONS (one query) --------
        # Independent lookups so a day with NULL reservation IDs
        # doesn't reset the reservation range on the next close.
        cursor.execute("""
            SELECT
              (SELECT end_bill_id FROM hotel_close_day
                WHERE property_id = %s AND end_bill_id IS NOT NULL
                ORDER BY id DESC LIMIT 1) AS last_bill,
              (SELECT end_reservation_id FROM hotel_close_day
                WHERE property_id = %s AND end_reservation_id IS NOT NULL
                ORDER BY id DESC LIMIT 1) AS last_res
        """, (property_id, property_id))
        last = cursor.fetchone()
        last_bill = last["last_bill"] or 0
        last_res = last["last_res"] or 0

        # -------- NEW BILL RANGE --------
        cursor.execute("""
            SELECT MIN(b.id) AS start_id, MAX(b.id) AS end_id
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE r.outlet = %s AND b.id > %s
        """, (property_name, last_bill))
        bills = cursor.fetchone()
        start_bill_id, end_bill_id = bills["start_id"], bills["end_id"]

        # -------- NEW RESERVATION RANGE --------
        cursor.execute("""
            SELECT MIN(id) AS start_id, MAX(id) AS end_id
            FROM hotel_tblreservation
            WHERE outlet = %s AND id > %s
        """, (property_name, last_res))
        res = cursor.fetchone()
        start_reservation_id, end_reservation_id = res["start_id"], res["end_id"]

        # -------- NEW GENERAL BILL RANGES (per bill type, this property only) --------
        # Last closed end id per bill type for this property
        cursor.execute("""
            SELECT g.bill_type, MAX(g.end_bill_id) AS last_end
            FROM hotel_close_day_generalbills g
            JOIN hotel_close_day cd ON g.close_day_id = cd.id
            WHERE cd.property_id = %s
            GROUP BY g.bill_type
        """, (property_id,))
        last_gb = {r["bill_type"]: r["last_end"] for r in cursor.fetchall()}

        general_ranges = []
        for bt in sorted(BILL_TYPES):
            cursor.execute("""
                SELECT MIN(id) AS start_id, MAX(id) AS end_id, COUNT(*) AS cnt
                FROM hotel_generalbills
                WHERE outlet = %s AND bill_type = %s AND id > %s
            """, (property_name, bt, last_gb.get(bt, 0)))
            r = cursor.fetchone()
            if r["start_id"] is not None:
                general_ranges.append({
                    "bill_type": bt,
                    "start_bill_id": r["start_id"],
                    "end_bill_id": r["end_id"],
                    "bill_count": r["cnt"],
                })

        # nothing at all to close: no hotel bills, no general bills, no reservations
        if start_bill_id is None and start_reservation_id is None and not general_ranges:
            return {"error": "No new bills, general bills or reservations since the last close for this property"}, 400

        # -------- INSERT (close record + general bill ranges, one transaction) --------
        try:
            cursor.execute("""
                INSERT INTO hotel_close_day
                    (property_id, business_date, start_bill_id, end_bill_id,
                     start_reservation_id, end_reservation_id, closed_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (property_id, parsed_date, start_bill_id, end_bill_id,
                  start_reservation_id, end_reservation_id, closed_by))
            close_day_id = cursor.lastrowid

            if general_ranges:
                cursor.executemany("""
                    INSERT INTO hotel_close_day_generalbills
                        (close_day_id, bill_type, start_bill_id, end_bill_id, bill_count)
                    VALUES (%s, %s, %s, %s, %s)
                """, [(close_day_id, g["bill_type"], g["start_bill_id"],
                       g["end_bill_id"], g["bill_count"]) for g in general_ranges])

            mydb.commit()
        except mysql.connector.IntegrityError:
            mydb.rollback()
            return {"error": "This business date has already been closed for this property"}, 400

        return jsonify({
            "message": "Day closed successfully",
            "close_day_id": close_day_id,
            "property_id": property_id,
            "business_date": str(parsed_date),
            "start_bill_id": start_bill_id,
            "end_bill_id": end_bill_id,
            "start_reservation_id": start_reservation_id,
            "end_reservation_id": end_reservation_id,
            "general_bills": general_ranges
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()


@app_file486.route("/front-office/closeday/check-restaurants", methods=["GET"])
@cross_origin()
def check_restaurants_closed():
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

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

        # -------- INPUT --------
        property_id = request.args.get("property_id")
        business_date = request.args.get("business_date")

        if not property_id or not business_date:
            return {"error": "property_id and business_date are required"}, 400

        try:
            parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        # -------- VALIDATE PROPERTY --------
        cursor.execute("SELECT id, name FROM hotel_company_property WHERE id = %s", (property_id,))
        property_row = cursor.fetchone()
        if not property_row:
            return {"error": "Property not found"}, 404

        # -------- GET ALL RESTAURANTS UNDER THIS PROPERTY --------
        cursor.execute("""
            SELECT id, Outlet, Company_name
            FROM outetNames
            WHERE company_property_id = %s
        """, (property_id,))
        outlets = cursor.fetchall()

        if not outlets:
            return jsonify({
                "property_id": property_id,
                "property_name": property_row["name"],
                "business_date": str(parsed_date),
                "all_closed": True,
                "restaurants": []
            }), 200

        outlet_ids = [o["id"] for o in outlets]

        # -------- CHECK WHICH OF THESE OUTLETS HAVE CLOSED FOR THIS DATE --------
        format_strings = ','.join(['%s'] * len(outlet_ids))
        cursor.execute(f"""
            SELECT outlet_id, closed_at, start_bill_id, end_bill_id
            FROM hotel_outlet_endday
            WHERE outlet_id IN ({format_strings})
            AND business_date = %s
        """, tuple(outlet_ids) + (parsed_date,))

        closed_map = {row["outlet_id"]: row for row in cursor.fetchall()}

        # -------- BUILD RESPONSE --------
        restaurants = []
        all_closed = True

        for outlet in outlets:
            closed_row = closed_map.get(outlet["id"])
            is_closed = closed_row is not None

            if not is_closed:
                all_closed = False

            restaurants.append({
                "outlet_id": outlet["id"],
                "outlet": outlet["Outlet"],
                "company_name": outlet["Company_name"],
                "closed": is_closed,
                "closed_at": str(closed_row["closed_at"]) if closed_row else None,
                "start_bill_id": closed_row["start_bill_id"] if closed_row else None,
                "end_bill_id": closed_row["end_bill_id"] if closed_row else None
            })

        return jsonify({
            "property_id": property_id,
            "property_name": property_row["name"],
            "business_date": str(parsed_date),
            "all_closed": all_closed,
            "restaurants": restaurants
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()