# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from root.auth.check import token_auth

# load_dotenv()

# app_file481 = Blueprint('app_file481', __name__)

# @app_file481.route("/employee-property-access", methods=["POST"])
# @cross_origin()
# def assign_property_to_employee():
#     mydb = None
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True)

#         data = request.get_json() or {}

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
#         employee_id = data.get("employee_id")
#         property_id = data.get("property_id")

#         if not employee_id or not property_id:
#             return {"error": "employee_id and property_id are required"}, 400

#         # -------- VALIDATE EMPLOYEE --------
#         cursor.execute("SELECT id FROM employeelogin WHERE id = %s", (employee_id,))
#         if not cursor.fetchone():
#             return {"error": "Employee not found"}, 404

#         # -------- VALIDATE PROPERTY --------
#         cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (property_id,))
#         if not cursor.fetchone():
#             return {"error": "Property not found"}, 404

#         # -------- INSERT RELATION --------
#         try:
#             cursor.execute("""
#                 INSERT INTO hotel_employee_property_access (employee_id, property_id)
#                 VALUES (%s, %s)
#             """, (employee_id, property_id))

#             mydb.commit()

#         except mysql.connector.IntegrityError as e:
#             print(e)
#             return {"error": "This employee already has access to this property"}, 400

#         return jsonify({
#             "message": "Property assigned to employee successfully"
#         }), 201

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()


# @app_file481.route("/employee-property-access", methods=["GET"])
# @cross_origin()
# def get_employee_properties():
#     mydb = None
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

#         # -------- INPUT --------
#         employee_id = request.args.get("employee_id")

#         if not employee_id:
#             return {"error": "employee_id is required"}, 400

#         # -------- VALIDATE EMPLOYEE --------
#         cursor.execute("SELECT id, userName, type FROM employeelogin WHERE id = %s", (employee_id,))
#         employee = cursor.fetchone()

#         if not employee:
#             return {"error": "Employee not found"}, 404

#         # -------- GET PROPERTIES THIS EMPLOYEE HAS ACCESS TO --------
#         cursor.execute("""
#             SELECT p.*
#             FROM hotel_employee_property_access ep
#             JOIN hotel_company_property p ON ep.property_id = p.id
#             WHERE ep.employee_id = %s
#         """, (employee_id,))

#         properties = cursor.fetchall()

#         return jsonify({
#             "employee": {
#                 "id": employee["id"],
#                 "username": employee["userName"],
#                 "type": employee["type"]
#             },
#             "count": len(properties),
#             "properties": properties
#         }), 200

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

load_dotenv()

app_file481 = Blueprint('app_file481', __name__)

@app_file481.route("/employee-property-access", methods=["POST"])
@cross_origin()
def assign_property_to_employee():
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        data = request.get_json() or {}

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
        employee_id = data.get("employee_id")
        property_id = data.get("property_id")

        if not employee_id or not property_id:
            return {"error": "employee_id and property_id are required"}, 400

        # -------- VALIDATE EMPLOYEE --------
        cursor.execute("SELECT id FROM EmployeeLogin WHERE id = %s", (employee_id,))
        if not cursor.fetchone():
            return {"error": "Employee not found"}, 404

        # -------- VALIDATE PROPERTY --------
        cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (property_id,))
        if not cursor.fetchone():
            return {"error": "Property not found"}, 404

        # -------- INSERT RELATION --------
        try:
            cursor.execute("""
                INSERT INTO hotel_employee_property_access (employee_id, property_id)
                VALUES (%s, %s)
            """, (employee_id, property_id))

            mydb.commit()

            access_id = cursor.lastrowid

        except mysql.connector.IntegrityError as e:
            print(e)
            return {"error": "This employee already has access to this property"}, 400

        return jsonify({
            "message": "Property assigned to employee successfully",
            "access_id": access_id,
            "employee_id": employee_id,
            "property_id": property_id
        }), 201

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()

@app_file481.route("/employee-property-access/<int:access_id>", methods=["DELETE"])
@cross_origin()
def remove_property_access_by_id(access_id):
    mydb = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        cursor.execute("DELETE FROM hotel_employee_property_access WHERE id = %s", (access_id,))

        if cursor.rowcount == 0:
            return {"error": "No such access record found"}, 404

        mydb.commit()
        return jsonify({"message": "Property access removed successfully"}), 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500
    finally:
        if mydb:
            mydb.close()

