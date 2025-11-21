/**
 * Agent Log Viewer Component
 * 
 * Displays real-time agent activity logs with severity-based styling
 * Validates Requirements 1.3, 2.4
 */

import { useEffect, useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  IconButton,
  Collapse,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';

interface LogEntry {
  timestamp: string;
  workflow_id: string;
  agent_name: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  metadata?: Record<string, any>;
}

interface AgentLogViewerProps {
  logs: LogEntry[];
  autoScroll?: boolean;
}

export default function AgentLogViewer({ logs, autoScroll = true }: AgentLogViewerProps) {
  const [expanded, setExpanded] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current && expanded) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll, expanded]);

  const getSeverityIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <ErrorIcon fontSize="small" />;
      case 'warning':
        return <WarningIcon fontSize="small" />;
      default:
        return <InfoIcon fontSize="small" />;
    }
  };

  const getSeverityColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Agent Activity Logs
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={`${logs.length} entries`}
            size="small"
            color="primary"
            variant="outlined"
          />
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? 'collapse' : 'expand'}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
      </Box>

      <Collapse in={expanded}>
        <Box
          ref={logContainerRef}
          sx={{
            maxHeight: '400px',
            overflowY: 'auto',
            bgcolor: 'grey.50',
            borderRadius: 1,
            p: 2,
          }}
        >
          {logs.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No logs yet. Logs will appear here as agents execute.
            </Typography>
          ) : (
            logs.map((log, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  gap: 1,
                  mb: 1,
                  pb: 1,
                  borderBottom: index < logs.length - 1 ? '1px solid' : 'none',
                  borderColor: 'grey.200',
                }}
              >
                <Box
                  sx={{
                    color: `${getSeverityColor(log.level)}.main`,
                    display: 'flex',
                    alignItems: 'flex-start',
                    pt: 0.5,
                  }}
                >
                  {getSeverityIcon(log.level)}
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                    <Typography
                      variant="caption"
                      sx={{
                        fontFamily: 'monospace',
                        color: 'text.secondary',
                      }}
                    >
                      {formatTimestamp(log.timestamp)}
                    </Typography>
                    <Chip
                      label={log.agent_name}
                      size="small"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                    <Chip
                      label={log.level.toUpperCase()}
                      size="small"
                      color={getSeverityColor(log.level) as any}
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>
                  <Typography
                    variant="body2"
                    sx={{
                      wordBreak: 'break-word',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {log.message}
                  </Typography>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <Box
                      sx={{
                        mt: 0.5,
                        p: 1,
                        bgcolor: 'grey.100',
                        borderRadius: 0.5,
                        fontSize: '0.75rem',
                        fontFamily: 'monospace',
                      }}
                    >
                      {JSON.stringify(log.metadata, null, 2)}
                    </Box>
                  )}
                </Box>
              </Box>
            ))
          )}
        </Box>
      </Collapse>
    </Paper>
  );
}
