/**
 * Main controller for guided demo mode
 * Manages demo state, playback controls, and step progression
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  LinearProgress,
  Stack,
  Tooltip
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  SkipNext,
  SkipPrevious,
  Replay,
  Speed
} from '@mui/icons-material';
import { DemoScenario, DemoState, DemoStep, PlaybackControl } from '../../types/demo';
import { DemoNarration } from './DemoNarration';
import { DemoCallouts } from './DemoCallouts';
import { DemoProgress } from './DemoProgress';
import AgentDetailPanel from '../visualization/AgentDetailPanel';

interface DemoModeControllerProps {
  scenario: DemoScenario;
  onExit: () => void;
  onStepChange?: (step: DemoStep) => void;
  currentStep?: DemoStep | null;
}

export const DemoModeController: React.FC<DemoModeControllerProps> = ({
  scenario,
  onStepChange,
  currentStep: externalCurrentStep
}) => {
  const [demoState, setDemoState] = useState<DemoState>({
    scenarioId: scenario.id,
    currentStepIndex: 0,
    isPlaying: false,
    isPaused: false,
    playbackSpeed: 1.0,
    completedSteps: [],
    annotations: []
  });

  const [elapsedTime, setElapsedTime] = useState(0);
  const [stepStartTime, setStepStartTime] = useState<number>(Date.now());

  const currentStep = scenario.steps[demoState.currentStepIndex];
  const isLastStep = demoState.currentStepIndex === scenario.steps.length - 1;
  const isFirstStep = demoState.currentStepIndex === 0;

  // Auto-advance timer
  useEffect(() => {
    if (!demoState.isPlaying || demoState.isPaused) return;

    const interval = setInterval(() => {
      setElapsedTime(prev => prev + 0.1);
    }, 100);

    return () => clearInterval(interval);
  }, [demoState.isPlaying, demoState.isPaused]);

  // Check if step should auto-advance
  useEffect(() => {
    if (!demoState.isPlaying || demoState.isPaused) return;
    if (!currentStep) return;

    const stepDuration = currentStep.duration / demoState.playbackSpeed;
    const stepElapsed = (Date.now() - stepStartTime) / 1000;

    if (stepElapsed >= stepDuration) {
      if (currentStep.pausePoint && !currentStep.autoAdvance) {
        handleControl('pause');
      } else if (!isLastStep) {
        handleControl('step-forward');
      } else {
        handleControl('pause');
      }
    }
  }, [elapsedTime, demoState.isPlaying, demoState.isPaused, currentStep, isLastStep, stepStartTime, demoState.playbackSpeed]);

  // Notify parent of step changes
  useEffect(() => {
    if (currentStep && onStepChange) {
      onStepChange(currentStep);
    }
  }, [currentStep, onStepChange]);

  const handleControl = useCallback((control: PlaybackControl, value?: any) => {
    switch (control) {
      case 'play':
        setDemoState(prev => ({
          ...prev,
          isPlaying: true,
          isPaused: false,
          startedAt: prev.startedAt || new Date().toISOString()
        }));
        setStepStartTime(Date.now());
        break;

      case 'pause':
        setDemoState(prev => ({ ...prev, isPaused: true }));
        break;

      case 'step-forward':
        if (!isLastStep) {
          const nextIndex = demoState.currentStepIndex + 1;
          setDemoState(prev => ({
            ...prev,
            currentStepIndex: nextIndex,
            completedSteps: [...prev.completedSteps, currentStep.id]
          }));
          setStepStartTime(Date.now());
        }
        break;

      case 'step-backward':
        if (!isFirstStep) {
          const prevIndex = demoState.currentStepIndex - 1;
          setDemoState(prev => ({
            ...prev,
            currentStepIndex: prevIndex,
            completedSteps: prev.completedSteps.filter(id => id !== scenario.steps[prevIndex].id)
          }));
          setStepStartTime(Date.now());
        }
        break;

      case 'restart':
        setDemoState(prev => ({
          ...prev,
          currentStepIndex: 0,
          isPlaying: false,
          isPaused: false,
          completedSteps: [],
          startedAt: undefined
        }));
        setElapsedTime(0);
        setStepStartTime(Date.now());
        break;

      case 'skip-to':
        if (typeof value === 'number' && value >= 0 && value < scenario.steps.length) {
          setDemoState(prev => ({
            ...prev,
            currentStepIndex: value,
            completedSteps: scenario.steps.slice(0, value).map(s => s.id)
          }));
          setStepStartTime(Date.now());
        }
        break;
    }
  }, [demoState.currentStepIndex, isLastStep, isFirstStep, currentStep, scenario.steps]);

  const handleSpeedChange = (speed: number) => {
    setDemoState(prev => ({ ...prev, playbackSpeed: speed }));
  };

  const totalDuration = scenario.steps.reduce((sum, step) => sum + step.duration, 0);
  const completedDuration = scenario.steps
    .slice(0, demoState.currentStepIndex)
    .reduce((sum, step) => sum + step.duration, 0);
  const progress = (completedDuration / totalDuration) * 100;

  return (
    <Box sx={{ position: 'relative', height: '100%' }}>
      {/* Current Step Display */}
      <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="overline" color="primary" fontWeight="bold">
              {currentStep.agent ? `Agent: ${currentStep.agent}` : 'System'}
            </Typography>
            <Typography variant="h6" fontWeight="bold" sx={{ mt: 0.5 }}>
              {currentStep.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {currentStep.description}
            </Typography>
          </Box>

          {/* Narration */}
          <DemoNarration
            narration={currentStep.narration}
            isPlaying={demoState.isPlaying && !demoState.isPaused}
          />

          {/* Agent Detail Panel */}
          {externalCurrentStep?.agent && (
            <Box>
              <AgentDetailPanel
                agent={{
                  agent_id: externalCurrentStep.agent,
                  agent_type: externalCurrentStep.agent,
                  status: 'running',
                  current_operation: externalCurrentStep.description,
                  progress: 50,
                  message: externalCurrentStep.title,
                  logs: [
                    {
                      timestamp: new Date().toISOString(),
                      level: 'info' as const,
                      message: externalCurrentStep.narration
                    }
                  ]
                }}
              />
            </Box>
          )}

          {/* Data Transformation */}
          {currentStep.dataTransformation && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                Data Transformation
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {currentStep.dataTransformation.reasoning}
                </Typography>
                <Stack direction="row" spacing={2}>
                  <Box flex={1}>
                    <Typography variant="caption" fontWeight="bold" color="error.main">
                      Before
                    </Typography>
                    <pre style={{ fontSize: '0.75rem', margin: '4px 0' }}>
                      {JSON.stringify(currentStep.dataTransformation.before, null, 2)}
                    </pre>
                  </Box>
                  <Box flex={1}>
                    <Typography variant="caption" fontWeight="bold" color="success.main">
                      After
                    </Typography>
                    <pre style={{ fontSize: '0.75rem', margin: '4px 0' }}>
                      {JSON.stringify(currentStep.dataTransformation.after, null, 2)}
                    </pre>
                  </Box>
                </Stack>
              </Paper>
            </Box>
          )}
        </Stack>
      </Paper>

      {/* Playback Controls */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          position: 'sticky',
          bottom: 0,
          bgcolor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider'
        }}
      >
        <Stack spacing={2}>
          {/* Main Controls */}
          <Stack direction="row" justifyContent="center" alignItems="center" spacing={2}>
            <Tooltip title="Restart Demo">
              <IconButton
                onClick={() => handleControl('restart')}
                color="primary"
                disabled={demoState.currentStepIndex === 0 && !demoState.isPlaying}
              >
                <Replay />
              </IconButton>
            </Tooltip>

            <Tooltip title="Previous Step">
              <span>
                <IconButton
                  onClick={() => handleControl('step-backward')}
                  disabled={isFirstStep}
                  color="primary"
                >
                  <SkipPrevious />
                </IconButton>
              </span>
            </Tooltip>

            {demoState.isPlaying && !demoState.isPaused ? (
              <Tooltip title="Pause">
                <IconButton
                  onClick={() => handleControl('pause')}
                  color="primary"
                  size="large"
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': { bgcolor: 'primary.dark' }
                  }}
                >
                  <Pause />
                </IconButton>
              </Tooltip>
            ) : (
              <Tooltip title="Play">
                <IconButton
                  onClick={() => handleControl('play')}
                  color="primary"
                  size="large"
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': { bgcolor: 'primary.dark' }
                  }}
                >
                  <PlayArrow />
                </IconButton>
              </Tooltip>
            )}

            <Tooltip title="Next Step">
              <span>
                <IconButton
                  onClick={() => handleControl('step-forward')}
                  disabled={isLastStep}
                  color="primary"
                >
                  <SkipNext />
                </IconButton>
              </span>
            </Tooltip>

            <Tooltip title="Playback Speed">
              <Button
                startIcon={<Speed />}
                onClick={() => {
                  const speeds = [0.5, 1.0, 1.5, 2.0];
                  const currentIndex = speeds.indexOf(demoState.playbackSpeed);
                  const nextSpeed = speeds[(currentIndex + 1) % speeds.length];
                  handleSpeedChange(nextSpeed);
                }}
                variant="outlined"
                size="small"
              >
                {demoState.playbackSpeed}x
              </Button>
            </Tooltip>
          </Stack>

          {/* Step Progress */}
          <DemoProgress
            currentStep={demoState.currentStepIndex + 1}
            totalSteps={scenario.steps.length}
            elapsedTime={elapsedTime}
            estimatedTimeRemaining={totalDuration - completedDuration}
          />
        </Stack>
      </Paper>
    </Box>
  );
};
