/**
 * Type definitions for the Synthetic Data Generator frontend
 */

export interface SchemaField {
  name: string;
  type: string;
  constraints?: Record<string, any>;
}

export interface WorkflowConfig {
  config_id?: string;
  name: string;
  description?: string;
  schema_fields: SchemaField[];
  generation_params: Record<string, any>;
  sdv_model: string;
  bedrock_model?: string;
  edge_case_frequency: number;
  target_systems: TargetSystem[];
  project_id?: string;
  team_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TargetSystem {
  type: string;
  name: string;
  config: Record<string, any>;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: 'running' | 'paused' | 'completed' | 'failed' | 'aborted';
  config_id: string;
  num_records: number;
  started_at: string;
  updated_at: string;
  completed_at?: string;
  progress: number;
  current_stage?: string;
  stages_completed: string[];
  error?: string;
  cost_usd: number;
}

export interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: string;
  current_operation?: string;
  progress: number;
  message?: string;
}

export interface QualityMetric {
  metric_name: string;
  value: number;
  threshold?: number;
  passed: boolean;
}

export interface QualityReport {
  workflow_id: string;
  generated_at: string;
  overall_score: number;
  metrics: QualityMetric[];
  statistical_tests: Record<string, any>;
  distribution_comparison: Record<string, any>;
}

export interface DataSample {
  record_id: number;
  data: Record<string, any>;
  is_edge_case: boolean;
  edge_case_type?: string;
}

export interface SystemMetrics {
  timestamp: string;
  active_workflows: number;
  total_workflows: number;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  cost_today_usd: number;
}

export interface AuditLogEntry {
  log_id: string;
  timestamp: string;
  workflow_id?: string;
  event_type: string;
  actor: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  ip_address?: string;
}

export interface AgentLogEntry {
  timestamp: string;
  workflow_id: string;
  agent_name: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  metadata?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResponse {
  valid: boolean;
  errors: ValidationError[];
}
