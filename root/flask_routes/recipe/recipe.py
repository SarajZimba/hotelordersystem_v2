# from flask import Blueprint, jsonify, request
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from flask_cors import cross_origin
# from root.auth.check import token_auth

# load_dotenv()

# app_file108 = Blueprint('app_file108', __name__)

# def get_db_connection():
#     return mysql.connector.connect(
#         host=os.getenv("host"),
#         user=os.getenv("user"),
#         password=os.getenv("password"),
#         database=os.getenv("database")
#     )

# @app_file108.route("/recipe", methods=["POST"])
# @cross_origin()
# def create_recipe():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         name = data.get("name")
#         outlet = data.get("outlet")
#         cost_price = data.get("cost_price")
#         selling_price = data.get("selling_price")
#         cost_percent = data.get("cost_percent")
#         item_type = data.get("item_type")
#         items = data.get("items", [])
#         sub_recipes = data.get("sub_recipes", [])

#         if (
#             not name or
#             not outlet or
#             cost_price is None or
#             selling_price is None or
#             cost_percent is None or
#             not item_type or
#             not isinstance(items, list) or
#             not isinstance(sub_recipes, list)
#         ):
#             return jsonify({"error": "Missing fields or invalid format for items, sub_recipes, or cost fields"}), 400

#         mydb = get_db_connection()
#         cursor = mydb.cursor()

#         # Insert main recipe
#         cursor.execute(
#             """
#             INSERT INTO recipe (name, outlet, costprice, sellingprice, cost_percent, ItemType)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """,
#             (name, outlet, cost_price, selling_price, cost_percent, item_type)
#         )
#         recipe_id = cursor.lastrowid

#         # Insert recipe items with 'unit'
#         for item in items:
#             item_name = item.get("name")
#             rate = item.get("rate")
#             uom = item.get("uom")
#             new_uom = item.get("new_uom")
#             quantity = item.get("quantity")
#             cost = item.get("cost")
#             unit = item.get("unit", 1)  # default to 1 if not provided

#             if not all([item_name, rate, uom, quantity, cost]):
#                 continue

#             cursor.execute("""
#                 INSERT INTO recipe_items (recipe_id, name, rate, uom, new_uom, unit, quantity, cost)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """, (recipe_id, item_name, rate, uom, new_uom, unit, quantity, cost))

#         # Insert sub-recipes
#         for sr in sub_recipes:
#             sub_recipe_id = sr.get("sub_recipe_id")
#             quantity = sr.get("quantity", 0)
#             uom = sr.get("uom")
#             unit = sr.get("unit")
#             new_uom = sr.get("new_uom")
#             costprice = sr.get("costprice")
#             rate = sr.get("rate")

#             if not sub_recipe_id:
#                 continue

#             cursor.execute("""
#                 INSERT INTO recipe_subrecipes (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """, (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom))

#         mydb.commit()
#         cursor.close()
#         mydb.close()

#         return jsonify({"message": "Recipe created successfully with sub-recipes."}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400



# # @app_file108.route("/recipe/<int:id>", methods=["GET", "PUT", "PATCH", "DELETE"])
# # @cross_origin()
# # def get_update_delete_recipe(id):
# #     try:
# #         if request.method == "GET":
# #             mydb = get_db_connection()
# #             cursor = mydb.cursor(dictionary=True)

# #             cursor.execute("SELECT * FROM recipe WHERE id = %s", (id,))
# #             recipe = cursor.fetchone()
# #             if not recipe:
# #                 return jsonify({"error": "Recipe not found."}), 404

# #             cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (id,))
# #             recipe["items"] = cursor.fetchall()

# #             cursor.execute("""
# #                 SELECT rs.id AS link_id, sr.id AS sub_recipe_id, sr.name, sr.outlet,
# #                        rs.quantity, rs.uom, rs.unit, rs.costprice, rs.rate, rs.new_uom
# #                 FROM recipe_subrecipes rs
# #                 JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
# #                 WHERE rs.recipe_id = %s
# #             """, (id,))
# #             sub_recipes = cursor.fetchall()

# #             for sub_recipe in sub_recipes:
# #                 cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
# #                 sub_recipe["items"] = cursor.fetchall()

# #             recipe["sub_recipes"] = sub_recipes

# #             cursor.close()
# #             mydb.close()
# #             return jsonify(recipe)

# #         data = request.get_json()
# #         token = data.get("token")
# #         if not token or not token_auth(token):
# #             return jsonify({"error": "Invalid or missing token."}), 400

