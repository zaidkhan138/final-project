// sab page ka JS yahin
const token = localStorage.getItem("campusbus_token")

function headers() {
  return {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json"
  }
}

async function api(url, options) {
  const res = await fetch(url, options)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Error")
  return data
}

// login
const loginForm = document.getElementById("loginForm")
if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault()
    try {
      const data = await api("/auth/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          email: document.getElementById("email").value,
          password: document.getElementById("password").value
        })
      })

      localStorage.setItem("campusbus_token", data.access_token)
      localStorage.setItem("campusbus_role", data.role)
      localStorage.setItem("campusbus_name", data.name)

      if (data.role == "admin") {
        window.location.href = "/admin"
      } else {
        window.location.href = "/dashboard"
      }
    } catch (error) {
      document.getElementById("message").textContent = error.message
    }
  })
}

// register
const registerForm = document.getElementById("registerForm")
if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault()
    try {
      const data = await api("/auth/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          name: document.getElementById("name").value,
          email: document.getElementById("email").value,
          password: document.getElementById("password").value,
          confirm_password: document.getElementById("confirmPassword").value
        })
      })
      document.getElementById("message").textContent = data.message
    } catch (error) {
      document.getElementById("message").textContent = error.message
    }
  })
}

// logout
const logout = document.getElementById("logoutBtn")
if (logout) {
  logout.addEventListener("click", () => {
    localStorage.clear()
    window.location.href = "/"
  })
}

// dashboard
const welcome = document.getElementById("welcome")
if (welcome) {
  welcome.textContent = "Welcome, " + localStorage.getItem("campusbus_name")

  async function load() {
    const trips = await api("/trips", {headers: headers()})
    const mine = await api("/bookings/my", {headers: headers()})

    document.getElementById("tripCount").textContent = trips.length
    document.getElementById("bookingCount").textContent = mine.bookings.length
    document.getElementById("waitingCount").textContent = mine.waiting_list.length

    const list = document.getElementById("tripList")
    list.innerHTML = ""
    trips.forEach((trip) => {
      const div = document.createElement("div")
      div.className = "item"
      div.innerHTML =
        "<b>" + trip.source + " to " + trip.destination + "</b>" +
        "<p>Date " + trip.travel_date +
        "<br>Time " + trip.departure_time +
        "<br>Seats " + trip.available + "</p>"
      list.append(div)
    })
  }
  load()
}

// trips
const tripList = document.getElementById("tripList")
const search = document.getElementById("search")
if (tripList && search) {
  let trips = []

  async function loadTrips() {
    trips = await api("/trips", {headers: headers()})
    showTrips()
  }

  function showTrips() {
    tripList.innerHTML = ""
    const text = search.value.toLowerCase()

    for (const trip of trips) {
      if ((trip.source + trip.destination).toLowerCase().includes(text)) {
        const div = document.createElement("div")
        div.className = "item"

        div.innerHTML =
          "<b>" + trip.source + " to " + trip.destination + "</b>" +
          "<p>Date " + trip.travel_date +
          "<br>Time " + trip.departure_time +
          "<br>Seats " + trip.available +
          "<br>Waiting " + trip.waiting + "</p>"

        const button = document.createElement("button")
        button.textContent = trip.available > 0 ? "Reserve" : "Join waiting"

        button.addEventListener("click", async () => {
          const result = await api("/bookings", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({trip_id: trip.id})
          })
          document.getElementById("status").textContent =
            result.status == "Confirmed" ? "Booking done" : "Waiting position " + result.position
          loadTrips()
        })

        div.append(button)
        tripList.append(div)
      }
    }
  }

  search.addEventListener("input", showTrips)
  loadTrips()
}

// my booking page
const bookingList = document.getElementById("bookingList")
if (bookingList) {
  async function loadBookings() {
    const data = await api("/bookings/my", {headers: headers()})
    bookingList.innerHTML = ""

    for (const booking of data.bookings) {
      const div = document.createElement("div")
      div.className = "item"
      div.innerHTML =
        "<b>" + booking.source + " to " + booking.destination + "</b>" +
        "<p>" + booking.status + "<br>" + booking.travel_date + "</p>"

      if (booking.status == "Confirmed") {
        const button = document.createElement("button")
        button.textContent = "Cancel"
        button.addEventListener("click", async () => {
          await api("/bookings/" + booking.id, {
            method: "DELETE",
            headers: headers()
          })
          loadBookings()
        })
        div.append(button)
      }

      bookingList.append(div)
    }

    const waitingList = document.getElementById("waitingList")
    waitingList.innerHTML = ""
    for (const wait of data.waiting_list) {
      const div = document.createElement("div")
      div.className = "item"
      div.innerHTML =
        "<b>Waiting</b><p>Position " + wait.position + "</p>"
      waitingList.append(div)
    }
  }
  loadBookings()
}

// admin page
const busForm = document.getElementById("busForm")
if (busForm) {
  async function loadAdmin() {
    const buses = await api("/buses", {headers: headers()})
    const requests = await api("/admin/extra-bus-requests", {headers: headers()})

    document.getElementById("busCount").textContent = buses.length
    document.getElementById("tripCount").textContent = "2"

    let pending = 0
    requests.forEach((x) => {
      if (x.status == "Pending") pending++
    })
    document.getElementById("requestCount").textContent = pending

    const busList = document.getElementById("busList")
    busList.innerHTML = ""
    for (const bus of buses) {
      const div = document.createElement("div")
      div.className = "item"
      div.innerHTML = "<b>" + bus.name + "</b><p>Seats " + bus.capacity + "</p>"
      busList.append(div)
    }

    const requestList = document.getElementById("requestList")
    requestList.innerHTML = ""
    for (const request of requests) {
      const div = document.createElement("div")
      div.className = "item"
      div.innerHTML =
        "<b>Waiting " + request.waiting_count + "</b>" +
        "<p>Status " + request.status + "</p>"

      if (request.status == "Pending") {
        const button = document.createElement("button")
        button.textContent = "Approve"
        button.addEventListener("click", async () => {
          await api("/admin/extra-bus-requests/" + request.id + "/approve", {
            method: "POST",
            headers: headers()
          })
          loadAdmin()
        })
        div.append(button)
      }

      if (request.status == "Approved") {
        const button = document.createElement("button")
        button.textContent = "Assign"
        button.addEventListener("click", async () => {
          await api("/admin/extra-bus-requests/" + request.id + "/assign", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({bus_id: 2})
          })
          loadAdmin()
        })
        div.append(button)
      }

      requestList.append(div)
    }
  }

  busForm.addEventListener("submit", async (event) => {
    event.preventDefault()
    await api("/buses", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({
        bus_number: document.getElementById("busNumber").value,
        name: document.getElementById("busName").value,
        capacity: Number(document.getElementById("busCapacity").value)
      })
    })
    busForm.reset()
    loadAdmin()
  })

  loadAdmin()
}
