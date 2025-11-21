"""
Demo: Guided Demo Mode

This example demonstrates the guided demo mode functionality,
showing how pre-configured scenarios can be used for presentations.

Validates Requirements 26.1, 26.2, 26.3, 26.4, 26.5
"""

import json
from datetime import datetime
from typing import Dict, Any, List


class DemoScenario:
    """Pre-configured demo scenario"""
    
    def __init__(
        self,
        scenario_id: str,
        name: str,
        description: str,
        industry: str,
        steps: List[Dict[str, Any]]
    ):
        self.scenario_id = scenario_id
        self.name = name
        self.description = description
        self.industry = industry
        self.steps = steps
        self.estimated_duration = sum(step['duration'] for step in steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary"""
        return {
            'id': self.scenario_id,
            'name': self.name,
            'description': self.description,
            'industry': self.industry,
            'steps': self.steps,
            'estimated_duration': self.estimated_duration
        }


class DemoStateManager:
    """Manages demo playback state"""
    
    def __init__(self, scenario: DemoScenario):
        self.scenario = scenario
        self.current_step_index = 0
        self.is_playing = False
        self.is_paused = False
        self.playback_speed = 1.0
        self.started_at = None
        self.completed_steps = []
    
    def play(self):
        """Start or resume playback"""
        self.is_playing = True
        self.is_paused = False
        if not self.started_at:
            self.started_at = datetime.now()
        print(f"▶️  Playing demo: {self.scenario.name}")
    
    def pause(self):
        """Pause playback"""
        self.is_paused = True
        print("⏸️  Demo paused")
    
    def step_forward(self):
        """Advance to next step"""
        if self.current_step_index < len(self.scenario.steps) - 1:
            self.current_step_index += 1
            current_step = self.scenario.steps[self.current_step_index]
            self.completed_steps.append(current_step['id'])
            print(f"⏭️  Advanced to step {self.current_step_index + 1}: {current_step['title']}")
            return current_step
        else:
            print("⏹️  Demo complete")
            return None
    
    def step_backward(self):
        """Go back to previous step"""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            current_step = self.scenario.steps[self.current_step_index]
            if current_step['id'] in self.completed_steps:
                self.completed_steps.remove(current_step['id'])
            print(f"⏮️  Went back to step {self.current_step_index + 1}: {current_step['title']}")
            return current_step
        else:
            print("⏹️  Already at first step")
            return None
    
    def restart(self):
        """Restart demo from beginning"""
        self.current_step_index = 0
        self.is_playing = False
        self.is_paused = False
        self.completed_steps = []
        self.started_at = None
        print("🔄 Demo restarted")
    
    def set_speed(self, speed: float):
        """Set playback speed"""
        self.playback_speed = speed
        print(f"⚡ Playback speed set to {speed}x")
    
    def get_current_step(self) -> Dict[str, Any]:
        """Get current step"""
        return self.scenario.steps[self.current_step_index]
    
    def get_progress(self) -> Dict[str, Any]:
        """Get demo progress"""
        total_steps = len(self.scenario.steps)
        completed = len(self.completed_steps)
        progress_percent = (completed / total_steps) * 100
        
        return {
            'current_step': self.current_step_index + 1,
            'total_steps': total_steps,
            'completed_steps': completed,
            'progress_percent': progress_percent,
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'playback_speed': self.playback_speed
        }


def create_telecom_scenario() -> DemoScenario:
    """Create pre-configured telecom demo scenario"""
    
    steps = [
        {
            'id': 'step-1',
            'title': 'Load Production Data',
            'description': 'Loading sample telecom customer data',
            'narration': 'We start by loading production customer data containing sensitive PII.',
            'duration': 5,
            'callouts': [
                {
                    'type': 'info',
                    'title': 'Production Data Source',
                    'content': 'Sample contains 10,000 real customer records'
                }
            ],
            'pause_point': True,
            'auto_advance': False
        },
        {
            'id': 'step-2',
            'title': 'Analyze Sensitive Fields',
            'description': 'Data Processor Agent identifies PII',
            'narration': 'The Data Processor Agent analyzes each field using multiple classifiers.',
            'agent': 'data_processor',
            'duration': 10,
            'callouts': [
                {
                    'type': 'decision',
                    'title': 'Classification Strategy',
                    'content': 'Using 4 classifiers: Pattern, Name-based, Content Analysis, Confluence'
                },
                {
                    'type': 'metric',
                    'title': 'Sensitivity Scores',
                    'content': 'name (0.95), email (0.98), phone (0.92), address (0.88)'
                }
            ],
            'pause_point': True,
            'auto_advance': False
        },
        {
            'id': 'step-3',
            'title': 'Generate Synthetic Data',
            'description': 'Creating GDPR-compliant replacements',
            'narration': 'Synthetic Data Agent uses SDV for tabular data and Bedrock for text fields.',
            'agent': 'synthetic_data',
            'duration': 15,
            'callouts': [
                {
                    'type': 'info',
                    'title': 'Dual Generation Strategy',
                    'content': 'SDV for numerical fields, Bedrock for text'
                },
                {
                    'type': 'metric',
                    'title': 'Statistical Preservation',
                    'content': 'Correlation preserved: 0.73 → 0.71'
                }
            ],
            'pause_point': True,
            'auto_advance': False
        }
    ]
    
    return DemoScenario(
        scenario_id='telecom-demo',
        name='Telecommunications Data Testing',
        description='Demonstrate synthetic data generation for telecom customer records',
        industry='telecom',
        steps=steps
    )


def demonstrate_playback_controls():
    """Demonstrate playback control functionality"""
    
    print("=" * 60)
    print("GUIDED DEMO MODE - PLAYBACK CONTROLS DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Create scenario
    scenario = create_telecom_scenario()
    print(f"📋 Scenario: {scenario.name}")
    print(f"🏭 Industry: {scenario.industry}")
    print(f"⏱️  Duration: {scenario.estimated_duration} seconds")
    print(f"📊 Steps: {len(scenario.steps)}")
    print()
    
    # Create state manager
    state = DemoStateManager(scenario)
    
    # Demonstrate controls
    print("🎮 DEMONSTRATING PLAYBACK CONTROLS")
    print("-" * 60)
    
    # Play
    state.play()
    current_step = state.get_current_step()
    print(f"📍 Current Step: {current_step['title']}")
    print(f"💬 Narration: {current_step['narration']}")
    print()
    
    # Show progress
    progress = state.get_progress()
    print(f"📊 Progress: {progress['progress_percent']:.1f}%")
    print(f"   Step {progress['current_step']} of {progress['total_steps']}")
    print()
    
    # Step forward
    state.step_forward()
    current_step = state.get_current_step()
    print(f"📍 Current Step: {current_step['title']}")
    print(f"🤖 Agent: {current_step.get('agent', 'N/A')}")
    print()
    
    # Show callouts
    if current_step.get('callouts'):
        print("💡 CALLOUTS:")
        for callout in current_step['callouts']:
            print(f"   [{callout['type'].upper()}] {callout['title']}")
            print(f"   → {callout['content']}")
        print()
    
    # Pause
    state.pause()
    print()
    
    # Change speed
    state.set_speed(1.5)
    print()
    
    # Step forward again
    state.step_forward()
    print()
    
    # Step backward
    state.step_backward()
    print()
    
    # Show final progress
    progress = state.get_progress()
    print(f"📊 Final Progress: {progress['progress_percent']:.1f}%")
    print(f"   Completed: {progress['completed_steps']} steps")
    print()
    
    # Restart
    state.restart()
    print()


def demonstrate_scenario_export():
    """Demonstrate scenario export for sharing"""
    
    print("=" * 60)
    print("DEMO SCENARIO EXPORT")
    print("=" * 60)
    print()
    
    scenario = create_telecom_scenario()
    scenario_dict = scenario.to_dict()
    
    # Export to JSON
    json_output = json.dumps(scenario_dict, indent=2)
    print("📄 Scenario exported to JSON:")
    print(json_output[:500] + "...")
    print()
    
    print("✅ Scenario can be shared with team members or imported into other environments")
    print()


def main():
    """Run guided demo mode demonstrations"""
    
    print("\n" + "=" * 60)
    print("GUIDED DEMO MODE - COMPREHENSIVE DEMONSTRATION")
    print("=" * 60)
    print()
    
    print("This example demonstrates the guided demo mode functionality:")
    print("✓ Pre-configured scenarios (Requirement 26.1)")
    print("✓ Step-by-step narration (Requirement 26.2)")
    print("✓ Playback controls (Requirement 26.3)")
    print("✓ Callout annotations (Requirement 26.4)")
    print("✓ Demo state management (Requirement 26.5)")
    print()
    
    # Demonstrate playback controls
    demonstrate_playback_controls()
    
    # Demonstrate scenario export
    demonstrate_scenario_export()
    
    print("=" * 60)
    print("✅ GUIDED DEMO MODE DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()
    print("To use in web application:")
    print("1. Navigate to /demo route")
    print("2. Select a pre-configured scenario")
    print("3. Use playback controls to navigate through steps")
    print("4. View callouts and narration for each step")
    print("5. Monitor workflow visualization in real-time")
    print()


if __name__ == "__main__":
    main()
