# # from decimal import Decimal
# # import os, requests


# # def post_hotelbill_and_create_journal(data, bill_id):
# #     print("inside hotel bill journal function")
# #     try:
# #         total = round(Decimal(str(data.get("Total", 0))), 2)
# #         vat = round(Decimal(str(data.get("VAT", 0))), 2)
# #         discount_amt = round(Decimal(str(data.get("DiscountAmt", 0))), 2)
# #         payment_mode = data.get("PaymentMode")
# #         bill_no = data.get("BillNo")
# #         date_str = data.get("Date")
# #         outlet = data.get("Outlet_Name")
# #         employee = data.get("Employee")
# #         billprinttime = data["billPrintTime"]

# #         # Room + mealplan revenue combine into a single "Sales" credit,
# #         # same treatment as the order-system's sale_amount = total - vat.
# #         sale_amount = total - vat

# #         accounting_url = os.getenv("accounting_url")
# #         ledger_api_url = accounting_url + "api/get-ledgers"
# #         ledger_response = requests.get(ledger_api_url)
# #         ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

# #         debit_ledgers, debit_particulars, debit_amounts = [], [], []
# #         credit_ledgers, credit_particulars, credit_amounts = [], [], []

# #         # -------- LEDGER NAME LOOKUP (normalized, case/space-insensitive) --------
# #         PAYMENT_LEDGER_MAP = {
# #             "cash": "Cash-In-Hand",
# #             "card": "Card Transactions",
# #             "mobile": "Mobile Payments",
# #         }

# #         def normalize_mode(mode):
# #             return (mode or "").strip().lower().replace(" ", "")

# #         if payment_mode and normalize_mode(payment_mode) == "split":
# #             split_payments = data.get("SplitPaymentDetailsList", [])
# #             if not split_payments:
# #                 raise ValueError("PaymentMode is 'Split' but SplitPaymentDetailsList is empty")

# #             for split_payment in split_payments:
# #                 split_mode_key = normalize_mode(split_payment.get("paymentMode"))
# #                 debit_ledger_name = PAYMENT_LEDGER_MAP.get(split_mode_key)

# #                 if not debit_ledger_name:
# #                     raise ValueError(f"Unhandled split payment mode for hotel bill: {split_payment.get('paymentMode')}")

# #                 debit_ledger_id = ledgers.get(debit_ledger_name)
# #                 if not debit_ledger_id:
# #                     raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")

# #                 debit_ledgers.append(debit_ledger_id)
# #                 debit_particulars.append(f"Split payment for hotel bill no: {bill_no}")
# #                 debit_amounts.append(round(Decimal(str(split_payment.get("paymentAmount", 0))), 2))

# #         else:
# #             debit_ledger_name = PAYMENT_LEDGER_MAP.get(normalize_mode(payment_mode))
# #             if not debit_ledger_name:
# #                 raise ValueError(f"Unhandled payment mode for hotel bill: {payment_mode}")

# #             debit_ledger_id = ledgers.get(debit_ledger_name)
# #             if not debit_ledger_id:
# #                 raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")

# #             debit_ledgers.append(debit_ledger_id)
# #             debit_particulars.append(f"Hotel bill payment for bill no: {bill_no}")
# #             debit_amounts.append(total)

# #         if sale_amount > 0:
# #             credit_ledgers.append(ledgers["Sales"])
# #             credit_particulars.append("Sales")
# #             credit_amounts.append(sale_amount)

# #         if vat > 0:
# #             credit_ledgers.append(ledgers["VAT Payable"])
# #             credit_particulars.append("VAT Payable")
# #             credit_amounts.append(vat)

# #         if discount_amt > 0:
# #             credit_ledgers.append(ledgers["Discount Sales"])
# #             credit_particulars.append("Discount Sales")
# #             credit_amounts.append(discount_amt)
# #             debit_ledgers.append(ledgers["Discount Expenses"])
# #             debit_particulars.append("Discount Expenses")
# #             debit_amounts.append(discount_amt)

# #         journal_entry_data = {
# #             "outlet_name": outlet,
# #             "bill_id": bill_no,
# #             "datetime": date_str,
# #             "user": employee,
# #             "debit_ledgers": debit_ledgers,
# #             "debit_particulars": debit_particulars,
# #             "debit_amounts": [str(a) for a in debit_amounts],
# #             "credit_ledgers": credit_ledgers,
# #             "credit_particulars": credit_particulars,
# #             "credit_amounts": [str(a) for a in credit_amounts],
# #             "billPrintTime" : billprinttime

# #         }

# #         accounting_token = os.getenv("accounting_token")
# #         journal_entry_api_url = accounting_url + "api/create_journal_entry/"
# #         headers = {"Authorization": f"Bearer {accounting_token}", "Content-Type": "application/json"}

# #         print(journal_entry_data)
# #         response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

# #         if response.status_code == 201:
# #             print({"message": "Hotel bill journal entry created successfully"})
# #         else:
# #             print({"error": str(response.json())})

# #     except Exception as error:
# #         print({"error": str(error)})



# # import requests
# # from decimal import Decimal
# # from datetime import datetime
# # import os
# # def post_hotelbill_and_create_journal_for_creditbills(data, bill_id):
# #     print("inside function")
# #     try:
# #         print("inside try")
# #         print(data)
# #         # Extract relevant data from request
# #         total = round(Decimal(data["Total"]), 2)
# #         vat = round(Decimal(data["VAT"]), 2)
# #         discount_amt = round(Decimal(data.get("DiscountAmt")), 2)
# #         payment_mode = data["PaymentMode"]
# #         bill_no = data["BillNo"]
# #         date_str = data["Date"]
# #         employee = data["Employee"]
# #         outlet = data["Outlet_Name"]
# #         # Convert date to required format
# #         formatted_date = date_str
# #         billprinttime = data["billPrintTime"]

# #         # Get ledger details from API
# #         accounting_url = os.getenv("accounting_url")


