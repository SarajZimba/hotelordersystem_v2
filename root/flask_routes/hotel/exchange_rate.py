# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv

# load_dotenv()
# from root.auth.check import token_auth

# app_file406 = Blueprint('app_file406', __name__)

# @app_file406.route("/create_exchange_rate", methods=["POST"])
# @cross_origin()
# def create_exchange_rate():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

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

#         # Extract exchange rate fields
#         currency = json_data.get("Currency")
#         amount = json_data.get("Amount")
#         buying_rate = json_data.get("buying_rate", 0)
#         sign = json_data.get("Sign")

#         if not currency or amount is None or not sign:
#             return {"error": "Currency, Amount, and Sign are required fields."}, 400

#         # Insert into DB
#         insert_sql = """
#             INSERT INTO hotel_tblexchangerate (Currency, Amount, buying_rate, Sign, is_active)
#             VALUES (%s, %s, %s, %s, 1)
#         """
#         cursor.execute(insert_sql, (currency, amount, buying_rate, sign))
#         mydb.commit()

#         exchange_id = cursor.lastrowid
#         mydb.close()

#         return jsonify({
#             "message": "Exchange rate created successfully",
#             "exchange_id": exchange_id
#         }), 201

#     except Exception as e:
#         return {"error": str(e)}, 400
    

# @app_file406.route("/create_exchange_rate_list", methods=["POST"])
# @cross_origin()
# def create_exchange_rate_list():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

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

#         # Extract the list of exchange rates
#         rates_list = json_data.get("Rates")
#         if not isinstance(rates_list, list) or len(rates_list) == 0:
#             return {"error": "Rates must be a non-empty list."}, 400

#         created_ids = []
#         errors = []

#         for idx, rate in enumerate(rates_list):
#             currency = rate.get("Currency")
#             amount = rate.get("Amount")
#             buying_rate = rate.get("buying_rate", 0)
#             sign = rate.get("Sign")

#             if not currency or amount is None or not sign:
#                 errors.append({
#                     "index": idx,
#                     "error": "Currency, Amount, and Sign are required."
#                 })
#                 continue

#             insert_sql = """
#                 INSERT INTO hotel_tblexchangerate (Currency, Amount, buying_rate, Sign, is_active)
#                 VALUES (%s, %s, %s, %s, 1)
#             """
#             cursor.execute(insert_sql, (currency, amount, buying_rate, sign))
#             created_ids.append(cursor.lastrowid)

#         mydb.commit()
#         mydb.close()

#         return jsonify({
#             "created_count": len(created_ids),
#             "created_ids": created_ids,
#             "errors": errors
#         }), 201

#     except Exception as e:
#         return {"error": str(e)}, 400
    
# @app_file406.route("/exchange-rate/list", methods=["GET"])
# @cross_origin()
# def get_exchange_rate_list():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
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

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         query = """
#             SELECT id, Currency, Amount, buying_rate, Sign, is_active
#             FROM hotel_tblexchangerate
#             ORDER BY id DESC
#         """
#         cursor.execute(query)
#         rates = cursor.fetchall()

#         mydb.close()

#         return jsonify({
#             "count": len(rates),
#             "rates": rates
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    
# @app_file406.route("/exchange-rate/update/<int:id>", methods=["PATCH"])
# @cross_origin()
# def update_exchange_rate(id):
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

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

#         rate_id = id
#         currency = json_data.get("Currency")
#         amount = json_data.get("Amount")
#         buying_rate = json_data.get("buying_rate")
#         sign = json_data.get("Sign")

#         if not rate_id:
#             return {"error": "Exchange rate id is required."}, 400

#         # Check if record exists
#         cursor.execute(
#             "SELECT id FROM hotel_tblexchangerate WHERE id = %s",
#             (rate_id,)
#         )
#         existing = cursor.fetchone()

#         if not existing:
#             return {"error": "Exchange rate not found."}, 404

#         update_sql = """
#             UPDATE hotel_tblexchangerate
#             SET Currency = %s,
#                 Amount = %s,
#                 buying_rate = %s,
#                 Sign = %s
#             WHERE id = %s
#         """

#         cursor.execute(
#             update_sql,
#             (currency, amount, buying_rate, sign, rate_id)
#         )

#         mydb.commit()
#         mydb.close()

#         return jsonify({
#             "message": "Exchange rate updated successfully",
#             "id": rate_id
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    
# @app_file406.route("/exchange_rate", methods=["POST"])
# @cross_origin()
# def get_exchange_rate_by_currency():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         json_data = request.get_json() or {}
#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         currency = json_data.get("Currency")

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         if not currency:
#             return {"error": "Currency is required."}, 400

