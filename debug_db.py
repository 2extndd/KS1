#!/usr/bin/env python3
import sqlite3
import json

# Connect to database
conn = sqlite3.connect('kufar_notifications.db')
cursor = conn.cursor()

# Show tables
print("=== TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"Table: {table[0]}")

# Show recent items with raw_data
print("\n=== RECENT ITEMS ===")
try:
    cursor.execute("SELECT title, raw_data, location, price FROM kufar_items ORDER BY created_at DESC LIMIT 3")
    items = cursor.fetchall()
    for title, raw_data, location, price in items:
        print(f"Title: {title}")
        print(f"Price: {price}")
        print(f"Location: {location}")
        print(f"Raw data: {raw_data}")
        
        # Try to parse raw_data as JSON
        if raw_data:
            try:
                parsed = json.loads(raw_data)
                print(f"Parsed raw_data: {parsed}")
                if 'size' in parsed:
                    print(f"SIZE FOUND: {parsed['size']}")
                else:
                    print("NO SIZE IN RAW_DATA")
            except:
                print(f"Raw data is not JSON: {raw_data}")
        print("---")
        
except Exception as e:
    print(f"Error querying kufar_items: {e}")
    
    # Try other table names
    try:
        cursor.execute("SELECT title, raw_data, location, price FROM items ORDER BY created_at DESC LIMIT 3")
        items = cursor.fetchall()
        print("Found items in 'items' table:")
        for title, raw_data, location, price in items:
            print(f"Title: {title}, Price: {price}, Raw: {raw_data}")
    except Exception as e2:
        print(f"Error querying items: {e2}")

conn.close()
