/**
 * Type definitions for Guided Demo Mode
 */

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  industry: 'telecom' | 'finance' | 'healthcare';
  config: any; // WorkflowConfig
  steps: DemoStep[];
  estimatedDuration: number; // in seconds
  highlights: string[];
}

export interface DemoStep {
  id: string;
  title: string;
  description: string;
  narration: string;
  agent?: string;
  duration: number; // in seconds
  callouts: Callout[];
  dataTransformation?: DataTransformation;
  pausePoint: boolean;
  autoAdvance: boolean;
}

export interface Callout {
  id: string;
  type: 'info' | 'highlight' | 'decision' | 'metric';
  position: { x: number; y: number };
  title: string;
  content: string;
  targetElement?: string;
}

export interface DataTransformation {
  before: any;
  after: any;
  changes: Change[];
  reasoning: string;
}

export interface Change {
  field: string;
  oldValue: any;
  newValue: any;
  reason: string;
}

export interface DemoState {
  scenarioId: string;
  currentStepIndex: number;
  isPlaying: boolean;
  isPaused: boolean;
  playbackSpeed: number;
  startedAt?: string;
  completedSteps: string[];
  annotations: Annotation[];
}

export interface Annotation {
  id: string;
  stepId: string;
  timestamp: string;
  note: string;
}

export type PlaybackControl = 'play' | 'pause' | 'step-forward' | 'step-backward' | 'restart' | 'skip-to';

export interface DemoProgress {
  currentStep: number;
  totalSteps: number;
  elapsedTime: number;
  estimatedTimeRemaining: number;
}
