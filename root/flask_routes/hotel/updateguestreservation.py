from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()
from root.auth.check import token_auth

app_file418 = Blueprint('app_file418', __name__)


from decimal import Decimal, InvalidOperation

ADVANCE_KEYS = ("Advance_Payment", "Advance_Payment_Currency", "Advance_Payment_Local")
 
 
def _dec(value):
    if value in (None, ""):
        return None
    return Decimal(str(value))
 
 
def normalize_advance_payment(reservation_data, existing):
    """
    Same rules as /create-reservation, applied to a partial update.
    Values the frontend did not send keep their current database value.
 
    Returns an error message, or None when OK. On success reservation_data is
    rewritten with the final amount / currency / local value, so the field_map
    in ReservationUpdate saves all three together.
    """
    if not any(k in reservation_data for k in ADVANCE_KEYS):
        return None  # advance payment not part of this update
 
    def pick(key):
        return reservation_data[key] if key in reservation_data else existing.get(key)
 
    # ---- amount ----
    raw_amount = pick("Advance_Payment")
    if raw_amount in (None, ""):
        amount = None
    else:
        try:
            amount = Decimal(str(raw_amount))
        except InvalidOperation:
            return "Advance_Payment must be a number."
        if amount < 0:
            return "Advance_Payment cannot be negative."
 
    # ---- currency ----
    currency = str(pick("Advance_Payment_Currency") or "").strip().upper() or None
 
    # ---- local amount (NPR) ----
    raw_local = pick("Advance_Payment_Local")
    if raw_local in (None, ""):
        local = None
    else:
        try:
            local = Decimal(str(raw_local))
        except InvalidOperation:
            return "Advance_Payment_Local must be a number."
        if local < 0:
            return "Advance_Payment_Local cannot be negative."
 
    if amount:
        if not currency:
            currency = "NPR"  # default when an amount exists without a currency
 
        # a changed amount or currency makes the old local value stale
        old_amount = _dec(existing.get("Advance_Payment"))
        old_currency = str(existing.get("Advance_Payment_Currency") or "").strip().upper() or None
        if "Advance_Payment_Local" not in reservation_data and (
            amount != old_amount or currency != old_currency
        ):
            return "Advance_Payment_Local is required when the advance amount or currency changes."
        if local is None:
            return "Advance_Payment_Local is required when Advance_Payment is sent."
    else:
        # no advance -> no currency, no local amount
        currency = None
        local = None
 
    reservation_data["Advance_Payment"] = amount
    reservation_data["Advance_Payment_Currency"] = currency
    reservation_data["Advance_Payment_Local"] = local
    return None

# class CustomerUpdate:
#     """Helper class for customer operations"""
#     @staticmethod
#     def update_or_create(cursor, customer_data, existing_customer_id=None):
#         """
#         Update existing customer or create new one
#         Returns: customer_id
#         """
#         # Check if we need to link to existing customer via new_id
#         if 'new_id' in customer_data:
#             new_id = customer_data.pop('new_id')
#             # Verify customer exists
#             cursor.execute("SELECT id FROM customers WHERE id = %s AND is_active = 1", (new_id,))
#             if cursor.fetchone():
#                 return new_id
#             else:
#                 raise ValueError(f"Customer with id {new_id} does not exist")

#         # Prepare customer fields
#         name = customer_data.get('name')
#         phone = customer_data.get('phone')
#         email = customer_data.get('email')
#         address = customer_data.get('address')
#         guest_pan = customer_data.get('guestPan')
#         customer_type = customer_data.get('customer_type')
#         outlet_guest_id = customer_data.get('outlet_guest_id')

#         if existing_customer_id:
#             # Update existing customer
#             update_fields = []
#             update_values = []

#             if name is not None:
#                 update_fields.append("name = %s")
#                 update_values.append(name)
#             if phone is not None:
#                 update_fields.append("phone = %s")
#                 update_values.append(phone)
#             if email is not None:
#                 update_fields.append("email = %s")
#                 update_values.append(email)
#             if address is not None:
#                 update_fields.append("address = %s")
#                 update_values.append(address)
#             if guest_pan is not None:
#                 update_fields.append("guestPan = %s")
#                 update_values.append(guest_pan)
#             if customer_type is not None:
#                 update_fields.append("customer_type = %s")
#                 update_values.append(customer_type)
#             if outlet_guest_id is not None:
#                 update_fields.append("outlet_guest_id = %s")
#                 update_values.append(outlet_guest_id)

#             if update_fields:
#                 query = f"UPDATE customers SET {', '.join(update_fields)} WHERE id = %s"
#                 update_values.append(existing_customer_id)
#                 cursor.execute(query, tuple(update_values))

#             return existing_customer_id
#         else:
#             # Create new customer
#             insert_query = """
#                 INSERT INTO customers
#                 (name, phone, email, address, guestPan, customer_type, outlet_guest_id)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(insert_query, (
#                 name, phone, email, address, guest_pan, customer_type, outlet_guest_id
#             ))
#             return cursor.lastrowid

# class CompanyUpdate:
#     """Helper class for company operations"""

#     FIELD_MAP = {
#         "company_name": "company_name",
#         "outlet": "outlet",
#         "contact_person": "contact_person",
#         "address": "address",
#         "phone": "phone",
#         "email": "email",
#         "pan_number": "pan_number",
#         "company_type": "company_type",
#         "source": "source",
#         "outlet_company_id": "outlet_company_id",
#     }

#     @staticmethod
#     def resolve(cursor, company_data, existing_company_id=None):
#         """
#         Returns the company_id to store on the reservation (None = no company).
#         """
#         # null -> unlink
#         if company_data is None:
#             return None

#         if not isinstance(company_data, dict):
#             raise ValueError("company must be an object or null")

#         # link to an existing company
#         if company_data.get("new_id") is not None:
#             new_id = company_data["new_id"]
#             cursor.execute(
#                 "SELECT id FROM companies WHERE id = %s AND status = 1", (new_id,)
#             )
#             row = cursor.fetchone()
#             if not row:
#                 raise ValueError(f"Company with id {new_id} does not exist")
#             return row["id"]

#         fields = {
#             col: company_data[key]
#             for key, col in CompanyUpdate.FIELD_MAP.items()
#             if key in company_data
#         }

#         # update the company already linked to this reservation
#         if existing_company_id:
#             if fields:
#                 if "company_name" in fields and not str(fields["company_name"] or "").strip():
#                     raise ValueError("company_name cannot be empty")
#                 if "phone" in fields:
#                     if not str(fields["phone"] or "").strip():
#                         raise ValueError("phone cannot be empty")
#                     cursor.execute(
#                         "SELECT id FROM companies WHERE phone = %s AND id <> %s",
#                         (fields["phone"], existing_company_id),
#                     )
#                     if cursor.fetchone():
#                         raise ValueError("Another company with this phone already exists")

#                 set_clause = ", ".join(f"{col} = %s" for col in fields)
#                 cursor.execute(
#                     f"UPDATE companies SET {set_clause} WHERE id = %s",
#                     list(fields.values()) + [existing_company_id],
#                 )
#             return existing_company_id

#         # no company linked yet -> create one (same rules as POST /companies)
#         if not str(fields.get("company_name") or "").strip() or not str(fields.get("phone") or "").strip():
#             raise ValueError("company_name and phone are required to create a company")

#         cursor.execute("SELECT id FROM companies WHERE phone = %s", (fields["phone"],))
#         if cursor.fetchone():
#             raise ValueError("A company with this phone already exists")

#         cols = ", ".join(fields.keys())
#         placeholders = ", ".join(["%s"] * len(fields))
#         cursor.execute(
#             f"INSERT INTO companies ({cols}) VALUES ({placeholders})",
#             list(fields.values()),
#         )
#         return cursor.lastrowid


# class ReservationUpdate:
#     """Helper class for reservation operations"""
#     @staticmethod
#     def update(cursor, reservation_id, reservation_data, guest_id=None):
#         """
#         Update reservation details
#         """
#         update_fields = []
#         update_values = []
        
#         # Map of field names to database columns
#         field_map = {
#             'outlet': 'outlet',
#             'Emp_ID': 'Emp_ID',
#             'Pay_Mode': 'Pay_Mode',
#             'Billing_Inst': 'Billing_Inst',
#             'Reservation_type': 'Reservation_type',
#             'designation': 'designation',
#             'Advance_Payment': 'Advance_Payment',
#             'Advance_Payment_Currency': 'Advance_Payment_Currency',
#             'Advance_Payment_Local': 'Advance_Payment_Local',
#             'Market_Seg': 'Market_Seg',
#             'business_Src': 'business_Src',
#             'Current_Status': 'Current_Status',
#             'reservation_outlet_id': 'reservation_outlet_id'
#         }
        
#         # Handle special fields
#         if 'Reservation_Date' in reservation_data:
#             update_fields.append("Reservation_Date = %s")
#             update_values.append(reservation_data['Reservation_Date'])
        
