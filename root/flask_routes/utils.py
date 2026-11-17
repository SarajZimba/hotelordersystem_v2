from flask import jsonify
def get_costcenterwisestockissue(item_name, startDate, endDate, cursor, outlet):

    # Query to get the stock requisition data filtered by date range and outlet
    query_storerequisition = """
        SELECT `idintblStoreRequisition`, `Date`, `CostCenter`, `Outlet`, `OutletREQID`
        FROM `intblstorerequisition`
         WHERE `Date` BETWEEN %s AND %s AND `Outlet` = %s
    """
    cursor.execute(query_storerequisition, (startDate, endDate, outlet))
    store_requisitions = cursor.fetchall()

    if not store_requisitions:
        return []

    all_requisitions = {}

    # Iterate over all store requisitions
    for store_requisition in store_requisitions:
        store_req_id = store_requisition[0]
        cost_center = store_requisition[2]

        # Fetch item details for each store requisition
        query_storereqdetails = """
            SELECT `ItemName`, `GroupName`, `BrandName`, `Amount`, `UOM`, `Rate`
            FROM `intblstorereqdetails`
            WHERE `StoreReqID` = %s  and `ItemName` = %s order by GroupName
        """
        cursor.execute(query_storereqdetails, (store_req_id, item_name))
        store_itemdetails = cursor.fetchall()

        # If the cost center does not exist in the dictionary, create it
        if cost_center not in all_requisitions:
            # all_requisitions[cost_center] = []
            all_requisitions[cost_center] = {"item_details": [], "grand_total": 0}
        # grand_total = 0
        # Iterate over the item details and group by ItemName and Rate
        for item in store_itemdetails:
            item_name = item[0]
            rate = item[5]
            amount = item[3]
            # Check if the item with the same name and rate already exists in the list for this cost center
            found = False
            for entry in all_requisitions[cost_center]["item_details"]:
                if entry["ItemName"] == item_name and entry["Rate"] == rate:
                    # If found, sum the amounts
                    entry["Amount"] += amount
                    entry["Amount"] = round(entry["Amount"], 2)
                    entry["Total"] =  round(entry["Rate"] * entry["Amount"], 2)
                    # all_requisitions[cost_center]["grand_total"] += entry["Total"]
                    found = True
                    break

            # If not found, add a new entry for this item
            if not found:
                all_requisitions[cost_center]["item_details"].append({
                    "ItemName": item_name,
                    "Rate": rate,
                    "Amount": round(amount, 2),
                    "UOM": item[4],
                    "GroupName": item[1],
                    "BrandName": item[2],
                    "Total": round(rate * amount, 2)
                })
                # all_requisitions[cost_center]["grand_total"] += round(rate * amount, 2)
    # Format the data as a list of cost centers with their items grouped and summed
    final_response = []
    for cost_center, items in all_requisitions.items():
        grand_total = sum(data["Total"] for data in items["item_details"])  # Calculate grand total
        sorted_item_details = sorted(items["item_details"], key=lambda x: x["GroupName"])
        final_response.append({
            "CostCenter": cost_center,
            "ItemDetailsList": sorted_item_details,
            "grand_total": grand_total,
        })

    return final_response


