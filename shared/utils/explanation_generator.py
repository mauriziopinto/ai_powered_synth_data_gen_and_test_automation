"""Plain-language explanation generator for agent actions and decisions."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class Explanation:
    """A plain-language explanation of an agent action or decision."""
    agent_name: str
    action: str
    plain_language: str
    reasoning: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    highlights: Optional[List[str]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ExplanationTemplate:
    """Template for generating explanations for specific agent actions."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load explanation templates for this agent."""
        # Override in subclasses
        return {}
    
    def generate(self, action: str, context: Dict[str, Any]) -> Explanation:
        """Generate an explanation for an action."""
        template = self.templates.get(action, {})
        
        plain_language = template.get('plain_language', '').format(**context)
        reasoning = template.get('reasoning', '').format(**context)
        
        return Explanation(
            agent_name=self.agent_name,
            action=action,
            plain_language=plain_language,
            reasoning=reasoning,
            before_state=context.get('before_state'),
            after_state=context.get('after_state'),
            highlights=context.get('highlights', [])
        )


class DataProcessorExplanations(ExplanationTemplate):
    """Explanation templates for Data Processor Agent."""
    
    def __init__(self):
        super().__init__("Data Processor Agent")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'start_analysis': {
                'plain_language': 'Starting analysis of production data file with {num_columns} columns and {num_rows} rows',
                'reasoning': 'The Data Processor Agent examines each field to identify sensitive information that must be replaced with synthetic data for GDPR compliance.'
            },
            'field_classification': {
                'plain_language': 'Analyzing field "{field_name}" to determine if it contains sensitive personal information',
                'reasoning': 'Using multiple classification methods: pattern matching for common PII formats (emails, phones), field name analysis, content characteristics, and organizational knowledge base queries.'
            },
            'pattern_detected': {
                'plain_language': 'Detected {pii_type} pattern in field "{field_name}" with {confidence}% confidence',
                'reasoning': 'Pattern matching found {match_count} values matching {pii_type} format out of {sample_size} samples. Examples: {examples}'
            },
            'name_match': {
                'plain_language': 'Field name "{field_name}" indicates {pii_type} data',
                'reasoning': 'The field name contains keyword "{keyword}" which is a strong indicator of {pii_type} information.'
            },
            'confluence_query': {
                'plain_language': 'Searching organizational knowledge base for documentation about "{field_name}"',
                'reasoning': 'Querying Confluence to find data dictionaries and field definitions that may clarify whether this field contains sensitive information.'
            },
            'confluence_found': {
                'plain_language': 'Found {doc_count} relevant documentation pages for "{field_name}"',
                'reasoning': 'Documentation indicates this is a {pii_type} field. References: {doc_titles}'
            },
            'field_classified_sensitive': {
                'plain_language': 'Field "{field_name}" classified as SENSITIVE ({pii_type}) with {confidence}% confidence',
                'reasoning': 'Classification based on: {reasoning_summary}. Recommended strategy: {strategy}'
            },
            'field_classified_non_sensitive': {
                'plain_language': 'Field "{field_name}" classified as NON-SENSITIVE with {confidence}% confidence',
                'reasoning': 'No PII patterns detected. This field will be processed using statistical methods to preserve data distributions.'
            },
            'analysis_complete': {
                'plain_language': 'Analysis complete: {sensitive_count} of {total_count} fields identified as sensitive',
                'reasoning': 'Sensitive fields will be replaced with synthetic data using appropriate generation strategies. Non-sensitive fields will use statistical synthesis to preserve distributions.'
            }
        }


