/**
 * Quality Metrics Display Component
 * 
 * Displays quality metrics including SDV scores, statistical tests,
 * and correlation preservation metrics.
 * 
 * Validates Requirements 11.4, 11.5
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Alert
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface QualityMetric {
  metric_name: string;
  value: number;
  threshold?: number;
  passed: boolean;
}

interface QualityMetricsDisplayProps {
  overallScore: number;
  metrics: QualityMetric[];
  statisticalTests?: Record<string, any>;
  correlationPreservation?: number;
  edgeCaseMatch?: number;
  warnings?: string[];
  recommendations?: string[];
}

const QualityMetricsDisplay: React.FC<QualityMetricsDisplayProps> = ({
  overallScore,
  metrics,
  statisticalTests = {},
  correlationPreservation,
  edgeCaseMatch,
  warnings = [],
  recommendations = []
}) => {
  const getMetricDescription = (metricName: string): string => {
    const descriptions: Record<string, string> = {
      'Column Shapes': 'Measures how well the distribution of values in each column matches the original data',
      'Column Pair Trends': 'Evaluates whether relationships between pairs of columns are preserved',
      'Data Validity': 'Checks if synthetic values are valid (no nulls where unexpected, values within expected ranges)',
      'Data Structure': 'Verifies that data types, formats, and structural properties match the original dataset',
      'Correlation Preservation': 'Measures how well the overall correlation structure between all columns is maintained',
      'Edge Case Frequency Match': 'Compares the frequency of edge cases (nulls, outliers) between synthetic and original data'
    };
    return descriptions[metricName] || '';
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.9) return 'success.main';
    if (score >= 0.7) return 'warning.main';
    return 'error.main';
  };

  const getScoreIcon = (passed: boolean) => {
    return passed ? (
      <CheckIcon color="success" fontSize="small" />
    ) : (
      <ErrorIcon color="error" fontSize="small" />
    );
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <Box>
      {/* Overall Score Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Overall Quality Score
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              <LinearProgress
                variant="determinate"
                value={overallScore * 100}
                sx={{
                  height: 12,
                  borderRadius: 6,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getScoreColor(overallScore),
                    borderRadius: 6
                  }
                }}
              />
            </Box>
            <Typography
              variant="h4"
              sx={{ color: getScoreColor(overallScore), minWidth: 80 }}
            >
              {formatPercentage(overallScore)}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {overallScore >= 0.9
              ? 'Excellent quality - synthetic data closely matches production data'
              : overallScore >= 0.7
              ? 'Good quality - minor differences detected'
              : 'Quality issues detected - review metrics below'}
          </Typography>
        </CardContent>
      </Card>

      {/* Individual Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {metrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    {metric.metric_name}
                  </Typography>
                  {getScoreIcon(metric.passed)}
                </Box>
                {getMetricDescription(metric.metric_name) && (
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1, minHeight: 32 }}>
                    {getMetricDescription(metric.metric_name)}
                  </Typography>
                )}
                <Typography variant="h5" sx={{ mb: 1 }}>
                  {formatPercentage(metric.value)}
                </Typography>
                {metric.threshold !== undefined && (
                  <Typography variant="caption" color="text.secondary">
                    Threshold: {formatPercentage(metric.threshold)}
                  </Typography>
                )}
                <LinearProgress
                  variant="determinate"
                  value={metric.value * 100}
                  sx={{
                    mt: 1,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: metric.passed ? 'success.main' : 'error.main',
                      borderRadius: 3
                    }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}

        {/* Correlation Preservation */}
        {correlationPreservation !== undefined && (
          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Correlation Preservation
                  </Typography>
                  {getScoreIcon(correlationPreservation >= 0.8)}
                </Box>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1, minHeight: 32 }}>
                  {getMetricDescription('Correlation Preservation')}
                </Typography>
                <Typography variant="h5" sx={{ mb: 1 }}>
                  {formatPercentage(correlationPreservation)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Threshold: 80%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={correlationPreservation * 100}
                  sx={{
                    mt: 1,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: correlationPreservation >= 0.8 ? 'success.main' : 'error.main',
                      borderRadius: 3
                    }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Edge Case Match */}
        {edgeCaseMatch !== undefined && (
          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Edge Case Frequency Match
                  </Typography>
                  {getScoreIcon(edgeCaseMatch >= 0.9)}
                </Box>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1, minHeight: 32 }}>
                  {getMetricDescription('Edge Case Frequency Match')}
                </Typography>
                <Typography variant="h5" sx={{ mb: 1 }}>
                  {formatPercentage(edgeCaseMatch)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Threshold: 90%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={edgeCaseMatch * 100}
                  sx={{
                    mt: 1,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: edgeCaseMatch >= 0.9 ? 'success.main' : 'error.main',
                      borderRadius: 3
                    }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Statistical Tests Summary */}
      {Object.keys(statisticalTests).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Statistical Tests
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(statisticalTests).map(([testName, testData]: [string, any]) => (
                <Grid item xs={12} sm={6} md={4} key={testName}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      {testName.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    {typeof testData === 'object' && testData !== null ? (
                      <Box sx={{ mt: 1 }}>
                        {testData.statistic !== undefined && (
                          <Typography variant="body2">
                            Statistic: {testData.statistic.toFixed(4)}
                          </Typography>
                        )}
                        {testData.p_value !== undefined && (
                          <Typography variant="body2">
                            P-value: {testData.p_value.toFixed(4)}
                          </Typography>
                        )}
                        {testData.passed !== undefined && (
                          <Chip
                            label={testData.passed ? 'Passed' : 'Failed'}
                            color={testData.passed ? 'success' : 'error'}
                            size="small"
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body2">{String(testData)}</Typography>
                    )}
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Quality Warnings
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            {warnings.map((warning, index) => (
              <li key={index}>
                <Typography variant="body2">{warning}</Typography>
              </li>
            ))}
          </Box>
        </Alert>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Alert severity="info" icon={<InfoIcon />}>
          <Typography variant="subtitle2" gutterBottom>
            Recommendations
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            {recommendations.map((recommendation, index) => (
              <li key={index}>
                <Typography variant="body2">{recommendation}</Typography>
              </li>
            ))}
          </Box>
        </Alert>
      )}
    </Box>
  );
};

export default QualityMetricsDisplay;
