#!/usr/bin/env python3
"""
Database backup script - engine agnostic
"""
import os
import sys
import subprocess
from datetime import datetime
from urllib.parse import urlparse
import shutil


def create_backup_dir():
    """Create backup directory if it doesn't exist"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups', 'db')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def backup_postgresql(database_url, backup_path):
    """Backup PostgreSQL database using pg_dump"""
    parsed_url = urlparse(database_url)
    
    # Set environment variables for pg_dump
    env = os.environ.copy()
    env['PGPASSWORD'] = parsed_url.password or ''
    
    # Build pg_dump command
    cmd = [
        'pg_dump',
        '-h', parsed_url.hostname or 'localhost',
        '-p', str(parsed_url.port or 5432),
        '-U', parsed_url.username or 'postgres',
        '-d', parsed_url.path.lstrip('/'),
        '--verbose',
        '--clean',
        '--if-exists',
        '--create',
        '--format=custom',
        '--file', backup_path
    ]
    
    try:
        print(f"Starting PostgreSQL backup to {backup_path}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL backup completed successfully")
            print(f"Backup size: {os.path.getsize(backup_path) / 1024 / 1024:.2f} MB")
            return True
        else:
            print("❌ PostgreSQL backup failed:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ pg_dump not found. Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL backup error: {e}")
        return False


def backup_sqlite(database_url, backup_path):
    """Backup SQLite database by copying the file"""
    try:
        # Extract file path from URL
        if database_url.startswith('sqlite:///'):
            db_path = database_url[10:]  # Remove 'sqlite:///'
        elif database_url.startswith('sqlite://'):
            db_path = database_url[9:]   # Remove 'sqlite://'
        else:
            db_path = database_url
        
        if not os.path.exists(db_path):
            print(f"❌ SQLite database file not found: {db_path}")
            return False
        
        print(f"Starting SQLite backup: {db_path} -> {backup_path}")
        shutil.copy2(db_path, backup_path)
        
        print("✅ SQLite backup completed successfully")
        print(f"Backup size: {os.path.getsize(backup_path) / 1024 / 1024:.2f} MB")
        return True
        
    except Exception as e:
        print(f"❌ SQLite backup error: {e}")
        return False


def backup_mysql(database_url, backup_path):
    """Backup MySQL database using mysqldump"""
    parsed_url = urlparse(database_url)
    
    cmd = [
        'mysqldump',
        '-h', parsed_url.hostname or 'localhost',
        '-P', str(parsed_url.port or 3306),
        '-u', parsed_url.username or 'root',
        f'-p{parsed_url.password}' if parsed_url.password else '',
        '--single-transaction',
        '--routines',
        '--triggers',
        parsed_url.path.lstrip('/'),
    ]
    
    try:
        print(f"Starting MySQL backup to {backup_path}")
        
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print("✅ MySQL backup completed successfully")
            print(f"Backup size: {os.path.getsize(backup_path) / 1024 / 1024:.2f} MB")
            return True
        else:
            print("❌ MySQL backup failed:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ mysqldump not found. Please install MySQL client tools.")
        return False
    except Exception as e:
        print(f"❌ MySQL backup error: {e}")
        return False


def main():
    """Main backup function"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Create backup directory
    backup_dir = create_backup_dir()
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Determine database type and backup accordingly
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        backup_filename = f"postgresql_backup_{timestamp}.dump"
        backup_path = os.path.join(backup_dir, backup_filename)
        success = backup_postgresql(database_url, backup_path)
        
    elif database_url.startswith('sqlite'):
        backup_filename = f"sqlite_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        success = backup_sqlite(database_url, backup_path)
        
    elif database_url.startswith('mysql://'):
        backup_filename = f"mysql_backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        success = backup_mysql(database_url, backup_path)
        
    else:
        print(f"❌ Unsupported database type in URL: {database_url}")
        sys.exit(1)
    
    if success:
        print(f"\n📁 Backup saved to: {backup_path}")
        
        # Clean up old backups (keep last 7 days)
        cleanup_old_backups(backup_dir, days=7)
        
        print("\n🚀 Backup completed successfully!")
        print("To restore this backup, use:")
        
        if database_url.startswith('postgresql') or database_url.startswith('postgres'):
            print(f"   pg_restore -d <database_name> {backup_path}")
        elif database_url.startswith('sqlite'):
            print(f"   cp {backup_path} <database_file>")
        elif database_url.startswith('mysql'):
            print(f"   mysql -u <user> -p <database_name> < {backup_path}")
            
        sys.exit(0)
    else:
        print("\n❌ Backup failed!")
        sys.exit(1)


def cleanup_old_backups(backup_dir, days=7):
    """Clean up backup files older than specified days"""
    try:
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        removed_count = 0
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                removed_count += 1
        
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old backup files (older than {days} days)")
            
    except Exception as e:
        print(f"⚠️ Warning: Failed to clean up old backups: {e}")


if __name__ == "__main__":
    main()