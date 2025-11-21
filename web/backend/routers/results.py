"""Results API endpoints.

Provides endpoints for:
- Quality reports
- Test results
- Data export
- Preview samples

Validates Requirements 11.4, 11.5
"""

import logging
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Workflow storage directory
WORKFLOW_STORAGE_DIR = Path("data/workflows")


def read_workflow_state(workflow_id: str) -> dict:
    """Read workflow state from file.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Workflow state dictionary
        
    Raises:
        HTTPException: If file not found or cannot be parsed
    """
    workflow_file = WORKFLOW_STORAGE_DIR / f"{workflow_id}.json"
    
    if not workflow_file.exists():
        logger.error(f"Workflow file not found: {workflow_file}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    try:
        with open(workflow_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse workflow file {workflow_file}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow state file is corrupted: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading workflow file {workflow_file}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read workflow state: {str(e)}"
        )


class QualityMetric(BaseModel):
    """Quality metric model."""
    metric_name: str
    value: float
    threshold: Optional[float] = None
    passed: bool


class QualityReport(BaseModel):
    """Quality report model."""
    workflow_id: str
    generated_at: str
    overall_score: float
    metrics: List[QualityMetric]
    statistical_tests: dict
    distribution_comparison: dict
    visualizations: Optional[dict] = None
    warnings: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class DataSample(BaseModel):
    """Data sample model."""
    record_id: int
    data: dict
    is_edge_case: bool = False
    edge_case_type: Optional[str] = None


class ExportRequest(BaseModel):
    """Data export request."""
    format: str  # 'csv', 'json', 'parquet', 'sql'
    include_metadata: bool = False


@router.get("/{workflow_id}/quality", response_model=QualityReport)
async def get_quality_report(workflow_id: str):
    """Get quality report for a workflow.
    
    Validates Requirement 11.5: Visual representations of data distributions
    and statistical comparisons.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Quality report
    """
    try:
        # Read workflow state from file
        workflow_state = read_workflow_state(workflow_id)
        
        # Extract quality metrics from synthetic_data_results
        synthetic_results = workflow_state.get('synthetic_data_results', {})
        quality_metrics = synthetic_results.get('quality_metrics', {})
        
        if not quality_metrics:
            logger.warning(f"No quality metrics found for workflow {workflow_id}, returning mock data")
            # Return mock data with warning
            return QualityReport(
                workflow_id=workflow_id,
                generated_at=datetime.now().isoformat(),
                overall_score=0.0,
                metrics=[],
                statistical_tests={},
                distribution_comparison={},
                warnings=["Quality metrics not available for this workflow"],
                recommendations=["Complete the workflow to generate quality metrics"]
            )
        
        # Extract overall score
        overall_score = quality_metrics.get('sdv_quality_score', 0.0)
        
        # Build metrics list
        metrics = []
        
        # Add SDV quality score
        if 'sdv_quality_score' in quality_metrics:
            metrics.append(QualityMetric(
                metric_name="SDV Quality Score",
                value=quality_metrics['sdv_quality_score'],
                threshold=0.80,
                passed=quality_metrics['sdv_quality_score'] >= 0.80
            ))
        
        # Add correlation preservation
        if 'correlation_preservation' in quality_metrics:
            metrics.append(QualityMetric(
                metric_name="Correlation Preservation",
                value=quality_metrics['correlation_preservation'],
                threshold=0.85,
                passed=quality_metrics['correlation_preservation'] >= 0.85
            ))
        
        # Add edge case frequency match
        if 'edge_case_frequency_match' in quality_metrics:
            metrics.append(QualityMetric(
                metric_name="Edge Case Frequency Match",
                value=quality_metrics['edge_case_frequency_match'],
                threshold=0.90,
                passed=quality_metrics['edge_case_frequency_match'] >= 0.90
            ))
        
        # Add column shapes score
        if 'column_shapes_score' in quality_metrics:
            metrics.append(QualityMetric(
                metric_name="Column Shapes",
                value=quality_metrics['column_shapes_score'],
                threshold=0.80,
                passed=quality_metrics['column_shapes_score'] >= 0.80
            ))
        
        # Add column pair trends score
        if 'column_pair_trends_score' in quality_metrics:
            metrics.append(QualityMetric(
                metric_name="Column Pair Trends",
                value=quality_metrics['column_pair_trends_score'],
                threshold=0.80,
                passed=quality_metrics['column_pair_trends_score'] >= 0.80
            ))
        
        # Build statistical tests
        statistical_tests = {}
        ks_tests = quality_metrics.get('ks_tests', {})
        if ks_tests:
            # Aggregate KS test results
            passed_count = sum(1 for test in ks_tests.values() if test.get('pvalue', 0) > 0.05)
            total_count = len(ks_tests)
            statistical_tests['ks_test'] = {
                "passed_fields": passed_count,
                "total_fields": total_count,
                "pass_rate": passed_count / total_count if total_count > 0 else 0,
                "passed": passed_count / total_count >= 0.80 if total_count > 0 else False
            }
        
        # Build distribution comparison
        distribution_comparison = {
            "correlation_preservation": quality_metrics.get('correlation_preservation', 0.0),
            "edge_case_match": quality_metrics.get('edge_case_frequency_match', 0.0)
        }
        
        # Generate warnings
        warnings = []
        if overall_score < 0.80:
            warnings.append(f"Overall quality score ({overall_score:.2f}) is below recommended threshold of 0.80")
        if quality_metrics.get('correlation_preservation', 1.0) < 0.85:
            warnings.append("Correlation preservation is below recommended threshold")
        
        # Generate recommendations
        recommendations = []
        if overall_score >= 0.80:
            recommendations.append("Quality metrics look good! Synthetic data is ready for use.")
        else:
            recommendations.append("Consider adjusting generation parameters to improve quality.")
        
        logger.info(f"Returning quality report for workflow {workflow_id} with score {overall_score}")
        
        return QualityReport(
            workflow_id=workflow_id,
            generated_at=quality_metrics.get('generated_at', datetime.now().isoformat()),
            overall_score=overall_score,
            metrics=metrics,
            statistical_tests=statistical_tests,
            distribution_comparison=distribution_comparison,
            visualizations={},
            warnings=warnings if warnings else None,
            recommendations=recommendations if recommendations else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality report for workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality report: {str(e)}"
        )


@router.get("/{workflow_id}/samples", response_model=List[DataSample])
async def get_data_samples(
    workflow_id: str,
    limit: int = 10,
    include_edge_cases: bool = True
):
    """Get preview samples of generated data.
    
    Validates Requirement 11.4: Display preview samples of generated data.
    
    Args:
        workflow_id: Workflow ID
        limit: Number of samples to return
        include_edge_cases: Whether to include edge cases
    
    Returns:
        List of data samples
    """
    try:
        # Read workflow state from file
        workflow_state = read_workflow_state(workflow_id)
        
        # Extract sample data from synthetic_data_results
        synthetic_results = workflow_state.get('synthetic_data_results', {})
        sample_data = synthetic_results.get('sample_data', [])
        
        if not sample_data:
            logger.warning(f"No sample data found for workflow {workflow_id}")
            return []
        
        # Transform to DataSample format
        samples = []
        edge_case_indices = set()
        
        # Get edge case information if available
        generation_metadata = synthetic_results.get('generation_metadata', {})
        edge_case_result = generation_metadata.get('edge_case_injection_result', {})
        if edge_case_result:
            edge_case_indices = set(edge_case_result.get('injected_indices', []))
        
        for idx, record in enumerate(sample_data[:limit]):
            is_edge = idx in edge_case_indices
            
            # Skip edge cases if not requested
            if not include_edge_cases and is_edge:
                continue
            
            samples.append(DataSample(
                record_id=idx,
                data=record,
                is_edge_case=is_edge,
                edge_case_type="injected" if is_edge else None
            ))
        
        logger.info(f"Returning {len(samples)} samples for workflow {workflow_id}")
        return samples
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting samples for workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get samples: {str(e)}"
        )


