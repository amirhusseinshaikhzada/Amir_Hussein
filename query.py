import os
import psycopg2
from dotenv import load_dotenv




load_dotenv()

# اتصال به دیتابیس PostgreSQL در Railway
DATABASE_URL = os.getenv('DATABASE_URL')

def connect():
    """ایجاد اتصال به PostgreSQL"""
    if not DATABASE_URL:
        raise ValueError("خطا: DATABASE_URL یافت نشد.")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    return conn, cursor

def insert_user(user_id, username):
    """تطبیق با جدول users (user_id, username)"""
    conn, cursor = connect()
    query = """
        INSERT INTO users (user_id, username) 
        VALUES (%s, %s) 
        ON CONFLICT (user_id) DO NOTHING
    """
    cursor.execute(query, (user_id, username))
    conn.commit()
    conn.close()

def get_services():
    """تطبیق با جدول services (service_id, name)"""
    conn, cursor = connect()
    cursor.execute("SELECT service_id, name FROM services")
    services = cursor.fetchall()
    conn.close()
    return services

def get_dates(service_id):
    """تطبیق با جدول slots (date)"""
    conn, cursor = connect()
    cursor.execute("SELECT DISTINCT date FROM slots WHERE service_id = %s", (service_id,))
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dates

def get_times(service_id, date):
    """تطبیق با جدول slots (slot_id, time)"""
    conn, cursor = connect()
    # اینجا از ستون time طبق اسکیما استفاده شده است
    query = """
        SELECT slot_id, time FROM slots
        WHERE service_id = %s AND date = %s AND status = 'available'
        ORDER BY time ASC
    """
    cursor.execute(query, (service_id, date))
    times = cursor.fetchall()
    conn.close()
    return times

def book_appointment(user_id, slot_id):
    """تطبیق با جدول appointments (user_id, slot_id)"""
    conn, cursor = connect()
    cursor.execute("INSERT INTO appointments (user_id, slot_id) VALUES (%s, %s)", (user_id, slot_id))
    conn.commit()
    conn.close()

def get_user_appointments(user_id):
    """
    دریافت رزروهای کاربر. 
    در SELECT از نام ستون‌ها بدون پیشوند استفاده شده تا خروجی دقیقاً مطابق با فیلدها باشد.
    """
    conn, cursor = connect()
    query = """
        SELECT slots.date, slots.time, services.name
        FROM appointments
        JOIN slots ON appointments.slot_id = slots.slot_id
        JOIN services ON slots.service_id = services.service_id
        WHERE appointments.user_id = %s
        ORDER BY slots.date, slots.time
    """
    cursor.execute(query, (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_admin_appointments(admin_id):
    """
    دریافت رزروها برای ادمین.
    در SELECT از نام ستون‌ها بدون پیشوند استفاده شده تا خروجی دقیقاً مطابق با فیلدها باشد.
    """
    conn, cursor = connect()
    query = """
        SELECT slots.date, slots.time, services.name, users.username
        FROM appointments
        JOIN slots ON appointments.slot_id = slots.slot_id
        JOIN services ON slots.service_id = services.service_id
        JOIN users ON appointments.user_id = users.user_id
        WHERE services.admin_id = %s
        ORDER BY slots.date, slots.time
    """
    cursor.execute(query, (admin_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def insert_slots(service_id, date, times):
    """تطبیق با جدول slots (service_id, date, time, status)"""
    conn, cursor = connect()
    for t in times:
        # ستون time دقیقاً مطابق اسکیما استفاده شده
        query = "INSERT INTO slots (service_id, date, time, status) VALUES (%s, %s, %s, 'available')"
        cursor.execute(query, (service_id, date, t))
    conn.commit()
    conn.close()

def update_slot_status(slot_id):
    """تطبیق با جدول slots (slot_id, status)"""
    conn, cursor = connect()
    cursor.execute("UPDATE slots SET status = 'booked' WHERE slot_id = %s", (slot_id,))
    conn.commit()
    conn.close()

def insert_service(name, admin_id):
    """تطبیق با جدول services (name, admin_id)"""
    conn, cursor = connect()
    query = "INSERT INTO services (name, admin_id) VALUES (%s, %s) RETURNING service_id"
    cursor.execute(query, (name, admin_id))
    service_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return service_id