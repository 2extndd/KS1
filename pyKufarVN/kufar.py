"""
Main Kufar class for API interaction
Entry point for pyKufarVN library
"""

import requests
import logging
from typing import Optional
from fake_useragent import UserAgent

from .items import Items
from .exceptions import KufarException, KufarConnectionException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuration_values import DEFAULT_HEADERS, PROXY_ENABLED, PROXY_LIST

logger = logging.getLogger(__name__)

class Kufar:
    """Main class for interacting with Kufar.by API"""
    
    def __init__(self, proxy: str = None, user_agent: str = None):
        """
        Initialize Kufar client
        
        Args:
            proxy: Proxy URL (optional)
            user_agent: Custom user agent (optional)
        """
        self.session = requests.Session()
        self.proxy = proxy
        self.user_agent = user_agent or self._get_random_user_agent()
        
        # Setup session
        self._setup_session()
        
        # Initialize items handler
        self.items = Items(session=self.session, proxy=self.proxy)
        
        logger.info("Kufar client initialized")
    
    def _setup_session(self):
        """Setup requests session with headers and proxy"""
        # Set headers
        headers = DEFAULT_HEADERS.copy()
        headers['User-Agent'] = self.user_agent
        self.session.headers.update(headers)
        
        # Set proxy if provided
        if self.proxy:
            self.session.proxies.update({
                'http': self.proxy,
                'https': self.proxy
            })
            logger.info(f"Using proxy: {self.proxy}")
        elif PROXY_ENABLED and PROXY_LIST:
            # Use random proxy from list
            import random
            self.proxy = random.choice(PROXY_LIST)
            self.session.proxies.update({
                'http': self.proxy,
                'https': self.proxy
            })
            logger.info(f"Using random proxy: {self.proxy}")
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent string"""
        try:
            ua = UserAgent()
            return ua.random
        except:
            # Fallback to default if UserAgent fails
            return DEFAULT_HEADERS['User-Agent']
    
    def test_connection(self) -> bool:
        """Test connection to Kufar.by"""
        try:
            response = self.session.get("https://www.kufar.by", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def change_proxy(self, new_proxy: str = None):
        """Change proxy for current session"""
        if new_proxy:
            self.proxy = new_proxy
        elif PROXY_ENABLED and PROXY_LIST:
            import random
            self.proxy = random.choice(PROXY_LIST)
        else:
            self.proxy = None
        
        # Update session proxy
        if self.proxy:
            self.session.proxies.update({
                'http': self.proxy,
                'https': self.proxy
            })
            logger.info(f"Changed proxy to: {self.proxy}")
        else:
            self.session.proxies.clear()
            logger.info("Removed proxy")
        
        # Update items handler proxy
        self.items.proxy = self.proxy
    
    def get_session_info(self) -> dict:
        """Get current session information"""
        return {
            'proxy': self.proxy,
            'user_agent': self.user_agent,
            'headers': dict(self.session.headers),
            'proxies': dict(self.session.proxies)
        }
