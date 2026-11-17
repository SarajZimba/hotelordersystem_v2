# from flask import Blueprint, jsonify, request
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from flask_cors import cross_origin
# from root.auth.check import token_auth
# from decimal import Decimal, ROUND_HALF_UP
# import re

# load_dotenv()

# app_file110 = Blueprint('app_file110', __name__)

# # Define standard UOMs
# STANDARD_UOMS = {
#     'kg', 'kilogram', 'kilograms',
#     'g', 'gram', 'grams', 'gms', 'gm', 'grm',
#     'ounce', 'ounces', 'oz',
#     'litre', 'litres', 'liter', 'liters', 'l', 'ltr',
#     'ml', 'millilitre', 'millilitres', 'milliliter', 'milliliters',
#     'lb', 'pound', 'pounds',
#     'mg', 'milligram', 'milligrams'
# }

# def is_standard_uom(uom):
#     """Check if UOM is a standard unit"""
#     if not uom:
#         return False
#     uom_lower = str(uom).lower().strip()
#     return uom_lower in STANDARD_UOMS

# def get_db_connection():
#     return mysql.connector.connect(
#         host=os.getenv("host"),
#         user=os.getenv("user"),
#         password=os.getenv("password"),
#         database=os.getenv("database")
#     )

# @app_file110.route("/menu-consumption", methods=["POST"])
# @cross_origin()
# def menu_consumption():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         start_date = data.get("startDate")
#         end_date = data.get("endDate")
#         outlet = data.get("outlet")
#         include_sub_recipe_items = data.get("includeSubRecipeItems", True)

#         if not start_date or not end_date or not outlet:
#             return jsonify({"error": "Missing startDate, endDate, or outlet."}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         cursor.execute("SELECT use_same_recipe FROM master_featured ORDER BY id DESC LIMIT 1")
#         flag_row = cursor.fetchone()
#         use_same_recipe = flag_row["use_same_recipe"] if flag_row else 0

#         # First get all item types from recipe table for this outlet
#         cursor.execute("SELECT DISTINCT ItemType FROM tblorder_detailshistory")
#         item_types = [row["ItemType"] for row in cursor.fetchall()]

#         result = {}
#         grand_total_items_sold = 0
#         grand_unique_items_sold = 0
#         grand_total_menu_items = 0
#         type_wise_consumption = {}
#         all_consumed_items = {}
#         inappropriate_uom_items = []  # Track items with inappropriate UOMs

#         for item_type in item_types:
#             type_wise_consumption[item_type] = {}

#             if use_same_recipe == 1:
#                 cursor.execute(
#                     "SELECT COUNT(DISTINCT name) AS total_menu_items FROM recipe WHERE ItemType = %s",
#                     (item_type,)
#                 )
#             else:
#                 cursor.execute(
#                     "SELECT COUNT(*) AS total_menu_items FROM recipe WHERE outlet = %s AND ItemType = %s",
#                     (outlet, item_type)
#                 )
#             total_menu_item = cursor.fetchone()["total_menu_items"]
#             grand_total_menu_items += total_menu_item

#             # Get all sold items of this type from order history
#             cursor.execute("""
#                 SELECT 
#                     d.ItemName,
#                     SUM(d.count) AS total_sold
#                 FROM tblorder_detailshistory d
#                 JOIN tblorderhistory o ON o.idtblorderHistory = d.order_ID
#                 WHERE o.Date BETWEEN %s AND %s
#                   AND o.Outlet_Name = %s
#                   AND d.ItemType = %s
#                 GROUP BY d.ItemName
#             """, (start_date, end_date, outlet, item_type))

#             sold_items = cursor.fetchall()
#             itemwise = []

#             total_sold = 0
#             unique_items_sold = 0

#             for sold_item in sold_items:
#                 item_name = sold_item["ItemName"]
#                 quantity_sold = sold_item["total_sold"]
#                 total_sold += quantity_sold
#                 if quantity_sold > 0:
#                     unique_items_sold += 1

