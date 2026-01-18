# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import io
import re
import traceback
from typing import Dict, List

from .. import models, auth
from ..database import get_db
from ..schemas import UserResponse, CourseCreate, CourseUpdate, StudentCreate, StudentUpdate, TeacherUpdate
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import require_admin
import os

router = APIRouter(prefix="/admin", tags=["admin"])

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "..", "templates")
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)


# ============ USER MANAGEMENT ============
@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(models.User).all()
    return users

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted successfully"}

# ============ COURSE MANAGEMENT ============
@router.get("/courses")
def get_all_courses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get all courses with optional search and pagination"""
    query = db.query(models.Course)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Course.code.ilike(search_term)) |
            (models.Course.title.ilike(search_term)) |
            (models.Course.course_type.ilike(search_term))
        )
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "count": len(courses),
        "courses": courses
    }

@router.get("/courses/{course_code}")
def get_course_by_code(
    course_code: str,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific course by code"""
    course = db.query(models.Course).filter(models.Course.code == course_code).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {
        "success": True,
        "course": course
    }

@router.post("/courses")
def create_course(
    course_data: CourseCreate,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    # Check if course already exists
    existing_course = db.query(models.Course).filter(
        models.Course.code == course_data.code
    ).first()
    
    if existing_course:
        raise HTTPException(status_code=400, detail="Course with this code already exists")
    
    # Create new course
    new_course = models.Course(**course_data.dict())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return {
        "success": True,
        "message": "Course created successfully",
        "course": new_course
    }

@router.put("/courses/{course_code}")
def update_course(
    course_code: str,
    course_data: CourseUpdate,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Update an existing course"""
    course = db.query(models.Course).filter(models.Course.code == course_code).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Update fields
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    
    return {
        "success": True,
        "message": "Course updated successfully",
        "course": course
    }

@router.delete("/courses/{course_code}")
def delete_course(
    course_code: str,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete a course"""
    course = db.query(models.Course).filter(models.Course.code == course_code).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if course has any attendance records
    
    
    # Check if course is assigned to any teachers
 
    # Check if course has student enrollments
   
    db.delete(course)
    db.commit()
    
    return {
        "success": True,
        "message": f"Course '{course.code} - {course.title}' deleted successfully"
    }

# ============ STUDENT MANAGEMENT ============
@router.get("/students")
def get_all_students(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    year: Optional[int] = None,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get all students with optional search, filtering and pagination"""
    query = db.query(models.Student)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Student.student_id.ilike(search_term)) |
            (models.Student.name.ilike(search_term)) |
            (models.Student.theory_section.ilike(search_term)) |
            (models.Student.practical_batch.ilike(search_term))
        )
    
    if year:
        query = query.filter(models.Student.year == year)
    
    total = query.count()
    students = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "count": len(students),
        "students": students
    }

@router.get("/students/{student_id}")
def get_student_by_id(
    student_id: str,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific student by ID"""
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's enrolled courses
    
    # Get student's attendance summary
   
    return {
        "success": True,
        "student": student,


    }

@router.post("/students")
def create_student(
    student_data: StudentCreate,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Create a new student"""
    # Check if student already exists
    existing_student = db.query(models.Student).filter(
        models.Student.student_id == student_data.student_id
    ).first()
    
    if existing_student:
        raise HTTPException(status_code=400, detail="Student with this ID already exists")
    
    # Create new student
    new_student = models.Student(**student_data.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return {
        "success": True,
        "message": "Student created successfully",
        "student": new_student
    }

@router.put("/students/{student_id}")
def update_student(
    student_id: str,
    student_data: StudentUpdate,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Update an existing student"""
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update fields
    update_data = student_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    
    return {
        "success": True,
        "message": "Student updated successfully",
        "student": student
    }

@router.delete("/students/{student_id}")
def delete_student(
    student_id: str,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete a student"""
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if student has any attendance records
   
    
    
    
   
    
    db.delete(student)
    db.commit()
    
    return {
        "success": True,
        "message": f"Student '{student.name} ({student.student_id})' deleted successfully"
    }

# ============ TEACHER MANAGEMENT ============
@router.post("/teachers")
def create_teacher(
    teacher_data: dict,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new teacher with user and profile information.
    """
    try:
        # Validate required fields
        required_fields = ['teacher_id', 'name', 'email']
        for field in required_fields:
            if field not in teacher_data or not teacher_data[field]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field}' is required"
                )
        
        # Check if email already exists
        existing_email = db.query(models.User).filter(
            models.User.email == teacher_data['email']
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail=f"User with email {teacher_data['email']} already exists"
            )
        
        # Check if teacher_id already exists
        existing_teacher_id = db.query(models.User).filter(
            models.User.teacher_id == teacher_data['teacher_id']
        ).first()
        if existing_teacher_id:
            raise HTTPException(
                status_code=400,
                detail=f"Teacher with ID {teacher_data['teacher_id']} already exists"
            )
        
        # Create user record
        user_data = {
            'email': teacher_data['email'],
            'name': teacher_data['name'],
            'teacher_id': teacher_data['teacher_id'],
            'role': 'teacher',
            'mobile': teacher_data.get('mobile'),
            'is_active': teacher_data.get('is_active', True)
        }
        
        new_user = models.User(**user_data)
        
        # Set password if provided, otherwise generate default
        password = teacher_data.get('password') or f"Teacher@{teacher_data['teacher_id']}"
        new_user.set_password(password)
        
        db.add(new_user)
        db.flush()  # Get the user ID
        
        # Create teacher profile
        profile_data = {
            'user_id': new_user.id,
            'employee_id': teacher_data.get('employee_id'),
            'designation': teacher_data.get('designation', 'Assistant Professor'),
            'department': teacher_data.get('department', 'General'),
            'qualification': teacher_data.get('qualification'),
            'experience': teacher_data.get('experience'),
            'is_hod': teacher_data.get('is_hod', False)
        }
        
        new_profile = models.TeacherProfile(**profile_data)
        db.add(new_profile)
        
        db.commit()
        db.refresh(new_user)
        
        # Get the created profile
        created_profile = db.query(models.TeacherProfile).filter(
            models.TeacherProfile.user_id == new_user.id
        ).first()
        
        return {
            "success": True,
            "message": "Teacher created successfully",
            "teacher": {
                "id": new_user.id,
                "teacher_id": new_user.teacher_id,
                "name": new_user.name,
                "email": new_user.email,
                "mobile": new_user.mobile,
                "is_active": new_user.is_active,
                "department": created_profile.department if created_profile else None,
                "designation": created_profile.designation if created_profile else None,
                "employee_id": created_profile.employee_id if created_profile else None,
                "qualification": created_profile.qualification if created_profile else None,
                "experience": created_profile.experience if created_profile else None,
                "is_hod": created_profile.is_hod if created_profile else False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating teacher: {str(e)}")
    

@router.get("/teachers/{teacher_id}")
def get_teacher_details(
    teacher_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a teacher"""
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get teacher profile
    profile = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.user_id == teacher.id
    ).first()
    
    # Get assigned courses
    assigned_courses = db.query(models.Course).join(
        models.TeacherCourse
    ).filter(
        models.TeacherCourse.teacher_id == teacher.id
    ).all()
    
    # Get attendance marked by this teacher
    attendance_count = db.query(models.Attendance).filter(
        models.Attendance.teacher_id == teacher.id
    ).count()
    
    return {
        "success": True,
        "teacher": {
            "id": teacher.id,
            "name": teacher.name,
            "email": teacher.email,
            "teacher_id": teacher.teacher_id,
            "role": teacher.role,
            "mobile": teacher.mobile,
            "is_active": teacher.is_active,
            "department": profile.department if profile else "General",
            "designation": profile.designation if profile else "Assistant Professor",
            "employee_id": profile.employee_id if profile else None,
            "qualification": profile.qualification if profile else None,
            "experience": profile.experience if profile else None
        },
        "assigned_courses": assigned_courses,
        "attendance_count": attendance_count
    }

@router.put("/teachers/{teacher_id}")
def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Update teacher information"""
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Update user fields
    update_data = teacher_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field in ['department', 'designation', 'employee_id', 'qualification', 'experience']:
            # These are profile fields
            profile = db.query(models.TeacherProfile).filter(
                models.TeacherProfile.user_id == teacher.id
            ).first()
            
            if not profile:
                # Create profile if it doesn't exist
                profile = models.TeacherProfile(user_id=teacher.id)
                db.add(profile)
                db.flush()
            
            setattr(profile, field, value)
        elif hasattr(teacher, field):
            # These are user fields
            setattr(teacher, field, value)
    
    db.commit()
    db.refresh(teacher)
    
    return {
        "success": True,
        "message": "Teacher updated successfully",
        "teacher": teacher
    }

@router.delete("/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete a teacher"""
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Check if teacher has any assigned courses
    assignment_count = db.query(models.TeacherCourse).filter(
        models.TeacherCourse.teacher_id == teacher_id
    ).count()
    
    if assignment_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete teacher with {assignment_count} course assignments. Remove course assignments first."
        )
    
    # Check if teacher has marked any attendance
    attendance_count = db.query(models.Attendance).filter(
        models.Attendance.teacher_id == teacher_id
    ).count()
    
    if attendance_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete teacher with {attendance_count} attendance records. Delete attendance records first."
        )
    
    # Delete teacher profile if exists
    profile = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.user_id == teacher_id
    ).first()
    if profile:
        db.delete(profile)
    
    # Delete the teacher/user
    db.delete(teacher)
    db.commit()
    
    return {
        "success": True,
        "message": f"Teacher '{teacher.name}' deleted successfully"
    }

# ============ EXCEL UPLOAD SERVICES ============

import re

def parse_course_line(line):
    """
    Parse a course line in the format:
    "1. IFP 101 Induction cum Foundation Programme 2 (0+2) (Non-gradial)"
    
    Returns: Dictionary with course information
    """
    try:
        # Remove numbering at the beginning (e.g., "1. ", "2. ", etc.)
        line = re.sub(r'^\d+\.\s*', '', line)
        
        # Extract course code (e.g., "IFP 101")
        # Course code is usually at the beginning: letters, space, numbers
        code_match = re.match(r'^([A-Z]+)\s*(\d+[A-Z]*)', line)
        if not code_match:
            # Try alternative pattern
            code_match = re.match(r'^([A-Z]+\s*\d+[A-Z]*)', line)
        
        if code_match:
            code = code_match.group(0).strip()
            # Remove the code from the line to get title
            remaining = line[len(code):].strip()
        else:
            # If no code pattern found, use first word as code
            parts = line.split()
            if parts:
                code = parts[0]
                remaining = ' '.join(parts[1:])
            else:
                code = "UNKNOWN"
                remaining = ""
        
        # Extract title (everything before the credits)
        # Look for credit pattern like "2 (0+2)"
        credit_match = re.search(r'(\d+)\s*\(\s*(\d+)\s*\+\s*(\d+)\s*\)', remaining)
        
        title = remaining
        theory_credits = 0
        practical_credits = 0
        total_credits = 0
        course_type = "Regular"
        
        if credit_match:
            # Extract title (everything before the credit pattern)
            credit_pos = remaining.find(credit_match.group(0))
            title = remaining[:credit_pos].strip()
            
            total_credits = int(credit_match.group(1))
            theory_credits = int(credit_match.group(2))
            practical_credits = int(credit_match.group(3))
            
            # Remove title from remaining to check for course type
            remaining_after_credits = remaining[credit_pos + len(credit_match.group(0)):].strip()
            
            # Check for course type in parentheses
            type_match = re.search(r'\((.*?)\)', remaining_after_credits)
            if type_match:
                course_type = type_match.group(1)
        
        # Determine has_theory and has_practical
        has_theory = theory_credits > 0
        has_practical = practical_credits > 0
        
        # Default year and semester (you might want to adjust these)
        year = 1
        semester = 1
        
        # Clean up title
        title = title.strip()
        
        # Remove extra parentheses from title if any
        if title.endswith(')'):
            title_parts = title.rsplit('(', 1)
            if len(title_parts) > 1:
                title = title_parts[0].strip()
        
        return {
            'code': code,
            'title': title,
            'year': year,
            'semester': semester,
            'credits': str(total_credits),
            'theory_credits': theory_credits,
            'practical_credits': practical_credits,
            'has_theory': has_theory,
            'has_practical': has_practical,
            'course_type': course_type,
            'raw_line': line
        }
    
    except Exception as e:
        print(f"Error parsing line: {line}")
        print(f"Error: {e}")
        return None


@router.post("/upload/courses")
async def upload_courses_from_excel(
    file: UploadFile = File(...),
    year: int = Query(1, description="Academic year for these courses"),
    semester: int = Query(1, description="Semester for these courses"),
    db: Session = Depends(get_db)
):
    """
    Upload courses from Excel file with single column format.
    Excel file should have course information in a single column like:
    "1. IFP 101 Induction cum Foundation Programme 2 (0+2) (Non-gradial)"
    """
    try:
        print(f"Processing file: {file.filename}")
        print(f"Year: {year}, Semester: {semester}")
        
        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        # Read Excel file
        contents = await file.read()
        print(f"File size: {len(contents)} bytes")
        
        try:
            # Read Excel file - try without header first
            df = pd.read_excel(io.BytesIO(contents), header=None)
            print(f"Excel file loaded successfully. Shape: {df.shape}")
            
            # Display file structure
            print("\n=== FILE STRUCTURE ===")
            for i in range(min(20, len(df))):
                for j in range(df.shape[1]):
                    cell_value = df.iloc[i, j]
                    if pd.notna(cell_value):
                        print(f"Row {i}, Col {j}: {cell_value}")
            
            # Find the column with course data
            course_column_index = None
            for j in range(df.shape[1]):
                column_has_data = False
                for i in range(min(20, len(df))):
                    cell_value = df.iloc[i, j]
                    if pd.notna(cell_value) and isinstance(cell_value, str):
                        if re.search(r'\d+\.\s*[A-Z]+\s*\d+', cell_value):
                            course_column_index = j
                            column_has_data = True
                            break
                if column_has_data:
                    break
            
            if course_column_index is None:
                # Try to find any column with data
                for j in range(df.shape[1]):
                    for i in range(min(20, len(df))):
                        cell_value = df.iloc[i, j]
                        if pd.notna(cell_value):
                            course_column_index = j
                            break
                    if course_column_index is not None:
                        break
            
            if course_column_index is None:
                raise HTTPException(status_code=400, detail="No course data found in the Excel file")
            
            print(f"\nUsing column {course_column_index} for course data")
            
            # Extract course lines
            course_lines = []
            for i in range(len(df)):
                cell_value = df.iloc[i, course_column_index]
                if pd.notna(cell_value):
                    course_lines.append(str(cell_value).strip())
            
            print(f"\nFound {len(course_lines)} course lines")
            
            # Process each course line
            results = {
                "successful": 0,
                "failed": 0,
                "errors": [],
                "processed": []
            }
            
            for i, line in enumerate(course_lines):
                row_num = i + 1
                try:
                    print(f"\nProcessing line {row_num}: {line}")
                    
                    # Parse the course line
                    course_info = parse_course_line(line)
                    
                    if not course_info:
                        raise ValueError(f"Could not parse course information from line")
                    
                    print(f"  Parsed: {course_info}")
                    
                    # Override year and semester from query parameters
                    course_info['year'] = year
                    course_info['semester'] = semester
                    
                    # Prepare course data for database
                    course_data = {
                        'code': course_info['code'],
                        'title': course_info['title'],
                        'year': course_info['year'],
                        'semester': course_info['semester'],
                        'credits': course_info['credits'],
                        'has_theory': course_info['has_theory'],
                        'has_practical': course_info['has_practical']
                    }
                    
                    # Check if course already exists
                    existing_course = db.query(models.Course).filter(
                        models.Course.code == course_data['code']
                    ).first()
                    
                    if existing_course:
                        print(f"  Course {course_data['code']} already exists, updating...")
                        # Update existing course
                        for field, value in course_data.items():
                            setattr(existing_course, field, value)
                        db.commit()
                        results["successful"] += 1
                        results["processed"].append({
                            "row": row_num,
                            "code": course_data['code'],
                            "action": "updated",
                            "title": course_data.get('title', 'N/A'),
                            "credits": course_data.get('credits', 'N/A')
                        })
                    else:
                        print(f"  Course {course_data['code']} is new, creating...")
                        # Create new course
                        new_course = models.Course(**course_data)
                        db.add(new_course)
                        db.commit()
                        results["successful"] += 1
                        results["processed"].append({
                            "row": row_num,
                            "code": course_data['code'],
                            "action": "created",
                            "title": course_data.get('title', 'N/A'),
                            "credits": course_data.get('credits', 'N/A')
                        })
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ERROR processing line {row_num}: {error_msg}")
                    results["failed"] += 1
                    results["errors"].append({
                        "row": row_num,
                        "line": line,
                        "error": error_msg
                    })
                    db.rollback()
                    continue
            
            print(f"\nProcessing complete: {results['successful']} successful, {results['failed']} failed")
            
            # Return summary of processed courses
            summary = []
            for course in results["processed"]:
                summary.append(f"{course['code']} - {course['title']} ({course['credits']} credits)")
            
            return {
                "success": True,
                "message": f"Processed {len(course_lines)} courses: {results['successful']} successful, {results['failed']} failed",
                "results": results,
                "summary": summary[:10]  # First 10 courses as summary
            }
            
        except Exception as e:
            print(f"Error reading/processing Excel file: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"Error processing Excel file: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(f"CRITICAL ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


# Also add a test endpoint to parse a single line
@router.post("/upload/courses/test-parse")
async def test_parse_course_line(
    line: str = Query(..., description="Course line to parse")
):
    """
    Test parsing a single course line
    """
    result = parse_course_line(line)
    return {
        "success": True,
        "original_line": line,
        "parsed_result": result
    }

@router.post("/upload/teachers")
async def upload_teachers_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload teachers from Excel file.
    Expected Excel columns:
    - teacher_id (required, unique)
    - name (required)
    - email (required, unique)
    - password (optional, default will be generated)
    - mobile (optional)
    - department (optional)
    - designation (optional)
    - employee_id (optional)
    - qualification (optional)
    - experience (optional)
    """
    try:
        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['teacher_id', 'name', 'email']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Required column '{col}' not found in Excel file"
                )
        
        # Process each row
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for index, row in df.iterrows():
            try:
                # Prepare teacher data
                teacher_data = {}
                
                # Map Excel columns to database fields
                column_mapping = {
                    'teacher_id': 'teacher_id',
                    'name': 'name',
                    'email': 'email',
                    'mobile': 'mobile',
                    'department': 'department',
                    'designation': 'designation',
                    'employee_id': 'employee_id',
                    'qualification': 'qualification',
                    'experience': 'experience'
                }
                
                for excel_col, db_field in column_mapping.items():
                    if excel_col in df.columns and pd.notna(row[excel_col]):
                        teacher_data[db_field] = row[excel_col]
                
                # Validate required fields
                for field in ['teacher_id', 'name', 'email']:
                    if field not in teacher_data or not str(teacher_data[field]).strip():
                        raise ValueError(f"{field} is required")
                
                # Check if teacher already exists by email
                existing_user = db.query(models.User).filter(
                    models.User.email == teacher_data['email']
                ).first()
                
                if existing_user:
                    # Update existing teacher
                    existing_user.role = "teacher"
                    for field, value in teacher_data.items():
                        if hasattr(existing_user, field):
                            setattr(existing_user, field, value)
                    
                    # Update or create teacher profile
                    profile = db.query(models.TeacherProfile).filter(
                        models.TeacherProfile.user_id == existing_user.id
                    ).first()
                    
                    if not profile:
                        profile = models.TeacherProfile(user_id=existing_user.id)
                        db.add(profile)
                    
                    # Update profile fields
                    profile_fields = ['department', 'designation', 'employee_id', 
                                     'qualification', 'experience']
                    for field in profile_fields:
                        if field in teacher_data:
                            setattr(profile, field, teacher_data[field])
                    
                    db.commit()
                    results["successful"] += 1
                else:
                    # Create new teacher user
                    # Generate default password if not provided
                    password = teacher_data.get('password') or "DefaultPassword123"
                    
                    new_user = models.User(
                        email=teacher_data['email'],
                        name=teacher_data['name'],
                        role="teacher",
                        teacher_id=teacher_data.get('teacher_id'),
                        mobile=teacher_data.get('mobile'),
                        is_active=True
                    )
                    new_user.set_password(password)
                    
                    db.add(new_user)
                    db.flush()  # Flush to get the user ID
                    
                    # Create teacher profile
                    profile_data = {}
                    profile_fields = ['department', 'designation', 'employee_id', 
                                     'qualification', 'experience']
                    for field in profile_fields:
                        if field in teacher_data:
                            profile_data[field] = teacher_data[field]
                    
                    if profile_data:
                        profile = models.TeacherProfile(
                            user_id=new_user.id,
                            **profile_data
                        )
                        db.add(profile)
                    
                    db.commit()
                    results["successful"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": index + 2,
                    "teacher_id": row.get('teacher_id', 'N/A'),
                    "error": str(e)
                })
                db.rollback()
                continue
        
        return {
            "success": True,
            "message": f"Processed {len(df)} teachers",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

@router.post("/upload/students")
async def upload_students_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload students from Excel file.
    Based on your Excel structure:
    - ID Number (student_id)
    - Name (name)
    - Year (year)
    - Theory (theory_section)
    - Practical (practical_batch)
    - Student mobile number (mobile)
    """
    try:
        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        # Read Excel file
        contents = await file.read()
        
        # Debug: Check file size
        file_size = len(contents)
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Read Excel file
        try:
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(
                    io.BytesIO(contents),
                    sheet_name=0,  # First sheet
                    engine='openpyxl'
                )
            else:
                df = pd.read_excel(
                    io.BytesIO(contents),
                    sheet_name=0  # First sheet
                )
        except Exception as read_error:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot read Excel file: {str(read_error)}"
            )
        
        # Clean column names - remove leading/trailing whitespace
        df.columns = df.columns.str.strip()
        
        # Debug: Show what columns were read
        print(f"Cleaned columns: {df.columns.tolist()}")
        print(f"DataFrame shape: {df.shape}")
        
        # Check if DataFrame is empty
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")
        
        # Define column mapping based on your Excel structure
        # Map Excel column names to database field names
        column_mapping = {
            # Excel column name: database field name
            'ID Number': 'student_id',
            'Name': 'name',
            'Year': 'year',
            'Theory': 'theory_section',
            'Practical': 'practical_batch',
            'Student mobile number': 'mobile',
            'Parent mobile number': 'parent_mobile',
            'S. NO.': 'serial_number'  # Optional, if you want to store it
        }
        
        # Check which columns we actually have in the Excel file
        available_columns = df.columns.tolist()
        print(f"Available columns after cleaning: {available_columns}")
        
        # Rename columns that exist in our mapping
        rename_dict = {}
        for excel_col, db_field in column_mapping.items():
            if excel_col in available_columns:
                rename_dict[excel_col] = db_field
            else:
                # Try case-insensitive match
                for actual_col in available_columns:
                    if actual_col.lower() == excel_col.lower():
                        rename_dict[actual_col] = db_field
                        break
        
        print(f"Renaming columns: {rename_dict}")
        
        # Rename the columns
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        # Check for required columns
        required_columns = ['student_id', 'name', 'year']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # Provide helpful error message
            raise HTTPException(
                status_code=400, 
                detail=f"Required columns not found. Available columns: {df.columns.tolist()}. Missing: {missing_columns}. Please ensure your Excel has columns: ID Number, Name, Year"
            )
        
        # Process each row
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for index, row in df.iterrows():
            try:
                # Prepare student data
                student_data = {}
                
                # Map all available columns to database fields
                db_fields_mapping = {
                    'student_id': 'student_id',
                    'name': 'name',
                    'year': 'year',
                    'theory_section': 'theory_section',
                    'practical_batch': 'practical_batch',
                    'mobile': 'mobile',
                    'parent_mobile': 'parent_mobile',
                    'email': 'email',  # Not in your Excel, but kept for compatibility
                    'serial_number': 'serial_number'  # Optional
                }
                
                for db_field in db_fields_mapping.values():
                    if db_field in df.columns and pd.notna(row[db_field]):
                        student_data[db_field] = row[db_field]
                
                # Validate required fields
                for field in ['student_id', 'name', 'year']:
                    if field not in student_data:
                        raise ValueError(f"{field} is missing")
                    
                    field_value = str(student_data[field]).strip()
                    if not field_value:
                        raise ValueError(f"{field} is empty")
                    
                    student_data[field] = field_value
                
                # Convert year to integer if possible
                if 'year' in student_data:
                    try:
                        student_data['year'] = int(float(student_data['year']))
                    except (ValueError, TypeError):
                        raise ValueError(f"Year must be a number, got: {student_data['year']}")
                
                # Check if student already exists
                existing_student = db.query(models.Student).filter(
                    models.Student.student_id == student_data['student_id']
                ).first()
                
                if existing_student:
                    # Update existing student
                    for field, value in student_data.items():
                        if field != 'student_id':  # Don't update the ID
                            setattr(existing_student, field, value)
                    db.commit()
                    db.refresh(existing_student)
                    results["successful"] += 1
                else:
                    # Create new student
                    new_student = models.Student(**student_data)
                    db.add(new_student)
                    db.commit()
                    db.refresh(new_student)
                    results["successful"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": index + 2,  # +2 because Excel rows are 1-indexed and header is row 1
                    "student_id": str(row.get('student_id', 'N/A')),
                    "name": str(row.get('name', 'N/A')),
                    "error": str(e)
                })
                db.rollback()
                continue
        
        return {
            "success": True,
            "message": f"Processed {len(df)} students from Sheet1. Successful: {results['successful']}, Failed: {results['failed']}",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Full error traceback: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing Excel file: {str(e)}"
        )
#======STATS================================
@router.get("/stats")
def get_system_stats(
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics - simplified version"""
    try:
        # Get counts
        total_users = db.query(models.User).count()
        total_teachers = db.query(models.User).filter(models.User.role == "teacher").count()
        total_courses = db.query(models.Course).count()
        total_students = db.query(models.Student).count()
        total_attendance = db.query(models.Attendance).count()
        
        # Get recent data without ordering
        recent_courses = db.query(models.Course).limit(5).all()
        recent_students = db.query(models.Student).limit(5).all()
        
        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_teachers": total_teachers,
                "total_courses": total_courses,
                "total_students": total_students,
                "total_attendance_records": total_attendance
            },
            "recent": {
                "courses": recent_courses,
                "students": recent_students
            },
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in get_system_stats: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "stats": {
                "total_users": 0,
                "total_teachers": 0,
                "total_courses": 0,
                "total_students": 0,
                "total_attendance_records": 0
            },
            "recent": {
                "courses": [],
                "students": []
            },
            "last_updated": datetime.now().isoformat()
        }

# ============ BULK OPERATIONS ============
@router.delete("/courses/bulk")
def bulk_delete_courses(
    course_codes: List[str] = Query(...),
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Bulk delete courses"""
    if not course_codes:
        raise HTTPException(status_code=400, detail="No course codes provided")
    
    success_count = 0
    failed_courses = []
    
    for course_code in course_codes:
        try:
            course = db.query(models.Course).filter(models.Course.code == course_code).first()
            if not course:
                failed_courses.append({"course": course_code, "reason": "Not found"})
                continue
            
            # Check for dependencies
            attendance_count = db.query(models.Attendance).filter(
                models.Attendance.course_id == course.id
            ).count()
            
            if attendance_count > 0:
                failed_courses.append({
                    "course": course_code, 
                    "reason": f"Has {attendance_count} attendance records"
                })
                continue
            
            assignment_count = db.query(models.TeacherCourse).filter(
                models.TeacherCourse.course_id == course.id
            ).count()
            
            if assignment_count > 0:
                failed_courses.append({
                    "course": course_code,
                    "reason": f"Assigned to {assignment_count} teachers"
                })
                continue
            
            db.delete(course)
            success_count += 1
            
        except Exception as e:
            failed_courses.append({"course": course_code, "reason": str(e)})
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Deleted {success_count} courses successfully",
        "results": {
            "successful": success_count,
            "failed": len(failed_courses),
            "failed_details": failed_courses
        }
    }

@router.delete("/students/bulk")
def bulk_delete_students(
    student_ids: List[str] = Query(...),
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Bulk delete students"""
    if not student_ids:
        raise HTTPException(status_code=400, detail="No student IDs provided")
    
    success_count = 0
    failed_students = []
    
    for student_id in student_ids:
        try:
            student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
            if not student:
                failed_students.append({"student": student_id, "reason": "Not found"})
                continue
            
            # Check for dependencies
            attendance_count = db.query(models.Attendance).filter(
                models.Attendance.student_id == student_id
            ).count()
            
            if attendance_count > 0:
                failed_students.append({
                    "student": student_id,
                    "reason": f"Has {attendance_count} attendance records"
                })
                continue
            
            db.delete(student)
            success_count += 1
            
        except Exception as e:
            failed_students.append({"student": student_id, "reason": str(e)})
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Deleted {success_count} students successfully",
        "results": {
            "successful": success_count,
            "failed": len(failed_students),
            "failed_details": failed_students
        }
    }
# ============ TEACHER MANAGEMENT ENDPOINTS ============
@router.get("/all/teachers/")
def get_all_teachers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    GET: Get all teachers with filtering and pagination
    """
    try:
        # Base query for teachers
        query = db.query(models.User).filter(
            models.User.role == "teacher"
        )
        
        # Apply search filter
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (models.User.name.ilike(search_term)) |
                (models.User.email.ilike(search_term)) |
                (models.User.teacher_id.ilike(search_term)) |
                (models.User.mobile.ilike(search_term))
            )
        
        # Apply department filter (join with profile)
        if department and department.strip() and department.lower() != "all":
            query = query.join(
                models.TeacherProfile,
                models.User.id == models.TeacherProfile.user_id
            ).filter(
                models.TeacherProfile.department == department.strip()
            )
        else:
            query = query.outerjoin(
                models.TeacherProfile,
                models.User.id == models.TeacherProfile.user_id
            )
        
        # Apply status filter
        if status and status.strip() and status.lower() != "all":
            is_active = status.strip().lower() == "active"
            query = query.filter(models.User.is_active == is_active)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        teachers = query.offset(skip).limit(limit).all()
        
        # Format response
        teacher_list = []
        for teacher in teachers:
            # Get teacher profile
            profile = db.query(models.TeacherProfile).filter(
                models.TeacherProfile.user_id == teacher.id
            ).first()
            
            # Get assigned courses count
            course_count = db.query(models.TeacherCourse).filter(
                models.TeacherCourse.teacher_id == teacher.id
            ).count()
            
            teacher_data = {
                "id": teacher.id,
                "teacher_id": teacher.teacher_id or "",
                "name": teacher.name or "",
                "email": teacher.email or "",
                "mobile": teacher.mobile or "",
                "is_active": teacher.is_active if teacher.is_active is not None else True,
                "department": profile.department if profile else "General",
                "designation": profile.designation if profile else "Assistant Professor",
                "employee_id": profile.employee_id if profile else None,
                "qualification": profile.qualification if profile else None,
                "experience": profile.experience if profile else None,
                "is_hod": profile.is_hod if profile else False,
                "assigned_courses": course_count
            }
            teacher_list.append(teacher_data)
        
        return {
            "success": True,
            "total": total_count,
            "count": len(teacher_list),
            "teachers": teacher_list,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "has_more": (skip + len(teacher_list)) < total_count
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "teachers": [],
            "total": 0,
            "count": 0
        }


@router.post("/teachers")
def create_teacher(
    teacher_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new teacher with user and profile information.
    Uses hashed_password column (store plain text for now)
    """
    try:
        # Validate required fields
        required_fields = ['teacher_id', 'name', 'email']
        for field in required_fields:
            if field not in teacher_data or not teacher_data[field]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field}' is required"
                )
        
        # Check if email already exists
        existing_email = db.query(models.User).filter(
            models.User.email == teacher_data['email']
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail=f"User with email {teacher_data['email']} already exists"
            )
        
        # Check if teacher_id already exists
        existing_teacher_id = db.query(models.User).filter(
            models.User.teacher_id == teacher_data['teacher_id']
        ).first()
        if existing_teacher_id:
            raise HTTPException(
                status_code=400,
                detail=f"Teacher with ID {teacher_data['teacher_id']} already exists"
            )
        
        # Get password or generate default
        password = teacher_data.get('password')
        if not password:
            password = f"Teacher@{teacher_data['teacher_id']}"
        
        # Create user - store plain password in hashed_password column
        new_user = models.User(
            email=teacher_data['email'].strip(),
            name=teacher_data['name'].strip(),
            teacher_id=teacher_data['teacher_id'].strip(),
            role='teacher',
            mobile=teacher_data.get('mobile', '').strip() if teacher_data.get('mobile') else None,
            is_active=teacher_data.get('is_active', True),
            hashed_password=password  # Store plain text in hashed_password column
        )
        
        db.add(new_user)
        db.flush()  # Get the user ID
        
        # Create teacher profile
        profile_data = {
            'user_id': new_user.id,
            'employee_id': teacher_data.get('employee_id', '').strip() if teacher_data.get('employee_id') else None,
            'designation': teacher_data.get('designation', 'Assistant Professor').strip(),
            'department': teacher_data.get('department', 'General').strip(),
            'qualification': teacher_data.get('qualification', '').strip() if teacher_data.get('qualification') else None,
            'experience': teacher_data.get('experience', '').strip() if teacher_data.get('experience') else None,
            'is_hod': teacher_data.get('is_hod', False)
        }
        
        new_profile = models.TeacherProfile(**profile_data)
        db.add(new_profile)
        
        db.commit()
        db.refresh(new_user)
        
        # Get the created profile
        created_profile = db.query(models.TeacherProfile).filter(
            models.TeacherProfile.user_id == new_user.id
        ).first()
        
        return {
            "success": True,
            "message": "Teacher created successfully",
            "teacher": {
                "id": new_user.id,
                "teacher_id": new_user.teacher_id,
                "name": new_user.name,
                "email": new_user.email,
                "mobile": new_user.mobile,
                "is_active": new_user.is_active,
                "department": created_profile.department if created_profile else None,
                "designation": created_profile.designation if created_profile else None,
                "employee_id": created_profile.employee_id if created_profile else None,
                "qualification": created_profile.qualification if created_profile else None,
                "experience": created_profile.experience if created_profile else None,
                "is_hod": created_profile.is_hod if created_profile else False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating teacher: {str(e)}")
@router.put("/teachers/{teacher_id}")
def update_teacher(
    teacher_id: int,
    teacher_data: dict,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Update teacher information including profile
    """
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    try:
        with db.begin():
            # Update user fields
            user_fields = ['name', 'email', 'teacher_id', 'mobile', 'is_active']
            for field in user_fields:
                if field in teacher_data:
                    # Check for duplicate teacher_id
                    if field == 'teacher_id' and teacher_data[field] != teacher.teacher_id:
                        existing = db.query(models.User).filter(
                            models.User.teacher_id == teacher_data[field]
                        ).first()
                        if existing and existing.id != teacher_id:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Teacher ID {teacher_data[field]} already exists"
                            )
                    
                    # Check for duplicate email
                    if field == 'email' and teacher_data[field] != teacher.email:
                        existing = db.query(models.User).filter(
                            models.User.email == teacher_data[field]
                        ).first()
                        if existing and existing.id != teacher_id:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Email {teacher_data[field]} already exists"
                            )
                    
                    setattr(teacher, field, teacher_data[field])
            
            # Update password if provided
            if 'password' in teacher_data and teacher_data['password']:
                teacher.set_password(teacher_data['password'])
            
            # Update or create profile
            profile = db.query(models.TeacherProfile).filter(
                models.TeacherProfile.user_id == teacher_id
            ).first()
            
            profile_fields = ['department', 'designation', 'employee_id', 
                             'qualification', 'experience', 'is_hod']
            
            if not profile:
                # Create new profile
                profile_data = {}
                for field in profile_fields:
                    if field in teacher_data:
                        profile_data[field] = teacher_data[field]
                
                if profile_data:
                    profile = models.TeacherProfile(
                        user_id=teacher_id,
                        **profile_data
                    )
                    db.add(profile)
            else:
                # Update existing profile
                for field in profile_fields:
                    if field in teacher_data:
                        setattr(profile, field, teacher_data[field])
        
        # Refresh data
        db.refresh(teacher)
        updated_profile = db.query(models.TeacherProfile).filter(
            models.TeacherProfile.user_id == teacher_id
        ).first()
        
        return {
            "success": True,
            "message": "Teacher updated successfully",
            "teacher": {
                "id": teacher.id,
                "teacher_id": teacher.teacher_id,
                "name": teacher.name,
                "email": teacher.email,
                "mobile": teacher.mobile,
                "is_active": teacher.is_active,
                "department": updated_profile.department if updated_profile else None,
                "designation": updated_profile.designation if updated_profile else None,
                "employee_id": updated_profile.employee_id if updated_profile else None,
                "qualification": updated_profile.qualification if updated_profile else None,
                "experience": updated_profile.experience if updated_profile else None,
                "is_hod": updated_profile.is_hod if updated_profile else False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating teacher: {str(e)}")

@router.delete("/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete a teacher"""
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    try:
        with db.begin():
            # Check if teacher has any assigned courses
            assignment_count = db.query(models.TeacherCourse).filter(
                models.TeacherCourse.teacher_id == teacher_id
            ).count()
            
            if assignment_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete teacher with {assignment_count} course assignments. Remove course assignments first."
                )
            
            # Delete teacher profile if exists
            profile = db.query(models.TeacherProfile).filter(
                models.TeacherProfile.user_id == teacher_id
            ).first()
            if profile:
                db.delete(profile)
            
            # Delete the teacher/user
            db.delete(teacher)
        
        return {
            "success": True,
            "message": f"Teacher '{teacher.name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting teacher: {str(e)}")

# ============ TEACHER COURSE MANAGEMENT ============

@router.get("/teachers/{teacher_id}/courses")
def get_teacher_courses(
    teacher_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get all courses assigned to a teacher"""
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get assigned courses with section and batch info
    # Note: TeacherCourse uses course_code, not course_id
    teacher_courses = db.query(
        models.TeacherCourse,
        models.Course
    ).outerjoin(
        models.Course,
        models.TeacherCourse.course_code == models.Course.code
    ).filter(
        models.TeacherCourse.teacher_id == teacher_id
    ).all()
    
    courses = []
    for teacher_course, course in teacher_courses:
        course_info = {
            "assignment_id": teacher_course.id,
            "course_code": teacher_course.course_code,
            "section": teacher_course.section,
            "batch": teacher_course.batch,
            "course_title": course.title if course else "Unknown Course",
            "course_details": {
                "credits": course.credits if course else None,
                "year": course.year if course else None,
                "semester": course.semester if course else None
            } if course else None
        }
        courses.append(course_info)
    
    return {
        "success": True,
        "teacher_id": teacher_id,
        "teacher_name": teacher.name,
        "teacher_email": teacher.email,
        "courses": courses,
        "count": len(courses)
    }

@router.post("/teachers/{teacher_id}/courses")
def assign_course_to_teacher(
    teacher_id: int,
    assignment_data: dict,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """
    Assign a course to a teacher
    Expected data:
    {
        "course_code": "CS101",  # Required
        "section": "A",          # Optional
        "batch": "1"             # Optional
    }
    """
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Validate required fields
    if 'course_code' not in assignment_data or not assignment_data['course_code']:
        raise HTTPException(status_code=400, detail="course_code is required")
    
    try:
        # Check if course exists
        course = db.query(models.Course).filter(
            models.Course.code == assignment_data['course_code']
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with code {assignment_data['course_code']} not found. Please create the course first."
            )
        
        # Check if already assigned
        existing_assignment = db.query(models.TeacherCourse).filter(
            models.TeacherCourse.teacher_id == teacher_id,
            models.TeacherCourse.course_code == assignment_data['course_code'],
            models.TeacherCourse.section == assignment_data.get('section'),
            models.TeacherCourse.batch == assignment_data.get('batch')
        ).first()
        
        if existing_assignment:
            raise HTTPException(
                status_code=400,
                detail="Course already assigned to this teacher with same section and batch"
            )
        
        # Create assignment
        new_assignment = models.TeacherCourse(
            teacher_id=teacher_id,
            course_code=assignment_data['course_code'],
            section=assignment_data.get('section'),
            batch=assignment_data.get('batch')
        )
        
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        
        return {
            "success": True,
            "message": f"Course {assignment_data['course_code']} assigned to {teacher.name}",
            "assignment": {
                "id": new_assignment.id,
                "teacher_id": teacher_id,
                "teacher_name": teacher.name,
                "course_code": assignment_data['course_code'],
                "course_title": course.title if course else "Unknown",
                "section": new_assignment.section,
                "batch": new_assignment.batch
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error assigning course: {str(e)}")
@router.delete("/teachers/{teacher_id}/courses/{assignment_id}")
def remove_course_from_teacher(
    teacher_id: int,
    assignment_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Remove a course assignment from a teacher"""
    assignment = db.query(models.TeacherCourse).filter(
        models.TeacherCourse.id == assignment_id,
        models.TeacherCourse.teacher_id == teacher_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Course assignment not found")
    
    course_code = assignment.course_code
    
    try:
        with db.begin():
            db.delete(assignment)
        
        return {
            "success": True,
            "message": f"Course {course_code} removed from teacher",
            "assignment_id": assignment_id,
            "course_code": course_code
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing course assignment: {str(e)}")

# ============ UPLOAD TEACHER-COURSE MAPPINGS ============

@router.post("/upload/teacher-courses")
async def upload_teacher_course_mappings(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload teacher-course mappings from Excel file.
    Expected Excel columns:
    - teacher_id (user_id from users table)
    - course_code (from courses table)
    - section (optional)
    - batch (optional)
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Check required columns
        required_columns = ['teacher_id', 'course_code']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Required column '{col}' not found"
                )
        
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for index, row in df.iterrows():
            try:
                teacher_id = int(row['teacher_id']) if pd.notna(row['teacher_id']) else None
                course_code = str(row['course_code']).strip() if pd.notna(row['course_code']) else None
                section = str(row.get('section', '')).strip() if pd.notna(row.get('section')) else None
                batch = str(row.get('batch', '')).strip() if pd.notna(row.get('batch')) else None
                
                # Validate
                if not teacher_id:
                    raise ValueError(f"Invalid teacher_id: {row['teacher_id']}")
                if not course_code:
                    raise ValueError(f"Invalid course_code: {row['course_code']}")
                
                # Get teacher
                teacher = db.query(models.User).filter(
                    models.User.id == teacher_id,
                    models.User.role == "teacher"
                ).first()
                
                if not teacher:
                    raise ValueError(f"Teacher with ID {teacher_id} not found")
                
                # Get course (optional validation)
                course = db.query(models.Course).filter(
                    models.Course.code == course_code
                ).first()
                
                if not course:
                    # You might want to warn but not fail
                    print(f"Warning: Course {course_code} not found in database")
                
                # Check if mapping already exists
                existing = db.query(models.TeacherCourse).filter(
                    models.TeacherCourse.teacher_id == teacher_id,
                    models.TeacherCourse.course_code == course_code,
                    models.TeacherCourse.section == section,
                    models.TeacherCourse.batch == batch
                ).first()
                
                if existing:
                    # Update existing
                    existing.section = section
                    existing.batch = batch
                    results["successful"] += 1
                else:
                    # Create new mapping
                    new_mapping = models.TeacherCourse(
                        teacher_id=teacher_id,
                        course_code=course_code,
                        section=section,
                        batch=batch
                    )
                    db.add(new_mapping)
                    results["successful"] += 1
                
                db.commit()
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": index + 2,
                    "teacher_id": str(row.get('teacher_id', 'N/A')),
                    "course_code": str(row.get('course_code', 'N/A')),
                    "error": str(e)
                })
                db.rollback()
                continue
        
        return {
            "success": True,
            "message": f"Processed {len(df)} mappings. Successful: {results['successful']}, Failed: {results['failed']}",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# ============ GET TEACHER BY ID ============

@router.get("/teachers/{teacher_id}")
def get_teacher_by_id(
    teacher_id: int,
    #current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed teacher information by ID"""
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get teacher profile
    profile = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.user_id == teacher_id
    ).first()
    
    # Get assigned courses count
    course_count = db.query(models.TeacherCourse).filter(
        models.TeacherCourse.teacher_id == teacher_id
    ).count()
    
    # Get actual assigned courses
    assigned_courses = db.query(models.TeacherCourse).filter(
        models.TeacherCourse.teacher_id == teacher_id
    ).all()
    
    # Get course details for assigned courses
    course_details = []
    for assignment in assigned_courses:
        course = db.query(models.Course).filter(
            models.Course.code == assignment.course_code
        ).first()
        course_details.append({
            "assignment_id": assignment.id,
            "course_code": assignment.course_code,
            "course_title": course.title if course else "Unknown",
            "section": assignment.section,
            "batch": assignment.batch
        })
    
    return {
        "success": True,
        "teacher": {
            "id": teacher.id,
            "teacher_id": teacher.teacher_id,
            "name": teacher.name,
            "email": teacher.email,
            "mobile": teacher.mobile,
            "is_active": teacher.is_active,
            "role": teacher.role,
            "department": profile.department if profile else "General",
            "designation": profile.designation if profile else "Assistant Professor",
            "employee_id": profile.employee_id if profile else None,
            "qualification": profile.qualification if profile else None,
            "experience": profile.experience if profile else None,
            "is_hod": profile.is_hod if profile else False,
            "assigned_courses_count": course_count,
            "assigned_courses": course_details
        }
    }