# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# load_dotenv()

# app_file400 = Blueprint('app_file400', __name__)
# from root.auth.check import token_auth

# @app_file400.route("/all-rates", methods=["POST"])
# @cross_origin()
# def all_rates():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'), 
#             user=os.getenv('user'), 
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json()

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

#         # Required fields from client
#         room_name = json_data.get("room_name")
#         room_type = json_data.get("room_type")
#         rate = json_data.get("rate")
#         currency = json_data.get("currency")
#         meal_price_id = json_data.get("meal_price_id")  # optional
#         outlet_rate_id = json_data.get("outlet_rate_id")  # optional
#         occupancy = json_data.get("occupancy")  # optional

#         if not room_name or not room_type or rate is None or not currency:
#             return {"error": "Missing required fields."}, 400


#         # Otherwise insert new record
#         insert_sql = """
#             INSERT INTO hotel_tblrates (room_name, room_type, rate, currency, meal_price_id, occupancy)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         """
#         cursor.execute(insert_sql, (
#             room_name,
#             room_type,
#             rate,
#             currency,
#             meal_price_id,
#             occupancy
#         ))
#         mydb.commit()

#         new_id = cursor.lastrowid
#         cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (new_id,))
#         new_record = cursor.fetchone()
#         mydb.close()
#         return new_record, 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file400.route("/all-rates", methods=["GET"])
# @cross_origin()
# def get_all_rates():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Token validation
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Fetch all rates where is_deleted = 0
#         cursor.execute("""
#             SELECT id, room_name, room_type, rate, currency, meal_price_id, outlet_rate_id, occupancy
#             FROM hotel_tblrates
#             ORDER BY id ASC
#         """)
#         results = cursor.fetchall()

#         if not results:
#             return {"error": "No rates found."}, 404

#         mydb.close()
#         return {"rates": results}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file400.route("/rates/delete/<int:rate_id>", methods=["DELETE"])
# @cross_origin()
# def delete_rate(rate_id):
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Check if rate exists
#         cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (rate_id,))
#         rate = cursor.fetchone()
#         if not rate:
#             return {"error": "Rate not found."}, 404

#         # Soft delete by setting is_deleted = 1
#         cursor.execute("DELETE from hotel_tblrates WHERE id=%s", (rate_id,))
#         mydb.commit()
#         mydb.close()

#         return {"message": "Rate deleted successfully"}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file400.route("/rates/update/<int:rate_id>", methods=["POST"])
# @cross_origin()
# def update_rate(rate_id):
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
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Check if rate exists
#         cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (rate_id,))
#         rate = cursor.fetchone()
#         if not rate:
#             return {"error": "Rate not found."}, 404

#         # Extract fields to update (keep existing if not provided)
#         room_name = json_data.get("room_name", rate["room_name"])
#         room_type = json_data.get("room_type", rate["room_type"])
#         rate_value = json_data.get("rate", rate["rate"])
#         currency = json_data.get("currency", rate["currency"])
#         meal_price_id = json_data.get("meal_price_id", rate["meal_price_id"])
#         outlet_rate_id = json_data.get("outlet_rate_id", rate["outlet_rate_id"])
#         is_active = json_data.get("is_active", rate["is_active"])

#         # Update record
#         update_sql = """
#             UPDATE hotel_tblrates
#             SET room_name=%s, room_type=%s, rate=%s, currency=%s, meal_price_id=%s, outlet_rate_id=%s, is_active=%s
#             WHERE id=%s
#         """
#         cursor.execute(update_sql, (
#             room_name, room_type, rate_value, currency, meal_price_id, outlet_rate_id, is_active, rate_id
#         ))
#         mydb.commit()
#         mydb.close()

#         return {"message": "Rate updated successfully"}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file400.route("/meal-price/delete/<int:meal_id>", methods=["GET"])
# @cross_origin()
# def delete_meal_price(meal_id):
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Token validation
#         # json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Check if meal exists
#         cursor.execute("SELECT * FROM hotel_tblmeal_price WHERE id=%s", (meal_id,))
#         meal = cursor.fetchone()
#         if not meal:
#             return {"error": "Meal price not found."}, 404

#         # Soft delete
#         cursor.execute("DELETE FROM hotel_tblmeal_price WHERE id=%s", (meal_id,))
#         mydb.commit()
#         mydb.close()

#         return {"message": "Meal price deleted successfully"}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400


# @app_file400.route("/meal-price", methods=["GET"])
# @cross_origin()
# def get_all_meal_prices():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # ✅ Get token from JSON payload
#         # json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token:
#             return jsonify({"error": "No token provided."}), 400
#         if not token_auth(token):
#             return jsonify({"error": "Invalid token."}), 400