class SyntheticDataExplanations(ExplanationTemplate):
    """Explanation templates for Synthetic Data Agent."""
    
    def __init__(self):
        super().__init__("Synthetic Data Agent")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'start_generation': {
                'plain_language': 'Starting synthetic data generation for {num_records} records using {sdv_model} model',
                'reasoning': 'The Synthetic Data Agent creates artificial data that mimics production statistics while ensuring no real customer data is exposed.'
            },
            'sdv_training': {
                'plain_language': 'Training {sdv_model} model on {num_fields} non-sensitive fields',
                'reasoning': 'SDV (Synthetic Data Vault) learns statistical properties including distributions, correlations, and value frequencies from production data.'
            },
            'sdv_sampling': {
                'plain_language': 'Generating {num_records} synthetic records using trained model',
                'reasoning': 'The model creates new records that maintain statistical properties of production data without copying actual values.'
            },
            'bedrock_text_generation': {
                'plain_language': 'Generating realistic {field_type} values for field "{field_name}" using Amazon Bedrock LLM',
                'reasoning': 'Using AI to create contextually appropriate text that matches the field type and related data patterns.'
            },
            'bedrock_batch': {
                'plain_language': 'Processing batch of {batch_size} {field_type} values (batch {batch_num} of {total_batches})',
                'reasoning': 'Batching API calls for efficiency. Each batch generates multiple values in a single request to reduce latency and cost.'
            },
            'rule_based_generation': {
                'plain_language': 'Generating {field_type} values using rule-based algorithm for field "{field_name}"',
                'reasoning': 'Using deterministic rules to create valid {field_type} formats (e.g., valid phone numbers, SSN formats) that are mathematically distinct from production data.'
            },
            'edge_case_injection': {
                'plain_language': 'Injecting {edge_case_count} edge cases ({edge_case_type}) at {frequency}% frequency',
                'reasoning': 'Adding intentional anomalies to test error handling: {edge_case_examples}'
            },
            'quality_evaluation': {
                'plain_language': 'Evaluating synthetic data quality using statistical tests',
                'reasoning': 'Comparing distributions, correlations, and patterns between production and synthetic data to ensure realistic output.'
            },
            'quality_score': {
                'plain_language': 'Quality Score: {score}/100 - {interpretation}',
                'reasoning': 'SDV Quality Score of {score} indicates {interpretation}. Column Shapes: {col_shapes}, Column Pair Trends: {col_trends}'
            },
            'generation_complete': {
                'plain_language': 'Generated {num_records} synthetic records with {quality_score}/100 quality score',
                'reasoning': 'Synthetic dataset maintains statistical properties of production data while ensuring GDPR compliance through complete data replacement.'
            }
        }


class DistributionExplanations(ExplanationTemplate):
    """Explanation templates for Distribution Agent."""
    
    def __init__(self):
        super().__init__("Distribution Agent")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'start_distribution': {
                'plain_language': 'Starting data distribution to {target_count} target systems',
                'reasoning': 'The Distribution Agent loads synthetic data into test environments, ensuring data is available for automated testing.'
            },
            'target_connection': {
                'plain_language': 'Connecting to {target_type} target: {target_name}',
                'reasoning': 'Establishing connection using provided credentials and configuration.'
            },
            'fk_analysis': {
                'plain_language': 'Analyzing foreign key relationships across {table_count} tables',
                'reasoning': 'Determining load order to respect referential integrity constraints. Parent tables must be loaded before child tables.'
            },
            'fk_order': {
                'plain_language': 'Load order determined: {table_order}',
                'reasoning': 'Tables will be loaded in topological order to satisfy foreign key constraints.'
            },
            'table_load_start': {
                'plain_language': 'Loading {record_count} records into table "{table_name}"',
                'reasoning': 'Using {load_strategy} strategy to insert data into target system.'
            },
            'table_load_complete': {
                'plain_language': 'Successfully loaded {record_count} records into "{table_name}" in {duration}s',
                'reasoning': 'Data is now available in the test environment for automated testing.'
            },
            'salesforce_bulk': {
                'plain_language': 'Using Salesforce Bulk API to load {record_count} records',
                'reasoning': 'Bulk API provides efficient loading for large datasets with automatic batching and retry logic.'
            },
            'api_load': {
                'plain_language': 'Posting {record_count} records to REST API endpoint: {endpoint}',
                'reasoning': 'Sending data via HTTP POST requests with appropriate authentication and headers.'
            },
            'load_error': {
                'plain_language': 'Error loading data to {target_name}: {error_message}',
                'reasoning': 'Load failed but workflow continues with remaining targets. Error details logged for troubleshooting.'
            },
            'distribution_complete': {
                'plain_language': 'Distribution complete: {success_count} of {total_count} targets loaded successfully',
                'reasoning': 'Synthetic data is now available in test environments. Failed targets: {failed_targets}'
            }
        }


