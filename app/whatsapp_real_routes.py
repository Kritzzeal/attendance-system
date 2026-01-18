# app/routes/whatsapp_real_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app import whatsapp_real_service

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp Real"])

class WhatsAppRealMessage(BaseModel):
    phone: str
    message: str

class WhatsAppRealAttendance(BaseModel):
    student_id: str
    student_name: str
    parent_mobile: str
    course: str
    date: str
    time: str
    session_type: str = "Class"

@router.post("/send-to-parent")
async def send_to_parent(request: WhatsAppRealMessage):
    """Send WhatsApp to REAL parent number"""
    try:
        if not request.phone or len(request.phone) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")
        
        result = await whatsapp_real_service.whatsapp_real.send_text_message(
            to_number=request.phone,
            message=request.message
        )
        
        return {
            "success": result["success"],
            "phone": request.phone,
            "error": result.get("error"),
            "message_id": result.get("message_id"),
            "note": result.get("note", ""),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-attendance-real")
async def send_attendance_real(request: WhatsAppRealAttendance):
    """Send attendance alert to REAL parent number"""
    try:
        if not request.parent_mobile or len(request.parent_mobile) < 10:
            raise HTTPException(status_code=400, detail="Invalid parent mobile number")
        
        print(f"📱 Sending attendance alert to {request.parent_mobile}")
        print(f"👨‍🎓 Student: {request.student_name}")
        
        result = await whatsapp_real_service.whatsapp_real.send_attendance_alert(
            to_number=request.parent_mobile,
            student_name=request.student_name,
            student_id=request.student_id,
            course=request.course,
            date=request.date,
            time=request.time
        )
        
        return {
            "success": result["success"],
            "student": request.student_name,
            "parent": request.parent_mobile,
            "error": result.get("error"),
            "error_code": result.get("error_code"),
            "message_id": result.get("message_id"),
            "timestamp": datetime.now().isoformat(),
            "note": result.get("note", "Message sent to parent")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-real-number")
async def test_real_number(phone: str):
    """Test sending to a real phone number"""
    return await whatsapp_real_service.whatsapp_real.test_with_real_number(phone)

@router.get("/check-number/{phone}")
async def check_number(phone: str):
    """Check if we can send to this number"""
    return await whatsapp_real_service.whatsapp_real.check_number_status(phone)

@router.post("/send-batch-attendance")
async def send_batch_attendance(requests: List[WhatsAppRealAttendance]):
    """Send attendance alerts to multiple parents"""
    results = []
    
    for request in requests:
        try:
            result = await whatsapp_real.send_attendance_alert(
                to_number=request.parent_mobile,
                student_name=request.student_name,
                student_id=request.student_id,
                course=request.course,
                date=request.date,
                time=request.time
            )
            
            results.append({
                "student": request.student_name,
                "parent": request.parent_mobile,
                "success": result["success"],
                "error": result.get("error"),
                "message_id": result.get("message_id")
            })
            
            # Delay between messages (2 seconds to avoid rate limit)
            import asyncio
            await asyncio.sleep(2)
            
        except Exception as e:
            results.append({
                "student": request.student_name,
                "parent": request.parent_mobile,
                "success": False,
                "error": str(e)
            })
    
    success_count = len([r for r in results if r["success"]])
    
    return {
        "success": success_count > 0,
        "total": len(results),
        "sent": success_count,
        "failed": len(results) - success_count,
        "results": results
    }