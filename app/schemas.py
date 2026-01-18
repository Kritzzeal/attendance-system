# app/schemas.py
from pydantic import BaseModel
from typing import Optional,List
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Simple User schemas
class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    teacher_id: Optional[str] = None
    role: Optional[str] = "teacher"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    teacher_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
# Add to existing app/schemas.py

class CourseBase(BaseModel):
    code: str
    title: str
    year: int
    semester: int
    has_theory: bool = True
    has_practical: bool = False

class CourseResponse(CourseBase):
    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    student_id: str
    name: str
    year: int
    theory_section: str
    practical_batch: str
    student_mobile: Optional[str] = None
    parent_mobile: str

class StudentResponse(StudentBase):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    message: str
    courses_created: Optional[int] = None
    courses_updated: Optional[int] = None
    students_created: Optional[int] = None
    students_updated: Optional[int] = None
    total: Optional[int] = None

class StatsResponse(BaseModel):
    total_users: int
    total_teachers: int
    total_courses: int
    total_students: int
    last_updated: str
# Add to your existing schemas.py

class TeacherCreate(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    designation: str = "Asst. Prof."
    qualification: Optional[str] = None
    experience: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None  # Auto-generate if not provided

class TeacherResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    email: str
    department: str
    designation: str
    qualification: Optional[str]
    experience: Optional[str]
    phone: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class TeacherAssignment(BaseModel):
    teacher_id: int
    course_code: str
    section: Optional[str] = None
    batch: Optional[str] = None
    is_primary: bool = True  # Primary teacher for the course

class TeacherAssignmentResponse(BaseModel):
    id: int
    teacher_name: str
    teacher_email: str
    course_code: str
    course_title: str
    section: Optional[str]
    batch: Optional[str]
    is_primary: bool
    
    class Config:
        from_attributes = True

class TeacherUploadResponse(BaseModel):
    message: str
    teachers_created: int = 0
    teachers_updated: int = 0
    assignments_created: int = 0
    errors: List[str] = []

# Course Schemas
class CourseBase(BaseModel):
    code: str
    title: str
    credits: int
    semester: int
    year: int
    has_theory: Optional[bool] = True
    has_practical: Optional[bool] = True

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    credits: Optional[int] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    has_theory: Optional[bool] = None
    has_practical: Optional[bool] = None


class CourseResponse(CourseBase):
    code: int
   
   
    
    class Config:
        orm_mode = True

# Student Schemas
class StudentBase(BaseModel):
    student_id: str
    name: str
    year: int
    theory_section: Optional[str] = "TA"
    practical_batch: Optional[str] = "PA"
    student_mobile: Optional[str] = None
    parent_mobile: Optional[str] = None
    is_active: Optional[bool] = True

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    theory_section: Optional[str] = None
    practical_batch: Optional[str] = None
    student_mobile: Optional[str] = None
    parent_mobile: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    id: int
   
    
    class Config:
        orm_mode = True

# Teacher Update Schema
class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    teacher_id: Optional[str] = None
    mobile: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None
# In schemas.py, update SMS schemas:

class SMSRequest(BaseModel):
    attendance_id: int
    absent_student_ids: List[int]
    course_id: Optional[str] = None
    date: Optional[str] = None
    session: Optional[str] = None

class SMSResult(BaseModel):
    student_id: int
    student_name: str
    parent_mobile: str
    status: str  # sent, failed
    message_id: Optional[str] = None

class SMSResponse(BaseModel):
    success: bool
    message: str
    sent_count: int
    failed_count: int
    results: List[SMSResult]

class SMSTemplateCreate(BaseModel):
    name: str
    template: str
    is_active: bool = True

class SMSTemplateUpdate(BaseModel):
    name: Optional[str] = None
    template: Optional[str] = None
    is_active: Optional[bool] = None

class SMSTemplateResponse(BaseModel):
    id: int
    name: str
    template: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None