# #         mydb = get_db_connection()
# #         cursor = mydb.cursor()

# #         if request.method == "PUT":
# #             name = data.get("name")
# #             outlet = data.get("outlet")
# #             cost_price = data.get("cost_price")
# #             selling_price = data.get("selling_price")
# #             cost_percent = data.get("cost_percent")
# #             item_type = data.get("item_type")
# #             items = data.get("items", [])
# #             sub_recipes = data.get("sub_recipes", [])

# #             if not name or not outlet or cost_price is None or selling_price is None or cost_percent is None or not item_type:
# #                 return jsonify({"error": "Missing required fields."}), 400

# #             cursor.execute("""
# #                 UPDATE recipe SET name = %s, outlet = %s, costprice = %s, sellingprice = %s, cost_percent = %s, ItemType = %s
# #                 WHERE id = %s
# #             """, (name, outlet, cost_price, selling_price, cost_percent, item_type, id))

# #             cursor.execute("SELECT id FROM recipe_items WHERE recipe_id = %s", (id,))
# #             existing_item_ids = {row[0] for row in cursor.fetchall()}
# #             sent_item_ids = set()

# #             for item in items:
# #                 item_id = item.get("id")
# #                 if item_id and item_id in existing_item_ids:
# #                     cursor.execute("""
# #                         UPDATE recipe_items SET name=%s, rate=%s, uom=%s, new_uom=%s, quantity=%s, cost=%s
# #                         WHERE id=%s AND recipe_id=%s
# #                     """, (item["name"], item["rate"], item["uom"], item.get("new_uom"), item["quantity"], item["cost"], item_id, id))
# #                     sent_item_ids.add(item_id)
# #                 else:
# #                     cursor.execute("""
# #                         INSERT INTO recipe_items (recipe_id, name, rate, uom, new_uom, quantity, cost)
# #                         VALUES (%s, %s, %s, %s, %s, %s, %s)
# #                     """, (id, item["name"], item["rate"], item["uom"], item.get("new_uom"), item["quantity"], item["cost"]))

# #             to_delete = existing_item_ids - sent_item_ids
# #             if to_delete:
# #                 cursor.execute(f"DELETE FROM recipe_items WHERE id IN ({','.join(['%s']*len(to_delete))})", tuple(to_delete))

# #             cursor.execute("SELECT id FROM recipe_subrecipes WHERE recipe_id = %s", (id,))
# #             existing_links = {row[0] for row in cursor.fetchall()}
# #             sent_links = set()

# #             for sub in sub_recipes:
# #                 link_id = sub.get("link_id")
# #                 if link_id and link_id in existing_links:
# #                     cursor.execute("""
# #                         UPDATE recipe_subrecipes SET sub_recipe_id=%s, quantity=%s, uom=%s, unit=%s, costprice=%s, rate=%s, new_uom=%s
# #                         WHERE id=%s AND recipe_id=%s
# #                     """, (sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"], sub["costprice"], sub["rate"], sub.get("new_uom"), link_id, id))
# #                     sent_links.add(link_id)
# #                 else:
# #                     cursor.execute("""
# #                         INSERT INTO recipe_subrecipes (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom)
# #                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
# #                     """, (id, sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"], sub["costprice"], sub["rate"], sub.get("new_uom")))

# #             to_delete = existing_links - sent_links
# #             if to_delete:
# #                 cursor.execute(f"DELETE FROM recipe_subrecipes WHERE recipe_id = %s AND id IN ({','.join(['%s']*len(to_delete))})", (id, *to_delete))

# #             mydb.commit()
# #             message = "Recipe updated."

# #         elif request.method == "PATCH":
# #             updates = []
# #             fields = ["name", "outlet", "costprice", "sellingprice", "cost_percent", "ItemType"]
# #             for field in fields:
# #                 if field in data:
# #                     updates.append(f"{field} = %s")

# #             if updates:
# #                 values = [data[field] for field in fields if field in data]
# #                 values.append(id)
# #                 cursor.execute(f"UPDATE recipe SET {', '.join(updates)} WHERE id = %s", values)

# #             if "items" in data:
# #                 for item in data["items"]:
# #                     if "id" in item:
# #                         cursor.execute("""
# #                             UPDATE recipe_items SET name=%s, rate=%s, uom=%s, new_uom=%s, quantity=%s, cost=%s
# #                             WHERE id=%s AND recipe_id=%s
# #                         """, (item["name"], item["rate"], item["uom"], item.get("new_uom"), item["quantity"], item["cost"], item["id"], id))