import requests
from decimal import Decimal
from datetime import datetime
import os
def post_sales_and_create_journal(data):
    print("inside function")
    try:
        print("inside try")
        print(data)
        # Extract relevant data from request
        total = round(Decimal(data["Total"]), 2)
        vat = round(Decimal(data["VAT"]), 2)
        discount_amt = round(Decimal(data["discountAmt"]), 2)
        payment_mode = data["paymentMode"]
        bill_no = data["Outlet_Name"] + " - " + data["bill_No"]
        date_str = data["date"]
        employee = data["Employee"]
        outlet = data["Outlet_Name"]
        billprinttime = data["billPrintTime"]

        # Convert date to required format
        formatted_date = date_str

        # Get ledger details from API
        # ledger_api_url = "https://9thamel.silverlinepos.com/api/get-ledgers"
        backend_url = os.getenv("accounting_url")

        ledger_api_url = backend_url + "api/get-ledgers"

        ledger_response = requests.get(ledger_api_url)
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}
        # Calculate ledger-specific values
        sale_amount = total - vat 

        # Debit Side
        debit_ledgers = []
        debit_particulars = []
        debit_amounts = []

        # Credit Side
        credit_ledgers = []
        credit_particulars = []
        credit_amounts = []
        if payment_mode != "Complimentary" and payment_mode != "Non Chargeable":
            if payment_mode == "Split":
                for split_payment in data.get("SplitPaymentDetailsList", []):
                    if split_payment["paymentMode"] == "Cash":
                        payment_ledger_id = ledgers.get("Cash-In-Hand")
                        payment_ledger_name = "Cash-In-Hand"
                    if split_payment["paymentMode"] == "Credit Card":
                        payment_ledger_id = ledgers.get("Card Transactions")
                        payment_ledger_name = "Card Transactions"

                    if split_payment["paymentMode"] == "Mobile Payment":
                        payment_ledger_id = ledgers.get("Mobile Payments")
                        payment_ledger_name = "Mobile Payments"

                    # payment_ledger_name = split_payment["paymentMode"] 
                    # payment_ledger_id = ledgers.get(payment_ledger_name)
                    if not payment_ledger_id:
                        raise ValueError(f"Invalid payment ledger name: {payment_ledger_name}")

                    debit_ledgers.append(payment_ledger_id)
                    debit_particulars.append(f"Split payment from bill no: {bill_no}")
                    debit_amounts.append(Decimal(split_payment["paymentAmount"]))
            else:
                if payment_mode == "Cash":
                    debit_ledger_name = "Cash-In-Hand"  
                if payment_mode == "Credit Card":
                    debit_ledger_name = "Card Transactions"  
                if payment_mode == "Mobile Payment":
                    debit_ledger_name = "Mobile Payments"  
                debit_ledger_id = ledgers.get(debit_ledger_name)
                print(debit_ledger_id)
                if not debit_ledger_id:
                    raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")

                debit_ledgers.append(debit_ledger_id)
                debit_particulars.append(f"Sale from bill no: {bill_no}")
                debit_amounts.append(total)

            if sale_amount > 0:
                credit_ledgers.append(ledgers["Sales"])
                credit_particulars.append("Sales")
                credit_amounts.append(sale_amount)

            if vat > 0:
                credit_ledgers.append(ledgers["VAT Payable"])
                credit_particulars.append("VAT Payable")
                credit_amounts.append(vat)

            if discount_amt > 0:
                credit_ledgers.append(ledgers["Discount Sales"])
                credit_particulars.append("Discount Sales")
                credit_amounts.append(discount_amt)
                # Discount Expenses
                debit_ledgers.append(ledgers["Discount Expenses"])
                debit_particulars.append("Discount Expenses")
                debit_amounts.append(discount_amt)
            # Prepare data for the journal entry API
        else:
            credit_ledgers.append(ledgers["Complimentary Sales"])
            credit_particulars.append("Complimentary Sales")
            credit_amounts.append(sale_amount)
                # Discount Expenses
            debit_ledgers.append(ledgers["Complimentary Expenses"])
            debit_particulars.append("Complimentary Expenses")
            debit_amounts.append(sale_amount)            
        journal_entry_data = {
            "outlet_name": outlet,
            "bill_id": bill_no,
            "datetime": formatted_date,
            "user": employee,
            "debit_ledgers": debit_ledgers,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(amount) for amount in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(amount) for amount in credit_amounts],
            "billPrintTime" : billprinttime,
            "sales_subledger_name": outlet,   # <- add this

        }
        journal_entry_data.update(_sales_entry_fields(data))
        token = os.getenv("accounting_token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_journal_entry/"
        journal_entry_api_url = backend_url + "api/create_journal_entry/"


        # Set the headers to include the bearer token
        headers = {
            "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        print(journal_entry_data)
        response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

        if response.status_code == 201:
            print({"message": "Journal entry created successfully"})
        else:
            # print(response.json())
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})


