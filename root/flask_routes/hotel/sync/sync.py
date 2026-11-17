# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()
# from root.auth.check import token_auth

# app_file417 = Blueprint('app_file417', __name__)

# # @app_file417.route("/unsynced/data", methods=["GET"])
# # @cross_origin()
# # def get_unassigned_data():
# #     """
# #     API to fetch all unassigned data (rates, meal prices, and reservations)
# #     where outlet_rate_id or reservation_outlet_id is null
# #     """
# #     try:
# #         mydb = mysql.connector.connect(
# #             host=os.getenv("host"),
# #             user=os.getenv("user"),
# #             password=os.getenv("password"),
# #             database=os.getenv("database")
# #         )

# #         cursor = mydb.cursor(dictionary=True, buffered=True)

# #         # -------- TOKEN FROM HEADER --------
# #         auth_header = request.headers.get("Authorization")

# #         if not auth_header:
# #             return {"error": "No token provided."}, 400

# #         try:
# #             token = auth_header.split(" ")[1]  # Remove "Bearer"
# #         except:
# #             return {"error": "Invalid Authorization header format."}, 400

# #         if not token:
# #             return {"error": "No token provided."}, 400

# #         if not token_auth(token):
# #             return {"error": "Invalid token."}, 400

# #         # Get filter parameters
# #         data_type = request.args.get('type', 'all')  # 'rates', 'meal_prices', 'reservations', or 'all'
        
# #         response_data = {}
        
# #         # 3. Fetch unassigned reservations with all related data
# #         if data_type in ['all', 'reservations']:
# #             # First, get all unassigned reservations
# #             # cursor.execute("""
# #             #     SELECT 
# #             #         r.*,
# #             #         c.name as guest_name,
# #             #         c.address as guest_address,
# #             #         c.guestPan as guest_tax_number,
# #             #         c.phone as guest_phone,
# #             #         c.email as guest_email,
# #             #         c.country,
# #             #         e.userName as employee_name
# #             #     FROM hotel_tblreservation r
# #             #     LEFT JOIN customers c ON r.Guest_ID = c.id
# #             #     LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
# #             #     WHERE r.reservation_outlet_id IS NULL 
# #             #     AND r.is_active = 1
# #             #     ORDER BY r.id DESC
# #             # """)

# #             cursor.execute("""
# #                 SELECT 
# #                     r.*,
# #                     c.name as guest_name,
# #                     c.address as guest_address,
# #                     c.guestPan as guest_tax_number,
# #                     c.phone as guest_phone,
# #                     c.email as guest_email,
# #                     c.country,

# #                     comp.company_name,
# #                     comp.address as company_address,
# #                     comp.pan_number as company_pan,
# #                     comp.phone as company_phone,
# #                     comp.email as company_email,

# #                     e.userName as employee_name
# #                 FROM hotel_tblreservation r
# #                 LEFT JOIN customers c ON r.Guest_ID = c.id
# #                 LEFT JOIN companies comp ON r.company_id = comp.id   -- ✅ ADD THIS
# #                 LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
# #                 WHERE r.reservation_outlet_id IS NULL 
# #                 AND r.is_active = 1
# #                 ORDER BY r.id DESC
# #             """)
            
# #             reservations = cursor.fetchall()
            
# #             formatted_reservations = []
            
# #             for reservation in reservations:
# #                 # Get guest reservation details
# #                 cursor.execute("""
# #                     SELECT *
# #                     FROM hotel_tblguestreservation
# #                     WHERE Reservation_ID = %s
# #                     AND is_active = 1
# #                 """, (reservation['id'],))
                
# #                 guest_reservations = cursor.fetchall()
                
# #                 formatted_guest_reservations = []
                
# #                 for gr in guest_reservations:
# #                     # Get fit rates for this guest reservation
# #                     cursor.execute("""
# #                         SELECT 
# #                             fr.*,
# #                             rt.room_name,
# #                             rt.room_type,
# #                             rt.rate as room_rate,
# #                             rt.currency as room_currency,
# #                             rt.outlet_rate_id as rate_outlet_rate_id,
# #                             rt.occupancy,
# #                             mp.mp as meal_plan,
# #                             mp.rate as meal_rate,
# #                             mp.currency as meal_currency,
# #                             mp.outlet_rate_id as meal_outlet_rate_id
# #                         FROM hotel_tblfitrate fr
# #                         LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
# #                         LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
# #                         WHERE fr.reservationID = %s
# #                         AND fr.is_active = 1
# #                     """, (reservation['id'],))
                    
# #                     fit_rates = cursor.fetchall()
                    
# #                     formatted_fit_rates = []
# #                     for fr in fit_rates:
# #                         formatted_fit_rates.append({
# #                             "id": fr['id'],
# #                             "quantity": fr['quantity'],
# #                             "rate": {
# #                                 "id": fr['rateID'],
# #                                 "room_name": fr['room_name'],
# #                                 "room_type": fr['room_type'],
# #                                 "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
# #                                 "currency": fr['room_currency'],
# #                                 "outlet_rate_id": fr['rate_outlet_rate_id'],
# #                                 "occupancy": fr['occupancy'],
# #                             } if fr['rateID'] else None,
# #                             "meal": {
# #                                 "id": fr['mealID'],
# #                                 "mp": fr['meal_plan'],
# #                                 "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
# #                                 "currency": fr['meal_currency'],
# #                                 "outlet_rate_id": fr['meal_outlet_rate_id'],

# #                             } if fr['mealID'] else None
# #                         })
                    
# #                     formatted_guest_reservations.append({
# #                         "id": gr['id'],
# #                         "no_of_children": gr['No_of_children'],
# #                         "no_of_adults": gr['No_of_adults'],
# #                         "likes": gr['Likes'],
# #                         "dislikes": gr['Dislikes'],
# #                         "guest_notes": gr['Guest_Notes'],
# #                         "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
# #                         "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
# #                         "fit_rates": formatted_fit_rates,
# #                         "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
# #                         "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None
# #                     })
                
# #                 # Format main reservation data
# #                 formatted_reservations.append({
# #                     "id": reservation['id'],
# #                     "outlet": reservation['outlet'],
# #                     "employee": {
# #                         "id": reservation['Emp_ID'],
# #                         "name": reservation['employee_name']
# #                     } if reservation['Emp_ID'] else None,
# #                     "pay_mode": reservation['Pay_Mode'],
# #                     "billing_inst": reservation['Billing_Inst'],
# #                     "reservation_type": reservation['Reservation_type'],
# #                     "designation": reservation['designation'],
# #                     "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
# #                     "guest": {
# #                         "id": reservation['Guest_ID'],
# #                         "name": reservation['guest_name'],
# #                         "address": reservation['guest_address'],
# #                         "tax_number": reservation['guest_tax_number'],
# #                         "phone": reservation['guest_phone'],
# #                         "email": reservation['guest_email'],
# #                         "country": reservation['country']
# #                     } if reservation['Guest_ID'] else None,
# #                     "company": {
# #                         "id": reservation['company_id'],
# #                         "name": reservation['company_name'],
# #                         "address": reservation['company_address'],
# #                         "pan_number": reservation['company_pan'],
# #                         "phone": reservation['company_phone'],
# #                         "email": reservation['company_email']
# #                     } if reservation['company_id'] else None,
# #                     "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
# #                     "market_seg": reservation['Market_Seg'],
# #                     "business_src": reservation['business_Src'],
# #                     "current_status": reservation['Current_Status'],
# #                     "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
# #                     "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
# #                     "guest_reservations": formatted_guest_reservations,
# #                     "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
# #                     "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
# #                     "is_updated": reservation['is_updated'] if reservation['updated_at'] else None,

# #                 })
            
# #             response_data['unassigned_reservations'] = {
# #                 "count": len(formatted_reservations),
# #                 "data": formatted_reservations
# #             }
        
# #         # Add summary
# #         # response_data['summary'] = {
# #         #     "total_unassigned_rates": response_data.get('unassigned_rates', {}).get('count', 0),
# #         #     "total_unassigned_meal_prices": response_data.get('unassigned_meal_prices', {}).get('count', 0),
# #         #     "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
# #         # }
# #         response_data['summary'] = {
# #             # "total_unassigned_rates": response_data.get('unassigned_rates', {}).get('count', 0),
# #             # "total_unassigned_meal_prices": response_data.get('unassigned_meal_prices', {}).get('count', 0),
# #             "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
# #         }
        
