/**
 * Workflow Visualization Page
 * 
 * Main page for visualizing workflow execution with real-time updates
 * Validates Requirements 20.1, 20.2, 20.3, 20.4, 20.5, 25.1, 25.2, 25.3, 25.4, 25.5
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  IconButton,
  Alert,
  CircularProgress,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';

import WorkflowCanvas from '../components/visualization/WorkflowCanvas';
import AgentDetailPanel from '../components/visualization/AgentDetailPanel';
import DataTransformationViewer from '../components/visualization/DataTransformationViewer';
import AgentDataTable from '../components/visualization/AgentDataTable';
import QualityMetricsPanel from '../components/workflow/QualityMetricsPanel';
import AgentLogViewer from '../components/workflow/AgentLogViewer';
import { workflowAPI, monitoringAPI } from '../services/api';
import websocketService from '../services/websocket';
import { AgentLogEntry } from '../types';

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
}

interface AgentDetail {
  agent_id: string;
  agent_type: string;
  status: string;
  current_operation?: string;
  progress: number;
  message?: string;
  logs?: any[];
  decisions?: any[];
  data_samples?: any[];
  metrics?: Record<string, any>;
}

interface TransformationData {
  before: any[];
  after: any[];
  changedFields: string[];
  transformationType: string;
  description?: string;
}

export default function WorkflowPage() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<any>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [agentDetails, setAgentDetails] = useState<Record<string, AgentDetail>>({});
  const [transformations, setTransformations] = useState<TransformationData[]>([]);
  const [agentLogs, setAgentLogs] = useState<AgentLogEntry[]>([]);

  // Auto-navigate to strategy selection when workflow reaches that state
  useEffect(() => {
    if (workflowStatus?.status === 'awaiting_strategy_selection') {
      navigate(`/workflow/${workflowId}/strategy-selection`);
    }
  }, [workflowStatus?.status, workflowId, navigate]);

  // Initialize workflow data
  useEffect(() => {
    if (!workflowId) {
      setError('No workflow ID provided');
      setLoading(false);
      return;
    }

    loadWorkflowData();
    connectWebSocket();

    return () => {
      websocketService.disconnect();
    };
  }, [workflowId]);

  // Polling mechanism for real-time updates (fallback if WebSocket fails)
  useEffect(() => {
    if (!workflowId || !workflowStatus) return;

    // Only poll if workflow is running or paused
    if (!['running', 'paused'].includes(workflowStatus.status)) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        await loadWorkflowData(false); // Don't show loading spinner during polling
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [workflowId, workflowStatus?.status]);

  const loadWorkflowData = async (isInitialLoad: boolean = true) => {
    try {
      // Only show loading spinner on initial load, not during polling
      if (isInitialLoad) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);

      // Load workflow status
      const statusResponse = await workflowAPI.getStatus(workflowId!);
      setWorkflowStatus(statusResponse.data);

      // Load agent information
      const agentsResponse = await monitoringAPI.getAgents(workflowId!);
      const agentData = Array.isArray(agentsResponse.data) ? agentsResponse.data : (agentsResponse.data.agents || []);
      
      // Transform agent data for canvas
      const canvasAgents: Agent[] = agentData.map((agent: any) => ({
        id: agent.agent_id,
        name: agent.agent_type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        status: agent.status,
        progress: agent.progress || 0,
      }));
      
      // Check if distribution was completed
      const completedDistributions = JSON.parse(localStorage.getItem('completed_distributions') || '[]');
      const isDistributionComplete = statusResponse.data.stages_completed?.includes('distribution') || 
                                     completedDistributions.includes(workflowId);
      
      // Check if distribution agent already exists (from backend)
      const hasDistributionAgent = canvasAgents.some(a => a.id === 'distribution' || a.name === 'Distribution');
      
      // Insert distribution agent in correct position only if it doesn't exist and distribution is complete
      if (isDistributionComplete && !hasDistributionAgent) {
        // Find the index of synthetic_data agent
        const syntheticDataIndex = canvasAgents.findIndex(a => a.id === 'synthetic_data');
        
        // Insert distribution agent after synthetic_data
        const insertIndex = syntheticDataIndex >= 0 ? syntheticDataIndex + 1 : canvasAgents.length;
        canvasAgents.splice(insertIndex, 0, {
          id: 'distribution',
          name: 'Distribution',
          status: 'completed',
          progress: 100,
        });
        
        // Update workflow status to include distribution in stages_completed
        if (!statusResponse.data.stages_completed) {
          statusResponse.data.stages_completed = [];
        }
        if (!statusResponse.data.stages_completed.includes('distribution')) {
          statusResponse.data.stages_completed.push('distribution');
        }
      } else if (isDistributionComplete && hasDistributionAgent) {
        // Update existing distribution agent status to completed
        const distAgent = canvasAgents.find(a => a.id === 'distribution' || a.name === 'Distribution');
        if (distAgent) {
          distAgent.status = 'completed';
          distAgent.progress = 100;
        }
      }
      
      setAgents(canvasAgents);

      // Store detailed agent information
      const detailsMap: Record<string, AgentDetail> = {};
      agentData.forEach((agent: any) => {
        detailsMap[agent.agent_id] = agent;
      });
      setAgentDetails(detailsMap);

      // Load persisted agent logs if available
      if (statusResponse.data.agent_logs && Array.isArray(statusResponse.data.agent_logs)) {
        setAgentLogs(statusResponse.data.agent_logs);
      }

      if (isInitialLoad) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    } catch (err: any) {
      console.error('Error loading workflow data:', err);
      setError(err.response?.data?.detail || 'Failed to load workflow data');
      if (isInitialLoad) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    }
  };



  const connectWebSocket = async () => {
    try {
      await websocketService.connect();

      // Subscribe to workflow updates
      websocketService.send({
        type: 'subscribe',
        workflow_id: workflowId,
      });

      // Handle workflow status updates
      websocketService.on('workflow_status', (data) => {
        if (data.workflow_id === workflowId) {
          setWorkflowStatus(data.status);
        }
      });

      // Handle agent updates
      websocketService.on('agent_update', (data) => {
        if (data.workflow_id === workflowId) {
          const agent = data.agent;
          
          // Update canvas agents
          setAgents(prev => prev.map(a => 
            a.id === agent.agent_id
              ? { ...a, status: agent.status, progress: agent.progress || 0 }
              : a
          ));

          // Update agent details
          setAgentDetails(prev => ({
            ...prev,
            [agent.agent_id]: agent,
          }));
        }
      });

      // Handle data transformation updates
      websocketService.on('data_transformation', (data) => {
        if (data.workflow_id === workflowId) {
          setTransformations(prev => [...prev, data.transformation]);
        }
      });



      // Handle agent log updates
      websocketService.on('agent_log', (data) => {
        if (data.data && data.data.workflow_id === workflowId) {
          setAgentLogs(prev => [...prev, data.data]);
        }
      });

    } catch (err) {
      console.error('WebSocket connection failed:', err);
    }
  };

  const handlePause = async () => {
    try {
      await workflowAPI.pause(workflowId!);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to pause workflow');
    }
  };

  const handleResume = async () => {
    try {
      await workflowAPI.resume(workflowId!);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resume workflow');
    }
  };

  const handleAbort = async () => {
    if (!window.confirm('Are you sure you want to abort this workflow?')) {
      return;
    }
    try {
      await workflowAPI.abort(workflowId!);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to abort workflow');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
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
        <Button onClick={() => navigate('/')}>
          Back to Workflows
        </Button>
      </Box>
    );
  }

  const selectedAgent = selectedAgentId ? agentDetails[selectedAgentId] : null;
  const canPause = workflowStatus?.status === 'running';
  const canResume = workflowStatus?.status === 'paused';
  const canAbort = ['running', 'paused'].includes(workflowStatus?.status);

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4">
              Workflow Execution
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                ID: {workflowId}
              </Typography>
              {refreshing && (
                <CircularProgress size={12} sx={{ ml: 1 }} />
              )}
            </Box>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton onClick={() => loadWorkflowData(true)} title="Refresh">
            <RefreshIcon />
          </IconButton>
          {canResume && (
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={handleResume}
            >
              Resume
            </Button>
          )}
          {canPause && (
            <Button
              variant="outlined"
              startIcon={<PauseIcon />}
              onClick={handlePause}
            >
              Pause
            </Button>
          )}
          {canAbort && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<StopIcon />}
              onClick={handleAbort}
            >
              Abort
            </Button>
          )}
        </Box>
      </Box>

      {/* Failed Workflow Alert */}
      {workflowStatus?.status === 'failed' && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            ⚠️ Workflow Failed
          </Typography>
          <Typography variant="body2" paragraph>
            The workflow execution encountered an error and could not complete.
          </Typography>
          
          <Paper sx={{ p: 2, bgcolor: 'background.default', mb: 2 }}>
            <Typography variant="subtitle2" color="error" gutterBottom>
              Error Details:
            </Typography>
            <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {workflowStatus?.error || 'Unknown error occurred'}
            </Typography>
          </Paper>

          {/* Show agent logs if available */}
          {agentLogs && agentLogs.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Agent Activity Logs:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'background.default', maxHeight: 300, overflow: 'auto' }}>
                <AgentLogViewer logs={agentLogs} />
              </Paper>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              color="error"
              onClick={() => navigate('/')}
            >
              Back to Workflows
            </Button>
            <Button
              variant="outlined"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </Box>
        </Alert>
      )}

      {/* Workflow Canvas - Full Width */}
      <Box sx={{ height: 250, mb: 2 }}>
        <WorkflowCanvas
          agents={agents}
          currentAgent={agents.find(a => a.status === 'running')?.id}
          onAgentClick={setSelectedAgentId}
        />
      </Box>

      {/* Main Content */}
      <Grid container spacing={2}>
        {/* Full Width Content */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>

            {/* Data Transformation Viewer */}
            {transformations.length > 0 && (
              <DataTransformationViewer transformations={transformations} />
            )}

            {/* Agent Data Tables - Show based on completed stages */}
            {workflowStatus?.stages_completed?.includes('data_processing') && (
              <AgentDataTable
                key="data_processor"
                workflowId={workflowId!}
                agentId="data_processor"
                agentType="data_processor"
              />
            )}
            {workflowStatus?.stages_completed?.includes('synthetic_generation') && (
              <>
                <AgentDataTable
                  key="synthetic_data"
                  workflowId={workflowId!}
                  agentId="synthetic_data"
                  agentType="synthetic_data"
                />
                
                {/* Download and Distribution Actions */}
                <Paper sx={{ p: 2, mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      Download Synthetic Dataset
                    </Typography>
                    <Button
                      variant="outlined"
                      color="primary"
                      href={`/api/v1/workflow/${workflowId}/download`}
                      download
                      startIcon={<DownloadIcon />}
                      sx={{ minWidth: 200 }}
                    >
                      Download CSV
                    </Button>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pt: 2, borderTop: 1, borderColor: 'divider' }}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Distribute Data to Targets
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Send synthetic data to external systems (databases, APIs, Salesforce, S3)
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => navigate(`/workflow/${workflowId}/mcp-distribution`)}
                        sx={{ minWidth: 200 }}
                      >
                        AI Distribution →
                      </Button>
                    </Box>
                  </Box>
                </Paper>
                
                {/* Quality Metrics Display */}
                <QualityMetricsPanel workflowId={workflowId!} />
              </>
            )}

            {/* Distribution Results - Show if distribution completed */}
            {workflowStatus?.stages_completed?.includes('distribution') && (
              <Paper sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box 
                    sx={{ 
                      width: 48, 
                      height: 48, 
                      borderRadius: '50%', 
                      bgcolor: 'success.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <Typography variant="h5" color="white">✓</Typography>
                  </Box>
                  <Box>
                    <Typography variant="h6">
                      Data Distribution Complete
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Synthetic data has been successfully distributed to target systems
                    </Typography>
                  </Box>
                </Box>
                
                <Alert severity="success" sx={{ mb: 2 }}>
                  Distribution completed successfully. Data has been sent to the configured targets.
                </Alert>

                {/* Removed legacy distribution buttons - now using MCP Distribution only */}
              </Paper>
            )}

            {/* Agent Activity Logs */}
            <AgentLogViewer logs={agentLogs} autoScroll={true} />
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
