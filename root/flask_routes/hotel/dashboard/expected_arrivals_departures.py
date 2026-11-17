from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date


from collections import defaultdict
load_dotenv()

app_file498 = Blueprint('app_file498', __name__)
from root.auth.check import token_auth

# @app_file498.route("/expected-arrivals", methods=["GET"])
# @cross_origin()
# def expected_arrivals():
#     mydb = None
#     try:
#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- OUTLET --------
#         outlet = request.args.get("outlet")
#         if not outlet:
#             return {"error": "outlet is required"}, 400

#         today = date.today()

#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- RESERVATIONS ARRIVING TODAY --------
#         cursor.execute("""
#             SELECT
#                 res.id AS reservation_id,
#                 res.reservation_outlet_id,
#                 res.Current_Status,
#                 res.Reservation_type,
#                 res.Market_Seg,
#                 res.business_Src,
#                 res.Pay_Mode,
#                 res.Billing_Inst,
#                 res.Advance_Payment,
#                 res.Advance_Payment_Currency,
#                 res.Advance_Payment_Local,
#                 res.Guest_ID,
#                 res.company_id,
#                 st.s AS start_date,
#                 st.e AS end_date,
#                 st.adults,
#                 st.children,
#                 c.name AS guest_name,
#                 c.phone AS guest_phone,
#                 c.email AS guest_email,
#                 c.address AS guest_address,
#                 c.country AS guest_country,
#                 c.customer_type,
#                 c.is_vip,
#                 co.company_name,
#                 co.contact_person,
#                 co.phone AS company_phone,
#                 co.email AS company_email,
#                 co.address AS company_address,
#                 co.pan_number,
#                 co.company_type
#             FROM hotel_tblreservation res
#             JOIN (
#                 SELECT Reservation_ID,
#                        MIN(start_date) AS s,
#                        MAX(end_date) AS e,
#                        SUM(COALESCE(No_of_adults, 0)) AS adults,
#                        SUM(COALESCE(No_of_children, 0)) AS children
#                 FROM hotel_tblguestreservation
#                 WHERE is_active = 1
#                 GROUP BY Reservation_ID
#             ) st ON st.Reservation_ID = res.id
#             LEFT JOIN customers c ON c.id = res.Guest_ID
#             LEFT JOIN companies co ON co.id = res.company_id
#             WHERE res.is_active = 1
#               AND res.Current_Status = 'Reserved'
#               AND res.outlet = %s
#               AND st.s = %s
#             ORDER BY res.created_at DESC
#         """, (outlet, today))

#         rows = cursor.fetchall()

#         if not rows:
#             return jsonify({"date": str(today), "total_arrivals": 0, "arrivals": []}), 200

#         # -------- ROOMS --------
#         reservation_ids = [r["reservation_id"] for r in rows]
#         placeholders = ",".join(["%s"] * len(reservation_ids))
#         cursor.execute(f"""
#             SELECT rd.Reservation_ID, r.id AS room_id, r.room_no, r.room_type
#             FROM hotel_tblreservation_details rd
#             JOIN hotel_tblrooms r ON rd.room_id = r.id
#             WHERE rd.Reservation_ID IN ({placeholders})
#               AND rd.is_current = 1
#               AND rd.is_active = 1
#             ORDER BY r.room_no
#         """, tuple(reservation_ids))

#         rooms_map = defaultdict(list)
#         for rm in cursor.fetchall():
#             rooms_map[rm["Reservation_ID"]].append({
#                 "room_id": rm["room_id"],
#                 "room_no": rm["room_no"],
#                 "room_type": rm["room_type"]
#             })

#         # -------- BUILD RESPONSE --------
#         arrivals = []
#         for r in rows:
#             has_company = bool(r["company_id"] and r["company_name"])

