import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt with work factor 12"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password using bcrypt, with fallback to False for legacy MD5"""
    try:
        # If the hashed string is not a valid bcrypt hash, this will raise an exception
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        # If any error occurs (e.g., invalid hash format), return False
        return False