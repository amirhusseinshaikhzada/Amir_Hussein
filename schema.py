import os
import psycopg2

# استفاده از DATABASE_URL که توسط Railway در محیط (Environment) ست می‌شود
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """ایجاد اتصال به پایگاه داده PostgreSQL"""
    if not DATABASE_URL:
        raise ValueError("خطا: متغیر محیطی DATABASE_URL یافت نشد. مطمئن شوید در Railway ست شده است.")
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    """ایجاد جداول با ساختار PostgreSQL"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # ایجاد جدول کاربران
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT
            );
        """)

        # ایجاد جدول سرویس‌ها
        cur.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                admin_id TEXT NOT NULL
            );
        """)

        # ایجاد جدول اسلات‌ها (زمان‌های موجود)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                slot_id SERIAL PRIMARY KEY,
                service_id INTEGER REFERENCES services(service_id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'available'
            );
        """)

        # ایجاد جدول قرار ملاقات‌ها
        cur.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id),
                slot_id INTEGER REFERENCES slots(slot_id) UNIQUE
            );
        """)

        conn.commit()
        print("✅ جداول با موفقیت در PostgreSQL ایجاد شدند.")
    except Exception as e:
        conn.rollback()
        print(f"❌ خطا در ایجاد جداول: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_tables()