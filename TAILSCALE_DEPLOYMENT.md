# Voice2Note - Tailscale Network Deployment 🌐

Deploy Voice2Note to your Tailscale network so multiple users can access it from anywhere.

## Quick Start

Your Voice2Note application is **already configured** to work on Tailscale! It's running on `0.0.0.0:5000`, which means it listens on all network interfaces including Tailscale.

## Prerequisites

1. **Tailscale installed** on the server running Voice2Note
2. **Server joined to your Tailnet** (Tailscale network)
3. **Python environment** set up (see main README.md)

## Setup Steps

### 1. Install and Configure Tailscale on Your Server

```bash
# Install Tailscale (Ubuntu/Debian)
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
sudo tailscale up

# Get your Tailscale IP address
tailscale ip -4
# Example output: 100.x.x.x
```

### 2. Configure Production Settings

Edit `config.py` for production use:

```python
# config.py
class Config:
    # Change this for production!
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secure-random-key-here')

    # Disable debug mode in production
    DEBUG = False

    # Optional: Increase file size limit for larger videos
    MAX_CONTENT_LENGTH = 1000 * 1024 * 1024  # 1GB
```

**Generate a secure secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Then set it as an environment variable:
```bash
export SECRET_KEY="your-generated-key-here"
```

### 3. Run Voice2Note for Network Access

#### Option A: Development Mode (Quick Testing)

```bash
# Voice2Note already runs on 0.0.0.0:5000
python app.py
```

Access at: `http://<your-tailscale-ip>:5000`

#### Option B: Production Mode with Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 600 app:app
```

The `--timeout 600` is important for long-running video processing requests.

#### Option C: Production with systemd (Auto-Start on Boot)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/voice2note.service
```

Add this content:

```ini
[Unit]
Description=Voice2Note Application
After=network.target tailscaled.service
Wants=tailscaled.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/Voice2Note
Environment="SECRET_KEY=your-secure-secret-key"
Environment="PATH=/home/your-username/Voice2Note/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/your-username/Voice2Note/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 --timeout 600 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable voice2note
sudo systemctl start voice2note
sudo systemctl status voice2note
```

View logs:
```bash
sudo journalctl -u voice2note -f
```

### 4. Access from Any Device on Your Tailscale Network

Once running, access Voice2Note from **any device on your Tailscale network**:

```
http://<server-tailscale-ip>:5000
```

Example:
```
http://100.64.1.100:5000
```

#### Find Your Server's Tailscale IP

On the server:
```bash
tailscale ip -4
```

Or check your Tailscale admin panel: https://login.tailscale.com/admin/machines

## Tailscale Features for Voice2Note

### 1. MagicDNS (Friendly Names)

Enable MagicDNS in your Tailscale admin panel, then access using hostnames:

```
http://your-server-name:5000
```

### 2. HTTPS with Tailscale Serve (Recommended)

Use Tailscale's built-in HTTPS proxy:

```bash
# Serve Voice2Note over HTTPS via Tailscale
tailscale serve --bg https / http://localhost:5000
```

Now access at: `https://your-server-name`

Benefits:
- ✅ Automatic HTTPS with valid certificates
- ✅ No port number needed
- ✅ Works on all Tailscale devices

### 3. Tailscale Funnel (Optional - External Access)

Share Voice2Note with people NOT on your Tailnet:

```bash
tailscale funnel --bg 5000
```

This creates a public HTTPS URL (e.g., `https://your-server-name.your-tailnet.ts.net`)

⚠️ **Security Warning**: Only use Funnel if you want public access. All users will be able to register accounts.

## Multi-User Configuration

### User Access Control

Voice2Note has built-in user authentication:
- ✅ Each user creates their own account
- ✅ User data is isolated (users only see their own videos)
- ✅ Passwords are hashed with SHA-256

### Recommended Setup for Teams

1. **First user registers** - becomes the first account
2. **Share Tailscale URL** with team members
3. **Team members register** their own accounts
4. Everyone has their own isolated workspace

### Security Best Practices

1. **Use a strong SECRET_KEY** in production
   ```bash
   export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
   ```

2. **Disable DEBUG mode** in production
   ```python
   # config.py
   DEBUG = False
   ```

3. **Use HTTPS** via Tailscale Serve
   ```bash
   tailscale serve --bg https / http://localhost:5000
   ```

4. **Regular backups** of the database
   ```bash
   # Backup script
   cp voice2note.db voice2note.db.backup.$(date +%Y%m%d)
   ```

5. **Use Tailscale ACLs** to restrict access (optional)
   - Configure in Tailscale admin panel
   - Limit which users/devices can access the server

## Firewall Configuration

If you have a firewall enabled:

```bash
# Allow port 5000 (if using direct access)
sudo ufw allow 5000/tcp

# Or just allow Tailscale traffic
sudo ufw allow in on tailscale0
```

## Performance Tips for 24GB Oracle VM

With your 24GB RAM Oracle VM, optimize for multiple concurrent users:

### 1. Use More Gunicorn Workers

```bash
# 8 workers for 24GB RAM
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 600 app:app
```

### 2. Configure Large Whisper Model

