# Visualization Components - Visual Guide

## Component Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Workflow Execution                                  │
│  [← Back]                                          [Refresh] [Pause] [Abort] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────┐  ┌──────────────────────────────┐  │
│  │      WORKFLOW CANVAS (8 cols)      │  │   AGENT DETAILS (4 cols)     │  │
│  │                                    │  │                              │  │
│  │  ┌────┐    ┌────┐    ┌────┐      │  │  Data Processor Agent        │  │
│  │  │Data│───>│Synth│───>│Dist│      │  │  Status: RUNNING             │  │
│  │  │Proc│    │Data│    │Agen│      │  │                              │  │
│  │  └────┘    └────┘    └────┘      │  │  ▼ Execution Logs (10)       │  │
│  │                                    │  │  ▼ Decisions & Reasoning (3) │  │
│  │  ┌────┐    ┌────┐                │  │  ▼ Data Transformations (5)  │  │
│  │  │Test│───>│Test│                │  │  ▼ Performance Metrics       │  │
│  │  │Case│    │Exec│                │  │                              │  │
│  │  └────┘    └────┘                │  │                              │  │
│  └────────────────────────────────────┘  └──────────────────────────────┘  │
│                                                                               │
│  ┌────────────────────────────────────┐                                     │
│  │      PROGRESS INDICATOR            │                                     │
│  │                                    │                                     │
│  │  Overall Progress: 45%             │                                     │
│  │  ████████████░░░░░░░░░░░░░░        │                                     │
│  │                                    │                                     │
│  │  Currently: Analyzing 50 fields... │                                     │
│  │                                    │                                     │
│  │  ✓ Data Processing                 │                                     │
│  │  ⏳ Synthetic Generation (45%)     │                                     │
│  │  ○ Data Distribution               │                                     │
│  │  ○ Test Case Creation              │                                     │
│  │  ○ Test Execution                  │                                     │
│  └────────────────────────────────────┘                                     │
│                                                                               │
│  ┌────────────────────────────────────┐                                     │
│  │   DATA TRANSFORMATION VIEWER       │                                     │
│  │                                    │                                     │
│  │  [PII Replacement] [Edge Cases]    │                                     │
│  │                                    │                                     │
│  │  Changed Fields: email, phone      │                                     │
│  │                                    │                                     │
│  │  Record | email                    │                                     │
│  │  ─────────────────────────────────│                                     │
│  │    1    | john@real.com → john@... │                                     │
│  │    2    | jane@real.com → jane@... │                                     │
│  └────────────────────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## WorkflowCanvas Component

### Visual Representation

