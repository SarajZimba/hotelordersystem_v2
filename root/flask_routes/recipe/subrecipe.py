from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth

load_dotenv()

app_file107 = Blueprint('app_file107', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )


# @app_file107.route("/sub-recipe", methods=["POST"])
# @cross_origin()
# def create_sub_recipe():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         name = data.get("name")
#         outlet = data.get("outlet")
#         uom = data.get("uom")
#         unit = data.get("unit")
#         costprice = data.get("costprice", 0)
#         items = data.get("items", [])

#         if not name or not outlet or not isinstance(items, list):
#             return jsonify({"error": "Missing fields or invalid items format"}), 400

#         mydb = get_db_connection()
#         cursor = mydb.cursor()

#         # Insert into sub_recipe with new fields
#         cursor.execute("""
#             INSERT INTO sub_recipe (name, outlet, uom, unit, costprice)
#             VALUES (%s, %s, %s, %s, %s)
#         """, (name, outlet, uom, unit, costprice))
#         sub_recipe_id = cursor.lastrowid

#         for item in items:
#             item_name = item.get("name")
#             rate = item.get("rate")
#             item_uom = item.get("uom")
#             new_uom = item.get("new_uom")  # New field
#             quantity = item.get("quantity")
#             cost = item.get("cost")

#             if not all([item_name, rate, item_uom, new_uom, quantity, cost]):
#                 continue

#             cursor.execute("""
#                 INSERT INTO sub_recipe_items (sub_recipe_id, name, rate, uom, new_uom, quantity, cost)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s)
#             """, (sub_recipe_id, item_name, rate, item_uom, new_uom, quantity, cost))

#         mydb.commit()
#         cursor.close()
#         mydb.close()

#         return jsonify({"message": "Sub recipe created successfully."}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

