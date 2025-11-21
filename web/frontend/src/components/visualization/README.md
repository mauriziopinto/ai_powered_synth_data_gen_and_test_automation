# Visualization Dashboard Components

This directory contains the components for the Workflow Visualization Dashboard, implementing Task 29 of the Synthetic Data Generator project.

## Components

### WorkflowCanvas
**File:** `WorkflowCanvas.tsx`

Interactive canvas that displays the workflow as a flowchart showing all agents and their current states.

**Features:**
- Visual representation of agent pipeline
- Color-coded agent status (idle, running, completed, failed, paused)
- Real-time progress indicators for active agents
- Click-to-select agent interaction
- Animated data flow between agents

**Props:**
- `agents`: Array of agent objects with id, name, status, and progress
- `currentAgent`: ID of the currently active agent (highlighted)
- `onAgentClick`: Callback when an agent is clicked

**Validates Requirements:** 20.1, 20.2, 20.4

---

### AgentDetailPanel
**File:** `AgentDetailPanel.tsx`

Displays detailed information about a selected agent with expandable accordion sections.

**Features:**
- Agent status and current operation display
- Expandable sections for:
  - Execution logs with severity icons
  - Decisions and reasoning with confidence scores
  - Data transformations with before/after comparisons
  - Performance metrics
- Color-coded status chips
- Timestamp display for all events

**Props:**
- `agent`: AgentDetail object containing all agent information

**Validates Requirements:** 20.2, 25.1, 25.3

---

### ProgressIndicator
**File:** `ProgressIndicator.tsx`

Shows workflow progress with contextual messages and stage-by-stage breakdown.

**Features:**
- Overall progress bar with percentage
- Current operation message display
- Vertical stepper showing all workflow stages
- Stage-specific progress indicators
- Start/end timestamps for completed stages
- Status icons (pending, active, completed, failed)

**Props:**
- `stages`: Array of workflow stages with status and progress
- `overallProgress`: Overall workflow completion percentage (0-100)
- `currentMessage`: Current contextual message to display

**Validates Requirements:** 20.3, 25.4, 25.5

---

### DataTransformationViewer
**File:** `DataTransformationViewer.tsx`

Displays before/after data comparisons with diff highlighting.

**Features:**
- Tabbed interface for multiple transformation types
- Side-by-side before/after value comparison
- Visual diff highlighting (red for removed, green for added)
- Changed fields summary with chips
- Table view with first 10 records
- Transformation type and description display

**Props:**
- `transformations`: Array of transformation data with before/after records

**Validates Requirements:** 20.4, 25.2

---

## WorkflowPage Integration

The main `WorkflowPage` component integrates all visualization components and provides:

1. **Real-time Updates via WebSocket**
   - Subscribes to workflow status updates
   - Receives agent state changes
   - Updates data transformations as they occur
   - Displays progress messages in real-time

2. **Workflow Controls**
   - Pause/Resume workflow execution
   - Abort workflow with confirmation
   - Refresh data manually
   - Navigate back to dashboard

3. **Layout**
   - Left column: Workflow canvas, progress indicator, data transformations
   - Right column: Selected agent details
   - Responsive grid layout

**Validates Requirements:** 20.1, 20.2, 20.3, 20.4, 20.5, 25.1, 25.2, 25.3, 25.4, 25.5

---

## WebSocket Events

The visualization dashboard listens for the following WebSocket events:

### `workflow_status`
Updates overall workflow status and stage information.

```typescript
{
  type: 'workflow_status',
  workflow_id: string,
  status: {
    status: 'running' | 'paused' | 'completed' | 'failed',
    progress: number,
    current_stage: string,
    stages_completed: string[]
  }
}
```

### `agent_update`
Updates individual agent status and progress.

```typescript
{
  type: 'agent_update',
  workflow_id: string,
  agent: {
    agent_id: string,
    agent_type: string,
    status: string,
    progress: number,
    message?: string,
    logs?: LogEntry[],
    decisions?: Decision[],
    data_samples?: DataSample[]
  }
}
```

### `data_transformation`
Provides before/after data transformation information.

```typescript
{
  type: 'data_transformation',
  workflow_id: string,
  transformation: {
    before: Record<string, any>[],
    after: Record<string, any>[],
    changedFields: string[],
    transformationType: string,
    description?: string
  }
}
```

### `progress_update`
Sends contextual progress messages.

```typescript
{
  type: 'progress_update',
  workflow_id: string,
  message: string
}
```

---

## Usage Example

```typescript
import WorkflowPage from './pages/WorkflowPage';

// In your router
<Route path="/workflow/:workflowId" element={<WorkflowPage />} />

// Navigate to workflow
navigate(`/workflow/${workflowId}`);
```

---

## Styling

All components use Material-UI (MUI) components and follow the application theme defined in `src/theme.ts`.

**Color Scheme:**
- Idle: Gray (#9e9e9e)
- Running: Blue (#2196f3)
- Completed: Green (#4caf50)
- Failed: Red (#f44336)
- Paused: Orange (#ff9800)

---

## Requirements Validation

This implementation validates the following requirements from the specification:

**Requirement 20: Workflow Visualization**
- 20.1: Workflow visualization dashboard showing all agents and their current states ✓
- 20.2: Active agent highlighting and progress indicators ✓
- 20.3: Data flow display between agents ✓
- 20.4: Animated data flow visualization ✓
- 20.5: Drill-down capabilities for detailed logs and outputs ✓

**Requirement 25: Plain-Language Explanations**
- 25.1: Plain-language explanation of agent actions ✓
- 25.2: Sample data transformations with before-after comparisons ✓
- 25.3: Reasoning display for sensitive field identification ✓
- 25.4: Interactive drill-down for detailed information ✓
- 25.5: Contextual progress indicators with specific actions ✓

---

## Future Enhancements

Potential improvements for future iterations:

1. **Guided Demo Mode** (Requirement 26)
   - Step-by-step narration
   - Playback controls
   - Callout annotations

2. **Enhanced Visualizations**
   - 3D workflow canvas
   - Animated transitions between stages
   - Real-time metrics charts

3. **Export Capabilities**
   - Export workflow visualization as image
   - Generate execution report PDF
   - Share workflow link

4. **Performance Optimizations**
   - Virtual scrolling for large datasets
   - Lazy loading of agent details
   - WebSocket message batching
