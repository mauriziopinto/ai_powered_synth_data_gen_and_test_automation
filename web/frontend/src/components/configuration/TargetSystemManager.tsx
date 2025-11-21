import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Storage as DatabaseIcon,
  Cloud as CloudIcon,
  Api as ApiIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { TargetSystem } from '../../types';

interface TargetSystemManagerProps {
  targets: TargetSystem[];
  onChange: (targets: TargetSystem[]) => void;
  errors?: Record<string, string>;
}

const TARGET_TYPES = [
  { value: 'database', label: 'Database', icon: DatabaseIcon, color: '#1976d2' },
  { value: 'salesforce', label: 'Salesforce', icon: CloudIcon, color: '#00a1e0' },
  { value: 'api', label: 'REST API', icon: ApiIcon, color: '#4caf50' },
  { value: 'file', label: 'File Storage', icon: FolderIcon, color: '#ff9800' },
];

const DATABASE_TYPES = ['postgresql', 'mysql', 'sqlserver', 'oracle'];
const LOAD_STRATEGIES = ['truncate_insert', 'upsert', 'append'];

export default function TargetSystemManager({ targets, onChange }: TargetSystemManagerProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [currentTarget, setCurrentTarget] = useState<TargetSystem>({
    type: 'database',
    name: '',
    config: {},
  });

  const handleOpenDialog = (index?: number) => {
    if (index !== undefined) {
      setEditingIndex(index);
      setCurrentTarget({ ...targets[index] });
    } else {
      setEditingIndex(null);
      setCurrentTarget({
        type: 'database',
        name: '',
        config: {},
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingIndex(null);
  };

  const handleSaveTarget = () => {
    if (!currentTarget.name.trim()) {
      return;
    }

    const newTargets = [...targets];
    if (editingIndex !== null) {
      newTargets[editingIndex] = currentTarget;
    } else {
      newTargets.push(currentTarget);
    }
    onChange(newTargets);
    handleCloseDialog();
  };

  const handleDeleteTarget = (index: number) => {
    const newTargets = targets.filter((_, i) => i !== index);
    onChange(newTargets);
  };

  const handleConfigChange = (key: string, value: any) => {
    setCurrentTarget({
      ...currentTarget,
      config: {
        ...currentTarget.config,
        [key]: value,
      },
    });
  };

  const getTargetIcon = (type: string) => {
    const targetType = TARGET_TYPES.find((t) => t.value === type);
    const Icon = targetType?.icon || DatabaseIcon;
    return <Icon sx={{ color: targetType?.color }} />;
  };

  const renderConfigFields = () => {
    switch (currentTarget.type) {
      case 'database':
        return (
          <>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Database Type</InputLabel>
                <Select
                  value={currentTarget.config.db_type || 'postgresql'}
                  label="Database Type"
                  onChange={(e) => handleConfigChange('db_type', e.target.value)}
                >
                  {DATABASE_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Host"
                value={currentTarget.config.host || ''}
                onChange={(e) => handleConfigChange('host', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Port"
                type="number"
                value={currentTarget.config.port || ''}
                onChange={(e) => handleConfigChange('port', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Database Name"
                value={currentTarget.config.database || ''}
                onChange={(e) => handleConfigChange('database', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Username"
                value={currentTarget.config.username || ''}
                onChange={(e) => handleConfigChange('username', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={currentTarget.config.password || ''}
                onChange={(e) => handleConfigChange('password', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Load Strategy</InputLabel>
                <Select
                  value={currentTarget.config.load_strategy || 'truncate_insert'}
                  label="Load Strategy"
                  onChange={(e) => handleConfigChange('load_strategy', e.target.value)}
                >
                  {LOAD_STRATEGIES.map((strategy) => (
                    <MenuItem key={strategy} value={strategy}>
                      {strategy.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </>
        );

      case 'salesforce':
        return (
          <>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Instance URL"
                value={currentTarget.config.instance_url || ''}
                onChange={(e) => handleConfigChange('instance_url', e.target.value)}
                placeholder="https://your-instance.salesforce.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Username"
                value={currentTarget.config.username || ''}
                onChange={(e) => handleConfigChange('username', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={currentTarget.config.password || ''}
                onChange={(e) => handleConfigChange('password', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Security Token"
                type="password"
                value={currentTarget.config.security_token || ''}
                onChange={(e) => handleConfigChange('security_token', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Object Name"
                value={currentTarget.config.object_name || ''}
                onChange={(e) => handleConfigChange('object_name', e.target.value)}
                placeholder="Account, Contact, Custom__c"
              />
            </Grid>
          </>
        );

      case 'api':
        return (
          <>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="API Endpoint"
                value={currentTarget.config.endpoint || ''}
                onChange={(e) => handleConfigChange('endpoint', e.target.value)}
                placeholder="https://api.example.com/data"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Method</InputLabel>
                <Select
                  value={currentTarget.config.method || 'POST'}
                  label="Method"
                  onChange={(e) => handleConfigChange('method', e.target.value)}
                >
                  <MenuItem value="POST">POST</MenuItem>
                  <MenuItem value="PUT">PUT</MenuItem>
                  <MenuItem value="PATCH">PATCH</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Batch Size"
                type="number"
                value={currentTarget.config.batch_size || 100}
                onChange={(e) => handleConfigChange('batch_size', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="API Key"
                type="password"
                value={currentTarget.config.api_key || ''}
                onChange={(e) => handleConfigChange('api_key', e.target.value)}
              />
            </Grid>
          </>
        );

      case 'file':
        return (
          <>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="File Path"
                value={currentTarget.config.path || ''}
                onChange={(e) => handleConfigChange('path', e.target.value)}
                placeholder="/path/to/output or s3://bucket/prefix"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  value={currentTarget.config.format || 'csv'}
                  label="Format"
                  onChange={(e) => handleConfigChange('format', e.target.value)}
                >
                  <MenuItem value="csv">CSV</MenuItem>
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="parquet">Parquet</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Compression</InputLabel>
                <Select
                  value={currentTarget.config.compression || 'none'}
                  label="Compression"
                  onChange={(e) => handleConfigChange('compression', e.target.value)}
                >
                  <MenuItem value="none">None</MenuItem>
                  <MenuItem value="gzip">GZIP</MenuItem>
                  <MenuItem value="snappy">Snappy</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Target Systems</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          size="small"
        >
          Add Target
        </Button>
      </Box>

      {targets.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No target systems configured. Add at least one target to distribute synthetic data.
        </Alert>
      )}

      <Stack spacing={2}>
        {targets.map((target, index) => (
          <Card key={index} variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', flex: 1, gap: 2 }}>
                  {getTargetIcon(target.type)}
                  <Box>
                    <Typography variant="subtitle1">{target.name}</Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                      <Chip
                        label={TARGET_TYPES.find((t) => t.value === target.type)?.label || target.type}
                        size="small"
                      />
                      {target.config.host && (
                        <Chip label={target.config.host} size="small" variant="outlined" />
                      )}
                      {target.config.endpoint && (
                        <Chip label={target.config.endpoint} size="small" variant="outlined" />
                      )}
                    </Box>
                  </Box>
                </Box>
                <IconButton size="small" onClick={() => handleOpenDialog(index)}>
                  <EditIcon />
                </IconButton>
                <IconButton size="small" color="error" onClick={() => handleDeleteTarget(index)}>
                  <DeleteIcon />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingIndex !== null ? 'Edit Target System' : 'Add Target System'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Target Name"
                value={currentTarget.name}
                onChange={(e) => setCurrentTarget({ ...currentTarget, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Target Type</InputLabel>
                <Select
                  value={currentTarget.type}
                  label="Target Type"
                  onChange={(e) =>
                    setCurrentTarget({ ...currentTarget, type: e.target.value, config: {} })
                  }
                >
                  {TARGET_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <type.icon sx={{ color: type.color }} />
                        {type.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {renderConfigFields()}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveTarget} variant="contained" disabled={!currentTarget.name.trim()}>
            {editingIndex !== null ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
