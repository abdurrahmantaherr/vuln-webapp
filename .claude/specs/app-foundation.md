# Software Specification Document (Implementation Addendum)

## Scope
This document captures implementation-level behavior necessary to reproduce the application exactly as implemented. It intentionally omits product goals, architecture, technology stack, vulnerability descriptions, database schema definitions, and endpoint inventories that are already documented in PRD.md and TDD.md. This specification focuses exclusively on runtime behavior, user flows, functional requirements, visual design specifications, form specifications, validation rules, session state model, data lifecycle rules, success paths, alternate paths, edge cases, business rules, rebuild requirements, acceptance criteria, test cases, and documentation gaps.

## Runtime Behavior
- Automatic database initialization occurs on application startup, creating the users table if it does not exist
- Missing database files are recreated automatically upon application restart
- User data (username, email, password hash) is preserved across application restarts via persistent SQLite database file
- Static assets (CSS, images) are served from disk and available immediately after application boot
- HTML templates are loaded from disk at request time with no caching mechanism applied
- Dashboard content is modified via runtime string substitution where `{{username}}` placeholder is replaced with the actual username from session data before HTML response is sent
- Authentication state is determined solely by the presence of `user_id` in the session; absence of this key results in unauthenticated state

## User Flows

### Registration Flow
1. User navigates to `/signup` endpoint and receives `signup.html` template
2. User fills in username, email, password, and confirm password fields in the form
3. Client-side validation occurs:
   - Password confirmation is checked before form submission (JavaScript comparison)
   - If passwords don't match, form submission is prevented and error message "Passwords do not match" is displayed below confirm password field
   - No page reload occurs during this client-side validation
4. Upon successful client-side validation, form is submitted via POST to `/signup`
5. Server processes registration:
   - Validates that all fields (username, email, password) are present
   - Hashes password using MD5 algorithm without salt via `hash_password()` function
   - Constructs SQL INSERT statement via string concatenation: `INSERT INTO users (username, email, password) VALUES ('" + username + "', '" + email + "', '" + hashed + "')"`
   - Executes query against SQLite database
   - If username already exists, returns HTML response with error message "Username already exists" (information leakage via error message)
   - On successful insertion, returns redirect response to `/login` endpoint
6. Browser follows redirect to `/login` endpoint, serving `login.html` template

### Login Flow
1. User navigates to `/login` endpoint and receives `login.html` template
2. User fills in username and password fields in the form
3. Form submission is handled via JavaScript `fetch()` API (not traditional form submission):
   - Event listener prevents default form submission
   - Form data is collected and sent as `application/x-www-form-urlencoded` via `URLSearchParams`
   - Request is sent to `/login` endpoint via POST
4. Server processes login:
   - Validates that username and password fields are present
   - Hashes provided password using MD5 algorithm without salt via `hash_password()` function
   - Constructs SQL SELECT statement via string concatenation: `SELECT * FROM users WHERE username = '" + username + "' AND password = '" + hashed + "'"`
   - Executes query against SQLite database
   - If query returns a row:
     - Sets session variables: `session['user_id'] = row['id']`, `session['username'] = row['username']`, `session['email'] = row['email']`
     - Returns JSON response with `{ "success": true, "redirect": "/welcome" }`
   - If query returns no rows:
     - Returns JSON response with `{ "success": false, "error": "Invalid credentials" }`
5. Client-side handling of login response:
   - On success: redirects browser to URL specified in `data.redirect` (`/welcome`)
   - On failure: displays error message from `data.error` in the error message area (initially hidden, made visible on error)
   - If response contains `unverified: true` flag, displays resend verification email UI
   - If response contains `otp_required: true` flag, redirects to OTP verification page (`/login/otp`)

### Dashboard Flow
1. User navigates to `/welcome` endpoint
2. Server checks for authentication:
   - Looks for `user_id` key in session
   - If absent, returns redirect response to `/login` endpoint
   - If present, proceeds to render dashboard
3. Server loads `dashboard.html` template from disk
4. Performs runtime string substitution:
   - Replaces `{{username}}` placeholder with value from `session['username']`
   - No other placeholders or templating mechanisms are used
5. Returns HTML response with substituted username
6. Client-side rendering occurs:
   - Browser displays header with title, theme toggle button, and three organizational logos (PUCIT, Excaliat, FCCU) each 54x54px
   - Hero banner appears below header with:
     - Left section: title "Security Vulnerability Lab" and subtitle "Explore, Exploit, and Learn"
     - Right section: "Logged in as <strong>[username]</strong>" text, Profile button, and Logout button
   - Main content area displays:
     - Mission card with section title "Our Mission" and descriptive paragraph
     - Vulnerabilities section with header "VULNERABILITIES TO DISCOVER" in uppercase small bold text
     - Two-column grid of vulnerability cards (each white, rounded corners, light border, hover shadow)
     - Each vulnerability card contains:
       - Colored pill tag indicating vulnerability type
       - Card title (h4 element)
       - Card description (p element)
     - Process steps section with three cards horizontally arranged:
       - Each card has circular numbered badge (1, 2, 3), title, and description
       - Cards have `#1a237e` background color with white text