#         if 'Check_In' in reservation_data:
#             update_fields.append("Check_In = %s")
#             update_values.append(reservation_data['Check_In'])
        
#         if 'Check_Out' in reservation_data:
#             update_fields.append("Check_Out = %s")
#             update_values.append(reservation_data['Check_Out'])
        
#         # Handle Guest_ID if provided
#         if guest_id:
#             update_fields.append("Guest_ID = %s")
#             update_values.append(guest_id)
        
#         # Handle other fields
#         for key, column in field_map.items():
#             if key in reservation_data:
#                 update_fields.append(f"{column} = %s")
#                 update_values.append(reservation_data[key])
        
#         if update_fields:
#             # update_fields.append("updated_at = NOW()")

#             query = f"UPDATE hotel_tblreservation SET {', '.join(update_fields)} WHERE id = %s"
#             update_values.append(reservation_id)
#             cursor.execute(query, tuple(update_values))
#             return cursor.rowcount > 0
        
#         return False


# class GuestReservationUpdate:
#     """Helper class for guest reservation operations"""
#     @staticmethod
#     def update(cursor, guest_reservation_id, guest_reservation_data):
#         """
#         Update guest reservation details
#         """
#         update_fields = []
#         update_values = []
        
#         # Map fields to database columns
#         field_map = {
#             'No_of_children': 'No_of_children',
#             'No_of_adults': 'No_of_adults',
#             'Likes': 'Likes',
#             'Dislikes': 'Dislikes',
#             'Guest_Notes': 'Guest_Notes',
#             'start_date': 'start_date',
#             'end_date': 'end_date'
#         }
        
#         for key, column in field_map.items():
#             if key in guest_reservation_data:
#                 update_fields.append(f"{column} = %s")
#                 update_values.append(guest_reservation_data[key])
        
#         if update_fields:
#             # update_fields.append("updated_at = NOW()")
#             query = f"UPDATE hotel_tblguestreservation SET {', '.join(update_fields)} WHERE id = %s"
#             update_values.append(guest_reservation_id)
#             cursor.execute(query, tuple(update_values))
#             return cursor.rowcount > 0
        
#         return False


# # @app_file418.route("/tblguestreservationupdate/<int:guest_reservation_id>", methods=["PUT", "PATCH"])
# # @cross_origin()
# # def update_guest_reservation(guest_reservation_id):
# #     """
# #     Update guest reservation with nested reservation and customer data
# #     Equivalent to Django's tblGuestReservationUpdateViewSet
# #     """
# #     try:
# #         # Connect to DB
# #         mydb = mysql.connector.connect(
# #             host=os.getenv("host"),
# #             user=os.getenv("user"),
# #             password=os.getenv("password"),
# #             database=os.getenv("database")
# #         )
# #         cursor = mydb.cursor(dictionary=True, buffered=True)

# #         # -------- TOKEN AUTH --------
# #         auth_header = request.headers.get("Authorization")
# #         if not auth_header:
# #             return {"error": "No token provided."}, 400
        
# #         try:
# #             token = auth_header.split(" ")[1]
# #         except:
# #             return {"error": "Invalid Authorization header format."}, 400
        
# #         if not token_auth(token):
# #             return {"error": "Invalid token."}, 400

# #         # Get JSON data
# #         json_data = request.get_json()
# #         if not json_data:
# #             return {"error": "No data provided"}, 400

# #         # Check if guest reservation exists
# #         # cursor.execute("""
# #         #     SELECT g.*, r.Guest_ID 
# #         #     FROM hotel_tblguestreservation g
# #         #     JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
# #         #     WHERE g.id = %s AND g.is_active = 1
# #         # """, (guest_reservation_id,))
        
# #         cursor.execute("""
# #             SELECT g.*, r.Guest_ID,
# #                    r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local
# #             FROM hotel_tblguestreservation g
# #             JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
# #             WHERE g.id = %s AND g.is_active = 1
# #         """, (guest_reservation_id,))

# #         existing_guest_reservation = cursor.fetchone()
        
# #         if not existing_guest_reservation:
# #             mydb.close()
# #             return {"error": "Guest reservation not found"}, 404

# #         reservation_id = existing_guest_reservation['Reservation_ID']
# #         current_guest_id = existing_guest_reservation['Guest_ID']


# #         print("reservation Id is ", reservation_id)
# #         # 🔥 FIX: Don't call start_transaction() explicitly
# #         # MySQL Connector/Python automatically starts a transaction
# #         # when autocommit is False (which is the default)
# #         # mydb.start_transaction()  # REMOVE THIS LINE

# #         try:
# #             # 1. Handle Customer/Guest data if provided
# #             reservation_data = json_data.get('Reservation_ID', {})
# #             advance_error = normalize_advance_payment(reservation_data, existing_guest_reservation)
# #             if advance_error:
# #                 mydb.close()
# #                 return {"error": advance_error}, 400
# #             guest_data = reservation_data.get('Guest_ID', {}) if reservation_data else {}
            
# #             new_guest_id = None
# #             if guest_data:
# #                 new_guest_id = CustomerUpdate.update_or_create(
# #                     cursor, 
# #                     guest_data, 
# #                     existing_customer_id=current_guest_id
# #                 )

# #             # 2. Handle Reservation update if provided
# #             if reservation_data:
# #                 ReservationUpdate.update(
# #                     cursor, 
# #                     reservation_id, 
# #                     reservation_data,
# #                     guest_id=new_guest_id
# #                 )

# #             # 3. Handle Guest Reservation update
# #             GuestReservationUpdate.update(cursor, guest_reservation_id, json_data)

# #             # Commit transaction
# #             mydb.commit()

# #             # Fetch updated data to return
# #             cursor.execute("""
# #                 SELECT 
# #                     g.*,
# #                     JSON_OBJECT(
# #                         'id', r.id,
# #                         'outlet', r.outlet,
# #                         'Emp_ID', r.Emp_ID,
# #                         'Pay_Mode', r.Pay_Mode,
# #                         'Billing_Inst', r.Billing_Inst,
# #                         'Reservation_type', r.Reservation_type,
# #                         'designation', r.designation,
# #                         'Advance_Payment', r.Advance_Payment,
# #                         'Advance_Payment_Currency', r.Advance_Payment_Currency,
# #                         'Advance_Payment_Local', r.Advance_Payment_Local,
# #                         'Market_Seg', r.Market_Seg,
# #                         'business_Src', r.business_Src,
# #                         'Current_Status', r.Current_Status,
# #                         'reservation_outlet_id', r.reservation_outlet_id,
# #                         'Reservation_Date', r.Reservation_Date,
# #                         'Check_In', r.Check_In,
# #                         'Check_Out', r.Check_Out,
# #                         'Guest_ID', JSON_OBJECT(
# #                             'id', c.id,
# #                             'name', c.name,
# #                             'phone', c.phone,
# #                             'email', c.email,
# #                             'address', c.address,
# #                             'guestPan', c.guestPan,
# #                             'customer_type', c.customer_type,
# #                             'outlet_guest_id', c.outlet_guest_id
# #                         )
# #                     ) as reservation_details
# #                 FROM hotel_tblguestreservation g
# #                 JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
# #                 JOIN customers c ON r.Guest_ID = c.id
# #                 WHERE g.id = %s
# #             """, (guest_reservation_id,))
            
# #             updated_data = cursor.fetchone()
            
# #             # Parse JSON fields
# #             if updated_data and updated_data.get('reservation_details'):
# #                 updated_data['Reservation_ID'] = json.loads(updated_data['reservation_details'])
# #                 del updated_data['reservation_details']

# #             print("reservation_id", reservation_id)

# #             # ✅ CHECK reservation_outlet_id FIRST
# #             cursor.execute(
# #                 """
# #                 SELECT reservation_outlet_id 
# #                 FROM hotel_tblreservation 
# #                 WHERE id = %s
# #                 """,
# #                 (reservation_id,)
# #             )
# #             result = cursor.fetchone()

# #             if result and result['reservation_outlet_id']:
# #                 # ✅ Only update if reservation_outlet_id has value (synced)
# #                 cursor.execute(
# #                     """
# #                     UPDATE hotel_tblreservation
# #                     SET is_updated = TRUE, updated_at = NOW()
# #                     WHERE id = %s
# #                     """,
# #                     (reservation_id,)
# #                 )
# #             mydb.commit()

# #             mydb.close()
            
# #             return jsonify({
# #                 "message": "Guest reservation updated successfully",
# #                 "data": updated_data
# #             }), 200

# #         except Exception as e:
# #             # Rollback on error
# #             mydb.rollback()
# #             raise e

# #     except ValueError as ve:
# #         return {"error": str(ve)}, 400
# #     except Exception as e:
# #         return {"error": str(e)}, 500


