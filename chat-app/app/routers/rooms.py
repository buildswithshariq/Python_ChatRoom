from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_user
from app.database import get_db
from app.models import Message, Room, RoomMember, User

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_class=HTMLResponse)
async def list_rooms(request: Request, user=Depends(require_user), db: AsyncSession = Depends(get_db)):
    from app.main import templates

    result = await db.execute(
        select(Room, func.count(RoomMember.id).label("member_count"))
        .outerjoin(RoomMember, RoomMember.room_id == Room.id)
        .group_by(Room.id)
        .order_by(Room.created_at.desc())
    )
    rows = result.all()

    rooms = []
    for room, count in rows:
        rooms.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "created_by": room.created_by,
            "created_at": room.created_at,
            "member_count": count,
        })

    member_result = await db.execute(
        select(RoomMember.room_id).where(RoomMember.user_id == user.id)
    )
    joined_room_ids = set(row[0] for row in member_result.all())

    return templates.TemplateResponse("rooms.html", {
        "request": request,
        "user": user,
        "rooms": rooms,
        "joined_room_ids": joined_room_ids,
    })


@router.post("")
async def create_room(
    name: str = Form(...),
    description: str = Form(""),
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if len(name.strip()) < 2:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    name = name.strip()

    existing = await db.execute(select(Room).where(Room.name == name))
    if existing.scalar_one_or_none():
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)

    room = Room(name=name, description=description, created_by=user.id)
    db.add(room)
    await db.commit()
    await db.refresh(room)

    membership = RoomMember(room_id=room.id, user_id=user.id)
    db.add(membership)
    await db.commit()

    return RedirectResponse(url=f"/rooms/{room.id}", status_code=status.HTTP_302_FOUND)


@router.get("/{room_id}", response_class=HTMLResponse)
async def chat_room(
    request: Request,
    room_id: int,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    from app.main import templates

    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)

    member_result = await db.execute(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user.id)
    )
    if not member_result.scalar_one_or_none():
        membership = RoomMember(room_id=room_id, user_id=user.id)
        db.add(membership)
        await db.commit()

    msg_result = await db.execute(
        select(Message, User.username)
        .join(User, User.id == Message.user_id)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.asc())
        .limit(50)
    )
    msg_rows = msg_result.all()

    messages = []
    for msg, username in msg_rows:
        messages.append({
            "id": msg.id,
            "room_id": msg.room_id,
            "user_id": msg.user_id,
            "username": username,
            "content": msg.content,
            "created_at": msg.created_at,
        })

    member_list = await db.execute(
        select(User.id, User.username)
        .join(RoomMember, RoomMember.user_id == User.id)
        .where(RoomMember.room_id == room_id)
    )
    from app.websocket import manager
    online_users = manager.get_online_users(room_id)
    online_ids = {u["user_id"] for u in online_users}
    members = [{"id": u_id, "username": u_name, "online": u_id in online_ids} for u_id, u_name in member_list.all()]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": user,
        "room": room,
        "messages": messages,
        "members": members,
    })


@router.post("/{room_id}/join")
async def join_room(
    room_id: int,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user.id)
    )
    if not existing.scalar_one_or_none():
        membership = RoomMember(room_id=room_id, user_id=user.id)
        db.add(membership)
        await db.commit()

    return RedirectResponse(url=f"/rooms/{room_id}", status_code=status.HTTP_302_FOUND)


@router.post("/{room_id}/leave")
async def leave_room(
    room_id: int,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user.id)
    )
    membership = result.scalar_one_or_none()
    if membership:
        await db.delete(membership)
        await db.commit()

    return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)


@router.get("/{room_id}/members", response_class=HTMLResponse)
async def room_members_partial(
    request: Request,
    room_id: int,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    from app.main import templates

    member_list = await db.execute(
        select(User.id, User.username)
        .join(RoomMember, RoomMember.user_id == User.id)
        .where(RoomMember.room_id == room_id)
    )
    members = [{"id": u_id, "username": u_name} for u_id, u_name in member_list.all()]

    from app.websocket import manager
    online = manager.get_online_users(room_id)
    online_ids = {u["user_id"] for u in online}

    for m in members:
        m["online"] = m["id"] in online_ids

    return templates.TemplateResponse("partials/member_list.html", {
        "request": request,
        "members": members,
        "room_id": room_id,
    })
