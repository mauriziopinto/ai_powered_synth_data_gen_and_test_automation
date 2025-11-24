import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Paper,
  Typography,
  TextField,
  IconButton,
  Chip,
  Divider,
  Avatar,
  CircularProgress,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
  Storage as StorageIcon,
  Cable as CableIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface DatasetInfo {
  columns: string[];
  row_count: number;
  sample_data: any[];
}

interface MCPServer {
  name: string;
  enabled: boolean;
  status: string;
}

export default function MCPDistributionPage() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [distributionId, setDistributionId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  
  const examplePrompts = [
    "Create a SQLite table called 'customers' and insert all records",
    "For each record, create a Jira issue with the name as the summary",
    "Insert all records into a database table",
    "Export all data to a JSON file",
    "Create a CSV file with all the data",
  ];
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load dataset info and MCP servers on mount
  useEffect(() => {
    loadDatasetInfo();
    loadMCPServers();
    
    // Cleanup polling on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [workflowId]);

  const loadDatasetInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/workflows/${workflowId}`);
      const workflow = response.data;
      
      if (workflow.synthetic_data_results?.sample_data) {
        const sampleData = workflow.synthetic_data_results.sample_data;
        setDatasetInfo({
          columns: Object.keys(sampleData[0] || {}),
          row_count: sampleData.length,
          sample_data: sampleData.slice(0, 3),
        });
        
        // Add welcome message
        setMessages([{
          role: 'assistant',
          content: `Hi! I'm your AI distribution assistant. I can see you have a dataset with ${sampleData.length} records and ${Object.keys(sampleData[0] || {}).length} columns.\n\nI can help you distribute this data to external systems using natural language. Click on one of the example prompts below or type your own instruction!`,
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      console.error('Failed to load dataset:', error);
    }
  };

  const loadMCPServers = async () => {
    try {
      const response = await axios.get(`${API_URL}/mcp-distribution/agent-status`);
      const servers = response.data.mcp_servers || [];
      setMcpServers(servers.map((s: any) => ({
        name: s.name,
        enabled: !s.disabled,
        status: s.disabled ? 'disabled' : 'active',
      })));
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsStreaming(true);

    // Add placeholder for assistant response
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Start distribution
      const response = await axios.post(`${API_URL}/mcp-distribution/distribute-strands`, {
        workflow_id: workflowId,
        instructions: inputMessage,
      });

      const distId = response.data.distribution_id;
      setDistributionId(distId);

      // Start polling for streaming updates
      startPolling(distId);

    } catch (error: any) {
      console.error('Distribution failed:', error);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1].content = `Error: ${error.response?.data?.detail || error.message}`;
        return updated;
      });
      setIsStreaming(false);
    }
  };

  const startPolling = (distId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/mcp-distribution/status/${distId}`);
        const status = response.data;

        // Update the last message with streaming content
        if (status.agent_stream && status.agent_stream.length > 0) {
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1].content = status.agent_stream.join('');
            return updated;
          });
        }

        // Check if completed
        if (status.status === 'completed' || status.status === 'failed') {
          setIsStreaming(false);
          setIsComplete(status.status === 'completed');
          
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }

          // Add completion message
          if (status.status === 'completed') {
            const completionMsg = `\n\n✅ Distribution completed successfully!\n• Processed: ${status.records_processed} records\n• Succeeded: ${status.records_succeeded}\n• Failed: ${status.records_failed}`;
            
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1].content += completionMsg;
              return updated;
            });
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 1000); // Poll every second
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'grey.50' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate(`/workflow/${workflowId}`)}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5" sx={{ flexGrow: 1 }}>
            AI Distribution Assistant
          </Typography>
          {isComplete && (
            <Button
              variant="contained"
              endIcon={<ArrowForwardIcon />}
              onClick={() => navigate(`/workflow/${workflowId}/test-synthesis`)}
            >
              Continue to Test Synthesis
            </Button>
          )}
        </Box>
      </Paper>

      {/* Dataset Info & MCP Servers Panel */}
      {datasetInfo && (
        <Paper elevation={0} sx={{ p: 3, borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
          <Grid container spacing={3}>
            {/* Dataset Info */}
            <Grid item xs={12} md={8}>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <StorageIcon color="primary" fontSize="small" />
                  <Typography variant="subtitle2" color="primary">
                    Dataset Overview
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {datasetInfo.row_count} records • {datasetInfo.columns.length} columns
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  Columns:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {datasetInfo.columns.map((col) => (
                    <Chip 
                      key={col} 
                      label={col} 
                      size="small" 
                      variant="outlined"
                      sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}
                    />
                  ))}
                </Box>
              </Box>
            </Grid>

            {/* MCP Servers */}
            <Grid item xs={12} md={4}>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CableIcon color="primary" fontSize="small" />
                  <Typography variant="subtitle2" color="primary">
                    Active MCP Servers
                  </Typography>
                </Box>
                {mcpServers.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No MCP servers configured
                  </Typography>
                ) : (
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {mcpServers.filter(s => s.enabled).map((server) => (
                      <Chip
                        key={server.name}
                        label={server.name}
                        size="small"
                        color="success"
                        icon={<CheckCircleIcon />}
                      />
                    ))}
                    {mcpServers.filter(s => !s.enabled).map((server) => (
                      <Chip
                        key={server.name}
                        label={server.name}
                        size="small"
                        variant="outlined"
                        disabled
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Chat Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              gap: 2,
              mb: 3,
              flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
            }}
          >
            <Avatar
              sx={{
                bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                width: 40,
                height: 40,
              }}
            >
              {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
            </Avatar>
            
            <Paper
              elevation={1}
              sx={{
                p: 2,
                maxWidth: '70%',
                bgcolor: message.role === 'user' ? 'primary.50' : 'white',
              }}
            >
              <Typography
                variant="body1"
                component="pre"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: message.role === 'assistant' ? 'monospace' : 'inherit',
                  fontSize: message.role === 'assistant' ? '0.875rem' : 'inherit',
                  margin: 0,
                  lineHeight: 1.6,
                }}
              >
                {message.content}
              </Typography>
              {message.role === 'assistant' && isStreaming && index === messages.length - 1 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="caption" color="text.secondary">
                    Thinking...
                  </Typography>
                </Box>
              )}
            </Paper>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper elevation={3} sx={{ p: 2, borderRadius: 0 }}>
        {/* Example Prompts */}
        {messages.length <= 1 && !isStreaming && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <LightbulbIcon fontSize="small" color="warning" />
              <Typography variant="caption" color="text.secondary">
                Quick Start Examples:
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {examplePrompts.map((prompt, index) => (
                <Chip
                  key={index}
                  label={prompt}
                  size="small"
                  variant="outlined"
                  onClick={() => setInputMessage(prompt)}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'primary.50' }
                  }}
                />
              ))}
            </Box>
            <Divider sx={{ mt: 2 }} />
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Tell me what you'd like to do with this data..."
            disabled={isStreaming}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'white',
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isStreaming}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' },
              '&:disabled': { bgcolor: 'grey.300' },
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
        
        {isComplete && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon color="success" />
            <Typography variant="body2" color="success.main">
              Distribution completed! You can ask follow-up questions or continue to test synthesis.
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
