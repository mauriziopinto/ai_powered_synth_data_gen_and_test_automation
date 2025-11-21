# Demo Data and Scenarios

This directory contains pre-configured demo data and scenarios for the Synthetic Data Generator system demonstrations.

## Overview

The demo data is designed to showcase the complete end-to-end workflow across three industry verticals:
- **Telecommunications**: Customer account data with usage patterns
- **Financial Services**: Transaction data with fraud indicators
- **Healthcare**: Patient records with HIPAA-protected information

## Demo Data Files

### Telecommunications

**File**: `telecom_customers.csv`

**Description**: Sample customer account data for a telecommunications provider

**Records**: 20 customers

**Key Features**:
- Contains PII (names, emails, phone numbers, addresses)
- Includes data quality issues (malformed phone numbers, invalid emails, missing data)
- Mix of account statuses (active, suspended)
- Various plan types (basic, standard, premium)
- Realistic usage patterns (data, calls, SMS)

**Sensitive Fields**:
- `name` - Customer full name (PII)
- `email` - Email address (PII)
- `phone` - Phone number (PII)
- `address`, `city`, `state`, `postal_code` - Location data (PII)

**Edge Cases**:
- Row 5: Invalid phone format (`+1-555-INVALID`)
- Row 6: Malformed email (`jennifer.lee@mail` - missing TLD)
- Row 9: Missing phone number (empty field)
- Row 12: Invalid postal code (`INVALID`)
- Rows 6, 16: Suspended accounts

### Financial Services

**File**: `finance_transactions.csv`

**Description**: Credit card transaction data with fraud indicators

**Records**: 30 transactions

**Key Features**:
- Contains payment card data (card numbers, CVV)
- Fraud indicators with various fraud types
- Realistic transaction amounts and merchants
- Geographic diversity
- Temporal patterns

**Sensitive Fields**:
- `customer_name` - Cardholder name (PII)
- `card_number` - Credit card number (PCI-DSS sensitive)
- `cvv` - Card verification value (PCI-DSS sensitive)

**Fraud Patterns** (6 fraudulent transactions out of 30 = 20%):
- Row 4: Stolen card fraud
- Row 8: Account takeover
- Row 12: Synthetic identity fraud
- Row 16: Unusual pattern (gambling)
- Row 21: Card testing
- Row 25: Velocity check failure
- Row 30: Cross-border fraud

**Card Types**:
- Visa: 4532-XXXX-XXXX-XXXX
- Mastercard: 5412-XXXX-XXXX-XXXX
- American Express: 3782-XXXXXX-XXXXX
- Discover: 6011-XXXX-XXXX-XXXX

### Healthcare

**File**: `healthcare_patients.csv`

**Description**: Patient medical records with HIPAA-protected information

**Records**: 20 patients

**Key Features**:
- Contains PHI (Protected Health Information)
- Valid ICD-10 diagnosis codes
- Temporal consistency (admission before discharge)
- Various medical departments
- Realistic treatment costs
- Insurance information

**Sensitive Fields** (18 HIPAA Identifiers):
- `patient_id`, `mrn` - Patient identifiers
- `name` - Patient name (PHI)
- `ssn` - Social Security Number (PHI)
- `dob` - Date of birth (PHI)
- `phone`, `email` - Contact information (PHI)
- `address`, `city`, `state`, `zip_code` - Location (PHI)
- `insurance_provider`, `policy_number` - Insurance data (PHI)
- `diagnosis_code`, `diagnosis_description` - Medical information (PHI)
- `admission_date`, `discharge_date` - Treatment dates (PHI)
- `room_number` - Location identifier (PHI)

**Edge Cases**:
- Row 4: Malformed phone number (`555-2004`)
- Row 7: Missing phone number
- Row 12: Invalid zip code (`INVALID`)

**Diagnosis Codes** (ICD-10):
- J18.9 - Pneumonia
- I10 - Hypertension
- E11.9 - Type 2 Diabetes
- M54.5 - Low back pain
- O80 - Normal delivery
- K21.9 - GERD
- C50.9 - Breast cancer
- S72.0 - Femur fracture
- F32.9 - Depression
- J44.0 - COPD
- I21.9 - Myocardial infarction
- N18.9 - Chronic kidney disease
- G43.9 - Migraine
- A41.9 - Sepsis
- J45.9 - Asthma
- G30.9 - Alzheimer's disease
- O34.2 - C-section
- C61 - Prostate cancer
- H26.9 - Cataract
- N18.6 - End stage renal disease

## Mock Jira Test Scenarios

**File**: `mock_jira_scenarios.json`

**Description**: Pre-configured test scenarios for automated test generation

**Scenarios**: 11 test scenarios across three domains

### Telecommunications Scenarios (5)
1. **TELECOM-101**: Customer profile update functionality
2. **TELECOM-102**: Data usage tracking accuracy
3. **TELECOM-103**: Payment processing with various card types
4. **TELECOM-104**: Plan upgrade/downgrade workflow
5. **TELECOM-105**: Account suspension and reactivation

### Financial Services Scenarios (3)
1. **FINANCE-201**: Fraud detection for unusual transactions
2. **FINANCE-202**: Credit card number validation (Luhn algorithm)
3. **FINANCE-203**: Transaction history export functionality

### Healthcare Scenarios (3)
1. **HEALTH-301**: Patient record access controls (HIPAA)
2. **HEALTH-302**: Appointment scheduling with conflict detection
3. **HEALTH-303**: Prescription refill request workflow

**Test Frameworks**:
- Playwright: Modern browser automation
- Selenium: Traditional web testing
- Robot Framework: Keyword-driven testing

