from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from app.services.auth_service import signup, login
from app.db.session import get_db
import os
import json

# Get project root directory for template paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
frontend_templates_dir = os.path.join(project_root, "frontend", "templates")
print(f"DEBUG: project_root = {project_root}")
print(f"DEBUG: frontend_templates_dir = {frontend_templates_dir}")

router = APIRouter()

@router.get("/")
async def index():
    """Redirect root to signup page"""
    return RedirectResponse(url="/signup", status_code=303)

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serve signup form by reading template from disk"""
    with open(os.path.join(frontend_templates_dir, "signup.html"), "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@router.post("/signup", response_class=HTMLResponse)
async def signup_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """Process user registration"""
    result = signup(username, email, password)

    if isinstance(result, dict) and result.get("success"):
        return RedirectResponse(url=result["redirect"], status_code=303)
    else:
        # Handle error: result is a JSONResponse
        # Extract the error message from the JSONResponse's body
        try:
            # We assume the response is application/json and contains an "error" key
            error_data = json.loads(result.body.decode())
            error_msg = error_data.get("error", "Registration failed")
        except:
            error_msg = "Registration failed"
        # Then we need to inject this error_msg into the template.
        with open(os.path.join(frontend_templates_dir, "signup.html"), "r", encoding="utf-8") as f:
            content = f.read()
        error_html = f'''
        <div class="error-message" style="display: block; margin-bottom: 16px; padding: 12px; background-color: #fef2f2; border: 1px solid #fecaca; color: #991b1b; border-radius: 8px;">
            {error_msg}
        </div>
        '''
        # Insert error after the form container opening tag
        content = content.replace('<div class="form-container">', f'<div class="form-container">{error_html}')
        return HTMLResponse(content=content)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login form by reading template from disk"""
    with open(os.path.join(frontend_templates_dir, "login.html"), "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """Process user login - returns JSONResponse for AJAX handling"""
    result = login(username, password)

    # Handle successful login (returns dict)
    if isinstance(result, dict) and result.get("success"):
        # Set session variables
        request.session["user_id"] = result["user_id"]
        request.session["username"] = result["username"]
        request.session["email"] = result["email"]
        # Return JSON response for client-side handling
        return JSONResponse(content={
            "success": True,
            "redirect": result["redirect"]
        })

    # Handle error cases (returns JSONResponse)
    elif hasattr(result, 'status_code'):  # It's a Response object (JSONResponse)
        return JSONResponse(content={"error": "Login failed"}, status_code=result.status_code)

    # Fallback for any other unexpected return type
    else:
        return JSONResponse(content={"error": "Authentication error"}, status_code=401)

@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request):
    """Serve dashboard with username substitution"""
    # Check for authentication (Vulnerability #4: Session Hijacking due to weak secret)
    if "user_id" not in request.session:
        return RedirectResponse(url="/login", status_code=303)

    # Get username from session
    username = request.session.get("username", "User")

    # Load dashboard template and perform string substitution
    with open(os.path.join(frontend_templates_dir, "dashboard.html"), "r", encoding="utf-8") as f:
        content = f.read()

    # Replace {{username}} placeholder with actual username
    content = content.replace("{{username}}", username)

    return HTMLResponse(content=content)

@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to login"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/search")
async def search_user(request: Request, query: str = ""):
    """Search users with reflected XSS vulnerability"""
    # No authentication check (intentional)

    # Build query with parameterized query (fix for SQL Injection)
    # Still vulnerable to XSS but SQL injection is fixed
    conn = get_db()
    search_pattern = f"%{query}%"
    results = conn.execute(
        "SELECT username, email FROM users WHERE username LIKE ? OR email LIKE ?",
        (search_pattern, search_pattern)
    ).fetchall()
    conn.close()

    # Build HTML response without escaping (Vulnerability #3: Reflected XSS)
    html_items = []
    for row in results:
        html_items.append(f"<li>{row['username']} ({row['email']})</li>")

    html_content = "<ul>" + "".join(html_items) + "</ul>" if html_items else ""
    return HTMLResponse(content=html_content)

@router.get("/download/db")
async def download_database(request: Request):
    """Serve database file with no authentication check"""
    # No authentication check (Vulnerability #6: Exposed Database)
    db_path = "vulnerable_app.db"

    if not os.path.exists(db_path):
        return HTMLResponse(content="Database file not found", status_code=404)

    with open(db_path, "rb") as f:
        content = f.read()

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=vulnerable_app.db"}
    )