# app/services/whatsapp_real_service.py
import httpx
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import re

class WhatsAppRealService:
    def __init__(self):
        # Your working credentials from screenshot
        self.access_token = "EAATaP3gEe98BQff6wxopVKkeIVrhzZBIltSNRha8qlZBFIWH878Jwq5AlNSwk6D6VfRDZAlhxMgMgQ5rWZBu2bMoADivpTfZA44WQ9r9BQKI75t4jNZBpN1ySIqm4VkNljSisMTsGzOXVMFH9hQdULfQjZByT0uKgOIWR5XNvZAZAYQyWKRxGTnTL7y6VTPOaycHHsFLx1a9PPaDD5xb6YwkRi7ezyaa3AUjH8BXiZCgTQEKeOJ2UdF6pacYynrnsFBFcSKZCxuv43msx62Q6YDmOhCBR26"
        self.phone_number_id = "994096853778961"
        self.api_version = "v22.0"
        
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        
        print(f"✅ WhatsApp Business API for REAL numbers")
        print(f"   Phone Number ID: {self.phone_number_id}")
        print(f"   API Version: {self.api_version}")
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format Indian phone number to international format for WhatsApp
        Input: 9791107478 (10 digits)
        Output: +919791107478
        """
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Check if it's 10 digits (Indian number)
        if len(digits) == 10:
            return f"+91{digits}"  # India country code
        
        # Check if it's 12 digits (already with 91)
        elif len(digits) == 12 and digits.startswith('91'):
            return f"+{digits}"
        
        # Check if it already has country code
        elif len(digits) > 10 and digits.startswith('91'):
            return f"+{digits}"
        
        else:
            # Return as is, let WhatsApp API handle validation
            return f"+{digits}" if not digits.startswith('+') else digits
    
    async def send_text_message(
        self,
        to_number: str,
        message: str
    ) -> Dict:
        """
        Send plain text message to REAL phone number
        """
        # Format phone number
        formatted_number = self.format_phone_number(to_number)
        
        print(f"📱 Sending to REAL number: {formatted_number}")
        print(f"   Original: {to_number}")
        
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        print(f"💬 Message: {message[:50]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                print(f"📡 Response Status: {response.status_code}")
                print(f"📡 Response: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "message_id": data.get("messages", [{}])[0].get("id"),
                        "response": data,
                        "phone_sent": formatted_number
                    }
                else:
                    data = response.json()
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    error_code = data.get("error", {}).get("code")
                    
                    # Handle common errors
                    if error_code == 131029:  # Not authorized to send to this number
                        return {
                            "success": False,
                            "error": f"Cannot send to {formatted_number}. Number needs to be registered with WhatsApp Business first.",
                            "error_code": error_code,
                            "note": "Recipient must have interacted with your business before"
                        }
                    elif error_code == 132000:  # Rate limit
                        return {
                            "success": False,
                            "error": "Rate limit exceeded. Wait before sending more messages.",
                            "error_code": error_code
                        }
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_code": error_code,
                        "status_code": response.status_code,
                        "response": data
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_attendance_alert(
        self,
        to_number: str,
        student_name: str,
        student_id: str,
        course: str,
        date: str,
        time: str
    ) -> Dict:
        """
        Send attendance alert to parent's REAL number
        """
        message = f"""📚 *Attendance Alert - College Management System*

Dear Parent/Guardian,

This is to inform you that *{student_name}* was marked absent today.

📋 *Student Details:*
• Name: {student_name}
• ID: {student_id}
• Course: {course}

📅 *Absence Details:*
• Date: {date}
• Time: {time}

Please acknowledge this notification and ensure your ward attends future classes regularly.

For any queries or discrepancies, please contact the college administration office during working hours.

---
*Automated Notification System*
*College Attendance Management*
📞 Contact: 9486760600
📧 Email: hortsekar@hotmail.com
"""
        
        return await self.send_text_message(to_number, message)
    
    async def test_with_real_number(self, phone: str) -> Dict:
        """
        Test sending to a real phone number
        """
        test_message = f"Test message from College Attendance System - {datetime.now().strftime('%H:%M')}"
        
        return await self.send_text_message(phone, test_message)
    
    async def check_number_status(self, phone: str) -> Dict:
        """
        Check if we can send to this number
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        formatted_number = self.format_phone_number(phone)
        
        # Note: WhatsApp Business API requires prior interaction
        # or the number to be in your contacts
        
        return {
            "phone": phone,
            "formatted": formatted_number,
            "note": "WhatsApp Business requires: 1. Business verification 2. Recipient initiated contact OR 3. Recipient is in your contacts",
            "requirements": [
                "Business must be verified by Meta",
                "Recipient must have sent a message to your business first",
                "OR you have their explicit opt-in",
                "Free tier only allows responses to user-initiated conversations"
            ]
        }

# Singleton instance
whatsapp_real = WhatsAppRealService()