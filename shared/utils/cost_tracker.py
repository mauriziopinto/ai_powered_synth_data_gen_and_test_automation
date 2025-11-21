"""AWS cost tracking and optimization for Bedrock and ECS usage.

This module provides comprehensive cost tracking, estimation, and optimization
recommendations for AWS Bedrock and ECS services used in the synthetic data generator.

Validates Requirements 27.1, 27.2, 27.3, 27.4, 27.5
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """AWS service types for cost tracking."""
    BEDROCK = "bedrock"
    ECS = "ecs"
    S3 = "s3"
    OTHER = "other"


class OptimizationType(Enum):
    """Types of cost optimization recommendations."""
    MODEL_SELECTION = "model_selection"
    BATCH_PROCESSING = "batch_processing"
    CACHING = "caching"
    RESOURCE_SIZING = "resource_sizing"
    SCHEDULING = "scheduling"


@dataclass
class CostEntry:
    """Individual cost tracking entry."""
    timestamp: datetime
    service_type: ServiceType
    operation: str
    cost_usd: float
    details: Dict[str, Any] = field(default_factory=dict)
    project_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'service_type': self.service_type.value,
            'operation': self.operation,
            'cost_usd': self.cost_usd,
            'details': self.details,
            'project_id': self.project_id,
            'workflow_id': self.workflow_id
        }


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    type: OptimizationType
    title: str
    description: str
    potential_savings_usd: float
    potential_savings_percent: float
    priority: int  # 1-5, 1 being highest
    implementation_effort: str  # 'low', 'medium', 'high'
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'potential_savings_usd': self.potential_savings_usd,
            'potential_savings_percent': self.potential_savings_percent,
            'priority': self.priority,
            'implementation_effort': self.implementation_effort,
            'created_at': self.created_at.isoformat()
        }


class BedrockCostCalculator:
    """Calculate costs for AWS Bedrock model usage.
    
    Pricing as of 2024 (per 1000 tokens).
    """
    
    # Model pricing per 1000 tokens
    MODEL_PRICING = {
        'anthropic.claude-3-sonnet-20240229-v1:0': {
            'input_per_1k': 0.003,
            'output_per_1k': 0.015
        },
        'anthropic.claude-3-haiku-20240307-v1:0': {
            'input_per_1k': 0.00025,
            'output_per_1k': 0.00125
        },
        'anthropic.claude-instant-v1': {
            'input_per_1k': 0.0008,
            'output_per_1k': 0.0024
        },
        'amazon.titan-text-express-v1': {
            'input_per_1k': 0.0008,
            'output_per_1k': 0.0016
        },
        'amazon.titan-text-lite-v1': {
            'input_per_1k': 0.0003,
            'output_per_1k': 0.0004
        }
    }
    
    @classmethod
    def calculate_cost(
        cls,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for model invocation.
        
        Args:
            model_id: Bedrock model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Cost in USD
        """
        pricing = cls.MODEL_PRICING.get(model_id)
        
        if not pricing:
            logger.warning(f"Unknown model {model_id}, using default pricing")
            # Default pricing for unknown models
            input_cost = (input_tokens / 1000) * 0.001
            output_cost = (output_tokens / 1000) * 0.002
        else:
            input_cost = (input_tokens / 1000) * pricing['input_per_1k']
            output_cost = (output_tokens / 1000) * pricing['output_per_1k']
        
        return input_cost + output_cost
    
    @classmethod
    def estimate_cost(
        cls,
        model_id: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> Dict[str, float]:
        """Estimate cost range for model invocation.
        
        Args:
            model_id: Bedrock model identifier
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
        
        Returns:
            Dictionary with min, max, and expected costs
        """
        base_cost = cls.calculate_cost(model_id, estimated_input_tokens, estimated_output_tokens)
        
        # Add variance for estimation (±20%)
        return {
            'min_cost_usd': base_cost * 0.8,
            'expected_cost_usd': base_cost,
            'max_cost_usd': base_cost * 1.2
        }
    
    @classmethod
    def get_cheapest_model(cls) -> str:
        """Get the cheapest model available.
        
        Returns:
            Model ID of cheapest model
        """
        cheapest_model = None
        lowest_avg_cost = float('inf')
        
        for model_id, pricing in cls.MODEL_PRICING.items():
            avg_cost = (pricing['input_per_1k'] + pricing['output_per_1k']) / 2
            if avg_cost < lowest_avg_cost:
                lowest_avg_cost = avg_cost
                cheapest_model = model_id
        
        return cheapest_model or 'amazon.titan-text-lite-v1'


class ECSCostCalculator:
    """Calculate costs for AWS ECS (Fargate) usage.
    
    Pricing as of 2024 for us-east-1.
    """
    
    # Fargate pricing per hour
    FARGATE_PRICING = {
        'vcpu_per_hour': 0.04048,  # Per vCPU
        'memory_gb_per_hour': 0.004445  # Per GB
    }
    
    @classmethod
    def calculate_cost(
        cls,
        vcpu: float,
        memory_gb: float,
        duration_seconds: float
    ) -> float:
        """Calculate cost for ECS Fargate task execution.
        
        Args:
            vcpu: Number of vCPUs
            memory_gb: Memory in GB
            duration_seconds: Task duration in seconds
        
        Returns:
            Cost in USD
        """
        duration_hours = duration_seconds / 3600
        
        vcpu_cost = vcpu * cls.FARGATE_PRICING['vcpu_per_hour'] * duration_hours
        memory_cost = memory_gb * cls.FARGATE_PRICING['memory_gb_per_hour'] * duration_hours
        
        return vcpu_cost + memory_cost
    
    @classmethod
    def estimate_cost(
        cls,
        vcpu: float,
        memory_gb: float,
        estimated_duration_seconds: float
    ) -> Dict[str, float]:
        """Estimate cost range for ECS task.
        
        Args:
            vcpu: Number of vCPUs
            memory_gb: Memory in GB
            estimated_duration_seconds: Estimated duration in seconds
        
        Returns:
            Dictionary with min, max, and expected costs
        """
        base_cost = cls.calculate_cost(vcpu, memory_gb, estimated_duration_seconds)
        
        # Add variance for estimation (±30% for duration uncertainty)
        return {
            'min_cost_usd': base_cost * 0.7,
            'expected_cost_usd': base_cost,
            'max_cost_usd': base_cost * 1.3
        }


class CostTracker:
    """Track and analyze AWS costs in real-time.
    
    Validates Requirements 27.1, 27.2, 27.3, 27.4, 27.5
    """
    
    def __init__(self, storage_path: str = "cost_data"):
        """Initialize cost tracker.
        
        Args:
            storage_path: Path to store cost data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.cost_entries: List[CostEntry] = []
        self.bedrock_calculator = BedrockCostCalculator()
        self.ecs_calculator = ECSCostCalculator()
        
        self._load_data()
        
        logger.info(f"Initialized cost tracker with storage: {storage_path}")
    
    def track_bedrock_usage(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = "invoke",
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> CostEntry:
        """Track Bedrock model usage and cost.
        
        Validates Requirement 27.1: Monitor AWS Bedrock usage including token consumption,
        model invocations, and associated costs in real-time.
        
        Args:
            model_id: Bedrock model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation: Operation type
            project_id: Optional project identifier
            workflow_id: Optional workflow identifier
        
        Returns:
            Created cost entry
        """
        cost = self.bedrock_calculator.calculate_cost(model_id, input_tokens, output_tokens)
        
        entry = CostEntry(
            timestamp=datetime.now(),
            service_type=ServiceType.BEDROCK,
            operation=operation,
            cost_usd=cost,
            details={
                'model_id': model_id,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            },
            project_id=project_id,
            workflow_id=workflow_id
        )
        
        self.cost_entries.append(entry)
        self._save_data()
        
        logger.debug(f"Tracked Bedrock usage: {model_id} - ${cost:.6f}")
        return entry
    
    def track_ecs_usage(
        self,
        vcpu: float,
        memory_gb: float,
        duration_seconds: float,
        operation: str = "task_execution",
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> CostEntry:
        """Track ECS Fargate usage and cost.
        
        Validates Requirement 27.1: Monitor AWS usage and associated costs in real-time.
        
        Args:
            vcpu: Number of vCPUs
            memory_gb: Memory in GB
            duration_seconds: Task duration in seconds
            operation: Operation type
            project_id: Optional project identifier
            workflow_id: Optional workflow identifier
        
        Returns:
            Created cost entry
        """
        cost = self.ecs_calculator.calculate_cost(vcpu, memory_gb, duration_seconds)
        
        entry = CostEntry(
            timestamp=datetime.now(),
            service_type=ServiceType.ECS,
            operation=operation,
            cost_usd=cost,
            details={
                'vcpu': vcpu,
                'memory_gb': memory_gb,
                'duration_seconds': duration_seconds,
                'duration_hours': duration_seconds / 3600
            },
            project_id=project_id,
            workflow_id=workflow_id
        )
        
        self.cost_entries.append(entry)
        self._save_data()
        
        logger.debug(f"Tracked ECS usage: {vcpu}vCPU, {memory_gb}GB - ${cost:.6f}")
        return entry
    
    def get_cost_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown.
        
        Validates Requirement 27.1: Provide detailed cost breakdowns by operation and time period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            project_id: Optional project filter
            workflow_id: Optional workflow filter
        
        Returns:
            Cost breakdown dictionary
        """
        filtered_entries = self._filter_entries(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            workflow_id=workflow_id
        )
        
        if not filtered_entries:
            return {
                'total_cost_usd': 0.0,
                'entry_count': 0,
                'by_service': {},
                'by_operation': {},
                'by_project': {},
                'by_workflow': {},
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None
            }
        
        total_cost = sum(e.cost_usd for e in filtered_entries)
        
        # Group by service
        by_service = {}
        for entry in filtered_entries:
            service = entry.service_type.value
            if service not in by_service:
                by_service[service] = {'cost_usd': 0.0, 'count': 0}
            by_service[service]['cost_usd'] += entry.cost_usd
            by_service[service]['count'] += 1
        
        # Group by operation
        by_operation = {}
        for entry in filtered_entries:
            op = entry.operation
            if op not in by_operation:
                by_operation[op] = {'cost_usd': 0.0, 'count': 0}
            by_operation[op]['cost_usd'] += entry.cost_usd
            by_operation[op]['count'] += 1
        
        # Group by project
        by_project = {}
        for entry in filtered_entries:
            proj = entry.project_id or 'unassigned'
            if proj not in by_project:
                by_project[proj] = {'cost_usd': 0.0, 'count': 0}
            by_project[proj]['cost_usd'] += entry.cost_usd
            by_project[proj]['count'] += 1
        
        # Group by workflow
        by_workflow = {}
        for entry in filtered_entries:
            wf = entry.workflow_id or 'unassigned'
            if wf not in by_workflow:
                by_workflow[wf] = {'cost_usd': 0.0, 'count': 0}
            by_workflow[wf]['cost_usd'] += entry.cost_usd
            by_workflow[wf]['count'] += 1
        
        return {
            'total_cost_usd': total_cost,
            'entry_count': len(filtered_entries),
            'average_cost_per_entry': total_cost / len(filtered_entries),
            'by_service': by_service,
            'by_operation': by_operation,
            'by_project': by_project,
            'by_workflow': by_workflow,
            'period_start': start_date.isoformat() if start_date else None,
            'period_end': end_date.isoformat() if end_date else None
        }
    
    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations.
        
        Validates Requirement 27.2: Provide cost optimization recommendations such as
        batch processing opportunities, alternative model selections, or caching strategies.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        if len(self.cost_entries) < 10:
            return recommendations
        
        # Analyze recent usage (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_entries = self._filter_entries(start_date=week_ago)
        
        if not recent_entries:
            return recommendations
        
        # Recommendation 1: Model selection optimization
        bedrock_entries = [e for e in recent_entries if e.service_type == ServiceType.BEDROCK]
        if bedrock_entries:
            recommendations.extend(self._recommend_model_optimization(bedrock_entries))
        
        # Recommendation 2: Batch processing
        if len(bedrock_entries) > 50:
            recommendations.extend(self._recommend_batch_processing(bedrock_entries))
        
        # Recommendation 3: Caching opportunities
        recommendations.extend(self._recommend_caching(bedrock_entries))
        
        # Recommendation 4: Resource sizing for ECS
        ecs_entries = [e for e in recent_entries if e.service_type == ServiceType.ECS]
        if ecs_entries:
            recommendations.extend(self._recommend_resource_sizing(ecs_entries))
        
        return sorted(recommendations, key=lambda r: r.priority)
    
    def _recommend_model_optimization(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Recommend cheaper model alternatives."""
        recommendations = []
        
        # Group by model
        model_costs = {}
        for entry in entries:
            model_id = entry.details.get('model_id')
            if model_id:
                if model_id not in model_costs:
                    model_costs[model_id] = 0.0
                model_costs[model_id] += entry.cost_usd
        
        cheapest_model = self.bedrock_calculator.get_cheapest_model()
        
        for model_id, cost in model_costs.items():
            if cost > 0.50 and model_id != cheapest_model:  # $0.50+ threshold
                # Calculate potential savings
                current_pricing = self.bedrock_calculator.MODEL_PRICING.get(model_id)
                cheapest_pricing = self.bedrock_calculator.MODEL_PRICING.get(cheapest_model)
                
                if current_pricing and cheapest_pricing:
                    current_avg = (current_pricing['input_per_1k'] + current_pricing['output_per_1k']) / 2
                    cheapest_avg = (cheapest_pricing['input_per_1k'] + cheapest_pricing['output_per_1k']) / 2
                    
                    savings_percent = ((current_avg - cheapest_avg) / current_avg) * 100
                    potential_savings = cost * (savings_percent / 100)
                    
                    if savings_percent > 10:
                        recommendations.append(OptimizationRecommendation(
                            type=OptimizationType.MODEL_SELECTION,
                            title=f"Switch from {model_id} to {cheapest_model}",
                            description=f"Consider using {cheapest_model} for cost savings. "
                                       f"Could reduce costs by {savings_percent:.1f}%.",
                            potential_savings_usd=potential_savings,
                            potential_savings_percent=savings_percent,
                            priority=2 if savings_percent > 30 else 3,
                            implementation_effort="medium"
                        ))
        
        return recommendations
    
    def _recommend_batch_processing(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Recommend batch processing for small operations."""
        recommendations = []
        
        # Count small operations (< 200 tokens)
        small_ops = [e for e in entries if e.details.get('total_tokens', 0) < 200]
        
        if len(small_ops) > 50:
            total_small_cost = sum(e.cost_usd for e in small_ops)
            potential_savings = total_small_cost * 0.25  # 25% savings estimate
            
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.BATCH_PROCESSING,
                title="Implement batch processing for small operations",
                description=f"You have {len(small_ops)} small operations that could benefit from "
                           f"batch processing. Batching can reduce overhead and costs by ~25%.",
                potential_savings_usd=potential_savings,
                potential_savings_percent=25.0,
                priority=2,
                implementation_effort="high"
            ))
        
        return recommendations
    
    def _recommend_caching(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Recommend caching for repeated operations."""
        recommendations = []
        
        # Simple pattern detection based on token counts
        token_patterns = {}
        for entry in entries:
            tokens = entry.details.get('total_tokens', 0)
            token_key = (tokens // 50) * 50  # Group by 50s
            if token_key not in token_patterns:
                token_patterns[token_key] = []
            token_patterns[token_key].append(entry)
        
        for token_count, pattern_entries in token_patterns.items():
            if len(pattern_entries) > 20:  # 20+ similar operations
                total_cost = sum(e.cost_usd for e in pattern_entries)
                potential_savings = total_cost * 0.5  # 50% savings for caching
                
                recommendations.append(OptimizationRecommendation(
                    type=OptimizationType.CACHING,
                    title="Implement response caching",
                    description=f"You have {len(pattern_entries)} operations with similar patterns "
                               f"(~{token_count} tokens). Caching could reduce costs by ~50%.",
                    potential_savings_usd=potential_savings,
                    potential_savings_percent=50.0,
                    priority=1,
                    implementation_effort="medium"
                ))
                break  # Only recommend once
        
        return recommendations
    
    def _recommend_resource_sizing(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Recommend ECS resource sizing optimization."""
        recommendations = []
        
        # Analyze resource utilization patterns
        if len(entries) > 10:
            avg_duration = sum(e.details.get('duration_seconds', 0) for e in entries) / len(entries)
            
            # If tasks are consistently short, recommend smaller resources
            if avg_duration < 300:  # Less than 5 minutes
                total_cost = sum(e.cost_usd for e in entries)
                potential_savings = total_cost * 0.20  # 20% savings estimate
                
                recommendations.append(OptimizationRecommendation(
                    type=OptimizationType.RESOURCE_SIZING,
                    title="Optimize ECS task resource allocation",
                    description=f"Your tasks run for an average of {avg_duration:.0f} seconds. "
                               f"Consider reducing vCPU/memory allocation for cost savings.",
                    potential_savings_usd=potential_savings,
                    potential_savings_percent=20.0,
                    priority=3,
                    implementation_effort="low"
                ))
        
        return recommendations
    
    def _filter_entries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        service_type: Optional[ServiceType] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> List[CostEntry]:
        """Filter cost entries by criteria."""
        filtered = self.cost_entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        if service_type:
            filtered = [e for e in filtered if e.service_type == service_type]
        
        if project_id:
            filtered = [e for e in filtered if e.project_id == project_id]
        
        if workflow_id:
            filtered = [e for e in filtered if e.workflow_id == workflow_id]
        
        return filtered
    
    def _save_data(self) -> None:
        """Save cost data to storage."""
        try:
            data_file = self.storage_path / "cost_entries.json"
            with open(data_file, 'w') as f:
                json.dump(
                    [e.to_dict() for e in self.cost_entries],
                    f,
                    indent=2
                )
            logger.debug("Cost data saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cost data: {str(e)}")
    
    def _load_data(self) -> None:
        """Load cost data from storage."""
        try:
            data_file = self.storage_path / "cost_entries.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                self.cost_entries = []
                for entry_data in data:
                    entry = CostEntry(
                        timestamp=datetime.fromisoformat(entry_data['timestamp']),
                        service_type=ServiceType(entry_data['service_type']),
                        operation=entry_data['operation'],
                        cost_usd=entry_data['cost_usd'],
                        details=entry_data.get('details', {}),
                        project_id=entry_data.get('project_id'),
                        workflow_id=entry_data.get('workflow_id')
                    )
                    self.cost_entries.append(entry)
                
                logger.debug(f"Loaded {len(self.cost_entries)} cost entries")
        except Exception as e:
            logger.error(f"Failed to load cost data: {str(e)}")
    
    def export_cost_report(
        self,
        filepath: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> None:
        """Export comprehensive cost report.
        
        Args:
            filepath: Output file path
            start_date: Start date for report
            end_date: End date for report
        """
        breakdown = self.get_cost_breakdown(start_date=start_date, end_date=end_date)
        recommendations = [r.to_dict() for r in self.generate_optimization_recommendations()]
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'period_start': start_date.isoformat() if start_date else None,
            'period_end': end_date.isoformat() if end_date else None,
            'cost_breakdown': breakdown,
            'optimization_recommendations': recommendations
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cost report exported to {filepath}")
    
    def close(self) -> None:
        """Close cost tracker and save data."""
        self._save_data()
        logger.info("Cost tracker closed")
