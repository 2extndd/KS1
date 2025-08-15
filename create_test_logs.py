#!/usr/bin/env python3
"""
Создание тестовых логов для демонстрации системы логирования
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import db

def create_test_logs():
    """Создает тестовые записи логов"""
    
    test_logs = [
        ('INFO', 'KF Searcher started successfully', 'System', None),
        ('INFO', 'Database connection established', 'Database', 'PostgreSQL connection active'),
        ('INFO', 'Kufar client initialized successfully', 'KufarSearcher', None),
        ('INFO', 'Starting search cycle', 'SearchCore', None),
        ('WARNING', 'No active searches found', 'SearchCore', 'Consider adding search queries'),
        ('INFO', 'WebUI server started', 'Flask', 'Server running on port 5000'),
        ('INFO', 'Telegram bot initialized', 'TelegramWorker', 'Bot token verified'),
        ('DEBUG', 'Proxy system initialized', 'ProxyManager', '59 proxies loaded'),
        ('INFO', 'Railway auto-redeploy system active', 'AutoRedeploy', 'Monitoring HTTP errors'),
        ('INFO', 'System ready for operation', 'System', 'All components initialized')
    ]
    
    print("🚀 Создаю тестовые логи...")
    
    for level, message, source, details in test_logs:
        try:
            db.add_log_entry(level, message, source, details)
            print(f"✅ {level}: {message}")
        except Exception as e:
            print(f"❌ Ошибка создания лога: {e}")
    
    print("✅ Тестовые логи созданы!")

if __name__ == "__main__":
    create_test_logs()
