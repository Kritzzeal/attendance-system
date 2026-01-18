# app/database.py - WITH HARCODED ADMIN
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models
from passlib.context import CryptContext
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/attendance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False},
    pool_pre_ping=True,
     pool_size=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with hardcoded admin account"""
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = db.query(models.User).filter(models.User.email == "hortsekar@yahoo.com").first()
        
        if not admin:
            # Create password hasher
            pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            
            # HARCODED ADMIN CREDENTIALS
            admin_email = "hortsekar@yahoo.com"      # Your email
            admin_password = "Admin@2025"           # Change this after first login!
            admin_name = "System Administrator"     # Your name
            admin_mobile = "0000000000"             # Your mobile number
            
            # Create admin user
            admin_user = models.User(
                email=admin_email,
                name=admin_name,
                teacher_id="ADMIN001",
                role="admin",
                mobile=admin_mobile,
                hashed_password=pwd_context.hash(admin_password)
            )
            
            db.add(admin_user)
            db.commit()
            print("=" * 50)
            print("✅ ADMIN ACCOUNT CREATED SUCCESSFULLY")
            print("=" * 50)
            print(f"📧 Email: {admin_email}")
            print(f"🔑 Password: {admin_password}")
            print(f"👤 Name: {admin_name}")
            print(f"📱 Mobile: {admin_mobile}")
            print("=" * 50)
            print("⚠️  IMPORTANT: Change this password after first login!")
            print("=" * 50)
        else:
            print("✅ Admin account already exists")
            print(f"📧 Email: {admin.email}")
            
        # Create a sample teacher for testing (optional)
        teacher = db.query(models.User).filter(models.User.email == "teacher@college.edu").first()
        if not teacher:
            pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            teacher_user = models.User(
                email="teacher@college.edu",
                name="Sample Teacher",
                teacher_id="T001",
                role="teacher",
                mobile="9876543210",
                hashed_password=pwd_context.hash("Teacher@123")
            )
            db.add(teacher_user)
            db.commit()
            print("✅ Sample teacher created for testing")
            print(f"   Email: teacher@college.edu")
            print(f"   Password: Teacher@123")
            
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("✅ Database initialization complete!")
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
        cursor.close()