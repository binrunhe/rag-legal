from datetime import datetime, timedelta, timezone
import os
import secrets
from typing import Any, Literal

from fastapi import APIRouter, Depends
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from utils import (
    EmailService,
    can_send_reset_code,
    can_send_register_code,
    delete_reset_code,
    delete_register_code,
    generate_6_digit_code,
    hash_password,
    get_reset_code_record,
    get_register_code_record,
    store_reset_code,
    store_register_code,
    verify_reset_code,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
RESET_CODE_EXPIRE_MINUTES = int(os.getenv("RESET_CODE_EXPIRE_MINUTES", "5"))
ADMIN_INVITE_CODE = os.getenv("ADMIN_INVITE_CODE", "").strip()
ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv("ADMIN_EMAILS", "").split(",")
    if email.strip()
}


class AuthStatus(BaseModel):
    status: Literal["success", "error"]
    msg: str


class APIResponse(BaseModel):
    status: Literal["success", "error"]
    data: Any | None = None
    msg: str


class UserData(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: Literal["user", "admin"] = "user"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "c0a8012e-6ef0-4d63-9c2d-7b7d89b2d5a1",
                "email": "test@example.com",
                "full_name": "张三",
                "role": "user",
            }
        }
    )


class TokenData(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 7200,
            }
        }
    )


class TokenPayloadData(BaseModel):
    payload: dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "payload": {
                    "sub": "c0a8012e-6ef0-4d63-9c2d-7b7d89b2d5a1",
                    "email": "test@example.com",
                    "role": "user",
                    "exp": 1776500000,
                }
            }
        }
    )


class SendCodeResponse(AuthStatus):
    data: None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": None,
                "msg": "验证码已发送",
            }
        }
    )


class RegisterData(BaseModel):
    user_id: str
    role: Literal["user", "admin"]


class RegisterResponse(AuthStatus):
    data: RegisterData

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {
                    "user_id": "xxx",
                    "role": "user",
                },
                "msg": "注册成功",
            }
        }
    )


class LoginData(BaseModel):
    token: TokenData
    user: UserData


class LoginResponse(AuthStatus):
    data: LoginData

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {
                    "token": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 7200,
                    },
                    "user": {
                        "id": "c0a8012e-6ef0-4d63-9c2d-7b7d89b2d5a1",
                        "email": "test@example.com",
                        "full_name": "张三",
                        "role": "user",
                    },
                },
                "msg": "登录成功",
            }
        }
    )


class ResetPasswordResponse(AuthStatus):
    data: None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": None,
                "msg": "密码已重置",
            }
        }
    )


class VerifyTokenResponse(AuthStatus):
    data: TokenPayloadData

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {
                    "payload": {
                        "sub": "c0a8012e-6ef0-4d63-9c2d-7b7d89b2d5a1",
                        "email": "test@example.com",
                        "role": "user",
                        "exp": 1776500000,
                    }
                },
                "msg": "JWT 校验通过",
            }
        }
    )


class SendCodeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "test@example.com", "purpose": "register"},
        }
    )

    email: EmailStr
    purpose: Literal["register", "reset"] = "reset"


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "test@example.com",
                "password": "abcdef",
                "full_name": "张三",
                "code": "123456",
                "invite_code": "ADMIN-INVITE",
            },
        }
    )

    email: EmailStr
    password: str = Field(min_length=6, max_length=1024)
    full_name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=6, max_length=6)
    invite_code: str | None = Field(default=None, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "test@example.com",
                "password": "abcdef",
            },
        }
    )

    email: EmailStr
    password: str = Field(min_length=6, max_length=1024)


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "test@example.com",
                "code": "123456",
                "new_password": "abcdef",
            },
        }
    )

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=1024)


class TokenVerifyRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            },
        }
    )

    token: str


class AuthError(Exception):
    def __init__(self, msg: str, status_code: int = 400):
        self.msg = msg
        self.status_code = status_code
        super().__init__(msg)


ERROR_RESPONSES = {
    400: {"model": APIResponse, "description": "Bad Request"},
    401: {"model": APIResponse, "description": "Unauthorized"},
    422: {"model": APIResponse, "description": "Validation Error"},
    404: {"model": APIResponse, "description": "Not Found"},
    409: {"model": APIResponse, "description": "Conflict"},
    429: {"model": APIResponse, "description": "Too Many Requests"},
    502: {"model": APIResponse, "description": "Bad Gateway"},
    500: {"model": APIResponse, "description": "Internal Server Error"},
}


def success(data: dict[str, Any], msg: str) -> APIResponse:
    return APIResponse(status="success", data=data, msg=msg)


def get_user_role(user: User) -> str:
    role = getattr(user, "role", None)
    return role if isinstance(role, str) and role else "user"


def build_register_response(user: User) -> RegisterResponse:
    return RegisterResponse(
        status="success",
        msg="注册成功，已开通会员权限",
        data=RegisterData(user_id=user.id, role=get_user_role(user)),
    )


def build_login_response(user: User, token_data: dict[str, Any]) -> LoginResponse:
    return LoginResponse(
        status="success",
        msg="登录成功",
        data={
            "token": token_data,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.username,
                "role": get_user_role(user),
            },
        },
    )


def create_access_token(user: User) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    role = get_user_role(user)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": role,
        "exp": int(expire_at.timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
    }


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise
    except JWTError as exc:
        raise AuthError("JWT 无效", status_code=401) from exc


