# Software Specification Document (Implementation Addendum)

## Overview / Purpose
This document specifies the implementation of bcrypt password hashing to replace the current unsalted MD5 implementation in the vulnerable web application. The change addresses Vulnerability #5: Weak Password Storage by using a modern, salted, adaptive hashing algorithm (bcrypt with work factor >= 12) while maintaining the exact same function signatures (`hash_password` and `verify_password`) and preserving all other intentional vulnerabilities (SQL Injection, XSS, etc.) for educational purposes. The update requires modifications to the password hashing logic, authentication flow, and dependency management, along with a note about existing MD5 hashes in the database requiring re-registration.

## Scope & Non-Goals

### In Scope
- Replace MD5 with bcrypt (work factor 12) in `backend/app/core/security.py`
- Update `hash_password()` to generate bcrypt hashes
- Update `verify_password()` to use `bcrypt.checkpw` with try/except fallback for legacy MD5 values
- Modify `auth_service.login()` to fetch user by username only, then verify password in Python (to avoid SQL matching bcrypt hashes)
- Add `bcrypt` dependency to both `backend/pyproject.toml` and root `pyproject.toml`
- Document that existing MD5 password hashes in the database will not work with the new verify function (users must re-register)
- Preserve all other 7 vulnerabilities exactly as implemented

### Intentionally NOT In Scope (Other Vulnerabilities Remain)
This change ONLY addresses Vulnerability #5 (Weak Password Storage). The following vulnerabilities MUST remain unchanged and exploitable:
1. **SQL Injection** — login and signup SQL queries via string concatenation remain unchanged
2. **Stored XSS** — username continues to be stored unsanitized and reflected on dashboard via `{{username}}` substitution
3. **Reflected XSS** — `/search` endpoint continues to interpolate the `query` parameter directly into HTML response without escaping
4. **Session Hijacking** — hardcoded weak session signing secret `"super-secret-key-12345"` remains unchanged
5. **Weak Password Storage** — **BEING FIXED** (this vulnerability)
6. **Exposed Database** — unauthenticated `/download/db` endpoint remains unchanged
7. **No Rate Limiting** — absent on all endpoints
8. **CSRF** — missing token validation on all forms

## Affected Files
- `backend/app/core/security.py` — password hashing implementation
- `backend/app/services/auth_service.py` — login function modification
- `backend/pyproject.toml` — add bcrypt dependency
- `pyproject.toml` (root) — add bcrypt dependency

## Functional Requirements

### FR-01: Secure Password Hashing
- `hash_password(password)` must return a bcrypt hash string (format: `$2b$12$...`)
- Use bcrypt with work factor 12 (or higher, but 12 is the minimum specified)
- The function must generate a unique salt for each password
- The output must be a string suitable for storage in the `password` column of the users table

### FR-02: Secure Password Verification with Legacy Support
- `verify_password(plain, hashed)` must return `True` if the plain text password matches the bcrypt hash
- If `hashed` is a legacy MD5 hash (32 character hex string), the function must return `False` (not crash)
- The function must wrap `bcrypt.checkpw` in a try/except block to handle potential malformed hashes gracefully
- For any non-bcrypt hash (including MD5), return `False` after attempting verification

### FR-03: Modified Login Flow to Accommodate bcrypt
- In `auth_service.login()`, the SQL query must ONLY match on username (not password) because bcrypt hashes cannot be matched in SQL
- After fetching the user record by username, call `verify_password(plain_password, stored_hash)` in Python
- If verification succeeds, proceed with setting session and returning success response
- If verification fails (including legacy MD5 hashes), return invalid credentials error

### FR-04: Dependency Management
- Add `bcrypt>=4.0.0` to the dependencies list in both `backend/pyproject.toml` and root `pyproject.toml`
- The version specifier must allow updates within the same major version (e.g., `>=4.0.0,<5.0.0` or simply `>=4.0.0`)

### FR-05: Migration Note for Existing MD5 Hashes
- Document that existing user accounts with MD5 password hashes will not be able to log in after this change
- Users must re-register (or the database must be reset) to use the new bcrypt hashing
- This is an acceptable trade-off for fixing the vulnerability in an educational context

## Non-Functional Requirements

### NFR-01: Computational Cost
- Bcrypt with work factor 12 should be intentionally slow (approximately 100ms per hash on modern hardware) to resist brute-force attacks
- This slowness is a security feature, not a bug

### NFR-02: Backward Compatibility (Limited)
- The public function signatures (`hash_password` and `verify_password`) remain unchanged
- However, the verification function will not validate legacy MD5 hashes (by design, to avoid false positives)
- Applications using this library must reset password data or handle migration separately

### NFR-03: Error Handling
- `verify_password` must not raise exceptions for any input (including malformed hashes)
- All exceptions from bcrypt operations must be caught and return `False`

