# Vulnerabilities in the Web Application

Based on code analysis, here are the 8 vulnerabilities present in the application:

## 1. SQL Injection ✓
**Status:** Present  
**Location:** `backend/app/api/routes/auth.py` lines 121-123  
**Description:** The `/search` endpoint uses f-string concatenation to build SQL queries, allowing SQL injection via the `query` parameter.  
**Code:** 
```python
conn.execute(
    f"SELECT username, email FROM users WHERE username LIKE '%{query}%' OR email LIKE '%{query}%'"
)
```

## 2. Stored XSS ✓
**Status:** Present  
**Location:** `frontend/templates/dashboard.html` line 49  
**Description:** The username is directly inserted into the HTML without escaping, allowing stored XSS when a malicious username is registered.  
**Code:**
```html
<p>Logged in as <strong>{{username}}</strong></p>
```

## 3. Reflected XSS ✓
**Status:** Present  
**Location:** `backend/app/api/routes/auth.py` lines 128-129  
**Description:** User data from the database is directly inserted into HTML responses without escaping in the `/search` endpoint.  
**Code:**
```python
html_items.append(f"<li>{row['username']} ({row['email']})</li>")
```

## 4. Session Hijacking ✓
**Status:** Present  
**Location:** `backend/app/main.py` lines 26-32  
**Description:** Hardcoded weak secret key used for session signing, making session tokens predictable and vulnerable to hijacking.  
**Code:**
```python
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-12345",  # Intentionally weak and hardcoded
    https_only=False,
    same_site="lax"
)
```

## 5. Weak Password Storage ✗ (FIXED)
**Status:** Fixed as documented  
**Location:** `backend/app/core/security.py` lines 3-5  
**Description:** Passwords are now hashed using bcrypt with work factor 12, fixing the previous MD5 without salt vulnerability.  
**Code:**
```python
def hash_password(password: str) -> str:
    """Hash password using bcrypt with work factor 12"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
```

## 6. Exposed Database ✓
**Status:** Present  
**Location:** `backend/app/api/routes/auth.py` lines 134-151  
**Description:** The `/download/db` endpoint serves the database file without any authentication check.  
**Code:**
```python
@router.get("/download/db")
async def download_database(request: Request):
    """Serve database file with no authentication check"""
    # No authentication check (Vulnerability #6: Exposed Database)
    # ... serves the database file
```

## 7. No Rate Limiting ✓
**Status:** Present  
**Location:** Throughout codebase - no implementation found  
**Description:** Absence of rate limiting on all endpoints allows unlimited login attempts and other brute force attacks.  
**Verification:** No rate limiting libraries or implementations found in the codebase.

## 8. CSRF ✓
**Status:** Present  
**Location:** Frontend forms and backend endpoints  
**Description:** Missing CSRF token validation on all forms (`/signup` and `/login` endpoints).  
**Evidence:** 
- `frontend/templates/signup.html` line 56: `<form id="signup-form" action="/signup" method="POST">` (no CSRF token)
- `frontend/templates/login.html` line 61: `<form id="login-form" action="/login" method="POST">` (no CSRF token)
- No CSRF validation in corresponding backend handlers

## Summary
- **Total Vulnerabilities:** 8 (as documented)
- **Fixed as Documented:** 1 (Weak Password Storage)
- **Currently Present:** 7 vulnerabilities
- **Note:** While CLAUDE.md stated SQL injection was in login/signup endpoints, analysis shows those are fixed with parameterized queries, but SQL injection exists in the search endpoint instead.

All vulnerabilities match the OWASP Top 10 categories as intended for security education purposes.