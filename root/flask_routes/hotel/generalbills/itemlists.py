
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

load_dotenv()

app_file493 = Blueprint('app_file493', __name__)
TWO = Decimal("0.01")

def _dec(value, field):
    try:
        return Decimal(str(value)).quantize(TWO, ROUND_HALF_UP)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid number for '{field}'")

def _check_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400
    return None


def _connect():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )


# ---------------- CREATE ----------------
@app_file493.route("/generalbill/items", methods=["POST"])
@cross_origin()
def create_generalbill_item():
    mydb = None
    try:
        err = _check_token()
        if err:
            return err

        data = request.get_json(silent=True) or {}

        outlet = (data.get("outlet") or "").strip()
        type_code = (data.get("type_code") or "").upper()
        item_name = (data.get("item_name") or "").strip()
        if not outlet:
            return {"error": "outlet is required"}, 400
        if not type_code:
            return {"error": "type_code is required"}, 400
        if not item_name:
            return {"error": "item_name is required"}, 400

        try:
            rate = _dec(data.get("rate", 0), "rate")
        except ValueError as e:
            return {"error": str(e)}, 400
        if rate < 0:
            return {"error": "rate cannot be negative"}, 400

        is_taxable = 1 if data.get("is_taxable", True) else 0

        mydb = _connect()
        cursor = mydb.cursor(dictionary=True)

        cursor.execute(
            "SELECT code FROM hotel_generalbill_types WHERE code = %s AND is_active = 1",
            (type_code,)
        )
        if not cursor.fetchone():
            return {"error": f"Bill type {type_code} not found or inactive"}, 404

        cursor.execute("""
            INSERT INTO hotel_generalbill_item_master
                (outlet, type_code, item_name, rate, is_taxable)
            VALUES (%s, %s, %s, %s, %s)
        """, (outlet, type_code, item_name, rate, is_taxable))
        item_id = cursor.lastrowid
        mydb.commit()

        return jsonify({
            "message": "Item created successfully",
            "item": {
                "id": item_id,
                "outlet": outlet,
                "type_code": type_code,
                "item_name": item_name,
                "rate": str(rate),
                "is_taxable": is_taxable,
                "is_active": 1
            }
        }), 201

    except mysql.connector.errors.IntegrityError as e:
        try:
            mydb.rollback()
        except:
            pass
        if e.errno == 1062:
            return {"error": "This item already exists for this outlet and bill type"}, 409
        return {"error": str(e)}, 500

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass


# ---------------- LIST ----------------
@app_file493.route("/generalbill/items", methods=["GET"])
@cross_origin()
def list_generalbill_items():
    mydb = None
    try:
        err = _check_token()
        if err:
            return err

        outlet = (request.args.get("outlet") or "").strip()
        type_code = (request.args.get("type_code") or "").upper()
        include_inactive = request.args.get("include_inactive") == "1"

        conds, params = [], []
        if outlet:
            conds.append("outlet = %s")
            params.append(outlet)
        if type_code:
            conds.append("type_code = %s")
            params.append(type_code)
        if not include_inactive:
            conds.append("is_active = 1")
        where = ("WHERE " + " AND ".join(conds)) if conds else ""

        mydb = _connect()
        cursor = mydb.cursor(dictionary=True)
        cursor.execute(f"""
            SELECT id, outlet, type_code, item_name, rate, is_taxable, is_active
            FROM hotel_generalbill_item_master
            {where}
            ORDER BY outlet, type_code, item_name
        """, tuple(params))
        rows = cursor.fetchall()

        for r in rows:
            r["rate"] = str(r["rate"])

        return jsonify({"total": len(rows), "items": rows}), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass

# # ---------------- UPDATE ----------------
# @app_file493.route("/generalbill/items/<int:item_id>", methods=["PUT"])
# @cross_origin()
# def update_generalbill_item(item_id):
#     mydb = None
#     try:
#         err = _check_token()
#         if err:
#             return err

#         data = request.get_json(silent=True) or {}

#         sets, params = [], []

#         if "item_name" in data:
#             item_name = (data.get("item_name") or "").strip()
#             if not item_name:
#                 return {"error": "item_name cannot be empty"}, 400
#             sets.append("item_name = %s")
#             params.append(item_name)

#         if "rate" in data:
#             try:
#                 rate = _dec(data["rate"], "rate")
#             except ValueError as e:
#                 return {"error": str(e)}, 400
#             if rate < 0:
#                 return {"error": "rate cannot be negative"}, 400
#             sets.append("rate = %s")
#             params.append(rate)

