# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin
# import mysql.connector
# import os
# from dotenv import load_dotenv
# from datetime import datetime, timedelta
# from calendar import monthrange
# import json

# load_dotenv()
# from root.auth.check import token_auth

# app_file415 = Blueprint('app_file415', __name__)

# @app_file415.route("/analytics/reservation-status", methods=["GET"])
# @cross_origin()
# def get_reservation_status_stats():
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

#         # Get month and year from query parameters, default to current month
#         month = request.args.get('month', default=datetime.now().month, type=int)
#         year = request.args.get('year', default=datetime.now().year, type=int)
        
#         # Optional filter by outlet
#         outlet = request.args.get('outlet', default=None, type=str)
        
#         # Validate month and year
#         if month < 1 or month > 12:
#             return {"error": "Invalid month. Month must be between 1 and 12."}, 400
            
#         # Get first and last day of the month
#         first_day = datetime(year, month, 1).date()
#         last_day = datetime(year, month, monthrange(year, month)[1]).date()
        
#         # Get today's date for checking-out logic
#         today = datetime.now().date()
        
#         # Initialize results dictionary with all days of the month
#         results = {}
#         current_date = first_day
#         while current_date <= last_day:
#             date_str = current_date.strftime('%Y-%m-%d')
#             results[date_str] = {
#                 "date": date_str,
#                 "reserved": 0,
#                 "registered": 0,
#                 "checking_out": 0,
#                 "checked_out": 0,
#                 "cancelled": 0,
#                 "total": 0
#             }
#             current_date += timedelta(days=1)
        
#         # Build the base query
#         base_query = """
#             SELECT 
#                 r.id,
#                 r.Current_Status,
#                 gr.start_date,
#                 gr.end_date,
#                 r.Check_In,
#                 r.Check_Out
#             FROM hotel_tblreservation r
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#             AND (
#                 (gr.start_date BETWEEN %s AND %s)
#                 OR (gr.end_date BETWEEN %s AND %s)
#                 OR (gr.start_date <= %s AND gr.end_date >= %s)
#             )
#         """
        
#         params = [first_day, last_day, first_day, last_day, first_day, last_day]
        
#         # Add outlet filter if provided
#         if outlet:
#             base_query += " AND r.outlet = %s"
#             params.append(outlet)
        
#         cursor.execute(base_query, params)
#         reservations = cursor.fetchall()
        
#         # Process each reservation and count for each day in the month
#         for reservation in reservations:
#             # Parse dates
#             start_date = reservation['start_date']
#             end_date = reservation['end_date']
#             current_status = reservation['Current_Status']
            
#             if isinstance(start_date, str):
#                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             if isinstance(end_date, str):
#                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
#             # Determine the range of days this reservation covers within the requested month
#             range_start = max(start_date, first_day)
#             range_end = min(end_date, last_day)
            
#             # For each day in the reservation's range
#             current_day = range_start
#             while current_day <= range_end:
#                 date_str = current_day.strftime('%Y-%m-%d')
                
#                 # Apply the special logic for checking-out
#                 if current_status == "Registered":
#                     if end_date < today:
#                         # This is considered checking-out
#                         results[date_str]["checking_out"] += 1
#                     else:
#                         # Regular registered
#                         results[date_str]["registered"] += 1
#                 elif current_status == "Reserved":
#                     results[date_str]["reserved"] += 1
#                 elif current_status == "Checked Out":
#                     results[date_str]["checked_out"] += 1
#                 elif current_status == "Cancelled":
#                     results[date_str]["cancelled"] += 1
#                 else:
#                     # For any other status, count as is
#                     status_key = current_status.lower().replace('-', '_')
#                     if status_key in results[date_str]:
#                         results[date_str][status_key] += 1
                
#                 results[date_str]["total"] += 1
#                 current_day += timedelta(days=1)
        
#         # Convert results to a list for easier frontend consumption
#         daily_stats = list(results.values())
        
