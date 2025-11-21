/**
 * Displays callout annotations for highlighting key features and decisions
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Chip,
  Zoom
} from '@mui/material';
import {
  Info,
  Highlight,
  Psychology,
  ShowChart
} from '@mui/icons-material';
import { Callout } from '../../types/demo';

interface DemoCalloutsProps {
  callouts: Callout[];
  isVisible: boolean;
}

export const DemoCallouts: React.FC<DemoCalloutsProps> = ({ callouts, isVisible }) => {
  const getCalloutIcon = (type: Callout['type']) => {
    switch (type) {
      case 'info':
        return <Info />;
      case 'highlight':
        return <Highlight />;
      case 'decision':
        return <Psychology />;
      case 'metric':
        return <ShowChart />;
      default:
        return <Info />;
    }
  };

  const getCalloutColor = (type: Callout['type']) => {
    switch (type) {
      case 'info':
        return 'info';
      case 'highlight':
        return 'warning';
      case 'decision':
        return 'secondary';
      case 'metric':
        return 'success';
      default:
        return 'info';
    }
  };

  return (
    <Box>
      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
        Key Points
      </Typography>
      <Stack spacing={1.5}>
        {callouts.map((callout, index) => (
          <Zoom
            in={isVisible}
            style={{ transitionDelay: `${index * 200}ms` }}
            key={callout.id}
          >
            <Paper
              elevation={2}
              sx={{
                p: 2,
                borderLeft: 4,
                borderColor: `${getCalloutColor(callout.type)}.main`,
                bgcolor: `${getCalloutColor(callout.type)}.50`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateX(4px)',
                  boxShadow: 4
                }
              }}
            >
              <Stack direction="row" spacing={2} alignItems="flex-start">
                <Box
                  sx={{
                    color: `${getCalloutColor(callout.type)}.main`,
                    display: 'flex',
                    alignItems: 'center',
                    mt: 0.5
                  }}
                >
                  {getCalloutIcon(callout.type)}
                </Box>
                <Box flex={1}>
                  <Stack direction="row" spacing={1} alignItems="center" mb={0.5}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {callout.title}
                    </Typography>
                    <Chip
                      label={callout.type}
                      size="small"
                      color={getCalloutColor(callout.type)}
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {callout.content}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Zoom>
        ))}
      </Stack>
    </Box>
  );
};
