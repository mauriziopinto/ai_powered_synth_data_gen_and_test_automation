"""Demo script for Data Processor Agent."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.data_processor import DataProcessorAgent


def main():
    """Run demo of Data Processor Agent."""
    # Path to sample data
    sample_file = Path('.kiro/specs/synthetic-data-generator/MGW_File.csv')
    
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return
    
    print("=" * 80)
    print("Data Processor Agent Demo")
    print("=" * 80)
    print(f"\nProcessing file: {sample_file}")
    
    # Create and run agent
    agent = DataProcessorAgent()
    report = agent.process(sample_file)
    
    # Display summary
    print(f"\n{'=' * 80}")
    print("SENSITIVITY REPORT SUMMARY")
    print("=" * 80)
    print(f"Total fields analyzed: {report.total_fields}")
    print(f"Sensitive fields found: {report.sensitive_fields}")
    print(f"Non-sensitive fields: {report.total_fields - report.sensitive_fields}")
    print(f"\nConfidence distribution:")
    print(f"  High confidence (≥0.8): {report.confidence_distribution['high']}")
    print(f"  Medium confidence (0.5-0.8): {report.confidence_distribution['medium']}")
    print(f"  Low confidence (<0.5): {report.confidence_distribution['low']}")
    
    # Display sensitive fields
    print(f"\n{'=' * 80}")
    print("SENSITIVE FIELDS DETECTED")
    print("=" * 80)
    
    sensitive_fields = sorted(
        [(name, report.classifications[name]) for name in report.get_sensitive_fields()],
        key=lambda x: x[1].confidence,
        reverse=True
    )
    
    for field_name, classification in sensitive_fields:
        print(f"\n{field_name}")
        print(f"  Type: {classification.sensitivity_type}")
        print(f"  Confidence: {classification.confidence:.2%}")
        print(f"  Recommended Strategy: {classification.recommended_strategy}")
        print(f"  Reasoning: {classification.reasoning[:120]}...")
        if classification.pattern_matches:
            print(f"  Sample matches: {classification.pattern_matches[:3]}")
    
    # Display some non-sensitive fields
    print(f"\n{'=' * 80}")
    print("SAMPLE NON-SENSITIVE FIELDS")
    print("=" * 80)
    
    non_sensitive = report.get_non_sensitive_fields()[:5]
    for field_name in non_sensitive:
        classification = report.classifications[field_name]
        print(f"\n{field_name}")
        print(f"  Type: {classification.sensitivity_type}")
        print(f"  Confidence: {classification.confidence:.2%}")
        print(f"  Reasoning: {classification.reasoning[:120]}...")
    
    # Save report
    output_file = Path('sensitivity_report.json')
    with open(output_file, 'w') as f:
        f.write(report.to_json())
    
    print(f"\n{'=' * 80}")
    print(f"Report saved to: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
