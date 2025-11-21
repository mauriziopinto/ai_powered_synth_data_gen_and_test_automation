import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  MenuItem,
  TextField,
  Typography,
  Chip,
  Stack,
  Divider,
  Collapse,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { SchemaField } from '../../types';

interface SchemaBuilderProps {
  fields: SchemaField[];
  onChange: (fields: SchemaField[]) => void;
  errors?: Record<string, string>;
}

const DATA_TYPES = [
  'string',
  'integer',
  'float',
  'boolean',
  'date',
  'datetime',
  'email',
  'phone',
  'address',
  'uuid',
];

const CONSTRAINT_TYPES: Record<string, string[]> = {
  string: ['minLength', 'maxLength', 'pattern', 'enum'],
  integer: ['min', 'max', 'enum'],
  float: ['min', 'max', 'precision'],
  date: ['min', 'max', 'format'],
  datetime: ['min', 'max', 'format'],
  email: ['pattern'],
  phone: ['pattern', 'format'],
  address: ['format'],
};

export default function SchemaBuilder({ fields, onChange, errors = {} }: SchemaBuilderProps) {
  const [expandedFields, setExpandedFields] = useState<Set<number>>(new Set());

  const handleAddField = () => {
    const newField: SchemaField = {
      name: '',
      type: 'string',
      constraints: {},
    };
    onChange([...fields, newField]);
    setExpandedFields(new Set([...expandedFields, fields.length]));
  };

  const handleRemoveField = (index: number) => {
    const newFields = fields.filter((_, i) => i !== index);
    onChange(newFields);
    const newExpanded = new Set(expandedFields);
    newExpanded.delete(index);
    setExpandedFields(newExpanded);
  };

  const handleFieldChange = (index: number, field: Partial<SchemaField>) => {
    const newFields = [...fields];
    newFields[index] = { ...newFields[index], ...field };
    onChange(newFields);
  };

  const handleConstraintChange = (index: number, key: string, value: any) => {
    const newFields = [...fields];
    newFields[index] = {
      ...newFields[index],
      constraints: {
        ...newFields[index].constraints,
        [key]: value,
      },
    };
    onChange(newFields);
  };

  const handleRemoveConstraint = (index: number, key: string) => {
    const newFields = [...fields];
    const { [key]: _, ...remainingConstraints } = newFields[index].constraints || {};
    newFields[index] = {
      ...newFields[index],
      constraints: remainingConstraints,
    };
    onChange(newFields);
  };

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedFields);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedFields(newExpanded);
  };

  const getAvailableConstraints = (type: string): string[] => {
    return CONSTRAINT_TYPES[type] || [];
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Schema Definition</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddField}
          size="small"
        >
          Add Field
        </Button>
      </Box>

      {fields.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No fields defined. Click "Add Field" to start building your schema.
        </Alert>
      )}

      <Stack spacing={2}>
        {fields.map((field, index) => {
          const isExpanded = expandedFields.has(index);
          const fieldError = errors[`fields.${index}`];
          const availableConstraints = getAvailableConstraints(field.type);

          return (
            <Card key={index} variant="outlined" sx={{ borderColor: fieldError ? 'error.main' : undefined }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <TextField
                    label="Field Name"
                    value={field.name}
                    onChange={(e) => handleFieldChange(index, { name: e.target.value })}
                    size="small"
                    required
                    error={!!fieldError}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    select
                    label="Data Type"
                    value={field.type}
                    onChange={(e) => handleFieldChange(index, { type: e.target.value, constraints: {} })}
                    size="small"
                    sx={{ minWidth: 150 }}
                  >
                    {DATA_TYPES.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type}
                      </MenuItem>
                    ))}
                  </TextField>
                  <IconButton
                    size="small"
                    onClick={() => toggleExpanded(index)}
                    title={isExpanded ? 'Collapse' : 'Expand constraints'}
                  >
                    {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleRemoveField(index)}
                    title="Remove field"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>

                {fieldError && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                    {fieldError}
                  </Typography>
                )}

                <Collapse in={isExpanded}>
                  <Box sx={{ mt: 2 }}>
                    <Divider sx={{ mb: 2 }} />
                    <Typography variant="subtitle2" gutterBottom>
                      Constraints
                    </Typography>

                    {Object.entries(field.constraints || {}).map(([key, value]) => (
                      <Box key={key} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                        <Chip
                          label={key}
                          size="small"
                          onDelete={() => handleRemoveConstraint(index, key)}
                        />
                        <TextField
                          value={value}
                          onChange={(e) => handleConstraintChange(index, key, e.target.value)}
                          size="small"
                          sx={{ flex: 1 }}
                        />
                      </Box>
                    ))}

                    {availableConstraints.length > 0 && (
                      <TextField
                        select
                        label="Add Constraint"
                        size="small"
                        value=""
                        onChange={(e) => handleConstraintChange(index, e.target.value, '')}
                        sx={{ mt: 1, minWidth: 200 }}
                      >
                        {availableConstraints
                          .filter((c) => !(field.constraints || {})[c])
                          .map((constraint) => (
                            <MenuItem key={constraint} value={constraint}>
                              {constraint}
                            </MenuItem>
                          ))}
                      </TextField>
                    )}
                  </Box>
                </Collapse>
              </CardContent>
            </Card>
          );
        })}
      </Stack>
    </Box>
  );
}