```python
# config.py
WHISPER_MODEL = 'large'
WHISPER_MODEL_PATH = '/path/to/whisper.cpp/models/ggml-large.bin'
```

### 3. Increase Upload Limit

```python
# config.py
MAX_CONTENT_LENGTH = 2000 * 1024 * 1024  # 2GB for very long videos
```

## Monitoring and Maintenance

### Check Service Status

```bash
sudo systemctl status voice2note
```

### View Real-Time Logs

```bash
sudo journalctl -u voice2note -f
```

### Restart Service

```bash
sudo systemctl restart voice2note
```

### Check Disk Space

```bash
df -h
du -sh /home/your-username/Voice2Note/temp/*
```

### Clean Up Old Temp Files

```bash
# Remove temp files older than 7 days
find /home/your-username/Voice2Note/temp -type f -mtime +7 -delete
```

## Troubleshooting

### Can't Connect from Tailscale

**Problem**: Unable to access `http://<tailscale-ip>:5000`

**Solutions**:
1. Verify server is running:
   ```bash
   sudo systemctl status voice2note
   # OR if running manually
   ps aux | grep python
   ```

2. Check Tailscale status:
   ```bash
   tailscale status
   ```

3. Test local access first:
   ```bash
   curl http://localhost:5000
   ```

4. Check firewall:
   ```bash
   sudo ufw status
   ```

### Port 5000 Already in Use

**Problem**: `Address already in use: 0.0.0.0:5000`

**Solutions**:
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill the process
sudo kill <PID>

# Or use a different port
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 600 app:app
```

### Users Can't Register/Login

**Problem**: 403 errors or "Invalid CSRF token"

**Solutions**:
1. Make sure SECRET_KEY is set:
   ```bash
   echo $SECRET_KEY
   ```

2. Access via HTTPS (Tailscale Serve):
   ```bash
   tailscale serve --bg https / http://localhost:5000
   ```

### Slow Performance with Multiple Users

**Solutions**:
1. Increase Gunicorn workers:
   ```bash
   gunicorn -w 8 -b 0.0.0.0:5000 --timeout 600 app:app
   ```

2. Use larger Whisper model (with 24GB RAM):
   ```python
   WHISPER_MODEL = 'large'
   ```

3. Monitor resource usage:
   ```bash
   htop  # or top
   ```

## Example: Complete Production Setup

Here's a complete setup for your 24GB Oracle VM:

```bash
# 1. Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 2. Generate secure secret key
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

# 3. Set up Voice2Note service
sudo tee /etc/systemd/system/voice2note.service > /dev/null << EOF
[Unit]
Description=Voice2Note Application
After=network.target tailscaled.service
Wants=tailscaled.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Voice2Note
Environment="SECRET_KEY=$SECRET_KEY"
Environment="PATH=$HOME/Voice2Note/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$HOME/Voice2Note/venv/bin/gunicorn -w 8 -b 0.0.0.0:5000 --timeout 600 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 4. Start service
sudo systemctl daemon-reload
sudo systemctl enable voice2note
sudo systemctl start voice2note

# 5. Enable Tailscale HTTPS
tailscale serve --bg https / http://localhost:5000

# 6. Get your access URL
echo "Access Voice2Note at: https://$(hostname)"
tailscale ip -4
```

## Sharing Access with Your Team

Once deployed, share these instructions with your team:

---

**Voice2Note is now available on our Tailscale network!**

**Access URL**: `https://your-server-name` (or `http://100.x.x.x:5000`)

**Getting Started:**
1. Install Tailscale on your device: https://tailscale.com/download
2. Join our Tailnet (use the invite link sent separately)
3. Open the Voice2Note URL above
4. Click "Register" to create your account
5. Start processing videos!

**Features:**
- ✅ Upload YouTube URLs or local video files
- ✅ Get AI-enhanced notes automatically
- ✅ Processing happens in background
- ✅ Your data is private and isolated
- ✅ Access from any device on our Tailscale network

---

## Backup Strategy

### Automated Daily Backups

```bash
# Create backup script
cat > ~/backup-voice2note.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/voice2note-backups"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y%m%d_%H%M%S)
cp "$HOME/Voice2Note/voice2note.db" "$BACKUP_DIR/voice2note.db.$DATE"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "voice2note.db.*" -mtime +30 -delete

echo "Backup completed: voice2note.db.$DATE"
EOF

chmod +x ~/backup-voice2note.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * $HOME/backup-voice2note.sh") | crontab -
```

## Summary

✅ **Voice2Note is ready for Tailscale deployment!**

**Quick commands:**
```bash
# Start the service
sudo systemctl start voice2note

# Enable HTTPS via Tailscale
tailscale serve --bg https / http://localhost:5000

# Check status
sudo systemctl status voice2note
tailscale status
```

**Access from anywhere on your Tailnet:**
- Via hostname: `https://your-server-name`
- Via IP: `http://100.x.x.x:5000`

**Next steps:**
1. Configure production settings in `config.py`
2. Set up systemd service for auto-start
3. Enable Tailscale Serve for HTTPS
4. Share access with your team!

---

**Need help?** Check the troubleshooting section above or open an issue.
