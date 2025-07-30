"""
Cron service for automated data collection and policy change detection.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path

from app.services.immigration_data_collector import ImmigrationDataCollector, ImmigrationPolicy
from app.services.data_normalizer import DataNormalizer, NormalizedPolicy
from app.core.config import settings

logger = logging.getLogger(__name__)


class CronService:
    """Service for managing automated data collection tasks."""
    
    def __init__(self):
        self.data_collector = ImmigrationDataCollector()
        self.data_normalizer = DataNormalizer()
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    async def run_daily_data_collection(self) -> Dict[str, Any]:
        """Run daily data collection for all supported countries."""
        logger.info("Starting daily data collection")
        
        try:
            # Collect data from all sources
            scraped_data = await self.data_collector.collect_data()
            
            # Normalize the data
            all_normalized_policies = []
            for country_code, data in scraped_data.items():
                normalized_policies = self.data_normalizer.normalize_policies(data.policies)
                all_normalized_policies.extend(normalized_policies)
                
                # Save country-specific data
                await self._save_country_data(country_code, normalized_policies)
            
            # Generate summary
            summary = self.data_normalizer.get_policy_summary(all_normalized_policies)
            
            # Save global summary
            await self._save_global_summary(summary)
            
            # Check for policy changes
            changes = await self.run_policy_change_detection()
            
            logger.info(f"Daily data collection completed. Found {len(changes)} policy changes.")
            
            return {
                'status': 'success',
                'policies_collected': len(all_normalized_policies),
                'countries_processed': len(scraped_data),
                'policy_changes_detected': len(changes),
                'summary': summary,
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error in daily data collection: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_weekly_data_collection(self) -> Dict[str, Any]:
        """Run comprehensive weekly data collection with detailed analysis."""
        logger.info("Starting weekly data collection")
        
        try:
            # Get supported countries
            supported_countries = await self.data_collector.get_supported_countries()
            
            # Collect data with detailed analysis
            results = {}
            total_policies = 0
            
            for country_code in supported_countries:
                try:
                    # Collect data for specific country
                    scraped_data = await self.data_collector.collect_data([country_code])
                    
                    if country_code in scraped_data:
                        data = scraped_data[country_code]
                        normalized_policies = self.data_normalizer.normalize_policies(data.policies)
                        
                        # Analyze country-specific data
                        country_analysis = await self._analyze_country_data(country_code, normalized_policies)
                        
                        results[country_code] = {
                            'policies_count': len(normalized_policies),
                            'analysis': country_analysis,
                            'last_updated': datetime.utcnow().isoformat()
                        }
                        
                        total_policies += len(normalized_policies)
                        
                        # Save detailed country analysis
                        await self._save_country_analysis(country_code, country_analysis)
                        
                except Exception as e:
                    logger.error(f"Error processing country {country_code}: {str(e)}")
                    results[country_code] = {
                        'error': str(e),
                        'policies_count': 0
                    }
            
            # Generate comprehensive summary
            comprehensive_summary = await self._generate_comprehensive_summary(results)
            
            # Save comprehensive summary
            await self._save_comprehensive_summary(comprehensive_summary)
            
            logger.info(f"Weekly data collection completed. Processed {total_policies} policies across {len(results)} countries.")
            
            return {
                'status': 'success',
                'total_policies': total_policies,
                'countries_processed': len(results),
                'comprehensive_summary': comprehensive_summary,
                'country_results': results
            }
            
        except Exception as e:
            logger.error(f"Error in weekly data collection: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_policy_change_detection(self) -> Dict[str, Any]:
        """Run policy change detection against previously collected data."""
        logger.info("Starting policy change detection")
        
        try:
            # Load previous data
            previous_data = await self._load_previous_data()
            
            if not previous_data:
                logger.warning("No previous data found for change detection")
                return {
                    'status': 'warning',
                    'message': 'No previous data available for comparison'
                }
            
            # Collect current data
            current_scraped_data = await self.data_collector.collect_data()
            
            changes_detected = []
            
            for country_code, current_data in current_scraped_data.items():
                if country_code not in previous_data:
                    # New country data
                    changes_detected.append({
                        'country_code': country_code,
                        'change_type': 'new_country',
                        'policies_count': len(current_data.policies)
                    })
                    continue
                
                # Compare policies
                previous_policies = previous_data[country_code]['policies']
                current_policies = current_data.policies
                
                # Detect changes using MCP server's change detection
                changes = self.data_collector.detect_policy_changes(previous_policies, current_policies)
                
                if changes:
                    changes_detected.append({
                        'country_code': country_code,
                        'change_type': 'policy_changes',
                        'changes_count': len(changes),
                        'changed_policies': [p.title for p in changes]
                    })
            
            # Save change detection results
            await self._save_change_detection_results(changes_detected)
            
            logger.info(f"Policy change detection completed. Found {len(changes_detected)} change events.")
            
            return {
                'status': 'success',
                'changes_detected': len(changes_detected),
                'change_details': changes_detected
            }
            
        except Exception as e:
            logger.error(f"Error in policy change detection: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _save_country_data(self, country_code: str, policies: List[NormalizedPolicy]) -> None:
        """Save country-specific data to file."""
        file_path = self.data_dir / f"{country_code}_policies.json"
        
        data = {
            'country_code': country_code,
            'last_updated': datetime.utcnow().isoformat(),
            'policies_count': len(policies),
            'policies': [
                {
                    'title': p.title,
                    'policy_type': p.policy_type,
                    'description': p.description,
                    'requirements': p.requirements,
                    'estimated_duration_days': p.estimated_duration_days,
                    'estimated_cost_usd': p.estimated_cost_usd,
                    'complexity_score': p.complexity_score,
                    'eligibility_criteria': p.eligibility_criteria,
                    'documents_required': p.documents_required,
                    'source_url': p.source_url
                }
                for p in policies
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _save_global_summary(self, summary: Dict[str, Any]) -> None:
        """Save global data summary."""
        file_path = self.data_dir / "global_summary.json"
        
        data = {
            'last_updated': datetime.utcnow().isoformat(),
            'summary': summary
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _analyze_country_data(self, country_code: str, policies: List[NormalizedPolicy]) -> Dict[str, Any]:
        """Analyze country-specific immigration data."""
        if not policies:
            return {'error': 'No policies found'}
        
        # Calculate statistics
        total_policies = len(policies)
        policy_types = list(set(p.policy_type for p in policies))
        
        # Complexity analysis
        complexity_distribution = {}
        for i in range(1, 6):
            complexity_distribution[f'level_{i}'] = len([p for p in policies if p.complexity_score == i])
        
        # Cost analysis
        costs = [p.estimated_cost_usd for p in policies if p.estimated_cost_usd]
        cost_stats = {
            'min': min(costs) if costs else None,
            'max': max(costs) if costs else None,
            'average': sum(costs) / len(costs) if costs else None
        }
        
        # Duration analysis
        durations = [p.estimated_duration_days for p in policies if p.estimated_duration_days]
        duration_stats = {
            'min': min(durations) if durations else None,
            'max': max(durations) if durations else None,
            'average': sum(durations) / len(durations) if durations else None
        }
        
        # Document requirements analysis
        all_documents = []
        for p in policies:
            all_documents.extend(p.documents_required)
        
        document_frequency = {}
        for doc in set(all_documents):
            document_frequency[doc] = all_documents.count(doc)
        
        return {
            'total_policies': total_policies,
            'policy_types': policy_types,
            'complexity_distribution': complexity_distribution,
            'cost_statistics': cost_stats,
            'duration_statistics': duration_stats,
            'most_common_documents': sorted(document_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
            'analysis_date': datetime.utcnow().isoformat()
        }
    
    async def _save_country_analysis(self, country_code: str, analysis: Dict[str, Any]) -> None:
        """Save country-specific analysis."""
        file_path = self.data_dir / f"{country_code}_analysis.json"
        
        with open(file_path, 'w') as f:
            json.dump(analysis, f, indent=2)
    
    async def _generate_comprehensive_summary(self, country_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary across all countries."""
        total_policies = sum(result.get('policies_count', 0) for result in country_results.values())
        
        # Aggregate complexity data
        total_complexity = {}
        for result in country_results.values():
            if 'analysis' in result and 'complexity_distribution' in result['analysis']:
                for level, count in result['analysis']['complexity_distribution'].items():
                    total_complexity[level] = total_complexity.get(level, 0) + count
        
        # Aggregate cost data
        all_costs = []
        for result in country_results.values():
            if 'analysis' in result and 'cost_statistics' in result['analysis']:
                cost_stats = result['analysis']['cost_statistics']
                if cost_stats.get('average'):
                    all_costs.append(cost_stats['average'])
        
        # Aggregate duration data
        all_durations = []
        for result in country_results.values():
            if 'analysis' in result and 'duration_statistics' in result['analysis']:
                duration_stats = result['analysis']['duration_statistics']
                if duration_stats.get('average'):
                    all_durations.append(duration_stats['average'])
        
        return {
            'total_policies': total_policies,
            'countries_analyzed': len(country_results),
            'global_complexity_distribution': total_complexity,
            'global_average_cost': sum(all_costs) / len(all_costs) if all_costs else None,
            'global_average_duration': sum(all_durations) / len(all_durations) if all_durations else None,
            'analysis_date': datetime.utcnow().isoformat()
        }
    
    async def _save_comprehensive_summary(self, summary: Dict[str, Any]) -> None:
        """Save comprehensive summary."""
        file_path = self.data_dir / "comprehensive_summary.json"
        
        with open(file_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    async def _load_previous_data(self) -> Optional[Dict[str, Any]]:
        """Load previously collected data for comparison."""
        try:
            file_path = self.data_dir / "previous_data.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading previous data: {str(e)}")
            return None
    
    async def _save_change_detection_results(self, changes: List[Dict[str, Any]]) -> None:
        """Save policy change detection results."""
        file_path = self.data_dir / "change_detection_results.json"
        
        data = {
            'detection_date': datetime.utcnow().isoformat(),
            'changes_detected': len(changes),
            'change_details': changes
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def get_data_collection_status(self) -> Dict[str, Any]:
        """Get the status of data collection."""
        try:
            # Check if data files exist
            data_files = list(self.data_dir.glob("*.json"))
            
            if not data_files:
                return {
                    'status': 'no_data',
                    'message': 'No data has been collected yet'
                }
            
            # Get the most recent data file
            latest_file = max(data_files, key=lambda f: f.stat().st_mtime)
            
            # Load global summary if available
            global_summary_path = self.data_dir / "global_summary.json"
            if global_summary_path.exists():
                with open(global_summary_path, 'r') as f:
                    global_summary = json.load(f)
            else:
                global_summary = None
            
            return {
                'status': 'data_available',
                'latest_update': datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                'data_files_count': len(data_files),
                'global_summary': global_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting data collection status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 