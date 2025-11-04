import mysql.connector
from mysql.connector import Error
import time

DB_NAME = "reservabook"

def _connect(database=None):
    """Create MySQL connection with retry logic"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="KATYAL0786",
                database=database,
                autocommit=True,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                connection_timeout=30,
            )
            return conn
        except Error as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Connection attempt {attempt + 1} failed: {e}")
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise

def get_connection():
    """Get database connection, creating DB and schema if needed"""
    try:
        return _connect(DB_NAME)
    except Error as e:
        if getattr(e, 'errno', None) == 1049 or 'Unknown database' in str(e):
            print(f"📦 Database '{DB_NAME}' not found. Creating...")
            root = _connect(None)
            cur = root.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.close()
            root.close()
            conn = _connect(DB_NAME)
            ensure_schema(conn)
            print(f"✅ Database '{DB_NAME}' created successfully!")
            return conn
        raise

def ensure_schema(conn):
    """Create tables and seed initial data"""
    cur = conn.cursor()
    
    # Create services table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INT PRIMARY KEY AUTO_INCREMENT,
            code VARCHAR(64) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            duration_min INT NOT NULL,
            price_cents INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # Create bookings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            service_code VARCHAR(64) NOT NULL,
            booking_date DATE NOT NULL,
            booking_time VARCHAR(16) NOT NULL,
            first_name VARCHAR(128) NOT NULL,
            last_name VARCHAR(128) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(32) NOT NULL,
            notes TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(code)
                ON DELETE RESTRICT ON UPDATE CASCADE,
            INDEX idx_date_time (booking_date, booking_time),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # Seed services if empty
    cur.execute("SELECT COUNT(*) FROM services")
    (count,) = cur.fetchone()
    if count == 0:
        print("🌱 Seeding initial services...")
        cur.executemany(
            "INSERT INTO services (code, name, duration_min, price_cents) VALUES (%s, %s, %s, %s)",
            [
                ("consultation", "Consultation", 30, 5000),
                ("repair", "Repair Service", 60, 8500),
                ("installation", "Installation", 120, 12000),
                ("maintenance", "Maintenance", 45, 6500),
            ],
        )
        print(f"✅ Seeded {cur.rowcount} services")
    
    cur.close()
    print("✅ Database schema ready!")