# @app_file481.route("/employee-property-access", methods=["GET"])
# @cross_origin()
# def get_employee_properties():
#     mydb = None
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

#         # -------- INPUT --------
#         employee_id = request.args.get("employee_id")

#         if not employee_id:
#             return {"error": "employee_id is required"}, 400

#         # -------- VALIDATE EMPLOYEE --------
#         cursor.execute("SELECT id, userName, type FROM employeelogin WHERE id = %s", (employee_id,))
#         employee = cursor.fetchone()

#         if not employee:
#             return {"error": "Employee not found"}, 404

#         # -------- GET PROPERTY IDs THIS EMPLOYEE HAS ACCESS TO --------
#         cursor.execute("""
#             SELECT property_id
#             FROM hotel_employee_property_access
#             WHERE employee_id = %s
#         """, (employee_id,))
#         accessible_ids = {row["property_id"] for row in cursor.fetchall()}

#         # -------- GET ALL PROPERTIES --------
#         cursor.execute("SELECT * FROM hotel_company_property")
#         all_properties = cursor.fetchall()

#         # -------- GET ALL OUTLETS, GROUPED BY PROPERTY --------
#         cursor.execute("""
#             SELECT id, Outlet, Company_name, address, confidencelevel, loyalty_percent,
#                    bill_prefix, postingToIRD, sms_text, logo, company_property_id
#             FROM outetNames
#         """)
#         all_outlets = cursor.fetchall()

#         outlets_by_property = {}
#         for outlet in all_outlets:
#             pid = outlet["company_property_id"]
#             outlets_by_property.setdefault(pid, []).append(outlet)

#         # -------- BUILD RESPONSE: properties, each with status + nested restaurants --------
#         properties = []
#         for prop in all_properties:
#             prop["status"] = prop["id"] in accessible_ids
#             prop["restaurants"] = outlets_by_property.get(prop["id"], [])
#             properties.append(prop)

#         return jsonify({
#             "employee": {
#                 "id": employee["id"],
#                 "username": employee["userName"],
#                 "type": employee["type"]
#             },
#             "count": len(properties),
#             "properties": properties
#         }), 200

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()


# @app_file481.route("/employee-property-access", methods=["GET"])
# @cross_origin()
# def get_employee_properties():
#     mydb = None
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

#         # -------- INPUT --------
#         employee_id = request.args.get("employee_id")

#         if not employee_id:
#             return {"error": "employee_id is required"}, 400

#         # -------- VALIDATE EMPLOYEE --------
#         cursor.execute("SELECT id, userName, type FROM employeelogin WHERE id = %s", (employee_id,))
#         employee = cursor.fetchone()

#         if not employee:
#             return {"error": "Employee not found"}, 404

#         employee_info = {
#             "id": employee["id"],
#             "username": employee["userName"],
#             "type": employee["type"]
#         }
#         employee_type = employee["type"]

#         # ============================================================
#         # RESTAURANT AGENT: no property access — return outlets only
#         # ============================================================
#         if employee_type == "restaurantagent":

#             cursor.execute("""
#                 SELECT eo.id AS access_id, eo.status, o.id, o.Outlet, o.Company_name, o.address,
#                        o.confidencelevel, o.loyalty_percent, o.bill_prefix,
#                        o.postingToIRD, o.sms_text, o.logo, o.company_property_id
#                 FROM employeeoutlets eo
#                 JOIN outetNames o ON eo.outlet_id = o.id
#                 WHERE eo.employee_id = %s
#             """, (employee_id,))
#             assigned_outlets = cursor.fetchall()

#             if not assigned_outlets:
#                 cursor.execute("""
#                     SELECT id, Outlet, Company_name, address, confidencelevel,
#                            loyalty_percent, bill_prefix, postingToIRD, sms_text,
#                            logo, company_property_id
#                     FROM outetNames
#                 """)
#                 all_outlets = cursor.fetchall()
#                 for outlet in all_outlets:
#                     outlet["status"] = False
#                     outlet["access_id"] = None
#                 restaurants = all_outlets
#             else:
#                 restaurants = []
#                 for outlet in assigned_outlets:
#                     outlet["status"] = bool(outlet["status"])
#                     restaurants.append(outlet)

