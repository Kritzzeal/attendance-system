# app/services/sms_service.py - FIXED VERSION
import httpx
import json
from typing import List, Dict
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.api_key = os.getenv("FAST2SMS_API_KEY")
        self.base_url = "https://www.fast2sms.com/dev/bulkV2"
        self.sender_id = "EDUATT"
        
        if not self.api_key:
            logger.warning("FAST2SMS_API_KEY not found")
            print("❌ FAST2SMS_API_KEY not configured!")
    
    async def send_sms(self, phone_numbers: List[str], message: str) -> Dict:
        """
        Send SMS using Fast2SMS API with better error handling
        """
        # Check if API key exists
        if not self.api_key:
            return {
                "status": "failed",
                "error": "SMS service not configured - No API key",
                "message_id": None,
                "cost": 0
            }
        
        # Clean phone numbers
        cleaned_numbers = []
        for num in phone_numbers:
            cleaned = str(num).strip()
            if cleaned.startswith("+91"):
                cleaned = cleaned[3:]
            elif cleaned.startswith("91"):
                cleaned = cleaned[2:]
            cleaned = ''.join(filter(str.isdigit, cleaned))
            
            if len(cleaned) == 10:
                cleaned_numbers.append(cleaned)
            else:
                logger.warning(f"Invalid phone number: {num}")
        
        if not cleaned_numbers:
            return {
                "status": "failed",
                "error": "No valid phone numbers",
                "message_id": None,
                "cost": 0
            }
        
        numbers_str = ",".join(cleaned_numbers)
        
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "route": "promo",  # Changed from 'v3' to 'otp' (cheaper)
            "sender_id": self.sender_id,
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": numbers_str
        }
        
        print(f"📤 Sending SMS via Fast2SMS to {len(cleaned_numbers)} numbers")
        print(f"🔑 API Key present: {'Yes' if self.api_key else 'No'}")
        print(f"🔑 API Key first 10 chars: {self.api_key[:10]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Make the request
                response = await client.post(self.base_url, json=payload, headers=headers)
                
                print(f"📡 Fast2SMS Response Status: {response.status_code}")
                print(f"📡 Response Headers: {dict(response.headers)}")
                print(f"📡 Raw Response Text: {response.text[:200]}...")
                
                # Try to parse JSON
                try:
                    response_data = response.json()
                    print(f"📡 Parsed JSON: {response_data}")
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"❌ Raw response: {response.text}")
                    
                    # Return structured error
                    return {
                        "status": "failed",
                        "error": f"Invalid JSON from Fast2SMS: {response.text[:100]}",
                        "message_id": None,
                        "cost": 0,
                        "provider_response": {"raw_response": response.text[:500]}
                    }
                
                # Check response
                if response.status_code == 200 and response_data.get("return"):
                    print(f"✅ SMS sent successfully!")
                    return {
                        "status": "sent",
                        "message_id": response_data.get("request_id"),
                        "cost": response_data.get("price", 0),
                        "provider_response": response_data
                    }
                else:
                    print(f"❌ SMS failed: {response_data}")
                    return {
                        "status": "failed",
                        "error": response_data.get("message", "Unknown error"),
                        "message_id": None,
                        "cost": 0,
                        "provider_response": response_data
                    }
                    
        except httpx.TimeoutException:
            error_msg = "Fast2SMS timeout - server not responding"
            print(f"❌ {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "message_id": None,
                "cost": 0
            }
        except Exception as e:
            error_msg = f"Fast2SMS error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "message_id": None,
                "cost": 0
            }

# Singleton
sms_service = SMSService()

async def send_bulk_sms(phone_numbers: List[str], message: str) -> Dict:
    return await sms_service.send_sms(phone_numbers, message)