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
        """Search for ads using Kufar URL - simplified approach first"""
        try:
            logger.info(f"🔍 Scraping Kufar URL: {search_url}")
            
            # Make request to search page
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for initial state data first
            ads_data = []
            
            # Method 1: Extract from script tags (preferred)
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    # Extract JSON data
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            initial_state = json.loads(match.group(1))
                            ads_data = self._extract_ads_from_state(initial_state)
                            logger.info(f"📦 Extracted {len(ads_data)} ads from initial state")
                            break
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing initial state: {e}")
            
            # Method 2: Extract from HTML structure if initial state failed
            if not ads_data:
                logger.info("🔄 Fallback to HTML extraction")
                ads_data = self._extract_ads_from_html(soup)
                logger.info(f"📦 Extracted {len(ads_data)} ads from HTML")
            
            # Method 3: Simple text parsing as last resort
            if not ads_data:
                logger.info("🔄 Fallback to text-based extraction")
                ads_data = self._extract_ads_from_text(soup)
                logger.info(f"📦 Extracted {len(ads_data)} ads from text parsing")
            
            # Limit results to requested amount
            final_result = ads_data[:max_items]
            logger.info(f"🔧 KufarScraper final: max_items={max_items}, found={len(ads_data)}, returning={len(final_result)}")
            return final_result
            
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
            # Realistic selectors based on actual Kufar structure
            ad_selectors = [
                # Links to item pages (most reliable)
                'a[href*="/item/"]',
                'a[href*="/ad/"]',
                # Common card selectors
                '[class*="card"]',
                '[class*="Card"]',
                '[class*="listing"]',
                '[class*="Listing"]',
                '[class*="item"]',
                '[class*="Item"]',
                # Data attributes
                '[data-testid*="listing"]',
                '[data-testid*="ad"]', 
                '[data-testid*="item"]',
                '[data-testid*="card"]',
                # Generic containers that might hold ads
                'article',
                'section',
                '.row > div',  # Bootstrap-style grid
                '.col > div',
                # Div containing price patterns
                'div:contains("р.")',
                'div:contains("BYN")',
                'div:contains("USD")',
            ]
            
            # Method 1: Find all links to items (most reliable)
            item_links = soup.find_all('a', href=True)
            item_links = [link for link in item_links if '/item/' in link.get('href', '')]
            
            logger.info(f"Found {len(item_links)} item links")
            
            if item_links:
                for i, link in enumerate(item_links):
                    try:
                        # Extract data from link and its parent containers
                        ad_data = self._extract_ad_from_link(link, i)
                        if ad_data:
                            ads.append(ad_data)
                    except Exception as e:
                        logger.debug(f"Error processing link {i}: {e}")
                        continue
            
            # Method 2: If no item links, try selector-based approach
            if not ads:
                logger.info("🔄 No item links found, trying selectors")
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
    
    def _extract_ads_from_text(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract ads using text patterns as last resort"""
        ads = []
        
        try:
            # Get all text from the page
            page_text = soup.get_text()
            
            # Look for price patterns that indicate ads
            import re
            
            # Pattern to find prices (e.g., "125 р.", "40 р.", etc.)
            price_pattern = r'(\d+)\s*р\.'
            prices = re.findall(price_pattern, page_text)
            
            logger.info(f"Found {len(prices)} price patterns in text")
            
            # For each price, try to find associated title and URL
            for i, price in enumerate(prices[:50]):  # Limit to first 50 matches
                try:
                    # Create a basic ad structure
                    ad_data = {
                        'ad_id': f'text_extracted_{i}',
                        'title': f'Item {i+1}',  # Placeholder title
                        'price': int(price),
                        'currency': 'BYN',
                        'description': f'Price: {price} р.',
                        'url': '',  # Will be filled if we find a link
                        'images': [],
                        'location': 'Минск',  # Default location
                        'size': ''
                    }
                    
                    ads.append(ad_data)
                    
                except (ValueError, AttributeError):
                    continue
            
            logger.info(f"Text extraction created {len(ads)} ad entries")
            
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
        
        return ads
    
    def _extract_ad_from_link(self, link, index: int) -> Optional[Dict[str, Any]]:
        """Extract ad data from item link and surrounding context"""
        try:
            # Get the URL
            url = link.get('href', '')
            if not url.startswith('http'):
                url = 'https://www.kufar.by' + url
            
            # Extract ID from URL
            import re
            id_match = re.search(r'/item/(\d+)', url)
            ad_id = id_match.group(1) if id_match else f'extracted_{index}'
            
            # Try to find parent container that might have all the ad info
            parent = link.parent
            for _ in range(5):  # Go up to 5 levels to find the ad container
                if parent is None:
                    break
                    
                # Look for price in this container
                price_text = parent.get_text()
                price_match = re.search(r'(\d+)\s*р\.', price_text)
                
                if price_match:
                    # Found price, this might be the ad container
                    price = int(price_match.group(1))
                    
                    # Extract title more intelligently
                    title = self._extract_title_from_container(link, parent)
                    
                    if not title or len(title) < 3:
                        title = f"Item {index + 1}"
                    
                    # Extract size information more intelligently
                    size = self._extract_size_from_container_smart(parent)
                    
                    # Try to extract location more intelligently  
                    location = self._extract_location_from_container_smart(parent)
                    
                    # Extract images from the container
                    images = self._extract_images_from_container(parent)
                    
                    ad_data = {
                        'ad_id': ad_id,
                        'title': title,
                        'price': price,
                        'currency': 'BYN',
                        'description': title,
                        'url': url,
                        'images': images,
                        'location': location,
                        'size': size
                    }
                    
                    logger.debug(f"📄 Extracted ad: {title} - {price} р. - {size}")
                    return ad_data
                
                parent = parent.parent
            
            # If no price found, create basic entry
            title = link.get_text(strip=True) or f"Item {index + 1}"
            ad_data = {
                'ad_id': ad_id,
                'title': title,
                'price': 0,
                'currency': 'BYN',
                'description': title,
                'url': url,
                'images': [],
                'location': '',
                'size': ''
            }
            
            return ad_data
            
        except Exception as e:
            logger.debug(f"Error extracting ad from link: {e}")
            return None
    
    def _extract_size_from_container_text(self, text: str) -> str:
        """Extract size from container text like '48 (M)' or '52 (XL)'"""
        import re
        
        # Patterns for sizes commonly found on Kufar
        size_patterns = [
            r'(\d{2,3}\s*\([XSMLXL]+\))',  # 48 (M), 52 (XL)
            r'(\d{2,3}-\d{2,3}\s*\([XSMLXL]+\))',  # 52-54 (XXL)
            r'(\d{2,3}[.,]\d{1,2})',  # 39.5 (shoes)
            r'\b(\d{2,3})\s*\(',  # Just number before parentheses
            r'\b([XSMLXL]{1,3})\b',  # Just size letters
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                size = match.group(1)
                # Validate it's actually a clothing size
                if self._is_valid_size_quick(size):
                    return size
        
        return ''
    
    def _extract_size_from_container_smart(self, parent) -> str:
        """Extract size from REAL Kufar structure - sizes appear after price"""
        import re
        
        # Method 1: Look for size patterns after price in real Kufar structure
        # Real Kufar shows sizes like: "15 р. Рубашка белая школьная, размер L 50 (L)"
        full_text = parent.get_text()
        
        # Look for sizes in typical Kufar format: after "р." and before badges
        kufar_size_patterns = [
            # Pattern: "15 р.от X р. в месяцТекст товара 48 (M), 50 (L)badge"
            r'р\.(?:от\s+[\d,]+\s*р\.\s*в\s*месяц)?[^0-9]+?(\d{2,3}\s*\([XSMLXL]+\)(?:\s*,\s*\d{2,3}\s*\([XSMLXL]+\))*)',
            
            # Pattern: "р. название товара размер 50 (L)"
            r'р\.[^0-9]+?размер\s+([XSMLXL]|\d{2,3}(?:\s*\([XSMLXL]+\))?)',
            
            # Pattern: just after price without other numbers in between 
            r'р\.[^0-9]*?(\d{2,3}\s*\([XSMLXL]+\))',
            
            # Pattern: standalone sizes in the middle of text
            r'\b(\d{2,3}\s*\([XSMLXL]+\))(?:\s*,\s*(\d{2,3}\s*\([XSMLXL]+\)))*',
            
            # Pattern: sizes after clothing items mention
            r'(?:рубашка|футболка|куртка|брюки|джинсы|костюм|свитер)[^0-9]*?(\d{2,3}(?:\s*\([XSMLXL]+\))?)',
        ]
        
        for pattern in kufar_size_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Take first non-empty element from tuple
                        size_candidate = next((m for m in match if m), '')
                    else:
                        size_candidate = match
                    
                    if size_candidate and self._is_valid_size_quick(size_candidate):
                        logger.debug(f"📏 Found size with pattern: {size_candidate}")
                        return size_candidate.strip()
        
        # Method 2: Look for sizes in smaller text elements (might be separate spans)
        small_elements = parent.find_all(['span', 'div', 'small'], string=re.compile(r'\d{2,3}\s*\([XSMLXL]+\)'))
        for elem in small_elements:
            text = elem.get_text(strip=True)
            size = self._extract_size_from_container_text(text)
            if size and self._is_valid_size_quick(size):
                logger.debug(f"📏 Found size in small element: {size}")
                return size
        
        # Method 3: Look for common size text patterns
        size_text_patterns = [
            r'размер\s+([XSMLXL]|\d{2,3})',
            r'р-р\s+(\d{2,3})',
            r'\b([XSMLXL]{1,3})\b(?!\s*размер)',  # Standalone size letters
        ]
        
        for pattern in size_text_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                size_candidate = match.group(1)
                if self._is_valid_size_quick(size_candidate):
                    logger.debug(f"📏 Found size with text pattern: {size_candidate}")
                    return size_candidate
        
        return ""
    
    def _is_likely_standalone_size(self, text: str) -> bool:
        """Check if text looks like standalone size info"""
        import re
        
        # Should not contain prices, locations, or long descriptions
        if any(word in text.lower() for word in ['р.', 'byn', 'usd', 'минск', 'гомель', 'брест']):
            return False
        
        # Should be mostly numbers, letters, and size-related symbols
        clean_text = re.sub(r'[\d\s\(\)XSMLXL\-,.]', '', text)
        return len(clean_text) < 3  # Very few other characters
    
    def _extract_location_from_container_smart(self, parent) -> str:
        """Extract location more intelligently from container"""
        import re
        
        belarus_cities = ['Минск', 'Гомель', 'Брест', 'Витебск', 'Гродно', 'Могилёв']
        
        # Method 1: Look for location in specific elements
        location_selectors = [
            '[class*="location"]', '[class*="Location"]',
            '[class*="address"]', '[class*="Address"]',
            '[class*="place"]', '[class*="Place"]',
            '[class*="region"]', '[class*="Region"]'
        ]
        
        for selector in location_selectors:
            location_elem = parent.select_one(selector)
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                for city in belarus_cities:
                    if city in location_text:
                        return self._clean_location_text(location_text)
        
        # Method 2: Look for cities in isolated text nodes
        for text_elem in parent.find_all(text=True):
            text = text_elem.strip()
            # Check if this text contains a city and looks like location info
            for city in belarus_cities:
                if city in text and len(text) < 50:  # Location info is usually short
                    # Make sure it's not part of a title or description
                    if not any(noise in text.lower() for noise in ['купить', 'продать', 'цена', 'р.']):
                        return self._clean_location_text(text)
        
        # Method 3: Fallback to old method
        full_text = parent.get_text()
        return self._extract_location_from_container_text(full_text)
    
    def _clean_location_text(self, location_text: str) -> str:
        """Clean location text more thoroughly"""
        import re
        
        if not location_text:
            return ""
        
        # Remove time stamps, prices, etc.
        location_text = re.sub(r'\d{1,2}:\d{2}', '', location_text)  # Remove time
        location_text = re.sub(r'\d+\s*(р\.|BYN|USD)', '', location_text)  # Remove prices
        location_text = re.sub(r'(от\s+)?\d+[.,]?\d*\s*р\.\s*(в\s*месяц)?', '', location_text)  # Remove detailed prices
        
        return location_text.strip()
    
    def _is_valid_size_quick(self, size: str) -> bool:
        """Quick validation for clothing sizes"""
        import re
        
        # Must not be a year, phone number, or obviously wrong
        if re.match(r'^(19|20)\d{2}$', size):  # Years like 1990, 2020
            return False
        if re.match(r'^[5-9]\d{2}$', size):  # Large numbers like 500+
            return False
        
        # Extract first number to check range
        numbers = re.findall(r'\d+', size)
        if numbers:
            num = int(numbers[0])
            if 25 <= num <= 70:  # Reasonable clothing/shoe size range
                return True
        
        # Accept letter sizes
        if re.match(r'^[XSMLXL]{1,4}$', size):
            return True
            
        return False
    
    def _extract_location_from_container_text(self, text: str) -> str:
        """Extract location from container text"""
        belarus_cities = ['Минск', 'Гомель', 'Брест', 'Витебск', 'Гродно', 'Могилёв']
        
        for city in belarus_cities:
            if city in text:
                # Try to extract district too
                import re
                pattern = f'{city}[^\\n]*?([А-Я][а-я]+ский|[А-Я][а-я]+кий)?'
                match = re.search(pattern, text)
                if match:
                    return match.group(0).strip()
                return city
        
        return ''
    
    def _clean_title(self, title: str) -> str:
        """Clean title from price and other junk"""
        if not title:
            return ""
        
        import re
        
        # Remove price prefixes like "170 р." or "650 р.от 54,17 р. в месяц"
        title = re.sub(r'^(\d+)\s*р\..*?(?=\s*[А-Яа-яA-Za-z])', '', title)
        
        # Remove other common prefixes
        title = re.sub(r'^(от\s+\d+[.,]?\d*\s*р\.\s*в\s*месяц)', '', title)
        title = re.sub(r'^(Договорная)', '', title)
        title = re.sub(r'^(Бесплатно)', '', title)
        
        # Clean up whitespace
        title = title.strip()
        
        # Remove leading digits and symbols if they exist
        title = re.sub(r'^[\d\s\.,\-:]+', '', title)
        
        return title.strip()
    
    def _extract_title_from_container(self, link, parent) -> str:
        """Extract clean title from link and container"""
        import re
        
        # Method 1: Try link text first
        title = link.get_text(strip=True)
        if title and len(title) > 5 and not re.match(r'^\d+', title):
            return self._clean_title(title)
        
        # Method 2: Look for title in specific elements within parent
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Headings
            '[class*="title"]', '[class*="Title"]',  # Title classes
            '[class*="name"]', '[class*="Name"]',    # Name classes
            '[class*="subject"]', '[class*="Subject"]'  # Subject classes
        ]
        
        for selector in title_selectors:
            title_elem = parent.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:
                    return self._clean_title(title)
        
        # Method 3: Look for the longest text that doesn't contain price or location
        text_candidates = []
        for text_elem in parent.find_all(text=True):
            text = text_elem.strip()
            if (len(text) > 10 and 
                'р.' not in text and 
                'BYN' not in text and
                'USD' not in text and
                not re.match(r'^\d+[.,]?\d*$', text) and  # Not just numbers
                not any(city in text for city in ['Минск', 'Гомель', 'Брест', 'Витебск', 'Гродно', 'Могилёв']) and
                not re.search(r'\d{4}-\d{2}-\d{2}', text) and  # Not dates
                not re.search(r'\d{1,2}:\d{2}', text)):  # Not times
                text_candidates.append(text)
        
        # Sort by length and take the longest reasonable one
        text_candidates.sort(key=len, reverse=True)
        for candidate in text_candidates[:3]:  # Check top 3
            cleaned = self._clean_title(candidate)
            if len(cleaned) > 5:
                return cleaned
        
        # Method 4: Fall back to link text, cleaned
        title = link.get_text(strip=True)
        return self._clean_title(title) if title else ""
    
    def _extract_images_from_container(self, parent) -> List[str]:
        """Extract image URLs from ad container"""
        images = []
        
        try:
            # Look for img tags
            img_tags = parent.find_all('img', src=True)
            
            for img in img_tags:
                src = img.get('src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.kufar.by' + src
                    elif not src.startswith('http'):
                        continue  # Skip invalid URLs
                    
                    # Filter out icons, logos, and other non-product images
                    if not any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'placeholder']):
                        images.append(src)
            
            # Also look for background images in style attributes
            elements_with_style = parent.find_all(attrs={'style': True})
            for element in elements_with_style:
                style = element.get('style', '')
                bg_match = re.search(r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)', style)
                if bg_match:
                    bg_url = bg_match.group(1)
                    if bg_url.startswith('//'):
                        bg_url = 'https:' + bg_url
                    elif bg_url.startswith('/'):
                        bg_url = 'https://www.kufar.by' + bg_url
                    images.append(bg_url)
        
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
        
        return images[:3]  # Limit to first 3 images
    
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
            
            # Extract location with improved patterns
            location_selectors = [
                '[data-testid*="location"]', 
                '.location', 
                '[class*="Location"]',
                '[class*="region"]',
                '[class*="address"]',
                '[class*="place"]',
                '[class*="geo"]',
                # Look for common location patterns
                'span:contains("Минск")',
                'span:contains("Гомель")', 
                'span:contains("Брест")',
                'span:contains("Витебск")',
                'span:contains("Гродно")',
                'span:contains("Могилёв")',
                'div:contains("область")',
                'span[class*="text-muted"]',
                # Additional patterns
                '*[class*="meta"]',
                '*[class*="info"]',
            ]
            
            # Try multiple approaches for location
            for selector in location_selectors:
                try:
                    location_elem = element.select_one(selector)
                    if location_elem:
                        location_text = location_elem.get_text(strip=True)
                        
                        # Clean and validate location
                        clean_location = self._clean_location_text(location_text)
                        if clean_location:
                            ad_data['location'] = clean_location
                            break
                except:
                    continue
            
            # If no location found, try to extract from all text
            if not ad_data.get('location'):
                element_text = element.get_text()
                extracted_location = self._extract_location_from_text(element_text)
                if extracted_location:
                    ad_data['location'] = extracted_location
            
            # Extract size information with priority order:
            # 1. From characteristics block (most reliable)
            # 2. From title and description (fallback)
            
            # Try to extract from characteristics first
            characteristics_size = self._extract_size_from_characteristics(element)
            if characteristics_size:
                ad_data['size'] = characteristics_size
                logger.debug(f"📏 Size extracted from characteristics: {characteristics_size}")
            else:
                # Fallback to text-based extraction
                ad_data['size'] = self._extract_size_from_text(ad_data.get('title', ''))
                if ad_data['size']:
                    logger.debug(f"📏 Size extracted from text: {ad_data['size']}")
                
                # If no size in title, try to extract from element text content
                if not ad_data['size']:
                    element_text = element.get_text()
                    ad_data['size'] = self._extract_size_from_text(element_text)
            
            # Only return if we have at least title and URL
            if ad_data.get('title') and ad_data.get('url'):
                return ad_data
                
        except Exception as e:
            logger.error(f"Error extracting ad from element: {e}")
        
        return None
    
    def _extract_size_from_text(self, text: str) -> str:
        """Extract size information from text using improved regex patterns with validation"""
        if not text:
            return ""
        
        import re
        
        # More precise size patterns with context
        size_patterns = [
            # Explicit size mentions
            r'размер[:.\s]+(\d+[-–]\d+\s*\([XSMLXL]+\))',  # размер: 52-54 (XXL)
            r'размер[:.\s]+(\d+\s*\([XSMLXL]+\))',         # размер: 48 (M)
            r'размер[:.\s]+([XSMLXL]{1,3})\b',             # размер: M, XL, XXL
            r'размер[:.\s]+(\d{2,3})\b',                   # размер: 48
            r'р-р[:.\s]+(\d+[-–]\d+)',                     # р-р: 48-50
            r'р-р[:.\s]+(\d{2,3})',                        # р-р: 48
            r'в\s+размере\s+([XSMLXL]{1,3})\b',           # в размере XXL
            r'в\s+размере\s+(\d{2,3})\b',                 # в размере 48
            r'size[:.\s]+([XSMLXL]{1,3})\b',              # size: XL
            
            # Size in parentheses after clothing items
            r'(?:куртка|рубашка|платье|джинсы|брюки|футболка|свитер|костюм|пальто|блузка|юбка|шорты|толстовка|худи|кофта|свитшот)\s+.*?(\d+[-–]\d+\s*\([XSMLXL]+\))',
            r'(?:куртка|рубашка|платье|джинсы|брюки|футболка|свитер|костюм|пальто|блузка|юбка|шорты|толстовка|худи|кофта|свитшот)\s+.*?(\d+\s*\([XSMLXL]+\))',
            r'(?:куртка|рубашка|платье|джинсы|брюки|футболка|свитер|костюм|пальто|блузка|юбка|шорты|толстовка|худи|кофта|свитшот)\s+.*?\b([XSMLXL]{1,3})\b',
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_size = match.group(1).strip()
                
                # Validate the extracted size
                if self._is_valid_clothing_size_scraper(potential_size, text):
                    return potential_size
        
        return ""
    
    def _extract_size_from_characteristics(self, element) -> str:
        """Extract size from Kufar characteristics block"""
        try:
            # Look for characteristics/specifications sections
            characteristics_selectors = [
                '.characteristics',
                '.specifications', 
                '.specs',
                '[class*="characteristic"]',
                '[class*="specification"]',
                '[class*="param"]',
                '[class*="attr"]',
                'dl',  # Definition list commonly used for characteristics
                '.list-unstyled',  # Bootstrap unstyled list often used
                '*:contains("Характеристики")',
                '*:contains("Параметры")',
                '*:contains("Размер")',
            ]
            
            for selector in characteristics_selectors:
                try:
                    characteristics_elem = element.select_one(selector)
                    if characteristics_elem:
                        size = self._parse_size_from_characteristics_text(characteristics_elem.get_text())
                        if size:
                            return size
                except:
                    continue
            
            # Alternative approach: look for any element containing size information
            # that looks like it's from a characteristics block
            all_text_elements = element.find_all(text=True)
            for text_elem in all_text_elements:
                text = str(text_elem).strip()
                if 'размер' in text.lower() and ('___' in text or ':' in text):
                    # This looks like a characteristics line
                    size = self._parse_size_from_characteristics_text(text)
                    if size:
                        return size
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting size from characteristics: {e}")
            return ""
    
    def _parse_size_from_characteristics_text(self, text: str) -> str:
        """Parse size from characteristics text like 'Размер _________ 48 (M), 50 (L)'"""
        if not text:
            return ""
        
        import re
        
        # Patterns for characteristics format
        characteristics_patterns = [
            # "Размер _________ 48 (M), 50 (L)" or similar
            r'размер\s*[_\s\.\-:]*\s*([^,\n]+(?:,\s*[^,\n]+)*)',
            # "Размер обуви__________39, 39,5"
            r'размер\s+обуви\s*[_\s\.\-:]*\s*([^,\n]+(?:,\s*[^,\n]+)*)',
            # More generic pattern for size lines
            r'размер[^:]*:\s*([^\n]+)',
            r'размер[^_]*[_\s\.\-]+([^\n]+)',
            # Pattern for lines that look like "Size: 48 (M), 50 (L)"
            r'size\s*[_\s\.\-:]*\s*([^,\n]+(?:,\s*[^,\n]+)*)',
        ]
        
        for pattern in characteristics_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                size_text = match.group(1).strip()
                
                # Clean up the extracted size text
                cleaned_size = self._clean_characteristics_size(size_text)
                if cleaned_size:
                    return cleaned_size
        
        return ""
    
    def _clean_characteristics_size(self, size_text: str) -> str:
        """Clean and validate size extracted from characteristics"""
        if not size_text:
            return ""
        
        import re
        
        # Remove trailing punctuation and whitespace
        size_text = size_text.strip(' \t\n\r.,;')
        
        # If it contains multiple sizes separated by commas, take the first valid one
        # Example: "48 (M), 50 (L)" -> "48 (M)"
        size_parts = [part.strip() for part in size_text.split(',')]
        
        for part in size_parts:
            # Clean each part
            part = part.strip(' \t\n\r.,;')
            
            # Check if this part looks like a valid size
            if self._is_valid_characteristics_size(part):
                return part
        
        # If no individual part is valid, return the whole thing if it's reasonable
        if len(size_text) <= 50 and self._is_valid_characteristics_size(size_text):
            return size_text
        
        return ""
    
    def _is_valid_characteristics_size(self, size: str) -> bool:
        """Check if extracted characteristics size is valid"""
        if not size or len(size) > 50:
            return False
        
        import re
        
        # Valid size patterns for characteristics
        valid_patterns = [
            r'^\d{1,3}$',  # 48, 52
            r'^\d{1,3}\s*\([XSMLXL]+\)$',  # 48 (M)
            r'^\d{1,3}[-–]\d{1,3}$',  # 48-50
            r'^\d{1,3}[-–]\d{1,3}\s*\([XSMLXL]+\)$',  # 48-50 (M)
            r'^[XSMLXL]{1,4}$',  # XL, XXL
            r'^\d{1,3}[.,]\d$',  # 39.5, 39,5 (for shoes)
            r'^\d{1,3}[.,]\d{1,2}$',  # 39.5, 39,5 (for shoes)
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, size.strip(), re.IGNORECASE):
                # Additional validation for reasonable ranges
                numbers = re.findall(r'\d+', size)
                if numbers:
                    main_num = int(numbers[0])
                    # Reasonable ranges for clothing (30-70) and shoes (20-60)
                    if 20 <= main_num <= 70:
                        return True
                return True  # For non-numeric sizes like XL
        
        return False
    
    def _is_valid_clothing_size_scraper(self, size: str, context: str) -> bool:
        """Validate if the extracted text is actually a clothing size (Scraper version)"""
        if not size:
            return False
        
        import re
        
        # List of words that indicate this is likely clothing
        clothing_indicators = [
            'куртка', 'рубашка', 'платье', 'джинсы', 'брюки', 'футболка', 'свитер', 
            'костюм', 'пальто', 'блузка', 'юбка', 'шорты', 'толстовка', 'худи', 
            'кофта', 'майка', 'рубашка', 'жакет', 'жилет', 'комбинезон', 'халат',
            'одежда', 'размер', 'р-р', 'size', 'свитшот'
        ]
        
        # Check if context contains clothing-related words
        has_clothing_context = any(word in context.lower() for word in clothing_indicators)
        
        # List of things that are definitely NOT clothing sizes
        false_positives = [
            # Years
            r'^(19|20)\d{2}$',  # 1990, 2020 etc
            # Large numbers that are likely prices or IDs
            r'^\d{4,}$',  # 1000, 10000 etc
            r'^[5-9]\d{2}$',  # 500+, likely IDs not sizes (like 648)
            # Phone numbers parts
            r'^\d{2,3}$' if not has_clothing_context else None,  # 25, 375 etc without clothing context
            # Common non-size words
            r'^(the|and|для|или|от|до|за|на|в|с|по)$',
        ]
        
        # Check against false positives
        for fp_pattern in false_positives:
            if fp_pattern and re.match(fp_pattern, size, re.IGNORECASE):
                return False
        
        # Valid size patterns
        valid_patterns = [
            r'^[XSMLXL]{1,4}$',  # XS, S, M, L, XL, XXL, XXXL
            r'^\d{2,3}$',        # 42, 48, 52 etc (if has clothing context)
            r'^\d{2,3}[-–]\d{2,3}$',  # 48-50, 52-54
            r'^\d{2,3}\s*\([XSMLXL]+\)$',  # 48 (M), 52 (L)
            r'^\d{2,3}[-–]\d{2,3}\s*\([XSMLXL]+\)$',  # 52-54 (XL)
            r'^(large|medium|small|extra)$',  # English size words
        ]
        
        # Check if size matches valid patterns
        for pattern in valid_patterns:
            if re.match(pattern, size, re.IGNORECASE):
                # For numeric sizes, require clothing context AND reasonable range
                if re.match(r'^\d', size):
                    if has_clothing_context:
                        # Additional check for reasonable clothing sizes
                        numeric_part = re.findall(r'\d+', size)
                        if numeric_part:
                            num = int(numeric_part[0])
                            # Reasonable clothing size range (european sizes mostly 36-70)
                            if 30 <= num <= 70:
                                return True
                    return False
                else:
                    # Letter sizes are usually valid
                    return True
        
        return False
    
    def _clean_location_text(self, location_text: str) -> str:
        """Clean and validate location text"""
        if not location_text:
            return ""
        
        # Remove extra whitespace
        location_text = location_text.strip()
        
        # Known Belarus cities and regions
        belarus_locations = [
            'Минск', 'Гомель', 'Брест', 'Витебск', 'Гродно', 'Могилёв',
            'Минская область', 'Гомельская область', 'Брестская область',
            'Витебская область', 'Гродненская область', 'Могилёвская область',
            'область', 'район', 'Беларусь', 'Belarus'
        ]
        
        # Check if text contains location indicators
        if any(loc in location_text for loc in belarus_locations):
            # Clean up common non-location prefixes/suffixes
            # Remove time stamps, prices, etc.
            import re
            
            # Remove obvious non-location patterns
            clean_text = re.sub(r'\d{1,2}:\d{2}', '', location_text)  # Remove time
            clean_text = re.sub(r'\d+\s*(р\.|BYN|USD)', '', clean_text)  # Remove prices
            clean_text = re.sub(r'вчера|сегодня|назад', '', clean_text, flags=re.IGNORECASE)  # Remove time words
            
            clean_text = clean_text.strip()
            
            # If still contains location indicators and is reasonable length
            if any(loc in clean_text for loc in belarus_locations) and 3 <= len(clean_text) <= 50:
                return clean_text
        
        return ""
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extract location from full element text"""
        if not text:
            return ""
        
        import re
        
        # Look for Belarus location patterns
        location_patterns = [
            r'(Минск(?:\s*,\s*[^,\n]{2,20})?)',
            r'(Гомель(?:\s*,\s*[^,\n]{2,20})?)',
            r'(Брест(?:\s*,\s*[^,\n]{2,20})?)',
            r'(Витебск(?:\s*,\s*[^,\n]{2,20})?)',
            r'(Гродно(?:\s*,\s*[^,\n]{2,20})?)',
            r'(Могилёв(?:\s*,\s*[^,\n]{2,20})?)',
            r'([А-Я][а-я]+(?:ская|ская)?\s+область)',
            r'([А-Я][а-я]+\s+район)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if 3 <= len(location) <= 50:  # Reasonable length
                    return location
        
        return ""
    
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
            'size': raw_data.get('size', ''),  # Add size information
        }
        
        return normalized
