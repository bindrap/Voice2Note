# Voice2Note Production Deployment

## Server Information
- **Hostname**: rainydaze
- **Tailscale IP**: 100.123.132.122
- **Access URL**: http://100.123.132.122:5000
- **Server Type**: Oracle Cloud (22GB RAM, 4 CPU cores)
- **Operating System**: Oracle Linux 9

## Application Configuration
- **Workers**: 8 Gunicorn workers
- **Timeout**: 1800 seconds (30 minutes)
- **Whisper Model**: large-v3 (3GB, best quality)
- **Upload Limit**: 1GB
- **Database**: SQLite (voice2note.db)

## Firewall Configuration
```bash
# Port 5000 open for application
sudo firewall-cmd --permanent --add-port=5000/tcp

# Tailscale interface in trusted zone
sudo firewall-cmd --permanent --add-interface=tailscale0 --zone=trusted

# Reload firewall
sudo firewall-cmd --reload
```

## Server Management

### Check Status
```bash
ps aux | grep gunicorn | grep 5000
curl http://localhost:5000
```

### Stop Server
```bash
pkill -f "gunicorn.*5000.*app:app"
```

### Start Server
```bash
cd /home/opc/Desktop/Voice2Note
source venv/bin/activate
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 1800 app:app --daemon
```

### Restart Server
```bash
pkill -f "gunicorn.*5000.*app:app"
cd /home/opc/Desktop/Voice2Note
source venv/bin/activate
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 1800 app:app --daemon
```

### View Logs
```bash
# Gunicorn access logs (if configured)
tail -f /tmp/gunicorn-access.log

# Gunicorn error logs (if configured)
tail -f /tmp/gunicorn-error.log

# Check process status
ps aux | grep gunicorn
```

## Environment Variables
Located in: `/home/opc/Desktop/Voice2Note/.env`

```bash
SECRET_KEY=<generated-secure-key>
DEBUG=False
HOST=0.0.0.0
PORT=5000
WHISPER_MODEL=large-v3
MAX_UPLOAD_SIZE=1000
OLLAMA_API_KEY=<your-api-key>
```

## Paths
- **Application Root**: `/home/opc/Desktop/Voice2Note`
- **Virtual Environment**: `/home/opc/Desktop/Voice2Note/venv`
- **Database**: `/home/opc/Desktop/Voice2Note/voice2note.db`
- **Whisper Binary**: `/home/opc/Desktop/Voice2Note/Whisper/build/bin/whisper-cli`
- **Whisper Models**: `/home/opc/Desktop/Voice2Note/Whisper/models/`
- **Temp Files**: `/home/opc/Desktop/Voice2Note/temp/`

## Access from Tailscale Devices
All devices on your Tailscale network can access the application:

- **Laptops**: http://100.123.132.122:5000
- **Phones**: http://100.123.132.122:5000
- **Tablets**: http://100.123.132.122:5000

Or using hostname (if MagicDNS enabled):
- http://rainydaze:5000

## Troubleshooting

### Can't Access Application
1. Check if server is running: `ps aux | grep gunicorn | grep 5000`
2. Check firewall: `sudo firewall-cmd --list-all`
3. Check Tailscale: `tailscale status`
4. Test locally: `curl http://localhost:5000`

### Application Not Starting
1. Check if port is in use: `sudo lsof -i :5000`
2. Check virtual environment: `which python` (should show venv path)
3. Check database: `ls -l voice2note.db`
4. Check whisper.cpp: `ls -l Whisper/build/bin/whisper-cli`

### Slow Processing
1. Check system resources: `htop` or `top`
2. Check model size: `ls -lh Whisper/models/`
3. Consider using medium model for faster processing
4. Check number of concurrent videos being processed

## Backup & Maintenance

### Backup Database
```bash
cp voice2note.db voice2note.db.backup.$(date +%Y%m%d_%H%M%S)
```

### Clean Temp Files
```bash
# Remove temp files older than 7 days
find /home/opc/Desktop/Voice2Note/temp -type f -mtime +7 -delete
```

### Update Application
```bash
cd /home/opc/Desktop/Voice2Note
git pull
source venv/bin/activate
pip install -r requirements.txt
# Restart server
pkill -f "gunicorn.*5000.*app:app"
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 1800 app:app --daemon
```

## Deployment Date
- **Initial Deployment**: November 11, 2025
- **Last Updated**: November 11, 2025
