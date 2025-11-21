/**
 * Displays list of available demo scenarios for selection
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Stack,
  Grid
} from '@mui/material';
import {
  PlayArrow,
  AccessTime,
  CheckCircle
} from '@mui/icons-material';
import { DemoScenario } from '../../types/demo';

interface DemoScenarioListProps {
  scenarios: DemoScenario[];
  onSelectScenario: (scenario: DemoScenario) => void;
}

export const DemoScenarioList: React.FC<DemoScenarioListProps> = ({
  scenarios,
  onSelectScenario
}) => {
  const getIndustryColor = (industry: string) => {
    switch (industry) {
      case 'telecom':
        return 'primary';
      case 'finance':
        return 'success';
      case 'healthcare':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Select a Demo Scenario
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Choose from pre-configured scenarios to see the complete workflow in action
      </Typography>

      <Grid container spacing={3}>
        {scenarios.map((scenario) => (
          <Grid item xs={12} md={6} key={scenario.id}>
            <Card
              elevation={2}
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6
                }
              }}
            >
              <CardContent sx={{ flex: 1 }}>
                <Stack spacing={2}>
                  <Box>
                    <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                      <Chip
                        label={scenario.industry.toUpperCase()}
                        size="small"
                        color={getIndustryColor(scenario.industry) as any}
                      />
                      <Chip
                        icon={<AccessTime />}
                        label={`${Math.floor(scenario.estimatedDuration / 60)} min`}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      {scenario.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {scenario.description}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      Highlights:
                    </Typography>
                    <Stack spacing={0.5}>
                      {scenario.highlights.map((highlight, index) => (
                        <Stack
                          key={index}
                          direction="row"
                          spacing={1}
                          alignItems="flex-start"
                        >
                          <CheckCircle
                            fontSize="small"
                            sx={{ color: 'success.main', mt: 0.2 }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {highlight}
                          </Typography>
                        </Stack>
                      ))}
                    </Stack>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {scenario.steps.length} steps • {scenario.config.generation_params.num_records} records
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>

              <CardActions sx={{ p: 2, pt: 0 }}>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<PlayArrow />}
                  onClick={() => onSelectScenario(scenario)}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #63408b 100%)'
                    }
                  }}
                >
                  Start Demo
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};
