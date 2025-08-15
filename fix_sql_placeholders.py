#!/usr/bin/env python3
"""
Script to fix SQL placeholder issues in db.py
"""

import re

def fix_sql_placeholders():
    """Fix SQL placeholder issues in db.py"""
    
    # Read the file
    with open('db.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all cursor.execute calls with self.execute_query
    # Pattern: cursor.execute(query, values) -> self.execute_query(cursor, query, values)
    content = re.sub(
        r'cursor\.execute\(query, values\)',
        'self.execute_query(cursor, query, values)',
        content
    )
    
    # Replace all cursor.execute calls with parameters with self.execute_query
    # Pattern: cursor.execute("SELECT ... WHERE id = %s", (search_id,)) -> self.execute_query(cursor, "SELECT ... WHERE id = %s", (search_id,))
    content = re.sub(
        r'cursor\.execute\(("""[\s\S]*?"""), \(([^)]+)\)\)',
        r'self.execute_query(cursor, \1, (\2))',
        content
    )
    
    # Replace simple cursor.execute calls
    content = re.sub(
        r'cursor\.execute\("([^"]*)"\)',
        r'self.execute_query(cursor, "\1")',
        content
    )
    
    # Write back to file
    with open('db.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ SQL placeholder fixes applied to db.py")

if __name__ == '__main__':
    fix_sql_placeholders()