### Logout Flow
1. User clicks Logout button (in dashboard hero banner) or navigates to `/logout` endpoint
2. Server processes logout:
   - Clears all session data by setting `session.clear()`
   - Returns redirect response to `/login` endpoint
3. Browser follows redirect to `/login` endpoint, serving `login.html` template
4. After logout, attempting to access `/welcome` or other protected endpoints results in redirect to `/login` due to missing `user_id` in session

## Functional Requirements

### FR-01: Session Management
- Session state is managed via Starlette SessionMiddleware (via FastAPI integration)
- Session cookie is set with default security characteristics (HttpOnly flag not explicitly set in implementation)
- Session data includes `user_id` (integer), `username` (string), and `email` (string) upon successful authentication
- Session is invalidated by calling `session.clear()` on logout
- Session persistence relies on client-side cookie; no server-side session store is used
- Session validation occurs by checking for presence of `user_id` key in session dictionary

### FR-02: Dynamic User Context
- Username is dynamically injected into dashboard template via string replacement of `{{username}}` placeholder
- Replacement occurs at request time in `welcome_page()` handler before HTML response is generated
- No client-side JavaScript is used for username display; it is purely server-side template substitution
- The same mechanism applies to any future template placeholders (though only `{{username}}` is currently used)
- User context is sourced exclusively from `session['username']` which is set during login

### FR-03: Route Protection
- Protection is implemented via explicit check in route handler, not middleware
- `/welcome` endpoint checks `if 'user_id' not in session:` before rendering dashboard
- If check fails, returns `RedirectResponse(url='/login')`
- No decorator or middleware-based protection is used; each protected route must implement check individually
- `/download/db` and `/search` endpoints intentionally lack authentication checks (vulnerabilities)
- `/profile` endpoint (referenced in dashboard) follows same protection pattern as `/welcome`

### FR-04: Error Handling
- Client-side form validation errors are displayed inline without page reload:
  - Login errors: displayed in `#error-message` div after AJAX call failure
  - Signup password mismatch: displayed in `#password-error` span when passwords don't match
  - Username already exists: returned in HTML response from `/signup` POST handler
- Server-side validation errors:
  - Missing form fields: results in SQL errors or undefined behavior (not explicitly handled)
  - Database errors: not caught or handled in current implementation
- Error messages are displayed in browser via DOM manipulation:
  - Error containers are initially hidden (`style.display = 'none'`)
  - On error, JavaScript sets `textContent` and changes `display` to `'block'`
- No centralized error handling mechanism exists; each handler manages its own errors

### FR-05: Search Processing
- `/search` endpoint accepts `query` parameter via GET request
- No authentication check is performed on this endpoint (intentional vulnerability)
- Implementation directly interpolates user input into HTML response:
  - Queries database: `SELECT username, email FROM users WHERE username LIKE '%{query}%' OR email LIKE '%{query}%'`
  - Builds response string: `f"<li>{row[0]} ({row[1]})</li>"` for each result
  - Returns concatenated list items wrapped in `<ul>` tags
- No escaping or sanitization of user input occurs before inclusion in HTML response
- Results are displayed as plain HTML in browser window (not within a template)
- Empty query returns empty response (no "no results" message)

### FR-06: Persistence
- Data persistence achieved via SQLite3 database file named `vulnerable_app.db` in project root
- Database file is created automatically by `init_db()` function on application startup if it doesn't exist
- Table schema:
  ```sql
  CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE,
      email TEXT,
      password TEXT
  )
  ```
- All write operations (INSERT) and read operations (SELECT) are committed immediately
- Database connection uses `check_same_thread=False` to allow cross-thread access
- Row factory is set to `sqlite3.Row` to enable dict-like access to query results
- No connection pooling; each database operation creates a new connection via `get_db()`
- File-based persistence ensures data survives application restarts

## Complete Visual Design Specification

### Global Design System
- **Typography**: 
  - Font family: `'Segoe UI', system-ui, -apple-system, sans-serif`
  - Typography scale:
    - Main titles: 2rem / font-weight 800
    - Section titles: 1.4rem / font-weight 700
    - Form titles: 1.7rem / font-weight 700
    - Card titles: 0.95rem / font-weight 700
    - Body text: 0.9rem / font-weight 400
    - Labels: 0.82rem / font-weight 600
    - Buttons: 1rem / font-weight 600

### Primary Colors Table
- `--color-brand-primary`: `#1a237e` (indigo/dark blue)
- `--color-brand-secondary`: `#3949ab` (lighter blue)
- `--color-brand-tertiary`: `#283593` (medium blue)
- `--color-brand-deep`: `#0d1b5e` (very dark blue for gradients)
- `--color-bg-dashboard`: `#eef1f8` (light blue-gray background)
- `--color-bg-surface`: `#ffffff` (white surface/card background)

