from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from .utils import (
    post_sales_and_create_journal,
    post_sales_and_create_journal_for_creditbills, parse_frontend_datetime, get_operational_date_from_datetime
)

load_dotenv()

app_file8 = Blueprint("app_file8", __name__)


from .menuengineering.currentleveladjustmentaftersale import adjust_item_current_level_after_sale


# @app_file8.route("/postsales", methods=["POST"])
# @cross_origin()
# def stats():
#     try:
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#         )
#         cursor = mydb.cursor(buffered=True)
#         cursor.execute("USE {};".format(os.getenv("database")))

#         data = request.get_json()

#         if not data:
#             return {"error": "Missing or invalid JSON body"}, 400
        
#         # Check if the entry already exists based on the date and Outlet_Name
#         cursor.execute(
#                 "SELECT * FROM tblorderhistory WHERE Date = %s AND bill_no = %s AND Outlet_Name=%s",
#                 (data["date"], data["bill_No"],data["Outlet_Name"],)
#         )
#         existing_entry = cursor.fetchone()

#         # If an existing entry is found, skip the insertion for this record
#         if existing_entry:
#             # print(f"Skipping date {data['date']} for Outlet {data['Outlet_Name']} (already exists).")
#             return({"data": f"Skipping date {data['date']} for Outlet {data['bill_No']} (already exists)."}, 200)

#         payment_mode = data.get("paymentMode")
#         hotel_room_no = (str(data.get("room_no") or "")).strip()
#         hotel_reservation_id = data.get("hotel_reservation_id")

#         if payment_mode == "Room Charge":
#             if not hotel_room_no:
#                 mydb.close()
#                 return {"error": "room_no is required for Room Charge"}, 400
#             if hotel_reservation_id in (None, ""):
#                 mydb.close()
#                 return {"error": "hotel_reservation_id is required for Room Charge"}, 400
#             try:
#                 hotel_reservation_id = int(hotel_reservation_id)
#             except (TypeError, ValueError):
#                 mydb.close()
#                 return {"error": "hotel_reservation_id must be a number"}, 400

#             # The reservation must be in-house, and this room must be one of its current rooms
#             cursor.execute("""
#                 SELECT res.id
#                 FROM hotel_tblreservation res
#                 INNER JOIN hotel_tblreservation_details rd ON rd.Reservation_ID = res.id
#                 INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
#                 WHERE res.id = %s
#                 AND r.room_no = %s
#                 AND res.Current_Status = 'Registered'
#                 AND res.is_active = 1
#                 AND rd.is_current = TRUE
#                 AND rd.is_active = 1
#                 AND r.is_active = 1
#                 LIMIT 1
#             """, (hotel_reservation_id, hotel_room_no))
#             if not cursor.fetchone():
#                 mydb.close()
#                 return {"error": f"Reservation {hotel_reservation_id} is not checked in to room {hotel_room_no}"}, 400
#         else:
#             hotel_room_no = None
#             hotel_reservation_id = None
            
#         # Insert into tblorderhistory
#         insert_order_sql = """
#             INSERT INTO tblorderhistory (
#                 Outlet_OrderID, Employee, Table_No, NoOfGuests, Start_Time, End_Time, State, Type,
#                 Discounts, Date, bill_no, Total, serviceCharge, VAT, DiscountAmt, PaymentMode,
#                 fiscal_year, GuestName, Outlet_Name, billPrintTime, guestID, guestEmail,
#                 guestPhone, guestAddress, order_id_ocular, guestPan, hotel_reservation_id, hotel_room_no
#             )
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         # Normalize noofGuest to integer, default 0 if empty or invalid
#         no_of_guests = data.get("noofGuest")
#         try:
#             no_of_guests = int(no_of_guests) if str(no_of_guests).strip() != "" else 0
#         except ValueError:
#             no_of_guests = 0

#         cursor.execute(
#             insert_order_sql,
#             (
#                 data["OrderID"],
#                 data["Employee"],
#                 data["TableNo"],
#                 no_of_guests,
#                 data["start_Time"],
#                 data["end_Time"],
#                 data["state"],
#                 data["type"],
#                 data["discounts"],
#                 data["date"],
#                 data["bill_No"],
#                 data["Total"],
#                 data["serviceCharge"],
#                 data["VAT"],
#                 data["discountAmt"],
#                 data["paymentMode"],
#                 data["fiscal_Year"],
#                 data["GuestName"],
#                 data["Outlet_Name"],
#                 data["billPrintTime"],
#                 data["guestID"],
#                 data["guestEmail"],
#                 data["guestPhone"],
#                 data["guestAddress"],
#                 data.get("order_id_ocular", None),
#                 data["guestPAN"],
#                 hotel_reservation_id,
#                 hotel_room_no,

