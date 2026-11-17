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


def get_sales_data_for_central_kitchen(cursor, outlet_name, from_date, to_date):
    """Get sales data for central kitchen (Finished Goods from store requisition)
    
    The cost calculation uses conversion factor to link production items to their recipes:
    Cost per unit = (Recipe cost price) / (Conversion factor)
    Total cost = (Cost per unit) * (Amount sold)
    """
    
    def to_float(value):
        if value is None:
            return 0.0
        return float(value)
    
    # Query to get sales data with proper cost calculation using conversion factor
    query = """
        SELECT 
            COALESCE(SUM(srd.Amount * srd.Rate), 0) AS gross_sales,
            COALESCE(SUM(
                CASE 
                    WHEN r.costprice IS NOT NULL AND cf.factor IS NOT NULL AND cf.factor > 0 
                    THEN (r.costprice / cf.factor) * srd.Amount
                    ELSE 0
                END
            ), 0) AS gross_cost
        FROM intblstorereqdetails srd
        JOIN intblstorerequisition sr 
            ON srd.StoreReqID = sr.idintblStoreRequisition
        LEFT JOIN stock_statement ss 
            ON ss.ItemName = srd.ItemName 
            AND ss.OutletName = sr.Outlet
        LEFT JOIN conversionfactor cf 
            ON cf.production_item_id = ss.id 
            AND cf.outlet = sr.Outlet
        LEFT JOIN recipe r 
            ON r.id = cf.production_recipe_id 
            AND r.outlet = sr.Outlet
        WHERE sr.Outlet = %s
            AND DATE(sr.Date) BETWEEN %s AND %s
            AND srd.GroupName = 'Finished Goods'
    """
    
    cursor.execute(query, (outlet_name, from_date, to_date))
    result = cursor.fetchone()
    
    gross_sales = to_float(result['gross_sales'])
    gross_cost = to_float(result['gross_cost'])
    
    # Calculate gross cost percentage
    gross_cost_percent = (gross_cost / gross_sales * 100) if gross_sales > 0 else 0
    
    return {
        'sales': gross_sales,
        'gross_cost': gross_cost,
        'gross_cost_percent': gross_cost_percent,
        'gross_sales': gross_sales
    }


from decimal import Decimal
from collections import defaultdict
from datetime import datetime

