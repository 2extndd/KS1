"""
Kufar.by web scraper for extracting ads data
Since Kufar doesn't provide public API, we use web scraping
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class KufarScraper:
    """Web scraper for Kufar.by"""
    
    def __init__(self, proxy: str = None):
        self.session = requests.Session()
        self.proxy = proxy
        
        # Set realistic headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if proxy:
            self.session.proxies.update({
                'http': proxy,
                'https': proxy
            })
    
    def search_ads(self, search_url: str, max_items: int = 50) -> List[Dict[str, Any]]:
        """Search for ads using Kufar URL"""
        try:
            # Make request to search page
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for initial state data
            ads_data = []
            
            # Method 1: Extract from script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    # Extract JSON data
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            initial_state = json.loads(match.group(1))
                            ads_data = self._extract_ads_from_state(initial_state)
                            break
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing initial state: {e}")
            
            # Method 2: Extract from ad cards in HTML
            if not ads_data:
                ads_data = self._extract_ads_from_html(soup)
            
            # Limit results
            return ads_data[:max_items]
            
        except Exception as e:
            logger.error(f"Error scraping Kufar: {e}")
            return []
    
    def _extract_ads_from_state(self, initial_state: Dict) -> List[Dict[str, Any]]:
        """Extract ads from initial state JSON"""
        ads = []
        
        try:
            # Navigate through the state structure to find ads
            # This structure may vary, so we try multiple paths
            possible_paths = [
                ['ads', 'list'],
                ['search', 'results'],
                ['listing', 'ads'],
                ['data', 'ads'],
                ['props', 'pageProps', 'ads']
            ]
            
            ads_list = None
            for path in possible_paths:
                current = initial_state
                try:
                    for key in path:
                        current = current[key]
                    if isinstance(current, list):
                        ads_list = current
                        break
                except (KeyError, TypeError):
                    continue
            
            if ads_list:
                for ad_data in ads_list:
                    if isinstance(ad_data, dict):
                        ads.append(self._normalize_ad_data(ad_data))
                        
        except Exception as e:
            logger.error(f"Error extracting ads from state: {e}")
        
        return ads
    
    def _extract_ads_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract ads from HTML structure"""
        ads = []
        
        try:
            # Updated selectors for modern Kufar
            ad_selectors = [
                # New Kufar selectors
                '[data-testid*="listing"]',
                '[data-testid*="ad"]',
                '[class*="listing"]',
                '[class*="CardComponent"]',
                '[class*="Card__root"]',
                'article',
                # Legacy selectors
                '.listing-card',
                '.ad-card',
                '.item-card',
                '[class*="AdCard"]',
                '[class*="ListingCard"]'
            ]
            
            for selector in ad_selectors:
                ad_elements = soup.select(selector)
                if ad_elements:
                    logger.info(f"Found {len(ad_elements)} ads with selector: {selector}")
                    
                    for element in ad_elements:
                        ad_data = self._extract_ad_from_element(element)
                        if ad_data:
                            ads.append(ad_data)
                    
                    if ads:
                        break
                        
        except Exception as e:
            logger.error(f"Error extracting ads from HTML: {e}")
        
        return ads
    
    def _extract_ad_from_element(self, element) -> Optional[Dict[str, Any]]:
        """Extract ad data from HTML element"""
        try:
            ad_data = {}
            
            # Extract title - updated selectors for modern Kufar
            title_selectors = [
                '[data-testid*="title"]', 
                '[data-testid*="subject"]',
                'h3', 'h2', 'h4',
                '.title', 
                'a[href*="/item/"]',
                'a[href*="/ad/"]',
                '[class*="Title"]',
                '[class*="Subject"]'
            ]
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 3:  # Make sure it's not empty or too short
                        ad_data['title'] = title_text
                        break
            
            # Extract price - updated selectors for modern Kufar
            price_selectors = [
                # Try to find price in various formats
                '[data-testid*="price"]', 
                '[data-testid*="cost"]',
                '.price', 
                '[class*="Price"]',
                '[class*="Cost"]',
                '[class*="price"]',
                # Common patterns on Kufar.by
                'span:contains("р.")',
                'div:contains("р.")',
                '[class*="listing"] span',
                '[class*="card"] span'
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = element.select_one(selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        # Look for price patterns: "100 р.", "1 500 р.", etc.
                        price_match = re.search(r'(\d+(?:\s+\d+)*)\s*р\.?', price_text)
                        if price_match:
                            try:
                                price_str = price_match.group(1).replace(' ', '')
                                ad_data['price'] = int(price_str)
                                break
                            except ValueError:
                                pass
                except:
                    continue
            
            # Extract URL - updated for modern Kufar
            link_selectors = ['a[href*="/item/"]', 'a[href*="/ad/"]', 'a[href]']
            for selector in link_selectors:
                link_elem = element.select_one(selector)
                if link_elem:
                    href = link_elem.get('href')
                    if href and ('/item/' in href or '/ad/' in href):
                        if href.startswith('/'):
                            ad_data['url'] = f"https://www.kufar.by{href}"
                        else:
                            ad_data['url'] = href
                        
                        # Extract ID from URL
                        id_match = re.search(r'/(?:item|ad)/(\d+)', href)
                        if id_match:
                            ad_data['ad_id'] = id_match.group(1)
                        break
            
            # Extract image
            # Extract image URL - improved selectors
            img_selectors = [
                'img[src*="rms.kufar.by"]',  # Real product images
                'img[data-src*="rms.kufar.by"]',
                'img[src*="kufar.by"]:not([src*="svg"])',  # Exclude SVG logos
                'img[data-src*="kufar.by"]:not([data-src*="svg"])',
                'img[src]',  # Fallback
                'img[data-src]'
            ]
            
            for selector in img_selectors:
                img_elem = element.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src and not src.startswith('data:') and 'svg' not in src.lower():
                        # Ensure full URL
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.kufar.by' + src
                        ad_data['images'] = [src]
                        break
            
            # Extract location
            location_selectors = [
                '[data-testid*="location"]', 
                '.location', 
                '[class*="Location"]',
                '[class*="region"]',
                '[class*="address"]',
                # Look for common location patterns
                'span:contains("Минск")',
                'span:contains("Гомель")', 
                'span:contains("Брест")',
                'span:contains("Витебск")',
                'span:contains("Гродно")',
                'span:contains("Могилёв")',
                'div:contains("область")',
                'span[class*="text-muted"]:contains(",")'
            ]
            for selector in location_selectors:
                try:
                    location_elem = element.select_one(selector)
                    if location_elem:
                        location_text = location_elem.get_text(strip=True)
                        # Filter out non-location text
                        if any(city in location_text for city in ['Минск', 'Гомель', 'Брест', 'Витебск', 'Гродно', 'Могилёв']) or 'область' in location_text:
                            ad_data['location'] = location_text
                            break
                except:
                    continue
            
            # Only return if we have at least title and URL
            if ad_data.get('title') and ad_data.get('url'):
                return ad_data
                
        except Exception as e:
            logger.error(f"Error extracting ad from element: {e}")
        
        return None
    
    def _normalize_ad_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize ad data to consistent format"""
        # For scraped data, the structure is different from API data
        normalized = {
            'ad_id': str(raw_data.get('ad_id', '')),
            'subject': raw_data.get('title', ''),  # Use 'title' from scraped data
            'body': raw_data.get('description', ''),
            'price_byn': raw_data.get('price', 0),
            'price_usd': 0,  # Not available in scraped data usually
            'images': raw_data.get('images', []),
            'area': {'name': raw_data.get('location', '')},  # Convert location to area format
            'account_parameters': {},
            'list_time': None,  # Not available in scraped data
            'refresh_time': None,
            'category': {},
            'url': raw_data.get('url', ''),  # Add URL to raw data
        }
        
        return normalized
