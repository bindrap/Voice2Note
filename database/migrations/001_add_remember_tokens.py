#!/usr/bin/env python3
"""
Migration: Add remember_tokens table
Date: 2025-11-13
Description: Adds the remember_tokens table for "Remember Me" login functionality
"""

import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import Config


def upgrade():
    """Apply the migration"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Create remember_tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remember_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_remember_tokens_token ON remember_tokens(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_remember_tokens_user ON remember_tokens(user_id)')

        conn.commit()
        print("✓ Migration 001_add_remember_tokens: SUCCESS")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration 001_add_remember_tokens: FAILED - {e}")
        return False

    finally:
        conn.close()


def downgrade():
    """Revert the migration"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('DROP TABLE IF EXISTS remember_tokens')
        conn.commit()
        print("✓ Migration 001_add_remember_tokens: ROLLED BACK")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration rollback failed - {e}")
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Remember tokens migration')
    parser.add_argument('--downgrade', action='store_true', help='Rollback this migration')
    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()
