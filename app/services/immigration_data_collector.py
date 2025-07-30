"""
Immigration Data Collector for gathering immigration policy data from government websites.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ImmigrationPolicy:
    """Immigration policy data structure."""
    country_code: str
    policy_type: str  # visa, work_permit, citizenship, etc.
    title: str
    description: str
    requirements: List[str]
    processing_time_days: Optional[int]
    cost_usd: Optional[float]
    source_url: str
    last_updated: datetime
    change_detected: bool = False


@dataclass
class ScrapedData:
    """Container for scraped immigration data."""
    policies: List[ImmigrationPolicy]
    raw_html: Optional[str] = None
    metadata: Dict[str, Any] = None


class ImmigrationDataCollector:
    """Service for collecting immigration data from various government sources."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.data_sources = self._initialize_data_sources()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _initialize_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize data sources for different countries."""
        return {
            'US': {
                'name': 'United States',
                'sources': [
                    {
                        'name': 'USCIS',
                        'base_url': 'https://www.uscis.gov',
                        'visa_urls': [
                            'https://www.uscis.gov/working-in-the-united-states/temporary-workers',
                            'https://www.uscis.gov/green-card/green-card-eligibility-categories'
                        ],
                        'scraper': 'uscis'
                    }
                ]
            },
            'CA': {
                'name': 'Canada',
                'sources': [
                    {
                        'name': 'IRCC',
                        'base_url': 'https://www.canada.ca/en/immigration-refugees-citizenship',
                        'visa_urls': [
                            'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada.html',
                            'https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html'
                        ],
                        'scraper': 'ircc'
                    }
                ]
            },
            'UK': {
                'name': 'United Kingdom',
                'sources': [
                    {
                        'name': 'UK Government',
                        'base_url': 'https://www.gov.uk',
                        'visa_urls': [
                            'https://www.gov.uk/browse/visas-immigration',
                            'https://www.gov.uk/apply-uk-visa'
                        ],
                        'scraper': 'uk_gov'
                    }
                ]
            },
            'AU': {
                'name': 'Australia',
                'sources': [
                    {
                        'name': 'Department of Home Affairs',
                        'base_url': 'https://immi.homeaffairs.gov.au',
                        'visa_urls': [
                            'https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing',
                            'https://immi.homeaffairs.gov.au/visas/working-in-australia'
                        ],
                        'scraper': 'australia_gov'
                    }
                ]
            },
            'DE': {
                'name': 'Germany',
                'sources': [
                    {
                        'name': 'Federal Foreign Office',
                        'base_url': 'https://www.auswaertiges-amt.de',
                        'visa_urls': [
                            'https://www.auswaertiges-amt.de/en/visa-service/visa-categories',
                            'https://www.auswaertiges-amt.de/en/visa-service/working-in-germany'
                        ],
                        'scraper': 'germany_gov'
                    }
                ]
            }
        }
    
    async def collect_data(self, country_codes: Optional[List[str]] = None) -> Dict[str, ScrapedData]:
        """Collect immigration data for specified countries."""
        if country_codes is None:
            country_codes = list(self.data_sources.keys())
        
        results = {}
        
        for country_code in country_codes:
            if country_code not in self.data_sources:
                logger.warning(f"Country code {country_code} not supported")
                continue
                
            try:
                logger.info(f"Collecting data for {country_code}")
                scraped_data = await self._scrape_country_data(country_code)
                results[country_code] = scraped_data
                
            except Exception as e:
                logger.error(f"Error collecting data for {country_code}: {str(e)}")
                results[country_code] = ScrapedData(policies=[])
        
        return results
    
    async def _scrape_country_data(self, country_code: str) -> ScrapedData:
        """Scrape immigration data for a specific country."""
        country_data = self.data_sources[country_code]
        all_policies = []
        
        for source in country_data['sources']:
            try:
                policies = await self._scrape_source(country_code, source)
                all_policies.extend(policies)
                
            except Exception as e:
                logger.error(f"Error scraping source {source['name']} for {country_code}: {str(e)}")
        
        return ScrapedData(policies=all_policies)
    
    async def _scrape_source(self, country_code: str, source: Dict[str, Any]) -> List[ImmigrationPolicy]:
        """Scrape data from a specific source."""
        scraper_method = getattr(self, f"_scrape_{source['scraper']}", None)
        
        if not scraper_method:
            logger.warning(f"No scraper found for {source['scraper']}")
            return []
        
        policies = []
        
        for url in source['visa_urls']:
            try:
                page_policies = await scraper_method(country_code, url, source)
                policies.extend(page_policies)
                
            except Exception as e:
                logger.error(f"Error scraping URL {url}: {str(e)}")
        
        return policies
    
    async def _scrape_uscis(self, country_code: str, url: str, source: Dict[str, Any]) -> List[ImmigrationPolicy]:
        """Scrape USCIS (US immigration) data."""
        async with self.session.get(url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        policies = []
        
        # Look for visa categories and requirements
        visa_sections = soup.find_all(['div', 'section'], class_=re.compile(r'visa|immigration|work'))
        
        for section in visa_sections:
            title_elem = section.find(['h1', 'h2', 'h3'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            description = ""
            desc_elem = section.find(['p', 'div'])
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract requirements
            requirements = []
            req_elements = section.find_all(['li', 'p'], string=re.compile(r'require|need|must'))
            for req in req_elements:
                requirements.append(req.get_text(strip=True))
            
            policy = ImmigrationPolicy(
                country_code=country_code,
                policy_type='visa',
                title=title,
                description=description,
                requirements=requirements,
                processing_time_days=None,
                cost_usd=None,
                source_url=url,
                last_updated=datetime.utcnow()
            )
            
            policies.append(policy)
        
        return policies
    
    async def _scrape_ircc(self, country_code: str, url: str, source: Dict[str, Any]) -> List[ImmigrationPolicy]:
        """Scrape IRCC (Canada immigration) data."""
        async with self.session.get(url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        policies = []
        
        # Look for immigration programs
        program_sections = soup.find_all(['div', 'section'], class_=re.compile(r'program|immigration|visa'))
        
        for section in program_sections:
            title_elem = section.find(['h1', 'h2', 'h3'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            description = ""
            desc_elem = section.find(['p', 'div'])
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract requirements
            requirements = []
            req_elements = section.find_all(['li', 'p'], string=re.compile(r'require|need|must|eligible'))
            for req in req_elements:
                requirements.append(req.get_text(strip=True))
            
            policy = ImmigrationPolicy(
                country_code=country_code,
                policy_type='immigration_program',
                title=title,
                description=description,
                requirements=requirements,
                processing_time_days=None,
                cost_usd=None,
                source_url=url,
                last_updated=datetime.utcnow()
            )
            
            policies.append(policy)
        
        return policies
    
    async def _scrape_uk_gov(self, country_code: str, url: str, source: Dict[str, Any]) -> List[ImmigrationPolicy]:
        """Scrape UK Government immigration data."""
        async with self.session.get(url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        policies = []
        
        # Look for visa information
        visa_sections = soup.find_all(['div', 'section'], class_=re.compile(r'visa|immigration'))
        
        for section in visa_sections:
            title_elem = section.find(['h1', 'h2', 'h3'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            description = ""
            desc_elem = section.find(['p', 'div'])
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract requirements
            requirements = []
            req_elements = section.find_all(['li', 'p'], string=re.compile(r'require|need|must|eligible'))
            for req in req_elements:
                requirements.append(req.get_text(strip=True))
            
            policy = ImmigrationPolicy(
                country_code=country_code,
                policy_type='visa',
                title=title,
                description=description,
                requirements=requirements,
                processing_time_days=None,
                cost_usd=None,
                source_url=url,
                last_updated=datetime.utcnow()
            )
            
            policies.append(policy)
        
        return policies
    
    async def _scrape_australia_gov(self, country_code: str, url: str, source: Dict[str, Any]) -> List[ImmigrationPolicy]:
        """Scrape Australia Government immigration data."""
        async with self.session.get(url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        policies = []
        
        # Look for visa categories
        visa_sections = soup.find_all(['div', 'section'], class_=re.compile(r'visa|immigration'))
        
        for section in visa_sections:
            title_elem = section.find(['h1', 'h2', 'h3'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            description = ""
            desc_elem = section.find(['p', 'div'])
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract requirements
            requirements = []
            req_elements = section.find_all(['li', 'p'], string=re.compile(r'require|need|must|eligible'))
            for req in req_elements:
                requirements.append(req.get_text(strip=True))
            
            policy = ImmigrationPolicy(
                country_code=country_code,
                policy_type='visa',
                title=title,
                description=description,
                requirements=requirements,
                processing_time_days=None,
                cost_usd=None,
                source_url=url,
                last_updated=datetime.utcnow()
            )
            
            policies.append(policy)
        
        return policies
    
    async def _scrape_germany_gov(self, country_code: str, url: str, source: Dict[str, Any]) -> List[ImmigrationPolicy]:
        """Scrape Germany Government immigration data."""
        async with self.session.get(url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        policies = []
        
        # Look for visa information
        visa_sections = soup.find_all(['div', 'section'], class_=re.compile(r'visa|immigration|einreise'))
        
        for section in visa_sections:
            title_elem = section.find(['h1', 'h2', 'h3'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            description = ""
            desc_elem = section.find(['p', 'div'])
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract requirements
            requirements = []
            req_elements = section.find_all(['li', 'p'], string=re.compile(r'require|need|must|eligible|benötigen'))
            for req in req_elements:
                requirements.append(req.get_text(strip=True))
            
            policy = ImmigrationPolicy(
                country_code=country_code,
                policy_type='visa',
                title=title,
                description=description,
                requirements=requirements,
                processing_time_days=None,
                cost_usd=None,
                source_url=url,
                last_updated=datetime.utcnow()
            )
            
            policies.append(policy)
        
        return policies
    
    def detect_policy_changes(self, old_policies: List[ImmigrationPolicy], 
                            new_policies: List[ImmigrationPolicy]) -> List[ImmigrationPolicy]:
        """Detect changes in immigration policies."""
        changes = []
        
        # Create lookup dictionaries
        old_lookup = {p.title: p for p in old_policies}
        new_lookup = {p.title: p for p in new_policies}
        
        # Check for new policies
        for title, new_policy in new_lookup.items():
            if title not in old_lookup:
                new_policy.change_detected = True
                changes.append(new_policy)
                continue
            
            old_policy = old_lookup[title]
            
            # Check for changes in requirements, processing time, or cost
            if (old_policy.requirements != new_policy.requirements or
                old_policy.processing_time_days != new_policy.processing_time_days or
                old_policy.cost_usd != new_policy.cost_usd):
                
                new_policy.change_detected = True
                changes.append(new_policy)
        
        return changes
    
    async def get_supported_countries(self) -> List[str]:
        """Get list of supported countries."""
        return list(self.data_sources.keys())
    
    async def get_data_source_info(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get information about data sources for a country."""
        if country_code not in self.data_sources:
            return None
        
        return self.data_sources[country_code] 