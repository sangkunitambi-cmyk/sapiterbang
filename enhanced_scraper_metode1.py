import cloudscraper
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
import json
import re
import os
from fake_useragent import UserAgent
from datetime import datetime

class AdvancedDonghuaScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.session = cloudscraper.create_scraper()
        self.ua = UserAgent()
        self.stop_flag = False
        self.progress = {
            'current_step': '',
            'total_items': 0,
            'completed_items': 0,
            'current_item': '',
            'status': 'ready',
            'errors': [],
            'start_time': None
        }
        
        # Create results directory
        self.results_dir = 'scraping_results'
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.setup_session()
        
    def setup_session(self):
        """Setup session with enhanced anti-detection"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
    def safe_filename(self, name):
        """Create safe filename from anime title"""
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '-', name)
        return name.strip('-').lower()[:100]  # Limit length
        
    def save_progress(self):
        """Save current progress to file"""
        progress_file = os.path.join(self.results_dir, 'scraping_progress.json')
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save progress: {e}")
            
    def log_error(self, error_msg, item=None):
        """Log error and add to progress"""
        logging.error(error_msg)
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error_msg,
            'item': item
        }
        self.progress['errors'].append(error_entry)
        self.save_progress()
        
    def update_progress(self, step, current_item='', increment=False):
        """Update scraping progress"""
        self.progress['current_step'] = step
        self.progress['current_item'] = current_item
        if increment:
            self.progress['completed_items'] += 1
        self.save_progress()
        logging.info(f"Progress: {step} - {current_item}")
        
    def get_html_with_fallback(self, url, wait_for_js=False):
        """Get HTML with CloudScraper using EXACT same method as manual test"""
        try:
            # Use EXACT same CloudScraper setup as in debug test that WORKS!
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            
            if response.status_code == 200:
                logging.info(f"CloudScraper success: {len(response.text)} chars")
                return response.text
            else:
                logging.warning(f"CloudScraper failed with status {response.status_code}")
                
        except Exception as e:
            logging.warning(f"CloudScraper failed: {e}")
        return None
        
    # ===== METODE 1: LIST SCRAPER =====
    def scrape_anime_list(self, list_url):
        """METODE 1: Extract anime list dari URL yang berisi daftar anime"""
        try:
            self.progress['status'] = 'running'
            self.progress['start_time'] = datetime.now()
            self.update_progress("Starting list scraping", list_url)
            
            # Get HTML content
            html = self.get_html_with_fallback(list_url)
            if not html:
                raise Exception("Failed to get HTML content")
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Fixed selectors based on debug results - use what actually works!
            anime_selectors = [
                'a[href*="/seri/"]'  # This one works and finds 497 links!
            ]
            
            anime_links = []
            
            for selector in anime_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    title = link.get_text().strip()
                    
                    if href:
                        # Convert to absolute URL first
                        full_url = urljoin(list_url, str(href))
                        
                        # Then validate the absolute URL
                        if self.is_valid_anime_url(str(full_url)):
                            if full_url not in [a['url'] for a in anime_links]:
                                anime_links.append({
                                    'title': title,
                                    'url': str(full_url),
                                    'selector_used': selector
                                })
                                logging.debug(f"Added valid anime URL: {full_url}")
                        else:
                            logging.debug(f"Rejected URL: {full_url}")
            
            # Save list results
            list_filename = f"anime_list_{self.safe_filename(urlparse(list_url).path)}.json"
            list_path = os.path.join(self.results_dir, list_filename)
            
            result = {
                'source_url': list_url,
                'scraped_at': datetime.now().isoformat(),
                'total_found': len(anime_links),
                'anime_list': anime_links
            }
            
            with open(list_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            self.progress['status'] = 'completed'
            self.progress['total_items'] = len(anime_links)
            self.progress['completed_items'] = len(anime_links)
            self.update_progress(f"List scraping completed: {len(anime_links)} anime found")
            
            logging.info(f"List scraping completed: {len(anime_links)} anime found")
            return result
            
        except Exception as e:
            self.log_error(f"List scraping failed: {str(e)}", list_url)
            self.progress['status'] = 'error'
            return None

    def is_valid_anime_url(self, url):
        """Enhanced URL validation - more flexible"""
        url_lower = url.lower()
        
        # Skip only critical unwanted URLs
        skip_keywords = [
            'wp-content', 'wp-admin', '.css', '.js', '.png', '.jpg', '.gif',
            'login', 'register', 'wp-json', 'feed', 'sitemap', 'robots.txt',
            'wp-includes', 'wp-login', 'wp-signup', '/author/', '/tag/', '/category/'
        ]
        
        for skip in skip_keywords:
            if skip in url_lower:
                logging.debug(f"Skipping URL (unwanted keyword '{skip}'): {url}")
                return False
        
        # Skip list/index pages but allow individual anime pages
        if url_lower.endswith('/seri/') or url_lower.endswith('/seri'):
            logging.debug(f"Skipping main directory URL: {url}")
            return False
            
        if '/list-mode/' in url_lower and not '/seri/' in url_lower:
            logging.debug(f"Skipping list-mode directory URL: {url}")
            return False
                
        # Must contain anime/donghua indicators (more flexible)
        anime_indicators = [
            '/seri/',           # Main anime URL pattern
            'episode',          # Episode pages
            'donghua',          # Donghua keyword
            'anime'             # Anime keyword
        ]
        
        has_anime_indicator = any(indicator in url_lower for indicator in anime_indicators)
        
        # Check domain
        is_anichin_domain = 'anichin.cafe' in url_lower
        
        # Additional check: if URL has /seri/ and a specific anime name (not just directory)
        if '/seri/' in url_lower:
            # Check if it's a specific anime URL (has content after /seri/)
            seri_part = url_lower.split('/seri/')
            if len(seri_part) > 1 and seri_part[1].strip('/'):
                # It's a specific anime URL, not just the directory
                has_anime_indicator = True
        
        result = has_anime_indicator and is_anichin_domain
        logging.debug(f"URL validation for {url}: indicator={has_anime_indicator}, domain={is_anichin_domain}, result={result}")
        
        return result

    def stop_scraping(self):
        """Stop the scraping process"""
        self.stop_flag = True
        self.progress['status'] = 'stopped'
        logging.info("Scraping stopped by user")

    def get_progress(self):
        """Get current progress"""
        return self.progress.copy()
