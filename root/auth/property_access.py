import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()


def get_employee_properties(employee_id):
    """
    Returns a list of full property dicts (id, name, address, etc.)
    that the given employee has access to, via hotel_employee_property_access.
    Returns an empty list if employee_id is falsy or the employee has no access rows.
    """
    if not employee_id:
        return []

    try:
        mydb = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = mydb.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.*
            FROM hotel_company_property p
            JOIN hotel_employee_property_access a ON a.property_id = p.id
            WHERE a.employee_id = %s
            ORDER BY p.id DESC
        """, (employee_id,))

        properties = cursor.fetchall()
        mydb.close()
        return properties

    except Exception:
        try:
            mydb.close()
        except:
            pass
        return []