#             return jsonify({
#                 "employee": employee_info,
#                 "count": len(restaurants),
#                 "restaurants": restaurants
#             }), 200

#         # ============================================================
#         # ADMIN / HOTEL AGENT: property access, with nested restaurants
#         # ============================================================

#         # -------- GET PROPERTY ACCESS ROWS THIS EMPLOYEE HAS (access_id + property_id) --------
#         cursor.execute("""
#             SELECT id AS access_id, property_id
#             FROM hotel_employee_property_access
#             WHERE employee_id = %s
#         """, (employee_id,))
#         accessible_properties_map = {row["property_id"]: row["access_id"] for row in cursor.fetchall()}

#         # -------- GET OUTLET ACCESS ROWS THIS EMPLOYEE HAS (access_id + outlet_id + status) --------
#         cursor.execute("""
#             SELECT id AS access_id, outlet_id, status
#             FROM employeeoutlets
#             WHERE employee_id = %s
#         """, (employee_id,))
#         accessible_outlets_map = {
#             row["outlet_id"]: {"status": bool(row["status"]), "access_id": row["access_id"]}
#             for row in cursor.fetchall()
#         }

#         # -------- GET PROPERTIES --------
#         if employee_type == "admin":
#             # Admin sees ALL properties, including ones without access (status False)
#             cursor.execute("SELECT * FROM hotel_company_property")
#             all_properties = cursor.fetchall()
#         else:
#             # hotelagent (or any other non-admin type) only sees properties they actually have access to
#             if not accessible_properties_map:
#                 return jsonify({
#                     "employee": employee_info,
#                     "count": 0,
#                     "properties": []
#                 }), 200

#             format_strings = ','.join(['%s'] * len(accessible_properties_map))
#             cursor.execute(
#                 f"SELECT * FROM hotel_company_property WHERE id IN ({format_strings})",
#                 tuple(accessible_properties_map.keys())
#             )
#             all_properties = cursor.fetchall()

#         # -------- GET ALL OUTLETS, GROUPED BY PROPERTY --------
#         cursor.execute("""
#             SELECT id, Outlet, Company_name, address, confidencelevel, loyalty_percent,
#                    bill_prefix, postingToIRD, sms_text, logo, company_property_id
#             FROM outetNames
#         """)
#         all_outlets = cursor.fetchall()

#         outlets_by_property = {}
#         for outlet in all_outlets:
#             access_info = accessible_outlets_map.get(outlet["id"])
#             outlet["status"] = access_info["status"] if access_info else False
#             outlet["access_id"] = access_info["access_id"] if access_info else None
#             pid = outlet["company_property_id"]
#             outlets_by_property.setdefault(pid, []).append(outlet)

#         # -------- BUILD RESPONSE: properties, each with status + access_id + nested restaurants --------
#         properties = []
#         for prop in all_properties:
#             prop["status"] = prop["id"] in accessible_properties_map
#             prop["access_id"] = accessible_properties_map.get(prop["id"])
#             prop["restaurants"] = outlets_by_property.get(prop["id"], [])
#             properties.append(prop)

#         return jsonify({
#             "employee": employee_info,
#             "count": len(properties),
#             "properties": properties
#         }), 200

#     except Exception as e:
#         if mydb:
#             mydb.rollback()
#         return {"error": str(e)}, 500

#     finally:
#         if mydb:
#             mydb.close()

