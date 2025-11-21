"""Demo of plain-language explanation system for agent actions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.utils.explanation_generator import (
    get_explanation_generator,
    Explanation
)
import json


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_explanation(explanation: Explanation):
    """Print an explanation in a formatted way."""
    print(f"\n🤖 Agent: {explanation.agent_name}")
    print(f"📋 Action: {explanation.action}")
    print(f"\n💬 Plain Language:")
    print(f"   {explanation.plain_language}")
    print(f"\n🧠 Reasoning:")
    print(f"   {explanation.reasoning}")
    
    if explanation.highlights:
        print(f"\n✨ Highlights:")
        for highlight in explanation.highlights:
            print(f"   • {highlight}")
    
    print()


def demo_data_processor_explanations():
    """Demonstrate Data Processor Agent explanations."""
    print_section("Data Processor Agent Explanations")
    
    generator = get_explanation_generator()
    
    # Start analysis
    exp1 = generator.generate('data_processor', 'start_analysis', {
        'num_columns': 50,
        'num_rows': 10000
    })
    print_explanation(exp1)
    
    # Field classification
    exp2 = generator.generate('data_processor', 'field_classification', {
        'field_name': 'customer_email'
    })
    print_explanation(exp2)
    
    # Pattern detected
    exp3 = generator.generate('data_processor', 'pattern_detected', {
        'pii_type': 'email',
        'field_name': 'customer_email',
        'confidence': 95,
        'match_count': 9500,
        'sample_size': 10000,
        'examples': 'user@example.com, test@test.org, admin@company.co.uk'
    })
    print_explanation(exp3)
    
    # Confluence query
    exp4 = generator.generate('data_processor', 'confluence_query', {
        'field_name': 'customer_email'
    })
    print_explanation(exp4)
    
    # Confluence found
    exp5 = generator.generate('data_processor', 'confluence_found', {
        'doc_count': 3,
        'field_name': 'customer_email',
        'pii_type': 'email',
        'doc_titles': 'Customer Data Dictionary, Email Field Standards, PII Classification Guide'
    })
    print_explanation(exp5)
    
    # Field classified as sensitive
    exp6 = generator.generate('data_processor', 'field_classified_sensitive', {
        'field_name': 'customer_email',
        'pii_type': 'email',
        'confidence': 95,
        'reasoning_summary': 'pattern matching (95%), name-based (85%), Confluence documentation (90%)',
        'strategy': 'bedrock_text'
    })
    print_explanation(exp6)
    
    # Analysis complete
    exp7 = generator.generate('data_processor', 'analysis_complete', {
        'sensitive_count': 12,
        'total_count': 50
    })
    print_explanation(exp7)


def demo_synthetic_data_explanations():
    """Demonstrate Synthetic Data Agent explanations."""
    print_section("Synthetic Data Agent Explanations")
    
    generator = get_explanation_generator()
    
    # Start generation
    exp1 = generator.generate('synthetic_data', 'start_generation', {
        'num_records': 10000,
        'sdv_model': 'GaussianCopula'
    })
    print_explanation(exp1)
    
    # SDV training
    exp2 = generator.generate('synthetic_data', 'sdv_training', {
        'sdv_model': 'GaussianCopula',
        'num_fields': 38
    })
    print_explanation(exp2)
    
    # Bedrock text generation
    exp3 = generator.generate('synthetic_data', 'bedrock_text_generation', {
        'field_type': 'email',
        'field_name': 'customer_email'
    })
    print_explanation(exp3)
    
    # Bedrock batch
    exp4 = generator.generate('synthetic_data', 'bedrock_batch', {
        'batch_size': 100,
        'field_type': 'email',
        'batch_num': 5,
        'total_batches': 100
    })
    print_explanation(exp4)
    
    # Edge case injection
    exp5 = generator.generate('synthetic_data', 'edge_case_injection', {
        'edge_case_count': 50,
        'edge_case_type': 'malformed_email',
        'frequency': 5,
        'edge_case_examples': 'missing@, @nodomain, spaces in email@test.com'
    })
    print_explanation(exp5)
    
    # Quality score
    exp6 = generator.generate('synthetic_data', 'quality_score', {
        'score': 87,
        'interpretation': 'Good quality - synthetic data closely matches production distributions',
        'col_shapes': 0.92,
        'col_trends': 0.85
    })
    print_explanation(exp6)
    
    # Generation complete
    exp7 = generator.generate('synthetic_data', 'generation_complete', {
        'num_records': 10000,
        'quality_score': 87
    })
    print_explanation(exp7)


def demo_distribution_explanations():
    """Demonstrate Distribution Agent explanations."""
    print_section("Distribution Agent Explanations")
    
    generator = get_explanation_generator()
    
    # Start distribution
    exp1 = generator.generate('distribution', 'start_distribution', {
        'target_count': 3
    })
    print_explanation(exp1)
    
    # FK analysis
    exp2 = generator.generate('distribution', 'fk_analysis', {
        'table_count': 5
    })
    print_explanation(exp2)
    
    # FK order
    exp3 = generator.generate('distribution', 'fk_order', {
        'table_order': 'customers → orders → order_items'
    })
    print_explanation(exp3)
    
    # Table load
    exp4 = generator.generate('distribution', 'table_load_start', {
        'record_count': 10000,
        'table_name': 'customers',
        'load_strategy': 'truncate-insert'
    })
    print_explanation(exp4)
    
    # Table load complete
    exp5 = generator.generate('distribution', 'table_load_complete', {
        'record_count': 10000,
        'table_name': 'customers',
        'duration': 2.5
    })
    print_explanation(exp5)
    
    # Distribution complete
    exp6 = generator.generate('distribution', 'distribution_complete', {
        'success_count': 3,
        'total_count': 3,
        'failed_targets': 'none'
    })
    print_explanation(exp6)


def demo_test_case_explanations():
    """Demonstrate Test Case Agent explanations."""
    print_section("Test Case Agent Explanations")
    
    generator = get_explanation_generator()
    
    # Start test generation
    exp1 = generator.generate('test_case', 'start_test_generation', {
        'test_tag': 'sprint-23-regression'
    })
    print_explanation(exp1)
    
    # Jira query
    exp2 = generator.generate('test_case', 'jira_query', {
        'scenario_count': 15
    })
    print_explanation(exp2)
    
    # Scenario parsing
    exp3 = generator.generate('test_case', 'scenario_parsing', {
        'scenario_title': 'Verify customer registration with valid email'
    })
    print_explanation(exp3)
    
    # Test code generation
    exp4 = generator.generate('test_case', 'test_code_generation', {
        'framework': 'Playwright',
        'scenario_title': 'Verify customer registration with valid email'
    })
    print_explanation(exp4)
    
    # Test case created
    exp5 = generator.generate('test_case', 'test_case_created', {
        'test_name': 'test_customer_registration_valid_email',
        'step_count': 8,
        'data_refs': 'customer_001, customer_002'
    })
    print_explanation(exp5)
    
    # Generation complete
    exp6 = generator.generate('test_case', 'generation_complete', {
        'test_count': 15,
        'framework': 'Playwright'
    })
    print_explanation(exp6)


def demo_test_execution_explanations():
    """Demonstrate Test Execution Agent explanations."""
    print_section("Test Execution Agent Explanations")
    
    generator = get_explanation_generator()
    
    # Start execution
    exp1 = generator.generate('test_execution', 'start_execution', {
        'test_count': 15,
        'framework': 'Playwright'
    })
    print_explanation(exp1)
    
    # Test passed
    exp2 = generator.generate('test_execution', 'test_passed', {
        'test_name': 'test_customer_registration_valid_email',
        'duration': 3.2
    })
    print_explanation(exp2)
    
    # Test failed
    exp3 = generator.generate('test_execution', 'test_failed', {
        'test_name': 'test_customer_login_invalid_password',
        'failure_reason': 'Expected error message not displayed'
    })
    print_explanation(exp3)
    
    # Jira issue created
    exp4 = generator.generate('test_execution', 'jira_issue_created', {
        'issue_key': 'BUG-1234'
    })
    print_explanation(exp4)
    
    # Execution complete
    exp5 = generator.generate('test_execution', 'execution_complete', {
        'passed_count': 13,
        'failed_count': 2,
        'total_count': 15,
        'pass_rate': 87
    })
    print_explanation(exp5)


def demo_progress_messages():
    """Demonstrate contextual progress messages."""
    print_section("Contextual Progress Messages")
    
    generator = get_explanation_generator()
    
    print("\n📊 Progress Messages During Workflow:\n")
    
    # Data Processor progress
    msg1 = generator.generate_progress_message('data_processor', 0.25, 'field_classification', {
        'field_name': 'customer_email'
    })
    print(msg1)
    
    # Synthetic Data progress
    msg2 = generator.generate_progress_message('synthetic_data', 0.50, 'bedrock_batch', {
        'batch_size': 100,
        'field_type': 'email',
        'batch_num': 50,
        'total_batches': 100
    })
    print(msg2)
    
    # Distribution progress
    msg3 = generator.generate_progress_message('distribution', 0.75, 'table_load_start', {
        'record_count': 10000,
        'table_name': 'customers',
        'load_strategy': 'truncate-insert'
    })
    print(msg3)
    
    # Test Execution progress
    msg4 = generator.generate_progress_message('test_execution', 0.90, 'test_start', {
        'test_name': 'test_customer_registration_valid_email'
    })
    print(msg4)


def demo_before_after_comparison():
    """Demonstrate before/after comparison with highlights."""
    print_section("Before/After Comparison with Highlights")
    
    generator = get_explanation_generator()
    
    # Example: Field transformation
    before = {
        'customer_email': 'john.doe@example.com',
        'customer_phone': '555-123-4567',
        'customer_name': 'John Doe',
        'account_balance': 1250.50,
        'account_status': 'active'
    }
    
    after = {
        'customer_email': 'synthetic.user.847@testmail.com',
        'customer_phone': '555-987-6543',
        'customer_name': 'Jane Smith',
        'account_balance': 1250.50,
        'account_status': 'active'
    }
    
    comparison = generator.generate_comparison(before, after, 
                                               highlights=['customer_email', 'customer_phone', 'customer_name'])
    
    print("\n🔄 Data Transformation Comparison:\n")
    print("Before (Production Data):")
    print(json.dumps(comparison['before'], indent=2))
    
    print("\nAfter (Synthetic Data):")
    print(json.dumps(comparison['after'], indent=2))
    
    print("\n✨ Highlighted Changes:")
    for change in comparison['changes']:
        print(f"\n  Field: {change['field']}")
        print(f"  Change Type: {change['change_type']}")
        print(f"  Before: {change['before_value']}")
        print(f"  After: {change['after_value']}")


def demo_decision_reasoning():
    """Demonstrate decision reasoning display."""
    print_section("Decision Reasoning Display")
    
    generator = get_explanation_generator()
    
    # Example: Classification decision
    decision_reasoning = generator.format_decision_reasoning(
        decision="Classify 'customer_email' as SENSITIVE (email)",
        factors=[
            {
                'classifier': 'Pattern Matching',
                'confidence': 0.95,
                'reasoning': 'Found email pattern in 95% of samples'
            },
            {
                'classifier': 'Name-Based',
                'confidence': 0.85,
                'reasoning': 'Field name contains keyword "email"'
            },
            {
                'classifier': 'Confluence Knowledge',
                'confidence': 0.90,
                'reasoning': 'Documentation confirms this is an email field containing customer contact information'
            },
            {
                'classifier': 'Content Analysis',
                'confidence': 0.60,
                'reasoning': 'High uniqueness (98%) and special characters (@) suggest PII'
            }
        ],
        conclusion="Aggregated confidence: 95%. Field classified as SENSITIVE. Recommended strategy: bedrock_text generation for realistic synthetic emails."
    )
    
    print("\n🎯 Decision: Classification of 'customer_email' field\n")
    print(f"Decision: {decision_reasoning['decision']}")
    print(f"\nFactors Considered:")
    for i, factor in enumerate(decision_reasoning['factors'], 1):
        print(f"\n  {i}. {factor['classifier']} (Confidence: {factor['confidence']:.0%})")
        print(f"     {factor['reasoning']}")
    
    print(f"\n✅ Conclusion:")
    print(f"   {decision_reasoning['conclusion']}")
    print(f"\n⏰ Timestamp: {decision_reasoning['timestamp']}")


def main():
    """Run all explanation demos."""
    print("\n" + "=" * 80)
    print("  PLAIN-LANGUAGE EXPLANATION SYSTEM DEMO")
    print("  Demonstrating transparent, understandable agent actions")
    print("=" * 80)
    
    demo_data_processor_explanations()
    demo_synthetic_data_explanations()
    demo_distribution_explanations()
    demo_test_case_explanations()
    demo_test_execution_explanations()
    demo_progress_messages()
    demo_before_after_comparison()
    demo_decision_reasoning()
    
    print("\n" + "=" * 80)
    print("  Demo Complete!")
    print("  The explanation system provides transparent, plain-language")
    print("  descriptions of all agent actions, decisions, and transformations.")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
