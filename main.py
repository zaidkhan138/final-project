import uuid
from datetime import datetime

import jwt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from auth import SECRET_KEY, ALGORITHM, create_token, hash_password, verify_password
from db import get_connection, create_tables, seed_data

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str

class LoginData(BaseModel):
    email: str
    password: str

class BusData(BaseModel):
    bus_number: str
    name: str
    capacity: int

class RouteData(BaseModel):
    source: str
    destination: str
    description: str = ""

class ScheduleData(BaseModel):
    bus_id: int
    route_id: int
    departure_time: str
    arrival_time: str
    operating_days: str

class TripData(BaseModel):
    bus_id: int
    route_id: int
    travel_date: str
    departure_time: str

class BookingData(BaseModel):
    trip_id: int

class AssignData(BaseModel):
    bus_id: int

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_user(token: str = Depends(oauth2)):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": int(data["sub"]), "role": data["role"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_admin(user=Depends(get_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

def confirmed(conn, trip_id):
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM bookings WHERE trip_id=? AND status='Confirmed'",
        (trip_id,)
    ).fetchone()
    return row["count"]

def waiting(conn, trip_id):
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM waiting_list WHERE trip_id=? AND status='Waiting'",
        (trip_id,)
    ).fetchone()
    return row["count"]

def promote(conn, trip_id):
    # pehla waiting student
    student = conn.execute("""
        SELECT * FROM waiting_list
        WHERE trip_id=? AND status='Waiting'
        ORDER BY position ASC LIMIT 1
    """, (trip_id,)).fetchone()

    trip = conn.execute("SELECT * FROM trips WHERE id=?", (trip_id,)).fetchone()
    if student and confirmed(conn, trip_id) < trip["capacity"]:
        conn.execute("""
            INSERT INTO bookings(booking_reference, user_id, trip_id, status, booked_at)
            VALUES (?, ?, ?, 'Confirmed', ?)
        """, ("CB-" + uuid.uuid4().hex[:8].upper(), student["user_id"], trip_id, now()))
        conn.execute("UPDATE waiting_list SET status='Promoted' WHERE id=?", (student["id"],))

def extra_request(conn, trip_id):
    count = waiting(conn, trip_id)
    if count < 15:
        return

    old = conn.execute(
        "SELECT id FROM extra_bus_requests WHERE original_trip_id=? AND status='Pending'",
        (trip_id,)
    ).fetchone()
    if old is None:
        conn.execute("""
            INSERT INTO extra_bus_requests(original_trip_id, waiting_count, status, created_at)
            VALUES (?, ?, 'Pending', ?)
        """, (trip_id, count, now()))

# yahin sab table banenge
create_tables()
seed_data()

@app.post("/auth/register", status_code=201)
def register(data: RegisterData):
    if not data.email.endswith("@college.edu"):
        raise HTTPException(status_code=400, detail="College email use karo")
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Password same nahi hai")

    conn = get_connection()
    old = conn.execute("SELECT id FROM users WHERE email=?", (data.email,)).fetchone()
    if old:
        conn.close()
        raise HTTPException(status_code=400, detail="Already registered")

    conn.execute("""
        INSERT INTO users(name, email, password_hash, role, created_at)
        VALUES (?, ?, ?, 'student', ?)
    """, (data.name, data.email, hash_password(data.password), now()))
    conn.commit()
    conn.close()
    return {"message": "Registration successful"}

@app.post("/auth/login")
def login(data: LoginData):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email=?", (data.email,)).fetchone()
    conn.close()

    if user is None or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], user["email"], user["role"])
    return {"access_token": token, "token_type": "bearer",
            "role": user["role"], "name": user["name"]}

@app.get("/trips")
def get_trips(user=Depends(get_user)):
    conn = get_connection()
    rows = conn.execute("""
        SELECT trips.*, routes.source, routes.destination
        FROM trips
        JOIN routes ON trips.route_id=routes.id
        WHERE trips.status='Scheduled'
    """).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["confirmed"] = confirmed(conn, row["id"])
        item["available"] = row["capacity"] - item["confirmed"]
        item["waiting"] = waiting(conn, row["id"])
        result.append(item)
    conn.close()
    return result

@app.post("/bookings", status_code=201)
def make_booking(data: BookingData, user=Depends(get_user)):
    conn = get_connection()
    trip = conn.execute("SELECT * FROM trips WHERE id=?", (data.trip_id,)).fetchone()
    if trip is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Trip not found")

    old = conn.execute("""
        SELECT id FROM bookings
        WHERE user_id=? AND trip_id=? AND status='Confirmed'
    """, (user["id"], data.trip_id)).fetchone()
    if old:
        conn.close()
        raise HTTPException(status_code=400, detail="Already booked")

    count = confirmed(conn, data.trip_id)
    if count < trip["capacity"]:
        ref = "CB-" + uuid.uuid4().hex[:8].upper()
        conn.execute("""
            INSERT INTO bookings(booking_reference, user_id, trip_id, status, booked_at)
            VALUES (?, ?, ?, 'Confirmed', ?)
        """, (ref, user["id"], data.trip_id, now()))
        conn.commit()
        conn.close()
        return {"status": "Confirmed", "booking_reference": ref}

    position = waiting(conn, data.trip_id) + 1
    conn.execute("""
        INSERT INTO waiting_list(user_id, trip_id, position, status, created_at)
        VALUES (?, ?, ?, 'Waiting', ?)
    """, (user["id"], data.trip_id, position, now()))
    extra_request(conn, data.trip_id)
    conn.commit()
    conn.close()
    return {"status": "Waiting", "position": position}

