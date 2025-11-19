# Design Document

## Overview

The Synthetic Data Generator is a sophisticated multi-agent system built on the Strands framework that orchestrates an end-to-end testing workflow. The system transforms production data into GDPR-compliant synthetic datasets, distributes them to test environments, generates and executes automated tests, and reports results—all while providing transparent, interactive visualization of the entire process.

The architecture follows a microservices pattern with five specialized agents coordinated through Strands orchestration. Each agent has a single responsibility and communicates through well-defined interfaces. The system integrates with external services (Amazon Bedrock for LLM-based text generation, SDV for statistical synthesis, Confluence for knowledge management, Jira for test management) and provides a rich web interface for configuration, monitoring, and result analysis.

Key design principles:
- **Agent autonomy**: Each agent operates independently with clear inputs and outputs
- **Transparency**: Every decision and transformation is logged and explainable
- **Resilience**: Comprehensive error handling with retry logic and graceful degradation
- **Scalability**: Designed to handle datasets from hundreds to millions of records
- **Compliance**: GDPR-first approach with complete audit trails
- **Demo-ready**: Interactive visualization and guided modes for stakeholder presentations

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Application                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Configuration│  │ Visualization│  │  Results Dashboard │   │
│  │   Interface  │  │   Dashboard  │  │  & Cost Tracking   │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    Strands Orchestration Layer                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Communication Bus                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────┬────────┬────────┬────────┬────────┬──────────────────────┘
      │        │        │        │        │
┌─────▼──┐ ┌──▼────┐ ┌─▼──────┐ ┌▼──────┐ ┌▼────────────┐
│  Data  │ │Synth  │ │Distrib │ │Test   │ │Test         │
│Process │ │Data   │ │ution   │ │Case   │ │Execution    │
│ Agent  │ │Agent  │ │Agent   │ │Agent  │ │Agent        │
└────┬───┘ └───┬───┘ └───┬────┘ └───┬───┘ └──┬──────────┘
     │         │         │          │        │
┌────▼─────────▼─────────▼──────────▼────────▼──────────┐
│              External Integrations                      │
│  ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌─────────┐ │
│  │ Bedrock  │ │ SDV  │ │Conflu│ │ Jira │ │ Target  │ │
│  │   LLM    │ │      │ │ence  │ │      │ │ Systems │ │
│  └──────────┘ └──────┘ └──────┘ └──────┘ └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
Production Data → Data Processor Agent
                       ↓
                  (Identifies sensitive fields)
                       ↓
                  (Queries Confluence)
                       ↓
                  Sensitivity Report → Synthetic Data Agent
                                            ↓
                                       (Uses SDV + Bedrock)
                                            ↓
                                       Synthetic Dataset → Distribution Agent
                                                                ↓
                                                           (Loads to targets)
                                                                ↓
                                                           Test Case Agent
                                                                ↓
                                                           (Queries Jira)
                                                                ↓
                                                           Test Cases → Test Execution Agent
                                                                             ↓
                                                                        (Runs tests)
                                                                             ↓
                                                                        Test Results
                                                                             ↓
                                                                        (Updates Jira)
```

## Components and Interfaces

### 1. Web Application Layer

**Technology Stack**: React with TypeScript, Material-UI for components, D3.js for visualizations

**Components**:

#### Configuration Interface
- **Schema Builder**: Visual editor for defining data schemas with drag-and-drop field types
- **Parameter Controls**: Forms for SDV model selection, Bedrock configuration, edge-case rules
- **Target System Manager**: Interface for configuring database connections, Salesforce credentials, API endpoints
- **Guided Demo Selector**: Pre-configured scenario picker with telecom/finance/healthcare options

#### Visualization Dashboard
- **Workflow Canvas**: Interactive flowchart showing agent states with real-time updates
- **Agent Detail Panels**: Expandable sections showing logs, decisions, and intermediate data
- **Progress Indicators**: Contextual status messages ("Analyzing 50 fields for PII patterns...")
- **Data Transformation Viewer**: Side-by-side before/after comparisons with diff highlighting

#### Results Dashboard
- **Quality Metrics Display**: SDV scores, statistical tests, distribution comparisons
- **Interactive Charts**: Histograms, Q-Q plots, correlation heatmaps using Plotly
- **Test Results Table**: Pass/fail status, execution times, failure details
- **Cost Tracker**: Real-time AWS cost accumulation with breakdown by service

**API Interface**:
```typescript
interface WebAPI {
  // Configuration
  saveConfiguration(config: WorkflowConfig): Promise<string>
  loadConfiguration(id: string): Promise<WorkflowConfig>
  listConfigurations(): Promise<ConfigurationSummary[]>
  
