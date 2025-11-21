# Configuration Interface Components

This directory contains the components for the Configuration Interface (Task 28).

## Components

### SchemaBuilder
Interactive schema definition component that allows users to:
- Add/remove fields with drag-and-drop interface
- Define field types (string, integer, float, date, email, phone, etc.)
- Set constraints (min/max, patterns, enums)
- Expand/collapse field details
- Real-time validation

**Props:**
- `fields`: Array of SchemaField objects
- `onChange`: Callback when fields change
- `errors`: Validation errors object

### ParameterControls
Form for configuring generation parameters:
- SDV model selection (Gaussian Copula, CTGAN, Copula GAN)
- Bedrock LLM selection (Claude 3 models)
- Number of records to generate
- Edge case frequency slider (0-50%)
- Advanced options (preserve edge cases, random seed, temperature)

**Props:**
- `params`: Parameter object
- `onChange`: Callback when parameters change
- `errors`: Validation errors object

### TargetSystemManager
Manager for configuring target systems where synthetic data will be loaded:
- Add/edit/delete target systems
- Support for multiple target types:
  - Database (PostgreSQL, MySQL, SQL Server, Oracle)
  - Salesforce (Bulk API)
  - REST API
  - File Storage (CSV, JSON, Parquet)
- Type-specific configuration forms
- Visual icons and color coding

**Props:**
- `targets`: Array of TargetSystem objects
- `onChange`: Callback when targets change
- `errors`: Validation errors object

### DemoScenarioSelector
Pre-configured demo scenarios for quick start:
- Telecommunications (MGW data with CDR, subscribers, network metrics)
- Financial Services (banking transactions, accounts, compliance)
- Healthcare (patient records, HIPAA-compliant)
- Each scenario includes:
  - Pre-defined schema
  - Appropriate SDV/Bedrock models
  - Sample target systems
  - Realistic edge case frequencies

**Props:**
- `onSelect`: Callback when scenario is selected
- `selectedScenario`: Currently selected scenario ID

## Usage

The main ConfigurationPage integrates all these components in a 5-step wizard:

1. **Demo Scenario** - Select a pre-configured scenario or start from scratch
2. **Schema** - Define data structure and field types
3. **Parameters** - Configure generation settings and models
4. **Target Systems** - Set up data distribution targets
5. **Review** - Review and save configuration

### Example

```tsx
import {
  SchemaBuilder,
  ParameterControls,
  TargetSystemManager,
  DemoScenarioSelector,
} from '../components/configuration';

function MyConfigPage() {
  const [config, setConfig] = useState<WorkflowConfig>(DEFAULT_CONFIG);
  
  return (
    <>
      <SchemaBuilder
        fields={config.schema_fields}
        onChange={(fields) => setConfig({ ...config, schema_fields: fields })}
      />
      <ParameterControls
        params={params}
        onChange={setParams}
      />
      <TargetSystemManager
        targets={config.target_systems}
        onChange={(targets) => setConfig({ ...config, target_systems: targets })}
      />
    </>
  );
}
```

## Validation

Form validation is implemented at the step level:
- Schema: At least one field required, all fields must have names
- Parameters: Configuration name required, num_records >= 1
- Target Systems: At least one target required

Validation errors are displayed inline with helpful messages.

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 11.2**: Interactive forms for defining schemas, specifying generation parameters, configuring edge-case rules, and selecting SDV models and Bedrock LLM settings
- **Requirement 26.1**: Pre-configured demo scenarios covering telecommunications, financial services, and healthcare use cases
- **Requirement 26.2**: Step-by-step guided interface with clear progression through configuration stages
