"""
Database models and operations for KF Searcher
Based on VS5 database structure, adapted for Kufar.by
"""

import os
import sqlite3
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import logging
from configuration_values import DATABASE_URL

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        
        # Determine database type
        if database_url and (database_url.startswith('postgresql://') or database_url.startswith('postgres://')):
            self.is_postgres = True
        elif database_url and database_url.startswith('sqlite://'):
            self.is_postgres = False
        else:
            # Default to SQLite for local development
            self.is_postgres = False
        
        # Fix PostgreSQL URL format if needed
        if self.is_postgres and self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("Fixed PostgreSQL URL format")
        
        # Force PostgreSQL mode for Railway
        if os.getenv('RAILWAY_ENVIRONMENT'):
            self.is_postgres = True
            # On Railway, DATABASE_URL should be PostgreSQL
            if not self.database_url or not (self.database_url.startswith('postgresql://') or self.database_url.startswith('postgres://')):
                # Try to get from environment
                self.database_url = os.getenv('DATABASE_URL')
                if not self.database_url:
                    raise ValueError("DATABASE_URL not set on Railway. Please set it in Railway environment variables.")
            logger.info("Forcing PostgreSQL mode for Railway environment")
            logger.info(f"Using database: {self.database_url[:50]}..." if self.database_url else "No database URL")
        
        # Don't initialize database immediately - let it be called explicitly
        # self.init_database()
    
    def force_postgres_mode(self):
        """Force PostgreSQL mode (useful for Railway)"""
        self.is_postgres = True
        logger.info("Forced PostgreSQL mode")
    
    def get_database_info(self):
        """Get database connection info for debugging"""
        return {
            'is_postgres': self.is_postgres,
            'database_url': self.database_url[:50] + "..." if self.database_url and len(self.database_url) > 50 else self.database_url,
            'railway_env': os.getenv('RAILWAY_ENVIRONMENT'),
            'has_database_url': bool(self.database_url)
        }
    
    def get_connection(self):
        """Get database connection based on database type"""
        if self.is_postgres:
            try:
                if not self.database_url:
                    raise ValueError("No database URL provided for PostgreSQL connection")
                
                conn = psycopg2.connect(self.database_url)
                conn.autocommit = False
                return conn
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                logger.error(f"Database info: {self.get_database_info()}")
                raise
        else:
            return sqlite3.connect(self.database_url.replace('sqlite:///', ''))
    
    def execute_query(self, cursor, query, values):
        """Execute query with proper placeholder handling for both PostgreSQL and SQLite"""
        if self.is_postgres:
            cursor.execute(query, values)
        else:
            # Convert %s placeholders to ? for SQLite
            sqlite_query = query.replace('%s', '?')
            cursor.execute(sqlite_query, values)
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create searches table (equivalent to queries in VS5)
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS searches (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        url TEXT NOT NULL,
                        region VARCHAR(100),
                        category VARCHAR(100),
                        min_price INTEGER,
                        max_price INTEGER,
                        keywords TEXT,
                        telegram_chat_id VARCHAR(100),
                        telegram_thread_id VARCHAR(100),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create items table (found ads from Kufar)
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS items (
                        id SERIAL PRIMARY KEY,
                        kufar_id VARCHAR(100) UNIQUE NOT NULL,
                        search_id INTEGER REFERENCES searches(id),
                        title TEXT NOT NULL,
                        price INTEGER,
                        currency VARCHAR(10) DEFAULT 'BYN',
                        description TEXT,
                        images TEXT,
                        location VARCHAR(255),
                        seller_name VARCHAR(255),
                        seller_phone VARCHAR(50),
                        url TEXT NOT NULL,
                        raw_data TEXT,
                        is_sent BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create settings table
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create error_tracking table for auto-redeploy
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS error_tracking (
                        id SERIAL PRIMARY KEY,
                        error_code INTEGER NOT NULL,
                        error_message TEXT,
                        search_id INTEGER REFERENCES searches(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create logs table (like in VS5)
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level VARCHAR(20) NOT NULL,
                        message TEXT NOT NULL,
                        source VARCHAR(100),
                        details TEXT
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_search(self, name: str, url: str, **kwargs) -> int:
        """Add new search query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use standard Python-style parameterized query with %s
                query = """
                    INSERT INTO searches (name, url, region, category, min_price, max_price, 
                                        keywords, telegram_chat_id, telegram_thread_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                # Ensure all values are properly formatted for PostgreSQL
                values = (
                    str(name), str(url), 
                    str(kwargs.get('region', '')) if kwargs.get('region') else None, 
                    str(kwargs.get('category', '')) if kwargs.get('category') else None,
                    int(kwargs.get('min_price', 0)) if kwargs.get('min_price') else None, 
                    int(kwargs.get('max_price', 0)) if kwargs.get('max_price') else None,
                    str(kwargs.get('keywords', '')) if kwargs.get('keywords') else None, 
                    str(kwargs.get('telegram_chat_id', '')) if kwargs.get('telegram_chat_id') else None,
                    str(kwargs.get('telegram_thread_id', '')) if kwargs.get('telegram_thread_id') else None, 
                    True
                )
                
                # Execute with proper error handling
                try:
                    self.execute_query(cursor, query, values)
                except Exception as e:
                    logger.error(f"SQL execution error: {e}")
                    logger.error(f"Query: {query}")
                    logger.error(f"Values: {values}")
                    raise
                
                result = cursor.fetchone()
                if result is None:
                    logger.error(f"Failed to get search ID for: {name}")
                    raise Exception("Failed to get search ID from database")
                
                search_id = result[0]
                conn.commit()
                logger.info(f"Added new search: {name} (ID: {search_id})")
                return search_id
                
        except Exception as e:
            logger.error(f"Error adding search: {e}")
            raise
    
    def get_active_searches(self) -> List[Dict]:
        """Get all active search queries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    SELECT * FROM searches WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """, ())
                
                columns = [desc[0] for desc in cursor.description]
                searches = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return searches
                
        except Exception as e:
            logger.error(f"Error getting active searches: {e}")
            return []
    
    def get_all_searches(self) -> List[Dict]:
        """Get all search queries with item counts and stats"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    SELECT s.id, s.name, s.url, s.region, s.category, s.min_price, s.max_price, 
                           s.keywords, s.telegram_chat_id, s.telegram_thread_id, s.is_active,
                           s.created_at, s.updated_at,
                           COUNT(i.id) as items_count,
                           MAX(i.created_at) as last_found_at
                    FROM searches s
                    LEFT JOIN items i ON s.id = i.search_id
                    GROUP BY s.id, s.name, s.url, s.region, s.category, s.min_price, s.max_price, 
                             s.keywords, s.telegram_chat_id, s.telegram_thread_id, s.is_active,
                             s.created_at, s.updated_at
                    ORDER BY s.created_at DESC
                """, ())
                
                columns = [desc[0] for desc in cursor.description]
                searches = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return searches
                
        except Exception as e:
            logger.error(f"Error getting all searches: {e}")
            return []
    
    def get_search_query(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Get search query by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    SELECT id, name, url, region, category, min_price, max_price, 
                           keywords, telegram_chat_id, telegram_thread_id, is_active,
                           created_at, updated_at
                    FROM searches 
                    WHERE id = %s
                """, (search_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0], 'name': row[1], 'url': row[2], 'region': row[3],
                        'category': row[4], 'min_price': row[5], 'max_price': row[6],
                        'keywords': row[7], 'telegram_chat_id': row[8], 
                        'telegram_thread_id': row[9], 'is_active': row[10],
                        'created_at': row[11], 'updated_at': row[12]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting search query: {e}")
            return None
    
    def update_search_query(self, search_id: int, **kwargs) -> bool:
        """Update search query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                param_count = 1
                
                for key, value in kwargs.items():
                    if key in ['name', 'url', 'region', 'category', 'min_price', 'max_price', 
                              'keywords', 'telegram_chat_id', 'telegram_thread_id', 'is_active']:
                        set_clauses.append(f"{key} = %s")
                        values.append(value)
                
                if not set_clauses:
                    return False
                
                values.append(search_id)
                query = f"""
                    UPDATE searches 
                    SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                
                # Execute with proper error handling
                try:
                    self.execute_query(cursor, query, values)
                except Exception as e:
                    logger.error(f"SQL execution error: {e}")
                    logger.error(f"Query: {query}")
                    logger.error(f"Values: {values}")
                    raise
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating search query: {e}")
            return False
    
    def delete_all_search_queries(self) -> bool:
        """Delete all search queries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, "DELETE FROM searches")
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting all search queries: {e}")
            return False
    
    def delete_search_query(self, search_id: int) -> bool:
        """Delete search query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, "DELETE FROM searches WHERE id = %s", (search_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting search query: {e}")
            return False
    
    def add_item(self, item_data: Dict[str, Any], search_id: int = None) -> int:
        """Add new item to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if item already exists
                if 'kufar_id' in item_data:
                    self.execute_query(cursor, """
                        SELECT id FROM items WHERE kufar_id = %s
                    """, (item_data['kufar_id'],))
                    
                    if cursor.fetchone():
                        logger.info(f"Item already exists: {item_data.get('title', 'Unknown')}")
                        return 0
                
                # Insert new item
                self.execute_query(cursor, """
                    INSERT INTO items (title, url, price, currency, location, created_at, 
                                     images, telegram_chat_id, telegram_thread_id, search_id, 
                                     kufar_id, is_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    item_data.get('title', ''),
                    item_data.get('url', ''),
                    item_data.get('price', 0),
                    item_data.get('currency', 'BYN'),
                    item_data.get('location', ''),
                    item_data.get('created_at'),
                    json.dumps(item_data.get('images', [])),
                    item_data.get('telegram_chat_id'),
                    item_data.get('telegram_thread_id'),
                    search_id,
                    item_data.get('kufar_id'),
                    False
                ))
                
                item_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Added new item: {item_data.get('title', 'Unknown')} (ID: {item_id})")
                return item_id
                
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return 0
    
    def get_unsent_items(self) -> List[Dict]:
        """Get items that haven't been sent to Telegram"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT i.*, s.telegram_chat_id, s.telegram_thread_id, s.name as search_name
                    FROM items i
                    JOIN searches s ON i.search_id = s.id
                    WHERE i.is_sent = FALSE
                    ORDER BY i.created_at ASC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                items = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for item in items:
                    if item.get('images'):
                        item['images'] = json.loads(item['images'])
                    if item.get('raw_data'):
                        item['raw_data'] = json.loads(item['raw_data'])
                
                return items
                
        except Exception as e:
            logger.error(f"Error getting unsent items: {e}")
            return []
    
    def mark_item_sent(self, item_id: int):
        """Mark item as sent to Telegram"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    UPDATE items SET is_sent = TRUE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (item_id,))
                conn.commit()
                logger.debug(f"Marked item {item_id} as sent")
                
        except Exception as e:
            logger.error(f"Error marking item as sent: {e}")
    
    def log_error(self, error_code: int, error_message: str, search_id: Optional[int] = None):
        """Log error for tracking and auto-redeploy"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Add to error_tracking table
                self.execute_query(cursor, """
                    INSERT INTO error_tracking (error_code, error_message, search_id)
                    VALUES (%s, %s, %s)
                """, (error_code, error_message, search_id))
                
                # Add to logs table
                self.execute_query(cursor, """
                    INSERT INTO logs (level, message, source, details)
                    VALUES (%s, %s, %s, %s)
                """, ('ERROR', error_message, 'search', str(error_code)))
                
                conn.commit()
                logger.error(f"Logged error {error_code}: {error_message}")
                
        except Exception as e:
            logger.error(f"Error logging error: {e}")
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    SELECT * FROM error_tracking
                    WHERE created_at >= NOW() - INTERVAL %s
                    ORDER BY created_at DESC
                """, (f"{hours} hours",))
                
                columns = [desc[0] for desc in cursor.description]
                errors = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return errors
                
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []
    
    def get_items_stats(self) -> Dict[str, Any]:
        """Get statistics about items"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total items
                self.execute_query(cursor, "SELECT COUNT(*) FROM items")
                stats['total_items'] = cursor.fetchone()[0]
                
                # Items today
                self.execute_query(cursor, """
                    SELECT COUNT(*) FROM items 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
                stats['items_today'] = cursor.fetchone()[0]
                
                # Unsent items
                self.execute_query(cursor, "SELECT COUNT(*) FROM items WHERE is_sent = FALSE")
                stats['unsent_items'] = cursor.fetchone()[0]
                
                # Active searches
                self.execute_query(cursor, "SELECT COUNT(*) FROM searches WHERE is_active = TRUE")
                stats['active_searches'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def add_log_entry(self, level: str, message: str, source: str = None, details: str = None):
        """Add log entry to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO logs (timestamp, level, message, source, details)
                    VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s)
                """, (level, message, source, details))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding log entry: {e}")
    
    def get_logs(self, limit: int = 100, level: str = None):
        """Get log entries from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if level:
                    self.execute_query(cursor, """
                        SELECT timestamp, level, message, source, details
                        FROM logs 
                        WHERE level = %s
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (level, limit))
                else:
                    self.execute_query(cursor, """
                        SELECT timestamp, level, message, source, details
                        FROM logs 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (limit,))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        'timestamp': row[0],
                        'level': row[1],
                        'message': row[2],
                        'source': row[3],
                        'details': row[4]
                    })
                return logs
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []

    def clear_logs(self):
        """Clear all log entries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, "DELETE FROM logs")
                conn.commit()
                logger.info("All logs cleared")
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
    
    def get_recent_logs(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    SELECT timestamp, level, message, source, details
                    FROM logs 
                    WHERE timestamp >= NOW() - INTERVAL %s
                    ORDER BY timestamp DESC
                """, (f"{minutes} minutes",))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        'timestamp': row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else '',
                        'level': row[1],
                        'message': row[2],
                        'source': row[3],
                        'details': row[4]
                    })
                return logs
                
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []

# Global database instance
db = DatabaseManager()