#                 if use_same_recipe == 1:
#                     cursor.execute("""
#                         SELECT id, sellingprice, costprice 
#                         FROM recipe 
#                         WHERE name = %s AND ItemType = %s
#                         LIMIT 1
#                     """, (item_name, item_type))
#                 else:
#                     cursor.execute("""
#                         SELECT id, sellingprice, costprice 
#                         FROM recipe 
#                         WHERE outlet = %s AND name = %s AND ItemType = %s
#                     """, (outlet, item_name, item_type))
#                 recipe_info = cursor.fetchone()

#                 item_data = {
#                     "ItemName": item_name,
#                     "ItemType": item_type,
#                     "total_sold": quantity_sold,
#                     "has_recipe": bool(recipe_info)
#                 }

#                 if recipe_info:
#                     item_data["recipe_id"] = recipe_info["id"]
#                     recipe_id = recipe_info["id"]

#                     # Get recipe items and calculate consumption
#                     cursor.execute("SELECT name, quantity, uom, new_uom FROM recipe_items WHERE recipe_id = %s", (recipe_id,))
#                     recipe_items = cursor.fetchall()
#                     for ri in recipe_items:
#                         ingredient_name = ri["name"]
#                         total_consumed = float(ri["quantity"]) * float(quantity_sold)
#                         uom = ri["uom"]
#                         new_uom = ri["new_uom"]
                        
#                         # Check if UOM is standard
#                         is_standard = is_standard_uom(uom)
#                         if not is_standard:
#                             inappropriate_uom_items.append({
#                                 "item_name": ingredient_name,
#                                 "uom": uom,
#                                 "source": "recipe_items",
#                                 "recipe": item_name,
#                                 "item_type": item_type
#                             })

#                         # Type-wise consumption
#                         if ingredient_name not in type_wise_consumption[item_type]:
#                             type_wise_consumption[item_type][ingredient_name] = {
#                                 "total_quantity": 0, 
#                                 "uom": uom, 
#                                 "new_uom": new_uom,
#                                 "is_standard_uom": is_standard  # Add flag
#                             }
#                         type_wise_consumption[item_type][ingredient_name]["total_quantity"] += total_consumed
#                         type_wise_consumption[item_type][ingredient_name]["is_standard_uom"] = type_wise_consumption[item_type][ingredient_name].get("is_standard_uom", True) and is_standard

#                         # Global consumption
#                         if ingredient_name not in all_consumed_items:
#                             all_consumed_items[ingredient_name] = {
#                                 "total_quantity": 0, 
#                                 "uom": uom, 
#                                 "new_uom": new_uom,
#                                 "is_standard_uom": is_standard  # Add flag
#                             }
#                         all_consumed_items[ingredient_name]["total_quantity"] += total_consumed
#                         # Update flag if any occurrence is non-standard
#                         if not is_standard:
#                             all_consumed_items[ingredient_name]["is_standard_uom"] = False

#                     # Handle sub-recipes
#                     cursor.execute("""
#                         SELECT rs.sub_recipe_id as sub_id, rs.quantity AS sr_qty, s.name AS sub_name, s.uom, s.unit, s.id, rs.new_uom AS new_uom
#                         FROM recipe_subrecipes rs
#                         JOIN sub_recipe s ON rs.sub_recipe_id = s.id
#                         WHERE rs.recipe_id = %s
#                     """, (recipe_id,))
#                     sub_recipes = cursor.fetchall()

#                     for sr in sub_recipes:
#                         if include_sub_recipe_items:
#                             cursor.execute("SELECT name, quantity, uom, new_uom FROM sub_recipe_items WHERE sub_recipe_id = %s", (sr["sub_id"],))
#                             sub_recipe_items = cursor.fetchall()
#                             for sri in sub_recipe_items:
#                                 ingredient_name = sri["name"]
#                                 total_consumed = float(sri["quantity"]) * float(sr["sr_qty"]) * float(quantity_sold)
#                                 uom = sri["uom"]
#                                 new_uom = sri["new_uom"]
                                
#                                 # Check if UOM is standard
#                                 is_standard = is_standard_uom(uom)
#                                 if not is_standard:
#                                     inappropriate_uom_items.append({
#                                         "item_name": ingredient_name,
#                                         "uom": uom,
#                                         "source": "sub_recipe_items",
#                                         "sub_recipe": sr["sub_name"],
#                                         "recipe": item_name,
#                                         "item_type": item_type
#                                     })

