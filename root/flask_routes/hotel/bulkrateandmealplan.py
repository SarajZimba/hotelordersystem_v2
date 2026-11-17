from flask import Blueprint, request
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

app_file401 = Blueprint('app_file401', __name__)
from root.auth.check import token_auth

# @app_file401.route("/create-rates-mealplans", methods=["POST"])
# @cross_origin()
# def create_rates_mealplans():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Token validation
#         json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Extract lists
#         rates_data = json_data.get("Rates", [])
#         meals_data = json_data.get("Meals", [])

#         if not isinstance(rates_data, list) or not isinstance(meals_data, list):
#             return {"error": "Both 'Rates' and 'Meals' must be lists."}, 400

#         # -----------------------
#         # 1️⃣ Meals (processed FIRST, so Rates can resolve meal_price_id from them)
#         # -----------------------
#         normalized_meals = []
#         for m in meals_data:
#             normalized_meals.append({
#                 "mp": m.get("Mp"),
#                 "outlet": m.get("Outlet"),
#                 "rate": m.get("Rate"),
#                 "currency": m.get("Currency"),
#                 "outlet_rate_id": m.get("OutletRateId")
#             })

#         # Existing (outlet_rate_id, outlet) -> real id
#         cursor.execute("SELECT id, outlet_rate_id, outlet FROM hotel_tblmeal_price WHERE outlet_rate_id IS NOT NULL")
#         meal_lookup = {(row['outlet_rate_id'], row['outlet']): row['id'] for row in cursor.fetchall()}

#         skipped_meal_ids = []
#         created_meals = []

#         for m in normalized_meals:
#             outlet_rate_id = m.get("outlet_rate_id")
#             outlet = m.get("outlet")
#             pair = (outlet_rate_id, outlet)

#             if outlet_rate_id and pair in meal_lookup:
#                 skipped_meal_ids.append(outlet_rate_id)
#             else:
#                 insert_sql = """
#                     INSERT INTO hotel_tblmeal_price (mp, outlet, rate, currency, outlet_rate_id)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """
#                 cursor.execute(insert_sql, (
#                     m['mp'], m['outlet'], m['rate'], m['currency'], m.get('outlet_rate_id')
#                 ))
#                 new_meal_id = cursor.lastrowid
#                 created_meals.append(new_meal_id)
#                 meal_lookup[pair] = new_meal_id  # so Rates below can resolve it

#         # -----------------------
#         # 2️⃣ Rates (resolves meal_price_id via (MealPriceID, Outlet) -> meal_lookup)
#         # -----------------------
#         normalized_rates = []
#         for r in rates_data:
#             normalized_rates.append({
#                 "room_name": r.get("RoomName"),
#                 "room_type": r.get("RoomType"),
#                 "outlet": r.get("Outlet"),
#                 "rate": r.get("RateAmount"),
#                 "currency": r.get("Currency"),
#                 "meal_outlet_rate_id": r.get("MealPriceID"),  # actually the meal plan's outlet_rate_id, not the real id
#                 "outlet_rate_id": r.get("OutletRateId")
#             })

#         # Existing (outlet_rate_id, outlet) pairs for hotel_tblrates
#         cursor.execute("SELECT outlet_rate_id, outlet FROM hotel_tblrates WHERE outlet_rate_id IS NOT NULL")
#         existing_rate_pairs = set((row['outlet_rate_id'], row['outlet']) for row in cursor.fetchall())

#         skipped_rate_ids = []
#         created_rates = []
#         rate_meal_resolution_errors = []

#         for r in normalized_rates:
#             outlet_rate_id = r.get("outlet_rate_id")
#             outlet = r.get("outlet")
#             pair = (outlet_rate_id, outlet)

#             if outlet_rate_id and pair in existing_rate_pairs:
#                 skipped_rate_ids.append(outlet_rate_id)
#                 continue

