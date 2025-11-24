import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  MenuItem,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Target {
  id: string;
  name: string;
  type: 'database' | 'salesforce' | 'api' | 's3';
  config: any;
  created_at: string;
  is_active: boolean;
}

const TARGET_TYPES = [
  { value: 'database', label: 'Database' },
  { value: 'salesforce', label: 'Salesforce' },
  { value: 'api', label: 'API' },
  { value: 's3', label: 'S3' }
];

export default function TargetsPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTarget, setEditingTarget] = useState<Target | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'database' as Target['type'],
    config: {}
  });
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [testing, setTesting] = useState(false);
  const [loadingMocks, setLoadingMocks] = useState(false);
  const [viewDataDialog, setViewDataDialog] = useState(false);
  const [targetData, setTargetData] = useState<any>(null);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    loadTargets();
  }, []);

  const handleLoadMockTargets = async () => {
    setLoadingMocks(true);
    try {
      await axios.post(`${API_URL}/mock-targets/seed`);
      loadTargets();
    } catch (error) {
      console.error('Failed to load mock targets:', error);
    } finally {
      setLoadingMocks(false);
    }
  };

  const handleViewData = async (target: Target) => {
    setLoadingData(true);
    setViewDataDialog(true);
    try {
      const response = await axios.get(`${API_URL}/mock-targets/${target.id}/data`);
      setTargetData(response.data);
    } catch (error) {
      console.error('Failed to load target data:', error);
      setTargetData({ error: 'Failed to load data' });
    } finally {
      setLoadingData(false);
    }
  };

  const loadTargets = async () => {
    try {
      const response = await axios.get(`${API_URL}/targets/`);
      setTargets(response.data);
    } catch (error) {
      console.error('Failed to load targets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (target?: Target) => {
    if (target) {
      setEditingTarget(target);
      setFormData({
        name: target.name,
        type: target.type,
        config: target.config
      });
    } else {
      setEditingTarget(null);
      setFormData({ name: '', type: 'database', config: {} });
    }
    setTestResult(null);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingTarget(null);
    setTestResult(null);
  };

  const handleSave = async () => {
    try {
      if (editingTarget) {
        await axios.put(`${API_URL}/targets/${editingTarget.id}`, {
          name: formData.name,
          config: formData.config
        });
      } else {
        await axios.post(`${API_URL}/targets/`, formData);
      }
      loadTargets();
      handleCloseDialog();
    } catch (error) {
      console.error('Failed to save target:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this target?')) return;
    
    try {
      await axios.delete(`${API_URL}/targets/${id}`);
      loadTargets();
    } catch (error) {
      console.error('Failed to delete target:', error);
    }
  };

  const handleTest = async () => {
    if (!editingTarget) return;
    
    setTesting(true);
    try {
      const response = await axios.post(`${API_URL}/targets/${editingTarget.id}/test`);
      setTestResult(response.data);
    } catch (error) {
      setTestResult({ success: false, message: 'Test failed' });
    } finally {
      setTesting(false);
    }
  };

  const renderConfigFields = () => {
    switch (formData.type) {
      case 'database':
        return (
          <>
            <TextField
              fullWidth
              label="Connection String"
              value={formData.config.connection_string || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, connection_string: e.target.value }
              })}
              margin="normal"
              placeholder="postgresql://user:pass@host:5432/db"
            />
            <TextField
              fullWidth
              label="Table Name"
              value={formData.config.table_name || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, table_name: e.target.value }
              })}
              margin="normal"
            />
          </>
        );
      
      case 'salesforce':
        return (
          <>
            <TextField
              fullWidth
              label="Instance URL"
              value={formData.config.instance_url || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, instance_url: e.target.value }
              })}
              margin="normal"
              placeholder="https://your-instance.salesforce.com"
            />
            <TextField
              fullWidth
              label="Access Token"
              type="password"
              value={formData.config.access_token || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, access_token: e.target.value }
              })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Object Type"
              value={formData.config.object_type || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, object_type: e.target.value }
              })}
              margin="normal"
              placeholder="Lead, Contact, Account, etc."
            />
          </>
        );
      
      case 'api':
        return (
          <>
            <TextField
              fullWidth
              label="Endpoint URL"
              value={formData.config.endpoint_url || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, endpoint_url: e.target.value }
              })}
              margin="normal"
              placeholder="https://api.example.com/data"
            />
            <TextField
              select
              fullWidth
              label="Method"
              value={formData.config.method || 'POST'}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, method: e.target.value }
              })}
              margin="normal"
            >
              <MenuItem value="POST">POST</MenuItem>
              <MenuItem value="PUT">PUT</MenuItem>
              <MenuItem value="PATCH">PATCH</MenuItem>
            </TextField>
          </>
        );
      
      case 's3':
        return (
          <>
            <TextField
              fullWidth
              label="Bucket Name"
              value={formData.config.bucket_name || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, bucket_name: e.target.value }
              })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Region"
              value={formData.config.region || 'us-east-1'}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, region: e.target.value }
              })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Path Prefix"
              value={formData.config.path_prefix || ''}
              onChange={(e) => setFormData({
                ...formData,
                config: { ...formData.config, path_prefix: e.target.value }
              })}
              margin="normal"
              placeholder="data/exports/"
            />
          </>
        );
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Distribution Targets</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            onClick={handleLoadMockTargets}
            disabled={loadingMocks}
          >
            {loadingMocks ? <CircularProgress size={20} /> : 'Load Mock Targets'}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Target
          </Button>
        </Box>
      </Box>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {targets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <Typography color="textSecondary">
                        No targets configured. Click "Add Target" to create one.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  targets.map((target) => (
                    <TableRow key={target.id}>
                      <TableCell>{target.name}</TableCell>
                      <TableCell>
                        <Chip label={target.type} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={target.is_active ? <CheckIcon /> : <ErrorIcon />}
                          label={target.is_active ? 'Active' : 'Inactive'}
                          color={target.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(target.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleViewData(target)}
                          title="View received data"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(target)}
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(target.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTarget ? 'Edit Target' : 'Add Target'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            margin="normal"
          />
          <TextField
            select
            fullWidth
            label="Type"
            value={formData.type}
            onChange={(e) => setFormData({
              ...formData,
              type: e.target.value as Target['type'],
              config: {}
            })}
            margin="normal"
            disabled={!!editingTarget}
          >
            {TARGET_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </TextField>
          
          {renderConfigFields()}

          {testResult && (
            <Alert severity={testResult.success ? 'success' : 'error'} sx={{ mt: 2 }}>
              {testResult.message}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          {editingTarget && (
            <Button onClick={handleTest} disabled={testing}>
              {testing ? <CircularProgress size={20} /> : 'Test Connection'}
            </Button>
          )}
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog 
        open={viewDataDialog} 
        onClose={() => setViewDataDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>Target Data</DialogTitle>
        <DialogContent>
          {loadingData ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : targetData?.error ? (
            <Alert severity="error">{targetData.error}</Alert>
          ) : targetData ? (
            <>
              <Typography variant="subtitle1" gutterBottom>
                <strong>{targetData.target_name}</strong> ({targetData.target_type})
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Records: {targetData.records_count}
              </Typography>
              {targetData.records_count > 0 ? (
                <Box 
                  sx={{ 
                    mt: 2, 
                    p: 2, 
                    bgcolor: 'grey.100', 
                    borderRadius: 1,
                    maxHeight: 400,
                    overflow: 'auto'
                  }}
                >
                  <pre style={{ margin: 0, fontSize: '12px' }}>
                    {JSON.stringify(targetData.records, null, 2)}
                  </pre>
                </Box>
              ) : (
                <Alert severity="info" sx={{ mt: 2 }}>
                  No data has been sent to this target yet.
                </Alert>
              )}
            </>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDataDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
