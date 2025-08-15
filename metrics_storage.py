"""
Persistent metrics storage using file-based approach
"""
import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path

METRICS_FILE = "/tmp/kufar_metrics.json"

class MetricsStorage:
    def __init__(self):
        self.lock = threading.Lock()
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
