import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ArrowBack,
  Info,
  Security,
  SmartToy,
  Analytics,
  CheckCircle,
} from '@mui/icons-material';
import TextField from '@mui/material/TextField';
import CostEstimationPanel from '../components/workflow/CostEstimationPanel';

interface FieldDetail {
  name: string;
  is_sensitive: boolean;
  sensitivity_type?: string;
  confidence: number;
  strategy: string;
  reasoning: string;
  sample_values?: any[];
}

interface AnalysisResults {
  total_fields: number;
  sensitive_fields: number;
  field_details: FieldDetail[];
  sample_data?: Record<string, any>[];
}

interface WorkflowStatus {
  workflow_id: string;
  status: string;
  num_records?: number;
  analysis_results?: AnalysisResults;
}

interface FieldStrategy {
  field_name: string;
  strategy: 'bedrock_llm' | 'sdv_preserve_distribution' | 'sdv_gaussian_copula' | 'bedrock_examples';
  custom_params?: Record<string, any>;
}

const STRATEGY_OPTIONS = [
  {
    value: 'bedrock_llm',
    label: 'Bedrock LLM',
    description: 'AI-powered generation for realistic, contextual data',
    icon: <SmartToy />,
    color: 'primary',
    bestFor: ['names', 'emails', 'addresses', 'text fields'],
  },
  {
    value: 'bedrock_examples',
    label: 'Example-Based Generation',
    description: 'Generate data based on your custom examples using AI',
    icon: <SmartToy />,
    color: 'primary',
    bestFor: ['custom formats', 'domain-specific data', 'branded content'],
    requiresExamples: true,
  },
  {
    value: 'sdv_preserve_distribution',
    label: 'SDV Preserve Distribution',
    description: 'Maintains statistical properties and distributions',
    icon: <Analytics />,
    color: 'secondary',
    bestFor: ['numerical data', 'categorical data', 'dates'],
  },
  {
    value: 'sdv_gaussian_copula',
    label: 'SDV Gaussian Copula',
    description: 'Advanced statistical modeling for complex relationships',
    icon: <Analytics />,
    color: 'info',
    bestFor: ['correlated fields', 'complex numerical relationships'],
  },
];

