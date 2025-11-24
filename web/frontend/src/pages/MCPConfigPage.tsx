import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import axios from 'axios';
import Editor from '@monaco-editor/react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const EXAMPLE_CONFIG = `{
  "mcpServers": {
    "jira": {
      "command": "uvx",
      "args": ["mcp-server-jira"],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_TOKEN": "your_api_token"
      },
      "disabled": false
    },
    "salesforce": {
      "command": "uvx",
      "args": ["mcp-server-salesforce"],
      "env": {
        "SF_INSTANCE_URL": "https://your-instance.salesforce.com",
        "SF_ACCESS_TOKEN": "your_token"
      },
      "disabled": false
    },
    "postgres": {
      "command": "uvx",
      "args": ["mcp-server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db"
      },
      "disabled": false
    }
  }
}`;

export default function MCPConfigPage() {
  const [config, setConfig] = useState(EXAMPLE_CONFIG);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<any>(null);
  const [saveResult, setSaveResult] = useState<any>(null);
  const [servers, setServers] = useState<any[]>([]);
  const [showExample, setShowExample] = useState(false);

  useEffect(() => {
    loadConfig();
    loadServers();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/mcp/config`);
      if (response.data && Object.keys(response.data.mcpServers || {}).length > 0) {
        setConfig(JSON.stringify(response.data, null, 2));
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadServers = async () => {
    try {
      const response = await axios.get(`${API_URL}/mcp/servers`);
      setServers(response.data.servers || []);
    } catch (error) {
      console.error('Failed to load servers:', error);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    setSaveResult(null);
    
    try {
      const response = await axios.post(`${API_URL}/mcp/validate`, {
        config
      });
      setValidation(response.data);
    } catch (error: any) {
      setValidation({
        valid: false,
        error: error.response?.data?.detail || 'Validation failed'
      });
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveResult(null);
    
    try {
      const response = await axios.post(`${API_URL}/mcp/config`, {
        config
      });
      setSaveResult({
        success: true,
        message: response.data.message,
        servers_count: response.data.servers_count
      });
      loadServers();
    } catch (error: any) {
      setSaveResult({
        success: false,
        message: error.response?.data?.detail || 'Failed to save configuration'
      });
    } finally {
      setSaving(false);
    }
  };

  const handleLoadExample = () => {
    setConfig(EXAMPLE_CONFIG);
    setShowExample(false);
    setValidation(null);
    setSaveResult(null);
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
        <Box>
          <Typography variant="h4">MCP Configuration</Typography>
          <Typography variant="body2" color="text.secondary">
            Configure MCP servers for data distribution
          </Typography>
        </Box>
        <Button
          variant="outlined"
          onClick={() => setShowExample(true)}
        >
          View Example
        </Button>
      </Box>

      {servers.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configured Servers ({servers.length})
            </Typography>
            <List dense>
              {servers.map((server, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={server.name}
                    secondary={`Command: ${server.command}`}
                  />
                  <Chip
                    label={server.disabled ? 'Disabled' : 'Active'}
                    color={server.disabled ? 'default' : 'success'}
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            MCP Configuration (JSON)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Edit the MCP server configuration below. Each server can be used as a distribution target.
          </Typography>

          <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mt: 2, mb: 2 }}>
            <Editor
              height="400px"
              defaultLanguage="json"
              value={config}
              onChange={(value) => setConfig(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true
              }}
            />
          </Box>

          {validation && (
            <Alert 
              severity={validation.valid ? 'success' : 'error'} 
              sx={{ mb: 2 }}
              icon={validation.valid ? <CheckIcon /> : <ErrorIcon />}
            >
              {validation.valid ? (
                <>
                  <strong>Valid configuration!</strong>
                  <br />
                  Found {validation.servers_count} server(s): {validation.servers?.join(', ')}
                </>
              ) : (
                <>
                  <strong>Invalid configuration</strong>
                  <br />
                  {validation.error}
                </>
              )}
            </Alert>
          )}

          {saveResult && (
            <Alert 
              severity={saveResult.success ? 'success' : 'error'} 
              sx={{ mb: 2 }}
            >
              {saveResult.message}
              {saveResult.success && saveResult.servers_count && (
                <> ({saveResult.servers_count} servers configured)</>
              )}
            </Alert>
          )}

          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              onClick={handleValidate}
              disabled={validating || !config}
              startIcon={validating ? <CircularProgress size={20} /> : <CheckIcon />}
            >
              Validate
            </Button>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={saving || !config || (validation && !validation.valid)}
              startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
            >
              Save Configuration
            </Button>
            <Button
              variant="outlined"
              onClick={() => { loadConfig(); loadServers(); }}
              startIcon={<RefreshIcon />}
            >
              Reload
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Dialog open={showExample} onClose={() => setShowExample(false)} maxWidth="md" fullWidth>
        <DialogTitle>Example MCP Configuration</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            This example shows how to configure Jira, Salesforce, and PostgreSQL MCP servers:
          </Typography>
          <Box sx={{ bgcolor: 'grey.900', p: 2, borderRadius: 1, mt: 2 }}>
            <pre style={{ margin: 0, color: 'white', fontSize: '12px', overflow: 'auto' }}>
              {EXAMPLE_CONFIG}
            </pre>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowExample(false)}>Cancel</Button>
          <Button onClick={handleLoadExample} variant="contained">
            Load This Example
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
