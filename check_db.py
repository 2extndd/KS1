#!/usr/bin/env python3
"""
Script to check database contents on Railway
"""

import os
import sys
import logging
from db import get_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check what's really in the database"""
    try:
        print("=" * 60)
        print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ RAILWAY")
        print("=" * 60)
        
        # Check active searches
        print("\n📋 АКТИВНЫЕ ПОИСКИ:")
        searches = get_db().get_active_searches()
        print(f"Всего активных поисков: {len(searches)}")
        
        for i, search in enumerate(searches, 1):
            print(f"\n{i}. ID: {search['id']}")
            print(f"   Название: {search.get('name', 'Без названия')}")
            print(f"   URL: {search['url']}")
            print(f"   Thread ID: {search.get('thread_id', 'Не задан')}")
            print(f"   Создан: {search.get('created_at', 'Неизвестно')}")
            
        # Check items
        print(f"\n📦 ТОВАРЫ В БАЗЕ:")
        try:
            items_stats = get_db().get_items_stats()
            print(f"Всего товаров: {items_stats.get('total_items', 0)}")
            
            # Get recent items
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                get_db().execute_query(cursor, """
                    SELECT title, price, location, created_at, search_name
                    FROM items 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                
                recent_items = cursor.fetchall()
                print(f"\nПоследние {len(recent_items)} товаров:")
                for i, item in enumerate(recent_items, 1):
                    title, price, location, created_at, search_name = item
                    print(f"  {i}. {title[:50]}...")
                    print(f"     Цена: {price}, Место: {location}")
                    print(f"     Поиск: {search_name}, Дата: {created_at}")
                    
        except Exception as e:
            print(f"Ошибка получения товаров: {e}")
            
        # Check configuration
        print(f"\n⚙️ КОНФИГУРАЦИЯ:")
        telegram_token = get_db().get_setting('TELEGRAM_BOT_TOKEN')
        telegram_chat = get_db().get_setting('TELEGRAM_CHAT_ID')
        max_items = get_db().get_setting('MAX_ITEMS_PER_SEARCH', '50')
        search_interval = get_db().get_setting('SEARCH_INTERVAL', '300')
        
        print(f"Telegram Token: {'Настроен' if telegram_token else 'НЕ НАСТРОЕН'}")
        print(f"Telegram Chat ID: {'Настроен' if telegram_chat else 'НЕ НАСТРОЕН'}")
        print(f"Max Items Per Search: {max_items}")
        print(f"Search Interval: {search_interval} сек")
        
        # Check logs
        print(f"\n📝 ПОСЛЕДНИЕ ЛОГИ:")
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                get_db().execute_query(cursor, """
                    SELECT timestamp, level, source, message
                    FROM log_entries 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                
                logs = cursor.fetchall()
                for log in logs:
                    timestamp, level, source, message = log
                    print(f"  [{timestamp}] {level} ({source}): {message[:80]}...")
                    
        except Exception as e:
            print(f"Ошибка получения логов: {e}")
            
        print("\n" + "=" * 60)
        
    except Exception as e:
        logger.error(f"Ошибка проверки базы данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
