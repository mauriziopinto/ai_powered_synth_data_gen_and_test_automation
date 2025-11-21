"""Demo showing end-to-end integration of explanation system with agents."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.data_processor.agent import DataProcessorAgent
from shared.utils.confluence_client import MockConfluenceClient
from shared.utils.explanation_generator import Explanation
from typing import List


class ExplanationCollector:
    """Collects explanations emitted by agents."""
    
    def __init__(self):
        self.explanations: List[Explanation] = []
    
    def collect(self, explanation: Explanation):
        """Collect an explanation."""
        self.explanations.append(explanation)
        
        # Print in real-time
        print(f"\n{'='*80}")
        print(f"🤖 {explanation.agent_name}")
        print(f"📋 {explanation.action}")
        print(f"\n💬 {explanation.plain_language}")
        print(f"\n🧠 {explanation.reasoning}")
        print('='*80)


def demo_data_processor_with_explanations():
    """Demonstrate Data Processor Agent with explanation system."""
    print("\n" + "="*80)
    print("  DATA PROCESSOR AGENT WITH EXPLANATIONS")
    print("  Real-time transparent processing")
    print("="*80)
    
    # Create explanation collector
    collector = ExplanationCollector()
    
    # Create agent with explanation callback
    confluence_client = MockConfluenceClient()
    agent = DataProcessorAgent(
        confluence_client=confluence_client,
        explanation_callback=collector.collect
    )
    
    # Process sample data
    data_file = Path('MGW_File.csv')
    
    if data_file.exists():
        print(f"\n📂 Processing file: {data_file}")
        print("   Watch as the agent explains each step...\n")
        
        # Process (this will emit explanations)
        report = agent.process(data_file)
        
        # Summary
        print(f"\n{'='*80}")
        print("  PROCESSING COMPLETE")
        print('='*80)
        print(f"\n📊 Summary:")
        print(f"   Total fields analyzed: {report.total_fields}")
        print(f"   Sensitive fields found: {report.sensitive_fields}")
        print(f"   Explanations generated: {len(collector.explanations)}")
        
        print(f"\n✨ Explanation Types:")
        action_counts = {}
        for exp in collector.explanations:
            action_counts[exp.action] = action_counts.get(exp.action, 0) + 1
        
        for action, count in sorted(action_counts.items()):
            print(f"   • {action}: {count}")
        
        print(f"\n🎯 Sensitive Fields Identified:")
        for field_name, classification in report.classifications.items():
            if classification.is_sensitive:
                print(f"   • {field_name}: {classification.sensitivity_type} "
                      f"({classification.confidence:.0%} confidence)")
    else:
        print(f"\n⚠️  Sample file not found: {data_file}")
        print("   This demo requires the MGW_File.csv sample data.")


def demo_explanation_replay():
    """Demonstrate replaying explanations (useful for debugging/analysis)."""
    print("\n" + "="*80)
    print("  EXPLANATION REPLAY")
    print("  Review all explanations after processing")
    print("="*80)
    
    collector = ExplanationCollector()
    
    # Simulate some explanations
    from shared.utils.explanation_generator import get_explanation_generator
    generator = get_explanation_generator()
    
    # Simulate a workflow
    explanations = [
        generator.generate('data_processor', 'start_analysis', {
            'num_columns': 50,
            'num_rows': 10000
        }),
        generator.generate('data_processor', 'field_classification', {
            'field_name': 'customer_email'
        }),
        generator.generate('data_processor', 'pattern_detected', {
            'pii_type': 'email',
            'field_name': 'customer_email',
            'confidence': 95,
            'match_count': 9500,
            'sample_size': 10000,
            'examples': 'user@example.com, test@test.org'
        }),
        generator.generate('data_processor', 'field_classified_sensitive', {
            'field_name': 'customer_email',
            'pii_type': 'email',
            'confidence': 95,
            'reasoning_summary': 'pattern matching (95%), name-based (85%)',
            'strategy': 'bedrock_text'
        }),
        generator.generate('synthetic_data', 'start_generation', {
            'num_records': 10000,
            'sdv_model': 'GaussianCopula'
        }),
        generator.generate('synthetic_data', 'bedrock_text_generation', {
            'field_type': 'email',
            'field_name': 'customer_email'
        }),
        generator.generate('synthetic_data', 'generation_complete', {
            'num_records': 10000,
            'quality_score': 87
        })
    ]
    
    print("\n📼 Replaying workflow explanations:\n")
    
    for i, exp in enumerate(explanations, 1):
        print(f"\n[{i}/{len(explanations)}] {exp.agent_name} → {exp.action}")
        print(f"    {exp.plain_language}")
        
        if i < len(explanations):
            print("    ↓")
    
    print("\n✅ Workflow replay complete")


def demo_explanation_filtering():
    """Demonstrate filtering explanations by agent or action."""
    print("\n" + "="*80)
    print("  EXPLANATION FILTERING")
    print("  Filter explanations by agent or action type")
    print("="*80)
    
    from shared.utils.explanation_generator import get_explanation_generator
    generator = get_explanation_generator()
    
    # Generate mixed explanations
    all_explanations = [
        generator.generate('data_processor', 'start_analysis', {'num_columns': 50, 'num_rows': 10000}),
        generator.generate('data_processor', 'field_classification', {'field_name': 'email'}),
        generator.generate('synthetic_data', 'start_generation', {'num_records': 10000, 'sdv_model': 'GaussianCopula'}),
        generator.generate('data_processor', 'analysis_complete', {'sensitive_count': 12, 'total_count': 50}),
        generator.generate('synthetic_data', 'generation_complete', {'num_records': 10000, 'quality_score': 87}),
        generator.generate('distribution', 'start_distribution', {'target_count': 3}),
    ]
    
    # Filter by agent
    print("\n🔍 Filter: Data Processor Agent only")
    data_processor_exps = [e for e in all_explanations if e.agent_name == "Data Processor Agent"]
    for exp in data_processor_exps:
        print(f"   • {exp.action}: {exp.plain_language}")
    
    # Filter by action type
    print("\n🔍 Filter: 'start_*' actions only")
    start_exps = [e for e in all_explanations if e.action.startswith('start_')]
    for exp in start_exps:
        print(f"   • {exp.agent_name} → {exp.plain_language}")
    
    # Filter by completion actions
    print("\n🔍 Filter: '*_complete' actions only")
    complete_exps = [e for e in all_explanations if e.action.endswith('_complete')]
    for exp in complete_exps:
        print(f"   • {exp.agent_name} → {exp.plain_language}")


def main():
    """Run all integration demos."""
    print("\n" + "="*80)
    print("  EXPLANATION SYSTEM INTEGRATION DEMO")
    print("  Showing real-world usage with agents")
    print("="*80)
    
    # Demo 1: Real agent integration
    demo_data_processor_with_explanations()
    
    # Demo 2: Explanation replay
    demo_explanation_replay()
    
    # Demo 3: Explanation filtering
    demo_explanation_filtering()
    
    print("\n" + "="*80)
    print("  Integration Demo Complete!")
    print("  The explanation system seamlessly integrates with agents")
    print("  to provide transparent, real-time workflow visibility.")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
