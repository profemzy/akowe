#!/usr/bin/env python3
"""
Fix SQLite compatibility issues in the migrations script.
This script modifies run_migrations.py to handle SQLite database correctly.
"""

import re
import sys
import os
from datetime import datetime

# Backup the original file
def backup_file(file_path):
    """Create a backup of the file before modifying it."""
    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    try:
        with open(file_path, 'r') as source, open(backup_path, 'w') as target:
            target.write(source.read())
        print(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return False

# Main function to fix the migrations script
def fix_migrations_script(file_path):
    """Fix SQLite compatibility issues in the migrations script."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False
    
    # Create backup
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Fix 1: SQLite tables and indices
        content = re.sub(
            r'# Create indexes\s+conn\.execute\(text\("create unique index ix_users_username on public\.users \(username\);\)\)\s+conn\.execute\(text\("create unique index ix_users_email on public\.users \(email\);\)\)',
            '''# Create indexes
            if dialect == 'sqlite':
                conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username);"))
                conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email);"))
            else:
                conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON public.users (username);"))
                conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON public.users (email);"))''',
            content
        )
        
        # Fix 2: Tables with serial/foreign keys for SQLite
        # Add SQLite condition for all table creations
        pattern = r'conn\.execute\(text\("""\s+create table public\.([a-zA-Z_]+)'
        replacement = '''if dialect == 'sqlite':
                conn.execute(text("""
                CREATE TABLE \\1
                '''.replace('\\1', '\\1')  # Escape the replacement
        
        content = re.sub(pattern, replacement, content)
        
        # Add SQLite-compatible variants for all tables with SERIAL
        content = re.sub(
            r'id\s+serial\s+primary key',
            'id INTEGER PRIMARY KEY AUTOINCREMENT' if dialect == 'sqlite' else 'id SERIAL PRIMARY KEY',
            content
        )
        
        # Fix foreign key syntax for SQLite
        content = re.sub(
            r'constraint\s+fk_[a-zA-Z_]+\s+references\s+public\.[a-zA-Z_]+',
            'FOREIGN KEY (user_id) REFERENCES users(id)',
            content
        )
        
        # Fix 3: PostgreSQL "owner" statements
        # Add "if dialect != 'sqlite'" condition around owner statements
        content = re.sub(
            r'alter table public\.[a-zA-Z_]+ owner to akowe_user',
            'if dialect != "sqlite": alter table public.[table] owner to akowe_user',
            content
        )
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(content)
        
        print(f"Successfully updated {file_path} with SQLite compatibility fixes")
        return True
    
    except Exception as e:
        print(f"Error updating file: {e}")
        return False

if __name__ == "__main__":
    file_path = "./run_migrations.py"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    success = fix_migrations_script(file_path)
    sys.exit(0 if success else 1)