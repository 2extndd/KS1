"""
Proxy management for KF Searcher
Based on VS5 proxy system, handles proxy rotation and validation
"""

import requests
import random
import time
import logging
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from configuration_values import PROXY_LIST, PROXY_ENABLED

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages proxy rotation and validation"""
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or PROXY_LIST
        self.working_proxies = []
        self.failed_proxies = []
        self.current_proxy_index = 0
        self.last_validation = 0
        
        # Validate proxies on initialization
        if self.proxy_list and PROXY_ENABLED:
            self.validate_proxies()
    
    def validate_proxies(self, timeout: int = 10) -> None:
        """Validate all proxies in parallel"""
        if not self.proxy_list:
            logger.info("No proxies to validate")
            return
        
        logger.info(f"Validating {len(self.proxy_list)} proxies...")
        
        working = []
        failed = []
        
        # Use ThreadPoolExecutor for parallel validation
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {
                executor.submit(self._test_proxy, proxy, timeout): proxy 
                for proxy in self.proxy_list
            }
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    is_working = future.result()
                    if is_working:
                        working.append(proxy)
                        logger.debug(f"Proxy {proxy} is working")
                    else:
                        failed.append(proxy)
                        logger.debug(f"Proxy {proxy} failed")
                except Exception as e:
                    logger.error(f"Error testing proxy {proxy}: {e}")
                    failed.append(proxy)
        
        self.working_proxies = working
        self.failed_proxies = failed
        self.last_validation = time.time()
        
        logger.info(f"Proxy validation completed: {len(working)} working, {len(failed)} failed")
    
    def _test_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """Test if a single proxy is working"""
        try:
            # Format proxy URL
            if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                proxy_url = f"http://{proxy}"
            else:
                proxy_url = proxy
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Test proxy with a simple request
            response = requests.get(
                'https://www.kufar.by',
                proxies=proxies,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"Proxy {proxy} test failed: {e}")
            return False
    
    def get_proxy(self) -> Optional[str]:
        """Get next working proxy in rotation"""
        if not self.working_proxies:
            logger.warning("No working proxies available")
            return None
        
        # Check if we need to revalidate proxies (every hour)
        if time.time() - self.last_validation > 3600:
            logger.info("Revalidating proxies...")
            self.validate_proxies()
        
        if not self.working_proxies:
            return None
        
        # Get next proxy in rotation
        proxy = self.working_proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.working_proxies)
        
        return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Get random working proxy"""
        if not self.working_proxies:
            return None
        
        return random.choice(self.working_proxies)
    
    def mark_proxy_failed(self, proxy: str) -> None:
        """Mark proxy as failed and remove from working list"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            if proxy not in self.failed_proxies:
                self.failed_proxies.append(proxy)
            logger.info(f"Marked proxy {proxy} as failed")
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        return {
            'total_proxies': len(self.proxy_list),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'last_validation': self.last_validation,
            'current_proxy_index': self.current_proxy_index
        }
    
    def refresh_failed_proxies(self) -> None:
        """Re-test failed proxies and move working ones back"""
        if not self.failed_proxies:
            return
        
        logger.info(f"Re-testing {len(self.failed_proxies)} failed proxies...")
        
        newly_working = []
        still_failed = []
        
        for proxy in self.failed_proxies:
            if self._test_proxy(proxy):
                newly_working.append(proxy)
            else:
                still_failed.append(proxy)
        
        # Update lists
        self.working_proxies.extend(newly_working)
        self.failed_proxies = still_failed
        
        if newly_working:
            logger.info(f"Recovered {len(newly_working)} proxies")

class ProxyRotator:
    """Simple proxy rotator for requests"""
    
    def __init__(self, proxy_manager: ProxyManager = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.current_proxy = None
        self.request_count = 0
        self.max_requests_per_proxy = 100  # Change proxy after N requests
    
    def get_proxies_dict(self) -> Dict[str, str]:
        """Get proxies dictionary for requests"""
        # Change proxy if needed
        if (self.current_proxy is None or 
            self.request_count >= self.max_requests_per_proxy):
            self.current_proxy = self.proxy_manager.get_proxy()
            self.request_count = 0
        
        if not self.current_proxy:
            return {}
        
        # Format proxy URL
        if not self.current_proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            proxy_url = f"http://{self.current_proxy}"
        else:
            proxy_url = self.current_proxy
        
        self.request_count += 1
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def mark_current_proxy_failed(self):
        """Mark current proxy as failed"""
        if self.current_proxy:
            self.proxy_manager.mark_proxy_failed(self.current_proxy)
            self.current_proxy = None
            self.request_count = 0

# Global proxy manager instance
proxy_manager = ProxyManager()
proxy_rotator = ProxyRotator(proxy_manager)
