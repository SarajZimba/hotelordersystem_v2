import json

def log_hotel_activity(cursor, outlet, action, description, reservation_id=None,
                       employee_id=None, employee_name=None, details=None, endpoint=None):
    """
    Writes one audit row using the caller's cursor, so it is committed or rolled
    back together with the action itself. Never raises: a logging problem must
    not break a check-in.
    """
    try:
        cursor.execute("""
            INSERT INTO hotel_activity_log
                (outlet, reservation_id, action, description,
                 employee_id, employee_name, details, endpoint, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Front Office')
        """, (
            outlet, reservation_id, action, description[:500],
            employee_id, employee_name,
            json.dumps(details, default=str) if details else None,
            endpoint
        ))
    except Exception:
        pass   # a failed INSERT only undoes that one statement in MySQL, the transaction continues


def get_employee_name(cursor, emp_id):
    if not emp_id:
        return None
    cursor.execute("SELECT userName FROM EmployeeLogin WHERE id = %s", (emp_id,))   # adjust table/column
    row = cursor.fetchone()
    return row["userName"] if row else None