### Text Colors
- `--color-text-primary`: `#1e293b` (dark slate - primary text)
- `--color-text-secondary`: `#475569` (gray - secondary text)
- `--color-text-muted`: `#64748b` (slate gray - muted/disabled text)
- `--color-text-accent`: `#1a237e` (brand primary - links/accents)
- `--color-text-on-brand`: `#ffffff` (white - text on brand backgrounds)

### Border Radius
- Inputs: 8px
- Buttons: 8px
- Cards: 10-12px (varies by component)
- Status tags: 6px

### Shadows
- Header: `0 2px 10px rgba(26,35,126,0.08)`
- Card hover: `0 4px 16px rgba(26,35,126,0.10)`
- Focus glow: `0 0 0 3px rgba(57,73,171,0.12)`

### Shared Header
- Fixed position at top of viewport
- Height: 70px
- Background: white (`--color-bg-header`)
- Bottom border: 1px solid `var(--color-border-soft)`
- Subtle shadow: `var(--shadow-header)`
- Layout: flex container with space-between alignment
- Left section: application title text
- Right section: container for three organizational logos
- Each logo: 54px width, 54px height, object-fit: contain

### Login Page
- Two-column 50/50 split-screen layout on desktop
- Left panel:
  - Deep blue gradient background: linear-gradient(135deg, #0d1b5e 0%, #1a237e 50%, #283593 100%)
  - Badge label: "SECURITY EDUCATION PLATFORM" (uppercase, letter-spaced)
  - Welcome heading: "Welcome Back" (2rem, 800 weight)
  - Description: paragraph about accessing security lab environment
  - Bullet list of 4 features with checkmark icons
  - Three semi-transparent white circle overlays:
    - circle-1: 300px diameter, positioned top:-60px, right:-80px, opacity ~7%
    - circle-2: 200px diameter, positioned bottom:80px, left:-50px, opacity ~7%
    - circle-3: 150px diameter, positioned bottom:-30px, right:60px, opacity ~7%
- Right panel:
  - White background (`--color-bg-surface`)
  - Form container constrained to max 400px width
  - Form title: "Sign In" (1.7rem, 700 weight)
  - Form subtitle: "Enter your credentials to access the lab" (0.9rem, muted text)
  - Username field:
    - Label: "Username" (0.82rem, 600 weight)
    - Input: background `#f8f9ff`, border 1.5px solid `#c5cae9`, border-radius 8px, padding 12px 16px
    - Focus state: border-color `#3949ab`, box-shadow `0 0 0 3px rgba(57,73,171,0.12)`
  - Password field: identical styling to username field
  - Error message area:
    - Initially hidden (`display: none`)
    - Background: `#fef2f2`, border: 1px solid `#fecaca`, text color: `#991b1b`
    - Padding: 12px, border-radius: 8px
  - Full-width login button:
    - Background: `#1a237e`, text color: white
    - Padding: 12px, border-radius: 8px, font-weight: 600
    - Hover state: background `#283593`
  - Signup link: "Don't have an account? Sign up" (0.85rem, muted text with accent-colored link)

### Signup Page
- Identical structure to login page (same split-screen layout, gradient, circles)
- Form title: "Create Account"
- Form subtitle: "Fill in your details to register for the lab"
- Form fields:
  - Username: same styling as login
  - Email: same styling as login (type="email")
  - Password: same styling as login
  - Confirm Password: same styling as login
- Password mismatch handling:
  - Error message "Passwords do not match" displayed in span below confirm field
  - Shown/hidden via JavaScript on form submit (no page reload)
  - Text color: red (`#dc2626` in error states)
- Password strength meter (advisory UX only):
  - Visual bar showing strength (empty to strong)
  - Criteria list showing requirements (length, lowercase, uppercase, digit, special)
  - Real-time validation as user types
  - No impact on form submission; purely frontend guidance
- Submit button: "Create Account" (same styling as login button)
- Signin link: "Already have an account? Sign in"

### Dashboard
- Body background: `#eef1f8` (`--color-bg-dashboard`)
- Hero banner beneath header:
  - Background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%)
  - Padding: 100px top, 32px sides, 32px bottom
  - Layout: flex row with space-between, wrapping enabled
  - Gap: 16px between columns
  - Left section:
    - Title: "Security Vulnerability Lab" (2rem, 800 weight, white text)
    - Subtitle: "Explore, Exploit, and Learn" (1rem, 85% opacity white text)
  - Right section:
    - Username display: "Logged in as <strong>[username]</strong>" (0.9rem, 90% opacity white text)
    - Profile button: links to `/profile`
    - Logout button: links to `/logout`
- Content area:
  - Max width: 1100px, centered horizontally
  - Padding: 32px top/bottom, 24px sides
- Mission card:
  - White background (`--color-bg-surface`)
  - Border radius: 12px
  - Padding: 32px
  - Margin bottom: 32px
  - Border: 1px solid `var(--color-border-soft)`
  - Section title: "Our Mission" (1.4rem, 700 weight)
  - Description: paragraph about educational purpose