  // Execution
  startWorkflow(configId: string): Promise<string>
  pauseWorkflow(workflowId: string): Promise<void>
  resumeWorkflow(workflowId: string): Promise<void>
  abortWorkflow(workflowId: string): Promise<void>
  
  // Monitoring
  getWorkflowStatus(workflowId: string): Promise<WorkflowStatus>
  subscribeToUpdates(workflowId: string): WebSocket
  
  // Results
  getQualityReport(workflowId: string): Promise<QualityReport>
  getTestResults(workflowId: string): Promise<TestResults>
  exportResults(workflowId: string, format: ExportFormat): Promise<Blob>
  
  // Audit
  getAuditLog(filters: AuditFilters): Promise<AuditEntry[]>
  exportAuditLog(filters: AuditFilters, format: string): Promise<Blob>
}
```

### 2. Strands Orchestration Layer

**Responsibilities**:
- Agent lifecycle management (start, stop, restart)
- Message routing between agents
- State persistence and recovery
- Error propagation and handling
- Workflow checkpointing

**Agent Communication Protocol**:
```python
@dataclass
class AgentMessage:
    sender: str
    recipient: str
    message_type: MessageType
    payload: Dict[str, Any]
    correlation_id: str
    timestamp: datetime
    
class MessageType(Enum):
    DATA_READY = "data_ready"
    PROCESSING_COMPLETE = "processing_complete"
    ERROR_OCCURRED = "error_occurred"
    STATUS_UPDATE = "status_update"
    REQUEST_INPUT = "request_input"
```

**Strands Configuration**:
```python
from strands import Agent, Workflow, OrchestrationStrategy

workflow = Workflow(
    name="synthetic-data-testing",
    strategy=OrchestrationStrategy.SEQUENTIAL,
    agents=[
        data_processor_agent,
        synthetic_data_agent,
        distribution_agent,
        test_case_agent,
        test_execution_agent
    ],
    error_handling=ErrorHandlingPolicy.PAUSE_AND_NOTIFY,
    checkpoint_interval=timedelta(minutes=5)
)
```

### 3. Data Processor Agent

**Purpose**: Analyze production data to identify sensitive fields requiring synthetic replacement

**Inputs**:
- Production data file (CSV, JSON, Parquet)
- Confluence API credentials
- Classification rules configuration

**Outputs**:
- Sensitivity report with field classifications
- Confidence scores per field
- Recommended generation strategies

**Core Logic**:

```python
class DataProcessorAgent(StrandsAgent):
    def __init__(self, confluence_client, bedrock_client):
        self.confluence_client = confluence_client
        self.bedrock_client = bedrock_client
        self.classifiers = [
            PatternClassifier(),
            NameBasedClassifier(),
            ContentAnalysisClassifier(),
            ConfluenceKnowledgeClassifier()
        ]
    
    async def process(self, data_file: Path) -> SensitivityReport:
        # Load and profile data
        df = self.load_data(data_file)
        profile = self.profile_data(df)
        
        # Classify each field
        classifications = {}
        for column in df.columns:
            scores = {}
            for classifier in self.classifiers:
                score = await classifier.classify(
                    column_name=column,
                    sample_values=df[column].head(100),
                    data_profile=profile[column]
                )
                scores[classifier.name] = score
            
            # Aggregate scores
            final_score = self.aggregate_scores(scores)
            classifications[column] = FieldClassification(
                field_name=column,
                is_sensitive=final_score.confidence > 0.7,
                sensitivity_type=final_score.type,
                confidence=final_score.confidence,
                reasoning=final_score.reasoning,
                recommended_strategy=self.select_strategy(final_score)
            )
        
        return SensitivityReport(
            classifications=classifications,
            data_profile=profile,
            timestamp=datetime.now()
        )
```

**Classification Strategies**:

1. **Pattern Classifier**: Regex patterns for emails, phones, SSNs, credit cards
2. **Name-Based Classifier**: Field name matching (email, phone, ssn, dob, etc.)
3. **Content Analysis Classifier**: Statistical analysis of value patterns
4. **Confluence Knowledge Classifier**: Queries Confluence for field definitions

**Confluence Integration**:
```python
class ConfluenceKnowledgeClassifier:
    async def classify(self, column_name, sample_values, data_profile):
        # Search Confluence for field documentation
        query = f"field definition {column_name}"
        results = await self.confluence_client.search(query, limit=5)
        
        if not results:
            return ClassificationScore(confidence=0.0)
        
        # Use Bedrock to analyze documentation
        context = "\n".join([r.content for r in results])
        prompt = f"""
        Analyze this field documentation and determine if the field contains
        sensitive personal information:
        
        Field name: {column_name}
        Sample values: {sample_values[:10]}
        Documentation: {context}
        
        Respond with JSON: {{"is_sensitive": bool, "type": str, "confidence": float, "reasoning": str}}
        """
        
        response = await self.bedrock_client.invoke(prompt)
        return ClassificationScore.from_json(response)
