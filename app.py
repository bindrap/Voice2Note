from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
import os
import traceback
from werkzeug.utils import secure_filename
from functools import wraps
import threading
from config import Config
from database.db_manager import DatabaseManager
from processors.video_handler import VideoHandler
from processors.transcriber import Transcriber
from processors.note_generator import NoteGenerator

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Initialize components
Config.init_app()
db = DatabaseManager()
video_handler = VideoHandler()
transcriber = Transcriber()
note_generator = NoteGenerator()

# Track active processing threads
active_processes = {}  # {video_id: {'thread': thread_obj, 'cancel': threading.Event()}}
process_lock = threading.Lock()


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# Context processor to make current_user available in templates
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = db.get_user_by_id(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}


# ===== Authentication Routes =====

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')

        if not email or '@' not in email:
            return render_template('register.html', error='Invalid email address')

        if not password or len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        # Check if username or email already exists
        if db.get_user_by_username(username):
            return render_template('register.html', error='Username already taken')

        if db.get_user_by_email(email):
            return render_template('register.html', error='Email already registered')

        # Create user
        user_id = db.create_user(username, email, password)
        if user_id:
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            return render_template('register.html', error='Registration failed')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login.html', error='Username and password are required')

        user = db.verify_password(username, password)
        if user:
            session['user_id'] = user['id']
            db.update_last_login(user['id'])
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = db.get_user_by_id(session['user_id'])
    stats = db.get_user_statistics(session['user_id'])
    recent_videos = db.get_user_videos(session['user_id'], limit=5)

    return render_template('profile.html', user=user, stats=stats, recent_videos=recent_videos)


# ===== Main Application Routes =====

@app.route('/')
@login_required
def index():
    """Main page"""
    stats = db.get_user_statistics(session['user_id'])
    return render_template('index.html', stats=stats)


@app.route('/history')
@login_required
def history():
    """View processing history"""
    videos = db.get_user_videos(session['user_id'], limit=50)
    return render_template('history.html', videos=videos)


