/**
 * Cost Estimation Panel Component
 * 
 * Displays estimated Bedrock costs before synthetic data generation
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  Grid,
  Divider,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  AttachMoney,
  Info,
  Warning,
  CheckCircle,
} from '@mui/icons-material';

interface CostEstimationPanelProps {
  numRecords: number;
  bedrockFields: string[];
  fieldExamples?: Record<string, string[]>;
  modelId?: string;
}

interface CostEstimation {
  estimated_cost_usd: number;
  num_records: number;
  num_bedrock_fields: number;
  bedrock_fields: string[];
  model_id: string;
  input_tokens_estimate: number;
  output_tokens_estimate: number;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
  breakdown: {
    input_tokens_cost: number;
    output_tokens_cost: number;
    cost_per_record: number;
    cost_per_field: number;
  };
  warnings: string[];
}

const CostEstimationPanel: React.FC<CostEstimationPanelProps> = ({
  numRecords,
  bedrockFields,
  fieldExamples = {},
  modelId = 'anthropic.claude-3-haiku-20240307-v1:0',
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [estimation, setEstimation] = useState<CostEstimation | null>(null);

  useEffect(() => {
    fetchCostEstimation();
  }, [numRecords, bedrockFields, fieldExamples, modelId]);

  const fetchCostEstimation = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/cost/estimate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          num_records: numRecords,
          bedrock_fields: bedrockFields,
          field_examples: fieldExamples,
          model_id: modelId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cost estimation');
      }

      const data = await response.json();
      setEstimation(data);
    } catch (err: any) {
      console.error('Error fetching cost estimation:', err);
      setError(err.message || 'Failed to estimate costs');
    } finally {
      setLoading(false);
    }
  };

  const getCostColor = (cost: number): string => {
    if (cost < 1) return 'success.main';
    if (cost < 10) return 'warning.main';
    return 'error.main';
  };

  const getCostIcon = (cost: number) => {
    if (cost < 1) return <CheckCircle color="success" />;
    if (cost < 10) return <Warning color="warning" />;
    return <Warning color="error" />;
  };

  const formatCost = (cost: number): string => {
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    if (cost < 1) return `$${cost.toFixed(3)}`;
    return `$${cost.toFixed(2)}`;
  };

  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(2)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
    return tokens.toString();
  };

  const getModelName = (modelId: string): string => {
    if (modelId.includes('haiku')) return 'Claude 3 Haiku';
    if (modelId.includes('sonnet')) return 'Claude 3.5 Sonnet';
    if (modelId.includes('opus')) return 'Claude 3 Opus';
    return modelId;
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 2 }}>
              Calculating costs...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!estimation) {
    return null;
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <AttachMoney color="primary" />
          <Typography variant="h6">
            Estimated Bedrock Costs
          </Typography>
          <Tooltip title="Cost estimation based on token usage and current Bedrock pricing">
            <IconButton size="small">
              <Info fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
          Estimated cost for generating {numRecords.toLocaleString()} records using {estimation.num_bedrock_fields} Bedrock field(s)
        </Typography>

        {/* Total Cost */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getCostIcon(estimation.estimated_cost_usd)}
              <Typography variant="body2" color="text.secondary">
                Total Estimated Cost
              </Typography>
            </Box>
            <Typography 
              variant="h4" 
              sx={{ color: getCostColor(estimation.estimated_cost_usd), fontWeight: 'bold' }}
            >
              {formatCost(estimation.estimated_cost_usd)}
            </Typography>
          </Box>
        </Box>

        {/* Model Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Model Configuration
          </Typography>
          <Chip 
            label={getModelName(estimation.model_id)} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Cost Breakdown */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Input Tokens
              </Typography>
              <Typography variant="body2" fontWeight="medium">
                {formatTokens(estimation.input_tokens_estimate)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatCost(estimation.breakdown.input_tokens_cost)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Output Tokens
              </Typography>
              <Typography variant="body2" fontWeight="medium">
                {formatTokens(estimation.output_tokens_estimate)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatCost(estimation.breakdown.output_tokens_cost)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Cost per Record
              </Typography>
              <Typography variant="body2" fontWeight="medium">
                {formatCost(estimation.breakdown.cost_per_record)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Cost per Field
              </Typography>
              <Typography variant="body2" fontWeight="medium">
                {formatCost(estimation.breakdown.cost_per_field)}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Bedrock Fields */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Bedrock-Generated Fields ({estimation.num_bedrock_fields})
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {estimation.bedrock_fields.map((field) => (
              <Chip 
                key={field} 
                label={field} 
                size="small" 
                variant="outlined"
              />
            ))}
          </Box>
        </Box>

        {/* Warnings */}
        {estimation.warnings.length > 0 && (
          <Box sx={{ mt: 2 }}>
            {estimation.warnings.map((warning, index) => (
              <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                {warning}
              </Alert>
            ))}
          </Box>
        )}

        {/* Pricing Info */}
        <Box sx={{ mt: 2, p: 1.5, bgcolor: 'info.lighter', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary" display="block">
            <strong>Pricing:</strong> Input ${(estimation.input_cost_per_1k * 1000).toFixed(2)}/1M tokens, 
            Output ${(estimation.output_cost_per_1k * 1000).toFixed(2)}/1M tokens
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
            Actual costs may vary based on actual token usage. This is an estimate.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CostEstimationPanel;
