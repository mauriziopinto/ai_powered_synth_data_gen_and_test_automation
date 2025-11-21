/**
 * Test Page for Data Tables
 * 
 * Simple page to test AgentDataTable component
 */

import { Box, Typography, Paper } from '@mui/material';
import AgentDataTable from '../components/visualization/AgentDataTable';

export default function TestDataTables() {
  // Use a known workflow ID for testing
  const testWorkflowId = 'wf_csv_20251120_074745';

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Data Tables Test Page
      </Typography>
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Testing AgentDataTable component with workflow: {testWorkflowId}
        </Typography>
      </Paper>

      {/* Data Processor Table */}
      <AgentDataTable
        workflowId={testWorkflowId}
        agentId="data_processor"
        agentType="data_processor"
      />

      {/* Synthetic Data Table */}
      <AgentDataTable
        workflowId={testWorkflowId}
        agentId="synthetic_data"
        agentType="synthetic_data"
      />
    </Box>
  );
}
