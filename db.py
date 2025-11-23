"""
Database models and operations for KF Searcher
Based on VS5 database structure, adapted for Kufar.by
"""

import os
import sqlite3
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import json
import logging
from configuration_values import DATABASE_URL

# Часовой пояс Беларуси (UTC+3)
import pytz
BELARUS_TZ = pytz.timezone('Europe/Minsk')

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
        
        # Проверяем DATABASE_URL на Railway
        if os.getenv('RAILWAY_ENVIRONMENT'):
            logger.info("🚀 Railway environment detected")
            
            # Проверяем есть ли PostgreSQL URL
            if self.database_url and (self.database_url.startswith('postgresql://') or self.database_url.startswith('postgres://')):
                self.is_postgres = True
                logger.info("✅ PostgreSQL DATABASE_URL found and validated for Railway")
                logger.info(f"Database: {self.database_url[:50]}...")
            else:
                # PostgreSQL недоступен - используем in-memory SQLite как временное решение
                logger.warning("⚠️ PostgreSQL not available on Railway, using in-memory SQLite as fallback")
                logger.warning("⚠️ Data will be lost on restart - please check Railway PostgreSQL service")
                self.is_postgres = False
                self.database_url = 'sqlite:///:memory:'  # In-memory SQLite для Railway
        
        # Don't initialize database immediately - let it be called explicitly
        # self.init_database()
    
    def get_belarus_time(self):
        """Получить текущее время в белорусском часовом поясе"""
        return datetime.now(BELARUS_TZ)
    
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
                
                # Проверяем состояние транзакции и восстанавливаем если нужно
                if conn.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                    logger.warning("🔄 Обнаружена прерванная транзакция PostgreSQL, выполняем rollback")
                    conn.rollback()
                
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
            try:
                cursor.execute(query, values)
            except psycopg2.Error as e:
                logger.error(f"❌ PostgreSQL error: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Values: {values}")
                
                # Попытка восстановления соединения
                if cursor.connection.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                    logger.warning("🔄 Выполняем rollback для восстановления транзакции")
                    cursor.connection.rollback()
                
                raise
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
                        last_scan_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """, ())
                
                # Add last_scan_time column if it doesn't exist (migration)
                try:
                    self.execute_query(cursor, """
                        ALTER TABLE searches ADD COLUMN last_scan_time TIMESTAMP
                    """, ())
                    logger.info("Добавлено поле last_scan_time в таблицу searches")
                except Exception as e:
                    # Column might already exist, ignore error
                    if "already exists" not in str(e).lower() and "duplicate column" not in str(e).lower():
                        logger.debug(f"Migration note: {e}")
                
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
                """, ())
                
                # Create settings table
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """, ())
                
                # Create error_tracking table for auto-redeploy
                self.execute_query(cursor, """
                    CREATE TABLE IF NOT EXISTS error_tracking (
                        id SERIAL PRIMARY KEY,
                        error_code INTEGER NOT NULL,
                        error_message TEXT,
                        search_id INTEGER REFERENCES searches(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """, ())
                
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
                """, ())
                
                conn.commit()
                logger.info("✅ PostgreSQL база данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА инициализации PostgreSQL: {e}")
            logger.error("🔧 Попытка восстановления подключения...")
            
            # Попытка повторной инициализации
            try:
                import time
                time.sleep(2)
                with self.get_connection() as conn:
                    conn.rollback()  # Сброс любых повисших транзакций
                    logger.info("♻️  Транзакции сброшены, повторная попытка инициализации...")
            except Exception as recovery_error:
                logger.error(f"❌ Ошибка восстановления: {recovery_error}")
            
            raise
    
    def add_search(self, name: str, url: str, **kwargs) -> int:
        """Add new search query"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Ensure all values are properly formatted
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
            if self.is_postgres:
                # PostgreSQL - use RETURNING
                query = """
                    INSERT INTO searches (name, url, region, category, min_price, max_price, 
                                        keywords, telegram_chat_id, telegram_thread_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                self.execute_query(cursor, query, values)
                result = cursor.fetchone()
                if result is None:
                    logger.error(f"Failed to get search ID for: {name}")
                    raise Exception("Failed to get search ID from database")
                search_id = result[0]
            else:
                # SQLite - use lastrowid
                query = """
                    INSERT INTO searches (name, url, region, category, min_price, max_price, 
                                        keywords, telegram_chat_id, telegram_thread_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.execute_query(cursor, query, values)
                search_id = cursor.lastrowid
                if not search_id:
                    logger.error(f"Failed to get search ID for: {name}")
                    raise Exception("Failed to get search ID from database")
            
            # CRITICAL: Commit BEFORE closing connection
            conn.commit()
            logger.info(f"✅ Added new search: {name} (ID: {search_id})")
            
            return search_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Error adding search: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            if conn:
                conn.close()
    
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
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['name', 'url', 'region', 'category', 'min_price', 'max_price', 
                          'keywords', 'telegram_chat_id', 'telegram_thread_id', 'is_active', 'last_scan_time']:
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
                rows_updated = cursor.rowcount
            except Exception as e:
                logger.error(f"SQL execution error: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Values: {values}")
                raise
            
            # CRITICAL: Commit BEFORE closing connection
            conn.commit()
            
            logger.info(f"Updated search query {search_id}, affected rows: {rows_updated}")
            return rows_updated > 0
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating search query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            if conn:
                conn.close()
    
    def update_search_scan_time(self, search_id: int) -> bool:
        """Обновить время последнего сканирования поиска (VS5-style)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Используем белорусское время
                belarus_time = self.get_belarus_time()
                
                if self.is_postgres:
                    # PostgreSQL - используем параметр времени
                    self.execute_query(cursor, """
                        UPDATE searches 
                        SET last_scan_time = %s, updated_at = %s
                        WHERE id = %s
                    """, (belarus_time, belarus_time, search_id))
                else:
                    # SQLite - используем CURRENT_TIMESTAMP
                    self.execute_query(cursor, """
                        UPDATE searches 
                        SET last_scan_time = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (search_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"✅ Обновлено время сканирования для поиска {search_id}: {belarus_time.strftime('%H:%M:%S')}")
                    return True
                else:
                    logger.warning(f"⚠️ Поиск {search_id} не найден для обновления времени")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления времени сканирования для поиска {search_id}: {e}")
            return False
    
    def get_searches_ready_for_scan(self, interval_seconds: int) -> List[Dict[str, Any]]:
        """Получить поиски, готовые для сканирования"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.is_postgres:
                    # PostgreSQL синтаксис
                    self.execute_query(cursor, """
                        SELECT s.*, 
                               EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - COALESCE(s.last_scan_time, s.created_at))) as seconds_since_scan
                        FROM searches s
                        WHERE s.is_active = TRUE 
                        AND (s.last_scan_time IS NULL OR 
                             CURRENT_TIMESTAMP - s.last_scan_time >= INTERVAL '%s seconds')
                        ORDER BY COALESCE(s.last_scan_time, s.created_at) ASC
                    """, (interval_seconds,))
                else:
                    # SQLite синтаксис
                    self.execute_query(cursor, """
                        SELECT s.*,
                               (julianday('now') - julianday(COALESCE(s.last_scan_time, s.created_at))) * 86400 as seconds_since_scan
                        FROM searches s
                        WHERE s.is_active = 1
                        AND (s.last_scan_time IS NULL OR 
                             (julianday('now') - julianday(s.last_scan_time)) * 86400 >= ?)
                        ORDER BY COALESCE(s.last_scan_time, s.created_at) ASC
                    """, (interval_seconds,))
                
                columns = [desc[0] for desc in cursor.description]
                searches = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return searches
                
        except Exception as e:
            logger.error(f"Ошибка получения поисков для сканирования: {e}")
            return []
    
    def delete_all_search_queries(self) -> bool:
        """Delete all search queries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, "DELETE FROM searches", ())
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting all search queries: {e}")
            return False
    
    def delete_search_query(self, search_id: int) -> bool:
        """Delete search query and associated items"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First delete associated items
            self.execute_query(cursor, "DELETE FROM items WHERE search_id = %s", (search_id,))
            items_deleted = cursor.rowcount
            logger.info(f"Deleted {items_deleted} items for search {search_id}")
            
            # Then delete the search query
            self.execute_query(cursor, "DELETE FROM searches WHERE id = %s", (search_id,))
            queries_deleted = cursor.rowcount
            
            # CRITICAL: Commit BEFORE closing connection
            conn.commit()
            
            logger.info(f"Deleted search query {search_id}, affected rows: {queries_deleted}")
            
            # Return True if query was deleted (even if no items were deleted)
            return queries_deleted > 0
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error deleting search query {search_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            if conn:
                conn.close()
    
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
                    
                    existing = cursor.fetchone()
                    if existing:
                        # Log duplicate item in VS5 style
                        title = item_data.get('title', 'Unknown')[:50]
                        price = item_data.get('price', 0)
                        currency = item_data.get('currency', 'BYN')
                        price_str = f"{price} {currency}" if price > 0 else "Без цены"
                        
                        logger.info(f"[DUPLICATE] {title} ({price_str}) - already exists in database")
                        self.add_log_entry('INFO', 
                                         f'Duplicate item skipped: {title}', 
                                         'core', 
                                         f'Item ID {item_data["kufar_id"]} already exists - {price_str}')
                        return 0
                
                # Insert new item
                item_values = (
                    item_data.get('kufar_id', ''),
                    search_id or item_data.get('search_id'),
                    item_data.get('title', ''),
                    item_data.get('price', 0),
                    item_data.get('currency', 'BYN'),
                    item_data.get('description', ''),
                    json.dumps(item_data.get('images', [])),
                    item_data.get('location', ''),
                    item_data.get('seller_name', ''),
                    item_data.get('seller_phone', ''),
                    item_data.get('url', ''),
                    json.dumps(item_data.get('raw_data', {})) if item_data.get('raw_data') else None,
                    False
                )
                
                if self.is_postgres:
                    # PostgreSQL - use RETURNING
                    self.execute_query(cursor, """
                        INSERT INTO items (kufar_id, search_id, title, price, currency, 
                                         description, images, location, seller_name, 
                                         seller_phone, url, raw_data, is_sent)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, item_values)
                    item_id = cursor.fetchone()[0]
                else:
                    # SQLite - use lastrowid
                    self.execute_query(cursor, """
                        INSERT INTO items (kufar_id, search_id, title, price, currency, 
                                         description, images, location, seller_name, 
                                         seller_phone, url, raw_data, is_sent)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, item_values)
                    item_id = cursor.lastrowid
                
                conn.commit()
                
                # Log new item in VS5 style
                title = item_data.get('title', 'Unknown')[:50]
                price = item_data.get('price', 0)
                currency = item_data.get('currency', 'BYN')
                price_str = f"{price} {currency}" if price > 0 else "Без цены"
                location = item_data.get('location', 'Без локации')
                
                logger.info(f"[NEW ITEM] {title} ({price_str}) from {location} - added to database")
                self.add_log_entry('INFO', 
                                 f'New item added: {title}', 
                                 'core', 
                                 f'Item ID {item_data["kufar_id"]} - {price_str} - {location}')
                
                return item_id
                
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return 0
    
    def get_unsent_items(self) -> List[Dict]:
        """Get items that haven't been sent to Telegram"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, """
                    SELECT i.*, s.telegram_chat_id, s.telegram_thread_id, s.name as search_name
                    FROM items i
                    JOIN searches s ON i.search_id = s.id
                    WHERE i.is_sent = FALSE
                    ORDER BY i.created_at ASC
                """, ())
                
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
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set a configuration setting"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.is_postgres:
                # PostgreSQL - use ON CONFLICT
                self.execute_query(cursor, """
                    INSERT INTO settings (key, value, updated_at) 
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE SET 
                    value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
                """, (key, value))
            else:
                # SQLite - use INSERT OR REPLACE
                # First check if setting exists
                self.execute_query(cursor, """
                    SELECT id FROM settings WHERE key = %s
                """, (key,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    self.execute_query(cursor, """
                        UPDATE settings 
                        SET value = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE key = %s
                    """, (value, key))
                else:
                    # Insert new
                    self.execute_query(cursor, """
                        INSERT INTO settings (key, value, updated_at) 
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                    """, (key, value))
            
            # CRITICAL: Commit BEFORE closing connection
            conn.commit()
            
            # ВАЖНО: Явно проверяем что commit прошёл успешно
            # Для PostgreSQL на Railway это критично!
            import time
            time.sleep(0.1)  # Даём время на commit
            
            # Проверяем что значение действительно сохранилось
            cursor_check = conn.cursor()
            self.execute_query(cursor_check, """
                SELECT value FROM settings WHERE key = %s
            """, (key,))
            check_result = cursor_check.fetchone()
            
            if check_result and check_result[0] == value:
                logger.info(f"✅ Setting saved and verified: {key} = {value}")
                return True
            else:
                logger.error(f"❌ Setting saved but verification FAILED: {key} (expected={value}, got={check_result[0] if check_result else None})")
                return False
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Error setting {key}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            if conn:
                conn.close()
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Get a configuration setting"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                self.execute_query(cursor, """
                    SELECT value FROM settings WHERE key = %s
                """, (key,))
                
                result = cursor.fetchone()
                return result[0] if result else default
                
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for Railway status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get error counts by type
                if self.is_postgres:
                    self.execute_query(cursor, """
                        SELECT error_code, COUNT(*) 
                        FROM error_tracking 
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                        GROUP BY error_code
                    """, ())
                else:
                    self.execute_query(cursor, """
                        SELECT error_code, COUNT(*) 
                        FROM error_tracking 
                        WHERE created_at > datetime('now', '-24 hours')
                        GROUP BY error_code
                    """, ())
                
                error_counts = dict(cursor.fetchall())
                
                # Get first and last error times
                if self.is_postgres:
                    self.execute_query(cursor, """
                        SELECT MIN(created_at), MAX(created_at), COUNT(*)
                        FROM error_tracking 
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                    """, ())
                else:
                    self.execute_query(cursor, """
                        SELECT MIN(created_at), MAX(created_at), COUNT(*)
                        FROM error_tracking 
                        WHERE created_at > datetime('now', '-24 hours')
                    """, ())
                
                result = cursor.fetchone()
                try:
                    first_error = result[0].strftime('%d.%m.%Y, %H:%M:%S') if result[0] else 'None'
                except:
                    first_error = str(result[0]) if result[0] else 'None'
                try:
                    last_error = result[1].strftime('%d.%m.%Y, %H:%M:%S') if result[1] else 'None'
                except:
                    last_error = str(result[1]) if result[1] else 'None'
                total_errors = result[2] or 0
                
                return {
                    '403': error_counts.get(403, 0),
                    '401': error_counts.get(401, 0),
                    '429': error_counts.get(429, 0),
                    'total': total_errors,
                    'first_error': first_error,
                    'last_error': last_error,
                    'last_redeploy': 'Never'  # This would come from deploy logs
                }
                
        except Exception as e:
            logger.error(f"Error getting error statistics: {e}")
            return {
                '403': 0, '401': 0, '429': 0, 'total': 0,
                'first_error': 'None', 'last_error': 'None', 'last_redeploy': 'Never'
            }
    
    def get_proxy_statistics(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        try:
            # Check if proxies are enabled
            proxy_enabled = self.get_setting('PROXY_ENABLED', 'false').lower() == 'true'
            proxy_list = self.get_setting('PROXY_LIST', '')
            
            if not proxy_enabled or not proxy_list:
                return {
                    'total_proxies': 0,
                    'working_proxies': 0,
                    'current_proxy': 'No proxies configured',
                    'last_check': 'Never'
                }
            
            # Count proxies from proxy list
            proxies = [p.strip() for p in proxy_list.split(',') if p.strip()]
            
            return {
                'total_proxies': len(proxies),
                'working_proxies': len(proxies),  # Assume all are working for now
                'current_proxy': f'Random from {len(proxies)} proxies',
                'last_check': datetime.now().strftime('%d.%m.%Y, %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error getting proxy statistics: {e}")
            return {
                'total_proxies': 0,
                'working_proxies': 0,
                'current_proxy': 'Error getting proxy info',
                'last_check': 'Error'
            }

    def get_last_found_item(self) -> Dict[str, Any]:
        """Get the last found item for dashboard"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                self.execute_query(cursor, """
                    SELECT i.title, i.created_at, s.name as search_name
                    FROM items i 
                    LEFT JOIN searches s ON i.search_id = s.id
                    ORDER BY i.created_at DESC 
                    LIMIT 1
                """, ())
                
                result = cursor.fetchone()
                if result:
                    return {
                        'title': result[0],
                        'date': result[1].strftime('%Y-%m-%d %H:%M:%S') if result[1] else 'Unknown',
                        'search_name': result[2] or 'Unknown'
                    }
                else:
                    return {
                        'title': 'No items yet',
                        'date': 'Never',
                        'search_name': ''
                    }
                    
        except Exception as e:
            logger.error(f"Error getting last found item: {e}")
            return {
                'title': 'Error loading',
                'date': 'Error',
                'search_name': ''
            }

    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.is_postgres:
                    # PostgreSQL syntax
                    self.execute_query(cursor, """
                        SELECT * FROM error_tracking
                        WHERE created_at >= NOW() - INTERVAL %s
                        ORDER BY created_at DESC
                    """, (f"{hours} hours",))
                else:
                    # SQLite syntax
                    self.execute_query(cursor, """
                        SELECT * FROM error_tracking
                        WHERE created_at >= datetime('now', '-' || %s || ' hours')
                        ORDER BY created_at DESC
                    """, (hours,))
                
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
                self.execute_query(cursor, "SELECT COUNT(*) FROM items", ())
                stats['total_items'] = cursor.fetchone()[0]
                
                # Items today
                self.execute_query(cursor, """
                    SELECT COUNT(*) FROM items 
                    WHERE DATE(created_at) = CURRENT_DATE
                """, ())
                stats['items_today'] = cursor.fetchone()[0]
                
                # Unsent items
                self.execute_query(cursor, "SELECT COUNT(*) FROM items WHERE is_sent = FALSE", ())
                stats['unsent_items'] = cursor.fetchone()[0]
                
                # Active searches
                self.execute_query(cursor, "SELECT COUNT(*) FROM searches WHERE is_active = TRUE", ())
                stats['active_searches'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def add_log_entry(self, level: str, message: str, source: str = None, details: str = None):
        """Add log entry to database with Belarus timezone"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use Belarus timezone for timestamp
                belarus_time = datetime.now(BELARUS_TZ)
                
                if self.is_postgres:
                    self.execute_query(cursor, """
                        INSERT INTO logs (timestamp, level, message, source, details)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (belarus_time, level, message, source, details))
                else:
                    # For SQLite, store as ISO string
                    self.execute_query(cursor, """
                        INSERT INTO logs (timestamp, level, message, source, details)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (belarus_time.isoformat(), level, message, source, details))
                    
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
                self.execute_query(cursor, "DELETE FROM logs", ())
                conn.commit()
                logger.info("All logs cleared")
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
    
    def clear_all_items(self):
        """Clear all items from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self.execute_query(cursor, "DELETE FROM items", ())
                conn.commit()
                logger.info("All items cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing all items: {e}")
            return False
    
    def get_recent_logs(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.is_postgres:
                    # PostgreSQL syntax
                    self.execute_query(cursor, """
                        SELECT timestamp, level, message, source, details
                        FROM logs 
                        WHERE timestamp >= NOW() - INTERVAL %s
                        ORDER BY timestamp DESC
                    """, (f"{minutes} minutes",))
                else:
                    # SQLite syntax
                    self.execute_query(cursor, """
                        SELECT timestamp, level, message, source, details
                        FROM logs 
                        WHERE timestamp >= datetime('now', '-' || %s || ' minutes')
                        ORDER BY timestamp DESC
                    """, (minutes,))
                
                logs = []
                for row in cursor.fetchall():
                    try:
                        # Parse timestamp and convert to Belarus timezone for display
                        if row[0]:
                            if isinstance(row[0], str):
                                # SQLite case - parse ISO string
                                dt = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
                            else:
                                # PostgreSQL case - already datetime object
                                dt = row[0]
                            
                            # Convert to Belarus timezone if needed
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            
                            belarus_dt = dt.astimezone(BELARUS_TZ)
                            timestamp = belarus_dt.strftime('%d.%m.%Y %H:%M:%S')
                        else:
                            timestamp = ''
                    except Exception as e:
                        logger.error(f"Error formatting timestamp {row[0]}: {e}")
                        timestamp = str(row[0]) if row[0] else ''
                    
                    logs.append({
                        'timestamp': timestamp,
                        'level': row[1],
                        'message': row[2],
                        'source': row[3],
                        'details': row[4]
                    })
                return logs
                
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []

# Global database instance - создается при первом обращении
db = None

def get_db():
    """Получить глобальный экземпляр базы данных"""
    global db
    if db is None:
        db = DatabaseManager()
    return db

# Для обратной совместимости - создаем db при импорте только если не на Railway
if not os.getenv('RAILWAY_ENVIRONMENT'):
    db = DatabaseManager()