# #         ledger_api_url = accounting_url + "api/get-ledgers"
# #         ledger_response = requests.get(ledger_api_url)
# #         ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}
# #         # Calculate ledger-specific values
# #         sale_amount = total - vat 

# #         # Debit Side
# #         debit_ledgers = []
# #         debit_ledger_names = []
# #         debit_particulars = []
# #         debit_amounts = []


# #         if payment_mode != "Complimentary" or payment_mode != "Non Chargeable":
# #             if payment_mode == "Split":
# #                 for split_payment in data.get("SplitPaymentDetailsList", []):
# #                     if split_payment["paymentMode"] == "Cash":
# #                         payment_ledger_id = ledgers.get("Cash-In-Hand")
# #                         payment_ledger_name = "Cash-In-Hand"
# #                     if split_payment["paymentMode"] == "Credit Card":
# #                         payment_ledger_id = ledgers.get("Card Transactions")
# #                         payment_ledger_name = "Card Transactions"

# #                     if split_payment["paymentMode"] == "Mobile Payment":
# #                         payment_ledger_id = ledgers.get("Mobile Payments")
# #                         payment_ledger_name = "Mobile Payments"

# #                     # payment_ledger_name = split_payment["paymentMode"] 
# #                     # payment_ledger_id = ledgers.get(payment_ledger_name)
# #                     if not payment_ledger_id:
# #                         raise ValueError(f"Invalid payment ledger name: {payment_ledger_name}")

# #                     debit_ledgers.append(payment_ledger_id)
# #                     debit_particulars.append(f"Split payment from bill no: {bill_no}")
# #                     debit_amounts.append(Decimal(split_payment["paymentAmount"]))
# #             else:
# #                 # if payment_mode == "Cash":
# #                 #     debit_ledger_name = "Cash-In-Hand"  
# #                 # if payment_mode == "Credit Card":
# #                 #     debit_ledger_name = "Card Transactions"  
# #                 # if payment_mode == "Mobile Payment":
# #                 #     debit_ledger_name = "Mobile Payments"  
# #                 # debit_ledger_id = ledgers.get(debit_ledger_name)
# #                 debit_ledger_id = data.get("guestID", "1")
# #                 print(debit_ledger_id)
# #                 # if not debit_ledger_id:
# #                 #     raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")
# #                 debit_ledger_name = data["PartyName"] + " - " + debit_ledger_id
# #                 debit_ledgers.append(debit_ledger_id)
# #                 debit_ledger_names.append(debit_ledger_name)
# #                 debit_particulars.append(f"Sale from bill no: {bill_no}")
# #                 debit_amounts.append(total)

# #             # Credit Side
# #             credit_ledgers = []
# #             credit_particulars = []
# #             credit_amounts = []

# #             if sale_amount > 0:
# #                 credit_ledgers.append(ledgers["Sales"])
# #                 credit_particulars.append("Sales")
# #                 credit_amounts.append(sale_amount)

# #             if vat > 0:
# #                 credit_ledgers.append(ledgers["VAT Payable"])
# #                 credit_particulars.append("VAT Payable")
# #                 credit_amounts.append(vat)

# #             if discount_amt > 0:
# #                 credit_ledgers.append(ledgers["Discount Sales"])
# #                 credit_particulars.append("Discount Sales")
# #                 credit_amounts.append(discount_amt)
# #                 # Discount Expenses
# #                 debit_ledgers.append(ledgers["Discount Expenses"])
# #                 debit_ledger_names.append("Discount Expenses")  # ✅ ADD THIS LINE
# #                 debit_particulars.append("Discount Expenses")
# #                 debit_amounts.append(discount_amt)
# #             # Prepare data for the journal entry API
# #         else:
# #             credit_ledgers.append(ledgers["Complimentary Sales"])
# #             credit_particulars.append("Complimentary Sales")
# #             credit_amounts.append(sale_amount)
# #                 # Discount Expenses
# #             debit_ledgers.append(ledgers["Complimentary Expenses"])
# #             debit_particulars.append("Complimentary Expenses")
# #             debit_amounts.append(sale_amount)            
# #         journal_entry_data = {
# #             "outlet_name": outlet,
# #             "bill_id": bill_no,
# #             "datetime": formatted_date,
# #             "user": employee,
# #             "debit_ledgers": debit_ledgers,
# #             "debit_particulars": debit_particulars,
# #             "debit_amounts": [str(amount) for amount in debit_amounts],
# #             "credit_ledgers": credit_ledgers,
# #             "credit_particulars": credit_particulars,
# #             "credit_amounts": [str(amount) for amount in credit_amounts],
# #             "debit_ledger_names": debit_ledger_names,
# #             "billPrintTime": billprinttime 

# #         }

# #         accounting_token = os.getenv("accounting_token")

# #         # Post to the Journal Entry API
# #         # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
# #         journal_entry_api_url = accounting_url + "api/create_credit_journal_entry/"


# #         # Set the headers to include the bearer token
# #         headers = {
# #             "Authorization": f"Bearer {accounting_token}",  # Pass the token as a Bearer token
# #             "Content-Type": "application/json"   # Optional, ensures JSON content
# #         }
# #         print("data posed to credit", journal_entry_data)
# #         response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

# #         if response.status_code == 201:
# #             print({"message": "Journal entry created successfully"})
# #         else:
# #             print({"error": str(response.json())})

# #     except Exception as error:
# #         print({"error": str(error)})







# from decimal import Decimal
# import os, requests
# import os
# import requests
# from decimal import Decimal

# class JournalRejected(Exception):
#     """Accounting definitely did NOT commit. Safe to roll back."""

# class AccountingEntryNotFound(JournalRejected):
#     """Accounting has no sales entry for this bill (it was never posted there)."""


# class JournalOutcomeUnknown(Exception):
#     """Timeout, dropped connection, or proxy 502/503/504. Accounting may have committed."""
# ALREADY_POSTED = "Journal entry already posted"
# CREATED = "Journal entry created successfully"

# def _check_journal_response(response):
#     """Return only if accounting confirms the entry exists (newly created or already posted)."""
#     code = response.status_code

