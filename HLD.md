# High-Level Design

## 1. Overview

CampusBus is a web application for reserving seats on college buses. The system has a student side and an administrator side.

The application uses FastAPI to provide APIs and Jinja2 templates for pages. SQLite stores users, buses, routes, trips, bookings, waiting lists, and extra-bus requests.

## 2. Architecture

```text
Browser
   |
   | HTML, CSS, JavaScript
   v
Jinja2 Pages + FastAPI Routes
   |
   | Python functions and SQL queries
   v
SQLite Database
```

## 3. Main Components

### Frontend

The frontend contains login, registration, dashboard, trip, booking, and admin pages. JavaScript sends Fetch API requests and shows API responses in the browser.

### Backend

The FastAPI backend handles:

- Registration and login
- JWT authentication
- Student and admin authorization
- Bus and route operations
- Trip availability
- Booking and cancellation
- Waiting-list management
- Extra-bus requests

### Database

SQLite stores all application data.

## 4. Main Modules

### Authentication Module

Handles password hashing, password verification, login, JWT token creation, and protected routes.

### Bus and Route Module

Allows administrators to add and update buses and routes.

### Trip Module

Displays scheduled trips and calculates available seats.

### Booking Module

Creates confirmed reservations or adds students to waiting lists.

### Waiting List Module

Stores waiting students in FIFO order and promotes the first student after cancellation.

### Extra Bus Module

Creates a request when the waiting-list count reaches 15. Administrators can approve or reject the request.

## 5. Main Data Flow

### Login Flow

1. Student enters email and password.
2. Backend verifies the password.
3. A JWT token is generated.
4. Browser stores the token.
5. The token is sent with protected API requests.

### Booking Flow

1. Student opens the available trips page.
2. Backend calculates confirmed bookings and available seats.
3. If seats are available, a confirmed booking is created.
4. If seats are full, the student is added to the waiting list.
5. Booking history is updated.

### Cancellation Flow

1. Student cancels a confirmed booking.
2. The booking status becomes cancelled.
3. The first waiting student is promoted.

## 6. Database Tables

- `users`
- `buses`
- `routes`
- `schedules`
- `trips`
- `bookings`
- `waiting_list`
- `extra_bus_requests`

## 7. Security

- Passwords are stored as PBKDF2-SHA256 hashes
- JWT tokens expire after 60 minutes
- Admin routes require an admin role
- Students cannot cancel another student's booking

## 8. Deployment

The project can run locally with Uvicorn:

```powershell
uvicorn main:app --reload
```