# #             if "sub_recipes" in data:
# #                 for sub in data["sub_recipes"]:
# #                     if "link_id" in sub:
# #                         cursor.execute("""
# #                             UPDATE recipe_subrecipes SET sub_recipe_id=%s, quantity=%s, uom=%s, unit=%s, costprice=%s, rate=%s, new_uom=%s
# #                             WHERE id=%s AND recipe_id=%s
# #                         """, (sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"], sub["costprice"], sub["rate"], sub.get("new_uom"), sub["link_id"], id))

# #             mydb.commit()
# #             message = "Recipe partially updated."

# #         elif request.method == "DELETE":
# #             cursor.execute("DELETE FROM recipe_items WHERE recipe_id = %s", (id,))
# #             cursor.execute("DELETE FROM recipe_subrecipes WHERE recipe_id = %s", (id,))
# #             cursor.execute("DELETE FROM recipe WHERE id = %s", (id,))
# #             mydb.commit()
# #             message = "Recipe deleted."

# #         cursor.close()
# #         mydb.close()
# #         return jsonify({"message": message})

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400


# @app_file108.route("/recipe/<int:id>", methods=["GET", "PUT", "PATCH", "DELETE"])
# @cross_origin()
# def get_update_delete_recipe(id):
#     try:
#         if request.method == "GET":
#             mydb = get_db_connection()
#             cursor = mydb.cursor(dictionary=True)

#             cursor.execute("SELECT * FROM recipe WHERE id = %s", (id,))
#             recipe = cursor.fetchone()
#             if not recipe:
#                 return jsonify({"error": "Recipe not found."}), 404

#             cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (id,))
#             recipe["items"] = cursor.fetchall()

#             cursor.execute("""
#                 SELECT rs.id AS link_id, sr.id AS sub_recipe_id, sr.name, sr.outlet,
#                        rs.quantity, rs.uom, rs.unit, rs.costprice, rs.rate, rs.new_uom
#                 FROM recipe_subrecipes rs
#                 JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
#                 WHERE rs.recipe_id = %s
#             """, (id,))
#             sub_recipes = cursor.fetchall()

#             for sub_recipe in sub_recipes:
#                 cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
#                 sub_recipe["items"] = cursor.fetchall()

#             recipe["sub_recipes"] = sub_recipes

#             cursor.close()
#             mydb.close()
#             return jsonify(recipe)

#         # PUT / PATCH / DELETE below
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         mydb = get_db_connection()
#         cursor = mydb.cursor()

#         if request.method == "PUT":
#             name = data.get("name")
#             outlet = data.get("outlet")
#             cost_price = data.get("cost_price")
#             selling_price = data.get("selling_price")
#             cost_percent = data.get("cost_percent")
#             item_type = data.get("item_type")
#             items = data.get("items", [])
#             sub_recipes = data.get("sub_recipes", [])

#             if not name or not outlet or cost_price is None or selling_price is None or cost_percent is None or not item_type:
#                 return jsonify({"error": "Missing required fields."}), 400

#             cursor.execute("""
#                 UPDATE recipe SET name = %s, outlet = %s, costprice = %s, sellingprice = %s, cost_percent = %s, ItemType = %s
#                 WHERE id = %s
#             """, (name, outlet, cost_price, selling_price, cost_percent, item_type, id))

#             # Recipe Items
#             cursor.execute("SELECT id FROM recipe_items WHERE recipe_id = %s", (id,))
#             existing_item_ids = {row[0] for row in cursor.fetchall()}
#             sent_item_ids = set()

#             for item in items:
#                 item_id = item.get("id")
#                 if item_id and item_id in existing_item_ids:
#                     cursor.execute("""
#                         UPDATE recipe_items SET name=%s, rate=%s, uom=%s, new_uom=%s, unit=%s, quantity=%s, cost=%s
#                         WHERE id=%s AND recipe_id=%s
#                     """, (
#                         item["name"], item["rate"], item["uom"], item.get("new_uom"),
#                         item.get("unit", 1), item["quantity"], item["cost"], item_id, id
#                     ))
#                     sent_item_ids.add(item_id)
#                 else:
#                     cursor.execute("""
#                         INSERT INTO recipe_items (recipe_id, name, rate, uom, new_uom, unit, quantity, cost)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#                     """, (
#                         id, item["name"], item["rate"], item["uom"], item.get("new_uom"),
#                         item.get("unit", 1), item["quantity"], item["cost"]
#                     ))

