"""
Data normalization service for immigration policy data.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.services.immigration_data_collector import ImmigrationPolicy

logger = logging.getLogger(__name__)


@dataclass
class NormalizedPolicy:
    """Normalized immigration policy data."""
    country_code: str
    policy_type: str
    title: str
    description: str
    requirements: List[str]
    processing_time_days: Optional[int]
    cost_usd: Optional[float]
    source_url: str
    last_updated: datetime
    normalized_requirements: List[str]
    estimated_duration_days: Optional[int]
    estimated_cost_usd: Optional[float]
    complexity_score: int  # 1-5 scale
    eligibility_criteria: List[str]
    documents_required: List[str]


class DataNormalizer:
    """Service for normalizing immigration policy data."""
    
    def __init__(self):
        self.cost_patterns = self._initialize_cost_patterns()
        self.time_patterns = self._initialize_time_patterns()
        self.requirement_patterns = self._initialize_requirement_patterns()
        self.document_patterns = self._initialize_document_patterns()
    
    def _initialize_cost_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for extracting cost information."""
        return [
            {
                'pattern': r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                'multiplier': 1.0,
                'description': 'USD amount'
            },
            {
                'pattern': r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)',
                'multiplier': 1.0,
                'description': 'USD with text'
            },
            {
                'pattern': r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:CAD|Canadian\s+dollars?)',
                'multiplier': 0.75,  # Approximate USD conversion
                'description': 'CAD amount'
            },
            {
                'pattern': r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:GBP|pounds?)',
                'multiplier': 1.25,  # Approximate USD conversion
                'description': 'GBP amount'
            },
            {
                'pattern': r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:AUD|Australian\s+dollars?)',
                'multiplier': 0.65,  # Approximate USD conversion
                'description': 'AUD amount'
            },
            {
                'pattern': r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:EUR|euros?)',
                'multiplier': 1.10,  # Approximate USD conversion
                'description': 'EUR amount'
            }
        ]
    
    def _initialize_time_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for extracting processing time information."""
        return [
            {
                'pattern': r'(\d+)\s*(?:to\s*)?(\d+)?\s*(?:business\s*)?(?:working\s*)?(?:days?|weeks?|months?)',
                'description': 'Time range with units'
            },
            {
                'pattern': r'(\d+)\s*(?:to\s*)?(\d+)?\s*(?:business\s*)?(?:working\s*)?(?:days?|weeks?|months?)',
                'description': 'Time with business/working qualifier'
            },
            {
                'pattern': r'(\d+)\s*(?:days?|weeks?|months?)',
                'description': 'Simple time with units'
            }
        ]
    
    def _initialize_requirement_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for extracting requirements."""
        return [
            {
                'pattern': r'(?:must|require|need|eligible|qualify).*?(?:be|have|hold|possess|maintain)',
                'description': 'Eligibility requirements'
            },
            {
                'pattern': r'(?:minimum|at least|no less than).*?(?:years?|months?|experience|education)',
                'description': 'Minimum requirements'
            },
            {
                'pattern': r'(?:prove|demonstrate|show|provide).*?(?:evidence|proof|documentation)',
                'description': 'Documentation requirements'
            }
        ]
    
    def _initialize_document_patterns(self) -> List[str]:
        """Initialize patterns for extracting required documents."""
        return [
            r'passport',
            r'birth\s+certificate',
            r'marriage\s+certificate',
            r'police\s+(?:certificate|clearance|record)',
            r'medical\s+(?:examination|certificate|report)',
            r'financial\s+(?:statement|evidence|proof)',
            r'employment\s+(?:letter|contract|offer)',
            r'education\s+(?:diploma|degree|certificate)',
            r'language\s+(?:test|certificate|proficiency)',
            r'photograph',
            r'application\s+form',
            r'fee\s+payment',
            r'bank\s+statement',
            r'tax\s+return',
            r'resume',
            r'cover\s+letter',
            r'reference\s+letter',
            r'criminal\s+record\s+check',
            r'health\s+insurance',
            r'proof\s+of\s+funds'
        ]
    
    def normalize_policies(self, policies: List[ImmigrationPolicy]) -> List[NormalizedPolicy]:
        """Normalize a list of immigration policies."""
        normalized_policies = []
        
        for policy in policies:
            try:
                normalized = self._normalize_single_policy(policy)
                normalized_policies.append(normalized)
                
            except Exception as e:
                logger.error(f"Error normalizing policy {policy.title}: {str(e)}")
                # Create a basic normalized version
                normalized = self._create_basic_normalized_policy(policy)
                normalized_policies.append(normalized)
        
        return normalized_policies
    
    def _normalize_single_policy(self, policy: ImmigrationPolicy) -> NormalizedPolicy:
        """Normalize a single immigration policy."""
        # Extract cost information
        estimated_cost = self._extract_cost(policy.description, policy.requirements)
        
        # Extract processing time
        estimated_duration = self._extract_processing_time(policy.description, policy.requirements)
        
        # Normalize requirements
        normalized_requirements = self._normalize_requirements(policy.requirements)
        
        # Extract eligibility criteria
        eligibility_criteria = self._extract_eligibility_criteria(policy.requirements)
        
        # Extract required documents
        documents_required = self._extract_required_documents(policy.description, policy.requirements)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            policy.requirements, 
            estimated_duration, 
            estimated_cost
        )
        
        return NormalizedPolicy(
            country_code=policy.country_code,
            policy_type=policy.policy_type,
            title=policy.title,
            description=policy.description,
            requirements=policy.requirements,
            processing_time_days=policy.processing_time_days,
            cost_usd=policy.cost_usd,
            source_url=policy.source_url,
            last_updated=policy.last_updated,
            normalized_requirements=normalized_requirements,
            estimated_duration_days=estimated_duration,
            estimated_cost_usd=estimated_cost,
            complexity_score=complexity_score,
            eligibility_criteria=eligibility_criteria,
            documents_required=documents_required
        )
    
    def _extract_cost(self, description: str, requirements: List[str]) -> Optional[float]:
        """Extract cost information from text."""
        text_to_search = description + " " + " ".join(requirements)
        
        for pattern_info in self.cost_patterns:
            matches = re.findall(pattern_info['pattern'], text_to_search, re.IGNORECASE)
            if matches:
                try:
                    # Take the first match and convert to float
                    cost_str = matches[0].replace(',', '')
                    cost = float(cost_str) * pattern_info['multiplier']
                    return round(cost, 2)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_processing_time(self, description: str, requirements: List[str]) -> Optional[int]:
        """Extract processing time information from text."""
        text_to_search = description + " " + " ".join(requirements)
        
        for pattern_info in self.time_patterns:
            matches = re.findall(pattern_info['pattern'], text_to_search, re.IGNORECASE)
            if matches:
                try:
                    match = matches[0]
                    if isinstance(match, tuple):
                        # Range format (e.g., "30 to 60 days")
                        min_days = int(match[0])
                        max_days = int(match[1]) if match[1] else min_days
                        return (min_days + max_days) // 2
                    else:
                        # Single value
                        return int(match)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _normalize_requirements(self, requirements: List[str]) -> List[str]:
        """Normalize and clean requirement text."""
        normalized = []
        
        for req in requirements:
            # Clean up the requirement text
            cleaned = re.sub(r'\s+', ' ', req.strip())
            cleaned = re.sub(r'[^\w\s\-.,()]', '', cleaned)
            
            if cleaned and len(cleaned) > 5:  # Filter out very short requirements
                normalized.append(cleaned)
        
        return normalized
    
    def _extract_eligibility_criteria(self, requirements: List[str]) -> List[str]:
        """Extract eligibility criteria from requirements."""
        criteria = []
        
        for req in requirements:
            for pattern_info in self.requirement_patterns:
                if re.search(pattern_info['pattern'], req, re.IGNORECASE):
                    criteria.append(req)
                    break
        
        return criteria
    
    def _extract_required_documents(self, description: str, requirements: List[str]) -> List[str]:
        """Extract required documents from text."""
        text_to_search = description + " " + " ".join(requirements)
        documents = []
        
        for pattern in self.document_patterns:
            if re.search(pattern, text_to_search, re.IGNORECASE):
                documents.append(pattern.replace(r'\s+', ' '))
        
        return list(set(documents))  # Remove duplicates
    
    def _calculate_complexity_score(self, requirements: List[str], 
                                  duration: Optional[int], 
                                  cost: Optional[float]) -> int:
        """Calculate complexity score (1-5) based on various factors."""
        score = 1
        
        # Factor 1: Number of requirements
        if len(requirements) > 10:
            score += 2
        elif len(requirements) > 5:
            score += 1
        
        # Factor 2: Processing time
        if duration and duration > 180:  # More than 6 months
            score += 1
        elif duration and duration > 90:  # More than 3 months
            score += 1
        
        # Factor 3: Cost
        if cost and cost > 5000:
            score += 1
        elif cost and cost > 1000:
            score += 1
        
        # Factor 4: Complex requirements (check for specific keywords)
        complex_keywords = ['sponsor', 'petition', 'labor certification', 'priority date', 'quota']
        for req in requirements:
            if any(keyword in req.lower() for keyword in complex_keywords):
                score += 1
                break
        
        return min(score, 5)  # Cap at 5
    
    def _create_basic_normalized_policy(self, policy: ImmigrationPolicy) -> NormalizedPolicy:
        """Create a basic normalized policy when normalization fails."""
        return NormalizedPolicy(
            country_code=policy.country_code,
            policy_type=policy.policy_type,
            title=policy.title,
            description=policy.description,
            requirements=policy.requirements,
            processing_time_days=policy.processing_time_days,
            cost_usd=policy.cost_usd,
            source_url=policy.source_url,
            last_updated=policy.last_updated,
            normalized_requirements=policy.requirements,
            estimated_duration_days=None,
            estimated_cost_usd=None,
            complexity_score=3,  # Default medium complexity
            eligibility_criteria=[],
            documents_required=[]
        )
    
    def get_policy_summary(self, normalized_policies: List[NormalizedPolicy]) -> Dict[str, Any]:
        """Generate a summary of normalized policies."""
        if not normalized_policies:
            return {}
        
        total_policies = len(normalized_policies)
        countries = list(set(p.country_code for p in normalized_policies))
        policy_types = list(set(p.policy_type for p in normalized_policies))
        
        # Calculate average complexity
        avg_complexity = sum(p.complexity_score for p in normalized_policies) / total_policies
        
        # Calculate average cost (excluding None values)
        costs = [p.estimated_cost_usd for p in normalized_policies if p.estimated_cost_usd]
        avg_cost = sum(costs) / len(costs) if costs else None
        
        # Calculate average duration (excluding None values)
        durations = [p.estimated_duration_days for p in normalized_policies if p.estimated_duration_days]
        avg_duration = sum(durations) / len(durations) if durations else None
        
        return {
            'total_policies': total_policies,
            'countries': countries,
            'policy_types': policy_types,
            'average_complexity': round(avg_complexity, 2),
            'average_cost_usd': round(avg_cost, 2) if avg_cost else None,
            'average_duration_days': round(avg_duration, 2) if avg_duration else None,
            'last_updated': max(p.last_updated for p in normalized_policies).isoformat()
        } 