**Scenario Structure**:
- **Objective**: What the test validates
- **Preconditions**: Required setup
- **Test Steps**: Detailed step-by-step instructions
- **Expected Results**: Success criteria
- **Test Data Requirements**: Data needed for execution

## Mock Confluence Documentation

**File**: `mock_confluence_docs.json`

**Description**: Knowledge base documentation for data classification

**Pages**: 5 documentation pages

### Documentation Pages

1. **CONF-1001**: Customer Data Dictionary (Telecom)
   - Defines all customer data fields
   - Sensitivity classifications
   - Data quality notes
   - Compliance requirements

2. **CONF-1002**: Payment Card Data Handling Guidelines (Finance)
   - PCI-DSS compliance requirements
   - Card number handling rules
   - Fraud detection patterns
   - Test card numbers

3. **CONF-1003**: Protected Health Information Data Standards (Healthcare)
   - HIPAA compliance overview
   - 18 HIPAA identifier types
   - Temporal consistency rules
   - De-identification standards

4. **CONF-1004**: Network Usage Metrics Specification (Telecom)
   - Network metrics definitions
   - Statistical properties
   - Data quality notes
   - Privacy considerations

5. **CONF-1005**: Test Data Generation Best Practices (Engineering)
   - General principles
   - Domain-specific guidelines
   - Synthetic data tools
   - Quality validation methods

## Usage in Demonstrations

### Guided Demo Mode

The demo data is integrated with the guided demo mode in the web application:

1. **Telecom Demo**: Uses `telecom_customers.csv`
   - Demonstrates PII detection
   - Shows edge case preservation
   - Validates statistical property preservation

2. **Finance Demo**: Uses `finance_transactions.csv`
   - Demonstrates PCI-DSS compliance
   - Shows fraud pattern preservation
   - Validates Luhn algorithm for card numbers

3. **Healthcare Demo**: Uses `healthcare_patients.csv`
   - Demonstrates HIPAA compliance
   - Shows temporal consistency validation
   - Validates ICD-10 code preservation

### Mock Integrations

The mock Jira and Confluence clients use these files:

```python
# Mock Jira Client
jira_client = MockJiraClient(scenarios_file="data/demo/mock_jira_scenarios.json")

# Mock Confluence Client
confluence_client = MockConfluenceClient(docs_file="data/demo/mock_confluence_docs.json")
```

### Data Processor Agent

The Data Processor Agent queries mock Confluence for field definitions:

```python
# Query for field classification
results = confluence_client.search("field definition customer_name")
# Returns CONF-1001 with sensitivity classification
```

### Test Case Agent

The Test Case Agent retrieves scenarios from mock Jira:

```python
# Retrieve test scenarios by tag
scenarios = jira_client.search_issues('labels = "telecom-regression"')
# Returns TELECOM-101 through TELECOM-105
```

## Data Quality Characteristics

### Intentional Data Quality Issues

The demo data includes realistic data quality issues found in production systems:

1. **Malformed Phone Numbers**: Various invalid formats
2. **Invalid Email Addresses**: Missing TLDs, invalid characters
3. **Missing Required Fields**: Null values in optional fields
4. **Invalid Postal Codes**: Non-existent or malformed codes
5. **Boundary Values**: Min/max values for numeric fields

### Statistical Properties

The data maintains realistic statistical properties:

1. **Distributions**: Right-skewed for usage/cost data
2. **Correlations**: Realistic relationships between fields
3. **Frequencies**: Appropriate edge case rates (5-10%)
4. **Temporal Patterns**: Logical date sequences

## Compliance Considerations

### GDPR/CCPA (Telecom)
- All customer names are fictional
- Email addresses use example domains
- Phone numbers use reserved ranges (+1-555-XXXX)
- Addresses are fictional

### PCI-DSS (Finance)
- Card numbers are test numbers (not real)
- All pass Luhn algorithm validation
- CVV values are fictional
- No real payment data included

### HIPAA (Healthcare)
- All patient names are fictional
- SSNs are fictional (not real SSNs)
- Medical record numbers are system-generated
- Diagnosis codes are valid ICD-10 but randomly assigned
- All dates are fictional

## Extending Demo Data

### Adding New Records

To add more demo data:

1. Maintain the same CSV structure
2. Include similar edge case frequency (5-10%)
3. Preserve statistical distributions
4. Ensure temporal consistency
5. Use fictional PII only

### Adding New Scenarios

To add new Jira test scenarios:

1. Follow the existing JSON structure
2. Include all required fields (objective, steps, expected results)
3. Tag appropriately for filtering
4. Specify test framework (playwright, selenium, robot)

### Adding New Documentation

To add new Confluence pages:

1. Follow the existing JSON structure
2. Include field definitions with sensitivity levels
3. Document data quality considerations
4. Provide compliance requirements

## References

- **Requirements**: See `.kiro/specs/synthetic-data-generator/requirements.md`
  - Requirement 22.1: Mock Confluence implementation
  - Requirement 22.2: Mock Jira implementation
  - Requirement 22.3: Mock target systems
  - Requirement 26.3: Pre-configured demo scenarios

- **Design**: See `.kiro/specs/synthetic-data-generator/design.md`
  - Section on Mock Integrations
  - Demo Mode Architecture

- **Tasks**: See `.kiro/specs/synthetic-data-generator/tasks.md`
  - Task 36: Create demo data and scenarios

## Contact

For questions about demo data:
- Data Engineering Team: data-eng@company.com
- Demo Support: demo-support@company.com
