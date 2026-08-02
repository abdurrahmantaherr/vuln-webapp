import sqlite3
import json
from fastapi import Form
from fastapi.responses import RedirectResponse, JSONResponse
from ..db.session import get_db
from ..core.security import hash_password

def signup(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """Handle user registration with SQL injection vulnerability"""
    # Validate all fields present
    if not username or not email or not password:
        return JSONResponse(content={"error": "All fields are required"}, status_code=400)

    # Hash password with MD5 without salt
    hashed_password = hash_password(password)

    # Build INSERT query via STRING CONCATENATION (vulnerability #1)
    query = f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{hashed_password}')"

    try:
        conn = get_db()
        conn.execute(query)
        conn.commit()
        conn.close()
        return {
            "success": True,
            "redirect": "/login"
        }
    except sqlite3.IntegrityError:
        # Handle UNIQUE constraint error for username
        return JSONResponse(content={"error": "Username already exists"}, status_code=409)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

def login(username: str = Form(...), password: str = Form(...)):
    """Handle user login with SQL injection vulnerability"""
    # Validate all fields present
    if not username or not password:
        return JSONResponse(content={"error": "Username and password are required"}, status_code=400)

    # Hash password with MD5 without salt
    hashed_password = hash_password(password)

    # Build SELECT query via STRING CONCATENATION (vulnerability #1)
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashed_password}'"

    conn = get_db()
    result = conn.execute(query).fetchone()
    conn.close()

    if result:
        # Set session variables (will be handled in route)
        return {
            "success": True,
            "user_id": result["id"],
            "username": result["username"],
            "email": result["email"],
            "redirect": "/welcome"
        }
    else:
        return JSONResponse(content={"error": "Invalid credentials"}, status_code=401)