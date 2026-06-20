# ChatBox - Real-Time Chat Application

ChatBox is a fast, lightweight, and real-time chat application built entirely with Python. It provides secure user authentication, the ability to create and join multiple chat rooms, and instant messaging capabilities using WebSockets. 

The application is designed using a modern Python stack, combining the speed of asynchronous backend programming with the simplicity of server-side rendered HTML, completely bypassing the need for a heavy frontend framework like React.

## 🚀 Tech Stack

- **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) - A high-performance, asynchronous web framework.
- **Real-Time Communication:** WebSockets (via FastAPI/Starlette) for instant message delivery and presence tracking.
- **Database:** SQLite (lightweight, serverless) with **aiosqlite** for non-blocking asynchronous queries.
- **ORM:** [SQLAlchemy (v2.0)](https://www.sqlalchemy.org/) - Maps database tables to Python objects.
- **Frontend / Templating:** [Jinja2](https://jinja.palletsprojects.com/) + HTML/CSS for server-side rendering, and **HTMX** for dynamic, zero-JavaScript UI updates (like the online member list).
- **Authentication:** JWT (JSON Web Tokens) stored securely in `HttpOnly` cookies, using `python-jose` and `bcrypt` for secure password hashing.

## ✨ Key Features

- **Secure Authentication:** User registration and login flows using JWTs securely passed via HttpOnly cookies to prevent XSS attacks.
- **Room Management:** Users can dynamically create new chat rooms or join existing ones.
- **Real-Time Messaging:** Instantly send and receive messages within rooms using bidirectional WebSockets.
- **Online Presence:** See who is currently online in a specific chat room in real-time.
- **Message History:** Recent chat history is preserved in the SQLite database and loaded automatically when joining a room.

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+ installed on your machine.

### 1. Clone the repository and navigate to the project directory
```bash
# Assuming you have downloaded the code into a folder named 'chat-app'
cd chat-app
```

### 2. Install Dependencies
It is recommended to use a virtual environment, but you can install the dependencies directly using `pip`:

```bash
python -m pip install -r requirements.txt
```

*(Note: Ensure you have packages like `fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite`, `python-jose[cryptography]`, `passlib`, `bcrypt`, and `jinja2` installed).*

### 3. Run the Development Server
Start the application using Uvicorn with the `--reload` flag so it automatically restarts when you make code changes:

```bash
python -m uvicorn app.main:app --reload
```

### 4. Access the App
Open your web browser and navigate to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

## 📁 Project Structure

```text
chat-app/
├── app/
│   ├── main.py            # The main FastAPI application and entry point
│   ├── auth.py            # Authentication logic, JWT generation, and password hashing
│   ├── config.py          # Environment variables and configuration settings
│   ├── database.py        # Database connection setup (SQLAlchemy & SQLite)
│   ├── models.py          # Database schemas (User, Room, Message, RoomMember)
│   ├── websocket.py       # WebSocket connection manager for real-time broadcasts
│   ├── routers/
│   │   ├── auth.py        # API routes for login, register, and logout
│   │   └── rooms.py       # API routes for listing, creating, and joining rooms
│   └── templates/         # Jinja2 HTML templates
│       ├── base.html      # The base layout template
│       ├── landing.html   # Homepage template
│       ├── login.html     # Login page template
│       ├── register.html  # Registration page template
│       ├── rooms.html     # Chat rooms dashboard
│       ├── chat.html      # The main real-time chat interface
│       └── partials/      # Reusable HTML snippets (e.g., HTMX member lists)
├── chat.db                # Auto-generated SQLite database file
└── requirements.txt       # Python dependencies
```

## 🚀 Before making app live

If you plan to deploy this application to a production environment (like AWS, Render, Heroku, or DigitalOcean), you must update several configurations to ensure it runs securely and efficiently at scale:

1. **Change the Database:**
   - Swap out the local SQLite database (`chat.db`) for a robust production database like **PostgreSQL** or **MySQL**.
   - Update the `DATABASE_URL` in `app/config.py` to point to your new production database URL.

2. **Update Security Keys:**
   - Change the `SECRET_KEY` in `app/config.py` to a strong, randomly generated secret string. Never use the default development key.

3. **Secure Cookies:**
   - Ensure your production server is using HTTPS.
   - Update the JWT cookie settings to include `secure=True` to ensure cookies are encrypted over the network.

4. **Disable Debug Mode:**
   - Run Uvicorn without the `--reload` flag in production.
   - Example: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
