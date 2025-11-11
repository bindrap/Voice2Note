#!/usr/bin/env python3
"""
Reset and reinitialize the database with the new schema
This script will backup the old database (if it exists) and create a new one
"""
import os
import shutil
from datetime import datetime
from config import Config
from database.db_manager import DatabaseManager

def reset_database():
    """Reset the database with new schema"""
    db_path = Config.DATABASE_PATH

    print("="*60)
    print("Voice2Note Database Reset")
    print("="*60)

    # Backup existing database if it exists
    if os.path.exists(db_path):
        backup_name = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"✓ Backing up existing database to: {backup_name}")
        shutil.copy(db_path, backup_name)

        # Remove old database
        os.remove(db_path)
        print(f"✓ Removed old database")
    else:
        print("ℹ No existing database found")

    # Initialize new database
    print("\n✓ Creating new database with updated schema...")
    db = DatabaseManager()
    db.init_database()

    print("\n✓ Database reset complete!")
    print("="*60)
    print("\nYou can now start the application and register a new user.")
    print("Run: python app.py")
    print("="*60)

if __name__ == '__main__':
    reset_database()
