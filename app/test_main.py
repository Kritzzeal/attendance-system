# test_main.py (temporary file)
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Test API"}

@app.get("/test")
def test():
    return {"test": "working"}

@app.get("/admin/teachers", response_class=HTMLResponse)
def admin_teachers():
    return """
    <html>
        <body>
            <h1>TEST PAGE</h1>
            <p>If you see this, routes are working!</p>
        </body>
    </html>
    """

# Debug print
print("\n=== ROUTES ===")
for route in app.routes:
    print(f"{route.path}")
print("=============\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)