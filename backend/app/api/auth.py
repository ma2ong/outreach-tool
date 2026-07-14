from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app import auth

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    password: str


@router.get("/auth/status")
def status(request: Request):
    token = request.cookies.get(auth.COOKIE_NAME)
    return {"enabled": auth.enabled(), "authed": auth.verify_token(token)}


@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response):
    if not auth.enabled():
        return {"ok": True}
    ip = request.client.host if request.client else "?"
    if auth.locked_out(ip):
        raise HTTPException(status_code=429, detail="尝试次数过多，请 1 分钟后再试")
    if not auth.check_password(req.password, ip):
        raise HTTPException(status_code=401, detail="密码不对")
    response.set_cookie(auth.COOKIE_NAME, auth.issue_token(), httponly=True,
                        samesite="lax", max_age=30 * 24 * 3600)
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(auth.COOKIE_NAME)
    return {"ok": True}