#             to_delete = existing_item_ids - sent_item_ids
#             if to_delete:
#                 cursor.execute(
#                     f"DELETE FROM recipe_items WHERE id IN ({','.join(['%s']*len(to_delete))})",
#                     tuple(to_delete)
#                 )

#             # Sub Recipes
#             cursor.execute("SELECT id FROM recipe_subrecipes WHERE recipe_id = %s", (id,))
#             existing_links = {row[0] for row in cursor.fetchall()}
#             sent_links = set()

#             for sub in sub_recipes:
#                 link_id = sub.get("link_id")
#                 if link_id and link_id in existing_links:
#                     cursor.execute("""
#                         UPDATE recipe_subrecipes SET sub_recipe_id=%s, quantity=%s, uom=%s, unit=%s, costprice=%s, rate=%s, new_uom=%s
#                         WHERE id=%s AND recipe_id=%s
#                     """, (
#                         sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"],
#                         sub["costprice"], sub["rate"], sub.get("new_uom"), link_id, id
#                     ))
#                     sent_links.add(link_id)
#                 else:
#                     cursor.execute("""
#                         INSERT INTO recipe_subrecipes (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#                     """, (
#                         id, sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"],
#                         sub["costprice"], sub["rate"], sub.get("new_uom")
#                     ))

#             to_delete = existing_links - sent_links
#             if to_delete:
#                 cursor.execute(
#                     f"DELETE FROM recipe_subrecipes WHERE recipe_id = %s AND id IN ({','.join(['%s']*len(to_delete))})",
#                     (id, *to_delete)
#                 )

#             mydb.commit()
#             message = "Recipe updated."

#         elif request.method == "PATCH":
#             updates = []
#             fields = ["name", "outlet", "costprice", "sellingprice", "cost_percent", "ItemType"]
#             for field in fields:
#                 if field in data:
#                     updates.append(f"{field} = %s")

#             if updates:
#                 values = [data[field] for field in fields if field in data]
#                 values.append(id)
#                 cursor.execute(f"UPDATE recipe SET {', '.join(updates)} WHERE id = %s", values)

#             if "items" in data:
#                 for item in data["items"]:
#                     if "id" in item:
#                         cursor.execute("""
#                             UPDATE recipe_items SET name=%s, rate=%s, uom=%s, new_uom=%s, unit=%s, quantity=%s, cost=%s
#                             WHERE id=%s AND recipe_id=%s
#                         """, (
#                             item["name"], item["rate"], item["uom"], item.get("new_uom"),
#                             item.get("unit", 1), item["quantity"], item["cost"], item["id"], id
#                         ))

#             if "sub_recipes" in data:
#                 for sub in data["sub_recipes"]:
#                     if "link_id" in sub:
#                         cursor.execute("""
#                             UPDATE recipe_subrecipes SET sub_recipe_id=%s, quantity=%s, uom=%s, unit=%s, costprice=%s, rate=%s, new_uom=%s
#                             WHERE id=%s AND recipe_id=%s
#                         """, (
#                             sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"],
#                             sub["costprice"], sub["rate"], sub.get("new_uom"), sub["link_id"], id
#                         ))

#             mydb.commit()
#             message = "Recipe partially updated."

#         elif request.method == "DELETE":
#             cursor.execute("DELETE FROM recipe_items WHERE recipe_id = %s", (id,))
#             cursor.execute("DELETE FROM recipe_subrecipes WHERE recipe_id = %s", (id,))
#             cursor.execute("DELETE FROM recipe WHERE id = %s", (id,))
#             mydb.commit()
#             message = "Recipe deleted."

#         cursor.close()
#         mydb.close()
#         return jsonify({"message": message})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400


# @app_file108.route("/recipes", methods=["GET"])
# @cross_origin()
# def get_all_recipes():
#     try:
#         outlet_filter = request.args.get("outlet")  # Get ?outlet=Kathmandu Outlet from URL

#         mydb = get_db_connection()
#         cursor = mydb.cursor(dictionary=True)

#         # Base query
#         if outlet_filter:
#             cursor.execute("SELECT * FROM recipe WHERE outlet = %s", (outlet_filter,))
#         else:
#             cursor.execute("SELECT * FROM recipe")
#         recipes = cursor.fetchall()

#         for recipe in recipes:
#             # Include ItemType (already fetched with main recipe record)
#             # Get recipe items
#             cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (recipe["id"],))
#             recipe["items"] = cursor.fetchall()

