"""
Core logic for KF Searcher
Based on VS5 core module, adapted for Kufar.by
"""

import logging
import time
import random
import pytz
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs

from pyKufarVN import Kufar, KufarException, KufarAPIException
from db import get_db
from configuration_values import (
    get_max_items_per_search,
    ERROR_CODES_FOR_REDEPLOY,
    KF_REGIONS,
    KF_CATEGORIES
)

logger = logging.getLogger(__name__)

class KufarSearcher:
    """Main searcher class for Kufar.by monitoring"""
    
    def __init__(self):
        self.kufar_client = None
        self.error_count = 0
        self.last_proxy_change = 0
        
        # Initialize Kufar client
        self._init_kufar_client()
    
    def _init_kufar_client(self):
        """Initialize Kufar API client"""
        try:
            self.kufar_client = Kufar()
            
            # Test connection
            if not self.kufar_client.test_connection():
                logger.warning("Initial connection test failed")
                self._change_proxy_if_needed()
            else:
                logger.info("Kufar client initialized successfully")
            get_db().add_log_entry('INFO', 'Kufar client initialized successfully', 'KufarSearcher')
                
        except Exception as e:
            logger.error(f"Failed to initialize Kufar client: {e}")
            raise
    
    def _change_proxy_if_needed(self):
        """Change proxy if connection issues"""
        current_time = time.time()
        
        # Change proxy max once per 5 minutes
        if current_time - self.last_proxy_change > 300:
            try:
                self.kufar_client.change_proxy()
                self.last_proxy_change = current_time
                logger.info("Changed proxy due to connection issues")
            except Exception as e:
                logger.error(f"Failed to change proxy: {e}")
    
    def search_all_queries(self) -> Dict[str, Any]:
        """Search all active queries and return results summary - простая логика"""
        logger.info("🔍 Запуск цикла сканирования")
        get_db().add_log_entry('INFO', 'Запуск цикла сканирования', 'core', 'Проверка готовности фильтров к обновлению')
        
        results = {
            'total_searches': 0,
            'ready_for_scan': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'new_items': 0,
            'skipped_searches': 0,
            'errors': []
        }
        
        try:
            # Получаем настройку интервала сканирования
            from configuration_values import get_search_interval
            interval_seconds = get_search_interval()
            
            # Получаем ВСЕ активные поиски для анализа
            all_searches = get_db().get_active_searches()
            results['total_searches'] = len(all_searches)
            
            if not all_searches:
                logger.info("❌ Нет активных поисков в системе")
                get_db().add_log_entry('INFO', 'Нет активных поисков в системе', 'core', 'Система простаивает')
                return results
            
            # Простая логика: определяем какие поиски готовы для сканирования
            ready_searches = []
            now = get_db().get_belarus_time()
            
            logger.info(f"📋 Анализируем {len(all_searches)} активных поисков (интервал: {interval_seconds}с)")
            
            for search in all_searches:
                last_scan = search.get('last_scan_time')
                if not last_scan:
                    # Никогда не сканировался - готов к сканированию
                    ready_searches.append(search)
                    logger.info(f"✅ '{search['name']}': никогда не сканировался, добавляем в очередь")
                else:
                    # Преобразуем время в правильный формат если нужно
                    if isinstance(last_scan, str):
                        try:
                            # Парсим строку времени
                            last_scan = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
                            # Конвертируем в белорусский часовой пояс
                            if last_scan.tzinfo is None:
                                last_scan = last_scan.replace(tzinfo=pytz.UTC)
                            from db import BELARUS_TZ
                            last_scan = last_scan.astimezone(BELARUS_TZ)
                        except:
                            logger.warning(f"Не удалось распарсить время для '{search['name']}', считаем готовым")
                            ready_searches.append(search)
                            continue
                    elif hasattr(last_scan, 'tzinfo') and last_scan.tzinfo is None:
                        # Добавляем часовой пояс если его нет
                        from db import BELARUS_TZ
                        last_scan = last_scan.replace(tzinfo=BELARUS_TZ)
                    
                    # Проверяем прошел ли интервал
                    time_since_scan = (now - last_scan).total_seconds()
                    if time_since_scan >= interval_seconds:
                        ready_searches.append(search)
                        minutes_ago = int(time_since_scan // 60)
                        seconds_ago = int(time_since_scan % 60)
                        logger.info(f"✅ '{search['name']}': последнее сканирование {minutes_ago}м {seconds_ago}с назад (интервал: {interval_seconds}с)")
                    else:
                        remaining = interval_seconds - time_since_scan
                        remaining_minutes = int(remaining // 60)
                        remaining_seconds = int(remaining % 60)
                        logger.debug(f"⏱️ '{search['name']}': ожидание еще {remaining_minutes}м {remaining_seconds}с")
                        results['skipped_searches'] += 1
            
            results['ready_for_scan'] = len(ready_searches)
            
            if not ready_searches:
                logger.info(f"⏱️ Нет поисков готовых для сканирования (интервал: {interval_seconds}с)")
                get_db().add_log_entry('INFO', f'Все поиски ожидают интервала ({interval_seconds}с)', 'core', 'Следующий цикл через минуту')
                return results
            
            logger.info(f"🚀 Начинаем сканирование {len(ready_searches)} готовых поисков")
            get_db().add_log_entry('INFO', f'Сканируем {len(ready_searches)} готовых поисков', 'core', f'Обрабатываем {len(ready_searches)} из {len(all_searches)} поисков')
            
            # Обрабатываем каждый готовый поиск
            for search in ready_searches:
                try:
                    logger.info(f"Processing search: {search['name']} (ID: {search['id']})")
                    get_db().add_log_entry('INFO', f"[DEBUG] Processing search: {search['name']}", 'core', f"Starting search for query ID {search['id']}")
                    
                    # Search for items
                    items = self.search_query(search)
                    total_items = len(items)
                    
                    if items:
                        # Process new items
                        new_items = self._process_new_items(items, search)
                        new_count = len(new_items)
                        duplicate_count = total_items - new_count
                        
                        results['new_items'] += new_count
                        
                        # Log in VS5 style with detailed statistics
                        if new_count > 0:
                            logger.info(f"[SEARCH] '{search['name']}': {total_items} total, {new_count} new, {duplicate_count} duplicates")
                            get_db().add_log_entry('INFO', 
                                           f"Search completed: {search['name']}", 
                                           'core', 
                                           f"Query ID {search['id']}: {total_items} total items, {new_count} new items, {duplicate_count} duplicates")
                        else:
                            logger.info(f"[SEARCH] '{search['name']}': {total_items} items found, all duplicates")
                            get_db().add_log_entry('INFO', 
                                           f"Search completed (all duplicates): {search['name']}", 
                                           'core', 
                                           f"Query ID {search['id']}: {total_items} items found, but all were duplicates")
                        
                        # Send telegram notifications for new items
                        for item in new_items:
                            try:
                                from simple_telegram_worker import send_notification_for_item
                                send_notification_for_item(item)
                                logger.debug(f"Telegram notification sent for item {item['kufar_id']}")
                            except Exception as e:
                                logger.error(f"Failed to send telegram notification: {e}")
                                get_db().add_log_entry('ERROR', f"Failed to send telegram notification: {str(e)}", 'core', f"Notification error for item {item['kufar_id']}")
                    else:
                        logger.info(f"[SEARCH] '{search['name']}': No items found")
                        get_db().add_log_entry('INFO', 
                                       f"Search completed (empty): {search['name']}", 
                                       'core', 
                                       f"Query ID {search['id']}: No items found on Kufar")
                    
                    results['successful_searches'] += 1
                    
                    # Обновляем время последнего сканирования
                    get_db().update_search_scan_time(search['id'])
                    logger.info(f"Обновлено время сканирования для поиска '{search['name']}'")
                    
                    # Add delay between searches
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Failed to process search '{search['name']}': {e}")
                    results['failed_searches'] += 1
                    results['errors'].append({
                        'search_id': search['id'],
                        'search_name': search['name'],
                        'error': str(e)
                    })
                    
                    # Log error to database
                    if isinstance(e, KufarAPIException) and e.status_code:
                        get_db().log_error(e.status_code, str(e), search['id'])
                        
                        # Check if should trigger redeploy
                        if e.status_code in ERROR_CODES_FOR_REDEPLOY:
                            self.error_count += 1
            
            # Подробная статистика завершения
            logger.info(f"🏁 Цикл сканирования завершен:")
            logger.info(f"   • Всего поисков: {results['total_searches']}")
            logger.info(f"   • Готовых к сканированию: {results['ready_for_scan']}")
            logger.info(f"   • Успешных: {results['successful_searches']}")
            logger.info(f"   • Неудачных: {results['failed_searches']}")
            logger.info(f"   • Пропущенных: {results['skipped_searches']}")
            logger.info(f"   • Новых объявлений: {results['new_items']}")
            
            if results['ready_for_scan'] > 0:
                get_db().add_log_entry('INFO', 
                               f"Цикл завершен: {results['successful_searches']}/{results['ready_for_scan']} успешных, {results['new_items']} новых", 
                               'core', 
                               f"Статистика: {results}")
            else:
                get_db().add_log_entry('INFO', 
                               f"Ожидание: {results['skipped_searches']} поисков ждут интервала ({interval_seconds}с)", 
                               'core', 
                               'Все поиски в режиме ожидания')
            
            return results
            
        except Exception as e:
            logger.error(f"Error in search_all_queries: {e}")
            results['errors'].append({'error': str(e)})
            return results
    
    def search_query(self, search: Dict[str, Any]) -> List[Any]:
        """Search for items using a single query"""
        try:
            if not self.kufar_client:
                self._init_kufar_client()
            
            # Search using Kufar API
            max_items_config = get_max_items_per_search()
            logger.info(f"🔧 Using MAX_ITEMS_PER_SEARCH setting: {max_items_config}")
            
            items = self.kufar_client.items.search(
                query_url=search['url'],
                max_items=max_items_config
            )
            
            logger.info(f"📦 Search returned {len(items)} items from Kufar for query '{search['name']}'")
            logger.info(f"🎯 Max items requested: {max_items_config}, actual items received: {len(items)}")
            
            # Update API request counter
            try:
                import metrics_storage
                total_requests = metrics_storage.metrics_storage.increment_api_requests()
                logger.info(f"📊 API request #{total_requests} completed for search query '{search['name']}'")
                
                # Also increment in shared_state for compatibility
                try:
                    import shared_state
                    shared_state.increment_api_requests()
                except:
                    pass
            except Exception as e:
                logger.error(f"Failed to increment API counter: {e}")
                # Log this as it affects metrics accuracy
                get_db().add_log_entry('ERROR', f'Failed to increment API counter: {e}', 'core', 'Metrics tracking error')
            
            return items
            
        except KufarAPIException as e:
            logger.error(f"Kufar API error for search {search['id']}: {e}")
            
            # Still increment API counter for failed requests
            try:
                import metrics_storage
                total_requests = metrics_storage.metrics_storage.increment_api_requests()
                logger.info(f"📊 API request #{total_requests} failed with error {e.status_code} for '{search['name']}'")
                
                # Log the failed API request
                get_db().add_log_entry('ERROR', f'Kufar API error {e.status_code}: {e}', 'core', f'Failed API request for search ID {search["id"]}')
                
                # Also increment in shared_state for compatibility
                try:
                    import shared_state
                    shared_state.increment_api_requests()
                except:
                    pass
            except Exception as counter_error:
                logger.error(f"Failed to increment API counter for error: {counter_error}")
            
            # Handle specific error codes
            if e.status_code in [403, 429]:
                self._change_proxy_if_needed()
            
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in search_query: {e}")
            
            # Still increment API counter for unexpected errors
            try:
                import metrics_storage
                total_requests = metrics_storage.metrics_storage.increment_api_requests()
                logger.info(f"📊 API request #{total_requests} failed with unexpected error for '{search['name']}'")
                
                # Log the unexpected error
                get_db().add_log_entry('ERROR', f'Unexpected search error: {e}', 'core', f'Unexpected error for search ID {search["id"]}')
                
                # Also increment in shared_state for compatibility
                try:
                    import shared_state
                    shared_state.increment_api_requests()
                except:
                    pass
            except Exception as counter_error:
                logger.error(f"Failed to increment API counter for unexpected error: {counter_error}")
            
            raise
    
    def _process_new_items(self, items: List[Any], search: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and save new items to database"""
        new_items = []
        
        for item in items:
            try:
                # Try to add item to database
                from configuration_values import get_telegram_chat_id
                
                # Extract size from item if available
                size_info = getattr(item, 'size', '')
                logger.info(f"🔍 SIZE DEBUG: Item '{item.title}' has size attribute: '{size_info}'")
                
                # Prepare raw_data with size information
                raw_data = item.raw_data.copy() if item.raw_data else {}
                if size_info:
                    raw_data['size'] = size_info
                    logger.info(f"🔍 SIZE DEBUG: Added size '{size_info}' to raw_data for '{item.title}'")
                
                item_data = {
                    'kufar_id': item.id,
                    'title': item.title,
                    'price': item.price,
                    'currency': item.currency,
                    'description': item.description,
                    'images': item.images,
                    'location': item.location,
                    'seller_name': item.seller_name,
                    'seller_phone': item.seller_phone,
                    'url': item.url,
                    'raw_data': raw_data,
                    'search_name': search.get('name', 'Unknown'),
                    'thread_id': search.get('telegram_thread_id')
                }
                
                item_id = get_db().add_item(item_data, search['id'])
                
                if item_id:  # New item was added
                    new_items.append({
                        'id': item_id,
                        'kufar_id': item.id,
                        'title': item.title,
                        'price': item.price,
                        'currency': item.currency,
                        'url': item.url,
                        'search_name': search['name'],
                        'thread_id': search.get('telegram_thread_id'),
                        'images': item.images,
                        'location': item.location,
                        'description': item.description,
                        'raw_data': raw_data  # Include raw_data with size
                    })
                
            except Exception as e:
                logger.error(f"Failed to process item {item.id}: {e}")
                continue
        
        return new_items
    
    def validate_search_url(self, url: str) -> Dict[str, Any]:
        """Validate and parse Kufar search URL"""
        try:
            parsed_url = urlparse(url)
            
            # Check if it's a valid Kufar URL
            if 'kufar.by' not in parsed_url.netloc:
                return {'valid': False, 'error': 'Not a Kufar.by URL'}
            
            # Parse query parameters
            query_params = parse_qs(parsed_url.query)
            
            # Extract useful information
            info = {
                'valid': True,
                'url': url,
                'query': query_params.get('q', [''])[0],
                'category': self._get_category_name(query_params.get('cat', [''])[0]),
                'region': self._get_region_name(query_params.get('rgn', [''])[0]),
                'price_from': query_params.get('prif', [''])[0],
                'price_to': query_params.get('prit', [''])[0],
                'parameters': query_params
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _get_category_name(self, category_id: str) -> str:
        """Get category name by ID"""
        # This would need to be populated with actual Kufar category mappings
        category_mapping = {
            '1000': 'Транспорт',
            '2000': 'Недвижимость',
            '3000': 'Работа',
            '4000': 'Услуги',
            '5000': 'Личные вещи',
            '6000': 'Для дома и дачи',
            '7000': 'Бытовая электроника',
            '8000': 'Хобби и отдых',
            '9000': 'Животные и растения',
            '10000': 'Для бизнеса'
        }
        
        return category_mapping.get(category_id, category_id)
    
    def _get_region_name(self, region_id: str) -> str:
        """Get region name by ID"""
        # This would need to be populated with actual Kufar region mappings
        region_mapping = {
            '1': 'Минск',
            '2': 'Минская область',
            '3': 'Брестская область',
            '4': 'Витебская область',
            '5': 'Гомельская область',
            '6': 'Гродненская область',
            '7': 'Могилёвская область'
        }
        
        return region_mapping.get(region_id, region_id)
    
    def get_searcher_status(self) -> Dict[str, Any]:
        """Get current searcher status"""
        return {
            'client_initialized': self.kufar_client is not None,
            'error_count': self.error_count,
            'proxy_info': self.kufar_client.get_session_info() if self.kufar_client else None,
            'last_proxy_change': self.last_proxy_change
        }
    
    def reset_error_count(self):
        """Reset error count (useful after successful redeploy)"""
        self.error_count = 0
        logger.info("Error count reset")

# Global searcher instance
searcher = KufarSearcher()
