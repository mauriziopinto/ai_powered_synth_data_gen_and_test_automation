# Guided Demo Mode Components

This directory contains components for the guided demo mode feature, which provides interactive, narrated demonstrations of the synthetic data generation workflow.

## Overview

The guided demo mode allows presenters to showcase the complete workflow with pre-configured scenarios, step-by-step narration, and interactive callouts. It's designed for stakeholder presentations and product demonstrations.

## Components

### DemoModeController
Main controller component that manages demo state, playback controls, and step progression.

**Features:**
- Play/pause/step-forward/step-backward controls
- Adjustable playback speed (0.5x, 1.0x, 1.5x, 2.0x)
- Progress tracking with time estimates
- Auto-advance with pause points
- Step completion tracking

**Props:**
- `scenario`: DemoScenario - The demo scenario to execute
- `onExit`: () => void - Callback when exiting demo mode
- `onStepChange`: (step: DemoStep) => void - Callback when step changes

### DemoNarration
Displays narration text for the current demo step with progressive reveal animation.

**Features:**
- Progressive text reveal during playback
- Text-to-speech toggle (placeholder for future implementation)
- Styled narration box with cursor animation

**Props:**
- `narration`: string - The narration text to display
- `isPlaying`: boolean - Whether demo is currently playing

### DemoCallouts
Displays callout annotations that highlight key features and decisions.

**Features:**
- Four callout types: info, highlight, decision, metric
- Staggered fade-in animations
- Color-coded by type
- Hover effects

**Props:**
- `callouts`: Callout[] - Array of callouts to display
- `isVisible`: boolean - Whether callouts should be visible

### DemoProgress
Displays demo progress information including elapsed time and remaining time.

**Features:**
- Step completion counter
- Elapsed time display
- Estimated time remaining
- Progress bar

**Props:**
- `currentStep`: number - Current step number
- `totalSteps`: number - Total number of steps
- `elapsedTime`: number - Elapsed time in seconds
- `estimatedTimeRemaining`: number - Estimated remaining time in seconds

### DemoScenarioList
Displays list of available demo scenarios for selection.

**Features:**
- Grid layout with scenario cards
- Industry-specific color coding
- Highlights and key features display
- Duration and step count information

**Props:**
- `scenarios`: DemoScenario[] - Array of available scenarios
- `onSelectScenario`: (scenario: DemoScenario) => void - Callback when scenario is selected

## Data Structures

### DemoScenario
Pre-configured demo scenario with complete workflow configuration.

```typescript
interface DemoScenario {
  id: string;
  name: string;
  description: string;
  industry: 'telecom' | 'finance' | 'healthcare';
  config: WorkflowConfig;
  steps: DemoStep[];
  estimatedDuration: number;
  highlights: string[];
}
```

### DemoStep
Individual step in the demo workflow.

```typescript
interface DemoStep {
  id: string;
  title: string;
  description: string;
  narration: string;
  agent?: string;
  duration: number;
  callouts: Callout[];
  dataTransformation?: DataTransformation;
  pausePoint: boolean;
  autoAdvance: boolean;
}
```

### Callout
Annotation that highlights a key feature or decision.

```typescript
interface Callout {
  id: string;
  type: 'info' | 'highlight' | 'decision' | 'metric';
  position: { x: number; y: number };
  title: string;
  content: string;
  targetElement?: string;
}
```

## Pre-configured Scenarios

### Telecom Demo
- **Duration**: 5 minutes
- **Records**: 1,000
- **Highlights**: PII detection, data quality preservation, statistical matching
- **Steps**: 8 (Load data → Analyze → Generate → Validate → Distribute → Test → Execute → Complete)

### Finance Demo
- **Duration**: 4.5 minutes
- **Records**: 5,000
- **Highlights**: Credit card masking, fraud pattern preservation, PCI-DSS compliance
- **Steps**: 3 (simplified for financial data focus)

### Healthcare Demo
- **Duration**: 5.5 minutes
- **Records**: 2,000
- **Highlights**: HIPAA compliance, medical record generation, temporal sequencing
- **Steps**: 3 (simplified for healthcare data focus)

## Usage Example

```typescript
import { DemoPage } from './pages/DemoPage';

// In your router
<Route path="/demo" element={<DemoPage />} />

// The DemoPage component handles:
// 1. Scenario selection
// 2. Demo execution with controls
// 3. Workflow visualization
// 4. Agent detail display
```

## Playback Controls

- **Play**: Start or resume demo playback
- **Pause**: Pause at current step
- **Step Forward**: Advance to next step
- **Step Backward**: Go back to previous step
- **Restart**: Reset to beginning
- **Speed**: Cycle through 0.5x, 1.0x, 1.5x, 2.0x

## Auto-Advance Behavior

Steps can be configured with:
- `pausePoint: true` - Demo pauses at this step for presenter interaction
- `autoAdvance: true` - Step automatically advances after duration
- `pausePoint: true, autoAdvance: false` - Step pauses and requires manual advance

## State Management

Demo state is managed locally in the DemoModeController component and includes:
- Current step index
- Play/pause status
- Playback speed
- Completed steps
- Annotations (for future enhancement)

State can be persisted to backend via `/api/v1/demo/state` endpoint for resuming demos.

## Backend Integration

The demo mode integrates with backend endpoints:
- `GET /api/v1/demo/scenarios` - List available scenarios
- `GET /api/v1/demo/scenarios/{id}` - Get scenario details
- `POST /api/v1/demo/state` - Save demo state
- `GET /api/v1/demo/state/{id}` - Load demo state
- `POST /api/v1/demo/scenarios/{id}/start` - Start demo workflow

## Future Enhancements

1. **Text-to-Speech**: Implement actual TTS for narration
2. **Recording**: Record demo sessions for playback
3. **Annotations**: Allow presenters to add notes during demo
4. **Custom Scenarios**: UI for creating custom demo scenarios
5. **Interactive Elements**: Allow audience to interact with certain steps
6. **Export**: Export demo as video or presentation slides

## Validation

This implementation validates the following requirements:
- **Requirement 26.1**: Pre-configured demo scenarios (telecom, finance, healthcare)
- **Requirement 26.2**: Step-by-step narration system
- **Requirement 26.3**: Playback controls (play, pause, step-forward, step-backward)
- **Requirement 26.4**: Callout annotation system
- **Requirement 26.5**: Demo state management
