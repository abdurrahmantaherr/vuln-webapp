# Software Specification Document (Implementation Addendum)

## Overview / Purpose
This document specifies the implementation of parameterized SQL queries to fix the SQL injection vulnerability in the authentication service. The change addresses Vulnerability #1: SQL Injection by replacing string concatenation with bound parameters in SQL queries while preserving all other intentional vulnerabilities (XSS, Session Hijacking, etc.) for educational purposes. The update requires modifications to the login() and signup() functions in auth_service.py to use SQLite3's parameterized query mechanism, preventing user-controlled input from being interpreted as SQL code.

## Scope & Non-Goals

### In Scope
- Replace SQL string concatenation with parameterized/bound queries in `backend/app/services/auth_service.py`
- Modify `signup()` function to use `?` placeholders for username, email, and password parameters
- Modify `login()` function to use `?` placeholder for username parameter only (password verification moved to Python)
- Preserve existing function signatures, return values, and behavior for legitimate use cases
- Ensure SQL injection payloads like `' OR '1'='1` and `' UNION SELECT ...` cannot bypass authentication or expose unintended records
- Use the repository's existing SQLite3 database mechanism; no new dependencies required

### Intentionally NOT In Scope (Other Vulnerabilities Remain Unfixed)
This change ONLY addresses Vulnerability #1 (SQL Injection). The following vulnerabilities MUST remain unchanged and exploitable:
1. **SQL Injection** — **BEING FIXED** (this vulnerability)
2. **Stored XSS** — username continues to be stored unsanitized and reflected on dashboard via `{{username}}` substitution
3. **Reflected XSS** — `/search` endpoint continues to interpolate the `query` parameter directly into HTML response without escaping
4. **Session Hijacking** — hardcoded weak session signing secret `"super-secret-key-12345"` remains unchanged
5. **Weak Password Storage** — MD5 hash without salt remains unchanged (or bcrypt if previously fixed)
6. **Exposed Database** — unauthenticated `/download/db` endpoint remains unchanged
7. **No Rate Limiting** — absent on all endpoints
8. **CSRF** — missing token validation on all forms

## Affected Files
- `backend/app/services/auth_service.py` — SQL query parameterization in login() and signup() functions

## Functional Requirements

### FR-01: Parameterized Signup Query
- The `signup()` function must construct INSERT queries using parameterized placeholders (`?`) instead of string concatenation
- Username, email, and hashed password values must be passed as parameters to `conn.execute()`, not embedded in the SQL string
- The SQL string must be: `"INSERT INTO users (username, email, password) VALUES (?, ?, ?)"`
- Parameters must be passed as a tuple: `(username, email, hashed_password)` in that order

### FR-02: Parameterized Login Query with Post-Verification
- The `login()` function must construct SELECT queries using parameterized placeholders (`?`) for username only
- The SQL string must be: `"SELECT * FROM users WHERE username = ?"`
- The username parameter must be passed as a tuple: `(username,)` to `conn.execute()`
- Password verification must occur in Python after fetching the user record, using the existing `verify_password()` function
- The function must NOT include password in the SQL WHERE clause under any circumstances

### FR-03: Preserve Existing Behavior for Valid Inputs
- For legitimate username/password combinations, the functions must return identical responses as before the change
- Registration success: redirect to `/login`
- Registration failure (duplicate username): JSON response with `"error": "Username already exists"` and status 409
- Login success: JSON response with `{ "success": true, "user_id": ..., "username": ..., "email": ..., "redirect": "/welcome" }`
- Login failure: JSON response with `{ "error": "Invalid credentials" }` and appropriate status code (401)
- All error handling and status codes must remain unchanged

### FR-04: SQL Injection Prevention
- User-controlled input (username, email, password) must never be interpreted as SQL syntax
- SQL injection payloads such as `' OR '1'='1`, `' UNION SELECT username, password FROM users--`, and `'; DROP TABLE users;--` must be treated as literal string values
- Such payloads must not bypass authentication, expose unintended records, or alter query execution beyond their intended literal matching

## Non-Functional Requirements

### NFR-01: Performance
- Parameterized queries must not introduce significant performance overhead compared to string concatenation
- Query execution time for legitimate inputs must remain within acceptable ranges for educational demonstration

### NFR-02: Code Maintainability
- The SQL query strings must be clear and readable
- Parameter binding must follow Python DB-API standards for SQLite3
- Code comments should clarify the security improvement without affecting educational value of other vulnerabilities