### NFR-04: Salt Uniqueness
- Each call to `hash_password` must generate a cryptographically random salt
- The probability of two users having the same salt must be negligible

## Success Paths

### SP-01: Successful Registration with Bcrypt
1. User navigates to `/signup`
2. User completes form with unique username, valid email, matching passwords
3. Client-side password match validation passes
4. Form submitted to `/signup`
5. Server validates fields, hashes password using bcrypt via `hash_password()`, inserts record
6. Server responds with redirect to `/login`
7. Browser redirects to `/login` and displays login form
8. The stored password in the database is a bcrypt string beginning with `$2b$`

### SP-02: Successful Login with Bcrypt
1. User navigates to `/login`
2. User enters valid username and password (matching a bcrypt hash in the database)
3. Form submission intercepted by JavaScript
4. AJAX request sent to `/login` with form data
5. Server validates fields, fetches user by username only (ignoring password in SQL)
6. Server calls `verify_password(plain_password, stored_hash)` which returns `True`
7. Server sets session variables and responds with `{ success: true, redirect: "/welcome" }`
8. Client receives response and redirects to `/welcome`
9. Server renders dashboard with username substitution
10. Browser displays authenticated dashboard

### SP-03: Graceful Failure with Legacy MD5 Hash
1. A user account exists in the database with an MD5 password hash (from before the change)
2. User navigates to `/login` and enters the correct password for that account
3. Form submission intercepted by JavaScript
4. AJAX request sent to `/login` with form data
5. Server fetches user by username, finds the MD5 hash
6. Server calls `verify_password(plain_password, md5_hash)` which returns `False` (after trying bcrypt and catching exception)
7. Server responds with `{ success: false, error: "Invalid credentials" }`
8. Client receives response and displays error message
9. No exception is raised or propagated

## Edge Cases

### EC-01: Invalid Bcrypt Hash in Database
- If the `password` field contains a string that is not a valid bcrypt hash (e.g., empty string, random text)
- `verify_password` will attempt `bcrypt.checkpw` which will raise an exception
- The exception is caught and the function returns `False`
- Login attempt fails with "Invalid credentials" (no crash)

### EC-02: Empty Password
- `hash_password("")` returns a valid bcrypt hash of the empty string
- `verify_password("", bcrypt_hash)` returns `True` if the hash matches
- This is bcrypt's correct behavior (though empty passwords are discouraged by policy)

### EC-03: Very Long Password
- Bcrypt has a password length limit of 72 bytes
- `hash_password` will correctly hash passwords longer than 72 bytes (bcrypt internally truncates)
- `verify_password` will correctly verify passwords longer than 72 bytes
- No special handling required

### EC-04: Concurrent Hashing
- Multiple simultaneous calls to `hash_password` are thread-safe (bcrypt is thread-safe)
- Each call generates an independent salt

## Acceptance Criteria

### AC-01: Bcrypt Hash Format
- Given a password string
- When `hash_password(password)` is called
- Then the returned string starts with `$2b$` (indicating bcrypt)
- And the string length is 60 characters (standard bcrypt hash length)

### AC-02: Password Verification Works
- Given a password string
- When `hash_password(password)` returns a hash
- And `verify_password(password, hash)` is called
- Then the function returns `True`

### AC-03: Wrong Password Returns False
- Given a password string "correct"
- When `hash_password("correct")` returns a hash
- And `verify_password("incorrect", hash)` is called
- Then the function returns `False`

### AC-04: Legacy MD5 Hash Returns False (No Crash)
- Given a known MD5 hash (e.g., `"d41d8cd98f00b204e9800998ecf8427e"` for empty string)
- When `verify_password("anything", "d41d8cd98f00b204e9800998ecf8427e")` is called
- Then the function returns `False` (does not raise an exception)

### AC-05: Login Query Change
- In `auth_service.login()`, the SQL query must NOT include the password in the WHERE clause
- The query must be: `SELECT * FROM users WHERE username = '{username}'`
- Password verification must happen in Python after fetching the user record

### AC-06: Dependency Added
- Both `backend/pyproject.toml` and root `pyproject.toml` contain `bcrypt>=4.0.0` in dependencies
- Running `uv sync` or `pip install` installs the bcrypt package

### AC-07: Other Vulnerabilities Unchanged
- All seven other vulnerabilities (SQLi, XSS, Session, etc.) remain exactly as implemented
- No escaping, sanitization, validation, or rate limiting is added elsewhere

## Test Cases