#             ),
#         )
#         mydb.commit()
#         order_id = cursor.lastrowid
#         # Handle Credit Entry
#         if data["paymentMode"] == "Credit":
#             credit_sql = """
#                 INSERT INTO CreditHistory (outetName, Date, customerName, guestID, creditState, Outlet_OrderID, Amount, guestPan)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(
#                 credit_sql,
#                 (
#                     data["Outlet_Name"],
#                     data["date"],
#                     data["GuestName"],
#                     data["guestID"],
#                     "InitialEntry",
#                     data["OrderID"],
#                     data["Total"],
#                     data["guestPAN"]

#                 ),
#             )
#             mydb.commit()

#         # # Get order ID for item insertion
#         # cursor.execute(
#         #     "SELECT idtblorderhistory FROM tblorderhistory ORDER BY idtblorderhistory DESC LIMIT 1"
#         # )
#         # order_id = cursor.fetchone()[0]

#         # -------------------------------
#         # SPLIT PAYMENTS
#         # -------------------------------
#         if data["paymentMode"] == "Split":
#             payment_sql = """
#                 INSERT INTO payment_history
#                 (bill_No, paymentMode, paymentAmount, orderHistoryid, FiscalYear)
#                 VALUES (%s,%s,%s,%s,%s)
#             """
#             for payment in data.get("SplitPaymentDetailsList", []):
#                 cursor.execute(payment_sql, (
#                     data["bill_No"],
#                     payment["paymentMode"],
#                     payment["paymentAmount"],
#                     order_id,
#                     data["fiscal_Year"],
#                 ))

#         # Insert each item into tblorder_detailshistory
#         insert_item_sql = """
#             INSERT INTO tblorder_detailshistory (
#                 order_ID, ItemName, itemRate, Total, ItemType, Description, discountExempt, count
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         for item in data["ItemDetailsList"]:
#             item_data = (
#                 order_id,
#                 item["itemName"],
#                 item["ItemRate"],
#                 item["total"],
#                 item["ItemType"],
#                 item["Description"],
#                 item["disExempt"],
#                 item["count"],
#             )
#             cursor.execute(insert_item_sql, item_data)
#             mydb.commit()

#             if item["count"] > 0:
#                 adjust_item_current_level_after_sale(item["itemName"], item["count"], data["Outlet_Name"], cursor, mydb, data["date"])

#         if data["guestPhone"] != "":

#             loyalty_received_check_query = """SELECT * FROM loyaltyqueue WHERE outlet = %s and bill_no = %s and date= %s"""
#             cursor.execute(
#                 loyalty_received_check_query,
#                 (
#                     data["Outlet_Name"],
#                     data["bill_No"],
#                     data["date"],
#                 ),
#             )
#             loyalty_received_record = cursor.fetchone()
#             print(loyalty_received_record)
#             if not loyalty_received_record or (loyalty_received_record[3] and loyalty_received_record[3].lower() == "pending"):
#                 # Check and Insert Guest if not exists
#                 guest_check_query = """
#                     SELECT * FROM guest WHERE guestPhone = %s
#                 """
#                 cursor.execute(guest_check_query, (data["guestPhone"],))
#                 guest_record = cursor.fetchone()
#                 print("guest recrd", guest_record)
#                 if not guest_record:
#                     insert_guest_query = """
#                         INSERT INTO guest (guestID, guestEmail, guestPhone, guestAddress, Outlet_Name, GuestName, loyalty_points, guestPan)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#                     """
#                     cursor.execute(
#                         insert_guest_query,
#                         (
#                             data["guestID"],
#                             data["guestEmail"],
#                             data["guestPhone"],
#                             data["guestAddress"],
#                             data["Outlet_Name"],
#                             data["GuestName"],
#                             0.00,
#                             data["guestPAN"]

#                         ),
#                     )
#                     mydb.commit()

#                 print("Outlet name is", data["Outlet_Name"])

#                 # Loyalty points logic
#                 cursor.execute(
#                     "SELECT loyalty_percent FROM outetNames WHERE Outlet = %s",
#                     (data["Outlet_Name"],),
#                 )

