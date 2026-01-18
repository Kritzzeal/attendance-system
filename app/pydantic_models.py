# app/pydantic_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, time
from enum import Enum

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class AttendanceMark(BaseModel):
    student_id: str
    status: str  # Using string instead of enum for flexibility

class AttendanceBatch(BaseModel):
    course_code: str
    session_type: str
    section_batch: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    attendance_list: List[AttendanceMark]

class AttendanceQuery(BaseModel):
    course_code: Optional[str] = None
    student_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    session_type: Optional[str] = None
    section_batch: Optional[str] = None

class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class AttendanceStats(BaseModel):
    student_id: str
    student_name: str
    total_classes: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float

# User models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

# Student models
class StudentCreate(BaseModel):
    student_id: str
    name: str
    year: int
    department: str
    theory_section: str
    practical_batch: str
    student_mobile: str
    parent_mobile: str

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    department: Optional[str] = None
    theory_section: Optional[str] = None
    practical_batch: Optional[str] = None
    student_mobile: Optional[str] = None
    parent_mobile: Optional[str] = None
    is_active: Optional[bool] = None

# Course models
class CourseCreate(BaseModel):
    code: str
    title: str
    year: int
    semester: int
    credits: int

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    credits: Optional[int] = None