#         # Fetch all meal prices
#         cursor.execute("""
#             SELECT id, mp, rate, currency, outlet_rate_id, is_active
#             FROM hotel_tblmeal_price
#         """)
#         meals = cursor.fetchall()
#         mydb.close()

#         return jsonify({"meals": meals}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    
# @app_file400.route("/meal-price", methods=["POST"])
# @cross_origin()
# def insert_meal_price():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
            
#         if not token:
#             return jsonify({"error": "No token provided."}), 400
            
#         if not token_auth(token):
#             return jsonify({"error": "Invalid token."}), 400

#         # Get JSON data from request
#         json_data = request.get_json()
        
#         if not json_data:
#             return jsonify({"error": "No data provided"}), 400

#         # Extract and validate required fields
#         mp = json_data.get('mp')
#         rate = json_data.get('rate')
#         currency = json_data.get('currency')
#         outlet_rate_id = json_data.get('outlet_rate_id')  # Optional field
        
#         # Validate required fields
#         if not mp:
#             return jsonify({"error": "Meal plan (mp) is required"}), 400
            
#         if rate is None:
#             return jsonify({"error": "Rate is required"}), 400
            
#         if not currency:
#             return jsonify({"error": "Currency is required"}), 400

#         # Convert rate to float/decimal
#         try:
#             rate = float(rate)
#         except ValueError:
#             return jsonify({"error": "Rate must be a valid number"}), 400

#         # Insert into database
#         insert_query = """
#             INSERT INTO hotel_tblmeal_price 
#             (mp, rate, currency, outlet_rate_id, created_at, updated_at, is_active) 
#             VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)
#         """
        
#         # Set is_active default to True (1) if not provided
#         is_active = json_data.get('is_active', True)
        
#         cursor.execute(insert_query, (
#             mp, 
#             rate, 
#             currency, 
#             outlet_rate_id, 
#             is_active
#         ))
        
#         mydb.commit()
        
#         # Get the inserted ID
#         inserted_id = cursor.lastrowid
        
#         # Fetch the newly inserted record to return it
#         cursor.execute("""
#             SELECT id, mp, rate, currency, outlet_rate_id, is_active, 
#                    created_at, updated_at
#             FROM hotel_tblmeal_price 
#             WHERE id = %s
#         """, (inserted_id,))
        
#         new_meal_price = cursor.fetchone()
        
#         mydb.close()

#         return jsonify({
#             "message": "Meal price inserted successfully",
#             "meal_price": new_meal_price
#         }), 201

#     except mysql.connector.Error as db_error:
#         return jsonify({"error": f"Database error: {str(db_error)}"}), 400
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    

# @app_file400.route("/meal-price/update/<int:meal_id>", methods=["POST"])
# @cross_origin()
# def update_meal_price(meal_id):
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
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Check if meal exists
#         cursor.execute("SELECT * FROM hotel_tblmeal_price WHERE id=%s", (meal_id,))
#         meal = cursor.fetchone()
#         if not meal:
#             return {"error": "Meal price not found."}, 404

#         # Extract fields to update
#         mp = json_data.get("mp", meal["mp"])
#         rate = json_data.get("rate", meal["rate"])
#         currency = json_data.get("currency", meal["currency"])
#         outlet_rate_id = json_data.get("outlet_rate_id", meal["outlet_rate_id"])
#         is_active = json_data.get("is_active", meal["is_active"])

#         # Update meal record
#         update_sql = """
#             UPDATE hotel_tblmeal_price
#             SET mp=%s, rate=%s, currency=%s, outlet_rate_id=%s, is_active=%s
#             WHERE id=%s
#         """
#         cursor.execute(update_sql, (mp, rate, currency, outlet_rate_id, is_active, meal_id))
#         mydb.commit()
#         mydb.close()

#         return {"message": "Meal price updated successfully"}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

app_file400 = Blueprint('app_file400', __name__)
from root.auth.check import token_auth

# @app_file400.route("/all-rates", methods=["POST"])
# @cross_origin()
# def all_rates():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'), 
#             user=os.getenv('user'), 
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json()

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

#         # Required fields from client
#         room_name = json_data.get("room_name")
#         room_type = json_data.get("room_type")
#         rate = json_data.get("rate")
#         currency = json_data.get("currency")
#         meal_price_id = json_data.get("meal_price_id")  # optional
#         outlet_rate_id = json_data.get("outlet_rate_id")  # optional
#         occupancy = json_data.get("occupancy")  # optional