# @app_file418.route("/tblguestreservationupdate/<int:guest_reservation_id>", methods=["PUT", "PATCH"])
# @cross_origin()
# def update_guest_reservation(guest_reservation_id):
#     """
#     Update guest reservation with nested reservation, customer and company data
#     Equivalent to Django's tblGuestReservationUpdateViewSet
#     """
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN AUTH --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get JSON data
#         json_data = request.get_json()
#         if not json_data:
#             return {"error": "No data provided"}, 400

#         # Check if guest reservation exists
#         cursor.execute("""
#             SELECT g.*, r.Guest_ID, r.company_id, r.Current_Status,
#                    r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local
#             FROM hotel_tblguestreservation g
#             JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
#             WHERE g.id = %s AND g.is_active = 1
#         """, (guest_reservation_id,))

#         existing_guest_reservation = cursor.fetchone()

#         if not existing_guest_reservation:
#             mydb.close()
#             return {"error": "Guest reservation not found"}, 404

#         reservation_id = existing_guest_reservation['Reservation_ID']
#         current_guest_id = existing_guest_reservation['Guest_ID']
#         current_company_id = existing_guest_reservation['company_id']

#         # MySQL Connector/Python starts a transaction automatically
#         # (autocommit is False by default), so no explicit start_transaction().

#         try:
#             # 1. Handle Customer/Guest data if provided
#             reservation_data = json_data.get('Reservation_ID', {})
#             advance_error = normalize_advance_payment(reservation_data, existing_guest_reservation)
#             if advance_error:
#                 mydb.close()
#                 return {"error": advance_error}, 400
#             guest_data = reservation_data.get('Guest_ID', {}) if reservation_data else {}

#             new_guest_id = None
#             if guest_data:
#                 new_guest_id = CustomerUpdate.update_or_create(
#                     cursor,
#                     guest_data,
#                     existing_customer_id=current_guest_id
#                 )

#             # 1b. Handle Company (only touched when the "company" key is sent)
#             update_company = bool(reservation_data) and "company" in reservation_data
#             company_id_to_set = None
#             if update_company:
#                 # A billed reservation's credit journal points at the old party,
#                 # so the company can't change after checkout.
#                 if existing_guest_reservation['Current_Status'] == 'Checked Out':
#                     mydb.close()
#                     return {"error": "Company cannot be changed after checkout."}, 400

#                 company_id_to_set = CompanyUpdate.resolve(
#                     cursor,
#                     reservation_data["company"],
#                     existing_company_id=current_company_id,
#                 )

#             # 2. Handle Reservation update if provided
#             if reservation_data:
#                 ReservationUpdate.update(
#                     cursor,
#                     reservation_id,
#                     reservation_data,
#                     guest_id=new_guest_id,
#                     update_company=update_company,
#                     company_id=company_id_to_set,
#                 )

#             # 3. Handle Guest Reservation update
#             GuestReservationUpdate.update(cursor, guest_reservation_id, json_data)

#             # Commit transaction
#             mydb.commit()

#             # Fetch updated data to return
#             cursor.execute("""
#                 SELECT 
#                     g.*,
#                     JSON_OBJECT(
#                         'id', r.id,
#                         'outlet', r.outlet,
#                         'Emp_ID', r.Emp_ID,
#                         'Pay_Mode', r.Pay_Mode,
#                         'Billing_Inst', r.Billing_Inst,
#                         'Reservation_type', r.Reservation_type,
#                         'designation', r.designation,
#                         'Advance_Payment', r.Advance_Payment,
#                         'Advance_Payment_Currency', r.Advance_Payment_Currency,
#                         'Advance_Payment_Local', r.Advance_Payment_Local,
#                         'Market_Seg', r.Market_Seg,
#                         'business_Src', r.business_Src,
#                         'Current_Status', r.Current_Status,
#                         'reservation_outlet_id', r.reservation_outlet_id,
#                         'Reservation_Date', r.Reservation_Date,
#                         'Check_In', r.Check_In,
#                         'Check_Out', r.Check_Out,
#                         'company_id', r.company_id,
#                         'Guest_ID', JSON_OBJECT(
#                             'id', c.id,
#                             'name', c.name,
#                             'phone', c.phone,
#                             'email', c.email,
#                             'address', c.address,
#                             'guestPan', c.guestPan,
#                             'customer_type', c.customer_type,
#                             'outlet_guest_id', c.outlet_guest_id
#                         )
#                     ) as reservation_details
#                 FROM hotel_tblguestreservation g
#                 JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
#                 JOIN customers c ON r.Guest_ID = c.id
#                 WHERE g.id = %s
#             """, (guest_reservation_id,))

#             updated_data = cursor.fetchone()

#             # Parse JSON fields
#             if updated_data and updated_data.get('reservation_details'):
#                 updated_data['Reservation_ID'] = json.loads(updated_data['reservation_details'])
#                 del updated_data['reservation_details']

#             # Attach the linked company (None when the reservation has no company)
#             if updated_data and updated_data.get('Reservation_ID'):
#                 linked_company_id = updated_data['Reservation_ID'].get('company_id')
#                 company_obj = None
#                 if linked_company_id:
#                     cursor.execute("""
#                         SELECT id, company_name, outlet, contact_person, address, phone,
#                                email, pan_number, company_type, status, source
#                         FROM companies
#                         WHERE id = %s
#                     """, (linked_company_id,))
#                     company_obj = cursor.fetchone()
#                 updated_data['Reservation_ID']['company'] = company_obj

#             # Only mark as updated if the reservation was already synced
#             cursor.execute(
#                 """
#                 SELECT reservation_outlet_id 
#                 FROM hotel_tblreservation 
#                 WHERE id = %s
#                 """,
#                 (reservation_id,)
#             )
#             result = cursor.fetchone()

#             if result and result['reservation_outlet_id']:
#                 cursor.execute(
#                     """
#                     UPDATE hotel_tblreservation
#                     SET is_updated = TRUE, updated_at = NOW()
#                     WHERE id = %s
#                     """,
#                     (reservation_id,)
#                 )
#             mydb.commit()

#             mydb.close()

#             return jsonify({
#                 "message": "Guest reservation updated successfully",
#                 "data": updated_data
#             }), 200

#         except Exception as e:
#             # Rollback on error
#             mydb.rollback()
#             raise e

#     except ValueError as ve:
#         return {"error": str(ve)}, 400
#     except Exception as e:
#         return {"error": str(e)}, 500