# #         mydb.close()
        
# #         return jsonify({
# #             "success": True,
# #             "message": "Unassigned data fetched successfully",
# #             "data": response_data
# #         }), 200

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500

# @app_file417.route("/unsynced/data", methods=["GET"])
# @cross_origin()
# def get_unassigned_data():
#     """
#     API to fetch all unassigned data (rates, meal prices, and reservations)
#     where outlet_rate_id or reservation_outlet_id is null, scoped to a given outlet
#     """
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get filter parameters
#         data_type = request.args.get('type', 'all')  # 'rates', 'meal_prices', 'reservations', or 'all'
#         outlet = request.args.get('outlet', default=None, type=str)

#         # Outlet is now required
#         if not outlet:
#             return {"error": "outlet is required."}, 400

#         response_data = {}

#         # 3. Fetch unassigned reservations with all related data, scoped to outlet
#         if data_type in ['all', 'reservations']:
#             cursor.execute("""
#                 SELECT 
#                     r.*,
#                     c.name as guest_name,
#                     c.address as guest_address,
#                     c.guestPan as guest_tax_number,
#                     c.phone as guest_phone,
#                     c.email as guest_email,
#                     c.country,

#                     comp.company_name,
#                     comp.address as company_address,
#                     comp.pan_number as company_pan,
#                     comp.phone as company_phone,
#                     comp.email as company_email,

#                     e.userName as employee_name
#                 FROM hotel_tblreservation r
#                 LEFT JOIN customers c ON r.Guest_ID = c.id
#                 LEFT JOIN companies comp ON r.company_id = comp.id
#                 LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#                 WHERE r.reservation_outlet_id IS NULL 
#                 AND r.is_active = 1
#                 AND r.outlet = %s
#                 ORDER BY r.id DESC
#             """, (outlet,))

#             reservations = cursor.fetchall()

#             formatted_reservations = []

#             for reservation in reservations:
#                 # Get guest reservation details
#                 cursor.execute("""
#                     SELECT *
#                     FROM hotel_tblguestreservation
#                     WHERE Reservation_ID = %s
#                     AND is_active = 1
#                 """, (reservation['id'],))

#                 guest_reservations = cursor.fetchall()

#                 formatted_guest_reservations = []

#                 for gr in guest_reservations:
#                     # Get fit rates for this guest reservation
#                     cursor.execute("""
#                         SELECT 
#                             fr.*,
#                             rt.room_name,
#                             rt.room_type,
#                             rt.rate as room_rate,
#                             rt.currency as room_currency,
#                             rt.outlet_rate_id as rate_outlet_rate_id,
#                             rt.occupancy,
#                             mp.mp as meal_plan,
#                             mp.rate as meal_rate,
#                             mp.currency as meal_currency,
#                             mp.outlet_rate_id as meal_outlet_rate_id
#                         FROM hotel_tblfitrate fr
#                         LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
#                         LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#                         WHERE fr.reservationID = %s
#                         AND fr.is_active = 1
#                     """, (reservation['id'],))

#                     fit_rates = cursor.fetchall()

#                     formatted_fit_rates = []
#                     for fr in fit_rates:
#                         formatted_fit_rates.append({
#                             "id": fr['id'],
#                             "quantity": fr['quantity'],
#                             "rate": {
#                                 "id": fr['rateID'],
#                                 "room_name": fr['room_name'],
#                                 "room_type": fr['room_type'],
#                                 "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
#                                 "currency": fr['room_currency'],
#                                 "outlet_rate_id": fr['rate_outlet_rate_id'],
#                                 "occupancy": fr['occupancy'],
#                             } if fr['rateID'] else None,
#                             "meal": {
#                                 "id": fr['mealID'],
#                                 "mp": fr['meal_plan'],
#                                 "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
#                                 "currency": fr['meal_currency'],
#                                 "outlet_rate_id": fr['meal_outlet_rate_id'],

#                             } if fr['mealID'] else None
#                         })

#                     formatted_guest_reservations.append({
#                         "id": gr['id'],
#                         "no_of_children": gr['No_of_children'],
#                         "no_of_adults": gr['No_of_adults'],
#                         "likes": gr['Likes'],
#                         "dislikes": gr['Dislikes'],
#                         "guest_notes": gr['Guest_Notes'],
#                         "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
#                         "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
#                         "fit_rates": formatted_fit_rates,
#                         "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
#                         "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None
#                     })

#                 # Format main reservation data
#                 formatted_reservations.append({
#                     "id": reservation['id'],
#                     "outlet": reservation['outlet'],
#                     "employee": {
#                         "id": reservation['Emp_ID'],
#                         "name": reservation['employee_name']
#                     } if reservation['Emp_ID'] else None,
#                     "pay_mode": reservation['Pay_Mode'],
#                     "billing_inst": reservation['Billing_Inst'],
#                     "reservation_type": reservation['Reservation_type'],
#                     "designation": reservation['designation'],
#                     "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
#                     "guest": {
#                         "id": reservation['Guest_ID'],
#                         "name": reservation['guest_name'],
#                         "address": reservation['guest_address'],
#                         "tax_number": reservation['guest_tax_number'],
#                         "phone": reservation['guest_phone'],
#                         "email": reservation['guest_email'],
#                         "country": reservation['country']
#                     } if reservation['Guest_ID'] else None,
#                     "company": {
#                         "id": reservation['company_id'],
#                         "name": reservation['company_name'],
#                         "address": reservation['company_address'],
#                         "pan_number": reservation['company_pan'],
#                         "phone": reservation['company_phone'],
#                         "email": reservation['company_email']
#                     } if reservation['company_id'] else None,
#                     "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
#                     "market_seg": reservation['Market_Seg'],
#                     "business_src": reservation['business_Src'],
#                     "current_status": reservation['Current_Status'],
#                     "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
#                     "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
#                     "guest_reservations": formatted_guest_reservations,
#                     "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
#                     "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
#                     "is_updated": reservation['is_updated'] if reservation['updated_at'] else None,
#                 })

#             response_data['unassigned_reservations'] = {
#                 "count": len(formatted_reservations),
#                 "data": formatted_reservations
#             }

#         response_data['summary'] = {
#             "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
#         }

#         mydb.close()

#         return jsonify({
#             "success": True,
#             "message": "Unassigned data fetched successfully",
#             "data": response_data
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app_file417.route("/unassigned/rates", methods=["GET"])
# @cross_origin()
# def get_unassigned_rates_only():
#     """Get only unassigned rates"""
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)
        
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         cursor.execute("""
#             SELECT *
#             FROM hotel_tblrates
#             WHERE outlet_rate_id IS NULL 
#             AND is_active = 1
#             ORDER BY id DESC
#         """)
        
#         rates = cursor.fetchall()
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "count": len(rates),
#             "data": rates
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app_file417.route("/unassigned/meal-prices", methods=["GET"])
# @cross_origin()
# def get_unassigned_meal_prices_only():
#     """Get only unassigned meal prices"""
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)
        
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         cursor.execute("""
#             SELECT *
#             FROM hotel_tblmeal_price
#             WHERE outlet_rate_id IS NULL 
#             AND is_active = 1
#             ORDER BY id DESC
#         """)
        
#         meal_prices = cursor.fetchall()
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "count": len(meal_prices),
#             "data": meal_prices
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app_file417.route("/unassigned/reservations", methods=["GET"])
# @cross_origin()
# def get_unassigned_reservations_only():
#     """Get only unassigned reservations with all related data"""
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)
        
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get date range filters
#         start_date = request.args.get('start_date')
#         end_date = request.args.get('end_date')
#         status = request.args.get('status')
        
#         query = """
#             SELECT r.*, c.name as guest_name, c.address, c.guestPan, c.country
#             FROM hotel_tblreservation r
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.reservation_outlet_id IS NULL 
#             AND r.is_active = 1
#         """
        
#         params = []
        
