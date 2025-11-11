#!/usr/bin/env python3
"""
Экспорт всех текущих queries в txt файл для версии 1.0
"""

import os
import sys
from datetime import datetime
from db import get_db

def export_queries_to_txt():
    """Экспортировать все queries в txt файл"""
    try:
        print("🔍 Экспорт текущих queries...")
        
        # Получаем все поиски из базы данных
        all_searches = get_db().get_all_searches()
        
        if not all_searches:
            print("❌ Нет queries для экспорта")
            return
        
        # Создаем txt файл с экспортом
        export_filename = f"queries_export_v1.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(export_filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("KUFAR SEARCHER - ЭКСПОРТ QUERIES (ВЕРСИЯ 1.0)\n")
            f.write("=" * 80 + "\n")
            f.write(f"Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего queries: {len(all_searches)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, query in enumerate(all_searches, 1):
                f.write(f"QUERY #{i}\n")
                f.write("-" * 40 + "\n")
                f.write(f"ID: {query['id']}\n")
                f.write(f"Название: {query.get('name', 'Без названия')}\n")
                f.write(f"URL: {query['url']}\n")
                f.write(f"Telegram Chat ID: {query.get('telegram_chat_id', 'Не задан')}\n")
                f.write(f"Telegram Thread ID: {query.get('telegram_thread_id', 'Не задан')}\n")
                f.write(f"Активен: {'Да' if query.get('is_active', True) else 'Нет'}\n")
                f.write(f"Создан: {query.get('created_at', 'Неизвестно')}\n")
                f.write(f"Обновлен: {query.get('updated_at', 'Неизвестно')}\n")
                f.write(f"Найдено объявлений: {query.get('items_count', 0)}\n")
                f.write(f"Последнее найденное: {query.get('last_found_at', 'Никогда')}\n")
                
                # Дополнительные параметры если есть
                if query.get('region'):
                    f.write(f"Регион: {query['region']}\n")
                if query.get('category'):
                    f.write(f"Категория: {query['category']}\n")
                if query.get('min_price'):
                    f.write(f"Мин. цена: {query['min_price']}\n")
                if query.get('max_price'):
                    f.write(f"Макс. цена: {query['max_price']}\n")
                if query.get('keywords'):
                    f.write(f"Ключевые слова: {query['keywords']}\n")
                
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("КОНЕЦ ЭКСПОРТА\n")
            f.write("=" * 80 + "\n")
        
        print(f"✅ Экспорт завершен: {export_filename}")
        print(f"📊 Экспортировано queries: {len(all_searches)}")
        
        # Показываем краткую статистику
        active_count = sum(1 for q in all_searches if q.get('is_active', True))
        with_chat_id = sum(1 for q in all_searches if q.get('telegram_chat_id'))
        with_thread_id = sum(1 for q in all_searches if q.get('telegram_thread_id'))
        
        print(f"📈 Статистика:")
        print(f"   • Активных: {active_count}")
        print(f"   • С Chat ID: {with_chat_id}")
        print(f"   • С Thread ID: {with_thread_id}")
        
        return export_filename
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        return None

if __name__ == "__main__":
    export_queries_to_txt()