@app.get("/bookings/my")
def my_bookings(user=Depends(get_user)):
    conn = get_connection()
    bookings = conn.execute("""
        SELECT bookings.*, trips.travel_date, trips.departure_time,
               routes.source, routes.destination
        FROM bookings
        JOIN trips ON bookings.trip_id=trips.id
        JOIN routes ON trips.route_id=routes.id
        WHERE bookings.user_id=?
    """, (user["id"],)).fetchall()

    waiting_rows = conn.execute("""
        SELECT waiting_list.*, trips.travel_date, trips.departure_time,
               routes.source, routes.destination
        FROM waiting_list
        JOIN trips ON waiting_list.trip_id=trips.id
        JOIN routes ON trips.route_id=routes.id
        WHERE waiting_list.user_id=?
    """, (user["id"],)).fetchall()
    conn.close()
    return {"bookings": [dict(row) for row in bookings],
            "waiting_list": [dict(row) for row in waiting_rows]}

@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int, user=Depends(get_user)):
    conn = get_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    conn.execute("UPDATE bookings SET status='Cancelled' WHERE id=?", (booking_id,))
    promote(conn, booking["trip_id"])
    conn.commit()
    conn.close()
    return {"message": "Cancelled"}

@app.get("/buses")
def buses(user=Depends(get_user)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM buses").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/buses", status_code=201)
def add_bus(data: BusData, user=Depends(get_admin)):
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO buses(bus_number, name, capacity, status)
        VALUES (?, ?, ?, 'Active')
    """, (data.bus_number, data.name, data.capacity))
    conn.commit()
    id = cursor.lastrowid
    conn.close()
    return {"id": id, "message": "Bus added"}

@app.put("/buses/{bus_id}")
def update_bus(bus_id: int, data: BusData, user=Depends(get_admin)):
    conn = get_connection()
    conn.execute("""
        UPDATE buses SET bus_number=?, name=?, capacity=? WHERE id=?
    """, (data.bus_number, data.name, data.capacity, bus_id))
    conn.commit()
    conn.close()
    return {"message": "Bus updated"}

@app.delete("/buses/{bus_id}")
def deactivate_bus(bus_id: int, user=Depends(get_admin)):
    conn = get_connection()
    conn.execute("UPDATE buses SET status='Inactive' WHERE id=?", (bus_id,))
    conn.commit()
    conn.close()
    return {"message": "Bus deactivated"}

@app.get("/routes")
def routes(user=Depends(get_user)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM routes").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/routes", status_code=201)
def add_route(data: RouteData, user=Depends(get_admin)):
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO routes(source, destination, description)
        VALUES (?, ?, ?)
    """, (data.source, data.destination, data.description))
    conn.commit()
    id = cursor.lastrowid
    conn.close()
    return {"id": id, "message": "Route added"}

@app.get("/admin/extra-bus-requests")
def extra_bus_requests(user=Depends(get_admin)):
    conn = get_connection()
    rows = conn.execute("""
        SELECT extra_bus_requests.*, routes.source, routes.destination
        FROM extra_bus_requests
        JOIN trips ON extra_bus_requests.original_trip_id=trips.id
        JOIN routes ON trips.route_id=routes.id
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/admin/extra-bus-requests/{request_id}/approve")
def approve(request_id: int, user=Depends(get_admin)):
    conn = get_connection()
    conn.execute("UPDATE extra_bus_requests SET status='Approved' WHERE id=?", (request_id,))
    conn.commit()
    conn.close()
    return {"message": "Approved"}

@app.post("/admin/extra-bus-requests/{request_id}/reject")
def reject(request_id: int, user=Depends(get_admin)):
    conn = get_connection()
    conn.execute("UPDATE extra_bus_requests SET status='Rejected' WHERE id=?", (request_id,))
    conn.commit()
    conn.close()
    return {"message": "Rejected"}

@app.post("/admin/extra-bus-requests/{request_id}/assign")
def assign(request_id: int, data: AssignData, user=Depends(get_admin)):
    conn = get_connection()
    request = conn.execute("SELECT * FROM extra_bus_requests WHERE id=?", (request_id,)).fetchone()
    bus = conn.execute("SELECT * FROM buses WHERE id=?", (data.bus_id,)).fetchone()
    original = conn.execute("SELECT * FROM trips WHERE id=?", (request["original_trip_id"],)).fetchone()
    waiting_rows = conn.execute("""
        SELECT * FROM waiting_list
        WHERE trip_id=? AND status='Waiting'
        ORDER BY position
    """, (request["original_trip_id"],)).fetchall()

    cursor = conn.execute("""
        INSERT INTO trips(bus_id, route_id, travel_date, departure_time, capacity, status)
        VALUES (?, ?, ?, ?, ?, 'Scheduled')
    """, (bus["id"], original["route_id"], original["travel_date"],
          original["departure_time"], bus["capacity"]))
    new_trip_id = cursor.lastrowid

    for student in waiting_rows:
        conn.execute("""
            INSERT INTO bookings(booking_reference, user_id, trip_id, status, booked_at)
            VALUES (?, ?, ?, 'Confirmed', ?)
        """, ("CB-" + uuid.uuid4().hex[:8].upper(), student["user_id"], new_trip_id, now()))
        conn.execute("UPDATE waiting_list SET status='Promoted' WHERE id=?", (student["id"],))

    conn.execute("""
        UPDATE extra_bus_requests SET status='Assigned', assigned_trip_id=? WHERE id=?
    """, (new_trip_id, request_id))
    conn.commit()
    conn.close()
    return {"message": "Bus assigned"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@app.get("/trips-page", response_class=HTMLResponse)
def trips_page(request: Request):
    return templates.TemplateResponse(request, "trips.html")

@app.get("/my-bookings", response_class=HTMLResponse)
def bookings_page(request: Request):
    return templates.TemplateResponse(request, "my_bookings.html")

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html")
