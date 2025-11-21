/**
 * Quality Metrics Panel Component
 * 
 * Fetches and displays quality metrics for synthetic data generation
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import QualityMetricsDisplay from '../results/QualityMetricsDisplay';

interface QualityMetricsPanelProps {
  workflowId: string;
}

interface QualityMetric {
  metric_name: string;
  value: number;
  threshold?: number;
  passed: boolean;
}

const QualityMetricsPanel: React.FC<QualityMetricsPanelProps> = ({ workflowId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [qualityData, setQualityData] = useState<any>(null);

  useEffect(() => {
    fetchQualityMetrics();
  }, [workflowId]);

  const fetchQualityMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch synthetic data agent results
      const response = await fetch(`/api/v1/workflow/${workflowId}/agent/synthetic_data/results`);
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('Synthetic data generation not yet complete');
        } else if (response.status === 500) {
          setError('Server error loading metrics. Please try refreshing.');
        } else {
          setError('Failed to fetch quality metrics');
        }
        return;
      }

      const data = await response.json();
      
      if (data.results && data.results.quality_metrics) {
        // Validate quality metrics structure
        const qm = data.results.quality_metrics;
        if (typeof qm.sdv_quality_score === 'number' && 
            typeof qm.column_shapes_score === 'number' &&
            typeof qm.column_pair_trends_score === 'number' &&
            typeof qm.correlation_preservation === 'number') {
          setQualityData(transformQualityMetrics(data.results));
        } else {
          console.warn('Invalid quality metrics structure:', qm);
          setError('Invalid quality metrics format');
        }
      } else {
        setError('Quality metrics not yet available');
      }
    } catch (err: any) {
      console.error('Error fetching quality metrics:', err);
      setError(err.message || 'Failed to load quality metrics');
    } finally {
      setLoading(false);
    }
  };

  const transformQualityMetrics = (results: any) => {
    const qm = results.quality_metrics;
    
    // Transform to QualityMetricsDisplay format
    const metrics: QualityMetric[] = [
      {
        metric_name: 'Column Shapes',
        value: qm.column_shapes_score,
        threshold: 0.7,
        passed: qm.column_shapes_score >= 0.7,
      },
      {
        metric_name: 'Column Pair Trends',
        value: qm.column_pair_trends_score,
        threshold: 0.7,
        passed: qm.column_pair_trends_score >= 0.7,
      },
      {
        metric_name: 'Data Validity',
        value: qm.data_validity_score || 0,
        threshold: 0.8,
        passed: (qm.data_validity_score || 0) >= 0.8,
      },
      {
        metric_name: 'Data Structure',
        value: qm.data_structure_score || 0,
        threshold: 0.8,
        passed: (qm.data_structure_score || 0) >= 0.8,
      },
    ];

    // Generate warnings based on scores
    const warnings: string[] = [];
    if (qm.sdv_quality_score < 0.7) {
      warnings.push('Overall quality score is below recommended threshold (70%)');
    }
    if (qm.column_shapes_score < 0.7) {
      warnings.push('Column shape distributions differ significantly from source data');
    }
    if (qm.column_pair_trends_score < 0.7) {
      warnings.push('Column pair correlations are not well preserved');
    }
    if (qm.correlation_preservation < 0.8) {
      warnings.push('Overall correlation structure differs from source data');
    }
    if (qm.column_order_preserved === false) {
      warnings.push('Column order does not match original data');
    }
    if (qm.data_validity_score && qm.data_validity_score < 0.8) {
      warnings.push('Data validity issues detected - some values may be invalid or out of range');
    }
    if (qm.data_structure_score && qm.data_structure_score < 0.8) {
      warnings.push('Data structure differs from original - check data types and formats');
    }
    
    // Check privacy metrics
    if (qm.nearest_neighbor_distances) {
      const avgDistance = Object.values(qm.nearest_neighbor_distances).reduce((a: any, b: any) => a + b, 0) / Object.keys(qm.nearest_neighbor_distances).length;
      if (avgDistance < 0.05) {
        warnings.push('Privacy concern: Synthetic data may be too similar to original records');
      }
    }

    // Generate recommendations
    const recommendations: string[] = [];
    if (qm.sdv_quality_score < 0.9) {
      recommendations.push('Consider increasing the number of training epochs for better quality');
    }
    if (results.generation_method?.bedrock_enabled === false && results.field_generation?.bedrock_fields?.length > 0) {
      recommendations.push('Enable Bedrock for improved quality on sensitive text fields');
    }
    if (qm.correlation_preservation < 0.9) {
      recommendations.push('Review field relationships to ensure important correlations are preserved');
    }

    return {
      overallScore: qm.sdv_quality_score,
      metrics,
      correlationPreservation: qm.correlation_preservation,
      columnOrderPreserved: qm.column_order_preserved !== false,
      columnOrderReport: qm.column_order_report,
      privacyMetrics: qm.nearest_neighbor_distances,
      diagnosticDetails: qm.diagnostic_details,
      warnings: warnings.length > 0 ? warnings : undefined,
      recommendations: recommendations.length > 0 ? recommendations : undefined,
      generationInfo: {
        totalRecords: results.total_records_generated,
        bedrockEnabled: results.generation_method?.bedrock_enabled,
        bedrockFields: results.field_generation?.bedrock_fields || [],
        sdvFields: results.field_generation?.sdv_fields || [],
      },
    };
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!qualityData) {
    return null;
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Synthetic Data Quality Metrics
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Generated {qualityData.generationInfo.totalRecords} records using{' '}
          {qualityData.generationInfo.bedrockEnabled ? 'Bedrock + SDV' : 'SDV only'}
        </Typography>
        
        <QualityMetricsDisplay
          overallScore={qualityData.overallScore}
          metrics={qualityData.metrics}
          correlationPreservation={qualityData.correlationPreservation}
          warnings={qualityData.warnings}
          recommendations={qualityData.recommendations}
        />

        {/* Column Order Status */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Column Order Preservation
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
            Verifies that synthetic data columns appear in the same order as the original dataset
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography 
              variant="body2" 
              sx={{ 
                color: qualityData.columnOrderPreserved ? 'success.main' : 'error.main',
                fontWeight: 'medium'
              }}
            >
              {qualityData.columnOrderPreserved ? '✓ Preserved' : '✗ Not Preserved'}
            </Typography>
            {!qualityData.columnOrderPreserved && qualityData.columnOrderReport && (
              <Typography variant="caption" color="text.secondary">
                ({qualityData.columnOrderReport.mismatches?.length || 0} mismatches)
              </Typography>
            )}
          </Box>
        </Box>

        {/* Privacy Metrics */}
        {qualityData.privacyMetrics && Object.keys(qualityData.privacyMetrics).length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Privacy & Data Leakage Analysis
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Measures how different synthetic records are from original data using nearest neighbor distances. 
              Higher values indicate better privacy protection (synthetic data is less similar to real records).
              Values below 0.05 may indicate potential data leakage.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {Object.entries(qualityData.privacyMetrics).map(([metric, value]: [string, any]) => (
                <Box key={metric}>
                  <Typography variant="caption" color="text.secondary">
                    {metric}:
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: value > 0.1 ? 'success.main' : value > 0.05 ? 'warning.main' : 'error.main',
                      fontWeight: 'medium'
                    }}
                  >
                    {typeof value === 'number' ? value.toFixed(4) : value}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {/* Diagnostic Details */}
        {qualityData.diagnosticDetails && Object.keys(qualityData.diagnosticDetails).length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Diagnostic Details
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
              Additional diagnostic information about data quality, including validity checks and structural analysis
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {Object.entries(qualityData.diagnosticDetails).map(([key, value]: [string, any]) => (
                <Box key={key}>
                  <Typography variant="caption" color="text.secondary">
                    {key.replace(/_/g, ' ')}:
                  </Typography>
                  <Typography variant="body2">
                    {typeof value === 'number' ? value.toFixed(3) : JSON.stringify(value)}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {/* Field Generation Breakdown */}
        {qualityData.generationInfo.bedrockEnabled && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Generation Method by Field
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {qualityData.generationInfo.bedrockFields.length > 0 && (
                <Box>
                  <Typography variant="caption" color="primary">
                    Bedrock ({qualityData.generationInfo.bedrockFields.length} fields):
                  </Typography>
                  <Typography variant="body2">
                    {qualityData.generationInfo.bedrockFields.join(', ')}
                  </Typography>
                </Box>
              )}
              {qualityData.generationInfo.sdvFields.length > 0 && (
                <Box>
                  <Typography variant="caption" color="secondary">
                    SDV ({qualityData.generationInfo.sdvFields.length} fields):
                  </Typography>
                  <Typography variant="body2">
                    {qualityData.generationInfo.sdvFields.join(', ')}
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default QualityMetricsPanel;
