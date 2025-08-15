"""
Shared state for tracking application metrics
"""
from datetime import datetime
import threading

# Thread-safe state management
_lock = threading.Lock()
_state = {
    'app_start_time': datetime.now(),
    'total_api_requests': 0,
    'total_items_found': 0,
    'last_search_time': None
}

def get_app_start_time():
    with _lock:
        return _state['app_start_time']

def set_app_start_time(start_time):
    with _lock:
        _state['app_start_time'] = start_time

def get_total_api_requests():
    with _lock:
        return _state['total_api_requests']

def increment_api_requests():
    with _lock:
        _state['total_api_requests'] += 1
        return _state['total_api_requests']

def get_total_items_found():
    with _lock:
        return _state['total_items_found']

def increment_items_found(count=1):
    with _lock:
        _state['total_items_found'] += count
        return _state['total_items_found']

def get_last_search_time():
    with _lock:
        return _state['last_search_time']

def set_last_search_time(search_time):
    with _lock:
        _state['last_search_time'] = search_time

def get_all_stats():
    with _lock:
        return dict(_state)

# Initialize when module is imported
print(f"[SHARED_STATE] Initialized at {_state['app_start_time']}")
