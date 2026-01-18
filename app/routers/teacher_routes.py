# app/routers/teacher_routes.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Optional
import pandas as pd
import io
import re
import random
import string
from datetime import datetime

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, require_admin
from ..utils import generate_password

router = APIRouter(prefix="/teachers", tags=["teachers"])

def generate_teacher_password():
    """Generate a random password for teachers"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(8))

def parse_teacher_name(full_name: str):
    """Parse teacher name from full string like 'Dr. C. Balavivin Sundar'"""
    # Remove titles and designations
    name = full_name.replace('Dr.', '').replace('Mr.', '').replace('Mrs.', '').replace('Ms.', '').strip()
    return name

def parse_department(description: str):
    """Parse department from description like 'Asst. Prof. Agricultural Extension'"""
    if 'Extension' in description:
        return 'Agricultural Extension'
    elif 'Microbiology' in description:
        return 'Microbiology'
    elif 'Economics' in description:
        return 'Agricultural Economics'
    elif 'Soil Science' in description:
        return 'Soil Science and Agricultural Chemistry'
    elif 'Horticulture' in description:
        return 'Horticulture'
    elif 'Plant Pathology' in description:
        return 'Plant Pathology'
    elif 'Agricultural Statistics' in description:
        return 'Agricultural Statistics'
    elif 'Physical Education' in description:
        return 'Physical Education'
    else:
        return 'General'


@router.get("/")
def get_all_teachers(
    db: Session = Depends(get_db)
):
    """Get all teachers - test endpoint"""
    teachers = db.query(models.User).filter(models.User.role == "teacher").all()
    
    # Return simple dict to test
    result = []
    for teacher in teachers:
        result.append({
            "id": teacher.id,
            "name": teacher.name,
            "email": teacher.email,
            "teacher_id": teacher.teacher_id,
            "role": teacher.role
        })
    
    return result

@router.get("/dropdown", response_model=List[dict])
def get_teachers_dropdown(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    course_code: Optional[str] = Query(None)
):
    """Get teachers for dropdown selection"""
    query = db.query(models.User).filter(
        models.User.role == "teacher",
        models.User.is_active == True
    ).order_by(models.User.name)
    
    teachers = query.all()
    
    result = []
    for teacher in teachers:
        result.append({
            "value": teacher.id,
            "label": f"{teacher.name} ({teacher.teacher_id or 'N/A'})",
            "name": teacher.name,
            "email": teacher.email,
            "teacher_id": teacher.teacher_id
        })
    
    return result

@router.post("/create", response_model=schemas.UserResponse)
def create_teacher(
    teacher_data: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    #current_user: models.User = Depends(require_admin)
):
    """Create a new teacher (Admin only)"""
    # Check if email already exists
    existing_user = db.query(models.User).filter(
        models.User.email == teacher_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(400, "Email already registered")
    
    # Check if employee_id already exists
    if teacher_data.employee_id:
        existing_employee = db.query(models.User).filter(
            models.User.teacher_id == teacher_data.employee_id
        ).first()
        if existing_employee:
            raise HTTPException(400, f"Employee ID {teacher_data.employee_id} already exists")
    
    # Generate password if not provided
    password = teacher_data.password or generate_teacher_password()
    
    # Create user account
    new_user = models.User(
        email=teacher_data.email,
        name=teacher_data.name,
        teacher_id=teacher_data.employee_id,
        role="teacher",
        mobile=teacher_data.phone,
        hashed_password=generate_password(password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log the created password for admin reference
    print(f"✅ Teacher created: {teacher_data.name}")
    print(f"   Email: {teacher_data.email}")
    print(f"   Password: {password}")
    
    return new_user

@router.post("/import/excel", response_model=schemas.TeacherUploadResponse)
async def import_teachers_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    #current_user: models.User = Depends(require_admin)
):
    """Import teachers and assignments from Excel (Admin only)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Only Excel files allowed")
    
    try:
        contents = await file.read()
        file_stream = io.BytesIO(contents)
        
        # Read all sheets
        xls = pd.ExcelFile(file_stream)
        sheet_names = xls.sheet_names
        
        print(f"📁 File: {file.filename}")
        print(f"📋 Sheets: {sheet_names}")
        
        teachers_created = 0
        teachers_updated = 0
        assignments_created = 0
        errors = []
        
        # SPECIFICALLY READ SHEET3 FOR TEACHER ASSIGNMENTS
        if "Sheet3" not in sheet_names:
            raise HTTPException(400, "Sheet3 not found in Excel file. Teacher assignments should be in Sheet3.")
        
        print(f"\n📊 Processing teacher assignments from Sheet3")
        df_teachers = pd.read_excel(file_stream, sheet_name="Sheet3", header=None)
        print(f"Sheet3 shape: {df_teachers.shape}")
        
        # Print first few rows for debugging
        print("\nFirst 20 rows of Sheet3:")
        for i in range(min(20, len(df_teachers))):
            row_data = df_teachers.iloc[i].fillna('').astype(str).tolist()
            print(f"Row {i}: {row_data}")
        
        current_course = None
        current_teachers = []
        
        # Process each row in Sheet3
        for idx, row in df_teachers.iterrows():
            # Fill NaN values with empty strings
            row = row.fillna('')
            
            # Get course code from column 0
            course_cell = str(row.iloc[0]).strip() if row.iloc[0] != '' else ""
            
            # Skip header row (row 0)
            if idx == 0 and course_cell == "Course code":
                print("Skipping header row")
                continue
            
            # Check if this is a course code row (non-empty course code)
            if course_cell and course_cell != "":
                # Process previous course's teachers if any
                if current_course and current_teachers:
                    print(f"\n📝 Processing course: {current_course}")
                    print(f"   Teachers: {current_teachers}")
                    created, updated = await process_course_teachers(current_course, current_teachers, db, errors)
                    teachers_created += created
                    teachers_updated += updated
                    assignments_created += len(current_teachers)
                
                # Start new course
                current_course = course_cell.replace(" ", "")
                current_teachers = []
                print(f"\n🎯 New course found: {current_course}")
                
                # Get teacher name from column 3
                teacher_cell = str(row.iloc[3]).strip() if row.iloc[3] != '' else ""
                
                if teacher_cell and teacher_cell != "":
                    # This is a teacher row
                    current_teachers.append({
                        'name': teacher_cell,
                        'department': ""  # Will be filled from next row
                    })
                    print(f"   👨‍🏫 Teacher: {teacher_cell}")
            
            # If we have a current course, check for additional rows
            elif current_course:
                # Get value from column 3
                cell_value = str(row.iloc[3]).strip() if row.iloc[3] != '' else ""
                
                if cell_value and cell_value != "":
                    # Check if this is a department row (contains professional titles)
                    if any(title in cell_value for title in ['Prof.', 'Director', 'Associate', 'Asst.', 'Assistant']):
                        # This is a department row - update last teacher's department
                        if current_teachers:
                            current_teachers[-1]['department'] = cell_value
                            print(f"   🏫 Department for last teacher: {cell_value}")
                    else:
                        # This is another teacher for the same course
                        current_teachers.append({
                            'name': cell_value,
                            'department': ""  # Will be filled from next row
                        })
                        print(f"   👨‍🏫 Additional teacher: {cell_value}")
        
        # Process the last course
        if current_course and current_teachers:
            print(f"\n📝 Processing last course: {current_course}")
            print(f"   Teachers: {current_teachers}")
            created, updated = await process_course_teachers(current_course, current_teachers, db, errors)
            teachers_created += created
            teachers_updated += updated
            assignments_created += len(current_teachers)
        
        print(f"\n📊 Import Summary:")
        print(f"   Teachers Created: {teachers_created}")
        print(f"   Teachers Updated: {teachers_updated}")
        print(f"   Assignments Created: {assignments_created}")
        print(f"   Errors: {errors}")
        
        return {
            "message": f"Teacher import completed",
            "teachers_created": teachers_created,
            "teachers_updated": teachers_updated,
            "assignments_created": assignments_created,
            "errors": errors if errors else []
        }
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(500, f"Import error: {str(e)}")
async def process_course_teachers(course_code: str, teachers: list, db: Session, errors: list):
    """Process teachers for a specific course"""
    # Extract base course code (e.g., "AEX101" -> "AEX")
    import re
    
    # Try to match course patterns like AEX101, AEX102, etc.
    match = re.match(r'^([A-Z]+)', course_code)  # Get the alphabetic part
    if match:
        base_course_code = match.group(1)  # e.g., "AEX"
    else:
        base_course_code = course_code
    
    # First, try exact match (e.g., "AEX101")
    course = db.query(models.Course).filter(
        models.Course.code == course_code
    ).first()
    
    # If not found, try base code (e.g., "AEX")
    if not course:
        course = db.query(models.Course).filter(
            models.Course.code == base_course_code
        ).first()
    
    # If still not found, try case-insensitive search
    if not course:
        course = db.query(models.Course).filter(
            models.Course.code.ilike(f"%{base_course_code}%")
        ).first()
    
    if not course:
        errors.append(f"Course {course_code} (or base {base_course_code}) not found in database")
        return 0, 0  # Return zero counts
    
    # Use the actual course code from database for assignment
    actual_course_code = course.code
    
    teachers_created = 0
    teachers_updated = 0
    
    print(f"🔍 Found course in DB: {actual_course_code} - {course.title}")
    
    for teacher_info in teachers:
        teacher_name = parse_teacher_name(teacher_info['name'])
        department = parse_department(teacher_info['department']) if teacher_info.get('department') else "General"
        
        # Skip if teacher name is empty or invalid
        if not teacher_name or teacher_name.lower() in ['nan', 'na', '']:
            continue
        
        print(f"   👨‍🏫 Processing teacher: {teacher_name} (Dept: {department})")
        
        # Generate email from name
        email_parts = teacher_name.lower().split()
        if len(email_parts) >= 2:
            email = f"{email_parts[0][0]}{email_parts[-1]}@college.edu"
        else:
            email = f"{teacher_name.lower().replace(' ', '.')}@college.edu"
        
        # Generate employee ID
        employee_id = f"T{random.randint(1000, 9999)}"
        
        # Check if teacher already exists by name
        existing_teacher = db.query(models.User).filter(
            models.User.name.ilike(f"%{teacher_name}%"),
            models.User.role == "teacher"
        ).first()
        
        if existing_teacher:
            print(f"   ✅ Found existing teacher: {existing_teacher.name} (ID: {existing_teacher.id})")
            teacher_user = existing_teacher
            teachers_updated += 1
        else:
            # Create new teacher
            password = generate_teacher_password()
            
            new_teacher = models.User(
                email=email,
                name=teacher_name,
                teacher_id=employee_id,
                role="teacher",
                hashed_password=generate_password(password)
            )
            
            db.add(new_teacher)
            db.flush()  # Get the ID
            teacher_user = new_teacher
            teachers_created += 1
            
            print(f"   ✅ Created teacher: {teacher_name} (ID: {teacher_user.id})")
            print(f"      Email: {email}")
            print(f"      Password: {password}")
            print(f"      Employee ID: {employee_id}")
        
        # Create teacher-course assignment using actual course code
        existing_assignment = db.query(models.TeacherCourse).filter(
            and_(
                models.TeacherCourse.teacher_id == teacher_user.id,
                models.TeacherCourse.course_code == actual_course_code
            )
        ).first()
        
        if not existing_assignment:
            new_assignment = models.TeacherCourse(
                teacher_id=teacher_user.id,
                course_code=actual_course_code,
                section=None,  # Will be assigned later
                batch=None
            )
            db.add(new_assignment)
            print(f"   🔗 Created assignment: {teacher_name} -> {actual_course_code}")
        else:
            print(f"   ℹ️  Assignment already exists for {teacher_name} -> {actual_course_code}")
    
    # Commit all changes for this course
    try:
        db.commit()
        print(f"   💾 Successfully committed changes for course {actual_course_code}")
    except Exception as e:
        db.rollback()
        errors.append(f"Failed to commit changes for course {actual_course_code}: {str(e)}")
        print(f"   ❌ Error committing changes: {str(e)}")
        return 0, 0
    
    return teachers_created, teachers_updated