#     # Gateway errors: the request may have reached Django and committed.
#     if code in (502, 503, 504):
#         raise JournalOutcomeUnknown(f"Accounting gateway error {code}")

#     # 201 = created now, 200 = idempotent repeat. Anything else is a definite rejection.
#     if code not in (200, 201):
#         raise JournalRejected(f"Accounting returned {code}: {response.text[:300]}")

#     # Django answered success but the body is unreadable: it probably committed.
#     try:
#         results = response.json()
#     except ValueError:
#         raise JournalOutcomeUnknown(f"Accounting returned {code} with an unreadable body")

#     if not isinstance(results, list) or not results:
#         raise JournalOutcomeUnknown(f"Unexpected accounting response: {results}")

#     for item in results:
#         if not isinstance(item, dict) or item.get("message") not in (CREATED, ALREADY_POSTED):
#             raise JournalOutcomeUnknown(f"Unconfirmed accounting response: {item}")


# def _ledger_id(ledgers, name):
#     ledger_id = ledgers.get(name)
#     if not ledger_id:
#         raise ValueError(f"Ledger '{name}' was not found in accounting")
#     return ledger_id


# def _normalize_mode(mode):
#     return (mode or "").strip().lower().replace(" ", "")


# PAYMENT_LEDGER_MAP = {
#     "cash": "Cash-In-Hand",
#     "card": "Card Transactions",
#     "creditcard": "Card Transactions",
#     "mobile": "Mobile Payments",
#     "mobilepayment": "Mobile Payments",
# }

# # def post_hotelbill_and_create_journal(data, bill_id):
# #     print("inside hotel bill journal function")
# #     try:
# #         total = round(Decimal(str(data.get("Total", 0))), 2)
# #         vat = round(Decimal(str(data.get("VAT", 0))), 2)
# #         discount_amt = round(Decimal(str(data.get("DiscountAmt", 0))), 2)
# #         payment_mode = data.get("PaymentMode")
# #         bill_no = data.get("BillNo")
# #         date_str = data.get("Date")
# #         outlet = data.get("Outlet_Name")
# #         employee = data.get("Employee")
# #         billprinttime = data["billPrintTime"]

# #         # Room + mealplan revenue combine into a single "Sales" credit,
# #         # same treatment as the order-system's sale_amount = total - vat.
# #         sale_amount = total - vat

# #         accounting_url = os.getenv("accounting_url")
# #         ledger_api_url = accounting_url + "api/get-ledgers"
# #         ledger_response = requests.get(ledger_api_url)
# #         ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

# #         debit_ledgers, debit_particulars, debit_amounts = [], [], []
# #         credit_ledgers, credit_particulars, credit_amounts = [], [], []

# #         # -------- LEDGER NAME LOOKUP (normalized, case/space-insensitive) --------
# #         PAYMENT_LEDGER_MAP = {
# #             "cash": "Cash-In-Hand",
# #             "card": "Card Transactions",
# #             "mobile": "Mobile Payments",
# #         }

# #         def normalize_mode(mode):
# #             return (mode or "").strip().lower().replace(" ", "")

# #         if payment_mode and normalize_mode(payment_mode) == "split":
# #             split_payments = data.get("SplitPaymentDetailsList", [])
# #             if not split_payments:
# #                 raise ValueError("PaymentMode is 'Split' but SplitPaymentDetailsList is empty")

# #             for split_payment in split_payments:
# #                 split_mode_key = normalize_mode(split_payment.get("paymentMode"))
# #                 debit_ledger_name = PAYMENT_LEDGER_MAP.get(split_mode_key)

# #                 if not debit_ledger_name:
# #                     raise ValueError(f"Unhandled split payment mode for hotel bill: {split_payment.get('paymentMode')}")

# #                 debit_ledger_id = ledgers.get(debit_ledger_name)
# #                 if not debit_ledger_id:
# #                     raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")

# #                 debit_ledgers.append(debit_ledger_id)
# #                 debit_particulars.append(f"Split payment for hotel bill no: {bill_no}")
# #                 debit_amounts.append(round(Decimal(str(split_payment.get("paymentAmount", 0))), 2))

# #         else:
# #             debit_ledger_name = PAYMENT_LEDGER_MAP.get(normalize_mode(payment_mode))
# #             if not debit_ledger_name:
# #                 raise ValueError(f"Unhandled payment mode for hotel bill: {payment_mode}")

# #             debit_ledger_id = ledgers.get(debit_ledger_name)
# #             if not debit_ledger_id:
# #                 raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")

# #             debit_ledgers.append(debit_ledger_id)
# #             debit_particulars.append(f"Hotel bill payment for bill no: {bill_no}")
# #             debit_amounts.append(total)

# #         if sale_amount > 0:
# #             credit_ledgers.append(ledgers["Sales"])
# #             credit_particulars.append("Sales")
# #             credit_amounts.append(sale_amount)

# #         if vat > 0:
# #             credit_ledgers.append(ledgers["VAT Payable"])
# #             credit_particulars.append("VAT Payable")
# #             credit_amounts.append(vat)

# #         if discount_amt > 0:
# #             credit_ledgers.append(ledgers["Discount Sales"])
# #             credit_particulars.append("Discount Sales")
# #             credit_amounts.append(discount_amt)
# #             debit_ledgers.append(ledgers["Discount Expenses"])
# #             debit_particulars.append("Discount Expenses")
# #             debit_amounts.append(discount_amt)

# #         journal_entry_data = {
# #             "outlet_name": outlet,
# #             "bill_id": bill_no,
# #             "datetime": date_str,
# #             "user": employee,
# #             "debit_ledgers": debit_ledgers,
# #             "debit_particulars": debit_particulars,
# #             "debit_amounts": [str(a) for a in debit_amounts],
# #             "credit_ledgers": credit_ledgers,
# #             "credit_particulars": credit_particulars,
# #             "credit_amounts": [str(a) for a in credit_amounts],
# #             "billPrintTime" : billprinttime,
# #             "customer_name": data.get("PartyName"),
# #             "customer_pan": data.get("PartyPAN"),
# #             "total_amount": str(total),
# #             "vat_amount": str(vat),
# #             "fiscal_year": data.get("fiscalYear"),
# #             "payment_mode": payment_mode,
# #         }