- Vulnerabilities section:
  - Header: "VULNERABILITIES TO DISCOVER" (0.82rem, 600 weight, uppercase, letter-spaced 1.5px)
  - Grid layout: 2 columns, 16px gap
  - Vulnerability cards:
    - Background: white (`--color-bg-surface`)
    - Border radius: 10px
    - Padding: 20px
    - Border: 1px solid `var(--color-border-soft)`
    - Transition: box-shadow 0.2s ease
    - Hover state: box-shadow `0 4px 16px rgba(26,35,126,0.10)`
    - Content:
      - Tag pill: display: inline-block, padding 4px 10px, border-radius 6px, font-size 0.75rem, font-weight 600
      - Title: h4 element, 0.95rem, 700 weight, primary text color
      - Description: p element, 0.85rem, secondary text color, line-height 1.5
    - Tag colors:
      - SQLi: background `#fef9c3`, text `#854d0e`
      - XSS: background `#fee2e2`, text `#991b1b`
      - Session: background `#f3e8ff`, text `#6b21a8`
      - Brute: background `#ffedd5`, text `#9a3412`
      - Crypto: background `#dcfce7`, text `#166534`
      - Exposed: background `#dbeafe`, text `#1e40af`
      - CSRF: background `#fce7f3`, text `#9d174d`
- Process steps section:
  - Container: flex row with 16px gap
  - Step cards:
    - Flex: 1 (equal width distribution)
    - Background: `#1a237e` (`--color-step-bg`)
    - Border radius: 12px
    - Padding: 24px
    - Text color: white (`--color-step-text`)
    - Text alignment: center
    - Step badge:
      - Width/height: 40px
      - Border radius: 50%
      - Background: `rgba(255,255,255,0.2)` (`--color-step-badge`)
      - Display: inline-flex, align-items center, justify-content center
      - Font size: 1.1rem, font-weight 700
      - Margin bottom: 12px
    - Step title: h4 element, 1.1rem, 700 weight, margin bottom 8px
    - Step description: p element, 0.82rem, color `rgba(255,255,255,0.85)` (`--color-step-muted`), line-height 1.5

### Responsive Behavior
- Breakpoint: 768px
- Below 768px:
  - Auth pages (login/signup):
    - Layout changes from grid-template-columns: 1fr 1fr to 1fr (single column)
    - Left panel: min-height: auto, padding: 90px 24px 40px
    - Right panel: padding: 32px 24px
  - Dashboard:
    - Vulnerability grid: grid-template-columns changes from 1fr 1fr to 1fr (single column)
    - Process steps: flex-direction changes from row to column (vertical stack)
  - Header:
    - Logo dimensions: reduced to 40px width, 40px height
  - Hero banner:
    - Flex-direction: column (stacks vertically)
    - Text-align: center
    - Padding-top: 90px (increased for mobile)
    - Hero-right: flex-direction: column (stacks vertically)
  - Theme toggle:
    - Dimensions: 36px width, 36px height
    - Font size: 1rem
    - Margin-right: 8px

## Form Specifications

### Registration Form
- Fields: username (text), email (email), password (password), confirm_password (password)
- Submission method: POST to `/signup` (traditional form submission, not AJAX)
- Client-side validation:
  - Occurs on form submit event via JavaScript
  - Compares password and confirm_password field values
  - If mismatch: prevents form submission (`e.preventDefault()`), displays "Passwords do not match" in span below confirm field
  - No page reload occurs during validation
  - Validation is purely frontend; identical check not performed on server
- Server-side processing:
  - Validates presence of all fields
  - MD5 hash of password (no salt)
  - SQL INSERT via string concatenation (vulnerable)
  - On success: redirect to `/login`
  - On username conflict: returns HTML with "Username already exists" message
- Field styling:
  - All inputs: width 100%, padding 12px 16px, font-size 0.9rem
  - Background: `#f8f9ff`, border: 1.5px solid `#c5cae9`, border-radius 8px
  - Focus: border-color `#3949ab`, box-shadow `0 0 0 3px rgba(57,73,171,0.12)`
  - Placeholder color: `#64748b` (`--color-text-muted`)
- Password strength meter:
  - Advisory only; does not affect form submission
  - Visual feedback via progress bar and criteria checklist
  - Updates in real-time on password input
  - Shows requirements: 8+ chars, lowercase, uppercase, digit, special character

### Login Form
- Fields: username (text), password (password)
- Submission method: AJAX via `fetch()` API (not traditional form submission)
- Client-side handling:
  - Event listener prevents default form submission (`e.preventDefault()`)
  - Form data collected via `new URLSearchParams(new FormData(form))`
  - Sent as `application/x-www-form-urlencoded` to `/login` endpoint
  - Response handling:
    - On success: `window.location.href = data.redirect`
    - On failure: displays `data.error` in `#error-message` div
    - Special handling for `unverified` and `otp_required` flags
- Field styling: identical to registration form
- Button: full-width, primary styling (`#1a237e` background, white text)
- CSRF token: included as hidden input but not validated (vulnerability)
- Error message area:
  - Initially hidden (`display: none`)
  - Background: `#fef2f2`, border: 1px solid `#fecaca`, text color: `#991b1b`
  - Padding: 12px, border-radius: 8px
  - Made visible on login failure

