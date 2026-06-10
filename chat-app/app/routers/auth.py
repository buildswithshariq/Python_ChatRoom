from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    from app.main import templates
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    from app.main import templates
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate
    if len(username.strip()) < 3:
        return RedirectResponse(url=f"/auth/register?error={quote('Username must be at least 3 characters')}", status_code=status.HTTP_302_FOUND)
    if len(password) < 6:
        return RedirectResponse(url=f"/auth/register?error={quote('Password must be at least 6 characters')}", status_code=status.HTTP_302_FOUND)

    # Check existing username
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        return RedirectResponse(url=f"/auth/register?error={quote('Username already taken')}", status_code=status.HTTP_302_FOUND)

    # Check existing email
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return RedirectResponse(url=f"/auth/register?error={quote('Email already registered')}", status_code=status.HTTP_302_FOUND)

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=60*60*24, samesite="lax", path="/")
    return response


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url=f"/auth/login?error={quote('Invalid credentials')}", status_code=status.HTTP_302_FOUND)

    token = create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=60*60*24, samesite="lax", path="/")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


@router.get("/me")
async def me(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"id": user.id, "username": user.username, "email": user.email}
