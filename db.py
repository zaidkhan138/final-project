import sqlite3
from auth import hash_password

DB_NAME = "campusbus.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()

    conn.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT UNIQUE, password_hash TEXT,
        role TEXT, created_at TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS buses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT UNIQUE, name TEXT,
        capacity INTEGER, status TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS routes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, destination TEXT, description TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS schedules(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER, route_id INTEGER,
        departure_time TEXT, arrival_time TEXT,
        operating_days TEXT, status TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS trips(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER, schedule_id INTEGER, route_id INTEGER,
        travel_date TEXT, departure_time TEXT,
        capacity INTEGER, status TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_reference TEXT UNIQUE,
        user_id INTEGER, trip_id INTEGER,
        status TEXT, booked_at TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS waiting_list(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, trip_id INTEGER,
        position INTEGER, status TEXT, created_at TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS extra_bus_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_trip_id INTEGER, waiting_count INTEGER,
        status TEXT, assigned_trip_id INTEGER, created_at TEXT)""")

    conn.commit()
    conn.close()

def seed_data():
    conn = get_connection()

    # demo accounts
    conn.execute("""INSERT OR IGNORE INTO users
        (name, email, password_hash, role, created_at)
        VALUES ('Student User', 'student@college.edu', ?, 'student', '2026-01-01')""",
        (hash_password("student123"),))

    conn.execute("""INSERT OR IGNORE INTO users
        (name, email, password_hash, role, created_at)
        VALUES ('Campus Admin', 'admin@college.edu', ?, 'admin', '2026-01-01')""",
        (hash_password("admin123"),))

    conn.execute("""INSERT OR IGNORE INTO buses
        (bus_number, name, capacity, status)
        VALUES ('RJ14-CB01', 'Campus Bus 1', 40, 'Active')""")

    conn.execute("""INSERT OR IGNORE INTO buses
        (bus_number, name, capacity, status)
        VALUES ('RJ14-CB02', 'Campus Bus 2', 35, 'Active')""")

    conn.execute("""INSERT OR IGNORE INTO routes
        (source, destination, description)
        VALUES ('College Campus', 'Jaipur', 'Jaipur route')""")

    conn.execute("""INSERT OR IGNORE INTO routes
        (source, destination, description)
        VALUES ('College Campus', 'Ajmer', 'Ajmer route')""")

    bus = conn.execute("SELECT * FROM buses WHERE bus_number='RJ14-CB01'").fetchone()
    jaipur = conn.execute("SELECT * FROM routes WHERE destination='Jaipur'").fetchone()
    ajmer = conn.execute("SELECT * FROM routes WHERE destination='Ajmer'").fetchone()

    # Jaipur wala trip
    trip = conn.execute("SELECT id FROM trips WHERE travel_date='2026-11-28'").fetchone()
    if trip is None:
        conn.execute("""INSERT INTO trips
            (bus_id, route_id, travel_date, departure_time, capacity, status)
            VALUES (?, ?, '2026-11-28', '17:00', 40, 'Scheduled')""",
            (bus["id"], jaipur["id"]))

    # Ajmer wala trip
    trip = conn.execute("SELECT id FROM trips WHERE travel_date='2026-11-29'").fetchone()
    if trip is None:
        conn.execute("""INSERT INTO trips
            (bus_id, route_id, travel_date, departure_time, capacity, status)
            VALUES (?, ?, '2026-11-29', '16:30', 40, 'Scheduled')""",
            (bus["id"], ajmer["id"]))

    conn.commit()
    conn.close()