#         if not room_name or not room_type or rate is None or not currency:
#             return {"error": "Missing required fields."}, 400


#         # Otherwise insert new record
#         insert_sql = """
#             INSERT INTO hotel_tblrates (room_name, room_type, rate, currency, meal_price_id, occupancy)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         """
#         cursor.execute(insert_sql, (
#             room_name,
#             room_type,
#             rate,
#             currency,
#             meal_price_id,
#             occupancy
#         ))
#         mydb.commit()

#         new_id = cursor.lastrowid
#         cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (new_id,))
#         new_record = cursor.fetchone()
#         mydb.close()
#         return new_record, 200

#     except Exception as e:
#         return {"error": str(e)}, 400


@app_file400.route("/all-rates", methods=["POST"])
@cross_origin()
def all_rates():
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv('host'), 
            user=os.getenv('user'), 
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        json_data = request.get_json()

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

        # Required fields from client
        room_name = json_data.get("room_name")
        room_type = json_data.get("room_type")
        outlet = json_data.get("outlet")
        rate = json_data.get("rate")
        currency = json_data.get("currency")
        meal_price_id = json_data.get("meal_price_id")  # optional
        outlet_rate_id = json_data.get("outlet_rate_id")  # optional
        occupancy = json_data.get("occupancy")  # optional

        if not room_name or not room_type or not outlet or rate is None or not currency:
            return {"error": "Missing required fields."}, 400


        # Otherwise insert new record
        insert_sql = """
            INSERT INTO hotel_tblrates (room_name, room_type, outlet, rate, currency, meal_price_id, occupancy)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            room_name,
            room_type,
            outlet,
            rate,
            currency,
            meal_price_id,
            occupancy
        ))
        mydb.commit()

        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (new_id,))
        new_record = cursor.fetchone()
        mydb.close()
        return new_record, 200

    except Exception as e:
        return {"error": str(e)}, 400
    

# @app_file400.route("/all-rates", methods=["GET"])
# @cross_origin()
# def get_all_rates():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Token validation
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Fetch all rates where is_deleted = 0
#         cursor.execute("""
#             SELECT id, room_name, room_type, rate, currency, meal_price_id, outlet_rate_id, occupancy
#             FROM hotel_tblrates
#             ORDER BY id ASC
#         """)
#         results = cursor.fetchall()

#         if not results:
#             return {"error": "No rates found."}, 404

#         mydb.close()
#         return {"rates": results}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400

@app_file400.route("/all-rates", methods=["GET"])
@cross_origin()
def get_all_rates():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Token validation
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- OUTLET FILTER (from query param) --------
        outlet = request.args.get("outlet")

        # Fetch rates, optionally filtered by outlet, with linked meal plan details
        query = """
            SELECT
                r.id, r.room_name, r.room_type, r.outlet, r.rate, r.currency,
                r.meal_price_id, r.outlet_rate_id, r.occupancy,
                mp.id AS meal_price_detail_id,
                mp.mp AS meal_plan_name,
                mp.rate AS meal_plan_rate,
                mp.currency AS meal_plan_currency,
                mp.outlet_rate_id AS meal_plan_outlet_rate_id
            FROM hotel_tblrates r
            LEFT JOIN hotel_tblmeal_price mp ON r.meal_price_id = mp.id
        """
        params = []

        if outlet:
            query += " WHERE r.outlet = %s"
            params.append(outlet)

        query += " ORDER BY r.id ASC"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        if not results:
            return {"error": "No rates found."}, 404

        # -------- NEST MEAL PLAN DETAILS UNDER EACH RATE --------
        rates = []
        for row in results:
            meal_price = None
            if row["meal_price_detail_id"] is not None:
                meal_price = {
                    "id": row["meal_price_detail_id"],
                    "mp": row["meal_plan_name"],
                    "rate": row["meal_plan_rate"],
                    "currency": row["meal_plan_currency"],
                    "outlet_rate_id": row["meal_plan_outlet_rate_id"]
                }

            rates.append({
                "id": row["id"],
                "room_name": row["room_name"],
                "room_type": row["room_type"],
                "outlet": row["outlet"],
                "rate": row["rate"],
                "currency": row["currency"],
                "meal_price_id": row["meal_price_id"],
                "outlet_rate_id": row["outlet_rate_id"],
                "occupancy": row["occupancy"],
                "meal_price": meal_price
            })

        mydb.close()
        return {"rates": rates}, 200

    except Exception as e:
        return {"error": str(e)}, 400
    

