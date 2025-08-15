"""
Database models and operations for KF Searcher
Based on VS5 database structure, adapted for Kufar.by
"""

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
        self.is_postgres = database_url.startswith('postgresql://') or database_url.startswith('postgres://')
        self.init_database()
    
    def get_connection(self):
        """Get database connection based on database type"""
        if self.is_postgres:
            return psycopg2.connect(self.database_url)
        else:
            return sqlite3.connect(self.database_url.replace('sqlite:///', ''))
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create searches table (equivalent to queries in VS5)
                cursor.execute("""
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
                cursor.execute("""
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
                
                # Create logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(20) NOT NULL,
                        message TEXT NOT NULL,
                        search_id INTEGER REFERENCES searches(id),
                        item_id INTEGER REFERENCES items(id),
                        error_code INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create error_tracking table for auto-redeploy
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS error_tracking (
                        id SERIAL PRIMARY KEY,
                        error_code INTEGER NOT NULL,
                        error_message TEXT,
                        search_id INTEGER REFERENCES searches(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create logs table (like in VS5)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level VARCHAR(20) NOT NULL,
                        message TEXT NOT NULL,
                        source VARCHAR(100),
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                
                # Use parameterized query with explicit column names
                query = """
                    INSERT INTO searches (name, url, region, category, min_price, max_price, 
                                        keywords, telegram_chat_id, telegram_thread_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                cursor.execute(query, (
                    name, url, kwargs.get('region'), kwargs.get('category'),
                    kwargs.get('min_price'), kwargs.get('max_price'),
                    kwargs.get('keywords'), kwargs.get('telegram_chat_id'),
                    kwargs.get('telegram_thread_id'), True
                ))
                
                search_id = cursor.fetchone()[0]
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
                cursor.execute("""
                    SELECT * FROM searches WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
                
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
                cursor.execute("""
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
                """)
                
                columns = [desc[0] for desc in cursor.description]
                searches = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return searches
                
        except Exception as e:
            logger.error(f"Error getting all searches: {e}")
            return []
    
    def get_search_query(self, search_id: int) -> Optional[Dict]:
        """Get single search query by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, url, region, category, min_price, max_price, 
                           keywords, telegram_chat_id, telegram_thread_id, is_active,
                           created_at, updated_at
                    FROM searches 
                    WHERE id = %s
                """, (search_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting search query {search_id}: {e}")
            return None
    
    def update_search_query(self, search_id: int, update_data: Dict) -> bool:
        """Update search query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in update_data.items():
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
                
                if not set_clauses:
                    return False
                
                # Add updated_at
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.append(search_id)
                
                query = f"""
                    UPDATE searches 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating search query {search_id}: {e}")
            return False
    
    def delete_all_search_queries(self) -> bool:
        """Delete all search queries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM searches")
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting all search queries: {e}")
            return False
    
    def delete_search_query(self, search_id: int) -> bool:
        """Delete single search query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM searches WHERE id = %s", (search_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting search query {search_id}: {e}")
            return False
    
    def add_item(self, kufar_id: str, search_id: int, title: str, **kwargs) -> Optional[int]:
        """Add new item if it doesn't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if item already exists
                cursor.execute("SELECT id FROM items WHERE kufar_id = %s", (kufar_id,))
                existing = cursor.fetchone()
                
                if existing:
                    logger.debug(f"Item {kufar_id} already exists")
                    return None
                
                query = """
                    INSERT INTO items (kufar_id, search_id, title, price, currency, description,
                                     images, location, seller_name, seller_phone, url, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                cursor.execute(query, (
                    kufar_id, search_id, title, kwargs.get('price'),
                    kwargs.get('currency', 'BYN'), kwargs.get('description'),
                    json.dumps(kwargs.get('images', [])), kwargs.get('location'),
                    kwargs.get('seller_name'), kwargs.get('seller_phone'),
                    kwargs.get('url'), json.dumps(kwargs.get('raw_data', {}))
                ))
                
                item_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Added new item: {title} (ID: {item_id})")
                return item_id
                
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return None
    
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
                cursor.execute("""
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
                cursor.execute("""
                    INSERT INTO error_tracking (error_code, error_message, search_id)
                    VALUES (%s, %s, %s)
                """, (error_code, error_message, search_id))
                
                # Add to logs table
                cursor.execute("""
                    INSERT INTO logs (level, message, search_id, error_code)
                    VALUES (%s, %s, %s, %s)
                """, ('ERROR', error_message, search_id, error_code))
                
                conn.commit()
                logger.error(f"Logged error {error_code}: {error_message}")
                
        except Exception as e:
            logger.error(f"Error logging error: {e}")
    
    def get_recent_errors(self, hours: int = 1) -> List[Dict]:
        """Get recent errors for auto-redeploy check"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
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
                cursor.execute("SELECT COUNT(*) FROM items")
                stats['total_items'] = cursor.fetchone()[0]
                
                # Items today
                cursor.execute("""
                    SELECT COUNT(*) FROM items 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
                stats['items_today'] = cursor.fetchone()[0]
                
                # Unsent items
                cursor.execute("SELECT COUNT(*) FROM items WHERE is_sent = FALSE")
                stats['unsent_items'] = cursor.fetchone()[0]
                
                # Active searches
                cursor.execute("SELECT COUNT(*) FROM searches WHERE is_active = TRUE")
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
                    cursor.execute("""
                        SELECT timestamp, level, message, source, details
                        FROM logs 
                        WHERE level = %s
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (level, limit))
                else:
                    cursor.execute("""
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
                cursor.execute("DELETE FROM logs")
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
    
    def get_recent_logs(self, minutes: int = 5):
        """Get recent log entries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
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
