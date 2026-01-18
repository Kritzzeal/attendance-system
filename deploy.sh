# deploy.sh
#!/bin/bash

echo "🚀 Deploying Attendance System..."

# 1. Clone or copy your code to server
# scp -r backend/ user@your-server:/opt/attendance-system/

# 2. On the server, run:
cd /opt/attendance-system/backend

# 3. Make sure data directory exists
mkdir -p data

# 4. Copy your SQLite database (if exists)
# scp user@local-machine:/path/to/attendance.db ./data/

# 5. Start with Docker Compose
docker-compose up -d

# 6. Set up auto-start on reboot
echo "@reboot cd /opt/attendance-system/backend && docker-compose up -d" | crontab -

echo "✅ Deployment complete!"
echo "📱 Access at: http://$(curl -s ifconfig.me):8000"