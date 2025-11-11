from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import traceback
from werkzeug.utils import secure_filename
from config import Config
from database.db_manager import DatabaseManager
from processors.video_handler import VideoHandler
from processors.transcriber import Transcriber
from processors.note_generator import NoteGenerator

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
Config.init_app()
db = DatabaseManager()
video_handler = VideoHandler()
transcriber = Transcriber()
note_generator = NoteGenerator()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/history')
def history():
    """View processing history"""
    videos = db.get_all_videos(limit=50)
    return render_template('history.html', videos=videos)


@app.route('/process', methods=['POST'])
def process():
    """Process video/audio from URL or upload"""
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
            source_url=source if source_type == 'youtube' else None,
            source_type=source_type,
            title='Processing...',
        )

        # Update status
        db.update_processing_status(video_id, 'extracting', progress=10)

        # Step 1: Extract audio
        print(f"\n{'='*50}")
        print(f"STEP 1: Extracting audio")
        print(f"{'='*50}")

        metadata = video_handler.process_source(
            source,
            is_file=is_file,
            file_path=file_path
        )

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

        db.update_processing_status(video_id, 'transcribing', progress=30)

        # Step 2: Transcribe audio
        print(f"\n{'='*50}")
        print(f"STEP 2: Transcribing audio")
        print(f"{'='*50}")

        transcript_result = transcriber.transcribe(metadata['audio_path'])
        transcript_text = transcript_result['transcript_text']

        # Save transcript
        db.create_transcript(
            video_id,
            transcript_text,
            transcript_result.get('timestamps')
        )

        db.update_processing_status(video_id, 'generating', progress=60)

        # Step 3: Generate notes
        print(f"\n{'='*50}")
        print(f"STEP 3: Generating notes")
        print(f"{'='*50}")

        notes = note_generator.generate_notes(transcript_text, metadata)

        # Save notes
        db.create_notes(video_id, notes)

        db.update_processing_status(video_id, 'completed', progress=100)

        # Cleanup
        video_handler.cleanup_audio(metadata['audio_path'])
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        print(f"\n{'='*50}")
        print(f"✓ Processing completed successfully!")
        print(f"{'='*50}\n")

        return jsonify({
            'success': True,
            'video_id': video_id,
            'title': metadata['title'],
            'message': 'Processing completed successfully!'
        })

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        traceback.print_exc()

        if 'video_id' in locals():
            db.update_processing_status(
                video_id,
                'failed',
                progress=0,
                error_message=error_msg
            )

        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/notes/<int:video_id>')
def view_notes(video_id):
    """View generated notes"""
    video = db.get_video(video_id)
    notes = db.get_notes(video_id)

    if not video or not notes:
        return "Notes not found", 404

    return render_template('notes.html', video=video, notes=notes)


@app.route('/download/<int:video_id>')
def download_notes(video_id):
    """Download notes as markdown file"""
    video = db.get_video(video_id)
    notes = db.get_notes(video_id)

    if not video or not notes:
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
def get_status(video_id):
    """Get processing status"""
    status = db.get_processing_status(video_id)

    if not status:
        return jsonify({'status': 'unknown', 'progress': 0})

    return jsonify({
        'status': status['status'],
        'progress': status['progress'],
        'error_message': status.get('error_message')
    })


@app.route('/api/videos')
def api_videos():
    """API endpoint to get all videos"""
    videos = db.get_all_videos(limit=50)
    return jsonify(videos)


@app.route('/api/search')
def api_search():
    """API endpoint to search videos"""
    query = request.args.get('q', '')
    videos = db.search_videos(query)
    return jsonify(videos)


@app.route('/delete/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    """Delete a video and its notes"""
    try:
        db.delete_video(video_id)
        return jsonify({'success': True, 'message': 'Video deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize database if needed
    if not os.path.exists(Config.DATABASE_PATH):
        print("Initializing database...")
        db.init_database()

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
