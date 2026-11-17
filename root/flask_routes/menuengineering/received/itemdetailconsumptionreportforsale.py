from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth
from decimal import Decimal

load_dotenv()

app_file118 = Blueprint('app_file118', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )


@app_file118.route("/itemconsumefromsale", methods=["POST"])
@cross_origin()
def item_consumption_details():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        outlet = data.get("outlet")
        item_name = data.get("item_name")
        start_date = data.get("startDate")
        end_date = data.get("endDate")
        item_type = data.get("item_type", "Food")  # "Food" or "Beverage"
        include_sub_recipe_items = data.get("includeSubRecipeItems", True)

        if not all([outlet, item_name, start_date, end_date]):
            return jsonify({"error": "Missing required parameters (outlet, item_name, startDate, endDate)."}), 400

        if item_type not in ("Food", "Beverage"):
            return jsonify({"error": "item_type must be 'Food' or 'Beverage'."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        # Step 1: Get all consumed items using EXACT SAME logic as inventory-summary-food
        all_consumed_items = {}

        # Same query as inventory-summary
        cursor.execute("""
            SELECT d.ItemName, SUM(d.count) AS total_sold
            FROM tblorder_detailshistory d
            JOIN tblorderhistory o ON o.idtblorderHistory = d.order_ID
            WHERE o.Date BETWEEN %s AND %s AND o.Outlet_Name = %s and d.ItemType = %s
            GROUP BY d.ItemName
        """, (start_date, end_date, outlet, item_type))

        for sold_item in cursor.fetchall():
            menu_item = sold_item["ItemName"]
            quantity_sold = float(sold_item["total_sold"]) if sold_item["total_sold"] else 0.0

            if quantity_sold == 0:
                continue

            cursor.execute("""
                SELECT id FROM recipe
                WHERE outlet = %s AND name = %s and ItemType = %s
            """, (outlet, menu_item, item_type))
            recipe_info = cursor.fetchone()

            if recipe_info:
                recipe_id = recipe_info["id"]

                # Direct recipe items - EXACT same logic
                cursor.execute("""
                    SELECT name, quantity, uom, new_uom
                    FROM recipe_items WHERE recipe_id = %s
                """, (recipe_id,))
                for ri in cursor.fetchall():
                    name = ri["name"]
                    consumed = float(ri["quantity"]) * float(quantity_sold)
                    if name not in all_consumed_items:
                        all_consumed_items[name] = {
                            "total_consumed": 0,
                            "real_consumed": 0,
                            "uom": ri["uom"],
                            "new_uom": ri["new_uom"],
                            "unitdefinition": {"unit": "", "uom": ""}
                        }
                    all_consumed_items[name]["total_consumed"] += consumed

                # Sub-recipe items - EXACT same logic
                if include_sub_recipe_items:
                    cursor.execute("""
                        SELECT rs.sub_recipe_id, rs.quantity AS sr_qty, s.id
                        FROM recipe_subrecipes rs
                        JOIN sub_recipe s ON rs.sub_recipe_id = s.id
                        WHERE rs.recipe_id = %s
                    """, (recipe_id,))
                    for sr in cursor.fetchall():
                        cursor.execute("""
                            SELECT name, quantity, uom, new_uom
                            FROM sub_recipe_items WHERE sub_recipe_id = %s
                        """, (sr["id"],))
                        for sri in cursor.fetchall():
                            name = sri["name"]
                            consumed = float(sri["quantity"]) * float(sr["sr_qty"]) * float(quantity_sold)
                            if name not in all_consumed_items:
                                all_consumed_items[name] = {
                                    "total_consumed": 0,
                                    "uom": sri["uom"],
                                    "new_uom": sri["new_uom"],
                                    "unitdefinition": {"unit": "", "uom": ""},
                                    "real_consumed": 0
                                }
                            all_consumed_items[name]["total_consumed"] += consumed

        print(f"All consumed items: {all_consumed_items}")

        # Step 2: Convert consumption using unitdefinition - EXACT same logic
        for item_name_key, details in all_consumed_items.items():
            total_consumed = details["total_consumed"]

            # Default real_consumed is same as total_consumed
            real_consumed = total_consumed

            cursor.execute("""
                SELECT unit, uom FROM tblunitdefinition
                WHERE name = %s and outlet = %s
            """, (item_name_key, outlet))
            result = cursor.fetchone()

            unitdefinition_dict = {
                "unit": None,
                "uom": None
            }

            if result:
                # factor = 1/float(result["unit"])
                # factor = float(result["unit"])
                # real_consumed = float(total_consumed) * factor
                real_consumed = float(total_consumed)
                unitdefinition_dict = {
                    "unit": result["unit"],
                    "uom": result["uom"]
                }

            all_consumed_items[item_name_key]["total_consumed"] = real_consumed
            all_consumed_items[item_name_key]["unitdefinition"] = unitdefinition_dict

        # Step 3: Extract data for the requested item
        requested_item_data = all_consumed_items.get(item_name, {
            "total_consumed": 0,
            "real_consumed": 0,
            "uom": None,
            "new_uom": None,
            "unitdefinition": {"unit": None, "uom": None}
        })
        cursor.execute("""
                SELECT primary_unit, secondary_unit, GroupName FROM stock_statement
                WHERE ItemName = %s and OutletName = %s
            """, (item_name, outlet))
        stockstatement_result = cursor.fetchone()

        cursor.execute("""
                SELECT unit, uom FROM tblunitdefinition
                WHERE name = %s and outlet = %s
            """, (item_name, outlet))
        unitdefinition_result = cursor.fetchone()

        # Step 4: Build the detailed breakdown for the response
        result = {
            "details": [],
            "summary": {
                "total_consumed": float(requested_item_data["total_consumed"]),
                "uom": requested_item_data["unitdefinition"]["uom"] or requested_item_data.get("uom"),
                "real_consumed": float(requested_item_data.get("real_consumed", 0)),
                "unitdefinition": {"unit":unitdefinition_result["unit"],"uom":unitdefinition_result["uom"] },
                "primary_unit": stockstatement_result["primary_unit"],
                "secondary_unit": stockstatement_result["secondary_unit"],
                "groupname": stockstatement_result["GroupName"],
            }
        }

        # Step 5: Rebuild the sold items to create detailed breakdown
        cursor.execute("""
            SELECT d.ItemName, SUM(d.count) AS total_sold
            FROM tblorder_detailshistory d
            JOIN tblorderhistory o ON o.idtblorderHistory = d.order_ID
            WHERE o.Date BETWEEN %s AND %s AND o.Outlet_Name = %s and d.ItemType = %s
            GROUP BY d.ItemName
        """, (start_date, end_date, outlet, item_type))

        sold_items = cursor.fetchall()

        for sold_item in sold_items:
            menu_item = sold_item["ItemName"]
            quantity_sold = float(sold_item["total_sold"]) if sold_item["total_sold"] else 0.0

            if quantity_sold == 0:
                continue

            cursor.execute("""
                SELECT id FROM recipe
                WHERE outlet = %s AND name = %s and ItemType = %s
            """, (outlet, menu_item, item_type))
            recipe_info = cursor.fetchone()

            if not recipe_info:
                continue

            recipe_id = recipe_info["id"]

            # Check if this recipe uses the requested item
            uses_item = False
            total_per_unit = 0.0
            direct_qty = 0.0
            sub_total = 0.0
            sub_recipe_details = []

            # Direct usage
            cursor.execute("""
                SELECT name, quantity, uom, new_uom FROM recipe_items WHERE recipe_id = %s
            """, (recipe_id,))
            for ri in cursor.fetchall():
                if ri["name"] == item_name:
                    uses_item = True
                    direct_qty = float(ri["quantity"])
                    total_per_unit += direct_qty

            # Sub-recipe usage
            if include_sub_recipe_items:
                cursor.execute("""
                    SELECT rs.sub_recipe_id, rs.quantity AS sr_qty, s.id, s.name as sub_recipe_name
                    FROM recipe_subrecipes rs
                    JOIN sub_recipe s ON rs.sub_recipe_id = s.id
                    WHERE rs.recipe_id = %s
                """, (recipe_id,))
                for sr in cursor.fetchall():
                    cursor.execute("""
                        SELECT name, quantity FROM sub_recipe_items WHERE sub_recipe_id = %s
                    """, (sr["id"],))
                    for sri in cursor.fetchall():
                        if sri["name"] == item_name:
                            uses_item = True
                            sub_qty = float(sr["sr_qty"])
                            item_qty = float(sri["quantity"])
                            calculated_quantity = sub_qty * item_qty
                            sub_total += calculated_quantity
                            total_per_unit += calculated_quantity
                            sub_recipe_details.append({
                                "sub_recipe_name": sr["sub_recipe_name"],
                                "sub_qty_in_recipe": sub_qty,
                                "item_qty_in_sub_recipe": item_qty,
                                "calculated_quantity": calculated_quantity
                            })

            if not uses_item:
                continue

            total_consumed = quantity_sold * total_per_unit

            result['details'].append({
                "recipe_item": menu_item,
                "uom": ri["uom"],
                "new_uom": ri["new_uom"],
                "item_type": item_type,
                "total_sold": quantity_sold,
                "direct_usage_recipe_per_unit": direct_qty,
                "total_direct_recipe_usage": quantity_sold * direct_qty,
                "sub_recipe_usage_per_unit": sub_total,
                "total_sub_recipe_usage": quantity_sold * sub_total,
                "total_consumed": total_consumed,
                "converted_uom": result['summary']['uom'],
                "sub_recipes": sub_recipe_details,
                "total_per_unit": total_per_unit  # Added for debugging
            })

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "item_name": item_name,
            "outlet": outlet,
            "item_type": item_type,
            "start_date": start_date,
            "end_date": end_date,
            "consumption_details": result,
            # "debug_all_items": all_consumed_items  # Optional: for debugging
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400