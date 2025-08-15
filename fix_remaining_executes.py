#!/usr/bin/env python3
"""
Script to fix all remaining cursor.execute calls in db.py
"""

import re

def fix_remaining_executes():
    """Fix all remaining cursor.execute calls in db.py"""
    
    # Read the file
    with open('db.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all remaining cursor.execute calls with self.execute_query
    # Pattern 1: cursor.execute("""...""")
    content = re.sub(
        r'cursor\.execute\("""([\s\S]*?)"""\)',
        r'self.execute_query(cursor, """\1""")',
        content
    )
    
    # Pattern 2: cursor.execute("...")
    content = re.sub(
        r'cursor\.execute\("([^"]*)"\)',
        r'self.execute_query(cursor, "\1")',
        content
    )
    
    # Pattern 3: cursor.execute("...", (...))
    content = re.sub(
        r'cursor\.execute\("([^"]*)", \(([^)]+)\)\)',
        r'self.execute_query(cursor, "\1", (\2))',
        content
    )
    
    # Write back to file
    with open('db.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ All remaining cursor.execute calls fixed in db.py")

if __name__ == '__main__':
    fix_remaining_executes()
