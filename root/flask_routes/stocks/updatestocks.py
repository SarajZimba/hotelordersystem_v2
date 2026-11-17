# from flask import Blueprint, jsonify, request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app_file122 = Blueprint('app_file122', __name__)

# @app_file122.route("/updatestocks", methods=["POST"])
# @cross_origin()
# def update_stocks():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password')
#         )
#         cursor = mydb.cursor(buffered=True)

#         cursor.execute(f"USE {os.getenv('database')}")

#         data = request.get_json()

#         if not data or "outlet_name" not in data or "stocks" not in data:
#             return jsonify({"error": "Please provide 'outlet_name' and 'stocks' list"}), 400

#         outlet_name = data["outlet_name"]
#         stocks = data["stocks"]

#         updated_count = 0
#         for stock in stocks:
#             item_name = stock.get("ItemName")
#             current_level = stock.get("CurrentLevel")
#             rate = stock.get("Rate")
#             total = stock.get("Total")

#             if not item_name:
#                 continue

#             update_fields = []
#             update_values = []

#             if current_level is not None:
#                 update_fields.append("CurrentLevel = %s")
#                 update_values.append(current_level)
#             if rate is not None:
#                 update_fields.append("Rate = %s")
#                 update_values.append(rate)
#             if total is not None:
#                 update_fields.append("Total = %s")
#                 update_values.append(total)

#             if update_fields:
#                 update_sql = f"""
#                 UPDATE stock_statement 
#                 SET {', '.join(update_fields)} 
#                 WHERE ItemName = %s AND OutletName = %s
#                 """
#                 update_values.extend([item_name, outlet_name])
#                 cursor.execute(update_sql, update_values)
#                 updated_count += cursor.rowcount

#                 if rate is not None:
#                     cursor.execute("UPDATE recipe_items SET rate = %s WHERE name = %s", (rate, item_name))
#                     cursor.execute("UPDATE sub_recipe_items SET rate = %s WHERE name = %s", (rate, item_name))

#                     cursor.execute("""
#                         UPDATE recipe_items 
#                         SET cost = rate * quantity 
#                         WHERE name = %s
#                     """, (item_name,))

#                     cursor.execute("""
#                         UPDATE sub_recipe_items 
#                         SET cost = rate * quantity 
#                         WHERE name = %s
#                     """, (item_name,))

#         mydb.commit()

#         return jsonify({"message": f"{updated_count} stock records updated and recipe rates/costs synced."}), 200

#     except mysql.connector.Error as db_error:
#         return jsonify({"error": f"Database error: {str(db_error)}"}), 500
#     except Exception as e:
#         return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
#     finally:
#         if 'mydb' in locals():
#             mydb.close()

from flask import Blueprint, jsonify, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv

load_dotenv()

app_file122 = Blueprint('app_file122', __name__)

# @app_file122.route("/updatestocks", methods=["POST"])
# @cross_origin()
# def update_stocks():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password')
#         )
#         cursor = mydb.cursor(buffered=True)

#         cursor.execute(f"USE {os.getenv('database')}")

#         data = request.get_json()

#         if not data or "outlet_name" not in data or "stocks" not in data:
#             return jsonify({"error": "Please provide 'outlet_name' and 'stocks' list"}), 400

#         outlet_name = data["outlet_name"]
#         stocks = data["stocks"]

#         updated_count = 0
#         for stock in stocks:
#             item_name = stock.get("ItemName")
#             current_level = stock.get("CurrentLevel")
#             rate = stock.get("Rate")
#             total = stock.get("Total")

#             if not item_name:
#                 continue

#             update_fields = []
#             update_values = []

#             if current_level is not None:
#                 update_fields.append("CurrentLevel = %s")
#                 update_values.append(current_level)
#             if rate is not None:
#                 update_fields.append("Rate = %s")
#                 update_values.append(rate)
#             if total is not None:
#                 update_fields.append("Total = %s")
#                 update_values.append(total)

#             if update_fields:
#                 update_sql = f"""
#                 UPDATE stock_statement 
#                 SET {', '.join(update_fields)} 
#                 WHERE ItemName = %s AND OutletName = %s
#                 """
#                 update_values.extend([item_name, outlet_name])
#                 cursor.execute(update_sql, update_values)
#                 updated_count += cursor.rowcount

#                 if rate is not None:
#                     cursor.execute("UPDATE recipe_items SET rate = %s WHERE name = %s", (rate, item_name))
#                     cursor.execute("UPDATE sub_recipe_items SET rate = %s WHERE name = %s", (rate, item_name))

#                     cursor.execute("""
#                         UPDATE recipe_items 
#                         SET cost = rate * quantity 
#                         WHERE name = %s
#                     """, (item_name,))

#                     cursor.execute("""
#                         UPDATE sub_recipe_items 
#                         SET cost = rate * quantity 
#                         WHERE name = %s
#                     """, (item_name,))

#         mydb.commit()

#         return jsonify({"message": f"{updated_count} stock records updated and recipe rates/costs synced."}), 200

