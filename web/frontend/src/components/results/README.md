# Results Dashboard Components

This directory contains components for the Results Dashboard, which displays comprehensive quality metrics, test results, visualizations, and cost tracking.

## Components

### QualityMetricsDisplay
Displays quality metrics including:
- Overall quality score with visual progress indicator
- Individual metric cards (Statistical Similarity, Correlation Preservation, etc.)
- Statistical test results (KS test, Chi-squared test)
- Warnings and recommendations based on quality analysis

**Props:**
- `overallScore`: Overall quality score (0-1)
- `metrics`: Array of quality metrics with thresholds
- `statisticalTests`: Statistical test results
- `correlationPreservation`: Correlation preservation score
- `edgeCaseMatch`: Edge case frequency match score
- `warnings`: Array of warning messages
- `recommendations`: Array of recommendation messages

**Validates:** Requirements 11.4, 11.5, 24.1, 24.2, 24.3

### InteractiveCharts
Displays interactive visualizations:
- Histogram comparisons (real vs synthetic data)
- Q-Q plots for distribution analysis
- Correlation heatmaps
- Zoom and download capabilities

**Props:**
- `charts`: Object containing paths to chart images
- `workflowId`: Workflow identifier for downloads

**Validates:** Requirements 11.5, 24.4

### TestResultsTable
Displays test execution results:
- Summary statistics (passed, failed, pass rate, total time)
- Sortable and filterable test results table
- Expandable rows showing error details and logs
- Jira issue links for failed tests

**Props:**
- `results`: Test results object with test cases

**Validates:** Requirements 11.4, 18.5, 19.1

### CostTracker
Real-time AWS cost tracking:
- Current workflow cost with real-time updates via WebSocket
- Cost breakdown by service (Bedrock, ECS, S3)
- Cost breakdown by operation
- Optimization recommendations with potential savings
- Priority-based recommendation display

**Props:**
- `workflowId`: Workflow identifier
- `initialCost`: Initial cost value

**Validates:** Requirements 27.3, 27.4

## Usage Example

```tsx
import {
  QualityMetricsDisplay,
  InteractiveCharts,
  TestResultsTable,
  CostTracker
} from '../components/results';

function ResultsPage() {
  return (
    <Box>
      <QualityMetricsDisplay
        overallScore={0.92}
        metrics={metrics}
        statisticalTests={tests}
      />
      
      <InteractiveCharts
        charts={visualizations}
        workflowId="workflow-123"
      />
      
      <TestResultsTable results={testResults} />
      
      <CostTracker
        workflowId="workflow-123"
        initialCost={0.0234}
      />
    </Box>
  );
}
```

## Features

### Drill-Down Capabilities
- Click on test rows to expand and view detailed error messages and logs
- Click on charts to zoom in for detailed analysis
- Expand optimization recommendations to see full descriptions

### Real-Time Updates
- Cost tracker subscribes to WebSocket updates for real-time cost tracking
- Automatic refresh of cost breakdown when new data arrives
- Last update timestamp displayed

### Interactive Filtering
- Test results can be filtered by status (passed, failed, error, skipped)
- Search functionality for finding specific tests
- Sortable columns for organizing results

### Export Capabilities
- Download individual charts as PNG files
- Export complete results via the main Results page

## Styling

All components use Material-UI theming and follow the application's design system:
- Consistent color scheme for status indicators (success, error, warning)
- Responsive grid layouts for mobile compatibility
- Accessible color contrasts and ARIA labels
- Smooth animations and transitions

## Data Flow

1. **ResultsPage** fetches data from backend API endpoints
2. Data is passed to individual components as props
3. **CostTracker** additionally subscribes to WebSocket for real-time updates
4. Components render visualizations and interactive elements
5. User interactions (expand, filter, sort) update local component state

## Backend Integration

Components expect the following API endpoints:
- `GET /api/v1/results/{workflow_id}/quality` - Quality report
- `GET /api/v1/results/{workflow_id}/test-results` - Test results
- `GET /api/v1/workflow/{workflow_id}/status` - Workflow status with cost
- `POST /api/v1/results/{workflow_id}/export` - Export results

WebSocket events:
- `cost_update` - Real-time cost updates
- `workflow_status` - Workflow status updates including cost
