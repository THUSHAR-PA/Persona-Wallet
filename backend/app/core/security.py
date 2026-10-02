from datetime import datetime, timedelta, timezone

import bcrypt
import os
from jose import jwt


SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Set SECRET_KEY to a private random string of at least 32 characters."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError("Password must be 72 bytes or less.")

    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {"sub": str(user_id), "exp": expire}

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
