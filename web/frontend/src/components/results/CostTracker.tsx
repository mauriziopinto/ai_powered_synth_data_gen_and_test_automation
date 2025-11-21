/**
 * Cost Tracker Component
 * 
 * Real-time AWS cost tracking with breakdown by service and operation.
 * Displays cost trends and optimization recommendations.
 * 
 * Validates Requirements 27.3, 27.4
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Lightbulb as LightbulbIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import websocketService from '../../services/websocket';

interface CostBreakdown {
  total_cost_usd: number;
  entry_count: number;
  by_service: Record<string, { cost_usd: number; count: number }>;
  by_operation: Record<string, { cost_usd: number; count: number }>;
}

interface OptimizationRecommendation {
  type: string;
  title: string;
  description: string;
  potential_savings_usd: number;
  potential_savings_percent: number;
  priority: number;
  implementation_effort: string;
}

interface CostTrackerProps {
  workflowId: string;
  initialCost?: number;
}

const CostTracker: React.FC<CostTrackerProps> = ({
  workflowId,
  initialCost = 0
}) => {
  const [currentCost, setCurrentCost] = useState(initialCost);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown | null>(null);
  const [recommendations, setRecommendations] = useState<OptimizationRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    // Subscribe to real-time cost updates via WebSocket
    const handleCostUpdate = (data: any) => {
      if (data.workflow_id === workflowId && data.cost_usd !== undefined) {
        setCurrentCost(data.cost_usd);
        setLastUpdate(new Date());
      }
    };

    websocketService.on('cost_update', handleCostUpdate);
    websocketService.on('workflow_status', handleCostUpdate);

    // Fetch initial cost breakdown
    fetchCostBreakdown();

    return () => {
      websocketService.off('cost_update', handleCostUpdate);
      websocketService.off('workflow_status', handleCostUpdate);
    };
  }, [workflowId]);

  const fetchCostBreakdown = async () => {
    setIsLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`/api/v1/cost/${workflowId}/breakdown`);
      // const data = await response.json();
      
      // Mock data for now
      const mockBreakdown: CostBreakdown = {
        total_cost_usd: currentCost,
        entry_count: 45,
        by_service: {
          'bedrock': { cost_usd: currentCost * 0.75, count: 30 },
          'ecs': { cost_usd: currentCost * 0.20, count: 10 },
          's3': { cost_usd: currentCost * 0.05, count: 5 }
        },
        by_operation: {
          'text_generation': { cost_usd: currentCost * 0.60, count: 25 },
          'model_training': { cost_usd: currentCost * 0.15, count: 5 },
          'task_execution': { cost_usd: currentCost * 0.20, count: 10 },
          'storage': { cost_usd: currentCost * 0.05, count: 5 }
        }
      };

      const mockRecommendations: OptimizationRecommendation[] = [
        {
          type: 'model_selection',
          title: 'Switch to more cost-effective model',
          description: 'Consider using Claude Haiku instead of Claude Sonnet for simple text generation tasks.',
          potential_savings_usd: currentCost * 0.30,
          potential_savings_percent: 30,
          priority: 1,
          implementation_effort: 'medium'
        },
        {
          type: 'batch_processing',
          title: 'Implement batch processing',
          description: 'Batch small operations together to reduce API overhead and costs.',
          potential_savings_usd: currentCost * 0.15,
          potential_savings_percent: 15,
          priority: 2,
          implementation_effort: 'high'
        }
      ];

      setCostBreakdown(mockBreakdown);
      setRecommendations(mockRecommendations);
    } catch (error) {
      console.error('Error fetching cost breakdown:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    }).format(amount);
  };

  const getEffortColor = (effort: string): 'success' | 'warning' | 'error' => {
    switch (effort) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getPriorityColor = (priority: number): string => {
    if (priority === 1) return 'error.main';
    if (priority === 2) return 'warning.main';
    return 'info.main';
  };

  return (
    <Box>
      {/* Current Cost Card */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ color: 'white', opacity: 0.9 }}>
                Current Workflow Cost
              </Typography>
              <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold', mt: 1 }}>
                {formatCurrency(currentCost)}
              </Typography>
              <Typography variant="caption" sx={{ color: 'white', opacity: 0.8 }}>
                Last updated: {lastUpdate.toLocaleTimeString()}
              </Typography>
            </Box>
            <Tooltip title="Refresh">
              <IconButton
                onClick={fetchCostBreakdown}
                disabled={isLoading}
                sx={{ color: 'white' }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </CardContent>
      </Card>

      {/* Cost Breakdown */}
      {costBreakdown && (
        <>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {/* By Service */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cost by Service
                  </Typography>
                  {Object.entries(costBreakdown.by_service)
                    .sort(([, a], [, b]) => b.cost_usd - a.cost_usd)
                    .map(([service, data]) => {
                      const percentage = (data.cost_usd / costBreakdown.total_cost_usd) * 100;
                      return (
                        <Box key={service} sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="body2" sx={{ textTransform: 'uppercase' }}>
                              {service}
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {formatCurrency(data.cost_usd)}
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={percentage}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              backgroundColor: 'grey.200',
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 4
                              }
                            }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {percentage.toFixed(1)}% ({data.count} operations)
                          </Typography>
                        </Box>
                      );
                    })}
                </CardContent>
              </Card>
            </Grid>

            {/* By Operation */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cost by Operation
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Operation</TableCell>
                          <TableCell align="right">Cost</TableCell>
                          <TableCell align="right">Count</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(costBreakdown.by_operation)
                          .sort(([, a], [, b]) => b.cost_usd - a.cost_usd)
                          .map(([operation, data]) => (
                            <TableRow key={operation}>
                              <TableCell>
                                <Typography variant="body2">
                                  {operation.replace(/_/g, ' ')}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" fontWeight="bold">
                                  {formatCurrency(data.cost_usd)}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Chip label={data.count} size="small" />
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Optimization Recommendations */}
          {recommendations.length > 0 && (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <LightbulbIcon color="warning" />
                  <Typography variant="h6">
                    Cost Optimization Recommendations
                  </Typography>
                </Box>

                {recommendations
                  .sort((a, b) => a.priority - b.priority)
                  .map((rec, index) => (
                    <Accordion key={index}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                          <Box
                            sx={{
                              width: 8,
                              height: 40,
                              backgroundColor: getPriorityColor(rec.priority),
                              borderRadius: 1
                            }}
                          />
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="subtitle1">
                              {rec.title}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                              <Chip
                                label={`Priority ${rec.priority}`}
                                size="small"
                                sx={{ backgroundColor: getPriorityColor(rec.priority), color: 'white' }}
                              />
                              <Chip
                                label={`${rec.implementation_effort} effort`}
                                size="small"
                                color={getEffortColor(rec.implementation_effort)}
                              />
                            </Box>
                          </Box>
                          <Box sx={{ textAlign: 'right' }}>
                            <Typography variant="h6" color="success.main">
                              {formatCurrency(rec.potential_savings_usd)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {rec.potential_savings_percent}% savings
                            </Typography>
                          </Box>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Alert severity="info" icon={<LightbulbIcon />}>
                          {rec.description}
                        </Alert>
                      </AccordionDetails>
                    </Accordion>
                  ))}

                <Box sx={{ mt: 2, p: 2, backgroundColor: 'success.light', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="success.dark" gutterBottom>
                    Total Potential Savings
                  </Typography>
                  <Typography variant="h5" color="success.dark">
                    {formatCurrency(recommendations.reduce((sum, rec) => sum + rec.potential_savings_usd, 0))}
                  </Typography>
                  <Typography variant="caption" color="success.dark">
                    Up to {recommendations.reduce((sum, rec) => sum + rec.potential_savings_percent, 0).toFixed(0)}% cost reduction
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <LinearProgress sx={{ width: '100%' }} />
        </Box>
      )}
    </Box>
  );
};

export default CostTracker;
