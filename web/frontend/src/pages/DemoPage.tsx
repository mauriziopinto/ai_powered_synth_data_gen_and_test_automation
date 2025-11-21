/**
 * Main page for guided demo mode
 */

import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Chip, Stack, IconButton, Tooltip } from '@mui/material';
import { Close } from '@mui/icons-material';
import { DemoScenario, DemoStep } from '../types/demo';
import { DEMO_SCENARIOS } from '../data/demoScenarios';
import { DemoScenarioList } from '../components/demo/DemoScenarioList';
import { DemoModeController } from '../components/demo/DemoModeController';
import WorkflowCanvas from '../components/visualization/WorkflowCanvas';
import AgentDetailPanel from '../components/visualization/AgentDetailPanel';

export const DemoPage: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null);
  const [currentStep, setCurrentStep] = useState<DemoStep | null>(null);

  const handleSelectScenario = (scenario: DemoScenario) => {
    setSelectedScenario(scenario);
    setCurrentStep(null);
  };

  const handleExitDemo = () => {
    setSelectedScenario(null);
    setCurrentStep(null);
  };

  const handleStepChange = (step: DemoStep) => {
    setCurrentStep(step);
  };

  // Update document title - must be called before any early returns
  useEffect(() => {
    if (selectedScenario) {
      document.title = `${selectedScenario.name} - Demo`;
    } else {
      document.title = 'Synthetic Data Generator';
    }
    return () => {
      document.title = 'Synthetic Data Generator';
    };
  }, [selectedScenario]);

  // Map demo step to agent status for visualization
  const getAgentStatusFromStep = (step: DemoStep | null) => {
    const agentNames: Record<string, string> = {
      'data_processor': 'Data Processor',
      'synthetic_data': 'Synthetic Data',
      'distribution': 'Distribution',
      'test_case': 'Test Case',
      'test_execution': 'Test Execution'
    };

    const agents = [
      'data_processor',
      'synthetic_data',
      'distribution',
      'test_case',
      'test_execution'
    ];

    return agents.map(agentId => ({
      id: agentId,
      name: agentNames[agentId],
      status: (step?.agent === agentId ? 'running' : 'idle') as 'idle' | 'running' | 'completed' | 'failed' | 'paused',
      progress: step?.agent === agentId ? 50 : 0
    }));
  };

  if (!selectedScenario) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <DemoScenarioList
          scenarios={DEMO_SCENARIOS}
          onSelectScenario={handleSelectScenario}
        />
      </Container>
    );
  }

  const totalDuration = selectedScenario.steps.reduce((sum, step) => sum + step.duration, 0);

  return (
    <Box>
      {/* Exit Demo Button */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Tooltip title="Back to Demo List">
          <IconButton onClick={handleExitDemo} color="primary">
            <Close />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Workflow pipeline visualization */}
      <Box 
        sx={{ 
          mb: 2,
          height: '120px',
          overflow: 'hidden',
          '& > *': {
            transform: 'scale(0.6)',
            transformOrigin: 'top left',
            width: '166.67%',
            height: '166.67%'
          }
        }}
      >
        <WorkflowCanvas
          agents={getAgentStatusFromStep(currentStep)}
          currentAgent={currentStep?.agent}
        />
      </Box>

      {/* Content area */}
      <Box>
        <DemoModeController
          scenario={selectedScenario}
          onExit={handleExitDemo}
          onStepChange={handleStepChange}
          currentStep={currentStep}
        />
      </Box>
    </Box>
  );
};
