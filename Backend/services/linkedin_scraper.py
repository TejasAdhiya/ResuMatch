import requests
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import List, Dict
import urllib.parse
import json

logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.guest_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.state_mapping = {
            'andhra-pradesh': 'Andhra Pradesh, India',
            'arunachal-pradesh': 'Arunachal Pradesh, India',
            'assam': 'Assam, India',
            'bihar': 'Bihar, India',
            'chhattisgarh': 'Chhattisgarh, India',
            'goa': 'Goa, India',
            'gujarat': 'Gujarat, India',
            'haryana': 'Haryana, India',
            'himachal-pradesh': 'Himachal Pradesh, India',
            'jharkhand': 'Jharkhand, India',
            'karnataka': 'Karnataka, India',
            'kerala': 'Kerala, India',
            'madhya-pradesh': 'Madhya Pradesh, India',
            'maharashtra': 'Maharashtra, India',
            'manipur': 'Manipur, India',
            'meghalaya': 'Meghalaya, India',
            'mizoram': 'Mizoram, India',
            'nagaland': 'Nagaland, India',
            'odisha': 'Odisha, India',
            'punjab': 'Punjab, India',
            'rajasthan': 'Rajasthan, India',
            'sikkim': 'Sikkim, India',
            'tamil-nadu': 'Tamil Nadu, India',
            'telangana': 'Telangana, India',
            'tripura': 'Tripura, India',
            'uttar-pradesh': 'Uttar Pradesh, India',
            'uttarakhand': 'Uttarakhand, India',
            'west-bengal': 'West Bengal, India',
            'delhi': 'Delhi, India',
            'mumbai': 'Mumbai, India',
            'bangalore': 'Bangalore, India',
            'chennai': 'Chennai, India',
            'hyderabad': 'Hyderabad, India',
            'pune': 'Pune, India'
        }
    
    def search_jobs(self, keywords: List[str], location: str, limit: int = 20) -> List[Dict]:
        """
        Search for jobs using multiple methods with priority order
        """
        logger.info(f"Starting job search for keywords: {keywords}, location: {location}")
        jobs = []
        
        # Method 1: LinkedIn Guest API (Most reliable)
        try:
            logger.info("Trying LinkedIn Guest API method...")
            jobs = self._search_linkedin_guest_api(keywords, location, limit)
            logger.info(f"Guest API returned {len(jobs)} jobs")
            if len(jobs) >= 5:
                return self._ensure_valid_jobs(jobs[:limit])
        except Exception as e:
            logger.warning(f"Guest API method failed: {str(e)}")
        
        # Method 2: Public LinkedIn scraping with requests
        try:
            logger.info("Trying public LinkedIn scraping...")
            additional_jobs = self._search_public_linkedin(keywords, location, limit - len(jobs))
            jobs.extend(additional_jobs)
            logger.info(f"Public scraping added {len(additional_jobs)} jobs, total: {len(jobs)}")
            if len(jobs) >= 5:
                return self._ensure_valid_jobs(jobs[:limit])
        except Exception as e:
            logger.warning(f"Public scraping failed: {str(e)}")
        
        # Method 3: Selenium with updated selectors (Last resort)
        try:
            logger.info("Trying Selenium method as last resort...")
            selenium_jobs = self._search_with_updated_selenium(keywords, location, limit - len(jobs))
            jobs.extend(selenium_jobs)
            logger.info(f"Selenium added {len(selenium_jobs)} jobs, total: {len(jobs)}")
        except Exception as e:
            logger.warning(f"Selenium method failed: {str(e)}")
        
        # Ensure we return valid jobs
        valid_jobs = self._ensure_valid_jobs(jobs)
        logger.info(f"Returning {len(valid_jobs)} valid jobs")
        
        return valid_jobs[:limit]
    
    def _search_linkedin_guest_api(self, keywords: List[str], location: str, limit: int) -> List[Dict]:
        """
        Use LinkedIn's guest API for job search (most reliable method)
        """
        jobs = []
        session = requests.Session()
        session.headers.update(self.headers)
        
        location_name = self.state_mapping.get(location, f"{location}, India")
        
        for keyword in keywords[:3]:
            try:
                # LinkedIn guest job search API
                params = {
                    'keywords': keyword,
                    'location': location_name,
                    'start': 0,
                    'count': min(25, limit)
                }
                
                response = session.get(self.guest_url, params=params, timeout=15)
                logger.info(f"Guest API response for '{keyword}': Status {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = soup.find_all('div', class_='base-card')
                    
                    logger.info(f"Found {len(job_cards)} job cards for keyword: {keyword}")
                    
                    for card in job_cards:
                        job_data = self._extract_from_guest_api_card(card, keyword, location)
                        if job_data and self._is_complete_job(job_data):
                            jobs.append(job_data)
                            logger.info(f"✓ Extracted: {job_data['title']} at {job_data['company']}")
                
                time.sleep(random.uniform(1, 2))
                
                if len(jobs) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Guest API error for keyword {keyword}: {str(e)}")
                continue
        
        return jobs
    
    def _extract_from_guest_api_card(self, card, keyword: str, location: str) -> Dict:
        """
        Extract job data from LinkedIn guest API response
        """
        try:
            # Extract job URL and title
            title_link = card.find('a', class_='base-card__full-link')
            if not title_link:
                return None
            
            job_url = title_link.get('href', '')
            if job_url and not job_url.startswith('http'):
                job_url = 'https://www.linkedin.com' + job_url
            
            # Extract title
            title_elem = card.find('h3', class_='base-search-card__title')
            if not title_elem:
                title_elem = title_link
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract company
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            if not company_elem:
                company_elem = card.find('a', {'data-tracking-control-name': 'public_jobs_jserp-result_job-search-card-subtitle'})
            company = company_elem.get_text(strip=True) if company_elem else ''
            
            # Extract location
            location_elem = card.find('span', class_='job-search-card__location')
            job_location = location_elem.get_text(strip=True) if location_elem else self.state_mapping.get(location, f"{location}, India")
            
            # Extract description snippet
            desc_elem = card.find('p', class_='job-search-card__snippet')
            description = desc_elem.get_text(strip=True) if desc_elem else f"Exciting {keyword} opportunity. Click to view full details."
            
            if title and company:  # Only return if we have essential data
                return {
                    'title': title,
                    'company': company,
                    'location': job_location,
                    'description': description,
                    'url': job_url,
                    'source': 'LinkedIn Guest API',
                    'scraped_at': time.time()
                }
            
        except Exception as e:
            logger.warning(f"Error extracting from guest API card: {str(e)}")
        
        return None
    
    def _search_public_linkedin(self, keywords: List[str], location: str, limit: int) -> List[Dict]:
        """
        Search public LinkedIn job pages
        """
        jobs = []
        session = requests.Session()
        session.headers.update(self.headers)
        
        for keyword in keywords[:2]:
            try:
                search_url = self._build_public_search_url(keyword, location)
                logger.info(f"Public search URL: {search_url}")
                
                response = session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors for job cards
                    job_cards = (
                        soup.find_all('div', {'data-view-name': 'job-search-card'}) or
                        soup.find_all('div', class_='job-search-card') or
                        soup.find_all('div', class_='base-card') or
                        soup.find_all('li', class_='jobs-search-results__list-item')
                    )
                    
                    logger.info(f"Public search found {len(job_cards)} cards for: {keyword}")
                    
                    for card in job_cards[:limit//len(keywords)]:
                        job_data = self._extract_from_public_card(card, keyword, location)
                        if job_data and self._is_complete_job(job_data):
                            jobs.append(job_data)
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Public search error for {keyword}: {str(e)}")
                continue
        
        return jobs
    
    def _extract_from_public_card(self, card, keyword: str, location: str) -> Dict:
        """
        Extract job data from public LinkedIn page
        """
        try:
            # Multiple selectors for title and URL
            title_selectors = [
                'h3.base-search-card__title a',
                'h3 a',
                'a.base-card__full-link',
                '.base-search-card__title',
                '.job-card-list__title a'
            ]
            
            title = ''
            job_url = ''
            
            for selector in title_selectors:
                elem = card.select_one(selector)
                if elem:
                    if elem.name == 'a':
                        title = elem.get_text(strip=True)
                        job_url = elem.get('href', '')
                    else:
                        title = elem.get_text(strip=True)
                        link_elem = elem.find('a')
                        if link_elem:
                            job_url = link_elem.get('href', '')
                    break
            
            # Extract company
            company_selectors = [
                'h4.base-search-card__subtitle a',
                '.base-search-card__subtitle',
                '.hidden-nested-link',
                'a[data-tracking-control-name*="company"]'
            ]
            
            company = ''
            for selector in company_selectors:
                elem = card.select_one(selector)
                if elem:
                    company = elem.get_text(strip=True)
                    break
            
            # Extract location
            location_selectors = [
                '.job-search-card__location',
                '.base-search-card__metadata',
                '[class*="location"]'
            ]
            
            job_location = ''
            for selector in location_selectors:
                elem = card.select_one(selector)
                if elem:
                    job_location = elem.get_text(strip=True)
                    break
            
            if not job_location:
                job_location = self.state_mapping.get(location, f"{location}, India")
            
            # Fix URL
            if job_url and not job_url.startswith('http'):
                job_url = 'https://www.linkedin.com' + job_url
            
            if title and company:
                return {
                    'title': title,
                    'company': company,
                    'location': job_location,
                    'description': f"Great opportunity for {keyword} professionals. Apply now to join a leading company.",
                    'url': job_url or f"https://www.linkedin.com/jobs/search?keywords={keyword}",
                    'source': 'LinkedIn Public',
                    'scraped_at': time.time()
                }
                
        except Exception as e:
            logger.warning(f"Error extracting from public card: {str(e)}")
        
        return None
    
    def _search_with_updated_selenium(self, keywords: List[str], location: str, limit: int) -> List[Dict]:
        """
        Updated Selenium method with current LinkedIn selectors
        """
        jobs = []
        options = Options()
        
        # Updated Chrome options
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--log-level=3')  # Suppress GPU errors
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            for keyword in keywords[:2]:
                try:
                    search_url = self._build_search_url(keyword, location)
                    driver.get(search_url)
                    time.sleep(random.uniform(3, 5))
                    
                    # Updated selectors for 2024 LinkedIn
                    card_selectors = [
                        '[data-view-name="job-search-card"]',
                        '.job-search-card',
                        '.base-card',
                        '.scaffold-layout__list-item',
                        '.jobs-search-results__list-item'
                    ]
                    
                    job_cards = []
                    for selector in card_selectors:
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                            if job_cards:
                                logger.info(f"Selenium found {len(job_cards)} cards with selector: {selector}")
                                break
                        except TimeoutException:
                            continue
                    
                    for card in job_cards[:limit//len(keywords)]:
                        job_data = self._extract_selenium_2024(card, keyword, location)
                        if job_data and self._is_complete_job(job_data):
                            jobs.append(job_data)
                    
                    time.sleep(random.uniform(2, 3))
                    
                except Exception as e:
                    logger.error(f"Selenium error for keyword {keyword}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Selenium driver error: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return jobs
    
    def _extract_selenium_2024(self, card, keyword: str, location: str) -> Dict:
        """
        Extract job data using updated 2024 LinkedIn selectors
        """
        try:
            # Updated selectors for title and URL
            title_selectors = [
                'h3 a[data-tracking-control-name*="job"]',
                '.base-search-card__title a',
                'h3.base-search-card__title',
                '.job-card-list__title a',
                'a[aria-label*="job"]'
            ]
            
            title = ''
            job_url = ''
            
            for selector in title_selectors:
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    if elem.tag_name == 'a':
                        title = elem.text.strip()
                        job_url = elem.get_attribute('href')
                    else:
                        title = elem.text.strip()
                        try:
                            link = elem.find_element(By.TAG_NAME, 'a')
                            job_url = link.get_attribute('href')
                        except:
                            pass
                    if title:
                        break
                except:
                    continue
            
            # Updated company selectors
            company_selectors = [
                'h4.base-search-card__subtitle a',
                '.base-search-card__subtitle',
                'a[data-tracking-control-name*="company"]',
                '.hidden-nested-link'
            ]
            
            company = ''
            for selector in company_selectors:
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    company = elem.text.strip()
                    if company:
                        break
                except:
                    continue
            
            # Location selectors
            job_location = self.state_mapping.get(location, f"{location}, India")
            location_selectors = [
                '.job-search-card__location',
                '.base-search-card__metadata',
                '[class*="location"]'
            ]
            
            for selector in location_selectors:
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    loc_text = elem.text.strip()
                    if loc_text:
                        job_location = loc_text
                        break
                except:
                    continue
            
            if title and company:
                return {
                    'title': title,
                    'company': company,
                    'location': job_location,
                    'description': f"Excellent {keyword} position with growth opportunities. Join our team today!",
                    'url': job_url or f"https://www.linkedin.com/jobs/search?keywords={keyword}",
                    'source': 'LinkedIn Selenium',
                    'scraped_at': time.time()
                }
                
        except Exception as e:
            logger.warning(f"Selenium extraction error: {str(e)}")
        
        return None
    
    def _build_search_url(self, keyword: str, location: str) -> str:
        """Build LinkedIn job search URL"""
        location_name = self.state_mapping.get(location, f"{location}, India")
        params = {
            'keywords': keyword,
            'location': location_name,
            'f_TPR': 'r604800',
            'position': '1',
            'pageNum': '0'
        }
        return f"{self.base_url}?" + urllib.parse.urlencode(params)
    
    def _build_public_search_url(self, keyword: str, location: str) -> str:
        """Build public LinkedIn search URL"""
        location_name = self.state_mapping.get(location, f"{location}, India")
        params = {
            'keywords': keyword,
            'location': location_name,
            'trk': 'public_jobs_jobs-search-bar_search-submit',
            'position': '1',
            'pageNum': '0'
        }
        return f"{self.base_url}?" + urllib.parse.urlencode(params)
    
    def _is_complete_job(self, job: Dict) -> bool:
        """Check if job has all required fields with meaningful data"""
        if not job:
            return False
        
        required_fields = ['title', 'company', 'location']
        for field in required_fields:
            value = job.get(field, '').strip()
            if not value or len(value) < 2:
                return False
            
            # Check for placeholder text
            placeholder_indicators = [
                'not available', 'not specified', 'click to view', 
                'company name', 'job title', 'location not'
            ]
            if any(indicator in value.lower() for indicator in placeholder_indicators):
                return False
        
        return True
    
    def _ensure_valid_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter and ensure all jobs are valid and complete"""
        valid_jobs = []
        
        for job in jobs:
            if self._is_complete_job(job):
                # Additional cleanup
                job['title'] = job['title'].strip()
                job['company'] = job['company'].strip()
                job['location'] = job['location'].strip()
                
                # Ensure URL is valid
                if not job.get('url') or not job['url'].startswith('http'):
                    job['url'] = f"https://www.linkedin.com/jobs/search?keywords={job['title']}"
                
                valid_jobs.append(job)
        
        logger.info(f"Filtered {len(jobs)} jobs down to {len(valid_jobs)} valid jobs")
        return valid_jobs