#                                 # Type-wise consumption
#                                 if ingredient_name not in type_wise_consumption[item_type]:
#                                     type_wise_consumption[item_type][ingredient_name] = {
#                                         "total_quantity": 0, 
#                                         "uom": uom, 
#                                         "new_uom": new_uom,
#                                         "is_standard_uom": is_standard
#                                     }
#                                 type_wise_consumption[item_type][ingredient_name]["total_quantity"] += total_consumed
#                                 if not is_standard:
#                                     type_wise_consumption[item_type][ingredient_name]["is_standard_uom"] = False

#                                 # Global consumption
#                                 if ingredient_name not in all_consumed_items:
#                                     all_consumed_items[ingredient_name] = {
#                                         "total_quantity": 0, 
#                                         "uom": uom, 
#                                         "new_uom": new_uom,
#                                         "is_standard_uom": is_standard
#                                     }
#                                 all_consumed_items[ingredient_name]["total_quantity"] += total_consumed
#                                 if not is_standard:
#                                     all_consumed_items[ingredient_name]["is_standard_uom"] = False
#                         else:
#                             sub_recipe_name = sr["sub_name"]
#                             total_consumed = float(sr["sr_qty"]) * float(quantity_sold)
#                             uom = sr["uom"]
#                             new_uom = sr.get("new_uom", "")
                            
#                             # Check if UOM is standard
#                             is_standard = is_standard_uom(uom)
#                             if not is_standard:
#                                 inappropriate_uom_items.append({
#                                     "item_name": sub_recipe_name,
#                                     "uom": uom,
#                                     "source": "sub_recipe",
#                                     "recipe": item_name,
#                                     "item_type": item_type
#                                 })

#                             if sub_recipe_name not in type_wise_consumption[item_type]:
#                                 type_wise_consumption[item_type][sub_recipe_name] = {
#                                     "total_quantity": 0,
#                                     "uom": uom,
#                                     "new_uom": new_uom,
#                                     "is_sub_recipe": True,
#                                     "is_standard_uom": is_standard
#                                 }
#                             type_wise_consumption[item_type][sub_recipe_name]["total_quantity"] += total_consumed
#                             if not is_standard:
#                                 type_wise_consumption[item_type][sub_recipe_name]["is_standard_uom"] = False

#                             if sub_recipe_name not in all_consumed_items:
#                                 all_consumed_items[sub_recipe_name] = {
#                                     "total_quantity": 0,
#                                     "uom": uom,
#                                     "new_uom": new_uom,
#                                     "is_standard_uom": is_standard
#                                 }
#                             all_consumed_items[sub_recipe_name]["total_quantity"] += total_consumed
#                             if not is_standard:
#                                 all_consumed_items[sub_recipe_name]["is_standard_uom"] = False

#                 itemwise.append(item_data)

#             grand_total_items_sold += total_sold
#             grand_unique_items_sold += unique_items_sold

#             result[item_type] = {
#                 "itemwise_summary": itemwise,
#                 "total_items_sold": total_sold,
#                 "unique_items_sold": unique_items_sold,
#                 "total_menu_items": total_menu_item,
#             }

#         # Round the quantities
#         for item_type, ingredients in type_wise_consumption.items():
#             for ingredient in ingredients.values():
#                 ingredient["total_quantity"] = float(Decimal(ingredient["total_quantity"]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

#         nested_consumed_group = {}
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT ItemName, GroupName, Type FROM stock_statement")
#         stock_info_lookup = {
#             row["ItemName"]: {
#                 "GroupName": row["GroupName"] or "Group Not Found",
#                 "Type": row["Type"] or "Type Not Found"
#             }
#             for row in cursor.fetchall()
#         }
#         cursor.close()

#         for name, info in all_consumed_items.items():
#             total_quantity = float(Decimal(info["total_quantity"]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
#             uom = info.get("uom")
#             new_uom = info.get("new_uom")
#             is_standard_uom_flag = info.get("is_standard_uom", False)

#             stock_info = stock_info_lookup.get(name, {"GroupName": "Group Not Found", "Type": "Type Not Found"})
#             group_name = stock_info["GroupName"]
#             item_type = stock_info["Type"]

#             if item_type not in nested_consumed_group:
#                 nested_consumed_group[item_type] = {}

