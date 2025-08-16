#!/usr/bin/env python3
"""
Анализ частоты сканирования KufarSearcher
Расчет нагрузки на Kufar.by при Query Refresh Delay = 10 секунд
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from configuration_values import get_search_interval
from db import get_db

def analyze_scanner_frequency():
    """Анализируем фактическую частоту сканирования"""
    
    print("🔍 АНАЛИЗ ЧАСТОТЫ СКАНИРОВАНИЯ KUFARSEARCHER")
    print("=" * 60)
    
    # Получаем текущие настройки
    try:
        interval_seconds = get_search_interval()
        print(f"📊 Текущий Query Refresh Delay: {interval_seconds} секунд")
        print(f"📊 Это равно: {interval_seconds/60:.1f} минут")
        print()
    except Exception as e:
        print(f"❌ Ошибка получения настроек: {e}")
        interval_seconds = 10  # Используем указанное значение
        print(f"📊 Используем указанное значение: {interval_seconds} секунд")
        print()
    
    # Получаем количество активных фильтров
    try:
        get_db().init_database()
        active_searches = get_db().get_active_searches()
        num_filters = len(active_searches)
        print(f"🎯 Количество активных фильтров: {num_filters}")
        
        if num_filters == 0:
            print("⚠️  Нет активных фильтров для анализа")
            return
        
        print("\n📋 Список активных фильтров:")
        for i, search in enumerate(active_searches, 1):
            print(f"   {i}. {search['name']}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка получения фильтров из БД: {e}")
        num_filters = 3  # Предполагаем 3 фильтра для расчета
        print(f"🎯 Предполагаем количество фильтров: {num_filters}")
        print()
    
    # Анализ логики планировщика
    print("⚙️ ЛОГИКА РАБОТЫ ПЛАНИРОВЩИКА:")
    print("-" * 40)
    print("1. ⏰ Планировщик запускается каждую минуту (60 секунд)")
    print(f"2. 🔍 В каждом цикле проверяется готовность {num_filters} фильтров")
    print(f"3. ✅ Фильтр готов, если прошло ≥{interval_seconds} секунд с последнего сканирования")
    print("4. 🚀 Готовые фильтры сканируются немедленно")
    print("5. ⏱️ Время последнего сканирования обновляется после каждого сканирования")
    print()
    
    # Расчет частоты сканирования для одного фильтра
    print("📊 ЧАСТОТА СКАНИРОВАНИЯ ОДНОГО ФИЛЬТРА:")
    print("-" * 45)
    scans_per_hour_per_filter = 3600 / interval_seconds
    scans_per_day_per_filter = 24 * scans_per_hour_per_filter
    
    print(f"• Один фильтр сканируется каждые: {interval_seconds} секунд")
    print(f"• Сканирований одного фильтра в час: {scans_per_hour_per_filter:.1f}")
    print(f"• Сканирований одного фильтра в день: {scans_per_day_per_filter:.0f}")
    print()
    
    # Расчет общей нагрузки на Kufar.by
    print("🌐 ОБЩАЯ НАГРУЗКА НА KUFAR.BY:")
    print("-" * 35)
    total_requests_per_hour = num_filters * scans_per_hour_per_filter
    total_requests_per_day = num_filters * scans_per_day_per_filter
    
    print(f"• Общих запросов к Kufar.by в час: {total_requests_per_hour:.0f}")
    print(f"• Общих запросов к Kufar.by в день: {total_requests_per_day:.0f}")
    print(f"• Средняя частота запросов: {total_requests_per_hour/60:.1f} запросов/минуту")
    print()
    
    # Анализ пиковой нагрузки
    print("⚡ АНАЛИЗ ПИКОВОЙ НАГРУЗКИ:")
    print("-" * 30)
    print("🔴 ВАЖНО: Все фильтры могут стать готовыми одновременно в следующих случаях:")
    print("   1. 🚀 Первый запуск приложения (все фильтры никогда не сканировались)")
    print("   2. 🔄 Перезапуск приложения")
    print("   3. ⏱️ Если все фильтры были добавлены одновременно")
    print()
    print(f"   В этом случае все {num_filters} запросов выполнятся за ~{num_filters * 3.5:.1f} секунд")
    print(f"   (с учетом задержки 2-5 секунд между запросами)")
    print()
    
    # Проверка риска блокировки
    print("⚠️  ОЦЕНКА РИСКА БЛОКИРОВКИ:")
    print("-" * 30)
    if total_requests_per_hour > 1000:
        risk_level = "🔴 ВЫСОКИЙ"
    elif total_requests_per_hour > 500:
        risk_level = "🟡 СРЕДНИЙ"
    else:
        risk_level = "🟢 НИЗКИЙ"
    
    print(f"Уровень риска: {risk_level}")
    print(f"• {total_requests_per_hour:.0f} запросов/час это {total_requests_per_hour/60:.2f} запросов/минуту")
    
    if total_requests_per_hour > 360:  # Больше 6 запросов в минуту
        print("⚠️  РЕКОМЕНДАЦИЯ: Увеличьте Query Refresh Delay!")
        recommended_delay = max(60, int(num_filters * 10))
        print(f"   Рекомендуемое значение: {recommended_delay} секунд")
        print(f"   Это снизит нагрузку до ~{(num_filters * 3600 / recommended_delay):.0f} запросов/час")
    else:
        print("✅ Текущая нагрузка приемлемая для Kufar.by")
    
    print()
    
    # Временная диаграмма работы
    print("📅 ПРИМЕР РАБОТЫ В ТЕЧЕНИЕ 5 МИНУТ:")
    print("-" * 42)
    
    current_time = 0
    scanned_filters = set()
    
    print("Время  | Действие")
    print("-------|--------------------------------------------------")
    
    for minute in range(6):  # 6 минут для демонстрации
        time_str = f"{minute:02d}:00"
        
        if minute == 0:
            print(f"{time_str}  | 🚀 Запуск приложения")
            print(f"{time_str}  | ✅ Все {num_filters} фильтров готовы (никогда не сканировались)")
            print(f"{time_str}  | 🌐 Выполняем {num_filters} запросов к Kufar.by")
            scanned_filters = set(range(num_filters))
            last_scan_time = 0
        else:
            time_passed = minute * 60
            ready_count = 0
            
            # Проверяем какие фильтры готовы
            for filter_id in range(num_filters):
                if time_passed >= interval_seconds:
                    ready_count += 1
            
            if ready_count > 0:
                print(f"{time_str}  | ✅ {ready_count} фильтров готовы к сканированию")
                print(f"{time_str}  | 🌐 Выполняем {ready_count} запросов к Kufar.by")
            else:
                print(f"{time_str}  | ⏱️  Все фильтры ожидают (до готовности осталось {interval_seconds - (time_passed % interval_seconds)}с)")
    
    print()
    print("🔚 ИТОГО:")
    print(f"📊 При Query Refresh Delay = {interval_seconds}с и {num_filters} фильтрах:")
    print(f"   • {total_requests_per_hour:.0f} запросов к Kufar.by в час")
    print(f"   • {total_requests_per_day:.0f} запросов к Kufar.by в день")
    print(f"   • Каждый фильтр обновляется {scans_per_hour_per_filter:.1f} раз в час")

if __name__ == "__main__":
    analyze_scanner_frequency()