# #         accounting_token = os.getenv("accounting_token")
# #         journal_entry_api_url = accounting_url + "api/create_journal_entry/"
# #         headers = {"Authorization": f"Bearer {accounting_token}", "Content-Type": "application/json"}

# #         print(journal_entry_data)
# #         response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

# #         if response.status_code == 201:
# #             print({"message": "Hotel bill journal entry created successfully"})
# #         else:
# #             print({"error": str(response.json())})

# #     except Exception as error:
# #         print({"error": str(error)})


# def post_hotelbill_and_create_journal(data, bill_id):
#     """Post a hotel CASH/CARD/MOBILE/SPLIT bill to accounting. Raises on any failure."""
#     try:
#         total = round(Decimal(str(data.get("Total") or 0)), 2)
#         vat = round(Decimal(str(data.get("VAT") or 0)), 2)
#         discount_amt = round(Decimal(str(data.get("DiscountAmt") or 0)), 2)
#         payment_mode = data.get("PaymentMode")
#         bill_no = data.get("BillNo")
#         date_str = data.get("Date")
#         outlet = data.get("Outlet_Name")
#         employee = data.get("Employee")
#         billprinttime = data["billPrintTime"]

#         sale_amount = total - vat

#         # -------- LEDGERS FROM ACCOUNTING --------
#         accounting_url = os.getenv("accounting_url")
#         ledger_response = requests.get(accounting_url + "api/get-ledgers", timeout=10)
#         ledger_response.raise_for_status()
#         ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

#         debit_ledgers, debit_particulars, debit_amounts = [], [], []
#         credit_ledgers, credit_particulars, credit_amounts = [], [], []

#         # -------- DEBIT SIDE --------
#         if _normalize_mode(payment_mode) == "split":
#             split_payments = data.get("SplitPaymentDetailsList") or []
#             if not split_payments:
#                 raise ValueError("PaymentMode is 'Split' but SplitPaymentDetailsList is empty")

#             for sp in split_payments:
#                 ledger_name = PAYMENT_LEDGER_MAP.get(_normalize_mode(sp.get("paymentMode")))
#                 if not ledger_name:
#                     raise ValueError(f"Unhandled split payment mode for hotel bill: {sp.get('paymentMode')}")

#                 debit_ledgers.append(_ledger_id(ledgers, ledger_name))
#                 debit_particulars.append(f"Split payment for hotel bill no: {bill_no}")
#                 debit_amounts.append(round(Decimal(str(sp.get("paymentAmount") or 0)), 2))
#         else:
#             ledger_name = PAYMENT_LEDGER_MAP.get(_normalize_mode(payment_mode))
#             if not ledger_name:
#                 raise ValueError(f"Unhandled payment mode for hotel bill: {payment_mode}")

#             debit_ledgers.append(_ledger_id(ledgers, ledger_name))
#             debit_particulars.append(f"Hotel bill payment for bill no: {bill_no}")
#             debit_amounts.append(total)

#         # -------- CREDIT SIDE --------
#         if sale_amount > 0:
#             credit_ledgers.append(_ledger_id(ledgers, "Sales"))
#             credit_particulars.append("Sales")
#             credit_amounts.append(sale_amount)

#         if vat > 0:
#             credit_ledgers.append(_ledger_id(ledgers, "VAT Payable"))
#             credit_particulars.append("VAT Payable")
#             credit_amounts.append(vat)

#         if discount_amt > 0:
#             credit_ledgers.append(_ledger_id(ledgers, "Discount Sales"))
#             credit_particulars.append("Discount Sales")
#             credit_amounts.append(discount_amt)

#             debit_ledgers.append(_ledger_id(ledgers, "Discount Expenses"))
#             debit_particulars.append("Discount Expenses")
#             debit_amounts.append(discount_amt)

#         journal_entry_data = {
#             "outlet_name": outlet,
#             "bill_id": bill_no,
#             "datetime": date_str,
#             "user": employee,
#             "debit_ledgers": debit_ledgers,
#             "debit_particulars": debit_particulars,
#             "debit_amounts": [str(a) for a in debit_amounts],
#             "credit_ledgers": credit_ledgers,
#             "credit_particulars": credit_particulars,
#             "credit_amounts": [str(a) for a in credit_amounts],
#             "billPrintTime": billprinttime,
#             # used by accounting to create the sales entry and tax entry
#             "customer_name": data.get("PartyName"),
#             "customer_pan": data.get("PartyPAN"),
#             "total_amount": str(total),
#             "vat_amount": str(vat),
#             "fiscal_year": data.get("fiscalYear"),
#             "payment_mode": payment_mode,
#             "sales_bill_no": bill_no,
#         }

#         headers = {
#             "Authorization": f"Bearer {os.getenv('accounting_token')}",
#             "Content-Type": "application/json",
#         }
#         print(journal_entry_data)

#         response = requests.post(
#             accounting_url + "api/create_journal_entry/",
#             json=[journal_entry_data],
#             headers=headers,
#             timeout=20,
#         )
#         _check_journal_response(response)

#     except Exception as error:
#         print({"error": str(error)})
#         raise

# import os
# import requests
# from decimal import Decimal


# def post_hotelbill_and_create_journal_for_creditbills(data, bill_id):
#     """
#     Post a hotel CREDIT bill to accounting. Only called when PaymentMode == "Credit".
#     Raises on any failure so /bill-by-id can roll the bill back.
#     """
#     try:
#         payment_mode = data["PaymentMode"]
#         if payment_mode != "Credit":
#             raise ValueError(f"Credit journal called for payment mode '{payment_mode}'")