#         if start_date:
#             query += " AND r.Reservation_Date >= %s"
#             params.append(start_date)
        
#         if end_date:
#             query += " AND r.Reservation_Date <= %s"
#             params.append(end_date)
        
#         if status:
#             query += " AND r.Current_Status = %s"
#             params.append(status)
        
#         query += " ORDER BY r.id DESC"
        
#         cursor.execute(query, params)
#         reservations = cursor.fetchall()
        
#         # Fetch related data for each reservation
#         for reservation in reservations:
#             # Get guest reservation details
#             cursor.execute("""
#                 SELECT *
#                 FROM hotel_tblguestreservation
#                 WHERE Reservation_ID = %s AND is_active = 1
#             """, (reservation['id'],))
#             reservation['guest_reservations'] = cursor.fetchall()
            
#             # Get fit rates for each guest reservation
#             for gr in reservation['guest_reservations']:
#                 cursor.execute("""
#                     SELECT fr.*, 
#                            rt.room_name, rt.room_type, rt.rate as room_rate,
#                            mp.mp, mp.rate as meal_rate
#                     FROM hotel_tblfitrate fr
#                     LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
#                     LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#                     WHERE fr.reservationID = %s AND fr.is_active = 1
#                 """, (reservation['id'],))
#                 gr['fit_rates'] = cursor.fetchall()
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "count": len(reservations),
#             "data": reservations
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app_file417.route("/sync/reservation", methods=["POST"])
# @cross_origin()
# def assign_reservation_outlet_id():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- GET DATA --------
#         json_data = request.get_json() or {}
#         reservations = json_data.get("reservations", [])

#         if not reservations or not isinstance(reservations, list):
#             return {"error": "reservations array is required"}, 400

#         success_updates = []
#         failed_updates = []

#         # -------- LOOP THROUGH ARRAY --------
#         for item in reservations:
#             reservation_id = item.get("reservation_id")
#             outlet_reservation_id = item.get("outlet_reservation_id")

#             if not reservation_id or not outlet_reservation_id:
#                 failed_updates.append({
#                     "reservation_id": reservation_id,
#                     "error": "Missing required fields"
#                 })
#                 continue

#             # Check reservation
#             cursor.execute("""
#                 SELECT id, reservation_outlet_id
#                 FROM hotel_tblreservation
#                 WHERE id = %s AND is_active = 1
#             """, (reservation_id,))
#             reservation = cursor.fetchone()

#             if not reservation:
#                 failed_updates.append({
#                     "reservation_id": reservation_id,
#                     "error": "Reservation not found"
#                 })
#                 continue

#             # Prevent overwrite
#             if reservation["reservation_outlet_id"]:
#                 failed_updates.append({
#                     "reservation_id": reservation_id,
#                     "error": "Already assigned"
#                 })
#                 continue

#             # Update
#             cursor.execute("""
#                 UPDATE hotel_tblreservation
#                 SET reservation_outlet_id = %s,
#                     updated_at = NOW()
#                 WHERE id = %s
#             """, (outlet_reservation_id, reservation_id))

#             success_updates.append({
#                 "reservation_id": reservation_id,
#                 "outlet_reservation_id": outlet_reservation_id
#             })

#         mydb.commit()

#         return jsonify({
#             "success": True,
#             "updated_count": len(success_updates),
#             "failed_count": len(failed_updates),
#             "updated": success_updates,
#             "failed": failed_updates
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     finally:
#         try:
#             mydb.close()
#         except:
#             pass


# # @app_file417.route("/updated/reservations", methods=["GET"])
# # @cross_origin()
# # def get_updated_reseravtions():
# #     """
# #     API to fetch all unassigned data (rates, meal prices, and reservations)
# #     where outlet_rate_id or reservation_outlet_id is null
# #     """
# #     try:
# #         mydb = mysql.connector.connect(
# #             host=os.getenv("host"),
# #             user=os.getenv("user"),
# #             password=os.getenv("password"),
# #             database=os.getenv("database")
# #         )

# #         cursor = mydb.cursor(dictionary=True, buffered=True)

# #         # -------- TOKEN FROM HEADER --------
# #         auth_header = request.headers.get("Authorization")

# #         if not auth_header:
# #             return {"error": "No token provided."}, 400

# #         try:
# #             token = auth_header.split(" ")[1]  # Remove "Bearer"
# #         except:
# #             return {"error": "Invalid Authorization header format."}, 400

# #         if not token:
# #             return {"error": "No token provided."}, 400

# #         if not token_auth(token):
# #             return {"error": "Invalid token."}, 400

# #         # Get filter parameters
# #         data_type = request.args.get('type', 'all')  # 'rates', 'meal_prices', 'reservations', or 'all'
        
# #         response_data = {}
        
# #         # 3. Fetch unassigned reservations with all related data
# #         if data_type in ['all', 'reservations']:
# #             # First, get all unassigned reservations
# #             cursor.execute("""
# #                 SELECT 
# #                     r.*,
# #                     c.name as guest_name,
# #                     c.address as guest_address,
# #                     c.guestPan as guest_tax_number,
# #                     c.phone as guest_phone,
# #                     c.email as guest_email,
# #                     c.country,
# #                     e.userName as employee_name
# #                 FROM hotel_tblreservation r
# #                 LEFT JOIN customers c ON r.Guest_ID = c.id
# #                 LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
# #                 WHERE r.is_updated IS TRUE 
# #                 AND r.is_active = 1
# #                 ORDER BY r.id DESC
# #             """)
            
# #             reservations = cursor.fetchall()
            
# #             formatted_reservations = []
            
# #             for reservation in reservations:
# #                 # Get guest reservation details
# #                 cursor.execute("""
# #                     SELECT *
# #                     FROM hotel_tblguestreservation
# #                     WHERE Reservation_ID = %s
# #                     AND is_active = 1
# #                 """, (reservation['id'],))
                
# #                 guest_reservations = cursor.fetchall()
                
# #                 formatted_guest_reservations = []
                
# #                 for gr in guest_reservations:
# #                     # Get fit rates for this guest reservation
# #                     cursor.execute("""
# #                         SELECT 
# #                             fr.*,
# #                             rt.room_name,
# #                             rt.room_type,
# #                             rt.rate as room_rate,
# #                             rt.currency as room_currency,
# #                             rt.outlet_rate_id as rate_outlet_rate_id,
# #                             rt.occupancy,
# #                             mp.mp as meal_plan,
# #                             mp.rate as meal_rate,
# #                             mp.currency as meal_currency,
# #                             mp.outlet_rate_id as meal_outlet_rate_id
# #                         FROM hotel_tblfitrate fr
# #                         LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
# #                         LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
# #                         WHERE fr.reservationID = %s
# #                         AND fr.is_active = 1
# #                     """, (reservation['id'],))
                    
# #                     fit_rates = cursor.fetchall()
                    
# #                     formatted_fit_rates = []
# #                     for fr in fit_rates:
# #                         formatted_fit_rates.append({
# #                             "id": fr['id'],
# #                             "quantity": fr['quantity'],
# #                             "rate": {
# #                                 "id": fr['rateID'],
# #                                 "room_name": fr['room_name'],
# #                                 "room_type": fr['room_type'],
# #                                 "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
# #                                 "currency": fr['room_currency'],
# #                                 "outlet_rate_id": fr['rate_outlet_rate_id'],
# #                                 "occupancy": fr['occupancy'],
# #                             } if fr['rateID'] else None,
# #                             "meal": {
# #                                 "id": fr['mealID'],
# #                                 "mp": fr['meal_plan'],
# #                                 "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
# #                                 "currency": fr['meal_currency'],
# #                                 "outlet_rate_id": fr['meal_outlet_rate_id'],

# #                             } if fr['mealID'] else None
# #                         })
                    
# #                     formatted_guest_reservations.append({
# #                         "id": gr['id'],
# #                         "no_of_children": gr['No_of_children'],
# #                         "no_of_adults": gr['No_of_adults'],
# #                         "likes": gr['Likes'],
# #                         "dislikes": gr['Dislikes'],
# #                         "guest_notes": gr['Guest_Notes'],
# #                         "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
# #                         "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
# #                         "fit_rates": formatted_fit_rates,
# #                         "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
# #                         "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None
# #                     })
                