class TestCaseExplanations(ExplanationTemplate):
    """Explanation templates for Test Case Agent."""
    
    def __init__(self):
        super().__init__("Test Case Agent")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'start_test_generation': {
                'plain_language': 'Retrieving test scenarios from Jira with tag "{test_tag}"',
                'reasoning': 'The Test Case Agent converts high-level test scenarios into executable automated tests.'
            },
            'jira_query': {
                'plain_language': 'Found {scenario_count} test scenarios in Jira',
                'reasoning': 'Each scenario will be analyzed and converted into executable test code for the selected framework.'
            },
            'scenario_parsing': {
                'plain_language': 'Parsing test scenario: "{scenario_title}"',
                'reasoning': 'Extracting test objectives, preconditions, steps, and expected outcomes from scenario description.'
            },
            'test_code_generation': {
                'plain_language': 'Generating {framework} test code for scenario "{scenario_title}"',
                'reasoning': 'Using AI to create executable test script that implements the scenario steps and validates expected outcomes.'
            },
            'data_mapping': {
                'plain_language': 'Mapping test data references to synthetic dataset',
                'reasoning': 'Linking test cases to specific synthetic records: {data_refs}'
            },
            'test_case_created': {
                'plain_language': 'Created test case "{test_name}" with {step_count} steps',
                'reasoning': 'Test case includes setup, execution steps, assertions, and teardown. Data references: {data_refs}'
            },
            'generation_complete': {
                'plain_language': 'Generated {test_count} executable test cases for {framework}',
                'reasoning': 'Test cases are ready for execution by the Test Execution Agent.'
            }
        }


class TestExecutionExplanations(ExplanationTemplate):
    """Explanation templates for Test Execution Agent."""
    
    def __init__(self):
        super().__init__("Test Execution Agent")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'start_execution': {
                'plain_language': 'Starting execution of {test_count} test cases using {framework}',
                'reasoning': 'The Test Execution Agent runs automated tests and captures results, logs, and screenshots.'
            },
            'framework_setup': {
                'plain_language': 'Configuring {framework} with browser drivers and environment settings',
                'reasoning': 'Setting up test automation framework with appropriate timeouts, browser configuration, and test data access.'
            },
            'test_start': {
                'plain_language': 'Executing test: "{test_name}"',
                'reasoning': 'Running test steps and validating expected outcomes against actual results.'
            },
            'test_passed': {
                'plain_language': 'Test PASSED: "{test_name}" completed in {duration}s',
                'reasoning': 'All assertions passed. Test validated expected behavior with synthetic data.'
            },
            'test_failed': {
                'plain_language': 'Test FAILED: "{test_name}" - {failure_reason}',
                'reasoning': 'Assertion failed or error occurred. Screenshot and logs captured for analysis. Creating Jira issue.'
            },
            'screenshot_captured': {
                'plain_language': 'Captured screenshot at failure point',
                'reasoning': 'Screenshot provides visual context for debugging the test failure.'
            },
            'jira_issue_created': {
                'plain_language': 'Created Jira issue {issue_key} for test failure',
                'reasoning': 'Issue includes failure details, logs, screenshots, and link to original test scenario.'
            },
            'jira_update': {
                'plain_language': 'Updated Jira scenario {scenario_key} with execution results',
                'reasoning': 'Test scenario status updated to reflect latest execution outcome.'
            },
            'execution_complete': {
                'plain_language': 'Execution complete: {passed_count} passed, {failed_count} failed out of {total_count} tests',
                'reasoning': 'Test results provide validation of system behavior with synthetic data. Pass rate: {pass_rate}%'
            }
        }


