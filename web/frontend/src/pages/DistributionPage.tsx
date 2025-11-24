import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Target {
  id: string;
  name: string;
  type: string;
}

interface ColumnDistribution {
  column: string;
  targets: string[]; // Array of target IDs that should receive this column
}

export default function DistributionPage() {
  const { workflowId } = useParams();
  const navigate = useNavigate();
  
  const [activeStep, setActiveStep] = useState(0);
  const [targets, setTargets] = useState<Target[]>([]);
  const [datasetColumns, setDatasetColumns] = useState<string[]>([]);
  const [selectedTargets, setSelectedTargets] = useState<string[]>([]);
  const [columnDistributions, setColumnDistributions] = useState<ColumnDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [distributing, setDistributing] = useState(false);
  const [progress, setProgress] = useState<any>(null);
  const [completed, setCompleted] = useState(false);

  const steps = ['Select Targets', 'Configure Columns', 'Distribute'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load targets
      const targetsRes = await axios.get(`${API_URL}/targets/`);
      setTargets(targetsRes.data);

      // Load dataset columns (mock for now - will get from workflow)
      setDatasetColumns(['name', 'email', 'phone', 'address', 'city', 'state', 'zip']);
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to load data:', error);
      setLoading(false);
    }
  };

  const handleToggleTarget = (targetId: string) => {
    setSelectedTargets(prev => 
      prev.includes(targetId)
        ? prev.filter(id => id !== targetId)
        : [...prev, targetId]
    );
  };

  const handleNextToColumnConfig = () => {
    if (selectedTargets.length === 0) return;
    
    // Initialize column distributions - by default all columns go to all targets
    const distributions = datasetColumns.map(col => ({
      column: col,
      targets: [...selectedTargets] // All selected targets by default
    }));
    
    setColumnDistributions(distributions);
    setActiveStep(1);
  };

  const handleToggleColumnTarget = (columnIndex: number, targetId: string) => {
    setColumnDistributions(prev => {
      const newDist = [...prev];
      const column = newDist[columnIndex];
      
      if (column.targets.includes(targetId)) {
        column.targets = column.targets.filter(id => id !== targetId);
      } else {
        column.targets = [...column.targets, targetId];
      }
      
      return newDist;
    });
  };

  const handleStartDistribution = async () => {
    setDistributing(true);
    setActiveStep(2);
    
    // Mock distribution progress for each target
    const targetProgress: any = {};
    selectedTargets.forEach(targetId => {
      targetProgress[targetId] = { sent: 0, total: 100, failed: 0 };
    });
    
    const interval = setInterval(() => {
      let allComplete = true;
      
      selectedTargets.forEach(targetId => {
        if (targetProgress[targetId].sent < targetProgress[targetId].total) {
          targetProgress[targetId].sent += Math.floor(Math.random() * 10) + 1;
          if (targetProgress[targetId].sent >= targetProgress[targetId].total) {
            targetProgress[targetId].sent = targetProgress[targetId].total;
            targetProgress[targetId].failed = Math.floor(Math.random() * 3);
          } else {
            allComplete = false;
          }
        }
      });
      
      setProgress({ ...targetProgress });
      
      if (allComplete) {
        clearInterval(interval);
        setCompleted(true);
        
        // Mark distribution as completed in workflow
        markDistributionComplete();
      }
    }, 500);
  };

  const markDistributionComplete = async () => {
    try {
      // This will be implemented in backend later
      // For now, we'll just store it in localStorage
      const completedWorkflows = JSON.parse(localStorage.getItem('completed_distributions') || '[]');
      if (!completedWorkflows.includes(workflowId)) {
        completedWorkflows.push(workflowId);
        localStorage.setItem('completed_distributions', JSON.stringify(completedWorkflows));
      }
    } catch (error) {
      console.error('Failed to mark distribution complete:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate(`/workflow/${workflowId}`)}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Data Distribution</Typography>
      </Box>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {activeStep === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Select Distribution Targets
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Choose one or more targets to receive the synthetic data
            </Typography>

            {targets.length === 0 ? (
              <Alert severity="info" sx={{ mt: 2 }}>
                No targets configured. <Button onClick={() => navigate('/targets')}>Create targets</Button>
              </Alert>
            ) : (
              <Box sx={{ mt: 2 }}>
                {targets.map((target) => (
                  <Card 
                    key={target.id}
                    sx={{ 
                      mb: 2, 
                      cursor: 'pointer',
                      border: 2,
                      borderColor: selectedTargets.includes(target.id) ? 'primary.main' : 'transparent',
                      '&:hover': { borderColor: 'primary.light' }
                    }}
                    onClick={() => handleToggleTarget(target.id)}
                  >
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="h6">{target.name}</Typography>
                          <Chip label={target.type} size="small" sx={{ mt: 1 }} />
                        </Box>
                        {selectedTargets.includes(target.id) && (
                          <CheckCircleIcon color="primary" sx={{ fontSize: 32 }} />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}

            <Box display="flex" gap={2} mt={3}>
              <Button
                variant="contained"
                onClick={handleNextToColumnConfig}
                disabled={selectedTargets.length === 0}
              >
                Next: Configure Columns ({selectedTargets.length} target{selectedTargets.length !== 1 ? 's' : ''})
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {activeStep === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configure Column Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              For each column, select which target(s) should receive it
            </Typography>

            <TableContainer sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Column</TableCell>
                    {selectedTargets.map(targetId => {
                      const target = targets.find(t => t.id === targetId);
                      return (
                        <TableCell key={targetId} align="center">
                          <Box>
                            <Typography variant="subtitle2">{target?.name}</Typography>
                            <Chip label={target?.type} size="small" />
                          </Box>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {columnDistributions.map((colDist, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body1" fontWeight="medium">
                          {colDist.column}
                        </Typography>
                      </TableCell>
                      {selectedTargets.map(targetId => (
                        <TableCell key={targetId} align="center">
                          <IconButton
                            color={colDist.targets.includes(targetId) ? 'primary' : 'default'}
                            onClick={() => handleToggleColumnTarget(index, targetId)}
                          >
                            {colDist.targets.includes(targetId) ? (
                              <CheckCircleIcon />
                            ) : (
                              <Box 
                                sx={{ 
                                  width: 24, 
                                  height: 24, 
                                  border: 2, 
                                  borderColor: 'grey.300',
                                  borderRadius: '50%'
                                }} 
                              />
                            )}
                          </IconButton>
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Box display="flex" gap={2} mt={3}>
              <Button onClick={() => setActiveStep(0)}>
                Back
              </Button>
              <Button
                variant="contained"
                color="success"
                onClick={handleStartDistribution}
                startIcon={<PlayArrowIcon />}
              >
                Start Distribution
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {activeStep === 2 && (
        <Card>
          <CardContent>
            {!completed ? (
              <>
                <Typography variant="h6" gutterBottom>
                  Distributing Data...
                </Typography>
                
                {selectedTargets.map(targetId => {
                  const target = targets.find(t => t.id === targetId);
                  const targetProg = progress?.[targetId];
                  const percentage = targetProg ? Math.round((targetProg.sent / targetProg.total) * 100) : 0;
                  
                  return (
                    <Box key={targetId} mb={3}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="subtitle1">
                          {target?.name}
                        </Typography>
                        <Chip label={target?.type} size="small" />
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={percentage} 
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Sent: {targetProg?.sent || 0} / {targetProg?.total || 0} records
                        {targetProg?.failed > 0 && ` (${targetProg.failed} failed)`}
                      </Typography>
                    </Box>
                  );
                })}
              </>
            ) : (
              <>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <CheckCircleIcon color="success" sx={{ fontSize: 48 }} />
                  <Typography variant="h5">
                    Distribution Complete!
                  </Typography>
                </Box>
                
                <Alert severity="success" sx={{ mb: 2 }}>
                  Successfully distributed data to {selectedTargets.length} target(s).
                </Alert>

                <TableContainer sx={{ mb: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Target</TableCell>
                        <TableCell align="right">Sent</TableCell>
                        <TableCell align="right">Failed</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedTargets.map(targetId => {
                        const target = targets.find(t => t.id === targetId);
                        const targetProg = progress?.[targetId];
                        return (
                          <TableRow key={targetId}>
                            <TableCell>{target?.name}</TableCell>
                            <TableCell align="right">{targetProg?.sent || 0}</TableCell>
                            <TableCell align="right">{targetProg?.failed || 0}</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Box display="flex" gap={2}>
                  <Button
                    variant="contained"
                    onClick={() => navigate(`/workflow/${workflowId}`)}
                  >
                    Back to Workflow
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => navigate('/targets')}
                  >
                    View Target Data
                  </Button>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
