# How to Get Proper YouTube Cookies

Your YouTube cookies need to include authentication tokens from a **logged-in** YouTube session.

## Steps to Export Cookies from Your Phone

### Option 1: Using Termux + yt-dlp (Recommended for Android)

1. **On your phone**, install Termux from F-Droid

2. **Open Termux** and run:
```bash
pkg install python yt-dlp
```

3. **Open YouTube in your phone browser** (Chrome/Firefox) and **make sure you're logged in**

4. **Back in Termux**, run this command to extract cookies from your browser:
```bash
# For Chrome on Android
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# OR for Firefox on Android
yt-dlp --cookies-from-browser firefox --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

5. **Transfer the cookies.txt file** to your server:
```bash
# In Termux
termux-setup-storage
cp cookies.txt ~/storage/downloads/

# Then from your server
scp "path/to/cookies.txt" opc@100.65.235.29:/home/opc/Desktop/Voice2Note/cookies.txt
```

### Option 2: Using Browser Extension (If accessing from computer)

1. **On your computer**, open Chrome/Firefox

2. **Go to YouTube.com and login** to your account

3. **Install the extension**:
   - Chrome: "Get cookies.txt LOCALLY" - https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Firefox: "cookies.txt" - https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

4. **Click the extension icon** while on YouTube.com

5. **Export** and save as `cookies.txt`

6. **Upload to server**:
```bash
scp cookies.txt opc@100.65.235.29:/home/opc/Desktop/Voice2Note/cookies.txt
```

## What Cookies Look Like When Properly Logged In

Your current cookies are missing authentication tokens. A proper cookies.txt should include lines like:

```
.youtube.com	TRUE	/	TRUE	...	SAPISID	...
.youtube.com	TRUE	/	TRUE	...	__Secure-1PAPISID	...
.youtube.com	TRUE	/	TRUE	...	SSID	...
.youtube.com	TRUE	/	TRUE	...	APISID	...
.youtube.com	TRUE	/	TRUE	...	HSID	...
.youtube.com	TRUE	/	TRUE	...	SID	...
```

These authentication cookies are only present when you're **logged into a Google account** on YouTube.

## Testing Your Cookies

After uploading new cookies, test with:

```bash
ssh opc@100.65.235.29
cd /home/opc/Desktop/Voice2Note
source venv/bin/activate

# Test download
python -c "
from processors.video_handler import VideoHandler
vh = VideoHandler()
result = vh.download_youtube_audio('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
print(f'✓ SUCCESS! Downloaded: {result[\"title\"]}')
"
```

## Troubleshooting

**"Sign in to confirm you're not a bot"**
- Your server's IP might be flagged by YouTube
- Solution: Use cookies from a **logged-in** Google account
- The cookies must include authentication tokens (SAPISID, HSID, etc.)

**"Cookies expired"**
- YouTube cookies typically last 1-2 weeks
- Re-export fresh cookies when they expire

**Still not working?**
- Make sure you're exporting cookies from a browser where you're **actively logged in** to YouTube
- Try using a different browser (Chrome vs Firefox)
- Check that cookies.txt has proper tab separation (not spaces)

## Current Status

Your app is working correctly! The issue is just that:
1. ✅ yt-dlp is updated to latest version (2025.10.14)
2. ✅ Code has fallback strategies for different video types
3. ✅ cookies.txt support is implemented
4. ⚠️ Need authenticated YouTube cookies from a logged-in session

Once you upload properly authenticated cookies, the downloads will work!