## Validation Rules

### Registration
- Fields required: username, email, password, confirm_password (client-side enforces password match)
- Username uniqueness: enforced at database level via UNIQUE constraint on username column
  - Violation results in "Username already exists" error
- Email format: validated via HTML5 `type="email"` attribute (browser-level)
- Password confirmation: client-side JavaScript comparison before form submission
  - No server-side confirmation of password match
- No length, complexity, or character requirements enforced server-side
- Password strength meter provides advisory frontend feedback only

### Login
- Fields required: username, password (both required for form submission to proceed)
- No client-side validation beyond HTML5 `required` attributes
- Server-side validation: checks presence of both fields
- Authentication: MD5 hash of password compared against stored hash via SQL query
- No rate limiting, lockout, or delay on failed attempts
- No IP-based or username-based throttling

### Search
- Parameter required: `query` (GET parameter)
- No validation performed on query parameter
- Empty string permitted (returns empty results)
- No length or character restrictions
- Direct interpolation into SQL LIKE clauses and HTML response (dual vulnerability: SQLi and XSS potential)

## Session State Model

### Stored Values
- `user_id`: integer value from `users.id` column
- `username`: string value from `users.username` column
- `email`: string value from `users.email` column

### Lifecycle
- Creation: 
  - Occurs upon successful login in `login_post()` handler
  - After validating credentials via SQL query
  - Set via: `session['user_id'] = row['id']`, `session['username'] = row['username']`, `session['email'] = row['email']`
- Usage:
  - Checked on every access to protected routes (`/welcome`, `/profile`, etc.)
  - Validation: `if 'user_id' not in session:` then redirect to `/login`
  - Value retrieved for dashboard display: `session['username']` used in string substitution
- Destruction:
  - Occurs on logout via `session.clear()` in `logout()` handler
  - Also occurs implicitly when session cookie expires (default lifetime)
  - No explicit timeout or idle timeout implemented
- Storage mechanism:
  - Client-side cookie (default Starlette SessionMiddleware behavior)
  - Cookie name: "session"
  - Contents: signed and encrypted session data
  - Signing key: hardcoded "super-secret-key-12345" (vulnerability)
  - No server-side storage; state resides entirely in client cookie

## Data Lifecycle Rules

### User Creation
- Occurs exclusively during registration (`/signup` POST handler)
- Triggered by successful form submission with valid, unique username
- Process:
  1. Hash password via `hash_password()` (MD5, no salt)
  2. Construct INSERT query via string concatenation
  3. Execute via `session.py:get_db()` connection
  4. Auto-increment `id` assigned by SQLite
- No alternative user creation mechanisms exist (no admin creation, no API creation, etc.)

### User Modification
- No modification workflow exists in the application
- No endpoints for updating username, email, or password
- No profile edit functionality implemented
- User attributes are immutable after creation (except via direct database manipulation)

### User Deletion
- No deletion workflow exists in the application
- No endpoints for removing user accounts
- Account persistence is permanent (until manual database deletion)
- No soft-delete or archival mechanism

### Recovery Workflow
- No account recovery or password reset functionality
- No email verification implementation (despite references in code)
- No ability to recover forgotten credentials
- Lost credentials require new account creation (if username/email available) or manual database reset

## Success Paths

### SP-01: Successful Registration
1. User navigates to `/signup`
2. User completes form with unique username, valid email, matching passwords
3. Client-side password match validation passes
4. Form submitted to `/signup`
5. Server validates fields, hashes password, inserts record
6. Server responds with redirect to `/login`
7. Browser redirects to `/login` and displays login form
8. User proceeds to login flow

### SP-02: Successful Login
1. User navigates to `/login`
2. User enters valid username and password
3. Form submission intercepted by JavaScript
4. AJAX request sent to `/login` with form data
5. Server validates credentials via SQL query
6. Query returns matching user record
7. Server sets session variables and responds with `{ success: true, redirect: "/welcome" }`
8. Client receives response and redirects to `/welcome`
9. Server renders dashboard with username substitution
10. Browser displays authenticated dashboard

### SP-03: Dashboard Access
1. Authenticated user navigates to `/welcome`
2. Server verifies `user_id` present in session
3. Server loads `dashboard.html` template
4. Performs string replacement: `{{username}}` → `session['username']`
5. Returns HTML response with personalized username
6. Browser renders page showing user's name in hero banner
7. User can interact with dashboard elements (logout, profile links)

### SP-04: Successful Logout
1. Authenticated user clicks logout button or navigates to `/logout`
2. Server invokes `logout()` handler
3. Session cleared via `session.clear()`
4. Server responds with redirect to `/login`
5. Browser redirects to login page
6. User session terminated; subsequent access to protected routes redirects to login

## Alternate Paths

