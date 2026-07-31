from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from ..services.auth_service import signup, login
from ..db.session import get_db
import os

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/")
async def index():
    """Redirect root to signup page"""
    return RedirectResponse(url="/signup", status_code=303)

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serve signup form by reading template from disk"""
    with open("frontend/templates/signup.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@router.post("/signup", response_class=HTMLResponse)
async def signup_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """Process user registration"""
    result = signup(username, email, password)

    if isinstance(result, RedirectResponse):
        return result
    else:
        # Return error message in HTML response by reading template and replacing error placeholder
        with open("frontend/templates/signup.html", "r", encoding="utf-8") as f:
            content = f.read()
        # Simple error injection - in a real app we'd use proper templating
        error_html = f'''
        <div class="error-message" style="display: block; margin-bottom: 16px; padding: 12px; background-color: #fef2f2; border: 1px solid #fecaca; color: #991b1b; border-radius: 8px;">
            {result.get("error", "Registration failed")}
        </div>
        '''
        # Insert error after the form container opening tag
        content = content.replace('<div class="form-container">', f'<div class="form-container">{error_html}')
        return HTMLResponse(content=content)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login form by reading template from disk"""
    with open("frontend/templates/login.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """Process user login - returns JSONResponse for AJAX handling"""
    result = login(username, password)

    if isinstance(result, dict) and result.get("success"):
        # Return JSON response for client-side handling
        return JSONResponse(content={
            "success": True,
            "redirect": result["redirect"]
        })
    else:
        return JSONResponse(content={"error": result.get("error", "Invalid credentials")}, status_code=401)

@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request):
    """Serve dashboard with username substitution"""
    # Check for authentication (Vulnerability #4: Session Hijacking due to weak secret)
    if "user_id" not in request.session:
        return RedirectResponse(url="/login", status_code=303)

    # Get username from session
    username = request.session.get("username", "User")

    # Load dashboard template and perform string substitution
    with open("frontend/templates/dashboard.html", "r", encoding="utf-8") as f:
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

    # Build query with string concatenation (Vulnerability #3: Reflected XSS potential)
    # Also vulnerable to SQL Injection but primarily demonstrated as XSS
    conn = get_db()
    results = conn.execute(
        f"SELECT username, email FROM users WHERE username LIKE '%{query}%' OR email LIKE '%{query}%'"
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