```

### 4. Synthetic Data Agent

**Purpose**: Generate synthetic data that preserves statistical properties while ensuring GDPR compliance

**Inputs**:
- Sensitivity report from Data Processor Agent
- Original production data
- Generation parameters (SDV model, Bedrock settings)

**Outputs**:
- Synthetic dataset
- Quality metrics
- Generation metadata

**Core Logic**:

```python
class SyntheticDataAgent(StrandsAgent):
    def __init__(self, bedrock_client):
        self.bedrock_client = bedrock_client
        self.sdv_models = {
            'gaussian_copula': GaussianCopulaSynthesizer,
            'ctgan': CTGANSynthesizer,
            'copula_gan': CopulaGANSynthesizer
        }
    
    async def process(self, 
                     data: pd.DataFrame,
                     sensitivity_report: SensitivityReport,
                     params: GenerationParams) -> SyntheticDataset:
        
        # Separate sensitive and non-sensitive fields
        sensitive_fields = [
            f for f, c in sensitivity_report.classifications.items()
            if c.is_sensitive
        ]
        non_sensitive_fields = [
            f for f in data.columns if f not in sensitive_fields
        ]
        
        # Use SDV for tabular structure
        synthesizer = self.sdv_models[params.sdv_model](
            metadata=self.create_metadata(data, sensitivity_report)
        )
        synthesizer.fit(data[non_sensitive_fields])
        synthetic_df = synthesizer.sample(num_rows=params.num_rows)
        
        # Use Bedrock for sensitive text fields
        for field in sensitive_fields:
            classification = sensitivity_report.classifications[field]
            if classification.sensitivity_type in ['name', 'email', 'address']:
                synthetic_df[field] = await self.generate_text_field(
                    field_name=field,
                    field_type=classification.sensitivity_type,
                    num_values=params.num_rows,
                    context=data[non_sensitive_fields].head()
                )
            else:
                # Use rule-based generation for structured sensitive data
                synthetic_df[field] = self.generate_structured_field(
                    field_name=field,
                    pattern=classification.pattern,
                    num_values=params.num_rows
                )
        
        # Evaluate quality
        quality_metrics = self.evaluate_quality(data, synthetic_df)
        
        return SyntheticDataset(
            data=synthetic_df,
            quality_metrics=quality_metrics,
            generation_metadata=self.create_metadata(params)
        )
```

**Bedrock Text Generation**:
```python
async def generate_text_field(self, field_name, field_type, num_values, context):
    # Batch requests for efficiency
    batch_size = 100
    results = []
    
    for i in range(0, num_values, batch_size):
        batch_count = min(batch_size, num_values - i)
        
        prompt = f"""
        Generate {batch_count} realistic synthetic {field_type} values.
        These should be diverse, realistic, and appropriate for a {field_type} field.
        
        Context from related fields:
        {context.to_string()}
        
        Return as JSON array: ["value1", "value2", ...]
        """
        
        response = await self.bedrock_client.invoke(
            model_id=self.params.bedrock_model,
            prompt=prompt,
            temperature=0.9,
            max_tokens=2000
        )
        
        batch_results = json.loads(response)
        results.extend(batch_results)
    
    return results[:num_values]
```

**Quality Evaluation**:
```python
def evaluate_quality(self, real_data, synthetic_data):
    from sdmetrics.reports.single_table import QualityReport
    
    # SDV quality metrics
    quality_report = QualityReport()
    quality_report.generate(real_data, synthetic_data, metadata)
    
    # Additional statistical tests
    ks_tests = {}
    for column in real_data.select_dtypes(include=[np.number]).columns:
        statistic, pvalue = ks_2samp(
            real_data[column].dropna(),
            synthetic_data[column].dropna()
        )
        ks_tests[column] = {'statistic': statistic, 'pvalue': pvalue}
    
    # Correlation preservation
    real_corr = real_data.corr()
    synth_corr = synthetic_data.corr()
    corr_diff = np.abs(real_corr - synth_corr).mean().mean()
    
    return QualityMetrics(
        sdv_quality_score=quality_report.get_score(),
        column_shapes=quality_report.get_details('Column Shapes'),
        column_pair_trends=quality_report.get_details('Column Pair Trends'),
        ks_tests=ks_tests,
        correlation_preservation=1 - corr_diff,
        edge_case_frequency_match=self.compare_edge_cases(real_data, synthetic_data)
    )
