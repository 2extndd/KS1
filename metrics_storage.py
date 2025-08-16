"""
Persistent metrics storage using file-based approach
"""
import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path

# ИСПРАВЛЕНО: На Railway /tmp не общий между сервисами!
# Используем PostgreSQL для хранения метрик вместо файла
METRICS_FILE = "/tmp/kufar_metrics.json"  # Fallback для локальной разработки

class MetricsStorage:
    def __init__(self):
        self.lock = threading.Lock()
        self.use_database = self._should_use_database()
        if self.use_database:
            self._ensure_database_metrics()
        else:
            self._ensure_file_exists()
    
    def _should_use_database(self):
        """Определяем нужно ли использовать БД (Railway) или файл (локально)"""
        try:
            import os
            # На Railway или если есть DATABASE_URL - используем БД
            if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('DATABASE_URL'):
                return True
        except:
            pass
        return False
    
    def _ensure_database_metrics(self):
        """Обеспечиваем наличие таблицы metrics в БД"""
        try:
            from db import get_db
            db = get_db()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Создаем таблицу metrics если её нет
                if db.is_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS metrics (
                            key VARCHAR(255) PRIMARY KEY,
                            value TEXT NOT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS metrics (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                
                conn.commit()
                
                # Инициализируем значения по умолчанию если их нет
                default_metrics = {
                    'app_start_time': datetime.now().isoformat(),
                    'total_api_requests': '0',
                    'total_items_found': '0',
                    'last_search_time': ''
                }
                
                for key, value in default_metrics.items():
                    if db.is_postgres:
                        cursor.execute("""
                            INSERT INTO metrics (key, value) VALUES (%s, %s)
                            ON CONFLICT (key) DO NOTHING
                        """, (key, value))
                    else:
                        cursor.execute("""
                            INSERT OR IGNORE INTO metrics (key, value) VALUES (?, ?)
                        """, (key, value))
                
                conn.commit()
                
        except Exception as e:
            print(f"Warning: Failed to initialize database metrics: {e}")
            # Fallback to file storage
            self.use_database = False
            self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure metrics file exists with default values"""
        if not os.path.exists(METRICS_FILE):
            default_metrics = {
                'app_start_time': datetime.now().isoformat(),
                'total_api_requests': 0,
                'total_items_found': 0,
                'last_search_time': None
            }
            self._write_metrics(default_metrics)
    
    def _read_metrics(self):
        """Read metrics from database or file"""
        if self.use_database:
            return self._read_metrics_from_db()
        else:
            return self._read_metrics_from_file()
    
    def _read_metrics_from_db(self):
        """Read metrics from database"""
        try:
            from db import get_db
            db = get_db()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM metrics")
                rows = cursor.fetchall()
                
                metrics = {}
                for key, value in rows:
                    if key in ['total_api_requests', 'total_items_found']:
                        metrics[key] = int(value) if value else 0
                    elif key == 'last_search_time':
                        metrics[key] = value if value else None
                    else:
                        metrics[key] = value
                
                # Ensure all required keys exist
                default_metrics = {
                    'app_start_time': datetime.now().isoformat(),
                    'total_api_requests': 0,
                    'total_items_found': 0,
                    'last_search_time': None
                }
                
                for key, default_value in default_metrics.items():
                    if key not in metrics:
                        metrics[key] = default_value
                
                return metrics
                
        except Exception as e:
            print(f"Error reading metrics from database: {e}")
            return {
                'app_start_time': datetime.now().isoformat(),
                'total_api_requests': 0,
                'total_items_found': 0,
                'last_search_time': None
            }
    
    def _read_metrics_from_file(self):
        """Read metrics from file"""
        try:
            with open(METRICS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {
                'app_start_time': datetime.now().isoformat(),
                'total_api_requests': 0,
                'total_items_found': 0,
                'last_search_time': None
            }
    
    def _write_metrics(self, metrics):
        """Write metrics to database or file"""
        if self.use_database:
            self._write_metrics_to_db(metrics)
        else:
            self._write_metrics_to_file(metrics)
    
    def _write_metrics_to_db(self, metrics):
        """Write metrics to database"""
        try:
            from db import get_db
            db = get_db()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                for key, value in metrics.items():
                    # Convert values to strings for storage
                    str_value = str(value) if value is not None else ''
                    
                    if db.is_postgres:
                        cursor.execute("""
                            INSERT INTO metrics (key, value, updated_at) VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = CURRENT_TIMESTAMP
                        """, (key, str_value, str_value))
                    else:
                        cursor.execute("""
                            INSERT OR REPLACE INTO metrics (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (key, str_value))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error writing metrics to database: {e}")
            # Fallback to file storage
            self._write_metrics_to_file(metrics)
    
    def _write_metrics_to_file(self, metrics):
        """Write metrics to file"""
        try:
            with open(METRICS_FILE, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            print(f"Error writing metrics: {e}")
    
    def get_app_start_time(self):
        """Get app start time"""
        with self.lock:
            metrics = self._read_metrics()
            return datetime.fromisoformat(metrics['app_start_time'])
    
    def set_app_start_time(self, start_time):
        """Set app start time"""
        with self.lock:
            metrics = self._read_metrics()
            metrics['app_start_time'] = start_time.isoformat()
            self._write_metrics(metrics)
    
    def get_total_api_requests(self):
        """Get total API requests"""
        with self.lock:
            metrics = self._read_metrics()
            return metrics['total_api_requests']
    
    def increment_api_requests(self):
        """Increment API requests counter"""
        with self.lock:
            metrics = self._read_metrics()
            metrics['total_api_requests'] += 1
            self._write_metrics(metrics)
            return metrics['total_api_requests']
    
    def get_total_items_found(self):
        """Get total items found"""
        with self.lock:
            metrics = self._read_metrics()
            return metrics['total_items_found']
    
    def increment_items_found(self, count=1):
        """Increment items found counter"""
        with self.lock:
            metrics = self._read_metrics()
            metrics['total_items_found'] += count
            self._write_metrics(metrics)
            return metrics['total_items_found']
    
    def get_last_search_time(self):
        """Get last search time"""
        with self.lock:
            metrics = self._read_metrics()
            last_search = metrics['last_search_time']
            return datetime.fromisoformat(last_search) if last_search else None
    
    def set_last_search_time(self, search_time):
        """Set last search time"""
        with self.lock:
            metrics = self._read_metrics()
            metrics['last_search_time'] = search_time.isoformat()
            self._write_metrics(metrics)
    
    def get_all_stats(self):
        """Get all statistics"""
        with self.lock:
            metrics = self._read_metrics()
            return {
                'app_start_time': datetime.fromisoformat(metrics['app_start_time']),
                'total_api_requests': metrics['total_api_requests'],
                'total_items_found': metrics['total_items_found'],
                'last_search_time': datetime.fromisoformat(metrics['last_search_time']) if metrics['last_search_time'] else None
            }

# Global instance
metrics_storage = MetricsStorage()

# Initialize app start time
metrics_storage.set_app_start_time(datetime.now())
print(f"[METRICS] Initialized at {datetime.now()}")
