/**
 * Pre-configured demo scenarios for guided demonstrations
 */

import { DemoScenario } from '../types/demo';

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'telecom-demo',
    name: 'Telecommunications Data Testing',
    description: 'Demonstrate synthetic data generation for telecom customer records with PII protection',
    industry: 'telecom',
    estimatedDuration: 300, // 5 minutes
    highlights: [
      'Automatic PII detection in customer records',
      'Preservation of data quality issues (malformed phone numbers)',
      'Statistical distribution matching for usage patterns',
      'Integration with test automation frameworks'
    ],
    config: {
      name: 'Telecom Demo Workflow',
      description: 'Generate synthetic telecom customer data',
      schema_fields: [
        { name: 'customer_id', type: 'string' },
        { name: 'name', type: 'string' },
        { name: 'email', type: 'string' },
        { name: 'phone', type: 'string' },
        { name: 'address', type: 'string' },
        { name: 'data_usage_gb', type: 'number' },
        { name: 'call_minutes', type: 'number' },
        { name: 'account_balance', type: 'number' }
      ],
      generation_params: {
        num_records: 1000,
        preserve_edge_cases: true
      },
      sdv_model: 'gaussian_copula',
      bedrock_model: 'anthropic.claude-3-sonnet',
      edge_case_frequency: 0.05,
      target_systems: [
        {
          type: 'database',
          name: 'Test Database',
          config: { connection_string: 'mock://testdb' }
        }
      ]
    },
    steps: [
      {
        id: 'step-1',
        title: 'Load Production Data',
        description: 'Loading sample telecom customer data from production',
        narration: 'We start by loading a sample of production customer data. This data contains real customer information including names, emails, phone numbers, and usage patterns. Notice the file contains 50+ columns of complex telecom data.',
        duration: 5,
        callouts: [
          {
            id: 'callout-1-1',
            type: 'info',
            position: { x: 100, y: 100 },
            title: 'Production Data Source',
            content: 'Sample contains 10,000 real customer records with sensitive PII that must be protected.'
          },
          {
            id: 'callout-1-2',
            type: 'highlight',
            position: { x: 300, y: 150 },
            title: 'Data Quality Issues',
            content: 'Notice some phone numbers are malformed and some emails are invalid - we\'ll preserve these patterns in synthetic data.'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-2',
        title: 'Analyze Sensitive Fields',
        description: 'Data Processor Agent identifies PII fields',
        narration: 'The Data Processor Agent now analyzes each field to identify sensitive personal information. It uses multiple classification strategies: pattern matching for emails and phones, name-based detection, and content analysis. For ambiguous fields, it queries our Confluence knowledge base.',
        agent: 'data_processor',
        duration: 10,
        callouts: [
          {
            id: 'callout-2-1',
            type: 'decision',
            position: { x: 150, y: 200 },
            title: 'Classification Strategy',
            content: 'Using 4 classifiers: Pattern (regex), Name-based, Content Analysis, and Confluence Knowledge'
          },
          {
            id: 'callout-2-2',
            type: 'metric',
            position: { x: 400, y: 180 },
            title: 'Sensitivity Scores',
            content: 'Fields with confidence > 0.7 are marked as sensitive: name (0.95), email (0.98), phone (0.92), address (0.88)'
          },
          {
            id: 'callout-2-3',
            type: 'highlight',
            position: { x: 250, y: 300 },
            title: 'Confluence Integration',
            content: 'Querying internal documentation for field "account_status" - found data dictionary confirming it\'s non-sensitive'
          }
        ],
        dataTransformation: {
          before: {
            customer_id: 'CUST-12345',
            name: 'John Smith',
            email: 'john.smith@example.com',
            classification: 'unknown'
          },
          after: {
            customer_id: 'CUST-12345',
            name: 'John Smith [SENSITIVE]',
            email: 'john.smith@example.com [SENSITIVE]',
            classification: 'sensitive'
          },
          changes: [
            {
              field: 'name',
              oldValue: 'unknown',
              newValue: 'sensitive (confidence: 0.95)',
              reason: 'Pattern match + name-based classifier'
            },
            {
              field: 'email',
              oldValue: 'unknown',
              newValue: 'sensitive (confidence: 0.98)',
              reason: 'Email regex pattern match'
            }
          ],
          reasoning: 'These fields contain personally identifiable information and must be replaced with synthetic values'
        },
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-2.5',
        title: 'Select Synthesis Strategies',
        description: 'Choose generation method for each field',
        narration: 'Before generating data, we select the synthesis strategy for each field. Sensitive text fields like names and emails will use Bedrock LLM for realistic generation. Numerical fields like usage and balance will use SDV to preserve statistical distributions. The system estimates the cost: approximately $0.25 for 1,000 records with 4 Bedrock fields using Claude Haiku.',
        duration: 8,
        callouts: [
          {
            id: 'callout-2.5-1',
            type: 'decision',
            position: { x: 150, y: 180 },
            title: 'Strategy Selection',
            content: 'Bedrock LLM: name, email, address, phone | SDV: data_usage_gb, call_minutes, account_balance'
          },
          {
            id: 'callout-2.5-2',
            type: 'metric',
            position: { x: 350, y: 220 },
            title: 'Cost Estimation',
            content: 'Estimated cost: $0.25 (4 Bedrock fields × 1,000 records × Claude Haiku pricing)'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-3',
        title: 'Generate Synthetic Data',
        description: 'Synthetic Data Agent creates GDPR-compliant replacements',
        narration: 'Now the Synthetic Data Agent generates synthetic replacements using the selected strategies. For tabular data like usage patterns and account balances, we use SDV\'s GaussianCopula model to preserve statistical distributions. For text fields like names and addresses, we use Amazon Bedrock\'s Claude Haiku model to generate realistic, contextually appropriate values.',
        agent: 'synthetic_data',
        duration: 15,
        callouts: [
          {
            id: 'callout-3-1',
            type: 'info',
            position: { x: 120, y: 150 },
            title: 'Dual Generation Strategy',
            content: 'SDV for numerical/categorical fields, Bedrock LLM for text fields'
          },
          {
            id: 'callout-3-2',
            type: 'metric',
            position: { x: 350, y: 200 },
            title: 'Statistical Preservation',
            content: 'Correlation between data_usage_gb and call_minutes preserved: Original 0.73 → Synthetic 0.71'
          },
          {
            id: 'callout-3-3',
            type: 'highlight',
            position: { x: 200, y: 320 },
            title: 'Edge Case Preservation',
            content: 'Maintaining 5% malformed phone numbers as specified, ensuring realistic test scenarios'
          }
        ],
        dataTransformation: {
          before: {
            name: 'John Smith',
            email: 'john.smith@example.com',
            phone: '+1-555-0123',
            data_usage_gb: 15.3
          },
          after: {
            name: 'Emma Rodriguez',
            email: 'emma.rodriguez@techmail.com',
            phone: '+1-555-8742',
            data_usage_gb: 14.8
          },
          changes: [
            {
              field: 'name',
              oldValue: 'John Smith',
              newValue: 'Emma Rodriguez',
              reason: 'Generated by Bedrock with diverse name distribution'
            },
            {
              field: 'email',
              oldValue: 'john.smith@example.com',
              newValue: 'emma.rodriguez@techmail.com',
              reason: 'Generated to match name context'
            },
            {
              field: 'data_usage_gb',
              oldValue: 15.3,
              newValue: 14.8,
              reason: 'Sampled from learned distribution (mean: 15.1, std: 8.2)'
            }
          ],
          reasoning: 'All PII replaced while maintaining statistical properties and realistic relationships'
        },
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-4',
        title: 'Validate Quality',
        description: 'Measuring statistical similarity between production and synthetic data',
        narration: 'Quality validation is critical. We use SDV quality metrics to measure how well the synthetic data matches the production data. The Column Shapes score measures distribution similarity, Column Pair Trends measures relationship preservation. We also evaluate Data Validity (checking for invalid values) and Data Structure (verifying data types). Privacy metrics using nearest neighbor distances confirm the synthetic data is sufficiently different from original records.',
        duration: 8,
        callouts: [
          {
            id: 'callout-4-1',
            type: 'metric',
            position: { x: 150, y: 180 },
            title: 'SDV Quality Score',
            content: 'Overall Quality: 0.87 (Excellent) - Column Shapes: 0.89, Column Pair Trends: 0.85'
          },
          {
            id: 'callout-4-2',
            type: 'metric',
            position: { x: 380, y: 220 },
            title: 'Diagnostic Metrics',
            content: 'Data Validity: 0.95, Data Structure: 0.98 - All values valid and properly formatted'
          },
          {
            id: 'callout-4-3',
            type: 'info',
            position: { x: 250, y: 320 },
            title: 'Privacy Analysis',
            content: 'Nearest neighbor distance: 0.12 (Good) - Synthetic data is sufficiently different from originals'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-5',
        title: 'Distribute to Test Systems',
        description: 'Distribution Agent loads data into target systems',
        narration: 'The Distribution Agent now loads the synthetic data into our test database. It handles foreign key constraints by loading tables in topological order. For this demo, we\'re using a mock database, but in production this would connect to PostgreSQL, MySQL, Salesforce, or REST APIs.',
        agent: 'distribution',
        duration: 7,
        callouts: [
          {
            id: 'callout-5-1',
            type: 'info',
            position: { x: 180, y: 160 },
            title: 'Smart Loading',
            content: 'Automatically detects foreign key dependencies and loads in correct order'
          },
          {
            id: 'callout-5-2',
            type: 'metric',
            position: { x: 350, y: 200 },
            title: 'Load Performance',
            content: '1,000 records loaded in 2.3 seconds using batch inserts'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-6',
        title: 'Generate Test Cases',
        description: 'Test Case Agent creates executable tests from Jira scenarios',
        narration: 'The Test Case Agent retrieves test scenarios from Jira and generates executable test code. It uses Bedrock to convert high-level test descriptions into Robot Framework, Selenium, or Playwright scripts. The generated tests reference specific synthetic data records.',
        agent: 'test_case',
        duration: 10,
        callouts: [
          {
            id: 'callout-6-1',
            type: 'info',
            position: { x: 150, y: 180 },
            title: 'Jira Integration',
            content: 'Retrieved 5 test scenarios tagged "telecom-regression"'
          },
          {
            id: 'callout-6-2',
            type: 'highlight',
            position: { x: 350, y: 220 },
            title: 'AI-Generated Tests',
            content: 'Bedrock converts scenario "Verify customer can update profile" into 45 lines of executable Playwright code'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'step-7',
        title: 'Execute Tests',
        description: 'Test Execution Agent runs automated tests',
        narration: 'Finally, the Test Execution Agent runs the generated tests in parallel. It captures logs, screenshots on failure, and performance metrics. Results are automatically synced back to Jira, creating issues for any failures.',
        agent: 'test_execution',
        duration: 12,
        callouts: [
          {
            id: 'callout-7-1',
            type: 'metric',
            position: { x: 180, y: 160 },
            title: 'Test Results',
            content: '5 tests executed: 4 passed, 1 failed - Execution time: 8.2 seconds'
          },
          {
            id: 'callout-7-2',
            type: 'highlight',
            position: { x: 350, y: 220 },
            title: 'Jira Integration',
            content: 'Created issue TELECOM-1234 for failed test with logs and screenshot attached'
          }
        ],
        pausePoint: false,
        autoAdvance: true
      },
      {
        id: 'step-8',
        title: 'Demo Complete',
        description: 'Review results and cost breakdown',
        narration: 'The workflow is complete! We\'ve gone from production data to synthetic data to executed tests, all automatically. The actual cost was $0.24, very close to our $0.25 estimate. The cost is tracked throughout the workflow and visible in the workflow list. You can now export the synthetic data, quality reports, and test results.',
        duration: 5,
        callouts: [
          {
            id: 'callout-8-1',
            type: 'metric',
            position: { x: 200, y: 180 },
            title: 'Actual vs Estimated Cost',
            content: 'Estimated: $0.25 | Actual: $0.24 (Bedrock: $0.22, ECS: $0.02) - 96% accuracy!'
          },
          {
            id: 'callout-8-2',
            type: 'info',
            position: { x: 350, y: 240 },
            title: 'Export Options',
            content: 'Download synthetic data as CSV, JSON, or Parquet. View detailed quality metrics with privacy analysis.'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      }
    ]
  },
  {
    id: 'finance-demo',
    name: 'Financial Services Data Testing',
    description: 'Generate synthetic financial transaction data with fraud patterns',
    industry: 'finance',
    estimatedDuration: 280,
    highlights: [
      'Credit card number masking and generation',
      'Fraud pattern preservation',
      'Regulatory compliance (PCI-DSS)',
      'Transaction correlation analysis'
    ],
    config: {
      name: 'Finance Demo Workflow',
      description: 'Generate synthetic financial transaction data',
      schema_fields: [
        { name: 'transaction_id', type: 'string' },
        { name: 'customer_name', type: 'string' },
        { name: 'card_number', type: 'string' },
        { name: 'amount', type: 'number' },
        { name: 'merchant', type: 'string' },
        { name: 'transaction_date', type: 'date' },
        { name: 'is_fraud', type: 'boolean' }
      ],
      generation_params: {
        num_records: 5000,
        preserve_edge_cases: true
      },
      sdv_model: 'ctgan',
      bedrock_model: 'anthropic.claude-3-sonnet',
      edge_case_frequency: 0.02,
      target_systems: [
        {
          type: 'database',
          name: 'Finance Test DB',
          config: { connection_string: 'mock://financedb' }
        }
      ]
    },
    steps: [
      {
        id: 'fin-step-1',
        title: 'Load Financial Data',
        description: 'Loading transaction history with fraud indicators',
        narration: 'We begin with real financial transaction data including credit card numbers, customer information, and fraud labels. This data is highly sensitive and subject to PCI-DSS compliance requirements.',
        duration: 5,
        callouts: [
          {
            id: 'fin-callout-1-1',
            type: 'highlight',
            position: { x: 120, y: 120 },
            title: 'Sensitive Financial Data',
            content: 'Contains credit card numbers, transaction amounts, and fraud indicators'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'fin-step-2',
        title: 'Detect PCI-DSS Fields',
        description: 'Identifying payment card industry data',
        narration: 'The Data Processor Agent identifies PCI-DSS regulated fields like credit card numbers. These require special handling with Luhn algorithm validation for synthetic generation.',
        agent: 'data_processor',
        duration: 8,
        callouts: [
          {
            id: 'fin-callout-2-1',
            type: 'decision',
            position: { x: 180, y: 180 },
            title: 'PCI-DSS Detection',
            content: 'Card numbers detected with 0.99 confidence using Luhn algorithm validation'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      },
      {
        id: 'fin-step-3',
        title: 'Generate Synthetic Transactions',
        description: 'Creating compliant synthetic financial data',
        narration: 'Synthetic card numbers are generated using the Luhn algorithm to ensure validity. Fraud patterns are preserved at the same 2% frequency as production data.',
        agent: 'synthetic_data',
        duration: 12,
        callouts: [
          {
            id: 'fin-callout-3-1',
            type: 'metric',
            position: { x: 200, y: 200 },
            title: 'Fraud Pattern Preservation',
            content: 'Original fraud rate: 2.1% → Synthetic fraud rate: 2.0%'
          }
        ],
        pausePoint: true,
        autoAdvance: false
      }
    ]
  }
];

export function getDemoScenario(id: string): DemoScenario | undefined {
  return DEMO_SCENARIOS.find(scenario => scenario.id === id);
}

export function getDemoScenariosByIndustry(industry: string): DemoScenario[] {
  return DEMO_SCENARIOS.filter(scenario => scenario.industry === industry);
}
