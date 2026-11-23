# Low-Level Design

## 1. Project Files

```text
main.py       FastAPI routes and Pydantic data models
auth.py       Password and JWT functions
db.py         SQLite connection, table creation, and demo data
templates/    Jinja2 HTML pages
static/       CSS and JavaScript files
```

## 2. Database Connection

The `get_connection()` function opens `campusbus.db` and sets `sqlite3.Row`, so query values can be read by column name.

```python
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
```

SQL values use `?` placeholders.

## 3. Authentication

### Password Hash

`hash_password()` creates a random salt and applies PBKDF2 with SHA-256.

The stored value format is:

```text
salt$password_hash
```

### Password Verification

`verify_password()` takes the salt from the saved value and hashes the entered password again.

### JWT Token

`create_token()` stores:

- user ID
- email
- role
- expiration time

## 4. Pydantic Models

The project uses simple Pydantic classes:

- `RegisterData`
- `LoginData`
- `BusData`
- `RouteData`
- `ScheduleData`
- `TripData`
- `BookingData`
- `AssignData`

## 5. Authentication Dependency

`get_user()` reads the bearer token and decodes it.

`get_admin()` calls `get_user()` and checks whether the role is `admin`.

## 6. Trip Availability

For one trip:

```text
confirmed_count = confirmed bookings
available_seats = trip capacity - confirmed_count
waiting_count = waiting entries with status Waiting
```

## 7. Booking Logic

The booking route:

1. Finds the trip.
2. Checks whether the student already has a confirmed booking.
3. Counts confirmed bookings.
4. Creates a confirmed booking if capacity is available.
5. Otherwise creates a waiting-list entry.
6. Calculates the next waiting position.

```python
position = waiting(conn, trip_id) + 1
```

## 8. Waiting List

Waiting entries are stored with a position number.

The first student has the smallest position.

After a confirmed booking is cancelled, `promote()` searches for the first waiting student and creates a confirmed booking for that student.

## 9. Cancellation Logic

The cancellation route:

1. Finds the booking.
2. Changes the status to `Cancelled`.
3. Calls `promote()` for the trip.
4. Saves the changes.

Cancelled bookings remain in the database for history.

## 10. Extra Bus Request Logic

`extra_request()` counts waiting students.

When the count reaches 15:

- A pending extra-bus request is inserted.
- Duplicate pending requests for the same trip are prevented.

The administrator can:

- Approve the request
- Reject the request
- Assign an additional bus

## 11. Extra Bus Assignment

The assignment route:

1. Finds the extra-bus request.
2. Finds the selected bus.
3. Finds the original trip.
4. Finds waiting students.
5. Creates a new trip.
6. Creates confirmed bookings for waiting students.
7. Changes their waiting status to `Promoted`.
8. Changes the request status to `Assigned`.

## 12. API Routes

### Authentication

- `POST /auth/register`
- `POST /auth/login`

### Trips and Bookings

- `GET /trips`
- `POST /bookings`
- `GET /bookings/my`
- `DELETE /bookings/{booking_id}`

### Administration

- `GET /buses`
- `POST /buses`
- `PUT /buses/{bus_id}`
- `DELETE /buses/{bus_id}`
- `GET /routes`
- `POST /routes`
- `GET /admin/extra-bus-requests`
- `POST /admin/extra-bus-requests/{request_id}/approve`
- `POST /admin/extra-bus-requests/{request_id}/reject`
- `POST /admin/extra-bus-requests/{request_id}/assign`

## 13. Frontend JavaScript

The frontend uses simple functions:

- `headers()` creates authorization headers
- `api()` sends Fetch requests
- `load()` loads dashboard data
- `loadTrips()` loads trips
- `showTrips()` renders trip cards
- `loadBookings()` loads booking history
- `loadAdmin()` loads buses and extra-bus requests