#         if "is_taxable" in data:
#             sets.append("is_taxable = %s")
#             params.append(1 if data["is_taxable"] else 0)

#         if "is_active" in data:
#             sets.append("is_active = %s")
#             params.append(1 if data["is_active"] else 0)

#         if not sets:
#             return {"error": "Nothing to update"}, 400

#         mydb = _connect()
#         cursor = mydb.cursor(dictionary=True)

#         cursor.execute(
#             "SELECT id FROM hotel_generalbill_item_master WHERE id = %s", (item_id,)
#         )
#         if not cursor.fetchone():
#             return {"error": "Item not found"}, 404

#         cursor.execute(
#             f"UPDATE hotel_generalbill_item_master SET {', '.join(sets)} WHERE id = %s",
#             tuple(params + [item_id])
#         )
#         mydb.commit()

#         cursor.execute("""
#             SELECT id, type_code, item_name, rate, is_taxable, is_active
#             FROM hotel_generalbill_item_master WHERE id = %s
#         """, (item_id,))
#         item = cursor.fetchone()
#         item["rate"] = str(item["rate"])

#         return jsonify({"message": "Item updated successfully", "item": item}), 200

#     except mysql.connector.errors.IntegrityError as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         if e.errno == 1062:
#             return {"error": "This item already exists for this bill type"}, 409
#         return {"error": str(e)}, 500

#     except Exception as e:
#         try:
#             mydb.rollback()
#         except:
#             pass
#         return {"error": str(e)}, 500

#     finally:
#         try:
#             mydb.close()
#         except:
#             pass


# ---------------- UPDATE ----------------
@app_file493.route("/generalbill/items/<int:item_id>", methods=["PUT"])
@cross_origin()
def update_generalbill_item(item_id):
    mydb = None
    try:
        err = _check_token()
        if err:
            return err

        data = request.get_json(silent=True) or {}

        sets, params = [], []

        if "outlet" in data:
            outlet = (data.get("outlet") or "").strip()
            if not outlet:
                return {"error": "outlet cannot be empty"}, 400
            sets.append("outlet = %s")
            params.append(outlet)

        if "item_name" in data:
            item_name = (data.get("item_name") or "").strip()
            if not item_name:
                return {"error": "item_name cannot be empty"}, 400
            sets.append("item_name = %s")
            params.append(item_name)

        if "rate" in data:
            try:
                rate = _dec(data["rate"], "rate")
            except ValueError as e:
                return {"error": str(e)}, 400
            if rate < 0:
                return {"error": "rate cannot be negative"}, 400
            sets.append("rate = %s")
            params.append(rate)

        if "is_taxable" in data:
            sets.append("is_taxable = %s")
            params.append(1 if data["is_taxable"] else 0)

        if "is_active" in data:
            sets.append("is_active = %s")
            params.append(1 if data["is_active"] else 0)

        if not sets:
            return {"error": "Nothing to update"}, 400

        mydb = _connect()
        cursor = mydb.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM hotel_generalbill_item_master WHERE id = %s", (item_id,)
        )
        if not cursor.fetchone():
            return {"error": "Item not found"}, 404

        cursor.execute(
            f"UPDATE hotel_generalbill_item_master SET {', '.join(sets)} WHERE id = %s",
            tuple(params + [item_id])
        )
        mydb.commit()

        cursor.execute("""
            SELECT id, outlet, type_code, item_name, rate, is_taxable, is_active
            FROM hotel_generalbill_item_master WHERE id = %s
        """, (item_id,))
        item = cursor.fetchone()
        item["rate"] = str(item["rate"])

        return jsonify({"message": "Item updated successfully", "item": item}), 200

    except mysql.connector.errors.IntegrityError as e:
        try:
            mydb.rollback()
        except:
            pass
        if e.errno == 1062:
            return {"error": "This item already exists for this outlet and bill type"}, 409
        return {"error": str(e)}, 500

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass


# ---------------- DELETE ----------------
@app_file493.route("/generalbill/items/<int:item_id>", methods=["DELETE"])
@cross_origin()
def delete_generalbill_item(item_id):
    mydb = None
    try:
        err = _check_token()
        if err:
            return err

        mydb = _connect()
        cursor = mydb.cursor(dictionary=True)

        cursor.execute(
            "DELETE FROM hotel_generalbill_item_master WHERE id = %s", (item_id,)
        )
        if cursor.rowcount == 0:
            return {"error": "Item not found"}, 404

        mydb.commit()
        return jsonify({"message": "Item deleted successfully", "id": item_id}), 200

    except Exception as e:
        try:
            mydb.rollback()
        except:
            pass
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass