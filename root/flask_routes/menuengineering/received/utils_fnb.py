from flask import Blueprint, jsonify, request
import mysql.connector
import os
from dotenv import load_dotenv
from flask_cors import cross_origin
from root.auth.check import token_auth
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

def get_db_connection_fnb():
    return mysql.connector.connect(
        host=os.getenv("host"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("database")
    )



def get_sales_data_for_snapshot(cursor, outlet_name, from_date, to_date, item_types=('Food', 'Beverage')):
    """
    Item-type-wise sales/discount/cost using the same order-by-order,
    item-by-item logic as receive_snapshot_details, so numbers reconcile.
    """
    def to_float(v):
        return float(v) if v is not None else 0.0

    cursor.execute("""
        SELECT
            idtblorderHistory as order_id,
            Total,
            VAT,
            DiscountAmt,
            bill_no,
            PaymentMode,
            (DiscountAmt / (Total - VAT)) * 100 AS discount_percent
        FROM tblorderhistory
        WHERE Outlet_Name = %s
            AND Date BETWEEN %s AND %s
            AND Total > 0
            AND (Total - VAT) > 0
    """, (outlet_name, from_date, to_date))
    orders = cursor.fetchall()

    type_wise_gross_sale = {t: 0.0 for t in item_types}
    type_wise_gross_cost = {t: 0.0 for t in item_types}
    type_wise_discount = {t: 0.0 for t in item_types}
    type_wise_complementary = {t: 0.0 for t in item_types}

    # for order in orders:
    #     order_id = order['order_id']
    #     discount_percent = order['discount_percent'] if order['discount_percent'] else 0
    #     is_complimentary = order['bill_no'] == '' and order['PaymentMode'] in ['Complimentary', 'Non Chargeable']
    for order in orders:
        order_id = order['order_id']
        discount_percent = to_float(order['discount_percent']) if order['discount_percent'] else 0
        is_complimentary = order['bill_no'] == '' and order['PaymentMode'] in ['Complimentary', 'Non Chargeable']
        cursor.execute("""
            SELECT ItemName, ItemType, Total, count, discountExempt
            FROM tblorder_detailshistory
            WHERE order_ID = %s
        """, (order_id,))
        items = cursor.fetchall()

        for item in items:
            item_type = item['ItemType']
            if not item_type or item_type not in item_types:
                continue

            item_total = to_float(item['Total'])
            item_count = to_float(item['count']) or 1

            cursor.execute("""
                SELECT costprice FROM recipe
                WHERE name = %s AND outlet = %s LIMIT 1
            """, (item['ItemName'], outlet_name))
            recipe = cursor.fetchone()
            item_cost = to_float(recipe['costprice']) * item_count if recipe else 0

            type_wise_gross_sale[item_type] += item_total
            type_wise_gross_cost[item_type] += item_cost

            if is_complimentary:
                type_wise_complementary[item_type] += item_total

            if discount_percent > 0 and item.get('discountExempt') != 'Yes':
                type_wise_discount[item_type] += item_total * (discount_percent / 100)

    gross_sales = sum(type_wise_gross_sale.values())
    gross_cost = sum(type_wise_gross_cost.values())
    gross_cost_percent = (gross_cost / gross_sales * 100) if gross_sales else 0

    return {
        'food_sales': type_wise_gross_sale.get('Food', 0.0),
        'beverage_sales': type_wise_gross_sale.get('Beverage', 0.0),
        'food_discount': type_wise_discount.get('Food', 0.0),
        'beverage_discount': type_wise_discount.get('Beverage', 0.0),
        'food_complimentary': type_wise_complementary.get('Food', 0.0),
        'beverage_complimentary': type_wise_complementary.get('Beverage', 0.0),
        'discounts_sales': sum(type_wise_discount.values()),
        'complimentary_sales': sum(type_wise_complementary.values()),
        'gross_sales': gross_sales,
        'gross_cost': gross_cost,   
        'gross_cost_percent': gross_cost_percent,
        'food_cost': type_wise_gross_cost.get('Food', 0.0),
        'beverage_cost': type_wise_gross_cost.get('Beverage', 0.0),
    }

def calculate_complimentary_cost_for_snapshot(cursor, outlet_name, from_date, to_date, item_types=('Food', 'Beverage')):
    """Complimentary cost by item type, using recipe cost (no fallback), matching endpoint-1 logic."""

    def to_float(val):
        return float(val) if val is not None else 0.0

    cursor.execute("""
        SELECT oh.idtblorderHistory
        FROM tblorderhistory oh
        WHERE oh.Outlet_Name = %s
            AND oh.Date BETWEEN %s AND %s
            AND oh.bill_no = ''
            AND oh.PaymentMode IN ('Complimentary', 'Non Chargeable')
    """, (outlet_name, from_date, to_date))
    complimentary_orders = cursor.fetchall()

    type_wise_complimentary_cost = {t: 0.0 for t in item_types}

    if not complimentary_orders:
        return type_wise_complimentary_cost

    for order in complimentary_orders:
        order_id = order['idtblorderHistory']

        cursor.execute("""
            SELECT od.ItemName, od.ItemType, od.count
            FROM tblorder_detailshistory od
            WHERE od.order_ID = %s
        """, (order_id,))
        items = cursor.fetchall()

        for item in items:
            item_type = item['ItemType']
            if not item_type or item_type not in item_types:
                continue

            cursor.execute("""
                SELECT costprice FROM recipe
                WHERE name = %s AND outlet = %s LIMIT 1
            """, (item['ItemName'], outlet_name))
            recipe = cursor.fetchone()

            quantity = to_float(item.get('count')) or 1
            item_cost = to_float(recipe['costprice']) * quantity if recipe else 0  # matches endpoint-1, no 0.6 fallback

            type_wise_complimentary_cost[item_type] += item_cost

    return type_wise_complimentary_cost

    
def calculate_employee_meal_cost(outlet_name, from_date, to_date, itemtype):
    """Calculate employee meal cost (Food/Beverage wise) from Staff Consumption"""
    try:
        mydb = get_db_connection_fnb()
        cursor = mydb.cursor(dictionary=True)

        query = """
            SELECT SUM(d.Amount * d.Rate) AS total_cost
            FROM intblstorerequisition r
            JOIN intblstorereqdetails d 
                ON r.idintblStoreRequisition = d.StoreReqID
            JOIN stock_statement s 
                ON s.ItemName = d.ItemName 
                AND s.OutletName = r.Outlet
            WHERE r.Date BETWEEN %s AND %s
              AND r.Outlet = %s
              AND r.CostCenter IN ('Staff Consumption', 'Staff Meal')
              AND s.Type = %s
        """

        cursor.execute(query, (from_date, to_date, outlet_name, itemtype))
        result = cursor.fetchone()

        total_cost = float(result["total_cost"] or 0)

        cursor.close()
        mydb.close()

        return round(total_cost, 2)

    except Exception as e:
        print(f"Error calculating employee meal cost: {str(e)}")
        return 0.0



def calculate_other_cost(outlet_name, from_date, to_date, itemtype):
    """Calculate Other Cost (Food/Beverage wise) excluding Kitchen, Bar, Staff Consumption"""
    try:
        mydb = get_db_connection_fnb()
        cursor = mydb.cursor(dictionary=True)

        query = """
            SELECT SUM(d.Amount * d.Rate) AS total_cost
            FROM intblstorerequisition r
            JOIN intblstorereqdetails d 
                ON r.idintblStoreRequisition = d.StoreReqID
            JOIN (
                SELECT ItemName, OutletName, MAX(Type) AS Type
                FROM stock_statement
                GROUP BY ItemName, OutletName
            ) s 
                ON s.ItemName = d.ItemName 
                AND s.OutletName = r.Outlet
            WHERE r.Date BETWEEN %s AND %s
              AND r.Outlet = %s
              AND r.CostCenter NOT IN ('Kitchen', 'Bar', 'Staff Consumption', 'Staff Meal', 'STAFF MEAL')
              AND LOWER(s.Type) = LOWER(%s)
        """

        cursor.execute(query, (from_date, to_date, outlet_name, itemtype))
        result = cursor.fetchone()

        total_cost = float(result["total_cost"] or 0)

        cursor.close()
        mydb.close()

        return round(total_cost, 2)

    except Exception as e:
        print(f"Error calculating other cost: {str(e)}")
        return 0.0