# #                 # Format main reservation data
# #                 formatted_reservations.append({
# #                     "id": reservation['id'],
# #                     "outlet": reservation['outlet'],
# #                     "employee": {
# #                         "id": reservation['Emp_ID'],
# #                         "name": reservation['employee_name']
# #                     } if reservation['Emp_ID'] else None,
# #                     "pay_mode": reservation['Pay_Mode'],
# #                     "billing_inst": reservation['Billing_Inst'],
# #                     "reservation_type": reservation['Reservation_type'],
# #                     "designation": reservation['designation'],
# #                     "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
# #                     "guest": {
# #                         "id": reservation['Guest_ID'],
# #                         "name": reservation['guest_name'],
# #                         "address": reservation['guest_address'],
# #                         "tax_number": reservation['guest_tax_number'],
# #                         "phone": reservation['guest_phone'],
# #                         "email": reservation['guest_email'],
# #                         "country": reservation['country']
# #                     } if reservation['Guest_ID'] else None,
# #                     "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
# #                     "market_seg": reservation['Market_Seg'],
# #                     "business_src": reservation['business_Src'],
# #                     "current_status": reservation['Current_Status'],
# #                     "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
# #                     "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
# #                     "guest_reservations": formatted_guest_reservations,
# #                     "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
# #                     "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
# #                     "is_updated": reservation['is_updated']
# #                 })
            
# #             response_data['unassigned_reservations'] = {
# #                 "count": len(formatted_reservations),
# #                 "data": formatted_reservations
# #             }
    
# #         response_data['summary'] = {
# #             "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
# #         }
        
# #         mydb.close()
        
# #         return jsonify({
# #             "success": True,
# #             "message": "Unassigned data fetched successfully",
# #             "data": response_data
# #         }), 200

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500


# @app_file417.route("/updated/reservations", methods=["GET"])
# @cross_origin()
# def get_updated_reseravtions():
#     """
#     API to fetch all unassigned data (rates, meal prices, and reservations)
#     where outlet_rate_id or reservation_outlet_id is null
#     """
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get filter parameters
#         data_type = request.args.get('type', 'all')
        
#         response_data = {}
        
#         # 3. Fetch unassigned reservations with all related data
#         if data_type in ['all', 'reservations']:
#             # First, get all unassigned reservations
#             cursor.execute("""
#                 SELECT 
#                     r.*,
#                     c.name as guest_name,
#                     c.address as guest_address,
#                     c.guestPan as guest_tax_number,
#                     c.phone as guest_phone,
#                     c.email as guest_email,
#                     c.country,
#                     c.outlet_guest_id,
#                     e.userName as employee_name
#                 FROM hotel_tblreservation r
#                 LEFT JOIN customers c ON r.Guest_ID = c.id
#                 LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#                 WHERE r.is_updated IS TRUE 
#                 AND r.is_active = 1
#                 ORDER BY r.id DESC
#             """)
            
#             reservations = cursor.fetchall()
            
#             formatted_reservations = []
            
#             for reservation in reservations:
#                 # Get reservation details (room assignments)
#                 cursor.execute("""
#                     SELECT 
#                         rd.*,
#                         r.room_no,
#                         r.outlet as room_outlet,
#                         r.room_state,
#                         r.phone_no as room_phone,
#                         r.preference,
#                         r.room_view,
#                         r.room_type as room_type_name,
#                         r.room_notes,
#                         r.outlet_room_id
#                     FROM hotel_tblreservation_details rd
#                     LEFT JOIN hotel_tblrooms r ON rd.room_id = r.id
#                     WHERE rd.Reservation_ID = %s
#                     AND rd.is_active = 1
#                     ORDER BY rd.id DESC
#                 """, (reservation['id'],))
                
#                 reservation_details = cursor.fetchall()
                
#                 formatted_reservation_details = []
#                 for rd in reservation_details:
#                     formatted_reservation_details.append({
#                         "id": rd['id'],
#                         "reservationID": rd['Reservation_ID'],
#                         "room": {
#                             "id": rd['room_id'],
#                             "room_no": rd['room_no'],
#                             "outlet": rd['room_outlet'],
#                             "room_state": rd['room_state'],
#                             "phone_no": rd['room_phone'],
#                             "preference": rd['preference'],
#                             "room_view": rd['room_view'],
#                             "room_type": rd['room_type_name'],
#                             "room_notes": rd['room_notes'],
#                             "outlet_room_id": rd['outlet_room_id']
#                         } if rd['room_id'] else None,
#                         "is_current": rd['is_current'],
#                         "created_at": rd['created_at'].strftime('%Y-%m-%d %H:%M:%S') if rd['created_at'] else None,
#                         "updated_at": rd['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if rd['updated_at'] else None
#                     })
                
#                 # Get guest reservation details
#                 cursor.execute("""
#                     SELECT *
#                     FROM hotel_tblguestreservation
#                     WHERE Reservation_ID = %s
#                     AND is_active = 1
#                 """, (reservation['id'],))
                
#                 guest_reservations = cursor.fetchall()
                
#                 # Get all FIT rates for this reservation (outside guest reservation)
#                 cursor.execute("""
#                     SELECT 
#                         fr.*,
#                         rt.room_name,
#                         rt.room_type,
#                         rt.rate as room_rate,
#                         rt.currency as room_currency,
#                         rt.outlet_rate_id as rate_outlet_rate_id,
#                         rt.occupancy,
#                         mp.mp as meal_plan,
#                         mp.rate as meal_rate,
#                         mp.currency as meal_currency,
#                         mp.outlet_rate_id as meal_outlet_rate_id
#                     FROM hotel_tblfitrate fr
#                     LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
#                     LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#                     WHERE fr.reservationID = %s
#                     AND fr.is_active = 1
#                 """, (reservation['id'],))
                
#                 fit_rates = cursor.fetchall()
                
#                 formatted_fit_rates = []
#                 for fr in fit_rates:
#                     formatted_fit_rates.append({
#                         "id": fr['id'],
#                         "quantity": fr['quantity'],
#                         "reservationID": fr['reservationID'],
#                         "rate": {
#                             "id": fr['rateID'],
#                             "room_name": fr['room_name'],
#                             "room_type": fr['room_type'],
#                             "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
#                             "currency": fr['room_currency'],
#                             "outlet_rate_id": fr['rate_outlet_rate_id'],
#                             "occupancy": fr['occupancy'],
#                         } if fr['rateID'] else None,
#                         "meal": {
#                             "id": fr['mealID'],
#                             "mp": fr['meal_plan'],
#                             "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
#                             "currency": fr['meal_currency'],
#                             "outlet_rate_id": fr['meal_outlet_rate_id'],
#                         } if fr['mealID'] else None
#                     })
                
#                 # Format guest reservations (without fit rates)
#                 formatted_guest_reservations = []
#                 for gr in guest_reservations:
#                     formatted_guest_reservations.append({
#                         "id": gr['id'],
#                         "no_of_children": gr['No_of_children'],
#                         "no_of_adults": gr['No_of_adults'],
#                         "likes": gr['Likes'],
#                         "dislikes": gr['Dislikes'],
#                         "guest_notes": gr['Guest_Notes'],
#                         "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
#                         "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
#                         "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
#                         "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None,
#                         "reservation_ID": gr["Reservation_ID"]
#                     })
                
