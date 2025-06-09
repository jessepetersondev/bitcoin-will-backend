#!/usr/bin/env python3
"""
Database initialization and migration script for Bitcoin Will application
"""

import os
import sys
import time
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be available"""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '3306'))
    db_username = os.getenv('DB_USERNAME', 'root')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_name = os.getenv('DB_NAME', 'railway')
    
    print(f"🔄 Waiting for database at {db_host}:{db_port}...")
    
    for attempt in range(max_retries):
        try:
            # Try to connect to MySQL server (without specifying database first)
            connection = pymysql.connect(
                host=db_host,
                port=db_port,
                user=db_username,
                password=db_password,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            
            # Check if database exists, create if not
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                cursor.execute(f"USE `{db_name}`")
            
            connection.close()
            print(f"✅ Database connection successful after {attempt + 1} attempts")
            return True
            
        except Exception as e:
            print(f"❌ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                print("❌ Failed to connect to database after all retries")
                return False
    
    return False

def create_tables():
    """Create all database tables"""
    try:
        from main import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test database connection
            result = db.session.execute(text('SELECT 1')).fetchone()
            if result:
                print("✅ Database connection test successful")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Starting Bitcoin Will database initialization...")
    
    # Wait for database to be available
    if not wait_for_database():
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    print("🎉 Database initialization completed successfully!")

if __name__ == "__main__":
    main()