def process_video_background(video_id, source, is_file, file_path, cancel_event):
    """Background task to process video"""
    try:
        # Step 1: Extract audio (10-30%)
        print(f"\n{'='*50}")
        print(f"STEP 1: Extracting audio [Video ID: {video_id}]")
        print(f"{'='*50}")

        db.update_processing_status(video_id, 'extracting', progress=10)

        # Check for cancellation
        if cancel_event.is_set():
            raise Exception("Processing cancelled by user")

        # Progress: Processing source
        db.update_processing_status(video_id, 'extracting', progress=15)

        metadata = video_handler.process_source(
            source,
            is_file=is_file,
            file_path=file_path
        )

        # Progress: Audio extracted
        db.update_processing_status(video_id, 'extracting', progress=25)

        # Check for cancellation
        if cancel_event.is_set():
            video_handler.cleanup_audio(metadata.get('audio_path'))
            raise Exception("Processing cancelled by user")

        # Update video metadata
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE videos
            SET title = ?, creator = ?, duration = ?, source_url = ?
            WHERE id = ?
        ''', (metadata['title'], metadata.get('channel'), metadata.get('duration'),
              metadata.get('url'), video_id))
        conn.commit()
        conn.close()

        # Progress: Metadata saved
        db.update_processing_status(video_id, 'extracting', progress=28)

        db.update_processing_status(video_id, 'transcribing', progress=30)

        # Step 2: Transcribe audio (30-60%)
        print(f"\n{'='*50}")
        print(f"STEP 2: Transcribing audio [Video ID: {video_id}]")
        print(f"{'='*50}")

        # Check for cancellation
        if cancel_event.is_set():
            video_handler.cleanup_audio(metadata['audio_path'])
            raise Exception("Processing cancelled by user")

        # Progress: Loading transcription model
        db.update_processing_status(video_id, 'transcribing', progress=35)

        # Progress: Starting transcription
        db.update_processing_status(video_id, 'transcribing', progress=40)

        transcript_result = transcriber.transcribe(metadata['audio_path'])
        transcript_text = transcript_result['transcript_text']

        # Progress: Transcription complete
        db.update_processing_status(video_id, 'transcribing', progress=55)

        # Check for cancellation
        if cancel_event.is_set():
            video_handler.cleanup_audio(metadata['audio_path'])
            raise Exception("Processing cancelled by user")

        # Save transcript
        db.create_transcript(
            video_id,
            transcript_text,
            transcript_result.get('timestamps')
        )

        # Progress: Transcript saved
        db.update_processing_status(video_id, 'transcribing', progress=58)

        db.update_processing_status(video_id, 'generating', progress=60)

        # Step 3: Generate notes (60-100%)
        print(f"\n{'='*50}")
        print(f"STEP 3: Generating notes [Video ID: {video_id}]")
        print(f"{'='*50}")

        # Check for cancellation
        if cancel_event.is_set():
            video_handler.cleanup_audio(metadata['audio_path'])
            raise Exception("Processing cancelled by user")

        # Progress: Analyzing transcript
        db.update_processing_status(video_id, 'generating', progress=70)

        # Progress: Generating notes
        db.update_processing_status(video_id, 'generating', progress=80)

        notes = note_generator.generate_notes(transcript_text, metadata)

        # Progress: Formatting notes
        db.update_processing_status(video_id, 'generating', progress=90)

        # Check for cancellation
        if cancel_event.is_set():
            video_handler.cleanup_audio(metadata['audio_path'])
            raise Exception("Processing cancelled by user")

        # Save notes
        db.create_notes(video_id, notes)

        # Progress: Saving notes
        db.update_processing_status(video_id, 'generating', progress=95)

        db.update_processing_status(video_id, 'completed', progress=100)

        # Cleanup
        video_handler.cleanup_audio(metadata['audio_path'])
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        print(f"\n{'='*50}")
        print(f"✓ Processing completed successfully! [Video ID: {video_id}]")
        print(f"{'='*50}\n")

    except Exception as e:
        error_msg = str(e)
        is_cancelled = "cancelled" in error_msg.lower()

        print(f"\n❌ {'Cancelled' if is_cancelled else 'Error'} processing video {video_id}: {error_msg}")
        if not is_cancelled:
            traceback.print_exc()

        db.update_processing_status(
            video_id,
            'cancelled' if is_cancelled else 'failed',
            progress=0,
            error_message=error_msg
        )
    finally:
        # Remove from active processes
        with process_lock:
            if video_id in active_processes:
                del active_processes[video_id]


@app.route('/process', methods=['POST'])
@login_required
def process():
    """Process video/audio from URL or upload - starts background processing"""
    try:
        # Get input source
        youtube_url = request.form.get('youtube_url', '').strip()
        uploaded_file = request.files.get('video_file')

        if not youtube_url and not uploaded_file:
            return jsonify({'success': False, 'error': 'No input provided'}), 400

        # Determine source
        is_file = uploaded_file and uploaded_file.filename
        source_type = 'local' if is_file else 'youtube'

        # Handle file upload
        file_path = None
        if is_file:
            if not allowed_file(uploaded_file.filename):
                return jsonify({'success': False, 'error': 'Invalid file type'}), 400

            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(Config.TEMP_DIR, filename)
            uploaded_file.save(file_path)
            source = filename
        else:
            source = youtube_url

        # Create video record
        video_id = db.create_video(
            user_id=session['user_id'],
            source_url=source if source_type == 'youtube' else None,
            source_type=source_type,
            title='Processing...',
        )

        # Initialize processing status
        db.update_processing_status(video_id, 'pending', progress=5)

        # Create cancel event and start background processing
        cancel_event = threading.Event()
        thread = threading.Thread(
            target=process_video_background,
            args=(video_id, source, is_file, file_path, cancel_event),
            daemon=True
        )

        # Track the thread
        with process_lock:
            active_processes[video_id] = {
                'thread': thread,
                'cancel': cancel_event
            }

        thread.start()

        print(f"✓ Started background processing for video {video_id}")

        # Return immediately
        return jsonify({
            'success': True,
            'video_id': video_id,
            'message': 'Processing started in background. You can navigate away and check progress later.',
            'processing': True
        })

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        traceback.print_exc()

        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/notes/<int:video_id>')
@login_required
def view_notes(video_id):
    """View generated notes"""
    video = db.get_video(video_id)
    notes = db.get_notes(video_id)

    # Verify ownership
    if not video or not notes or video['user_id'] != session['user_id']:
        return "Notes not found", 404

    return render_template('notes.html', video=video, notes=notes)


@app.route('/download/<int:video_id>')
@login_required
def download_notes(video_id):
    """Download notes as markdown file"""
    video = db.get_video(video_id)
    notes = db.get_notes(video_id)

    # Verify ownership
    if not video or not notes or video['user_id'] != session['user_id']:
        return "Notes not found", 404

    # Save to temp file
    filename = f"{video['title']}.md".replace('/', '-')
    temp_file = os.path.join(Config.TEMP_DIR, filename)

    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(notes['content'])

    return send_file(
        temp_file,
        as_attachment=True,
        download_name=filename,
        mimetype='text/markdown'
    )


@app.route('/status/<int:video_id>')
@login_required
def get_status(video_id):
    """Get processing status"""
    # Verify ownership
    video = db.get_video(video_id)
    if not video or video['user_id'] != session['user_id']:
        return jsonify({'status': 'unknown', 'progress': 0}), 404

    status = db.get_processing_status(video_id)

    if not status:
        return jsonify({'status': 'unknown', 'progress': 0})

    return jsonify({
        'status': status['status'],
        'progress': status['progress'],
        'error_message': status.get('error_message')
    })


@app.route('/api/videos')
@login_required
def api_videos():
    """API endpoint to get all videos"""
    videos = db.get_user_videos(session['user_id'], limit=50)
    return jsonify(videos)


@app.route('/api/search')
@login_required
def api_search():
    """API endpoint to search videos"""
    query = request.args.get('q', '')
    user_id = session['user_id']

    # Get user's videos and filter by query
    videos = db.get_user_videos(user_id, limit=100)
    filtered = [v for v in videos if query.lower() in v['title'].lower() or
                (v.get('creator') and query.lower() in v['creator'].lower())]
    return jsonify(filtered)


@app.route('/cancel/<int:video_id>', methods=['POST'])
@login_required
def cancel_processing(video_id):
    """Cancel processing of a video"""
    try:
        # Verify ownership
        video = db.get_video(video_id)
        if not video or video['user_id'] != session['user_id']:
            return jsonify({'success': False, 'error': 'Video not found'}), 404

        # Check database status first
        status = db.get_processing_status(video_id)
        if not status:
            return jsonify({'success': False, 'error': 'No processing status found'}), 404

        # Check if video is in a cancellable state
        processing_states = ['pending', 'extracting', 'transcribing', 'generating']
        if status['status'] not in processing_states:
            return jsonify({'success': False, 'error': f'Cannot cancel video with status: {status["status"]}'}), 400

        # Try to cancel active thread if it exists
        with process_lock:
            if video_id in active_processes:
                # Set cancel flag for active thread
                active_processes[video_id]['cancel'].set()

                # Immediately update database status to prevent duplicate cancellations
                db.update_processing_status(video_id, 'cancelled', progress=0,
                                          error_message='Cancelled by user')

                # Remove from active processes immediately
                del active_processes[video_id]

                print(f"✓ Cancelled active thread for video {video_id}")
                return jsonify({'success': True, 'message': 'Processing cancelled'})
            else:
                # Thread reference lost (server restart, crashed thread, etc.)
                # Directly update database to mark as cancelled
                db.update_processing_status(video_id, 'cancelled', progress=0,
                                          error_message='Cancelled by user (thread reference lost)')
                print(f"✓ Marked video {video_id} as cancelled in database (no active thread found)")
                return jsonify({'success': True, 'message': 'Processing cancelled (thread was not found, status updated)'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/restart/<int:video_id>', methods=['POST'])
@login_required
def restart_processing(video_id):
    """Restart processing of a failed or cancelled video"""
    try:
        # Verify ownership
        video = db.get_video(video_id)
        if not video or video['user_id'] != session['user_id']:
            return jsonify({'success': False, 'error': 'Video not found'}), 404

        # Check if video can be restarted
        status = db.get_processing_status(video_id)
        if status and status['status'] not in ['failed', 'cancelled']:
            return jsonify({'success': False, 'error': 'Can only restart failed or cancelled videos'}), 400

        # Determine source
        source = video['source_url'] or video['title']  # Use title as fallback for local files
        source_type = video['source_type']
        is_file = source_type == 'local'
        file_path = None  # For restarts, we'll need to re-download/upload

        if is_file:
            return jsonify({'success': False, 'error': 'Cannot restart local file uploads - please re-upload the file'}), 400

        # Reset processing status
        db.update_processing_status(video_id, 'pending', progress=5)

        # Start background processing
        cancel_event = threading.Event()
        thread = threading.Thread(
            target=process_video_background,
            args=(video_id, source, is_file, file_path, cancel_event),
            daemon=True
        )

        # Track the thread
        with process_lock:
            active_processes[video_id] = {
                'thread': thread,
                'cancel': cancel_event
            }

        thread.start()

        print(f"✓ Restarted processing for video {video_id}")

        return jsonify({'success': True, 'message': 'Processing restarted', 'video_id': video_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/delete/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    """Delete a video and its notes"""
    try:
        # Verify ownership
        video = db.get_video(video_id)
        if not video or video['user_id'] != session['user_id']:
            return jsonify({'success': False, 'error': 'Video not found'}), 404

        # Cancel if currently processing
        with process_lock:
            if video_id in active_processes:
                active_processes[video_id]['cancel'].set()

        db.delete_video(video_id)
        return jsonify({'success': True, 'message': 'Video deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize database if needed or if schema is outdated
    import sqlite3
    needs_init = False

    if not os.path.exists(Config.DATABASE_PATH):
        print("Database not found. Initializing...")
        needs_init = True
    else:
        # Check if users table exists (new schema requirement)
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("Old database schema detected. Reinitializing...")
                needs_init = True
            conn.close()
        except Exception as e:
            print(f"Error checking database: {e}")
            needs_init = True

    if needs_init:
        # Backup old database if it exists
        if os.path.exists(Config.DATABASE_PATH):
            from datetime import datetime
            backup_path = f"{Config.DATABASE_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy(Config.DATABASE_PATH, backup_path)
            print(f"✓ Backed up old database to: {backup_path}")
            os.remove(Config.DATABASE_PATH)

        db.init_database()
        print("✓ Database initialized with new schema")

    print(f"\n{'='*60}")
    print("Voice2Note Application Starting")
    print(f"{'='*60}")
    print(f"Database: {Config.DATABASE_PATH}")
    print(f"Temp directory: {Config.TEMP_DIR}")
    print(f"Notes directory: {Config.NOTES_DIR}")
    print(f"Whisper model: {Config.WHISPER_MODEL}")
    print(f"Ollama model: {Config.OLLAMA_MODEL}")
    print(f"{'='*60}\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