@router.get("/assignments", response_model=List[schemas.TeacherAssignmentResponse])
def get_teacher_assignments(
    db: Session = Depends(get_db),
    #current_user: models.User = Depends(get_current_user),
    teacher_id: Optional[int] = Query(None),
    course_code: Optional[str] = Query(None)
):
    """Get teacher-course assignments"""
    query = db.query(models.TeacherCourse).options(
        joinedload(models.TeacherCourse.teacher),
        joinedload(models.TeacherCourse.course)
    )
    
    #if current_user.role == "teacher":
        # Teachers can only see their own assignments
        #query = query.filter(models.TeacherCourse.teacher_id == current_user.id)
    #elif teacher_id and current_user.role == "admin":
        # Admin can filter by teacher
        #query = query.filter(models.TeacherCourse.teacher_id == teacher_id)
    
    if course_code:
        query = query.filter(models.TeacherCourse.course_code == course_code)
    
    assignments = query.all()
    
    result = []
    for assignment in assignments:
        result.append({
            "id": assignment.id,
            "teacher_name": assignment.teacher.name,
            "teacher_email": assignment.teacher.email,
            "course_code": assignment.course_code,
            "course_title": assignment.course.title if assignment.course else "N/A",
            "section": assignment.section,
            "batch": assignment.batch,
            "is_primary": True  # You might want to add this field to the model
        })
    
    return result

