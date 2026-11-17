# from flask import Blueprint, request, jsonify
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# from root.auth.check import token_auth
# import re
# from collections import defaultdict

# load_dotenv()

# app_file30 = Blueprint('app_file30', __name__)

# def valid_date(datestring):
#     try:
#         regex = re.compile(r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
#         return re.match(regex, datestring) is not None
#     except ValueError:
#         return False

# @app_file30.route("/item-lists", methods=["POST"])
# @cross_origin()
# def stats():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password')
#         )
#         cursor = mydb.cursor(buffered=True)
#         cursor.execute(f"USE {os.getenv('database')}")

#         json_data = request.get_json()

#         token = json_data.get("token")
#         outlet = json_data.get("outlet")

#         if not token:
#             return {"error": "No token provided."}, 400
#         if not outlet:
#             return {"error": "No outlet provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Fetch all recipes for current outlet
#         recipe_query = "SELECT name FROM recipe WHERE outlet = %s"
#         cursor.execute(recipe_query, (outlet,))
#         recipe_names = set(row[0].strip().lower() for row in cursor.fetchall() if row[0])

#         # Fetch all menus for the outlet
#         menu_query = """
#             SELECT Name, Description, Type, Price, Restaurant, state, discountExempt, serviceChargeExempt
#             FROM tblmenu
#             WHERE Restaurant = %s
#         """
#         cursor.execute(menu_query, (outlet,))
#         menus = cursor.fetchall()

#         grouped_data = defaultdict(lambda: defaultdict(list))

#         for menu in menus:
#             name = menu[0].strip() if menu[0] else ""
#             has_recipe = name.lower() in recipe_names

#             menu_data = {
#                 "Name": name,
#                 "Description": menu[1],
#                 "Type": menu[2],
#                 "Price": str(menu[3]),
#                 "Restaurant": menu[4],
#                 "state": menu[5],
#                 "discountExempt": menu[6],
#                 "serviceChargeExempt": menu[7],
#                 "hasRecipe": has_recipe
#             }

#             desc_key = menu[1].lower() if menu[1] else "undefined"
#             grouped_data[menu[2]][desc_key].append(menu_data)

#         response_data = []
#         for menu_type, descriptions in grouped_data.items():
#             type_group = {'Type': menu_type, 'items': []}
#             for desc, items in descriptions.items():
#                 menu_group = {'Description': desc.title(), 'items': items}
#                 type_group['items'].append(menu_group)
#             response_data.append(type_group)

#         return jsonify(response_data), 200

#     except mysql.connector.Error as db_error:
#         return jsonify({"error": f"Database error: {str(db_error)}"}), 500
#     except Exception as error:
#         return jsonify({"error": f"Internal server error: {str(error)}"}), 500
#     finally:
#         if 'cursor' in locals():
#             cursor.close()
#         if 'mydb' in locals():
#             mydb.close()



from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from root.auth.check import token_auth
import re
from collections import defaultdict

load_dotenv()

app_file30 = Blueprint('app_file30', __name__)