#                 loyalty_result = cursor.fetchone()
#                 loyalty_percent = (
#                     loyalty_result[0] if loyalty_result and loyalty_result[0] else 0.0
#                 )

#                 if loyalty_percent > 0:
#                     loyalty_earned = (
#                         float(data["Total"] - data["VAT"]) * float(loyalty_percent)
#                     ) / 100

#                     # Get previous points
#                     cursor.execute(
#                         """
#                         SELECT loyalty_points FROM guest 
#                         WHERE guestID = %s AND GuestName = %s AND Outlet_Name = %s
#                     """,
#                         (data["guestID"], data["GuestName"], data["Outlet_Name"]),
#                     )
#                     prev_points_result = cursor.fetchone()
#                     prev_points = (
#                         float(prev_points_result[0]) if prev_points_result else 0.00
#                     )

#                     new_total_points = round(prev_points + loyalty_earned, 2)

#                     # Update guest's total loyalty points
#                     update_loyalty_query = """
#                         UPDATE guest
#                         SET loyalty_points = %s
#                         WHERE guestID = %s AND GuestName = %s AND Outlet_Name = %s
#                     """
#                     cursor.execute(
#                         update_loyalty_query,
#                         (
#                             new_total_points,
#                             data["guestID"],
#                             data["GuestName"],
#                             data["Outlet_Name"],
#                         ),
#                     )
#                     mydb.commit()

#                     # Insert history
#                     insert_loyalty_history = """
#                         INSERT INTO GuestLoyaltyHistory (
#                             guestID, GuestName, Outlet_Name, Date, PreviousPoints, EarnedPoints, TotalPoints, phone_no, guestPan
#                         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#                     """
#                     cursor.execute(
#                         insert_loyalty_history,
#                         (
#                             data["guestID"],
#                             data["GuestName"],
#                             data["Outlet_Name"],
#                             data["date"],
#                             round(prev_points, 2),
#                             round(loyalty_earned, 2),
#                             new_total_points,
#                             data["guestPhone"],
#                             data["guestPAN"]                            
#                         ),
#                     )
#                     mydb.commit()

#                     # LoyaltyQueue update or insert
#                     loyaltyqueue_pending_check_query = """
#                         SELECT id FROM loyaltyqueue 
#                         WHERE outlet = %s AND bill_no = %s AND date = %s and status='pending'
#                     """
#                     cursor.execute(
#                         loyaltyqueue_pending_check_query,
#                         (data["Outlet_Name"], data["bill_No"], data["date"]),
#                     )
#                     loyalty_row = cursor.fetchone()

#                     if loyalty_row:
#                         # Update existing entry to received if it was pending
#                         update_loyalty_status = """
#                             UPDATE loyaltyqueue
#                             SET status = 'received'
#                             WHERE outlet = %s AND bill_no = %s AND date = %s AND status = 'pending'
#                         """
#                         cursor.execute(
#                             update_loyalty_status,
#                             (data["Outlet_Name"], data["bill_No"], data["date"]),
#                         )
#                         mydb.commit()
#                     else:
#                         # Insert new entry marked as received
#                         insert_loyalty_entry = """
#                             INSERT INTO loyaltyqueue (hash_code, status, outlet, bill_no, sub_total, date)
#                             VALUES ( %s, 'received', %s, %s, %s, %s)
#                         """
#                         import hashlib

#                         hash_input = (
#                             f"{data['bill_No']}{data['Outlet_Name']}{data['date']}"
#                         )
#                         hash_code = hashlib.sha256(hash_input.encode()).hexdigest()

#                         cursor.execute(
#                             insert_loyalty_entry,
#                             (
#                                 hash_code,
#                                 data["Outlet_Name"],
#                                 data["bill_No"],
#                                 data["Total"],  # Using total as sub_total here
#                                 data["date"],
#                             ),
#                         )
#                         mydb.commit()

#             # Check and Insert Guest if not exists
#             customer_check_query = """
#                 SELECT * FROM customers WHERE phone = %s
#             """
#             cursor.execute(customer_check_query, (data["guestPhone"],))
#             customer_record = cursor.fetchone()
#             print("customer recrd", customer_record)
#             if not customer_record:
#                 insert_customer_query = """
#                     INSERT INTO customers (email, phone, address, source, name, guestPan)
#                     VALUES (%s, %s, %s, %s, %s, %s)
#                 """
#                 cursor.execute(
#                     insert_customer_query,
#                         (
#                             data["guestEmail"],
#                             data["guestPhone"],
#                             data["guestAddress"],
#                             data["Outlet_Name"],
#                             data["GuestName"],
#                             data["guestPAN"]
#                         ),
#                 )
#                 mydb.commit()