#             # -------- RESOLVE meal_price_id from (meal_outlet_rate_id, outlet) --------
#             meal_price_id = None
#             meal_outlet_rate_id = r.get("meal_outlet_rate_id")
#             if meal_outlet_rate_id:
#                 meal_key = (meal_outlet_rate_id, outlet)
#                 meal_price_id = meal_lookup.get(meal_key)
#                 if meal_price_id is None:
#                     # MealPriceID was sent but no matching meal (existing or just-created) was found for this outlet
#                     rate_meal_resolution_errors.append({
#                         "outlet_rate_id": outlet_rate_id,
#                         "outlet": outlet,
#                         "requested_meal_outlet_rate_id": meal_outlet_rate_id,
#                         "error": "No matching meal plan found for this outlet_rate_id + outlet combination"
#                     })
#                     continue  # skip inserting this rate; nothing to safely link it to

#             # Insert new rate
#             insert_sql = """
#                 INSERT INTO hotel_tblrates (room_name, room_type, outlet, rate, currency, meal_price_id, outlet_rate_id, is_active)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
#             """
#             cursor.execute(insert_sql, (
#                 r['room_name'], r['room_type'], r['outlet'], r['rate'], r['currency'],
#                 meal_price_id, r.get('outlet_rate_id')
#             ))
#             created_rates.append(cursor.lastrowid)
#             existing_rate_pairs.add(pair)

#         # -----------------------
#         # 3️⃣ Exchange Rates
#         # -----------------------
#         exchange_data = json_data.get("ExchangeRates", [])

#         if not isinstance(exchange_data, list):
#             return {"error": "'ExchangeRates' must be a list."}, 400

#         normalized_exchange = []
#         for e in exchange_data:
#             normalized_exchange.append({
#                 "currency": e.get("Currency"),
#                 "outlet": e.get("Outlet"),
#                 "amount": e.get("Amount"),
#                 "buying_rate": e.get("BuyingRate"),
#                 "sign": e.get("Sign")
#             })

#         # Existing (Currency, outlet) pairs
#         cursor.execute("SELECT Currency, outlet FROM hotel_tblexchangerate WHERE Currency IS NOT NULL")
#         existing_currency_pairs = set((row['Currency'], row['outlet']) for row in cursor.fetchall())

#         skipped_exchange = []
#         created_exchange = []

#         for e in normalized_exchange:
#             currency = e.get("currency")
#             outlet = e.get("outlet")
#             pair = (currency, outlet)

#             if currency and pair in existing_currency_pairs:
#                 skipped_exchange.append(currency)
#             else:
#                 insert_sql = """
#                     INSERT INTO hotel_tblexchangerate 
#                     (Currency, outlet, Amount, buying_rate, Sign, created_at, is_active)
#                     VALUES (%s, %s, %s, %s, %s, NOW(), 1)
#                 """
#                 cursor.execute(insert_sql, (
#                     e['currency'],
#                     e['outlet'],
#                     e['amount'],
#                     e['buying_rate'],
#                     e['sign']
#                 ))
#                 created_exchange.append(cursor.lastrowid)
#                 existing_currency_pairs.add(pair)

#         mydb.commit()
#         mydb.close()

#         return {
#             "meals": {
#                 "created_count": len(created_meals),
#                 "skipped_count": len(skipped_meal_ids),
#                 "skipped_ids": skipped_meal_ids,
#                 "created_ids": created_meals
#             },
#             "rates": {
#                 "created_count": len(created_rates),
#                 "skipped_count": len(skipped_rate_ids),
#                 "skipped_ids": skipped_rate_ids,
#                 "created_ids": created_rates,
#                 "meal_resolution_errors": rate_meal_resolution_errors
#             },
#             "exchange_rates": {
#                 "created_count": len(created_exchange),
#                 "skipped_count": len(skipped_exchange),
#                 "skipped_currencies": skipped_exchange,
#                 "created_ids": created_exchange
#             }
#         }, 201

#     except Exception as e:
#         return {"error": str(e)}, 400