#         total = round(Decimal(str(data.get("Total") or 0)), 2)
#         vat = round(Decimal(str(data.get("VAT") or 0)), 2)
#         discount_amt = round(Decimal(str(data.get("DiscountAmt") or 0)), 2)
#         bill_no = data["BillNo"]
#         date_str = data["Date"]
#         employee = data["Employee"]
#         outlet = data["Outlet_Name"]
#         billprinttime = data["billPrintTime"]

#         # the debtor ledger is the guest or company, so both are required
#         guest_id = str(data.get("guestID") or "").strip()
#         party_name = (data.get("PartyName") or "").strip()
#         if not guest_id:
#             raise ValueError("guestID is required for credit bills")
#         if not party_name:
#             raise ValueError("PartyName is required for credit bills")

#         # -------- LEDGERS FROM ACCOUNTING --------
#         accounting_url = os.getenv("accounting_url")
#         ledger_response = requests.get(accounting_url + "api/get-ledgers", timeout=10)
#         ledger_response.raise_for_status()
#         ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

#         sale_amount = total - vat

#         # -------- DEBIT SIDE: the debtor ledger (+ discount expense) --------
#         debit_ledgers = [guest_id]
#         debit_ledger_names = [f"{party_name} - {guest_id}"]
#         debit_particulars = [f"Sale from bill no: {bill_no}"]
#         debit_amounts = [total]

#         # -------- CREDIT SIDE --------
#         credit_ledgers, credit_particulars, credit_amounts = [], [], []

#         if sale_amount > 0:
#             credit_ledgers.append(_ledger_id(ledgers, "Sales"))
#             credit_particulars.append("Sales")
#             credit_amounts.append(sale_amount)

#         if vat > 0:
#             credit_ledgers.append(_ledger_id(ledgers, "VAT Payable"))
#             credit_particulars.append("VAT Payable")
#             credit_amounts.append(vat)

#         if discount_amt > 0:
#             credit_ledgers.append(_ledger_id(ledgers, "Discount Sales"))
#             credit_particulars.append("Discount Sales")
#             credit_amounts.append(discount_amt)

#             debit_ledgers.append(_ledger_id(ledgers, "Discount Expenses"))
#             debit_ledger_names.append("Discount Expenses")
#             debit_particulars.append("Discount Expenses")
#             debit_amounts.append(discount_amt)

#         journal_entry_data = {
#             "outlet_name": outlet,
#             "bill_id": bill_no,
#             "datetime": date_str,
#             "user": employee,
#             "debit_ledgers": debit_ledgers,
#             "debit_ledger_names": debit_ledger_names,
#             "debit_particulars": debit_particulars,
#             "debit_amounts": [str(a) for a in debit_amounts],
#             "credit_ledgers": credit_ledgers,
#             "credit_particulars": credit_particulars,
#             "credit_amounts": [str(a) for a in credit_amounts],
#             "billPrintTime": billprinttime,
#             # used by accounting to create the sales entry and tax entry
#             "customer_name": party_name,
#             "customer_pan": data.get("PartyPAN"),
#             "total_amount": str(total),
#             "vat_amount": str(vat),
#             "fiscal_year": data.get("fiscalYear"),
#             "payment_mode": payment_mode,
#             "sales_bill_no": bill_no,
#         }

#         headers = {
#             "Authorization": f"Bearer {os.getenv('accounting_token')}",
#             "Content-Type": "application/json",
#         }
#         print("data posted to credit", journal_entry_data)

#         response = requests.post(
#             accounting_url + "api/create_credit_journal_entry/",
#             json=[journal_entry_data],
#             headers=headers,
#             timeout=20,
#         )
#         _check_journal_response(response)

#     except Exception as error:
#         print({"error": str(error)})
#         raise



# # def get_next_hotel_bill_info():
# #     """Reserve the next hotel bill number from the accounting app."""
# #     accounting_url = os.getenv("accounting_url")
# #     accounting_token = os.getenv("accounting_token")
# #     resp = requests.get(
# #         accounting_url + "api/givehotelbillnumber/",
# #         headers={"Authorization": f"Bearer {accounting_token}", "Content-Type": "application/json"},
# #         timeout=10,
# #     )
# #     resp.raise_for_status()
# #     data = resp.json()

# #     if not isinstance(data, dict) or not str(data.get("next_bill_no") or "").strip():
# #         raise ValueError(f"Unexpected bill number response from accounting: {data}")

# #     return {
# #         "bill_no": str(data["next_bill_no"]).strip(),
# #         "fiscal_year": data.get("fiscal_year"),
# #         "terminal": data.get("terminal"),
# #     }


# def get_next_hotel_bill_info(cursor, property_id):
#     """Reserve the next bill number for a property.
#     Must run inside the caller's transaction (dictionary cursor): the row lock
#     is held until the caller commits, and a rollback gives the number back."""
#     cursor.execute("""
#         SELECT bill_no_count, fiscal_year
#         FROM hotel_company_property
#         WHERE id=%s FOR UPDATE
#     """, (property_id,))
#     row = cursor.fetchone()
#     if not row:
#         raise ValueError(f"Property {property_id} not found.")
#     if not (row["fiscal_year"] or "").strip():
#         raise ValueError("Fiscal year is not configured for this property.")

#     next_no = (row["bill_no_count"] or 0) + 1
#     cursor.execute(
#         "UPDATE hotel_company_property SET bill_no_count=%s WHERE id=%s",
#         (next_no, property_id)
#     )
#     return {"bill_no": str(next_no), "fiscal_year": row["fiscal_year"]}


# def get_next_hotel_bill_no():
#     return get_next_hotel_bill_info()["bill_no"]


# import os
# import requests
# from decimal import Decimal


# def void_hotelbill(data):
#     """
#     void hotelbill in accounting
#     """
#     try:
#         print("got upto here")
#         json_data = data

#         journal_entry_data = json_data
#         accounting_url = os.getenv("accounting_url")

#         headers = {
#             "Authorization": f"Bearer {os.getenv('accounting_token')}",
#             "Content-Type": "application/json",
#         }
#         print("data posted to credit", journal_entry_data)

