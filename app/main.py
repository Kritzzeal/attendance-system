# app/main.py - FIXED VERSION
import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from .database import init_db
from .routers import users, attendance, teacher_routes, admin,sms_routes
from app.auth import get_user_profile, get_current_user
from app import models, whatsapp_real_service,whatsapp_real_routes


# Initialize database
init_db()

app = FastAPI(
    title="Attendance Management System API",
    description="API for Teacher Attendance System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Configuration for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Check if React build exists
react_build_path = os.path.join(current_dir, "..", "frontend", "build")
react_build_exists = os.path.exists(react_build_path)

# Include API routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(teacher_routes.router, prefix="/api/v1")
app.include_router(sms_routes.router, prefix="/api/v1")
app.include_router(whatsapp_real_routes.router) 
# ============ REACT APP SERVING ============
async def serve_react_app():
    """Serve React index.html if build exists"""
    if react_build_exists:
        index_path = os.path.join(react_build_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=200)
    
    # Fallback: Simple HTML message
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Attendance System API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            .api-link { 
                display: block; 
                margin: 10px 0; 
                padding: 10px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
            .api-link:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 Attendance System API</h1>
            <p>API server is running. Frontend is served separately.</p>
            
            <h3>📚 API Documentation:</h3>
            <a class="api-link" href="/api/docs">OpenAPI/Swagger Documentation</a>
            <a class="api-link" href="/api/redoc">ReDoc Documentation</a>
            
            <h3>🔑 Test Accounts:</h3>
            <ul>
                <li>Admin: hortsekar@yahoo.com / Admin@2025</li>
                <li>Teacher: teacher@college.edu / Teacher@123</li>
            </ul>
            
            <h3>🏠 Frontend:</h3>
            <p>React frontend should be running at: <a href="http://localhost:3000">http://localhost:3000</a></p>
            
            <h3>📞 API Endpoints:</h3>
            <ul>
                <li><code>POST /api/v1/auth/login</code> - User login</li>
                <li><code>GET /api/v1/teachers</code> - Get all teachers</li>
                <li><code>POST /api/v1/attendance/mark</code> - Mark attendance</li>
                <li><code>GET /api/v1/attendance/teacher/courses</code> - Get teacher courses</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# Root route
@app.get("/api/v1/auth/profile", response_model=dict)
async def profile(current_user: models.User = Depends(get_current_user)):
    """Get current user profile with role"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or current_user.email.split('@')[0],
        "role": current_user.role,
        "is_active": current_user.is_active,
        "teacher_id": getattr(current_user, 'teacher_id', None)
    }
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main page"""
    return await serve_react_app()

# Specific frontend routes (for direct navigation)
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve login page"""
    return await serve_react_app()

@app.get("/admin/teachers", response_class=HTMLResponse)
async def admin_teachers_page():
    """Serve admin teachers page"""
    return await serve_react_app()

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page():
    """Serve admin dashboard page"""
    return await serve_react_app()

@app.get("/teacher/my-classes", response_class=HTMLResponse)
async def teacher_classes_page():
    """Serve teacher my-classes page"""
    return await serve_react_app()

@app.get("/teacher/mark-attendance", response_class=HTMLResponse)
async def mark_attendance_page():
    """Serve mark attendance page"""
    return await serve_react_app()

# Catch-all route for React Router (only if React build exists)
if react_build_exists:
    @app.get("/{full_path:path}")
    async def catch_all(request: Request, full_path: str):
        """Catch all other routes for React Router"""
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": f"API endpoint not found: {full_path}"}
            )
        
        # Check if file exists in build directory
        file_path = os.path.join(react_build_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except:
                pass
        
        # Fallback to index.html for React Router
        index_path = os.path.join(react_build_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        
        return await serve_react_app()
else:
    @app.get("/{full_path:path}")
    async def catch_all_api_only(full_path: str):
        """Catch all for API-only mode"""
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": f"API endpoint not found: {full_path}"}
            )
        return await serve_react_app()

# ============ API INFO ============
@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "attendance-system"}

@app.get("/api/info")
def api_info():
    return {
        "name": "Attendance Management System",
        "version": "1.0.0",
        "api_base": "/api/v1",
        "docs": "/api/docs",
        "frontend": "http://localhost:3000" if not react_build_exists else "Built-in",
        "endpoints": {
            "auth": ["POST /api/v1/auth/login", "POST /api/v1/auth/register"],
            "attendance": ["POST /api/v1/attendance/mark", "GET /api/v1/attendance/teacher/courses"],
            "admin": ["GET /api/v1/admin/teachers", "POST /api/v1/admin/upload-courses"],
            "teachers": ["GET /api/v1/teachers", "POST /api/v1/teachers/import/excel"]
        }
    }

@app.on_event("startup")
async def startup_event():
    """Startup configuration"""
    print("\n" + "="*50)
    print("🚀 Attendance System API Started")
    print("="*50)
    print(f"📚 API Documentation: http://localhost:8000/api/docs")
    
    if react_build_exists:
        print(f"🏠 Frontend: Built-in (from {react_build_path})")
        print(f"   Access at: http://localhost:8000/")
    else:
        print(f"🏠 Frontend: Separate React app")
        print(f"   Run React on: http://localhost:3000")
    
    print(f"🔑 Admin Login: hortsekar@yahoo.com / Admin@2025")
    print(f"👨‍🏫 Teacher Login: teacher@college.edu / Teacher@123")
    print("="*50)

    