### AP-01: Duplicate Username Registration
1. User navigates to `/signup`
2. User completes form with username that already exists in database
3. Client-side password match validation passes (if passwords match)
4. Form submitted to `/signup`
5. Server validates fields, hashes password
6. Attempts INSERT query: `INSERT INTO users ... VALUES ('duplicate_username', ...)`
7. SQLite throws constraint violation on UNIQUE username
8. Server catches exception and returns HTML response with "Username already exists" message
9. Browser displays registration form with error message visible
10. User must choose different username to proceed

### AP-02: Invalid Credentials Login
1. User navigates to `/login`
2. User enters incorrect username or password
3. Form submission intercepted by JavaScript
4. AJAX request sent to `/login` with form data
5. Server validates fields, hashes provided password
6. Executes SQL query: `SELECT * FROM users WHERE username = '...' AND password = '...'`
7. Query returns zero rows (no match)
8. Server responds with `{ success: false, error: "Invalid credentials" }`
9. Client receives response and displays error message in `#error-message` div
10. Error message becomes visible; form remains for retry

### AP-03: Unauthorized Dashboard Access
1. User (authenticated or not) navigates to `/welcome`
2. Server executes `welcome_page()` handler
3. Checks `if 'user_id' not in session:`
4. If no user_id in session (or session expired/cleared):
   - Returns `RedirectResponse(url='/login')`
5. Browser redirects to `/login` endpoint
6. Login form displayed; user must authenticate to access dashboard
7. Authenticated users with valid session proceed to dashboard rendering

### AP-04: Empty Search Query
1. User navigates to `/search` (directly or via form)
2. Provides empty query parameter (`?q=` or no parameter)
3. Server processes request in `search_user()` handler
4. No authentication check performed
5. SQL query constructed: `SELECT username, email FROM users WHERE username LIKE '%%' OR email LIKE '%%'`
6. Query returns all users (since empty string matches everything)
7. Response built via string concatenation of results
8. Browser displays list of all users in format: `username (email)` for each
9. No "no results" message; empty query returns all records

## Edge Cases

### EC-01: Existing Username During Registration
- As described in AP-01: SQL constraint violation triggers error handling
- User receives "Username already exists" message
- No differentiation between exact match vs case-insensitive match (database collation dependent)
- Error message displayed in HTML response (not via AJAX)

### EC-02: Empty Registration Data
- User submits registration form with empty fields
- Client-side: HTML5 `required` attributes prevent submission if fields empty
- If bypassed (e.g., via direct API call):
  - Server receives empty strings for username, email, password
  - Password hashed: MD5 of empty string = `d41d8cd98f00b204e9800998ecf8427e`
  - SQL INSERT attempted with empty values
  - Username field empty string may violate UNIQUE constraint if another empty username exists
  - No explicit validation or error handling for empty fields
  - Behavior depends on database constraints and SQLite's handling of empty strings

### EC-03: Empty Login Data
- User submits login form with empty fields
- Client-side: HTML5 `required` attributes prevent submission if fields empty
- If bypassed (e.g., via direct API call):
  - Server receives empty strings for username and password
  - Password hashed: MD5 of empty string = `d41d8cd98f00b204e9800998ecf8427e`
  - SQL query: `SELECT * FROM users WHERE username = '' AND password = 'd41d8cd98f00b204e9800998ecf8427e'`
  - Returns row only if user exists with empty username and password hash of empty string
  - Otherwise returns no results → "Invalid credentials" error
  - No distinction between missing credentials vs invalid credentials