class ExplanationGenerator:
    """Main explanation generator that coordinates all agent explanations."""
    
    def __init__(self):
        self.templates = {
            'data_processor': DataProcessorExplanations(),
            'synthetic_data': SyntheticDataExplanations(),
            'distribution': DistributionExplanations(),
            'test_case': TestCaseExplanations(),
            'test_execution': TestExecutionExplanations()
        }
    
    def generate(self, agent_name: str, action: str, context: Dict[str, Any]) -> Explanation:
        """Generate explanation for an agent action.
        
        Args:
            agent_name: Name of the agent (data_processor, synthetic_data, etc.)
            action: Action being performed
            context: Context data for template formatting
            
        Returns:
            Explanation object with plain-language description and reasoning
        """
        template = self.templates.get(agent_name)
        if not template:
            return Explanation(
                agent_name=agent_name,
                action=action,
                plain_language=f"Agent {agent_name} is performing action: {action}",
                reasoning="No detailed explanation template available for this action."
            )
        
        return template.generate(action, context)
    
    def generate_progress_message(self, agent_name: str, progress: float, current_action: str, context: Dict[str, Any]) -> str:
        """Generate contextual progress message.
        
        Args:
            agent_name: Name of the agent
            progress: Progress percentage (0.0 to 1.0)
            current_action: Current action being performed
            context: Context data for message formatting
            
        Returns:
            Contextual progress message
        """
        percentage = int(progress * 100)
        
        # Generate action-specific progress message
        explanation = self.generate(agent_name, current_action, context)
        
        return f"[{percentage}%] {explanation.plain_language}"
    
    def generate_comparison(self, before: Dict[str, Any], after: Dict[str, Any], highlights: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate before/after comparison with highlights.
        
        Args:
            before: State before transformation
            after: State after transformation
            highlights: List of keys to highlight as changed
            
        Returns:
            Comparison data structure with highlights
        """
        if highlights is None:
            # Auto-detect changes
            highlights = []
            for key in set(list(before.keys()) + list(after.keys())):
                if before.get(key) != after.get(key):
                    highlights.append(key)
        
        return {
            'before': before,
            'after': after,
            'highlights': highlights,
            'changes': [
                {
                    'field': key,
                    'before_value': before.get(key),
                    'after_value': after.get(key),
                    'change_type': self._classify_change(before.get(key), after.get(key))
                }
                for key in highlights
            ]
        }
    
    def _classify_change(self, before_value: Any, after_value: Any) -> str:
        """Classify the type of change between two values."""
        if before_value is None and after_value is not None:
            return 'added'
        elif before_value is not None and after_value is None:
            return 'removed'
        elif before_value != after_value:
            return 'modified'
        else:
            return 'unchanged'
    
    def format_decision_reasoning(self, decision: str, factors: List[Dict[str, Any]], conclusion: str) -> Dict[str, Any]:
        """Format decision reasoning for display.
        
        Args:
            decision: The decision that was made
            factors: List of factors that influenced the decision
            conclusion: Final conclusion/reasoning
            
        Returns:
            Formatted decision reasoning structure
        """
        return {
            'decision': decision,
            'factors': factors,
            'conclusion': conclusion,
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
_explanation_generator = None


def get_explanation_generator() -> ExplanationGenerator:
    """Get the singleton explanation generator instance."""
    global _explanation_generator
    if _explanation_generator is None:
        _explanation_generator = ExplanationGenerator()
    return _explanation_generator
