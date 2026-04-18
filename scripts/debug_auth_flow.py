from __future__ import annotations

import asyncio
import traceback

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from api_server import app
from database import AsyncSessionLocal
from models import User
from utils import verify_password


TEST_EMAIL = "test_user@example.com"
TEST_PASSWORD = "TestUser123!"
TEST_FULL_NAME = "test_user"


async def load_user(email: str) -> User | None:
    async with AsyncSessionLocal() as db:
        return await db.scalar(select(User).where(User.email == email))


async def clear_user(email: str) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(User).where(User.email == email))
        await db.commit()


def main() -> None:
    with TestClient(app) as client:
        try:
            asyncio.run(clear_user(TEST_EMAIL))

            print("[1] 调用注册接口...")
            register_response = client.post(
                "/api/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "full_name": TEST_FULL_NAME,
                },
            )
            print("[register] status:", register_response.status_code)
            print("[register] body:", register_response.json())
            register_response.raise_for_status()

            print("[2] 查询数据库中的用户...")
            user = asyncio.run(load_user(TEST_EMAIL))
            if user is None:
                raise RuntimeError("注册成功但数据库中未找到用户")

            print("[db] user_id:", user.id)
            print("[db] email:", user.email)
            print("[db] full_name:", user.username)
            print("[db] password_hash:", user.password_hash)
            print("[db] password_is_hashed:", user.password_hash != TEST_PASSWORD)
            print("[db] password_verify:", verify_password(TEST_PASSWORD, user.password_hash or ""))

            if not user.password_hash or not verify_password(TEST_PASSWORD, user.password_hash):
                raise RuntimeError("数据库里的密码哈希校验失败")

            print("[3] 调用登录接口...")
            login_response = client.post(
                "/api/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                },
            )
            print("[login] status:", login_response.status_code)
            print("[login] body:", login_response.json())
            login_response.raise_for_status()

            print("[done] 注册、存库、密码校验、登录全部通过")
        except Exception:
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()
