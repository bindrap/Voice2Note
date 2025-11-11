# Quick Start: Deploy Voice2Note on Tailscale Network

Get Voice2Note running on your Tailscale network in under 5 minutes!

## Prerequisites Checklist

- ✅ Server with 24GB RAM (Oracle VM)
- ✅ Python 3.8+ installed
- ✅ Tailscale installed on server
- ✅ Voice2Note repository cloned

## 5-Minute Setup

### Step 1: Install Tailscale (1 minute)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Get your Tailscale IP:
```bash
tailscale ip -4
# Example output: 100.64.1.100
```

### Step 2: Set Up Python Environment (2 minutes)

```bash
cd Voice2Note

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Gunicorn for production
pip install gunicorn
```

### Step 3: Configure for Production (1 minute)

```bash
# Generate secure secret key
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Set production mode
export DEBUG=False

# For 24GB RAM: increase upload limit to 2GB
export MAX_UPLOAD_SIZE=2000

# Save to your shell profile for persistence
echo "export SECRET_KEY=\"$SECRET_KEY\"" >> ~/.bashrc
echo "export DEBUG=False" >> ~/.bashrc
echo "export MAX_UPLOAD_SIZE=2000" >> ~/.bashrc
```

### Step 4: Initialize Database (30 seconds)

```bash
python init_db.py
```

You should see:
```
✓ Database initialized successfully!
```

### Step 5: Start Voice2Note (30 seconds)

```bash
# Quick test (development mode)
python app.py

# OR: Production mode with the startup script
./start-production.sh

# OR: Production with Gunicorn directly
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 600 app:app
```

## Access Voice2Note

### From Your Tailscale Network

Open in your browser:
```
http://<your-tailscale-ip>:5000
```

Example:
```
http://100.64.1.100:5000
```

### Enable HTTPS (Optional but Recommended)

```bash
# Use Tailscale's built-in HTTPS
tailscale serve --bg https / http://localhost:5000
```

Now access at:
```
https://<your-server-name>
```

## Auto-Start on Boot (Optional)

Create a systemd service:

```bash
# Quick setup
cat > /tmp/voice2note.service << EOF
[Unit]
Description=Voice2Note Application
After=network.target tailscaled.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Voice2Note
Environment="SECRET_KEY=$SECRET_KEY"
Environment="DEBUG=False"
Environment="PATH=$HOME/Voice2Note/venv/bin:/usr/bin:/bin"
ExecStart=$HOME/Voice2Note/venv/bin/gunicorn -w 8 -b 0.0.0.0:5000 --timeout 600 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Install and start
sudo mv /tmp/voice2note.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice2note
sudo systemctl start voice2note
```

Check status:
```bash
sudo systemctl status voice2note
```

## Share with Your Team

Send this to your team members:

```
Voice2Note is ready! 🎉

Access: http://100.x.x.x:5000
(or https://server-name if using Tailscale Serve)

1. Install Tailscale: https://tailscale.com/download
2. Join our network (use the invite link)
3. Open the URL above
4. Click "Register" to create your account
5. Start uploading videos!

Features:
- Upload YouTube URLs or video files
- Get AI-enhanced notes automatically
- Background processing (navigate away anytime)
- Your own private workspace
```

## Verify Everything Works

1. **Access the web interface** at your Tailscale IP
2. **Register a test account**
3. **Upload a short test video** (or YouTube URL)
4. **Check History page** - you should see real-time progress
5. **Wait for completion** - processing happens in background
6. **View notes** - click "View Notes" when done

## Next Steps

- ✅ Read [TAILSCALE_DEPLOYMENT.md](TAILSCALE_DEPLOYMENT.md) for detailed configuration
- ✅ Configure large Whisper model for 24GB RAM (see README.md)
- ✅ Set up automated backups
- ✅ Share access with team members

## Troubleshooting

**Can't access from Tailscale?**
```bash
# Check if service is running
sudo systemctl status voice2note

# Check Tailscale connection
tailscale status

# Test local access
curl http://localhost:5000
```

**Port already in use?**
```bash
# Find what's using the port
sudo lsof -i :5000

# Kill it
sudo kill $(sudo lsof -t -i:5000)
```

**Errors in logs?**
```bash
# View live logs
sudo journalctl -u voice2note -f
```

## Performance Tips for 24GB RAM

Your Oracle VM can handle heavy workloads:

1. **Use 8 workers** (already configured in startup script)
2. **Use large Whisper model** for best quality
3. **Increase upload limit** to 2GB (already set above)
4. **Multiple concurrent users** - can handle 4-8 users processing videos simultaneously

## That's It!

You now have Voice2Note running on your Tailscale network! 🚀

Access it from any device on your Tailnet and start converting videos to notes.

---

**Need help?** Check [TAILSCALE_DEPLOYMENT.md](TAILSCALE_DEPLOYMENT.md) for detailed docs.
