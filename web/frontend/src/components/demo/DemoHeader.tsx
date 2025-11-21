/**
 * Demo scenario header component
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Chip,
  Stack,
  Tooltip
} from '@mui/material';
import { Close } from '@mui/icons-material';
import { DemoScenario } from '../../types/demo';

interface DemoHeaderProps {
  scenario: DemoScenario;
  onExit: () => void;
}

export const DemoHeader: React.FC<DemoHeaderProps> = ({ scenario, onExit }) => {
  const totalDuration = scenario.steps.reduce((sum, step) => sum + step.duration, 0);

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        borderRadius: 0
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h5" fontWeight="bold">
            {scenario.name}
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
            {scenario.description}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip
            label={`${scenario.industry.toUpperCase()}`}
            size="small"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip
            label={`${Math.floor(totalDuration / 60)}:${(totalDuration % 60).toString().padStart(2, '0')}`}
            size="small"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Tooltip title="Exit Demo Mode">
            <IconButton onClick={onExit} sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>
    </Paper>
  );
};
