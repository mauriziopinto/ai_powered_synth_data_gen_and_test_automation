/**
 * Agent Detail Panel Component
 * 
 * Displays detailed information about a specific agent with expandable sections
 * Validates Requirements 20.2, 25.1, 25.3
 */

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Chip,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';

interface AgentDetail {
  agent_id: string;
  agent_type: string;
  status: string;
  current_operation?: string;
  progress: number;
  message?: string;
  logs?: LogEntry[];
  decisions?: Decision[];
  data_samples?: DataSample[];
  metrics?: Record<string, any>;
}

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
}

interface Decision {
  timestamp: string;
  decision: string;
  reasoning: string;
  confidence?: number;
}

interface DataSample {
  field: string;
  before?: any;
  after?: any;
  transformation?: string;
}

interface AgentDetailPanelProps {
  agent: AgentDetail;
}

const STATUS_COLORS: Record<string, string> = {
  idle: 'default',
  running: 'primary',
  completed: 'success',
  failed: 'error',
  paused: 'warning',
};

export default function AgentDetailPanel({ agent }: AgentDetailPanelProps) {
  const getLogIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'warning':
        return <ErrorIcon color="warning" fontSize="small" />;
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%', overflow: 'auto' }}>
      {/* Agent Header */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          {agent.agent_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
          <Chip
            label={agent.status.toUpperCase()}
            color={STATUS_COLORS[agent.status] as any}
            size="small"
          />
          {agent.status === 'completed' && (
            <CheckCircleIcon color="success" fontSize="small" />
          )}
        </Box>
        {agent.current_operation && (
          <Typography variant="body2" color="text.secondary">
            {agent.current_operation}
          </Typography>
        )}
        {agent.message && (
          <Typography variant="body2" color="primary" sx={{ mt: 1, fontStyle: 'italic' }}>
            {agent.message}
          </Typography>
        )}
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Expandable Sections */}
      
      {/* Logs Section */}
      {agent.logs && agent.logs.length > 0 && (
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">
              Execution Logs ({agent.logs.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {agent.logs.slice(-10).map((log, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
                    {getLogIcon(log.level)}
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </Typography>
                      <Typography variant="body2">{log.message}</Typography>
                    </Box>
                  </Box>
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Decisions Section */}
      {agent.decisions && agent.decisions.length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">
              Decisions & Reasoning ({agent.decisions.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {agent.decisions.map((decision, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    {decision.decision}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {decision.reasoning}
                  </Typography>
                  {decision.confidence !== undefined && (
                    <Typography variant="caption" color="text.secondary">
                      Confidence: {(decision.confidence * 100).toFixed(1)}%
                    </Typography>
                  )}
                  {index < (agent.decisions?.length || 0) - 1 && <Divider sx={{ mt: 1 }} />}
                </Box>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Data Transformations Section */}
      {agent.data_samples && agent.data_samples.length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">
              Data Transformations ({agent.data_samples.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {agent.data_samples.map((sample, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    {sample.field}
                  </Typography>
                  {sample.transformation && (
                    <Typography variant="caption" color="primary" sx={{ display: 'block', mb: 0.5 }}>
                      {sample.transformation}
                    </Typography>
                  )}
                  <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                    {sample.before !== undefined && (
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Before:
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            bgcolor: 'error.light',
                            color: 'error.contrastText',
                            p: 0.5,
                            borderRadius: 1,
                          }}
                        >
                          {JSON.stringify(sample.before)}
                        </Typography>
                      </Box>
                    )}
                    {sample.after !== undefined && (
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          After:
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            bgcolor: 'success.light',
                            color: 'success.contrastText',
                            p: 0.5,
                            borderRadius: 1,
                          }}
                        >
                          {JSON.stringify(sample.after)}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  {index < (agent.data_samples?.length || 0) - 1 && <Divider sx={{ mt: 1 }} />}
                </Box>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Metrics Section */}
      {agent.metrics && Object.keys(agent.metrics).length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">
              Performance Metrics
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {Object.entries(agent.metrics).map(([key, value]) => (
                <ListItem key={key}>
                  <ListItemText
                    primary={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    secondary={typeof value === 'number' ? value.toFixed(2) : String(value)}
                  />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
    </Paper>
  );
}
