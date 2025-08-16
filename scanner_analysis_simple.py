#!/usr/bin/env python3
"""
Простой анализ частоты сканирования KufarSearcher
Расчет нагрузки на Kufar.by при Query Refresh Delay = 10 секунд
"""

def analyze_scanner_frequency():
    """Анализируем фактическую частоту сканирования"""
    
    print("🔍 АНАЛИЗ ЧАСТОТЫ СКАНИРОВАНИЯ KUFARSEARCHER")
    print("=" * 60)
    
    # Параметры для анализа
    interval_seconds = 10  # Query Refresh Delay из веб-интерфейса
    num_filters = 3  # Предполагаем 3 активных фильтра
    
    print(f"📊 Query Refresh Delay: {interval_seconds} секунд")
    print(f"📊 Количество активных фильтров: {num_filters}")
    print(f"📊 Планировщик проверяет готовность: каждые 60 секунд")
    print()
    
    # Анализ логики планировщика
    print("⚙️ ЛОГИКА РАБОТЫ ПЛАНИРОВЩИКА:")
    print("-" * 40)
    print("1. ⏰ schedule.every(1).minutes.do(search_and_notify)")
    print("   → Функция search_and_notify() вызывается каждые 60 секунд")
    print()
    print("2. 🔍 В каждом вызове search_and_notify():")
    print("   → Получаем все активные фильтры")
    print("   → Для каждого фильтра проверяем: (now - last_scan_time) >= 10 секунд")
    print("   → Сканируем только готовые фильтры")
    print("   → Обновляем last_scan_time после сканирования")
    print()
    print("3. ⏸️ Задержка между сканированиями фильтров: 2-5 секунд")
    print()
    
    # Расчет частоты сканирования для одного фильтра
    print("📊 ЧАСТОТА СКАНИРОВАНИЯ ОДНОГО ФИЛЬТРА:")
    print("-" * 45)
    scans_per_hour_per_filter = 3600 / interval_seconds
    scans_per_day_per_filter = 24 * scans_per_hour_per_filter
    
    print(f"• Теоретически один фильтр должен сканироваться каждые: {interval_seconds} секунд")
    print(f"• Но планировщик проверяет готовность только каждые: 60 секунд")
    print()
    print("🔍 ФАКТИЧЕСКАЯ ЧАСТОТА:")
    
    # Моделируем реальную работу
    actual_intervals = []
    for check_minute in range(10):  # Моделируем 10 минут
        check_time = check_minute * 60  # Время проверки в секундах
        if check_time == 0:
            # Первый запуск - фильтр готов
            actual_intervals.append(0)
            last_scan = 0
        else:
            # Проверяем готовность
            time_since_last = check_time - last_scan
            if time_since_last >= interval_seconds:
                actual_intervals.append(check_time)
                last_scan = check_time
    
    print("Время проверки планировщика | Действие")
    print("---------------------------|------------------")
    last_scan = 0
    for minute in range(6):
        check_time = minute * 60
        if minute == 0:
            print(f"00:00 (0 сек)              | ✅ Первый запуск - сканируем")
            last_scan = 0
        else:
            time_since_last = check_time - last_scan
            if time_since_last >= interval_seconds:
                print(f"{minute:02d}:00 ({check_time} сек)           | ✅ Прошло {time_since_last}с ≥ {interval_seconds}с - сканируем")
                last_scan = check_time
            else:
                print(f"{minute:02d}:00 ({check_time} сек)           | ⏱️  Прошло {time_since_last}с < {interval_seconds}с - ждем")
    
    print()
    
    # Реальная частота с учетом планировщика
    effective_interval = 60  # Планировщик проверяет каждую минуту
    actual_scans_per_hour = 3600 / effective_interval
    actual_scans_per_day = 24 * actual_scans_per_hour
    
    print("📈 РЕАЛЬНАЯ ЧАСТОТА СКАНИРОВАНИЯ:")
    print("-" * 35)
    print(f"• Фактически один фильтр сканируется каждые: ~{effective_interval} секунд")
    print(f"• Реальных сканирований одного фильтра в час: {actual_scans_per_hour:.0f}")
    print(f"• Реальных сканирований одного фильтра в день: {actual_scans_per_day:.0f}")
    print()
    
    # Расчет общей нагрузки на Kufar.by
    print("🌐 ОБЩАЯ НАГРУЗКА НА KUFAR.BY:")
    print("-" * 35)
    total_requests_per_hour = num_filters * actual_scans_per_hour
    total_requests_per_day = num_filters * actual_scans_per_day
    
    print(f"• Общих запросов к Kufar.by в час: {total_requests_per_hour:.0f}")
    print(f"• Общих запросов к Kufar.by в день: {total_requests_per_day:.0f}")
    print(f"• Средняя частота запросов: {total_requests_per_hour/60:.1f} запросов/минуту")
    print()
    
    # Анализ пиковой нагрузки
    print("⚡ АНАЛИЗ ПИКОВОЙ НАГРУЗКИ:")
    print("-" * 30)
    print("🔴 Максимальная пиковая нагрузка:")
    print(f"   • При первом запуске все {num_filters} фильтров сканируются одновременно")
    print(f"   • Время выполнения: ~{num_filters * 3.5:.1f} секунд (с задержками 2-5с)")
    print(f"   • Затем каждый фильтр сканируется отдельно каждую минуту")
    print()
    
    # Проблема текущей логики
    print("⚠️  ПРОБЛЕМА ТЕКУЩЕЙ ЛОГИКИ:")
    print("-" * 30)
    print(f"🔴 Query Refresh Delay = {interval_seconds} секунд, но планировщик проверяет каждые 60 секунд!")
    print()
    print("Это означает:")
    print(f"• Если Query Refresh Delay < 60 секунд → фильтры будут сканироваться каждую минуту")
    print(f"• Настройка {interval_seconds} секунд фактически игнорируется!")
    print("• Реальный интервал сканирования = 60 секунд")
    print()
    
    # Рекомендации
    print("💡 РЕКОМЕНДАЦИИ ДЛЯ ИСПРАВЛЕНИЯ:")
    print("-" * 35)
    print("1. 🔧 Изменить логику планировщика:")
    print("   if interval_seconds < 60:")
    print("       schedule.every(interval_seconds).seconds.do(search_and_notify)")
    print("   else:")
    print("       schedule.every(1).minutes.do(search_and_notify)")
    print()
    print("2. 📊 При текущей настройке Query Refresh Delay = 10 секунд:")
    print("   • Планировщик должен проверять каждые 10 секунд")
    print("   • Это даст 6 проверок в минуту")
    print(f"   • Нагрузка: {num_filters * 6 * 60:.0f} запросов/час вместо {total_requests_per_hour:.0f}")
    print()
    
    # Расчет при правильной логике
    print("🎯 ПРИ ПРАВИЛЬНОЙ ЛОГИКЕ (Query Refresh Delay = 10с):")
    print("-" * 50)
    correct_scans_per_hour = num_filters * (3600 / interval_seconds)
    correct_scans_per_day = correct_scans_per_hour * 24
    
    print(f"• Запросов к Kufar.by в час: {correct_scans_per_hour:.0f}")
    print(f"• Запросов к Kufar.by в день: {correct_scans_per_day:.0f}")
    print(f"• Это {correct_scans_per_hour/60:.1f} запросов каждую минуту!")
    
    if correct_scans_per_hour > 1000:
        print("🔴 КРИТИЧНО: Слишком высокая нагрузка!")
        print("   Рекомендуется увеличить Query Refresh Delay до 60+ секунд")
    elif correct_scans_per_hour > 500:
        print("🟡 ВНИМАНИЕ: Высокая нагрузка на Kufar.by")
    else:
        print("🟢 Приемлемая нагрузка")
    
    print()
    print("=" * 60)
    print("🔚 ИТОГОВЫЙ ВЫВОД:")
    print(f"Текущая логика НЕ соответствует настройке Query Refresh Delay!")
    print(f"Фактический интервал: 60 секунд вместо {interval_seconds} секунд")

if __name__ == "__main__":
    analyze_scanner_frequency()
