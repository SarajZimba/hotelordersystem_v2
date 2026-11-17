# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv

# load_dotenv()
# from root.auth.check import token_auth

# app_file480 = Blueprint('app_file480', __name__)


# @app_file480.route("/properties", methods=["POST"])
# @cross_origin()
# def create_property():
#     # -------- TOKEN --------
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return {"error": "No token provided."}, 400
#     try:
#         token = auth_header.split(" ")[1]
#     except IndexError:
#         return {"error": "Invalid Authorization header format."}, 400
#     if not token_auth(token):
#         return {"error": "Invalid token."}, 400

#     # -------- INPUT --------
#     data = request.get_json() or {}

#     def clean(key):
#         """Trim strings; turn empty values into NULL."""
#         value = data.get(key)
#         if isinstance(value, str):
#             value = value.strip()
#         return value or None

#     name = clean("name")
#     address = clean("address")
#     contact_no = clean("contact_no")
#     website = clean("website")
#     pan_no = clean("pan_no")
#     fiscal_year = clean("fiscal_year")

#     if not name:
#         return {"error": "Property name is required"}, 400

#     # bill_no_count: optional, defaults to 0 (kept out of clean() so 0 stays 0)
#     raw_count = data.get("bill_no_count")
#     if raw_count is None or raw_count == "":
#         bill_no_count = 0
#     else:
#         try:
#             bill_no_count = int(raw_count)
#         except (TypeError, ValueError):
#             return {"error": "bill_no_count must be an integer."}, 400
#         if bill_no_count < 0:
#             return {"error": "bill_no_count cannot be negative."}, 400

#     mydb = None
#     cursor = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database"),
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Name must be unique (same rule as the update endpoint)
#         cursor.execute(
#             "SELECT id FROM hotel_company_property WHERE name = %s",
#             (name,),
#         )
#         if cursor.fetchone():
#             return {"error": "A property with this name already exists."}, 400

#         cursor.execute(
#             """
#             INSERT INTO hotel_company_property
#                 (name, address, contact_no, website, pan_no,
#                  bill_no_count, fiscal_year)
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#             """,
#             (name, address, contact_no, website, pan_no,
#              bill_no_count, fiscal_year),
#         )
#         mydb.commit()
#         property_id = cursor.lastrowid

#         return jsonify({
#             "message": "Property created successfully",
#             "property_id": property_id,
#         }), 201

#     except Exception as e:
#         if mydb:
#             try:
#                 mydb.rollback()
#             except Exception:
#                 pass
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             try:
#                 cursor.close()
#             except Exception:
#                 pass
#         if mydb:
#             try:
#                 mydb.close()
#             except Exception:
#                 pass

# from root.auth.property_access import get_employee_properties

# @app_file480.route("/properties", methods=["GET"])
# @cross_origin()
# def get_properties():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

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

#         # -------- EMPLOYEE FILTER (from query param) --------
#         employee_id = request.args.get("employee_id")

#         if employee_id:
#             properties = get_employee_properties(employee_id)
#         else:
#             return {"error": "No Employee id provided"}, 400

#             # cursor.execute("""
#             #     SELECT * FROM hotel_company_property
#             #     ORDER BY id DESC
#             # """)
#             # properties = cursor.fetchall()

#         mydb.close()

#         return jsonify({
#             "total_properties": len(properties),
#             "properties": properties
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500

# from root.auth.property_access import get_employee_properties

# @app_file480.route("/properties/<int:id>", methods=["GET"])
# @cross_origin()
# def get_property(id):
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # TOKEN
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token"}, 400

#         # -------- EMPLOYEE ACCESS CHECK --------
#         employee_id = request.args.get("employee_id")
#         if not employee_id:
#             return {"error": "No Employee id provided"}, 400

#         allowed_properties = get_employee_properties(employee_id)
#         allowed_ids = {p["id"] for p in allowed_properties}

#         if id not in allowed_ids:
#             return {"error": "You do not have access to this property"}, 403

