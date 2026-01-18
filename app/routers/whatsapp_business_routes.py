# app/routes/whatsapp_business_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.services.whatsapp_business_service import whatsapp_business

router = APIRouter(prefix="/api/v1/whatsapp-business", tags=["WhatsApp Business"])

class WhatsAppBusinessMessage(BaseModel):
    message: str

class WhatsAppAttendanceRequest(BaseModel):
    student_id: str
    student_name: str
    course: str
    date: str
    time: str

@router.post("/send-test")
async def send_test_message(request: WhatsAppBusinessMessage):
    """Send test message to your test number"""
    try:
        result = await whatsapp_business.send_text_message(
            to_number=whatsapp_business.test_number,
            message=request.message
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=result.get("error", "Failed to send WhatsApp")
            )
        
        return {
            "success": True,
            "message": f"Test sent to {whatsapp_business.test_number}",
            "message_id": result.get("message_id"),
            "note": "Check WhatsApp on the test phone number"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-attendance-alert")
async def send_business_attendance_alert(request: WhatsAppAttendanceRequest):
    """Send attendance alert via WhatsApp Business API"""
    try:
        result = await whatsapp_business.send_attendance_alert(
            student_name=request.student_name,
            student_id=request.student_id,
            course=request.course,
            date=request.date,
            time=request.time
        )
        
        return {
            "success": result["success"],
            "student": request.student_name,
            "sent_to": whatsapp_business.test_number,
            "error": result.get("error"),
            "message_id": result.get("message_id"),
            "timestamp": datetime.now().isoformat(),
            "note": "Sent to test number +4915259184059 (free for 90 days)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-connection")
async def test_whatsapp_business():
    """Test the exact curl command from Meta"""
    return await whatsapp_business.test_connection()

@router.get("/info")
async def whatsapp_info():
    """Get WhatsApp Business API info"""
    return {
        "phone_number_id": whatsapp_business.phone_number_id,
        "test_number": whatsapp_business.test_number,
        "api_version": whatsapp_business.api_version,
        "note": "Free messages for 90 days to test number"
    }