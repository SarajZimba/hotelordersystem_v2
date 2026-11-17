

# from flask import  Blueprint,request, jsonify
# import mysql.connector
# from flask_cors import  cross_origin
# import os
# from dotenv import load_dotenv
# load_dotenv()
# app_file2 = Blueprint('app_file2',__name__)
# from root.auth.check import token_auth



# @app_file2.route("/outlets", methods=["POST"])
# @cross_origin()
# def outlets():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(buffered=True)
#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)
#         json = request.get_json()
#         if "token" not in json  or not any([json["token"]])  or json["token"]=="":
#             data = {"error":"No token provided."}
#             return data,400
#         token = json["token"]
#         if not token_auth(token):
#             data = {"error":"Invalid token."}
#             return data,400
#         # Validate employee_id
#         # if "employee_id" not in json or not json["employee_id"]:
#         #     return {"error": "No employee_id provided."}, 400
#         # employee_id = json["employee_id"]

#         employee_id = json.get("employee_id", None)

#         if employee_id:


#             # Get only outlets the employee has access to (status = TRUE)
#             cursor.execute("""
#                 SELECT o.id, o.Outlet, o.Company_name, o.address, o.logo, o.sms_text, o.bill_prefix, o.loyalty_percent
#                 FROM outetNames o
#                 JOIN employeeoutlets eo ON eo.outlet_id = o.id
#                 WHERE eo.employee_id = %s AND eo.status = TRUE
#             """, (employee_id,))

#         else:
#             get_outlet_sql =f"""select distinct Outlet, Company_name, address, loyalty_percent, sms_text, logo, bill_prefix from outetNames"""
#             cursor.execute(get_outlet_sql)
#             # result = cursor.fetchall()
#             # if result == []:
#             #     data = {"error":"Temporarily unavailable."}
#             #     return data,400
#         result = cursor.fetchall()

#         if not result:
#             return {"error": "No outlets available for this employee."}, 400
#         row_headers=[x[0] for x in cursor.description] 
#         json_data=[]
#         for res in result:
#             json_data.append(dict(zip(row_headers,res)))
#         response_json = []
#         for i in json_data:
#             outlet_json ={"name":i["Outlet"],"value":i["Outlet"], "company": i["Company_name"], "address": i["address"], "loyalty_percent": float(i["loyalty_percent"]), "sms_text": i["sms_text"], "logo": i["logo"], "bill_prefix": i["bill_prefix"]}
#             response_json.append(outlet_json)
#         mydb.close()
#         return response_json,200
#     except Exception as error:
#         data ={'error':str(error)}
#         return data,400


# @app_file2.route("/create_restaurant", methods=["POST"])
# @cross_origin()
# def create_restaurant():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         json_data = request.get_json() or {}

#         # -------- TOKEN --------
#         token = json_data.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         outlet_name = json_data.get("Outlet")
#         if not outlet_name:
#             return {"error": "Outlet is required"}, 400

#         company_property_id = json_data.get("company_property_id")  # optional

#         # -------- CHECK DUPLICATE OUTLET NAME --------
#         cursor.execute("SELECT id FROM outetNames WHERE Outlet = %s", (outlet_name,))
#         existing = cursor.fetchone()
#         if existing:
#             return {"error": "An outlet with this name already exists"}, 400

#         # -------- VALIDATE company_property_id IF PROVIDED --------
#         if company_property_id:
#             cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (company_property_id,))
#             if not cursor.fetchone():
#                 return {"error": "No hotel property found with that company_property_id"}, 400