### NFR-03: Error Handling Preservation
- All existing error handling (IntegrityError for duplicate username, generic Exception handling) must remain unchanged
- Database connection handling (get_db(), commit(), close()) must remain identical
- No new error types should be introduced by the parameterization

## Success Paths

### SP-01: Successful Registration with Parameterized Queries
1. User navigates to `/signup`
2. User completes form with unique username, valid email, matching passwords
3. Client-side password match validation passes
4. Form submitted to `/signup`
5. Server validates fields, hashes password, executes parameterized INSERT query
6. Server responds with redirect to `/login`
7. Browser redirects to `/login` and displays login form
8. The account is created in the database with proper values

### SP-02: Successful Login with Parameterized Queries
1. User navigates to `/login`
2. User enters valid username and password matching database records
3. Form submission intercepted by JavaScript
4. AJAX request sent to `/login` with form data
5. Server validates fields, executes parameterized SELECT query with username only
6. Server fetches user record, calls `verify_password()` on stored hash
7. On success, server sets session variables and responds with `{ success: true, redirect: "/welcome" }`
8. Client receives response and redirects to `/welcome`
9. Server renders dashboard with username substitution
10. Browser displays authenticated dashboard

## Edge Cases

### EC-01: SQL Injection Payloads in Registration
- Attempting to register with username: `' OR '1'='1` must treat the value as a literal username string
- The INSERT query must attempt to create a user with the literal username `' OR '1'='1` (not modify query logic)
- If username doesn't exist, registration proceeds normally (creating a user with that strange username)
- If username exists, appropriate "Username already exists" error is returned
- No SQL injection or authentication bypass occurs