import requests
from decimal import Decimal
from datetime import datetime
import os
def post_sales_and_create_journal_for_creditbills(data):
    print("inside function")
    try:
        print("inside try")
        print(data)
        # Extract relevant data from request
        total = round(Decimal(data["Total"]), 2)
        vat = round(Decimal(data["VAT"]), 2)
        discount_amt = round(Decimal(data["discountAmt"]), 2)
        payment_mode = data["paymentMode"]
        bill_no = data["bill_No"]
        date_str = data["date"]
        employee = data["Employee"]
        outlet = data["Outlet_Name"]
        # Convert date to required format
        formatted_date = date_str
        billprinttime = data["billPrintTime"]

        # Get ledger details from API
        backend_url = os.getenv("accounting_url")

        ledger_api_url = backend_url + "api/get-ledgers"
        ledger_response = requests.get(ledger_api_url)
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}
        # Calculate ledger-specific values
        sale_amount = total - vat 

        # Debit Side
        debit_ledgers = []
        debit_ledger_names = []
        debit_particulars = []
        debit_amounts = []


        if payment_mode != "Complimentary" or payment_mode != "Non Chargeable":
            if payment_mode == "Split":
                for split_payment in data.get("SplitPaymentDetailsList", []):
                    if split_payment["paymentMode"] == "Cash":
                        payment_ledger_id = ledgers.get("Cash-In-Hand")
                        payment_ledger_name = "Cash-In-Hand"
                    if split_payment["paymentMode"] == "Credit Card":
                        payment_ledger_id = ledgers.get("Card Transactions")
                        payment_ledger_name = "Card Transactions"

                    if split_payment["paymentMode"] == "Mobile Payment":
                        payment_ledger_id = ledgers.get("Mobile Payments")
                        payment_ledger_name = "Mobile Payments"

                    # payment_ledger_name = split_payment["paymentMode"] 
                    # payment_ledger_id = ledgers.get(payment_ledger_name)
                    if not payment_ledger_id:
                        raise ValueError(f"Invalid payment ledger name: {payment_ledger_name}")

                    debit_ledgers.append(payment_ledger_id)
                    debit_particulars.append(f"Split payment from bill no: {bill_no}")
                    debit_amounts.append(Decimal(split_payment["paymentAmount"]))
            else:
                # if payment_mode == "Cash":
                #     debit_ledger_name = "Cash-In-Hand"  
                # if payment_mode == "Credit Card":
                #     debit_ledger_name = "Card Transactions"  
                # if payment_mode == "Mobile Payment":
                #     debit_ledger_name = "Mobile Payments"  
                # debit_ledger_id = ledgers.get(debit_ledger_name)
                debit_ledger_id = data["guestID"]
                print(debit_ledger_id)
                # if not debit_ledger_id:
                #     raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")
                debit_ledger_name = data["GuestName"] + " - " + data["guestID"]
                debit_ledgers.append(debit_ledger_id)
                debit_ledger_names.append(debit_ledger_name)
                debit_particulars.append(f"Sale from bill no: {bill_no}")
                debit_amounts.append(total)

            # Credit Side
            credit_ledgers = []
            credit_particulars = []
            credit_amounts = []

            if sale_amount > 0:
                credit_ledgers.append(ledgers["Sales"])
                credit_particulars.append("Sales")
                credit_amounts.append(sale_amount)

            if vat > 0:
                credit_ledgers.append(ledgers["VAT Payable"])
                credit_particulars.append("VAT Payable")
                credit_amounts.append(vat)

            if discount_amt > 0:
                credit_ledgers.append(ledgers["Discount Sales"])
                credit_particulars.append("Discount Sales")
                credit_amounts.append(discount_amt)
                # Discount Expenses
                debit_ledgers.append(ledgers["Discount Expenses"])
                debit_ledger_names.append("Discount Expenses")  # ✅ ADD THIS LINE
                debit_particulars.append("Discount Expenses")
                debit_amounts.append(discount_amt)
            # Prepare data for the journal entry API
        else:
            credit_ledgers.append(ledgers["Complimentary Sales"])
            credit_particulars.append("Complimentary Sales")
            credit_amounts.append(sale_amount)
                # Discount Expenses
            debit_ledgers.append(ledgers["Complimentary Expenses"])
            debit_particulars.append("Complimentary Expenses")
            debit_amounts.append(sale_amount)            
        journal_entry_data = {
            "outlet_name": outlet,
            "bill_id": bill_no,
            "datetime": formatted_date,
            "user": employee,
            "debit_ledgers": debit_ledgers,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(amount) for amount in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(amount) for amount in credit_amounts],
            "debit_ledger_names": debit_ledger_names,
            "billPrintTime": billprinttime 

        }
        journal_entry_data.update(_sales_entry_fields(data))
        token = os.getenv("accounting_token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
        journal_entry_api_url = backend_url + "api/create_credit_journal_entry/"


        # Set the headers to include the bearer token
        headers = {
            "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        print(journal_entry_data)
        response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

        if response.status_code == 201:
            print({"message": "Journal entry created successfully"})
        else:
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})