#         response = requests.post(
#             accounting_url + "api/hotelbillvoid/",
#             json=journal_entry_data,
#             headers=headers,
#             timeout=20,
#         )
#         _check_journal_response(response)

#     except Exception as error:
#         print({"error": str(error)})
#         raise




from decimal import Decimal
import os, requests
import os
import requests
from decimal import Decimal

class JournalRejected(Exception):
    """Accounting definitely did NOT commit. Safe to roll back."""

class JournalOutcomeUnknown(Exception):
    """Timeout, dropped connection, or proxy 502/503/504. Accounting may have committed."""
ALREADY_POSTED = "Journal entry already posted"
CREATED = "Journal entry created successfully"

class AccountingEntryNotFound(JournalRejected):
    """Accounting has no sales entry for this bill (it was never posted there)."""

def _check_journal_response(response):
    """Return only if accounting confirms the entry exists (newly created or already posted)."""
    code = response.status_code

    # Gateway errors: the request may have reached Django and committed.
    if code in (502, 503, 504):
        raise JournalOutcomeUnknown(f"Accounting gateway error {code}")

    # 201 = created now, 200 = idempotent repeat. Anything else is a definite rejection.
    if code not in (200, 201):
        raise JournalRejected(f"Accounting returned {code}: {response.text[:300]}")

    # Django answered success but the body is unreadable: it probably committed.
    try:
        results = response.json()
    except ValueError:
        raise JournalOutcomeUnknown(f"Accounting returned {code} with an unreadable body")

    if not isinstance(results, list) or not results:
        raise JournalOutcomeUnknown(f"Unexpected accounting response: {results}")

    for item in results:
        if not isinstance(item, dict) or item.get("message") not in (CREATED, ALREADY_POSTED):
            raise JournalOutcomeUnknown(f"Unconfirmed accounting response: {item}")


def _ledger_id(ledgers, name):
    ledger_id = ledgers.get(name)
    if not ledger_id:
        raise ValueError(f"Ledger '{name}' was not found in accounting")
    return ledger_id


def _normalize_mode(mode):
    return (mode or "").strip().lower().replace(" ", "")


PAYMENT_LEDGER_MAP = {
    "cash": "Cash-In-Hand",
    "card": "Card Transactions",
    "creditcard": "Card Transactions",
    "mobile": "Mobile Payments",
    "mobilepayment": "Mobile Payments",
}


def post_hotelbill_and_create_journal(data, bill_id):
    """Post a hotel CASH/CARD/MOBILE/SPLIT bill to accounting. Raises on any failure."""
    try:
        total = round(Decimal(str(data.get("Total") or 0)), 2)
        vat = round(Decimal(str(data.get("VAT") or 0)), 2)
        discount_amt = round(Decimal(str(data.get("DiscountAmt") or 0)), 2)
        payment_mode = data.get("PaymentMode")
        bill_no = data.get("BillNo")
        date_str = data.get("Date")
        outlet = data.get("Outlet_Name")
        employee = data.get("Employee")
        billprinttime = data["billPrintTime"]

        sale_amount = total - vat

        # -------- LEDGERS FROM ACCOUNTING --------
        accounting_url = os.getenv("accounting_url")
        ledger_response = requests.get(accounting_url + "api/get-ledgers", timeout=10)
        ledger_response.raise_for_status()
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

        debit_ledgers, debit_particulars, debit_amounts = [], [], []
        credit_ledgers, credit_particulars, credit_amounts = [], [], []

        # -------- DEBIT SIDE --------
        if _normalize_mode(payment_mode) == "split":
            split_payments = data.get("SplitPaymentDetailsList") or []
            if not split_payments:
                raise ValueError("PaymentMode is 'Split' but SplitPaymentDetailsList is empty")

            for sp in split_payments:
                ledger_name = PAYMENT_LEDGER_MAP.get(_normalize_mode(sp.get("paymentMode")))
                if not ledger_name:
                    raise ValueError(f"Unhandled split payment mode for hotel bill: {sp.get('paymentMode')}")

                debit_ledgers.append(_ledger_id(ledgers, ledger_name))
                debit_particulars.append(f"Split payment for hotel bill no: {bill_no}")
                debit_amounts.append(round(Decimal(str(sp.get("paymentAmount") or 0)), 2))
        else:
            ledger_name = PAYMENT_LEDGER_MAP.get(_normalize_mode(payment_mode))
            if not ledger_name:
                raise ValueError(f"Unhandled payment mode for hotel bill: {payment_mode}")

            debit_ledgers.append(_ledger_id(ledgers, ledger_name))
            debit_particulars.append(f"Hotel bill payment for bill no: {bill_no}")
            debit_amounts.append(total)

        # -------- CREDIT SIDE --------
        if sale_amount > 0:
            credit_ledgers.append(_ledger_id(ledgers, "Sales"))
            credit_particulars.append("Sales")
            credit_amounts.append(sale_amount)

        if vat > 0:
            credit_ledgers.append(_ledger_id(ledgers, "VAT Payable"))
            credit_particulars.append("VAT Payable")
            credit_amounts.append(vat)

        if discount_amt > 0:
            credit_ledgers.append(_ledger_id(ledgers, "Discount Sales"))
            credit_particulars.append("Discount Sales")
            credit_amounts.append(discount_amt)

            debit_ledgers.append(_ledger_id(ledgers, "Discount Expenses"))
            debit_particulars.append("Discount Expenses")
            debit_amounts.append(discount_amt)

        journal_entry_data = {
            "outlet_name": outlet,
            "bill_id": bill_no,
            "datetime": date_str,
            "user": employee,
            "debit_ledgers": debit_ledgers,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(a) for a in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(a) for a in credit_amounts],
            "billPrintTime": billprinttime,
            # used by accounting to create the sales entry and tax entry
            "customer_name": data.get("PartyName"),
            "customer_pan": data.get("PartyPAN"),
            "total_amount": str(total),
            "vat_amount": str(vat),
            "fiscal_year": data.get("fiscalYear"),
            "payment_mode": payment_mode,
            "sales_bill_no": bill_no,
        }

        headers = {
            "Authorization": f"Bearer {os.getenv('accounting_token')}",
            "Content-Type": "application/json",
        }
        print(journal_entry_data)

        response = requests.post(
            accounting_url + "api/create_journal_entry/",
            json=[journal_entry_data],
            headers=headers,
            timeout=20,
        )
        _check_journal_response(response)

    except Exception as error:
        print({"error": str(error)})
        raise