#                 # Format main reservation data
#                 formatted_reservations.append({
#                     "tblReservation": {
#                         "id": reservation['id'],
#                         "outlet": reservation['outlet'],
#                         "employee": {
#                             "id": reservation['Emp_ID'],
#                             "name": reservation['employee_name']
#                         } if reservation['Emp_ID'] else None,
#                         "pay_mode": reservation['Pay_Mode'],
#                         "billing_inst": reservation['Billing_Inst'],
#                         "reservation_type": reservation['Reservation_type'],
#                         "designation": reservation['designation'],
#                         "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
#                         "guest": {
#                             "id": reservation['Guest_ID'],
#                             "name": reservation['guest_name'],
#                             "address": reservation['guest_address'],
#                             "tax_number": reservation['guest_tax_number'],
#                             "phone": reservation['guest_phone'],
#                             "email": reservation['guest_email'],
#                             "country": reservation['country'],
#                             "outlet_guest_id": reservation['outlet_guest_id'],
#                         } if reservation['Guest_ID'] else None,
#                         "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
#                         "market_seg": reservation['Market_Seg'],
#                         "business_src": reservation['business_Src'],
#                         "current_status": reservation['Current_Status'],
#                         "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
#                         "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
#                         "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
#                         "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
#                         "is_updated": reservation['is_updated'],
#                         "reservation_outlet_id": reservation['reservation_outlet_id']
#                     },
#                     "tblGuestReservation": formatted_guest_reservations,
#                     "tblFITRate": formatted_fit_rates,  # FIT rates at the top level
#                     "reservation_details": formatted_reservation_details
#                 })
            
#             response_data['updated_reservations'] = {
#                 "count": len(formatted_reservations),
#                 "data": formatted_reservations
#             }
    
#         response_data['summary'] = {
#             "total_updated_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
#         }
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "message": "Updated data fetched successfully",
#             "data": response_data
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
from root.auth.check import token_auth

app_file417 = Blueprint('app_file417', __name__)

# @app_file417.route("/unsynced/data", methods=["GET"])
# @cross_origin()
# def get_unassigned_data():
#     """
#     API to fetch all unassigned data (rates, meal prices, and reservations)
#     where outlet_rate_id or reservation_outlet_id is null
#     """
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get filter parameters
#         data_type = request.args.get('type', 'all')  # 'rates', 'meal_prices', 'reservations', or 'all'
        
#         response_data = {}
        
#         # 3. Fetch unassigned reservations with all related data
#         if data_type in ['all', 'reservations']:
#             # First, get all unassigned reservations
#             # cursor.execute("""
#             #     SELECT 
#             #         r.*,
#             #         c.name as guest_name,
#             #         c.address as guest_address,
#             #         c.guestPan as guest_tax_number,
#             #         c.phone as guest_phone,
#             #         c.email as guest_email,
#             #         c.country,
#             #         e.userName as employee_name
#             #     FROM hotel_tblreservation r
#             #     LEFT JOIN customers c ON r.Guest_ID = c.id
#             #     LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#             #     WHERE r.reservation_outlet_id IS NULL 
#             #     AND r.is_active = 1
#             #     ORDER BY r.id DESC
#             # """)

#             cursor.execute("""
#                 SELECT 
#                     r.*,
#                     c.name as guest_name,
#                     c.address as guest_address,
#                     c.guestPan as guest_tax_number,
#                     c.phone as guest_phone,
#                     c.email as guest_email,
#                     c.country,

#                     comp.company_name,
#                     comp.address as company_address,
#                     comp.pan_number as company_pan,
#                     comp.phone as company_phone,
#                     comp.email as company_email,

#                     e.userName as employee_name
#                 FROM hotel_tblreservation r
#                 LEFT JOIN customers c ON r.Guest_ID = c.id
#                 LEFT JOIN companies comp ON r.company_id = comp.id   -- ✅ ADD THIS
#                 LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#                 WHERE r.reservation_outlet_id IS NULL 
#                 AND r.is_active = 1
#                 ORDER BY r.id DESC
#             """)
            
#             reservations = cursor.fetchall()
            
#             formatted_reservations = []
            
#             for reservation in reservations:
#                 # Get guest reservation details
#                 cursor.execute("""
#                     SELECT *
#                     FROM hotel_tblguestreservation
#                     WHERE Reservation_ID = %s
#                     AND is_active = 1
#                 """, (reservation['id'],))
                
#                 guest_reservations = cursor.fetchall()
                
#                 formatted_guest_reservations = []
                
#                 for gr in guest_reservations:
#                     # Get fit rates for this guest reservation
#                     cursor.execute("""
#                         SELECT 
#                             fr.*,
#                             rt.room_name,
#                             rt.room_type,
#                             rt.rate as room_rate,
#                             rt.currency as room_currency,
#                             rt.outlet_rate_id as rate_outlet_rate_id,
#                             rt.occupancy,
#                             mp.mp as meal_plan,
#                             mp.rate as meal_rate,
#                             mp.currency as meal_currency,
#                             mp.outlet_rate_id as meal_outlet_rate_id
#                         FROM hotel_tblfitrate fr
#                         LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
#                         LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#                         WHERE fr.reservationID = %s
#                         AND fr.is_active = 1
#                     """, (reservation['id'],))
                    
#                     fit_rates = cursor.fetchall()
                    
#                     formatted_fit_rates = []
#                     for fr in fit_rates:
#                         formatted_fit_rates.append({
#                             "id": fr['id'],
#                             "quantity": fr['quantity'],
#                             "rate": {
#                                 "id": fr['rateID'],
#                                 "room_name": fr['room_name'],
#                                 "room_type": fr['room_type'],
#                                 "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
#                                 "currency": fr['room_currency'],
#                                 "outlet_rate_id": fr['rate_outlet_rate_id'],
#                                 "occupancy": fr['occupancy'],
#                             } if fr['rateID'] else None,
#                             "meal": {
#                                 "id": fr['mealID'],
#                                 "mp": fr['meal_plan'],
#                                 "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
#                                 "currency": fr['meal_currency'],
#                                 "outlet_rate_id": fr['meal_outlet_rate_id'],

#                             } if fr['mealID'] else None
#                         })
                    
#                     formatted_guest_reservations.append({
#                         "id": gr['id'],
#                         "no_of_children": gr['No_of_children'],
#                         "no_of_adults": gr['No_of_adults'],
#                         "likes": gr['Likes'],
#                         "dislikes": gr['Dislikes'],
#                         "guest_notes": gr['Guest_Notes'],
#                         "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
#                         "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
#                         "fit_rates": formatted_fit_rates,
#                         "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
#                         "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None
#                     })
                
#                 # Format main reservation data
#                 formatted_reservations.append({
#                     "id": reservation['id'],
#                     "outlet": reservation['outlet'],
#                     "employee": {
#                         "id": reservation['Emp_ID'],
#                         "name": reservation['employee_name']
#                     } if reservation['Emp_ID'] else None,
#                     "pay_mode": reservation['Pay_Mode'],
#                     "billing_inst": reservation['Billing_Inst'],
#                     "reservation_type": reservation['Reservation_type'],
#                     "designation": reservation['designation'],
#                     "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
#                     "guest": {
#                         "id": reservation['Guest_ID'],
#                         "name": reservation['guest_name'],
#                         "address": reservation['guest_address'],
#                         "tax_number": reservation['guest_tax_number'],
#                         "phone": reservation['guest_phone'],
#                         "email": reservation['guest_email'],
#                         "country": reservation['country']
#                     } if reservation['Guest_ID'] else None,
#                     "company": {
#                         "id": reservation['company_id'],
#                         "name": reservation['company_name'],
#                         "address": reservation['company_address'],
#                         "pan_number": reservation['company_pan'],
#                         "phone": reservation['company_phone'],
#                         "email": reservation['company_email']
#                     } if reservation['company_id'] else None,
#                     "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
#                     "market_seg": reservation['Market_Seg'],
#                     "business_src": reservation['business_Src'],
#                     "current_status": reservation['Current_Status'],
#                     "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
#                     "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
#                     "guest_reservations": formatted_guest_reservations,
#                     "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
#                     "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
#                     "is_updated": reservation['is_updated'] if reservation['updated_at'] else None,
#                 })
            
#             response_data['unassigned_reservations'] = {
#                 "count": len(formatted_reservations),
#                 "data": formatted_reservations
#             }
        
