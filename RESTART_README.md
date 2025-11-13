# Application Restart Guide

## Quick Restart

After pulling new changes from git or modifying code:

```bash
./restart.sh
```

This script will:
1. ✅ Stop all running Voice2Note processes (port 5000)
2. ✅ Wait for graceful shutdown
3. ✅ Start the application with 8 workers
4. ✅ Verify successful startup

## After Git Pull

```bash
# Pull latest changes
git pull

# Restart to apply changes
./restart.sh
```

## Manual Commands

If you need to manually control the application:

### Stop Application
```bash
pkill -f "gunicorn.*5000"
```

### Start Application
```bash
source venv/bin/activate
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 1800 app:app \
  --error-logfile logs/error.log \
  --access-logfile logs/access.log \
  --daemon
```

### Check Status
```bash
ps aux | grep gunicorn | grep 5000
```

### View Logs
```bash
# Error log
tail -f logs/error.log

# Access log
tail -f logs/access.log

# Startup log
tail -f logs/gunicorn.log
```

## Troubleshooting

### Port Already in Use
If restart fails with "Address already in use":
```bash
# Force kill all processes
pkill -9 -f "gunicorn.*5000"

# Then restart
./restart.sh
```

### Application Won't Start
Check the error log:
```bash
cat logs/error.log
```

Common issues:
- Missing dependencies: `pip install -r requirements.txt`
- Database issues: Check `voice2note.db` exists
- Permission errors: Ensure logs directory is writable

### Check if Application is Responding
```bash
curl http://localhost:5000/
```

Should redirect to `/login` if working correctly.

## Production Notes

- Application runs on port **5000**
- Uses **8 worker processes**
- Timeout set to **1800 seconds** (30 minutes) for long video processing
- Logs stored in `logs/` directory
- SSL/TLS is handled by the port 5008 instance (separate deployment)
