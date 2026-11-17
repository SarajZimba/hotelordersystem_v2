from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from root.auth.check import token_auth
load_dotenv()

app_file502 = Blueprint('app_file502', __name__)

from datetime import date
from mysql.connector import errors as mysql_errors
from .bill import _safe_rollback

def _num(value):
    """Safe decimal-ish conversion for summing detail rows."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0

    
from datetime import date, datetime
from decimal import Decimal


def _serialize(row):
    """Make a DB row JSON-safe (Decimal -> float, date/datetime -> ISO string)."""
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _check_token():
    """Returns an error response tuple, or None if the token is valid."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except Exception:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400
    return None


def _connect():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database"),
    )

def _num(value):
    """Safe decimal-ish conversion for summing detail rows."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


@app_file502.route("/complimentary-bill-by-id", methods=["POST"])
@cross_origin()
def create_complimentary_bill_by_reservation_id():
    """
    Complimentary checkout:
      - saves header + per-night details (room cost / meal cost) for history
      - checks out the reservation, frees the in-house guest row, marks rooms Dirty
      - NO bill number, VAT, discount, IRD or journal posting
    """
    mydb = None
    cursor = None
    committed = False
    try:
        data = request.get_json() or {}

        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        reservationID = data.get("reservationID") or data.get("Reservation_ID")
        bill_details = data.get("bill_details") or []
        fiscal_year = data.get("fiscalYear")
        guest_id = str(data.get("guestID") or "").strip()

        if not reservationID:
            return {"error": "reservationID is required"}, 400
        if not fiscal_year:
            return {"error": "fiscalYear is required"}, 400
        if not isinstance(bill_details, list):
            return {"error": "bill_details must be a list."}, 400

        # Totals: use what the frontend sent, else compute from the detail rows
        room_cost = data.get("RoomCost")
        meal_cost = data.get("MealplanCost")
        if room_cost is None:
            room_cost = sum(_num(d.get("RateAmt")) for d in bill_details)
        if meal_cost is None:
            meal_cost = sum(_num(d.get("MealPlanAmt")) for d in bill_details)
        total_cost = _num(room_cost) + _num(meal_cost)

        # -------- DB --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESERVATION (row locked) + duplicate checks --------
        cursor.execute("""
            SELECT r.id, r.reservation_outlet_id, r.Current_Status, r.Emp_ID,
                   e.userName AS employee_name,
                   (SELECT b.id FROM hotel_tblhotelbills b
                    WHERE b.reservationID = r.id LIMIT 1) AS existing_bill_id,
                   (SELECT c.id FROM hotel_tblcomplimentarybills c
                    WHERE c.reservationID = r.id LIMIT 1) AS existing_comp_id
            FROM hotel_tblreservation r
            LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
            WHERE r.id = %s AND r.is_active = 1
            FOR UPDATE
        """, (reservationID,))
        reservation = cursor.fetchone()

        if not reservation:
            return {"error": "Reservation not found"}, 404
        if reservation["existing_bill_id"]:
            return {"error": "A regular bill already exists for this reservation"}, 400
        if reservation["existing_comp_id"]:
            return {"error": "Complimentary bill already exists for this reservation"}, 400
        if reservation["Current_Status"] != "Registered":
            return {
                "error": f"Reservation is {reservation['Current_Status']}; "
                         "only Registered reservations can be checked out."
            }, 400

        reservationID = reservation["id"]
        employee_name = reservation["employee_name"] or str(reservation["Emp_ID"])

        # -------- HEADER --------
        cursor.execute("""
            INSERT INTO hotel_tblcomplimentarybills (
                reservationID, Guest_ID, outlet_reservationID, fiscalYear,
                PaymentMode, Date, NoOfNights, RoomCost, MealplanCost,
                subTotal, CompAmount, Total,
                Remarks, ApprovedBy, Employee, time, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, 'Complimentary', %s, %s, %s, %s,
                      %s, %s, 0,
                      %s, %s, %s, %s, NOW(), NOW())
        """, (
            reservationID,
            guest_id or None,
            reservation["reservation_outlet_id"],
            fiscal_year,
            data.get("Date"),
            data.get("NoOfNights"),
            room_cost,
            meal_cost,
            total_cost,   # subTotal: gross value of room + meal
            total_cost,   # CompAmount: 100% waived
            data.get("Remarks"),
            data.get("ApprovedBy"),
            employee_name,
            data.get("time", ""),
        ))
        bill_id = cursor.lastrowid

        # -------- DETAILS (room cost + meal cost per night) --------
        if bill_details:
            cursor.executemany("""
                INSERT INTO hotel_tblcomplimentarybilldetails (
                    bill_id, Date, RoomNumber, RoomType, RoomRate, RoomRateName,
                    RateAmt, MealPlan, MealPlanAmt, Amount, Currency, ExeRate,
                    AmountInclCurr, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, [
                (
                    bill_id,
                    d.get("Date"),
                    d.get("RoomNumber"),
                    d.get("RoomType"),
                    d.get("RoomRate", 0),
                    d.get("RoomRateName"),
                    d.get("RateAmt", 0),
                    d.get("MealPlan"),
                    d.get("MealPlanAmt", 0),
                    d.get("Amount", 0),
                    d.get("Currency"),
                    d.get("ExeRate", 0),
                    d.get("AmountInclCurr", 0),
                )
                for d in bill_details
            ])

        # -------- CHECKOUT + FREE THE ROOM (same transaction) --------
        cursor.execute("""
            UPDATE hotel_tblreservation
            SET Current_Status = 'Checked Out', Check_Out = NOW()
            WHERE id = %s
        """, (reservationID,))

        cursor.execute("""
            UPDATE hotel_tblinhouse_guests
            SET is_active = 0, checked_out_at = NOW()
            WHERE reservation_id = %s AND is_active = 1
        """, (reservationID,))

        cursor.execute("""
            INSERT INTO hotel_tblhousekeeping
                (room_id, hk_date, hk_status, cleaned_at, cleaned_by, remarks)
            SELECT rd.room_id, %s, 'Dirty', NULL, NULL, 'Checkout'
            FROM hotel_tblreservation_details rd
            WHERE rd.Reservation_ID = %s AND rd.is_current = 1 AND rd.is_active = 1
            ON DUPLICATE KEY UPDATE
                hk_status = 'Dirty', cleaned_at = NULL,
                cleaned_by = NULL, remarks = VALUES(remarks)
        """, (date.today(), reservationID))

        mydb.commit()
        committed = True

        return jsonify({
            "message": "Complimentary bill created and room checked out successfully",
            "bill_id": bill_id,
            "reservationID": reservationID,
            "RoomCost": float(room_cost),
            "MealplanCost": float(meal_cost),
            "TotalCost": total_cost,
            "total_details": len(bill_details),
        }), 201

    except mysql_errors.IntegrityError as e:
        if mydb and not committed:
            _safe_rollback(mydb)
        if e.errno == 1062 and "uniq_comp_reservation" in str(e):
            return {"error": "Complimentary bill already exists for this reservation"}, 409
        # current_app.logger.exception("Integrity error in /complimentary-bill-by-id")
        return {"error": str(e)}, 500

    except Exception as e:
        if mydb and not committed:
            _safe_rollback(mydb)
        # current_app.logger.exception("Unhandled error in /complimentary-bill-by-id")
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass


# ---------------------------------------------------------------
# GET one complimentary bill + its details
#   /complimentary-bill?reservationID=123
#   /complimentary-bill?bill_id=45
# ---------------------------------------------------------------
@app_file502.route("/complimentary-bill", methods=["GET"])
@cross_origin()
def get_complimentary_bill():
    mydb = None
    cursor = None
    try:
        err = _check_token()
        if err:
            return err

        reservation_id = request.args.get("reservationID")
        bill_id = request.args.get("bill_id")
        if not reservation_id and not bill_id:
            return {"error": "Provide reservationID or bill_id"}, 400

        mydb = _connect()
        cursor = mydb.cursor(dictionary=True, buffered=True)

        if bill_id:
            cursor.execute(
                "SELECT * FROM hotel_tblcomplimentarybills WHERE id = %s LIMIT 1",
                (bill_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM hotel_tblcomplimentarybills WHERE reservationID = %s LIMIT 1",
                (reservation_id,),
            )
        bill = cursor.fetchone()
        if not bill:
            return {"error": "Complimentary bill not found"}, 404

        cursor.execute(
            "SELECT * FROM hotel_tblcomplimentarybilldetails WHERE bill_id = %s ORDER BY Date, id",
            (bill["id"],),
        )
        details = [_serialize(r) for r in cursor.fetchall()]

        return jsonify({
            "bill": _serialize(bill),
            "bill_details": details,
            "total_details": len(details),
        }), 200

    except Exception as e:
        # current_app.logger.exception("Error in GET /complimentary-bill")
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass


# ---------------------------------------------------------------
# GET list of complimentary bills (history), optional filters:
#   /complimentary-bills?fiscalYear=2083/84&from=2026-10-01&to=2026-10-31
#                       &limit=50&offset=0&include_details=1
# ---------------------------------------------------------------
@app_file502.route("/complimentary-bills", methods=["GET"])
@cross_origin()
def list_complimentary_bills():
    mydb = None
    cursor = None
    try:
        err = _check_token()
        if err:
            return err

        fiscal_year = request.args.get("fiscalYear")
        date_from = request.args.get("from")
        date_to = request.args.get("to")
        include_details = request.args.get("include_details") in ("1", "true", "True")
        try:
            limit = min(int(request.args.get("limit", 50)), 500)
            offset = max(int(request.args.get("offset", 0)), 0)
        except ValueError:
            return {"error": "limit and offset must be integers"}, 400

        where, params = ["1=1"], []
        if fiscal_year:
            where.append("fiscalYear = %s")
            params.append(fiscal_year)
        if date_from:
            where.append("Date >= %s")
            params.append(date_from)
        if date_to:
            where.append("Date <= %s")
            params.append(date_to)
        where_sql = " AND ".join(where)

        mydb = _connect()
        cursor = mydb.cursor(dictionary=True, buffered=True)

        cursor.execute(
            f"SELECT COUNT(*) AS total FROM hotel_tblcomplimentarybills WHERE {where_sql}",
            params,
        )
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"""SELECT * FROM hotel_tblcomplimentarybills
                WHERE {where_sql}
                ORDER BY id DESC
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        bills = [_serialize(r) for r in cursor.fetchall()]

        if include_details and bills:
            ids = [b["id"] for b in bills]
            placeholders = ", ".join(["%s"] * len(ids))
            cursor.execute(
                f"""SELECT * FROM hotel_tblcomplimentarybilldetails
                    WHERE bill_id IN ({placeholders})
                    ORDER BY bill_id, Date, id""",
                ids,
            )
            by_bill = {}
            for r in cursor.fetchall():
                by_bill.setdefault(r["bill_id"], []).append(_serialize(r))
            for b in bills:
                b["bill_details"] = by_bill.get(b["id"], [])

        return jsonify({
            "total": total,
            "limit": limit,
            "offset": offset,
            "bills": bills,
        }), 200

    except Exception as e:
        # current_app.logger.exception("Error in GET /complimentary-bills")
        return {"error": str(e)}, 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if mydb:
            try:
                mydb.close()
            except Exception:
                pass