#         # Add summary
#         # response_data['summary'] = {
#         #     "total_unassigned_rates": response_data.get('unassigned_rates', {}).get('count', 0),
#         #     "total_unassigned_meal_prices": response_data.get('unassigned_meal_prices', {}).get('count', 0),
#         #     "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
#         # }
#         response_data['summary'] = {
#             # "total_unassigned_rates": response_data.get('unassigned_rates', {}).get('count', 0),
#             # "total_unassigned_meal_prices": response_data.get('unassigned_meal_prices', {}).get('count', 0),
#             "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
#         }
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "message": "Unassigned data fetched successfully",
#             "data": response_data
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app_file417.route("/unsynced/data", methods=["GET"])
@cross_origin()
def get_unassigned_data():
    """
    API to fetch all unassigned data (rates, meal prices, and reservations)
    where outlet_rate_id or reservation_outlet_id is null, scoped to a given outlet
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get filter parameters
        data_type = request.args.get('type', 'all')  # 'rates', 'meal_prices', 'reservations', or 'all'
        outlet = request.args.get('outlet', default=None, type=str)

        # Outlet is now required
        if not outlet:
            return {"error": "outlet is required."}, 400

        response_data = {}

        # 3. Fetch unassigned reservations with all related data, scoped to outlet
        if data_type in ['all', 'reservations']:
            cursor.execute("""
                SELECT 
                    r.*,
                    c.name as guest_name,
                    c.address as guest_address,
                    c.guestPan as guest_tax_number,
                    c.phone as guest_phone,
                    c.email as guest_email,
                    c.country,

                    comp.company_name,
                    comp.address as company_address,
                    comp.pan_number as company_pan,
                    comp.phone as company_phone,
                    comp.email as company_email,

                    e.userName as employee_name
                FROM hotel_tblreservation r
                LEFT JOIN customers c ON r.Guest_ID = c.id
                LEFT JOIN companies comp ON r.company_id = comp.id
                LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
                WHERE r.reservation_outlet_id IS NULL 
                AND r.is_active = 1
                AND r.outlet = %s
                ORDER BY r.id DESC
            """, (outlet,))

            reservations = cursor.fetchall()

            formatted_reservations = []

            for reservation in reservations:
                # Get guest reservation details
                cursor.execute("""
                    SELECT *
                    FROM hotel_tblguestreservation
                    WHERE Reservation_ID = %s
                    AND is_active = 1
                """, (reservation['id'],))

                guest_reservations = cursor.fetchall()

                formatted_guest_reservations = []

                for gr in guest_reservations:
                    # Get fit rates for this guest reservation
                    cursor.execute("""
                        SELECT 
                            fr.*,
                            rt.room_name,
                            rt.room_type,
                            rt.rate as room_rate,
                            rt.currency as room_currency,
                            rt.outlet_rate_id as rate_outlet_rate_id,
                            rt.occupancy,
                            mp.mp as meal_plan,
                            mp.rate as meal_rate,
                            mp.currency as meal_currency,
                            mp.outlet_rate_id as meal_outlet_rate_id
                        FROM hotel_tblfitrate fr
                        LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
                        LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
                        WHERE fr.reservationID = %s
                        AND fr.is_active = 1
                    """, (reservation['id'],))

                    fit_rates = cursor.fetchall()

                    formatted_fit_rates = []
                    for fr in fit_rates:
                        formatted_fit_rates.append({
                            "id": fr['id'],
                            "quantity": fr['quantity'],
                            "rate": {
                                "id": fr['rateID'],
                                "room_name": fr['room_name'],
                                "room_type": fr['room_type'],
                                "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
                                "currency": fr['room_currency'],
                                "outlet_rate_id": fr['rate_outlet_rate_id'],
                                "occupancy": fr['occupancy'],
                            } if fr['rateID'] else None,
                            "meal": {
                                "id": fr['mealID'],
                                "mp": fr['meal_plan'],
                                "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
                                "currency": fr['meal_currency'],
                                "outlet_rate_id": fr['meal_outlet_rate_id'],

                            } if fr['mealID'] else None
                        })

                    formatted_guest_reservations.append({
                        "id": gr['id'],
                        "no_of_children": gr['No_of_children'],
                        "no_of_adults": gr['No_of_adults'],
                        "likes": gr['Likes'],
                        "dislikes": gr['Dislikes'],
                        "guest_notes": gr['Guest_Notes'],
                        "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
                        "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
                        "fit_rates": formatted_fit_rates,
                        "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
                        "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None
                    })

                # Format main reservation data
                formatted_reservations.append({
                    "id": reservation['id'],
                    "outlet": reservation['outlet'],
                    "employee": {
                        "id": reservation['Emp_ID'],
                        "name": reservation['employee_name']
                    } if reservation['Emp_ID'] else None,
                    "pay_mode": reservation['Pay_Mode'],
                    "billing_inst": reservation['Billing_Inst'],
                    "reservation_type": reservation['Reservation_type'],
                    "designation": reservation['designation'],
                    "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
                    "guest": {
                        "id": reservation['Guest_ID'],
                        "name": reservation['guest_name'],
                        "address": reservation['guest_address'],
                        "tax_number": reservation['guest_tax_number'],
                        "phone": reservation['guest_phone'],
                        "email": reservation['guest_email'],
                        "country": reservation['country']
                    } if reservation['Guest_ID'] else None,
                    "company": {
                        "id": reservation['company_id'],
                        "name": reservation['company_name'],
                        "address": reservation['company_address'],
                        "pan_number": reservation['company_pan'],
                        "phone": reservation['company_phone'],
                        "email": reservation['company_email']
                    } if reservation['company_id'] else None,
                    "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
                    "market_seg": reservation['Market_Seg'],
                    "business_src": reservation['business_Src'],
                    "current_status": reservation['Current_Status'],
                    "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
                    "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
                    "guest_reservations": formatted_guest_reservations,
                    "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
                    "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
                    "is_updated": reservation['is_updated'] if reservation['updated_at'] else None,
                })

            response_data['unassigned_reservations'] = {
                "count": len(formatted_reservations),
                "data": formatted_reservations
            }

        response_data['summary'] = {
            "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
        }

        mydb.close()

        return jsonify({
            "success": True,
            "message": "Unassigned data fetched successfully",
            "data": response_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @app_file417.route("/unassigned/rates", methods=["GET"])
# @cross_origin()
# def get_unassigned_rates_only():
#     """Get only unassigned rates"""
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)
        
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         cursor.execute("""
#             SELECT *
#             FROM hotel_tblrates
#             WHERE outlet_rate_id IS NULL 
#             AND is_active = 1
#             ORDER BY id DESC
#         """)
        
