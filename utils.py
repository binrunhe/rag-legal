import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def generate_6_digit_code() -> str:
    import secrets

    return f"{secrets.randbelow(1_000_000):06d}"


def _send_email_blocking(to_email: str, code: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD 未配置，无法发送验证码邮件")

    subject = "【法律智能体】邮箱验证码"
    body = (
        f"您好，\n\n您的验证码是：{code}\n"
        "验证码 10 分钟内有效，请勿泄露给他人。\n\n"
        "如果不是您本人操作，请忽略本邮件。"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("法律智能体", smtp_from))
    msg["To"] = to_email

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_from, [to_email], msg.as_string())


async def send_verification_email(to_email: str, code: str) -> None:
    await asyncio.to_thread(_send_email_blocking, to_email, code)
