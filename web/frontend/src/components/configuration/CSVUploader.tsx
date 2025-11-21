import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  LinearProgress,
  Chip,
  Stack,
  TextField
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useNavigate } from 'react-router-dom';

interface CSVUploaderProps {
  onUploadSuccess?: (workflowId: string) => void;
}

const CSVUploader: React.FC<CSVUploaderProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [numRecords, setNumRecords] = useState<number>(100);
  const [workflowName, setWorkflowName] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [uploadedWorkflowId, setUploadedWorkflowId] = useState<string | null>(null);
  const [workflowProgress, setWorkflowProgress] = useState<number>(0);
  const [workflowStage, setWorkflowStage] = useState<string>('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
      setSuccess(false);
      
      // Auto-generate workflow name from filename
      if (!workflowName) {
        const name = selectedFile.name.replace('.csv', '');
        setWorkflowName(`Synthetic Data from ${name}`);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('num_records', numRecords.toString());
      if (workflowName) {
        formData.append('workflow_name', workflowName);
      }

      const response = await fetch('/api/v1/workflow/upload-csv', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setUploadedWorkflowId(data.workflow_id);
      
      if (onUploadSuccess) {
        onUploadSuccess(data.workflow_id);
      }

      // Don't set success yet - wait for workflow to start processing
      // The polling effect will handle progress updates

    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  // Poll for workflow progress after upload
  React.useEffect(() => {
    if (!uploadedWorkflowId) return;

    const pollProgress = async () => {
      try {
        const response = await fetch(`/api/v1/workflow/${uploadedWorkflowId}/status`);
        if (!response.ok) return;

        const data = await response.json();
        setWorkflowProgress(data.progress);
        setWorkflowStage(data.current_stage || '');

        // If workflow completed, show success and redirect
        if (data.status === 'completed') {
          setSuccess(true);
          setUploading(false);
          setTimeout(() => {
            navigate(`/workflow/${uploadedWorkflowId}`);
          }, 2000);
        } else if (data.status === 'failed') {
          setError('Workflow failed: ' + (data.error || 'Unknown error'));
          setUploading(false);
        }
      } catch (err) {
        console.error('Progress polling error:', err);
      }
    };

    // Poll immediately, then every 1 second
    pollProgress();
    const interval = setInterval(pollProgress, 1000);

    return () => clearInterval(interval);
  }, [uploadedWorkflowId, navigate]);

  const handleReset = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    setUploadedWorkflowId(null);
    setWorkflowName('');
    setWorkflowProgress(0);
    setWorkflowStage('');
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        📊 Upload CSV for Synthetic Data Generation
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Upload a CSV file to automatically generate synthetic data matching its structure and patterns.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && uploadedWorkflowId && (
        <Alert 
          severity="success" 
          sx={{ mb: 2 }}
          icon={<CheckCircleIcon />}
        >
          <Typography variant="body2" gutterBottom>
            CSV uploaded successfully! Workflow started.
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Redirecting to workflow page...
          </Typography>
        </Alert>
      )}

      {!success && (
        <Box>
          <Stack spacing={2}>
            {/* File Upload */}
            <Box>
              <input
                accept=".csv"
                style={{ display: 'none' }}
                id="csv-file-upload"
                type="file"
                onChange={handleFileChange}
                disabled={uploading}
              />
              <label htmlFor="csv-file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  fullWidth
                  disabled={uploading}
                  sx={{ py: 2 }}
                >
                  {file ? 'Change File' : 'Select CSV File'}
                </Button>
              </label>
              
              {file && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip 
                    label={file.name} 
                    onDelete={handleReset}
                    color="primary"
                    variant="outlined"
                  />
                  <Typography variant="caption" color="text.secondary">
                    {(file.size / 1024).toFixed(2)} KB
                  </Typography>
                </Box>
              )}
            </Box>

            {/* Workflow Name */}
            <TextField
              label="Workflow Name (Optional)"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              disabled={uploading}
              fullWidth
              placeholder="e.g., Customer Data Synthesis"
              helperText="Give your workflow a descriptive name"
            />

            {/* Number of Records */}
            <TextField
              label="Number of Records to Generate"
              type="number"
              value={numRecords}
              onChange={(e) => setNumRecords(Math.max(1, parseInt(e.target.value) || 100))}
              disabled={uploading}
              fullWidth
              inputProps={{ min: 1, max: 10000 }}
              helperText="How many synthetic records should we generate?"
            />

            {/* Upload Button */}
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!file || uploading}
              fullWidth
              size="large"
              sx={{ py: 1.5 }}
            >
              {uploading ? 'Uploading...' : 'Upload & Start Workflow'}
            </Button>
          </Stack>

          {uploading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress 
                variant={workflowProgress > 0 ? "determinate" : "indeterminate"}
                value={workflowProgress}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {workflowStage ? workflowStage.replace(/_/g, ' ') : 'Processing your CSV file...'}
                </Typography>
                {workflowProgress > 0 && (
                  <Typography variant="caption" color="text.secondary">
                    {Math.round(workflowProgress)}%
                  </Typography>
                )}
              </Box>
            </Box>
          )}
        </Box>
      )}

      {success && (
        <Button
          variant="outlined"
          onClick={handleReset}
          fullWidth
          sx={{ mt: 2 }}
        >
          Upload Another File
        </Button>
      )}

      {/* Info Box */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
        <Typography variant="caption" color="info.dark">
          <strong>💡 How it works:</strong>
          <br />
          1. Upload your CSV file
          <br />
          2. We analyze the schema and data patterns
          <br />
          3. Generate synthetic data matching your structure
          <br />
          4. Download results or distribute to target systems
        </Typography>
      </Box>
    </Paper>
  );
};

export default CSVUploader;