```
┌──────────────────────────────────────────────────────────────┐
│                    Workflow Pipeline                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐            │
│   │  Data   │      │ Synth   │      │  Dist   │            │
│   │ Process │─────>│  Data   │─────>│  Agent  │            │
│   │  Agent  │      │  Agent  │      │         │            │
│   │         │      │         │      │         │            │
│   │COMPLETED│      │RUNNING  │      │  IDLE   │            │
│   │         │      │  45%    │      │         │            │
│   └─────────┘      └─────────┘      └─────────┘            │
│                                                               │
│   ┌─────────┐      ┌─────────┐                              │
│   │  Test   │      │  Test   │                              │
│   │  Case   │─────>│  Exec   │                              │
│   │  Agent  │      │  Agent  │                              │
│   │         │      │         │                              │
│   │  IDLE   │      │  IDLE   │                              │
│   │         │      │         │                              │
│   └─────────┘      └─────────┘                              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Color Coding
- **Gray Box**: Idle agent (not yet started)
- **Blue Box**: Running agent (currently processing)
- **Green Box**: Completed agent (successfully finished)
- **Red Box**: Failed agent (encountered error)
- **Orange Box**: Paused agent (temporarily stopped)

### Interactive Features
- Click any agent box to view details in the right panel
- Active agent has thicker border (3px vs 1px)
- Progress bar shows completion percentage for running agents

## AgentDetailPanel Component

### Collapsed View
```
┌────────────────────────────────┐
│ Data Processor Agent           │
│ [RUNNING]                      │
│                                │
│ Analyzing production data...   │
│                                │
│ ▼ Execution Logs (10)          │
│ ▼ Decisions & Reasoning (3)    │
│ ▼ Data Transformations (5)     │
│ ▼ Performance Metrics          │
└────────────────────────────────┘
```

### Expanded Logs Section
```
┌────────────────────────────────┐
│ ▲ Execution Logs (10)          │
├────────────────────────────────┤
│ ℹ️ 10:30:15 Loading data file  │
│ ℹ️ 10:30:16 Analyzing schema   │
│ ⚠️ 10:30:17 Large file warning │
│ ℹ️ 10:30:18 Profiling data     │
│ ✓ 10:30:20 Analysis complete   │
└────────────────────────────────┘
```

### Expanded Decisions Section
```
┌────────────────────────────────┐
│ ▲ Decisions & Reasoning (3)    │
├────────────────────────────────┤
│ Field 'email' classified as    │
│ sensitive                      │
│                                │
│ Pattern match: email regex     │
│ Confidence: 95.2%              │
│ ────────────────────────────   │
│ Field 'phone' classified as    │
│ sensitive                      │
│                                │
│ Pattern match: phone regex     │
│ Confidence: 89.7%              │
└────────────────────────────────┘
```

### Expanded Transformations Section
```
┌────────────────────────────────┐
│ ▲ Data Transformations (5)     │
├────────────────────────────────┤
│ email                          │
│ PII Replacement                │
│                                │
│ Before:                        │
│ john.doe@company.com           │
│                                │
│ After:                         │
│ synthetic.user@example.com     │
│ ────────────────────────────   │
│ phone                          │
│ PII Replacement                │
│                                │
│ Before:                        │
│ +1-555-123-4567                │
│                                │
│ After:                         │
│ +1-555-987-6543                │
└────────────────────────────────┘
```

## ProgressIndicator Component

```
┌────────────────────────────────────┐
│      Workflow Progress             │
├────────────────────────────────────┤
│ Overall Progress            45%    │
│ ████████████░░░░░░░░░░░░░░        │
│                                    │
│ Currently: Analyzing 50 fields for │
│ PII patterns                       │
│                                    │
│ ✓ Data Processing                  │
│   Started: 10:30:00                │
│   Completed: 10:30:30              │
│                                    │
│ ⏳ Synthetic Generation (45%)      │
│   ████████░░░░░░░░                │
│   Started: 10:30:31                │
│   Generating synthetic email       │
│   addresses using Bedrock          │
│                                    │
│ ○ Data Distribution                │
│                                    │
│ ○ Test Case Creation               │
│                                    │
│ ○ Test Execution                   │
└────────────────────────────────────┘
```

### Status Icons
- ✓ (Green checkmark): Completed stage
- ⏳ (Blue hourglass): Active stage
- ○ (Gray circle): Pending stage
- ✗ (Red X): Failed stage

## DataTransformationViewer Component

### Tabbed View
```
┌────────────────────────────────────────────────────────┐
│      Data Transformations                              │
├────────────────────────────────────────────────────────┤
│ [PII Replacement] [Edge Cases] [Schema Validation]     │
│                                                         │
│ [PII Replacement]                                       │
│                                                         │
│ Changed Fields: [email] [phone] [ssn]                  │
│                                                         │
│ ┌──────┬─────────────────────────────────────────┐    │
│ │ Rec# │ email                                   │    │
│ ├──────┼─────────────────────────────────────────┤    │
│ │  1   │ john@real.com → john@synthetic.com      │    │
│ │  2   │ jane@real.com → jane@synthetic.com      │    │
│ │  3   │ bob@real.com → bob@synthetic.com        │    │
│ └──────┴─────────────────────────────────────────┘    │
│                                                         │
│ Showing first 10 of 1000 records                       │
└────────────────────────────────────────────────────────┘
```

### Diff Highlighting
```
┌────────────────────────────────────────────┐
│ email field                                │
│                                            │
│ john@real.com  →  john@synthetic.com       │
│ ─────────────      ───────────────────     │
│   (red bg)           (green bg)            │
│  strikethrough                             │
└────────────────────────────────────────────┘
```

## Responsive Behavior

### Desktop (≥960px)
- Left column: 8/12 width (Workflow Canvas, Progress, Transformations)
- Right column: 4/12 width (Agent Details)

### Tablet (600-960px)
- Stacked layout
- Full width for all components

### Mobile (<600px)
- Single column layout
- Simplified canvas view
- Collapsible sections

## Color Palette

### Status Colors
```
Idle:      #9e9e9e  ████ Gray
Running:   #2196f3  ████ Blue
Completed: #4caf50  ████ Green
Failed:    #f44336  ████ Red
Paused:    #ff9800  ████ Orange
```

### Diff Colors
```
Removed:   #ffebee  ████ Light Red
Added:     #e8f5e9  ████ Light Green
```

### Background Colors
```
Primary:   #1976d2  ████ Dark Blue
Secondary: #f5f5f5  ████ Light Gray
Paper:     #ffffff  ████ White
```

## Animation & Transitions

### Canvas
- Agent status changes: Smooth color transition (300ms)
- Progress bar updates: Linear animation (200ms)
- Active agent border: Pulse effect (1s loop)

### Accordions
- Expand/collapse: Slide animation (300ms)
- Content fade-in: Opacity transition (200ms)

### Progress Indicator
- Progress bar: Linear fill animation (500ms)
- Stage transitions: Fade and slide (400ms)

## Accessibility

### Keyboard Navigation
- Tab through interactive elements
- Enter/Space to expand accordions
- Arrow keys for canvas navigation (future)

### Screen Readers
- ARIA labels on all interactive elements
- Status announcements for workflow changes
- Descriptive alt text for visual indicators

### Color Contrast
- All text meets WCAG AA standards (4.5:1 ratio)
- Status colors distinguishable by shape/icon
- High contrast mode support

## Performance Considerations

### Canvas Rendering
- Uses device pixel ratio for crisp rendering
- Redraws only on state changes
- Efficient click detection

### WebSocket Updates
- Throttled updates (max 10/second)
- Batched state updates
- Automatic reconnection

### Data Display
- Virtualized lists for large datasets (future)
- Lazy loading of agent details
- Pagination for transformations (10 records)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Testing Checklist

- [ ] Canvas renders all agents correctly
- [ ] Agent status colors update in real-time
- [ ] Click agent to view details
- [ ] Accordion sections expand/collapse
- [ ] Progress bar animates smoothly
- [ ] Data transformations display correctly
- [ ] Diff highlighting shows changes
- [ ] WebSocket reconnects on disconnect
- [ ] Pause/Resume/Abort buttons work
- [ ] Responsive layout on mobile
- [ ] Keyboard navigation works
- [ ] Screen reader announces changes
