# How to Export YouTube Cookies for Bot-Protected Videos

Some YouTube videos require authentication cookies to bypass bot detection. If you encounter "Sign in to confirm you're not a bot" errors, follow these steps to export your YouTube cookies.

## Method 1: Using Browser Extension (Easiest)

### For Chrome/Edge/Brave

1. Install the extension **"Get cookies.txt LOCALLY"**
   - Chrome Web Store: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. Visit YouTube.com and **sign in** to your account

3. Click the extension icon in your browser toolbar

4. Click **"Export"** button

5. Save the file as `cookies.txt` in the Voice2Note project root directory:
   ```
   /home/opc/Desktop/Voice2Note/cookies.txt
   ```

### For Firefox

1. Install the extension **"cookies.txt"**
   - Firefox Add-ons: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. Visit YouTube.com and **sign in** to your account

3. Click the extension icon in your toolbar

4. Click **"Export cookies.txt"**

5. Save the file as `cookies.txt` in the Voice2Note project root directory

## Method 2: Using yt-dlp Command (Advanced)

If you have Chrome/Firefox installed and logged into YouTube:

```bash
# For Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# For Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

This will create a `cookies.txt` file that you can reuse.

## Important Notes

1. **Privacy**: The cookies.txt file contains your authentication tokens. Keep it secure and don't share it.

2. **Expiration**: Cookies expire over time (usually days to weeks). If downloads stop working, export fresh cookies.

3. **File Location**: The app automatically looks for `cookies.txt` in:
   ```
   /home/opc/Desktop/Voice2Note/cookies.txt
   ```

4. **Gitignore**: cookies.txt is already in .gitignore, so it won't be committed to git.

## Testing

After adding cookies.txt, test with a video:

```bash
source venv/bin/activate
python -c "
from processors.video_handler import VideoHandler
vh = VideoHandler()
result = vh.download_youtube_audio('https://www.youtube.com/watch?v=YOUR_VIDEO_ID')
print(f'Success! Downloaded: {result[\"title\"]}')
"
```

## Troubleshooting

**"ERROR: Sign in to confirm you're not a bot"**
- Solution: Export fresh cookies using Method 1 above

**"Cookies file not found"**
- Make sure the file is named exactly `cookies.txt` (all lowercase)
- Check the file is in the correct directory: `/home/opc/Desktop/Voice2Note/`

**Downloads work without cookies.txt**
- Great! Most videos don't need cookies. Only bot-protected videos require them.

## On Phone (Android)

If you're accessing from your phone:

1. Use a browser on your phone to access YouTube
2. Install the extension (if supported) or use method 2
3. Transfer the cookies.txt file to your server using:
   ```bash
   # On phone (Termux)
   scp cookies.txt opc@your-server:/home/opc/Desktop/Voice2Note/cookies.txt
   ```