#             # Get sub-recipes linked to this recipe along with all fields
#             cursor.execute("""
#                 SELECT sr.id AS sub_recipe_id, sr.name, sr.outlet,
#                        rs.quantity, rs.uom, rs.unit, rs.costprice, rs.rate, rs.new_uom
#                 FROM recipe_subrecipes rs
#                 JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
#                 WHERE rs.recipe_id = %s
#             """, (recipe["id"],))
#             sub_recipes = cursor.fetchall()

#             # For each sub_recipe, get its items
#             for sub_recipe in sub_recipes:
#                 cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
#                 sub_recipe["items"] = cursor.fetchall()

#             recipe["sub_recipes"] = sub_recipes

#         cursor.close()
#         mydb.close()
#         return jsonify(recipes)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app_file108.route("/recipes", methods=["POST"])
# @cross_origin()
# def get_filtered_recipes_by_name():
#     try:
#         data = request.get_json()
#         item_name = data.get("item_name")
#         outlet_filter = data.get("outlet")

#         if not item_name:
#             return jsonify({"error": "Missing item_name in request body"}), 400

#         mydb = get_db_connection()
#         cursor = mydb.cursor(dictionary=True)

#         # Dynamic query construction with ItemType already selected
#         query = "SELECT * FROM recipe WHERE name LIKE %s"
#         values = [f"%{item_name}%"]

#         if outlet_filter:
#             query += " AND outlet = %s"
#             values.append(outlet_filter)

#         cursor.execute(query, tuple(values))
#         recipes = cursor.fetchall()

#         for recipe in recipes:
#             # Include ItemType (already fetched in base query)

#             # Get recipe items
#             cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (recipe["id"],))
#             recipe["items"] = cursor.fetchall()

#             # Get linked sub-recipes
#             cursor.execute("""
#                 SELECT 
#                     rs.id AS link_id,
#                     sr.id AS sub_recipe_id,
#                     sr.name,
#                     sr.outlet,
#                     rs.quantity,
#                     rs.uom,
#                     rs.new_uom,
#                     rs.unit,
#                     rs.costprice,
#                     rs.rate
#                 FROM recipe_subrecipes rs
#                 JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
#                 WHERE rs.recipe_id = %s
#             """, (recipe["id"],))
#             sub_recipes = cursor.fetchall()

#             for sub_recipe in sub_recipes:
#                 cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
#                 sub_recipe["items"] = cursor.fetchall()

#             recipe["sub_recipes"] = sub_recipes

#         cursor.close()
#         mydb.close()
#         return jsonify(recipes)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth

load_dotenv()

app_file108 = Blueprint('app_file108', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )

# @app_file108.route("/recipe", methods=["POST"])
# @cross_origin()
# def create_recipe():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         name = data.get("name")
#         outlet = data.get("outlet")
#         cost_price = data.get("cost_price")
#         selling_price = data.get("selling_price")
#         cost_percent = data.get("cost_percent")
#         item_type = data.get("item_type")
#         items = data.get("items", [])
#         sub_recipes = data.get("sub_recipes", [])

#         if (
#             not name or
#             not outlet or
#             cost_price is None or
#             selling_price is None or
#             cost_percent is None or
#             not item_type or
#             not isinstance(items, list) or
#             not isinstance(sub_recipes, list)
#         ):
#             return jsonify({"error": "Missing fields or invalid format for items, sub_recipes, or cost fields"}), 400

#         mydb = get_db_connection()
#         cursor = mydb.cursor()

#         # Insert main recipe
#         cursor.execute(
#             """
#             INSERT INTO recipe (name, outlet, costprice, sellingprice, cost_percent, ItemType)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """,
#             (name, outlet, cost_price, selling_price, cost_percent, item_type)
#         )
#         recipe_id = cursor.lastrowid

#         # Insert recipe items with 'unit'
#         for item in items:
#             item_name = item.get("name")
#             rate = item.get("rate")
#             uom = item.get("uom")
#             new_uom = item.get("new_uom")
#             quantity = item.get("quantity")
#             cost = item.get("cost")
#             unit = item.get("unit", 1)  # default to 1 if not provided

#             if not all([item_name, rate, uom, quantity, cost]):
#                 continue

#             cursor.execute("""
#                 INSERT INTO recipe_items (recipe_id, name, rate, uom, new_uom, unit, quantity, cost)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """, (recipe_id, item_name, rate, uom, new_uom, unit, quantity, cost))

#         # Insert sub-recipes
#         for sr in sub_recipes:
#             sub_recipe_id = sr.get("sub_recipe_id")
#             quantity = sr.get("quantity", 0)
#             uom = sr.get("uom")
#             unit = sr.get("unit")
#             new_uom = sr.get("new_uom")
#             costprice = sr.get("costprice")
#             rate = sr.get("rate")

