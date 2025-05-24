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
import logging
from typing import List, Dict
import urllib.parse
from selenium.webdriver.chrome.service import Service  # Add at top

logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
        Search for jobs on LinkedIn using multiple methods
        """
        jobs = []
        
        # Try Selenium method first (more reliable)
        try:
            jobs = self._search_with_selenium(keywords, location, limit)
            if len(jobs) >= 5:
                return jobs
        except Exception as e:
            logger.warning(f"Selenium method failed: {str(e)}")
        
        # Fallback to requests method
        try:
            jobs.extend(self._search_with_requests(keywords, location, limit - len(jobs)))
        except Exception as e:
            logger.warning(f"Requests method failed: {str(e)}")
        
        # If still no jobs, return sample data
        if not jobs:
            logger.info("Using sample data as fallback")
            return self._get_sample_jobs(keywords, location)
        
        return jobs
    
    def _search_with_selenium(self, keywords: List[str], location: str, limit: int) -> List[Dict]:
        """
        Use Selenium to scrape LinkedIn jobs (more reliable but slower)
        """
        jobs = []
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        
        try:
            # Updated WebDriver initialization with proper Service()
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
    
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),  # Fixed initialization
                options=options
             )
    
            # Search for each keyword (your existing logic)
            for keyword in keywords[:3]:  # Limit to top 3 keywords
                search_url = self._build_search_url(keyword, location)
                logger.info(f"Searching: {search_url}")
        
                driver.get(search_url)
                time.sleep(random.uniform(2, 4))
        
                # Wait for job listings to load
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
                    )
                except:
                    continue
        
                # Extract job cards
                job_cards = driver.find_elements(By.CLASS_NAME, "job-search-card")
        
                for card in job_cards[:limit//len(keywords)]:
                    try:
                        job_data = self._extract_job_data_selenium(card, driver)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.warning(f"Error extracting job data: {str(e)}")
                    continue
        
                if len(jobs) >= limit:
                    break
            
                time.sleep(random.uniform(1, 2))

        except Exception as e:
            logger.error(f"Selenium scraping error: {str(e)}")
        finally:
            try:
                driver.quit()
            except:
                pass
                

        return jobs[:limit]
    
    def _search_with_requests(self, keywords: List[str], location: str, limit: int) -> List[Dict]:
        """
        Fallback method using requests (may be blocked)
        """
        jobs = []
        session = requests.Session()
        session.headers.update(self.headers)
        
        for keyword in keywords[:2]:
            try:
                search_url = self._build_search_url(keyword, location)
                response = session.get(search_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = soup.find_all('div', {'class': 'job-search-card'})
                    
                    for card in job_cards[:limit//len(keywords)]:
                        job_data = self._extract_job_data_bs4(card)
                        if job_data:
                            jobs.append(job_data)
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.warning(f"Request failed for keyword {keyword}: {str(e)}")
                continue
        
        return jobs
    
    def _extract_job_data_selenium(self, card, driver) -> Dict:
        """
        Extract job data from Selenium WebElement
        """
        try:
            # Extract job link
            link_element = card.find_element(By.CSS_SELECTOR, "h3 a")
            job_url = link_element.get_attribute('href')
            
            # Extract basic info
            title = link_element.text.strip()
            
            try:
                company = card.find_element(By.CSS_SELECTOR, ".hidden-nested-link").text.strip()
            except:
                company = "Company Name Not Available"
            
            try:
                location = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text.strip()
            except:
                location = self.state_mapping.get(location, "Location Not Specified")
            
            # Get job description preview
            try:
                # Click to expand description
                card.click()
                time.sleep(1)
                description_element = driver.find_element(By.CLASS_NAME, "jobs-description-content__text")
                description = description_element.text.strip()[:500] + "..."
            except:
                description = "Job description not available. Click to view full details on LinkedIn."
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': job_url,
                'source': 'LinkedIn',
                'scraped_at': time.time()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {str(e)}")
            return None
    
    def _extract_job_data_bs4(self, card) -> Dict:
        """
        Extract job data from BeautifulSoup element
        """
        try:
            link_element = card.find('a')
            if not link_element:
                return None
                
            job_url = link_element.get('href')
            if job_url and not job_url.startswith('http'):
                job_url = 'https://www.linkedin.com' + job_url
            
            title_element = card.find('h3')
            title = title_element.text.strip() if title_element else "Job Title Not Available"
            
            company_element = card.find('a', {'data-tracking-control-name': 'public_jobs_jserp-result_job-search-card-subtitle'})
            company = company_element.text.strip() if company_element else "Company Not Available"
            
            location_element = card.find('span', class_='job-search-card__location')
            location = location_element.text.strip() if location_element else "Location Not Specified"
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': "Click to view full job description on LinkedIn.",
                'url': job_url,
                'source': 'LinkedIn',
                'scraped_at': time.time()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {str(e)}")
            return None
    
    def _build_search_url(self, keyword: str, location: str) -> str:
        """
        Build LinkedIn job search URL
        """
        location_name = self.state_mapping.get(location, f"{location}, India")
        
        params = {
            'keywords': keyword,
            'location': location_name,
            'f_TPR': 'r604800',  # Past week
            'position': '1',
            'pageNum': '0'
        }
        
        return f"{self.base_url}?" + urllib.parse.urlencode(params)
    
    def _get_sample_jobs(self, keywords: List[str], location: str) -> List[Dict]:
        """
        Return sample jobs when scraping fails (for testing/demo)
        """
        primary_keyword = keywords[0] if keywords else "developer"
        location_name = self.state_mapping.get(location, f"{location}, India")
        
        sample_jobs = [
            {
                'title': f'Senior {primary_keyword.title()}',
                'company': 'Tech Solutions India',
                'location': location_name,
                'description': f'We are looking for an experienced {primary_keyword} to join our dynamic team. The ideal candidate should have strong technical skills and experience in modern development practices.',
                'url': 'https://www.linkedin.com/jobs/view/sample1',
                'source': 'LinkedIn',
                'scraped_at': time.time()
            },
            {
                'title': f'{primary_keyword.title()} - Remote',
                'company': 'Innovation Labs',
                'location': f'Remote, {location_name}',
                'description': f'Remote {primary_keyword} position with flexible working hours. Join our innovative team and work on cutting-edge projects.',
                'url': 'https://www.linkedin.com/jobs/view/sample2',
                'source': 'LinkedIn',
                'scraped_at': time.time()
            },
            {
                'title': f'Lead {primary_keyword.title()}',
                'company': 'Digital Enterprises',
                'location': location_name,
                'description': f'Leadership role for experienced {primary_keyword}. Guide a team of developers and drive technical excellence in our projects.',
                'url': 'https://www.linkedin.com/jobs/view/sample3',
                'source': 'LinkedIn',
                'scraped_at': time.time()
            }
        ]
        
        return sample_jobs