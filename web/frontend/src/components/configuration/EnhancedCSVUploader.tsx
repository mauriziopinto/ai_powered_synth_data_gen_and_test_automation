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
  TextField,
  Stepper,
  Step,
  StepLabel,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useNavigate } from 'react-router-dom';
import ParameterControls from './ParameterControls';

interface EnhancedCSVUploaderProps {
  onUploadSuccess?: (workflowId: string) => void;
}

const steps = ['Upload CSV', 'Configure Parameters', 'Review & Start'];

const EnhancedCSVUploader: React.FC<EnhancedCSVUploaderProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  
  // Step management
  const [activeStep, setActiveStep] = useState(0);
  
  // File upload state
  const [file, setFile] = useState<File | null>(null);
  const [workflowName, setWorkflowName] = useState<string>('');
  
  // CSV analysis state
  const [csvPreview, setCsvPreview] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  
  // Parameters state
  const [params, setParams] = useState({
    sdv_model: 'gaussian_copula',
    bedrock_model: 'anthropic.claude-3-sonnet-20240229-v1:0',
    num_records: 100,
    edge_case_frequency: 0.1,
    preserve_edge_cases: true,
    random_seed: undefined as number | undefined,
    temperature: 0.7,
    max_tokens: 2000,
  });
  
  // Workflow execution state
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [uploadedWorkflowId, setUploadedWorkflowId] = useState<string | null>(null);
  const [workflowProgress, setWorkflowProgress] = useState<number>(0);
  const [workflowStage, setWorkflowStage] = useState<string>('');

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
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

      // Analyze CSV file
      await analyzeCSV(selectedFile);
    }
  };

  const analyzeCSV = async (file: File) => {
    setAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/csv/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to analyze CSV');
      }

      const data = await response.json();
      setCsvPreview(data);
      
      // Auto-suggest parameters based on analysis
      if (data.row_count) {
        setParams(prev => ({
          ...prev,
          num_records: Math.min(data.row_count * 2, 1000), // Suggest 2x original size
        }));
      }
    } catch (err) {
      console.error('CSV analysis error:', err);
      setError('Failed to analyze CSV file. You can still proceed with default settings.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleNext = () => {
    if (activeStep === 0 && !file) {
      setError('Please select a CSV file');
      return;
    }
    setError(null);
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setError(null);
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleStartWorkflow = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('workflow_name', workflowName || `CSV Upload ${new Date().toISOString()}`);
      
      // Add all parameters
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formData.append(key, value.toString());
        }
      });

      const response = await fetch('/api/v1/csv/upload-csv-enhanced', {
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

    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload file');
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
    setCsvPreview(null);
    setActiveStep(0);
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Upload a CSV file to automatically generate synthetic data matching its structure and patterns.
            </Typography>

            <Stack spacing={2}>
              {/* File Upload */}
              <Box>
                <input
                  accept=".csv"
                  style={{ display: 'none' }}
                  id="csv-file-upload"
                  type="file"
                  onChange={handleFileChange}
                  disabled={analyzing}
                />
                <label htmlFor="csv-file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<CloudUploadIcon />}
                    fullWidth
                    disabled={analyzing}
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
                label="Workflow Name"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                disabled={analyzing}
                fullWidth
                placeholder="e.g., Customer Data Synthesis"
                helperText="Give your workflow a descriptive name"
              />

              {analyzing && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Analyzing CSV file...
                  </Typography>
                </Box>
              )}

              {csvPreview && (
                <Card variant="outlined" sx={{ mt: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      📊 CSV Analysis
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="body2">
                        <strong>Rows:</strong> {csvPreview.row_count?.toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Columns:</strong> {csvPreview.column_count}
                      </Typography>
                      {csvPreview.columns && (
                        <Box>
                          <Typography variant="body2" gutterBottom>
                            <strong>Column Types:</strong>
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {csvPreview.columns.slice(0, 10).map((col: any, idx: number) => (
                              <Chip 
                                key={idx}
                                label={`${col.name}: ${col.type}`}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                            {csvPreview.columns.length > 10 && (
                              <Chip 
                                label={`+${csvPreview.columns.length - 10} more`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </Box>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              )}
            </Stack>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure the parameters for synthetic data generation. These settings control how the data is generated.
            </Typography>
            
            <ParameterControls
              params={params}
              onChange={setParams}
            />
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Review your configuration before starting the workflow.
            </Typography>

            <Stack spacing={2}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    📁 File Information
                  </Typography>
                  <Typography variant="body2">
                    <strong>File:</strong> {file?.name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Workflow Name:</strong> {workflowName}
                  </Typography>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    ⚙️ Generation Parameters
                  </Typography>
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      <strong>SDV Model:</strong> {params.sdv_model}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Bedrock Model:</strong> {params.bedrock_model.split('/').pop()}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Records to Generate:</strong> {params.num_records.toLocaleString()}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Edge Case Frequency:</strong> {(params.edge_case_frequency * 100).toFixed(0)}%
                    </Typography>
                    <Typography variant="body2">
                      <strong>Preserve Edge Cases:</strong> {params.preserve_edge_cases ? 'Yes' : 'No'}
                    </Typography>
                    {params.random_seed && (
                      <Typography variant="body2">
                        <strong>Random Seed:</strong> {params.random_seed}
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Box>
        );

      default:
        return null;
    }
  };

  if (success && uploadedWorkflowId) {
    return (
      <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
        <Alert 
          severity="success" 
          sx={{ mb: 2 }}
          icon={<CheckCircleIcon />}
        >
          <Typography variant="body2" gutterBottom>
            Workflow started successfully!
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Redirecting to workflow page...
          </Typography>
        </Alert>
        <Button
          variant="outlined"
          onClick={handleReset}
          fullWidth
        >
          Upload Another File
        </Button>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Stepper activeStep={activeStep} sx={{ my: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ minHeight: 300 }}>
        {renderStepContent()}
      </Box>

      {uploading && (
        <Box sx={{ mt: 3 }}>
          <LinearProgress 
            variant={workflowProgress > 0 ? "determinate" : "indeterminate"}
            value={workflowProgress}
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {workflowStage ? workflowStage.replace(/_/g, ' ') : 'Starting workflow...'}
            </Typography>
            {workflowProgress > 0 && (
              <Typography variant="caption" color="text.secondary">
                {Math.round(workflowProgress)}%
              </Typography>
            )}
          </Box>
        </Box>
      )}

      <Divider sx={{ my: 3 }} />

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          disabled={activeStep === 0 || uploading}
          onClick={handleBack}
          startIcon={<ArrowBackIcon />}
        >
          Back
        </Button>
        
        {activeStep === steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleStartWorkflow}
            disabled={uploading}
            size="large"
          >
            {uploading ? 'Starting...' : 'Start Workflow'}
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleNext}
            endIcon={<ArrowForwardIcon />}
            disabled={!file || analyzing}
          >
            Next
          </Button>
        )}
      </Box>
    </Paper>
  );
};

export default EnhancedCSVUploader;
