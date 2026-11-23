# CampusBus

CampusBus is a college bus reservation and waiting-list system built with FastAPI, SQLite, Jinja2, HTML, CSS, and JavaScript.

Students can view trips, reserve seats, join waiting lists, cancel bookings, and view their booking history. Administrators can manage buses and routes and handle extra-bus requests.

## Setup

1. Open a terminal in this folder.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Start the application:

   ```powershell
   uvicorn main:app --reload
   ```

4. Open `http://127.0.0.1:8000`.

## Test Accounts

- Student: `student@college.edu`
- Password: `student123`
- Admin: `admin@college.edu`
- Password: `admin123`

## Main Pages

- `/` - Login
- `/register` - Student registration
- `/dashboard` - Student dashboard
- `/trips-page` - Available trips and reservation
- `/my-bookings` - Booking history and waiting list
- `/admin` - Administrator dashboard

## API Documentation

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## Database

The application uses `campusbus.db` and the built-in `sqlite3` module.
Database tables and demo data are created automatically at startup.