```

### 5. Distribution Agent

**Purpose**: Load synthetic data into target test systems

**Inputs**:
- Synthetic dataset
- Target system configurations

**Outputs**:
- Load status per target
- Record counts
- Error reports

**Supported Targets**:
- PostgreSQL/MySQL databases
- Salesforce (via Bulk API)
- REST APIs
- S3/file storage

**Core Logic**:

```python
class DistributionAgent(StrandsAgent):
    def __init__(self):
        self.loaders = {
            'database': DatabaseLoader(),
            'salesforce': SalesforceLoader(),
            'api': APILoader(),
            'file': FileLoader()
        }
    
    async def process(self,
                     synthetic_data: pd.DataFrame,
                     targets: List[TargetConfig]) -> DistributionReport:
        
        results = []
        for target in targets:
            try:
                loader = self.loaders[target.type]
                result = await loader.load(synthetic_data, target)
                results.append(LoadResult(
                    target=target.name,
                    status='success',
                    records_loaded=len(synthetic_data),
                    duration=result.duration
                ))
            except Exception as e:
                results.append(LoadResult(
                    target=target.name,
                    status='failed',
                    error=str(e),
                    records_loaded=0
                ))
        
        return DistributionReport(results=results)
```

**Database Loader**:
```python
class DatabaseLoader:
    async def load(self, data: pd.DataFrame, config: TargetConfig):
        engine = create_engine(config.connection_string)
        
        # Handle foreign key constraints
        if config.respect_fk_order:
            tables = self.topological_sort(config.tables)
        else:
            tables = config.tables
        
        for table in tables:
            table_data = data[config.table_mappings[table]]
            
            if config.load_strategy == 'truncate_insert':
                with engine.begin() as conn:
                    conn.execute(f"TRUNCATE TABLE {table}")
                    table_data.to_sql(table, conn, if_exists='append', index=False)
            elif config.load_strategy == 'upsert':
                self.upsert_data(engine, table, table_data, config.primary_keys[table])
```

### 6. Test Case Agent

**Purpose**: Generate executable test cases from Jira test scenarios

**Inputs**:
- Jira test scenarios
- Synthetic data references
- Test framework selection

**Outputs**:
- Executable test scripts
- Test data mappings

**Core Logic**:

```python
class TestCaseAgent(StrandsAgent):
    def __init__(self, jira_client, bedrock_client):
        self.jira_client = jira_client
        self.bedrock_client = bedrock_client
        self.generators = {
            'robot': RobotFrameworkGenerator(),
            'selenium': SeleniumGenerator(),
            'playwright': PlaywrightGenerator()
        }
    
    async def process(self,
                     test_run_tag: str,
                     framework: str,
                     data_references: Dict) -> List[TestCase]:
        
        # Fetch scenarios from Jira
        scenarios = await self.jira_client.search_issues(
            jql=f'labels = "{test_run_tag}" AND type = "Test Scenario"'
        )
        
        test_cases = []
        for scenario in scenarios:
            # Parse scenario description
            parsed = self.parse_scenario(scenario.description)
            
            # Generate test code using Bedrock
            test_code = await self.generate_test_code(
                framework=framework,
                scenario=parsed,
                data_references=data_references
            )
            
            test_cases.append(TestCase(
                id=scenario.key,
                name=scenario.summary,
                framework=framework,
                code=test_code,
                data_refs=self.extract_data_refs(parsed, data_references)
            ))
        
        return test_cases
```

**Test Code Generation**:
```python
async def generate_test_code(self, framework, scenario, data_references):
    prompt = f"""
    Generate a {framework} test case for the following scenario:
    
    Title: {scenario.title}
    Preconditions: {scenario.preconditions}
    Steps: {scenario.steps}
    Expected Results: {scenario.expected_results}
    
    Available test data: {data_references}
    
    Generate complete, executable test code following {framework} best practices.
    """
    
    response = await self.bedrock_client.invoke(
        model_id='anthropic.claude-3-sonnet',
        prompt=prompt,
        temperature=0.3,
        max_tokens=4000
    )
    
    return response
