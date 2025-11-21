/**
 * Agent Data Table Component
 * 
 * Displays sample data from agent execution results in a table format
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DatasetIcon from '@mui/icons-material/Dataset';

interface AgentDataTableProps {
  workflowId: string;
  agentId: string;
  agentType: string;
}

interface AgentResults {
  agent_type: string;
  status: string;
  total_rows?: number;
  total_columns?: number;
  total_records_generated?: number;
  columns: string[];
  sample_data: Record<string, any>[];
  generation_method?: string;
  privacy_level?: string;
}

export default function AgentDataTable({ workflowId, agentId, agentType }: AgentDataTableProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AgentResults | null>(null);

  useEffect(() => {
    loadAgentResults();
  }, [workflowId, agentId]);

  const loadAgentResults = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/workflow/${workflowId}/agent/${agentId}/results?limit=10`);
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('Agent results not found. The agent may not have completed yet.');
        } else if (response.status === 500) {
          setError('Server error loading results. Please try refreshing the page.');
        } else {
          setError('Failed to load agent results');
        }
        return;
      }

      const data = await response.json();
      
      if (data.results) {
        // Extract columns from sample_data if not provided directly
        let columns = data.results.columns;
        if (!columns || !Array.isArray(columns) || columns.length === 0) {
          // Try to extract columns from sample_data
          if (data.results.sample_data && Array.isArray(data.results.sample_data) && data.results.sample_data.length > 0) {
            columns = Object.keys(data.results.sample_data[0]);
            console.log('Extracted columns from sample_data:', columns);
          }
        }
        
        // Validate that we have sample data
        if (!data.results.sample_data || !Array.isArray(data.results.sample_data)) {
          console.warn('Missing or invalid sample_data field in response:', data);
          setError('Invalid response structure: missing sample data');
          return;
        }
        
        // Set results with extracted or provided columns
        setResults({
          ...data.results,
          columns: columns || []
        });
      } else {
        setError(data.message || 'No results available');
      }
    } catch (err: any) {
      console.error('Error loading agent results:', err);
      setError(err.message || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!results) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No results available yet
      </Alert>
    );
  }

  if (!results.columns || results.columns.length === 0) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        No columns found in results
      </Alert>
    );
  }

  if (!results.sample_data || results.sample_data.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No sample data available
      </Alert>
    );
  }

  const getAgentTitle = () => {
    switch (agentType) {
      case 'data_processor':
        return 'Original Data Sample';
      case 'synthetic_data':
        return 'Synthetic Data Sample';
      default:
        return 'Data Sample';
    }
  };

  const getAgentIcon = () => {
    switch (agentType) {
      case 'data_processor':
        return '📊';
      case 'synthetic_data':
        return '🔮';
      default:
        return '📋';
    }
  };

  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6">
            {getAgentIcon()} {getAgentTitle()}
          </Typography>
          {results.status && (
            <Chip
              icon={<CheckCircleIcon />}
              label={results.status.toUpperCase()}
              color="success"
              size="small"
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {results.total_rows && (
            <Chip
              icon={<DatasetIcon />}
              label={`${results.total_rows} rows`}
              size="small"
              variant="outlined"
            />
          )}
          {results.total_records_generated && (
            <Chip
              icon={<DatasetIcon />}
              label={`${results.total_records_generated} generated`}
              size="small"
              variant="outlined"
            />
          )}
          {results.total_columns && (
            <Chip
              label={`${results.total_columns} columns`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      </Box>

      {/* Additional Info */}
      {(results.generation_method || results.privacy_level) && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
          {results.generation_method && (
            <Chip
              label={`Method: ${results.generation_method}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
          {results.privacy_level && (
            <Chip
              label={`Privacy: ${results.privacy_level}`}
              size="small"
              color="success"
              variant="outlined"
            />
          )}
        </Box>
      )}

      {/* Data Table */}
      <TableContainer sx={{ maxHeight: 400 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                #
              </TableCell>
              {results.columns.map((column) => (
                <TableCell
                  key={column}
                  sx={{ fontWeight: 'bold', bgcolor: 'primary.light', color: 'primary.contrastText' }}
                >
                  {column}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {results.sample_data.map((row, index) => (
              <TableRow key={index} hover>
                <TableCell sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>
                  {index + 1}
                </TableCell>
                {results.columns.map((column) => (
                  <TableCell key={column}>
                    {row[column] !== null && row[column] !== undefined
                      ? String(row[column])
                      : <span style={{ color: '#999', fontStyle: 'italic' }}>null</span>
                    }
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Footer */}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        Showing {results.sample_data.length} sample rows
        {results.total_rows && ` of ${results.total_rows} total`}
        {results.total_records_generated && ` (${results.total_records_generated} generated)`}
      </Typography>
    </Paper>
  );
}