#     except mysql.connector.Error as db_error:
#         return jsonify({"error": f"Database error: {str(db_error)}"}), 500
#     except Exception as e:
#         return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
#     finally:
#         if 'mydb' in locals():
#             mydb.close()


@app_file122.route("/updatestocks", methods=["POST"])
@cross_origin()
def update_stocks():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)

        cursor.execute(f"USE {os.getenv('database')}")

        data = request.get_json()

        if not data or "outlet_name" not in data or "stocks" not in data:
            return jsonify({"error": "Please provide 'outlet_name' and 'stocks' list"}), 400

        outlet_name = data["outlet_name"]
        stocks = data["stocks"]

        updated_count = 0
        for stock in stocks:
            item_name = stock.get("ItemName")
            current_level = stock.get("CurrentLevel")
            rate = stock.get("Rate")
            total = stock.get("Total")
            primary_unit = stock.get("primary_unit")
            secondary_unit = stock.get("secondary_unit")

            if not item_name:
                continue

            update_fields = []
            update_values = []

            if current_level is not None:
                update_fields.append("CurrentLevel = %s")
                update_values.append(current_level)
            if rate is not None:
                update_fields.append("Rate = %s")
                update_values.append(rate)
            if total is not None:
                update_fields.append("Total = %s")
                update_values.append(total)
            if primary_unit is not None:
                update_fields.append("primary_unit = %s")
                update_values.append(primary_unit)
            if secondary_unit is not None:
                update_fields.append("secondary_unit = %s")
                update_values.append(secondary_unit)

            if update_fields:
                update_sql = f"""
                UPDATE stock_statement 
                SET {', '.join(update_fields)} 
                WHERE ItemName = %s AND OutletName = %s
                """
                update_values.extend([item_name, outlet_name])
                cursor.execute(update_sql, update_values)
                updated_count += cursor.rowcount

                if rate is not None:
                    # Scope recipe_items updates to this outlet's recipes only
                    cursor.execute("""
                        UPDATE recipe_items ri
                        JOIN recipe r ON ri.recipe_id = r.id
                        SET ri.rate = %s
                        WHERE ri.name = %s AND r.outlet = %s
                    """, (rate, item_name, outlet_name))

                    # Scope sub_recipe_items updates to this outlet's sub-recipes only
                    cursor.execute("""
                        UPDATE sub_recipe_items sri
                        JOIN sub_recipe sr ON sri.sub_recipe_id = sr.id
                        SET sri.rate = %s
                        WHERE sri.name = %s AND sr.outlet = %s
                    """, (rate, item_name, outlet_name))

                    cursor.execute("""
                        UPDATE recipe_items ri
                        JOIN recipe r ON ri.recipe_id = r.id
                        SET ri.cost = ri.rate * ri.quantity
                        WHERE ri.name = %s AND r.outlet = %s
                    """, (item_name, outlet_name))

                    cursor.execute("""
                        UPDATE sub_recipe_items sri
                        JOIN sub_recipe sr ON sri.sub_recipe_id = sr.id
                        SET sri.cost = sri.rate * sri.quantity
                        WHERE sri.name = %s AND sr.outlet = %s
                    """, (item_name, outlet_name))

                    # Sync rate into tblunitdefinition for this item/outlet
                    cursor.execute("""
                        UPDATE tblunitdefinition
                        SET rate = %s
                        WHERE name = %s AND outlet = %s
                    """, (rate, item_name, outlet_name))

        mydb.commit()

        return jsonify({"message": f"{updated_count} stock records updated and recipe rates/costs synced."}), 200

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    finally:
        if 'mydb' in locals():
            mydb.close()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )


@app_file122.route("/updatestockitemname", methods=["POST"])
@cross_origin()
def update_stock_item_name():

    mydb = None
    cursor = None

    try:

        data = request.get_json()

        outlet_name = data.get("outlet_name")
        old_item_name = data.get("old_item_name")
        new_item_name = data.get("new_item_name")

        # =====================================================
        # VALIDATION
        # =====================================================

        if not outlet_name:
            return jsonify({
                "error": "outlet_name is required"
            }), 400

        if not old_item_name:
            return jsonify({
                "error": "old_item_name is required"
            }), 400

        if not new_item_name:
            return jsonify({
                "error": "new_item_name is required"
            }), 400

        if old_item_name.strip() == new_item_name.strip():
            return jsonify({
                "error": "Old and new item names cannot be same"
            }), 400

        # =====================================================
        # DB CONNECTION
        # =====================================================

        mydb = get_db_connection()

        cursor = mydb.cursor(dictionary=True)

        # =====================================================
        # CHECK OLD ITEM EXISTS
        # =====================================================

        cursor.execute("""
            SELECT
                id,
                GroupName
            FROM stock_statement
            WHERE ItemName = %s
            AND OutletName = %s
            LIMIT 1
        """, (
            old_item_name,
            outlet_name
        ))

        stock_item = cursor.fetchone()

        if not stock_item:
            return jsonify({
                "error": "Item not found in this outlet"
            }), 404

        group_name = stock_item.get("GroupName")

        # =====================================================
        # CHECK NEW ITEM DOES NOT ALREADY EXIST
        # =====================================================

        cursor.execute("""
            SELECT id
            FROM stock_statement
            WHERE ItemName = %s
            AND OutletName = %s
            LIMIT 1
        """, (
            new_item_name,
            outlet_name
        ))

        existing_item = cursor.fetchone()

        if existing_item:
            return jsonify({
                "error": "New item name already exists in this outlet"
            }), 400

        # =====================================================
        # UPDATE SUMMARY
        # =====================================================

        update_summary = {}

        # =====================================================
        # 1. stock_statement
        # =====================================================

        cursor.execute("""
            UPDATE stock_statement
            SET ItemName = %s
            WHERE ItemName = %s
            AND OutletName = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["stock_statement"] = cursor.rowcount

        # =====================================================
        # 2. stock_statement_lots
        # =====================================================

        cursor.execute("""
            UPDATE stock_statement_lots
            SET item_name = %s
            WHERE item_name = %s
            AND outlet_name = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["stock_statement_lots"] = cursor.rowcount

        # =====================================================
        # 3. recipe_items
        # recipe_items -> recipe -> outlet
        # =====================================================

        cursor.execute("""
            UPDATE recipe_items ri
            INNER JOIN recipe r
                ON ri.recipe_id = r.id
            SET ri.name = %s
            WHERE ri.name = %s
            AND r.outlet = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["recipe_items"] = cursor.rowcount

        # =====================================================
        # 4. sub_recipe_items
        # sub_recipe_items -> sub_recipe -> outlet
        # =====================================================

        cursor.execute("""
            UPDATE sub_recipe_items sri
            INNER JOIN sub_recipe sr
                ON sri.sub_recipe_id = sr.id
            SET sri.name = %s
            WHERE sri.name = %s
            AND sr.outlet = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["sub_recipe_items"] = cursor.rowcount

        # =====================================================
        # 5. intblstorereqdetails
        # details -> requisition -> outlet
        # =====================================================

        cursor.execute("""
            UPDATE intblstorereqdetails d
            INNER JOIN intblstorerequisition s
                ON d.StoreReqID = s.idintblStoreRequisition
            SET d.ItemName = %s
            WHERE d.ItemName = %s
            AND s.Outlet = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["intblstorereqdetails"] = cursor.rowcount

        # =====================================================
        # 6. intbl_purchaserequisition_contract
        # contract -> purchase requisition -> outlet
        # =====================================================

        cursor.execute("""
            UPDATE intbl_purchaserequisition_contract c
            INNER JOIN intbl_purchaserequisition p
                ON c.PurchaseReqID = p.IDIntbl_PurchaseRequisition
            SET c.Name = %s
            WHERE c.Name = %s
            AND p.Outlet_Name = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["intbl_purchaserequisition_contract"] = cursor.rowcount

        # =====================================================
        # 7. tblunitdefinition
        # =====================================================

        cursor.execute("""
            UPDATE tblunitdefinition
            SET name = %s
            WHERE name = %s
            AND outlet = %s
        """, (
            new_item_name,
            old_item_name,
            outlet_name
        ))

        update_summary["tblunitdefinition"] = cursor.rowcount

        # =====================================================
        # 8. centralkitchen_productionitems
        # ONLY FOR FINISHED GOODS
        # =====================================================

        production_updated = 0

        if group_name == "Finished Goods":

            cursor.execute("""
                UPDATE centralkitchen_productionitems cp
                INNER JOIN centralkitchen_production p
                    ON cp.production_id = p.id
                SET cp.itemname = %s
                WHERE cp.itemname = %s
                AND p.outlet = %s
            """, (
                new_item_name,
                old_item_name,
                outlet_name
            ))

            production_updated = cursor.rowcount

        update_summary["centralkitchen_productionitems"] = production_updated

        # =====================================================
        # COMMIT
        # =====================================================

        mydb.commit()

        return jsonify({
            "success": True,
            "message": "Item name updated successfully",
            "outlet_name": outlet_name,
            "old_item_name": old_item_name,
            "new_item_name": new_item_name,
            "updated_rows": update_summary
        }), 200

    # =========================================================
    # MYSQL ERROR
    # =========================================================

    except mysql.connector.Error as db_error:

        if mydb:
            mydb.rollback()

        return jsonify({
            "success": False,
            "error": f"MySQL Error: {str(db_error)}"
        }), 500

    # =========================================================
    # GENERAL ERROR
    # =========================================================

    except Exception as e:

        if mydb:
            mydb.rollback()

        return jsonify({
            "success": False,
            "error": f"Unexpected Error: {str(e)}"
        }), 500

    # =========================================================
    # FINALLY
    # =========================================================

    finally:

        if cursor:
            cursor.close()

        if mydb:
            mydb.close()