@app_file400.route("/rates/delete/<int:rate_id>", methods=["DELETE"])
@cross_origin()
def delete_rate(rate_id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # json_data = request.get_json() or {}
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Check if rate exists
        cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (rate_id,))
        rate = cursor.fetchone()
        if not rate:
            return {"error": "Rate not found."}, 404

        # Soft delete by setting is_deleted = 1
        cursor.execute("DELETE from hotel_tblrates WHERE id=%s", (rate_id,))
        mydb.commit()
        mydb.close()

        return {"message": "Rate deleted successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 400
    

@app_file400.route("/rates/update/<int:rate_id>", methods=["POST"])
@cross_origin()
def update_rate(rate_id):
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Token validation
        json_data = request.get_json() or {}
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Check if rate exists
        cursor.execute("SELECT * FROM hotel_tblrates WHERE id=%s", (rate_id,))
        rate = cursor.fetchone()
        if not rate:
            return {"error": "Rate not found."}, 404

        # Extract fields to update (keep existing if not provided)
        room_name = json_data.get("room_name", rate["room_name"])
        room_type = json_data.get("room_type", rate["room_type"])
        rate_value = json_data.get("rate", rate["rate"])
        currency = json_data.get("currency", rate["currency"])
        meal_price_id = json_data.get("meal_price_id", rate["meal_price_id"])
        outlet_rate_id = json_data.get("outlet_rate_id", rate["outlet_rate_id"])
        is_active = json_data.get("is_active", rate["is_active"])

        # Update record
        update_sql = """
            UPDATE hotel_tblrates
            SET room_name=%s, room_type=%s, rate=%s, currency=%s, meal_price_id=%s, outlet_rate_id=%s, is_active=%s
            WHERE id=%s
        """
        cursor.execute(update_sql, (
            room_name, room_type, rate_value, currency, meal_price_id, outlet_rate_id, is_active, rate_id
        ))
        mydb.commit()
        mydb.close()

        return {"message": "Rate updated successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 400
    

@app_file400.route("/meal-price/delete/<int:meal_id>", methods=["GET"])
@cross_origin()
def delete_meal_price(meal_id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Token validation
        # json_data = request.get_json() or {}
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Check if meal exists
        cursor.execute("SELECT * FROM hotel_tblmeal_price WHERE id=%s", (meal_id,))
        meal = cursor.fetchone()
        if not meal:
            return {"error": "Meal price not found."}, 404

        # Soft delete
        cursor.execute("DELETE FROM hotel_tblmeal_price WHERE id=%s", (meal_id,))
        mydb.commit()
        mydb.close()

        return {"message": "Meal price deleted successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 400


@app_file400.route("/meal-price", methods=["GET"])
@cross_origin()
def get_all_meal_prices():
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return jsonify({"error": "No token provided."}), 400
        if not token_auth(token):
            return jsonify({"error": "Invalid token."}), 400

        # -------- OUTLET FILTER (from query param) --------
        outlet = request.args.get("outlet")

        query = """
            SELECT id, mp, outlet, rate, currency, outlet_rate_id, is_active
            FROM hotel_tblmeal_price
        """
        params = []

        if outlet:
            query += " WHERE outlet = %s"
            params.append(outlet)

        cursor.execute(query, tuple(params))
        meals = cursor.fetchall()
        mydb.close()

        return jsonify({"meals": meals}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
# @app_file400.route("/meal-price", methods=["POST"])
# @cross_origin()
# def insert_meal_price():
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
            
#         if not token:
#             return jsonify({"error": "No token provided."}), 400
            
#         if not token_auth(token):
#             return jsonify({"error": "Invalid token."}), 400

#         # Get JSON data from request
#         json_data = request.get_json()
        
#         if not json_data:
#             return jsonify({"error": "No data provided"}), 400

#         # Extract and validate required fields
#         mp = json_data.get('mp')
#         rate = json_data.get('rate')
#         currency = json_data.get('currency')
#         outlet_rate_id = json_data.get('outlet_rate_id')  # Optional field
        
#         # Validate required fields
#         if not mp:
#             return jsonify({"error": "Meal plan (mp) is required"}), 400
            
#         if rate is None:
#             return jsonify({"error": "Rate is required"}), 400
            
#         if not currency:
#             return jsonify({"error": "Currency is required"}), 400

#         # Convert rate to float/decimal
#         try:
#             rate = float(rate)
#         except ValueError:
#             return jsonify({"error": "Rate must be a valid number"}), 400

#         # Insert into database
#         insert_query = """
#             INSERT INTO hotel_tblmeal_price 
#             (mp, rate, currency, outlet_rate_id, created_at, updated_at, is_active) 
#             VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)
#         """
        
#         # Set is_active default to True (1) if not provided
#         is_active = json_data.get('is_active', True)
        
#         cursor.execute(insert_query, (
#             mp, 
#             rate, 
#             currency, 
#             outlet_rate_id, 
#             is_active
#         ))
        
#         mydb.commit()
        
#         # Get the inserted ID
#         inserted_id = cursor.lastrowid
        
#         # Fetch the newly inserted record to return it
#         cursor.execute("""
#             SELECT id, mp, rate, currency, outlet_rate_id, is_active, 
#                    created_at, updated_at
#             FROM hotel_tblmeal_price 
#             WHERE id = %s
#         """, (inserted_id,))
        
#         new_meal_price = cursor.fetchone()
        
#         mydb.close()

#         return jsonify({
#             "message": "Meal price inserted successfully",
#             "meal_price": new_meal_price
#         }), 201

#     except mysql.connector.Error as db_error:
#         return jsonify({"error": f"Database error: {str(db_error)}"}), 400
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    

@app_file400.route("/meal-price", methods=["POST"])
@cross_origin()
def insert_meal_price():
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
            
        if not token:
            return jsonify({"error": "No token provided."}), 400
            
        if not token_auth(token):
            return jsonify({"error": "Invalid token."}), 400

        # Get JSON data from request
        json_data = request.get_json()
        
        if not json_data:
            return jsonify({"error": "No data provided"}), 400

        # Extract and validate required fields
        mp = json_data.get('mp')
        outlet = json_data.get('outlet')
        rate = json_data.get('rate')
        currency = json_data.get('currency')
        outlet_rate_id = json_data.get('outlet_rate_id')  # Optional field
        
        # Validate required fields
        if not mp:
            return jsonify({"error": "Meal plan (mp) is required"}), 400

        if not outlet:
            return jsonify({"error": "Outlet is required"}), 400
            
        if rate is None:
            return jsonify({"error": "Rate is required"}), 400
            
        if not currency:
            return jsonify({"error": "Currency is required"}), 400

        # Convert rate to float/decimal
        try:
            rate = float(rate)
        except ValueError:
            return jsonify({"error": "Rate must be a valid number"}), 400

        # Insert into database
        insert_query = """
            INSERT INTO hotel_tblmeal_price 
            (mp, outlet, rate, currency, outlet_rate_id, created_at, updated_at, is_active) 
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), %s)
        """
        
        # Set is_active default to True (1) if not provided
        is_active = json_data.get('is_active', True)
        
        cursor.execute(insert_query, (
            mp, 
            outlet,
            rate, 
            currency, 
            outlet_rate_id, 
            is_active
        ))
        
        mydb.commit()
        
        # Get the inserted ID
        inserted_id = cursor.lastrowid
        
        # Fetch the newly inserted record to return it
        cursor.execute("""
            SELECT id, mp, outlet, rate, currency, outlet_rate_id, is_active, 
                   created_at, updated_at
            FROM hotel_tblmeal_price 
            WHERE id = %s
        """, (inserted_id,))
        
        new_meal_price = cursor.fetchone()
        
        mydb.close()

        return jsonify({
            "message": "Meal price inserted successfully",
            "meal_price": new_meal_price
        }), 201

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Database error: {str(db_error)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app_file400.route("/meal-price/update/<int:meal_id>", methods=["POST"])
@cross_origin()
def update_meal_price(meal_id):
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Token validation
        json_data = request.get_json() or {}
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Check if meal exists
        cursor.execute("SELECT * FROM hotel_tblmeal_price WHERE id=%s", (meal_id,))
        meal = cursor.fetchone()
        if not meal:
            return {"error": "Meal price not found."}, 404

        # Extract fields to update
        mp = json_data.get("mp", meal["mp"])
        rate = json_data.get("rate", meal["rate"])
        currency = json_data.get("currency", meal["currency"])
        outlet_rate_id = json_data.get("outlet_rate_id", meal["outlet_rate_id"])
        is_active = json_data.get("is_active", meal["is_active"])

        # Update meal record
        update_sql = """
            UPDATE hotel_tblmeal_price
            SET mp=%s, rate=%s, currency=%s, outlet_rate_id=%s, is_active=%s
            WHERE id=%s
        """
        cursor.execute(update_sql, (mp, rate, currency, outlet_rate_id, is_active, meal_id))
        mydb.commit()
        mydb.close()

        return {"message": "Meal price updated successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 400