### EC-04: Missing Session
- User attempts to access `/welcome` with no session cookie
- Server checks `if 'user_id' not in session:` → evaluates to True
- Returns `RedirectResponse(url='/login')`
- Browser redirects`
- No session creation or initialization attempted
- Pure redirect to login page

### EC-05: Corrupted Session
- User presents invalid or tampered session cookie
- Signature verification fails due to incorrect secret key
- Depending on middleware implementation:
  - May result in empty session dict (`{}`)
  - May cause exception during request processing
  - In either case, `'user_id' not in session` evaluates to True
  - Results in redirect to `/login`
- No explicit error messaging for tampered sessions
- User experience identical to missing session

### EC-06: Missing Template File
- User requests endpoint that attempts to load missing template (e.g., `/nonexistent`)
- If route exists but template file missing:
  - `FileNotFoundError` raised when attempting to open template
  - Not caught by route handler → results in 500 Internal Server Error
  - Error details exposed in response (debug information)
- If route itself missing:
  - Standard 404 Not Found response from framework
- No custom error pages or graceful degradation

### EC-07: Missing Database File
- Application starts with `vulnerable_app.db` file missing or deleted
- On startup, `main.py` calls `init_db()` before starting server
- `init_db()` calls `session.py:init_db()` 
- `init_db()` executes: `CREATE TABLE IF NOT EXISTS users ...`
- Since file doesn't exist, SQLite creates new empty database file
- Table created successfully in new file
- Application continues normally with empty database
- No error or warning displayed to user
- Subsequent registrations will populate the new database

### EC-08: Application Restart
- Application process terminated and restarted
- On startup:
  - `main.py` executes: calls `init_db()`, creates FastAPI app, mounts routes, starts server
  - `init_db()` checks for existence of `vulnerable_app.db`
  - If file exists: verifies table exists, creates if missing
  - If file missing: creates new database file with users table
  - No data migration or preservation logic beyond file persistence
- Existing data preserved if database file persists across restarts
- New database created if file missing (data loss)
- All in-memory state (including sessions) lost on restart
- Users must log in again after restart (session cookies become invalid)

## Business Rules

1. Authentication depends solely on the presence of `user_id` in the session dictionary; no additional validation or expiration checks are performed beyond this key's existence.
2. Dashboard requires runtime string substitution of the `{{username}}` placeholder with the value from `session['username']`; no client-side rendering or alternative display methods are used.
3. User records are immutable after creation; no update, modification, or profile editing workflows exist in the application.
4. Login and registration use different response formats: login returns JSON for AJAX handling, registration returns HTML for traditional form submission.
5. Template updates are visible immediately without requiring application restart; templates are read from disk on each request.
6. Database constraint enforcement (UNIQUE on username) serves as the primary uniqueness mechanism; no application-level pre-check for duplicate usernames is performed.

## Rebuild Requirements

A compatible implementation must reproduce the following exact behaviors:

1. **Startup Sequence**:
   - Call `init_db()` to ensure users table exists
   - Initialize FastAPI application instance
   - Configure SessionMiddleware with hardcoded secret "super-secret-key-12345"
   - Mount static files directory at `/static/*`
   - Include auth router
   - Configure Uvicorn to run on host 0.0.0.0, port 3001 (or PORT env var)

2. **Database Handling**:
   - Use SQLite3 with file `vulnerable_app.db` in project root
   - Table schema: `CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT, password TEXT)`
   - Connection parameters: `check_same_thread=False`, `row_factory=sqlite3.Row`
   - No connection pooling; each operation gets new connection via `get_db()`

3. **Authentication Flow**:
   - Login: AJAX form submission to `/login` via `fetch()` API
   - Login validation: presence check + MD5 hash + SQL string concatenation query
   - Session population: set `user_id`, `username`, `email` keys on successful auth
   - Session validation: check `if 'user_id' not in session:` for route protection
   - Logout: `session.clear()` + redirect to `/login`

4. **Registration Flow**:
   - Traditional form submission to `/signup`
   - Client-side: password match validation via JavaScript (prevents submit on mismatch)
   - Server-side: field presence check + MD5 hash + SQL string concatenation INSERT
   - Username uniqueness: enforced by SQLite UNIQUE constraint (error message on violation)
   - Success: redirect to `/login`
   - Failure: HTML response with error message

5. **Template Handling**:
   - Load HTML templates from disk on each request (no caching)
   - Perform runtime string substitution: replace `{{username}}` with `session['username']` in dashboard template
   - No other template placeholders or processing
   - Serve static assets (CSS, images) unchanged from `/static/*`

6. **Vulnerability Implementations** (must be preserved exactly):
   - SQL Injection: string concatenation in SQL queries (login and signup)
   - Stored XSS: unsanitized username stored and reflected via `{{username}}` substitution
   - Reflected XSS: direct interpolation of search query into HTML response without escaping
   - Session Hijacking: hardcoded weak secret key for session signing
   - Weak Password Storage: MD5 hash without salt
   - Exposed Database: `/download/db` endpoint with no authentication check
   - No Rate Limiting: absent on all endpoints
   - CSRF: missing token validation on all POST endpoints

7. **Frontend Behavior**:
   - Login form submitted via AJAX `fetch()` (not traditional submit)
   - Signup form submitted via traditional POST (not AJAX)
   - Password match validation: client-only for signup (prevents submit), none for login
   - Error display: DOM manipulation to show/hide message containers
   - Theme toggle: client-side only via `localStorage` and `data-theme` attribute
   - Responsive breakpoints: 768px for mobile layout changes
   - Visual fidelity: exact colors, spacing, typography, and component styling as specified in CSS

## Acceptance Criteria

### AC-01: Registration Functionality
- Given a user with unique username, valid email, and matching passwords
- When they submit the registration form
- Then an account is created in the database
- And they are redirected to the login page
- And the password is stored as an MD5 hash (no salt)
- And attempting to register with the same username yields "Username already exists" error

### AC-02: Login Functionality
- Given a user with valid credentials in the database
- When they submit the login form with those credentials
- Then they are authenticated and redirected to the dashboard
- And their session contains `user_id`, `username`, and `email` values
- And invalid credentials produce an "Invalid credentials" error message
- And the login form uses AJAX submission without page reload

### AC-03: Dashboard Access
- Given an authenticated user with active session
- When they access the `/welcome` endpoint
- Then they receive the dashboard page with their username displayed in the hero banner
- And the username appears via server-side string substitution of `{{username}}`
- And unauthorized access (missing/invalid session) redirects to login page

### AC-04: Logout Functionality
- Given an authenticated user with active session
- When they invoke the logout endpoint or click the logout button
- Then their session is completely cleared (`session.clear()` called)
- And they are redirected to the login page
- And subsequent attempts to access protected routes redirect to login

### AC-05: Search Functionality
- Given a search query parameter provided to the `/search` endpoint
- When the endpoint is accessed (regardless of authentication status)
- Then it returns an HTML response containing matching user information
- And the query parameter is directly interpolated into the response without escaping
- And no authentication check is performed on the request

### AC-06: Data Persistence
- Given user accounts created via registration
- When the application is stopped and restarted
- Then all previously created accounts remain accessible via login
- And the database file `vulnerable_app.db` retains all user records
- And new accounts created after restart are persisted to the same file

## Test Cases

| TC-ID | Description | Preconditions | Steps | Expected Result |
|-------|-------------|---------------|-------|-----------------|
| TC-01 | Successful registration with valid data | Clean database, server running | 1. Navigate to /signup<br>2. Fill form: username="testuser", email="test@example.com", password="Password123!", confirm="Password123!"<br>3. Submit form | Account created, redirected to /login, password stored as MD5 hash |
| TC-02 | Registration with duplicate username | Existing user "existinguser" in DB | 1. Navigate to /signup<br>2. Fill form: username="existinguser", email="test2@example.com", password="Pass456!", confirm="Pass456!"<br>3. Submit form | Form remains on signup page, "Username already exists" message displayed |
| TC-03 | Registration with password mismatch | Clean database | 1. Navigate to /signup<br>2. Fill form: username="user3", email="user3@test.com", password="Pass789!", confirm="DifferentPass!"<br>3. Submit form | Form submission blocked, "Passwords do not match" message appears below confirm field |
| TC-04 | Successful login with valid credentials | User "logintest" with password "SecurePass456!" in DB | 1. Navigate to /login<br>2. Fill form: username="logintest", password="SecurePass456!"<br>3. Submit form via AJAX | Redirected to /welcome, session contains user data |
| TC-05 | Login with invalid credentials | Any username/password combination not in DB | 1. Navigate to /login<br>2. Fill form: username="wronguser", password="wrongpass"<br>3. Submit form via AJAX | Error message displayed: "Invalid credentials", remains on login page |
| TC-06 | Dashboard access after login | Successfully logged in as "dashboarduser" | 1. After login, navigate to /welcome<br>2. Observe dashboard content | Dashboard displays "Logged in as <strong>dashboarduser</strong>" in hero banner |
| TC-07 | Dashboard access without authentication | No active session | 1. Navigate directly to /welcome<br>2. Observe response | Redirected to /login page |
| TC-08 | Logout functionality | Authenticated session for user "logouttest" | 1. While logged in, navigate to /logout<br>2. Observe response | Redirected to /login, session cleared, subsequent /welcome redirects to login |
| TC-09 | Search with valid query | Users "alice@example.com" and "bob@test.com" in DB | 1. Navigate to /search?q=alice<br>2. Observe response | Returns HTML: "<li>alice (alice@example.com)</li>" |
| TC-10 | Search with empty query | Any database state | 1. Navigate to /search (no parameter) or /search?q=<br>2. Observe response | Returns HTML list of ALL users in format "username (email)" for each record |
| TC-11 | Responsive layout - desktop | Browser width > 768px | 1. Load login or signup page<br>2. Observe layout | Two-column layout: left panel (gradient + content), right panel (form) |
| TC-12 | Responsive layout - mobile | Browser width < 768px | 1. Load login or signup page<br>2. Observe layout | Single-column layout: full-width sections stacked vertically |
| TC-13 | Persistence across restart | User "persisttest" created via registration | 1. Create account "persisttest"<br>2. Stop application<br>3. Start application<br>4. Attempt login with "persisttest"/password | Login successful, session established, redirected to dashboard |
| TC-14 | Template changes visible without restart | Running application | 1. Modify dashboard.html to change text<br>2. Save file<br>3. Refresh dashboard page in browser | Changes visible immediately without restarting application |
| TC-15 | Session invalidation on logout | Authenticated session | 1. Log in as user "sessiontest"<br>2. Access /welcome to confirm access<br>3. Navigate to /logout<br>4. Immediately attempt to access /warn again | Redirected to /login, access denied until re-authentication |

## Documentation Gaps

1. **Template Caching Behavior**: The documentation states templates are "loaded from disk at request time with no caching" but does not specify whether this is implemented via disabling template caching in the framework or simply reading files directly. The implementation uses direct file reads without any caching layer, but this detail is not explicitly documented.

2. **Password Match Validation Scope**: Documents mention client-side password confirmation for registration but fail to specify that this validation is purely frontend-only with no server-side counterpart, creating a potential bypass vector if JavaScript is disabled or circumvented.

3. **Session Cookie Security Characteristics**: While the implementation uses Starlette SessionMiddleware, the documentation does not mention that the session cookie lacks HttpOnly and Secure flags, leaving it accessible to JavaScript and transmittable over non-HTTPS connections.

4. **Error Information Leakage**: The documentation mentions error messages like "Username already exists" but does not document that this represents user enumeration vulnerability (information disclosure about existing accounts) which could be exploited for reconnaissance attacks.