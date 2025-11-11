-- Voice2Note Database Schema

-- Videos table: stores metadata about processed videos
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT,
    source_type TEXT NOT NULL,  -- 'youtube' or 'local'
    title TEXT NOT NULL,
    creator TEXT,
    duration INTEGER,
    upload_date DATE,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notes table: stores generated markdown notes
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Transcripts table: stores raw transcriptions
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    transcript_text TEXT NOT NULL,
    timestamps TEXT,  -- JSON array of timestamp data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Processing status table: tracks processing progress
CREATE TABLE IF NOT EXISTS processing_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    status TEXT NOT NULL,  -- 'pending', 'extracting', 'transcribing', 'generating', 'completed', 'failed'
    progress INTEGER DEFAULT 0,  -- 0-100
    error_message TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_videos_title ON videos(title);
CREATE INDEX IF NOT EXISTS idx_videos_processed_date ON videos(processed_date DESC);
CREATE INDEX IF NOT EXISTS idx_notes_video ON notes(video_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_video ON transcripts(video_id);
CREATE INDEX IF NOT EXISTS idx_processing_status_video ON processing_status(video_id);
