from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth

from datetime import date
from decimal import Decimal

load_dotenv()

app_file494 = Blueprint('app_file494', __name__)

def _fmt(v):
    return str(v if v is not None else Decimal("0.00"))


def get_general_bill_summary(cursor, outlet, bill_date):
    """
    Department-wise general bill totals for one outlet and one date.
    `cursor` must be a dictionary cursor. Returns (departments, totals).
    """
    cursor.execute("""
        SELECT
            t.code                                   AS code,
            t.name                                   AS department,
            COUNT(b.id)                              AS bills,
            COALESCE(SUM(b.sub_total), 0)            AS gross,
            COALESCE(SUM(b.discount_amount), 0)      AS discount,
            COALESCE(SUM(b.sub_total - b.discount_amount), 0) AS net,
            COALESCE(SUM(b.tax_amount), 0)           AS tax,
            COALESCE(SUM(b.grand_total), 0)          AS total
        FROM hotel_generalbill_types t
        LEFT JOIN hotel_generalbills b
               ON b.bill_type = t.code
              AND b.bill_date = %s
              AND b.outlet = %s
        WHERE t.is_active = 1
        GROUP BY t.code, t.name
        ORDER BY t.name
    """, (bill_date, outlet))
    rows = cursor.fetchall()

    departments = []
    totals = {k: Decimal("0.00") for k in ("gross", "discount", "net", "tax", "total")}
    total_bills = 0

    for r in rows:
        departments.append({
            "code": r["code"],
            "department": r["department"],
            "bills": int(r["bills"]),
            "gross": _fmt(r["gross"]),
            "discount": _fmt(r["discount"]),
            "net": _fmt(r["net"]),
            "tax": _fmt(r["tax"]),
            "total": _fmt(r["total"]),
        })
        total_bills += int(r["bills"])
        for k in totals:
            totals[k] += Decimal(r[k])

    totals = {k: _fmt(v) for k, v in totals.items()}
    totals["bills"] = total_bills
    return departments, totals


@app_file494.route("/generalbill_summary", methods=["POST"])
@cross_origin()
def general_bill_summary():
    mydb = None
    try:
        data = request.get_json(silent=True) or {}

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

        outlet = (data.get("outlet") or "").strip()
        if not outlet:
            return {"error": "outlet is required"}, 400

        # defaults to today; the date is optional so past audits can be re-run
        bill_date = (data.get("date") or date.today().strftime("%Y-%m-%d")).strip()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        departments, totals = get_general_bill_summary(cursor, outlet, bill_date)

        return jsonify({
            "date": bill_date,
            "outlet": outlet,
            "departments": departments,
            "totals": totals
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        try:
            mydb.close()
        except:
            pass