#!/usr/bin/env python3
"""Initialize the Voice2Note database"""

from database.db_manager import DatabaseManager
from config import Config

if __name__ == '__main__':
    # Initialize directories
    Config.init_app()

    # Initialize database
    db = DatabaseManager()
    db.init_database()

    print("✓ Database initialized successfully!")
