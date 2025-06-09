#!/usr/bin/env python3
"""
Startup script for Bitcoin Will application
Handles database initialization and starts the application
"""

import os
import sys
import time
import subprocess
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

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
            # Try to connect to MySQL server
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

def initialize_database():
    """Initialize database tables"""
    try:
        # Add src directory to path
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
        
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

def start_application():
    """Start the application with Gunicorn"""
    try:
        # Change to src directory
        os.chdir('src')
        
        # Start Gunicorn
        cmd = ['gunicorn', '-c', '../gunicorn.conf.py', 'wsgi:app']
        print(f"🚀 Starting application: {' '.join(cmd)}")
        
        # Execute Gunicorn
        os.execvp('gunicorn', cmd)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🚀 Starting Bitcoin Will application...")
    
    # Wait for database
    if not wait_for_database():
        print("❌ Database not available, exiting...")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("❌ Database initialization failed, exiting...")
        sys.exit(1)
    
    # Start application
    print("🎉 Starting application server...")
    start_application()

if __name__ == "__main__":
    main()