#             if group_name not in nested_consumed_group[item_type]:
#                 nested_consumed_group[item_type][group_name] = []

#             nested_consumed_group[item_type][group_name].append({
#                 "name": name,
#                 "uom": uom,
#                 "new_uom": new_uom,
#                 "total_quantity": total_quantity,
#                 "is_standard_uom": is_standard_uom_flag  # Add flag to final output
#             })

#         cursor.close()
#         conn.close()
        
#         # Prepare warning summary
#         inappropriate_uom_summary = {
#             "has_inappropriate_uoms": len(inappropriate_uom_items) > 0,
#             "total_inappropriate_items": len(inappropriate_uom_items),
#             "inappropriate_items": inappropriate_uom_items
#         }
        
#         return jsonify({
#             "grouped_by_item_type": result,
#             "grand_total_items_sold": grand_total_items_sold,
#             "grand_unique_items_sold": grand_unique_items_sold,
#             "grand_total_menu_items": grand_total_menu_items,
#             "type_wise_consumption": type_wise_consumption,
#             "all_consumed_items": nested_consumed_group,
#             "uom_validation": inappropriate_uom_summary  # Add UOM validation summary
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400


from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth
from decimal import Decimal, ROUND_HALF_UP
import re

load_dotenv()

app_file110 = Blueprint('app_file110', __name__)

# Define standard UOMs
STANDARD_UOMS = {
    'kg', 'kilogram', 'kilograms',
    'g', 'gram', 'grams', 'gms', 'gm', 'grm', 'grms',
    'ounce', 'ounces', 'oz',
    'litre', 'litres', 'liter', 'liters', 'l', 'ltr',
    'ml', 'millilitre', 'millilitres', 'milliliter', 'milliliters',
    'lb', 'pound', 'pounds',
    'mg', 'milligram', 'milligrams'
}

UOM_FAMILY_MAP = {
    # mass
    'kg': 'mass', 'kilogram': 'mass', 'kilograms': 'mass',
    'g': 'mass', 'gram': 'mass', 'grams': 'mass',
    'gms': 'mass', 'gm': 'mass', 'grm': 'mass', 'grms': 'mass',
    'mg': 'mass', 'milligram': 'mass', 'milligrams': 'mass',
    'lb': 'mass', 'pound': 'mass', 'pounds': 'mass',
    'oz': 'mass', 'ounce': 'mass', 'ounces': 'mass',

    # volume
    'l': 'volume', 'litre': 'volume', 'litres': 'volume',
    'liter': 'volume', 'liters': 'volume', 'ltr': 'volume',
    'ml': 'volume', 'millilitre': 'volume', 'millilitres': 'volume',
    'milliliter': 'volume', 'milliliters': 'volume',
}


def normalize_uom(uom):
    return str(uom).strip().lower() if uom else None


def get_uom_family(uom):
    """
    Returns the conversion family for a uom (e.g. 'kg' and 'g' both
    return 'mass'). If the uom isn't in a known conversion family
    (e.g. 'pcs', 'box', 'nos'), falls back to the normalized string
    itself -- so exact spelling matches still count as consistent,
    but different arbitrary units (pcs vs box) won't.
    """
    normalized = normalize_uom(uom)
    if not normalized:
        return None
    return UOM_FAMILY_MAP.get(normalized, normalized)

# def is_standard_uom(uom):
#     """Check if UOM is a standard unit"""
#     if not uom:
#         return False
#     uom_lower = str(uom).lower().strip()
#     return uom_lower in STANDARD_UOMS


def is_standard_uom(recipe_uom, ingredient_name, unitdef_lookup, stock_info_lookup):
    """
    True only if the recipe/sub-recipe uom, tblunitdefinition.uom, and
    stock_statement.secondary_unit all belong to the same unit family
    (e.g. kg/g -> both 'mass' -> True; pcs/pcs/pcs -> exact match -> True;
    pcs/pcs/g -> different families -> False).
    Requires both reference values (unitdef uom and secondary_unit) to
    exist -- if either is missing, we can't confirm convertibility, so
    it's treated as False rather than assumed True.
    """
    recipe_family = get_uom_family(recipe_uom)
    if not recipe_family:
        return False

    unit_def = unitdef_lookup.get(ingredient_name)
    stock_info = stock_info_lookup.get(ingredient_name)

    unitdef_uom = unit_def["uom"] if unit_def else None
    secondary_unit = stock_info["secondary_unit"] if stock_info else None

    if not unitdef_uom or not secondary_unit:
        return False

    unitdef_family = get_uom_family(unitdef_uom)
    secondary_family = get_uom_family(secondary_unit)

    return recipe_family == unitdef_family == secondary_family