import os
import requests
from decimal import Decimal


def post_hotelbill_and_create_journal_for_creditbills(data, bill_id):
    """
    Post a hotel CREDIT bill to accounting. Only called when PaymentMode == "Credit".
    Raises on any failure so /bill-by-id can roll the bill back.
    """
    try:
        payment_mode = data["PaymentMode"]
        if payment_mode != "Credit":
            raise ValueError(f"Credit journal called for payment mode '{payment_mode}'")

        total = round(Decimal(str(data.get("Total") or 0)), 2)
        vat = round(Decimal(str(data.get("VAT") or 0)), 2)
        discount_amt = round(Decimal(str(data.get("DiscountAmt") or 0)), 2)
        bill_no = data["BillNo"]
        date_str = data["Date"]
        employee = data["Employee"]
        outlet = data["Outlet_Name"]
        billprinttime = data["billPrintTime"]

        # the debtor ledger is the guest or company, so both are required
        guest_id = str(data.get("guestID") or "").strip()
        party_name = (data.get("PartyName") or "").strip()
        if not guest_id:
            raise ValueError("guestID is required for credit bills")
        if not party_name:
            raise ValueError("PartyName is required for credit bills")

        # -------- LEDGERS FROM ACCOUNTING --------
        accounting_url = os.getenv("accounting_url")
        ledger_response = requests.get(accounting_url + "api/get-ledgers", timeout=10)
        ledger_response.raise_for_status()
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

        sale_amount = total - vat

        # -------- DEBIT SIDE: the debtor ledger (+ discount expense) --------
        debit_ledgers = [guest_id]
        debit_ledger_names = [f"{party_name} - {guest_id}"]
        debit_particulars = [f"Sale from bill no: {bill_no}"]
        debit_amounts = [total]

        # -------- CREDIT SIDE --------
        credit_ledgers, credit_particulars, credit_amounts = [], [], []

        if sale_amount > 0:
            credit_ledgers.append(_ledger_id(ledgers, "Sales"))
            credit_particulars.append("Sales")
            credit_amounts.append(sale_amount)

        if vat > 0:
            credit_ledgers.append(_ledger_id(ledgers, "VAT Payable"))
            credit_particulars.append("VAT Payable")
            credit_amounts.append(vat)

        if discount_amt > 0:
            credit_ledgers.append(_ledger_id(ledgers, "Discount Sales"))
            credit_particulars.append("Discount Sales")
            credit_amounts.append(discount_amt)

            debit_ledgers.append(_ledger_id(ledgers, "Discount Expenses"))
            debit_ledger_names.append("Discount Expenses")
            debit_particulars.append("Discount Expenses")
            debit_amounts.append(discount_amt)

        journal_entry_data = {
            "outlet_name": outlet,
            "bill_id": bill_no,
            "datetime": date_str,
            "user": employee,
            "debit_ledgers": debit_ledgers,
            "debit_ledger_names": debit_ledger_names,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(a) for a in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(a) for a in credit_amounts],
            "billPrintTime": billprinttime,
            # used by accounting to create the sales entry and tax entry
            "customer_name": party_name,
            "customer_pan": data.get("PartyPAN"),
            "total_amount": str(total),
            "vat_amount": str(vat),
            "fiscal_year": data.get("fiscalYear"),
            "payment_mode": payment_mode,
            "sales_bill_no": bill_no,
        }

        headers = {
            "Authorization": f"Bearer {os.getenv('accounting_token')}",
            "Content-Type": "application/json",
        }
        print("data posted to credit", journal_entry_data)

        response = requests.post(
            accounting_url + "api/create_credit_journal_entry/",
            json=[journal_entry_data],
            headers=headers,
            timeout=20,
        )
        _check_journal_response(response)

    except Exception as error:
        print({"error": str(error)})
        raise


import requests

# def get_next_hotel_bill_no():
#     """Reserve the next hotel bill number from the accounting app."""
#     accounting_url = os.getenv("accounting_url")
#     accounting_token = os.getenv("accounting_token")
#     resp = requests.get(
#         accounting_url + "api/givehotelbillnumber/",     # use the path you registered
#         headers={"Authorization": f"Bearer {accounting_token}", "Content-Type": "application/json"},
#         timeout=10,
#     )
#     resp.raise_for_status()
#     return resp.json()