from datetime import datetime
import os
import mysql.connector
from flask import request, jsonify
from flask_cors import cross_origin


@app_file401.route("/create-rates-mealplans", methods=["POST"])
@cross_origin()
def create_rates_mealplans():
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

        # -------- PAYLOAD VALIDATION --------
        json_data = request.get_json() or {}
        rates_data = json_data.get("Rates", [])
        meals_data = json_data.get("Meals", [])
        exchange_data = json_data.get("ExchangeRates", [])

        if not isinstance(rates_data, list) or not isinstance(meals_data, list):
            return {"error": "Both 'Rates' and 'Meals' must be lists."}, 400
        if not isinstance(exchange_data, list):
            return {"error": "'ExchangeRates' must be a list."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -----------------------
        # 1️⃣ Meals (processed FIRST, so Rates can resolve meal_price_id from them)
        # -----------------------
        normalized_meals = []
        for m in meals_data:
            normalized_meals.append({
                "mp": m.get("Mp"),
                "outlet": m.get("Outlet"),
                "rate": m.get("Rate"),
                "currency": m.get("Currency"),
                "outlet_rate_id": m.get("OutletRateId")
            })

        # Existing (outlet_rate_id, outlet) -> real id
        cursor.execute("SELECT id, outlet_rate_id, outlet FROM hotel_tblmeal_price WHERE outlet_rate_id IS NOT NULL")
        meal_lookup = {(row['outlet_rate_id'], row['outlet']): row['id'] for row in cursor.fetchall()}

        updated_meal_ids = []
        created_meals = []

        for m in normalized_meals:
            outlet_rate_id = m.get("outlet_rate_id")
            outlet = m.get("outlet")
            pair = (outlet_rate_id, outlet)

            if outlet_rate_id and pair in meal_lookup:
                # UPDATE existing meal plan
                cursor.execute("""
                    UPDATE hotel_tblmeal_price
                    SET mp=%s, rate=%s, currency=%s
                    WHERE id=%s
                """, (m['mp'], m['rate'], m['currency'], meal_lookup[pair]))
                updated_meal_ids.append(meal_lookup[pair])
            else:
                cursor.execute("""
                    INSERT INTO hotel_tblmeal_price (mp, outlet, rate, currency, outlet_rate_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (m['mp'], m['outlet'], m['rate'], m['currency'], m.get('outlet_rate_id')))
                new_meal_id = cursor.lastrowid
                created_meals.append(new_meal_id)
                if outlet_rate_id:
                    meal_lookup[pair] = new_meal_id  # so Rates below (and later duplicates) can resolve it

        # -----------------------
        # 2️⃣ Rates (resolves meal_price_id via (MealPriceID, Outlet) -> meal_lookup)
        # -----------------------
        normalized_rates = []
        for r in rates_data:
            normalized_rates.append({
                "room_name": r.get("RoomName"),
                "room_type": r.get("RoomType"),
                "outlet": r.get("Outlet"),
                "rate": r.get("RateAmount"),
                "currency": r.get("Currency"),
                "meal_outlet_rate_id": r.get("MealPriceID"),  # the meal plan's outlet_rate_id, not the real id
                "outlet_rate_id": r.get("OutletRateId")
            })

        # Existing (outlet_rate_id, outlet) -> real id for hotel_tblrates
        cursor.execute("SELECT id, outlet_rate_id, outlet FROM hotel_tblrates WHERE outlet_rate_id IS NOT NULL")
        rate_lookup = {(row['outlet_rate_id'], row['outlet']): row['id'] for row in cursor.fetchall()}

        updated_rate_ids = []
        created_rates = []
        rate_meal_resolution_errors = []

        for r in normalized_rates:
            outlet_rate_id = r.get("outlet_rate_id")
            outlet = r.get("outlet")
            pair = (outlet_rate_id, outlet)

            # -------- RESOLVE meal_price_id from (meal_outlet_rate_id, outlet) --------
            meal_price_id = None
            meal_outlet_rate_id = r.get("meal_outlet_rate_id")
            if meal_outlet_rate_id:
                meal_price_id = meal_lookup.get((meal_outlet_rate_id, outlet))
                if meal_price_id is None:
                    rate_meal_resolution_errors.append({
                        "outlet_rate_id": outlet_rate_id,
                        "outlet": outlet,
                        "requested_meal_outlet_rate_id": meal_outlet_rate_id,
                        "error": "No matching meal plan found for this outlet_rate_id + outlet combination"
                    })
                    continue  # don't insert or update this rate

            if outlet_rate_id and pair in rate_lookup:
                # UPDATE existing rate.
                # meal_price_id is only changed when MealPriceID was sent in the payload.
                cursor.execute("""
                    UPDATE hotel_tblrates
                    SET room_name=%s, room_type=%s, rate=%s, currency=%s,
                        meal_price_id=COALESCE(%s, meal_price_id)
                    WHERE id=%s
                """, (r['room_name'], r['room_type'], r['rate'], r['currency'],
                      meal_price_id, rate_lookup[pair]))
                updated_rate_ids.append(rate_lookup[pair])
            else:
                cursor.execute("""
                    INSERT INTO hotel_tblrates
                        (room_name, room_type, outlet, rate, currency, meal_price_id, outlet_rate_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """, (r['room_name'], r['room_type'], r['outlet'], r['rate'], r['currency'],
                      meal_price_id, r.get('outlet_rate_id')))
                new_rate_id = cursor.lastrowid
                created_rates.append(new_rate_id)
                if outlet_rate_id:
                    rate_lookup[pair] = new_rate_id

        # -----------------------
        # 3️⃣ Exchange Rates
        # -----------------------
        normalized_exchange = []
        for e in exchange_data:
            normalized_exchange.append({
                "currency": e.get("Currency"),
                "outlet": e.get("Outlet"),
                "amount": e.get("Amount"),
                "buying_rate": e.get("BuyingRate"),
                "sign": e.get("Sign")
            })

        cursor.execute("SELECT Currency, outlet FROM hotel_tblexchangerate WHERE Currency IS NOT NULL")
        existing_currency_pairs = set((row['Currency'], row['outlet']) for row in cursor.fetchall())

        updated_exchange = []
        created_exchange = []

        for e in normalized_exchange:
            currency = e.get("currency")
            outlet = e.get("outlet")
            pair = (currency, outlet)

            if currency and pair in existing_currency_pairs:
                # UPDATE existing exchange rate
                cursor.execute("""
                    UPDATE hotel_tblexchangerate
                    SET Amount=%s, buying_rate=%s, Sign=%s
                    WHERE Currency=%s AND outlet=%s
                """, (e['amount'], e['buying_rate'], e['sign'], currency, outlet))
                updated_exchange.append(currency)
            else:
                cursor.execute("""
                    INSERT INTO hotel_tblexchangerate
                        (Currency, outlet, Amount, buying_rate, Sign, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, NOW(), 1)
                """, (e['currency'], e['outlet'], e['amount'], e['buying_rate'], e['sign']))
                created_exchange.append(cursor.lastrowid)
                if currency:
                    existing_currency_pairs.add(pair)

        mydb.commit()

        return {
            "meals": {
                "created_count": len(created_meals),
                "updated_count": len(updated_meal_ids),
                "created_ids": created_meals,
                "updated_ids": updated_meal_ids
            },
            "rates": {
                "created_count": len(created_rates),
                "updated_count": len(updated_rate_ids),
                "created_ids": created_rates,
                "updated_ids": updated_rate_ids,
                "meal_resolution_errors": rate_meal_resolution_errors
            },
            "exchange_rates": {
                "created_count": len(created_exchange),
                "updated_count": len(updated_exchange),
                "created_ids": created_exchange,
                "updated_currencies": updated_exchange
            }
        }, 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 400

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()