# A Developer's Guide to ChatBox (For MERN Developers)

Welcome to the internal developer guide! If you're coming from a MERN (MongoDB, Express, React, Node) background, this guide will bridge the conceptual gaps and help you understand how ChatBox functions under the hood.

## 1. The Big Picture: Monolithic Server-Side Rendering (SSR)
In a standard MERN stack, you have an API backend (Express) and a completely separate frontend (React). They run on different ports and communicate primarily via JSON over HTTP.

In ChatBox, we use a monolithic pattern. **FastAPI** handles the backend API routes, but it also directly injects data into HTML templates and sends fully formed web pages directly to the browser. There is no separate `localhost:3000` React application to manage.

## 2. Component Breakdown

### Express vs FastAPI (Routing)
- In Express, you define routes using `app.get('/path')` and `router.get('/path')`.
- In FastAPI, we use decorators like `@app.get("/path")` and `@router.get("/path")`.
- **Location in codebase:** Check `app/routers/rooms.py` and `app/routers/auth.py` to see how routes are grouped.

### Mongoose vs SQLAlchemy (Database)
Instead of NoSQL JSON documents (MongoDB/Mongoose), we use a structured relational SQL database (SQLite) managed by **SQLAlchemy**.
- Mongoose schemas map perfectly to SQLAlchemy Models.
- **Location:** `app/models.py`. Here you define the exact tables like `User` and `Room` and their columns.

### React vs Jinja2 + HTMX (Frontend)
Instead of JSX components loaded with `useState` and `useEffect`, we use **Jinja2** templates located in `app/templates/`.
When a route is requested, FastAPI passes Python objects (like arrays of rooms) into an `.html` file. Jinja2 renders loops (using `{% for room in rooms %}`) directly into pure HTML before sending it to the client.

**What about Reactivity? (HTMX)**
Normally, if you want a live-updating online member list, you'd use a React `useEffect` to poll an endpoint and `setState` to trigger a re-render.
Instead, we use a tiny library called **HTMX**. Inside `chat.html`, there is a JavaScript snippet:
```javascript
htmx.ajax('GET', '/rooms/1/members', {target: '#member-list', swap: 'innerHTML'})
```
This automatically fetches fresh HTML from the server and swaps it directly into the DOM without a page reload, completely replacing the need for complex React state management.

## 3. The Authentication Flow (JWT & Cookies)
In a typical MERN app, you might send a JWT back in a JSON response and store it in `localStorage` (which is vulnerable to Cross-Site Scripting or XSS attacks).

In ChatBox, we generate a JWT using `python-jose` and attach it to an **HttpOnly Cookie** (`response.set_cookie(...)`).
- **Why?** HttpOnly cookies absolutely cannot be read by JavaScript `document.cookie`, making them incredibly secure against XSS.
- The browser automatically attaches this cookie to every subsequent request, including WebSocket connections!
- FastAPI checks this cookie using the `require_user` dependency in `app/auth.py` to ensure the user is logged in before rendering sensitive pages.

## 4. Real-Time WebSockets
Socket.io is heavily used in the Node.js ecosystem for real-time chat. FastAPI, however, has native, built-in WebSocket support using standard Python `async/await`.
- **Location:** `app/websocket.py` holds the `ConnectionManager` class.
- When a user joins a room, their connection is stored in memory. When someone types a message, `manager.broadcast()` sends that JSON message instantly to all connected clients in that specific room.

## Summary of a Request Flow
1. **User clicks "Login":** Submits an HTML form sending a `POST /auth/login` request.
2. **Backend Processing:** FastAPI validates the password via `bcrypt`.
3. **Session Creation:** FastAPI generates a JWT token and returns an HTTP `302 Redirect` back to `/rooms` along with a `Set-Cookie` header.
4. **Final Render:** The browser automatically navigates to `GET /rooms` and attaches the cookie. FastAPI verifies the cookie using `require_user`, queries the SQLite database via SQLAlchemy, passes the resulting data to `rooms.html`, and Jinja2 renders the final page visible to the user.

Enjoy exploring the codebase!