#         # -------- INSERT --------
#         insert_sql = """
#             INSERT INTO outetNames (
#                 Outlet, Company_name, address, confidencelevel, loyalty_percent,
#                 bill_prefix, postingToIRD, sms_text, logo, company_property_id
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         cursor.execute(insert_sql, (
#             outlet_name,
#             json_data.get("Company_name"),
#             json_data.get("address"),
#             json_data.get("confidencelevel"),
#             json_data.get("loyalty_percent", 0),
#             json_data.get("bill_prefix", ""),
#             json_data.get("postingToIRD", 0),
#             json_data.get("sms_text"),
#             json_data.get("logo"),
#             company_property_id
#         ))

#         new_outlet_id = cursor.lastrowid
#         mydb.commit()
#         mydb.close()

#         return jsonify({
#             "message": "Restaurant created successfully",
#             "outlet_id": new_outlet_id,
#             "Outlet": outlet_name,
#             "company_property_id": company_property_id
#         }), 201

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500


# @app_file2.route("/assign_restaurant_to_hotel", methods=["POST"])
# @cross_origin()
# def assign_restaurant_to_hotel():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

#         json_data = request.get_json() or {}

#         # -------- TOKEN --------
#         token = json_data.get("token")
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- INPUT --------
#         outlet_id = json_data.get("outlet_id")
#         company_property_id = json_data.get("company_property_id")

#         if not outlet_id or not company_property_id:
#             return {"error": "outlet_id and company_property_id are required"}, 400

#         # -------- VALIDATE OUTLET EXISTS --------
#         cursor.execute("SELECT id FROM outetNames WHERE id = %s", (outlet_id,))
#         if not cursor.fetchone():
#             return {"error": "No outlet found with that outlet_id"}, 400

#         # -------- VALIDATE PROPERTY EXISTS --------
#         cursor.execute("SELECT id, name FROM hotel_company_property WHERE id = %s", (company_property_id,))
#         property_row = cursor.fetchone()
#         if not property_row:
#             return {"error": "No hotel property found with that company_property_id"}, 400

#         # -------- UPDATE --------
#         cursor.execute(
#             "UPDATE outetNames SET company_property_id = %s WHERE id = %s",
#             (company_property_id, outlet_id)
#         )
#         mydb.commit()
#         mydb.close()

#         return jsonify({
#             "message": "Restaurant assigned to hotel successfully",
#             "outlet_id": outlet_id,
#             "company_property_id": company_property_id,
#             "hotel_name": property_row["name"]
#         }), 200

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500


from flask import  Blueprint,request, jsonify
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file2 = Blueprint('app_file2',__name__)
from root.auth.check import token_auth



@app_file2.route("/outlets", methods=["POST"])
@cross_origin()
def outlets():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        # Validate employee_id
        # if "employee_id" not in json or not json["employee_id"]:
        #     return {"error": "No employee_id provided."}, 400
        # employee_id = json["employee_id"]

        employee_id = json.get("employee_id", None)

        if employee_id:


            # Get only outlets the employee has access to (status = TRUE)
            cursor.execute("""
                SELECT o.id, o.Outlet, o.Company_name, o.address, o.logo, o.sms_text, o.bill_prefix, o.loyalty_percent
                FROM outetNames o
                JOIN employeeoutlets eo ON eo.outlet_id = o.id
                WHERE eo.employee_id = %s AND eo.status = TRUE
            """, (employee_id,))

        else:
            get_outlet_sql =f"""select distinct Outlet, Company_name, address, loyalty_percent, sms_text, logo, bill_prefix from outetNames"""
            cursor.execute(get_outlet_sql)
            # result = cursor.fetchall()
            # if result == []:
            #     data = {"error":"Temporarily unavailable."}
            #     return data,400
        result = cursor.fetchall()

        if not result:
            return {"error": "No outlets available for this employee."}, 400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        response_json = []
        for i in json_data:
            outlet_json ={"name":i["Outlet"],"value":i["Outlet"], "company": i["Company_name"], "address": i["address"], "loyalty_percent": float(i["loyalty_percent"]), "sms_text": i["sms_text"], "logo": i["logo"], "bill_prefix": i["bill_prefix"]}
            response_json.append(outlet_json)
        mydb.close()
        return response_json,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400


@app_file2.route("/create_restaurant", methods=["POST"])
@cross_origin()
def create_restaurant():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(dictionary=True, buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

        json_data = request.get_json() or {}

        # -------- TOKEN --------
        token = json_data.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        outlet_name = json_data.get("Outlet")
        if not outlet_name:
            return {"error": "Outlet is required"}, 400

        company_property_id = json_data.get("company_property_id")  # optional

        # -------- CHECK DUPLICATE OUTLET NAME --------
        cursor.execute("SELECT id FROM outetNames WHERE Outlet = %s", (outlet_name,))
        existing = cursor.fetchone()
        if existing:
            return {"error": "An outlet with this name already exists"}, 400

        # -------- VALIDATE company_property_id IF PROVIDED --------
        if company_property_id:
            cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (company_property_id,))
            if not cursor.fetchone():
                return {"error": "No hotel property found with that company_property_id"}, 400

        # -------- INSERT --------
        insert_sql = """
            INSERT INTO outetNames (
                Outlet, Company_name, address, confidencelevel, loyalty_percent,
                bill_prefix, postingToIRD, sms_text, logo, company_property_id, phone, pan_no
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            outlet_name,
            json_data.get("Company_name"),
            json_data.get("address"),
            json_data.get("confidencelevel"),
            json_data.get("loyalty_percent", 0),
            json_data.get("bill_prefix", ""),
            json_data.get("postingToIRD", 0),
            json_data.get("sms_text"),
            json_data.get("logo"),
            company_property_id,
            json_data.get("phone"),
            json_data.get("pan_no"),
        ))

        new_outlet_id = cursor.lastrowid
        mydb.commit()
        mydb.close()

        return jsonify({
            "message": "Restaurant created successfully",
            "outlet_id": new_outlet_id,
            "Outlet": outlet_name,
            "company_property_id": company_property_id
        }), 201

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500


# @app_file2.route("/get_restaurants", methods=["GET"])
# @cross_origin()
# def get_restaurants():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(dictionary=True, buffered=True)
#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)

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

#         # -------- OPTIONAL FILTERS --------
#         outlet_id = request.args.get("id")
#         company_property_id = request.args.get("company_property_id")

#         query = """
#             SELECT o.id, o.Outlet, o.Company_name, o.address, o.confidencelevel, o.loyalty_percent,
#                    o.bill_prefix, o.postingToIRD, o.sms_text, o.logo, o.company_property_id,
#                    p.id AS property_id, p.*
#             FROM outetNames o
#             LEFT JOIN hotel_company_property p ON o.company_property_id = p.id
#             WHERE 1=1
#         """
#         params = []

#         if outlet_id:
#             query += " AND o.id = %s"
#             params.append(outlet_id)

#         if company_property_id:
#             query += " AND o.company_property_id = %s"
#             params.append(company_property_id)

#         query += " ORDER BY o.Outlet"

#         cursor.execute(query, params)
#         rows = cursor.fetchall()

#         # -------- SHAPE RESPONSE: nest property fields under "hotel_property" --------
#         restaurants = []
#         for row in rows:
#             hotel_property = None
#             if row.get("property_id"):
#                 # Everything selected via p.* that isn't already an outlet column
#                 hotel_property = {
#                     k: v for k, v in row.items()
#                     if k not in (
#                         "id", "Outlet", "Company_name", "address", "confidencelevel",
#                         "loyalty_percent", "bill_prefix", "postingToIRD", "sms_text",
#                         "logo", "company_property_id", "property_id"
#                     )
#                 }
#                 hotel_property["id"] = row["property_id"]

#             restaurants.append({
#                 "id": row["id"],
#                 "Outlet": row["Outlet"],
#                 "Company_name": row["Company_name"],
#                 "address": row["address"],
#                 "confidencelevel": row["confidencelevel"],
#                 "loyalty_percent": row["loyalty_percent"],
#                 "bill_prefix": row["bill_prefix"],
#                 "postingToIRD": row["postingToIRD"],
#                 "sms_text": row["sms_text"],
#                 "logo": row["logo"],
#                 "company_property_id": row["company_property_id"],
#                 "hotel_property": hotel_property
#             })

#         mydb.close()

#         return jsonify({
#             "count": len(restaurants),
#             "restaurants": restaurants
#         }), 200

#     except Exception as e:
#         return {"error": str(e)}, 500


@app_file2.route("/get_restaurants", methods=["GET"])
@cross_origin()
def get_restaurants():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(dictionary=True, buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

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

        # -------- OPTIONAL FILTERS --------
        outlet_id = request.args.get("id")
        company_property_id = request.args.get("company_property_id")

        query = """
            SELECT o.id AS outlet_id, o.Outlet, o.Company_name, o.address, o.confidencelevel, o.loyalty_percent,
                o.bill_prefix, o.postingToIRD, o.sms_text, o.logo, o.company_property_id,
                o.phone, o.pan_no,
                p.id AS property_id, p.name AS property_name,
                p.address AS property_address, p.contact_no, p.website,
                p.pan_no AS property_pan_no
            FROM outetNames o
            LEFT JOIN hotel_company_property p ON o.company_property_id = p.id
            WHERE 1=1
        """
        params = []

        if outlet_id:
            query += " AND o.id = %s"
            params.append(outlet_id)

        if company_property_id:
            query += " AND o.company_property_id = %s"
            params.append(company_property_id)

        query += " ORDER BY o.Outlet"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # -------- SHAPE RESPONSE: nest property fields under "hotel_property" --------
        restaurants = []
        for row in rows:
            hotel_property = None
            if row.get("property_id"):
                hotel_property = {
                    "id": row["property_id"],
                    "name": row.get("property_name"),
                    "address": row.get("property_address"),
                    "contact_no": row.get("contact_no"),
                    "website": row.get("website"),
                    "pan_no": row.get("property_pan_no"),
                }

            restaurants.append({
                "id": row["outlet_id"],
                "Outlet": row["Outlet"],
                "Company_name": row["Company_name"],
                "address": row["address"],
                "confidencelevel": row["confidencelevel"],
                "loyalty_percent": row["loyalty_percent"],
                "bill_prefix": row["bill_prefix"],
                "postingToIRD": row["postingToIRD"],
                "sms_text": row["sms_text"],
                "logo": row["logo"],
                "company_property_id": row["company_property_id"],
                "phone": row["phone"],
                "pan_no": row["pan_no"],
                "hotel_property": hotel_property
            })

        mydb.close()

        return jsonify({
            "count": len(restaurants),
            "restaurants": restaurants
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500


@app_file2.route("/assign_restaurant_to_hotel", methods=["POST"])
@cross_origin()
def assign_restaurant_to_hotel():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(dictionary=True, buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

        json_data = request.get_json() or {}

        # -------- TOKEN --------
        token = json_data.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        outlet_id = json_data.get("outlet_id")
        company_property_id = json_data.get("company_property_id")

        if not outlet_id or not company_property_id:
            return {"error": "outlet_id and company_property_id are required"}, 400

        # -------- VALIDATE OUTLET EXISTS --------
        cursor.execute("SELECT id FROM outetNames WHERE id = %s", (outlet_id,))
        if not cursor.fetchone():
            return {"error": "No outlet found with that outlet_id"}, 400

        # -------- VALIDATE PROPERTY EXISTS --------
        cursor.execute("SELECT id, name FROM hotel_company_property WHERE id = %s", (company_property_id,))
        property_row = cursor.fetchone()
        if not property_row:
            return {"error": "No hotel property found with that company_property_id"}, 400

        # -------- UPDATE --------
        cursor.execute(
            "UPDATE outetNames SET company_property_id = %s WHERE id = %s",
            (company_property_id, outlet_id)
        )
        mydb.commit()
        mydb.close()

        return jsonify({
            "message": "Restaurant assigned to hotel successfully",
            "outlet_id": outlet_id,
            "company_property_id": company_property_id,
            "hotel_name": property_row["name"]
        }), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500



@app_file2.route("/edit_restaurant", methods=["POST"])
@cross_origin()
def edit_restaurant():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(dictionary=True, buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

        json_data = request.get_json() or {}

        # -------- TOKEN --------
        token = json_data.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        outlet_id = json_data.get("id")
        if not outlet_id:
            return {"error": "id is required"}, 400

        # -------- CHECK EXISTS --------
        cursor.execute("SELECT id FROM outetNames WHERE id = %s", (outlet_id,))
        existing = cursor.fetchone()
        if not existing:
            return {"error": "No outlet found with that id"}, 400

        # -------- IF Outlet NAME IS BEING CHANGED, CHECK FOR DUPLICATES --------
        new_outlet_name = json_data.get("Outlet")
        if new_outlet_name:
            cursor.execute("SELECT id FROM outetNames WHERE Outlet = %s AND id != %s", (new_outlet_name, outlet_id))
            dup = cursor.fetchone()
            if dup:
                return {"error": "An outlet with this name already exists"}, 400

        # -------- VALIDATE company_property_id IF PROVIDED AND NOT NULL --------
        # "company_property_id" in json_data distinguishes "not sent" from "sent as null"
        if "company_property_id" in json_data and json_data.get("company_property_id") is not None:
            company_property_id = json_data.get("company_property_id")
            cursor.execute("SELECT id FROM hotel_company_property WHERE id = %s", (company_property_id,))
            if not cursor.fetchone():
                return {"error": "No hotel property found with that company_property_id"}, 400

        # -------- BUILD DYNAMIC UPDATE --------
        editable_fields = [
            "Outlet", "Company_name", "address", "confidencelevel", "loyalty_percent",
            "bill_prefix", "postingToIRD", "sms_text", "logo", "company_property_id",
            "phone", "pan_no"
        ]

        update_fields = []
        update_values = []
        for field in editable_fields:
            if field in json_data:
                update_fields.append(f"{field} = %s")
                update_values.append(json_data.get(field))  # None passes through as NULL

        if not update_fields:
            return {"error": "No fields provided to update"}, 400

        update_values.append(outlet_id)
        update_sql = "UPDATE outetNames SET {} WHERE id = %s".format(", ".join(update_fields))
        cursor.execute(update_sql, tuple(update_values))
        mydb.commit()
        mydb.close()

        return jsonify({
            "message": "Restaurant updated successfully",
            "outlet_id": outlet_id
        }), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500


@app_file2.route("/delete_restaurant", methods=["POST"])
@cross_origin()
def delete_restaurant():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(dictionary=True, buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

        json_data = request.get_json() or {}

        # -------- TOKEN --------
        token = json_data.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        outlet_id = json_data.get("id")
        if not outlet_id:
            return {"error": "id is required"}, 400

        # -------- CHECK EXISTS --------
        cursor.execute("SELECT id, Outlet FROM outetNames WHERE id = %s", (outlet_id,))
        existing = cursor.fetchone()
        if not existing:
            return {"error": "No outlet found with that id"}, 400

        # -------- DELETE --------
        cursor.execute("DELETE FROM outetNames WHERE id = %s", (outlet_id,))
        mydb.commit()
        mydb.close()

        return jsonify({
            "message": "Restaurant deleted successfully",
            "outlet_id": outlet_id,
            "Outlet": existing["Outlet"]
        }), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500