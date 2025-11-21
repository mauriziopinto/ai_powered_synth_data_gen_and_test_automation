import { useNavigate } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import EnhancedCSVUploader from '../components/configuration/EnhancedCSVUploader';

export default function ConfigurationPage() {
  const navigate = useNavigate();

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Upload CSV File
        </Typography>
        <Typography color="text.secondary">
          Upload your CSV file to automatically generate synthetic data
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1 }}>
        <EnhancedCSVUploader onUploadSuccess={(workflowId) => navigate(`/workflow/${workflowId}`)} />
      </Box>
    </Box>
  );
}
