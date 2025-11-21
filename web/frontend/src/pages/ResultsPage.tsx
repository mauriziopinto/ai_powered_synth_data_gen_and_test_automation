/**
 * Results Dashboard Page
 * 
 * Comprehensive results dashboard displaying quality metrics, test results,
 * visualizations, and cost tracking with real-time updates.
 * 
 * Validates Requirements 11.4, 11.5, 27.3, 27.4
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Button,
  Grid,
  Paper
} from '@mui/material';
import {
  Assessment as MetricsIcon,
  BarChart as ChartsIcon,
  PlaylistAddCheck as TestsIcon,
  AttachMoney as CostIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import {
  QualityMetricsDisplay,
  InteractiveCharts,
  TestResultsTable,
  CostTracker
} from '../components/results';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`results-tabpanel-${index}`}
      aria-labelledby={`results-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ResultsPage() {
  const [selectedTab, setSelectedTab] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workflowId] = useState<string>('demo-workflow-001');
  
  // Quality data
  const [qualityData, setQualityData] = useState<any>(null);
  
  // Test results data
  const [testResults, setTestResults] = useState<any>(null);
  
  // Cost data
  const [currentCost, setCurrentCost] = useState<number>(0);

  useEffect(() => {
    fetchResultsData();
  }, [workflowId]);

  const fetchResultsData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch quality report
      const qualityResponse = await fetch(`/api/v1/results/${workflowId}/quality`);
      if (!qualityResponse.ok) throw new Error('Failed to fetch quality report');
      const qualityData = await qualityResponse.json();
      setQualityData(qualityData);
      
      // Fetch test results
      const testResponse = await fetch(`/api/v1/results/${workflowId}/test-results`);
      if (!testResponse.ok) throw new Error('Failed to fetch test results');
      const testData = await testResponse.json();
      setTestResults(testData);
      
      // Fetch workflow status for cost
      const statusResponse = await fetch(`/api/v1/workflow/${workflowId}/status`);
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setCurrentCost(statusData.cost_usd || 0);
      }
      
    } catch (err) {
      console.error('Error fetching results:', err);
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleExportResults = async () => {
    try {
      const response = await fetch(`/api/v1/results/${workflowId}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format: 'json', include_metadata: true })
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      const data = await response.json();
      window.open(data.download_url, '_blank');
    } catch (err) {
      console.error('Error exporting results:', err);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchResultsData} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Results Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Workflow ID: {workflowId}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchResultsData}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleExportResults}
          >
            Export Results
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'primary.light' }}>
            <Typography variant="h4" color="primary.dark">
              {qualityData?.overall_score ? (qualityData.overall_score * 100).toFixed(1) : '0'}%
            </Typography>
            <Typography variant="body2" color="primary.dark">
              Quality Score
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'success.light' }}>
            <Typography variant="h4" color="success.dark">
              {testResults?.passed || 0}/{testResults?.total_tests || 0}
            </Typography>
            <Typography variant="body2" color="success.dark">
              Tests Passed
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'warning.light' }}>
            <Typography variant="h4" color="warning.dark">
              ${currentCost.toFixed(4)}
            </Typography>
            <Typography variant="body2" color="warning.dark">
              Total Cost
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'info.light' }}>
            <Typography variant="h4" color="info.dark">
              {qualityData?.metrics?.length || 0}
            </Typography>
            <Typography variant="body2" color="info.dark">
              Metrics Tracked
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<MetricsIcon />} label="Quality Metrics" iconPosition="start" />
          <Tab icon={<ChartsIcon />} label="Visualizations" iconPosition="start" />
          <Tab icon={<TestsIcon />} label="Test Results" iconPosition="start" />
          <Tab icon={<CostIcon />} label="Cost Analysis" iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={selectedTab} index={0}>
        {qualityData ? (
          <QualityMetricsDisplay
            overallScore={qualityData.overall_score}
            metrics={qualityData.metrics}
            statisticalTests={qualityData.statistical_tests}
            correlationPreservation={qualityData.distribution_comparison?.correlation_preservation}
            edgeCaseMatch={qualityData.distribution_comparison?.edge_case_match}
            warnings={qualityData.warnings}
            recommendations={qualityData.recommendations}
          />
        ) : (
          <Alert severity="info">No quality data available</Alert>
        )}
      </TabPanel>

      <TabPanel value={selectedTab} index={1}>
        {qualityData?.visualizations ? (
          <InteractiveCharts
            charts={qualityData.visualizations}
            workflowId={workflowId}
          />
        ) : (
          <Alert severity="info">
            Visualizations will be generated once quality analysis is complete
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={selectedTab} index={2}>
        {testResults ? (
          <TestResultsTable results={testResults} />
        ) : (
          <Alert severity="info">No test results available</Alert>
        )}
      </TabPanel>

      <TabPanel value={selectedTab} index={3}>
        <CostTracker workflowId={workflowId} initialCost={currentCost} />
      </TabPanel>
    </Box>
  );
}
