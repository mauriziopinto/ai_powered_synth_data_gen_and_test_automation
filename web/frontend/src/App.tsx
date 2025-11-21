import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout';
import ConfigurationPage from './pages/ConfigurationPage';
import WorkflowListPage from './pages/WorkflowListPage';
import WorkflowPage from './pages/WorkflowPage';
import StrategySelectionPage from './pages/StrategySelectionPage';
import { DemoPage } from './pages/DemoPage';

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<WorkflowListPage />} />
          <Route path="/configuration" element={<ConfigurationPage />} />
          <Route path="/configuration/:configId" element={<ConfigurationPage />} />
          <Route path="/workflow" element={<WorkflowListPage />} />
          <Route path="/workflow/:workflowId" element={<WorkflowPage />} />
          <Route path="/workflow/:workflowId/strategy-selection" element={<StrategySelectionPage />} />
          <Route path="/demo" element={<DemoPage />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;
