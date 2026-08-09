# Bcrypt Password Hashing Implementation Plan

## Overview
This plan outlines the implementation of bcrypt password hashing to replace the current unsalted MD5 implementation in the vulnerable web application. This change addresses Vulnerability #5: Weak Password Storage while preserving all other intentional vulnerabilities for educational purposes.

## Phase 1: Dependency Updates
- Add `bcrypt>=4.0.0` to the dependencies list in `backend/pyproject.toml`
- Add `bcrypt>=4.0.0` to the dependencies list in the root `pyproject.toml`
- Run `uv sync` in the backend directory to install the new dependency

## Phase 2: Update Security Utilities (`backend/app/core/security.py`)
Replace the existing MD5-based implementation with bcrypt:
- Replace `import hashlib` with `import bcrypt`
- Update `hash_password(password: str) -> str`:
  - Use bcrypt with work factor 12: `bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')`
  - Update docstring to reflect bcrypt usage
- Update `verify_password(plain: str, hashed: str) -> bool`:
  - Wrap `bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))` in a try/except block
  - Return `True` if passwords match
  - Return `False` for any exception (including invalid hash format or legacy MD5)
  - Update docstring to describe the fallback behavior for legacy MD5

## Phase 3: Update Authentication Service (`backend/app/services/auth_service.py`)
Modify the login function to accommodate bcrypt:
- In the `login` function:
  - Remove the password hashing step before building the SQL query
  - Modify the SQL query to select by username only: `f"SELECT * FROM users WHERE username = '{username}'"`
  - After fetching the user record, call `verify_password(password, result["password"])` to verify the password in Python
  - Only proceed with setting the session if verification returns `True`
- Leave the `signup` function unchanged (it will now use the updated `hash_password` function)

## Phase 4: Migration Note
Document that existing user accounts with MD5 password hashes will not be able to log in after this change:
- Add a note in the application documentation or deployment instructions
- Explain that users must re-register or the database must be reset to use the new bcrypt hashing
- This is an acceptable trade-off for fixing the vulnerability in an educational context

## Phase 5: Verification
Follow the verification steps outlined in the specification:
1. Start the application and verify it runs on http://localhost:3001
2. Verify bcrypt hash format (should start with `$2b$` and be 60 characters)
3. Verify password verification works for correct and incorrect passwords
4. Verify legacy MD5 hash handling returns `False` without raising exceptions
5. Verify login flow works with newly registered accounts (bcrypt)
6. Verify legacy MD5 login fails gracefully (no crash, returns invalid credentials)
7. Verify SQL injection vulnerability still works (authentication bypass via username field)
8. Confirm only the four specified files are modified
9. Verify dependencies are installed correctly
10. Spot-check that other vulnerabilities (Stored XSS, Reflected XSS, Session Hijacking, Exposed Database, No Rate Limiting, CSRF) remain unchanged

## Notes
- All other vulnerabilities (SQL Injection, Stored XSS, Reflected XSS, Session Hijacking, Exposed Database, No Rate Limiting, CSRF) must remain exactly as implemented
- The work factor for bcrypt is set to 12 as specified, which provides appropriate security for educational purposes
- The verification function's try/except ensures graceful handling of malformed hashes and legacy MD5 values