### EC-02: SQL Injection Payloads in Login Username Field
- Submitting username: `' OR '1'='1` must treat the value as a literal username to match
- The SELECT query must look for a user with literally that username (which likely doesn't exist)
- Query returns no results, leading to "Invalid credentials" error (correct behavior)
- Authentication bypass is prevented because the payload is not interpreted as SQL logic

### EC-03: Union-Based SQL Injection Attempts
- Submitting username: `' UNION SELECT 1, 'admin', 'password'--` must be treated as literal username
- The query searches for a user with that exact string as username
- No union operation is performed; no unintended records are exposed
- Login fails with "Invalid credentials" as expected for non-existent username

### EC-04: Password Field SQL Injection (Login)
- Although password is not used in SQL after fix, submitting SQL-like strings in password field must be handled safely
- Password value is passed to `verify_password()` as a string; no SQL interpretation occurs
- No vulnerability introduced through password field

## Acceptance Criteria

### AC-01: Parameterized Signup Query Format
- Given the `signup()` function is called with username, email, and password parameters
- When the function executes the database INSERT operation
- Then the SQL string must contain `?` placeholders for all user-provided values
- And the actual values must be passed as parameters to `conn.execute()`, not embedded in the SQL string

### AC-02: Parameterized Login Query Format
- Given the `login()` function is called with username and password parameters
- When the function executes the database SELECT operation
- Then the SQL string must contain exactly one `?` placeholder for the username
- And the username value must be passed as a parameter to `conn.execute()`
- And the SQL string must NOT contain any reference to the password parameter

### AC-03: Legitimate Registration Still Works
- Given a unique username, valid email, and matching password
- When the registration form is submitted
- Then the account is created in the database
- And the user is redirected to `/login`
- And no SQL errors occur

### AC-04: Legitimate Login Still Works
- Given a username and password matching a database record
- When the login form is submitted via AJAX
- Then the server returns `{ success: true, redirect: "/welcome" }`
- And the user is redirected to the dashboard
- And session variables are properly set

### AC-05: SQL Injection Payloads Defeated in Registration
- Given a registration attempt with username containing SQL injection payload (e.g., `' OR '1'='1`)
- When the form is submitted
- Then the payload is treated as a literal username value
- And no authentication bypass occurs
- And the behavior matches what would happen with any other username string

### AC-06: SQL Injection Payloads Defeated in Login
- Given a login attempt with username containing SQL injection payload (e.g., `' OR '1'='1`)
- When the form is submitted via AJAX
- Then the payload is treated as a literal username to match
- And no authentication bypass occurs
- And the server returns appropriate error for non-existent username

### AC-07: Other Vulnerabilities Unchanged
- All seven other vulnerabilities (XSS, Session, etc.) remain exactly as implemented
- No escaping, sanitization, validation, or rate limiting is added elsewhere

## Test Cases

| TC-ID | Scenario | Precondition | Expected Result |
|-------|----------|--------------|-----------------|
| TC-01 | Parameterized signup query structure | Function signup() | SQL string contains `INSERT INTO users (username, email, password) VALUES (?, ?, ?)` and values passed as parameters |
| TC-02 | Parameterized login query structure | Function login() | SQL string contains `SELECT * FROM users WHERE username = ?` and username passed as parameter; password verified in Python |
| TC-03 | Successful registration with valid data | Clean database, server running | Account created, redirected to /login, password stored as hash (MD5 or bcrypt per current state) |
| TC-04 | Registration with duplicate username | Existing user "existinguser" in DB | Form remains on signup page, "Username already exists" message displayed |
| TC-05 | Successful login with valid credentials | User "logintest" with password "SecurePass456!" in DB | Redirected to /welcome, session contains user data |
| TC-06 | Login with invalid credentials | Any username/password combination not in DB | Error message displayed: "Invalid credentials", remains on login page |
| TC-07 | SQLi payload in registration username | Clean database | Registration attempt with username="' OR '1'='1" creates user with that literal username (if unique) or returns "Username already exists" error; no query manipulation |
| TC-08 | SQLi payload in login username | Any database state | Login attempt with username="' OR '1'='1" and any password returns "Invalid credentials" (treats payload as literal username) |
| TC-09 | Union-based SQLi in login username | Database with at least one user | Login attempt with username="' UNION SELECT 1, 'admin', 'password'--" returns "Invalid credentials" (no union execution) |
| TC-10 | Legacy behavior preservation | Same as TC-03 and TC-05 | All success/failure responses, status codes, and redirects identical to pre-fix behavior for valid inputs |
| TC-11 | Other vulnerabilities unchanged | As specified in app-foundation.md | All 7 other vulnerabilities remain exploitable (XSS, Session, etc.) |

## Verification Steps

Manual verification on a developer workstation after rebuild:

1. **Start the application**:
   ```bash
   uv run backend/app/main.py
   ```
   Expected console output: Uvicorn running on `http://0.0.0.0:3001` (or `http://127.0.0.1:3001` if `HOST` is set).

2. **Verify parameterized signup query (TC-01)**:
   - Examine `backend/app/services/auth_service.py` signup() function
   - Confirm SQL string uses `?` placeholders: `INSERT INTO users (username, email, password) VALUES (?, ?, ?)`
   - Confirm values passed as parameters: `(username, email, hashed_password)`

3. **Verify parameterized login query (TC-02)**:
   - Examine `backend/app/services/auth_service.py` login() function
   - Confirm SQL string uses `?` placeholder: `SELECT * FROM users WHERE username = ?`
   - Confirm username passed as parameter: `(username,)`
   - Confirm password verification happens in Python after query execution

4. **Verify legitimate registration still works (TC-03)**:
   - Visit `http://localhost:3001/signup`
   - Register a new account: username="testuser", email="test@example.com", password="Password123!"
   - Expected: registration successful, redirected to `/login`

5. **Verify legitimate login still works (TC-05)**:
   - Visit `http://localhost:3001/login`
   - Login with username="testuser", password="Password123!"
   - Expected: successful login, redirected to `/welcome`
   - Observe that the dashboard shows "Logged in as <strong>testuser</strong>"

6. **Verify SQLi payload defeated in registration (TC-07)**:
   - Visit `http://localhost:3001/signup`
   - Attempt registration with username="' OR '1'='1", email="test@example.com", password="Password123!"
   - Expected: Either creates user with literal username "' OR '1'='1" (if unique) or shows "Username already exists" error
   - Expected: No authentication bypass or query manipulation

7. **Verify SQLi payload defeated in login (TC-08)**:
   - Visit `http://localhost:3001/login`
   - Attempt login with username="' OR '1'='1", password="anything"
   - Expected: Returns `{ success: false, error: "Invalid credentials" }` (treats username as literal string)
   - Expected: No authentication bypass or successful login

8. **Verify union-based SQLi defeated (TC-09)**:
   - Visit `http://localhost:3001/login`
   - Attempt login with username="' UNION SELECT 1, 'admin', 'password'--", password="anything"
   - Expected: Returns `{ success: false, error: "Invalid credentials" }` (no union execution)
   - Expected: No exposure of unintended records

9. **Verify no new files modified**:
   ```bash
   git status
   ```
   Expected: only `backend/app/services/auth_service.py` is modified.

10. **Verify other vulnerabilities unchanged (AC-07)**:
    - Perform quick checks that the other 7 vulnerabilities are still present (e.g., Stored XSS with `<script>alert(1)</script>` username, Reflected XSS via `/search?q=<script>alert(1)</script>`, etc.)