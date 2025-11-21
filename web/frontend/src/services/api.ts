import axios, { AxiosInstance } from 'axios';

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Configuration API
export const configurationAPI = {
  list: () => apiClient.get('/config'),
  get: (configId: string) => apiClient.get(`/config/${configId}`),
  create: (data: any) => apiClient.post('/config', data),
  update: (configId: string, data: any) => apiClient.put(`/config/${configId}`, data),
  delete: (configId: string) => apiClient.delete(`/config/${configId}`),
  validate: (data: any) => apiClient.post('/config/validate', data),
};

// Workflow API
export const workflowAPI = {
  start: (data: any) => apiClient.post('/workflow/start', data),
  pause: (workflowId: string) => apiClient.post(`/workflow/${workflowId}/pause`),
  resume: (workflowId: string) => apiClient.post(`/workflow/${workflowId}/resume`),
  abort: (workflowId: string) => apiClient.post(`/workflow/${workflowId}/abort`),
  getStatus: (workflowId: string) => apiClient.get(`/workflow/${workflowId}/status`),
  list: (params?: any) => apiClient.get('/workflow', { params }),
  delete: (workflowId: string) => apiClient.delete(`/workflow/${workflowId}`),
  getAnalysis: (workflowId: string) => apiClient.get(`/workflow/${workflowId}/analysis`),
  getAgentResults: (workflowId: string, agentId: string, limit?: number) => 
    apiClient.get(`/workflow/${workflowId}/agent/${agentId}/results`, { params: { limit } }),
};

// Monitoring API
export const monitoringAPI = {
  getAgents: (workflowId: string) => apiClient.get(`/monitoring/agents/${workflowId}`),
  getMetrics: () => apiClient.get('/monitoring/metrics'),
};

// Results API
export const resultsAPI = {
  getQuality: (workflowId: string) => apiClient.get(`/results/${workflowId}/quality`),
  getSamples: (workflowId: string, params?: any) => 
    apiClient.get(`/results/${workflowId}/samples`, { params }),
  export: (workflowId: string, format: string) => 
    apiClient.post(`/results/${workflowId}/export`, { format }),
  getTestResults: (workflowId: string) => apiClient.get(`/results/${workflowId}/test-results`),
};

// Audit API
export const auditAPI = {
  getLogs: (params?: any) => apiClient.get('/audit/logs', { params }),
  getWorkflowLogs: (workflowId: string) => apiClient.get(`/audit/logs/${workflowId}`),
  export: (params?: any) => apiClient.post('/audit/logs/export', params),
};

export default apiClient;
