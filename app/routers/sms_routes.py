# app/routes/sms_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SMSTemplate, SMSSent
from app.models import Attendance, SMSTemplate, SMSSent, Student 
from app.schemas import SMSRequest, SMSResponse, SMSResult, SMSTemplateUpdate
from app.auth import get_current_user

router = APIRouter(prefix="/sms", tags=["SMS"])


@router.post("/send-attendance-sms", response_model=SMSResponse)
async def send_attendance_sms(
    request: SMSRequest,
    db: Session = Depends(get_db),
    
):
    """
    Send SMS to parents WITHOUT saving to database
    """
    try:
        print(f"📱 SMS Request: {request.dict()}")
        
        # 1. Get template
        template = db.query(SMSTemplate).first()
        if not template:
            template = SMSTemplate(
                name="Default",
                template="Dear Parent, {student_name} was absent for {course} on {date}.",
                is_active=True
            )
            db.add(template)
            db.commit()
            db.refresh(template)
        
        # 2. Get students
        students = db.query(Student).filter(
            Student.id.in_(request.absent_student_ids)
        ).all()
        
        if not students:
            return SMSResponse(
                success=False,
                message="No students found",
                sent_count=0,
                failed_count=0,
                results=[]
            )
        
        # 3. Send SMS WITHOUT database save
        results = []
        for student in students:
            if not student.parent_mobile:
                continue
                
            message = template.template.format(
                student_name=student.name,
                student_id=student.student_id,
                course=request.course_id or "Course",
                date=request.date or "Today",
                session=request.session or "Session",
                teacher= "Teacher"
            )
            
            # Send SMS
            sms_result = await send_bulk_sms([student.parent_mobile], message)
            
            # Just print result, don't save to database
            print(f"📤 SMS to {student.parent_mobile}: {sms_result['status']}")
            
            # FIXED: Use SMSResult (capital S)
            results.append(SMSResult(
                student_id=student.id,
                student_name=student.name,
                parent_mobile=student.parent_mobile,
                status=sms_result["status"],
                message_id=sms_result.get("message_id")
            ))
        
        # Count results
        sent = len([r for r in results if r.status == "sent"])
        
        return SMSResponse(
            success=sent > 0,
            message=f"SMS sent: {sent}, failed: {len(results)-sent}",
            sent_count=sent,
            failed_count=len(results) - sent,
            results=results
        )
        
    except Exception as e:
        print(f"🔥 Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/templates", response_model=List[dict])
async def get_sms_templates(
    db: Session = Depends(get_db),
   
):
    """
    Get all SMS templates
    """
    try:
        templates = db.query(SMSTemplate).all()
        
        print(f"Found {len(templates)} templates")
        
        result = []
        for template in templates:
            # Debug print
            print(f"Template ID: {template.id}, Active: {template.is_active}, Type: {type(template.is_active)}")
            
            result.append({
                "id": template.id,
                "name": template.name,
                "template": template.template,
                "is_active": bool(template.is_active),  # Force to boolean
                "is_active_raw": template.is_active,  # Keep raw value for debugging
                "created_at": template.created_at,
                "updated_at": template.updated_at
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")

@router.put("/templates/{template_id}", response_model=dict)
async def update_sms_template(
    template_id: int,
    template_data: SMSTemplateUpdate,
    db: Session = Depends(get_db),
   
):
    template = db.query(SMSTemplate).filter(SMSTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_data.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    db.commit()
    return {"message": "Template updated"}

@router.get("/logs", response_model=List[dict])
async def get_sms_logs(
    attendance_id: int = None,
    db: Session = Depends(get_db),
):
    query = db.query(SMSSent)
    if attendance_id:
        query = query.filter(SMSSent.attendance_id == attendance_id)
    
    logs = query.order_by(SMSSent.sent_at.desc()).limit(100).all()
    return [
        {
            "id": log.id,
            "attendance_id": log.attendance_id,
            "student_id": log.student_id,
            "parent_mobile": log.parent_mobile,
            "message": log.message,
            "sent_at": log.sent_at,
            "status": log.status,
            "cost": log.cost,
            "message_id": log.message_id
        }
        for log in logs
    ]