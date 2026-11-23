import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt


SECRET_KEY = os.getenv("CAMPUSBUS_SECRET", "campusbus-secret-key-123456789")
ALGORITHM = "HS256"


def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return salt + "$" + hashed.hex()


def verify_password(password, saved):
    salt, hashed = saved.split("$")
    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return secrets.compare_digest(new_hash.hex(), hashed)


def create_token(user_id, email, role):
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    data = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