```

### 7. Test Execution Agent

**Purpose**: Execute automated tests and report results

**Inputs**:
- Test cases
- Test framework configuration
- Target system URLs

**Outputs**:
- Test results
- Logs and screenshots
- Jira updates

**Core Logic**:

```python
class TestExecutionAgent(StrandsAgent):
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.executors = {
            'robot': RobotExecutor(),
            'selenium': SeleniumExecutor(),
            'playwright': PlaywrightExecutor()
        }
    
    async def process(self,
                     test_cases: List[TestCase],
                     config: ExecutionConfig) -> TestResults:
        
        results = []
        
        # Execute in parallel if configured
        if config.parallel_execution:
            tasks = [
                self.execute_test(tc, config)
                for tc in test_cases
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for test_case in test_cases:
                result = await self.execute_test(test_case, config)
                results.append(result)
        
        # Update Jira
        if config.update_jira:
            await self.update_jira_results(results)
        
        return TestResults(
            total=len(results),
            passed=sum(1 for r in results if r.status == 'passed'),
            failed=sum(1 for r in results if r.status == 'failed'),
            results=results
        )
    
    async def execute_test(self, test_case, config):
        executor = self.executors[test_case.framework]
        
        try:
            result = await executor.run(
                code=test_case.code,
                timeout=config.timeout,
                capture_screenshots=True
            )
            
            return TestResult(
                test_id=test_case.id,
                status='passed' if result.success else 'failed',
                duration=result.duration,
                logs=result.logs,
                screenshots=result.screenshots,
                error=result.error if not result.success else None
            )
        except Exception as e:
            return TestResult(
                test_id=test_case.id,
                status='error',
                error=str(e)
            )
```

## Data Models

### Core Data Structures

```python
@dataclass
class WorkflowConfig:
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    
    # Data source
    production_data_path: Path
    
    # Generation parameters
    sdv_model: str  # 'gaussian_copula', 'ctgan', 'copula_gan'
    bedrock_model: str  # 'anthropic.claude-3-sonnet', etc.
    num_synthetic_records: int
    preserve_edge_cases: bool
    edge_case_frequency: float
    
    # Target systems
    targets: List[TargetConfig]
    
    # Test configuration
    test_framework: str  # 'robot', 'selenium', 'playwright'
    jira_test_tag: str
    parallel_execution: bool
    
    # External integrations
    confluence_space: str
    jira_project: str
    
    tags: List[str]

@dataclass
class FieldClassification:
    field_name: str
    is_sensitive: bool
    sensitivity_type: str  # 'name', 'email', 'phone', 'ssn', 'address', etc.
    confidence: float
    reasoning: str
    recommended_strategy: str
    confluence_references: List[str]

@dataclass
class SensitivityReport:
    classifications: Dict[str, FieldClassification]
    data_profile: Dict[str, Any]
    timestamp: datetime
    total_fields: int
    sensitive_fields: int
    confidence_distribution: Dict[str, int]

@dataclass
class QualityMetrics:
    sdv_quality_score: float
    column_shapes_score: float
    column_pair_trends_score: float
    ks_tests: Dict[str, Dict[str, float]]
    correlation_preservation: float
    edge_case_frequency_match: float
    
    # Per-field metrics
    field_scores: Dict[str, float]
    
    # Visualizations
    distribution_plots: Dict[str, bytes]  # PNG images
    correlation_heatmaps: Dict[str, bytes]
    qq_plots: Dict[str, bytes]

@dataclass
class SyntheticDataset:
    data: pd.DataFrame
    quality_metrics: QualityMetrics
    generation_metadata: Dict[str, Any]
    timestamp: datetime
    seed: int

@dataclass
class TestResult:
    test_id: str
    test_name: str
    status: str  # 'passed', 'failed', 'error', 'skipped'
    duration: float
    logs: str
    screenshots: List[bytes]
    error: Optional[str]
    jira_issue_created: Optional[str]

@dataclass
class AuditEntry:
    timestamp: datetime
    user: str
    action: str
    agent: Optional[str]
    details: Dict[str, Any]
    workflow_id: Optional[str]
    cost_incurred: Optional[float]
```

### Database Schema

```sql
-- Workflow configurations
CREATE TABLE workflow_configs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config_json JSONB NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    tags TEXT[]
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    config_id UUID REFERENCES workflow_configs(id),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error TEXT,
    checkpoint_data JSONB
);

-- Agent execution logs
CREATE TABLE agent_logs (
    id SERIAL PRIMARY KEY,
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    agent_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL
);

-- Audit trail
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    agent VARCHAR(100),
    workflow_id UUID,
    details JSONB,
    cost_usd DECIMAL(10, 4)
);

-- Results archive
CREATE TABLE results_archive (
    id UUID PRIMARY KEY,
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    result_type VARCHAR(50) NOT NULL,  -- 'synthetic_data', 'quality_report', 'test_results'
    storage_path VARCHAR(500) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL
);

