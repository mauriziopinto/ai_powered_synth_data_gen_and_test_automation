/**
 * Interactive Charts Component
 * 
 * Displays interactive visualizations including histograms, Q-Q plots,
 * and correlation heatmaps for quality analysis.
 * 
 * Validates Requirements 11.5, 24.4
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  Download as DownloadIcon,
  Close as CloseIcon
} from '@mui/icons-material';

interface ChartData {
  histograms?: string;
  qq_plots?: string;
  correlation_heatmaps?: string;
}

interface InteractiveChartsProps {
  charts: ChartData;
  workflowId: string;
}

const InteractiveCharts: React.FC<InteractiveChartsProps> = ({
  charts,
  workflowId
}) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleZoom = (imagePath: string) => {
    setZoomedImage(imagePath);
  };

  const handleCloseZoom = () => {
    setZoomedImage(null);
  };

  const handleDownload = (imagePath: string, filename: string) => {
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = imagePath;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const chartTabs = [
    {
      label: 'Histograms',
      key: 'histograms',
      description: 'Distribution comparison between real and synthetic data',
      path: charts.histograms
    },
    {
      label: 'Q-Q Plots',
      key: 'qq_plots',
      description: 'Quantile-quantile plots showing distribution similarity',
      path: charts.qq_plots
    },
    {
      label: 'Correlation Heatmaps',
      key: 'correlation_heatmaps',
      description: 'Correlation matrices for real and synthetic data',
      path: charts.correlation_heatmaps
    }
  ].filter(tab => tab.path); // Only show tabs with available charts

  if (chartTabs.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Visualizations
          </Typography>
          <Typography color="text.secondary">
            No visualizations available yet. Charts will appear once quality analysis is complete.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const currentChart = chartTabs[selectedTab];

  return (
    <>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quality Visualizations
          </Typography>
          
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
          >
            {chartTabs.map((tab) => (
              <Tab key={tab.key} label={tab.label} />
            ))}
          </Tabs>

          {currentChart && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  {currentChart.description}
                </Typography>
                <Box>
                  <Tooltip title="Zoom">
                    <IconButton
                      size="small"
                      onClick={() => handleZoom(currentChart.path!)}
                      sx={{ mr: 1 }}
                    >
                      <ZoomInIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Download">
                    <IconButton
                      size="small"
                      onClick={() => handleDownload(currentChart.path!, `${currentChart.key}_${workflowId}.png`)}
                    >
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              <Box
                sx={{
                  width: '100%',
                  display: 'flex',
                  justifyContent: 'center',
                  backgroundColor: 'grey.50',
                  borderRadius: 1,
                  p: 2,
                  cursor: 'pointer'
                }}
                onClick={() => handleZoom(currentChart.path!)}
              >
                <img
                  src={currentChart.path}
                  alt={currentChart.label}
                  style={{
                    maxWidth: '100%',
                    height: 'auto',
                    borderRadius: 4
                  }}
                />
              </Box>

              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
                Click image to zoom
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Zoom Dialog */}
      <Dialog
        open={!!zoomedImage}
        onClose={handleCloseZoom}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {chartTabs.find(tab => tab.path === zoomedImage)?.label}
            </Typography>
            <IconButton onClick={handleCloseZoom} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {zoomedImage && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <img
                src={zoomedImage}
                alt="Zoomed chart"
                style={{
                  maxWidth: '100%',
                  height: 'auto'
                }}
              />
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default InteractiveCharts;
