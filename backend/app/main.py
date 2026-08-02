import sys
import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

# Add backend/ directory to sys.path so the app can be run from any directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
    print(f"Added {backend_dir} to sys.path")

# Also add the app directory to sys.path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
    print(f"Added {app_dir} to sys.path")

print(f"Current sys.path: {sys.path}")

# Project root is one level above backend_dir
project_dir = os.path.dirname(backend_dir)

# Create FastAPI application
app = FastAPI(title="Vulnerable Web Application")

# Configure SessionMiddleware with hardcoded weak secret (Vulnerability #4: Session Hijacking)
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-12345",  # Intentionally weak and hardcoded
    https_only=False,  # Not setting Secure flag for educational purposes
    same_site="lax"    # Not setting to strict for educational purposes
)

# Import and include authentication routes
print("Attempting to import auth router...")
try:
    from app.api.routes.auth import router as auth_router
    print("Successfully imported auth router")
    app.include_router(auth_router)
    print("Successfully included auth router")
except Exception as e:
    print(f"Failed to import auth router: {e}")
    raise

# Mount static files directory
from fastapi.staticfiles import StaticFiles
frontend_static_dir = os.path.join(project_dir, "frontend", "static")
app.mount("/static", StaticFiles(directory=frontend_static_dir), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    from app.db.session import init_db
    init_db()

# Configure to run on port 3001 (can be overridden by PORT environment variable)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3001))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"DEBUG: PORT environment variable = {os.getenv('PORT')}")
    print(f"DEBUG: HOST environment variable = {os.getenv('HOST')}")
    print(f"DEBUG: Calculated host = {host}")
    print(f"DEBUG: Calculated port = {port}")
    uvicorn.run(app, host=host, port=port)