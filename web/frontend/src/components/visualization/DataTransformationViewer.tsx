/**
 * Data Transformation Viewer Component
 * 
 * Displays before/after data comparisons with diff highlighting
 * Validates Requirements 20.4, 25.2
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Tabs,
  Tab,
} from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

interface DataRecord {
  [key: string]: any;
}

interface TransformationData {
  before: DataRecord[];
  after: DataRecord[];
  changedFields: string[];
  transformationType: string;
  description?: string;
}

interface DataTransformationViewerProps {
  transformations: TransformationData[];
}

export default function DataTransformationViewer({
  transformations,
}: DataTransformationViewerProps) {
  const [selectedTab, setSelectedTab] = useState(0);

  if (transformations.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No data transformations to display
        </Typography>
      </Paper>
    );
  }

  const currentTransformation = transformations[selectedTab];

  const isFieldChanged = (field: string): boolean => {
    return currentTransformation.changedFields.includes(field);
  };

  const getFieldValue = (record: DataRecord, field: string): string => {
    const value = record[field];
    if (value === null || value === undefined) {
      return '—';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  const renderDiffCell = (
    beforeValue: string,
    afterValue: string,
    isChanged: boolean
  ) => {
    if (!isChanged) {
      return (
        <TableCell>
          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
            {afterValue}
          </Typography>
        </TableCell>
      );
    }

    return (
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              bgcolor: 'error.light',
              color: 'error.contrastText',
              px: 1,
              py: 0.5,
              borderRadius: 1,
              textDecoration: 'line-through',
            }}
          >
            {beforeValue}
          </Typography>
          <ArrowForwardIcon fontSize="small" color="action" />
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              bgcolor: 'success.light',
              color: 'success.contrastText',
              px: 1,
              py: 0.5,
              borderRadius: 1,
            }}
          >
            {afterValue}
          </Typography>
        </Box>
      </TableCell>
    );
  };

  const allFields = currentTransformation.before.length > 0
    ? Object.keys(currentTransformation.before[0])
    : [];

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Data Transformations
      </Typography>

      {/* Transformation Type Tabs */}
      {transformations.length > 1 && (
        <Tabs
          value={selectedTab}
          onChange={(_, newValue) => setSelectedTab(newValue)}
          sx={{ mb: 2 }}
        >
          {transformations.map((t, index) => (
            <Tab key={index} label={t.transformationType} />
          ))}
        </Tabs>
      )}

      {/* Transformation Description */}
      <Box sx={{ mb: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
        <Chip
          label={currentTransformation.transformationType}
          color="primary"
          size="small"
        />
        {currentTransformation.description && (
          <Typography variant="body2" color="text.secondary">
            {currentTransformation.description}
          </Typography>
        )}
      </Box>

      {/* Changed Fields Summary */}
      {currentTransformation.changedFields.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Changed Fields:
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {currentTransformation.changedFields.map(field => (
              <Chip key={field} label={field} size="small" variant="outlined" />
            ))}
          </Box>
        </Box>
      )}

      {/* Data Comparison Table */}
      <TableContainer sx={{ maxHeight: 400 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>Record #</TableCell>
              {allFields.map(field => (
                <TableCell key={field} sx={{ fontWeight: 'bold' }}>
                  {field}
                  {isFieldChanged(field) && (
                    <Chip
                      label="Modified"
                      size="small"
                      color="warning"
                      sx={{ ml: 1, height: 16, fontSize: '0.65rem' }}
                    />
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {currentTransformation.after.slice(0, 10).map((afterRecord, index) => {
              const beforeRecord = currentTransformation.before[index] || {};
              return (
                <TableRow key={index} hover>
                  <TableCell>{index + 1}</TableCell>
                  {allFields.map(field => {
                    const beforeValue = getFieldValue(beforeRecord, field);
                    const afterValue = getFieldValue(afterRecord, field);
                    const isChanged = isFieldChanged(field) && beforeValue !== afterValue;

                    return (
                      <React.Fragment key={field}>
                        {renderDiffCell(beforeValue, afterValue, isChanged)}
                      </React.Fragment>
                    );
                  })}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {currentTransformation.after.length > 10 && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Showing first 10 of {currentTransformation.after.length} records
        </Typography>
      )}
    </Paper>
  );
}