import requests
from decimal import Decimal
from datetime import datetime
import os
def post_purchases_and_create_journal(data):
    print("inside function")
    print(data)
    try:
        backend_url = os.getenv("backend_url")


        token = os.getenv("token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
        journal_entry_api_url = backend_url + "api/purchase-create/"

        # Set the headers to include the bearer token
        headers = {
            "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        response = requests.post(journal_entry_api_url, json=data, headers=headers)

        if response.status_code == 201:
            print({"message": "Journal entry created successfully"})
        else:
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})


import requests
from decimal import Decimal
from datetime import datetime
import os
def delete_purchases_and_journal(data):
    print("inside function")
    print(data)
    try:
        backend_url = os.getenv("backend_url")


        token = os.getenv("token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
        delete_purchase_journal_entry_api_url = backend_url + "api/purchase-delete/"

        # Set the headers to include the bearer token
        headers = {
            # "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        response = requests.post(delete_purchase_journal_entry_api_url, json=data, headers=headers)

        if response.status_code == 201:
            print({"message": "Purchase and Journal entry deleted  successfully"})
        else:
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})

def poststocktransfertoaccounting(data):
    print("inside function")
    print(data)
    try:
        backend_url = os.getenv("backend_url")


        token = os.getenv("token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
        poststock_api_url = backend_url + "api/stocktransferexpense-create/"

        # Set the headers to include the bearer token
        headers = {
            "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        response = requests.post(poststock_api_url, json=data, headers=headers)

        if response.status_code == 201:
            print({"message": "Stock Posted successfully"})
        else:
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})

def deletestocktransfertoaccounting(data):
    print("inside function")
    print(data)
    try:
        backend_url = os.getenv("backend_url")


        token = os.getenv("token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
        deletestock_api_url = backend_url + "api/stocktransferexpense-delete/"

        # Set the headers to include the bearer token
        headers = {
            # "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        response = requests.post(deletestock_api_url, json=data, headers=headers)

        if response.status_code == 201:
            print({"message": "Stock Deleted successfully"})
        else:
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

KATHMANDU_TZ = ZoneInfo("Asia/Kathmandu")

def parse_frontend_datetime(date_str, time_str):
    """
    date_str: 'YYYY-MM-DD'
    time_str: 'H:MM AM/PM'
    """
    combined_str = f"{date_str} {time_str}"
    dt = datetime.strptime(combined_str, "%Y-%m-%d %I:%M %p")

    # make Kathmandu-timezone aware
    return dt.replace(tzinfo=KATHMANDU_TZ)


def get_operational_date_from_datetime(dt):
    """
    If time < 6:00 AM → previous day
    Else → same day
    Returns date as string: YYYY-MM-DD
    """
    shift_cutoff = time(6, 0)

    if dt.time() < shift_cutoff:
        op_date = dt.date() - timedelta(days=1)
    else:
        op_date = dt.date()

    return op_date.strftime("%Y-%m-%d")

def _sales_entry_fields(data):
    """Extra keys that tell accounting whether and how to create the sales entry."""
    info = data.get("sales_entry") or {"skip": True}
    if info.get("skip"):
        return {"skip_sales_entry": True}

    bill_no = info["sales_bill_no"]
    return {
        "bill_id": bill_no,
        "sales_bill_no": bill_no,
        "external_numbering": True,
        "fiscal_year": data["fiscal_Year"],
        "total_amount": str(round(Decimal(str(data["Total"])), 2)),
        "vat_amount": str(round(Decimal(str(data["VAT"])), 2)),
        "customer_name": data.get("GuestName"),
        "customer_pan": data.get("guestPAN"),
        "payment_mode": data["paymentMode"],
    }