#         cursor.execute("""
#             SELECT * FROM hotel_company_property WHERE id = %s
#         """, (id,))
#         property = cursor.fetchone()

#         mydb.close()

#         if not property:
#             return {"error": "Property not found"}, 404

#         return jsonify(property), 200

#     except Exception as e:
#         return {"error": str(e)}, 500



# from root.auth.property_access import get_employee_properties

# @app_file480.route("/properties/<int:id>", methods=["PUT", "PATCH"])
# @cross_origin()
# def update_property(id):
#     mydb = None
#     cursor = None
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
#             return {"error": "Invalid token"}, 400

#         data = request.get_json() or {}

#         # -------- EMPLOYEE ACCESS CHECK --------
#         employee_id = data.get("employee_id")
#         if not employee_id:
#             return {"error": "No Employee id provided"}, 400

#         allowed_properties = get_employee_properties(employee_id)
#         allowed_ids = {p["id"] for p in allowed_properties}

#         if id not in allowed_ids:
#             return {"error": "You do not have access to this property"}, 403

#         # -------- FIELDS (only what was sent gets updated) --------
#         allowed_fields = [
#             "name", "address", "contact_no", "website", "pan_no",
#             "bill_no_count", "fiscal_year",
#         ]
#         updates = {k: data[k] for k in allowed_fields if k in data}

#         if not updates:
#             return {"error": "No updatable fields provided."}, 400

#         if "name" in updates and not str(updates["name"] or "").strip():
#             return {"error": "name cannot be empty."}, 400

#         if "bill_no_count" in updates:
#             try:
#                 updates["bill_no_count"] = int(updates["bill_no_count"])
#             except (TypeError, ValueError):
#                 return {"error": "bill_no_count must be an integer."}, 400
#             if updates["bill_no_count"] < 0:
#                 return {"error": "bill_no_count cannot be negative."}, 400

#         # -------- DB --------
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # Lock the row so this can't interleave with a bill being numbered
#         cursor.execute("""
#             SELECT id, name, fiscal_year, bill_no_count
#             FROM hotel_company_property
#             WHERE id = %s
#             FOR UPDATE
#         """, (id,))
#         current = cursor.fetchone()
#         if not current:
#             mydb.rollback()
#             return {"error": "Property not found"}, 404

#         # Name must stay unique
#         if "name" in updates and updates["name"] != current["name"]:
#             cursor.execute(
#                 "SELECT id FROM hotel_company_property WHERE name = %s AND id <> %s",
#                 (updates["name"], id),
#             )
#             if cursor.fetchone():
#                 mydb.rollback()
#                 return {"error": "Another property with this name already exists."}, 400

#         # New fiscal year -> restart the bill counter unless one was sent explicitly
#         if (
#             "fiscal_year" in updates
#             and updates["fiscal_year"] != current["fiscal_year"]
#             and "bill_no_count" not in updates
#         ):
#             updates["bill_no_count"] = 0

#         set_clause = ", ".join(f"{col} = %s" for col in updates)
#         params = list(updates.values()) + [id]

#         cursor.execute(
#             f"UPDATE hotel_company_property SET {set_clause} WHERE id = %s",
#             params,
#         )
#         mydb.commit()

#         return jsonify({
#             "message": "Property updated successfully",
#             "updated_fields": list(updates.keys()),
#         }), 200

#     except Exception as e:
#         if mydb:
#             try:
#                 mydb.rollback()
#             except Exception:
#                 pass
#         return {"error": str(e)}, 500

#     finally:
#         if cursor:
#             try:
#                 cursor.close()
#             except Exception:
#                 pass
#         if mydb:
#             try:
#                 mydb.close()
#             except Exception:
#                 pass
    
# from root.auth.property_access import get_employee_properties

# @app_file480.route("/properties/<int:id>", methods=["DELETE"])
# @cross_origin()
# def delete_property(id):
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         # TOKEN
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token"}, 400

