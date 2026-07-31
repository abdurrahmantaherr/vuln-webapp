import sys
import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from .api.routes.auth import router as auth_router

# Add backend/ directory to sys.path so the app can be run from any directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Create FastAPI application
app = FastAPI(title="Vulnerable Web Application")

# Configure SessionMiddleware with hardcoded weak secret (Vulnerability #4: Session Hijacking)
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-12345",  # Intentionally weak and hardcoded
    https_only=False,  # Not setting Secure flag for educational purposes
    same_site="lax"    # Not setting to strict for educational purposes
)

# Include authentication routes
app.include_router(auth_router)

# Mount static files directory
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    from .db.session import init_db
    init_db()

# Configure to run on port 3001 (can be overridden by PORT environment variable)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)