"""
Enhanced Immigration Data Collector for gathering and storing immigration policy data.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.immigration_requirements import ImmigrationRequirements, CountryData, ScrapingLog
from app.models.country import Country

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    success: bool
    country_code: str
    records_scraped: int
    records_updated: int
    records_failed: int
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    data_size_bytes: Optional[int] = None


class EnhancedImmigrationDataCollector:
    """Enhanced service for collecting and storing immigration data."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.data_sources = self._initialize_data_sources()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
                            'https://www.uscis.gov/green-card/green-card-eligibility-categories',
                            'https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors'
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
                            'https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html',
                            'https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada.html'
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
                            'https://www.gov.uk/apply-uk-visa',
                            'https://www.gov.uk/student-visa'
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
                            'https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-finder'
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
                            'https://www.auswaertiges-amt.de/en/visa-service',
                            'https://www.auswaertiges-amt.de/en/travel-and-security'
                        ],
                        'scraper': 'germany_gov'
                    }
                ]
            }
        }
    
    async def scrape_country_data(self, db: AsyncSession, country_code: str) -> ScrapingResult:
        """Scrape immigration data for a specific country and store in database."""
        start_time = datetime.utcnow()
        scraping_log = ScrapingLog(
            country_code=country_code,
            source_name="enhanced_collector",
            operation_type="full_scrape",
            status="running",
            started_at=start_time
        )
        
        try:
            # Add scraping log to database
            db.add(scraping_log)
            await db.commit()
            await db.refresh(scraping_log)
            
            if country_code not in self.data_sources:
                raise ValueError(f"Country {country_code} not supported")
            
            country_data = self.data_sources[country_code]
            total_records_scraped = 0
            total_records_updated = 0
            total_records_failed = 0
            
            # Scrape from all sources for this country
            for source in country_data['sources']:
                try:
                    source_records = await self._scrape_source(db, country_code, source)
                    total_records_scraped += source_records['scraped']
                    total_records_updated += source_records['updated']
                    total_records_failed += source_records['failed']
                except Exception as e:
                    logger.error(f"Error scraping source {source['name']} for {country_code}: {e}")
                    total_records_failed += 1
            
            # Update scraping log with success
            duration = (datetime.utcnow() - start_time).total_seconds()
            scraping_log.status = "success"
            scraping_log.records_scraped = total_records_scraped
            scraping_log.records_updated = total_records_updated
            scraping_log.records_failed = total_records_failed
            scraping_log.duration_seconds = duration
            scraping_log.completed_at = datetime.utcnow()
            
            await db.commit()
            
            return ScrapingResult(
                success=True,
                country_code=country_code,
                records_scraped=total_records_scraped,
                records_updated=total_records_updated,
                records_failed=total_records_failed,
                duration_seconds=duration
            )
            
        except Exception as e:
            # Update scraping log with failure
            duration = (datetime.utcnow() - start_time).total_seconds()
            scraping_log.status = "failed"
            scraping_log.error_message = str(e)
            scraping_log.duration_seconds = duration
            scraping_log.completed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.error(f"Error scraping data for {country_code}: {e}")
            return ScrapingResult(
                success=False,
                country_code=country_code,
                records_scraped=0,
                records_updated=0,
                records_failed=1,
                error_message=str(e),
                duration_seconds=duration
            )
    
    async def _scrape_source(self, db: AsyncSession, country_code: str, source: Dict[str, Any]) -> Dict[str, int]:
        """Scrape data from a specific source."""
        scraper_method = getattr(self, f"_scrape_{source['scraper']}", None)
        if not scraper_method:
            raise ValueError(f"Scraper method {source['scraper']} not found")
        
        records_scraped = 0
        records_updated = 0
        records_failed = 0
        
        for url in source['visa_urls']:
            try:
                requirements = await scraper_method(country_code, url, source)
                
                for requirement in requirements:
                    try:
                        # Store or update requirement in database
                        await self._store_requirement(db, requirement)
                        records_scraped += 1
                        records_updated += 1
                    except Exception as e:
                        logger.error(f"Error storing requirement: {e}")
                        records_failed += 1
                        
            except Exception as e:
                logger.error(f"Error scraping URL {url}: {e}")
                records_failed += 1
        
        return {
            'scraped': records_scraped,
            'updated': records_updated,
            'failed': records_failed
        }
    
    async def _store_requirement(self, db: AsyncSession, requirement_data: Dict[str, Any]) -> None:
        """Store or update immigration requirement in database."""
        # Check if requirement already exists
        stmt = select(ImmigrationRequirements).where(
            ImmigrationRequirements.country_code == requirement_data['country_code'],
            ImmigrationRequirements.visa_type == requirement_data['visa_type'],
            ImmigrationRequirements.source_url == requirement_data['source_url']
        )
        
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            for key, value in requirement_data.items():
                if hasattr(existing, key) and key not in ['id', 'created_at']:
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
        else:
            # Create new record
            new_requirement = ImmigrationRequirements(**requirement_data)
            db.add(new_requirement)
        
        await db.commit()
    
    async def _scrape_uscis(self, country_code: str, url: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape USCIS website for US immigration requirements."""
        requirements = []
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return requirements
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract visa information from USCIS pages
                # This is a simplified example - real implementation would be more sophisticated
                visa_sections = soup.find_all(['div', 'section'], class_=re.compile(r'visa|immigration|work|study'))
                
                for section in visa_sections:
                    title_elem = section.find(['h1', 'h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Determine visa type from title
                    visa_type = self._determine_visa_type(title)
                    
                    # Extract requirements and fees
                    requirements_list = []
                    fee_info = None
                    
                    # Look for requirements in lists
                    lists = section.find_all(['ul', 'ol'])
                    for lst in lists:
                        items = lst.find_all('li')
                        for item in items:
                            text = item.get_text(strip=True)
                            if 'fee' in text.lower() or '$' in text:
                                fee_info = text
                            else:
                                requirements_list.append(text)
                    
                    if title and visa_type:
                        requirement = {
                            'country_code': country_code,
                            'visa_type': visa_type,
                            'visa_category': title,
                            'requirements': requirements_list,
                            'application_fee_usd': self._extract_fee(fee_info) if fee_info else None,
                            'source_url': url,
                            'source_name': source['name'],
                            'last_updated': datetime.utcnow(),
                            'data_confidence_score': 0.8
                        }
                        requirements.append(requirement)
                
        except Exception as e:
            logger.error(f"Error scraping USCIS: {e}")
        
        return requirements
    
    async def _scrape_ircc(self, country_code: str, url: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape IRCC website for Canadian immigration requirements."""
        requirements = []
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return requirements
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract visa information from IRCC pages
                visa_sections = soup.find_all(['div', 'section'], class_=re.compile(r'visa|immigration|work|study'))
                
                for section in visa_sections:
                    title_elem = section.find(['h1', 'h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    visa_type = self._determine_visa_type(title)
                    
                    # Extract requirements
                    requirements_list = []
                    fee_info = None
                    
                    lists = section.find_all(['ul', 'ol'])
                    for lst in lists:
                        items = lst.find_all('li')
                        for item in items:
                            text = item.get_text(strip=True)
                            if 'fee' in text.lower() or 'cad' in text.lower():
                                fee_info = text
                            else:
                                requirements_list.append(text)
                    
                    if title and visa_type:
                        requirement = {
                            'country_code': country_code,
                            'visa_type': visa_type,
                            'visa_category': title,
                            'requirements': requirements_list,
                            'application_fee_usd': self._extract_fee(fee_info) if fee_info else None,
                            'source_url': url,
                            'source_name': source['name'],
                            'last_updated': datetime.utcnow(),
                            'data_confidence_score': 0.8
                        }
                        requirements.append(requirement)
                
        except Exception as e:
            logger.error(f"Error scraping IRCC: {e}")
        
        return requirements
    
    async def _scrape_uk_gov(self, country_code: str, url: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape UK Government website for immigration requirements."""
        # Similar implementation to USCIS/IRCC but for UK
        return []
    
    async def _scrape_australia_gov(self, country_code: str, url: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape Australian Government website for immigration requirements."""
        # Similar implementation to USCIS/IRCC but for Australia
        return []
    
    async def _scrape_germany_gov(self, country_code: str, url: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape German Government website for immigration requirements."""
        # Similar implementation to USCIS/IRCC but for Germany
        return []
    
    def _determine_visa_type(self, title: str) -> str:
        """Determine visa type from title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['work', 'employment', 'job']):
            return 'work'
        elif any(word in title_lower for word in ['student', 'study', 'education']):
            return 'student'
        elif any(word in title_lower for word in ['family', 'spouse', 'partner']):
            return 'family'
        elif any(word in title_lower for word in ['business', 'investor', 'entrepreneur']):
            return 'business'
        elif any(word in title_lower for word in ['tourist', 'visitor', 'travel']):
            return 'tourist'
        elif any(word in title_lower for word in ['permanent', 'residence', 'green card']):
            return 'permanent_residence'
        else:
            return 'other'
    
    def _extract_fee(self, fee_text: str) -> Optional[float]:
        """Extract fee amount from text."""
        if not fee_text:
            return None
        
        # Look for currency amounts
        import re
        patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|CAD|GBP|EUR|AUD)',  # 1234.56 USD
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|pounds?|euros?)',  # 1234.56 dollars
        ]
        
        for pattern in patterns:
            match = re.search(pattern, fee_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    async def get_supported_countries(self) -> List[str]:
        """Get list of supported countries."""
        return list(self.data_sources.keys())
    
    async def get_scraping_status(self, db: AsyncSession, country_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get scraping status for countries."""
        stmt = select(ScrapingLog)
        if country_code:
            stmt = stmt.where(ScrapingLog.country_code == country_code)
        stmt = stmt.order_by(ScrapingLog.started_at.desc()).limit(100)
        
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        return [
            {
                'id': log.id,
                'country_code': log.country_code,
                'source_name': log.source_name,
                'operation_type': log.operation_type,
                'status': log.status,
                'records_scraped': log.records_scraped,
                'records_updated': log.records_updated,
                'records_failed': log.records_failed,
                'error_message': log.error_message,
                'duration_seconds': log.duration_seconds,
                'started_at': log.started_at.isoformat() if log.started_at else None,
                'completed_at': log.completed_at.isoformat() if log.completed_at else None
            }
            for log in logs
        ]