@app_file107.route("/sub-recipe", methods=["POST"])
@cross_origin()
def create_sub_recipe():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        name = data.get("name")
        outlet = data.get("outlet")
        uom = data.get("uom")
        unit = data.get("unit")  # This is the unit for the main sub_recipe
        costprice = data.get("costprice", 0)
        items = data.get("items", [])

        if not name or not outlet or not isinstance(items, list):
            return jsonify({"error": "Missing fields or invalid items format"}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor()

        # Insert into sub_recipe
        cursor.execute("""
            INSERT INTO sub_recipe (name, outlet, uom, unit, costprice)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, outlet, uom, unit, costprice))
        sub_recipe_id = cursor.lastrowid

        for item in items:
            item_name = item.get("name")
            rate = item.get("rate")
            item_uom = item.get("uom")
            new_uom = item.get("new_uom")
            quantity = item.get("quantity")
            cost = item.get("cost")
            item_unit = item.get("unit", 1)  # Default to 1 if not provided

            if not all([item_name, rate, item_uom, new_uom, quantity, cost]):
                continue

            cursor.execute("""
                INSERT INTO sub_recipe_items (sub_recipe_id, name, rate, uom, new_uom, quantity, cost, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (sub_recipe_id, item_name, rate, item_uom, new_uom, quantity, cost, item_unit))

        mydb.commit()
        cursor.close()
        mydb.close()

        return jsonify({"message": "Sub recipe created successfully."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# @app_file107.route("/sub-recipe/<int:id>", methods=["GET", "PUT", "DELETE", "PATCH"])
# @cross_origin()
# def get_update_delete_sub_recipe(id):
#     try:
#         print("this is the request", request.method)
#         if request.method == "GET":
#             mydb = get_db_connection()
#             cursor = mydb.cursor(dictionary=True)

#             cursor.execute("SELECT * FROM sub_recipe WHERE id = %s", (id,))
#             recipe = cursor.fetchone()
#             if not recipe:
#                 return jsonify({"error": "Sub recipe not found."}), 404

#             cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (id,))
#             items = cursor.fetchall()
#             recipe["items"] = items

#             cursor.close()
#             mydb.close()
#             return jsonify(recipe)

#         # Shared logic for PUT / PATCH / DELETE
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         mydb = get_db_connection()
#         cursor = mydb.cursor()

#         if request.method == "PUT":
#             name = data.get("name")
#             outlet = data.get("outlet")
#             items = data.get("items", [])

#             if not name or not outlet or not isinstance(items, list):
#                 return jsonify({"error": "Missing fields or invalid items format"}), 400

#             # Update sub_recipe main record
#             cursor.execute("UPDATE sub_recipe SET name = %s, outlet = %s WHERE id = %s", (name, outlet, id))

#             # Get existing item ids from database
#             cursor.execute("SELECT id FROM sub_recipe_items WHERE sub_recipe_id = %s", (id,))
#             existing_ids = {row[0] for row in cursor.fetchall()}
#             sent_ids = set()

#             for item in items:
#                 item_id = item.get("id")
#                 item_name = item.get("name")
#                 rate = item.get("rate")
#                 uom = item.get("uom")
#                 new_uom = item.get("new_uom")  # <-- New Field
#                 quantity = item.get("quantity")
#                 cost = item.get("cost")

#                 if not all([item_name, rate, uom, new_uom, quantity, cost]):
#                     continue

#                 if item_id and item_id in existing_ids:
#                     # Update existing item
#                     cursor.execute("""
#                         UPDATE sub_recipe_items
#                         SET name = %s, rate = %s, uom = %s, new_uom = %s, quantity = %s, cost = %s
#                         WHERE id = %s AND sub_recipe_id = %s
#                     """, (item_name, rate, uom, new_uom, quantity, cost, item_id, id))
#                     sent_ids.add(item_id)
#                 else:
#                     # Insert new item
#                     cursor.execute("""
#                         INSERT INTO sub_recipe_items (sub_recipe_id, name, rate, uom, new_uom, quantity, cost)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s)
#                     """, (id, item_name, rate, uom, new_uom, quantity, cost))

#             # Delete removed items
#             to_delete = existing_ids - sent_ids
#             if to_delete:
#                 cursor.execute(
#                     f"DELETE FROM sub_recipe_items WHERE id IN ({','.join(['%s'] * len(to_delete))})",
#                     tuple(to_delete)
#                 )

#             mydb.commit()
#             message = "Sub recipe updated."

#         elif request.method == "PATCH":
#             fields = []
#             values = []
#             for field in ["name", "outlet", "uom", "unit", "costprice"]:
#                 if field in data:
#                     fields.append(f"{field} = %s")
#                     values.append(data[field])

#             if fields:
#                 query = f"UPDATE sub_recipe SET {', '.join(fields)} WHERE id = %s"
#                 values.append(id)
#                 cursor.execute(query, tuple(values))

#             # Partial update for items
#             items = data.get("items")
#             if isinstance(items, list):
#                 for item in items:
#                     item_id = item.get("id")
#                     item_fields = []
#                     item_values = []

#                     for field in ["name", "rate", "uom", "new_uom", "quantity", "cost"]:
#                         if field in item:
#                             item_fields.append(f"{field} = %s")
#                             item_values.append(item[field])

#                     if item_id and item_fields:
#                         query = f"UPDATE sub_recipe_items SET {', '.join(item_fields)} WHERE id = %s AND sub_recipe_id = %s"
#                         item_values.extend([item_id, id])
#                         cursor.execute(query, tuple(item_values))
#                     elif not item_id:
#                         # Insert if full details are present
#                         required = [item.get(f) for f in ["name", "rate", "uom", "new_uom", "quantity", "cost"]]
#                         if all(required):
#                             cursor.execute("""
#                                 INSERT INTO sub_recipe_items (sub_recipe_id, name, rate, uom, new_uom, quantity, cost)
#                                 VALUES (%s, %s, %s, %s, %s, %s, %s)
#                             """, (id, *required))

#             mydb.commit()
#             message = "Sub recipe patched."

#         elif request.method == "DELETE":
#             print("got delete request")
#             cursor.execute("DELETE FROM sub_recipe_items WHERE sub_recipe_id = %s", (id,))
#             cursor.execute("DELETE FROM sub_recipe WHERE id = %s", (id,))
#             mydb.commit()
#             message = "Sub recipe deleted."

#         cursor.close()
#         mydb.close()
#         return jsonify({"message": message})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

@app_file107.route("/sub-recipe/<int:id>", methods=["GET", "PUT", "DELETE", "PATCH"])
@cross_origin()
def get_update_delete_sub_recipe(id):
    try:
        if request.method == "GET":
            mydb = get_db_connection()
            cursor = mydb.cursor(dictionary=True)

            cursor.execute("SELECT * FROM sub_recipe WHERE id = %s", (id,))
            recipe = cursor.fetchone()
            if not recipe:
                return jsonify({"error": "Sub recipe not found."}), 404

            cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (id,))
            items = cursor.fetchall()
            recipe["items"] = items

            cursor.close()
            mydb.close()
            return jsonify(recipe)

        # Shared logic for PUT / PATCH / DELETE
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor()

        if request.method == "PUT":
            name = data.get("name")
            outlet = data.get("outlet")
            uom = data.get("uom")
            unit = data.get("unit")
            costprice = data.get("costprice", 0)
            items = data.get("items", [])

            if not name or not outlet or not isinstance(items, list):
                return jsonify({"error": "Missing fields or invalid items format"}), 400

            cursor.execute("""
                UPDATE sub_recipe SET name = %s, outlet = %s, uom = %s, unit = %s, costprice = %s
                WHERE id = %s
            """, (name, outlet, uom, unit, costprice, id))

            cursor.execute("SELECT id FROM sub_recipe_items WHERE sub_recipe_id = %s", (id,))
            existing_ids = {row[0] for row in cursor.fetchall()}
            sent_ids = set()

            for item in items:
                item_id = item.get("id")
                item_name = item.get("name")
                rate = item.get("rate")
                item_uom = item.get("uom")
                new_uom = item.get("new_uom")
                quantity = item.get("quantity")
                cost = item.get("cost")
                item_unit = item.get("unit", 1)

                if not all([item_name, rate, item_uom, new_uom, quantity, cost]):
                    continue

                if item_id and item_id in existing_ids:
                    cursor.execute("""
                        UPDATE sub_recipe_items
                        SET name = %s, rate = %s, uom = %s, new_uom = %s, quantity = %s, cost = %s, unit = %s
                        WHERE id = %s AND sub_recipe_id = %s
                    """, (item_name, rate, item_uom, new_uom, quantity, cost, item_unit, item_id, id))
                    sent_ids.add(item_id)
                else:
                    cursor.execute("""
                        INSERT INTO sub_recipe_items (sub_recipe_id, name, rate, uom, new_uom, quantity, cost, unit)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id, item_name, rate, item_uom, new_uom, quantity, cost, item_unit))

            to_delete = existing_ids - sent_ids
            if to_delete:
                cursor.execute(
                    f"DELETE FROM sub_recipe_items WHERE id IN ({','.join(['%s'] * len(to_delete))})",
                    tuple(to_delete)
                )

            mydb.commit()
            message = "Sub recipe updated."

        elif request.method == "PATCH":
            fields = []
            values = []
            for field in ["name", "outlet", "uom", "unit", "costprice"]:
                if field in data:
                    fields.append(f"{field} = %s")
                    values.append(data[field])

            if fields:
                query = f"UPDATE sub_recipe SET {', '.join(fields)} WHERE id = %s"
                values.append(id)
                cursor.execute(query, tuple(values))

            items = data.get("items")
            if isinstance(items, list):
                for item in items:
                    item_id = item.get("id")
                    item_fields = []
                    item_values = []

                    for field in ["name", "rate", "uom", "new_uom", "quantity", "cost", "unit"]:
                        if field in item:
                            item_fields.append(f"{field} = %s")
                            item_values.append(item[field])

                    if item_id and item_fields:
                        query = f"UPDATE sub_recipe_items SET {', '.join(item_fields)} WHERE id = %s AND sub_recipe_id = %s"
                        item_values.extend([item_id, id])
                        cursor.execute(query, tuple(item_values))
                    elif not item_id:
                        required = [item.get(f) for f in ["name", "rate", "uom", "new_uom", "quantity", "cost"]]
                        item_unit = item.get("unit", 1)
                        if all(required):
                            cursor.execute("""
                                INSERT INTO sub_recipe_items (sub_recipe_id, name, rate, uom, new_uom, quantity, cost, unit)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (id, *required, item_unit))

            mydb.commit()
            message = "Sub recipe patched."

        elif request.method == "DELETE":
            cursor.execute("DELETE FROM sub_recipe_items WHERE sub_recipe_id = %s", (id,))
            cursor.execute("DELETE FROM sub_recipe WHERE id = %s", (id,))
            mydb.commit()
            message = "Sub recipe deleted."

        cursor.close()
        mydb.close()
        return jsonify({"message": message})

    except Exception as e:
        return jsonify({"error": str(e)}), 400



@app_file107.route("/sub-recipes", methods=["GET"])
@cross_origin()
def get_all_sub_recipes():
    try:
        outlet_filter = request.args.get("outlet")  # e.g. ?outlet=Kathmandu Outlet

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True)

        # Apply filter if outlet is provided
        if outlet_filter:
            cursor.execute("SELECT * FROM sub_recipe WHERE outlet = %s", (outlet_filter,))
        else:
            cursor.execute("SELECT * FROM sub_recipe")

        recipes = cursor.fetchall()

        # For each recipe, fetch its items
        for recipe in recipes:
            cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (recipe["id"],))
            items = cursor.fetchall()
            recipe["items"] = items

        cursor.close()
        mydb.close()
        return jsonify(recipes)

    except Exception as e:
        return jsonify({"error": str(e)}), 400
