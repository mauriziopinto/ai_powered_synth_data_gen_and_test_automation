import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  Typography,
  Chip,
  Stack,
  Alert,
} from '@mui/material';
import {
  Phone as TelecomIcon,
  AccountBalance as FinanceIcon,
  LocalHospital as HealthcareIcon,
} from '@mui/icons-material';
import { WorkflowConfig } from '../../types';

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  tags: string[];
  config: Partial<WorkflowConfig>;
}

interface DemoScenarioSelectorProps {
  onSelect: (config: Partial<WorkflowConfig>) => void;
  selectedScenario?: string;
}

const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'telecom',
    name: 'Telecommunications',
    description: 'Mobile gateway data with call records, subscriber information, and network metrics. Includes edge cases like malformed phone numbers and missing payment data.',
    icon: TelecomIcon,
    color: '#2196f3',
    tags: ['CDR', 'Subscribers', 'Network'],
    config: {
      name: 'Telecom Demo - MGW Data',
      description: 'Pre-configured scenario for telecommunications testing with mobile gateway file data',
      schema_fields: [
        { name: 'subscriber_id', type: 'string', constraints: { pattern: '^[0-9]{10}$' } },
        { name: 'phone_number', type: 'phone', constraints: {} },
        { name: 'call_duration', type: 'integer', constraints: { min: 0, max: 86400 } },
        { name: 'call_type', type: 'string', constraints: { enum: ['voice', 'sms', 'data'] } },
        { name: 'timestamp', type: 'datetime', constraints: {} },
        { name: 'cell_tower_id', type: 'string', constraints: {} },
        { name: 'data_usage_mb', type: 'float', constraints: { min: 0 } },
        { name: 'billing_amount', type: 'float', constraints: { min: 0 } },
      ],
      generation_params: {},
      sdv_model: 'gaussian_copula',
      bedrock_model: 'anthropic.claude-3-haiku-20240307-v1:0',
      edge_case_frequency: 0.15,
      target_systems: [
        {
          type: 'database',
          name: 'Test Database',
          config: {
            db_type: 'postgresql',
            host: 'localhost',
            port: '5432',
            database: 'telecom_test',
            load_strategy: 'truncate_insert',
          },
        },
      ],
    },
  },
  {
    id: 'finance',
    name: 'Financial Services',
    description: 'Banking transactions, customer accounts, and payment processing data. Tests fraud detection and compliance scenarios with realistic financial patterns.',
    icon: FinanceIcon,
    color: '#4caf50',
    tags: ['Transactions', 'Accounts', 'Compliance'],
    config: {
      name: 'Finance Demo - Banking Data',
      description: 'Pre-configured scenario for financial services testing',
      schema_fields: [
        { name: 'account_id', type: 'uuid', constraints: {} },
        { name: 'customer_name', type: 'string', constraints: {} },
        { name: 'account_type', type: 'string', constraints: { enum: ['checking', 'savings', 'credit'] } },
        { name: 'balance', type: 'float', constraints: { min: -10000, max: 1000000 } },
        { name: 'transaction_id', type: 'uuid', constraints: {} },
        { name: 'transaction_amount', type: 'float', constraints: {} },
        { name: 'transaction_date', type: 'datetime', constraints: {} },
        { name: 'merchant_name', type: 'string', constraints: {} },
        { name: 'card_number', type: 'string', constraints: { pattern: '^[0-9]{16}$' } },
      ],
      generation_params: {},
      sdv_model: 'ctgan',
      bedrock_model: 'anthropic.claude-3-sonnet-20240229-v1:0',
      edge_case_frequency: 0.1,
      target_systems: [
        {
          type: 'database',
          name: 'Finance Test DB',
          config: {
            db_type: 'postgresql',
            host: 'localhost',
            port: '5432',
            database: 'finance_test',
            load_strategy: 'upsert',
          },
        },
      ],
    },
  },
  {
    id: 'healthcare',
    name: 'Healthcare',
    description: 'Patient records, appointments, and medical billing data. HIPAA-compliant synthetic data generation with realistic medical terminology and codes.',
    icon: HealthcareIcon,
    color: '#f44336',
    tags: ['Patients', 'HIPAA', 'Medical Records'],
    config: {
      name: 'Healthcare Demo - Patient Data',
      description: 'Pre-configured scenario for healthcare testing with HIPAA compliance',
      schema_fields: [
        { name: 'patient_id', type: 'uuid', constraints: {} },
        { name: 'patient_name', type: 'string', constraints: {} },
        { name: 'date_of_birth', type: 'date', constraints: {} },
        { name: 'ssn', type: 'string', constraints: { pattern: '^[0-9]{3}-[0-9]{2}-[0-9]{4}$' } },
        { name: 'diagnosis_code', type: 'string', constraints: {} },
        { name: 'procedure_code', type: 'string', constraints: {} },
        { name: 'appointment_date', type: 'datetime', constraints: {} },
        { name: 'provider_name', type: 'string', constraints: {} },
        { name: 'insurance_id', type: 'string', constraints: {} },
        { name: 'billing_amount', type: 'float', constraints: { min: 0 } },
      ],
      generation_params: {},
      sdv_model: 'copula_gan',
      bedrock_model: 'anthropic.claude-3-sonnet-20240229-v1:0',
      edge_case_frequency: 0.05,
      target_systems: [
        {
          type: 'database',
          name: 'Healthcare Test DB',
          config: {
            db_type: 'postgresql',
            host: 'localhost',
            port: '5432',
            database: 'healthcare_test',
            load_strategy: 'truncate_insert',
          },
        },
      ],
    },
  },
];

export default function DemoScenarioSelector({ onSelect, selectedScenario }: DemoScenarioSelectorProps) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Guided Demo Scenarios
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Select a pre-configured demo scenario to quickly get started. Each scenario includes sample data,
        appropriate models, and target system configurations.
      </Alert>

      <Grid container spacing={3}>
        {DEMO_SCENARIOS.map((scenario) => {
          const Icon = scenario.icon;
          const isSelected = selectedScenario === scenario.id;

          return (
            <Grid item xs={12} md={4} key={scenario.id}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  borderColor: isSelected ? scenario.color : undefined,
                  borderWidth: isSelected ? 2 : 1,
                }}
              >
                <CardActionArea onClick={() => onSelect(scenario.config)} sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Icon sx={{ fontSize: 40, color: scenario.color, mr: 2 }} />
                      <Typography variant="h6">{scenario.name}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 80 }}>
                      {scenario.description}
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {scenario.tags.map((tag) => (
                        <Chip key={tag} label={tag} size="small" sx={{ mb: 1 }} />
                      ))}
                    </Stack>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