MASS_UOM_BASE = {
    'kg': 1000, 'kilogram': 1000, 'kilograms': 1000,
    'g': 1, 'gram': 1, 'grams': 1, 'gms': 1, 'gm': 1, 'grm': 1, 'grms': 1,
    'mg': 0.001, 'milligram': 0.001, 'milligrams': 0.001,
    'lb': 453.592, 'pound': 453.592, 'pounds': 453.592,
    'oz': 28.3495, 'ounce': 28.3495, 'ounces': 28.3495,
}

VOLUME_UOM_BASE = {
    'l': 1000, 'litre': 1000, 'litres': 1000, 'liter': 1000, 'liters': 1000, 'ltr': 1000,
    'ml': 1, 'millilitre': 1, 'millilitres': 1, 'milliliter': 1, 'milliliters': 1,
}

def _norm_uom(uom):
    return uom.strip().lower() if uom else ""

def _uom_category_and_base(uom):
    u = _norm_uom(uom)
    if u in MASS_UOM_BASE:
        return "mass", MASS_UOM_BASE[u]
    if u in VOLUME_UOM_BASE:
        return "volume", VOLUME_UOM_BASE[u]
    return None, None

def convert_to_secondary_unit(quantity, from_uom, to_uom):
    """Converts quantity from from_uom to to_uom if both are recognized
    and in the same category (mass or volume). Returns (value, is_valid)."""
    if not to_uom:
        return quantity, False

    from_cat, from_base = _uom_category_and_base(from_uom)
    to_cat, to_base = _uom_category_and_base(to_uom)

    if from_cat is None or to_cat is None or from_cat != to_cat:
        return quantity, False

    return quantity * (from_base / to_base), True


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )


@app_file110.route("/menu-consumption", methods=["POST"])
@cross_origin()
def menu_consumption():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        start_date = data.get("startDate")
        end_date = data.get("endDate")
        outlet = data.get("outlet")
        include_sub_recipe_items = data.get("includeSubRecipeItems", True)

        if not start_date or not end_date or not outlet:
            return jsonify({"error": "Missing startDate, endDate, or outlet."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT use_same_recipe FROM master_featured ORDER BY id DESC LIMIT 1")
        flag_row = cursor.fetchone()
        use_same_recipe = flag_row["use_same_recipe"] if flag_row else 0

        # First get all item types from recipe table for this outlet
        cursor.execute("SELECT DISTINCT ItemType FROM tblorder_detailshistory")
        item_types = [row["ItemType"] for row in cursor.fetchall()]

        # ----------------- Bulk lookups for stock info and unit definitions -----------------
        # cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ItemName, GroupName, Type, primary_unit, secondary_unit
            FROM stock_statement
            WHERE OutletName = %s
        """, (outlet,))
        stock_info_lookup = {
            row["ItemName"]: {
                "GroupName": row["GroupName"] or "Group Not Found",
                "Type": row["Type"] or "Type Not Found",
                "primary_unit": row["primary_unit"],
                "secondary_unit": row["secondary_unit"]
            }
            for row in cursor.fetchall()
        }

        cursor.execute("""
            SELECT name, unit, uom FROM tblunitdefinition WHERE outlet = %s
        """, (outlet,))
        unitdef_lookup = {
            row["name"]: {"unit": float(row["unit"]), "uom": row["uom"]}
            for row in cursor.fetchall()
        }
        # cursor.close()

        result = {}
        grand_total_items_sold = 0
        grand_unique_items_sold = 0
        grand_total_menu_items = 0
        type_wise_consumption = {}
        all_consumed_items = {}
        inappropriate_uom_items = []  # Track items with inappropriate UOMs

        for item_type in item_types:
            type_wise_consumption[item_type] = {}

            if use_same_recipe == 1:
                cursor.execute(
                    "SELECT COUNT(DISTINCT name) AS total_menu_items FROM recipe WHERE ItemType = %s",
                    (item_type,)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) AS total_menu_items FROM recipe WHERE outlet = %s AND ItemType = %s",
                    (outlet, item_type)
                )
            total_menu_item = cursor.fetchone()["total_menu_items"]
            grand_total_menu_items += total_menu_item

            # Get all sold items of this type from order history
            cursor.execute("""
                SELECT 
                    d.ItemName,
                    SUM(d.count) AS total_sold
                FROM tblorder_detailshistory d
                JOIN tblorderhistory o ON o.idtblorderHistory = d.order_ID
                WHERE o.Date BETWEEN %s AND %s
                  AND o.Outlet_Name = %s
                  AND d.ItemType = %s
                GROUP BY d.ItemName
            """, (start_date, end_date, outlet, item_type))

            sold_items = cursor.fetchall()
            itemwise = []

            total_sold = 0
            unique_items_sold = 0

            for sold_item in sold_items:
                item_name = sold_item["ItemName"]
                quantity_sold = sold_item["total_sold"]
                total_sold += quantity_sold
                if quantity_sold > 0:
                    unique_items_sold += 1

                if use_same_recipe == 1:
                    cursor.execute("""
                        SELECT id, sellingprice, costprice 
                        FROM recipe 
                        WHERE name = %s AND ItemType = %s
                        LIMIT 1
                    """, (item_name, item_type))
                else:
                    cursor.execute("""
                        SELECT id, sellingprice, costprice 
                        FROM recipe 
                        WHERE outlet = %s AND name = %s AND ItemType = %s
                    """, (outlet, item_name, item_type))
                recipe_info = cursor.fetchone()

                item_data = {
                    "ItemName": item_name,
                    "ItemType": item_type,
                    "total_sold": quantity_sold,
                    "has_recipe": bool(recipe_info)
                }

                if recipe_info:
                    item_data["recipe_id"] = recipe_info["id"]
                    recipe_id = recipe_info["id"]

                    # Get recipe items and calculate consumption
                    cursor.execute("SELECT name, quantity, uom, new_uom FROM recipe_items WHERE recipe_id = %s", (recipe_id,))
                    recipe_items = cursor.fetchall()
                    for ri in recipe_items:
                        ingredient_name = ri["name"]
                        total_consumed = float(ri["quantity"]) * float(quantity_sold)
                        uom = ri["uom"]
                        new_uom = ri["new_uom"]

                        # Check if UOM is standard
                        # is_standard = is_standard_uom(uom)
                        is_standard = is_standard_uom(new_uom, ingredient_name, unitdef_lookup, stock_info_lookup)
                        if not is_standard:
                            inappropriate_uom_items.append({
                                "item_name": ingredient_name,
                                "uom": uom,
                                "source": "recipe_items",
                                "recipe": item_name,
                                "item_type": item_type
                            })

                        # Type-wise consumption
                        if ingredient_name not in type_wise_consumption[item_type]:
                            type_wise_consumption[item_type][ingredient_name] = {
                                "total_quantity": 0,
                                "uom": uom,
                                "new_uom": new_uom,
                                "is_standard_uom": is_standard  # Add flag
                            }
                        type_wise_consumption[item_type][ingredient_name]["total_quantity"] += total_consumed
                        type_wise_consumption[item_type][ingredient_name]["is_standard_uom"] = type_wise_consumption[item_type][ingredient_name].get("is_standard_uom", True) and is_standard

                        # Global consumption
                        if ingredient_name not in all_consumed_items:
                            all_consumed_items[ingredient_name] = {
                                "total_quantity": 0,
                                "uom": uom,
                                "new_uom": new_uom,
                                "is_standard_uom": is_standard  # Add flag
                            }
                        all_consumed_items[ingredient_name]["total_quantity"] += total_consumed
                        # Update flag if any occurrence is non-standard
                        if not is_standard:
                            all_consumed_items[ingredient_name]["is_standard_uom"] = False

                    # Handle sub-recipes
                    cursor.execute("""
                        SELECT rs.sub_recipe_id as sub_id, rs.quantity AS sr_qty, s.name AS sub_name, s.uom, s.unit, s.id, rs.new_uom AS new_uom
                        FROM recipe_subrecipes rs
                        JOIN sub_recipe s ON rs.sub_recipe_id = s.id
                        WHERE rs.recipe_id = %s
                    """, (recipe_id,))
                    sub_recipes = cursor.fetchall()

                    for sr in sub_recipes:
                        if include_sub_recipe_items:
                            cursor.execute("SELECT name, quantity, uom, new_uom FROM sub_recipe_items WHERE sub_recipe_id = %s", (sr["sub_id"],))
                            sub_recipe_items = cursor.fetchall()
                            for sri in sub_recipe_items:
                                ingredient_name = sri["name"]
                                total_consumed = float(sri["quantity"]) * float(sr["sr_qty"]) * float(quantity_sold)
                                uom = sri["uom"]
                                new_uom = sri["new_uom"]

                                # Check if UOM is standard
                                # is_standard = is_standard_uom(uom)
                                is_standard = is_standard_uom(uom, ingredient_name, unitdef_lookup, stock_info_lookup)

                                if not is_standard:
                                    inappropriate_uom_items.append({
                                        "item_name": ingredient_name,
                                        "uom": uom,
                                        "source": "sub_recipe_items",
                                        "sub_recipe": sr["sub_name"],
                                        "recipe": item_name,
                                        "item_type": item_type
                                    })

                                # Type-wise consumption
                                if ingredient_name not in type_wise_consumption[item_type]:
                                    type_wise_consumption[item_type][ingredient_name] = {
                                        "total_quantity": 0,
                                        "uom": uom,
                                        "new_uom": new_uom,
                                        "is_standard_uom": is_standard
                                    }
                                type_wise_consumption[item_type][ingredient_name]["total_quantity"] += total_consumed
                                if not is_standard:
                                    type_wise_consumption[item_type][ingredient_name]["is_standard_uom"] = False

                                # Global consumption
                                if ingredient_name not in all_consumed_items:
                                    all_consumed_items[ingredient_name] = {
                                        "total_quantity": 0,
                                        "uom": uom,
                                        "new_uom": new_uom,
                                        "is_standard_uom": is_standard
                                    }
                                all_consumed_items[ingredient_name]["total_quantity"] += total_consumed
                                if not is_standard:
                                    all_consumed_items[ingredient_name]["is_standard_uom"] = False
                        else:
                            sub_recipe_name = sr["sub_name"]
                            total_consumed = float(sr["sr_qty"]) * float(quantity_sold)
                            uom = sr["uom"]
                            new_uom = sr.get("new_uom", "")

                            # Check if UOM is standard
                            # is_standard = is_standard_uom(uom)
                            is_standard = is_standard_uom(uom, sub_recipe_name, unitdef_lookup, stock_info_lookup)

                            if not is_standard:
                                inappropriate_uom_items.append({
                                    "item_name": sub_recipe_name,
                                    "uom": uom,
                                    "source": "sub_recipe",
                                    "recipe": item_name,
                                    "item_type": item_type
                                })

                            if sub_recipe_name not in type_wise_consumption[item_type]:
                                type_wise_consumption[item_type][sub_recipe_name] = {
                                    "total_quantity": 0,
                                    "uom": uom,
                                    "new_uom": new_uom,
                                    "is_sub_recipe": True,
                                    "is_standard_uom": is_standard
                                }
                            type_wise_consumption[item_type][sub_recipe_name]["total_quantity"] += total_consumed
                            if not is_standard:
                                type_wise_consumption[item_type][sub_recipe_name]["is_standard_uom"] = False

                            if sub_recipe_name not in all_consumed_items:
                                all_consumed_items[sub_recipe_name] = {
                                    "total_quantity": 0,
                                    "uom": uom,
                                    "new_uom": new_uom,
                                    "is_standard_uom": is_standard
                                }
                            all_consumed_items[sub_recipe_name]["total_quantity"] += total_consumed
                            if not is_standard:
                                all_consumed_items[sub_recipe_name]["is_standard_uom"] = False

                itemwise.append(item_data)

            grand_total_items_sold += total_sold
            grand_unique_items_sold += unique_items_sold

            result[item_type] = {
                "itemwise_summary": itemwise,
                "total_items_sold": total_sold,
                "unique_items_sold": unique_items_sold,
                "total_menu_items": total_menu_item,
            }

        def enrich_with_conversion(ingredient_name, raw_total_quantity):
            """Rounds total_quantity and computes secondary-unit conversion
            fields using stock_info_lookup / unitdef_lookup."""
            total_quantity = float(Decimal(raw_total_quantity))

            stock_info = stock_info_lookup.get(ingredient_name, {
                "GroupName": "Group Not Found", "Type": "Type Not Found",
                "primary_unit": None, "secondary_unit": None
            })
            primary_unit = stock_info.get("primary_unit")
            secondary_unit = stock_info.get("secondary_unit")

            unit_def = unitdef_lookup.get(ingredient_name)
            converted_secondary_qty = total_quantity
            invalid_unitdefinition_uom = True
            if primary_unit:

                if unit_def:
                    qty_in_unitdef_uom = total_quantity * unit_def["unit"]
                    unitdef_uom = unit_def["uom"]

                    if secondary_unit:
                        converted_secondary_qty, is_valid = convert_to_secondary_unit(
                            qty_in_unitdef_uom, unitdef_uom, secondary_unit
                        )
                        invalid_unitdefinition_uom = not is_valid
                    else:
                        converted_secondary_qty = qty_in_unitdef_uom
                        invalid_unitdefinition_uom = True


            converted_secondary_qty = float(
                Decimal(converted_secondary_qty)
            )

            return {
                "total_quantity": total_quantity,
                "primary_unit": primary_unit,
                "secondary_unit": secondary_unit,
                "converted_secondary_quantity": converted_secondary_qty,
                "invalid_unitdefinition_uom": invalid_unitdefinition_uom,
                "stock_group": stock_info["GroupName"],
                "stock_type": stock_info["Type"]
            }

        # Round + enrich type_wise_consumption
        for item_type, ingredients in type_wise_consumption.items():
            for ingredient_name, ingredient in ingredients.items():
                enriched = enrich_with_conversion(ingredient_name, ingredient["total_quantity"])
                ingredient["total_quantity"] = enriched["total_quantity"]
                ingredient["primary_unit"] = enriched["primary_unit"]
                ingredient["secondary_unit"] = enriched["secondary_unit"]
                ingredient["converted_secondary_quantity"] = enriched["converted_secondary_quantity"]
                ingredient["invalid_unitdefinition_uom"] = enriched["invalid_unitdefinition_uom"]

        # Round + enrich all_consumed_items, grouped by stock Type/GroupName
        nested_consumed_group = {}
        for name, info in all_consumed_items.items():
            uom = info.get("uom")
            new_uom = info.get("new_uom")
            is_standard_uom_flag = info.get("is_standard_uom", False)

            enriched = enrich_with_conversion(name, info["total_quantity"])
            item_type = enriched["stock_type"]
            group_name = enriched["stock_group"]

            if item_type not in nested_consumed_group:
                nested_consumed_group[item_type] = {}
            if group_name not in nested_consumed_group[item_type]:
                nested_consumed_group[item_type][group_name] = []

            nested_consumed_group[item_type][group_name].append({
                "name": name,
                "uom": uom,
                "new_uom": new_uom,
                "total_quantity": enriched["total_quantity"],
                "is_standard_uom": is_standard_uom_flag,
                "primary_unit": enriched["primary_unit"],
                "secondary_unit": enriched["secondary_unit"],
                "converted_secondary_quantity": enriched["converted_secondary_quantity"],
                "invalid_unitdefinition_uom": enriched["invalid_unitdefinition_uom"]
            })

        conn.close()

        # Prepare warning summary
        inappropriate_uom_summary = {
            "has_inappropriate_uoms": len(inappropriate_uom_items) > 0,
            "total_inappropriate_items": len(inappropriate_uom_items),
            "inappropriate_items": inappropriate_uom_items
        }

        return jsonify({
            "grouped_by_item_type": result,
            "grand_total_items_sold": grand_total_items_sold,
            "grand_unique_items_sold": grand_unique_items_sold,
            "grand_total_menu_items": grand_total_menu_items,
            "type_wise_consumption": type_wise_consumption,
            # "all_consumed_items": nested_consumed_group,
            # "uom_validation": inappropriate_uom_summary  # Add UOM validation summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400