@router.post("/assign", response_model=dict)
def assign_teacher_to_course(
    assignment: schemas.TeacherAssignment,
    db: Session = Depends(get_db),
    #current_user: models.User = Depends(require_admin)
):
    """Assign teacher to a course (Admin only)"""
    # Check if teacher exists
    teacher = db.query(models.User).filter(
        models.User.id == assignment.teacher_id,
        models.User.role == "teacher"
    ).first()
    
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    
    # Check if course exists
    course = db.query(models.Course).filter(
        models.Course.code == assignment.course_code
    ).first()
    
    if not course:
        raise HTTPException(404, "Course not found")
    
    # Check if assignment already exists
    existing = db.query(models.TeacherCourse).filter(
        and_(
            models.TeacherCourse.teacher_id == assignment.teacher_id,
            models.TeacherCourse.course_code == assignment.course_code
        )
    ).first()
    
    if existing:
        raise HTTPException(400, "Teacher already assigned to this course")
    
    # Create assignment
    new_assignment = models.TeacherCourse(
        teacher_id=assignment.teacher_id,
        course_code=assignment.course_code,
        section=assignment.section,
        batch=assignment.batch
    )
    
    db.add(new_assignment)
    db.commit()
    
    return {
        "success": True,
        "message": f"Teacher {teacher.name} assigned to {course.code}",
        "assignment_id": new_assignment.id
    }

@router.delete("/assign/{assignment_id}")
def remove_teacher_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    #current_user: models.User = Depends(require_admin)
):
    """Remove teacher from course assignment (Admin only)"""
    assignment = db.query(models.TeacherCourse).filter(
        models.TeacherCourse.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    db.delete(assignment)
    db.commit()
    
    return {"success": True, "message": "Assignment removed"}

@router.get("/my-courses")
def get_my_courses(
    db: Session = Depends(get_db),
    #current_user: models.User = Depends(get_current_user)
):
    """Get courses assigned to current teacher"""
    #if current_user.role != "teacher":
        #raise HTTPException(403, "Only teachers can access this endpoint")
    
    assignments = db.query(models.TeacherCourse).options(
        joinedload(models.TeacherCourse.course)
    ).filter(
        #models.TeacherCourse.teacher_id == current_user.id
    ).all()
    
    courses = []
    for assignment in assignments:
        if assignment.course:
            courses.append({
                "code": assignment.course.code,
                "title": assignment.course.title,
                "year": assignment.course.year,
                "semester": assignment.course.semester,
                "section": assignment.section,
                "batch": assignment.batch,
                "has_theory": assignment.course.has_theory,
                "has_practical": assignment.course.has_practical
            })
    
    return courses