@app_file481.route("/employee-property-access", methods=["GET"])
@cross_origin()
def get_employee_properties():
    mydb = None
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

        # -------- INPUT --------
        employee_id = request.args.get("employee_id")

        if not employee_id:
            return {"error": "employee_id is required"}, 400

        # -------- VALIDATE EMPLOYEE --------
        cursor.execute("SELECT id, userName, type FROM EmployeeLogin WHERE id = %s", (employee_id,))
        employee = cursor.fetchone()

        if not employee:
            return {"error": "Employee not found"}, 404

        employee_info = {
            "id": employee["id"],
            "username": employee["userName"],
            "type": employee["type"]
        }
        employee_type = employee["type"]

        # -------- GET PROPERTY ACCESS ROWS THIS EMPLOYEE HAS (access_id + property_id) --------
        cursor.execute("""
            SELECT id AS access_id, property_id
            FROM hotel_employee_property_access
            WHERE employee_id = %s
        """, (employee_id,))
        accessible_properties_map = {row["property_id"]: row["access_id"] for row in cursor.fetchall()}

        # -------- GET OUTLET ACCESS ROWS THIS EMPLOYEE HAS (access_id + outlet_id + status) --------
        cursor.execute("""
            SELECT id AS access_id, outlet_id, status
            FROM employeeoutlets
            WHERE employee_id = %s
        """, (employee_id,))
        accessible_outlets_map = {
            row["outlet_id"]: {"status": bool(row["status"]), "access_id": row["access_id"]}
            for row in cursor.fetchall()
        }

        # -------- GET ALL OUTLETS, GROUPED BY PROPERTY --------
        cursor.execute("""
            SELECT id, Outlet, Company_name, address, confidencelevel, loyalty_percent,
                   bill_prefix, postingToIRD, sms_text, logo, company_property_id
            FROM outetNames
        """)
        all_outlets = cursor.fetchall()

        outlets_by_property = {}
        for outlet in all_outlets:
            access_info = accessible_outlets_map.get(outlet["id"])
            outlet["status"] = access_info["status"] if access_info else False
            outlet["access_id"] = access_info["access_id"] if access_info else None
            pid = outlet["company_property_id"]
            outlets_by_property.setdefault(pid, []).append(outlet)

        # -------- DECIDE WHICH PROPERTIES TO INCLUDE, BASED ON TYPE --------
        if employee_type == "admin":
            # Admin sees ALL properties (status will be True for every one)
            cursor.execute("SELECT * FROM hotel_company_property")
            all_properties = cursor.fetchall()

        elif employee_type == "hotelagent":
            # hotelagent only sees properties they've been explicitly granted
            if not accessible_properties_map:
                return jsonify({
                    "employee": employee_info,
                    "count": 0,
                    "properties": []
                }), 200

            format_strings = ','.join(['%s'] * len(accessible_properties_map))
            cursor.execute(
                f"SELECT * FROM hotel_company_property WHERE id IN ({format_strings})",
                tuple(accessible_properties_map.keys())
            )
            all_properties = cursor.fetchall()

        elif employee_type == "restaurantagent":
            # restaurantagent only sees properties containing their OWN assigned restaurant(s)
            if not accessible_outlets_map:
                return jsonify({
                    "employee": employee_info,
                    "count": 0,
                    "properties": []
                }), 200

            assigned_property_ids = {
                outlet["company_property_id"]
                for outlet in all_outlets
                if outlet["id"] in accessible_outlets_map
            }

            format_strings = ','.join(['%s'] * len(assigned_property_ids))
            cursor.execute(
                f"SELECT * FROM hotel_company_property WHERE id IN ({format_strings})",
                tuple(assigned_property_ids)
            )
            all_properties = cursor.fetchall()

        else:
            return {"error": f"Unrecognized user type: {employee_type}"}, 400

        # -------- BUILD RESPONSE: properties, each with status + access_id + nested restaurants --------
        properties = []
        for prop in all_properties:
            if employee_type == "restaurantagent":
                # restaurantagent never has property-level access
                prop["status"] = False
                prop["access_id"] = None
                # Only show THEIR OWN restaurant(s) under this property, not siblings
                prop["restaurants"] = [
                    outlet for outlet in outlets_by_property.get(prop["id"], [])
                    if outlet["id"] in accessible_outlets_map
                ]
            else:
                prop["status"] = prop["id"] in accessible_properties_map
                prop["access_id"] = accessible_properties_map.get(prop["id"])
                prop["restaurants"] = outlets_by_property.get(prop["id"], [])

            properties.append(prop)

        return jsonify({
            "employee": employee_info,
            "count": len(properties),
            "properties": properties
        }), 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()