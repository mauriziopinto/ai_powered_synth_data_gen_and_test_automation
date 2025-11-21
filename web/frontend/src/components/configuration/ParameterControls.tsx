
import {
  Box,
  Card,
  CardContent,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Switch,
  TextField,
  Typography,
  Tooltip,
  IconButton,
} from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';

interface ParameterControlsProps {
  params: {
    sdv_model: string;
    bedrock_model: string;
    num_records: number;
    edge_case_frequency: number;
    preserve_edge_cases: boolean;
    random_seed?: number;
    temperature?: number;
    max_tokens?: number;
  };
  onChange: (params: any) => void;
  errors?: Record<string, string>;
}

const SDV_MODELS = [
  { value: 'gaussian_copula', label: 'Gaussian Copula', description: 'Fast, good for normally distributed data' },
  { value: 'ctgan', label: 'CTGAN', description: 'Deep learning, handles complex distributions' },
  { value: 'copula_gan', label: 'Copula GAN', description: 'Hybrid approach, best quality' },
];

const BEDROCK_MODELS = [
  { value: 'anthropic.claude-3-sonnet-20240229-v1:0', label: 'Claude 3 Sonnet', description: 'Balanced performance and cost' },
  { value: 'anthropic.claude-3-haiku-20240307-v1:0', label: 'Claude 3 Haiku', description: 'Fast and cost-effective' },
  { value: 'anthropic.claude-3-opus-20240229-v1:0', label: 'Claude 3 Opus', description: 'Highest quality' },
];

export default function ParameterControls({ params, onChange, errors = {} }: ParameterControlsProps) {
  const handleChange = (field: string, value: any) => {
    onChange({ ...params, [field]: value });
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Generation Parameters
      </Typography>

      <Grid container spacing={3}>
        {/* SDV Model Selection */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" sx={{ flex: 1 }}>
                  SDV Model
                </Typography>
                <Tooltip title="Statistical model for generating tabular data">
                  <IconButton size="small">
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              <FormControl fullWidth error={!!errors.sdv_model}>
                <InputLabel>Model Type</InputLabel>
                <Select
                  value={params.sdv_model}
                  label="Model Type"
                  onChange={(e) => handleChange('sdv_model', e.target.value)}
                >
                  {SDV_MODELS.map((model) => (
                    <MenuItem key={model.value} value={model.value}>
                      <Box>
                        <Typography variant="body2">{model.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {model.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.sdv_model && <FormHelperText>{errors.sdv_model}</FormHelperText>}
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Bedrock Model Selection */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" sx={{ flex: 1 }}>
                  Bedrock LLM
                </Typography>
                <Tooltip title="Model for generating realistic text fields">
                  <IconButton size="small">
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              <FormControl fullWidth error={!!errors.bedrock_model}>
                <InputLabel>Model Type</InputLabel>
                <Select
                  value={params.bedrock_model}
                  label="Model Type"
                  onChange={(e) => handleChange('bedrock_model', e.target.value)}
                >
                  {BEDROCK_MODELS.map((model) => (
                    <MenuItem key={model.value} value={model.value}>
                      <Box>
                        <Typography variant="body2">{model.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {model.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.bedrock_model && <FormHelperText>{errors.bedrock_model}</FormHelperText>}
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Number of Records */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Number of Records
              </Typography>
              <TextField
                type="number"
                fullWidth
                value={params.num_records}
                onChange={(e) => {
                  const value = e.target.value === '' ? '' : parseInt(e.target.value);
                  handleChange('num_records', value === '' ? 1 : (isNaN(value as number) ? 1 : value));
                }}
                error={!!errors.num_records}
                helperText={errors.num_records || 'Number of synthetic records to generate'}
                inputProps={{ min: 1, max: 1000000 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Edge Case Frequency */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" sx={{ flex: 1 }}>
                  Edge Case Frequency
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {(params.edge_case_frequency * 100).toFixed(0)}%
                </Typography>
              </Box>
              <Slider
                value={params.edge_case_frequency}
                onChange={(_, value) => handleChange('edge_case_frequency', value)}
                min={0}
                max={0.5}
                step={0.01}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 0.1, label: '10%' },
                  { value: 0.25, label: '25%' },
                  { value: 0.5, label: '50%' },
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <FormHelperText>
                Percentage of records with injected edge cases (malformed data, boundary values)
              </FormHelperText>
            </CardContent>
          </Card>
        </Grid>

        {/* Advanced Options */}
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Advanced Options
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={params.preserve_edge_cases}
                        onChange={(e) => handleChange('preserve_edge_cases', e.target.checked)}
                      />
                    }
                    label="Preserve Edge Cases"
                  />
                  <FormHelperText>
                    Maintain edge cases from production data
                  </FormHelperText>
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    type="number"
                    label="Random Seed (optional)"
                    fullWidth
                    value={params.random_seed || ''}
                    onChange={(e) => handleChange('random_seed', e.target.value ? parseInt(e.target.value) : undefined)}
                    helperText="For reproducible generation"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    type="number"
                    label="Temperature"
                    fullWidth
                    value={params.temperature || 0.9}
                    onChange={(e) => handleChange('temperature', parseFloat(e.target.value) || 0.9)}
                    inputProps={{ min: 0, max: 1, step: 0.1 }}
                    helperText="LLM creativity (0-1)"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
