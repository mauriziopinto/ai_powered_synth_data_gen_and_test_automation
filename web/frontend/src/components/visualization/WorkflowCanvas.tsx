/**
 * Workflow Canvas Component
 * 
 * Displays the workflow as an interactive flowchart showing agent states
 * Validates Requirements 20.1, 20.2, 20.4
 */

import { Box, Paper, Typography } from '@mui/material';
import { useEffect, useRef } from 'react';

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
}

interface WorkflowCanvasProps {
  agents: Agent[];
  currentAgent?: string;
  onAgentClick?: (agentId: string) => void;
}

const AGENT_COLORS = {
  idle: '#9e9e9e',
  running: '#2196f3',
  completed: '#4caf50',
  failed: '#f44336',
  paused: '#ff9800',
};

export default function WorkflowCanvas({ agents, currentAgent, onAgentClick }: WorkflowCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    // Draw workflow
    drawWorkflow(ctx, agents, currentAgent, rect.width, rect.height);
  }, [agents, currentAgent]);

  const drawWorkflow = (
    ctx: CanvasRenderingContext2D,
    agents: Agent[],
    currentAgent: string | undefined,
    _width: number,
    height: number
  ) => {
    const agentWidth = 120;
    const agentHeight = 80;
    const spacing = 40;
    const startX = 50;
    const startY = height / 2 - agentHeight / 2;

    agents.forEach((agent, index) => {
      const x = startX + index * (agentWidth + spacing);
      const y = startY;

      // Draw connection line to next agent
      if (index < agents.length - 1) {
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x + agentWidth, y + agentHeight / 2);
        ctx.lineTo(x + agentWidth + spacing, y + agentHeight / 2);
        ctx.stroke();

        // Draw arrow
        ctx.beginPath();
        ctx.moveTo(x + agentWidth + spacing - 10, y + agentHeight / 2 - 5);
        ctx.lineTo(x + agentWidth + spacing, y + agentHeight / 2);
        ctx.lineTo(x + agentWidth + spacing - 10, y + agentHeight / 2 + 5);
        ctx.stroke();
      }

      // Draw agent box
      const isActive = agent.id === currentAgent;
      ctx.fillStyle = AGENT_COLORS[agent.status];
      ctx.strokeStyle = isActive ? '#1976d2' : '#bdbdbd';
      ctx.lineWidth = isActive ? 3 : 1;

      // Rounded rectangle
      const radius = 8;
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + agentWidth - radius, y);
      ctx.quadraticCurveTo(x + agentWidth, y, x + agentWidth, y + radius);
      ctx.lineTo(x + agentWidth, y + agentHeight - radius);
      ctx.quadraticCurveTo(x + agentWidth, y + agentHeight, x + agentWidth - radius, y + agentHeight);
      ctx.lineTo(x + radius, y + agentHeight);
      ctx.quadraticCurveTo(x, y + agentHeight, x, y + agentHeight - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Draw agent name
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.name, x + agentWidth / 2, y + 20);

      // Draw status
      ctx.font = '10px Arial';
      ctx.fillText(agent.status.toUpperCase(), x + agentWidth / 2, y + 40);

      // Draw progress bar
      if (agent.status === 'running' || agent.status === 'paused') {
        const progressWidth = agentWidth - 20;
        const progressHeight = 6;
        const progressX = x + 10;
        const progressY = y + agentHeight - 20;

        // Background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.fillRect(progressX, progressY, progressWidth, progressHeight);

        // Progress
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(progressX, progressY, progressWidth * (agent.progress / 100), progressHeight);

        // Progress text
        ctx.fillStyle = '#ffffff';
        ctx.font = '9px Arial';
        ctx.fillText(`${Math.round(agent.progress)}%`, x + agentWidth / 2, y + agentHeight - 8);
      }
    });
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onAgentClick) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const agentWidth = 120;
    const agentHeight = 80;
    const spacing = 40;
    const startX = 50;
    const startY = rect.height / 2 - agentHeight / 2;

    agents.forEach((agent, index) => {
      const agentX = startX + index * (agentWidth + spacing);
      const agentY = startY;

      if (x >= agentX && x <= agentX + agentWidth && y >= agentY && y <= agentY + agentHeight) {
        onAgentClick(agent.id);
      }
    });
  };

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Box sx={{ position: 'relative', height: '100%' }}>
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          style={{
            width: '100%',
            height: '100%',
            cursor: onAgentClick ? 'pointer' : 'default',
          }}
        />
      </Box>
    </Paper>
  );
}
