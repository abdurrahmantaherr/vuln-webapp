# stored-xss-spec-plan.md

## 1. Feature Summary
Fix the stored Cross-Site Scripting (XSS) vulnerability in the dashboard username display by implementing HTML escaping for the username variable before it is substituted into the dashboard template. This prevents malicious usernames containing HTML/JavaScript from executing scripts when rendered in the browser.

## 2. Pre-conditions & Setup
- The application is running on Python with FastAPI framework
- The backend/auth_service.py already handles user registration and login
- The dashboard template exists at frontend/templates/dashboard.html with a {{username}} placeholder
- User session data is managed via Starlette SessionMiddleware
- The html module from Python standard library is available for use
- No additional dependencies need to be installed
- Git branch fix/stored-xss is currently checked out for development

## 3. Task Breakdown (T1 …)
T1: Import html module in backend/app/api/routes/auth.py
T2: Modify welcome_page function to escape username before template substitution
T3: Verify the dashboard.html template contains the {{username}} placeholder
T4: Ensure no other files need modification for this specific fix
T5: Prepare test cases to validate the fix works correctly

## 4. File & Module Map (exact paths)
- backend/app/api/routes/auth.py - Primary file to modify (import html, escape username)
- frontend/templates/dashboard.html - Template file containing {{username}} placeholder (verify only)
- backend/app/services/auth_service.py - Unchanged (username storage remains as-is)
- backend/app/main.py - Unchanged (session configuration unaffected)

## 5. Scaffolding Notes
- The fix requires minimal changes: only adding an import and two lines of code
- No new classes, functions, or modules need to be created
- The existing template substitution mechanism will be reused
- No changes to routing, controllers, or service layers are required
- The solution leverages Python's built-in html.escape() function

## 6. Integration Points
- The welcome_page function in auth.py integrates with:
  - Session management (request.session) to retrieve username
  - Template system (frontend/templates/dashboard.html) for display
  - HTML response generation (HTMLResponse) for returning the page
- The fix sits between username retrieval and template substitution
- No changes needed to authentication flow or session handling
- The escaped username flows directly into the existing template system

## 7. Test Plan
- Verify legitimate usernames display correctly (T1, T2 from spec)
- Verify special HTML characters are escaped (T3, T4 from spec)
- Verify script tags are neutralized (T5 from spec)
- Verify login/logout functionality remains intact (T6 from spec)
- Verify session persistence works (T7 from spec)
- Verify HTTP status codes for authenticated/unauthenticated access (T8, T9 from spec)
- Verify HTML output contains properly escaped entities (T10 from spec)
- Manual testing: Register user with XSS payload, login, view dashboard source
- Automated testing: Unit test html.escape() function behavior

## 8. Edge Cases & Error Handling
- Empty username: Should default to "User" and escape correctly
- Very long username: Ensure escaping doesn't cause performance issues
- Username with only special characters: Should escape completely
- Already escaped username: Double escaping should be handled correctly (html.escape is idempotent)
- Missing session data: Existing authentication redirect should still work
- Template file missing: Existing error handling should remain unchanged
- Non-ASCII characters: HTML escaping should handle UTF-8 correctly

## 9. Rollback Strategy
- Remove the import html statement from backend/app/api/routes/auth.py
- Revert the welcome_page function to use raw username instead of escaped_username
- Verify the application returns to its pre-fix state (vulnerable but otherwise functional)
- No database migrations or data changes are involved, so rollback is purely code-based
- Git checkout of the previous commit would restore the vulnerable state if needed

## 10. Definition of Done
- The stored-xss-spec.md feature specification has been implemented
- All acceptance criteria (AC1-AC5) are satisfied
- The fix has been verified to eliminate stored XSS via username display
- All existing functionality (login, logout, session management) remains intact
- No new vulnerabilities have been introduced by the fix
- The application starts and runs successfully with the changes
- Code has been reviewed and meets the project's coding standards
- The fix is ready for merging into the main branch after approval