#             arrivals.append({
#                 "reservation_id": r["reservation_id"],
#                 "reservation_outlet_id": r["reservation_outlet_id"],
#                 "display_name": r["company_name"] if has_company else r["guest_name"],
#                 "display_type": "company" if has_company else "guest",
#                 "guest": {
#                     "id": r["Guest_ID"],
#                     "name": r["guest_name"],
#                     "phone": r["guest_phone"],
#                     "email": r["guest_email"],
#                     "address": r["guest_address"],
#                     "country": r["guest_country"],
#                     "customer_type": r["customer_type"],
#                     "is_vip": bool(r["is_vip"]) if r["is_vip"] is not None else False
#                 } if r["Guest_ID"] else None,
#                 "company": {
#                     "id": r["company_id"],
#                     "company_name": r["company_name"],
#                     "contact_person": r["contact_person"],
#                     "phone": r["company_phone"],
#                     "email": r["company_email"],
#                     "address": r["company_address"],
#                     "pan_number": r["pan_number"],
#                     "company_type": r["company_type"]
#                 } if has_company else None,
#                 "start_date": str(r["start_date"]),
#                 "end_date": str(r["end_date"]),
#                 "no_of_adults": int(r["adults"] or 0),
#                 "no_of_children": int(r["children"] or 0),
#                 "current_status": r["Current_Status"],
#                 "reservation_type": r["Reservation_type"],
#                 "market_seg": r["Market_Seg"],
#                 "business_src": r["business_Src"],
#                 "pay_mode": r["Pay_Mode"],
#                 "billing_inst": r["Billing_Inst"],
#                 "advance_payment": float(r["Advance_Payment"]) if r["Advance_Payment"] is not None else None,
#                 "advance_payment_currency": r["Advance_Payment_Currency"],
#                 "advance_payment_local": float(r["Advance_Payment_Local"]) if r["Advance_Payment_Local"] is not None else None,
#                 "rooms": rooms_map.get(r["reservation_id"], [])
#             })

#         return jsonify({
#             "date": str(today),
#             "total_arrivals": len(arrivals),
#             "arrivals": arrivals
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

#     finally:
#         if mydb is not None:
#             try:
#                 mydb.close()
#             except Exception:
#                 pass


