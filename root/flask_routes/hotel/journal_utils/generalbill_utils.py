from datetime import date   # at the top of the file

GENERALBILL_CREDIT_MODES = {"credit", "roomcharge"}   # keys use _normalize_mode

# non-credit modes that PAYMENT_LEDGER_MAP doesn't cover
GENERALBILL_EXTRA_LEDGER_MAP = {
    "online": "Mobile Payments",   # assumption: online settles like mobile
}



from decimal import Decimal
import os, requests
import os
import requests
from decimal import Decimal

from .utils import JournalOutcomeUnknown, _check_journal_response, _normalize_mode, PAYMENT_LEDGER_MAP, _ledger_id
def _post_generalbill_entry(endpoint, journal_entry_data):
    headers = {
        "Authorization": f"Bearer {os.getenv('accounting_token')}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            os.getenv("accounting_url") + endpoint,
            json=[journal_entry_data],
            headers=headers,
            timeout=20,
        )
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise JournalOutcomeUnknown(
            "Accounting request timed out or the connection dropped; the entry may have been posted"
        )
    _check_journal_response(response)


def post_generalbill_and_create_journal(bill):
    """Post a general bill (LA/SPA/MB/TR) paid by CASH/CARD/ONLINE to accounting.
    Raises on any failure."""
    try:
        payment_mode = bill["payment_mode"]
        mode_key = _normalize_mode(payment_mode)
        if mode_key in GENERALBILL_CREDIT_MODES:
            raise ValueError(f"Normal journal called for payment mode '{payment_mode}'")

        total = round(Decimal(str(bill.get("grand_total") or 0)), 2)
        vat = round(Decimal(str(bill.get("tax_amount") or 0)), 2)
        taxable = round(Decimal(str(bill.get("taxable_amount") or 0)), 2)
        discount_amt = round(Decimal(str(bill.get("discount_amount") or 0)), 2)
        bill_no = bill["bill_number"]
        type_name = (bill.get("type_name") or "").strip()
        if not type_name:
            raise ValueError("type_name is required")
        bill_date = bill.get("bill_date") or date.today().strftime("%Y-%m-%d")

        if total <= 0:
            return

        sale_amount = total - vat

        # -------- LEDGERS FROM ACCOUNTING --------
        accounting_url = os.getenv("accounting_url")
        ledger_response = requests.get(accounting_url + "api/get-ledgers", timeout=10)
        ledger_response.raise_for_status()
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

        # -------- DEBIT SIDE --------
        ledger_name = PAYMENT_LEDGER_MAP.get(mode_key) or GENERALBILL_EXTRA_LEDGER_MAP.get(mode_key)
        if not ledger_name:
            raise ValueError(f"Unhandled payment mode for general bill: {payment_mode}")

        debit_ledgers = [_ledger_id(ledgers, ledger_name)]
        debit_particulars = [f"{type_name} bill payment for bill no: {bill_no}"]
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
            debit_particulars.append("Discount Expenses")
            debit_amounts.append(discount_amt)

        journal_entry_data = {
            "outlet_name": bill.get("outlet"),
            "bill_id": bill_no,
            "datetime": bill_date,
            "user": bill.get("created_by"),
            "debit_ledgers": debit_ledgers,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(a) for a in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(a) for a in credit_amounts],
            "billPrintTime": "",
            # used by accounting to create the sales entry and tax entry
            "customer_name": bill.get("customer_name"),
            "customer_pan": bill.get("customer_tax_number"),
            "total_amount": str(total),
            "vat_amount": str(vat),
            "taxable_amount": str(taxable),
            "fiscal_year": bill.get("fiscal_year"),
            "payment_mode": payment_mode,
            "sales_bill_no": bill_no,
            "sales_subledger_name": type_name,
            "external_numbering": True,
        }

        _post_generalbill_entry("api/create_journal_entry/", journal_entry_data)

    except Exception as error:
        print({"error": str(error)})
        raise


def post_generalbill_and_create_journal_for_creditbills(bill):
    """Post a general bill paid by CREDIT / ROOM CHARGE to accounting.
    Raises on any failure."""
    try:
        payment_mode = bill["payment_mode"]
        if _normalize_mode(payment_mode) not in GENERALBILL_CREDIT_MODES:
            raise ValueError(f"Credit journal called for payment mode '{payment_mode}'")

        total = round(Decimal(str(bill.get("grand_total") or 0)), 2)
        vat = round(Decimal(str(bill.get("tax_amount") or 0)), 2)
        taxable = round(Decimal(str(bill.get("taxable_amount") or 0)), 2)
        discount_amt = round(Decimal(str(bill.get("discount_amount") or 0)), 2)
        bill_no = bill["bill_number"]
        type_name = (bill.get("type_name") or "").strip()
        if not type_name:
            raise ValueError("type_name is required")
        bill_date = bill.get("bill_date") or date.today().strftime("%Y-%m-%d")

        # the debtor ledger is the guest or company, so both are required
        guest_id = str(bill.get("guest_id") or "").strip()
        party_name = (bill.get("customer_name") or "").strip()
        if not guest_id:
            raise ValueError("guestID is required for credit and room charge bills")
        if not party_name:
            raise ValueError("customer_name is required for credit and room charge bills")

        if total <= 0:
            return

        sale_amount = total - vat

        # -------- LEDGERS FROM ACCOUNTING --------
        accounting_url = os.getenv("accounting_url")
        ledger_response = requests.get(accounting_url + "api/get-ledgers", timeout=10)
        ledger_response.raise_for_status()
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}

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
            "outlet_name": bill.get("outlet"),
            "bill_id": bill_no,
            "datetime": bill_date,
            "user": bill.get("created_by"),
            "debit_ledgers": debit_ledgers,
            "debit_ledger_names": debit_ledger_names,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(a) for a in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(a) for a in credit_amounts],
            "billPrintTime": "",
            # used by accounting to create the sales entry and tax entry
            "customer_name": party_name,
            "customer_pan": bill.get("customer_tax_number"),
            "total_amount": str(total),
            "vat_amount": str(vat),
            "taxable_amount": str(taxable),
            "fiscal_year": bill.get("fiscal_year"),
            "payment_mode": payment_mode,
            "sales_bill_no": bill_no,
            "sales_subledger_name": type_name,
            "external_numbering": True,
        }

        _post_generalbill_entry("api/create_credit_journal_entry/", journal_entry_data)

    except Exception as error:
        print({"error": str(error)})
        raise