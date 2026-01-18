# app/services.py - CORRECTED WHATSAPP API
import httpx
import os
import json
from typing import List, Dict, Optional
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

class WhatsAppService:
    def __init__(self):
        self.api_key = os.getenv("FAST2SMS_API_KEY")
        self.base_url = "https://www.fast2sms.com/dev"
        self.default_message_id = "10633"
        self.phone_number_id = "932888079913083"  # From your Excel file
        
        if not self.api_key:
            print("⚠️ FAST2SMS_API_KEY not configured")
        else:
            masked_key = self.api_key[:10] + "..." + self.api_key[-10:] if len(self.api_key) > 20 else "***"
            print(f"✅ Fast2SMS API Key loaded: {masked_key}")
    
    async def send_whatsapp(
        self, 
        phone_numbers: List[str], 
        message_id: str = None,
        template_params: List[str] = None
    ) -> Dict:
        """
        Send WhatsApp message via Fast2SMS WhatsApp API (NOT Quicksms)
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "message_id": None
            }
        
        # Clean phone numbers
        cleaned_numbers = []
        for num in phone_numbers:
            if not num:
                continue
                
            cleaned = str(num).strip()
            
            # Remove country code if present
            if cleaned.startswith("+91"):
                cleaned = cleaned[3:]
            elif cleaned.startswith("91"):
                cleaned = cleaned[2:]
            
            # Keep only digits
            cleaned = ''.join(filter(str.isdigit, cleaned))
            
            if len(cleaned) == 10:
                cleaned_numbers.append(cleaned)
            else:
                print(f"⚠️ Skipping invalid number format: {num} -> {cleaned}")
        
        if not cleaned_numbers:
            return {
                "success": False,
                "error": "No valid phone numbers (need 10-digit Indian numbers)",
                "message_id": None
            }
        
        # Use Message ID
        message_id_to_use = message_id or self.default_message_id
        
        print(f"📱 Using Fast2SMS WhatsApp Message ID: {message_id_to_use}")
        
        # Send WhatsApp using correct WhatsApp API
        return await self.send_whatsapp_template(
            phone_numbers=cleaned_numbers,
            message_id=message_id_to_use,
            template_params=template_params
        )
    
    async def send_whatsapp_template(
        self, 
        phone_numbers: List[str], 
        message_id: str,
        template_params: List[str] = None
    ) -> Dict:
        """
        Send WhatsApp template message using /dev/whatsapp endpoint
        Format: https://www.fast2sms.com/dev/whatsapp?authorization=API_KEY&message_id=10633&...
        """
        try:
            # Format template parameters as pipe-separated (|)
            variables_values = ""
            if template_params:
                variables_values = "|".join(template_params)
            
            # Build URL parameters
            params = {
                "authorization": self.api_key,
                "message_id": message_id,
                "phone_number_id": self.phone_number_id,
                "numbers": ",".join(phone_numbers),
            }
            
            if variables_values:
                params["variables_values"] = variables_values
            
            # Build URL - WhatsApp API uses GET request with URL parameters
            query_string = "&".join([f"{key}={quote(str(value))}" for key, value in params.items()])
            url = f"{self.base_url}/whatsapp?{query_string}"
            
            print(f"📱 WhatsApp Template API URL: {url}")
            print(f"📱 Message ID: {message_id}")
            print(f"📱 Phone Numbers: {phone_numbers}")
            print(f"📱 Template Params: {template_params}")
            
            # Make GET request to WhatsApp API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                
                print(f"📡 Response Status: {response.status_code}")
                print(f"📡 Response: {response.text}")
                
                try:
                    data = response.json()
                except:
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {response.text}",
                        "status_code": response.status_code
                    }
                
                if response.status_code == 200 and data.get("return", False):
                    return {
                        "success": True,
                        "message_id": data.get("message_id"),
                        "request_id": data.get("request_id"),
                        "cost": data.get("cost", 0),
                        "response": data,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Failed to send WhatsApp"),
                        "status_code": response.status_code,
                        "response": data
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message_id": None
            }
    
    async def send_whatsapp_session(
        self,
        to_number: str,
        message_type: str,
        **kwargs
    ) -> Dict:
        """
        Send WhatsApp session message using /dev/whatsapp-session endpoint
        Format: https://www.fast2sms.com/dev/whatsapp-session?authorization=API_KEY&...
        """
        try:
            # Base parameters
            params = {
                "authorization": self.api_key,
                "phone_number_id": self.phone_number_id,
                "to": to_number,
                "type": message_type.lower()
            }
            
            # Add additional parameters based on message type
            if message_type.upper() == "TEXT":
                params["text"] = kwargs.get("text", "")
            elif message_type.upper() == "IMAGE":
                params["url"] = kwargs.get("url", "")
            elif message_type.upper() == "DOCUMENT":
                params["url"] = kwargs.get("url", "")
                params["document_filename"] = kwargs.get("filename", "document.pdf")
            elif message_type.upper() == "LOCATION":
                params["latitude"] = kwargs.get("latitude", "")
                params["longitude"] = kwargs.get("longitude", "")
                params["name"] = kwargs.get("name", "")
                params["address"] = kwargs.get("address", "")
            
            # Build URL
            query_string = "&".join([f"{key}={quote(str(value))}" for key, value in params.items()])
            url = f"{self.base_url}/whatsapp-session?{query_string}"
            
            print(f"📱 WhatsApp Session API URL: {url[:200]}...")
            
            # Make GET request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                data = response.json()
                
                return {
                    "success": response.status_code == 200 and data.get("return", False),
                    "response": data,
                    "message_type": message_type,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_balance(self) -> Dict:
        """Check WhatsApp balance"""
        if not self.api_key:
            return {"error": "API key not configured"}
        
        headers = {"authorization": self.api_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/wallet",
                    headers=headers
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def verify_api_key(self) -> Dict:
        """Verify API key works"""
        if not self.api_key:
            return {"error": "API key not configured", "is_valid": False}
        
        headers = {"authorization": self.api_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/wallet",
                    headers=headers
                )
                
                return {
                    "status_code": response.status_code,
                    "is_valid": response.status_code == 200,
                    "response": response.text[:100]
                }
        except Exception as e:
            return {"error": str(e), "is_valid": False}
    
    async def test_whatsapp_send(self, phone: str) -> Dict:
        """Test WhatsApp sending with a simple text"""
        try:
            # Use WhatsApp session API for testing
            return await self.send_whatsapp_session(
                to_number=phone,
                message_type="TEXT",
                text="Test WhatsApp message from Attendance System"
            )
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton instance
whatsapp_service = WhatsAppService()