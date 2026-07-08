import sqlite3
import os
import pandas as pd
import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "kigalirent.db")
CSV_PATH = os.path.join(BASE_DIR, "Kigali_Rental_Dataset1.csv")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if users table has old username column, drop if present to run migrations
    try:
        cursor.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cursor.fetchall()]
        if cols and "username" in cols:
            print("Detected legacy users table (username-based). Recreating for phone-based auth...")
            cursor.execute("DROP TABLE users")
            cursor.execute("DROP TABLE inquiries")
            conn.commit()
    except Exception as e:
        print(f"Migration check error: {e}")
    
    # 1. Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            phone TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # 2. Create inquiries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            customer_phone TEXT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            move_in_date TEXT,
            budget TEXT,
            notes TEXT,
            property_type TEXT,
            location TEXT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            amenities_count INTEGER,
            furnished_status TEXT,
            parking TEXT,
            security TEXT,
            road_access TEXT,
            rent_min REAL,
            rent_max REAL,
            whatsapp_sent INTEGER DEFAULT 0
        )
    ''')
    
    # 3. Create listings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monthly_rent_rwf REAL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            amenities_count INTEGER,
            location TEXT,
            property_type TEXT,
            furnished_status TEXT,
            parking TEXT,
            security TEXT,
            road_access TEXT,
            review_note TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Import dataset CSV if database is newly initialized
    import_csv_if_empty()
    seed_realistic_inquiries()

def import_csv_if_empty():
    """Import dataset from CSV into SQLite listings table if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM listings")
    count = cursor.fetchone()[0]
    
    if count == 0 and os.path.exists(CSV_PATH):
        try:
            print("Importing Kigali rental dataset CSV into listings table...")
            df = pd.read_csv(CSV_PATH)
            # Fill NaNs where appropriate
            df = df.where(pd.notnull(df), None)
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO listings (
                        monthly_rent_rwf, bedrooms, bathrooms, amenities_count, 
                        location, property_type, furnished_status, parking, 
                        security, road_access, review_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('monthly_rent_rwf'),
                    row.get('bedrooms'),
                    row.get('bathrooms'),
                    row.get('amenities_count'),
                    row.get('location'),
                    row.get('property_type'),
                    row.get('furnished_status'),
                    row.get('parking'),
                    row.get('security'),
                    row.get('road_access'),
                    row.get('review_note')
                ))
            conn.commit()
            print(f"Successfully imported {len(df)} listings.")
        except Exception as e:
            print(f"Failed to import listings CSV: {e}")
    conn.close()

# ─── USER DATA OPERATIONS ───

def load_users():
    """Retrieve all users as list of dicts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def find_user_by_phone(phone):
    """Find a single user by phone number."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def find_user_by_email(email):
    """Find a single user by email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def find_user_by_id(user_id):
    """Find user details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_user(user_id, phone, name, email, password_hash, role, status):
    """Add a new user record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.datetime.utcnow().isoformat() + "Z"
    try:
        cursor.execute('''
            INSERT INTO users (id, phone, name, email, password_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, phone, name, email, password_hash, role, status, created_at))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_user_status(user_id, status):
    """Update status of a user account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
    conn.commit()
    conn.close()

# ─── INQUIRY DATA OPERATIONS ───

def load_inquiries():
    """Retrieve all inquiries as list of dicts formatted with nested property info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inquiries ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    inquiries = []
    for r in rows:
        d = dict(r)
        # Nest property info to match JSON format
        d["property"] = {
            "property_type": d.pop("property_type"),
            "location": d.pop("location"),
            "bedrooms": d.pop("bedrooms"),
            "bathrooms": d.pop("bathrooms"),
            "amenities_count": d.pop("amenities_count"),
            "furnished_status": d.pop("furnished_status"),
            "parking": d.pop("parking"),
            "security": d.pop("security"),
            "road_access": d.pop("road_access"),
            "rent_min": d.pop("rent_min"),
            "rent_max": d.pop("rent_max")
        }
        d["whatsapp_sent"] = bool(d["whatsapp_sent"])
        inquiries.append(d)
    return inquiries

def save_inquiry(inq):
    """Persist a new customer inquiry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    prop = inq.get("property", {})
    cursor.execute('''
        INSERT INTO inquiries (
            id, timestamp, customer_id, customer_phone, name, phone, email, 
            move_in_date, budget, notes, property_type, location, bedrooms, 
            bathrooms, amenities_count, furnished_status, parking, security, 
            road_access, rent_min, rent_max, whatsapp_sent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        inq["id"],
        inq["timestamp"],
        inq["customer_id"],
        inq.get("customer_phone"),
        inq["name"],
        inq["phone"],
        inq["email"],
        inq.get("move_in_date"),
        inq.get("budget"),
        inq.get("notes"),
        prop.get("property_type"),
        prop.get("location"),
        prop.get("bedrooms"),
        prop.get("bathrooms"),
        prop.get("amenities_count"),
        prop.get("furnished_status"),
        prop.get("parking"),
        prop.get("security"),
        prop.get("road_access"),
        prop.get("rent_min"),
        prop.get("rent_max"),
        1 if inq.get("whatsapp_sent") else 0
    ))
    conn.commit()
    conn.close()

def update_inquiry_whatsapp_sent(inquiry_id, sent):
    """Update WhatsApp notification success status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE inquiries SET whatsapp_sent = ? WHERE id = ?", (1 if sent else 0, inquiry_id))
    conn.commit()
    conn.close()

