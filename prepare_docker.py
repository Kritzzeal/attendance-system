# prepare_docker.py
#!/usr/bin/env python3
import os
import shutil
import sqlite3

def prepare_for_docker():
    """Prepare your local setup for Docker"""
    
    print("🔧 Preparing your app for Docker...")
    
    # 1. Check if data directory exists
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Created {data_dir}/ directory")
    
    # 2. Check if SQLite database exists
    db_path = os.path.join(data_dir, "attendance.db")
    
    if os.path.exists(db_path):
        # Verify it's a valid SQLite database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            print(f"✅ Found existing database with {len(tables)} tables")
            for table in tables[:5]:  # Show first 5 tables
                print(f"   - {table[0]}")
            if len(tables) > 5:
                print(f"   ... and {len(tables) - 5} more")
                
        except Exception as e:
            print(f"⚠️  Database might be corrupted: {e}")
    else:
        print("ℹ️  No existing database found. One will be created on first run.")
    
    # 3. Create necessary files
    files_to_create = {
        "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    curl \\
    sqlite3 \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/
COPY templates/ ./templates/

RUN mkdir -p /app/data

RUN useradd -m -u 1000 fastapi && \\
    chown -R fastapi:fastapi /app

USER fastapi

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]""",
        
        "docker-compose.yml": """version: '3.8'

services:
  attendance-app:
    build: .
    container_name: attendance-backend
    ports:
      - "8000:8000"
    environment:
      SQLITE_DB_PATH: /app/data/attendance.db
      SECRET_KEY: your-secret-key-change-this
      ENVIRONMENT: production
      ALLOWED_ORIGINS: "*"
      FAST2SMS_API_KEY: "GjYSIu5N9E...z9rTdjqEaf"
      WHATSAPP_PHONE_NUMBER_ID: "994096853778961"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3""",
        
        ".dockerignore": """venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
*.sqlite
*.sqlite3
.DS_Store
.git/
.github/
.vscode/
.idea/
logs/
tmp/
temp/"""
    }
    
    for filename, content in files_to_create.items():
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(content)
            print(f"✅ Created {filename}")
        else:
            print(f"ℹ️  {filename} already exists, skipping")
    
    print("\n" + "="*50)
    print("🎉 Docker setup complete!")
    print("="*50)
    print("\nTo run your app in Docker:")
    print("1. docker-compose up -d")
    print("2. Visit: http://localhost:8000")
    print("3. Check logs: docker-compose logs -f")
    print("\nTo stop: docker-compose down")
    print("\nYour local venv setup remains unchanged!")

if __name__ == "__main__":
    prepare_for_docker()