# Results Dashboard Component Guide

## Component Architecture

```
ResultsPage
├── Summary Cards (4 cards)
│   ├── Quality Score
│   ├── Tests Passed
│   ├── Total Cost
│   └── Metrics Tracked
│
├── Tab Navigation
│   ├── Quality Metrics Tab
│   │   └── QualityMetricsDisplay
│   │       ├── Overall Score Card
│   │       ├── Individual Metric Cards (grid)
│   │       ├── Statistical Tests Summary
│   │       ├── Warnings Alert
│   │       └── Recommendations Alert
│   │
│   ├── Visualizations Tab
│   │   └── InteractiveCharts
│   │       ├── Chart Type Tabs
│   │       │   ├── Histograms
│   │       │   ├── Q-Q Plots
│   │       │   └── Correlation Heatmaps
│   │       ├── Zoom Dialog
│   │       └── Download Buttons
│   │
│   ├── Test Results Tab
│   │   └── TestResultsTable
│   │       ├── Summary Stats (4 cards)
│   │       ├── Search & Filter Controls
│   │       ├── Sortable Table
│   │       └── Expandable Error Details
│   │
│   └── Cost Analysis Tab
│       └── CostTracker
│           ├── Current Cost Card (gradient)
│           ├── Cost by Service (progress bars)
│           ├── Cost by Operation (table)
│           └── Optimization Recommendations (accordions)
```

## Component Interactions

### Data Flow
```
Backend API
    ↓
ResultsPage (fetches data)
    ↓
Props passed to child components
    ↓
Components render visualizations
    ↓
User interactions (expand, filter, sort)
    ↓
Local state updates
```

### Real-Time Updates
```
WebSocket Server
    ↓
websocketService
    ↓
CostTracker (subscribes to events)
    ↓
State updates on cost_update events
    ↓
UI re-renders with new cost
```

## Component Responsibilities

### QualityMetricsDisplay
- **Input:** Quality metrics data
- **Output:** Visual representation of quality scores
- **State:** None (stateless presentation component)
- **Side Effects:** None

### InteractiveCharts
- **Input:** Chart image paths
- **Output:** Tabbed chart viewer with zoom
- **State:** Selected tab, zoomed image
- **Side Effects:** Image downloads

### TestResultsTable
- **Input:** Test results array
- **Output:** Sortable, filterable table
- **State:** Expanded rows, search term, status filter, sort config
- **Side Effects:** None

### CostTracker
- **Input:** Workflow ID, initial cost
- **Output:** Cost breakdown and recommendations
- **State:** Current cost, breakdown data, recommendations, loading state
- **Side Effects:** WebSocket subscription, API calls

## Styling Patterns

### Color Coding
- **Success:** Green (#4caf50) - Passed tests, good metrics
- **Error:** Red (#f44336) - Failed tests, poor metrics
- **Warning:** Orange (#ff9800) - Warnings, medium priority
- **Info:** Blue (#2196f3) - Information, low priority

### Layout Patterns
- **Cards:** Primary container for grouped content
- **Grid:** Responsive layout (xs=12, sm=6, md=4, lg=3)
- **Paper:** Elevated surfaces for summary stats
- **Accordion:** Expandable sections for detailed info

### Typography
- **h4:** Page titles
- **h6:** Section titles
- **subtitle1/2:** Subsection titles
- **body1/2:** Regular content
- **caption:** Helper text, timestamps

## Accessibility

- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast ratios meet WCAG AA standards
- Screen reader friendly table structure
- Semantic HTML elements

## Performance Considerations

- Lazy loading of chart images
- Efficient filtering and sorting (client-side)
- Memoization opportunities for expensive calculations
- WebSocket connection management with reconnection logic
- Conditional rendering to avoid unnecessary updates

## Future Enhancements

1. **Export Options:**
   - PDF report generation
   - Excel export with multiple sheets
   - Custom date range selection

2. **Advanced Filtering:**
   - Multi-column sorting
   - Advanced search with regex
   - Saved filter presets

3. **Comparison Mode:**
   - Compare multiple workflow results
   - Historical trend analysis
   - Benchmark against baselines

4. **Interactive Charts:**
   - Replace static images with Plotly/D3.js
   - Hover tooltips with detailed values
   - Brush selection for zooming
   - Export charts as SVG

5. **Cost Optimization:**
   - Cost prediction based on historical data
   - Budget alerts and thresholds
   - Cost allocation by team/project
   - Detailed cost timeline visualization