const StrategySelectionPage: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<Record<string, FieldStrategy>>({});
  const [submitting, setSubmitting] = useState(false);
  const [showStrategyInfo, setShowStrategyInfo] = useState<string | null>(null);
  const [sdvModel, setSdvModel] = useState<string>('gaussian_copula');
  const [sdvParams, setSdvParams] = useState<Record<string, any>>({
    epochs: 300,
    batch_size: 500,
  });

  useEffect(() => {
    fetchWorkflowStatus();
  }, [workflowId]);

  const fetchWorkflowStatus = async () => {
    try {
      const response = await fetch(`/api/v1/workflow/${workflowId}/status`);
      if (!response.ok) {
        throw new Error('Failed to fetch workflow status');
      }
      
      const data = await response.json();
      setWorkflowStatus(data);
      
      // Initialize strategies with recommended values
      if (data.analysis_results?.field_details) {
        const initialStrategies: Record<string, FieldStrategy> = {};
        data.analysis_results.field_details.forEach((field: FieldDetail) => {
          initialStrategies[field.name] = {
            field_name: field.name,
            strategy: (field.strategy as any) || 'sdv_preserve_distribution',
          };
        });
        setStrategies(initialStrategies);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleStrategyChange = (fieldName: string, strategy: string) => {
    setStrategies(prev => {
      const newStrategy = {
        ...prev[fieldName],
        strategy: strategy as any,
        custom_params: undefined,
      };

      // Pre-fill examples if switching to bedrock_examples
      if (strategy === 'bedrock_examples') {
        const sampleValues = getSampleValuesForField(fieldName);
        if (sampleValues.length > 0) {
          newStrategy.custom_params = {
            examples: sampleValues.join('\n'),
          };
        }
      }

      return {
        ...prev,
        [fieldName]: newStrategy,
      };
    });
  };

  const getSampleValuesForField = (fieldName: string): string[] => {
    if (!workflowStatus?.analysis_results?.sample_data) return [];
    
    const sampleData = workflowStatus.analysis_results.sample_data;
    const values: any[] = [];
    
    // Extract values for this field from sample data
    for (const row of sampleData) {
      if (row[fieldName] !== null && row[fieldName] !== undefined) {
        values.push(row[fieldName]);
      }
    }
    
    // Get 3 random unique values
    const uniqueValues = [...new Set(values.map(v => String(v)))];
    const shuffled = uniqueValues.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 3);
  };

  const handleExamplesChange = (fieldName: string, examples: string) => {
    setStrategies(prev => ({
      ...prev,
      [fieldName]: {
        ...prev[fieldName],
        custom_params: {
          ...prev[fieldName]?.custom_params,
          examples: examples,
        },
      },
    }));
  };

  const handleBulkStrategyChange = (strategy: string, fieldType: 'sensitive' | 'non_sensitive' | 'all') => {
    if (!workflowStatus?.analysis_results?.field_details) return;
    
    const updatedStrategies = { ...strategies };
    
    workflowStatus.analysis_results.field_details.forEach((field: FieldDetail) => {
      const shouldUpdate = 
        fieldType === 'all' ||
        (fieldType === 'sensitive' && field.is_sensitive) ||
        (fieldType === 'non_sensitive' && !field.is_sensitive);
      
      if (shouldUpdate) {
        updatedStrategies[field.name] = {
          ...updatedStrategies[field.name],
          strategy: strategy as any,
        };
      }
    });
    
    setStrategies(updatedStrategies);
  };

  const getBedrockFields = (): string[] => {
    return Object.entries(strategies)
      .filter(([_, strategy]) => 
        strategy.strategy === 'bedrock_llm' || strategy.strategy === 'bedrock_examples'
      )
      .map(([fieldName, _]) => fieldName);
  };

  const getFieldExamples = (): Record<string, string[]> => {
    const examples: Record<string, string[]> = {};
    Object.entries(strategies).forEach(([fieldName, strategy]) => {
      if (strategy.strategy === 'bedrock_examples' && strategy.custom_params?.examples) {
        const exampleText = strategy.custom_params.examples as string;
        examples[fieldName] = exampleText.split('\n').filter(line => line.trim());
      }
    });
    return examples;
  };

  const handleSubmit = async () => {
    if (!workflowId) return;
    
    setSubmitting(true);
    try {
      const strategyList = Object.values(strategies);
      
      const response = await fetch(`/api/v1/workflow/${workflowId}/strategy-selection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          field_strategies: strategyList,
          sdv_model: sdvModel,
          sdv_params: sdvParams,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to submit strategy selection');
      }
      
      // Navigate back to workflow page
      navigate(`/workflow/${workflowId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit strategies');
    } finally {
      setSubmitting(false);
    }
  };

  const getStrategyInfo = (strategyValue: string) => {
    return STRATEGY_OPTIONS.find(opt => opt.value === strategyValue);
  };

  const getSensitiveFieldCount = () => {
    return workflowStatus?.analysis_results?.sensitive_fields || 0;
  };

  const getTotalFieldCount = () => {
    return workflowStatus?.analysis_results?.total_fields || 0;
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading workflow analysis...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate(`/workflow/${workflowId}`)}
          sx={{ mt: 2 }}
        >
          Back to Workflow
        </Button>
      </Box>
    );
  }

  if (!workflowStatus?.analysis_results) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          No analysis results found for this workflow.
        </Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate(`/workflow/${workflowId}`)}
          sx={{ mt: 2 }}
        >
          Back to Workflow
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate(`/workflow/${workflowId}`)} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Box>
          <Typography variant="h4" gutterBottom>
            Configure Synthesis Strategies
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Workflow: {workflowId}
          </Typography>
        </Box>
      </Box>

      {/* Summary */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Analysis Summary
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary">
                {getTotalFieldCount()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Fields
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="error">
                {getSensitiveFieldCount()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sensitive Fields
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="success.main">
                {getTotalFieldCount() - getSensitiveFieldCount()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Non-Sensitive Fields
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Bulk Actions */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Bulk Actions
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            onClick={() => handleBulkStrategyChange('bedrock_llm', 'sensitive')}
          >
            Bedrock for All Sensitive
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleBulkStrategyChange('sdv_preserve_distribution', 'non_sensitive')}
          >
            SDV for All Non-Sensitive
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleBulkStrategyChange('sdv_preserve_distribution', 'all')}
          >
            SDV for All Fields
          </Button>
        </Box>
      </Paper>

      {/* SDV Model Configuration */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          SDV Model Configuration
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Choose the SDV model and configure its parameters. Different models have different strengths and parameter options.
        </Typography>
        
        <Grid container spacing={3}>
          {/* Model Selection */}
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>SDV Model</InputLabel>
              <Select
                value={sdvModel}
                label="SDV Model"
                onChange={(e) => setSdvModel(e.target.value)}
              >
                <MenuItem value="gaussian_copula">
                  <Box>
                    <Typography variant="body1">Gaussian Copula</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Fast, statistical model. Best for: numerical data, simple distributions
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="ctgan">
                  <Box>
                    <Typography variant="body1">CTGAN</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Neural network model. Best for: complex patterns, mixed data types
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="copula_gan">
                  <Box>
                    <Typography variant="body1">CopulaGAN</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Hybrid model. Best for: complex correlations, high-quality synthesis
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Neural Network Parameters (CTGAN, CopulaGAN only) */}
          {(sdvModel === 'ctgan' || sdvModel === 'copula_gan') && (
            <>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Neural Network Training Parameters
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Training Epochs"
                  type="number"
                  value={sdvParams.epochs || 300}
                  onChange={(e) => setSdvParams({ ...sdvParams, epochs: parseInt(e.target.value) || 300 })}
                  helperText="Number of training iterations. Higher values improve quality but take longer. Recommended: 300-500"
                  inputProps={{ min: 100, max: 1000, step: 50 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Batch Size"
                  type="number"
                  value={sdvParams.batch_size || 500}
                  onChange={(e) => setSdvParams({ ...sdvParams, batch_size: parseInt(e.target.value) || 500 })}
                  helperText="Number of samples per training batch. Recommended: 500"
                  inputProps={{ min: 100, max: 2000, step: 100 }}
                />
              </Grid>
            </>
          )}

          {/* Gaussian Copula Parameters */}
          {sdvModel === 'gaussian_copula' && (
            <>
              <Grid item xs={12}>
                <Alert severity="info">
                  Gaussian Copula is a statistical model that doesn't require training epochs. 
                  It's fast and works well for numerical data with simple distributions.
                </Alert>
              </Grid>
            </>
          )}
        </Grid>
      </Paper>

      {/* Field Strategy Selection */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Field-Level Strategy Selection
        </Typography>
        <Grid container spacing={2}>
          {workflowStatus.analysis_results.field_details.map((field: FieldDetail) => (
            <Grid item xs={12} key={field.name}>
              <Card
                variant="outlined"
                sx={{
                  borderLeft: field.is_sensitive ? '4px solid #f44336' : '4px solid #4caf50',
                }}
              >
                <CardContent>
                  <Grid container spacing={2} alignItems="center">
                    {/* Field Info */}
                    <Grid item xs={12} md={4}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {field.name}
                        </Typography>
                        {field.is_sensitive ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Security color="error" fontSize="small" />
                            <Typography variant="body2" color="error">
                              Sensitive: {field.sensitivity_type}
                            </Typography>
                          </Box>
                        ) : (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <CheckCircle color="success" fontSize="small" />
                            <Typography variant="body2" color="success.main">
                              Non-sensitive
                            </Typography>
                          </Box>
                        )}
                        <Typography variant="body2" color="text.secondary">
                          Confidence: {Math.round(field.confidence * 100)}%
                        </Typography>
                      </Box>
                    </Grid>

                    {/* Strategy Selection */}
                    <Grid item xs={12} md={4}>
                      <FormControl fullWidth>
                        <InputLabel>Synthesis Strategy</InputLabel>
                        <Select
                          value={strategies[field.name]?.strategy || 'sdv_preserve_distribution'}
                          onChange={(e) => handleStrategyChange(field.name, e.target.value)}
                          label="Synthesis Strategy"
                        >
                          {STRATEGY_OPTIONS.map((option) => (
                            <MenuItem key={option.value} value={option.value}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {option.icon}
                                {option.label}
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    {/* Strategy Info */}
                    <Grid item xs={12} md={4}>
                      <Box>
                        {strategies[field.name] && (
                          <>
                            <Typography variant="body2" gutterBottom>
                              {getStrategyInfo(strategies[field.name].strategy)?.description}
                            </Typography>
                            <Tooltip title="View strategy details">
                              <IconButton
                                size="small"
                                onClick={() => setShowStrategyInfo(strategies[field.name].strategy)}
                              >
                                <Info />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                      </Box>
                    </Grid>
                  </Grid>

                  {/* Examples Input for bedrock_examples strategy */}
                  {strategies[field.name]?.strategy === 'bedrock_examples' && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="Example Values (one per line)"
                        placeholder="Enter 5-10 example values, one per line&#10;Example:&#10;PROD-2024-001&#10;PROD-2024-002&#10;DEV-2024-003"
                        value={strategies[field.name]?.custom_params?.examples || ''}
                        onChange={(e) => handleExamplesChange(field.name, e.target.value)}
                        helperText="Provide at least 3 example values. AI will analyze the pattern and generate similar values."
                        variant="outlined"
                      />
                    </Box>
                  )}

                  {/* Reasoning */}
                  {field.reasoning && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Analysis:</strong> {field.reasoning}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Cost Estimation */}
      {getBedrockFields().length > 0 && (
        <Box sx={{ mb: 3 }}>
          <CostEstimationPanel
            numRecords={workflowStatus.num_records || 1000}
            bedrockFields={getBedrockFields()}
            fieldExamples={getFieldExamples()}
          />
        </Box>
      )}

      {/* Submit Actions */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBack />}
            onClick={() => navigate(`/workflow/${workflowId}`)}
          >
            Back to Workflow
          </Button>
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit}
            disabled={submitting}
            sx={{ minWidth: 200 }}
          >
            {submitting ? 'Applying Strategies...' : 'Apply Strategies & Continue'}
          </Button>
        </Box>
      </Paper>

      {/* Strategy Info Dialog */}
      <Dialog
        open={!!showStrategyInfo}
        onClose={() => setShowStrategyInfo(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Strategy Details
        </DialogTitle>
        <DialogContent>
          {showStrategyInfo && (
            <Box>
              {(() => {
                const strategy = getStrategyInfo(showStrategyInfo);
                return strategy ? (
                  <>
                    <Typography variant="h6" gutterBottom>
                      {strategy.label}
                    </Typography>
                    <Typography variant="body1" paragraph>
                      {strategy.description}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom>
                      Best for:
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {strategy.bestFor.map((item) => (
                        <Chip key={item} label={item} size="small" />
                      ))}
                    </Box>
                  </>
                ) : null;
              })()}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowStrategyInfo(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategySelectionPage;