@router.post("/{workflow_id}/export")
async def export_data(workflow_id: str, request: ExportRequest):
    """Export generated data in specified format.
    
    Validates Requirement 11.4: Provide download options for complete datasets
    in multiple formats.
    
    Args:
        workflow_id: Workflow ID
        request: Export request
    
    Returns:
        File download response
    """
    try:
        # TODO: Implement actual export logic
        # For now, return a mock response
        
        filename = f"{workflow_id}_data.{request.format}"
        
        # In production, this would generate the actual file
        return {
            "download_url": f"/api/v1/results/{workflow_id}/download/{filename}",
            "filename": filename,
            "format": request.format,
            "size_bytes": 1024000,
            "expires_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export data: {str(e)}"
        )


@router.get("/{workflow_id}/test-results")
async def get_test_results(workflow_id: str):
    """Get test execution results for a workflow.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Test results
    """
    # Mock data for now
    return {
        "workflow_id": workflow_id,
        "total_tests": 25,
        "passed": 23,
        "failed": 2,
        "skipped": 0,
        "execution_time_seconds": 45.2,
        "test_cases": [
            {
                "test_id": "test_001",
                "name": "Validate email format",
                "status": "passed",
                "duration_seconds": 1.2
            },
            {
                "test_id": "test_002",
                "name": "Check data distribution",
                "status": "failed",
                "duration_seconds": 2.5,
                "error": "Distribution mismatch detected"
            }
        ]
    }
