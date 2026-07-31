import hashlib

def hash_password(password: str) -> str:
    """Hash password using MD5 without salt (Vulnerability #5: Weak Password Storage)"""
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password by comparing MD5 hashes"""
    return hash_password(plain) == hashed