#         # -------- ACCOUNTING --------
#         try:
#             data["sales_entry"] = get_outlet_sales_entry_info(cursor, data)
#         except Exception as e:
#             print({"error": f"sales entry info failed: {e}"})
#             data["sales_entry"] = {"skip": True}   # journal still posts; no sales entry / IRD

#         if data["paymentMode"] != "Credit" and data["paymentMode"] != "Room Charge":
#             post_sales_and_create_journal(data)
#         else:
#             post_sales_and_create_journal_for_creditbills(data)

#         mydb.close()
#         return {"success": "Data posted successfully"}

#     except Exception as error:
#         return {"error": str(error)}, 400


# def get_outlet_sales_entry_info(cursor, data):
#     """Decide whether this outlet bill creates a sales entry in accounting, and under which number.
#     Returns {"skip": True} or {"skip": False, "sales_bill_no": "ALG-12"}."""
#     if data.get("paymentMode") in ("Complimentary", "Non Chargeable"):
#         return {"skip": True}

#     cursor.execute(
#         "SELECT postingToIRD, bill_prefix FROM outetNames WHERE Outlet = %s LIMIT 1",
#         (data["Outlet_Name"],)
#     )
#     row = cursor.fetchone()
#     if not row or not row[0]:
#         return {"skip": True}

#     prefix = (row[1] or "").strip()
#     if not prefix:
#         raise ValueError(f"Outlet '{data['Outlet_Name']}' posts to IRD but has no bill_prefix")

#     return {"skip": False, "sales_bill_no": f"{prefix}-{data['bill_No']}"}


