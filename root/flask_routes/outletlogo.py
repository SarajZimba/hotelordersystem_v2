from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app_file208 = Blueprint('app_file208', __name__)

# Import your token_auth function
from root.auth.check import token_auth

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Set upload folder to be inside 'root/uploads'
basedir = os.path.abspath(os.path.dirname(__file__))  # points to 'root/api' or wherever this file is
# Go up one level to 'root' folder
root_dir = os.path.abspath(os.path.join(basedir, '..'))
UPLOAD_FOLDER = os.path.join(root_dir, 'uploads')

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app_file208.route("/upload_outlet_logo", methods=["POST"])
@cross_origin()
def upload_outlet_logo():
    try:
        outlet = request.form.get("outlet")
        token = request.form.get("token")
        file = request.files.get("logo")

        if not token or not token_auth(token):
            return {"error": "Invalid or missing token"}, 400

        if not outlet:
            return {"error": "Missing outlet name"}, 400

        if not file or not allowed_file(file.filename):
            return {"error": "Invalid or missing logo file"}, 400

        # Secure filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Save file
        file.save(filepath)

        # Save filename to database
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor()

        update_sql = """
            UPDATE outetNames 
            SET logo = %s 
            WHERE Outlet = %s
        """
        cursor.execute(update_sql, (filename, outlet))
        mydb.commit()
        mydb.close()

        return {"message": "Logo uploaded successfully", "filename": filename}, 200

    except Exception as e:
        return {"error": str(e)}, 500


MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB
import uuid

@app_file208.route("/upload_hotel_logo", methods=["POST"])
@cross_origin()
def upload_hotel_logo():
    # -------- TOKEN (Authorization: Bearer <token>) --------
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No token provided."}, 400
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return {"error": "Invalid Authorization header format."}, 400
    if not token_auth(token):
        return {"error": "Invalid token."}, 400

    # -------- INPUT (multipart/form-data) --------
    property_id = request.form.get("property_id")
    hotel_name = (request.form.get("name") or "").strip()
    file = request.files.get("logo")

    if not property_id and not hotel_name:
        return {"error": "property_id or name is required."}, 400
    if not file or not file.filename or not allowed_file(file.filename):
        return {"error": "Invalid or missing logo file (png, jpg, jpeg, gif)."}, 400

    # size check without loading the file into memory
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size == 0:
        return {"error": "Empty file."}, 400
    if size > MAX_LOGO_BYTES:
        return {"error": "Logo must be 2 MB or smaller."}, 400

    mydb = None
    new_path = None
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database"),
        )
        cursor = mydb.cursor(dictionary=True)

        # -------- FIND THE HOTEL --------
        if property_id:
            cursor.execute(
                "SELECT id, logo FROM hotel_company_property WHERE id = %s",
                (property_id,),
            )
        else:
            cursor.execute(
                "SELECT id, logo FROM hotel_company_property WHERE name = %s LIMIT 1",
                (hotel_name,),
            )
        prop = cursor.fetchone()
        if not prop:
            return {"error": "Hotel not found."}, 404

        old_logo = prop["logo"]

        # -------- SAVE FILE (unique name, only after the hotel exists) --------
        ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
        filename = f"hotel_{prop['id']}_{uuid.uuid4().hex}.{ext}"
        new_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(new_path)

        # -------- UPDATE DB --------
        cursor.execute(
            "UPDATE hotel_company_property SET logo = %s WHERE id = %s",
            (filename, prop["id"]),
        )
        mydb.commit()

        # -------- REMOVE OLD LOGO FILE --------
        if old_logo:
            old_path = os.path.join(UPLOAD_FOLDER, os.path.basename(old_logo))
            if os.path.isfile(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass

        return {
            "message": "Hotel logo uploaded successfully",
            "property_id": prop["id"],
            "filename": filename,
        }, 200

    except Exception as e:
        if mydb:
            mydb.rollback()
        if new_path and os.path.isfile(new_path):
            try:
                os.remove(new_path)
            except OSError:
                pass
        return {"error": str(e)}, 500

    finally:
        if mydb:
            mydb.close()