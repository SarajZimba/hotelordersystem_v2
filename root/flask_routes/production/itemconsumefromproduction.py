
from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth
from decimal import Decimal, ROUND_HALF_UP
import re

load_dotenv()

app_file242 = Blueprint('app_file242', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )

@app_file242.route("/itemconsumefromproduction", methods=["POST"])
@cross_origin()
def item_consumption_from_production():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        outlet = data.get("outlet")
        item_name = data.get("item_name")
        start_date = data.get("startDate")
        end_date = data.get("endDate")

        if not all([outlet, item_name, start_date, end_date]):
            return jsonify({"error": "Missing required parameters (outlet, item_name, startDate, endDate)."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        result = {
            "details": [],
            "summary": {
                "total_consumed": 0.0,
                "uom": None,
                "new_uom": None
            }
        }

        # =====================================================
        # Fetch unit definition for the searched item
        # =====================================================
        cursor.execute("""
            SELECT unit, uom FROM tblunitdefinition
            WHERE BINARY name = %s AND outlet = %s
        """, (item_name, outlet))
        unit_def = cursor.fetchone()
        if unit_def:
            result['summary']['uom'] = unit_def['uom']

        # =====================================================
        # Get all produced finished goods for outlet + date range
        # =====================================================
        cursor.execute("""
            SELECT 
                pi.itemname AS ItemName, 
                SUM(pi.quantity) AS total_produced
            FROM centralkitchen_productionitems pi
            JOIN centralkitchen_production p ON p.id = pi.production_id
            JOIN stock_statement s 
                ON s.ItemName COLLATE utf8mb4_general_ci = pi.itemname COLLATE utf8mb4_general_ci
                AND s.OutletName COLLATE utf8mb4_general_ci = p.outlet COLLATE utf8mb4_general_ci
                AND s.GroupName = 'Finished Goods'
            WHERE p.production_date BETWEEN %s AND %s 
                AND p.outlet = %s 
            GROUP BY pi.itemname
        """, (start_date, end_date, outlet))

        produced_items = cursor.fetchall()

        for produced_item in produced_items:
            finished_item_name = produced_item["ItemName"]
            total_produced = float(produced_item["total_produced"])

            # =====================================================
            # Get stock_statement id for this finished good
            # =====================================================
            cursor.execute("""
                SELECT id FROM stock_statement 
                WHERE BINARY ItemName = %s 
                    AND OutletName = %s 
                    AND GroupName = 'Finished Goods'
                LIMIT 1
            """, (finished_item_name, outlet))
            stock_item = cursor.fetchone()

            if not stock_item:
                continue

            production_item_id = stock_item["id"]

            # =====================================================
            # Get conversion factor and recipe id
            # =====================================================
            cursor.execute("""
                SELECT factor, production_recipe_id
                FROM conversionfactor
                WHERE production_item_id = %s AND outlet = %s
                LIMIT 1
            """, (production_item_id, outlet))
            conversion = cursor.fetchone()

            if not conversion:
                continue

            factor = float(conversion["factor"])
            production_recipe_id = conversion["production_recipe_id"]

            if factor == 0:
                continue

            # =====================================================
            # Verify it's a Production recipe
            # =====================================================
            cursor.execute("""
                SELECT id, name FROM recipe
                WHERE id = %s AND recipe_type = 'Production'
                LIMIT 1
            """, (production_recipe_id,))
            recipe_info = cursor.fetchone()

            if not recipe_info:
                continue

            # actual batches run = total_produced / factor
            actual_batches = total_produced / factor

            # =====================================================
            # Check if item_name is used directly in recipe_items
            # =====================================================
            cursor.execute("""
                SELECT quantity, uom, new_uom FROM recipe_items
                WHERE recipe_id = %s AND BINARY name = %s
                LIMIT 1
            """, (production_recipe_id, item_name))
            ri = cursor.fetchone()
            direct_qty = float(ri["quantity"]) if ri else 0.0
            item_uom = ri["uom"] if ri else None
            item_new_uom = ri["new_uom"] if ri else None

            # =====================================================
            # Check if item_name is used in any sub-recipes
            # =====================================================
            cursor.execute("""
                SELECT 
                    rs.quantity AS sub_qty,
                    sri.quantity AS item_qty,
                    sr.name AS sub_recipe_name
                FROM recipe_subrecipes rs
                JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
                JOIN sub_recipe_items sri 
                    ON sri.sub_recipe_id = rs.sub_recipe_id 
                    AND BINARY sri.name = %s
                WHERE rs.recipe_id = %s
            """, (item_name, production_recipe_id))
            sub_items = cursor.fetchall()

            sub_total = 0.0
            sub_recipe_details = []
            for row in sub_items:
                sub_qty = float(row["sub_qty"])
                item_qty = float(row["item_qty"])
                calculated_quantity = sub_qty * item_qty
                sub_total += calculated_quantity
                sub_recipe_details.append({
                    "sub_recipe_name": row["sub_recipe_name"],
                    "sub_qty_in_recipe": sub_qty,
                    "item_qty_in_sub_recipe": item_qty,
                    "calculated_quantity_per_batch": round(calculated_quantity, 4)
                })

            # Skip if this finished item doesn't use the searched item at all
            if direct_qty == 0 and sub_total == 0:
                continue

            # =====================================================
            # Calculate total consumption
            # total_consumed = batches * (direct + sub usage per batch)
            # =====================================================
            total_direct_consumed = actual_batches * direct_qty
            total_sub_consumed = actual_batches * sub_total
            total_consumed = total_direct_consumed + total_sub_consumed

            # Capture uom from sub-recipe if not found in direct
            if not item_uom and sub_items:
                cursor.execute("""
                    SELECT uom, new_uom FROM sub_recipe_items
                    WHERE BINARY name = %s
                    LIMIT 1
                """, (item_name,))
                sri_uom = cursor.fetchone()
                if sri_uom:
                    item_uom = sri_uom["uom"]
                    item_new_uom = sri_uom["new_uom"]

            # Set summary uom from first match
            if not result["summary"]["uom"] and item_uom:
                result["summary"]["uom"] = item_uom
            if not result["summary"]["new_uom"] and item_new_uom:
                result["summary"]["new_uom"] = item_new_uom

            result["details"].append({
                "finished_item": finished_item_name,
                "recipe_id": production_recipe_id,
                "recipe_name": recipe_info["name"],
                "total_produced": round(total_produced, 4),
                "production_factor": factor,
                "actual_batches": round(actual_batches, 4),
                "direct_usage_per_batch": direct_qty,
                "total_direct_usage": round(total_direct_consumed, 4),
                "sub_recipe_usage_per_batch": round(sub_total, 4),
                "total_sub_recipe_usage": round(total_sub_consumed, 4),
                "total_consumed": round(total_consumed, 4),
                "uom": item_uom,
                "new_uom": item_new_uom,
                "sub_recipes": sub_recipe_details
            })

            result["summary"]["total_consumed"] += total_consumed

        result["summary"]["total_consumed"] = round(result["summary"]["total_consumed"], 4)

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "item_name": item_name,
            "outlet": outlet,
            "start_date": start_date,
            "end_date": end_date,
            "consumption_details": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400    


# @app_file242.route("/itemconsumefromproduction", methods=["POST"])
# @cross_origin()
# def item_consumption_from_production():
#     try:
#         data = request.get_json()
#         token = data.get("token")
#         if not token or not token_auth(token):
#             return jsonify({"error": "Invalid or missing token."}), 400

#         outlet = data.get("outlet")
#         item_name = data.get("item_name")
#         start_date = data.get("startDate")
#         end_date = data.get("endDate")

#         if not all([outlet, item_name, start_date, end_date]):
#             return jsonify({"error": "Missing required parameters (outlet, item_name, startDate, endDate)."}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         debug_log = []

#         result = {
#             "details": [],
#             "summary": {
#                 "total_consumed": 0.0,
#                 "uom": None,
#                 "new_uom": None
#             }
#         }

#         # =====================================================
#         # Fetch unit definition for the searched item
#         # =====================================================
#         cursor.execute("""
#             SELECT unit, uom FROM tblunitdefinition
#             WHERE BINARY name = %s AND outlet = %s
#         """, (item_name, outlet))
#         unit_def = cursor.fetchone()
#         if unit_def:
#             result['summary']['uom'] = unit_def['uom']
#         debug_log.append({"step": "unit_def", "result": unit_def})

#         # =====================================================
#         # Get all produced finished goods for outlet + date range
#         # =====================================================
#         cursor.execute("""
#             SELECT 
#                 pi.itemname AS ItemName, 
#                 SUM(pi.quantity) AS total_produced
#             FROM centralkitchen_productionitems pi
#             JOIN centralkitchen_production p ON p.id = pi.production_id
#             JOIN stock_statement s 
#                 ON s.ItemName COLLATE utf8mb4_general_ci = pi.itemname COLLATE utf8mb4_general_ci
#                 AND s.OutletName COLLATE utf8mb4_general_ci = p.outlet COLLATE utf8mb4_general_ci
#                 AND s.GroupName = 'Finished Goods'
#             WHERE p.production_date BETWEEN %s AND %s 
#                 AND p.outlet = %s 
#             GROUP BY pi.itemname
#         """, (start_date, end_date, outlet))

#         produced_items = cursor.fetchall()
#         debug_log.append({"step": "produced_items", "count": len(produced_items), "items": [i["ItemName"] for i in produced_items]})

#         for produced_item in produced_items:
#             finished_item_name = produced_item["ItemName"]
#             total_produced = float(produced_item["total_produced"])
#             item_debug = {"finished_item": finished_item_name, "total_produced": total_produced}

#             # =====================================================
#             # Get stock_statement id for this finished good
#             # =====================================================
#             cursor.execute("""
#                 SELECT id FROM stock_statement 
#                 WHERE ItemName = %s 
#                     AND OutletName = %s 
#                     AND GroupName = 'Finished Goods'
#                 LIMIT 1
#             """, (finished_item_name, outlet))
#             stock_item = cursor.fetchone()
#             item_debug["stock_item"] = stock_item

#             if not stock_item:
#                 item_debug["skipped"] = "stock_item not found"
#                 debug_log.append(item_debug)
#                 continue

#             production_item_id = stock_item["id"]

#             # =====================================================
#             # Get conversion factor and recipe id
#             # =====================================================
#             cursor.execute("""
#                 SELECT factor, production_recipe_id
#                 FROM conversionfactor
#                 WHERE production_item_id = %s AND outlet = %s
#                 LIMIT 1
#             """, (production_item_id, outlet))
#             conversion = cursor.fetchone()
#             item_debug["conversion"] = conversion

#             if not conversion:
#                 item_debug["skipped"] = "no conversion factor"
#                 debug_log.append(item_debug)
#                 continue

#             factor = float(conversion["factor"])
#             production_recipe_id = conversion["production_recipe_id"]

#             if factor == 0:
#                 item_debug["skipped"] = "factor is 0"
#                 debug_log.append(item_debug)
#                 continue

#             # =====================================================
#             # Verify it's a Production recipe
#             # =====================================================
#             cursor.execute("""
#                 SELECT id, name FROM recipe
#                 WHERE id = %s AND recipe_type = 'Production'
#                 LIMIT 1
#             """, (production_recipe_id,))
#             recipe_info = cursor.fetchone()
#             item_debug["recipe_info"] = recipe_info

#             if not recipe_info:
#                 item_debug["skipped"] = "no production recipe found"
#                 debug_log.append(item_debug)
#                 continue

#             actual_batches = total_produced / factor

#             # =====================================================
#             # Check if item_name is used directly in recipe_items
#             # =====================================================
#             cursor.execute("""
#                 SELECT quantity, uom, new_uom FROM recipe_items
#                 WHERE recipe_id = %s AND BINARY name = %s
#                 LIMIT 1
#             """, (production_recipe_id, item_name))
#             ri = cursor.fetchone()
#             direct_qty = float(ri["quantity"]) if ri else 0.0
#             item_uom = ri["uom"] if ri else None
#             item_new_uom = ri["new_uom"] if ri else None
#             item_debug["direct_recipe_item"] = ri

#             # =====================================================
#             # Check if item_name is used in any sub-recipes
#             # =====================================================
#             cursor.execute("""
#                 SELECT 
#                     rs.quantity AS sub_qty,
#                     sri.quantity AS item_qty,
#                     sr.name AS sub_recipe_name
#                 FROM recipe_subrecipes rs
#                 JOIN sub_recipe sr ON sr.id = rs.sub_recipe_id
#                 JOIN sub_recipe_items sri 
#                     ON sri.sub_recipe_id = rs.sub_recipe_id 
#                     AND BINARY sri.name = %s
#                 WHERE rs.recipe_id = %s
#             """, (item_name, production_recipe_id))
#             sub_items = cursor.fetchall()
#             item_debug["sub_items"] = sub_items

#             sub_total = 0.0
#             sub_recipe_details = []
#             for row in sub_items:
#                 sub_qty = float(row["sub_qty"])
#                 item_qty = float(row["item_qty"])
#                 calculated_quantity = sub_qty * item_qty
#                 sub_total += calculated_quantity
#                 sub_recipe_details.append({
#                     "sub_recipe_name": row["sub_recipe_name"],
#                     "sub_qty_in_recipe": sub_qty,
#                     "item_qty_in_sub_recipe": item_qty,
#                     "calculated_quantity_per_batch": round(calculated_quantity, 4)
#                 })

#             item_debug["direct_qty"] = direct_qty
#             item_debug["sub_total"] = sub_total

#             if direct_qty == 0 and sub_total == 0:
#                 item_debug["skipped"] = f"item '{item_name}' not found in recipe or sub-recipes"
#                 debug_log.append(item_debug)
#                 continue

#             total_direct_consumed = actual_batches * direct_qty
#             total_sub_consumed = actual_batches * sub_total
#             total_consumed = total_direct_consumed + total_sub_consumed

#             if not item_uom and sub_items:
#                 cursor.execute("""
#                     SELECT uom, new_uom FROM sub_recipe_items
#                     WHERE BINARY name = %s
#                     LIMIT 1
#                 """, (item_name,))
#                 sri_uom = cursor.fetchone()
#                 if sri_uom:
#                     item_uom = sri_uom["uom"]
#                     item_new_uom = sri_uom["new_uom"]

#             if not result["summary"]["uom"] and item_uom:
#                 result["summary"]["uom"] = item_uom
#             if not result["summary"]["new_uom"] and item_new_uom:
#                 result["summary"]["new_uom"] = item_new_uom

#             result["details"].append({
#                 "finished_item": finished_item_name,
#                 "recipe_id": production_recipe_id,
#                 "recipe_name": recipe_info["name"],
#                 "total_produced": round(total_produced, 4),
#                 "production_factor": factor,
#                 "actual_batches": round(actual_batches, 4),
#                 "direct_usage_per_batch": direct_qty,
#                 "total_direct_usage": round(total_direct_consumed, 4),
#                 "sub_recipe_usage_per_batch": round(sub_total, 4),
#                 "total_sub_recipe_usage": round(total_sub_consumed, 4),
#                 "total_consumed": round(total_consumed, 4),
#                 "uom": item_uom,
#                 "new_uom": item_new_uom,
#                 "sub_recipes": sub_recipe_details
#             })

#             result["summary"]["total_consumed"] += total_consumed
#             debug_log.append(item_debug)

#         result["summary"]["total_consumed"] = round(result["summary"]["total_consumed"], 4)

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "status": "success",
#             "item_name": item_name,
#             "outlet": outlet,
#             "start_date": start_date,
#             "end_date": end_date,
#             "consumption_details": result,
#             "debug": debug_log  # Remove this after debugging
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400