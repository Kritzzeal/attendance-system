# app/routers/attendance.py - FIXED VERSION
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..database import get_db
from .. import models

router = APIRouter(prefix="/attendance", tags=["attendance"])

# ============ PYDANTIC MODELS ============
class AttendanceMark(BaseModel):
    student_id: str
    status: str  # present, absent, late, excused

class AttendanceBatch(BaseModel):
    course_code: str
    session_type: str  # theory, practical, lab, tutorial
    section_batch: str  # TA/TB for theory, PA/PB/PC/PD for practical
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    attendance_list: List[AttendanceMark]

# ============ HELPER FUNCTIONS ============
def validate_status(status: str) -> bool:
    """Validate attendance status"""
    valid_statuses = ['present', 'absent', 'late', 'excused']
    return status.lower() in valid_statuses

def get_teacher_by_id(db: Session, teacher_id: int):
    """Get teacher from users table"""
    return db.query(models.User).filter(
        models.User.id == teacher_id
    ).first()

# ============ ATTENDANCE ENDPOINTS ============

# TEST ENDPOINT - Add this first to verify router works
@router.get("/test")
def test_attendance():
    """Test endpoint to verify attendance router is working"""
    return {
        "success": True,
        "message": "Attendance router is working!",
        "endpoints": [
            "POST /api/v1/attendance/mark",
            "GET /api/v1/attendance/students-list",
            "GET /api/v1/attendance/today",
            "GET /api/v1/attendance/teacher/courses"
        ]
    }

@router.post("/mark", status_code=status.HTTP_201_CREATED)
async def mark_attendance(
    attendance_data: AttendanceBatch,
    teacher_id: int = Query(..., description="Teacher ID from users table"),
    db: Session = Depends(get_db)
):
    """
    Mark attendance for a batch of students
    """
    try:
        # Parse dates
        attendance_date = datetime.strptime(attendance_data.date, "%Y-%m-%d").date()
        start_time = datetime.strptime(attendance_data.start_time, "%H:%M").time()
        end_time = datetime.strptime(attendance_data.end_time, "%H:%M").time()
        
        # Validate times
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )
        
        # Verify teacher exists
        teacher = get_teacher_by_id(db, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Get course to verify it exists
        course = db.query(models.Course).filter(
            models.Course.code == attendance_data.course_code
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {attendance_data.course_code} not found"
            )
        
        records_created = 0
        records_updated = 0
        errors = []
        successful_students = []
        
        for student_att in attendance_data.attendance_list:
            try:
                # Validate status
                if not validate_status(student_att.status):
                    errors.append(f"Invalid status '{student_att.status}' for student {student_att.student_id}")
                    continue
                
                # Check if student exists
                student = db.query(models.Student).filter(
                    models.Student.student_id == student_att.student_id,
                    models.Student.is_active == True
                ).first()
                
                if not student:
                    errors.append(f"Student {student_att.student_id} not found or inactive")
                    continue
                
                # Check if attendance already exists for this session
                existing = db.query(models.Attendance).filter(
                    models.Attendance.student_id == student_att.student_id,
                    models.Attendance.course_code == attendance_data.course_code,
                    models.Attendance.date == attendance_date,
                    models.Attendance.session_type == attendance_data.session_type
                ).first()
                
                if existing:
                    # Update existing record
                    existing.status = student_att.status.lower()
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.teacher_id = teacher_id
                    existing.section_batch = attendance_data.section_batch
                    records_updated += 1
                else:
                    # Create new record
                    new_attendance = models.Attendance(
                        date=attendance_date,
                        start_time=start_time,
                        end_time=end_time,
                        course_code=attendance_data.course_code,
                        session_type=attendance_data.session_type,
                        section_batch=attendance_data.section_batch,
                        student_id=student_att.student_id,
                        status=student_att.status.lower(),
                        teacher_id=teacher_id,
                        sms_sent=False,
                        sms_sent_at=None
                    )
                    db.add(new_attendance)
                    records_created += 1
                
                successful_students.append(student_att.student_id)
                    
            except Exception as e:
                error_msg = f"Error for student {student_att.student_id}: {str(e)}"
                errors.append(error_msg)
                continue
        
        db.commit()
        
        response = {
            "success": True,
            "message": "Attendance marked successfully",
            "date": attendance_date.isoformat(),
            "course_code": attendance_data.course_code,
            "course_title": course.title,
            "session_type": attendance_data.session_type,
            "section_batch": attendance_data.section_batch,
            "teacher_id": teacher_id,
            "teacher_name": teacher.name,
            "records_created": records_created,
            "records_updated": records_updated,
            "successful_students": len(successful_students),
            "total_attempted": len(attendance_data.attendance_list),
            "errors": errors if errors else None
        }
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date/time format: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking attendance: {str(e)}"
        )

