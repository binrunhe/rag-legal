import asyncio
import importlib
import hashlib
import hmac
import json
import os
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any

from dotenv import load_dotenv
from passlib.context import CryptContext
from passlib.exc import MissingBackendError

load_dotenv()

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt_sha256", "bcrypt"],
    deprecated="auto",
    argon2__type="ID",
    argon2__memory_cost=int(os.getenv("ARGON2_MEMORY_COST", "19456")),
    argon2__time_cost=int(os.getenv("ARGON2_TIME_COST", "2")),
    argon2__parallelism=int(os.getenv("ARGON2_PARALLELISM", "1")),
    bcrypt__rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
)

_memory_reset_code_cache: dict[str, dict[str, Any]] = {}
_memory_reset_code_lock = asyncio.Lock()
_memory_register_code_cache: dict[str, dict[str, Any]] = {}
_memory_register_code_lock = asyncio.Lock()
_redis_client: Any | None = None

RESET_CODE_EXPIRE_MINUTES = int(os.getenv("RESET_CODE_EXPIRE_MINUTES", "5"))
RESET_CODE_EXPIRE_SECONDS = RESET_CODE_EXPIRE_MINUTES * 60
RESET_CODE_RESEND_INTERVAL_SECONDS = int(os.getenv("RESET_CODE_RESEND_INTERVAL_SECONDS", "60"))
RESET_CODE_CACHE_PREFIX = os.getenv("RESET_CODE_CACHE_PREFIX", "auth:reset-code")
REGISTER_CODE_EXPIRE_MINUTES = int(os.getenv("REGISTER_CODE_EXPIRE_MINUTES", str(RESET_CODE_EXPIRE_MINUTES)))
REGISTER_CODE_EXPIRE_SECONDS = REGISTER_CODE_EXPIRE_MINUTES * 60
REGISTER_CODE_RESEND_INTERVAL_SECONDS = int(
    os.getenv("REGISTER_CODE_RESEND_INTERVAL_SECONDS", str(RESET_CODE_RESEND_INTERVAL_SECONDS))
)
REGISTER_CODE_CACHE_PREFIX = os.getenv("REGISTER_CODE_CACHE_PREFIX", "auth:register-code")
RESET_CODE_SECRET = os.getenv("RESET_CODE_SECRET") or os.getenv("JWT_SECRET") or "change-me-in-production"


def _prehash_password(password: str) -> str:
    # Backward compatibility with a temporary migration strategy that pre-hashed before bcrypt.
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    import base64

    return base64.b64encode(digest).decode("ascii")


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("密码不能为空")

    last_error: Exception | None = None
    for scheme in ("argon2", "bcrypt_sha256", "bcrypt"):
        try:
            return pwd_context.hash(password, scheme=scheme)
        except MissingBackendError as exc:
            last_error = exc
            continue
        except Exception as exc:
            last_error = exc
            continue

    if last_error is not None:
        print(f"[auth][hash_password] all schemes failed: {type(last_error).__name__}: {last_error}")
    raise ValueError("密码哈希失败，请稍后重试")


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    # Preferred verification for Argon2/bcrypt_sha256/bcrypt hashes.
    try:
        if pwd_context.verify(plain_password, password_hash):
            return True
    except Exception:
        pass

    # Backward compatibility for temporary pre-hashed bcrypt hashes.
    try:
        return pwd_context.verify(_prehash_password(plain_password), password_hash)
    except Exception:
        return False


def generate_6_digit_code() -> str:
    import secrets

    return f"{secrets.randbelow(1_000_000):06d}"


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _reset_code_key(email: str) -> str:
    return f"{RESET_CODE_CACHE_PREFIX}:{_normalize_email(email)}"


def _register_code_key(email: str) -> str:
    return f"{REGISTER_CODE_CACHE_PREFIX}:{_normalize_email(email)}"


