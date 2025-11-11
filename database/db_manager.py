import sqlite3
import json
from datetime import datetime
from config import Config


class DatabaseManager:
    """Manages database operations for Voice2Note"""

    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def init_database(self):
        """Initialize database with schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Read and execute schema
        with open('database/schema.sql', 'r') as f:
            schema = f.read()
            cursor.executescript(schema)

        conn.commit()
        conn.close()
        print(f"Database initialized at: {self.db_path}")

    def create_video(self, source_url, source_type, title, creator=None, duration=None):
        """Create a new video record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO videos (source_url, source_type, title, creator, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (source_url, source_type, title, creator, duration))

        video_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return video_id

    def create_transcript(self, video_id, transcript_text, timestamps=None):
        """Create a transcript record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        timestamps_json = json.dumps(timestamps) if timestamps else None

        cursor.execute('''
            INSERT INTO transcripts (video_id, transcript_text, timestamps)
            VALUES (?, ?, ?)
        ''', (video_id, transcript_text, timestamps_json))

        transcript_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return transcript_id

    def create_notes(self, video_id, content, format='markdown'):
        """Create a notes record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notes (video_id, content, format)
            VALUES (?, ?, ?)
        ''', (video_id, content, format))

        notes_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return notes_id

    def update_processing_status(self, video_id, status, progress=None, error_message=None):
        """Update or create processing status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if status exists
        cursor.execute('SELECT id FROM processing_status WHERE video_id = ?', (video_id,))
        existing = cursor.fetchone()

        if existing:
            # Update existing
            cursor.execute('''
                UPDATE processing_status
                SET status = ?, progress = ?, error_message = ?, updated_at = ?
                WHERE video_id = ?
            ''', (status, progress, error_message, datetime.now(), video_id))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO processing_status (video_id, status, progress, error_message)
                VALUES (?, ?, ?, ?)
            ''', (video_id, status, progress, error_message))

        conn.commit()
        conn.close()

    def get_video(self, video_id):
        """Get video by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
        video = cursor.fetchone()

        conn.close()
        return dict(video) if video else None

    def get_notes(self, video_id):
        """Get notes for a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM notes WHERE video_id = ?', (video_id,))
        notes = cursor.fetchone()

        conn.close()
        return dict(notes) if notes else None

    def get_transcript(self, video_id):
        """Get transcript for a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM transcripts WHERE video_id = ?', (video_id,))
        transcript = cursor.fetchone()

        conn.close()
        return dict(transcript) if transcript else None

    def get_processing_status(self, video_id):
        """Get processing status for a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM processing_status WHERE video_id = ?', (video_id,))
        status = cursor.fetchone()

        conn.close()
        return dict(status) if status else None

    def get_all_videos(self, limit=50, offset=0):
        """Get all videos with pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT v.*, n.id as notes_id, ps.status as processing_status
            FROM videos v
            LEFT JOIN notes n ON v.id = n.video_id
            LEFT JOIN processing_status ps ON v.id = ps.video_id
            ORDER BY v.processed_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        videos = cursor.fetchall()
        conn.close()

        return [dict(video) for video in videos]

    def search_videos(self, query):
        """Search videos by title or creator"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT v.*, n.id as notes_id
            FROM videos v
            LEFT JOIN notes n ON v.id = n.video_id
            WHERE v.title LIKE ? OR v.creator LIKE ?
            ORDER BY v.processed_date DESC
        ''', (f'%{query}%', f'%{query}%'))

        videos = cursor.fetchall()
        conn.close()

        return [dict(video) for video in videos]

    def delete_video(self, video_id):
        """Delete a video and all related data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))

        conn.commit()
        conn.close()
