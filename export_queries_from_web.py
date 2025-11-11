#!/usr/bin/env python3
"""
Экспорт всех queries из сохраненного HTML файла веб-интерфейса для версии 1.0
"""

import re
import html
from datetime import datetime
from bs4 import BeautifulSoup

def clean_text(text):
    """Очистить текст от HTML тегов и лишних пробелов"""
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Убираем лишние пробелы и переносы строк
    text = ' '.join(text.split())
    return text.strip()

def export_queries_from_html():
    """Экспортировать все queries из HTML файла"""
    try:
        html_file = '/Users/extndd/Downloads/513513513.html'
        print(f"🔍 Читаем HTML файл: {html_file}")
        
        # Читаем HTML файл
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Используем BeautifulSoup для более точного парсинга
        soup = BeautifulSoup(content, 'html.parser')
        
        # Находим все строки таблицы
        rows = soup.find_all('tr')
        queries = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                try:
                    # Номер в таблице
                    num_cell = cells[0]
                    if 'fw-bold' in num_cell.get('class', []):
                        num = clean_text(num_cell.get_text())
                        
                        # Ссылка и название
                        link_cell = cells[1]
                        link = link_cell.find('a')
                        if link:
                            url = link.get('href', '')
                            title = clean_text(link.get_text())
                            
                            # Thread ID
                            thread_cell = cells[2]
                            thread_span = thread_cell.find('span', class_='text-primary')
                            thread_id = clean_text(thread_span.get_text()) if thread_span else 'Не задан'
                            
                            # Количество объявлений
                            count_cell = cells[4] if len(cells) > 4 else cells[3]
                            count_span = count_cell.find('span', class_='text-info')
                            items_count = clean_text(count_span.get_text()) if count_span else '0'
                            
                            queries.append({
                                'num': num,
                                'title': title,
                                'url': html.unescape(url),
                                'thread_id': thread_id,
                                'items_count': items_count
                            })
                except Exception as e:
                    continue
        
        print(f'✅ Найдено {len(queries)} queries в HTML файле')
        
        # Создаем экспорт
        export_filename = f'queries_export_from_web_clean_v1.0_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(export_filename, 'w', encoding='utf-8') as f:
            f.write('=' * 80 + '\n')
            f.write('KUFAR SEARCHER - ЭКСПОРТ QUERIES ИЗ ВЕБ-ИНТЕРФЕЙСА (ВЕРСИЯ 1.0)\n')
            f.write('=' * 80 + '\n')
            f.write(f'Дата экспорта: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'Всего queries: {len(queries)}\n')
            f.write(f'Источник: Веб-интерфейс Railway (https://web-production-81c7.up.railway.app/queries)\n')
            f.write('=' * 80 + '\n\n')
            
            for i, query in enumerate(queries, 1):
                f.write(f'QUERY #{i}\n')
                f.write('-' * 40 + '\n')
                f.write(f'Номер в таблице: {query["num"]}\n')
                f.write(f'Название: {query["title"]}\n')
                f.write(f'URL: {query["url"]}\n')
                f.write(f'Thread ID: {query["thread_id"]}\n')
                f.write(f'Найдено объявлений: {query["items_count"]}\n')
                f.write('\n')
            
            f.write('=' * 80 + '\n')
            f.write('КОНЕЦ ЭКСПОРТА\n')
            f.write('=' * 80 + '\n')
        
        print(f'✅ Экспорт завершен: {export_filename}')
        print(f'📊 Экспортировано queries: {len(queries)}')
        
        # Статистика
        total_items = sum(int(q['items_count']) for q in queries if q['items_count'].isdigit())
        active_queries = len([q for q in queries if int(q['items_count']) > 0 if q['items_count'].isdigit()])
        
        print(f'📈 Статистика:')
        print(f'   • Всего queries: {len(queries)}')
        print(f'   • С найденными объявлениями: {active_queries}')
        print(f'   • Общее количество объявлений: {total_items}')
        
        return export_filename
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        return None

if __name__ == "__main__":
    export_queries_from_html()