#         query = """
#             SELECT id, Currency, Amount, buying_rate, Sign, is_active
#             FROM hotel_tblexchangerate
#             WHERE Currency = %s AND is_active = 1
#         """

#         cursor.execute(query, (currency,))
#         rate = cursor.fetchone()

#         mydb.close()

#         if not rate:
                 
#             data = {"exchange_rate": {}
#                     }
#             return data, 200

#         return jsonify({
#             "exchange_rate": rate
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 400
    
# @app_file406.route("/update-exchange-rate", methods=["POST"])
# @cross_origin()
# def update_exchange_rate_currency():
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
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Extract fields
#         currency = json_data.get("Currency")
#         amount = json_data.get("Amount")
#         buying_rate = json_data.get("BuyingRate")
#         sign = json_data.get("Sign")

#         if not currency:
#             return {"error": "Currency is required."}, 400

#         # Check if currency exists
#         cursor.execute("SELECT id FROM hotel_tblexchangerate WHERE Currency = %s AND is_active = 1", (currency,))
#         existing = cursor.fetchone()
#         if not existing:
#             return {"error": f"Currency '{currency}' not found."}, 404

#         # Build dynamic update query
#         fields = []
#         values = []

#         if amount is not None:
#             fields.append("Amount = %s")
#             values.append(amount)
#         if buying_rate is not None:
#             fields.append("buying_rate = %s")
#             values.append(buying_rate)
#         if sign is not None:
#             fields.append("Sign = %s")
#             values.append(sign)

#         if not fields:
#             return {"error": "No fields to update provided."}, 400

#         values.append(currency)  # for WHERE clause

#         update_sql = f"UPDATE hotel_tblexchangerate SET {', '.join(fields)}, updated_at = NOW() WHERE Currency = %s AND is_active = 1"
#         cursor.execute(update_sql, tuple(values))
#         mydb.commit()
#         mydb.close()

#         return {"message": f"Currency '{currency}' updated successfully."}, 200

#     except Exception as e:
#         return {"error": str(e)}, 400


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
from root.auth.check import token_auth

app_file406 = Blueprint('app_file406', __name__)

@app_file406.route("/create_exchange_rate", methods=["POST"])
@cross_origin()
def create_exchange_rate():
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
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Extract exchange rate fields
        currency = json_data.get("Currency")
        amount = json_data.get("Amount")
        buying_rate = json_data.get("buying_rate", 0)
        sign = json_data.get("Sign")

        if not currency or amount is None or not sign:
            return {"error": "Currency, Amount, and Sign are required fields."}, 400

        # Insert into DB
        insert_sql = """
            INSERT INTO hotel_tblexchangerate (Currency, Amount, buying_rate, Sign, is_active)
            VALUES (%s, %s, %s, %s, 1)
        """
        cursor.execute(insert_sql, (currency, amount, buying_rate, sign))
        mydb.commit()

        exchange_id = cursor.lastrowid
        mydb.close()

        return jsonify({
            "message": "Exchange rate created successfully",
            "exchange_id": exchange_id
        }), 201

    except Exception as e:
        return {"error": str(e)}, 400
    

@app_file406.route("/create_exchange_rate_list", methods=["POST"])
@cross_origin()
def create_exchange_rate_list():
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
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Extract the list of exchange rates
        rates_list = json_data.get("Rates")
        if not isinstance(rates_list, list) or len(rates_list) == 0:
            return {"error": "Rates must be a non-empty list."}, 400

        created_ids = []
        errors = []

        for idx, rate in enumerate(rates_list):
            currency = rate.get("Currency")
            amount = rate.get("Amount")
            buying_rate = rate.get("buying_rate", 0)
            sign = rate.get("Sign")

            if not currency or amount is None or not sign:
                errors.append({
                    "index": idx,
                    "error": "Currency, Amount, and Sign are required."
                })
                continue

            insert_sql = """
                INSERT INTO hotel_tblexchangerate (Currency, Amount, buying_rate, Sign, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """
            cursor.execute(insert_sql, (currency, amount, buying_rate, sign))
            created_ids.append(cursor.lastrowid)

        mydb.commit()
        mydb.close()

        return jsonify({
            "created_count": len(created_ids),
            "created_ids": created_ids,
            "errors": errors
        }), 201

    except Exception as e:
        return {"error": str(e)}, 400
    