def resolve_role(email: str, invite_code: str | None) -> str:
    if email in ADMIN_EMAILS:
        return "admin"

    if invite_code and ADMIN_INVITE_CODE and secrets.compare_digest(
        invite_code.strip(), ADMIN_INVITE_CODE
    ):
        return "admin"

    return "user"


@router.post(
    "/send-code",
    response_model=SendCodeResponse,
    responses=ERROR_RESPONSES,
)
async def send_code(payload: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower().strip()
    purpose = payload.purpose
    existing_user = await db.scalar(select(User).where(User.email == email))

    if purpose == "register":
        if existing_user:
            raise AuthError("邮箱已注册，请直接登录或使用找回密码", status_code=409)

        can_send, remaining_seconds = await can_send_register_code(email)
        if not can_send:
            raise AuthError(f"请 {remaining_seconds} 秒后再获取验证码", status_code=429)

        code = generate_6_digit_code()
        await store_register_code(email, code)

        try:
            await EmailService.send_verification_email(email, code)
        except Exception as exc:
            await delete_register_code(email)
            raise AuthError("验证码邮件发送失败，请稍后重试", status_code=502) from exc

        return SendCodeResponse(
            status="success",
            msg="注册验证码已发送",
            data=None,
        )

    if not existing_user:
        raise AuthError("邮箱未注册，请先注册账号", status_code=404)

    can_send, remaining_seconds = await can_send_reset_code(email)
    if not can_send:
        raise AuthError(f"请 {remaining_seconds} 秒后再获取验证码", status_code=429)

    code = generate_6_digit_code()
    await store_reset_code(email, code)

    try:
        await EmailService.send_reset_code_email(email, code)
    except Exception as exc:
        await delete_reset_code(email)
        raise AuthError("验证码邮件发送失败，请稍后重试", status_code=502) from exc

    return SendCodeResponse(
        status="success",
        msg="验证码已发送",
        data=None,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    responses=ERROR_RESPONSES,
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower().strip()
    full_name = payload.full_name.strip()
    role = resolve_role(email, payload.invite_code)
    code = payload.code.strip()

    existing_user = await db.scalar(select(User).where(User.email == email))

    if existing_user:
        raise AuthError("邮箱已注册，请直接登录或使用找回密码", status_code=409)

    code_record = await get_register_code_record(email)
    if not code_record:
        raise AuthError("验证码错误或已失效", status_code=400)

    expected_digest = str(code_record.get("code_digest") or "")
    if not expected_digest or not verify_reset_code(code, expected_digest):
        raise AuthError("验证码错误或已失效", status_code=400)

    password_hash = hash_password(payload.password)

    user = User(
        email=email,
        username=full_name,
        password_hash=password_hash,
        provider="local",
        role=role,
        tier="premium",
        is_premium=True,
        is_verified=True,
    )

    db.add(user)
    await delete_register_code(email)
    await db.commit()
    await db.refresh(user)

    welcome_msg = "注册成功"
    try:
        await EmailService.send_welcome_email(email, full_name, role)
        welcome_msg = "注册成功，欢迎邮件已发送"
    except Exception as exc:
        print(f"[auth][register] welcome email failed: {exc}")
        welcome_msg = "注册成功，但欢迎邮件发送失败"

    response = build_register_response(user)
    response.msg = welcome_msg
    return response


@router.post("/login", response_model=LoginResponse, responses=ERROR_RESPONSES)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower().strip()

    user = await db.scalar(select(User).where(User.email == email))
    if not user or not user.password_hash:
        raise AuthError("邮箱或密码错误", status_code=401)

    if not user.is_verified:
        raise AuthError("账号未完成验证", status_code=401)

    if not verify_password(payload.password, user.password_hash):
        raise AuthError("邮箱或密码错误", status_code=401)

    token_data = create_access_token(user)

    return build_login_response(user, token_data)


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    responses=ERROR_RESPONSES,
)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower().strip()
    code = payload.code.strip()

    # 验证验证码
    code_record = await get_reset_code_record(email)
    if not code_record:
        raise AuthError("验证码无效或已过期", status_code=400)

    expected_digest = str(code_record.get("code_digest") or "")
    if not expected_digest or not verify_reset_code(code, expected_digest):
        raise AuthError("验证码错误", status_code=400)

    # 仅允许已注册用户重置密码
    user = await db.scalar(select(User).where(User.email == email))

    if not user:
        raise AuthError("邮箱未注册，请先注册账号", status_code=404)

    # 已注册的用户：重置密码
    user.password_hash = hash_password(payload.new_password)
    user.is_verified = True
    user.provider = "local"
    user.is_premium = True
    user.tier = "premium"
    db.add(user)

    await delete_reset_code(email)
    await db.commit()
    await db.refresh(user)

    return ResetPasswordResponse(
        status="success",
        msg="密码已重置",
        data=None,
    )


@router.post("/token/verify", response_model=VerifyTokenResponse, responses=ERROR_RESPONSES)
async def verify_token(payload: TokenVerifyRequest):
    token_payload = decode_access_token(payload.token)
    return VerifyTokenResponse(
        status="success",
        msg="JWT 校验通过",
        data=TokenPayloadData(payload=token_payload),
    )