def adjust_production_item_after_sale(production_item_name, sold_qty, outlet, cursor, mydb, order_date):
    """
    Adjust inventory for production items (Finished Goods) when sold/transferred.
    """
    
    # Step 1: Get production item ID from stock_statement
    cursor.execute("""
        SELECT id, ItemName, GroupName, UOM
        FROM stock_statement 
        WHERE ItemName = %s AND OutletName = %s AND GroupName = 'Finished Goods'
    """, (production_item_name, outlet))
    
    stock_item = cursor.fetchone()
    if not stock_item:
        print(f"Production item '{production_item_name}' not found in stock_statement")
        return
    
    production_item_id = stock_item['id']
    
    # Step 2: Get conversion factor and production recipe ID
    cursor.execute("""
        SELECT factor, production_recipe_id
        FROM conversionfactor
        WHERE production_item_id = %s AND outlet = %s
    """, (production_item_id, outlet))
    
    conversion = cursor.fetchone()
    if not conversion:
        print(f"No conversion factor found for production_item_id: {production_item_id}")
        return
    
    factor = float(conversion['factor'])
    production_recipe_id = conversion['production_recipe_id']
    
    # Step 3: Get recipe type
    cursor.execute("""
        SELECT id, name, outlet, recipe_type, ItemType
        FROM recipe
        WHERE id = %s
    """, (production_recipe_id,))
    
    recipe_info = cursor.fetchone()
    if not recipe_info:
        print(f"No recipe found for production_recipe_id: {production_recipe_id}")
        return
    
    recipe_item_type = recipe_info['ItemType']
    
    # Determine cost center
    costcenter = "Central Kitchen" 
    # Step 4: Calculate actual production quantity
    actual_production_quantity = sold_qty / factor if factor > 0 else 0
    
    if actual_production_quantity <= 0:
        print(f"Invalid production quantity for {production_item_name}: {actual_production_quantity}")
        return
    
    # Step 5: Initialize ingredient aggregator
    aggregated_ingredients = defaultdict(float)
    
    # Step 6: Get direct recipe ingredients
    cursor.execute("""
        SELECT name, quantity
        FROM recipe_items 
        WHERE recipe_id = %s
    """, (production_recipe_id,))
    
    direct_ingredients = cursor.fetchall()
    
    for ingredient in direct_ingredients:
        ingredient_name = ingredient['name']
        recipe_quantity = float(ingredient['quantity'])
        total_consumption = recipe_quantity * actual_production_quantity
        aggregated_ingredients[ingredient_name] += total_consumption
    
    # Step 7: Get sub-recipe ingredients
    cursor.execute("""
        SELECT rs.sub_recipe_id, rs.quantity AS sub_recipe_qty
        FROM recipe_subrecipes rs
        WHERE rs.recipe_id = %s
    """, (production_recipe_id,))
    
    sub_recipes = cursor.fetchall()
    
    for sub_recipe in sub_recipes:
        sub_recipe_id = sub_recipe['sub_recipe_id']
        sub_recipe_qty = float(sub_recipe['sub_recipe_qty'])
        
        cursor.execute("""
            SELECT name, quantity
            FROM sub_recipe_items 
            WHERE sub_recipe_id = %s
        """, (sub_recipe_id,))
        
        sub_ingredients = cursor.fetchall()
        
        for sub_ingredient in sub_ingredients:
            ingredient_name = sub_ingredient['name']
            ingredient_quantity = float(sub_ingredient['quantity'])
            total_consumption = ingredient_quantity * sub_recipe_qty * actual_production_quantity
            aggregated_ingredients[ingredient_name] += total_consumption
    
    # Step 8: Subtract from inventory using FIFO
    print(f"\n--- Adjusting inventory for production item: {production_item_name}")
    print(f"Production quantity needed: {actual_production_quantity}")
    
    for ingredient_name, total_to_decrease in aggregated_ingredients.items():
        remaining_to_decrease = total_to_decrease
        
        while remaining_to_decrease > 0:
            # Get oldest stock with positive quantity
            cursor.execute("""
                SELECT id, quantity, rate FROM production_item_current_level
                WHERE itemname = %s AND outlet = %s AND quantity > 0 AND costcenter = %s
                ORDER BY id ASC LIMIT 1
            """, (ingredient_name, outlet, costcenter))
            
            stock_row = cursor.fetchone()
            
            if stock_row:
                item_id = stock_row['id']
                current_qty = float(stock_row['quantity'])
                rate = float(stock_row['rate'])
                
                if current_qty >= remaining_to_decrease:
                    new_qty = current_qty - remaining_to_decrease
                    
                    cursor.execute("""
                        UPDATE production_item_current_level SET quantity = %s WHERE id = %s
                    """, (new_qty, item_id))
                    
                    cursor.execute("""
                        INSERT INTO production_consumption_tracker 
                        (item_name, consumed_quantity, rate, outlet, recipe_name, order_date, ItemType)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ingredient_name, 
                        remaining_to_decrease, 
                        rate, 
                        outlet, 
                        production_item_name,
                        order_date,
                        recipe_item_type
                    ))
                    
                    print(f"✅ Consumed {remaining_to_decrease:.2f} {ingredient_name}")
                    remaining_to_decrease = 0
                    
                else:
                    cursor.execute("""
                        UPDATE production_item_current_level SET quantity = 0 WHERE id = %s
                    """, (item_id,))
                    
                    cursor.execute("""
                        INSERT INTO production_consumption_tracker 
                        (item_name, consumed_quantity, rate, outlet, recipe_name, order_date, ItemType)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ingredient_name, 
                        current_qty, 
                        rate, 
                        outlet, 
                        production_item_name,
                        order_date,
                        recipe_item_type
                    ))
                    
                    print(f"⚠️ Partially consumed {current_qty:.2f} {ingredient_name}")
                    remaining_to_decrease -= current_qty
                    
            else:
                print(f"❌ Not enough stock for ingredient: {ingredient_name}")
                break
    
    print(f"--- Finished adjusting inventory for {production_item_name}\n")