class CustomerUpdate:
    """Helper class for customer operations"""
    @staticmethod
    def update_or_create(cursor, customer_data, existing_customer_id=None):
        """
        Update existing customer or create new one
        Returns: customer_id
        """
        # Check if we need to link to existing customer via new_id
        if 'new_id' in customer_data:
            new_id = customer_data.pop('new_id')
            # Verify customer exists
            cursor.execute("SELECT id FROM customers WHERE id = %s AND is_active = 1", (new_id,))
            if cursor.fetchone():
                return new_id
            else:
                raise ValueError(f"Customer with id {new_id} does not exist")

        # Prepare customer fields
        name = customer_data.get('name')
        phone = customer_data.get('phone')
        email = customer_data.get('email')
        address = customer_data.get('address')
        guest_pan = customer_data.get('guestPan')
        customer_type = customer_data.get('customer_type')
        outlet_guest_id = customer_data.get('outlet_guest_id')

        if existing_customer_id:
            # Update existing customer
            update_fields = []
            update_values = []

            if name is not None:
                update_fields.append("name = %s")
                update_values.append(name)
            if phone is not None:
                update_fields.append("phone = %s")
                update_values.append(phone)
            if email is not None:
                update_fields.append("email = %s")
                update_values.append(email)
            if address is not None:
                update_fields.append("address = %s")
                update_values.append(address)
            if guest_pan is not None:
                update_fields.append("guestPan = %s")
                update_values.append(guest_pan)
            if customer_type is not None:
                update_fields.append("customer_type = %s")
                update_values.append(customer_type)
            if outlet_guest_id is not None:
                update_fields.append("outlet_guest_id = %s")
                update_values.append(outlet_guest_id)

            if update_fields:
                query = f"UPDATE customers SET {', '.join(update_fields)} WHERE id = %s"
                update_values.append(existing_customer_id)
                cursor.execute(query, tuple(update_values))

            return existing_customer_id
        else:
            # Create new customer
            insert_query = """
                INSERT INTO customers
                (name, phone, email, address, guestPan, customer_type, outlet_guest_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                name, phone, email, address, guest_pan, customer_type, outlet_guest_id
            ))
            return cursor.lastrowid

class CompanyUpdate:
    """Helper class for company operations"""

    FIELD_MAP = {
        "company_name": "company_name",
        "outlet": "outlet",
        "contact_person": "contact_person",
        "address": "address",
        "phone": "phone",
        "email": "email",
        "pan_number": "pan_number",
        "company_type": "company_type",
        "source": "source",
        "outlet_company_id": "outlet_company_id",
    }

    @staticmethod
    def resolve(cursor, company_data, existing_company_id=None):
        """
        Returns the company_id to store on the reservation (None = no company).
        """
        # null -> unlink
        if company_data is None:
            return None

        if not isinstance(company_data, dict):
            raise ValueError("company must be an object or null")

        # link to an existing company
        if company_data.get("new_id") is not None:
            new_id = company_data["new_id"]
            cursor.execute(
                "SELECT id FROM companies WHERE id = %s AND status = 1", (new_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Company with id {new_id} does not exist")
            return row["id"]

        fields = {
            col: company_data[key]
            for key, col in CompanyUpdate.FIELD_MAP.items()
            if key in company_data
        }

        # update the company already linked to this reservation
        if existing_company_id:
            if fields:
                if "company_name" in fields and not str(fields["company_name"] or "").strip():
                    raise ValueError("company_name cannot be empty")
                if "phone" in fields:
                    if not str(fields["phone"] or "").strip():
                        raise ValueError("phone cannot be empty")
                    cursor.execute(
                        "SELECT id FROM companies WHERE phone = %s AND id <> %s",
                        (fields["phone"], existing_company_id),
                    )
                    if cursor.fetchone():
                        raise ValueError("Another company with this phone already exists")

                set_clause = ", ".join(f"{col} = %s" for col in fields)
                cursor.execute(
                    f"UPDATE companies SET {set_clause} WHERE id = %s",
                    list(fields.values()) + [existing_company_id],
                )
            return existing_company_id

        # no company linked yet -> create one (same rules as POST /companies)
        if not str(fields.get("company_name") or "").strip() or not str(fields.get("phone") or "").strip():
            raise ValueError("company_name and phone are required to create a company")

        cursor.execute("SELECT id FROM companies WHERE phone = %s", (fields["phone"],))
        if cursor.fetchone():
            raise ValueError("A company with this phone already exists")

        cols = ", ".join(fields.keys())
        placeholders = ", ".join(["%s"] * len(fields))
        cursor.execute(
            f"INSERT INTO companies ({cols}) VALUES ({placeholders})",
            list(fields.values()),
        )
        return cursor.lastrowid


# class ReservationUpdate:
#     """Helper class for reservation operations"""
#     @staticmethod
#     def update(cursor, reservation_id, reservation_data, guest_id=None,
#                update_company=False, company_id=None):
#         """
#         Update reservation details.
#         update_company=True writes company_id (None unlinks the company).
#         """
#         update_fields = []
#         update_values = []

#         # Map of field names to database columns
#         field_map = {
#             'outlet': 'outlet',
#             'Emp_ID': 'Emp_ID',
#             'Pay_Mode': 'Pay_Mode',
#             'Billing_Inst': 'Billing_Inst',
#             'Reservation_type': 'Reservation_type',
#             'designation': 'designation',
#             'Advance_Payment': 'Advance_Payment',
#             'Advance_Payment_Currency': 'Advance_Payment_Currency',
#             'Advance_Payment_Local': 'Advance_Payment_Local',
#             'Market_Seg': 'Market_Seg',
#             'business_Src': 'business_Src',
#             'Current_Status': 'Current_Status',
#             'reservation_outlet_id': 'reservation_outlet_id'
#         }

#         # Handle special fields
#         if 'Reservation_Date' in reservation_data:
#             update_fields.append("Reservation_Date = %s")
#             update_values.append(reservation_data['Reservation_Date'])

#         if 'Check_In' in reservation_data:
#             update_fields.append("Check_In = %s")
#             update_values.append(reservation_data['Check_In'])

#         if 'Check_Out' in reservation_data:
#             update_fields.append("Check_Out = %s")
#             update_values.append(reservation_data['Check_Out'])

#         # Handle Guest_ID if provided
#         if guest_id:
#             update_fields.append("Guest_ID = %s")
#             update_values.append(guest_id)

#         # Handle company (None unlinks it)
#         if update_company:
#             update_fields.append("company_id = %s")
#             update_values.append(company_id)

#         # Handle other fields
#         for key, column in field_map.items():
#             if key in reservation_data:
#                 update_fields.append(f"{column} = %s")
#                 update_values.append(reservation_data[key])

#         if update_fields:
#             query = f"UPDATE hotel_tblreservation SET {', '.join(update_fields)} WHERE id = %s"
#             update_values.append(reservation_id)
#             cursor.execute(query, tuple(update_values))
#             return cursor.rowcount > 0

#         return False


# class GuestReservationUpdate:
#     """Helper class for guest reservation operations"""
#     @staticmethod
#     def update(cursor, guest_reservation_id, guest_reservation_data):
#         """
#         Update guest reservation details
#         """
#         update_fields = []
#         update_values = []
        
#         # Map fields to database columns
#         field_map = {
#             'No_of_children': 'No_of_children',
#             'No_of_adults': 'No_of_adults',
#             'Likes': 'Likes',
#             'Dislikes': 'Dislikes',
#             'Guest_Notes': 'Guest_Notes',
#             'start_date': 'start_date',
#             'end_date': 'end_date'
#         }
        
#         for key, column in field_map.items():
#             if key in guest_reservation_data:
#                 update_fields.append(f"{column} = %s")
#                 update_values.append(guest_reservation_data[key])
        
#         if update_fields:
#             # update_fields.append("updated_at = NOW()")
#             query = f"UPDATE hotel_tblguestreservation SET {', '.join(update_fields)} WHERE id = %s"
#             update_values.append(guest_reservation_id)
#             cursor.execute(query, tuple(update_values))
#             return cursor.rowcount > 0
        
#         return False



# @app_file418.route("/tblguestreservationupdate/<int:guest_reservation_id>", methods=["PUT", "PATCH"])
# @cross_origin()
# def update_guest_reservation(guest_reservation_id):
#     """
#     Update guest reservation with nested reservation, customer and company data
#     Equivalent to Django's tblGuestReservationUpdateViewSet
#     """
#     try:
#         # Connect to DB
#         mydb = mysql.connector.connect(
#             host=os.getenv("host"),
#             user=os.getenv("user"),
#             password=os.getenv("password"),
#             database=os.getenv("database")
#         )
#         cursor = mydb.cursor(dictionary=True, buffered=True)

#         # -------- TOKEN AUTH --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400

#         try:
#             token = auth_header.split(" ")[1]
#         except:
#             return {"error": "Invalid Authorization header format."}, 400

#         if not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # Get JSON data
#         json_data = request.get_json()
#         if not json_data:
#             return {"error": "No data provided"}, 400

#         # Check if guest reservation exists
#         cursor.execute("""
#             SELECT g.*, r.Guest_ID, r.company_id, r.Current_Status,
#                    r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local
#             FROM hotel_tblguestreservation g
#             JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
#             WHERE g.id = %s AND g.is_active = 1
#         """, (guest_reservation_id,))

#         existing_guest_reservation = cursor.fetchone()

#         if not existing_guest_reservation:
#             mydb.close()
#             return {"error": "Guest reservation not found"}, 404

#         reservation_id = existing_guest_reservation['Reservation_ID']
#         current_guest_id = existing_guest_reservation['Guest_ID']
#         current_company_id = existing_guest_reservation['company_id']

#         # MySQL Connector/Python starts a transaction automatically
#         # (autocommit is False by default), so no explicit start_transaction().

#         try:
#             # 1. Handle Customer/Guest data if provided
#             reservation_data = json_data.get('Reservation_ID', {})
#             advance_error = normalize_advance_payment(reservation_data, existing_guest_reservation)
#             if advance_error:
#                 mydb.close()
#                 return {"error": advance_error}, 400
#             guest_data = reservation_data.get('Guest_ID', {}) if reservation_data else {}

#             new_guest_id = None
#             if guest_data:
#                 new_guest_id = CustomerUpdate.update_or_create(
#                     cursor,
#                     guest_data,
#                     existing_customer_id=current_guest_id
#                 )

#             # 1b. Handle Company (only touched when the "company" key is sent)
#             update_company = bool(reservation_data) and "company" in reservation_data
#             company_id_to_set = None
#             if update_company:
#                 # A billed reservation's credit journal points at the old party,
#                 # so the company can't change after checkout.
#                 if existing_guest_reservation['Current_Status'] == 'Checked Out':
#                     mydb.close()
#                     return {"error": "Company cannot be changed after checkout."}, 400

#                 company_id_to_set = CompanyUpdate.resolve(
#                     cursor,
#                     reservation_data["company"],
#                     existing_company_id=current_company_id,
#                 )

#             # 2. Handle Reservation update if provided
#             if reservation_data:
#                 ReservationUpdate.update(
#                     cursor,
#                     reservation_id,
#                     reservation_data,
#                     guest_id=new_guest_id,
#                     update_company=update_company,
#                     company_id=company_id_to_set,
#                 )

