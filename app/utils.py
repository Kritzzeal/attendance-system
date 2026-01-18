# app/utils.py
from passlib.context import CryptContext
import random
import string

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def generate_password(plain_password: str = None) -> str:
    """Generate or hash password"""
    if plain_password:
        # Truncate if too long for hashing
        if len(plain_password) > 72:
            plain_password = plain_password[:72]
        return pwd_context.hash(plain_password)
    else:
        # Generate random password
        letters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(letters) for i in range(10))
        return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)