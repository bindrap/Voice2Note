import sqlite3
import json
from datetime import datetime
from config import Config
import hashlib


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

    def create_video(self, user_id, source_url, source_type, title, creator=None, duration=None):
        """Create a new video record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO videos (user_id, source_url, source_type, title, creator, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, source_url, source_type, title, creator, duration))

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

    # ===== User Management Methods =====

    def create_user(self, username, email, password):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        conn.close()
        return dict(user) if user else None

    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        conn.close()
        return dict(user) if user else None

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        conn.close()
        return dict(user) if user else None

    def verify_password(self, username, password):
        """Verify user password"""
        user = self.get_user_by_username(username)
        if not user:
            # Also try email
            user = self.get_user_by_email(username)

        if not user:
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] == password_hash:
            return user
        return None

    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET last_login = ?
            WHERE id = ?
        ''', (datetime.now(), user_id))

        conn.commit()
        conn.close()

    def get_user_statistics(self, user_id):
        """Get statistics for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Count videos
        cursor.execute('SELECT COUNT(*) FROM videos WHERE user_id = ?', (user_id,))
        total_videos = cursor.fetchone()[0]

        # Count notes
        cursor.execute('''
            SELECT COUNT(*) FROM notes n
            JOIN videos v ON n.video_id = v.id
            WHERE v.user_id = ?
        ''', (user_id,))
        total_notes = cursor.fetchone()[0]

        # Count transcripts
        cursor.execute('''
            SELECT COUNT(*) FROM transcripts t
            JOIN videos v ON t.video_id = v.id
            WHERE v.user_id = ?
        ''', (user_id,))
        total_transcripts = cursor.fetchone()[0]

        # Calculate storage (approximate by counting characters)
        cursor.execute('''
            SELECT
                COALESCE(SUM(LENGTH(n.content)), 0) as notes_size,
                COALESCE(SUM(LENGTH(t.transcript_text)), 0) as transcript_size
            FROM videos v
            LEFT JOIN notes n ON v.id = n.video_id
            LEFT JOIN transcripts t ON v.id = t.video_id
            WHERE v.user_id = ?
        ''', (user_id,))
        sizes = cursor.fetchone()
        total_bytes = (sizes[0] or 0) + (sizes[1] or 0)
        storage_mb = round(total_bytes / (1024 * 1024), 2)

        conn.close()

        return {
            'total_videos': total_videos,
            'total_notes': total_notes,
            'total_transcripts': total_transcripts,
            'storage_mb': storage_mb
        }

    def get_user_videos(self, user_id, limit=50, offset=0):
        """Get all videos for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT v.*, n.id as notes_id, ps.status as processing_status
            FROM videos v
            LEFT JOIN notes n ON v.id = n.video_id
            LEFT JOIN processing_status ps ON v.id = ps.video_id
            WHERE v.user_id = ?
            ORDER BY v.processed_date DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))

        videos = cursor.fetchall()
        conn.close()

        return [dict(video) for video in videos]

    # ===== Remember Me Token Methods =====

    def create_remember_token(self, user_id, token, expires_at):
        """Create a remember me token"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO remember_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, token, expires_at))

            token_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return token_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def get_remember_token(self, token):
        """Get remember token and associated user if valid"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT rt.*, u.*
            FROM remember_tokens rt
            JOIN users u ON rt.user_id = u.id
            WHERE rt.token = ? AND rt.expires_at > ?
        ''', (token, datetime.now()))

        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def delete_remember_token(self, token):
        """Delete a specific remember token"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM remember_tokens WHERE token = ?', (token,))

        conn.commit()
        conn.close()

    def delete_user_remember_tokens(self, user_id):
        """Delete all remember tokens for a user (used on logout)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM remember_tokens WHERE user_id = ?', (user_id,))

        conn.commit()
        conn.close()

    def cleanup_expired_tokens(self):
        """Delete all expired remember tokens"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM remember_tokens WHERE expires_at < ?', (datetime.now(),))

        conn.commit()
        conn.close()
