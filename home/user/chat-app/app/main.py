from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_user
from app.config import ALGORITHM, SECRET_KEY, STATIC_DIR, TEMPLATES_DIR
from app.database import async_session, init_db, get_db
from app.models import Message, Room, RoomMember, User

from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.templating import Jinja2Templates


def setup_jinja() -> Jinja2Templates:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    def format_datetime(dt):
        if dt is None:
            return ""
        return dt.strftime("%b %d, %Y %I:%M %p")
    env.filters["format_datetime"] = format_datetime
    return Jinja2Templates(env=env)


templates = setup_jinja()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Create a default general room if none exists
    async with async_session() as session:
        result = await session.execute(select(Room).where(Room.name == "general"))
        if not result.scalar_one_or_none():
            # Need a user first — skip if no users
            user_result = await session.execute(select(User).limit(1))
            admin = user_result.scalar_one_or_none()
            if admin:
                room = Room(name="general", description="General chat room for everyone", created_by=admin.id)
                session.add(room)
                await session.commit()
    yield


app = FastAPI(title="ChatBox", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Include Routers ──────────────────────────────────────────────────────────
from app.routers import auth, rooms

app.include_router(auth.router)
app.include_router(rooms.router)


# ─── Pages ────────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/rooms", status_code=302)
    return templates.TemplateResponse("landing.html", {"request": request})


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────

from app.websocket import manager


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
):
    # Extract token from query parameter
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4001, reason="No token")
        return

    # Decode token to get user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            await websocket.close(code=4002, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=4002, reason="Invalid token")
        return

    # Verify user exists and belongs to room
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            await websocket.close(code=4003, reason="User not found")
            return

        result = await db.execute(select(Room).where(Room.id == room_id))
        room = result.scalar_one_or_none()
        if not room:
            await websocket.close(code=4004, reason="Room not found")
            return

        # Ensure membership
        member_result = await db.execute(
            select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
        )
        if not member_result.scalar_one_or_none():
            membership = RoomMember(room_id=room_id, user_id=user_id)
            db.add(membership)
            await db.commit()

        username = user.username

    await manager.connect(room_id, user_id, username, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Persist message to database
            async with async_session() as db:
                message = Message(
                    room_id=room_id,
                    user_id=user_id,
                    content=data,
                )
                db.add(message)
                await db.commit()
                await db.refresh(message)

            # Broadcast to room
            payload = {
                "type": "chat",
                "id": message.id,
                "room_id": room_id,
                "user_id": user_id,
                "username": username,
                "content": data,
                "timestamp": message.created_at.isoformat(),
            }
            await manager.broadcast(room_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        await manager.broadcast(
            room_id,
            {
                "type": "system",
                "content": f"{username} left the room",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        await manager.broadcast_user_list(room_id)