@app_file498.route("/expected-arrivals", methods=["GET"])
@cross_origin()
def expected_arrivals():
    mydb = None
    try:
        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- OUTLET --------
        outlet = request.args.get("outlet")
        if not outlet:
            return {"error": "outlet is required"}, 400

        today = date.today()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESERVATIONS ARRIVING TODAY --------
        cursor.execute("""
            SELECT
                res.id AS reservation_id,
                res.reservation_outlet_id,
                res.Current_Status,
                res.Reservation_type,
                res.Market_Seg,
                res.business_Src,
                res.Pay_Mode,
                res.Billing_Inst,
                res.Advance_Payment,
                res.Advance_Payment_Currency,
                res.Advance_Payment_Local,
                res.Guest_ID,
                res.company_id,
                st.s AS start_date,
                st.e AS end_date,
                st.adults,
                st.children,
                c.name AS guest_name,
                c.phone AS guest_phone,
                c.email AS guest_email,
                c.address AS guest_address,
                c.country AS guest_country,
                c.customer_type,
                c.is_vip,
                co.company_name,
                co.contact_person,
                co.phone AS company_phone,
                co.email AS company_email,
                co.address AS company_address,
                co.pan_number,
                co.company_type
            FROM hotel_tblreservation res
            JOIN (
                SELECT Reservation_ID,
                       MIN(start_date) AS s,
                       MAX(end_date) AS e,
                       SUM(COALESCE(No_of_adults, 0)) AS adults,
                       SUM(COALESCE(No_of_children, 0)) AS children
                FROM hotel_tblguestreservation
                WHERE is_active = 1
                GROUP BY Reservation_ID
            ) st ON st.Reservation_ID = res.id
            LEFT JOIN customers c ON c.id = res.Guest_ID
            LEFT JOIN companies co ON co.id = res.company_id
            WHERE res.is_active = 1
              AND res.Current_Status = 'Reserved'
              AND res.outlet = %s
              AND st.s = %s
            ORDER BY res.created_at DESC
        """, (outlet, today))

        rows = cursor.fetchall()

        if not rows:
            return jsonify({"date": str(today), "total_arrivals": 0, "arrivals": []}), 200

        reservation_ids = [r["reservation_id"] for r in rows]
        placeholders = ",".join(["%s"] * len(reservation_ids))

        # -------- ROOMS --------
        cursor.execute(f"""
            SELECT rd.Reservation_ID, r.id AS room_id, r.room_no, r.room_type
            FROM hotel_tblreservation_details rd
            JOIN hotel_tblrooms r ON rd.room_id = r.id
            WHERE rd.Reservation_ID IN ({placeholders})
              AND rd.is_current = 1
              AND rd.is_active = 1
            ORDER BY r.room_no
        """, tuple(reservation_ids))

        rooms_map = defaultdict(list)
        for rm in cursor.fetchall():
            rooms_map[rm["Reservation_ID"]].append({
                "room_id": rm["room_id"],
                "room_no": rm["room_no"],
                "room_type": rm["room_type"]
            })

        # -------- FITRATES --------
        cursor.execute(f"""
            SELECT
                fr.id,
                fr.reservationID,
                fr.rateID,
                fr.mealID,
                fr.quantity,
                fr.created_at,
                rt.room_name,
                rt.room_type,
                rt.rate AS room_rate,
                rt.currency AS room_currency,
                mp.mp AS meal_plan,
                mp.rate AS meal_rate,
                mp.currency AS meal_currency
            FROM hotel_tblfitrate fr
            LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
            LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
            WHERE fr.reservationID IN ({placeholders})
              AND fr.is_active = 1
            ORDER BY fr.id DESC
        """, tuple(reservation_ids))

        fitrates_map = defaultdict(list)
        for fr in cursor.fetchall():
            fitrates_map[fr["reservationID"]].append({
                "id": fr["id"],
                "quantity": fr["quantity"],
                "rate_details": {
                    "id": fr["rateID"],
                    "room_name": fr["room_name"],
                    "room_type": fr["room_type"],
                    "rate": float(fr["room_rate"]) if fr["room_rate"] else 0,
                    "currency": fr["room_currency"]
                } if fr["rateID"] else None,
                "meal_details": {
                    "id": fr["mealID"],
                    "mp": fr["meal_plan"],
                    "rate": float(fr["meal_rate"]) if fr["meal_rate"] else 0,
                    "currency": fr["meal_currency"]
                } if fr["mealID"] else None,
                "created_at": fr["created_at"].strftime("%Y-%m-%d %H:%M:%S") if fr["created_at"] else None
            })

        # -------- BUILD RESPONSE --------
        arrivals = []
        for r in rows:
            has_company = bool(r["company_id"] and r["company_name"])
            fit_rates = fitrates_map.get(r["reservation_id"], [])
            total_amount = sum(
                (f["quantity"] or 0) * f["rate_details"]["rate"]
                for f in fit_rates if f["rate_details"]
            )

            arrivals.append({
                "reservation_id": r["reservation_id"],
                "reservation_outlet_id": r["reservation_outlet_id"],
                "display_name": r["company_name"] if has_company else r["guest_name"],
                "display_type": "company" if has_company else "guest",
                "guest": {
                    "id": r["Guest_ID"],
                    "name": r["guest_name"],
                    "phone": r["guest_phone"],
                    "email": r["guest_email"],
                    "address": r["guest_address"],
                    "country": r["guest_country"],
                    "customer_type": r["customer_type"],
                    "is_vip": bool(r["is_vip"]) if r["is_vip"] is not None else False
                } if r["Guest_ID"] else None,
                "company": {
                    "id": r["company_id"],
                    "company_name": r["company_name"],
                    "contact_person": r["contact_person"],
                    "phone": r["company_phone"],
                    "email": r["company_email"],
                    "address": r["company_address"],
                    "pan_number": r["pan_number"],
                    "company_type": r["company_type"]
                } if has_company else None,
                "start_date": str(r["start_date"]),
                "end_date": str(r["end_date"]),
                "no_of_adults": int(r["adults"] or 0),
                "no_of_children": int(r["children"] or 0),
                "current_status": r["Current_Status"],
                "reservation_type": r["Reservation_type"],
                "market_seg": r["Market_Seg"],
                "business_src": r["business_Src"],
                "pay_mode": r["Pay_Mode"],
                "billing_inst": r["Billing_Inst"],
                "advance_payment": float(r["Advance_Payment"]) if r["Advance_Payment"] is not None else None,
                "advance_payment_currency": r["Advance_Payment_Currency"],
                "advance_payment_local": float(r["Advance_Payment_Local"]) if r["Advance_Payment_Local"] is not None else None,
                "rooms": rooms_map.get(r["reservation_id"], []),
                "fit_rates": fit_rates,
                "fitrate_count": len(fit_rates),
                "total_amount": total_amount
            })

        return jsonify({
            "date": str(today),
            "total_arrivals": len(arrivals),
            "arrivals": arrivals
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb is not None:
            try:
                mydb.close()
            except Exception:
                pass


@app_file498.route("/expected-departures", methods=["GET"])
@cross_origin()
def expected_departures():
    mydb = None
    try:
        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- OUTLET --------
        outlet = request.args.get("outlet")
        if not outlet:
            return {"error": "outlet is required"}, 400

        today = date.today()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESERVATIONS DEPARTING TODAY OR OVERDUE --------
        cursor.execute("""
            SELECT
                res.id AS reservation_id,
                res.reservation_outlet_id,
                res.Current_Status,
                res.Reservation_type,
                res.Market_Seg,
                res.business_Src,
                res.Pay_Mode,
                res.Billing_Inst,
                res.Advance_Payment,
                res.Advance_Payment_Currency,
                res.Advance_Payment_Local,
                res.Check_In,
                res.Guest_ID,
                res.company_id,
                st.s AS start_date,
                st.e AS end_date,
                st.adults,
                st.children,
                c.name AS guest_name,
                c.phone AS guest_phone,
                c.email AS guest_email,
                c.address AS guest_address,
                c.country AS guest_country,
                c.customer_type,
                c.is_vip,
                co.company_name,
                co.contact_person,
                co.phone AS company_phone,
                co.email AS company_email,
                co.address AS company_address,
                co.pan_number,
                co.company_type
            FROM hotel_tblreservation res
            JOIN (
                SELECT Reservation_ID,
                       MIN(start_date) AS s,
                       MAX(end_date) AS e,
                       SUM(COALESCE(No_of_adults, 0)) AS adults,
                       SUM(COALESCE(No_of_children, 0)) AS children
                FROM hotel_tblguestreservation
                WHERE is_active = 1
                GROUP BY Reservation_ID
            ) st ON st.Reservation_ID = res.id
            LEFT JOIN customers c ON c.id = res.Guest_ID
            LEFT JOIN companies co ON co.id = res.company_id
            WHERE res.is_active = 1
              AND res.Current_Status = 'Registered'
              AND res.outlet = %s
              AND st.e <= %s
            ORDER BY st.e ASC, res.created_at DESC
        """, (outlet, today))

        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "date": str(today),
                "total_departures": 0,
                "total_overdue": 0,
                "departures": []
            }), 200

        # -------- ROOMS --------
        reservation_ids = [r["reservation_id"] for r in rows]
        placeholders = ",".join(["%s"] * len(reservation_ids))
        cursor.execute(f"""
            SELECT rd.Reservation_ID, r.id AS room_id, r.room_no, r.room_type
            FROM hotel_tblreservation_details rd
            JOIN hotel_tblrooms r ON rd.room_id = r.id
            WHERE rd.Reservation_ID IN ({placeholders})
              AND rd.is_current = 1
              AND rd.is_active = 1
            ORDER BY r.room_no
        """, tuple(reservation_ids))

        rooms_map = defaultdict(list)
        for rm in cursor.fetchall():
            rooms_map[rm["Reservation_ID"]].append({
                "room_id": rm["room_id"],
                "room_no": rm["room_no"],
                "room_type": rm["room_type"]
            })

        # -------- BUILD RESPONSE --------
        departures = []
        total_overdue = 0

        for r in rows:
            has_company = bool(r["company_id"] and r["company_name"])

            end_d = r["end_date"]
            if isinstance(end_d, str):
                end_d = datetime.strptime(end_d, "%Y-%m-%d").date()
            days_overdue = max((today - end_d).days, 0)
            is_overdue = days_overdue > 0
            if is_overdue:
                total_overdue += 1

            departures.append({
                "reservation_id": r["reservation_id"],
                "reservation_outlet_id": r["reservation_outlet_id"],
                "display_name": r["company_name"] if has_company else r["guest_name"],
                "display_type": "company" if has_company else "guest",
                "guest": {
                    "id": r["Guest_ID"],
                    "name": r["guest_name"],
                    "phone": r["guest_phone"],
                    "email": r["guest_email"],
                    "address": r["guest_address"],
                    "country": r["guest_country"],
                    "customer_type": r["customer_type"],
                    "is_vip": bool(r["is_vip"]) if r["is_vip"] is not None else False
                } if r["Guest_ID"] else None,
                "company": {
                    "id": r["company_id"],
                    "company_name": r["company_name"],
                    "contact_person": r["contact_person"],
                    "phone": r["company_phone"],
                    "email": r["company_email"],
                    "address": r["company_address"],
                    "pan_number": r["pan_number"],
                    "company_type": r["company_type"]
                } if has_company else None,
                "start_date": str(r["start_date"]),
                "end_date": str(end_d),
                "is_overdue": is_overdue,
                "days_overdue": days_overdue,
                "check_in": r["Check_In"].strftime("%Y-%m-%d %H:%M:%S") if r["Check_In"] else None,
                "no_of_adults": int(r["adults"] or 0),
                "no_of_children": int(r["children"] or 0),
                "current_status": r["Current_Status"],
                "reservation_type": r["Reservation_type"],
                "market_seg": r["Market_Seg"],
                "business_src": r["business_Src"],
                "pay_mode": r["Pay_Mode"],
                "billing_inst": r["Billing_Inst"],
                "advance_payment": float(r["Advance_Payment"]) if r["Advance_Payment"] is not None else None,
                "advance_payment_currency": r["Advance_Payment_Currency"],
                "advance_payment_local": float(r["Advance_Payment_Local"]) if r["Advance_Payment_Local"] is not None else None,
                "rooms": rooms_map.get(r["reservation_id"], [])
            })

        return jsonify({
            "date": str(today),
            "total_departures": len(departures),
            "total_overdue": total_overdue,
            "departures": departures
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb is not None:
            try:
                mydb.close()
            except Exception:
                pass