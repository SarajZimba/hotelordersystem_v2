# import os
# import smtplib
# from email.message import EmailMessage

# from flask import Blueprint, request, jsonify
# from flask_cors import cross_origin

# app_file505 = Blueprint('app_file505', __name__)

# MAX_ATTACHMENT_MB = 10
# ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "xlsx", "xls", "csv", "docx", "txt"}

# def _allowed(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# @app_file505.route("/send_email_with_file", methods=["POST"])
# @cross_origin()
# def send_email_with_file():
#     try:
#         # -------- TOKEN --------
#         auth_header = request.headers.get("Authorization")
#         if not auth_header:
#             return {"error": "No token provided."}, 400
#         try:
#             token = auth_header.split(" ")[1]
#         except Exception:
#             return {"error": "Invalid Authorization header format."}, 400
#         if not token or not token_auth(token):
#             return {"error": "Invalid token."}, 400

#         # -------- FORM FIELDS (not JSON, because a file is attached) --------
#         to_email = (request.form.get("to") or "").strip()
#         subject = (request.form.get("subject") or "").strip()
#         body = request.form.get("body") or ""

#         if not to_email or not subject:
#             return {"error": "to and subject are required."}, 400

#         # -------- FILES --------
#         files = request.files.getlist("file")   # one or many files under the key "file"
#         files = [f for f in files if f and f.filename]

#         # -------- BUILD EMAIL --------
#         msg = EmailMessage()
#         msg["From"] = os.getenv("smtp_from") or os.getenv("smtp_user")
#         msg["To"] = to_email
#         msg["Subject"] = subject
#         msg.set_content(body)

#         for f in files:
#             if not _allowed(f.filename):
#                 return {"error": f"File type not allowed: {f.filename}"}, 400

#             data = f.read()
#             if len(data) > MAX_ATTACHMENT_MB * 1024 * 1024:
#                 return {"error": f"{f.filename} is larger than {MAX_ATTACHMENT_MB} MB."}, 400

#             maintype, _, subtype = (f.mimetype or "application/octet-stream").partition("/")
#             msg.add_attachment(
#                 data,
#                 maintype=maintype or "application",
#                 subtype=subtype or "octet-stream",
#                 filename=f.filename,
#             )

#         # -------- SEND --------
#         host = os.getenv("MAIL_SERVER")
#         port = int(os.getenv("MAIL_PORT", "587"))
#         with smtplib.SMTP(host, port, timeout=30) as server:
#             server.starttls()
#             server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
#             server.send_message(msg)

#         return jsonify({"message": "Email sent.", "attachments": len(files)}), 200

#     except Exception as e:
#         return {"error": str(e)}, 500



import os
import re
import smtplib
from email.message import EmailMessage
from root.auth.check import token_auth

import mysql.connector
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

app_file505 = Blueprint('app_file505', __name__)

MAX_ATTACHMENT_MB = 10
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "xlsx", "xls", "csv", "docx", "txt"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app_file505.route("/send_email_to_recipients", methods=["POST"])
@cross_origin()
def send_email_to_recipients():
    mydb = None
    cursor = None
    try:
        # -------- TOKEN --------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "No token provided."}, 400
        try:
            token = auth_header.split(" ")[1]
        except Exception:
            return {"error": "Invalid Authorization header format."}, 400
        if not token or not token_auth(token):
            return {"error": "Invalid token."}, 400

        # -------- FORM FIELDS --------
        # subject = (request.form.get("subject") or "").strip()
        # body = request.form.get("body") or ""
        subject = "Hotel sales report"
        body = "Please find the report attached."
        company_name = (request.form.get("company_name") or "").strip()   # optional filter
        user_group = (request.form.get("user_group") or "").strip()       # optional filter

        if not subject:
            return {"error": "subject is required."}, 400

        # -------- READ ATTACHMENTS ONCE --------
        attachments = []
        for f in request.files.getlist("file"):
            if not f or not f.filename:
                continue
            if not _allowed(f.filename):
                return {"error": f"File type not allowed: {f.filename}"}, 400
            data = f.read()
            if len(data) > MAX_ATTACHMENT_MB * 1024 * 1024:
                return {"error": f"{f.filename} is larger than {MAX_ATTACHMENT_MB} MB."}, 400
            maintype, _, subtype = (f.mimetype or "application/octet-stream").partition("/")
            attachments.append((data, maintype or "application", subtype or "octet-stream", f.filename))

        # -------- ACTIVE RECIPIENTS --------
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)

        query = """
            SELECT DISTINCT LOWER(TRIM(email)) AS email, name
            FROM mailrecipient
            WHERE status = 1
              AND email IS NOT NULL AND TRIM(email) <> ''
        """
        params = []
        if company_name:
            query += " AND Company_name = %s"
            params.append(company_name)
        if user_group:
            query += " AND user_group = %s"
            params.append(user_group)

        cursor.execute(query, params)
        recipients = cursor.fetchall()
        cursor.close(); cursor = None
        mydb.close(); mydb = None

        if not recipients:
            return {"error": "No active recipients found."}, 404

        # -------- SEND (one SMTP connection, one email per recipient) --------
        sender = os.getenv("MAIL_USERNAME") or os.getenv("MAIL_USERNAME")
        sent, failed = [], []

        with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT", "587")), timeout=30) as server:
            server.starttls()
            server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))

            for r in recipients:
                email = r["email"]
                if not EMAIL_RE.match(email):
                    failed.append({"email": email, "error": "Invalid email address."})
                    continue
                try:
                    msg = EmailMessage()
                    msg["From"] = sender
                    msg["To"] = f'{r["name"]} <{email}>' if r["name"] else email
                    msg["Subject"] = subject
                    msg.set_content(body)
                    for data, maintype, subtype, filename in attachments:
                        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
                    server.send_message(msg)
                    sent.append(email)
                except Exception as e:
                    failed.append({"email": email, "error": str(e)})

        return jsonify({
            "total_recipients": len(recipients),
            "sent_count": len(sent),
            "failed_count": len(failed),
            "sent": sent,
            "failed": failed,
        }), 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()