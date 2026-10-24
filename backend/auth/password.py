"""
EngageAI Backend — auth/password.py
Password hashing and verification using raw bcrypt library.
"""

import bcrypt


def hash_password(plain: str) -> str:
    # Truncate to 72 bytes max for bcrypt compatibility
    pwd_bytes = plain.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)