@app_file406.route("/exchange-rate/list", methods=["GET"])
@cross_origin()
def get_exchange_rate_list():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
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

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        query = """
            SELECT id, Currency, Amount, buying_rate, Sign, is_active
            FROM hotel_tblexchangerate
            ORDER BY id DESC
        """
        cursor.execute(query)
        rates = cursor.fetchall()

        mydb.close()

        return jsonify({
            "count": len(rates),
            "rates": rates
        }), 200

    except Exception as e:
        return {"error": str(e)}, 400
    
@app_file406.route("/exchange-rate/update/<int:id>", methods=["PATCH"])
@cross_origin()
def update_exchange_rate(id):
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
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400


        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        rate_id = id
        currency = json_data.get("Currency")
        amount = json_data.get("Amount")
        buying_rate = json_data.get("buying_rate")
        sign = json_data.get("Sign")

        if not rate_id:
            return {"error": "Exchange rate id is required."}, 400

        # Check if record exists
        cursor.execute(
            "SELECT id FROM hotel_tblexchangerate WHERE id = %s",
            (rate_id,)
        )
        existing = cursor.fetchone()

        if not existing:
            return {"error": "Exchange rate not found."}, 404

        update_sql = """
            UPDATE hotel_tblexchangerate
            SET Currency = %s,
                Amount = %s,
                buying_rate = %s,
                Sign = %s
            WHERE id = %s
        """

        cursor.execute(
            update_sql,
            (currency, amount, buying_rate, sign, rate_id)
        )

        mydb.commit()
        mydb.close()

        return jsonify({
            "message": "Exchange rate updated successfully",
            "id": rate_id
        }), 200

    except Exception as e:
        return {"error": str(e)}, 400
    
@app_file406.route("/exchange_rate", methods=["POST"])
@cross_origin()
def get_exchange_rate_by_currency():
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
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400
        currency = json_data.get("Currency")

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        if not currency:
            return {"error": "Currency is required."}, 400

        query = """
            SELECT id, Currency, Amount, buying_rate, Sign, is_active
            FROM hotel_tblexchangerate
            WHERE Currency = %s AND is_active = 1
        """

        cursor.execute(query, (currency,))
        rate = cursor.fetchone()

        mydb.close()

        if not rate:
                 
            data = {"exchange_rate": {}
                    }
            return data, 200

        return jsonify({
            "exchange_rate": rate
        }), 200

    except Exception as e:
        return {"error": str(e)}, 400
    
@app_file406.route("/update-exchange-rate", methods=["POST"])
@cross_origin()
def update_exchange_rate_currency():
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
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Extract fields
        currency = json_data.get("Currency")
        amount = json_data.get("Amount")
        buying_rate = json_data.get("BuyingRate")
        sign = json_data.get("Sign")

        if not currency:
            return {"error": "Currency is required."}, 400

        # Check if currency exists
        cursor.execute("SELECT id FROM hotel_tblexchangerate WHERE Currency = %s AND is_active = 1", (currency,))
        existing = cursor.fetchone()
        if not existing:
            return {"error": f"Currency '{currency}' not found."}, 404

        # Build dynamic update query
        fields = []
        values = []

        if amount is not None:
            fields.append("Amount = %s")
            values.append(amount)
        if buying_rate is not None:
            fields.append("buying_rate = %s")
            values.append(buying_rate)
        if sign is not None:
            fields.append("Sign = %s")
            values.append(sign)

        if not fields:
            return {"error": "No fields to update provided."}, 400

        values.append(currency)  # for WHERE clause

        update_sql = f"UPDATE hotel_tblexchangerate SET {', '.join(fields)}, updated_at = NOW() WHERE Currency = %s AND is_active = 1"
        cursor.execute(update_sql, tuple(values))
        mydb.commit()
        mydb.close()

        return {"message": f"Currency '{currency}' updated successfully."}, 200

    except Exception as e:
        return {"error": str(e)}, 400

@app_file406.route("/exchange_rate/<int:id>", methods=["DELETE"])
@cross_origin()
def delete_exchange_rate(id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
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
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- DELETE --------
        cursor.execute("DELETE FROM hotel_tblexchangerate WHERE id = %s", (id,))
        mydb.commit()

        if cursor.rowcount == 0:
            mydb.close()
            return {"error": "Exchange rate not found"}, 404

        mydb.close()

        return jsonify({
            "message": "Exchange rate deleted successfully",
            "exchange_id": id
        }), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 400