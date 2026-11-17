from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

from root.auth.check import token_auth
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

app_file488 = Blueprint('app_file488', __name__)

import calendar
from datetime import date, datetime, timedelta
import requests

def _get_front_office_block_by_bill_range(cursor, outlet, start_bill_id, end_bill_id):
    cursor.execute("""
        SELECT
            COALESCE(SUM(b.subTotal + b.DiscountAmt + b.VAT), 0) AS total_sale,
            COALESCE(SUM(b.subTotal), 0) AS total_net_sale,
            COALESCE(SUM(b.VAT), 0) AS vat,
            COALESCE(SUM(b.RoomRevenue), 0) AS room_revenue,
            COALESCE(SUM(b.MealplanRevenue), 0) AS mealplan_revenue,
            COALESCE(SUM(b.DiscountAmt), 0) AS discount,
            COALESCE(SUM(b.ExtraChargeSettlement), 0) AS ex_charge_settlement,
            COUNT(*) AS total_bills,
            COALESCE(SUM(b.DiscountAmt <> 0), 0) AS discounted_bills,
            MIN(b.Date) AS earliest_date,
            MAX(b.Date) AS latest_date
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE b.id BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
    """, (start_bill_id, end_bill_id, outlet))
    base = cursor.fetchone()

    # -------- NON-SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(b.PaymentMode)) AS mode, SUM(b.Total) AS amt
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE b.id BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
          AND LOWER(TRIM(b.PaymentMode)) != 'split'
        GROUP BY LOWER(TRIM(b.PaymentMode))
    """, (start_bill_id, end_bill_id, outlet))
    direct_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    # -------- SPLIT PAYMENT MODE SUMS (case-insensitive) --------
    cursor.execute("""
        SELECT LOWER(TRIM(p.PaymentMode)) AS mode, SUM(p.PaymentAmount) AS amt
        FROM hotel_tblbillpayments p
        JOIN hotel_tblhotelbills b ON p.bill_id = b.id
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE b.id BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
          AND LOWER(TRIM(b.PaymentMode)) = 'split'
        GROUP BY LOWER(TRIM(p.PaymentMode))
    """, (start_bill_id, end_bill_id, outlet))
    split_modes = {row["mode"]: float(row["amt"] or 0) for row in cursor.fetchall()}

    def mode_total(*names):
        return sum(direct_modes.get(n, 0) + split_modes.get(n, 0) for n in names)

    # -------- GUEST COUNT (for revenue-per-guest) --------
    cursor.execute("""
        SELECT COALESCE(SUM(gr.No_of_adults + gr.No_of_children), 0) AS total_guests
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        JOIN hotel_tblguestreservation gr ON gr.Reservation_ID = r.id AND gr.is_active = 1
        WHERE b.id BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
    """, (start_bill_id, end_bill_id, outlet))
    guest_row = cursor.fetchone()
    total_guests = int(guest_row["total_guests"] or 0)

    total_sale = float(base["total_sale"])
    # revenue_per_guest = round(total_sale / total_guests, 2) if total_guests > 0 else 0
    revenue_per_guest = round(float(base["room_revenue"]) / total_guests, 2) if total_guests > 0 else 0

    return {
        "Total Sale": total_sale,
        "Total Net Sale": float(base["total_net_sale"]),
        "Service Charge": 0,
        "VAT": float(base["vat"]),
        "Room Revenue": float(base["room_revenue"]),
        "Mealplan Revenue": float(base["mealplan_revenue"]),
        "Cash": mode_total("cash"),
        "Credit Card": mode_total("card"),
        "Mobile Payment": mode_total("mobile payment"),
        "Credit": mode_total("credit"),
        "Discount": float(base["discount"]),
        "Total Bills": int(base["total_bills"] or 0),
        "Discounted Bills": int(base["discounted_bills"] or 0),
        "Ex. Charge Settlement": float(base["ex_charge_settlement"]),
        "Total Guests": total_guests,
        "Revenue Per Guest": revenue_per_guest,
        "earliest_bill_date": str(base["earliest_date"]) if base["earliest_date"] else None,
        "latest_bill_date": str(base["latest_date"]) if base["latest_date"] else None,
    }

def _get_room_revenue_by_type(cursor, outlet, start_bill_id, end_bill_id):
    """
    Room revenue + meal revenue + ADR per room type for hotel bills in [start_bill_id, end_bill_id].
    ADR stays room-only (standard definition); meal revenue is reported next to it.
    ExeRate is 1/empty for base currency and e.g. 150 for USD, so a NULL or 0 rate falls back to 1.
    Rooms sold = distinct (room, night).
    Room types with no sales are included with zeros (types come from hotel_tblrooms).
    """
    # -------- ALL ACTIVE ROOM TYPES FOR THIS PROPERTY --------
    cursor.execute("""
        SELECT TRIM(room_type) AS room_type, COUNT(*) AS total_rooms
        FROM hotel_tblrooms
        WHERE outlet = %s AND is_active = 1
          AND room_type IS NOT NULL AND TRIM(room_type) != ''
        GROUP BY TRIM(room_type)
    """, (outlet,))
    inventory = {row["room_type"]: int(row["total_rooms"]) for row in cursor.fetchall()}

    # -------- SALES BY ROOM TYPE --------
    cursor.execute("""
        SELECT
            COALESCE(NULLIF(TRIM(bd.RoomType), ''), 'Unknown')                      AS room_type,
            COUNT(DISTINCT bd.RoomNumber, bd.Date)                                  AS rooms_sold,
            COALESCE(SUM(bd.RoomRate * COALESCE(NULLIF(bd.ExeRate, 0), 1)), 0)      AS room_revenue,
            COALESCE(SUM(COALESCE(bd.MealPlanAmt, 0)
                         * COALESCE(NULLIF(bd.ExeRate, 0), 1)), 0)                  AS meal_revenue
        FROM hotel_tblbilldetails bd
        JOIN hotel_tblhotelbills b   ON bd.bill_id = b.id
        JOIN hotel_tblreservation r  ON b.reservationID = r.id
        WHERE r.outlet = %s
          AND b.status = 1
          AND b.id BETWEEN %s AND %s
        GROUP BY COALESCE(NULLIF(TRIM(bd.RoomType), ''), 'Unknown')
    """, (outlet, start_bill_id, end_bill_id))
    sales = {row["room_type"]: row for row in cursor.fetchall()}

    # -------- MERGE: every room type, sold or not --------
    all_types = set(inventory) | set(sales)

    room_types = []
    total_revenue = 0.0
    total_meal_revenue = 0.0
    total_rooms_sold = 0

    for rt in all_types:
        sale = sales.get(rt)
        revenue = float(sale["room_revenue"]) if sale else 0.0
        meal_revenue = float(sale["meal_revenue"]) if sale else 0.0
        rooms_sold = int(sale["rooms_sold"]) if sale else 0

        room_types.append({
            "room_type": rt,
            "total_rooms": inventory.get(rt, 0),
            "rooms_sold": rooms_sold,
            "room_revenue": round(revenue, 2),
            "meal_revenue": round(meal_revenue, 2),
            "total_revenue": round(revenue + meal_revenue, 2),
            "adr": round(revenue / rooms_sold, 2) if rooms_sold else 0
        })
        total_revenue += revenue
        total_meal_revenue += meal_revenue
        total_rooms_sold += rooms_sold

    # Highest room revenue first; unsold types follow alphabetically
    room_types.sort(key=lambda x: (-x["room_revenue"], x["room_type"]))

    return {
        "room_types": room_types,
        "total": {
            "total_rooms": sum(inventory.values()),
            "rooms_sold": total_rooms_sold,
            "room_revenue": round(total_revenue, 2),
            "meal_revenue": round(total_meal_revenue, 2),
            "total_revenue": round(total_revenue + total_meal_revenue, 2),
            "adr": round(total_revenue / total_rooms_sold, 2) if total_rooms_sold else 0
        }
    }

def _get_guest_summary_by_bill_range(cursor, outlet, start_bill_id, end_bill_id):
    """
    Adults / children for the reservations behind hotel bills in [start_bill_id, end_bill_id],
    split into national / international / unknown by the booking guest's country,
    plus a VIP count (bookings made by a customer with is_vip = 1).
    Each reservation is counted once, even if it has several bills in the range.
    country 'Nepal' (any case, trimmed) = national; any other country = international;
    blank or missing country = unknown.
    """
    cursor.execute("""
        SELECT
            CASE
                WHEN c.country IS NULL OR TRIM(c.country) = '' THEN 'unknown'
                WHEN LOWER(TRIM(c.country)) = 'nepal'          THEN 'national'
                ELSE 'international'
            END                                                   AS nationality,
            COUNT(DISTINCT rb.reservationID)                      AS reservations,
            COALESCE(SUM(gr.No_of_adults), 0)                     AS adults,
            COALESCE(SUM(gr.No_of_children), 0)                   AS children,
            COUNT(DISTINCT CASE WHEN c.is_vip = 1
                                THEN rb.reservationID END)        AS vip_reservations,
            COALESCE(SUM(CASE WHEN c.is_vip = 1
                              THEN gr.No_of_adults ELSE 0 END), 0)   AS vip_adults,
            COALESCE(SUM(CASE WHEN c.is_vip = 1
                              THEN gr.No_of_children ELSE 0 END), 0) AS vip_children
        FROM (
            SELECT DISTINCT b.reservationID
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE r.outlet = %s
              AND b.status = 1
              AND b.id BETWEEN %s AND %s
        ) rb
        JOIN hotel_tblreservation res ON res.id = rb.reservationID
        LEFT JOIN customers c
               ON c.id = res.Guest_ID
        LEFT JOIN hotel_tblguestreservation gr
               ON gr.Reservation_ID = rb.reservationID AND gr.is_active = 1
        GROUP BY nationality
    """, (outlet, start_bill_id, end_bill_id))
    rows = {row["nationality"]: row for row in cursor.fetchall()}

    def bucket(name):
        row = rows.get(name)
        reservations = int(row["reservations"]) if row else 0
        adults = int(row["adults"]) if row else 0
        children = int(row["children"]) if row else 0
        return {
            "reservations": reservations,
            "adults": adults,
            "children": children,
            "total_guests": adults + children
        }

    national = bucket("national")
    international = bucket("international")
    unknown = bucket("unknown")

    reservations = national["reservations"] + international["reservations"] + unknown["reservations"]
    adults = national["adults"] + international["adults"] + unknown["adults"]
    children = national["children"] + international["children"] + unknown["children"]
    total_guests = adults + children

    # VIP totals are summed across the nationality groups (a VIP is also national/international)
    vip_reservations = sum(int(r["vip_reservations"] or 0) for r in rows.values())
    vip_adults = sum(int(r["vip_adults"] or 0) for r in rows.values())
    vip_children = sum(int(r["vip_children"] or 0) for r in rows.values())
    vip_guests = vip_adults + vip_children

    return {
        "reservations": reservations,
        "adults": adults,
        "children": children,
        "total_guests": total_guests,
        "avg_guests_per_reservation": round(total_guests / reservations, 2) if reservations else 0,
        "national_guests": national["total_guests"],
        "international_guests": international["total_guests"],
        "unknown_country_guests": unknown["total_guests"],
        "vip_reservations": vip_reservations,
        "vip_guests": vip_guests,
        "vip": {
            "reservations": vip_reservations,
            "adults": vip_adults,
            "children": vip_children,
            "total_guests": vip_guests
        },
        "by_nationality": {
            "national": national,
            "international": international,
            "unknown": unknown
        }
    }

def _get_inhouse_guest_summary(cursor, outlet):
    """
    Guest summary for reservations that are currently Registered (in-house) at this outlet.

    - Guests         : active rows in hotel_tblinhouse_guests (one row per person)
    - Nationality    : the in-house guest's own nationality
                       ('Nepal' = national, other = international, blank = unknown)
    - Adults/children: from hotel_tblguestreservation (reservation level)
    - VIP            : reservation.designation = 'VIP' -> all its in-house guests are VIP
    """
    # ---- 1) Reservation level: count, adults/children, VIP ----
    cursor.execute("""
        SELECT
            COUNT(*)                                                             AS reservations,
            COALESCE(SUM(t.adults), 0)                                           AS adults,
            COALESCE(SUM(t.children), 0)                                         AS children,
            COALESCE(SUM(t.is_vip), 0)                                           AS vip_reservations,
            COALESCE(SUM(CASE WHEN t.is_vip = 1 THEN t.adults   ELSE 0 END), 0)  AS vip_adults,
            COALESCE(SUM(CASE WHEN t.is_vip = 1 THEN t.children ELSE 0 END), 0)  AS vip_children
        FROM (
            SELECT
                r.id,
                CASE WHEN UPPER(TRIM(r.designation)) = 'VIP' THEN 1 ELSE 0 END AS is_vip,
                COALESCE((SELECT SUM(gr.No_of_adults)
                          FROM hotel_tblguestreservation gr
                          WHERE gr.Reservation_ID = r.id AND gr.is_active = 1), 0) AS adults,
                COALESCE((SELECT SUM(gr.No_of_children)
                          FROM hotel_tblguestreservation gr
                          WHERE gr.Reservation_ID = r.id AND gr.is_active = 1), 0) AS children
            FROM hotel_tblreservation r
            WHERE r.outlet = %s
              AND r.Current_Status = 'Registered'
        ) t
    """, (outlet,))
    res = cursor.fetchone() or {}

    # ---- 2) In-house guests by nationality (+ VIP guests) ----
    cursor.execute("""
        SELECT
            CASE
                WHEN g.nationality IS NULL OR TRIM(g.nationality) = '' THEN 'unknown'
                WHEN LOWER(TRIM(g.nationality)) IN ('nepal', 'nepali', 'nepalese') THEN 'national'
                ELSE 'international'
            END                                                   AS nationality,
            COUNT(*)                                              AS guests,
            COUNT(DISTINCT g.reservation_id)                      AS reservations,
            SUM(CASE WHEN UPPER(TRIM(r.designation)) = 'VIP' THEN 1 ELSE 0 END) AS vip_guests
        FROM hotel_tblinhouse_guests g
        JOIN hotel_tblreservation r ON r.id = g.reservation_id
        WHERE g.is_active = 1
          AND r.outlet = %s
          AND r.Current_Status = 'Registered'
        GROUP BY nationality
    """, (outlet,))
    rows = {row["nationality"]: row for row in cursor.fetchall()}

    def bucket(name):
        row = rows.get(name)
        return {
            "reservations": int(row["reservations"]) if row else 0,
            "total_guests": int(row["guests"]) if row else 0,
        }

    national = bucket("national")
    international = bucket("international")
    unknown = bucket("unknown")

    reservations = int(res.get("reservations") or 0)
    adults = int(res.get("adults") or 0)
    children = int(res.get("children") or 0)
    vip_reservations = int(res.get("vip_reservations") or 0)
    vip_adults = int(res.get("vip_adults") or 0)
    vip_children = int(res.get("vip_children") or 0)

    total_guests = national["total_guests"] + international["total_guests"] + unknown["total_guests"]
    vip_guests = sum(int(r["vip_guests"] or 0) for r in rows.values())

    return {
        "reservations": reservations,
        "adults": adults,
        "children": children,
        "total_guests": total_guests,
        "avg_guests_per_reservation": round(total_guests / reservations, 2) if reservations else 0,
        "national_guests": national["total_guests"],
        "international_guests": international["total_guests"],
        "unknown_country_guests": unknown["total_guests"],
        "vip_reservations": vip_reservations,
        "vip_guests": vip_guests,
        "vip": {
            "reservations": vip_reservations,
            "adults": vip_adults,
            "children": vip_children,
            "total_guests": vip_guests,
        },
        "by_nationality": {
            "national": national,
            "international": international,
            "unknown": unknown,
        },
    }

def _get_reservations_by_source(cursor, outlet, start_bill_id, end_bill_id):
    """
    Reservations (behind hotel bills in [start_bill_id, end_bill_id]) grouped by
    hotel_tblreservation.business_Src, e.g. Online / Walk In.
    Each reservation is counted once, even if it has several bills in the range.
    Revenue = RoomRevenue + MealplanRevenue from hotel_tblhotelbills.
    Blank or missing source is reported as 'Unknown'.
    """
    cursor.execute("""
        SELECT
            COALESCE(NULLIF(TRIM(r.business_Src), ''), 'Unknown')  AS source,
            COUNT(DISTINCT r.id)                                   AS reservations,
            COALESCE(SUM(b.RoomRevenue), 0)                        AS room_revenue,
            COALESCE(SUM(b.MealplanRevenue), 0)                    AS mealplan_revenue
        FROM hotel_tblhotelbills b
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE r.outlet = %s
          AND b.status = 1
          AND b.id BETWEEN %s AND %s
        GROUP BY source
        ORDER BY reservations DESC, source
    """, (outlet, start_bill_id, end_bill_id))
    rows = cursor.fetchall()

    total = sum(int(row["reservations"]) for row in rows)
    total_room = sum(float(row["room_revenue"]) for row in rows)
    total_meal = sum(float(row["mealplan_revenue"]) for row in rows)
    total_revenue = total_room + total_meal

    sources = []
    for row in rows:
        room = float(row["room_revenue"])
        meal = float(row["mealplan_revenue"])
        revenue = room + meal
        sources.append({
            "source": row["source"],
            "reservations": int(row["reservations"]),
            "share_pct": round(int(row["reservations"]) / total * 100, 2) if total else 0,
            "room_revenue": round(room, 2),
            "mealplan_revenue": round(meal, 2),
            "revenue": round(revenue, 2),
            "revenue_share_pct": round(revenue / total_revenue * 100, 2) if total_revenue else 0,
        })

    return {
        "total_reservations": total,
        "total_room_revenue": round(total_room, 2),
        "total_mealplan_revenue": round(total_meal, 2),
        "total_revenue": round(total_revenue, 2),
        "sources": sources,
    }

def _get_forex_receipts_by_bill_range(cursor, outlet, start_bill_id, end_bill_id):
    """
    Foreign currency actually received on hotel bills in [start_bill_id, end_bill_id],
    from hotel_tblbillforexreceipts.
 
    Per currency: number of bills, amount received (in that currency), its local value
    (AmountLocal = amount * rate at the time of receipt), average rate, and a split
    by payment mode (cash / card / ...).
 
    NOTE: this is a breakdown, not an extra amount. The bill's Total is already counted
    under Cash / Credit Card / etc. in the sales block, and the local value of the
    foreign currency is part of that figure.
    """
    # -------- PER CURRENCY --------
    cursor.execute("""
        SELECT UPPER(TRIM(f.Currency))                    AS currency,
               COUNT(DISTINCT f.bill_id)                  AS bills,
               COALESCE(SUM(f.AmountReceived), 0)         AS amount_received,
               COALESCE(SUM(f.AmountLocal), 0)            AS local_value
        FROM hotel_tblbillforexreceipts f
        JOIN hotel_tblhotelbills b  ON f.bill_id = b.id
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE b.id BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
        GROUP BY UPPER(TRIM(f.Currency))
        ORDER BY local_value DESC
    """, (start_bill_id, end_bill_id, outlet))
    by_currency = cursor.fetchall()
 
    # -------- PER CURRENCY + PAYMENT MODE --------
    cursor.execute("""
        SELECT UPPER(TRIM(f.Currency))                    AS currency,
               LOWER(TRIM(f.PaymentMode))                 AS mode,
               COALESCE(SUM(f.AmountReceived), 0)         AS amount_received,
               COALESCE(SUM(f.AmountLocal), 0)            AS local_value
        FROM hotel_tblbillforexreceipts f
        JOIN hotel_tblhotelbills b  ON f.bill_id = b.id
        JOIN hotel_tblreservation r ON b.reservationID = r.id
        WHERE b.id BETWEEN %s AND %s AND r.outlet = %s AND b.status = 1
        GROUP BY UPPER(TRIM(f.Currency)), LOWER(TRIM(f.PaymentMode))
    """, (start_bill_id, end_bill_id, outlet))
 
    modes = {}
    for row in cursor.fetchall():
        modes.setdefault(row["currency"], {})[row["mode"]] = {
            "amount_received": round(float(row["amount_received"]), 2),
            "local_value": round(float(row["local_value"]), 2),
        }
 
    currencies = []
    total_local = 0.0
    for row in by_currency:
        received = float(row["amount_received"])
        local = float(row["local_value"])
        total_local += local
        currencies.append({
            "currency": row["currency"],
            "bills": int(row["bills"]),
            "amount_received": round(received, 2),
            "local_value": round(local, 2),
            "avg_rate": round(local / received, 4) if received else 0,
            "by_payment_mode": modes.get(row["currency"], {}),
        })
 
    return {
        "total_local_value": round(total_local, 2),
        "currencies": currencies,
    }

def _get_advance_received_by_reservation_range(cursor, outlet, start_res_id, end_res_id):
    """
    Advance payments on reservations created in [start_res_id, end_res_id] for this outlet
    (the same reservation range close-day stores). Grouped by currency.
    Local value = Advance_Payment_Local, falling back to Advance_Payment for base-currency rows.
    """
    empty = {
        "total_local_value": 0.0,
        "total_reservations": 0,
        "currencies": [],
        "reservations": [],
    }
    if start_res_id is None or end_res_id is None:
        return empty

    # -------- PER CURRENCY --------
    cursor.execute("""
        SELECT
            COALESCE(NULLIF(UPPER(TRIM(Advance_Payment_Currency)), ''), 'LOCAL') AS currency,
            COUNT(*)                                                           AS reservations,
            COALESCE(SUM(Advance_Payment), 0)                                  AS amount_received,
            COALESCE(SUM(COALESCE(Advance_Payment_Local, Advance_Payment)), 0) AS local_value
        FROM hotel_tblreservation
        WHERE outlet = %s
          AND id BETWEEN %s AND %s
          AND is_active = 1
          AND COALESCE(Advance_Payment, 0) > 0
        GROUP BY COALESCE(NULLIF(UPPER(TRIM(Advance_Payment_Currency)), ''), 'LOCAL')
        ORDER BY local_value DESC
    """, (outlet, start_res_id, end_res_id))
    rows = cursor.fetchall()

    # -------- PER RESERVATION (for reconciliation) --------
    cursor.execute("""
        SELECT r.id,
               r.reservation_outlet_id,
               r.Reservation_Date,
               r.Current_Status,
               r.Pay_Mode,
               COALESCE(NULLIF(UPPER(TRIM(r.Advance_Payment_Currency)), ''), 'LOCAL') AS currency,
               r.Advance_Payment,
               COALESCE(r.Advance_Payment_Local, r.Advance_Payment)                   AS local_value
        FROM hotel_tblreservation r
        WHERE r.outlet = %s
          AND r.id BETWEEN %s AND %s
          AND r.is_active = 1
          AND COALESCE(r.Advance_Payment, 0) > 0
        ORDER BY r.id
    """, (outlet, start_res_id, end_res_id))
    detail = cursor.fetchall()

    currencies = []
    total_local = 0.0
    total_res = 0
    for row in rows:
        received = float(row["amount_received"])
        local = float(row["local_value"])
        total_local += local
        total_res += int(row["reservations"])
        currencies.append({
            "currency": row["currency"],
            "reservations": int(row["reservations"]),
            "amount_received": round(received, 2),
            "local_value": round(local, 2),
        })

    return {
        "total_local_value": round(total_local, 2),
        "total_reservations": total_res,
        "currencies": currencies,
        "reservations": [
            {
                "reservation_id": d["id"],
                "reservation_outlet_id": d["reservation_outlet_id"],
                "reservation_date": str(d["Reservation_Date"]) if d["Reservation_Date"] else None,
                "status": d["Current_Status"],
                "pay_mode": d["Pay_Mode"],
                "currency": d["currency"],
                "amount": float(d["Advance_Payment"]),
                "local_value": float(d["local_value"]),
            }
            for d in detail
        ],
    }


from root.flask_routes.hotel.generalbills.generalbill import BILL_TYPES, CREDIT_PAYMENT_MODES
def _get_general_bills_since_last_close(cursor, property_id, outlet):
    def f(v):
        return float(v) if v is not None else 0.0

    # last closed end id per bill type for this property
    cursor.execute("""
        SELECT g.bill_type, MAX(g.end_bill_id) AS last_end
        FROM hotel_close_day_generalbills g
        JOIN hotel_close_day cd ON g.close_day_id = cd.id
        WHERE cd.property_id = %s
        GROUP BY g.bill_type
    """, (property_id,))
    last_gb = {r["bill_type"]: r["last_end"] for r in cursor.fetchall()}

    # pending range per bill type (same logic as close day)
    ranges = []
    for bt in sorted(BILL_TYPES):
        cursor.execute("""
            SELECT MIN(id) AS start_id, MAX(id) AS end_id, COUNT(*) AS cnt
            FROM hotel_generalbills
            WHERE outlet = %s AND bill_type = %s AND id > %s
        """, (outlet, bt, last_gb.get(bt, 0)))
        r = cursor.fetchone()
        if r["start_id"] is not None:
            ranges.append({"bill_type": bt, "start_bill_id": r["start_id"],
                           "end_bill_id": r["end_id"], "bill_count": r["cnt"]})

    empty = {
        "ranges": [], "sales_by_type": [], "totals": {
            "bills": 0, "sub_total": 0.0, "discount_amount": 0.0, "taxable_amount": 0.0,
            "tax_amount": 0.0, "grand_total": 0.0,
            "settled_total": 0.0, "room_charge_credit_total": 0.0},
        "voided_bills": 0,
        "forex": {"total_local_value": 0.0, "by_currency": []},
    }
    if not ranges:
        return empty

    cond = " OR ".join(["(gb.bill_type = %s AND gb.id BETWEEN %s AND %s)"] * len(ranges))
    cond_params = []
    for r in ranges:
        cond_params += [r["bill_type"], r["start_bill_id"], r["end_bill_id"]]

    # sales by type and payment mode (active bills only)
    cursor.execute(f"""
        SELECT gb.bill_type, gb.payment_mode, COUNT(*) AS bills,
               SUM(gb.sub_total) AS sub_total, SUM(gb.discount_amount) AS discount_amount,
               SUM(gb.taxable_amount) AS taxable_amount, SUM(gb.tax_amount) AS tax_amount,
               SUM(gb.grand_total) AS grand_total
        FROM hotel_generalbills gb
        WHERE gb.outlet = %s AND gb.status = 1 AND ({cond})
        GROUP BY gb.bill_type, gb.payment_mode
        ORDER BY gb.bill_type, gb.payment_mode
    """, tuple([outlet] + cond_params))
    rows = cursor.fetchall()

    sales_by_type = [{
        "bill_type": r["bill_type"], "payment_mode": r["payment_mode"], "bills": r["bills"],
        "sub_total": f(r["sub_total"]), "discount_amount": f(r["discount_amount"]),
        "taxable_amount": f(r["taxable_amount"]), "tax_amount": f(r["tax_amount"]),
        "grand_total": f(r["grand_total"]),
    } for r in rows]

    totals = dict(empty["totals"])
    for r in sales_by_type:
        totals["bills"] += r["bills"]
        for k in ("sub_total", "discount_amount", "taxable_amount", "tax_amount", "grand_total"):
            totals[k] += r[k]
        if r["payment_mode"] in CREDIT_PAYMENT_MODES:
            totals["room_charge_credit_total"] += r["grand_total"]
        else:
            totals["settled_total"] += r["grand_total"]

    # voided bills in the range (shown separately, not in totals)
    cursor.execute(f"""
        SELECT COUNT(*) AS n FROM hotel_generalbills gb
        WHERE gb.outlet = %s AND gb.status = 0 AND ({cond})
    """, tuple([outlet] + cond_params))
    voided = cursor.fetchone()["n"]

    # forex received on those bills
    cursor.execute(f"""
        SELECT fr.Currency, SUM(fr.AmountReceived) AS amount_received,
               SUM(fr.AmountLocal) AS amount_local, COUNT(*) AS receipts
        FROM hotel_generalbill_forex_receipts fr
        JOIN hotel_generalbills gb ON gb.id = fr.bill_id
        WHERE gb.outlet = %s AND gb.status = 1 AND ({cond})
        GROUP BY fr.Currency
        ORDER BY fr.Currency
    """, tuple([outlet] + cond_params))
    by_currency = [{
        "currency": r["Currency"], "receipts": r["receipts"],
        "amount_received": f(r["amount_received"]), "amount_local": f(r["amount_local"]),
    } for r in cursor.fetchall()]

    return {
        "ranges": ranges,
        "sales_by_type": sales_by_type,
        "totals": totals,
        "voided_bills": voided,
        "forex": {
            "total_local_value": sum(c["amount_local"] for c in by_currency),
            "by_currency": by_currency,
        },
    }

@app_file488.route("/front_office_sales_since_last_close", methods=["POST"])
@cross_origin()
def front_office_sales_since_last_close():
    mydb = None
    try:
        # -------- INPUT + TOKEN (from body) --------
        body = request.get_json(silent=True) or {}

        token = body.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        outlet = body.get("outlet")  # hotel property name (matches hotel_tblreservation.outlet)
        if not outlet:
            return {"error": "outlet is required"}, 400

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- RESOLVE property_id FROM name --------
        cursor.execute("SELECT id FROM hotel_company_property WHERE name = %s", (outlet,))
        property_row = cursor.fetchone()
        if not property_row:
            return {"error": "Company property not found."}, 404
        property_id = property_row["id"]

        # # -------- LAST CLOSED end_bill_id (same logic as close-day) --------
        # cursor.execute("""
        #     SELECT end_bill_id
        #     FROM hotel_close_day
        #     WHERE property_id = %s AND end_bill_id IS NOT NULL
        #     ORDER BY id DESC
        #     LIMIT 1
        # """, (property_id,))
        # last_entry = cursor.fetchone()
        # last_bill = last_entry["end_bill_id"] if last_entry else 0

        # -------- LAST CLOSED POSITIONS (same logic as close-day) --------
        cursor.execute("""
            SELECT
              (SELECT end_bill_id FROM hotel_close_day
                WHERE property_id = %s AND end_bill_id IS NOT NULL
                ORDER BY id DESC LIMIT 1) AS last_bill,
              (SELECT end_reservation_id FROM hotel_close_day
                WHERE property_id = %s AND end_reservation_id IS NOT NULL
                ORDER BY id DESC LIMIT 1) AS last_res
        """, (property_id, property_id))
        last = cursor.fetchone()
        last_bill = last["last_bill"] or 0
        last_res = last["last_res"] or 0

        # -------- PENDING BILL RANGE --------
        cursor.execute("""
            SELECT MIN(b.id) AS start_id, MAX(b.id) AS end_id
            FROM hotel_tblhotelbills b
            JOIN hotel_tblreservation r ON b.reservationID = r.id
            WHERE r.outlet = %s AND b.id > %s
        """, (outlet, last_bill))
        rng = cursor.fetchone()
        start_bill_id, end_bill_id = rng["start_id"], rng["end_id"]

        # if start_bill_id is None:
        #     return jsonify({
        #         "outlet": outlet,
        #         "start_bill_id": None,
        #         "end_bill_id": None,
        #         "has_new_bills": False
        #     }), 200
        
        # -------- PENDING RESERVATION RANGE (same as close-day) --------
        cursor.execute("""
            SELECT MIN(id) AS start_id, MAX(id) AS end_id
            FROM hotel_tblreservation
            WHERE outlet = %s AND id > %s
        """, (outlet, last_res))
        res = cursor.fetchone()
        start_res_id, end_res_id = res["start_id"], res["end_id"]
        advance_block = _get_advance_received_by_reservation_range(
            cursor, outlet, start_res_id, end_res_id
        )
        general_block = _get_general_bills_since_last_close(cursor, property_id, outlet)

        # no new bills: still return the advance block, since advances can exist without bills
        if start_bill_id is None:
            return jsonify({
                "outlet": outlet,
                "start_bill_id": None,
                "end_bill_id": None,
                "start_reservation_id": start_res_id,
                "end_reservation_id": end_res_id,
                "has_new_bills": False,
                "Advance Received": advance_block["total_local_value"],
                "advance_received": advance_block,
                "general_bills": general_block,
                "GeneralBillsForex": general_block["forex"]["total_local_value"],
            }), 200

        sales_block = _get_front_office_block_by_bill_range(cursor, outlet, start_bill_id, end_bill_id)
        room_revenue_block = _get_room_revenue_by_type(cursor, outlet, start_bill_id, end_bill_id)
        # guest_block = _get_guest_summary_by_bill_range(cursor, outlet, start_bill_id, end_bill_id)
        guest_block = _get_inhouse_guest_summary(cursor, outlet)
        source_block = _get_reservations_by_source(cursor, outlet, start_bill_id, end_bill_id)
        forex_block = _get_forex_receipts_by_bill_range(cursor, outlet, start_bill_id, end_bill_id)

        return jsonify({
            "outlet": outlet,
            "start_bill_id": start_bill_id,
            "end_bill_id": end_bill_id,
            "start_reservation_id": start_res_id,
            "end_reservation_id": end_res_id,
            "has_new_bills": True,
            **sales_block,
            "room_revenue_by_type": room_revenue_block,
            "guest_summary": guest_block,
            "reservations_by_source": source_block,
            # "Foreign Currency": forex_block["total_local_value"],
            "forex_receipts": forex_block,
            "Advance Received": advance_block["total_local_value"],
            "advance_received": advance_block,
            "general_bills": general_block,
            "GeneralBillsForex": general_block["forex"]["total_local_value"],
            "ForeignCurrency": float(forex_block["total_local_value"] or 0)
                                + general_block["forex"]["total_local_value"],
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()

from datetime import datetime, date

@app_file488.route("/frontoffice/reservations_since_last_close", methods=["GET"])
@cross_origin()
def reservations_since_last_close():
    mydb = None
    try:
        # -------- TOKEN (header) --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return {"error": "Invalid Authorization header format."}, 400
        if not token_auth(parts[1]):
            return {"error": "Invalid token."}, 400

        # -------- INPUT --------
        outlet = request.args.get("outlet")  # hotel property name
        include_details = request.args.get("details", "false").lower() == "true"

        if not outlet:
            return {"error": "outlet is required"}, 400

        today = date.today()

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- PROPERTY --------
        cursor.execute("SELECT id FROM hotel_company_property WHERE name = %s", (outlet,))
        prop = cursor.fetchone()
        if not prop:
            return {"error": "Property not found"}, 404
        property_id = prop["id"]

        # -------- LAST CLOSE (latest row that has a reservation range) --------
        cursor.execute("""
            SELECT id, business_date, end_reservation_id, closed_at
            FROM hotel_close_day
            WHERE property_id = %s
              AND end_reservation_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
        """, (property_id,))
        last_close = cursor.fetchone()

        # No previous close -> everything counts as "since last close"
        last_end_reservation_id = int(last_close["end_reservation_id"]) if last_close else 0

        # -------- RESERVATIONS AFTER THE LAST CLOSE --------
        # One row per reservation (guest rows collapsed with MIN/MAX),
        # rooms taken from fitrate so they are not multiplied by guest rows.
        cursor.execute("""
            SELECT
                r.id AS reservation_id,
                r.Current_Status AS status,
                MIN(gr.start_date) AS start_date,
                MAX(gr.end_date)   AS end_date,
                (SELECT COALESCE(SUM(fr.quantity), 0)
                   FROM hotel_tblfitrate fr
                  WHERE fr.reservationID = r.id AND fr.is_active = 1) AS rooms
            FROM hotel_tblreservation r
            JOIN hotel_tblguestreservation gr
              ON gr.Reservation_ID = r.id AND gr.is_active = 1
            WHERE r.is_active = 1
              AND r.outlet = %s
              AND r.id > %s
              AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out', 'Cancelled')
            GROUP BY r.id, r.Current_Status
            ORDER BY r.id
        """, (outlet, last_end_reservation_id))
        rows = cursor.fetchall()

        # -------- CLASSIFY --------
        def bucket_template():
            return {"reservations": 0, "rooms": 0}

        summary = {
            "confirmed":       bucket_template(),  # Reserved + Registered (same as rooms-confirmed API)
            "checked_in":      bucket_template(),  # Registered
            "checked_out":     bucket_template(),  # Checked Out
            "no_show":         bucket_template(),  # Reserved, arrival date already passed
            "cancelled":       bucket_template(),  # Cancelled
            "pending_arrival": bucket_template(),  # Reserved, arrival today or later
        }
        details = []

        def add(bucket, rooms):
            summary[bucket]["reservations"] += 1
            summary[bucket]["rooms"] += rooms

        for row in rows:
            status = row["status"]
            start_date = row["start_date"]
            end_date = row["end_date"]
            rooms = int(row["rooms"] or 0) or 1  # a reservation holds at least one room

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            buckets = []
            if status == "Reserved":
                buckets.append("confirmed")
                buckets.append("pending_arrival" if start_date >= today else "no_show")
            elif status == "Registered":
                buckets.append("confirmed")
                buckets.append("checked_in")
            elif status == "Checked Out":
                buckets.append("checked_out")
            elif status == "Cancelled":
                buckets.append("cancelled")

            for b in buckets:
                add(b, rooms)

            if include_details:
                details.append({
                    "reservation_id": row["reservation_id"],
                    "status": status,
                    "buckets": buckets,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "rooms": rooms
                })

        response = {
            "outlet": outlet,
            "as_of_date": today.strftime("%Y-%m-%d"),
            "last_close": {
                "business_date": last_close["business_date"].strftime("%Y-%m-%d"),
                "end_reservation_id": last_end_reservation_id,
                "closed_at": last_close["closed_at"].strftime("%Y-%m-%d %H:%M:%S")
            } if last_close else None,
            "from_reservation_id": last_end_reservation_id + 1,
            "total_reservations": len(rows),
            **summary
        }

        if include_details:
            response["reservations"] = details

        return jsonify(response), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()


def _get_general_bills_by_ranges(cursor, outlet, ranges):
    """
    Same output as _get_general_bills_since_last_close, but for explicit per-type
    ranges (e.g. the rows saved in hotel_close_day_generalbills for a closed day).

    ranges: list of {"bill_type", "start_bill_id", "end_bill_id", "bill_count"}
    """
    def f(v):
        return float(v) if v is not None else 0.0

    empty = {
        "ranges": [], "sales_by_type": [], "totals": {
            "bills": 0, "sub_total": 0.0, "discount_amount": 0.0, "taxable_amount": 0.0,
            "tax_amount": 0.0, "grand_total": 0.0,
            "settled_total": 0.0, "room_charge_credit_total": 0.0},
        "voided_bills": 0,
        "forex": {"total_local_value": 0.0, "by_currency": []},
    }

    ranges = [r for r in (ranges or [])
              if r.get("start_bill_id") is not None and r.get("end_bill_id") is not None]
    if not ranges:
        return empty

    cond = " OR ".join(["(gb.bill_type = %s AND gb.id BETWEEN %s AND %s)"] * len(ranges))
    cond_params = []
    for r in ranges:
        cond_params += [r["bill_type"], r["start_bill_id"], r["end_bill_id"]]

    # sales by type and payment mode (active bills only)
    cursor.execute(f"""
        SELECT gb.bill_type, gb.payment_mode, COUNT(*) AS bills,
               SUM(gb.sub_total) AS sub_total, SUM(gb.discount_amount) AS discount_amount,
               SUM(gb.taxable_amount) AS taxable_amount, SUM(gb.tax_amount) AS tax_amount,
               SUM(gb.grand_total) AS grand_total
        FROM hotel_generalbills gb
        WHERE gb.outlet = %s AND gb.status = 1 AND ({cond})
        GROUP BY gb.bill_type, gb.payment_mode
        ORDER BY gb.bill_type, gb.payment_mode
    """, tuple([outlet] + cond_params))
    rows = cursor.fetchall()

    sales_by_type = [{
        "bill_type": r["bill_type"], "payment_mode": r["payment_mode"], "bills": r["bills"],
        "sub_total": f(r["sub_total"]), "discount_amount": f(r["discount_amount"]),
        "taxable_amount": f(r["taxable_amount"]), "tax_amount": f(r["tax_amount"]),
        "grand_total": f(r["grand_total"]),
    } for r in rows]

    totals = dict(empty["totals"])
    for r in sales_by_type:
        totals["bills"] += r["bills"]
        for k in ("sub_total", "discount_amount", "taxable_amount", "tax_amount", "grand_total"):
            totals[k] += r[k]
        if r["payment_mode"] in CREDIT_PAYMENT_MODES:
            totals["room_charge_credit_total"] += r["grand_total"]
        else:
            totals["settled_total"] += r["grand_total"]

    # voided bills in the ranges (shown separately, not in totals)
    cursor.execute(f"""
        SELECT COUNT(*) AS n FROM hotel_generalbills gb
        WHERE gb.outlet = %s AND gb.status = 0 AND ({cond})
    """, tuple([outlet] + cond_params))
    voided = cursor.fetchone()["n"]

    # forex received on those bills
    cursor.execute(f"""
        SELECT fr.Currency, SUM(fr.AmountReceived) AS amount_received,
               SUM(fr.AmountLocal) AS amount_local, COUNT(*) AS receipts
        FROM hotel_generalbill_forex_receipts fr
        JOIN hotel_generalbills gb ON gb.id = fr.bill_id
        WHERE gb.outlet = %s AND gb.status = 1 AND ({cond})
        GROUP BY fr.Currency
        ORDER BY fr.Currency
    """, tuple([outlet] + cond_params))
    by_currency = [{
        "currency": r["Currency"], "receipts": r["receipts"],
        "amount_received": f(r["amount_received"]), "amount_local": f(r["amount_local"]),
    } for r in cursor.fetchall()]

    return {
        "ranges": ranges,
        "sales_by_type": sales_by_type,
        "totals": totals,
        "voided_bills": voided,
        "forex": {
            "total_local_value": sum(c["amount_local"] for c in by_currency),
            "by_currency": by_currency,
        },
    }

@app_file488.route("/front_office_sales_by_close_day", methods=["POST"])
@cross_origin()
def front_office_sales_by_close_day():
    mydb = None
    try:
        body = request.get_json(silent=True) or {}

        token = body.get("token")
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        outlet = body.get("outlet")
        business_date = body.get("business_date")
        if not outlet or not business_date:
            return {"error": "outlet and business_date are required"}, 400
        try:
            parsed_date = datetime.strptime(business_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- PROPERTY --------
        cursor.execute("SELECT id FROM hotel_company_property WHERE name = %s", (outlet,))
        property_row = cursor.fetchone()
        if not property_row:
            return {"error": "Company property not found."}, 404
        property_id = property_row["id"]

        # -------- CLOSE RECORD FOR THAT BUSINESS DATE --------
        cursor.execute("""
            SELECT id, business_date, start_bill_id, end_bill_id,
                   start_reservation_id, end_reservation_id, closed_by
            FROM hotel_close_day
            WHERE property_id = %s AND business_date = %s
        """, (property_id, parsed_date))
        close = cursor.fetchone()
        if not close:
            return {"error": "No closed day found for this outlet and business date."}, 404

        start_bill_id = close["start_bill_id"]
        end_bill_id = close["end_bill_id"]
        start_res_id = close["start_reservation_id"]
        end_res_id = close["end_reservation_id"]

        # -------- GENERAL BILL RANGES SAVED AT CLOSE --------
        cursor.execute("""
            SELECT bill_type, start_bill_id, end_bill_id, bill_count
            FROM hotel_close_day_generalbills
            WHERE close_day_id = %s
        """, (close["id"],))
        general_ranges = cursor.fetchall()

        advance_block = _get_advance_received_by_reservation_range(
            cursor, outlet, start_res_id, end_res_id
        )
        general_block = _get_general_bills_by_ranges(cursor, outlet, general_ranges)

        base = {
            "outlet": outlet,
            "business_date": str(close["business_date"]),
            "close_day_id": close["id"],
            "closed_by": close["closed_by"],
            "start_bill_id": start_bill_id,
            "end_bill_id": end_bill_id,
            "start_reservation_id": start_res_id,
            "end_reservation_id": end_res_id,
            "Advance Received": advance_block["total_local_value"],
            "advance_received": advance_block,
            "general_bills": general_block,
            "GeneralBillsForex": general_block["forex"]["total_local_value"],
        }

        # that session had no hotel bills (only advances / general bills)
        if start_bill_id is None:
            return jsonify({**base, "has_new_bills": False}), 200

        sales_block = _get_front_office_block_by_bill_range(cursor, outlet, start_bill_id, end_bill_id)
        room_revenue_block = _get_room_revenue_by_type(cursor, outlet, start_bill_id, end_bill_id)
        source_block = _get_reservations_by_source(cursor, outlet, start_bill_id, end_bill_id)
        forex_block = _get_forex_receipts_by_bill_range(cursor, outlet, start_bill_id, end_bill_id)

        return jsonify({
            **base,
            "has_new_bills": True,
            **sales_block,
            "room_revenue_by_type": room_revenue_block,
            "reservations_by_source": source_block,
            "forex_receipts": forex_block,
            "ForeignCurrency": float(forex_block["total_local_value"] or 0)
                               + general_block["forex"]["total_local_value"],
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        if mydb:
            mydb.close()