#         # Calculate summary statistics for the month
#         summary = {
#             "total_reservations": sum(day["total"] for day in daily_stats),
#             "total_reserved": sum(day["reserved"] for day in daily_stats),
#             "total_registered": sum(day["registered"] for day in daily_stats),
#             "total_checking_out": sum(day["checking_out"] for day in daily_stats),
#             "total_checked_out": sum(day["checked_out"] for day in daily_stats),
#             "total_cancelled": sum(day["cancelled"] for day in daily_stats),
#             "month": month,
#             "year": year
#         }
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "data": {
#                 "daily": daily_stats,
#                 "summary": summary,
#                 "filters": {
#                     "month": month,
#                     "year": year,
#                     "outlet": outlet
#                 }
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app_file415.route("/analytics/reservation-status/export", methods=["POST"])
# @cross_origin()
# def export_reservation_status():
#     """
#     Endpoint to export the data in a different format (for CSV/Excel download)
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
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         json_data = request.get_json() or {}
#         month = json_data.get('month', datetime.now().month)
#         year = json_data.get('year', datetime.now().year)
#         outlet = json_data.get('outlet')
#         format_type = json_data.get('format', 'json')  # 'json', 'csv', etc.

#         # Similar logic as above to get the data
#         # Then format it appropriately for export
        

#         # For now, return a success message
#         return jsonify({
#             "success": True,
#             "message": f"Export functionality for {format_type} format would be implemented here"
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app_file415.route("/analytics/reservation-status/summary", methods=["GET"])
# @cross_origin()
# def get_reservation_summary():
#     """
#     Get just the summary statistics without daily breakdown
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
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get date range from query parameters
#         start_date = request.args.get('start_date')
#         end_date = request.args.get('end_date')
#         outlet = request.args.get('outlet')

#         # Build query for summary
#         query = """
#             SELECT 
#                 r.Current_Status,
#                 COUNT(DISTINCT r.id) as count
#             FROM hotel_tblreservation r
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#         """
        
#         params = []
        
#         if start_date and end_date:
#             query += " AND ((gr.start_date BETWEEN %s AND %s) OR (gr.end_date BETWEEN %s AND %s))"
#             params.extend([start_date, end_date, start_date, end_date])
        
#         if outlet:
#             query += " AND r.outlet = %s"
#             params.append(outlet)
        
#         query += " GROUP BY r.Current_Status"
        
#         cursor.execute(query, params)
#         results = cursor.fetchall()
        
#         # Format the summary
#         summary = {
#             "Reserved": 0,
#             "Registered": 0,
#             "Checked Out": 0,
#             "Cancelled": 0
#         }
        
#         for row in results:
#             summary[row['Current_Status']] = row['count']
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "data": summary
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app_file415.route("/cancel-reservation", methods=["POST"])
# @cross_origin()
# def cancel_reservation():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True)

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

#         # -------- INPUT --------
#         data = request.get_json()
#         reservation_id = data.get("reservation_id")

#         if not reservation_id:
#             return {"error": "reservation_id is required"}, 400

#         # -------- CHECK IF EXISTS --------
#         cursor.execute(
#             "SELECT id, Current_Status FROM hotel_tblreservation WHERE id = %s",
#             (reservation_id,)
#         )
#         reservation = cursor.fetchone()

#         if not reservation:
#             return {"error": "Reservation not found"}, 404

#         # -------- OPTIONAL: ALREADY CANCELLED --------
#         if reservation["Current_Status"] == "Cancelled":
#             return {"message": "Reservation already cancelled"}, 200

#         # -------- UPDATE STATUS --------
#         cursor.execute(
#             "UPDATE hotel_tblreservation SET Current_Status = %s WHERE id = %s",
#             ("Cancelled", reservation_id)
#         )

#         mydb.commit()
#         mydb.close()

#         return {
#             "message": "Reservation cancelled successfully",
#             "reservation_id": reservation_id
#         }, 200

#     except Exception as e:
#         return {"error": str(e)}, 500
    
# @app_file415.route("/cancel-reservation-by-outlet-id", methods=["POST"])
# @cross_origin()
# def cancel_reservation_by_outlet_id():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv('host'),
#             user=os.getenv('user'),
#             password=os.getenv('password'),
#             database=os.getenv('database')
#         )
#         cursor = mydb.cursor(dictionary=True)

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

#         # -------- INPUT --------
#         data = request.get_json()
#         outlet_reservation_id = data.get("reservation_outlet_id")

#         if not outlet_reservation_id:
#             return {"error": "reservation_outlet_id is required"}, 400

#         # -------- FIND RESERVATION --------
#         cursor.execute(
#             """
#             SELECT id, Current_Status
#             FROM hotel_tblreservation
#             WHERE reservation_outlet_id = %s
#             LIMIT 1
#             """,
#             (outlet_reservation_id,)
#         )
#         reservation = cursor.fetchone()

#         if not reservation:
#             return {"error": "Reservation not found"}, 404

#         reservation_id = reservation["id"]

#         # -------- ALREADY CANCELLED --------
#         if reservation["Current_Status"] == "Cancelled":
#             return {
#                 "message": "Reservation already cancelled",
#                 "reservation_id": reservation_id
#             }, 200

#         # -------- CANCEL RESERVATION --------
#         cursor.execute(
#             """
#             UPDATE hotel_tblreservation
#             SET Current_Status = %s
#             WHERE id = %s
#             """,
#             ("Cancelled", reservation_id)
#         )

#         # -------- OPTIONAL: ALSO DEACTIVATE FIT RATES --------
#         cursor.execute(
#             """
#             UPDATE hotel_tblfitrate
#             SET is_active = 0
#             WHERE reservationID = %s
#             """,
#             (reservation_id,)
#         )

#         mydb.commit()
#         mydb.close()

#         return {
#             "message": "Reservation cancelled successfully",
#             "reservation_id": reservation_id,
#             "reservation_outlet_id": outlet_reservation_id
#         }, 200

#     except Exception as e:
#         return {"error": str(e)}, 500


# # from collections import defaultdict
# # from datetime import datetime, timedelta, date
# # from calendar import monthrange

# # @app_file415.route("/analytics/rooms-confirmed", methods=["GET"])
# # @cross_origin()
# # def get_rooms_confirmed_stats():
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
# #             token = auth_header.split(" ")[1]
# #         except:
# #             return {"error": "Invalid Authorization header format."}, 400

# #         if not token:
# #             return {"error": "No token provided."}, 400

# #         if not token_auth(token):
# #             return {"error": "Invalid token."}, 400

# #         # Get from_date and to_date from query parameters
# #         from_date = request.args.get('from_date')
# #         to_date = request.args.get('to_date')
        
# #         # Optional filter by outlet
# #         outlet = request.args.get('outlet', default=None, type=str)
        
# #         # Validate dates
# #         if not from_date or not to_date:
# #             return {"error": "Both from_date and to_date are required (format: YYYY-MM-DD)"}, 400
        
# #         try:
# #             first_day = datetime.strptime(from_date, '%Y-%m-%d').date()
# #             last_day = datetime.strptime(to_date, '%Y-%m-%d').date()
# #         except ValueError:
# #             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
        
# #         # Get total hotel rooms count and details from hotel_tblrooms
# #         total_rooms_query = """
# #             SELECT 
# #                 COUNT(*) as total_rooms,
# #                 SUM(CASE WHEN room_state = 'Occupied' THEN 1 ELSE 0 END) as currently_occupied,
# #                 room_type,
# #                 COUNT(*) as type_count
# #             FROM hotel_tblrooms
# #             WHERE is_active = 1
# #         """
# #         total_rooms_params = []
        
# #         if outlet:
# #             total_rooms_query += " AND outlet = %s"
# #             total_rooms_params.append(outlet)
        
# #         # total_rooms_query += " GROUP BY room_type WITH ROLLUP"
# #         total_rooms_query += " GROUP BY room_type WITH ROLLUP"
        
# #         cursor.execute(total_rooms_query, total_rooms_params)
# #         room_stats = cursor.fetchall()
        
# #         # Calculate total hotel rooms and breakdown by type
# #         hotel_total_rooms = 0
# #         rooms_by_type_capacity = {}
        
# #         for stat in room_stats:
# #             if stat['room_type'] is None:  # This is the rollup row with total
# #                 hotel_total_rooms = stat['total_rooms']
# #             else:
# #                 rooms_by_type_capacity[stat['room_type']] = {
# #                     "room_type": stat['room_type'],
# #                     "total_capacity": stat['total_rooms'],
# #                     "currently_occupied": stat['currently_occupied'] or 0
# #                 }
        
# #         # Initialize results dictionary with all days of the month
# #         results = {}
# #         current_date = first_day
# #         while current_date <= last_day:
# #             date_str = current_date.strftime('%Y-%m-%d')
# #             results[date_str] = {
# #                 "date": date_str,
# #                 "booked_rooms": 0,  # From fitrate (Reserved + Registered + Checked-out)
# #                 "occupied_rooms": 0,  # From registered_rooms (only Registered)

# #                 "rooms_by_type": defaultdict(lambda: {
# #                     "room_name": "",
# #                     "room_type": "",
# #                     "booked_quantity": 0,
# #                     "occupied_quantity": 0,
# #                     "rate": 0,
# #                     "reservation_ids": []
# #                 }),
# #                 "reservations": [],
# #                 "arrivals": {
# #                     "booked_rooms": 0,
# #                     "amount": 0,
# #                     "reservations": []
# #                 },
# #                 "departures": {
# #                     "booked_rooms": 0,
# #                     "amount": 0,
# #                     "reservations": []
# #                 },
# #                 "registered_rooms": {
# #                     "total_rooms": 0,
# #                     "total_amount": 0,
# #                     "rooms": []  # Will contain detailed room information
# #                 },
# #                 "confirmed":{
# #                     "booked_rooms": 0,
# #                     "amount": 0,
# #                     "reservations": []
# #                 },
# #                 "cancelled":{
# #                     "booked_rooms": 0,
# #                     "amount": 0,
# #                     "reservations": []
# #                 },
# #                 "stayovers":{
# #                     "booked_rooms": 0,
# #                     "amount": 0,
# #                     "reservations": []
# #                 }
# #             }
# #             current_date += timedelta(days=1)

# #         # Build the query to get all confirmed reservations with their room details
# #         base_query = """
# #             SELECT 
# #                 r.id AS reservation_id,
# #                 r.Current_Status,
# #                 gr.start_date,
# #                 gr.end_date,
# #                 r.outlet,
# #                 fr.id AS fitrate_id,
# #                 fr.quantity AS room_quantity,
# #                 fr.rateID,
# #                 rt.room_name,
# #                 rt.room_type,
# #                 rt.rate AS room_rate,
# #                 rt.currency,
# #                 mp.mp AS meal_plan,
# #                 mp.rate AS meal_rate
# #             FROM hotel_tblreservation r
# #             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
# #             INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
# #             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
# #             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
# #             WHERE r.is_active = 1 
# #             AND gr.is_active = 1
# #             AND fr.is_active = 1
# #             AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out', 'Cancelled')
# #             AND (
# #                 (gr.start_date BETWEEN %s AND %s)
# #                 OR (gr.end_date BETWEEN %s AND %s)
# #                 OR (gr.start_date <= %s AND gr.end_date >= %s)
# #             )
# #         """

# #         params = [first_day, last_day, first_day, last_day, first_day, last_day]

# #         # Add outlet filter if provided
# #         if outlet:
# #             base_query += " AND r.outlet = %s"
# #             params.append(outlet)

# #         # Order by date for consistent processing
# #         base_query += " ORDER BY gr.start_date"

# #         cursor.execute(base_query, params)
# #         reservations = cursor.fetchall()

# #         # Process each reservation and its fitrate entries
# #         for reservation in reservations:
# #             # Parse dates
# #             start_date = reservation['start_date']
# #             end_date = reservation['end_date']
# #             status = reservation['Current_Status']
            
# #             if isinstance(start_date, str):
# #                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
# #             if isinstance(end_date, str):
# #                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
# #             # Determine the nights to process
# #             # For same-day stay, we need to process the arrival day but not have a night stay
# #             is_single_night = start_date == end_date
            
# #             # 🔥 FIX: Handle date range properly
# #             if is_single_night:
# #                 # For single night, we only process the arrival day, no overnight stay
# #                 night_dates = []  # No nights to process for occupancy
# #                 arrival_date = start_date
# #             else:
# #                 # Normal case: exclude checkout day from loop
# #                 range_start = max(start_date, first_day)
# #                 range_end = min(end_date - timedelta(days=1), last_day)
                
# #                 # Generate all nights between start_date and end_date (excluding checkout day)
# #                 night_dates = []
# #                 current_day = range_start
# #                 while current_day <= range_end:
# #                     night_dates.append(current_day)
# #                     current_day += timedelta(days=1)
                
# #                 arrival_date = start_date
            
# #             # Rates
# #             room_rate = float(reservation['room_rate'] or 0)
# #             meal_rate = float(reservation['meal_rate'] or 0)
# #             total_rate_per_room = room_rate + meal_rate
            
# #             room_quantity = int(reservation['room_quantity'] or 1)
# #             room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"
            
# #             # 👉 Process arrival (always for start_date if within range)
# #             if arrival_date >= first_day and arrival_date <= last_day:
# #                 date_str = arrival_date.strftime('%Y-%m-%d')
# #                 daily_amount = room_quantity * total_rate_per_room
                
# #                 # ✅ BOOKINGS (all reserved nights) - arrival day counts as a booked night
# #                 if date_str in results:
# #                     results[date_str]["booked_rooms"] += room_quantity
                    
# #                     # # ✅ OCCUPIED (only checked-in guests)
# #                     # if status == 'Registered':
# #                     #     results[date_str]["occupied_rooms"] += room_quantity
                    
# #                     # ✅ ROOM TYPE BREAKDOWN
# #                     results[date_str]["rooms_by_type"][room_type_key]["room_name"] = reservation['room_name']
# #                     results[date_str]["rooms_by_type"][room_type_key]["room_type"] = reservation['room_type']
# #                     results[date_str]["rooms_by_type"][room_type_key]["booked_quantity"] += room_quantity
# #                     results[date_str]["rooms_by_type"][room_type_key]["rate"] = total_rate_per_room
                    
# #                     if reservation['reservation_id'] not in results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"]:
# #                         results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"].append(reservation['reservation_id'])
                    
# #                     # Reservation detail
# #                     reservation_detail = {
# #                         "reservation_id": reservation['reservation_id'],
# #                         "room_name": reservation['room_name'],
# #                         "room_type": reservation['room_type'],
# #                         "quantity": room_quantity,
# #                         "rate_per_room": total_rate_per_room,
# #                         "total_amount": daily_amount,
# #                         "meal_plan": reservation['meal_plan'],
# #                         "currency": reservation['currency'],
# #                         "outlet": reservation['outlet'],
# #                         "start_date": start_date.strftime('%Y-%m-%d'),
# #                         "end_date": end_date.strftime('%Y-%m-%d'),
# #                         "status": status
# #                     }
                    
# #                     results[date_str]["reservations"].append(reservation_detail)
                    
# #                     # ✅ CONFIRMED
# #                     if status in ['Reserved', 'Registered']:
# #                         results[date_str]["confirmed"]["booked_rooms"] += room_quantity
# #                         results[date_str]["confirmed"]["amount"] += daily_amount
# #                         results[date_str]["confirmed"]["reservations"].append(reservation_detail)
                    
# #                     # ✅ CANCELLED
# #                     if status == 'Cancelled':
# #                         results[date_str]["cancelled"]["booked_rooms"] += room_quantity
# #                         results[date_str]["cancelled"]["amount"] += daily_amount
# #                         results[date_str]["cancelled"]["reservations"].append(reservation_detail)
                    
# #                     # ✅ ARRIVAL (always for start_date)
# #                     if status in ['Registered', 'Checked Out']:
# #                         results[date_str]["arrivals"]["booked_rooms"] += room_quantity
# #                         results[date_str]["arrivals"]["amount"] += daily_amount
# #                         results[date_str]["arrivals"]["reservations"].append(reservation_detail)
            
# #             # 👉 Process nights (excluding arrival day for multi-night stays)
# #             for current_day in night_dates:
# #                 # Skip the arrival date for multi-night stays (already processed above)
# #                 if not is_single_night and current_day == start_date:
# #                     continue
                    
# #                 date_str = current_day.strftime('%Y-%m-%d')
# #                 daily_amount = room_quantity * total_rate_per_room
                
# #                 if date_str not in results:
# #                     continue
                
# #                 # ✅ BOOKINGS (all reserved nights)
# #                 if start_date <= current_day < end_date:
# #                     results[date_str]["booked_rooms"] += room_quantity
                
# #                 # ✅ OCCUPIED (only checked-in guests)
# #                 # if status == 'Registered' and start_date <= current_day < end_date:
# #                 #     results[date_str]["occupied_rooms"] += room_quantity
                
# #                 # ✅ ROOM TYPE BREAKDOWN
# #                 results[date_str]["rooms_by_type"][room_type_key]["room_name"] = reservation['room_name']
# #                 results[date_str]["rooms_by_type"][room_type_key]["room_type"] = reservation['room_type']

# #                 if status in ['Reserved', 'Registered'] and start_date <= current_day < end_date:
# #                     results[date_str]["rooms_by_type"][room_type_key]["booked_quantity"] += room_quantity
# #                 results[date_str]["rooms_by_type"][room_type_key]["rate"] = total_rate_per_room
                
# #                 if reservation['reservation_id'] not in results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"]:
# #                     results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"].append(reservation['reservation_id'])
                
# #                 # Reservation detail
# #                 reservation_detail = {
# #                     "reservation_id": reservation['reservation_id'],
# #                     "room_name": reservation['room_name'],
# #                     "room_type": reservation['room_type'],
# #                     "quantity": room_quantity,
# #                     "rate_per_room": total_rate_per_room,
# #                     "total_amount": daily_amount,
# #                     "meal_plan": reservation['meal_plan'],
# #                     "currency": reservation['currency'],
# #                     "outlet": reservation['outlet'],
# #                     "start_date": start_date.strftime('%Y-%m-%d'),
# #                     "end_date": end_date.strftime('%Y-%m-%d'),
# #                     "status": status
# #                 }
                
# #                 results[date_str]["reservations"].append(reservation_detail)
                
# #                 # ✅ CONFIRMED
# #                 if status in ['Reserved', 'Registered']:
# #                     results[date_str]["confirmed"]["booked_rooms"] += room_quantity
# #                     results[date_str]["confirmed"]["amount"] += daily_amount
# #                     results[date_str]["confirmed"]["reservations"].append(reservation_detail)
                
# #                 # ✅ CANCELLED
# #                 if status == 'Cancelled' and start_date == current_day :
# #                     results[date_str]["cancelled"]["booked_rooms"] += room_quantity
# #                     results[date_str]["cancelled"]["amount"] += daily_amount
# #                     results[date_str]["cancelled"]["reservations"].append(reservation_detail)
                
# #                 # ✅ STAYOVER (middle days only, not arrival or departure)
# #                 if status in ['Registered', 'Checked Out'] and start_date < current_day < end_date:
# #                     results[date_str]["stayovers"]["booked_rooms"] += room_quantity
# #                     results[date_str]["stayovers"]["amount"] += daily_amount
# #                     results[date_str]["stayovers"]["reservations"].append(reservation_detail)
            
# #             # ✅ DEPARTURE (handled for all reservations, even single-night)
# #             dep_date_str = end_date.strftime('%Y-%m-%d')
            
# #             if dep_date_str in results and status in ['Registered', 'Checked Out']:
# #                 daily_amount = room_quantity * total_rate_per_room
                
# #                 reservation_detail = {
# #                     "reservation_id": reservation['reservation_id'],
# #                     "room_name": reservation['room_name'],
# #                     "room_type": reservation['room_type'],
# #                     "quantity": room_quantity,
# #                     "rate_per_room": total_rate_per_room,
# #                     "total_amount": daily_amount,
# #                     "meal_plan": reservation['meal_plan'],
# #                     "currency": reservation['currency'],
# #                     "outlet": reservation['outlet'],
# #                     "start_date": start_date.strftime('%Y-%m-%d'),
# #                     "end_date": end_date.strftime('%Y-%m-%d'),
# #                     "status": status
# #                 }
                
# #                 results[dep_date_str]["departures"]["booked_rooms"] += room_quantity
# #                 results[dep_date_str]["departures"]["amount"] += daily_amount
# #                 results[dep_date_str]["departures"]["reservations"].append({
# #                     **reservation_detail,
# #                     "departure_status": status
# #                 })

# #         # # Now get the registered rooms information from reservation_details
# #         registered_rooms_query = """
# #             SELECT DISTINCT
# #                 rd.id AS detail_id,
# #                 rd.Reservation_ID,
# #                 rd.room_id,
# #                 rd.is_current,
# #                 r.id AS reservation_id,
# #                 r.Current_Status,
# #                 gr.start_date,
# #                 gr.end_date,
# #                 rm.id AS room_id,
# #                 rm.outlet AS room_outlet,
# #                 rm.room_no,
# #                 rm.room_state,
# #                 rm.phone_no,
# #                 rm.preference,
# #                 rm.room_view,
# #                 rm.room_type,
# #                 rm.room_notes,
# #                 rt.room_name,
# #                 rt.rate AS room_rate,
# #                 mp.mp AS meal_plan,
# #                 mp.rate AS meal_rate
# #             FROM hotel_tblreservation_details rd
# #             INNER JOIN hotel_tblreservation r ON rd.Reservation_ID = r.id
# #             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
# #             INNER JOIN hotel_tblrooms rm ON rd.room_id = rm.id
# #             LEFT JOIN hotel_tblfitrate fr ON r.id = fr.reservationID AND fr.is_active = 1
# #             LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
# #             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id AND mp.is_active = 1
# #             WHERE r.is_active = 1 
# #             AND gr.is_active = 1
# #             AND rd.is_active = 1
# #             AND r.Current_Status = 'Registered'
# #             AND rd.is_current = 1
# #             AND (
# #                 (gr.start_date BETWEEN %s AND %s)
# #                 OR (gr.end_date BETWEEN %s AND %s)
# #                 OR (gr.start_date <= %s AND gr.end_date >= %s)
# #             )
# #         """
        
# #         registered_params = [first_day, last_day, first_day, last_day, first_day, last_day]
        
# #         # Add outlet filter if provided
# #         if outlet:
# #             registered_rooms_query += " AND r.outlet = %s"
# #             registered_params.append(outlet)
        
# #         cursor.execute(registered_rooms_query, registered_params)
# #         registered_rooms = cursor.fetchall()
        
# #         # Process registered rooms
# #         for room in registered_rooms:
# #             # Parse dates
# #             start_date = room['start_date']
# #             end_date = room['end_date']
            
# #             if isinstance(start_date, str):
# #                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
# #             if isinstance(end_date, str):
# #                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
# #             # Determine the range of days this registered room covers within the requested month
# #             range_start = max(start_date, first_day)
# #             # range_end = min(end_date, last_day)
# #             range_end = min(end_date - timedelta(days=1), last_day)  # Subtract 1 day to exclude departure
# #             # Calculate rate per room
# #             room_rate = float(room['room_rate'] or 0)
# #             meal_rate = float(room['meal_rate'] or 0)
# #             total_rate_per_room = room_rate + meal_rate
            
# #             # Create room type key for grouping
# #             room_type_key = f"{room['room_name']}_{room['room_type']}"
            
# #             # For each day in the range
# #             current_day = range_start
# #             while current_day <= range_end:
# #                 date_str = current_day.strftime('%Y-%m-%d')
                
# #                 # Add to occupied rooms count (from registered rooms)
# #                 results[date_str]["occupied_rooms"] += 1
# #                 results[date_str]["registered_rooms"]["total_amount"] += total_rate_per_room
                
                
# #                 # Add room details
# #                 room_detail = {
# #                     "reservation_id": room['reservation_id'],
# #                     "room_id": room['room_id'],
# #                     "room_no": room['room_no'],
# #                     "room_type": room['room_type'],
# #                     "room_name": room['room_name'],
# #                     "room_state": room['room_state'],
# #                     "preference": room['preference'],
# #                     "room_view": room['room_view'],
# #                     "phone_no": room['phone_no'],
# #                     "room_notes": room['room_notes'],
# #                     "rate": total_rate_per_room,
# #                     "meal_plan": room['meal_plan'],
# #                     "start_date": start_date.strftime('%Y-%m-%d'),
# #                     "end_date": end_date.strftime('%Y-%m-%d')
# #                 }
                
# #                 results[date_str]["registered_rooms"]["rooms"].append(room_detail)
                
# #                 current_day += timedelta(days=1)
        
# #         # Convert defaultdict to regular dict for JSON serialization
# #         daily_stats = []
# #         for date_str, day_data in results.items():
# #             # Convert rooms_by_type to list
# #             rooms_list = []
# #             for room_key, room_data in day_data["rooms_by_type"].items():
# #                 rooms_list.append({
# #                     "room_name": room_data["room_name"],
# #                     "room_type": room_data["room_type"],
# #                     "booked_quantity": room_data["booked_quantity"],
# #                     "occupied_quantity": room_data["occupied_quantity"],
# #                     "rate": room_data["rate"],
# #                     # "booked_amount": room_data["booked_amount"],
# #                     # "occupied_amount": room_data["occupied_amount"],
# #                     "reservation_count": len(room_data["reservation_ids"])
# #                 })
            
# #             # Remove duplicates from registered rooms (if any)
# #             unique_rooms = []
# #             seen_room_ids = set()
# #             for room in day_data["registered_rooms"]["rooms"]:
# #                 if room["room_id"] not in seen_room_ids:
# #                     seen_room_ids.add(room["room_id"])
# #                     unique_rooms.append(room)
            
# #             daily_stats.append({
# #                 "date": day_data["date"],
# #                 "hotel_capacity": hotel_total_rooms,
# #                 "booked_rooms": day_data["booked_rooms"],

# #                 "occupied_rooms": day_data["occupied_rooms"],

# #                 "vacant_rooms": hotel_total_rooms - day_data["occupied_rooms"],
# #                 "occupancy_rate": round((day_data["occupied_rooms"] / hotel_total_rooms * 100), 2) if hotel_total_rooms > 0 else 0,
# #                 # "rooms_by_type": rooms_list,
# #                 "reservations_count": len(day_data["reservations"]),
# #                 "arrivals": day_data["arrivals"]["booked_rooms"],
# #                 "stayovers": day_data["stayovers"]["booked_rooms"],
                
# #                 "departures":  day_data["departures"]["booked_rooms"],

                
# #                 "confirmed": day_data["confirmed"]["booked_rooms"],
                  
# #                 "cancelled": day_data["cancelled"]["booked_rooms"],
# #                 "registered_rooms": unique_rooms
                
# #             })
        
# #         mydb.close()
        
# #         return jsonify({
# #             "success": True,
# #             "data": {
# #                 "daily": daily_stats,
# #                 # "summary": summary,
# #                 "filters": {
# #                     "from_date": from_date,
# #                     "to_date": to_date,
# #                     "outlet": outlet
# #                 }
# #             }
# #         }), 200

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500


# from collections import defaultdict
# from datetime import datetime, timedelta, date
# from calendar import monthrange

# @app_file415.route("/analytics/rooms-confirmed", methods=["GET"])
# @cross_origin()
# def get_rooms_confirmed_stats():
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
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get from_date and to_date from query parameters
#         from_date = request.args.get('from_date')
#         to_date = request.args.get('to_date')
        
#         # Optional filter by outlet
#         outlet = request.args.get('outlet', default=None, type=str)
        
#         # Validate dates
#         if not from_date or not to_date:
#             return {"error": "Both from_date and to_date are required (format: YYYY-MM-DD)"}, 400
        
#         try:
#             first_day = datetime.strptime(from_date, '%Y-%m-%d').date()
#             last_day = datetime.strptime(to_date, '%Y-%m-%d').date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
        
#         # Get total hotel rooms count and details from hotel_tblrooms
#         total_rooms_query = """
#             SELECT 
#                 COUNT(*) as total_rooms,
#                 SUM(CASE WHEN room_state = 'Occupied' THEN 1 ELSE 0 END) as currently_occupied,
#                 room_type,
#                 COUNT(*) as type_count
#             FROM hotel_tblrooms
#             WHERE is_active = 1
#         """
#         total_rooms_params = []
        
#         if outlet:
#             total_rooms_query += " AND outlet = %s"
#             total_rooms_params.append(outlet)
        
#         total_rooms_query += " GROUP BY room_type WITH ROLLUP"
        
#         cursor.execute(total_rooms_query, total_rooms_params)
#         room_stats = cursor.fetchall()
        
#         # Calculate total hotel rooms and breakdown by type
#         hotel_total_rooms = 0
#         rooms_by_type_capacity = {}
        
#         for stat in room_stats:
#             if stat['room_type'] is None:  # This is the rollup row with total
#                 hotel_total_rooms = stat['total_rooms']
#             else:
#                 rooms_by_type_capacity[stat['room_type']] = {
#                     "room_type": stat['room_type'],
#                     "total_capacity": stat['total_rooms'],
#                     "currently_occupied": stat['currently_occupied'] or 0
#                 }
        
#         # Initialize results dictionary with all days of the month
#         results = {}
#         current_date = first_day
#         while current_date <= last_day:
#             date_str = current_date.strftime('%Y-%m-%d')
#             results[date_str] = {
#                 "date": date_str,
#                 "booked_rooms": 0,  # From fitrate (Reserved + Registered + Checked-out)

#                 "rooms_by_type": defaultdict(lambda: {
#                     "room_name": "",
#                     "room_type": "",
#                     "booked_quantity": 0,
#                     "occupied_quantity": 0,
#                     "rate": 0,
#                     "reservation_ids": []
#                 }),
#                 "reservations": [],
#                 "arrivals": {
#                     "booked_rooms": 0,
#                     "amount": 0,
#                     "reservations": []
#                 },
#                 "departures": {
#                     "booked_rooms": 0,
#                     "amount": 0,
#                     "reservations": []
#                 },
#                 "registered_rooms": {
#                     "total_rooms": 0,
#                     "total_amount": 0,
#                     "rooms": []  # Will contain detailed room information
#                 },
#                 "confirmed":{
#                     "booked_rooms": 0,
#                     "amount": 0,
#                     "reservations": []
#                 },
#                 "cancelled":{
#                     "booked_rooms": 0,
#                     "amount": 0,
#                     "reservations": []
#                 },
#                 "stayovers":{
#                     "booked_rooms": 0,
#                     "amount": 0,
#                     "reservations": []
#                 }
#             }
#             current_date += timedelta(days=1)

#         # Build the query to get all confirmed reservations with their room details
#         base_query = """
#             SELECT 
#                 r.id AS reservation_id,
#                 r.Current_Status,
#                 gr.start_date,
#                 gr.end_date,
#                 r.outlet,
#                 fr.id AS fitrate_id,
#                 fr.quantity AS room_quantity,
#                 fr.rateID,
#                 rt.room_name,
#                 rt.room_type,
#                 rt.rate AS room_rate,
#                 rt.currency,
#                 mp.mp AS meal_plan,
#                 mp.rate AS meal_rate
#             FROM hotel_tblreservation r
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#             AND fr.is_active = 1
#             AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out', 'Cancelled')
#             AND (
#                 (gr.start_date BETWEEN %s AND %s)
#                 OR (gr.end_date BETWEEN %s AND %s)
#                 OR (gr.start_date <= %s AND gr.end_date >= %s)
#             )
#         """

#         params = [first_day, last_day, first_day, last_day, first_day, last_day]

#         # Add outlet filter if provided
#         if outlet:
#             base_query += " AND r.outlet = %s"
#             params.append(outlet)

#         # Order by date for consistent processing
#         base_query += " ORDER BY gr.start_date"

#         cursor.execute(base_query, params)
#         reservations = cursor.fetchall()

#         # Process each reservation and its fitrate entries
#         for reservation in reservations:
#             # Parse dates
#             start_date = reservation['start_date']
#             end_date = reservation['end_date']
#             status = reservation['Current_Status']
            
#             if isinstance(start_date, str):
#                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             if isinstance(end_date, str):
#                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
#             # Determine the nights to process
#             # For same-day stay, we need to process the arrival day but not have a night stay
#             is_single_night = start_date == end_date
            
#             if is_single_night:
#                 # For single night, we only process the arrival day, no overnight stay
#                 night_dates = []  # No nights to process for occupancy
#                 arrival_date = start_date
#             else:
#                 # Normal case: exclude checkout day from loop
#                 range_start = max(start_date, first_day)
#                 range_end = min(end_date - timedelta(days=1), last_day)
                
#                 # Generate all nights between start_date and end_date (excluding checkout day)
#                 night_dates = []
#                 current_day = range_start
#                 while current_day <= range_end:
#                     night_dates.append(current_day)
#                     current_day += timedelta(days=1)
                
#                 arrival_date = start_date
            
#             # Rates
#             room_rate = float(reservation['room_rate'] or 0)
#             meal_rate = float(reservation['meal_rate'] or 0)
#             total_rate_per_room = room_rate + meal_rate
            
#             room_quantity = int(reservation['room_quantity'] or 1)
#             room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"
            
#             # Process arrival (always for start_date if within range)
#             if arrival_date >= first_day and arrival_date <= last_day:
#                 date_str = arrival_date.strftime('%Y-%m-%d')
#                 daily_amount = room_quantity * total_rate_per_room
                
#                 if date_str in results:
#                     results[date_str]["booked_rooms"] += room_quantity
                    
#                     results[date_str]["rooms_by_type"][room_type_key]["room_name"] = reservation['room_name']
#                     results[date_str]["rooms_by_type"][room_type_key]["room_type"] = reservation['room_type']
#                     results[date_str]["rooms_by_type"][room_type_key]["booked_quantity"] += room_quantity
#                     results[date_str]["rooms_by_type"][room_type_key]["rate"] = total_rate_per_room
                    
#                     if reservation['reservation_id'] not in results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"]:
#                         results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"].append(reservation['reservation_id'])
                    
#                     reservation_detail = {
#                         "reservation_id": reservation['reservation_id'],
#                         "room_name": reservation['room_name'],
#                         "room_type": reservation['room_type'],
#                         "quantity": room_quantity,
#                         "rate_per_room": total_rate_per_room,
#                         "total_amount": daily_amount,
#                         "meal_plan": reservation['meal_plan'],
#                         "currency": reservation['currency'],
#                         "outlet": reservation['outlet'],
#                         "start_date": start_date.strftime('%Y-%m-%d'),
#                         "end_date": end_date.strftime('%Y-%m-%d'),
#                         "status": status
#                     }
                    
#                     results[date_str]["reservations"].append(reservation_detail)
                    
#                     if status in ['Reserved', 'Registered']:
#                         results[date_str]["confirmed"]["booked_rooms"] += room_quantity
#                         results[date_str]["confirmed"]["amount"] += daily_amount
#                         results[date_str]["confirmed"]["reservations"].append(reservation_detail)
                    
#                     if status == 'Cancelled':
#                         results[date_str]["cancelled"]["booked_rooms"] += room_quantity
#                         results[date_str]["cancelled"]["amount"] += daily_amount
#                         results[date_str]["cancelled"]["reservations"].append(reservation_detail)
                    
#                     # ARRIVAL (always for start_date) -- counts toward occupancy for that night
#                     if status in ['Registered', 'Checked Out']:
#                         results[date_str]["arrivals"]["booked_rooms"] += room_quantity
#                         results[date_str]["arrivals"]["amount"] += daily_amount
#                         results[date_str]["arrivals"]["reservations"].append(reservation_detail)
            
#             # Process nights (excluding arrival day for multi-night stays)
#             for current_day in night_dates:
#                 if not is_single_night and current_day == start_date:
#                     continue
                    
#                 date_str = current_day.strftime('%Y-%m-%d')
#                 daily_amount = room_quantity * total_rate_per_room
                
#                 if date_str not in results:
#                     continue
                
#                 if start_date <= current_day < end_date:
#                     results[date_str]["booked_rooms"] += room_quantity
                
#                 results[date_str]["rooms_by_type"][room_type_key]["room_name"] = reservation['room_name']
#                 results[date_str]["rooms_by_type"][room_type_key]["room_type"] = reservation['room_type']

#                 if status in ['Reserved', 'Registered'] and start_date <= current_day < end_date:
#                     results[date_str]["rooms_by_type"][room_type_key]["booked_quantity"] += room_quantity
#                 results[date_str]["rooms_by_type"][room_type_key]["rate"] = total_rate_per_room
                
#                 if reservation['reservation_id'] not in results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"]:
#                     results[date_str]["rooms_by_type"][room_type_key]["reservation_ids"].append(reservation['reservation_id'])
                
#                 reservation_detail = {
#                     "reservation_id": reservation['reservation_id'],
#                     "room_name": reservation['room_name'],
#                     "room_type": reservation['room_type'],
#                     "quantity": room_quantity,
#                     "rate_per_room": total_rate_per_room,
#                     "total_amount": daily_amount,
#                     "meal_plan": reservation['meal_plan'],
#                     "currency": reservation['currency'],
#                     "outlet": reservation['outlet'],
#                     "start_date": start_date.strftime('%Y-%m-%d'),
#                     "end_date": end_date.strftime('%Y-%m-%d'),
#                     "status": status
#                 }
                
#                 results[date_str]["reservations"].append(reservation_detail)
                
#                 if status in ['Reserved', 'Registered']:
#                     results[date_str]["confirmed"]["booked_rooms"] += room_quantity
#                     results[date_str]["confirmed"]["amount"] += daily_amount
#                     results[date_str]["confirmed"]["reservations"].append(reservation_detail)
                
#                 if status == 'Cancelled' and start_date == current_day :
#                     results[date_str]["cancelled"]["booked_rooms"] += room_quantity
#                     results[date_str]["cancelled"]["amount"] += daily_amount
#                     results[date_str]["cancelled"]["reservations"].append(reservation_detail)
                
#                 # STAYOVER (middle days only, not arrival or departure) -- counts toward occupancy for that night
#                 if status in ['Registered', 'Checked Out'] and start_date < current_day < end_date:
#                     results[date_str]["stayovers"]["booked_rooms"] += room_quantity
#                     results[date_str]["stayovers"]["amount"] += daily_amount
#                     results[date_str]["stayovers"]["reservations"].append(reservation_detail)
            
#             # DEPARTURE (handled for all reservations, even single-night) -- does NOT count toward occupancy
#             dep_date_str = end_date.strftime('%Y-%m-%d')
            
#             if dep_date_str in results and status in ['Registered', 'Checked Out']:
#                 daily_amount = room_quantity * total_rate_per_room
                
#                 reservation_detail = {
#                     "reservation_id": reservation['reservation_id'],
#                     "room_name": reservation['room_name'],
#                     "room_type": reservation['room_type'],
#                     "quantity": room_quantity,
#                     "rate_per_room": total_rate_per_room,
#                     "total_amount": daily_amount,
#                     "meal_plan": reservation['meal_plan'],
#                     "currency": reservation['currency'],
#                     "outlet": reservation['outlet'],
#                     "start_date": start_date.strftime('%Y-%m-%d'),
#                     "end_date": end_date.strftime('%Y-%m-%d'),
#                     "status": status
#                 }
                
#                 results[dep_date_str]["departures"]["booked_rooms"] += room_quantity
#                 results[dep_date_str]["departures"]["amount"] += daily_amount
#                 results[dep_date_str]["departures"]["reservations"].append({
#                     **reservation_detail,
#                     "departure_status": status
#                 })

#         # Registered rooms query -- kept ONLY for room-level detail (room_no, room_state, etc.)
#         # in the response; no longer used to compute occupied_rooms.
#         registered_rooms_query = """
#             SELECT DISTINCT
#                 rd.id AS detail_id,
#                 rd.Reservation_ID,
#                 rd.room_id,
#                 rd.is_current,
#                 r.id AS reservation_id,
#                 r.Current_Status,
#                 gr.start_date,
#                 gr.end_date,
#                 rm.id AS room_id,
#                 rm.outlet AS room_outlet,
#                 rm.room_no,
#                 rm.room_state,
#                 rm.phone_no,
#                 rm.preference,
#                 rm.room_view,
#                 rm.room_type,
#                 rm.room_notes,
#                 rt.room_name,
#                 rt.rate AS room_rate,
#                 mp.mp AS meal_plan,
#                 mp.rate AS meal_rate
#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblreservation r ON rd.Reservation_ID = r.id
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             INNER JOIN hotel_tblrooms rm ON rd.room_id = rm.id
#             LEFT JOIN hotel_tblfitrate fr ON r.id = fr.reservationID AND fr.is_active = 1
#             LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
#             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id AND mp.is_active = 1
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#             AND rd.is_active = 1
#             AND r.Current_Status = 'Registered'
#             AND rd.is_current = 1
#             AND (
#                 (gr.start_date BETWEEN %s AND %s)
#                 OR (gr.end_date BETWEEN %s AND %s)
#                 OR (gr.start_date <= %s AND gr.end_date >= %s)
#             )
#         """
        
#         registered_params = [first_day, last_day, first_day, last_day, first_day, last_day]
        
#         if outlet:
#             registered_rooms_query += " AND r.outlet = %s"
#             registered_params.append(outlet)
        
#         cursor.execute(registered_rooms_query, registered_params)
#         registered_rooms = cursor.fetchall()
        
#         # Process registered rooms -- room-detail list only, does NOT touch occupied_rooms anymore
#         for room in registered_rooms:
#             start_date = room['start_date']
#             end_date = room['end_date']
            
#             if isinstance(start_date, str):
#                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             if isinstance(end_date, str):
#                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
#             range_start = max(start_date, first_day)
#             range_end = min(end_date - timedelta(days=1), last_day)  # Subtract 1 day to exclude departure
            
#             room_rate = float(room['room_rate'] or 0)
#             meal_rate = float(room['meal_rate'] or 0)
#             total_rate_per_room = room_rate + meal_rate
            
#             room_type_key = f"{room['room_name']}_{room['room_type']}"
            
#             current_day = range_start
#             while current_day <= range_end:
#                 date_str = current_day.strftime('%Y-%m-%d')
                
#                 results[date_str]["registered_rooms"]["total_amount"] += total_rate_per_room
                
#                 room_detail = {
#                     "reservation_id": room['reservation_id'],
#                     "room_id": room['room_id'],
#                     "room_no": room['room_no'],
#                     "room_type": room['room_type'],
#                     "room_name": room['room_name'],
#                     "room_state": room['room_state'],
#                     "preference": room['preference'],
#                     "room_view": room['room_view'],
#                     "phone_no": room['phone_no'],
#                     "room_notes": room['room_notes'],
#                     "rate": total_rate_per_room,
#                     "meal_plan": room['meal_plan'],
#                     "start_date": start_date.strftime('%Y-%m-%d'),
#                     "end_date": end_date.strftime('%Y-%m-%d')
#                 }
                
#                 results[date_str]["registered_rooms"]["rooms"].append(room_detail)
                
#                 current_day += timedelta(days=1)
        
#         # Convert defaultdict to regular dict for JSON serialization
#         daily_stats = []
#         for date_str, day_data in results.items():
#             rooms_list = []
#             for room_key, room_data in day_data["rooms_by_type"].items():
#                 rooms_list.append({
#                     "room_name": room_data["room_name"],
#                     "room_type": room_data["room_type"],
#                     "booked_quantity": room_data["booked_quantity"],
#                     "occupied_quantity": room_data["occupied_quantity"],
#                     "rate": room_data["rate"],
#                     "reservation_count": len(room_data["reservation_ids"])
#                 })
            
#             unique_rooms = []
#             seen_room_ids = set()
#             for room in day_data["registered_rooms"]["rooms"]:
#                 if room["room_id"] not in seen_room_ids:
#                     seen_room_ids.add(room["room_id"])
#                     unique_rooms.append(room)

#             # -------- OCCUPANCY = ARRIVALS + STAYOVERS --------
#             occupied_rooms = day_data["arrivals"]["booked_rooms"] + day_data["stayovers"]["booked_rooms"]
            
#             daily_stats.append({
#                 "date": day_data["date"],
#                 "hotel_capacity": hotel_total_rooms,
#                 "booked_rooms": day_data["booked_rooms"],

#                 "occupied_rooms": occupied_rooms,

#                 "vacant_rooms": hotel_total_rooms - occupied_rooms,
#                 "occupancy_rate": round((occupied_rooms / hotel_total_rooms * 100), 2) if hotel_total_rooms > 0 else 0,
#                 "reservations_count": len(day_data["reservations"]),
#                 "arrivals": day_data["arrivals"]["booked_rooms"],
#                 "stayovers": day_data["stayovers"]["booked_rooms"],
                
#                 "departures":  day_data["departures"]["booked_rooms"],

                
#                 "confirmed": day_data["confirmed"]["booked_rooms"],
                  
#                 "cancelled": day_data["cancelled"]["booked_rooms"],
#                 "registered_rooms": unique_rooms
                
#             })
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "data": {
#                 "daily": daily_stats,
#                 "filters": {
#                     "from_date": from_date,
#                     "to_date": to_date,
#                     "outlet": outlet
#                 }
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app_file415.route("/analytics/rooms-details", methods=["GET"])
# @cross_origin()
# def get_rooms_details():
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
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token:
#             return {"error": "No token provided."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get date from query parameters
#         date_param = request.args.get('date')
#         outlet = request.args.get('outlet', default=None, type=str)
#         filter_type = request.args.get('filter', default=None, type=str)
        
#         # Validate date
#         if not date_param:
#             return {"error": "Date is required (format: YYYY-MM-DD)"}, 400
        
#         try:
#             target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
        
#         # Validate filter if provided
#         valid_filters = ['arrival', 'stayover', 'departure', 'cancelled', 'booked']
#         if filter_type and filter_type not in valid_filters:
#             return {"error": f"Invalid filter. Must be one of: {', '.join(valid_filters)}"}, 400
        
#         # Get total hotel rooms count
#         total_rooms_query = """
#             SELECT COUNT(*) as total_rooms
#             FROM hotel_tblrooms
#             WHERE is_active = 1
#         """
#         total_rooms_params = []
        
#         if outlet:
#             total_rooms_query += " AND outlet = %s"
#             total_rooms_params.append(outlet)
        
#         cursor.execute(total_rooms_query, total_rooms_params)
#         hotel_total_rooms = cursor.fetchone()['total_rooms'] or 0
        
#         # Initialize response data
#         response_data = {
#             "date": target_date.strftime('%Y-%m-%d'),
#             "hotel_capacity": hotel_total_rooms,
#             "filters": {
#                 "date": target_date.strftime('%Y-%m-%d'),
#                 "outlet": outlet,
#                 "filter": filter_type
#             }
#         }
        
#         # Get registered rooms with their FIT rates
#         registered_query = """
#             SELECT DISTINCT
#                 rd.id AS detail_id,
#                 rd.Reservation_ID as reservation_id,
#                 rd.room_id,
#                 r.Current_Status,
#                 gr.No_of_children,
#                 gr.No_of_adults,
#                 gr.Guest_Notes,
#                 gr.start_date,
#                 gr.end_date,
#                 rm.id AS room_id,
#                 rm.outlet AS room_outlet,
#                 rm.room_no,
#                 rm.room_state,
#                 rm.phone_no,
#                 rm.preference,
#                 rm.room_view,
#                 rm.room_type,
#                 rm.room_notes,
#                 c.name,
#                 c.email,
#                 c.phone
#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblreservation r ON rd.Reservation_ID = r.id
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             INNER JOIN hotel_tblrooms rm ON rd.room_id = rm.id
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#             AND rd.is_active = 1
#             AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
#             AND rd.is_current = 1
#             AND gr.start_date <= %s
#             AND gr.end_date >= %s
#         """

#         registered_params = [target_date, target_date]

#         if outlet:
#             registered_query += " AND r.outlet = %s"
#             registered_params.append(outlet)

#         cursor.execute(registered_query, registered_params)
#         registered_rooms = cursor.fetchall()

#         # Get all reservation IDs
#         reservation_ids = [room['reservation_id'] for room in registered_rooms]

#         # Second query: Get FIT rates for these reservations
#         fit_rates_by_reservation = {}
#         if reservation_ids:
#             fit_rates_query = """
#                 SELECT 
#                     fr.reservationID,
#                     rt.room_name,
#                     rt.rate AS room_rate,
#                     mp.mp AS meal_plan,
#                     mp.rate AS meal_rate,
#                     fr.quantity
#                 FROM hotel_tblfitrate fr
#                 LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
#                 LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id AND mp.is_active = 1
#                 WHERE fr.is_active = 1
#                 AND fr.reservationID IN ({})
#             """.format(','.join(['%s'] * len(reservation_ids)))
            
#             cursor.execute(fit_rates_query, reservation_ids)
#             fit_rates = cursor.fetchall()
            
#             # Group fit rates by reservation_id
#             for rate in fit_rates:
#                 rid = rate['reservationID']
#                 if rid not in fit_rates_by_reservation:
#                     fit_rates_by_reservation[rid] = []
#                 fit_rates_by_reservation[rid].append({
#                     "room_name": rate['room_name'],
#                     "room_rate": float(rate['room_rate']) if rate['room_rate'] else 0,
#                     "meal_plan": rate['meal_plan'],
#                     "meal_rate": float(rate['meal_rate']) if rate['meal_rate'] else 0,
#                     "quantity": rate['quantity']
#                 })

#         # Process registered rooms into arrivals, stayovers, departures
#         arrivals_list = []
#         stayover_list = []
#         departures_list = []
        
#         for room in registered_rooms:
#             start_date = room['start_date']
#             end_date = room['end_date']
            
#             if isinstance(start_date, str):
#                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             if isinstance(end_date, str):
#                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
#             # Check if it's a same-day stay
#             is_single_night = start_date == end_date
            
#             # Get fit rates for this reservation
#             room_fit_rates = fit_rates_by_reservation.get(room['reservation_id'], [])
            
#             # Calculate total rate
#             total_rate = 0
#             for fr in room_fit_rates:
#                 total_rate += (fr['room_rate'] + fr['meal_rate']) * fr['quantity']
            
#             # Get unique meal plans and room names
#             meal_plans = list(set([fr['meal_plan'] for fr in room_fit_rates if fr.get('meal_plan')]))
#             meal_plan = ', '.join(meal_plans) if meal_plans else None
            
#             room_names = list(set([fr['room_name'] for fr in room_fit_rates if fr.get('room_name')]))
#             room_name = ', '.join(room_names) if room_names else room['room_type']
            
#             room_detail = {
#                 "reservation_id": room['reservation_id'],
#                 "detail_id": room['detail_id'],
#                 "room_id": room['room_id'],
#                 "room_no": room['room_no'],
#                 "room_type": room['room_type'],
#                 "room_name": room_name,
#                 "room_state": room['room_state'],
#                 "preference": room['preference'],
#                 "room_view": room['room_view'],
#                 "phone_no": room['phone_no'],
#                 "room_notes": room['room_notes'],
#                 "rate": total_rate,
#                 "meal_plan": meal_plan,
#                 "start_date": start_date.strftime('%Y-%m-%d'),
#                 "end_date": end_date.strftime('%Y-%m-%d'),
#                 "guest": {
#                     "name": room['name'],
#                     "email": room['email'],
#                     "phone": room['phone']
#                 },
#                 "no_of_adults": room['No_of_adults'],
#                 "no_of_children": room['No_of_children'],
#                 "guest_notes": room['Guest_Notes'],
#                 "fit_rates": room_fit_rates
#             }

#             # Determine if it's arrival, stayover, or departure
#             is_arrival = start_date == target_date
#             is_departure = end_date == target_date
#             is_stayover = start_date < target_date < end_date
            
#             # For same-day stay, both arrival and departure are true
#             if is_arrival:
#                 arrivals_list.append(room_detail)
#             if is_departure:
#                 departures_list.append(room_detail)
#             if is_stayover:
#                 stayover_list.append(room_detail)
        
#         # Add to response based on filter
#         if not filter_type or filter_type == 'arrival':
#             response_data["arrivals"] = {
#                 "count": len(arrivals_list),
#                 "rooms": arrivals_list
#             }
        
#         if not filter_type or filter_type == 'stayover':
#             response_data["stayover_rooms"] = {
#                 "count": len(stayover_list),
#                 "rooms": stayover_list
#             }
        
#         if not filter_type or filter_type == 'departure':
#             response_data["departures"] = {
#                 "count": len(departures_list),
#                 "rooms": departures_list
#             }
        
#         # 2. GET BOOKED ROOMS (from fitrate - all confirmed reservations for this date)
#         booked_query = """
#             SELECT 
#                 r.id AS reservation_id,
#                 r.Current_Status,
#                 gr.No_of_children,
#                 gr.No_of_adults,
#                 gr.Guest_Notes,
#                 gr.start_date,
#                 gr.end_date,
#                 r.outlet,
#                 fr.id AS fitrate_id,
#                 fr.quantity AS room_quantity,
#                 fr.rateID,
#                 rt.room_name,
#                 rt.room_type,
#                 rt.rate AS room_rate,
#                 rt.currency,
#                 mp.mp AS meal_plan,
#                 mp.rate AS meal_rate,
#                 c.name,
#                 c.email,
#                 c.phone
#             FROM hotel_tblreservation r
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#             AND fr.is_active = 1
#             AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
#             AND gr.start_date <= %s
#             AND gr.end_date > %s
#         """
        
#         booked_params = [target_date, target_date]
        
#         if outlet:
#             booked_query += " AND r.outlet = %s"
#             booked_params.append(outlet)
        
#         cursor.execute(booked_query, booked_params)
#         booked_reservations = cursor.fetchall()
        
#         # Process booked reservations
#         booked_rooms_by_type = defaultdict(lambda: {
#             "room_name": "",
#             "room_type": "",
#             "quantity": 0,
#             "rate": 0,
#             "total_amount": 0,
#             "reservations": []
#         })
        
#         for reservation in booked_reservations:
#             start_date = reservation['start_date']
#             end_date = reservation['end_date']
#             status = reservation['Current_Status']
            
#             if isinstance(start_date, str):
#                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             if isinstance(end_date, str):
#                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
#             room_rate = float(reservation['room_rate'] or 0)
#             meal_rate = float(reservation['meal_rate'] or 0)
#             total_rate = room_rate + meal_rate
#             room_quantity = int(reservation['room_quantity'] or 1)
#             daily_amount = room_quantity * total_rate
            
#             room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"
            
#             # Group by room type for booked rooms
#             booked_rooms_by_type[room_type_key]["room_name"] = reservation['room_name']
#             booked_rooms_by_type[room_type_key]["room_type"] = reservation['room_type']
#             booked_rooms_by_type[room_type_key]["quantity"] += room_quantity
#             booked_rooms_by_type[room_type_key]["rate"] = total_rate
#             booked_rooms_by_type[room_type_key]["total_amount"] += daily_amount
#             booked_rooms_by_type[room_type_key]["reservations"].append({
#                 "reservation_id": reservation['reservation_id'],
#                 "status": status,
#                 "no_of_adults": reservation['No_of_adults'],
#                 "no_of_children": reservation['No_of_children'],
#                 "guest_notes": reservation['Guest_Notes'],
#                 "quantity": room_quantity,
#                 "rate_per_room": total_rate,
#                 "total_amount": daily_amount,
#                 "start_date": start_date.strftime('%Y-%m-%d'),
#                 "end_date": end_date.strftime('%Y-%m-%d'),
#                 "meal_plan": reservation['meal_plan'],
#                 "currency": reservation['currency'],
#                 "guest": {
#                     "name": reservation['name'],
#                     "email": reservation['email'],
#                     "phone": reservation['phone']
#                 }
#             })
        
#         # Add booked rooms to response if no filter or filter is 'booked'
#         if not filter_type or filter_type == 'booked':
#             response_data["booked_rooms"] = {
#                 "count": sum(room["quantity"] for room in booked_rooms_by_type.values()),
#                 "by_type": list(booked_rooms_by_type.values())
#             }
        
#         # 3. GET CANCELLED ROOMS for this date
#         cancelled_query = """
#             SELECT 
#                 r.id AS reservation_id,
#                 r.Current_Status,
#                 gr.No_of_children,
#                 gr.No_of_adults,
#                 gr.Guest_Notes,
#                 gr.start_date,
#                 gr.end_date,
#                 r.outlet,
#                 fr.id AS fitrate_id,
#                 fr.quantity AS room_quantity,
#                 fr.rateID,
#                 rt.room_name,
#                 rt.room_type,
#                 rt.rate AS room_rate,
#                 rt.currency,
#                 mp.mp AS meal_plan,
#                 mp.rate AS meal_rate,
#                 c.name,
#                 c.email,
#                 c.phone
#             FROM hotel_tblreservation r
#             INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
#             INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
#             LEFT JOIN customers c ON r.Guest_ID = c.id
#             WHERE r.is_active = 1 
#             AND gr.is_active = 1
#             AND fr.is_active = 1
#             AND r.Current_Status = 'Cancelled'
#             AND gr.start_date <= %s
#             AND gr.end_date >= %s
#         """
        
#         cancelled_params = [target_date, target_date]
        
#         if outlet:
#             cancelled_query += " AND r.outlet = %s"
#             cancelled_params.append(outlet)
        
#         cursor.execute(cancelled_query, cancelled_params)
#         cancelled_reservations = cursor.fetchall()
        
#         # Process cancelled reservations
#         cancelled_rooms_by_type = defaultdict(lambda: {
#             "room_name": "",
#             "room_type": "",
#             "quantity": 0,
#             "rate": 0,
#             "total_amount": 0,
#             "reservations": []
#         })
        
#         cancelled_arrivals_list = []
#         cancelled_departures_list = []
        
#         for reservation in cancelled_reservations:
#             start_date = reservation['start_date']
#             end_date = reservation['end_date']
#             status = reservation['Current_Status']
            
#             if isinstance(start_date, str):
#                 start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             if isinstance(end_date, str):
#                 end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
#             room_rate = float(reservation['room_rate'] or 0)
#             meal_rate = float(reservation['meal_rate'] or 0)
#             total_rate = room_rate + meal_rate
#             room_quantity = int(reservation['room_quantity'] or 1)
#             daily_amount = room_quantity * total_rate
            
#             room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"
            
#             # Group by room type for cancelled rooms
#             cancelled_rooms_by_type[room_type_key]["room_name"] = reservation['room_name']
#             cancelled_rooms_by_type[room_type_key]["room_type"] = reservation['room_type']
#             cancelled_rooms_by_type[room_type_key]["quantity"] += room_quantity
#             cancelled_rooms_by_type[room_type_key]["rate"] = total_rate
#             cancelled_rooms_by_type[room_type_key]["total_amount"] += daily_amount
            
#             reservation_detail = {
#                 "reservation_id": reservation['reservation_id'],
#                 "status": status,
#                 "quantity": room_quantity,
#                 "rate_per_room": total_rate,
#                 "total_amount": daily_amount,
#                 "start_date": start_date.strftime('%Y-%m-%d'),
#                 "end_date": end_date.strftime('%Y-%m-%d'),
#                 "meal_plan": reservation['meal_plan'],
#                 "currency": reservation['currency'],
#                 "guest": {
#                     "name": reservation['name'],
#                     "email": reservation['email'],
#                     "phone": reservation['phone']
#                 },
#                 "no_of_adults": reservation['No_of_adults'],
#                 "no_of_children": reservation['No_of_children'],
#                 "guest_notes": reservation['Guest_Notes']
#             }
            
#             cancelled_rooms_by_type[room_type_key]["reservations"].append(reservation_detail)
            
#             # Check if cancelled reservation was supposed to arrive today
#             if start_date == target_date:
#                 cancelled_arrivals_list.append(reservation_detail)
            
#             # Check if cancelled reservation was supposed to depart today
#             if end_date == target_date:
#                 cancelled_departures_list.append(reservation_detail)
        
#         # Add cancelled rooms to response if no filter or filter is 'cancelled'
#         if not filter_type or filter_type == 'cancelled':
#             response_data["cancelled_rooms"] = {
#                 "count": sum(room["quantity"] for room in cancelled_rooms_by_type.values()),
#                 "by_type": list(cancelled_rooms_by_type.values()),
#                 "cancelled_arrivals": {
#                     "count": len(cancelled_arrivals_list),
#                     "rooms": cancelled_arrivals_list
#                 },
#                 "cancelled_departures": {
#                     "count": len(cancelled_departures_list),
#                     "rooms": cancelled_departures_list
#                 }
#             }
        
#         mydb.close()
        
#         return jsonify({
#             "success": True,
#             "data": response_data
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from calendar import monthrange
import json

load_dotenv()
from root.auth.check import token_auth

app_file415 = Blueprint('app_file415', __name__)

@app_file415.route("/analytics/reservation-status", methods=["GET"])
@cross_origin()
def get_reservation_status_stats():
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

        # Get month and year from query parameters, default to current month
        month = request.args.get('month', default=datetime.now().month, type=int)
        year = request.args.get('year', default=datetime.now().year, type=int)
        
        # Optional filter by outlet
        outlet = request.args.get('outlet', default=None, type=str)
        
        # Validate month and year
        if month < 1 or month > 12:
            return {"error": "Invalid month. Month must be between 1 and 12."}, 400
            
        # Get first and last day of the month
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, monthrange(year, month)[1]).date()
        
        # Get today's date for checking-out logic
        today = datetime.now().date()
        
        # Initialize results dictionary with all days of the month
        results = {}
        current_date = first_day
        while current_date <= last_day:
            date_str = current_date.strftime('%Y-%m-%d')
            results[date_str] = {
                "date": date_str,
                "reserved": 0,
                "registered": 0,
                "checking_out": 0,
                "checked_out": 0,
                "cancelled": 0,
                "total": 0
            }
            current_date += timedelta(days=1)
        
        # Build the base query
        base_query = """
            SELECT 
                r.id,
                r.Current_Status,
                gr.start_date,
                gr.end_date,
                r.Check_In,
                r.Check_Out
            FROM hotel_tblreservation r
            INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
            WHERE r.is_active = 1 
            AND gr.is_active = 1
            AND (
                (gr.start_date BETWEEN %s AND %s)
                OR (gr.end_date BETWEEN %s AND %s)
                OR (gr.start_date <= %s AND gr.end_date >= %s)
            )
        """
        
        params = [first_day, last_day, first_day, last_day, first_day, last_day]
        
        # Add outlet filter if provided
        if outlet:
            base_query += " AND r.outlet = %s"
            params.append(outlet)
        
        cursor.execute(base_query, params)
        reservations = cursor.fetchall()
        
        # Process each reservation and count for each day in the month
        for reservation in reservations:
            # Parse dates
            start_date = reservation['start_date']
            end_date = reservation['end_date']
            current_status = reservation['Current_Status']
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Determine the range of days this reservation covers within the requested month
            range_start = max(start_date, first_day)
            range_end = min(end_date, last_day)
            
            # For each day in the reservation's range
            current_day = range_start
            while current_day <= range_end:
                date_str = current_day.strftime('%Y-%m-%d')
                
                # Apply the special logic for checking-out
                if current_status == "Registered":
                    if end_date < today:
                        # This is considered checking-out
                        results[date_str]["checking_out"] += 1
                    else:
                        # Regular registered
                        results[date_str]["registered"] += 1
                elif current_status == "Reserved":
                    results[date_str]["reserved"] += 1
                elif current_status == "Checked Out":
                    results[date_str]["checked_out"] += 1
                elif current_status == "Cancelled":
                    results[date_str]["cancelled"] += 1
                else:
                    # For any other status, count as is
                    status_key = current_status.lower().replace('-', '_')
                    if status_key in results[date_str]:
                        results[date_str][status_key] += 1
                
                results[date_str]["total"] += 1
                current_day += timedelta(days=1)
        
        # Convert results to a list for easier frontend consumption
        daily_stats = list(results.values())
        
        # Calculate summary statistics for the month
        summary = {
            "total_reservations": sum(day["total"] for day in daily_stats),
            "total_reserved": sum(day["reserved"] for day in daily_stats),
            "total_registered": sum(day["registered"] for day in daily_stats),
            "total_checking_out": sum(day["checking_out"] for day in daily_stats),
            "total_checked_out": sum(day["checked_out"] for day in daily_stats),
            "total_cancelled": sum(day["cancelled"] for day in daily_stats),
            "month": month,
            "year": year
        }
        
        mydb.close()
        
        return jsonify({
            "success": True,
            "data": {
                "daily": daily_stats,
                "summary": summary,
                "filters": {
                    "month": month,
                    "year": year,
                    "outlet": outlet
                }
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app_file415.route("/analytics/reservation-status/export", methods=["POST"])
@cross_origin()
def export_reservation_status():
    """
    Endpoint to export the data in a different format (for CSV/Excel download)
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
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        json_data = request.get_json() or {}
        month = json_data.get('month', datetime.now().month)
        year = json_data.get('year', datetime.now().year)
        outlet = json_data.get('outlet')
        format_type = json_data.get('format', 'json')  # 'json', 'csv', etc.

        # Similar logic as above to get the data
        # Then format it appropriately for export
        

        # For now, return a success message
        return jsonify({
            "success": True,
            "message": f"Export functionality for {format_type} format would be implemented here"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app_file415.route("/analytics/reservation-status/summary", methods=["GET"])
@cross_origin()
def get_reservation_summary():
    """
    Get just the summary statistics without daily breakdown
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
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        outlet = request.args.get('outlet')

        # Build query for summary
        query = """
            SELECT 
                r.Current_Status,
                COUNT(DISTINCT r.id) as count
            FROM hotel_tblreservation r
            INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
            WHERE r.is_active = 1 
            AND gr.is_active = 1
        """
        
        params = []
        
        if start_date and end_date:
            query += " AND ((gr.start_date BETWEEN %s AND %s) OR (gr.end_date BETWEEN %s AND %s))"
            params.extend([start_date, end_date, start_date, end_date])
        
        if outlet:
            query += " AND r.outlet = %s"
            params.append(outlet)
        
        query += " GROUP BY r.Current_Status"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Format the summary
        summary = {
            "Reserved": 0,
            "Registered": 0,
            "Checked Out": 0,
            "Cancelled": 0
        }
        
        for row in results:
            summary[row['Current_Status']] = row['count']
        
        mydb.close()
        
        return jsonify({
            "success": True,
            "data": summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app_file415.route("/cancel-reservation", methods=["POST"])
@cross_origin()
def cancel_reservation():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True)

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

        # -------- INPUT --------
        data = request.get_json()
        reservation_id = data.get("reservation_id")

        if not reservation_id:
            return {"error": "reservation_id is required"}, 400

        # -------- CHECK IF EXISTS --------
        cursor.execute(
            "SELECT id, Current_Status FROM hotel_tblreservation WHERE id = %s",
            (reservation_id,)
        )
        reservation = cursor.fetchone()

        if not reservation:
            return {"error": "Reservation not found"}, 404

        # -------- OPTIONAL: ALREADY CANCELLED --------
        if reservation["Current_Status"] == "Cancelled":
            return {"message": "Reservation already cancelled"}, 200

        # -------- UPDATE STATUS --------
        cursor.execute(
            "UPDATE hotel_tblreservation SET Current_Status = %s WHERE id = %s",
            ("Cancelled", reservation_id)
        )

        mydb.commit()
        mydb.close()

        return {
            "message": "Reservation cancelled successfully",
            "reservation_id": reservation_id
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500
    
@app_file415.route("/cancel-reservation-by-outlet-id", methods=["POST"])
@cross_origin()
def cancel_reservation_by_outlet_id():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True)

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

        # -------- INPUT --------
        data = request.get_json()
        outlet_reservation_id = data.get("reservation_outlet_id")

        if not outlet_reservation_id:
            return {"error": "reservation_outlet_id is required"}, 400

        # -------- FIND RESERVATION --------
        cursor.execute(
            """
            SELECT id, Current_Status
            FROM hotel_tblreservation
            WHERE reservation_outlet_id = %s
            LIMIT 1
            """,
            (outlet_reservation_id,)
        )
        reservation = cursor.fetchone()

        if not reservation:
            return {"error": "Reservation not found"}, 404

        reservation_id = reservation["id"]

        # -------- ALREADY CANCELLED --------
        if reservation["Current_Status"] == "Cancelled":
            return {
                "message": "Reservation already cancelled",
                "reservation_id": reservation_id
            }, 200

        # -------- CANCEL RESERVATION --------
        cursor.execute(
            """
            UPDATE hotel_tblreservation
            SET Current_Status = %s
            WHERE id = %s
            """,
            ("Cancelled", reservation_id)
        )

        # -------- OPTIONAL: ALSO DEACTIVATE FIT RATES --------
        cursor.execute(
            """
            UPDATE hotel_tblfitrate
            SET is_active = 0
            WHERE reservationID = %s
            """,
            (reservation_id,)
        )

        mydb.commit()
        mydb.close()

        return {
            "message": "Reservation cancelled successfully",
            "reservation_id": reservation_id,
            "reservation_outlet_id": outlet_reservation_id
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

# from datetime import date
# from collections import defaultdict
# @app_file415.route("/analytics/rooms-confirmed", methods=["GET"])
# @cross_origin()
# def get_rooms_confirmed_stats():
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
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token:
#             return {"error": "No token provided."}, 400
#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         from_date = request.args.get('from_date')
#         to_date = request.args.get('to_date')
#         outlet = request.args.get('outlet', default=None, type=str)

#         if not outlet:
#             return {"error": "outlet is required."}, 400
#         if not from_date or not to_date:
#             return {"error": "Both from_date and to_date are required (format: YYYY-MM-DD)"}, 400

#         try:
#             first_day = datetime.strptime(from_date, '%Y-%m-%d').date()
#             last_day = datetime.strptime(to_date, '%Y-%m-%d').date()
#         except ValueError:
#             return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

#         today = date.today()

#         def to_date_obj(v):
#             return datetime.strptime(v, '%Y-%m-%d').date() if isinstance(v, str) else v

#         def fmt(d):
#             return d.strftime('%Y-%m-%d')

#         # -------- capacity (active rooms for the outlet) --------
#         cursor.execute("""
#             SELECT COUNT(*) AS total_rooms
#             FROM hotel_tblrooms
#             WHERE is_active = 1 AND outlet = %s
#         """, (outlet,))
#         hotel_total_rooms = cursor.fetchone()["total_rooms"] or 0

#         # -------- per-day skeleton --------
#         results = {}
#         d = first_day
#         while d <= last_day:
#             ds = fmt(d)
#             results[ds] = {
#                 "date": ds,
#                 "booked_rooms": 0,
#                 "occupied": 0,
#                 "overdue": 0,
#                 "ooo_rooms": set(),
#                 "rooms_by_type": defaultdict(lambda: {
#                     "room_name": "", "room_type": "",
#                     "booked_quantity": 0, "occupied_quantity": 0,
#                     "rate": 0, "reservation_ids": []
#                 }),
#                 "reservations": [],
#                 "arrivals": {"booked_rooms": 0, "amount": 0, "reservations": []},
#                 "departures": {"booked_rooms": 0, "amount": 0, "reservations": []},
#                 "registered_rooms": {"total_rooms": 0, "total_amount": 0, "rooms": []},
#                 "confirmed": {"booked_rooms": 0, "amount": 0, "reservations": []},
#                 "cancelled": {"booked_rooms": 0, "amount": 0, "reservations": []},
#                 "stayovers": {"booked_rooms": 0, "amount": 0, "reservations": []},
#             }
#             d += timedelta(days=1)

#         # one row per reservation, same as the rooms API
#         stay_sq = """
#             SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
#             FROM hotel_tblguestreservation
#             WHERE is_active = 1
#             GROUP BY Reservation_ID
#         """

#         base_query = f"""
#             SELECT
#                 r.id AS reservation_id,
#                 r.Current_Status,
#                 st.s AS start_date,
#                 st.e AS end_date,
#                 r.outlet,
#                 fr.id AS fitrate_id,
#                 fr.quantity AS room_quantity,
#                 fr.rateID,
#                 rt.room_name,
#                 rt.room_type,
#                 rt.rate AS room_rate,
#                 rt.currency,
#                 mp.mp AS meal_plan,
#                 mp.rate AS meal_rate
#             FROM hotel_tblreservation r
#             INNER JOIN ({stay_sq}) st ON st.Reservation_ID = r.id
#             INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
#             INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
#             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
#             WHERE r.is_active = 1
#               AND fr.is_active = 1
#               AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out', 'Cancelled')
#               AND r.outlet = %s
#               AND st.s <= %s
#               AND (st.e >= %s OR r.Current_Status = 'Registered')
#             ORDER BY st.s
#         """
#         cursor.execute(base_query, [outlet, last_day, first_day])
#         reservations = cursor.fetchall()

#         for reservation in reservations:
#             start_date = to_date_obj(reservation['start_date'])
#             end_date = to_date_obj(reservation['end_date'])
#             status = reservation['Current_Status']

#             room_rate = float(reservation['room_rate'] or 0)
#             meal_rate = float(reservation['meal_rate'] or 0)
#             total_rate_per_room = room_rate + meal_rate
#             room_quantity = int(reservation['room_quantity'] or 1)
#             room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"
#             daily_amount = room_quantity * total_rate_per_room

#             reservation_detail = {
#                 "reservation_id": reservation['reservation_id'],
#                 "room_name": reservation['room_name'],
#                 "room_type": reservation['room_type'],
#                 "quantity": room_quantity,
#                 "rate_per_room": total_rate_per_room,
#                 "total_amount": daily_amount,
#                 "meal_plan": reservation['meal_plan'],
#                 "currency": reservation['currency'],
#                 "outlet": reservation['outlet'],
#                 "start_date": fmt(start_date),
#                 "end_date": fmt(end_date),
#                 "status": status
#             }

#             # ---------- OCCUPIED / OVERDUE (fitrate based; today is overridden below) ----------
#             if status in ('Reserved', 'Registered', 'Checked Out'):
#                 eff_end = end_date
#                 if status == 'Registered' and end_date < today:
#                     eff_end = today
#                 occ_from = max(start_date, first_day)
#                 occ_to = min(eff_end, last_day)
#                 dd = occ_from
#                 while dd <= occ_to:
#                     counts = (
#                         status == 'Registered'
#                         or (status == 'Checked Out' and dd < today)
#                         or (status == 'Reserved' and dd > today)
#                     )
#                     if counts:
#                         results[fmt(dd)]["occupied"] += room_quantity
#                         if status == 'Registered' and dd > end_date:
#                             results[fmt(dd)]["overdue"] += room_quantity
#                     dd += timedelta(days=1)

#             # ---------- arrival ----------
#             if first_day <= start_date <= last_day:
#                 ds = fmt(start_date)
#                 day = results[ds]
#                 day["booked_rooms"] += room_quantity

#                 rbt = day["rooms_by_type"][room_type_key]
#                 rbt["room_name"] = reservation['room_name']
#                 rbt["room_type"] = reservation['room_type']
#                 rbt["booked_quantity"] += room_quantity
#                 rbt["rate"] = total_rate_per_room
#                 if reservation['reservation_id'] not in rbt["reservation_ids"]:
#                     rbt["reservation_ids"].append(reservation['reservation_id'])

#                 day["reservations"].append(reservation_detail)

#                 if status in ('Reserved', 'Registered'):
#                     day["confirmed"]["booked_rooms"] += room_quantity
#                     day["confirmed"]["amount"] += daily_amount
#                     day["confirmed"]["reservations"].append(reservation_detail)
#                 if status == 'Cancelled':
#                     day["cancelled"]["booked_rooms"] += room_quantity
#                     day["cancelled"]["amount"] += daily_amount
#                     day["cancelled"]["reservations"].append(reservation_detail)
#                 if status in ('Registered', 'Checked Out'):
#                     day["arrivals"]["booked_rooms"] += room_quantity
#                     day["arrivals"]["amount"] += daily_amount
#                     day["arrivals"]["reservations"].append(reservation_detail)

#             # ---------- nights (multi-night stays, arrival day skipped) ----------
#             if start_date != end_date:
#                 cur = max(start_date, first_day)
#                 night_end = min(end_date - timedelta(days=1), last_day)
#                 while cur <= night_end:
#                     if cur != start_date:
#                         ds = fmt(cur)
#                         day = results[ds]
#                         day["booked_rooms"] += room_quantity

#                         rbt = day["rooms_by_type"][room_type_key]
#                         rbt["room_name"] = reservation['room_name']
#                         rbt["room_type"] = reservation['room_type']
#                         if status in ('Reserved', 'Registered'):
#                             rbt["booked_quantity"] += room_quantity
#                         rbt["rate"] = total_rate_per_room
#                         if reservation['reservation_id'] not in rbt["reservation_ids"]:
#                             rbt["reservation_ids"].append(reservation['reservation_id'])

#                         day["reservations"].append(reservation_detail)

#                         if status in ('Reserved', 'Registered'):
#                             day["confirmed"]["booked_rooms"] += room_quantity
#                             day["confirmed"]["amount"] += daily_amount
#                             day["confirmed"]["reservations"].append(reservation_detail)
#                         if status in ('Registered', 'Checked Out'):
#                             day["stayovers"]["booked_rooms"] += room_quantity
#                             day["stayovers"]["amount"] += daily_amount
#                             day["stayovers"]["reservations"].append(reservation_detail)
#                     cur += timedelta(days=1)

#             # ---------- departure ----------
#             dep_ds = fmt(end_date)
#             if dep_ds in results and status in ('Registered', 'Checked Out'):
#                 results[dep_ds]["departures"]["booked_rooms"] += room_quantity
#                 results[dep_ds]["departures"]["amount"] += daily_amount
#                 results[dep_ds]["departures"]["reservations"].append({
#                     **reservation_detail,
#                     "departure_status": status
#                 })

#         # -------- out-of-order blocks (same source as the rooms API) --------
#         cursor.execute("""
#             SELECT b.room_id, b.start_date, b.end_date
#             FROM hotel_tblroom_blocks b
#             JOIN hotel_tblrooms rm ON rm.id = b.room_id AND rm.is_active = 1
#             WHERE b.is_active = 1
#               AND b.released_at IS NULL
#               AND rm.outlet = %s
#               AND b.start_date <= %s
#               AND b.end_date >= %s
#         """, (outlet, last_day, first_day))
#         for b in cursor.fetchall():
#             bs = to_date_obj(b["start_date"])
#             be = to_date_obj(b["end_date"])
#             dd = max(bs, first_day)
#             while dd <= min(be, last_day):
#                 results[fmt(dd)]["ooo_rooms"].add(b["room_id"])
#                 dd += timedelta(days=1)

#         # -------- TODAY: physical-room occupancy and departures, same as the rooms API --------
#         today_override = None
#         if first_day <= today <= last_day:
#             cursor.execute(f"""
#                 SELECT rd.room_id, st.s AS start_date, st.e AS end_date
#                 FROM hotel_tblreservation_details rd
#                 JOIN hotel_tblreservation res
#                     ON rd.Reservation_ID = res.id AND res.is_active = 1
#                 JOIN ({stay_sq}) st ON st.Reservation_ID = res.id
#                 JOIN hotel_tblrooms rm
#                     ON rm.id = rd.room_id AND rm.is_active = 1 AND rm.outlet = %s
#                 WHERE rd.is_active = 1
#                   AND rd.is_current = 1
#                   AND res.Current_Status = 'Registered'
#                   AND st.s <= %s
#             """, (outlet, today))

#             # same state rule and priority as the rooms API
#             PRIORITY = {"Overdue": 3, "Check-In": 2, "Departing Today": 1}
#             state_by_room = {}
#             for row in cursor.fetchall():
#                 s = to_date_obj(row["start_date"])
#                 e = to_date_obj(row["end_date"])
#                 if e < today:
#                     state = "Overdue"
#                 elif e > today or s == e:
#                     state = "Check-In"
#                 else:
#                     state = "Departing Today"
#                 rid = row["room_id"]
#                 if PRIORITY[state] > PRIORITY.get(state_by_room.get(rid), 0):
#                     state_by_room[rid] = state

#             ooo_today = results[fmt(today)]["ooo_rooms"]

#             # occupied/overdue skip out-of-order rooms (as housekeeping_counts does)
#             occupied_ids = {r for r in state_by_room if r not in ooo_today}
#             overdue_ids = {r for r in occupied_ids if state_by_room[r] == "Overdue"}
#             # departing matches the room list's departing_today flag
#             departing_ids = {r for r, st_ in state_by_room.items() if st_ == "Departing Today"}

#             today_override = {
#                 "occupied": len(occupied_ids),
#                 "overdue": len(overdue_ids),
#                 "departures": len(departing_ids),
#             }

#         # -------- registered rooms (room-level detail only) --------
#         registered_rooms_query = f"""
#             SELECT DISTINCT
#                 rd.id AS detail_id,
#                 rd.Reservation_ID,
#                 rd.room_id,
#                 rd.is_current,
#                 r.id AS reservation_id,
#                 r.Current_Status,
#                 st.s AS start_date,
#                 st.e AS end_date,
#                 rm.id AS room_id,
#                 rm.outlet AS room_outlet,
#                 rm.room_no,
#                 rm.room_state,
#                 rm.phone_no,
#                 rm.preference,
#                 rm.room_view,
#                 rm.room_type,
#                 rm.room_notes,
#                 rt.room_name,
#                 rt.rate AS room_rate,
#                 mp.mp AS meal_plan,
#                 mp.rate AS meal_rate
#             FROM hotel_tblreservation_details rd
#             INNER JOIN hotel_tblreservation r ON rd.Reservation_ID = r.id
#             INNER JOIN ({stay_sq}) st ON st.Reservation_ID = r.id
#             INNER JOIN hotel_tblrooms rm ON rd.room_id = rm.id
#             LEFT JOIN hotel_tblfitrate fr ON r.id = fr.reservationID AND fr.is_active = 1
#             LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
#             LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id AND mp.is_active = 1
#             WHERE r.is_active = 1
#               AND rd.is_active = 1
#               AND r.Current_Status = 'Registered'
#               AND rd.is_current = 1
#               AND r.outlet = %s
#               AND st.s <= %s
#               AND (st.e >= %s OR r.Current_Status = 'Registered')
#         """
#         cursor.execute(registered_rooms_query, [outlet, last_day, first_day])

#         for room in cursor.fetchall():
#             start_date = to_date_obj(room['start_date'])
#             end_date = to_date_obj(room['end_date'])
#             list_end = max(end_date, today) if end_date < today else end_date
#             total_rate_per_room = float(room['room_rate'] or 0) + float(room['meal_rate'] or 0)

#             cur = max(start_date, first_day)
#             stop = min(list_end, last_day)
#             while cur <= stop:
#                 day = results[fmt(cur)]
#                 day["registered_rooms"]["total_amount"] += total_rate_per_room
#                 day["registered_rooms"]["rooms"].append({
#                     "reservation_id": room['reservation_id'],
#                     "room_id": room['room_id'],
#                     "room_no": room['room_no'],
#                     "room_type": room['room_type'],
#                     "room_name": room['room_name'],
#                     "room_state": room['room_state'],
#                     "preference": room['preference'],
#                     "room_view": room['room_view'],
#                     "phone_no": room['phone_no'],
#                     "room_notes": room['room_notes'],
#                     "rate": total_rate_per_room,
#                     "meal_plan": room['meal_plan'],
#                     "start_date": fmt(start_date),
#                     "end_date": fmt(end_date)
#                 })
#                 cur += timedelta(days=1)

#         # -------- response --------
#         today_str = fmt(today)
#         daily_stats = []
#         for ds, day in results.items():
#             unique_rooms = []
#             seen = set()
#             for r in day["registered_rooms"]["rooms"]:
#                 if r["room_id"] not in seen:
#                     seen.add(r["room_id"])
#                     unique_rooms.append(r)

#             occupied = day["occupied"]
#             overdue = day["overdue"]
#             departures = day["departures"]["booked_rooms"]
#             out_of_order = len(day["ooo_rooms"])

#             if ds == today_str and today_override is not None:
#                 occupied = today_override["occupied"]
#                 overdue = today_override["overdue"]
#                 departures = today_override["departures"]

#             vacant = max(hotel_total_rooms - occupied - out_of_order, 0)

#             # daily_stats.append({
#             #     "date": ds,
#             #     "hotel_capacity": hotel_total_rooms,
#             #     "booked_rooms": day["booked_rooms"],
#             #     "occupied_rooms": occupied,
#             #     "overdue_rooms": overdue,
#             #     "out_of_order": out_of_order,
#             #     "vacant_rooms": vacant,
#             #     "occupancy_rate": round(occupied / hotel_total_rooms * 100, 2) if hotel_total_rooms > 0 else 0,
#             #     "reservations_count": len(day["reservations"]),
#             #     "arrivals": day["arrivals"]["booked_rooms"],
#             #     "stayovers": day["stayovers"]["booked_rooms"],
#             #     "departures": departures,
#             #     "confirmed": day["confirmed"]["booked_rooms"],
#             #     "cancelled": day["cancelled"]["booked_rooms"],
#             #     "registered_rooms": unique_rooms
#             # })

#             # out-of-order rooms can't be sold, so they come out of the denominator.
#             # vacant and occupancy_rate now use the same base.
#             sellable_rooms = max(hotel_total_rooms - out_of_order, 0)
#             vacant = max(sellable_rooms - occupied, 0)
#             occupancy_rate = (
#                 round(occupied / sellable_rooms * 100, 2) if sellable_rooms > 0 else 0
#             )

#             daily_stats.append({
#                 "date": ds,
#                 "hotel_capacity": hotel_total_rooms,
#                 "sellable_rooms": sellable_rooms,
#                 "booked_rooms": day["booked_rooms"],
#                 "occupied_rooms": occupied,
#                 "overdue_rooms": overdue,
#                 "out_of_order": out_of_order,
#                 "vacant_rooms": vacant,
#                 "occupancy_rate": occupancy_rate,
#                 "reservations_count": len(day["reservations"]),
#                 "arrivals": day["arrivals"]["booked_rooms"],
#                 "stayovers": day["stayovers"]["booked_rooms"],
#                 "departures": departures,
#                 "confirmed": day["confirmed"]["booked_rooms"],
#                 "cancelled": day["cancelled"]["booked_rooms"],
#                 "registered_rooms": unique_rooms
#             })

#         mydb.close()

#         return jsonify({
#             "success": True,
#             "data": {
#                 "daily": daily_stats,
#                 "filters": {"from_date": from_date, "to_date": to_date, "outlet": outlet}
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


from datetime import date
from collections import defaultdict
@app_file415.route("/analytics/rooms-confirmed", methods=["GET"])
@cross_origin()
def get_rooms_confirmed_stats():
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
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token:
            return {"error": "No token provided."}, 400
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        outlet = request.args.get('outlet', default=None, type=str)

        if not outlet:
            return {"error": "outlet is required."}, 400
        if not from_date or not to_date:
            return {"error": "Both from_date and to_date are required (format: YYYY-MM-DD)"}, 400

        try:
            first_day = datetime.strptime(from_date, '%Y-%m-%d').date()
            last_day = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        today = date.today()

        def to_date_obj(v):
            return datetime.strptime(v, '%Y-%m-%d').date() if isinstance(v, str) else v

        def fmt(d):
            return d.strftime('%Y-%m-%d')

        # -------- capacity (active rooms for the outlet) --------
        cursor.execute("""
            SELECT COUNT(*) AS total_rooms
            FROM hotel_tblrooms
            WHERE is_active = 1 AND outlet = %s
        """, (outlet,))
        hotel_total_rooms = cursor.fetchone()["total_rooms"] or 0

        # -------- per-day skeleton --------
        results = {}
        d = first_day
        while d <= last_day:
            ds = fmt(d)
            results[ds] = {
                "date": ds,
                "booked_rooms": 0,
                "occupied": 0,
                "complimentary": 0,             # <-- new: occupied rooms that are complimentary
                "complimentary_confirmed": 0,   # <-- new: Reserved + Registered complimentary rooms
                "overdue": 0,
                "ooo_rooms": set(),
                "rooms_by_type": defaultdict(lambda: {
                    "room_name": "", "room_type": "",
                    "booked_quantity": 0, "occupied_quantity": 0,
                    "rate": 0, "reservation_ids": []
                }),
                "reservations": [],
                "arrivals": {"booked_rooms": 0, "amount": 0, "reservations": []},
                "departures": {"booked_rooms": 0, "amount": 0, "reservations": []},
                "registered_rooms": {"total_rooms": 0, "total_amount": 0, "rooms": []},
                "confirmed": {"booked_rooms": 0, "amount": 0, "reservations": []},
                "cancelled": {"booked_rooms": 0, "amount": 0, "reservations": []},
                "stayovers": {"booked_rooms": 0, "amount": 0, "reservations": []},
            }
            d += timedelta(days=1)

        # one row per reservation, same as the rooms API
        stay_sq = """
            SELECT Reservation_ID, MIN(start_date) AS s, MAX(end_date) AS e
            FROM hotel_tblguestreservation
            WHERE is_active = 1
            GROUP BY Reservation_ID
        """

        base_query = f"""
            SELECT
                r.id AS reservation_id,
                r.Current_Status,
                r.is_complimentary,
                st.s AS start_date,
                st.e AS end_date,
                r.outlet,
                fr.id AS fitrate_id,
                fr.quantity AS room_quantity,
                fr.rateID,
                rt.room_name,
                rt.room_type,
                rt.rate AS room_rate,
                rt.currency,
                mp.mp AS meal_plan,
                mp.rate AS meal_rate
            FROM hotel_tblreservation r
            INNER JOIN ({stay_sq}) st ON st.Reservation_ID = r.id
            INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
            INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
            LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
            WHERE r.is_active = 1
              AND fr.is_active = 1
              AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out', 'Cancelled')
              AND r.outlet = %s
              AND st.s <= %s
              AND (st.e >= %s OR r.Current_Status = 'Registered')
            ORDER BY st.s
        """
        cursor.execute(base_query, [outlet, last_day, first_day])
        reservations = cursor.fetchall()

        for reservation in reservations:
            start_date = to_date_obj(reservation['start_date'])
            end_date = to_date_obj(reservation['end_date'])
            status = reservation['Current_Status']
            is_comp = bool(reservation['is_complimentary'])   # <-- new

            room_rate = float(reservation['room_rate'] or 0)
            meal_rate = float(reservation['meal_rate'] or 0)
            total_rate_per_room = room_rate + meal_rate
            room_quantity = int(reservation['room_quantity'] or 1)
            room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"
            daily_amount = room_quantity * total_rate_per_room

            reservation_detail = {
                "reservation_id": reservation['reservation_id'],
                "room_name": reservation['room_name'],
                "room_type": reservation['room_type'],
                "quantity": room_quantity,
                "rate_per_room": total_rate_per_room,
                "total_amount": daily_amount,
                "meal_plan": reservation['meal_plan'],
                "currency": reservation['currency'],
                "outlet": reservation['outlet'],
                "start_date": fmt(start_date),
                "end_date": fmt(end_date),
                "status": status
            }

            # ---------- OCCUPIED / OVERDUE (fitrate based; today is overridden below) ----------
            if status in ('Reserved', 'Registered', 'Checked Out'):
                eff_end = end_date
                if status == 'Registered' and end_date < today:
                    eff_end = today
                occ_from = max(start_date, first_day)
                occ_to = min(eff_end, last_day)
                dd = occ_from
                while dd <= occ_to:
                    counts = (
                        status == 'Registered'
                        or (status == 'Checked Out' and dd < today)
                        or (status == 'Reserved' and dd > today)
                    )
                    if counts:
                        results[fmt(dd)]["occupied"] += room_quantity
                        if is_comp:                                              # <-- new
                            results[fmt(dd)]["complimentary"] += room_quantity   # <-- new
                        if status == 'Registered' and dd > end_date:
                            results[fmt(dd)]["overdue"] += room_quantity
                    dd += timedelta(days=1)

            # ---------- arrival ----------
            if first_day <= start_date <= last_day:
                ds = fmt(start_date)
                day = results[ds]
                day["booked_rooms"] += room_quantity

                rbt = day["rooms_by_type"][room_type_key]
                rbt["room_name"] = reservation['room_name']
                rbt["room_type"] = reservation['room_type']
                rbt["booked_quantity"] += room_quantity
                rbt["rate"] = total_rate_per_room
                if reservation['reservation_id'] not in rbt["reservation_ids"]:
                    rbt["reservation_ids"].append(reservation['reservation_id'])

                day["reservations"].append(reservation_detail)

                if status in ('Reserved', 'Registered'):
                    day["confirmed"]["booked_rooms"] += room_quantity
                    day["confirmed"]["amount"] += daily_amount
                    day["confirmed"]["reservations"].append(reservation_detail)
                    if is_comp:                                                  # <-- new
                        day["complimentary_confirmed"] += room_quantity          # <-- new
                if status == 'Cancelled':
                    day["cancelled"]["booked_rooms"] += room_quantity
                    day["cancelled"]["amount"] += daily_amount
                    day["cancelled"]["reservations"].append(reservation_detail)
                if status in ('Registered', 'Checked Out'):
                    day["arrivals"]["booked_rooms"] += room_quantity
                    day["arrivals"]["amount"] += daily_amount
                    day["arrivals"]["reservations"].append(reservation_detail)

            # ---------- nights (multi-night stays, arrival day skipped) ----------
            if start_date != end_date:
                cur = max(start_date, first_day)
                night_end = min(end_date - timedelta(days=1), last_day)
                while cur <= night_end:
                    if cur != start_date:
                        ds = fmt(cur)
                        day = results[ds]
                        day["booked_rooms"] += room_quantity

                        rbt = day["rooms_by_type"][room_type_key]
                        rbt["room_name"] = reservation['room_name']
                        rbt["room_type"] = reservation['room_type']
                        if status in ('Reserved', 'Registered'):
                            rbt["booked_quantity"] += room_quantity
                        rbt["rate"] = total_rate_per_room
                        if reservation['reservation_id'] not in rbt["reservation_ids"]:
                            rbt["reservation_ids"].append(reservation['reservation_id'])

                        day["reservations"].append(reservation_detail)

                        if status in ('Reserved', 'Registered'):
                            day["confirmed"]["booked_rooms"] += room_quantity
                            day["confirmed"]["amount"] += daily_amount
                            day["confirmed"]["reservations"].append(reservation_detail)
                            if is_comp:                                          # <-- new
                                day["complimentary_confirmed"] += room_quantity  # <-- new
                        if status in ('Registered', 'Checked Out'):
                            day["stayovers"]["booked_rooms"] += room_quantity
                            day["stayovers"]["amount"] += daily_amount
                            day["stayovers"]["reservations"].append(reservation_detail)
                    cur += timedelta(days=1)

            # ---------- departure ----------
            dep_ds = fmt(end_date)
            if dep_ds in results and status in ('Registered', 'Checked Out'):
                results[dep_ds]["departures"]["booked_rooms"] += room_quantity
                results[dep_ds]["departures"]["amount"] += daily_amount
                results[dep_ds]["departures"]["reservations"].append({
                    **reservation_detail,
                    "departure_status": status
                })

        # -------- out-of-order blocks (same source as the rooms API) --------
        cursor.execute("""
            SELECT b.room_id, b.start_date, b.end_date
            FROM hotel_tblroom_blocks b
            JOIN hotel_tblrooms rm ON rm.id = b.room_id AND rm.is_active = 1
            WHERE b.is_active = 1
              AND b.released_at IS NULL
              AND rm.outlet = %s
              AND b.start_date <= %s
              AND b.end_date >= %s
        """, (outlet, last_day, first_day))
        for b in cursor.fetchall():
            bs = to_date_obj(b["start_date"])
            be = to_date_obj(b["end_date"])
            dd = max(bs, first_day)
            while dd <= min(be, last_day):
                results[fmt(dd)]["ooo_rooms"].add(b["room_id"])
                dd += timedelta(days=1)

        # -------- TODAY: physical-room occupancy and departures, same as the rooms API --------
        today_override = None
        if first_day <= today <= last_day:
            cursor.execute(f"""
                SELECT rd.room_id, st.s AS start_date, st.e AS end_date,
                       res.is_complimentary AS is_complimentary
                FROM hotel_tblreservation_details rd
                JOIN hotel_tblreservation res
                    ON rd.Reservation_ID = res.id AND res.is_active = 1
                JOIN ({stay_sq}) st ON st.Reservation_ID = res.id
                JOIN hotel_tblrooms rm
                    ON rm.id = rd.room_id AND rm.is_active = 1 AND rm.outlet = %s
                WHERE rd.is_active = 1
                  AND rd.is_current = 1
                  AND res.Current_Status = 'Registered'
                  AND st.s <= %s
            """, (outlet, today))

            # same state rule and priority as the rooms API
            PRIORITY = {"Overdue": 3, "Check-In": 2, "Departing Today": 1}
            state_by_room = {}
            comp_by_room = {}   # <-- new: room -> is the reservation in it complimentary
            for row in cursor.fetchall():
                s = to_date_obj(row["start_date"])
                e = to_date_obj(row["end_date"])
                if e < today:
                    state = "Overdue"
                elif e > today or s == e:
                    state = "Check-In"
                else:
                    state = "Departing Today"
                rid = row["room_id"]
                if PRIORITY[state] > PRIORITY.get(state_by_room.get(rid), 0):
                    state_by_room[rid] = state
                    comp_by_room[rid] = bool(row["is_complimentary"])   # <-- new

            ooo_today = results[fmt(today)]["ooo_rooms"]

            # occupied/overdue skip out-of-order rooms (as housekeeping_counts does)
            occupied_ids = {r for r in state_by_room if r not in ooo_today}
            overdue_ids = {r for r in occupied_ids if state_by_room[r] == "Overdue"}
            # departing matches the room list's departing_today flag
            departing_ids = {r for r, st_ in state_by_room.items() if st_ == "Departing Today"}
            # complimentary rooms among the occupied ones (distinct physical rooms)
            complimentary_ids = {r for r in occupied_ids if comp_by_room.get(r)}   # <-- new

            today_override = {
                "occupied": len(occupied_ids),
                "complimentary": len(complimentary_ids),   # <-- new
                "overdue": len(overdue_ids),
                "departures": len(departing_ids),
            }

        # -------- registered rooms (room-level detail only) --------
        registered_rooms_query = f"""
            SELECT DISTINCT
                rd.id AS detail_id,
                rd.Reservation_ID,
                rd.room_id,
                rd.is_current,
                r.id AS reservation_id,
                r.Current_Status,
                st.s AS start_date,
                st.e AS end_date,
                rm.id AS room_id,
                rm.outlet AS room_outlet,
                rm.room_no,
                rm.room_state,
                rm.phone_no,
                rm.preference,
                rm.room_view,
                rm.room_type,
                rm.room_notes,
                rt.room_name,
                rt.rate AS room_rate,
                mp.mp AS meal_plan,
                mp.rate AS meal_rate
            FROM hotel_tblreservation_details rd
            INNER JOIN hotel_tblreservation r ON rd.Reservation_ID = r.id
            INNER JOIN ({stay_sq}) st ON st.Reservation_ID = r.id
            INNER JOIN hotel_tblrooms rm ON rd.room_id = rm.id
            LEFT JOIN hotel_tblfitrate fr ON r.id = fr.reservationID AND fr.is_active = 1
            LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
            LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id AND mp.is_active = 1
            WHERE r.is_active = 1
              AND rd.is_active = 1
              AND r.Current_Status = 'Registered'
              AND rd.is_current = 1
              AND r.outlet = %s
              AND st.s <= %s
              AND (st.e >= %s OR r.Current_Status = 'Registered')
        """
        cursor.execute(registered_rooms_query, [outlet, last_day, first_day])

        for room in cursor.fetchall():
            start_date = to_date_obj(room['start_date'])
            end_date = to_date_obj(room['end_date'])
            list_end = max(end_date, today) if end_date < today else end_date
            total_rate_per_room = float(room['room_rate'] or 0) + float(room['meal_rate'] or 0)

            cur = max(start_date, first_day)
            stop = min(list_end, last_day)
            while cur <= stop:
                day = results[fmt(cur)]
                day["registered_rooms"]["total_amount"] += total_rate_per_room
                day["registered_rooms"]["rooms"].append({
                    "reservation_id": room['reservation_id'],
                    "room_id": room['room_id'],
                    "room_no": room['room_no'],
                    "room_type": room['room_type'],
                    "room_name": room['room_name'],
                    "room_state": room['room_state'],
                    "preference": room['preference'],
                    "room_view": room['room_view'],
                    "phone_no": room['phone_no'],
                    "room_notes": room['room_notes'],
                    "rate": total_rate_per_room,
                    "meal_plan": room['meal_plan'],
                    "start_date": fmt(start_date),
                    "end_date": fmt(end_date)
                })
                cur += timedelta(days=1)

        # -------- response --------
        today_str = fmt(today)
        daily_stats = []
        for ds, day in results.items():
            unique_rooms = []
            seen = set()
            for r in day["registered_rooms"]["rooms"]:
                if r["room_id"] not in seen:
                    seen.add(r["room_id"])
                    unique_rooms.append(r)

            occupied = day["occupied"]
            complimentary = day["complimentary"]   # <-- new
            overdue = day["overdue"]
            departures = day["departures"]["booked_rooms"]
            out_of_order = len(day["ooo_rooms"])

            if ds == today_str and today_override is not None:
                occupied = today_override["occupied"]
                complimentary = today_override["complimentary"]   # <-- new
                overdue = today_override["overdue"]
                departures = today_override["departures"]

            # out-of-order rooms can't be sold, so they come out of the denominator.
            # vacant and occupancy_rate now use the same base.
            sellable_rooms = max(hotel_total_rooms - out_of_order, 0)
            vacant = max(sellable_rooms - occupied, 0)
            occupancy_rate = (
                round(occupied / sellable_rooms * 100, 2) if sellable_rooms > 0 else 0
            )

            # complimentary is part of occupied, so paying = occupied - complimentary
            paying = max(occupied - complimentary, 0)   # <-- new

            daily_stats.append({
                "date": ds,
                "hotel_capacity": hotel_total_rooms,
                "sellable_rooms": sellable_rooms,
                "booked_rooms": day["booked_rooms"],
                "occupied_rooms": occupied,
                "complimentary_rooms": complimentary,                              # <-- new
                "paying_rooms": paying,                                            # <-- new
                "complimentary_confirmed_rooms": day["complimentary_confirmed"],   # <-- new
                "overdue_rooms": overdue,
                "out_of_order": out_of_order,
                "vacant_rooms": vacant,
                "occupancy_rate": occupancy_rate,
                "reservations_count": len(day["reservations"]),
                "arrivals": day["arrivals"]["booked_rooms"],
                "stayovers": day["stayovers"]["booked_rooms"],
                "departures": departures,
                "confirmed": day["confirmed"]["booked_rooms"],
                "cancelled": day["cancelled"]["booked_rooms"],
                "registered_rooms": unique_rooms
            })

        mydb.close()

        return jsonify({
            "success": True,
            "data": {
                "daily": daily_stats,
                "filters": {"from_date": from_date, "to_date": to_date, "outlet": outlet}
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app_file415.route("/analytics/rooms-details", methods=["GET"])
@cross_origin()
def get_rooms_details():
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
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token:
            return {"error": "No token provided."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get date from query parameters
        date_param = request.args.get('date')
        outlet = request.args.get('outlet', default=None, type=str)
        filter_type = request.args.get('filter', default=None, type=str)

        # Outlet is now required
        if not outlet:
            return {"error": "outlet is required."}, 400

        # Validate date
        if not date_param:
            return {"error": "Date is required (format: YYYY-MM-DD)"}, 400

        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

        # Validate filter if provided
        valid_filters = ['arrival', 'stayover', 'departure', 'cancelled', 'booked']
        if filter_type and filter_type not in valid_filters:
            return {"error": f"Invalid filter. Must be one of: {', '.join(valid_filters)}"}, 400

        # Get total hotel rooms count (scoped to outlet)
        total_rooms_query = """
            SELECT COUNT(*) as total_rooms
            FROM hotel_tblrooms
            WHERE is_active = 1
            AND outlet = %s
        """
        total_rooms_params = [outlet]

        cursor.execute(total_rooms_query, total_rooms_params)
        hotel_total_rooms = cursor.fetchone()['total_rooms'] or 0

        # Initialize response data
        response_data = {
            "date": target_date.strftime('%Y-%m-%d'),
            "hotel_capacity": hotel_total_rooms,
            "filters": {
                "date": target_date.strftime('%Y-%m-%d'),
                "outlet": outlet,
                "filter": filter_type
            }
        }

        # Get registered rooms with their FIT rates (scoped to outlet)
        registered_query = """
            SELECT DISTINCT
                rd.id AS detail_id,
                rd.Reservation_ID as reservation_id,
                rd.room_id,
                r.Current_Status,
                gr.No_of_children,
                gr.No_of_adults,
                gr.Guest_Notes,
                gr.start_date,
                gr.end_date,
                rm.id AS room_id,
                rm.outlet AS room_outlet,
                rm.room_no,
                rm.room_state,
                rm.phone_no,
                rm.preference,
                rm.room_view,
                rm.room_type,
                rm.room_notes,
                c.name,
                c.email,
                c.phone
            FROM hotel_tblreservation_details rd
            INNER JOIN hotel_tblreservation r ON rd.Reservation_ID = r.id
            INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
            INNER JOIN hotel_tblrooms rm ON rd.room_id = rm.id
            LEFT JOIN customers c ON r.Guest_ID = c.id
            WHERE r.is_active = 1 
            AND gr.is_active = 1
            AND rd.is_active = 1
            AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
            AND rd.is_current = 1
            AND gr.start_date <= %s
            AND gr.end_date >= %s
            AND r.outlet = %s
        """

        registered_params = [target_date, target_date, outlet]

        cursor.execute(registered_query, registered_params)
        registered_rooms = cursor.fetchall()

        # Get all reservation IDs
        reservation_ids = [room['reservation_id'] for room in registered_rooms]

        # Second query: Get FIT rates for these reservations
        fit_rates_by_reservation = {}
        if reservation_ids:
            fit_rates_query = """
                SELECT 
                    fr.reservationID,
                    rt.room_name,
                    rt.rate AS room_rate,
                    mp.mp AS meal_plan,
                    mp.rate AS meal_rate,
                    fr.quantity
                FROM hotel_tblfitrate fr
                LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id AND rt.is_active = 1
                LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id AND mp.is_active = 1
                WHERE fr.is_active = 1
                AND fr.reservationID IN ({})
            """.format(','.join(['%s'] * len(reservation_ids)))

            cursor.execute(fit_rates_query, reservation_ids)
            fit_rates = cursor.fetchall()

            # Group fit rates by reservation_id
            for rate in fit_rates:
                rid = rate['reservationID']
                if rid not in fit_rates_by_reservation:
                    fit_rates_by_reservation[rid] = []
                fit_rates_by_reservation[rid].append({
                    "room_name": rate['room_name'],
                    "room_rate": float(rate['room_rate']) if rate['room_rate'] else 0,
                    "meal_plan": rate['meal_plan'],
                    "meal_rate": float(rate['meal_rate']) if rate['meal_rate'] else 0,
                    "quantity": rate['quantity']
                })

        # Process registered rooms into arrivals, stayovers, departures
        arrivals_list = []
        stayover_list = []
        departures_list = []

        for room in registered_rooms:
            start_date = room['start_date']
            end_date = room['end_date']

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Check if it's a same-day stay
            is_single_night = start_date == end_date

            # Get fit rates for this reservation
            room_fit_rates = fit_rates_by_reservation.get(room['reservation_id'], [])

            # Calculate total rate
            total_rate = 0
            for fr in room_fit_rates:
                total_rate += (fr['room_rate'] + fr['meal_rate']) * fr['quantity']

            # Get unique meal plans and room names
            meal_plans = list(set([fr['meal_plan'] for fr in room_fit_rates if fr.get('meal_plan')]))
            meal_plan = ', '.join(meal_plans) if meal_plans else None

            room_names = list(set([fr['room_name'] for fr in room_fit_rates if fr.get('room_name')]))
            room_name = ', '.join(room_names) if room_names else room['room_type']

            room_detail = {
                "reservation_id": room['reservation_id'],
                "detail_id": room['detail_id'],
                "room_id": room['room_id'],
                "room_no": room['room_no'],
                "room_type": room['room_type'],
                "room_name": room_name,
                "room_state": room['room_state'],
                "preference": room['preference'],
                "room_view": room['room_view'],
                "phone_no": room['phone_no'],
                "room_notes": room['room_notes'],
                "rate": total_rate,
                "meal_plan": meal_plan,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "guest": {
                    "name": room['name'],
                    "email": room['email'],
                    "phone": room['phone']
                },
                "no_of_adults": room['No_of_adults'],
                "no_of_children": room['No_of_children'],
                "guest_notes": room['Guest_Notes'],
                "fit_rates": room_fit_rates
            }

            # Determine if it's arrival, stayover, or departure
            is_arrival = start_date == target_date
            is_departure = end_date == target_date
            is_stayover = start_date < target_date < end_date

            # For same-day stay, both arrival and departure are true
            if is_arrival:
                arrivals_list.append(room_detail)
            if is_departure:
                departures_list.append(room_detail)
            if is_stayover:
                stayover_list.append(room_detail)

        # Add to response based on filter
        if not filter_type or filter_type == 'arrival':
            response_data["arrivals"] = {
                "count": len(arrivals_list),
                "rooms": arrivals_list
            }

        if not filter_type or filter_type == 'stayover':
            response_data["stayover_rooms"] = {
                "count": len(stayover_list),
                "rooms": stayover_list
            }

        if not filter_type or filter_type == 'departure':
            response_data["departures"] = {
                "count": len(departures_list),
                "rooms": departures_list
            }

        # 2. GET BOOKED ROOMS (from fitrate - all confirmed reservations for this date) (scoped to outlet)
        booked_query = """
            SELECT 
                r.id AS reservation_id,
                r.Current_Status,
                gr.No_of_children,
                gr.No_of_adults,
                gr.Guest_Notes,
                gr.start_date,
                gr.end_date,
                r.outlet,
                fr.id AS fitrate_id,
                fr.quantity AS room_quantity,
                fr.rateID,
                rt.room_name,
                rt.room_type,
                rt.rate AS room_rate,
                rt.currency,
                mp.mp AS meal_plan,
                mp.rate AS meal_rate,
                c.name,
                c.email,
                c.phone
            FROM hotel_tblreservation r
            INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
            INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
            INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
            LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
            LEFT JOIN customers c ON r.Guest_ID = c.id
            WHERE r.is_active = 1 
            AND gr.is_active = 1
            AND fr.is_active = 1
            AND r.Current_Status IN ('Reserved', 'Registered', 'Checked Out')
            AND gr.start_date <= %s
            AND gr.end_date > %s
            AND r.outlet = %s
        """

        booked_params = [target_date, target_date, outlet]

        cursor.execute(booked_query, booked_params)
        booked_reservations = cursor.fetchall()

        # Process booked reservations
        booked_rooms_by_type = defaultdict(lambda: {
            "room_name": "",
            "room_type": "",
            "quantity": 0,
            "rate": 0,
            "total_amount": 0,
            "reservations": []
        })

        for reservation in booked_reservations:
            start_date = reservation['start_date']
            end_date = reservation['end_date']
            status = reservation['Current_Status']

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            room_rate = float(reservation['room_rate'] or 0)
            meal_rate = float(reservation['meal_rate'] or 0)
            total_rate = room_rate + meal_rate
            room_quantity = int(reservation['room_quantity'] or 1)
            daily_amount = room_quantity * total_rate

            room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"

            # Group by room type for booked rooms
            booked_rooms_by_type[room_type_key]["room_name"] = reservation['room_name']
            booked_rooms_by_type[room_type_key]["room_type"] = reservation['room_type']
            booked_rooms_by_type[room_type_key]["quantity"] += room_quantity
            booked_rooms_by_type[room_type_key]["rate"] = total_rate
            booked_rooms_by_type[room_type_key]["total_amount"] += daily_amount
            booked_rooms_by_type[room_type_key]["reservations"].append({
                "reservation_id": reservation['reservation_id'],
                "status": status,
                "no_of_adults": reservation['No_of_adults'],
                "no_of_children": reservation['No_of_children'],
                "guest_notes": reservation['Guest_Notes'],
                "quantity": room_quantity,
                "rate_per_room": total_rate,
                "total_amount": daily_amount,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "meal_plan": reservation['meal_plan'],
                "currency": reservation['currency'],
                "guest": {
                    "name": reservation['name'],
                    "email": reservation['email'],
                    "phone": reservation['phone']
                }
            })

        # Add booked rooms to response if no filter or filter is 'booked'
        if not filter_type or filter_type == 'booked':
            response_data["booked_rooms"] = {
                "count": sum(room["quantity"] for room in booked_rooms_by_type.values()),
                "by_type": list(booked_rooms_by_type.values())
            }

        # 3. GET CANCELLED ROOMS for this date (scoped to outlet)
        cancelled_query = """
            SELECT 
                r.id AS reservation_id,
                r.Current_Status,
                gr.No_of_children,
                gr.No_of_adults,
                gr.Guest_Notes,
                gr.start_date,
                gr.end_date,
                r.outlet,
                fr.id AS fitrate_id,
                fr.quantity AS room_quantity,
                fr.rateID,
                rt.room_name,
                rt.room_type,
                rt.rate AS room_rate,
                rt.currency,
                mp.mp AS meal_plan,
                mp.rate AS meal_rate,
                c.name,
                c.email,
                c.phone
            FROM hotel_tblreservation r
            INNER JOIN hotel_tblguestreservation gr ON r.id = gr.Reservation_ID
            INNER JOIN hotel_tblfitrate fr ON r.id = fr.reservationID
            INNER JOIN hotel_tblrates rt ON fr.rateID = rt.id
            LEFT JOIN hotel_tblmeal_price mp ON rt.meal_price_id = mp.id
            LEFT JOIN customers c ON r.Guest_ID = c.id
            WHERE r.is_active = 1 
            AND gr.is_active = 1
            AND fr.is_active = 1
            AND r.Current_Status = 'Cancelled'
            AND gr.start_date <= %s
            AND gr.end_date >= %s
            AND r.outlet = %s
        """

        cancelled_params = [target_date, target_date, outlet]

        cursor.execute(cancelled_query, cancelled_params)
        cancelled_reservations = cursor.fetchall()

        # Process cancelled reservations
        cancelled_rooms_by_type = defaultdict(lambda: {
            "room_name": "",
            "room_type": "",
            "quantity": 0,
            "rate": 0,
            "total_amount": 0,
            "reservations": []
        })

        cancelled_arrivals_list = []
        cancelled_departures_list = []

        for reservation in cancelled_reservations:
            start_date = reservation['start_date']
            end_date = reservation['end_date']
            status = reservation['Current_Status']

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            room_rate = float(reservation['room_rate'] or 0)
            meal_rate = float(reservation['meal_rate'] or 0)
            total_rate = room_rate + meal_rate
            room_quantity = int(reservation['room_quantity'] or 1)
            daily_amount = room_quantity * total_rate

            room_type_key = f"{reservation['room_name']}_{reservation['room_type']}"

            # Group by room type for cancelled rooms
            cancelled_rooms_by_type[room_type_key]["room_name"] = reservation['room_name']
            cancelled_rooms_by_type[room_type_key]["room_type"] = reservation['room_type']
            cancelled_rooms_by_type[room_type_key]["quantity"] += room_quantity
            cancelled_rooms_by_type[room_type_key]["rate"] = total_rate
            cancelled_rooms_by_type[room_type_key]["total_amount"] += daily_amount

            reservation_detail = {
                "reservation_id": reservation['reservation_id'],
                "status": status,
                "quantity": room_quantity,
                "rate_per_room": total_rate,
                "total_amount": daily_amount,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "meal_plan": reservation['meal_plan'],
                "currency": reservation['currency'],
                "guest": {
                    "name": reservation['name'],
                    "email": reservation['email'],
                    "phone": reservation['phone']
                },
                "no_of_adults": reservation['No_of_adults'],
                "no_of_children": reservation['No_of_children'],
                "guest_notes": reservation['Guest_Notes']
            }

            cancelled_rooms_by_type[room_type_key]["reservations"].append(reservation_detail)

            # Check if cancelled reservation was supposed to arrive today
            if start_date == target_date:
                cancelled_arrivals_list.append(reservation_detail)

            # Check if cancelled reservation was supposed to depart today
            if end_date == target_date:
                cancelled_departures_list.append(reservation_detail)

        # Add cancelled rooms to response if no filter or filter is 'cancelled'
        if not filter_type or filter_type == 'cancelled':
            response_data["cancelled_rooms"] = {
                "count": sum(room["quantity"] for room in cancelled_rooms_by_type.values()),
                "by_type": list(cancelled_rooms_by_type.values()),
                "cancelled_arrivals": {
                    "count": len(cancelled_arrivals_list),
                    "rooms": cancelled_arrivals_list
                },
                "cancelled_departures": {
                    "count": len(cancelled_departures_list),
                    "rooms": cancelled_departures_list
                }
            }

        mydb.close()

        return jsonify({
            "success": True,
            "data": response_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500