from fastapi.responses import Response
res = Response()
res.set_cookie(key="access_token", value="token123", httponly=True, max_age=86400, samesite="lax")
print(res.headers.get("set-cookie"))