def valid_date(datestring):
    try:
        regex = re.compile(r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
        return re.match(regex, datestring) is not None
    except ValueError:
        return False

@app_file30.route("/item-lists", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        json_data = request.get_json()

        token = json_data.get("token")
        outlet = json_data.get("outlet")

        if not token:
            return {"error": "No token provided."}, 400
        if not outlet:
            return {"error": "No outlet provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Fetch all recipes for current outlet
        recipe_query = "SELECT name FROM recipe WHERE outlet = %s"
        cursor.execute(recipe_query, (outlet,))
        recipe_names = set(row[0].strip().lower() for row in cursor.fetchall() if row[0])

        # Fetch all menus for the outlet
        menu_query = """
            SELECT Name, Description, Type, Price, Restaurant, state, discountExempt, serviceChargeExempt
            FROM tblmenu
            WHERE Restaurant = %s
        """
        cursor.execute(menu_query, (outlet,))
        menus = cursor.fetchall()

        grouped_data = defaultdict(lambda: defaultdict(list))

        for menu in menus:
            name = menu[0].strip() if menu[0] else ""
            has_recipe = name.lower() in recipe_names

            menu_data = {
                "Name": name,
                "Description": menu[1],
                "Type": menu[2],
                "Price": str(menu[3]),
                "Restaurant": menu[4],
                "state": menu[5],
                "discountExempt": menu[6],
                "serviceChargeExempt": menu[7],
                "hasRecipe": has_recipe
            }

            desc_key = menu[1].lower() if menu[1] else "undefined"
            grouped_data[menu[2]][desc_key].append(menu_data)

        response_data = []
        for menu_type, descriptions in grouped_data.items():
            type_group = {'Type': menu_type, 'items': []}
            for desc, items in descriptions.items():
                menu_group = {'Description': desc.title(), 'items': items}
                type_group['items'].append(menu_group)
            response_data.append(type_group)

        return jsonify(response_data), 200

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
    except Exception as error:
        return jsonify({"error": f"Internal server error: {str(error)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'mydb' in locals():
            mydb.close()

@app_file30.route("/menu-by-type", methods=["POST"])
@cross_origin()
def menu_by_type():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        json_data = request.get_json()

        token = json_data.get("token")
        outlet = json_data.get("outlet")
        type_filter = json_data.get("type")  # optional

        if not token:
            return {"error": "No token provided."}, 400
        if not outlet:
            return {"error": "No outlet provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Fetch menu names grouped by type for the outlet
        menu_query = "SELECT Name, Type FROM tblmenu WHERE Restaurant = %s"
        params = [outlet]

        if type_filter:
            menu_query += " AND Type = %s"
            params.append(type_filter)

        cursor.execute(menu_query, tuple(params))
        menus = cursor.fetchall()

        grouped_data = defaultdict(list)

        for menu in menus:
            name = menu[0].strip() if menu[0] else ""
            grouped_data[menu[1]].append(name)

        response_data = [
            {"Type": menu_type, "items": names}
            for menu_type, names in grouped_data.items()
        ]

        return jsonify(response_data), 200

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
    except Exception as error:
        return jsonify({"error": f"Internal server error: {str(error)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'mydb' in locals():
            mydb.close()


from datetime import date

@app_file30.route("/menu-forversioning", methods=["POST"])
@cross_origin()
def post_menu_forversioning():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        items = data.get("items")
        combo_items = data.get("combo_items", [])  # List of combo items
        remarks = data.get("remarks")  # NEW

        if not items or not isinstance(items, list):
            return jsonify({"error": "items must be a non-empty list."}), 400

        menu_date = date.today().isoformat()

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # Get next version number
        cursor.execute("SELECT MAX(version) FROM tblmenu_master")
        max_version = cursor.fetchone()[0]
        next_version = (max_version or 0) + 1

        # 1. Insert master row
        master_insert = """
            INSERT INTO tblmenu_master (version, menu_date, remarks)
            VALUES (%s, %s, %s)
        """
        cursor.execute(master_insert, (next_version, menu_date, remarks))
        menu_master_id = cursor.lastrowid

        # 2. Insert main menu items with combo flag
        detail_insert = """
            INSERT INTO tblmenu_details
                (menu_master_id, Name, Description, Type, Price, priceAfterTax, 
                 discountExempt, serviceChargeExempt, status, is_combo, group_display_order, item_display_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        rows = []
        for item in items:
            status = item.get("status", 1)
            status = 1 if status else 0
            
            is_combo = item.get("is_combo", 0)
            is_combo = 1 if is_combo else 0
            
            price = item.get("Price")
            price_after_tax = item.get("priceAfterTax")
            
            if price_after_tax is None and price is not None:
                tax_rate = 0.13
                price_after_tax = float(price) * (1 + tax_rate)
                price_after_tax = round(price_after_tax, 2)

            group_display_order = item.get("group_display_order", 0)
            item_display_order = item.get("item_display_order", 0)
            rows.append((
                menu_master_id,
                item.get("Name"),
                item.get("Description"),
                item.get("Type"),
                price,
                price_after_tax,
                item.get("discountExempt"),
                item.get("serviceChargeExempt"),
                status,
                is_combo,
                group_display_order,
                item_display_order
            ))

        cursor.executemany(detail_insert, rows)
        mydb.commit()

        # 3. Insert combo items if any
        if combo_items:
            combo_insert = """
                INSERT INTO tblmenu_combo_details
                    (menu_master_id, Name, Description, Type, Price, priceAfterTax,
                     discountExempt, serviceChargeExempt, status, quantity, display_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            combo_rows = []
            for combo_item in combo_items:
                combo_status = combo_item.get("status", 1)
                combo_status = 1 if combo_status else 0
                
                combo_price = combo_item.get("Price")
                combo_price_after_tax = combo_item.get("priceAfterTax")
                
                if combo_price_after_tax is None and combo_price is not None:
                    tax_rate = 0.13
                    combo_price_after_tax = float(combo_price) * (1 + tax_rate)
                    combo_price_after_tax = round(combo_price_after_tax, 2)
                
                combo_rows.append((
                    menu_master_id,
                    combo_item.get("Name"),
                    combo_item.get("Description"),
                    combo_item.get("Type"),
                    combo_price,
                    combo_price_after_tax,
                    combo_item.get("discountExempt"),
                    combo_item.get("serviceChargeExempt"),
                    combo_status,
                    combo_item.get("quantity", 1),
                    combo_item.get("display_order", 0)
                ))
            
            if combo_rows:
                cursor.executemany(combo_insert, combo_rows)
                mydb.commit()

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "menu_master_id": menu_master_id,
            "version": next_version,
            "menu_date": menu_date,
            "remarks": remarks,
            "inserted_count": len(rows),
            "combo_count": len(combo_rows) if combo_items else 0
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/assign-outlets", methods=["POST"])
@cross_origin()
def assign_menu_to_outlets():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        menu_master_id = data.get("menu_master_id")
        outlets = data.get("outlets")  # List of outlet names or objects with vat_applicable
        force = data.get("force", False)  # If True, demote existing published menus

        if not menu_master_id:
            return jsonify({"error": "menu_master_id is required."}), 400

        if not outlets or not isinstance(outlets, list):
            return jsonify({"error": "outlets must be a non-empty list."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # Parse outlets format - support both simple and detailed
        parsed_outlets = []
        for item in outlets:
            if isinstance(item, dict):
                outlet_name = item.get("outlet")
                vat_applicable = item.get("vat_applicable", 1)  # Default to 1 (True)
            else:
                outlet_name = item
                vat_applicable = 1  # Default to True
            
            if outlet_name:
                parsed_outlets.append({
                    "outlet": outlet_name, 
                    "vat_applicable": 1 if vat_applicable else 0
                })

        if not parsed_outlets:
            cursor.close()
            mydb.close()
            return jsonify({"error": "No valid outlets provided."}), 400

        # Get outlet names
        outlet_names = [p["outlet"] for p in parsed_outlets]
        placeholders = ", ".join(["%s"] * len(outlet_names))

        # 1. Check if menu exists
        cursor.execute("SELECT id FROM tblmenu_master WHERE id = %s", (menu_master_id,))
        if not cursor.fetchone():
            cursor.close()
            mydb.close()
            return jsonify({"error": "Menu not found."}), 404

        # 2. Check for existing published menus (only state = 'published' is a conflict)
        cursor.execute(
            f"""
            SELECT DISTINCT om.outlet
            FROM tblmenu_outlet_mapping om
            WHERE om.outlet IN ({placeholders}) 
            AND om.state = 'published'
            """,
            tuple(outlet_names)
        )
        
        existing_published = cursor.fetchall()
        published_outlets = [row['outlet'] for row in existing_published]
        
        if published_outlets:
            if force:
                # Demote existing published menus to 'saved'
                cursor.execute(
                    f"""
                    UPDATE tblmenu_outlet_mapping 
                    SET state = 'saved', updated_at = CURRENT_TIMESTAMP
                    WHERE outlet IN ({placeholders}) AND state = 'published'
                    """,
                    tuple(outlet_names)
                )
            else:
                cursor.close()
                mydb.close()
                return jsonify({
                    "error": "Cannot assign published menu to outlets that already have a published menu.",
                    "published_outlets": published_outlets,
                    "message": f"These outlets already have a published menu: {', '.join(published_outlets)}. Use force=true to override."
                }), 400

        # 3. Insert or update outlet mappings with state = 'published' and vat_applicable
        insert_query = """
            INSERT INTO tblmenu_outlet_mapping (menu_master_id, outlet, state, vat_applicable)
            VALUES (%s, %s, 'published', %s)
            ON DUPLICATE KEY UPDATE 
                state = 'published',
                vat_applicable = VALUES(vat_applicable),
                updated_at = CURRENT_TIMESTAMP
        """
        
        assigned_count = 0
        updated_count = 0
        already_assigned = []
        demoted_outlets = []
        
        for p in parsed_outlets:
            cursor.execute(insert_query, (menu_master_id, p["outlet"], p["vat_applicable"]))
            if cursor.rowcount == 1:
                assigned_count += 1
            else:
                # Check if it was already assigned
                cursor.execute(
                    "SELECT state, vat_applicable FROM tblmenu_outlet_mapping WHERE menu_master_id = %s AND outlet = %s",
                    (menu_master_id, p["outlet"])
                )
                existing = cursor.fetchone()
                if existing:
                    already_assigned.append({
                        "outlet": p["outlet"], 
                        "previous_state": existing['state'],
                        "previous_vat_applicable": existing['vat_applicable'],
                        "new_vat_applicable": p["vat_applicable"]
                    })
                    updated_count += 1

        mydb.commit()
        
        # 4. Get the assigned outlets with their states and vat_applicable
        cursor.execute(
            """
            SELECT outlet, state, vat_applicable, assigned_at 
            FROM tblmenu_outlet_mapping 
            WHERE menu_master_id = %s
            """,
            (menu_master_id,)
        )
        assigned_outlets = cursor.fetchall()

        cursor.close()
        mydb.close()

        response = {
            "status": "success",
            "menu_master_id": menu_master_id,
            "assigned_count": assigned_count,
            "updated_count": updated_count,
            "assigned_outlets": assigned_outlets,
            "message": f"Successfully published menu for {assigned_count} outlet(s)."
        }
        
        if demoted_outlets:
            response["demoted_outlets"] = demoted_outlets
            response["message"] += f" Demoted {len(demoted_outlets)} previously published outlet(s)."
        
        if already_assigned:
            response["already_assigned"] = already_assigned
            response["warning"] = f"These outlets were already assigned and updated."

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/get", methods=["POST"])
@cross_origin()
def get_menu_forversioning():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        menu_date = data.get("menu_date")
        type_filter = data.get("Type")
        status_filter = data.get("status")  # "active", "inactive", "archived", "draft"
        outlet_filter = data.get("outlet")

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # First get all masters
        master_query = """
            SELECT
                id,
                version,
                menu_date,
                created_at,
                updated_at,
                remarks
            FROM tblmenu_master
            WHERE 1=1
        """
        master_params = []

        if menu_date:
            master_query += " AND menu_date = %s"
            master_params.append(menu_date)

        master_query += " ORDER BY id DESC"

        cursor.execute(master_query, tuple(master_params))
        masters = cursor.fetchall()

        # For each master, get outlet mappings
        for m in masters:
            cursor.execute(
                """
                SELECT outlet, state, vat_applicable, assigned_at, updated_at, id as mapping_id
                FROM tblmenu_outlet_mapping
                WHERE menu_master_id = %s
                """,
                (m["id"],)
            )
            outlet_mappings = cursor.fetchall()
            
            # Apply outlet filter if provided
            if outlet_filter:
                outlet_mappings = [om for om in outlet_mappings if om["outlet"] == outlet_filter]
            
            m["outlets"] = outlet_mappings
            
            # Compute status
            has_published = any(om["state"] == "published" for om in outlet_mappings)
            has_archived = any(om["state"] == "archived" for om in outlet_mappings)
            
            if has_published or has_archived:
                m["status"] = "active"
            else:
                m["status"] = "inactive"

        # Apply status filter after computing
        if status_filter:
            masters = [m for m in masters if m["status"] == status_filter]

        # Fetch items for all masters
        items_by_master = {}
        combo_items_by_master = {}
        
        if masters:
            master_ids = [m["id"] for m in masters]
            placeholders = ", ".join(["%s"] * len(master_ids))

            # Fetch main menu items with sorting
            detail_query = f"""
                SELECT * FROM tblmenu_details 
                WHERE menu_master_id IN ({placeholders})
            """
            detail_params = list(master_ids)

            if type_filter:
                detail_query += " AND Type = %s"
                detail_params.append(type_filter)
            
            # Sort by Type alphabetically, then group_display_order, then item_display_order
            detail_query += """
                ORDER BY 
                    Type ASC,
                    group_display_order ASC, 
                    item_display_order ASC
            """

            cursor.execute(detail_query, tuple(detail_params))
            details = cursor.fetchall()

            for d in details:
                items_by_master.setdefault(d["menu_master_id"], []).append(d)

            # Fetch combo items separately
            combo_query = f"""
                SELECT * FROM tblmenu_combo_details 
                WHERE menu_master_id IN ({placeholders}) AND status = 1
                ORDER BY display_order, Name
            """
            cursor.execute(combo_query, tuple(master_ids))
            combo_items = cursor.fetchall()

            for c in combo_items:
                combo_items_by_master.setdefault(c["menu_master_id"], []).append(c)

        for m in masters:
            m["items"] = items_by_master.get(m["id"], [])
            m["combo_items"] = combo_items_by_master.get(m["id"], [])

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "count": len(masters),
            "menus": masters
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app_file30.route("/menu-forversioning/get-items", methods=["POST"])
@cross_origin()
def get_menu_forversioning_items():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        menu_master_id = data.get("menu_master_id")
        type_filter = data.get("Type")  # optional filter

        if not menu_master_id:
            return jsonify({"error": "menu_master_id is required."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # confirm the master exists so a bad id returns a clear 404, not an empty list
        cursor.execute(
            "SELECT * FROM tblmenu_master WHERE id = %s",
            (menu_master_id,)
        )
        master = cursor.fetchone()

        if not master:
            cursor.close()
            mydb.close()
            return jsonify({"error": "menu_master_id not found."}), 404

        detail_query = "SELECT * FROM tblmenu_details WHERE menu_master_id = %s"
        detail_params = [menu_master_id]

        if type_filter:
            detail_query += " AND Type = %s"
            detail_params.append(type_filter)

        cursor.execute(detail_query, tuple(detail_params))
        items = cursor.fetchall()

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "menu": master,
            "count": len(items),
            "items": items
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app_file30.route("/menu-forversioning/update-state", methods=["POST"])
@cross_origin()
def update_menu_forversioning_state():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        menu_master_id = data.get("menu_master_id")
        new_state = data.get("state")

        if not menu_master_id:
            return jsonify({"error": "menu_master_id is required."}), 400

        if not new_state:
            return jsonify({"error": "state is required."}), 400

        allowed_states = ("saved", "published", "cancelled")
        if new_state not in allowed_states:
            return jsonify({"error": f"state must be one of {allowed_states}."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # confirm it exists first, and fetch outlet for the supersede step below
        cursor.execute(
            "SELECT outlet FROM tblmenu_master WHERE id = %s",
            (menu_master_id,)
        )
        row = cursor.fetchone()

        if not row:
            cursor.close()
            mydb.close()
            return jsonify({"error": "menu_master_id not found."}), 404

        outlet = row[0]

        # if publishing, supersede any previously published version for this outlet
        if new_state == "published":
            cursor.execute(
                """
                UPDATE tblmenu_master
                SET state = 'cancelled'
                WHERE outlet = %s AND state = 'published' AND id != %s
                """,
                (outlet, menu_master_id)
            )

        cursor.execute(
            "UPDATE tblmenu_master SET state = %s WHERE id = %s",
            (new_state, menu_master_id)
        )
        mydb.commit()

        updated = cursor.rowcount

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "menu_master_id": menu_master_id,
            "state": new_state,
            "updated": updated
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/delete", methods=["POST"])
@cross_origin()
def delete_menu_forversioning():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        menu_master_id = data.get("menu_master_id")

        if not menu_master_id:
            return jsonify({"error": "menu_master_id is required."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # confirm it exists first
        cursor.execute(
            "SELECT id FROM tblmenu_master WHERE id = %s",
            (menu_master_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            mydb.close()
            return jsonify({"error": "menu_master_id not found."}), 404

        # details are deleted automatically via ON DELETE CASCADE,
        # but deleting explicitly first keeps this safe even if the FK/cascade
        # is ever missing or disabled on some environment
        cursor.execute(
            "DELETE FROM tblmenu_details WHERE menu_master_id = %s",
            (menu_master_id,)
        )
        deleted_details = cursor.rowcount

        cursor.execute(
            "DELETE FROM tblmenu_master WHERE id = %s",
            (menu_master_id,)
        )
        deleted_master = cursor.rowcount

        mydb.commit()

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "menu_master_id": menu_master_id,
            "deleted_master": deleted_master,
            "deleted_details": deleted_details
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-details", methods=["POST"])
@cross_origin()
def menu_details():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password")
        )
        cursor = mydb.cursor(dictionary=True)
        cursor.execute(f"USE {os.getenv('database')}")

        json_data = request.get_json()

        token = json_data.get("token")
        outlet = json_data.get("outlet")
        type_filter = json_data.get("type")  # Optional

        if not token:
            return jsonify({"error": "No token provided."}), 400

        if not outlet:
            return jsonify({"error": "No outlet provided."}), 400

        if not token_auth(token):
            return jsonify({"error": "Invalid token."}), 400

        query = """
            SELECT
                Name,
                Description,
                Price,
                Type
            FROM tblmenu
            WHERE Restaurant = %s
        """

        params = [outlet]

        if type_filter:
            query += " AND Type = %s"
            params.append(type_filter)

        query += " ORDER BY Type, Name"

        cursor.execute(query, tuple(params))
        menu_items = cursor.fetchall()

        return jsonify(menu_items), 200

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500

    except Exception as error:
        return jsonify({"error": f"Internal server error: {str(error)}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'mydb' in locals():
            mydb.close()

@app_file30.route("/menu-forversioning/update-items", methods=["POST"])
@cross_origin()
def update_menu_items():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        updates = data.get("updates")
        if not updates or not isinstance(updates, list):
            return jsonify({"error": "updates must be a non-empty list."}), 400

        # Fields that can be updated - added group_display_order and item_display_order
        updateable_fields = [
            'Name', 'Description', 'Type', 'Price', 'priceAfterTax', 
            'discountExempt', 'serviceChargeExempt', 'status', 'is_combo',
            'group_display_order', 'item_display_order'  # Added these two
        ]

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        updated_items = []
        failed_validation = []

        # First, validate all items exist
        for idx, update_item in enumerate(updates):
            item_id = update_item.get("item_id")
            if not item_id:
                failed_validation.append({
                    "index": idx,
                    "error": "item_id is required."
                })
                continue

            cursor.execute("SELECT id FROM tblmenu_details WHERE id = %s", (item_id,))
            if not cursor.fetchone():
                failed_validation.append({
                    "item_id": item_id,
                    "index": idx,
                    "error": "Item not found."
                })

        if failed_validation:
            cursor.close()
            mydb.close()
            return jsonify({
                "status": "error",
                "message": "Validation failed. No items were updated.",
                "failed_validation": failed_validation
            }), 400

        # Perform all updates in a transaction
        try:
            for update_item in updates:
                item_id = update_item["item_id"]
                update_fields = []
                update_values = []
                
                for field in updateable_fields:
                    if field in update_item:
                        update_fields.append(f"{field} = %s")
                        update_values.append(update_item[field])
                
                if update_fields:
                    update_values.append(item_id)
                    update_query = f"UPDATE tblmenu_details SET {', '.join(update_fields)} WHERE id = %s"
                    cursor.execute(update_query, tuple(update_values))

            mydb.commit()

            # Fetch all updated items
            item_ids = [u["item_id"] for u in updates]
            placeholders = ", ".join(["%s"] * len(item_ids))
            cursor.execute(
                f"SELECT * FROM tblmenu_details WHERE id IN ({placeholders})",
                tuple(item_ids)
            )
            updated_items = cursor.fetchall()

        except Exception as e:
            mydb.rollback()
            cursor.close()
            mydb.close()
            return jsonify({
                "status": "error",
                "message": f"Update failed. Transaction rolled back: {str(e)}"
            }), 400

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "message": f"Successfully updated {len(updated_items)} item(s).",
            "updated_count": len(updated_items),
            "items": updated_items
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/update-by-description", methods=["POST"])
@cross_origin()
def update_menu_items_by_description():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        description = data.get("description")
        if not description:
            return jsonify({"error": "description is required."}), 400

        # Optional filters to narrow down the update
        menu_master_id = data.get("menu_master_id")  # Optional: limit to specific menu
        
        # Fields to update (these will apply to ALL items with this description)
        status = data.get("status")  # Optional
        group_display_order = data.get("group_display_order")  # Optional - updates whole group
        # NOTE: item_display_order is NOT included here because it should be updated per item

        # Check if at least one field to update is provided
        if status is None and group_display_order is None:
            return jsonify({
                "error": "At least one of 'status' or 'group_display_order' must be provided."
            }), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # Build query to find items with the description
        select_query = "SELECT * FROM tblmenu_details WHERE Description = %s"
        select_params = [description]
        
        if menu_master_id:
            select_query += " AND menu_master_id = %s"
            select_params.append(menu_master_id)

        cursor.execute(select_query, tuple(select_params))
        affected_items = cursor.fetchall()

        if not affected_items:
            cursor.close()
            mydb.close()
            return jsonify({
                "status": "success",
                "message": f"No items found with description: '{description}'",
                "updated_count": 0,
                "items": []
            }), 200

        # Build dynamic update query
        update_fields = []
        update_params = []
        
        if status is not None:
            update_fields.append("status = %s")
            update_params.append(status)
        
        if group_display_order is not None:
            update_fields.append("group_display_order = %s")
            update_params.append(group_display_order)

        # Build the WHERE clause
        where_clause = "Description = %s"
        where_params = [description]
        
        if menu_master_id:
            where_clause += " AND menu_master_id = %s"
            where_params.append(menu_master_id)

        # Combine all parameters
        all_params = update_params + where_params

        # Execute update
        update_query = f"UPDATE tblmenu_details SET {', '.join(update_fields)} WHERE {where_clause}"
        cursor.execute(update_query, tuple(all_params))
        mydb.commit()
        updated_count = cursor.rowcount

        # Fetch the updated items
        cursor.execute(select_query, tuple(select_params))
        updated_items = cursor.fetchall()

        cursor.close()
        mydb.close()

        # Build response message
        updated_fields = []
        if status is not None:
            updated_fields.append(f"status={status}")
        if group_display_order is not None:
            updated_fields.append(f"group_display_order={group_display_order}")

        return jsonify({
            "status": "success",
            "message": f"Successfully updated {updated_count} item(s) with description: '{description}'. Updated fields: {', '.join(updated_fields)}",
            "updated_count": updated_count,
            "items": updated_items
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app_file30.route("/menu-forversioning/get-published-menu", methods=["POST"])
@cross_origin()
def get_published_menu():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        restaurant = data.get("Restaurant")
        if not restaurant:
            return jsonify({"error": "Restaurant is required."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # 1. Find the published menu for this outlet
        cursor.execute(
            """
            SELECT om.id as mapping_id, om.menu_master_id, om.vat_applicable, om.outlet,
                   m.version, m.menu_date
            FROM tblmenu_outlet_mapping om
            JOIN tblmenu_master m ON om.menu_master_id = m.id
            WHERE om.outlet = %s AND om.state = 'published'
            ORDER BY om.updated_at DESC, m.version DESC
            LIMIT 1
            """,
            (restaurant,)
        )
        
        published_menu = cursor.fetchone()
        
        if not published_menu:
            cursor.close()
            mydb.close()
            return jsonify({
                "status": "success",
                "count": 0,
                "items": [],
                "message": f"No published menu found for {restaurant}."
            }), 200

        menu_master_id = published_menu["menu_master_id"]
        vat_applicable = published_menu["vat_applicable"]
        mapping_id = published_menu["mapping_id"]

        # 2. Get all active items sorted by Type, group_display_order, and item_display_order
        cursor.execute(
            """
            SELECT id, Name, Description, Type, Price, priceAfterTax, 
                   discountExempt, serviceChargeExempt, is_combo, status,
                   group_display_order, item_display_order
            FROM tblmenu_details
            WHERE menu_master_id = %s
            ORDER BY Type ASC, group_display_order ASC, item_display_order ASC
            """,
            (menu_master_id,)
        )
        
        items = cursor.fetchall()

        # 3. Get ALL combo items for this menu (no linking)
        cursor.execute(
            """
            SELECT id, Name, Description, Type, Price, priceAfterTax,
                   discountExempt, serviceChargeExempt, quantity, display_order
            FROM tblmenu_combo_details
            WHERE menu_master_id = %s AND status = 1
            ORDER BY display_order, Name
            """,
            (menu_master_id,)
        )
        
        combo_items = cursor.fetchall()

        # 4. Format combo items with price logic
        formatted_combo_items = []
        for combo_item in combo_items:
            if vat_applicable == 1:
                price = combo_item["Price"]
            else:
                price = combo_item["priceAfterTax"] if combo_item["priceAfterTax"] is not None else combo_item["Price"]
            
            formatted_combo_items.append({
                "id": combo_item["id"],
                "Name": combo_item["Name"],
                "Description": combo_item["Description"],
                "Type": combo_item["Type"],
                "Price": str(price) if price is not None else "0.00",
                "discountExempt": combo_item["discountExempt"] or "no",
                "serviceChargeExempt": combo_item["serviceChargeExempt"] or "no",
                "quantity": combo_item["quantity"],
                "display_order": combo_item["display_order"]
            })

        # 5. Format response - add combo_items to all items where is_combo = 1
        formatted_items = []
        for item in items:
            if vat_applicable == 1:
                price = item["Price"]
            else:
                price = item["priceAfterTax"] if item["priceAfterTax"] is not None else item["Price"]
            
            formatted_item = {
                "id": item["id"],
                "Name": item["Name"],
                "Description": item["Description"],
                "Type": item["Type"],
                "Price": str(price) if price is not None else "0.00",
                "Restaurant": restaurant,
                "discountExempt": item["discountExempt"] or "no",
                "serviceChargeExempt": item["serviceChargeExempt"] or "no",
                "state": "Active" if item["status"] else "In-Active",
                "is_combo": item["is_combo"],
                "group_display_order": item["group_display_order"],
                "item_display_order": item["item_display_order"]
            }
            
            # If it's a combo, add ALL combo items
            if item["is_combo"] == 1:
                formatted_item["combo_items"] = formatted_combo_items
            else:
                formatted_item["combo_items"] = []
            
            formatted_items.append(formatted_item)

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "count": len(formatted_items),
            "mapping_id": mapping_id,  # Send mapping_id to frontend
            "items": formatted_items
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/archive-published-menu", methods=["POST"])
@cross_origin()
def archive_published_menu():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        mapping_id = data.get("mapping_id")
        if not mapping_id:
            return jsonify({"error": "mapping_id is required."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # Update the mapping state to archived
        cursor.execute(
            """
            UPDATE tblmenu_outlet_mapping 
            SET state = 'archived', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND state = 'published'
            """,
            (mapping_id,)
        )

        # Check if any row was updated
        if cursor.rowcount == 0:
            cursor.close()
            mydb.close()
            return jsonify({
                "status": "error",
                "message": "No published menu found with this mapping_id or already archived."
            }), 404

        mydb.commit()
        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "message": "Menu has been archived successfully.",
            "mapping_id": mapping_id,
            "new_state": "archived"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/unpublish-menu", methods=["POST"])
@cross_origin()
def unpublish_menu():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        mapping_id = data.get("mapping_id")
        if not mapping_id:
            return jsonify({"error": "mapping_id is required."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # Check if mapping exists and is published
        cursor.execute(
            "SELECT id FROM tblmenu_outlet_mapping WHERE id = %s AND state = 'published'",
            (mapping_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            mydb.close()
            return jsonify({
                "error": "No published menu found with this mapping_id."
            }), 404

        # Update state from 'published' to 'saved'
        cursor.execute(
            """
            UPDATE tblmenu_outlet_mapping 
            SET state = 'saved', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (mapping_id,)
        )
        mydb.commit()

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "message": "Menu unpublished successfully.",
            "mapping_id": mapping_id,
            "new_state": "saved"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app_file30.route("/menu-forversioning/publish-menu", methods=["POST"])
@cross_origin()
def publish_menu():
    try:
        data = request.get_json()

        token = data.get("token")
        if not token or not token_auth(token):
            return jsonify({"error": "Invalid or missing token."}), 400

        mapping_id = data.get("mapping_id")
        if not mapping_id:
            return jsonify({"error": "mapping_id is required."}), 400

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)
        cursor.execute(f"USE {os.getenv('database')}")

        # Get mapping information
        cursor.execute(
            """
            SELECT id, outlet, state
            FROM tblmenu_outlet_mapping
            WHERE id = %s
            """,
            (mapping_id,)
        )

        mapping = cursor.fetchone()

        if not mapping:
            cursor.close()
            mydb.close()
            return jsonify({
                "error": "Mapping not found."
            }), 404

        # Already published
        if mapping["state"] == "published":
            cursor.close()
            mydb.close()
            return jsonify({
                "error": "This menu is already published."
            }), 400

        # Check if another menu is already published for this outlet
        cursor.execute(
            """
            SELECT id, menu_master_id
            FROM tblmenu_outlet_mapping
            WHERE outlet = %s
              AND state = 'published'
              AND id <> %s
            """,
            (mapping["outlet"], mapping_id)
        )

        existing = cursor.fetchone()

        if existing:
            cursor.close()
            mydb.close()
            return jsonify({
                "error": "A published menu already exists for this outlet.",
                "message": "Please unpublish the currently published menu before publishing this one.",
                "published_mapping_id": existing["id"],
                "published_menu_master_id": existing["menu_master_id"],
                "outlet": mapping["outlet"]
            }), 400

        # Publish this menu
        cursor.execute(
            """
            UPDATE tblmenu_outlet_mapping
            SET state = 'published',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (mapping_id,)
        )

        mydb.commit()

        cursor.close()
        mydb.close()

        return jsonify({
            "status": "success",
            "message": "Menu published successfully.",
            "mapping_id": mapping_id,
            "outlet": mapping["outlet"],
            "new_state": "published"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400