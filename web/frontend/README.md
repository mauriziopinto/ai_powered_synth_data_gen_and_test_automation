# Synthetic Data Generator - Frontend

React + TypeScript frontend for the Synthetic Data Generator web application.

## Features

- **Modern Stack**: React 18, TypeScript, Vite
- **UI Framework**: Material-UI (MUI) v5
- **Routing**: React Router v6
- **API Client**: Axios with interceptors
- **WebSocket**: Real-time updates support
- **State Management**: Zustand (lightweight)
- **Charts**: Recharts for data visualization

## Project Structure

```
src/
├── components/          # Shared UI components
│   ├── Layout.tsx      # Main layout with navigation
│   ├── LoadingSpinner.tsx
│   └── ErrorAlert.tsx
├── pages/              # Page components
│   ├── Dashboard.tsx
│   ├── ConfigurationPage.tsx
│   ├── WorkflowPage.tsx
│   ├── ResultsPage.tsx
│   └── AuditPage.tsx
├── services/           # API and WebSocket services
│   ├── api.ts         # REST API client
│   └── websocket.ts   # WebSocket service
├── types/             # TypeScript type definitions
│   └── index.ts
├── App.tsx            # Main app component with routing
├── main.tsx           # Application entry point
└── theme.ts           # Material-UI theme configuration
```

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The app will be available at http://localhost:3000

## Build

```bash
npm run build
```

## Type Checking

```bash
npm run type-check
```

## Linting

```bash
npm run lint
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

## API Integration

The frontend connects to the FastAPI backend through:

1. **REST API** (`services/api.ts`):
   - Configuration management
   - Workflow control
   - Results retrieval
   - Audit logs

2. **WebSocket** (`services/websocket.ts`):
   - Real-time workflow updates
   - Agent status changes
   - System metrics

## Routing

- `/` - Dashboard with system overview
- `/configuration` - Configuration management
- `/configuration/:configId` - Edit configuration
- `/workflow` - Workflow list
- `/workflow/:workflowId` - Workflow details
- `/results/:workflowId` - Results dashboard
- `/audit` - Audit log viewer

## Theme Customization

The Material-UI theme is configured in `src/theme.ts`. Customize colors, typography, and component styles there.

## WebSocket Usage

```typescript
import websocketService from './services/websocket';

// Connect
await websocketService.connect();

// Listen for updates
websocketService.on('workflow_update', (data) => {
  console.log('Workflow updated:', data);
});

// Send message
websocketService.send({ type: 'subscribe', workflow_id: 'wf_123' });

// Disconnect
websocketService.disconnect();
```

## Next Steps

The following features will be implemented in subsequent tasks:

- **Task 28**: Configuration interface with schema builder
- **Task 29**: Workflow visualization dashboard
- **Task 30**: Results dashboard with charts
- **Task 31**: Guided demo mode
- **Task 32**: Plain-language explanations

## Validation

Validates Requirements:
- 11.1: Web-based user interface accessible through standard browsers
- 11.2: Interactive forms for configuration
- 11.3: Real-time monitoring via WebSocket