@router.get("/students-list")
def get_students_for_attendance(
    course_code: str = Query(..., description="Course code"),
    session_type: str = Query(..., description="Session type: theory/practical/lab"),
    section_batch: str = Query(..., description="Section/Batch: TA/TB/PA/PB etc"),
    teacher_id: int = Query(..., description="Teacher ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of students for attendance marking
    """
    try:
        # Verify teacher exists
        teacher = get_teacher_by_id(db, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Get course details
        course = db.query(models.Course).filter(
            models.Course.code == course_code
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Get students based on year and section/batch
        query = db.query(models.Student).filter(
            models.Student.year == course.year,
            models.Student.is_active == True
        )
        
        # Filter by section/batch based on session type
        if session_type.lower() in ['theory', 'lecture']:
            query = query.filter(models.Student.theory_section == section_batch)
        elif session_type.lower() in ['practical', 'lab']:
            query = query.filter(models.Student.practical_batch == section_batch)
        
        students = query.all()
        
        student_list = []
        for student in students:
            student_list.append({
                "student_id": student.student_id,
                "name": student.name,
                "year": student.year,
                "theory_section": student.theory_section,
                "practical_batch": student.practical_batch,
                "student_mobile": student.student_mobile,
                "parent_mobile": student.parent_mobile,
                "is_active": student.is_active
            })
        
        return {
            "success": True,
            "course_code": course_code,
            "course_title": course.title,
            "session_type": session_type,
            "section_batch": section_batch,
            "year": course.year,
            "semester": course.semester,
            "teacher_id": teacher_id,
            "teacher_name": teacher.name,
            "total_students": len(student_list),
            "students": student_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching students: {str(e)}"
        )

@router.get("/teacher/courses")
def get_teacher_courses(
    teacher_id: int = Query(..., description="Teacher ID"),
    db: Session = Depends(get_db)
):
    """
    Get all courses assigned to a teacher
    """
    try:
        # Get teacher details
        teacher = get_teacher_by_id(db, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # If admin, return all courses
        if teacher.role == 'admin':
            courses = db.query(models.Course).all()
            return {
                "teacher_id": teacher_id,
                "teacher_name": teacher.name,
                "role": "admin",
                "total_courses": len(courses),
                "courses": [
                    {
                        "code": course.code,
                        "title": course.title,
                        "year": course.year,
                        "semester": course.semester,
                        "credits": course.credits,
                        "has_theory": course.has_theory,
                        "has_practical": course.has_practical
                    }
                    for course in courses
                ]
            }
        
        # Get courses from teacher_courses table
        teacher_courses = db.query(models.TeacherCourse).filter(
            models.TeacherCourse.teacher_id == teacher_id
        ).all()
        
        courses_list = []
        for tc in teacher_courses:
            course = db.query(models.Course).filter(
                models.Course.code == tc.course_code
            ).first()
            
            if course:
                courses_list.append({
                    "code": course.code,
                    "title": course.title,
                    "year": course.year,
                    "semester": course.semester,
                    "credits": course.credits,
                    "has_theory": course.has_theory,
                    "has_practical": course.has_practical,
                    "section": tc.section,
                    "batch": tc.batch
                })
        
        return {
            "success": True,
            "teacher_id": teacher_id,
            "teacher_name": teacher.name,
            "role": teacher.role,
            "total_courses": len(courses_list),
            "courses": courses_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching teacher courses: {str(e)}"
        )

@router.get("/today")
def get_today_attendance(
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    course_code: Optional[str] = Query(None, description="Filter by course code"),
    db: Session = Depends(get_db)
):
    """
    Get today's attendance records
    """
    try:
        today = date.today()
        
        # Build query
        query = db.query(models.Attendance).filter(
            models.Attendance.date == today
        )
        
        if teacher_id:
            query = query.filter(models.Attendance.teacher_id == teacher_id)
        
        if course_code:
            query = query.filter(models.Attendance.course_code == course_code)
        
        attendance_records = query.order_by(
            models.Attendance.start_time.desc()
        ).all()
        
        records_with_details = []
        for att in attendance_records:
            # Get student name
            student = db.query(models.Student).filter(
                models.Student.student_id == att.student_id
            ).first()
            
            # Get course title
            course = db.query(models.Course).filter(
                models.Course.code == att.course_code
            ).first()
            
            # Get teacher name
            teacher = get_teacher_by_id(db, att.teacher_id)
            
            records_with_details.append({
                "id": att.id,
                "student_id": att.student_id,
                "student_name": student.name if student else "Unknown",
                "course_code": att.course_code,
                "course_title": course.title if course else "Unknown",
                "session_type": att.session_type,
                "section_batch": att.section_batch,
                "status": att.status,
                "date": att.date.isoformat(),
                "start_time": att.start_time.strftime("%H:%M") if att.start_time else "",
                "end_time": att.end_time.strftime("%H:%M") if att.end_time else "",
                "teacher_id": att.teacher_id,
                "teacher_name": teacher.name if teacher else "Unknown",
                "sms_sent": att.sms_sent,
                "sms_sent_at": att.sms_sent_at.strftime("%H:%M") if att.sms_sent_at else None
            })
        
        # Calculate summary
        summary = {
            "total": len(attendance_records),
            "present": len([a for a in attendance_records if a.status == 'present']),
            "absent": len([a for a in attendance_records if a.status == 'absent']),
            "late": len([a for a in attendance_records if a.status == 'late']),
            "excused": len([a for a in attendance_records if a.status == 'excused'])
        }
        
        return {
            "success": True,
            "date": today.isoformat(),
            "summary": summary,
            "count": len(records_with_details),
            "attendance": records_with_details
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching today's attendance: {str(e)}"
        )

@router.get("/student/{student_id}")
def get_student_attendance(
    student_id: str,
    course_code: Optional[str] = Query(None, description="Filter by course code"),
    month: Optional[int] = Query(None, description="Filter by month (1-12)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """
    Get attendance records for a specific student
    """
    try:
        # Check if student exists
        student = db.query(models.Student).filter(
            models.Student.student_id == student_id
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Build query
        query = db.query(models.Attendance).filter(
            models.Attendance.student_id == student_id
        )
        
        if course_code:
            query = query.filter(models.Attendance.course_code == course_code)
        
        if year and month:
            # Filter by month and year
            query = query.filter(
                extract('year', models.Attendance.date) == year,
                extract('month', models.Attendance.date) == month
            )
        
        attendance_records = query.order_by(
            models.Attendance.date.desc()
        ).all()
        
        # Calculate statistics
        total_classes = len(attendance_records)
        present_count = len([a for a in attendance_records if a.status == 'present'])
        attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
        
        return {
            "success": True,
            "student_id": student_id,
            "student_name": student.name,
            "year": student.year,
            "total_classes": total_classes,
            "present": present_count,
            "absent": len([a for a in attendance_records if a.status == 'absent']),
            "late": len([a for a in attendance_records if a.status == 'late']),
            "excused": len([a for a in attendance_records if a.status == 'excused']),
            "attendance_percentage": round(attendance_percentage, 2),
            "records": [
                {
                    "id": a.id,
                    "date": a.date.isoformat(),
                    "course_code": a.course_code,
                    "session_type": a.session_type,
                    "section_batch": a.section_batch,
                    "status": a.status,
                    "start_time": a.start_time.strftime("%H:%M") if a.start_time else "",
                    "end_time": a.end_time.strftime("%H:%M") if a.end_time else "",
                    "teacher_id": a.teacher_id
                }
                for a in attendance_records[:50]  # Limit to 50 records
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching student attendance: {str(e)}"
        )