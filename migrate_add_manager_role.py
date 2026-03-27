"""
Migration script to add is_manager column to users table.
Run this script to update the database schema without losing data.
"""

import sqlite3
import os

def migrate_database():
    """Add is_manager column to users table."""
    
    # Database path
    db_path = os.path.join('instance', 'campus_explorer.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Creating new database with updated schema...")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_manager' in columns:
            print("Column 'is_manager' already exists in users table.")
            conn.close()
            return
        
        print("Adding 'is_manager' column to users table...")
        
        # Add the new column with default value False
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN is_manager BOOLEAN DEFAULT 0 NOT NULL
        """)
        
        conn.commit()
        print("✓ Successfully added 'is_manager' column to users table.")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nUpdated table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        print("\n✓ Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"✗ Error: {e}")
        if conn:
            conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add Manager Role")
    print("=" * 60)
    migrate_database()