#             # 3. Handle Guest Reservation update
#             GuestReservationUpdate.update(cursor, guest_reservation_id, json_data)

#             # Commit transaction
#             mydb.commit()

#             # Fetch updated data to return
#             cursor.execute("""
#                 SELECT 
#                     g.*,
#                     JSON_OBJECT(
#                         'id', r.id,
#                         'outlet', r.outlet,
#                         'Emp_ID', r.Emp_ID,
#                         'Pay_Mode', r.Pay_Mode,
#                         'Billing_Inst', r.Billing_Inst,
#                         'Reservation_type', r.Reservation_type,
#                         'designation', r.designation,
#                         'Advance_Payment', r.Advance_Payment,
#                         'Advance_Payment_Currency', r.Advance_Payment_Currency,
#                         'Advance_Payment_Local', r.Advance_Payment_Local,
#                         'Market_Seg', r.Market_Seg,
#                         'business_Src', r.business_Src,
#                         'Current_Status', r.Current_Status,
#                         'reservation_outlet_id', r.reservation_outlet_id,
#                         'Reservation_Date', r.Reservation_Date,
#                         'Check_In', r.Check_In,
#                         'Check_Out', r.Check_Out,
#                         'company_id', r.company_id,
#                         'Guest_ID', JSON_OBJECT(
#                             'id', c.id,
#                             'name', c.name,
#                             'phone', c.phone,
#                             'email', c.email,
#                             'address', c.address,
#                             'guestPan', c.guestPan,
#                             'customer_type', c.customer_type,
#                             'outlet_guest_id', c.outlet_guest_id
#                         )
#                     ) as reservation_details
#                 FROM hotel_tblguestreservation g
#                 JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
#                 JOIN customers c ON r.Guest_ID = c.id
#                 WHERE g.id = %s
#             """, (guest_reservation_id,))

#             updated_data = cursor.fetchone()

#             # Parse JSON fields
#             if updated_data and updated_data.get('reservation_details'):
#                 updated_data['Reservation_ID'] = json.loads(updated_data['reservation_details'])
#                 del updated_data['reservation_details']

#             # Attach the linked company (None when the reservation has no company)
#             if updated_data and updated_data.get('Reservation_ID'):
#                 linked_company_id = updated_data['Reservation_ID'].get('company_id')
#                 company_obj = None
#                 if linked_company_id:
#                     cursor.execute("""
#                         SELECT id, company_name, outlet, contact_person, address, phone,
#                                email, pan_number, company_type, status, source
#                         FROM companies
#                         WHERE id = %s
#                     """, (linked_company_id,))
#                     company_obj = cursor.fetchone()
#                 updated_data['Reservation_ID']['company'] = company_obj

#             # Only mark as updated if the reservation was already synced
#             cursor.execute(
#                 """
#                 SELECT reservation_outlet_id 
#                 FROM hotel_tblreservation 
#                 WHERE id = %s
#                 """,
#                 (reservation_id,)
#             )
#             result = cursor.fetchone()

#             if result and result['reservation_outlet_id']:
#                 cursor.execute(
#                     """
#                     UPDATE hotel_tblreservation
#                     SET is_updated = TRUE, updated_at = NOW()
#                     WHERE id = %s
#                     """,
#                     (reservation_id,)
#                 )
#             mydb.commit()

#             mydb.close()

#             return jsonify({
#                 "message": "Guest reservation updated successfully",
#                 "data": updated_data
#             }), 200

#         except Exception as e:
#             # Rollback on error
#             mydb.rollback()
#             raise e

#     except ValueError as ve:
#         return {"error": str(ve)}, 400
#     except Exception as e:
#         return {"error": str(e)}, 500


class ReservationUpdate:
    """Helper class for reservation operations"""
    @staticmethod
    def update(cursor, reservation_id, reservation_data, guest_id=None,
               update_company=False, company_id=None):
        """
        Update reservation details.
        update_company=True writes company_id (None unlinks the company).
        """
        update_fields = []
        update_values = []

        # Map of field names to database columns
        field_map = {
            'outlet': 'outlet',
            'Emp_ID': 'Emp_ID',
            'Pay_Mode': 'Pay_Mode',
            'Billing_Inst': 'Billing_Inst',
            'Reservation_type': 'Reservation_type',
            'designation': 'designation',
            'Advance_Payment': 'Advance_Payment',
            'Advance_Payment_Currency': 'Advance_Payment_Currency',
            'Advance_Payment_Local': 'Advance_Payment_Local',
            'Market_Seg': 'Market_Seg',
            'business_Src': 'business_Src',
            'Current_Status': 'Current_Status',
            'reservation_outlet_id': 'reservation_outlet_id',
            'is_complimentary': 'is_complimentary'
        }

        # Handle special fields
        if 'Reservation_Date' in reservation_data:
            update_fields.append("Reservation_Date = %s")
            update_values.append(reservation_data['Reservation_Date'])

        if 'Check_In' in reservation_data:
            update_fields.append("Check_In = %s")
            update_values.append(reservation_data['Check_In'])

        if 'Check_Out' in reservation_data:
            update_fields.append("Check_Out = %s")
            update_values.append(reservation_data['Check_Out'])

        # Handle Guest_ID if provided
        if guest_id:
            update_fields.append("Guest_ID = %s")
            update_values.append(guest_id)

        # Handle company (None unlinks it)
        if update_company:
            update_fields.append("company_id = %s")
            update_values.append(company_id)

        # Handle other fields
        for key, column in field_map.items():
            if key in reservation_data:
                update_fields.append(f"{column} = %s")
                update_values.append(reservation_data[key])

        if update_fields:
            query = f"UPDATE hotel_tblreservation SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(reservation_id)
            cursor.execute(query, tuple(update_values))
            return cursor.rowcount > 0

        return False


class GuestReservationUpdate:
    """Helper class for guest reservation operations"""
    @staticmethod
    def update(cursor, guest_reservation_id, guest_reservation_data):
        """
        Update guest reservation details
        """
        update_fields = []
        update_values = []
        
        # Map fields to database columns
        field_map = {
            'No_of_children': 'No_of_children',
            'No_of_adults': 'No_of_adults',
            'Likes': 'Likes',
            'Dislikes': 'Dislikes',
            'Guest_Notes': 'Guest_Notes',
            'start_date': 'start_date',
            'end_date': 'end_date'
        }
        
        for key, column in field_map.items():
            if key in guest_reservation_data:
                update_fields.append(f"{column} = %s")
                update_values.append(guest_reservation_data[key])
        
        if update_fields:
            # update_fields.append("updated_at = NOW()")
            query = f"UPDATE hotel_tblguestreservation SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(guest_reservation_id)
            cursor.execute(query, tuple(update_values))
            return cursor.rowcount > 0
        
        return False

