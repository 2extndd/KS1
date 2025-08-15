"""
Items module for Kufar.by API interaction
Handles searching and processing of Kufar advertisements
"""

import requests
import time
import random
import json
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime

from .exceptions import (
    KufarAPIException, 
    KufarConnectionException, 
    KufarParsingException,
    KufarRateLimitException,
    KufarBlockedException
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuration_values import (
    KF_BASE_URL, 
    KF_API_BASE_URL,
    DEFAULT_HEADERS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX
)

logger = logging.getLogger(__name__)

class Item:
    """Represents a single Kufar advertisement"""
    
    def __init__(self, data: Dict[str, Any]):
        self.raw_data = data
        self._parse_item_data()
    
    def _parse_item_data(self):
        """Parse raw item data from Kufar API response"""
        try:
            # Basic item information
            self.id = str(self.raw_data.get('ad_id', ''))
            self.title = self.raw_data.get('subject', '')
            self.description = self.raw_data.get('body', '')
            
            # Price information
            price_byn = self.raw_data.get('price_byn')
            price_usd = self.raw_data.get('price_usd')
            
            if price_byn:
                self.price = int(price_byn)
                self.currency = 'BYN'
            elif price_usd:
                self.price = int(price_usd)
                self.currency = 'USD'
            else:
                self.price = 0
                self.currency = 'BYN'
            
            # Location information
            self.location = self._parse_location()
            
            # Images
            self.images = self._parse_images()
            
            # URL
            self.url = f"{KF_BASE_URL}/item/{self.id}"
            
            # Seller information
            self.seller_name = self.raw_data.get('account_parameters', {}).get('name', '')
            self.seller_phone = self._extract_phone()
            
            # Timestamps
            self.created_at = self._parse_timestamp(self.raw_data.get('list_time'))
            self.updated_at = self._parse_timestamp(self.raw_data.get('refresh_time'))
            
            # Category
            self.category = self._parse_category()
            
        except Exception as e:
            logger.error(f"Error parsing item data: {e}")
            raise KufarParsingException(f"Failed to parse item data: {e}")
    
    def _parse_location(self) -> str:
        """Parse location from item data"""
        try:
            area = self.raw_data.get('area', {})
            if isinstance(area, dict):
                return area.get('name', '')
            return str(area) if area else ''
        except:
            return ''
    
    def _parse_images(self) -> List[str]:
        """Parse images from item data"""
        try:
            images = []
            image_data = self.raw_data.get('images', [])
            
            if isinstance(image_data, list):
                for img in image_data:
                    if isinstance(img, dict):
                        # Get different sizes, prefer larger ones
                        for size in ['780x520', '570x380', '320x213']:
                            if size in img:
                                images.append(img[size])
                                break
                    elif isinstance(img, str):
                        images.append(img)
            
            return images[:5]  # Limit to 5 images
        except:
            return []
    
    def _extract_phone(self) -> str:
        """Extract phone number from account parameters"""
        try:
            account = self.raw_data.get('account_parameters', {})
            return account.get('phone', '')
        except:
            return ''
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Parse timestamp from various formats"""
        if not timestamp:
            return None
        
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # Try different timestamp formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d.%m.%Y %H:%M']:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
        except:
            pass
        
        return None
    
    def _parse_category(self) -> str:
        """Parse category information"""
        try:
            category = self.raw_data.get('category', {})
            if isinstance(category, dict):
                return category.get('name', '')
            return str(category) if category else ''
        except:
            return ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'currency': self.currency,
            'location': self.location,
            'images': self.images,
            'url': self.url,
            'seller_name': self.seller_name,
            'seller_phone': self.seller_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'category': self.category,
            'raw_data': self.raw_data
        }

class Items:
    """Handles searching and retrieving items from Kufar.by"""
    
    def __init__(self, session: requests.Session = None, proxy: str = None):
        self.session = session or requests.Session()
        self.proxy = proxy
        self.last_request_time = 0
        
        # Set default headers
        self.session.headers.update(DEFAULT_HEADERS)
        
        # Set proxy if provided
        if self.proxy:
            self.session.proxies.update({
                'http': self.proxy,
                'https': self.proxy
            })
    
    def _make_request(self, url: str, params: Dict = None, retries: int = 3) -> Dict:
        """Make HTTP request with error handling and rate limiting"""
        self._rate_limit()
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    raise KufarBlockedException(f"Access forbidden (403)", response.status_code)
                elif response.status_code == 429:
                    raise KufarRateLimitException(f"Rate limit exceeded (429)", response.status_code)
                elif response.status_code == 404:
                    raise KufarAPIException(f"Not found (404)", response.status_code)
                else:
                    raise KufarAPIException(f"HTTP {response.status_code}", response.status_code)
                    
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise KufarConnectionException(f"Connection error: {e}")
                
                # Wait before retry
                time.sleep(random.uniform(2, 5))
        
        raise KufarConnectionException("Max retries exceeded")
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        min_delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search(self, query_url: str, max_items: int = 50) -> List[Item]:
        """Search for items using Kufar URL via web scraping"""
        try:
            # Import scraper
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from kufar_scraper import KufarScraper
            
            # Create scraper instance
            scraper = KufarScraper(proxy=self.proxy)
            
            # Search for ads
            ads_data = scraper.search_ads(query_url, max_items)
            
            # Convert to Item objects
            items = []
            for ad_data in ads_data:
                try:
                    item = Item(ad_data)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse item: {e}")
                    continue
            
            logger.info(f"Found {len(items)} items for query")
            return items
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _parse_search_url(self, url: str) -> Dict[str, Any]:
        """Parse Kufar search URL to extract API parameters"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Convert query parameters to API format for real Kufar API
            api_params = {
                'size': '50',  # Number of results
                'sort': 'lst',  # Sort by listing time
                'offset': '0',
                'lang': 'ru'
            }
            
            # Map Kufar.by parameters to API format
            if 'query' in query_params or 'q' in query_params:
                query = query_params.get('query', query_params.get('q', ['']))[0]
                if query:
                    api_params['query'] = query
            
            if 'cat' in query_params:
                api_params['cat'] = query_params['cat'][0]
                
            if 'rgn' in query_params:
                api_params['rgn'] = query_params['rgn'][0]
                
            if 'price_from' in query_params or 'prif' in query_params:
                price_from = query_params.get('price_from', query_params.get('prif', ['']))[0]
                if price_from:
                    api_params['price_from'] = price_from
                    
            if 'price_to' in query_params or 'prit' in query_params:
                price_to = query_params.get('price_to', query_params.get('prit', ['']))[0]
                if price_to:
                    api_params['price_to'] = price_to
            
            # Add common filters
            if 'cmp' in query_params:
                api_params['cmp'] = query_params['cmp'][0]
                
            if 'typ' in query_params:
                api_params['typ'] = query_params['typ'][0]
            
            return api_params
            
        except Exception as e:
            logger.error(f"Failed to parse URL {url}: {e}")
            # Return basic parameters if parsing fails
            return {'size': '50', 'sort': 'lst', 'offset': '0', 'lang': 'ru'}
    
    def get_item_details(self, item_id: str) -> Optional[Item]:
        """Get detailed information about specific item"""
        try:
            api_url = f"{KF_API_BASE_URL}/ad/{item_id}"
            response_data = self._make_request(api_url)
            
            ad_data = response_data.get('ad', {})
            if ad_data:
                return Item(ad_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get item details for {item_id}: {e}")
            return None
