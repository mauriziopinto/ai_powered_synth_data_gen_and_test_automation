/**
 * Workflow List Page
 * 
 * Lists all workflows with filtering, sorting, and management capabilities
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Button,
  TextField,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import RefreshIcon from '@mui/icons-material/Refresh';
import { workflowAPI } from '../services/api';

interface Workflow {
  workflow_id: string;
  status: string;
  config_id: string;
  num_records: number;
  started_at: string;
  updated_at: string;
  completed_at?: string;
  progress: number;
  current_stage?: string;
  stages_completed: string[];
  error?: string;
  cost_usd: number;
}

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success'> = {
  running: 'primary',
  completed: 'success',
  failed: 'error',
  paused: 'warning',
  aborted: 'default',
};

export default function WorkflowListPage() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [workflowToDelete, setWorkflowToDelete] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, [statusFilter]);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = { limit: 100 };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      
      const response = await workflowAPI.list(params);
      setWorkflows(response.data);
      setLoading(false);
    } catch (err: any) {
      console.error('Error loading workflows:', err);
      setError(err.response?.data?.detail || 'Failed to load workflows');
      setLoading(false);
    }
  };

  const handleViewWorkflow = (workflowId: string) => {
    navigate(`/workflow/${workflowId}`);
  };

  const handleDeleteClick = (workflowId: string) => {
    setWorkflowToDelete(workflowId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!workflowToDelete) return;

    try {
      setDeleting(true);
      await workflowAPI.delete(workflowToDelete);
      setDeleteDialogOpen(false);
      setWorkflowToDelete(null);
      await loadWorkflows(); // Reload list
    } catch (err: any) {
      console.error('Error deleting workflow:', err);
      setError(err.response?.data?.detail || 'Failed to delete workflow');
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDuration = (startedAt: string, completedAt?: string) => {
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const durationMs = end.getTime() - start.getTime();
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Workflows</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            select
            size="small"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            sx={{ minWidth: 150 }}
            label="Filter by Status"
          >
            <MenuItem value="all">All Statuses</MenuItem>
            <MenuItem value="running">Running</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="paused">Paused</MenuItem>
            <MenuItem value="aborted">Aborted</MenuItem>
          </TextField>
          <IconButton onClick={loadWorkflows} title="Refresh">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Workflows Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Workflow ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Current Stage</TableCell>
              <TableCell>Records</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Cost</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {workflows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    No workflows found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              workflows.map((workflow) => (
                <TableRow
                  key={workflow.workflow_id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handleViewWorkflow(workflow.workflow_id)}
                >
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {workflow.workflow_id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={workflow.status}
                      color={STATUS_COLORS[workflow.status] || 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ flexGrow: 1, maxWidth: 100 }}>
                        <Box
                          sx={{
                            height: 8,
                            bgcolor: 'grey.200',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              height: '100%',
                              bgcolor: workflow.status === 'failed' ? 'error.main' : 'primary.main',
                              width: `${workflow.progress}%`,
                              transition: 'width 0.3s',
                            }}
                          />
                        </Box>
                      </Box>
                      <Typography variant="caption">{Math.round(workflow.progress)}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {workflow.current_stage || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{workflow.num_records.toLocaleString()}</TableCell>
                  <TableCell>
                    <Tooltip title={formatDate(workflow.started_at)}>
                      <Typography variant="body2" noWrap>
                        {new Date(workflow.started_at).toLocaleDateString()}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    {formatDuration(workflow.started_at, workflow.completed_at)}
                  </TableCell>
                  <TableCell>${workflow.cost_usd.toFixed(5)}</TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewWorkflow(workflow.workflow_id)}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Workflow">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteClick(workflow.workflow_id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => !deleting && setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Workflow?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this workflow? This action cannot be undone.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontFamily: 'monospace' }}>
            Workflow ID: {workflowToDelete}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
