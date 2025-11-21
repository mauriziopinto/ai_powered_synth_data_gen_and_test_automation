/**
 * Progress Indicator Component
 * 
 * Displays contextual progress messages and completion status
 * Validates Requirements 20.3, 25.4, 25.5
 */

import {
  Box,
  LinearProgress,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';

interface WorkflowStage {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  message?: string;
  progress?: number;
  startTime?: string;
  endTime?: string;
}

interface ProgressIndicatorProps {
  stages: WorkflowStage[];
  overallProgress: number;
  currentMessage?: string;
}

export default function ProgressIndicator({
  stages,
  overallProgress,
  currentMessage,
}: ProgressIndicatorProps) {
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'active':
        return <HourglassEmptyIcon color="primary" />;
      default:
        return null;
    }
  };

  const activeStepIndex = stages.findIndex(s => s.status === 'active');

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Workflow Progress
      </Typography>

      {/* Overall Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Overall Progress
          </Typography>
          <Typography variant="body2" fontWeight="bold">
            {Math.round(overallProgress)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={overallProgress}
          sx={{ height: 8, borderRadius: 1 }}
        />
      </Box>

      {/* Current Message */}
      {currentMessage && (
        <Box
          sx={{
            mb: 2,
            p: 1.5,
            bgcolor: 'primary.light',
            color: 'primary.contrastText',
            borderRadius: 1,
          }}
        >
          <Typography variant="body2" fontWeight="medium">
            {currentMessage}
          </Typography>
        </Box>
      )}

      {/* Stage Stepper */}
      <Stepper activeStep={activeStepIndex} orientation="vertical">
        {stages.map((stage) => (
          <Step key={stage.name} completed={stage.status === 'completed'}>
            <StepLabel
              error={stage.status === 'failed'}
              StepIconComponent={() => getStepIcon(stage.status)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" fontWeight="medium">
                  {stage.name}
                </Typography>
                {stage.status === 'active' && stage.progress !== undefined && (
                  <Typography variant="caption" color="text.secondary">
                    ({Math.round(stage.progress)}%)
                  </Typography>
                )}
              </Box>
            </StepLabel>
            <StepContent>
              {stage.message && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {stage.message}
                </Typography>
              )}
              {stage.status === 'active' && stage.progress !== undefined && (
                <LinearProgress
                  variant="determinate"
                  value={stage.progress}
                  sx={{ mb: 1, height: 4 }}
                />
              )}
              {stage.startTime && (
                <Typography variant="caption" color="text.secondary">
                  Started: {new Date(stage.startTime).toLocaleTimeString()}
                </Typography>
              )}
              {stage.endTime && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                  Completed: {new Date(stage.endTime).toLocaleTimeString()}
                </Typography>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Paper>
  );
}