#         rates = cursor.fetchall()
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "count": len(rates),
#             "data": rates
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app_file417.route("/unassigned/rates", methods=["GET"])
@cross_origin()
def get_unassigned_rates_only():
    """Get only unassigned rates for a given outlet"""
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        outlet = request.args.get('outlet', default=None, type=str)

        if not outlet:
            return {"error": "outlet is required."}, 400

        cursor.execute("""
            SELECT *
            FROM hotel_tblrates
            WHERE outlet_rate_id IS NULL 
            AND is_active = 1
            AND outlet = %s
            ORDER BY id DESC
        """, (outlet,))

        rates = cursor.fetchall()

        mydb.close()

        return jsonify({
            "success": True,
            "count": len(rates),
            "data": rates
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app_file417.route("/unassigned/meal-prices", methods=["GET"])
@cross_origin()
def get_unassigned_meal_prices_only():
    """Get only unassigned meal prices"""
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        cursor.execute("""
            SELECT *
            FROM hotel_tblmeal_price
            WHERE outlet_rate_id IS NULL 
            AND is_active = 1
            ORDER BY id DESC
        """)
        
        meal_prices = cursor.fetchall()
        
        mydb.close()
        
        return jsonify({
            "success": True,
            "count": len(meal_prices),
            "data": meal_prices
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app_file417.route("/unassigned/reservations", methods=["GET"])
@cross_origin()
def get_unassigned_reservations_only():
    """Get only unassigned reservations with all related data"""
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get date range filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        query = """
            SELECT r.*, c.name as guest_name, c.address, c.guestPan, c.country
            FROM hotel_tblreservation r
            LEFT JOIN customers c ON r.Guest_ID = c.id
            WHERE r.reservation_outlet_id IS NULL 
            AND r.is_active = 1
        """
        
        params = []
        
        if start_date:
            query += " AND r.Reservation_Date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND r.Reservation_Date <= %s"
            params.append(end_date)
        
        if status:
            query += " AND r.Current_Status = %s"
            params.append(status)
        
        query += " ORDER BY r.id DESC"
        
        cursor.execute(query, params)
        reservations = cursor.fetchall()
        
        # Fetch related data for each reservation
        for reservation in reservations:
            # Get guest reservation details
            cursor.execute("""
                SELECT *
                FROM hotel_tblguestreservation
                WHERE Reservation_ID = %s AND is_active = 1
            """, (reservation['id'],))
            reservation['guest_reservations'] = cursor.fetchall()
            
            # Get fit rates for each guest reservation
            for gr in reservation['guest_reservations']:
                cursor.execute("""
                    SELECT fr.*, 
                           rt.room_name, rt.room_type, rt.rate as room_rate,
                           mp.mp, mp.rate as meal_rate
                    FROM hotel_tblfitrate fr
                    LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
                    LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
                    WHERE fr.reservationID = %s AND fr.is_active = 1
                """, (reservation['id'],))
                gr['fit_rates'] = cursor.fetchall()
        
        mydb.close()
        
        return jsonify({
            "success": True,
            "count": len(reservations),
            "data": reservations
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app_file417.route("/sync/reservation", methods=["POST"])
@cross_origin()
def assign_reservation_outlet_id():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)

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

        # -------- GET DATA --------
        json_data = request.get_json() or {}
        reservations = json_data.get("reservations", [])

        if not reservations or not isinstance(reservations, list):
            return {"error": "reservations array is required"}, 400

        success_updates = []
        failed_updates = []

        # -------- LOOP THROUGH ARRAY --------
        for item in reservations:
            reservation_id = item.get("reservation_id")
            outlet_reservation_id = item.get("outlet_reservation_id")

            if not reservation_id or not outlet_reservation_id:
                failed_updates.append({
                    "reservation_id": reservation_id,
                    "error": "Missing required fields"
                })
                continue

            # Check reservation
            cursor.execute("""
                SELECT id, reservation_outlet_id
                FROM hotel_tblreservation
                WHERE id = %s AND is_active = 1
            """, (reservation_id,))
            reservation = cursor.fetchone()

            if not reservation:
                failed_updates.append({
                    "reservation_id": reservation_id,
                    "error": "Reservation not found"
                })
                continue

            # Prevent overwrite
            if reservation["reservation_outlet_id"]:
                failed_updates.append({
                    "reservation_id": reservation_id,
                    "error": "Already assigned"
                })
                continue

            # Update
            cursor.execute("""
                UPDATE hotel_tblreservation
                SET reservation_outlet_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (outlet_reservation_id, reservation_id))

            success_updates.append({
                "reservation_id": reservation_id,
                "outlet_reservation_id": outlet_reservation_id
            })

        mydb.commit()

        return jsonify({
            "success": True,
            "updated_count": len(success_updates),
            "failed_count": len(failed_updates),
            "updated": success_updates,
            "failed": failed_updates
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            mydb.close()
        except:
            pass


# @app_file417.route("/updated/reservations", methods=["GET"])
# @cross_origin()
# def get_updated_reseravtions():
#     """
#     API to fetch all unassigned data (rates, meal prices, and reservations)
#     where outlet_rate_id or reservation_outlet_id is null
#     """
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )

#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN FROM HEADER --------
#         auth_header = request.headers.get("Authorization")

#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]  # Remove "Bearer"
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get filter parameters
#         data_type = request.args.get('type', 'all')  # 'rates', 'meal_prices', 'reservations', or 'all'
        
#         response_data = {}
        
#         # 3. Fetch unassigned reservations with all related data
#         if data_type in ['all', 'reservations']:
#             # First, get all unassigned reservations
#             cursor.execute("""
#                 SELECT 
#                     r.*,
#                     c.name as guest_name,
#                     c.address as guest_address,
#                     c.guestPan as guest_tax_number,
#                     c.phone as guest_phone,
#                     c.email as guest_email,
#                     c.country,
#                     e.userName as employee_name
#                 FROM hotel_tblreservation r
#                 LEFT JOIN customers c ON r.Guest_ID = c.id
#                 LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
#                 WHERE r.is_updated IS TRUE 
#                 AND r.is_active = 1
#                 ORDER BY r.id DESC
#             """)
            
#             reservations = cursor.fetchall()
            
#             formatted_reservations = []
            
#             for reservation in reservations:
#                 # Get guest reservation details
#                 cursor.execute("""
#                     SELECT *
#                     FROM hotel_tblguestreservation
#                     WHERE Reservation_ID = %s
#                     AND is_active = 1
#                 """, (reservation['id'],))
                
#                 guest_reservations = cursor.fetchall()
                
#                 formatted_guest_reservations = []
                
#                 for gr in guest_reservations:
#                     # Get fit rates for this guest reservation
#                     cursor.execute("""
#                         SELECT 
#                             fr.*,
#                             rt.room_name,
#                             rt.room_type,
#                             rt.rate as room_rate,
#                             rt.currency as room_currency,
#                             rt.outlet_rate_id as rate_outlet_rate_id,
#                             rt.occupancy,
#                             mp.mp as meal_plan,
#                             mp.rate as meal_rate,
#                             mp.currency as meal_currency,
#                             mp.outlet_rate_id as meal_outlet_rate_id
#                         FROM hotel_tblfitrate fr
#                         LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
#                         LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
#                         WHERE fr.reservationID = %s
#                         AND fr.is_active = 1
#                     """, (reservation['id'],))
                    
#                     fit_rates = cursor.fetchall()
                    
#                     formatted_fit_rates = []
#                     for fr in fit_rates:
#                         formatted_fit_rates.append({
#                             "id": fr['id'],
#                             "quantity": fr['quantity'],
#                             "rate": {
#                                 "id": fr['rateID'],
#                                 "room_name": fr['room_name'],
#                                 "room_type": fr['room_type'],
#                                 "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
#                                 "currency": fr['room_currency'],
#                                 "outlet_rate_id": fr['rate_outlet_rate_id'],
#                                 "occupancy": fr['occupancy'],
#                             } if fr['rateID'] else None,
#                             "meal": {
#                                 "id": fr['mealID'],
#                                 "mp": fr['meal_plan'],
#                                 "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
#                                 "currency": fr['meal_currency'],
#                                 "outlet_rate_id": fr['meal_outlet_rate_id'],

#                             } if fr['mealID'] else None
#                         })
                    
#                     formatted_guest_reservations.append({
#                         "id": gr['id'],
#                         "no_of_children": gr['No_of_children'],
#                         "no_of_adults": gr['No_of_adults'],
#                         "likes": gr['Likes'],
#                         "dislikes": gr['Dislikes'],
#                         "guest_notes": gr['Guest_Notes'],
#                         "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
#                         "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
#                         "fit_rates": formatted_fit_rates,
#                         "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
#                         "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None
#                     })
                
#                 # Format main reservation data
#                 formatted_reservations.append({
#                     "id": reservation['id'],
#                     "outlet": reservation['outlet'],
#                     "employee": {
#                         "id": reservation['Emp_ID'],
#                         "name": reservation['employee_name']
#                     } if reservation['Emp_ID'] else None,
#                     "pay_mode": reservation['Pay_Mode'],
#                     "billing_inst": reservation['Billing_Inst'],
#                     "reservation_type": reservation['Reservation_type'],
#                     "designation": reservation['designation'],
#                     "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
#                     "guest": {
#                         "id": reservation['Guest_ID'],
#                         "name": reservation['guest_name'],
#                         "address": reservation['guest_address'],
#                         "tax_number": reservation['guest_tax_number'],
#                         "phone": reservation['guest_phone'],
#                         "email": reservation['guest_email'],
#                         "country": reservation['country']
#                     } if reservation['Guest_ID'] else None,
#                     "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
#                     "market_seg": reservation['Market_Seg'],
#                     "business_src": reservation['business_Src'],
#                     "current_status": reservation['Current_Status'],
#                     "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
#                     "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
#                     "guest_reservations": formatted_guest_reservations,
#                     "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
#                     "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
#                     "is_updated": reservation['is_updated']
#                 })
            
#             response_data['unassigned_reservations'] = {
#                 "count": len(formatted_reservations),
#                 "data": formatted_reservations
#             }
    
#         response_data['summary'] = {
#             "total_unassigned_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
#         }
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "message": "Unassigned data fetched successfully",
#             "data": response_data
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app_file417.route("/updated/reservations", methods=["GET"])
@cross_origin()
def get_updated_reseravtions():
    """
    API to fetch all unassigned data (rates, meal prices, and reservations)
    where outlet_rate_id or reservation_outlet_id is null
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )

        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]  # Remove "Bearer"
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get filter parameters
        data_type = request.args.get('type', 'all')
        
        response_data = {}
        
        # 3. Fetch unassigned reservations with all related data
        if data_type in ['all', 'reservations']:
            # First, get all unassigned reservations
            cursor.execute("""
                SELECT 
                    r.*,
                    c.name as guest_name,
                    c.address as guest_address,
                    c.guestPan as guest_tax_number,
                    c.phone as guest_phone,
                    c.email as guest_email,
                    c.country,
                    c.outlet_guest_id,
                    e.userName as employee_name
                FROM hotel_tblreservation r
                LEFT JOIN customers c ON r.Guest_ID = c.id
                LEFT JOIN EmployeeLogin e ON r.Emp_ID = e.id
                WHERE r.is_updated IS TRUE 
                AND r.is_active = 1
                ORDER BY r.id DESC
            """)
            
            reservations = cursor.fetchall()
            
            formatted_reservations = []
            
            for reservation in reservations:
                # Get reservation details (room assignments)
                cursor.execute("""
                    SELECT 
                        rd.*,
                        r.room_no,
                        r.outlet as room_outlet,
                        r.room_state,
                        r.phone_no as room_phone,
                        r.preference,
                        r.room_view,
                        r.room_type as room_type_name,
                        r.room_notes,
                        r.outlet_room_id
                    FROM hotel_tblreservation_details rd
                    LEFT JOIN hotel_tblrooms r ON rd.room_id = r.id
                    WHERE rd.Reservation_ID = %s
                    AND rd.is_active = 1
                    ORDER BY rd.id DESC
                """, (reservation['id'],))
                
                reservation_details = cursor.fetchall()
                
                formatted_reservation_details = []
                for rd in reservation_details:
                    formatted_reservation_details.append({
                        "id": rd['id'],
                        "reservationID": rd['Reservation_ID'],
                        "room": {
                            "id": rd['room_id'],
                            "room_no": rd['room_no'],
                            "outlet": rd['room_outlet'],
                            "room_state": rd['room_state'],
                            "phone_no": rd['room_phone'],
                            "preference": rd['preference'],
                            "room_view": rd['room_view'],
                            "room_type": rd['room_type_name'],
                            "room_notes": rd['room_notes'],
                            "outlet_room_id": rd['outlet_room_id']
                        } if rd['room_id'] else None,
                        "is_current": rd['is_current'],
                        "created_at": rd['created_at'].strftime('%Y-%m-%d %H:%M:%S') if rd['created_at'] else None,
                        "updated_at": rd['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if rd['updated_at'] else None
                    })
                
                # Get guest reservation details
                cursor.execute("""
                    SELECT *
                    FROM hotel_tblguestreservation
                    WHERE Reservation_ID = %s
                    AND is_active = 1
                """, (reservation['id'],))
                
                guest_reservations = cursor.fetchall()
                
                # Get all FIT rates for this reservation (outside guest reservation)
                cursor.execute("""
                    SELECT 
                        fr.*,
                        rt.room_name,
                        rt.room_type,
                        rt.rate as room_rate,
                        rt.currency as room_currency,
                        rt.outlet_rate_id as rate_outlet_rate_id,
                        rt.occupancy,
                        mp.mp as meal_plan,
                        mp.rate as meal_rate,
                        mp.currency as meal_currency,
                        mp.outlet_rate_id as meal_outlet_rate_id
                    FROM hotel_tblfitrate fr
                    LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
                    LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
                    WHERE fr.reservationID = %s
                    AND fr.is_active = 1
                """, (reservation['id'],))
                
                fit_rates = cursor.fetchall()
                
                formatted_fit_rates = []
                for fr in fit_rates:
                    formatted_fit_rates.append({
                        "id": fr['id'],
                        "quantity": fr['quantity'],
                        "reservationID": fr['reservationID'],
                        "rate": {
                            "id": fr['rateID'],
                            "room_name": fr['room_name'],
                            "room_type": fr['room_type'],
                            "rate": float(fr['room_rate']) if fr['room_rate'] else 0,
                            "currency": fr['room_currency'],
                            "outlet_rate_id": fr['rate_outlet_rate_id'],
                            "occupancy": fr['occupancy'],
                        } if fr['rateID'] else None,
                        "meal": {
                            "id": fr['mealID'],
                            "mp": fr['meal_plan'],
                            "rate": float(fr['meal_rate']) if fr['meal_rate'] else 0,
                            "currency": fr['meal_currency'],
                            "outlet_rate_id": fr['meal_outlet_rate_id'],
                        } if fr['mealID'] else None
                    })
                
                # Format guest reservations (without fit rates)
                formatted_guest_reservations = []
                for gr in guest_reservations:
                    formatted_guest_reservations.append({
                        "id": gr['id'],
                        "no_of_children": gr['No_of_children'],
                        "no_of_adults": gr['No_of_adults'],
                        "likes": gr['Likes'],
                        "dislikes": gr['Dislikes'],
                        "guest_notes": gr['Guest_Notes'],
                        "start_date": gr['start_date'].strftime('%Y-%m-%d') if gr['start_date'] else None,
                        "end_date": gr['end_date'].strftime('%Y-%m-%d') if gr['end_date'] else None,
                        "created_at": gr['created_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['created_at'] else None,
                        "updated_at": gr['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if gr['updated_at'] else None,
                        "reservation_ID": gr["Reservation_ID"]
                    })
                
                # Format main reservation data
                formatted_reservations.append({
                    "tblReservation": {
                        "id": reservation['id'],
                        "outlet": reservation['outlet'],
                        "employee": {
                            "id": reservation['Emp_ID'],
                            "name": reservation['employee_name']
                        } if reservation['Emp_ID'] else None,
                        "pay_mode": reservation['Pay_Mode'],
                        "billing_inst": reservation['Billing_Inst'],
                        "reservation_type": reservation['Reservation_type'],
                        "designation": reservation['designation'],
                        "advance_payment": float(reservation['Advance_Payment']) if reservation['Advance_Payment'] else 0,
                        "guest": {
                            "id": reservation['Guest_ID'],
                            "name": reservation['guest_name'],
                            "address": reservation['guest_address'],
                            "tax_number": reservation['guest_tax_number'],
                            "phone": reservation['guest_phone'],
                            "email": reservation['guest_email'],
                            "country": reservation['country'],
                            "outlet_guest_id": reservation['outlet_guest_id'],
                        } if reservation['Guest_ID'] else None,
                        "reservation_date": reservation['Reservation_Date'].strftime('%Y-%m-%d') if reservation['Reservation_Date'] else None,
                        "market_seg": reservation['Market_Seg'],
                        "business_src": reservation['business_Src'],
                        "current_status": reservation['Current_Status'],
                        "check_in": reservation['Check_In'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_In'] else None,
                        "check_out": reservation['Check_Out'].strftime('%Y-%m-%d %H:%M:%S') if reservation['Check_Out'] else None,
                        "created_at": reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['created_at'] else None,
                        "updated_at": reservation['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if reservation['updated_at'] else None,
                        "is_updated": reservation['is_updated'],
                        "reservation_outlet_id": reservation['reservation_outlet_id']
                    },
                    "tblGuestReservation": formatted_guest_reservations,
                    "tblFITRate": formatted_fit_rates,  # FIT rates at the top level
                    "reservation_details": formatted_reservation_details
                })
            
            response_data['updated_reservations'] = {
                "count": len(formatted_reservations),
                "data": formatted_reservations
            }
    
        response_data['summary'] = {
            "total_updated_reservations": response_data.get('unassigned_reservations', {}).get('count', 0)
        }
        
        mydb.close()
        
        return jsonify({
            "success": True,
            "message": "Updated data fetched successfully",
            "data": response_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500