from root.flask_routes.hotel.reservation import _parse_bool_flag
@app_file418.route("/tblguestreservationupdate/<int:guest_reservation_id>", methods=["PUT", "PATCH"])
@cross_origin()
def update_guest_reservation(guest_reservation_id):
    """
    Update guest reservation with nested reservation, customer and company data
    Equivalent to Django's tblGuestReservationUpdateViewSet
    """
    try:
        # Connect to DB
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN AUTH --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400

        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Get JSON data
        json_data = request.get_json()
        if not json_data:
            return {"error": "No data provided"}, 400

        # Check if guest reservation exists
        cursor.execute("""
            SELECT g.*, r.Guest_ID, r.company_id, r.Current_Status,
                   r.Advance_Payment, r.Advance_Payment_Currency, r.Advance_Payment_Local
            FROM hotel_tblguestreservation g
            JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
            WHERE g.id = %s AND g.is_active = 1
        """, (guest_reservation_id,))

        existing_guest_reservation = cursor.fetchone()

        if not existing_guest_reservation:
            mydb.close()
            return {"error": "Guest reservation not found"}, 404

        reservation_id = existing_guest_reservation['Reservation_ID']
        current_guest_id = existing_guest_reservation['Guest_ID']
        current_company_id = existing_guest_reservation['company_id']

        # MySQL Connector/Python starts a transaction automatically
        # (autocommit is False by default), so no explicit start_transaction().

        try:
            # 1. Handle Customer/Guest data if provided
            reservation_data = json_data.get('Reservation_ID', {})
            advance_error = normalize_advance_payment(reservation_data, existing_guest_reservation)
            if advance_error:
                mydb.close()
                return {"error": advance_error}, 400

            # ---- is_complimentary: normalise to 0/1 ----
            if reservation_data and "is_complimentary" in reservation_data:
                # a billed reservation can't switch between complimentary and paid
                if existing_guest_reservation['Current_Status'] == 'Checked Out':
                    mydb.close()
                    return {"error": "is_complimentary cannot be changed after checkout."}, 400

                try:
                    comp_flag = _parse_bool_flag(reservation_data["is_complimentary"], default=None)
                except ValueError:
                    mydb.close()
                    return {"error": "is_complimentary must be true or false."}, 400
                if comp_flag is None:
                    mydb.close()
                    return {"error": "is_complimentary must be true or false."}, 400

                reservation_data["is_complimentary"] = 1 if comp_flag else 0

            guest_data = reservation_data.get('Guest_ID', {}) if reservation_data else {}

            new_guest_id = None
            if guest_data:
                new_guest_id = CustomerUpdate.update_or_create(
                    cursor,
                    guest_data,
                    existing_customer_id=current_guest_id
                )

            # 1b. Handle Company (only touched when the "company" key is sent)
            update_company = bool(reservation_data) and "company" in reservation_data
            company_id_to_set = None
            if update_company:
                # A billed reservation's credit journal points at the old party,
                # so the company can't change after checkout.
                if existing_guest_reservation['Current_Status'] == 'Checked Out':
                    mydb.close()
                    return {"error": "Company cannot be changed after checkout."}, 400

                company_id_to_set = CompanyUpdate.resolve(
                    cursor,
                    reservation_data["company"],
                    existing_company_id=current_company_id,
                )

            # 2. Handle Reservation update if provided
            if reservation_data:
                ReservationUpdate.update(
                    cursor,
                    reservation_id,
                    reservation_data,
                    guest_id=new_guest_id,
                    update_company=update_company,
                    company_id=company_id_to_set,
                )

            # 2b. Keep in-house guests in step with the reservation's complimentary flag
            if reservation_data and "is_complimentary" in reservation_data:
                cursor.execute("""
                    UPDATE hotel_tblinhouse_guests
                    SET is_complimentary = %s
                    WHERE reservation_id = %s AND is_active = 1
                """, (reservation_data["is_complimentary"], reservation_id))

            # 3. Handle Guest Reservation update
            GuestReservationUpdate.update(cursor, guest_reservation_id, json_data)

            # Commit transaction
            mydb.commit()

            # Fetch updated data to return
            cursor.execute("""
                SELECT 
                    g.*,
                    JSON_OBJECT(
                        'id', r.id,
                        'outlet', r.outlet,
                        'Emp_ID', r.Emp_ID,
                        'Pay_Mode', r.Pay_Mode,
                        'Billing_Inst', r.Billing_Inst,
                        'Reservation_type', r.Reservation_type,
                        'designation', r.designation,
                        'Advance_Payment', r.Advance_Payment,
                        'Advance_Payment_Currency', r.Advance_Payment_Currency,
                        'Advance_Payment_Local', r.Advance_Payment_Local,
                        'Market_Seg', r.Market_Seg,
                        'business_Src', r.business_Src,
                        'Current_Status', r.Current_Status,
                        'reservation_outlet_id', r.reservation_outlet_id,
                        'Reservation_Date', r.Reservation_Date,
                        'Check_In', r.Check_In,
                        'Check_Out', r.Check_Out,
                        'company_id', r.company_id,
                        'Guest_ID', JSON_OBJECT(
                            'id', c.id,
                            'name', c.name,
                            'phone', c.phone,
                            'email', c.email,
                            'address', c.address,
                            'guestPan', c.guestPan,
                            'customer_type', c.customer_type,
                            'outlet_guest_id', c.outlet_guest_id
                        )
                    ) as reservation_details
                FROM hotel_tblguestreservation g
                JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
                JOIN customers c ON r.Guest_ID = c.id
                WHERE g.id = %s
            """, (guest_reservation_id,))

            updated_data = cursor.fetchone()

            # Parse JSON fields
            if updated_data and updated_data.get('reservation_details'):
                updated_data['Reservation_ID'] = json.loads(updated_data['reservation_details'])
                del updated_data['reservation_details']

            # Attach the linked company (None when the reservation has no company)
            if updated_data and updated_data.get('Reservation_ID'):
                linked_company_id = updated_data['Reservation_ID'].get('company_id')
                company_obj = None
                if linked_company_id:
                    cursor.execute("""
                        SELECT id, company_name, outlet, contact_person, address, phone,
                               email, pan_number, company_type, status, source
                        FROM companies
                        WHERE id = %s
                    """, (linked_company_id,))
                    company_obj = cursor.fetchone()
                updated_data['Reservation_ID']['company'] = company_obj

            # Only mark as updated if the reservation was already synced
            cursor.execute(
                """
                SELECT reservation_outlet_id 
                FROM hotel_tblreservation 
                WHERE id = %s
                """,
                (reservation_id,)
            )
            result = cursor.fetchone()

            if result and result['reservation_outlet_id']:
                cursor.execute(
                    """
                    UPDATE hotel_tblreservation
                    SET is_updated = TRUE, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (reservation_id,)
                )
            mydb.commit()

            mydb.close()

            return jsonify({
                "message": "Guest reservation updated successfully",
                "data": updated_data
            }), 200

        except Exception as e:
            # Rollback on error
            mydb.rollback()
            raise e

    except ValueError as ve:
        return {"error": str(ve)}, 400
    except Exception as e:
        return {"error": str(e)}, 500


@app_file418.route("/tblguestreservation/bulk-update", methods=["POST"])
@cross_origin()
def bulk_update_guest_reservations():
    """
    Bulk update multiple guest reservations
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN AUTH --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        
        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        json_data = request.get_json()
        if not json_data or 'updates' not in json_data:
            return {"error": "No updates provided"}, 400

        updates = json_data['updates']
        results = []
        errors = []

        # Start transaction
        mydb.start_transaction()

        try:
            for update_item in updates:
                guest_reservation_id = update_item.get('id')
                if not guest_reservation_id:
                    errors.append({"error": "Missing guest reservation ID", "data": update_item})
                    continue

                try:
                    # Check if exists
                    cursor.execute("""
                        SELECT g.*, r.Guest_ID 
                        FROM hotel_tblguestreservation g
                        JOIN hotel_tblreservation r ON g.Reservation_ID = r.id
                        WHERE g.id = %s AND g.is_active = 1
                    """, (guest_reservation_id,))
                    
                    existing = cursor.fetchone()
                    
                    if not existing:
                        errors.append({"id": guest_reservation_id, "error": "Guest reservation not found"})
                        continue

                    # Process update (similar logic as single update)
                    reservation_data = update_item.get('Reservation_ID', {})
                    guest_data = reservation_data.get('Guest_ID', {}) if reservation_data else {}
                    
                    # Update customer if needed
                    if guest_data:
                        CustomerUpdate.update_or_create(
                            cursor, 
                            guest_data, 
                            existing_customer_id=existing['Guest_ID']
                        )

                    # Update reservation
                    if reservation_data:
                        ReservationUpdate.update(
                            cursor, 
                            existing['Reservation_ID'], 
                            reservation_data
                        )

                    # Update guest reservation
                    GuestReservationUpdate.update(cursor, guest_reservation_id, update_item)

                    results.append({
                        "id": guest_reservation_id,
                        "status": "updated"
                    })

                except Exception as e:
                    errors.append({
                        "id": guest_reservation_id,
                        "error": str(e)
                    })

            # Commit if no errors
            if not errors:
                mydb.commit()
            else:
                mydb.rollback()
                raise Exception("Errors occurred in bulk update")

            mydb.close()

            return jsonify({
                "message": f"Successfully updated {len(results)} reservations",
                "updated": results,
                "errors": errors if errors else None
            }), 200 if results else 400

        except Exception as e:
            mydb.rollback()
            raise e

    except Exception as e:
        return {"error": str(e)}, 500


@app_file418.route("/tblguestreservation/partial-update/<int:guest_reservation_id>", methods=["PATCH"])
@cross_origin()
def partial_update_guest_reservation(guest_reservation_id):
    """
    Partial update endpoint (PATCH) for guest reservations
    """
    return update_guest_reservation(guest_reservation_id)


# Additional endpoint for updating fitrates
@app_file418.route("/tblguestreservation/<int:guest_reservation_id>/fitrates", methods=["PUT"])
@cross_origin()
def update_guest_reservation_fitrates(guest_reservation_id):
    """
    Update fitrates for a guest reservation
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        # -------- TOKEN AUTH --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        
        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        json_data = request.get_json()
        fitrates = json_data.get('fitrates', [])

        # Get reservation ID from guest reservation
        cursor.execute("""
            SELECT Reservation_ID 
            FROM hotel_tblguestreservation 
            WHERE id = %s AND is_active = 1
        """, (guest_reservation_id,))
        
        result = cursor.fetchone()
        if not result:
            mydb.close()
            return {"error": "Guest reservation not found"}, 404

        reservation_id = result['Reservation_ID']

        # Start transaction
        mydb.start_transaction()

        try:
            # Soft delete existing fitrates
            cursor.execute("""
                UPDATE hotel_tblfitrate 
                SET is_active = 0, updated_at = NOW() 
                WHERE reservationID = %s
            """, (reservation_id,))

            # Insert new fitrates
            for fr in fitrates:
                insert_query = """
                    INSERT INTO hotel_tblfitrate 
                    (rateID, mealID, reservationID, quantity, created_at, updated_at, is_active) 
                    VALUES (%s, %s, %s, %s, NOW(), NOW(), 1)
                """
                cursor.execute(insert_query, (
                    fr.get('rateID'),
                    fr.get('mealID'),
                    reservation_id,
                    fr.get('quantity', 1)
                ))

            mydb.commit()

            # Fetch updated fitrates
            cursor.execute("""
                SELECT fr.*, 
                       rt.room_name, rt.rate as room_rate,
                       mp.mp, mp.rate as meal_rate
                FROM hotel_tblfitrate fr
                LEFT JOIN hotel_tblrates rt ON fr.rateID = rt.id
                LEFT JOIN hotel_tblmeal_price mp ON fr.mealID = mp.id
                WHERE fr.reservationID = %s AND fr.is_active = 1
            """, (reservation_id,))
            
            updated_fitrates = cursor.fetchall()

            mydb.close()

            return jsonify({
                "message": "Fitrates updated successfully",
                "fitrates": updated_fitrates
            }), 200

        except Exception as e:
            mydb.rollback()
            raise e

    except Exception as e:
        return {"error": str(e)}, 500


@app_file418.route("/update-reservation-v2/", methods=["PUT", "PATCH", "POST"])
@cross_origin()
def update_reservation_v2():
    """
    Update reservation by deleting all related data and recreating with new data
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        json_data = request.get_json() or {}
        
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Extract data from request
        reservation_data = json_data.get("tblReservation", {})
        guest_reservation_data = json_data.get("tblGuestReservation", {})
        fit_rate_data = json_data.get("tblFITRate", [])
        reservation_details_data = json_data.get("checkin_list", [])
        guest_info = reservation_data.pop("guest_info", None)
        company_info = reservation_data.pop("company_info", None)
        company_id = None

        # Validate required data
        if not reservation_data:
            return {"error": "Missing 'tblReservation' data"}, 400
        if not guest_reservation_data:
            return {"error": "Missing 'tblGuestReservation' data"}, 400
        if not fit_rate_data:
            return {"error": "Missing 'tblFITRate' data"}, 400
        if not guest_info or not guest_info.get("outlet_guest_id"):
            return {"error": "guest_info with outlet_guest_id is required"}, 400
        
        reservation_outlet_id = reservation_data.get('reservation_outlet_id')

        if not reservation_outlet_id:
            return {"error": "reservation outlet id is required"}, 400


        # Check if reservation exists
        cursor.execute("SELECT id FROM hotel_tblreservation WHERE reservation_outlet_id = %s AND is_active = 1", (reservation_outlet_id,))
        existing_reservation = cursor.fetchone()

        reservation_id = existing_reservation["id"]

        print("existing reservation", reservation_id)
        
        if not existing_reservation:

            print("No existing rservation")
            mydb.close()    
            return {"error": "Reservation not found"}, 404

        # # Start transaction
        # mydb.start_transaction()

        try:
            from datetime import datetime
            now_datetime = datetime.now()
            now_date = now_datetime.date()

            # -----------------------
            # 1️⃣ Handle Customer (Create or Update)
            # -----------------------
            outlet_guest_id = guest_info.get("outlet_guest_id")
            
            cursor.execute("SELECT * FROM customers WHERE outlet_guest_id=%s LIMIT 1", (outlet_guest_id,))
            customer = cursor.fetchone()

            if not customer:
                cursor.execute("""
                    INSERT INTO customers (name, phone, email, address, outlet_guest_id, customer_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    guest_info.get("name"),
                    guest_info.get("contact_number"),
                    guest_info.get("email"),
                    guest_info.get("address"),
                    outlet_guest_id,
                    guest_info.get("type")
                ))
                customer_id = cursor.lastrowid
            else:
                # Update existing customer
                cursor.execute("""
                    UPDATE customers 
                    SET name = %s, phone = %s, email = %s, address = %s, customer_type = %s
                    WHERE id = %s
                """, (
                    guest_info.get("name"),
                    guest_info.get("contact_number"),
                    guest_info.get("email"),
                    guest_info.get("address"),
                    guest_info.get("type"),
                    customer["id"]
                ))
                customer_id = customer["id"]

            # -----------------------
            # 2️⃣ Hard Delete all related data for this reservation
            # -----------------------
            
            # Delete FIT rates
            cursor.execute("DELETE FROM hotel_tblfitrate WHERE reservationID = %s", (reservation_id,))
            
            # Delete reservation details (room assignments)
            cursor.execute("DELETE FROM hotel_tblreservation_details WHERE Reservation_ID = %s", (reservation_id,))
            
            # Delete guest reservation
            cursor.execute("DELETE FROM hotel_tblguestreservation WHERE Reservation_ID = %s", (reservation_id,))
            
            # Delete the main reservation
            cursor.execute("DELETE FROM hotel_tblreservation WHERE id = %s", (reservation_id,))

            # -----------------------
            # 3️⃣ Insert New Reservation
            # -----------------------
            reservation_data["Guest_ID"] = customer_id

            if company_info and company_info.get("outlet_company_id"):
                outlet_company_id = company_info.get("outlet_company_id")

                cursor.execute("""
                    SELECT * FROM companies 
                    WHERE outlet_company_id=%s 
                    LIMIT 1
                """, (outlet_company_id,))
                company = cursor.fetchone()

                if not company:
                    cursor.execute("""
                        INSERT INTO companies (
                            company_name,
                            phone,
                            email,
                            address,
                            pan_number,
                            outlet_company_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        company_info.get("company_name"),
                        company_info.get("phone"),
                        company_info.get("email"),
                        company_info.get("address"),
                        company_info.get("pan_number"),
                        outlet_company_id
                    ))
                    company_id = cursor.lastrowid
                else:
                    company_id = company["id"]

                # attach to reservation
                reservation_data["company_id"] = company_id
            else:
                # attach to reservation
                reservation_data["company_id"] = None    
            
            reservation_fields = (
                "outlet", "Emp_ID", "Pay_Mode", "Billing_Inst", "Reservation_type", "designation",
                "Advance_Payment", "Guest_ID", "Reservation_Date", "Market_Seg", "business_Src",
                "Current_Status", "Check_In", "Check_Out", "reservation_outlet_id", "company_id"
            )

            reservation_values = tuple(
                (
                    None if f == "Emp_ID" and reservation_data.get(f) == ""
                    else reservation_data.get(f)
                ) if f not in ["Current_Status", "Reservation_Date", "Check_In"]
                else reservation_data.get(f) or (
                    "Reserved" if f == "Current_Status"
                    else now_datetime if f == "Check_In"
                    else now_date
                )
                for f in reservation_fields
            )

            placeholders = ", ".join(["%s"] * len(reservation_fields))
            cursor.execute(f"""
                INSERT INTO hotel_tblreservation ({', '.join(reservation_fields)}, created_at)
                VALUES ({placeholders}, %s)
            """, reservation_values + (now_datetime,))
            new_reservation_id = cursor.lastrowid

            # -----------------------
            # 4️⃣ Insert New Guest Reservation
            # -----------------------
            guest_fields = (
                "Reservation_ID", "No_of_children", "No_of_adults", "Likes", "Dislikes",
                "Guest_Notes", "start_date", "end_date"
            )
            guest_values = (
                new_reservation_id,
                guest_reservation_data.get("No_of_children"),
                guest_reservation_data.get("No_of_adults"),
                guest_reservation_data.get("Likes"),
                guest_reservation_data.get("Dislikes"),
                guest_reservation_data.get("Guest_Notes"),
                guest_reservation_data.get("start_date"),
                guest_reservation_data.get("end_date")
            )
            placeholders = ", ".join(["%s"] * len(guest_fields))
            cursor.execute(f"""
                INSERT INTO hotel_tblguestreservation ({', '.join(guest_fields)}, created_at)
                VALUES ({placeholders}, %s)
            """, guest_values + (now_datetime,))

            # -----------------------
            # 5️⃣ Insert New FIT Rates (with automatic rate/meal creation)
            # -----------------------
            for item in fit_rate_data:
                outlet_rate_id = item.get("rateID")
                outlet_meal_id = item.get("mealID")
                quantity = item.get("quantity", 0)
                
                # Get rate details and meal details from the request
                rate_details = item.get("rate_details", {})
                meal_details = item.get("meal_details", {})
                
                # ---------- Handle Rate ----------
                rate_id = None
                
                # First, check if rate exists by outlet_rate_id
                if outlet_rate_id:
                    cursor.execute("SELECT id FROM hotel_tblrates WHERE outlet_rate_id=%s LIMIT 1", (outlet_rate_id,))
                    rate_obj = cursor.fetchone()
                    if rate_obj:
                        rate_id = rate_obj["id"]
                
                # If rate doesn't exist, create it with the provided details
                if not rate_id and rate_details:
                    rate_fields = []
                    rate_values = []
                    
                    # Map frontend fields to database fields
                    field_mapping = {
                        "room_name": rate_details.get("room_name"),
                        "room_type": rate_details.get("room_type"),
                        "rate": rate_details.get("rate"),
                        "currency": rate_details.get("currency"),
                        "outlet_rate_id": outlet_rate_id,
                    }
                    
                    # Add optional fields if they exist
                    if rate_details.get("meal_price_id"):
                        field_mapping["meal_price_id"] = rate_details.get("meal_price_id")
                    if rate_details.get("occupancy"):
                        field_mapping["occupancy"] = rate_details.get("occupancy")
                    
                    # Build INSERT query
                    for field, value in field_mapping.items():
                        if value is not None:
                            rate_fields.append(field)
                            rate_values.append(value)
                    
                    # Add created_at and is_active
                    rate_fields.append("created_at")
                    rate_values.append(now_datetime)
                    rate_fields.append("is_active")
                    rate_values.append(True)
                    
                    # Insert new rate
                    placeholders = ", ".join(["%s"] * len(rate_fields))
                    cursor.execute(f"""
                        INSERT INTO hotel_tblrates ({', '.join(rate_fields)})
                        VALUES ({placeholders})
                    """, rate_values)
                    rate_id = cursor.lastrowid
                
                if not rate_id:
                    raise Exception(f"Rate not found and no rate details provided for outlet_rate_id {outlet_rate_id}")
                
                # ---------- Handle Meal ----------
                meal_id = None
                
                # First, check if meal exists by outlet_rate_id
                if outlet_meal_id:
                    cursor.execute("SELECT id FROM hotel_tblmeal_price WHERE outlet_rate_id=%s LIMIT 1", (outlet_meal_id,))
                    meal_obj = cursor.fetchone()
                    if meal_obj:
                        meal_id = meal_obj["id"]
                
                # If meal doesn't exist, create it with the provided details
                if not meal_id and meal_details:
                    meal_fields = []
                    meal_values = []
                    
                    # Map frontend fields to database fields
                    meal_field_mapping = {
                        "mp": meal_details.get("mp"),
                        "rate": meal_details.get("rate"),
                        "currency": meal_details.get("currency"),
                        "outlet_rate_id": outlet_meal_id,
                    }
                    
                    # Build INSERT query
                    for field, value in meal_field_mapping.items():
                        if value is not None:
                            meal_fields.append(field)
                            meal_values.append(value)
                    
                    # Add created_at and is_active
                    meal_fields.append("created_at")
                    meal_values.append(now_datetime)
                    meal_fields.append("is_active")
                    meal_values.append(True)
                    
                    # Insert new meal
                    placeholders = ", ".join(["%s"] * len(meal_fields))
                    cursor.execute(f"""
                        INSERT INTO hotel_tblmeal_price ({', '.join(meal_fields)})
                        VALUES ({placeholders})
                    """, meal_values)
                    meal_id = cursor.lastrowid
                
                # Insert FIT Rate
                cursor.execute("""
                    INSERT INTO hotel_tblfitrate (rateID, mealID, reservationID, quantity, is_active, created_at)
                    VALUES (%s, %s, %s, %s, 1, %s)
                """, (rate_id, meal_id, new_reservation_id, quantity, now_datetime))

            # -----------------------
            # 6️⃣ Insert New Reservation Details (Room Assignments with auto-creation)
            # -----------------------
            for detail in reservation_details_data:
                outlet_room_id = detail.get("room_id")
                # room_id = detail.get("room_id")
                is_current = detail.get("is_current", True)
                
                # Get room details if creation is needed
                room_details = detail.get("room_details", {})
                
                # # If room_id is provided directly, use it
                # if room_id:
                #     # Verify room exists
                #     cursor.execute("SELECT id FROM hotel_tblrooms WHERE id = %s AND is_active = 1", (room_id,))
                #     room = cursor.fetchone()
                #     if not room:
                #         raise Exception(f"Room with id {room_id} not found")
                #     final_room_id = room_id
                
                # If outlet_room_id is provided, try to find existing room
                if outlet_room_id:
                    cursor.execute("SELECT id FROM hotel_tblrooms WHERE outlet_room_id = %s AND is_active = 1", (outlet_room_id,))
                    room = cursor.fetchone()
                    
                    if room:
                        final_room_id = room["id"]
                    else:
                        # Create new room with provided details
                        if not room_details:
                            raise Exception(f"Room not found for outlet_room_id {outlet_room_id} and no room_details provided")
                        
                        room_fields = []
                        room_values = []
                        
                        # Map frontend fields to database fields
                        room_field_mapping = {
                            "outlet": room_details.get("outlet") or reservation_data.get("outlet"),
                            "room_no": room_details.get("room_no"),
                            "room_state": room_details.get("room_state", "Vacant"),
                            "phone_no": room_details.get("phone_no"),
                            "preference": room_details.get("preference"),
                            "room_view": room_details.get("room_view"),
                            "room_type": room_details.get("room_type"),
                            "room_notes": room_details.get("room_notes"),
                            "outlet_room_id": outlet_room_id,
                        }
                        
                        # Build INSERT query
                        for field, value in room_field_mapping.items():
                            if value is not None:
                                room_fields.append(field)
                                room_values.append(value)
                        
                        # Add created_at and is_active
                        room_fields.append("created_at")
                        room_values.append(now_datetime)
                        room_fields.append("is_active")
                        room_values.append(True)
                        
                        # Insert new room
                        placeholders = ", ".join(["%s"] * len(room_fields))
                        cursor.execute(f"""
                            INSERT INTO hotel_tblrooms ({', '.join(room_fields)})
                            VALUES ({placeholders})
                        """, room_values)
                        final_room_id = cursor.lastrowid
                
                else:
                    raise Exception("Either room_id or outlet_room_id must be provided for reservation detail")
                
                # Insert reservation detail
                cursor.execute("""
                    INSERT INTO hotel_tblreservation_details (Reservation_ID, room_id, is_current, created_at, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                """, (new_reservation_id, final_room_id, is_current, now_datetime))

            # Commit transaction
            mydb.commit()
            mydb.close()

            return {
                "message": f"Reservation updated successfully",
                "old_reservation_id": reservation_id,
                "new_reservation_id": new_reservation_id
            }, 200

        except Exception as e:
            # Rollback on error
            mydb.rollback()
            raise e

    except Exception as e:
        return {"error": str(e)}, 400
    
@app_file418.route("/update-reservation-flag/", methods=["PUT", "PATCH", "POST"])
@cross_origin()
def update_reservation_flag():
    """
    Update reservation's is_updated flag to false based on reservation_outlet_id
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        json_data = request.get_json() or {}
        
        # -------- TOKEN FROM HEADER --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400

        try:
            token = auth_header.split(" ")[1]
        except:
            return {"error": "Invalid Authorization header format."}, 400
        
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # Extract reservation_outlet_id from request
        reservation_outlet_id = json_data.get('reservation_outlet_id')
        
        if not reservation_outlet_id:
            return {"error": "reservation_outlet_id is required"}, 400

        # Check if reservation exists and is active
        cursor.execute("""
            SELECT id, is_updated, is_active 
            FROM hotel_tblreservation 
            WHERE reservation_outlet_id = %s AND is_active = 1
        """, (reservation_outlet_id,))
        
        existing_reservation = cursor.fetchone()

        if not existing_reservation:
            mydb.close()    
            return {"error": "Reservation not found or inactive"}, 404

        # Update the is_updated flag to false
        cursor.execute("""
            UPDATE hotel_tblreservation 
            SET is_updated = 0, updated_at = NOW() 
            WHERE reservation_outlet_id = %s AND is_active = 1
        """, (reservation_outlet_id,))

        # Check if update was successful
        if cursor.rowcount == 0:
            mydb.close()
            return {"error": "Failed to update reservation flag"}, 400

        # Commit the transaction
        mydb.commit()

        # Fetch the updated reservation to return in response
        cursor.execute("""
            SELECT id, reservation_outlet_id, is_updated, updated_at 
            FROM hotel_tblreservation 
            WHERE reservation_outlet_id = %s AND is_active = 1
        """, (reservation_outlet_id,))
        
        updated_reservation = cursor.fetchone()
        
        mydb.close()

        return {
            "message": "Reservation flag updated successfully",
            "data": updated_reservation,
            "success": True
        }, 200

    except mysql.connector.Error as e:
        # Handle database errors
        if mydb:
            mydb.rollback()
            mydb.close()
        return {"error": f"Database error: {str(e)}"}, 500
    
    except Exception as e:
        # Handle other exceptions
        if mydb:
            mydb.rollback()
            mydb.close()
        return {"error": str(e)}, 400