def _hash_reset_code(code: str) -> str:
    return hmac.new(
        RESET_CODE_SECRET.encode("utf-8"),
        code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _is_code_match(expected_digest: str, code: str) -> bool:
    return hmac.compare_digest(expected_digest, _hash_reset_code(code))


def verify_reset_code(code: str, expected_digest: str) -> bool:
    return _is_code_match(expected_digest, code)


async def _get_redis_client() -> Any | None:
    global _redis_client

    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None

    if _redis_client is None:
        try:
            redis_asyncio = importlib.import_module("redis.asyncio")
        except Exception:  # pragma: no cover - redis is optional
            return None

        _redis_client = redis_asyncio.from_url(redis_url, decode_responses=True)

    return _redis_client


def _current_timestamp() -> float:
    return time.time()


def _build_reset_code_record(code: str) -> dict[str, Any]:
    now = _current_timestamp()
    return {
        "code_digest": _hash_reset_code(code),
        "created_at": now,
        "expires_at": now + RESET_CODE_EXPIRE_SECONDS,
    }


def _build_code_record(code: str, expire_seconds: int) -> dict[str, Any]:
    now = _current_timestamp()
    return {
        "code_digest": _hash_reset_code(code),
        "created_at": now,
        "expires_at": now + expire_seconds,
    }


async def _store_code_record(
    email: str,
    code: str,
    expire_seconds: int,
    cache_prefix_key: str,
    memory_cache: dict[str, dict[str, Any]],
    memory_lock: asyncio.Lock,
) -> None:
    normalized_email = _normalize_email(email)
    record = _build_code_record(code, expire_seconds)
    redis_client = await _get_redis_client()

    if redis_client is not None:
        await redis_client.set(
            cache_prefix_key,
            json.dumps(record, ensure_ascii=False),
            ex=expire_seconds,
        )
        return

    async with memory_lock:
        memory_cache[normalized_email] = record


async def _get_code_record(
    email: str,
    cache_prefix_key: str,
    memory_cache: dict[str, dict[str, Any]],
    memory_lock: asyncio.Lock,
) -> dict[str, Any] | None:
    normalized_email = _normalize_email(email)
    redis_client = await _get_redis_client()

    if redis_client is not None:
        raw_record = await redis_client.get(cache_prefix_key)
        if not raw_record:
            return None
        try:
            record = json.loads(raw_record)
        except json.JSONDecodeError:
            await redis_client.delete(cache_prefix_key)
            return None

        expires_at = float(record.get("expires_at") or 0)
        if expires_at and expires_at <= _current_timestamp():
            await redis_client.delete(cache_prefix_key)
            return None

        return record

    async with memory_lock:
        record = memory_cache.get(normalized_email)
        if not record:
            return None

        expires_at = float(record.get("expires_at") or 0)
        if expires_at and expires_at <= _current_timestamp():
            memory_cache.pop(normalized_email, None)
            return None

        return record


async def _delete_code_record(
    email: str,
    cache_prefix_key: str,
    memory_cache: dict[str, dict[str, Any]],
    memory_lock: asyncio.Lock,
) -> None:
    normalized_email = _normalize_email(email)
    redis_client = await _get_redis_client()

    if redis_client is not None:
        await redis_client.delete(cache_prefix_key)
        return

    async with memory_lock:
        memory_cache.pop(normalized_email, None)


async def _can_send_code(
    email: str,
    cache_prefix_key: str,
    memory_cache: dict[str, dict[str, Any]],
    memory_lock: asyncio.Lock,
    resend_interval_seconds: int,
) -> tuple[bool, int]:
    record = await _get_code_record(email, cache_prefix_key, memory_cache, memory_lock)
    if not record:
        return True, 0

    created_at = float(record.get("created_at") or 0)
    elapsed = int(_current_timestamp() - created_at)
    remaining = max(0, resend_interval_seconds - elapsed)
    return remaining == 0, remaining


async def store_reset_code(email: str, code: str) -> None:
    await _store_code_record(
        email,
        code,
        RESET_CODE_EXPIRE_SECONDS,
        _reset_code_key(_normalize_email(email)),
        _memory_reset_code_cache,
        _memory_reset_code_lock,
    )


async def get_reset_code_record(email: str) -> dict[str, Any] | None:
    return await _get_code_record(
        email,
        _reset_code_key(_normalize_email(email)),
        _memory_reset_code_cache,
        _memory_reset_code_lock,
    )


async def delete_reset_code(email: str) -> None:
    await _delete_code_record(
        email,
        _reset_code_key(_normalize_email(email)),
        _memory_reset_code_cache,
        _memory_reset_code_lock,
    )


async def can_send_reset_code(email: str) -> tuple[bool, int]:
    return await _can_send_code(
        email,
        _reset_code_key(_normalize_email(email)),
        _memory_reset_code_cache,
        _memory_reset_code_lock,
        RESET_CODE_RESEND_INTERVAL_SECONDS,
    )


async def store_register_code(email: str, code: str) -> None:
    await _store_code_record(
        email,
        code,
        REGISTER_CODE_EXPIRE_SECONDS,
        _register_code_key(_normalize_email(email)),
        _memory_register_code_cache,
        _memory_register_code_lock,
    )


async def get_register_code_record(email: str) -> dict[str, Any] | None:
    return await _get_code_record(
        email,
        _register_code_key(_normalize_email(email)),
        _memory_register_code_cache,
        _memory_register_code_lock,
    )


async def delete_register_code(email: str) -> None:
    await _delete_code_record(
        email,
        _register_code_key(_normalize_email(email)),
        _memory_register_code_cache,
        _memory_register_code_lock,
    )


async def can_send_register_code(email: str) -> tuple[bool, int]:
    return await _can_send_code(
        email,
        _register_code_key(_normalize_email(email)),
        _memory_register_code_cache,
        _memory_register_code_lock,
        REGISTER_CODE_RESEND_INTERVAL_SECONDS,
    )


def _smtp_settings() -> dict[str, object]:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    use_ssl = os.getenv("SMTP_USE_SSL", "true").strip().lower() in {"1", "true", "yes", "on"}
    use_tls = os.getenv("SMTP_USE_TLS", "false").strip().lower() in {"1", "true", "yes", "on"}

    return {
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_password": smtp_password,
        "smtp_from": smtp_from,
        "use_ssl": use_ssl,
        "use_tls": use_tls,
    }


def _send_email_blocking(
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: str | None = None,
) -> None:
    settings = _smtp_settings()
    smtp_host = settings["smtp_host"]
    smtp_port = settings["smtp_port"]
    smtp_user = settings["smtp_user"]
    smtp_password = settings["smtp_password"]
    smtp_from = settings["smtp_from"]
    use_ssl = bool(settings["use_ssl"])
    use_tls = bool(settings["use_tls"])

    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD 未配置，无法发送邮件")

    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        msg = MIMEText(plain_body, "plain", "utf-8")

    msg["Subject"] = subject
    msg["From"] = formataddr(("法律智能体", smtp_from))
    msg["To"] = to_email

    if use_ssl:
        server_factory = smtplib.SMTP_SSL
        server_kwargs = {"context": ssl.create_default_context()}
    else:
        server_factory = smtplib.SMTP
        server_kwargs = {}

    with server_factory(smtp_host, smtp_port, **server_kwargs) as server:
        if not use_ssl and use_tls:
            server.starttls(context=ssl.create_default_context())
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_from, [to_email], msg.as_string())