@app_file8.route("/postsales", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute("USE {};".format(os.getenv("database")))

        data = request.get_json()

        if not data:
            return {"error": "Missing or invalid JSON body"}, 400
        
        # Check if the entry already exists based on the date and Outlet_Name
        cursor.execute(
                "SELECT * FROM tblorderhistory WHERE Date = %s AND bill_no = %s AND Outlet_Name=%s",
                (data["date"], data["bill_No"],data["Outlet_Name"],)
        )
        existing_entry = cursor.fetchone()

        # If an existing entry is found, skip the insertion for this record
        if existing_entry:
            # print(f"Skipping date {data['date']} for Outlet {data['Outlet_Name']} (already exists).")
            return({"data": f"Skipping date {data['date']} for Outlet {data['bill_No']} (already exists)."}, 200)

        payment_mode = data.get("paymentMode")
        hotel_room_no = (str(data.get("room_no") or "")).strip()
        hotel_reservation_id = data.get("hotel_reservation_id")

        # if payment_mode == "Room Charge":
        #     if not hotel_room_no:
        #         mydb.close()
        #         return {"error": "room_no is required for Room Charge"}, 400
        #     if hotel_reservation_id in (None, ""):
        #         mydb.close()
        #         return {"error": "hotel_reservation_id is required for Room Charge"}, 400
        #     try:
        #         hotel_reservation_id = int(hotel_reservation_id)
        #     except (TypeError, ValueError):
        #         mydb.close()
        #         return {"error": "hotel_reservation_id must be a number"}, 400

        #     # The reservation must be in-house, and this room must be one of its current rooms
        #     cursor.execute("""
        #         SELECT res.id
        #         FROM hotel_tblreservation res
        #         INNER JOIN hotel_tblreservation_details rd ON rd.Reservation_ID = res.id
        #         INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
        #         WHERE res.id = %s
        #         AND r.room_no = %s
        #         AND res.Current_Status = 'Registered'
        #         AND res.is_active = 1
        #         AND rd.is_current = TRUE
        #         AND rd.is_active = 1
        #         AND r.is_active = 1
        #         LIMIT 1
        #     """, (hotel_reservation_id, hotel_room_no))
        #     if not cursor.fetchone():
        #         mydb.close()
        #         return {"error": f"Reservation {hotel_reservation_id} is not checked in to room {hotel_room_no}"}, 400
        # else:
        #     hotel_room_no = None
        #     hotel_reservation_id = None

        if payment_mode == "Room Charge":
            if not hotel_room_no:
                mydb.close()
                return {"error": "room_no is required for Room Charge"}, 400
            if hotel_reservation_id in (None, ""):
                mydb.close()
                return {"error": "hotel_reservation_id is required for Room Charge"}, 400
            try:
                hotel_reservation_id = int(hotel_reservation_id)
            except (TypeError, ValueError):
                mydb.close()
                return {"error": "hotel_reservation_id must be a number"}, 400

            # The reservation must be in-house, this room must be one of its current rooms,
            # and we read who to bill (company if there is one, otherwise the guest)
            cursor.execute("""
                SELECT res.Guest_ID, res.company_id,
                       c.name, c.guestPan,
                       comp.company_name, comp.pan_number
                FROM hotel_tblreservation res
                INNER JOIN hotel_tblreservation_details rd ON rd.Reservation_ID = res.id
                INNER JOIN hotel_tblrooms r ON rd.room_id = r.id
                LEFT JOIN customers c ON res.Guest_ID = c.id
                LEFT JOIN companies comp ON res.company_id = comp.id
                WHERE res.id = %s
                AND r.room_no = %s
                AND res.Current_Status = 'Registered'
                AND res.is_active = 1
                AND rd.is_current = TRUE
                AND rd.is_active = 1
                AND r.is_active = 1
                LIMIT 1
            """, (hotel_reservation_id, hotel_room_no))
            res_row = cursor.fetchone()
            if not res_row:
                mydb.close()
                return {"error": f"Reservation {hotel_reservation_id} is not checked in to room {hotel_room_no}"}, 400

            guest_id, company_id, guest_name, guest_pan, company_name, company_pan = res_row

            if company_id:
                # company reservation: bill the company, id looks like C-1
                data["guestID"] = f"C-{company_id}"
                data["GuestName"] = company_name or ""
                data["guestPAN"] = company_pan or ""
            elif guest_id:
                # individual reservation: bill the guest, id looks like G-1
                data["guestID"] = f"G-{guest_id}"
                data["GuestName"] = guest_name or ""
                data["guestPAN"] = guest_pan or ""
            else:
                mydb.close()
                return {"error": f"Reservation {hotel_reservation_id} has no guest or company"}, 400
        else:
            hotel_room_no = None
            hotel_reservation_id = None
            
        # Insert into tblorderhistory
        insert_order_sql = """
            INSERT INTO tblorderhistory (
                Outlet_OrderID, Employee, Table_No, NoOfGuests, Start_Time, End_Time, State, Type,
                Discounts, Date, bill_no, Total, serviceCharge, VAT, DiscountAmt, PaymentMode,
                fiscal_year, GuestName, Outlet_Name, billPrintTime, guestID, guestEmail,
                guestPhone, guestAddress, order_id_ocular, guestPan, hotel_reservation_id, hotel_room_no
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Normalize noofGuest to integer, default 0 if empty or invalid
        no_of_guests = data.get("noofGuest")
        try:
            no_of_guests = int(no_of_guests) if str(no_of_guests).strip() != "" else 0
        except ValueError:
            no_of_guests = 0

        cursor.execute(
            insert_order_sql,
            (
                data["OrderID"],
                data["Employee"],
                data["TableNo"],
                no_of_guests,
                data["start_Time"],
                data["end_Time"],
                data["state"],
                data["type"],
                data["discounts"],
                data["date"],
                data["bill_No"],
                data["Total"],
                data["serviceCharge"],
                data["VAT"],
                data["discountAmt"],
                data["paymentMode"],
                data["fiscal_Year"],
                data["GuestName"],
                data["Outlet_Name"],
                data["billPrintTime"],
                data["guestID"],
                data["guestEmail"],
                data["guestPhone"],
                data["guestAddress"],
                data.get("order_id_ocular", None),
                data["guestPAN"],
                hotel_reservation_id,
                hotel_room_no,

            ),
        )
        mydb.commit()
        order_id = cursor.lastrowid
        # Handle Credit Entry
        if data["paymentMode"] == "Credit":
            credit_sql = """
                INSERT INTO CreditHistory (outetName, Date, customerName, guestID, creditState, Outlet_OrderID, Amount, guestPan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                credit_sql,
                (
                    data["Outlet_Name"],
                    data["date"],
                    data["GuestName"],
                    data["guestID"],
                    "InitialEntry",
                    data["OrderID"],
                    data["Total"],
                    data["guestPAN"]

                ),
            )
            mydb.commit()

        # # Get order ID for item insertion
        # cursor.execute(
        #     "SELECT idtblorderhistory FROM tblorderhistory ORDER BY idtblorderhistory DESC LIMIT 1"
        # )
        # order_id = cursor.fetchone()[0]

        # -------------------------------
        # SPLIT PAYMENTS
        # -------------------------------
        if data["paymentMode"] == "Split":
            payment_sql = """
                INSERT INTO payment_history
                (bill_No, paymentMode, paymentAmount, orderHistoryid, FiscalYear)
                VALUES (%s,%s,%s,%s,%s)
            """
            for payment in data.get("SplitPaymentDetailsList", []):
                cursor.execute(payment_sql, (
                    data["bill_No"],
                    payment["paymentMode"],
                    payment["paymentAmount"],
                    order_id,
                    data["fiscal_Year"],
                ))

        # Insert each item into tblorder_detailshistory
        insert_item_sql = """
            INSERT INTO tblorder_detailshistory (
                order_ID, ItemName, itemRate, Total, ItemType, Description, discountExempt, count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for item in data["ItemDetailsList"]:
            item_data = (
                order_id,
                item["itemName"],
                item["ItemRate"],
                item["total"],
                item["ItemType"],
                item["Description"],
                item["disExempt"],
                item["count"],
            )
            cursor.execute(insert_item_sql, item_data)
            mydb.commit()

            if item["count"] > 0:
                adjust_item_current_level_after_sale(item["itemName"], item["count"], data["Outlet_Name"], cursor, mydb, data["date"])

        if data["guestPhone"] != "":

            loyalty_received_check_query = """SELECT * FROM loyaltyqueue WHERE outlet = %s and bill_no = %s and date= %s"""
            cursor.execute(
                loyalty_received_check_query,
                (
                    data["Outlet_Name"],
                    data["bill_No"],
                    data["date"],
                ),
            )
            loyalty_received_record = cursor.fetchone()
            print(loyalty_received_record)
            if not loyalty_received_record or (loyalty_received_record[3] and loyalty_received_record[3].lower() == "pending"):
                # Check and Insert Guest if not exists
                guest_check_query = """
                    SELECT * FROM guest WHERE guestPhone = %s
                """
                cursor.execute(guest_check_query, (data["guestPhone"],))
                guest_record = cursor.fetchone()
                print("guest recrd", guest_record)
                if not guest_record:
                    insert_guest_query = """
                        INSERT INTO guest (guestID, guestEmail, guestPhone, guestAddress, Outlet_Name, GuestName, loyalty_points, guestPan)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_guest_query,
                        (
                            data["guestID"],
                            data["guestEmail"],
                            data["guestPhone"],
                            data["guestAddress"],
                            data["Outlet_Name"],
                            data["GuestName"],
                            0.00,
                            data["guestPAN"]

                        ),
                    )
                    mydb.commit()

                print("Outlet name is", data["Outlet_Name"])

                # Loyalty points logic
                cursor.execute(
                    "SELECT loyalty_percent FROM outetNames WHERE Outlet = %s",
                    (data["Outlet_Name"],),
                )

                loyalty_result = cursor.fetchone()
                loyalty_percent = (
                    loyalty_result[0] if loyalty_result and loyalty_result[0] else 0.0
                )

                if loyalty_percent > 0:
                    loyalty_earned = (
                        float(data["Total"] - data["VAT"]) * float(loyalty_percent)
                    ) / 100

                    # Get previous points
                    cursor.execute(
                        """
                        SELECT loyalty_points FROM guest 
                        WHERE guestID = %s AND GuestName = %s AND Outlet_Name = %s
                    """,
                        (data["guestID"], data["GuestName"], data["Outlet_Name"]),
                    )
                    prev_points_result = cursor.fetchone()
                    prev_points = (
                        float(prev_points_result[0]) if prev_points_result else 0.00
                    )

                    new_total_points = round(prev_points + loyalty_earned, 2)

                    # Update guest's total loyalty points
                    update_loyalty_query = """
                        UPDATE guest
                        SET loyalty_points = %s
                        WHERE guestID = %s AND GuestName = %s AND Outlet_Name = %s
                    """
                    cursor.execute(
                        update_loyalty_query,
                        (
                            new_total_points,
                            data["guestID"],
                            data["GuestName"],
                            data["Outlet_Name"],
                        ),
                    )
                    mydb.commit()

                    # Insert history
                    insert_loyalty_history = """
                        INSERT INTO GuestLoyaltyHistory (
                            guestID, GuestName, Outlet_Name, Date, PreviousPoints, EarnedPoints, TotalPoints, phone_no, guestPan
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_loyalty_history,
                        (
                            data["guestID"],
                            data["GuestName"],
                            data["Outlet_Name"],
                            data["date"],
                            round(prev_points, 2),
                            round(loyalty_earned, 2),
                            new_total_points,
                            data["guestPhone"],
                            data["guestPAN"]                            
                        ),
                    )
                    mydb.commit()

                    # LoyaltyQueue update or insert
                    loyaltyqueue_pending_check_query = """
                        SELECT id FROM loyaltyqueue 
                        WHERE outlet = %s AND bill_no = %s AND date = %s and status='pending'
                    """
                    cursor.execute(
                        loyaltyqueue_pending_check_query,
                        (data["Outlet_Name"], data["bill_No"], data["date"]),
                    )
                    loyalty_row = cursor.fetchone()

                    if loyalty_row:
                        # Update existing entry to received if it was pending
                        update_loyalty_status = """
                            UPDATE loyaltyqueue
                            SET status = 'received'
                            WHERE outlet = %s AND bill_no = %s AND date = %s AND status = 'pending'
                        """
                        cursor.execute(
                            update_loyalty_status,
                            (data["Outlet_Name"], data["bill_No"], data["date"]),
                        )
                        mydb.commit()
                    else:
                        # Insert new entry marked as received
                        insert_loyalty_entry = """
                            INSERT INTO loyaltyqueue (hash_code, status, outlet, bill_no, sub_total, date)
                            VALUES ( %s, 'received', %s, %s, %s, %s)
                        """
                        import hashlib

                        hash_input = (
                            f"{data['bill_No']}{data['Outlet_Name']}{data['date']}"
                        )
                        hash_code = hashlib.sha256(hash_input.encode()).hexdigest()

                        cursor.execute(
                            insert_loyalty_entry,
                            (
                                hash_code,
                                data["Outlet_Name"],
                                data["bill_No"],
                                data["Total"],  # Using total as sub_total here
                                data["date"],
                            ),
                        )
                        mydb.commit()

            # Check and Insert Guest if not exists
            customer_check_query = """
                SELECT * FROM customers WHERE phone = %s
            """
            cursor.execute(customer_check_query, (data["guestPhone"],))
            customer_record = cursor.fetchone()
            print("customer recrd", customer_record)
            if not customer_record:
                insert_customer_query = """
                    INSERT INTO customers (email, phone, address, source, name, guestPan)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(
                    insert_customer_query,
                        (
                            data["guestEmail"],
                            data["guestPhone"],
                            data["guestAddress"],
                            data["Outlet_Name"],
                            data["GuestName"],
                            data["guestPAN"]
                        ),
                )
                mydb.commit()

        # -------- ACCOUNTING --------
        try:
            data["sales_entry"] = get_outlet_sales_entry_info(cursor, data)
        except Exception as e:
            print({"error": f"sales entry info failed: {e}"})
            data["sales_entry"] = {"skip": True}   # journal still posts; no sales entry / IRD

        if data["paymentMode"] != "Credit" and data["paymentMode"] != "Room Charge":
            post_sales_and_create_journal(data)
        else:
            post_sales_and_create_journal_for_creditbills(data)

        mydb.close()
        return {"success": "Data posted successfully"}

    except Exception as error:
        return {"error": str(error)}, 400



def get_outlet_sales_entry_info(cursor, data):
    """Decide whether this outlet bill creates a sales entry in accounting, and under which number.
    Returns {"skip": True} or {"skip": False, "sales_bill_no": "ALG-12"}."""
    if data.get("paymentMode") in ("Complimentary", "Non Chargeable"):
        return {"skip": True}

    cursor.execute(
        "SELECT postingToIRD, bill_prefix FROM outetNames WHERE Outlet = %s LIMIT 1",
        (data["Outlet_Name"],)
    )
    row = cursor.fetchone()
    if not row or not row[0]:
        return {"skip": True}

    prefix = (row[1] or "").strip()
    if not prefix:
        raise ValueError(f"Outlet '{data['Outlet_Name']}' posts to IRD but has no bill_prefix")

    return {"skip": False, "sales_bill_no": f"{prefix}-{data['bill_No']}"}