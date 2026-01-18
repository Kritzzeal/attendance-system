# Save this as app/models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Boolean
from sqlalchemy.sql import func
Base = declarative_base()
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In app/models.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    teacher_id = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)  # Changed from hashed_password to password for plain text
    role = Column(String, default="teacher")
    mobile = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Remove set_password and verify_password methods for now
    # Or keep them but make them simple
    def set_password(self, password: str):
        """Store plain password (for testing only)"""
        self.password = password
    
    def verify_password(self, password: str):
        """Simple password check (for testing only)"""
        return self.password == password

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    name = Column(String)
    year = Column(Integer)
    theory_section = Column(String)
    practical_batch = Column(String)
    student_mobile = Column(String)
    parent_mobile = Column(String)
    is_active = Column(Boolean, default=True)

class Course(Base):
    __tablename__ = "courses"
    
    code = Column(String, primary_key=True)  # Primary key is code, not id
    title = Column(String)
    year = Column(Integer)
    semester = Column(Integer)
    credits = Column(String)  # VARCHAR in your schema
    has_theory = Column(Boolean, default=False)
    has_practical = Column(Boolean, default=False)

class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    employee_id = Column(String, unique=True, index=True)
    designation = Column(String)
    department = Column(String)
    qualification = Column(String)
    experience = Column(String)
    profile_image = Column(String, nullable=True)
    is_hod = Column(Boolean, default=False)
    
    user = relationship("User", backref="profile")

class TeacherCourse(Base):
    __tablename__ = "teacher_courses"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))  # References users.id
    course_code = Column(String, ForeignKey("courses.code"))
    section = Column(String)
    batch = Column(String)

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    course_code = Column(String, ForeignKey("courses.code"))
    session_type = Column(String)  # theory, practical, lab, tutorial
    section_batch = Column(String)  # TA/TB for theory, PA/PB/PC/PD for practical
    student_id = Column(String, ForeignKey("students.student_id"))
    status = Column(String)  # present, absent, late, excused
    teacher_id = Column(Integer, ForeignKey("users.id"))
    sms_sent = Column(Boolean, default=False)
    sms_sent_at = Column(Time, nullable=True)


# In models.py, update these models:

class SMSTemplate(Base):
    __tablename__ = "sms_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SMSSent(Base):
    __tablename__ = "sms_sent"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ADD autoincrement=True
    attendance_id = Column(Integer, nullable=True)
    student_id = Column(Integer, nullable=True)
    parent_mobile = Column(String(15), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="pending")
    cost = Column(DECIMAL(10, 2), default=0)
    message_id = Column(String(100), nullable=True)
    provider_response = Column(Text, nullable=True)