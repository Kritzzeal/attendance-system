# app/routes/setup_routes.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/setup/whatsapp", response_class=HTMLResponse)
async def whatsapp_setup_guide():
    return """
    <html>
    <head><title>WhatsApp Setup Guide</title></head>
    <body>
        <h1>📱 WhatsApp Setup Guide</h1>
        
        <h2>🔧 Prerequisites:</h2>
        <ol>
            <li>Google Chrome or Microsoft Edge browser installed</li>
            <li>WhatsApp account on your phone</li>
            <li>Phone connected to internet</li>
        </ol>
        
        <h2>🚀 First-Time Setup:</h2>
        <ol>
            <li>Make sure you're logged into WhatsApp on your phone</li>
            <li>Run the test endpoint: <code>GET /api/v1/whatsapp/test</code></li>
            <li>A browser window will open with WhatsApp Web</li>
            <li>Scan the QR code with your phone's WhatsApp</li>
            <li>Close the browser tab after scanning</li>
            <li>Now you can send messages!</li>
        </ol>
        
        <h2>⚠️ Important Notes:</h2>
        <ul>
            <li>Keep your phone connected to internet</li>
            <li>WhatsApp Web session stays active for about 30 days</li>
            <li>Don't log out of WhatsApp Web on browser</li>
            <li>Messages are sent from YOUR WhatsApp account</li>
        </ul>
        
        <h2>🧪 Test Now:</h2>
        <form action="/api/v1/whatsapp/send-message" method="POST">
            Phone: <input type="text" name="phone" placeholder="9791107478"><br>
            Message: <input type="text" name="message" value="Test from Attendance System"><br>
            <button type="submit">Send Test</button>
        </form>
    </body>
    </html>
    """