-- Cost tracking
CREATE TABLE cost_tracking (
    id SERIAL PRIMARY KEY,
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    service VARCHAR(100) NOT NULL,  -- 'bedrock', 's3', 'compute'
    operation VARCHAR(100) NOT NULL,
    quantity DECIMAL(15, 2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    cost_usd DECIMAL(10, 4) NOT NULL,
    timestamp TIMESTAMP NOT NULL
);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Statistical Property Preservation
*For any* production dataset with measurable statistical properties (distributions, correlations, frequencies), when synthetic data is generated, the statistical distance between production and synthetic data should be within the configured tolerance threshold.
**Validates: Requirements 1.2**

### Property 2: No Data Leakage
*For any* production dataset and generated synthetic dataset, no synthetic record should contain values that exactly match production record values (excluding intentionally preserved masked fields).
**Validates: Requirements 1.3**

### Property 3: Schema Constraint Enforcement
*For any* schema definition with specified constraints (ranges, patterns, required fields), all generated synthetic records should satisfy those constraints.
**Validates: Requirements 2.3**

### Property 4: Referential Integrity Preservation
*For any* schema with foreign key relationships, all foreign key values in generated synthetic data should reference existing primary key values.
**Validates: Requirements 2.4**

### Property 5: Edge Case Frequency Matching
*For any* edge-case generation rule with specified frequency F, the actual frequency of edge cases in generated data should be within ±5% of F.
**Validates: Requirements 3.1**

### Property 6: Edge Case Tagging Completeness
*For any* generated dataset with injected edge cases, all edge-case records should have appropriate tags identifying the anomaly type.
**Validates: Requirements 3.3**

### Property 7: Exact Record Count
*For any* specified target record count N, the generated synthetic dataset should contain exactly N records.
**Validates: Requirements 4.1**

### Property 8: Deterministic Generation
*For any* random seed value S and configuration C, generating synthetic data twice with the same S and C should produce identical datasets.
**Validates: Requirements 6.1**

### Property 9: Configuration Round-Trip
*For any* workflow configuration, saving then loading the configuration should restore all settings identically.
**Validates: Requirements 30.4**

### Property 10: Sensitive Field Classification
*For any* production dataset, all fields containing PII patterns (emails, phones, SSNs, etc.) should be classified as sensitive with confidence > 0.7.
**Validates: Requirements 14.2**

### Property 11: Data Quality Issue Preservation
*For any* production dataset with data quality issues (malformed emails, invalid postcodes), the frequency of these issues in synthetic data should match the production frequency within ±10%.
**Validates: Requirements 23.2**

### Property 12: Quality Metrics Calculation
*For any* pair of production and synthetic datasets, SDV quality metrics (Column Shapes, Column Pair Trends, Quality Score) should be calculated and returned.
**Validates: Requirements 24.1**

### Property 13: Statistical Test Execution
*For any* pair of production and synthetic datasets, statistical tests (KS test, Chi-squared, Wasserstein distance) should be performed on appropriate field types.
**Validates: Requirements 24.2**

### Property 14: Error Information Capture
*For any* agent error during workflow execution, the error log should contain error type, context, affected data, and timestamp.
**Validates: Requirements 28.1**

### Property 15: Retry with Exponential Backoff
*For any* transient failure (API timeout, network error), retry attempts should occur with exponentially increasing delays.
**Validates: Requirements 28.2**

### Property 16: Audit Log Completeness
*For any* workflow execution, the audit log should contain start time, end time, user identifier, input sources, and output destinations.
**Validates: Requirements 29.1**

### Property 17: Sensitive Field Processing Log
*For any* production data processing, the audit log should record which fields were classified as sensitive, confidence scores, and generation methods used.
**Validates: Requirements 29.2**

### Property 18: Export Format Support
*For any* generated synthetic dataset, export should succeed in all specified formats (CSV, JSON, Parquet, SQL).
**Validates: Requirements 31.1**

### Property 19: Bedrock Prompt Context Inclusion
*For any* text field generation using Bedrock, the prompt should include context from related fields and specified constraints.
**Validates: Requirements 13.3**

### Property 20: Database Foreign Key Ordering
*For any* database loading operation with foreign key constraints, tables should be loaded in topological order respecting dependencies.
**Validates: Requirements 16.3**

### Property 21: Test Artifact Capture
*For any* executed test case, the system should capture execution logs, screenshots (on failure), and performance metrics.
**Validates: Requirements 18.3**

### Property 22: File Format Parsing
*For any* supported production data file format (CSV, JSON, Parquet), the system should successfully parse and extract column names, data types, and value patterns.
**Validates: Requirements 23.1**

### Property 23: Configuration Metadata Assignment
*For any* saved workflow configuration, the system should assign a unique identifier and store the provided name and tags.
**Validates: Requirements 30.2**
## Error Handling

### Error Categories

1. **Transient Errors**: API timeouts, network issues, temporary service unavailability
   - Strategy: Automatic retry with exponential backoff (max 3 attempts)
   - Backoff: 1s, 2s, 4s

2. **Configuration Errors**: Invalid schemas, missing credentials, inaccessible resources
   - Strategy: Immediate failure with detailed validation messages
   - User action: Fix configuration and retry

3. **Data Errors**: Malformed input files, constraint violations, data type mismatches
   - Strategy: Fail fast with specific error location (row/column)
   - User action: Fix data or adjust schema

4. **Integration Errors**: Bedrock API failures, Jira/Confluence unavailability, target system errors
   - Strategy: Retry transient, fallback for non-critical (e.g., mock Confluence), fail for critical
   - User action: Check credentials, service status

5. **Resource Errors**: Out of memory, disk space, compute limits
   - Strategy: Graceful degradation (reduce batch size), checkpoint and pause
   - User action: Allocate more resources or reduce dataset size

### Error Handling Flow

```python
class ErrorHandler:
    def handle_error(self, error: Exception, context: ErrorContext) -> ErrorAction:
        # Classify error
        category = self.classify_error(error)
        
        if category == ErrorCategory.TRANSIENT:
            if context.retry_count < 3:
                delay = 2 ** context.retry_count
                return ErrorAction.RETRY_AFTER(delay)
            else:
                return ErrorAction.PAUSE_WORKFLOW
        
        elif category == ErrorCategory.CONFIGURATION:
            return ErrorAction.FAIL_WITH_MESSAGE(
                self.generate_remediation_steps(error, context)
            )
        
        elif category == ErrorCategory.DATA:
            return ErrorAction.FAIL_WITH_LOCATION(
                row=context.current_row,
                column=context.current_column,
                message=str(error)
            )
        
        elif category == ErrorCategory.INTEGRATION:
            if self.is_critical_service(context.service):
                return ErrorAction.PAUSE_WORKFLOW
            else:
                return ErrorAction.USE_FALLBACK
        
        else:
            return ErrorAction.PAUSE_WORKFLOW
```

### Checkpoint and Recovery

The system maintains checkpoints at key workflow stages:
- After data profiling completes
- After synthetic data generation completes
- After each target system load completes
- After test case generation completes

Checkpoints include:
- Workflow state (current agent, progress)
- Intermediate data (stored in S3)
- Configuration snapshot
- Timestamp and user

Recovery process:
1. User selects failed workflow
2. System loads last checkpoint
3. User reviews error and takes action (retry/skip/abort)
4. Workflow resumes from checkpoint

## Testing Strategy

### Unit Testing

**Scope**: Individual components and functions within each agent

**Key Areas**:
- Data classification algorithms (pattern matching, name-based, content analysis)
- Schema validation logic
- Statistical metric calculations
- Data transformation functions
- Export format generation

**Framework**: pytest with fixtures for sample data

**Example**:
```python
def test_email_pattern_classifier():
    classifier = PatternClassifier()
    
    # Test with email samples
    samples = ['user@example.com', 'test@test.org', 'admin@company.co.uk']
    result = classifier.classify('email_field', samples, {})
    
    assert result.sensitivity_type == 'email'
    assert result.confidence > 0.9
```

### Property-Based Testing

**Scope**: Universal properties that should hold across all inputs

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**: Minimum 100 iterations per property test

**Key Properties** (see Correctness Properties section for complete list):
- Statistical property preservation
- No data leakage
- Schema constraint enforcement
- Referential integrity
- Deterministic generation
- Configuration round-trip

**Example**:
```python
from hypothesis import given, strategies as st
import pandas as pd

@given(
    df=st.data_frames(
        columns=[
            st.column('age', dtype=int, elements=st.integers(0, 120)),
            st.column('name', dtype=str),
            st.column('email', dtype=str)
        ],
        rows=st.tuples(st.integers(10, 1000))
    ),
    seed=st.integers(0, 2**32-1)
)
def test_deterministic_generation(df, seed):
    """
    Feature: synthetic-data-generator, Property 8: Deterministic Generation
    For any random seed and configuration, generating twice should produce identical results
    """
    config = GenerationConfig(sdv_model='gaussian_copula', seed=seed)
    
    # Generate twice with same seed
    result1 = generate_synthetic_data(df, config)
    result2 = generate_synthetic_data(df, config)
    
    # Should be identical
    pd.testing.assert_frame_equal(result1.data, result2.data)
```

### Integration Testing

**Scope**: Agent interactions and external service integrations

**Key Scenarios**:
- End-to-end workflow execution with mock services
- Bedrock API integration (using actual API in test environment)
- SDV integration with various model types
- Database loading with different schemas
- Error handling and recovery flows

**Framework**: pytest with docker-compose for service mocking

### Demo Testing

**Scope**: Guided demo mode functionality

**Approach**:
- Manual testing of demo scenarios
- Verification of visualization accuracy
- Timing and pacing validation
- Cost estimation accuracy checks

## Deployment Architecture

### AWS Services Used

1. **Amazon Bedrock**: LLM text generation
2. **Amazon ECS/Fargate**: Container hosting for agents
3. **Amazon RDS (PostgreSQL)**: Configuration and audit storage
4. **Amazon S3**: Data storage (production samples, synthetic datasets, results)
5. **Amazon CloudWatch**: Logging and monitoring
6. **AWS Lambda**: Lightweight operations (cost calculation, notifications)
7. **Amazon API Gateway**: REST API for web application
8. **Amazon CloudFront**: Web application CDN
9. **AWS Secrets Manager**: Credentials storage

### Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    CloudFront (CDN)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              S3 (Static Web App)                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API Gateway (REST API)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│         ECS Cluster (Fargate)                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Strands Orchestrator + 5 Agent Containers       │  │
│  └──────────────────────────────────────────────────┘  │
└─────┬────────┬────────┬────────┬──────────────────────┘
      │        │        │        │
┌─────▼──┐ ┌──▼────┐ ┌─▼──────┐ ┌▼────────┐
│ RDS    │ │ S3    │ │Bedrock │ │Secrets  │
│(Config)│ │(Data) │ │(LLM)   │ │Manager  │
└────────┘ └───────┘ └────────┘ └─────────┘
```

### Scaling Considerations

- **Horizontal scaling**: Multiple ECS tasks for parallel workflow execution
- **Data partitioning**: Large datasets split into chunks for parallel processing
- **Caching**: Confluence documentation cached, Bedrock responses cached for identical prompts
- **Batch processing**: Bedrock API calls batched to reduce latency and cost

### Security

- **Encryption at rest**: S3 (SSE-S3), RDS (encryption enabled)
- **Encryption in transit**: TLS for all API calls
- **IAM roles**: Least privilege for each service
- **Secrets management**: AWS Secrets Manager for credentials
- **Network isolation**: VPC with private subnets for ECS tasks
- **Audit logging**: CloudTrail for AWS API calls, application audit log in RDS

## Performance Considerations

### Expected Performance

| Dataset Size | Generation Time | Memory Usage | Cost Estimate |
|--------------|----------------|--------------|---------------|
| 1K records   | 30 seconds     | 512 MB       | $0.10         |
| 10K records  | 2 minutes      | 1 GB         | $0.50         |
| 100K records | 15 minutes     | 2 GB         | $3.00         |
| 1M records   | 2 hours        | 4 GB         | $25.00        |

### Optimization Strategies

1. **Bedrock batching**: Generate multiple text values per API call
2. **SDV model selection**: Use faster models (GaussianCopula) for large datasets
3. **Parallel processing**: Split data into chunks, process in parallel
4. **Incremental generation**: Generate in batches, checkpoint between batches
5. **Caching**: Cache Bedrock responses for similar prompts

### Monitoring Metrics

- Workflow execution time per stage
- Agent processing time
- Bedrock API latency and token usage
- SDV model training time
- Database load time
- Memory and CPU utilization
- Error rates per agent
- Cost per workflow execution

## Mock Implementations

For demo purposes, the system includes mock implementations of external services:

### Mock Confluence
- Returns pre-configured documentation for common field names
- Simulates search latency (500ms delay)
- Provides realistic field definitions and data dictionaries

### Mock Jira
- Returns pre-configured test scenarios
- Simulates issue creation with generated IDs
- Provides realistic test scenario descriptions

### Mock Target Systems
- **Mock Database**: In-memory SQLite with sample schema
- **Mock Salesforce**: REST API simulator accepting bulk data loads
- **Mock REST API**: Echo service that accepts and validates JSON payloads

### Configuration Toggle
```python
class ServiceFactory:
    def create_confluence_client(self, config):
        if config.demo_mode:
            return MockConfluenceClient()
        else:
            return RealConfluenceClient(config.confluence_url, config.credentials)
```

## Cost Estimation

### Cost Components

1. **Amazon Bedrock**:
   - Input tokens: $0.003 per 1K tokens
   - Output tokens: $0.015 per 1K tokens
   - Estimated: 100 tokens per text field
   - Formula: `num_text_fields * num_records * 100 * $0.018 / 1000`

2. **ECS Fargate**:
   - vCPU: $0.04048 per vCPU-hour
   - Memory: $0.004445 per GB-hour
   - Estimated: 2 vCPU, 4 GB, 1 hour per 100K records
   - Formula: `(2 * $0.04048 + 4 * $0.004445) * execution_hours`

3. **RDS**:
   - db.t3.medium: $0.068 per hour
   - Storage: $0.115 per GB-month
   - Estimated: $50/month baseline

4. **S3**:
   - Storage: $0.023 per GB-month
   - Requests: $0.0004 per 1K PUT requests
   - Estimated: Negligible for typical usage

5. **Data Transfer**:
   - Out to internet: $0.09 per GB
   - Estimated: Minimal for typical usage

### Example Cost Calculation

For 10,000 records with 5 text fields:
- Bedrock: 10,000 * 5 * 100 * $0.018 / 1000 = $0.90
- ECS: (2 * $0.04048 + 4 * $0.004445) * 0.1 = $0.01
- Total: ~$0.91

The web interface displays these estimates before execution and tracks actual costs during execution.