#         # -------- EMPLOYEE ACCESS CHECK --------
#         employee_id = request.args.get("employee_id")
#         if not employee_id:
#             return {"error": "No Employee id provided"}, 400

#         allowed_properties = get_employee_properties(employee_id)
#         allowed_ids = {p["id"] for p in allowed_properties}

#         if id not in allowed_ids:
#             return {"error": "You do not have access to this property"}, 403

#         cursor.execute("""
#             DELETE FROM hotel_company_property WHERE id = %s
#         """, (id,))

#         mydb.commit()

#         if cursor.rowcount == 0:
#             mydb.close()
#             return {"error": "Property not found"}, 404

#         mydb.close()

#         return jsonify({"message": "Property deleted successfully"}), 200

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500
    

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
from root.auth.check import token_auth

app_file480 = Blueprint('app_file480', __name__)

@app_file480.route("/properties", methods=["POST"])
@cross_origin()
def create_property():
    # -------- TOKEN --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- INPUT --------
    data = request.get_json() or {}

    def clean(key):
        """Trim strings; turn empty values into NULL."""
        value = data.get(key)
        if isinstance(value, str):
            value = value.strip()
        return value or None

    name = clean("name")
    address = clean("address")
    contact_no = clean("contact_no")
    website = clean("website")
    pan_no = clean("pan_no")
    fiscal_year = clean("fiscal_year")

    if not name:
        return {"error": "Property name is required"}, 400

    # bill_no_count: optional, defaults to 0 (kept out of clean() so 0 stays 0)
    raw_count = data.get("bill_no_count")
    if raw_count is None or raw_count == "":
        bill_no_count = 0
    else:
        try:
            bill_no_count = int(raw_count)
        except (TypeError, ValueError):
            return {"error": "bill_no_count must be an integer."}, 400
        if bill_no_count < 0:
            return {"error": "bill_no_count cannot be negative."}, 400

    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Name must be unique (same rule as the update endpoint)
        cursor.execute(
            "SELECT id FROM hotel_company_property WHERE name = %s",
            (name,),
        )
        if cursor.fetchone():
            return {"error": "A property with this name already exists."}, 400

        cursor.execute(
            """
            INSERT INTO hotel_company_property
                (name, address, contact_no, website, pan_no,
                 bill_no_count, fiscal_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name, address, contact_no, website, pan_no,
             bill_no_count, fiscal_year),
        )
        mydb.commit()
        property_id = cursor.lastrowid

        return jsonify({
            "message": "Property created successfully",
            "property_id": property_id,
        }), 201

    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
            except Exception:
                pass
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass


from root.auth.property_access import get_employee_properties

@app_file480.route("/properties", methods=["GET"])
@cross_origin()
def get_properties():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

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

        # -------- EMPLOYEE FILTER (from query param) --------
        employee_id = request.args.get("employee_id")

        if employee_id:
            properties = get_employee_properties(employee_id)
        else:
            return {"error": "No Employee id provided"}, 400

            # cursor.execute("""
            #     SELECT * FROM hotel_company_property
            #     ORDER BY id DESC
            # """)
            # properties = cursor.fetchall()

        mydb.close()

        return jsonify({
            "total_properties": len(properties),
            "properties": properties
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500
    

from root.auth.property_access import get_employee_properties

@app_file480.route("/properties/<int:id>", methods=["GET"])
@cross_origin()
def get_property(id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        # TOKEN
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token"}, 400

        # -------- EMPLOYEE ACCESS CHECK --------
        employee_id = request.args.get("employee_id")
        if not employee_id:
            return {"error": "No Employee id provided"}, 400

        allowed_properties = get_employee_properties(employee_id)
        allowed_ids = {p["id"] for p in allowed_properties}

        if id not in allowed_ids:
            return {"error": "You do not have access to this property"}, 403

        cursor.execute("""
            SELECT * FROM hotel_company_property WHERE id = %s
        """, (id,))
        property = cursor.fetchone()

        mydb.close()

        if not property:
            return {"error": "Property not found"}, 404

        return jsonify(property), 200

    except Exception as e:
        return {"error": str(e)}, 500


from root.auth.property_access import get_employee_properties

@app_file480.route("/properties/<int:id>", methods=["PUT", "PATCH"])
@cross_origin()
def update_property(id):
    mydb = None
    cursor = None
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
            return {"error": "Invalid token"}, 400

        data = request.get_json() or {}

        # -------- EMPLOYEE ACCESS CHECK --------
        employee_id = data.get("employee_id")
        if not employee_id:
            return {"error": "No Employee id provided"}, 400

        allowed_properties = get_employee_properties(employee_id)
        allowed_ids = {p["id"] for p in allowed_properties}

        if id not in allowed_ids:
            return {"error": "You do not have access to this property"}, 403

        # -------- FIELDS (only what was sent gets updated) --------
        allowed_fields = [
            "name", "address", "contact_no", "website", "pan_no",
            "bill_no_count", "fiscal_year",
        ]
        updates = {k: data[k] for k in allowed_fields if k in data}

        if not updates:
            return {"error": "No updatable fields provided."}, 400

        if "name" in updates and not str(updates["name"] or "").strip():
            return {"error": "name cannot be empty."}, 400

        if "bill_no_count" in updates:
            try:
                updates["bill_no_count"] = int(updates["bill_no_count"])
            except (TypeError, ValueError):
                return {"error": "bill_no_count must be an integer."}, 400
            if updates["bill_no_count"] < 0:
                return {"error": "bill_no_count cannot be negative."}, 400

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # Lock the row so this can't interleave with a bill being numbered
        cursor.execute("""
            SELECT id, name, fiscal_year, bill_no_count
            FROM hotel_company_property
            WHERE id = %s
            FOR UPDATE
        """, (id,))
        current = cursor.fetchone()
        if not current:
            mydb.rollback()
            return {"error": "Property not found"}, 404

        # Name must stay unique
        if "name" in updates and updates["name"] != current["name"]:
            cursor.execute(
                "SELECT id FROM hotel_company_property WHERE name = %s AND id <> %s",
                (updates["name"], id),
            )
            if cursor.fetchone():
                mydb.rollback()
                return {"error": "Another property with this name already exists."}, 400

        # New fiscal year -> restart the bill counter unless one was sent explicitly
        if (
            "fiscal_year" in updates
            and updates["fiscal_year"] != current["fiscal_year"]
            and "bill_no_count" not in updates
        ):
            updates["bill_no_count"] = 0

        set_clause = ", ".join(f"{col} = %s" for col in updates)
        params = list(updates.values()) + [id]

        cursor.execute(
            f"UPDATE hotel_company_property SET {set_clause} WHERE id = %s",
            params,
        )
        mydb.commit()

        return jsonify({
            "message": "Property updated successfully",
            "updated_fields": list(updates.keys()),
        }), 200

    except Exception as e:
        if mydb:
            try:
                mydb.rollback()
            except Exception:
                pass
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass
    
from root.auth.property_access import get_employee_properties

@app_file480.route("/properties/<int:id>", methods=["DELETE"])
@cross_origin()
def delete_property(id):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        # TOKEN
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token"}, 400

        # -------- EMPLOYEE ACCESS CHECK --------
        employee_id = request.args.get("employee_id")
        if not employee_id:
            return {"error": "No Employee id provided"}, 400

        allowed_properties = get_employee_properties(employee_id)
        allowed_ids = {p["id"] for p in allowed_properties}

        if id not in allowed_ids:
            return {"error": "You do not have access to this property"}, 403

        cursor.execute("""
            DELETE FROM hotel_company_property WHERE id = %s
        """, (id,))

        mydb.commit()

        if cursor.rowcount == 0:
            mydb.close()
            return {"error": "Property not found"}, 404

        mydb.close()

        return jsonify({"message": "Property deleted successfully"}), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500
    