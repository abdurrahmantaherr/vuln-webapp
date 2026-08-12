# Implementation Plan for SQL Injection Fix

## Phase 1: Analyze Current Implementation
- Examine `backend/app/services/auth_service.py` to identify SQL injection vulnerabilities
- Locate the `signup()` function's INSERT query construction (line 18)
- Locate the `login()` function's SELECT query construction (line 42)
- Note current string concatenation patterns:
  - Signup: `f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{hashed_password}')"`
  - Login: `f"SELECT * FROM users WHERE username = '{username}'"`

## Phase 2: Modify Signup Function
- Replace string concatenation INSERT with parameterized query
- Change SQL string to: `"INSERT INTO users (username, email, password) VALUES (?, ?, ?)"`
- Modify `conn.execute(query)` to `conn.execute(query, (username, email, hashed_password))`
- Preserve all existing validation, error handling, and return values
- Ensure function signature and behavior remain identical for valid inputs

## Phase 3: Modify Login Function
- Replace string concatenation SELECT with parameterized query for username only
- Change SQL string to: `"SELECT * FROM users WHERE username = ?"`
- Modify `conn.execute(query)` to `conn.execute(query, (username,))`
- Move password verification to Python after fetching user record:
  - Fetch user record with parameterized query
  - If record exists, call `verify_password(password, result["password"])`
  - If verification succeeds, proceed with session setup
  - If verification fails, return invalid credentials error
- Preserve all existing validation, error handling, and return values
- Ensure function signature and behavior remain identical for valid inputs

## Phase 4: Verify No Other Changes Needed
- Confirm that `verify_password()` function in `backend/app/core/security.py` remains unchanged (unless bcrypt was previously implemented)
- Confirm no modifications to password hashing logic are made
- Confirm no changes to other vulnerability implementations (XSS, Session, etc.)
- Confirm no new dependencies are required

## Phase 5: Test Implementation
- Start the application and verify legitimate registration/login still works
- Test SQL injection payloads to confirm they are now treated as literal values
- Verify all other vulnerabilities remain exploitable as intended