async def send_email(
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: str | None = None,
) -> None:
    await asyncio.to_thread(_send_email_blocking, to_email, subject, plain_body, html_body)


class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        plain_body: str,
        html_body: str | None = None,
    ) -> None:
        await send_email(to_email, subject, plain_body, html_body)

    @staticmethod
    async def send_verification_email(to_email: str, code: str) -> None:
        await send_verification_email(to_email, code)

    @staticmethod
    async def send_reset_code_email(to_email: str, code: str) -> None:
        await send_reset_code_email(to_email, code)

    @staticmethod
    async def send_welcome_email(to_email: str, name: str, role: str) -> None:
        await send_welcome_email(to_email, name, role)


async def send_verification_email(to_email: str, code: str) -> None:
    subject = "【法律智能体】邮箱验证码"
    plain_body = (
        f"您好，\n\n您的验证码是：{code}\n"
        "验证码 5 分钟内有效，请勿泄露给他人。\n\n"
        "如果不是您本人操作，请忽略本邮件。"
    )
    html_body = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #111827;">
      <h2 style="margin: 0 0 16px;">法律智能体邮箱验证码</h2>
      <p>您好，</p>
      <p>您的验证码是：</p>
      <div style="font-size: 32px; font-weight: 700; letter-spacing: 6px; margin: 16px 0;">{code}</div>
      <p>验证码 5 分钟内有效，请勿泄露给他人。</p>
      <p style="color: #6b7280;">如果不是您本人操作，请忽略本邮件。</p>
    </div>
    """.strip()
    await send_email(to_email, subject, plain_body, html_body)


async def send_reset_code_email(to_email: str, code: str) -> None:
    await send_verification_email(to_email, code)


async def send_welcome_email(to_email: str, name: str, role: str) -> None:
    subject = "【法律智能体】欢迎加入"
    plain_body = (
        f"{name}，您好。\n\n"
        "您的账户已创建成功，欢迎使用法律智能体。\n"
        f"当前账号角色：{role}\n\n"
        "如需找回密码，可在登录页使用邮箱验证码功能。"
    )
    html_body = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; line-height: 1.7; color: #111827;">
      <h2 style="margin: 0 0 16px;">欢迎加入法律智能体</h2>
      <p>{name}，您好。</p>
      <p>您的账户已创建成功，欢迎开始使用。</p>
      <p><strong>当前账号角色：</strong>{role}</p>
      <p style="color: #6b7280;">如需找回密码，可在登录页使用邮箱验证码功能。</p>
    </div>
    """.strip()
    await send_email(to_email, subject, plain_body, html_body)