def get_next_hotel_bill_info(cursor, property_id):
    """Reserve the next bill number for a property.
    Must run inside the caller's transaction (dictionary cursor): the row lock
    is held until the caller commits, and a rollback gives the number back."""
    cursor.execute("""
        SELECT bill_no_count, fiscal_year
        FROM hotel_company_property
        WHERE id=%s FOR UPDATE
    """, (property_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Property {property_id} not found.")
    if not (row["fiscal_year"] or "").strip():
        raise ValueError("Fiscal year is not configured for this property.")

    next_no = (row["bill_no_count"] or 0) + 1
    cursor.execute(
        "UPDATE hotel_company_property SET bill_no_count=%s WHERE id=%s",
        (next_no, property_id)
    )
    return {"bill_no": str(next_no), "fiscal_year": row["fiscal_year"]}


def get_next_hotel_bill_no():
    return get_next_hotel_bill_info()["bill_no"]


import os
import requests
from decimal import Decimal


# def void_hotelbill(data):
#     """
#     void hotelbill in accounting
#     """
#     try:
#         print("got upto here")
#         json_data = data

#         journal_entry_data = json_data
#         accounting_url = os.getenv("accounting_url")

#         headers = {
#             "Authorization": f"Bearer {os.getenv('accounting_token')}",
#             "Content-Type": "application/json",
#         }
#         print("data posted to credit", journal_entry_data)

#         response = requests.post(
#             accounting_url + "api/hotelbillvoid/",
#             json=journal_entry_data,
#             headers=headers,
#             timeout=20,
#         )
#         _check_journal_response(response)

#     except Exception as error:
#         print({"error": str(error)})
#         raise



# def void_hotelbill(data):
#     """Void a hotel bill in accounting. Returns normally if the void succeeded or the
#     bill was already voided there. Raises on any failure."""
#     try:
#         accounting_url = os.getenv("accounting_url")

#         headers = {
#             "Authorization": f"Bearer {os.getenv('accounting_token')}",
#             "Content-Type": "application/json",
#         }

#         try:
#             response = requests.post(
#                 accounting_url + "api/hotelbillvoid/",
#                 json=data,
#                 headers=headers,
#                 timeout=45,   # accounting posts to IRD inside this request
#             )
#         except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
#             raise JournalOutcomeUnknown(
#                 "Accounting request timed out or the connection dropped; the void may have been applied"
#             )

#         code = response.status_code
#         if code in (502, 503, 504):
#             raise JournalOutcomeUnknown(f"Accounting gateway error {code}")

#         try:
#             body = response.json()
#         except ValueError:
#             body = None

#         if code == 200:
#             if isinstance(body, dict) and body.get("voided") is True:
#                 return body
#             raise JournalOutcomeUnknown(f"Unexpected accounting response: {body}")

#         if isinstance(body, dict):
#             error_text = str(body.get("error") or body.get("detail") or body)
#         else:
#             error_text = response.text[:300]

#         if code == 400 and (
#             (isinstance(body, dict) and body.get("code") == "ALREADY_VOIDED")
#             or "already voided" in error_text.lower()
#         ):
#             return body

#         raise JournalRejected(error_text or f"Accounting returned {code}")

#     except Exception as error:
#         print({"error": str(error)})
#         raise


def void_hotelbill(data):
    """Void a bill in accounting. Returns normally if the void succeeded or the
    bill was already voided there. Raises on any failure."""
    try:
        accounting_url = os.getenv("accounting_url")

        headers = {
            "Authorization": f"Bearer {os.getenv('accounting_token')}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                accounting_url + "api/hotelbillvoid/",
                json=data,
                headers=headers,
                timeout=45,   # accounting posts to IRD inside this request
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise JournalOutcomeUnknown(
                "Accounting request timed out or the connection dropped; the void may have been applied"
            )

        code = response.status_code
        if code in (502, 503, 504):
            raise JournalOutcomeUnknown(f"Accounting gateway error {code}")

        try:
            body = response.json()
        except ValueError:
            body = None

        if code == 200:
            if isinstance(body, dict) and body.get("voided") is True:
                return body
            raise JournalOutcomeUnknown(f"Unexpected accounting response: {body}")

        if isinstance(body, dict):
            error_text = str(body.get("error") or body.get("detail") or body)
        else:
            error_text = response.text[:300]

        if code == 400 and (
            (isinstance(body, dict) and body.get("code") == "ALREADY_VOIDED")
            or "already voided" in error_text.lower()
        ):
            return body

        if code == 404 and isinstance(body, dict) and body.get("code") == "SALES_ENTRY_NOT_FOUND":
            raise AccountingEntryNotFound(error_text)

        raise JournalRejected(error_text or f"Accounting returned {code}")

    except Exception as error:
        print({"error": str(error)})
        raise


import os
import requests
from decimal import Decimal
from datetime import datetime

PAYMENT_MODE_LEDGERS = {
    "Cash": "Cash-In-Hand",
    "Credit Card": "Card Transactions",
    "Card": "Card Transactions",
    "Mobile Payment": "Mobile Payments",
}

def post_party_payment_journal(data):
    """
    data = {
        "customer_ledger_id": "guest-12",       # namespaced id from frontend
        "payments": [{"paymentMode": "Cash", "paymentAmount": 1000}, ...],
        "Employee": "...", "date": "...", "bill_no": "...", "particular": "..."
    }
    Returns (ok, payload) so the API can respond properly.
    """
    try:
        backend_url = os.getenv("accounting_url")
        token = os.getenv("accounting_token")

        ledger_resp = requests.get(backend_url + "api/get-ledgers", timeout=15)
        ledgers = {l["ledger_name"]: l["id"] for l in ledger_resp.json()}

        amount_by_ledger = {}
        for p in data["payments"]:
            ledger_name = PAYMENT_MODE_LEDGERS.get(p["paymentMode"])
            if not ledger_name:
                raise ValueError(f"Unsupported payment mode: {p['paymentMode']}")
            ledger_id = ledgers.get(ledger_name)
            if not ledger_id:
                raise ValueError(f"Ledger not found: {ledger_name}")
            amount = round(Decimal(str(p["paymentAmount"])), 2)
            if amount <= 0:
                raise ValueError(f"Invalid amount for {p['paymentMode']}")
            amount_by_ledger[ledger_id] = amount_by_ledger.get(ledger_id, Decimal("0")) + amount

        payload = {
            "customer_ledger_id": str(data["customer_ledger_id"]),
            "datetime": data.get("date") or datetime.now().strftime("%Y-%m-%d"),
            "user": data["Employee"],
            "particular": data.get("particular", ""),
            "bill_id": data.get("bill_no", ""),
            "reference": data.get("reference", ""),
            "payments": [{"ledger_id": lid, "amount": str(a)} for lid, a in amount_by_ledger.items()],
        }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        resp = requests.post(backend_url + "api/create_party_payment_journal/",
                             json=[payload], headers=headers, timeout=30)
        try:
            body = resp.json()
        except ValueError:
            body = {"error": resp.text}

        return (resp.status_code == 201), body

    except Exception as error:
        return False, {"error": str(error)}