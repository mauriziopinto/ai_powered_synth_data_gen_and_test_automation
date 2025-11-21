/**
 * Displays demo progress information
 */

import React from 'react';
import { Box, Typography, Stack, LinearProgress } from '@mui/material';
import { AccessTime, CheckCircle } from '@mui/icons-material';

interface DemoProgressProps {
  currentStep: number;
  totalSteps: number;
  elapsedTime: number;
  estimatedTimeRemaining: number;
}

export const DemoProgress: React.FC<DemoProgressProps> = ({
  currentStep,
  totalSteps,
  elapsedTime,
  estimatedTimeRemaining
}) => {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = (currentStep / totalSteps) * 100;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Stack direction="row" spacing={1} alignItems="center">
          <CheckCircle fontSize="small" color="success" />
          <Typography variant="body2" color="text.secondary">
            {currentStep} of {totalSteps} steps completed
          </Typography>
        </Stack>
        <Stack direction="row" spacing={2} alignItems="center">
          <Stack direction="row" spacing={0.5} alignItems="center">
            <AccessTime fontSize="small" color="action" />
            <Typography variant="body2" color="text.secondary">
              Elapsed: {formatTime(elapsedTime)}
            </Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Remaining: ~{formatTime(estimatedTimeRemaining)}
          </Typography>
        </Stack>
      </Stack>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 6,
          borderRadius: 3,
          bgcolor: 'grey.200',
          '& .MuiLinearProgress-bar': {
            bgcolor: 'success.main',
            borderRadius: 3
          }
        }}
      />
    </Box>
  );
};