# ─── REAL DATA DYNAMIC SQL ANALYTICS ───

def get_listings_stats():
    """Query listings data dynamically to return aggregate stats."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total listings and overall average rent
    cursor.execute("SELECT COUNT(*), AVG(monthly_rent_rwf) FROM listings WHERE review_note IS NULL")
    total_count, avg_rent = cursor.fetchone()
    total_count = total_count or 0
    avg_rent = avg_rent or 0.0
    
    # 2. Location Stats: average rent and count by location
    cursor.execute('''
        SELECT location, AVG(monthly_rent_rwf) as avg_rent, COUNT(*) as listing_count 
        FROM listings 
        WHERE review_note IS NULL 
        GROUP BY location 
        ORDER BY avg_rent DESC
    ''')
    location_rows = cursor.fetchall()
    location_stats = [dict(r) for r in location_rows]
    
    # 3. Property Type Stats: count and average by property type
    cursor.execute('''
        SELECT property_type, AVG(monthly_rent_rwf) as avg_rent, COUNT(*) as listing_count 
        FROM listings 
        WHERE review_note IS NULL 
        GROUP BY property_type
        ORDER BY listing_count DESC
    ''')
    property_rows = cursor.fetchall()
    property_stats = [dict(r) for r in property_rows]
    
    conn.close()
    
    return {
        "total_listings": total_count,
        "overall_avg_rent": avg_rent,
        "location_stats": location_stats,
        "property_stats": property_stats
    }

def seed_realistic_inquiries():
    """Seeds realistic inquiries to make the app look authentic for presentation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We will clear existing developer test entries to ensure presentation data is pristine
    cursor.execute("DELETE FROM inquiries")
    
    realistic_data = [
        {
            "id": "inq_20260708000001",
            "timestamp": "2026-07-08T09:30:00Z",
            "customer_id": "u_seeker_demo",
            "customer_phone": "+250788111111",
            "name": "Jean Luc Mugisha",
            "phone": "+250 788 123 456",
            "email": "j.mugisha@gmail.com",
            "move_in_date": "2026-08-01",
            "budget": "750000",
            "notes": "Looking for a spacious family home with a small garden. Access to a paved road is highly preferred.",
            "property_type": "House",
            "location": "Kibagabaga",
            "bedrooms": 3,
            "bathrooms": 2,
            "amenities_count": 4,
            "furnished_status": "Semi-Furnished",
            "parking": "Yes",
            "security": "Yes",
            "road_access": "Good",
            "rent_min": 680000,
            "rent_max": 890000,
            "whatsapp_sent": 1
        },
        {
            "id": "inq_20260708000002",
            "timestamp": "2026-07-07T18:05:00Z",
            "customer_id": "u_seeker_demo",
            "customer_phone": "+250788111111",
            "name": "Sandrine Uwera",
            "phone": "+250 785 654 321",
            "email": "s.uwera@workmail.rw",
            "move_in_date": "2026-07-25",
            "budget": "600000",
            "notes": "Professional seeking a modern apartment near government ministries. Must include reliable security and backup generator access.",
            "property_type": "Apartment",
            "location": "Kacyiru",
            "bedrooms": 2,
            "bathrooms": 2,
            "amenities_count": 3,
            "furnished_status": "Furnished",
            "parking": "Yes",
            "security": "Yes",
            "road_access": "Good",
            "rent_min": 480000,
            "rent_max": 620000,
            "whatsapp_sent": 1
        },
        {
            "id": "inq_20260708000003",
            "timestamp": "2026-07-06T14:22:00Z",
            "customer_id": "u_seeker_demo",
            "customer_phone": "+250788111111",
            "name": "David Mukunzi",
            "phone": "+250 782 333 444",
            "email": "david.m@kigalitech.co",
            "move_in_date": "2026-09-01",
            "budget": "350000",
            "notes": "Looking for an inclusive studio apartment with fast internet. Close proximity to Gisimenti dining and transport routes.",
            "property_type": "Apartment",
            "location": "Remera",
            "bedrooms": 1,
            "bathrooms": 1,
            "amenities_count": 2,
            "furnished_status": "Furnished",
            "parking": "No",
            "security": "Yes",
            "road_access": "Good",
            "rent_min": 290000,
            "rent_max": 390000,
            "whatsapp_sent": 0
        }
    ]
    
    for inq in realistic_data:
        cursor.execute('''
            INSERT INTO inquiries (
                id, timestamp, customer_id, customer_phone, name, phone, email, 
                move_in_date, budget, notes, property_type, location, bedrooms, 
                bathrooms, amenities_count, furnished_status, parking, security, 
                road_access, rent_min, rent_max, whatsapp_sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            inq["id"],
            inq["timestamp"],
            inq["customer_id"],
            inq["customer_phone"],
            inq["name"],
            inq["phone"],
            inq["email"],
            inq["move_in_date"],
            inq["budget"],
            inq["notes"],
            inq["property_type"],
            inq["location"],
            inq["bedrooms"],
            inq["bathrooms"],
            inq["amenities_count"],
            inq["furnished_status"],
            inq["parking"],
            inq["security"],
            inq["road_access"],
            inq["rent_min"],
            inq["rent_max"],
            inq["whatsapp_sent"]
        ))
    conn.commit()
    conn.close()