#             if not sub_recipe_id:
#                 continue

#             cursor.execute("""
#                 INSERT INTO recipe_subrecipes (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """, (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom))

#         mydb.commit()
#         cursor.close()
#         mydb.close()

#         return jsonify({"message": "Recipe created successfully with sub-recipes."}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

@app_file108.route("/recipe", methods=["POST"])
@cross_origin()
def create_recipe():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        name = data.get("name")
        outlet = data.get("outlet")
        cost_price = data.get("cost_price")
        selling_price = data.get("selling_price")
        cost_percent = data.get("cost_percent")
        item_type = data.get("item_type")
        items = data.get("items", [])
        sub_recipes = data.get("sub_recipes", [])

        if (
            not name or
            not outlet or
            cost_price is None or
            selling_price is None or
            cost_percent is None or
            not item_type or
            not isinstance(items, list) or
            not isinstance(sub_recipes, list)
        ):
            return jsonify({"error": "Missing fields or invalid format for items, sub_recipes, or cost fields"}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor()

        # Check if recipe already exists
        cursor.execute(
            "SELECT id FROM recipe WHERE name = %s AND outlet = %s",
            (name, outlet)
        )
        existing_recipe = cursor.fetchone()

        # If recipe exists, delete it (and its related items/sub-recipes)
        if existing_recipe:
            recipe_id_to_delete = existing_recipe[0]
            
            # Delete related items
            cursor.execute(
                "DELETE FROM recipe_items WHERE recipe_id = %s",
                (recipe_id_to_delete,)
            )
            
            # Delete related sub-recipes
            cursor.execute(
                "DELETE FROM recipe_subrecipes WHERE recipe_id = %s",
                (recipe_id_to_delete,)
            )
            
            # Finally, delete the recipe itself
            cursor.execute(
                "DELETE FROM recipe WHERE id = %s",
                (recipe_id_to_delete,)
            )
            mydb.commit()  # Commit deletions before proceeding

        # Insert new recipe (same as before)
        cursor.execute(
            """
            INSERT INTO recipe (name, outlet, costprice, sellingprice, cost_percent, ItemType)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, outlet, cost_price, selling_price, cost_percent, item_type)
        )
        new_recipe_id = cursor.lastrowid

        # Insert recipe items
        for item in items:
            item_name = item.get("name")
            rate = item.get("rate")
            uom = item.get("uom")
            new_uom = item.get("new_uom")
            quantity = item.get("quantity")
            cost = item.get("cost")
            unit = item.get("unit", 1)

            if not all([item_name, rate, uom, quantity, cost]):
                continue

            cursor.execute("""
                INSERT INTO recipe_items (recipe_id, name, rate, uom, new_uom, unit, quantity, cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_recipe_id, item_name, rate, uom, new_uom, unit, quantity, cost))

        # Insert sub-recipes
        for sr in sub_recipes:
            sub_recipe_id = sr.get("sub_recipe_id")
            quantity = sr.get("quantity", 0)
            uom = sr.get("uom")
            unit = sr.get("unit")
            new_uom = sr.get("new_uom")
            costprice = sr.get("costprice")
            rate = sr.get("rate")

            if not sub_recipe_id:
                continue

            cursor.execute("""
                INSERT INTO recipe_subrecipes (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom))

        mydb.commit()
        cursor.close()
        mydb.close()

        return jsonify({"message": "Recipe created successfully with sub-recipes."}), 201

    except Exception as e:
        mydb.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 400


@app_file108.route("/recipe/<int:id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@cross_origin()
def get_update_delete_recipe(id):
    try:
        if request.method == "GET":
            mydb = get_db_connection()
            cursor = mydb.cursor(dictionary=True)

            cursor.execute("SELECT * FROM recipe WHERE id = %s", (id,))
            recipe = cursor.fetchone()
            if not recipe:
                return jsonify({"error": "Recipe not found."}), 404

            cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (id,))
            recipe["items"] = cursor.fetchall()

            cursor.execute("""
                SELECT rs.id AS link_id, sr.id AS sub_recipe_id, sr.name, sr.outlet,
                       rs.quantity, rs.uom, rs.unit, rs.costprice, rs.rate, rs.new_uom
                FROM recipe_subrecipes rs
                JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
                WHERE rs.recipe_id = %s
            """, (id,))
            sub_recipes = cursor.fetchall()

            for sub_recipe in sub_recipes:
                cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
                sub_recipe["items"] = cursor.fetchall()

            recipe["sub_recipes"] = sub_recipes

            cursor.close()
            mydb.close()
            return jsonify(recipe)

        # PUT / PATCH / DELETE below
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor()

        if request.method == "PUT":
            name = data.get("name")
            outlet = data.get("outlet")
            cost_price = data.get("cost_price")
            selling_price = data.get("selling_price")
            cost_percent = data.get("cost_percent")
            item_type = data.get("item_type")
            items = data.get("items", [])
            sub_recipes = data.get("sub_recipes", [])

            if not name or not outlet or cost_price is None or selling_price is None or cost_percent is None or not item_type:
                return jsonify({"error": "Missing required fields."}), 400

            cursor.execute("""
                UPDATE recipe SET name = %s, outlet = %s, costprice = %s, sellingprice = %s, cost_percent = %s, ItemType = %s
                WHERE id = %s
            """, (name, outlet, cost_price, selling_price, cost_percent, item_type, id))

            # Recipe Items
            cursor.execute("SELECT id FROM recipe_items WHERE recipe_id = %s", (id,))
            existing_item_ids = {row[0] for row in cursor.fetchall()}
            sent_item_ids = set()

            for item in items:
                item_id = item.get("id")
                if item_id and item_id in existing_item_ids:
                    cursor.execute("""
                        UPDATE recipe_items SET name=%s, rate=%s, uom=%s, new_uom=%s, unit=%s, quantity=%s, cost=%s
                        WHERE id=%s AND recipe_id=%s
                    """, (
                        item["name"], item["rate"], item["uom"], item.get("new_uom"),
                        item.get("unit", 1), item["quantity"], item["cost"], item_id, id
                    ))
                    sent_item_ids.add(item_id)
                else:
                    cursor.execute("""
                        INSERT INTO recipe_items (recipe_id, name, rate, uom, new_uom, unit, quantity, cost)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id, item["name"], item["rate"], item["uom"], item.get("new_uom"),
                        item.get("unit", 1), item["quantity"], item["cost"]
                    ))

            to_delete = existing_item_ids - sent_item_ids
            if to_delete:
                cursor.execute(
                    f"DELETE FROM recipe_items WHERE id IN ({','.join(['%s']*len(to_delete))})",
                    tuple(to_delete)
                )

            # Sub Recipes
            cursor.execute("SELECT id FROM recipe_subrecipes WHERE recipe_id = %s", (id,))
            existing_links = {row[0] for row in cursor.fetchall()}
            sent_links = set()

            for sub in sub_recipes:
                link_id = sub.get("link_id")
                if link_id and link_id in existing_links:
                    cursor.execute("""
                        UPDATE recipe_subrecipes SET sub_recipe_id=%s, quantity=%s, uom=%s, unit=%s, costprice=%s, rate=%s, new_uom=%s
                        WHERE id=%s AND recipe_id=%s
                    """, (
                        sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"],
                        sub["costprice"], sub["rate"], sub.get("new_uom"), link_id, id
                    ))
                    sent_links.add(link_id)
                else:
                    cursor.execute("""
                        INSERT INTO recipe_subrecipes (recipe_id, sub_recipe_id, quantity, uom, unit, costprice, rate, new_uom)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id, sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"],
                        sub["costprice"], sub["rate"], sub.get("new_uom")
                    ))

            to_delete = existing_links - sent_links
            if to_delete:
                cursor.execute(
                    f"DELETE FROM recipe_subrecipes WHERE recipe_id = %s AND id IN ({','.join(['%s']*len(to_delete))})",
                    (id, *to_delete)
                )

            mydb.commit()
            message = "Recipe updated."

        elif request.method == "PATCH":
            updates = []
            fields = ["name", "outlet", "costprice", "sellingprice", "cost_percent", "ItemType"]
            for field in fields:
                if field in data:
                    updates.append(f"{field} = %s")

            if updates:
                values = [data[field] for field in fields if field in data]
                values.append(id)
                cursor.execute(f"UPDATE recipe SET {', '.join(updates)} WHERE id = %s", values)

            if "items" in data:
                for item in data["items"]:
                    if "id" in item:
                        cursor.execute("""
                            UPDATE recipe_items SET name=%s, rate=%s, uom=%s, new_uom=%s, unit=%s, quantity=%s, cost=%s
                            WHERE id=%s AND recipe_id=%s
                        """, (
                            item["name"], item["rate"], item["uom"], item.get("new_uom"),
                            item.get("unit", 1), item["quantity"], item["cost"], item["id"], id
                        ))

            if "sub_recipes" in data:
                for sub in data["sub_recipes"]:
                    if "link_id" in sub:
                        cursor.execute("""
                            UPDATE recipe_subrecipes SET sub_recipe_id=%s, quantity=%s, uom=%s, unit=%s, costprice=%s, rate=%s, new_uom=%s
                            WHERE id=%s AND recipe_id=%s
                        """, (
                            sub["sub_recipe_id"], sub["quantity"], sub["uom"], sub["unit"],
                            sub["costprice"], sub["rate"], sub.get("new_uom"), sub["link_id"], id
                        ))

            mydb.commit()
            message = "Recipe partially updated."

        elif request.method == "DELETE":
            cursor.execute("DELETE FROM recipe_items WHERE recipe_id = %s", (id,))
            cursor.execute("DELETE FROM recipe_subrecipes WHERE recipe_id = %s", (id,))
            cursor.execute("DELETE FROM recipe WHERE id = %s", (id,))
            mydb.commit()
            message = "Recipe deleted."

        cursor.close()
        mydb.close()
        return jsonify({"message": message})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file108.route("/recipes", methods=["GET"])
@cross_origin()
def get_all_recipes():
    try:
        outlet_filter = request.args.get("outlet")  # Get ?outlet=Kathmandu Outlet from URL

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True)

        # Base query
        if outlet_filter:
            cursor.execute("SELECT * FROM recipe WHERE outlet = %s", (outlet_filter,))
        else:
            cursor.execute("SELECT * FROM recipe")
        recipes = cursor.fetchall()

        for recipe in recipes:
            # Include ItemType (already fetched with main recipe record)
            # Get recipe items
            cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (recipe["id"],))
            recipe["items"] = cursor.fetchall()

            # Get sub-recipes linked to this recipe along with all fields
            cursor.execute("""
                SELECT sr.id AS sub_recipe_id, sr.name, sr.outlet,
                       rs.quantity, rs.uom, rs.unit, rs.costprice, rs.rate, rs.new_uom
                FROM recipe_subrecipes rs
                JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
                WHERE rs.recipe_id = %s
            """, (recipe["id"],))
            sub_recipes = cursor.fetchall()

            # For each sub_recipe, get its items
            for sub_recipe in sub_recipes:
                cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
                sub_recipe["items"] = cursor.fetchall()

            recipe["sub_recipes"] = sub_recipes

        cursor.close()
        mydb.close()
        return jsonify(recipes)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app_file108.route("/recipes", methods=["POST"])
@cross_origin()
def get_filtered_recipes_by_name():
    try:
        data = request.get_json()
        item_name = data.get("item_name")
        outlet_filter = data.get("outlet")

        if not item_name:
            return jsonify({"error": "Missing item_name in request body"}), 400

        mydb = get_db_connection()
        cursor = mydb.cursor(dictionary=True)

        # Dynamic query construction with ItemType already selected
        query = "SELECT * FROM recipe WHERE name LIKE %s"
        values = [f"%{item_name}%"]

        if outlet_filter:
            query += " AND outlet = %s"
            values.append(outlet_filter)

        cursor.execute(query, tuple(values))
        recipes = cursor.fetchall()

        for recipe in recipes:
            # Include ItemType (already fetched in base query)

            # Get recipe items
            cursor.execute("SELECT * FROM recipe_items WHERE recipe_id = %s", (recipe["id"],))
            recipe["items"] = cursor.fetchall()

            # Get linked sub-recipes
            cursor.execute("""
                SELECT 
                    rs.id AS link_id,
                    sr.id AS sub_recipe_id,
                    sr.name,
                    sr.outlet,
                    rs.quantity,
                    rs.uom,
                    rs.new_uom,
                    rs.unit,
                    rs.costprice,
                    rs.rate
                FROM recipe_subrecipes rs
                JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
                WHERE rs.recipe_id = %s
            """, (recipe["id"],))
            sub_recipes = cursor.fetchall()

            for sub_recipe in sub_recipes:
                cursor.execute("SELECT * FROM sub_recipe_items WHERE sub_recipe_id = %s", (sub_recipe["sub_recipe_id"],))
                sub_recipe["items"] = cursor.fetchall()

            recipe["sub_recipes"] = sub_recipes

        cursor.close()
        mydb.close()
        return jsonify(recipes)

    except Exception as e:
        return jsonify({"error": str(e)}), 400