| TC-ID | Scenario | Precondition | Expected Result |
|-------|----------|--------------|-----------------|
| TC-01 | Hash password returns bcrypt format | Any password string | `hash_password("test")` returns string starting with `$2b$` and length 60 |
| TC-02 | Verify correct password returns True | Hash from TC-01 | `verify_password("test", hash_from_TC01)` returns `True` |
| TC-03 | Verify wrong password returns False | Hash from TC-01 | `verify_password("wrong", hash_from_TC01)` returns `False` |
| TC-04 | Verify legacy MD5 returns False (no crash) | Legacy MD5 hash | `verify_password("anything", "d41d8cd98f00b204e9800998ecf8427e")` returns `False` |
| TC-05 | Verify empty string | Empty password | `hash_password("")` returns valid bcrypt hash; `verify_password("", that_hash)` returns `True` |
| TC-06 | Verify very long password | 100-character password | Hash and verify works correctly (bcrypt handles truncation) |
| TC-07 | Login with bcrypt hash works | User registered with new bcrypt hash | Login succeeds with correct credentials |
| TC-08 | Login with legacy MD5 hash fails gracefully | User with pre-existing MD5 hash | Login fails with "Invalid credentials", no server error |
| TC-09 | Dependency installed | Fresh environment | `uv sync` or `pip install` installs bcrypt package |
| TC-10 | SQL injection still works | `/login` endpoint | Submitting `' OR '1'='1` as username and any password returns `{ success: true, redirect: "/welcome" }` |
| TC-11 | Other vulnerabilities unchanged | As specified in app-foundation.md | All 7 other vulnerabilities remain exploitable |

## Verification Steps

Manual verification on a developer workstation after rebuild:

1. **Start the application**:
   ```bash
   uv run backend/app/main.py
   ```
   Expected console output: Uvicorn running on `http://0.0.0.0:3001` (or `http://127.0.0.1:3001` if `HOST` is set).

2. **Verify bcrypt hash format (TC-01)**:
   - In a Python shell, import the security module: `from backend.app.core.security import hash_password`
   - Call `hash_password("testpassword")`
   - Expected: returns a string starting with `$2b$` and exactly 60 characters long

3. **Verify password verification (TC-02, TC-03)**:
   - In the same Python shell, store the hash from step 2
   - Call `verify_password("testpassword", stored_hash)` → Expected: `True`
   - Call `verify_password("wrongpassword", stored_hash)` → Expected: `False`

4. **Verify legacy MD5 handling (TC-04)**:
   - Call `verify_password("anything", "d41d8cd98f00b204e9800998ecf8427e")`
   - Expected: `False` (no exception raised)

5. **Verify login flow with bcrypt (TC-07)**:
   - Delete `theme` key from localStorage (if testing dark mode, but not required for this spec)
   - Visit `http://localhost:3001/signup`
   - Register a new account: username="bcrypttest", email="test@example.com", password="SecurePass123!"
   - Expected: registration successful, redirected to `/login`
   - Now visit `http://localhost:3001/login`
   - Login with username="bcrypttest", password="SecurePass123!"
   - Expected: successful login, redirected to `/welcome`
   - Observe that the dashboard shows "Logged in as <strong>bcrypttest</strong>"

6. **Verify legacy MD5 login fails gracefully (TC-08)**:
   - First, create a user with the OLD system (MD5) OR manually insert a known MD5 hash into the database:
     - SQLite command: `INSERT INTO users (username, email, password) VALUES ('md5test', 'md5@example.com', 'd41d8cd98f00b204e9800998ecf8427e');`
   - Note: The password hash above is MD5 of empty string.
   - Visit `http://localhost:3001/login`
   - Login with username="md5test", password="anything" (or empty string)
   - Expected: login fails with "Invalid credentials", but no 500 error or crash
   - Check server logs: no exception traceback related to bcrypt

7. **Verify SQL injection still works (TC-10)**:
   - On `http://localhost:3001/login`, submit username: `' OR '1'='1` and any password (e.g., "x")
   - Expected: response is `{ success: true, redirect: "/welcome" }` (authentication bypass)
   - Note: This works because the SQL injection is in the username field, and we now only check username in SQL (but the injection still works to modify the WHERE clause)

8. **Verify no new files (beyond the four specified)**:
   ```bash
   git status
   ```
   Expected: only `backend/app/core/security.py`, `backend/app/services/auth_service.py`, `backend/pyproject.toml`, and root `pyproject.toml` are modified.

9. **Verify dependencies**:
   - Check that both `backend/pyproject.toml` and root `pyproject.tomol` contain `bcrypt>=4.0.0`
   - Run `uv sync` and verify bcrypt is installed in the virtual environment

10. **Verify other vulnerabilities unchanged (AC-07)**:
    - Perform quick checks that the other 7 vulnerabilities are still present (e.g., Stored XSS with `<script>alert(1)</script>` username, Reflected XSS via `/search?q=<script>alert(1)</script>`, etc.)
