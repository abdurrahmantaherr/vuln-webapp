# stored-xss-spec.md

## 1. Feature Overview
Fix the stored Cross-Site Scripting (XSS) vulnerability in the dashboard username display. The vulnerability occurs when a user's username containing malicious HTML/JavaScript is stored in the database and later rendered without escaping in the dashboard template, allowing persistent script execution.

## 2. User Story
As a security-conscious user, I want my username to be safely displayed on the dashboard so that even if my account contains malicious data (through exploitation of other vulnerabilities), it cannot execute scripts in my browser or other users' browsers when they view the dashboard.

## 3. Acceptance Criteria
- **AC1**: Legitimate usernames (alphanumeric, spaces, hyphens, underscores) display correctly in the dashboard
- **AC2**: Usernames containing HTML special characters (<, >, &, ", ') are displayed as plain text without executing scripts
- **AC3**: Usernames containing script tags (<script>alert('XSS')</script>) are rendered as escaped HTML entities
- **AC4**: The fix does not break existing login, logout, or session functionality
- **AC5**: The dashboard page continues to return HTTP 200 for authenticated users and HTTP 303 redirect for unauthenticated users

## 4. Functional Specifications
The application shall implement HTML escaping for the username variable before substituting it into the dashboard template. Specifically:
- The username string obtained from the session shall be processed through an HTML escaping function
- The escaped string shall replace the {{username}} placeholder in the dashboard.html template
- The escaping shall convert: < to &lt;, > to &gt;, & to &amp;, " to &quot;, ' to &#x27;
- The substituted template shall be returned as an HTMLResponse

## 5. UI/UX Requirements
- **Visual Consistency**: Legitimate usernames must appear exactly as entered (no visual alteration)
- **Error Prevention**: Malicious usernames must not cause visual rendering issues or broken layouts
- **Accessibility**: Escaped content must remain readable by screen readers
- **Performance**: The escaping operation shall not noticeably impact page load times
- **Browser Compatibility**: Solution must work in all supported browsers (Chrome, Firefox, Safari, Edge)

## 6. API Contract (exact signature)
```python
from fastapi import Request
from fastapi.responses import HTMLResponse

@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request) -> HTMLResponse:
    """
    Serve dashboard with username substitution (XSS-fixed version)
    
    Args:
        request: FastAPI Request object containing session data
        
    Returns:
        HTMLResponse: Rendered dashboard template with escaped username
        
    Raises:
        HTTPException: 303 redirect to /login if user not authenticated
    ```
## 7. Data Requirements
- **Input**: Username string from request.session.get("username", "User")
- **Validation**: No additional validation required beyond existing session checks
- **Storage**: No changes to data storage; username remains stored as-is in database
- **Output**: Escaped username string safe for HTML context insertion
- **Data Flow**: Session → HTML escaping → Template substitution → HTTP response

## 8. Business Logic (numbered rules)
1. **Authentication Check**: If "user_id" not in request.session, return HTTP 303 redirect to "/login"
2. **Username Retrieval**: Extract username from request.session.get("username", "User")
3. **HTML Escaping**: Apply html.escape() to the username string
4. **Template Loading**: Read the dashboard.html template file from frontend_templates_dir
5. **Placeholder Substitution**: Replace "{{username}}" with the escaped username string
6. **Response Generation**: Return the modified template as HTMLResponse with 200 status code

## 9. Dependencies
- **Python Standard Library**: `html` module (for html.escape function)
- **Existing Modules**: FastAPI, app.services.auth_service, app.db.session (no changes required)
- **Template File**: frontend/templates/dashboard.html (must contain {{username}} placeholder)
- **No New External Dependencies**: The fix uses only built-in Python functionality

## 10. Out of Scope
- **Reflected XSS**: The search endpoint XSS vulnerability remains intentionally unpatched for educational purposes
- **Other Vulnerabilities**: Session hijacking, exposed database, missing rate limiting, and CSRF vulnerabilities are not addressed by this feature
- **Template Engine Migration**: Not adopting a templating system with auto-escaping (e.g., Jinja2) as it would require architectural changes beyond scope
- **Input Validation**: Not implementing server-side username validation during registration (to preserve other vulnerability demonstrations)
- **Output Contexts**: Only fixing username display in dashboard; other potential output contexts (if any) are not modified

## 11. Testing Requirements (matching ACs)
- **T1 (AC1)**: Register user with username "John Doe", login, visit /dashboard, verify "John Doe" appears correctly
- **T2 (AC1)**: Register user with username "Mary-Jane Smith", login, visit /dashboard, verify exact string match
- **T3 (AC2)**: Register user with username "<script>", login, visit /dashboard, verify "&lt;script&gt;" appears in page source
- **T4 (AC2)**: Register user with username ">alert<", login, visit /dashboard, verify "&gt;alert&lt;" appears in page source
- **T5 (AC3)**: Register user with username "<img src=x onerror=alert(1)>", login, visit /dashboard, verify no script execution occurs
- **T6 (AC4)**: Test login/logout flow still works after fix
- **T7 (AC4)**: Test session persistence across multiple requests
- **T8 (AC5)**: Verify authenticated users get 200 OK on /welcome
- **T9 (AC5)**: Verify unauthenticated users get 303 redirect to /login when accessing /welcome
- **T10**: Verify that the HTML response contains properly escaped entities and no unescaped user input in script contexts