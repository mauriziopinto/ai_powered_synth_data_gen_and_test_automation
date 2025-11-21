/**
 * Test Results Table Component
 * 
 * Displays test execution results in a sortable, filterable table
 * with drill-down capabilities.
 * 
 * Validates Requirements 11.4, 18.5, 19.1
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Chip,
  IconButton,
  Collapse,
  TextField,
  InputAdornment,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  Paper
} from '@mui/material';
import {
  KeyboardArrowDown as ExpandMoreIcon,
  KeyboardArrowUp as ExpandLessIcon,
  Search as SearchIcon,
  CheckCircle as PassedIcon,
  Error as FailedIcon,
  Warning as SkippedIcon,
  BugReport as ErrorIcon
} from '@mui/icons-material';

interface TestCase {
  test_id: string;
  name: string;
  status: 'passed' | 'failed' | 'error' | 'skipped';
  duration_seconds: number;
  error?: string;
  logs?: string;
  jira_issue?: string;
}

interface TestResults {
  workflow_id: string;
  total_tests: number;
  passed: number;
  failed: number;
  skipped: number;
  execution_time_seconds: number;
  test_cases: TestCase[];
}

interface TestResultsTableProps {
  results: TestResults;
}

type SortField = 'name' | 'status' | 'duration_seconds';
type SortOrder = 'asc' | 'desc';

const TestResultsTable: React.FC<TestResultsTableProps> = ({ results }) => {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const handleExpandClick = (testId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(testId)) {
      newExpanded.delete(testId);
    } else {
      newExpanded.add(testId);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <PassedIcon color="success" fontSize="small" />;
      case 'failed':
        return <FailedIcon color="error" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'skipped':
        return <SkippedIcon color="warning" fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (status) {
      case 'passed':
        return 'success';
      case 'failed':
      case 'error':
        return 'error';
      case 'skipped':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  // Filter and sort test cases
  const filteredAndSortedTests = results.test_cases
    .filter(test => {
      const matchesSearch = test.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           test.test_id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || test.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        case 'duration_seconds':
          comparison = a.duration_seconds - b.duration_seconds;
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  const passRate = results.total_tests > 0
    ? ((results.passed / results.total_tests) * 100).toFixed(1)
    : '0.0';

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Test Execution Results
        </Typography>

        {/* Summary Stats */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'success.light' }}>
              <Typography variant="h4" color="success.dark">
                {results.passed}
              </Typography>
              <Typography variant="body2" color="success.dark">
                Passed
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'error.light' }}>
              <Typography variant="h4" color="error.dark">
                {results.failed}
              </Typography>
              <Typography variant="body2" color="error.dark">
                Failed
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'grey.200' }}>
              <Typography variant="h4">
                {passRate}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pass Rate
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'grey.200' }}>
              <Typography variant="h4">
                {formatDuration(results.execution_time_seconds)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Time
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Filters */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} sm={8}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search tests..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="passed">Passed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="error">Error</MenuItem>
                <MenuItem value="skipped">Skipped</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Results Table */}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width={50} />
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'name'}
                    direction={sortField === 'name' ? sortOrder : 'asc'}
                    onClick={() => handleSort('name')}
                  >
                    Test Name
                  </TableSortLabel>
                </TableCell>
                <TableCell width={120}>
                  <TableSortLabel
                    active={sortField === 'status'}
                    direction={sortField === 'status' ? sortOrder : 'asc'}
                    onClick={() => handleSort('status')}
                  >
                    Status
                  </TableSortLabel>
                </TableCell>
                <TableCell width={120}>
                  <TableSortLabel
                    active={sortField === 'duration_seconds'}
                    direction={sortField === 'duration_seconds' ? sortOrder : 'asc'}
                    onClick={() => handleSort('duration_seconds')}
                  >
                    Duration
                  </TableSortLabel>
                </TableCell>
                <TableCell width={150}>Jira Issue</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAndSortedTests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary" sx={{ py: 2 }}>
                      No tests found matching the current filters
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredAndSortedTests.map((test) => (
                  <React.Fragment key={test.test_id}>
                    <TableRow hover>
                      <TableCell>
                        {(test.error || test.logs) && (
                          <IconButton
                            size="small"
                            onClick={() => handleExpandClick(test.test_id)}
                          >
                            {expandedRows.has(test.test_id) ? (
                              <ExpandLessIcon />
                            ) : (
                              <ExpandMoreIcon />
                            )}
                          </IconButton>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getStatusIcon(test.status)}
                          <Typography variant="body2">{test.name}</Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {test.test_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={test.status.toUpperCase()}
                          color={getStatusColor(test.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDuration(test.duration_seconds)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {test.jira_issue && (
                          <Chip
                            label={test.jira_issue}
                            size="small"
                            clickable
                            component="a"
                            href={`https://jira.example.com/browse/${test.jira_issue}`}
                            target="_blank"
                          />
                        )}
                      </TableCell>
                    </TableRow>
                    {(test.error || test.logs) && (
                      <TableRow>
                        <TableCell colSpan={5} sx={{ py: 0, borderBottom: 0 }}>
                          <Collapse in={expandedRows.has(test.test_id)} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 2, backgroundColor: 'grey.50', borderRadius: 1, my: 1 }}>
                              {test.error && (
                                <Box sx={{ mb: 2 }}>
                                  <Typography variant="subtitle2" color="error" gutterBottom>
                                    Error:
                                  </Typography>
                                  <Paper sx={{ p: 1.5, backgroundColor: 'error.light' }}>
                                    <Typography
                                      variant="body2"
                                      component="pre"
                                      sx={{
                                        fontFamily: 'monospace',
                                        fontSize: '0.75rem',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        m: 0
                                      }}
                                    >
                                      {test.error}
                                    </Typography>
                                  </Paper>
                                </Box>
                              )}
                              {test.logs && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Logs:
                                  </Typography>
                                  <Paper sx={{ p: 1.5, backgroundColor: 'white' }}>
                                    <Typography
                                      variant="body2"
                                      component="pre"
                                      sx={{
                                        fontFamily: 'monospace',
                                        fontSize: '0.75rem',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        m: 0,
                                        maxHeight: 300,
                                        overflow: 'auto'
                                      }}
                                    >
                                      {test.logs}
                                    </Typography>
                                  </Paper>
                                </Box>
                              )}
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
          Showing {filteredAndSortedTests.length} of {results.test_cases.length} tests
        </Typography>
      </CardContent>
    </Card>
  );
};

export default TestResultsTable;
