import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  Checkbox,
  Chip,
  Stack,
  Typography,
  Skeleton,
  Box,
  FormControlLabel,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  KeyboardArrowUp as ArrowUpIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import { Beneficiary } from '../../types/api';
import {
  formatAccountNumberOnInput,
  validateAndFormatHungarianAccountNumber,
} from '../../utils/bankAccountValidation';
import {
  validateBeneficiaryName,
  validateRemittanceInfo,
  normalizeWhitespace,
} from '../../utils/stringValidation';

interface BeneficiaryTableProps {
  beneficiaries: Beneficiary[];
  isLoading: boolean;
  onEdit: (beneficiary: Beneficiary) => void;
  onDelete: (id: number) => void;
  onUpdate: (id: number, data: Partial<Beneficiary>) => Promise<void>;
  onSort: (field: string, direction: 'asc' | 'desc') => void;
  sortField?: string;
  sortDirection?: 'asc' | 'desc';
}

// Type guard for backend validation errors
const hasValidationErrors = (
  error: unknown
): error is { response: { status: number; data: Record<string, string | string[]> } } => {
  if (typeof error !== 'object' || error === null) return false;
  if (!('response' in error)) return false;

  const errorWithResponse = error as { response: unknown };
  if (typeof errorWithResponse.response !== 'object' || errorWithResponse.response === null)
    return false;
  if (!('status' in errorWithResponse.response) || !('data' in errorWithResponse.response))
    return false;

  const response = errorWithResponse.response as { status: unknown; data: unknown };
  return typeof response.status === 'number' && typeof response.data === 'object';
};

const BeneficiaryTable: React.FC<BeneficiaryTableProps> = ({
  beneficiaries,
  isLoading,
  onEdit: _onEdit,
  onDelete,
  onUpdate,
  onSort,
  sortField,
  sortDirection,
}) => {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<Beneficiary>>({});
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});

  const handleStartEdit = (beneficiary: Beneficiary) => {
    setEditingId(beneficiary.id);
    setEditData({
      name: beneficiary.name,
      ...(beneficiary.account_number !== undefined && { account_number: beneficiary.account_number }),
      ...(beneficiary.vat_number !== undefined && { vat_number: beneficiary.vat_number }),
      ...(beneficiary.tax_number !== undefined && { tax_number: beneficiary.tax_number }),
      description: beneficiary.description,
      remittance_information: beneficiary.remittance_information,
      is_frequent: beneficiary.is_frequent,
      is_active: beneficiary.is_active,
    });
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      // Toggle direction
      const newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(field, newDirection);
    } else {
      // New field, start with ascending
      onSort(field, 'asc');
    }
  };

  const handleSaveEdit = async () => {
    if (editingId && editData) {
      // Clear previous errors
      setFieldErrors({});

      // Validate that at least one identifier is provided
      if (!editData.account_number && !editData.vat_number && !editData.tax_number) {
        setFieldErrors({
          account_number: 'Meg kell adni a számlaszámot, adóazonosító jelet vagy céges adószámot',
        });
        return;
      }

      // Format account number before saving
      const updatedData = { ...editData };
      if (editData.account_number) {
        const validation = validateAndFormatHungarianAccountNumber(editData.account_number);
        if (validation.isValid) {
          updatedData.account_number = validation.formatted;
        } else {
          setFieldErrors({ account_number: validation.error || 'Érvénytelen számlaszám' });
          return;
        }
      }

      // Validate VAT number if provided
      if (editData.vat_number) {
        const cleanVat = editData.vat_number.replace(/[\s-]/g, '');
        if (!/^\d{10}$/.test(cleanVat)) {
          setFieldErrors({
            vat_number:
              'Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8440961790)',
          });
          return;
        }
        updatedData.vat_number = cleanVat;
      }

      // Validate tax number if provided
      if (editData.tax_number) {
        const cleanTax = editData.tax_number.replace(/[\s-]/g, '');
        if (!/^\d{8}$/.test(cleanTax)) {
          setFieldErrors({
            tax_number: 'Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)',
          });
          return;
        }
        updatedData.tax_number = cleanTax;
      }

      // Validate name
      const nameValidation = validateBeneficiaryName(editData.name || '');
      if (!nameValidation.isValid) {
        setFieldErrors({ name: nameValidation.error || 'Érvénytelen név' });
        return;
      }

      // Validate remittance information
      if (editData.remittance_information) {
        const remittanceValidation = validateRemittanceInfo(editData.remittance_information);
        if (!remittanceValidation.isValid) {
          setFieldErrors({
            remittance_information: remittanceValidation.error || 'Érvénytelen közlemény',
          });
          return;
        }
      }

      // Normalize string fields
      if (updatedData.name) {
        updatedData.name = normalizeWhitespace(updatedData.name);
      }
      if (updatedData.remittance_information) {
        updatedData.remittance_information = normalizeWhitespace(
          updatedData.remittance_information
        );
      }

      try {
        await onUpdate(editingId, updatedData);
        setEditingId(null);
        setEditData({});
        setFieldErrors({});
      } catch (error: unknown) {
        // Handle backend validation errors
        if (hasValidationErrors(error) && error.response.status === 400) {
          const backendErrors = error.response.data;
          const newFieldErrors: { [key: string]: string } = {};

          Object.keys(backendErrors).forEach((field) => {
            const fieldErrors = backendErrors[field];
            const errorMessage = Array.isArray(fieldErrors)
              ? fieldErrors[0] || 'Validation error'
              : fieldErrors || 'Validation error';
            newFieldErrors[field] = errorMessage;
          });

          setFieldErrors(newFieldErrors);
        }
      }
    }
  };

  const handleAccountNumberChange = (value: string) => {
    const formatted = formatAccountNumberOnInput(value);
    setEditData({ ...editData, account_number: formatted });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditData({});
    setFieldErrors({});
  };

  if (isLoading) {
    return (
      <TableContainer sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Table size="small" stickyHeader sx={{ minWidth: 1200 }}>
          <TableHead>
            <TableRow
              sx={{
                '& .MuiTableCell-head': {
                  backgroundColor: 'background.paper',
                  borderBottom: '2px solid',
                  borderBottomColor: 'divider',
                },
              }}
            >
              <TableCell sx={{ width: '20%', minWidth: 200, backgroundColor: 'background.paper' }}>
                Név
              </TableCell>
              <TableCell sx={{ width: '15%', minWidth: 140, backgroundColor: 'background.paper' }}>
                Leírás
              </TableCell>
              <TableCell sx={{ width: '16%', minWidth: 140, backgroundColor: 'background.paper' }}>
                Számlaszám
              </TableCell>
              <TableCell sx={{ width: '10%', minWidth: 100, backgroundColor: 'background.paper' }}>
                Adóazonosító jel
              </TableCell>
              <TableCell sx={{ width: '10%', minWidth: 100, backgroundColor: 'background.paper' }}>
                Céges adószám
              </TableCell>
              <TableCell sx={{ width: '18%', minWidth: 160, backgroundColor: 'background.paper' }}>
                Közlemény
              </TableCell>
              <TableCell sx={{ width: '10%', minWidth: 120, backgroundColor: 'background.paper' }}>
                Állapot
              </TableCell>
              <TableCell
                align="right"
                sx={{ width: '5%', minWidth: 80, backgroundColor: 'background.paper' }}
              >
                Műveletek
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...Array(5)].map((_, i) => (
              <TableRow key={i}>
                <TableCell>
                  <Skeleton variant="text" width="80%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="60%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="90%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="70%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="70%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="70%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="60%" />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width="40%" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  if (beneficiaries.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Nincsenek kedvezményezettek
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer sx={{ flexGrow: 1, overflow: 'auto' }}>
      <Table size="small" stickyHeader sx={{ minWidth: 1200 }}>
        <TableHead>
          <TableRow
            sx={{
              '& .MuiTableCell-head': {
                backgroundColor: 'background.paper',
                borderBottom: '2px solid',
                borderBottomColor: 'divider',
              },
            }}
          >
            <TableCell
              sx={{
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' },
                fontWeight: 600,
                backgroundColor: 'background.paper',
                width: '20%',
                minWidth: 200,
              }}
              onClick={() => handleSort('name')}
            >
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="body2" fontWeight="inherit">
                  Név
                </Typography>
                {sortField === 'name' &&
                  (sortDirection === 'asc' ? (
                    <ArrowUpIcon fontSize="small" />
                  ) : (
                    <ArrowDownIcon fontSize="small" />
                  ))}
              </Stack>
            </TableCell>
            <TableCell
              sx={{
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' },
                fontWeight: 600,
                backgroundColor: 'background.paper',
                width: '15%',
                minWidth: 140,
              }}
              onClick={() => handleSort('description')}
            >
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="body2" fontWeight="inherit">
                  Leírás
                </Typography>
                {sortField === 'description' &&
                  (sortDirection === 'asc' ? (
                    <ArrowUpIcon fontSize="small" />
                  ) : (
                    <ArrowDownIcon fontSize="small" />
                  ))}
              </Stack>
            </TableCell>
            <TableCell
              sx={{
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' },
                fontWeight: 600,
                backgroundColor: 'background.paper',
                width: '18%',
                minWidth: 160,
              }}
              onClick={() => handleSort('account_number')}
            >
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="body2" fontWeight="inherit">
                  Számlaszám
                </Typography>
                {sortField === 'account_number' &&
                  (sortDirection === 'asc' ? (
                    <ArrowUpIcon fontSize="small" />
                  ) : (
                    <ArrowDownIcon fontSize="small" />
                  ))}
              </Stack>
            </TableCell>
            <TableCell
              sx={{
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' },
                fontWeight: 600,
                backgroundColor: 'background.paper',
                width: '12%',
                minWidth: 120,
              }}
              onClick={() => handleSort('vat_number')}
            >
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="body2" fontWeight="inherit">
                  Adóazonosító jel
                </Typography>
                {sortField === 'vat_number' &&
                  (sortDirection === 'asc' ? (
                    <ArrowUpIcon fontSize="small" />
                  ) : (
                    <ArrowDownIcon fontSize="small" />
                  ))}
              </Stack>
            </TableCell>
            <TableCell
              sx={{
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' },
                fontWeight: 600,
                backgroundColor: 'background.paper',
                width: '10%',
                minWidth: 100,
              }}
              onClick={() => handleSort('tax_number')}
            >
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="body2" fontWeight="inherit">
                  Céges adószám
                </Typography>
                {sortField === 'tax_number' &&
                  (sortDirection === 'asc' ? (
                    <ArrowUpIcon fontSize="small" />
                  ) : (
                    <ArrowDownIcon fontSize="small" />
                  ))}
              </Stack>
            </TableCell>
            <TableCell
              sx={{
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' },
                fontWeight: 600,
                backgroundColor: 'background.paper',
                width: '18%',
                minWidth: 160,
              }}
              onClick={() => handleSort('remittance_information')}
            >
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="body2" fontWeight="inherit">
                  Közlemény
                </Typography>
                {sortField === 'remittance_information' &&
                  (sortDirection === 'asc' ? (
                    <ArrowUpIcon fontSize="small" />
                  ) : (
                    <ArrowDownIcon fontSize="small" />
                  ))}
              </Stack>
            </TableCell>
            <TableCell
              sx={{
                fontWeight: 600,
                width: '10%',
                minWidth: 120,
                backgroundColor: 'background.paper',
              }}
            >
              <Typography variant="body2" fontWeight="inherit">
                Állapot
              </Typography>
            </TableCell>
            <TableCell
              align="right"
              sx={{
                fontWeight: 600,
                width: '5%',
                minWidth: 80,
                backgroundColor: 'background.paper',
              }}
            >
              <Typography variant="body2" fontWeight="inherit">
                Műveletek
              </Typography>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {beneficiaries.map((beneficiary) => (
            <TableRow key={beneficiary.id} hover>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.name || ''}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    fullWidth
                    error={!!fieldErrors.name}
                    helperText={fieldErrors.name}
                    sx={{
                      '& .MuiInputBase-input': { fontSize: '0.875rem', py: '6px' },
                    }}
                  />
                ) : (
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Typography variant="body2" fontWeight={500}>
                      {beneficiary.name}
                    </Typography>
                    {beneficiary.is_frequent && (
                      <StarIcon fontSize="small" sx={{ color: 'warning.main' }} />
                    )}
                  </Stack>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.description || ''}
                    onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                    placeholder="Leírás..."
                    fullWidth
                    sx={{
                      '& .MuiInputBase-input': { fontSize: '0.875rem', py: '6px' },
                    }}
                  />
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {beneficiary.description || '-'}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.account_number || ''}
                    onChange={(e) => handleAccountNumberChange(e.target.value)}
                    placeholder="12345678-12345678"
                    fullWidth
                    error={!!fieldErrors.account_number}
                    helperText={fieldErrors.account_number}
                    InputProps={{
                      sx: {
                        fontFamily: 'monospace',
                        letterSpacing: '0.5px',
                        fontSize: '0.875rem',
                      },
                    }}
                    sx={{
                      '& .MuiInputBase-input': { py: '6px' },
                    }}
                  />
                ) : (
                  <Typography variant="body2" fontFamily="monospace">
                    {beneficiary.account_number || '-'}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.vat_number || ''}
                    onChange={(e) => setEditData({ ...editData, vat_number: e.target.value })}
                    placeholder="8440961790"
                    fullWidth
                    error={!!fieldErrors.vat_number}
                    helperText={fieldErrors.vat_number}
                    InputProps={{
                      sx: {
                        fontFamily: 'monospace',
                        letterSpacing: '0.5px',
                        fontSize: '0.875rem',
                      },
                    }}
                    sx={{
                      '& .MuiInputBase-input': { py: '6px' },
                    }}
                  />
                ) : (
                  <Typography variant="body2" fontFamily="monospace">
                    {beneficiary.vat_number || '-'}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.tax_number || ''}
                    onChange={(e) => setEditData({ ...editData, tax_number: e.target.value })}
                    placeholder="12345678"
                    fullWidth
                    error={!!fieldErrors.tax_number}
                    helperText={fieldErrors.tax_number}
                    InputProps={{
                      sx: {
                        fontFamily: 'monospace',
                        letterSpacing: '0.5px',
                        fontSize: '0.875rem',
                      },
                    }}
                  />
                ) : (
                  <Typography variant="body2" fontFamily="monospace">
                    {beneficiary.tax_number || '-'}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.remittance_information || ''}
                    onChange={(e) =>
                      setEditData({ ...editData, remittance_information: e.target.value })
                    }
                    placeholder="Közlemény..."
                    fullWidth
                    sx={{
                      '& .MuiInputBase-input': { fontSize: '0.875rem', py: '6px' },
                    }}
                  />
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {beneficiary.remittance_information || '-'}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <Stack spacing={0.25}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          size="small"
                          checked={editData.is_active || false}
                          onChange={(e) =>
                            setEditData({ ...editData, is_active: e.target.checked })
                          }
                        />
                      }
                      label={
                        <Typography variant="caption" fontSize="0.75rem">
                          Aktív
                        </Typography>
                      }
                      sx={{ m: 0, '& .MuiFormControlLabel-label': { fontSize: '0.75rem' } }}
                    />
                    <FormControlLabel
                      control={
                        <Checkbox
                          size="small"
                          checked={editData.is_frequent || false}
                          onChange={(e) =>
                            setEditData({ ...editData, is_frequent: e.target.checked })
                          }
                        />
                      }
                      label={
                        <Typography variant="caption" fontSize="0.75rem">
                          Gyakori
                        </Typography>
                      }
                      sx={{ m: 0, '& .MuiFormControlLabel-label': { fontSize: '0.75rem' } }}
                    />
                  </Stack>
                ) : (
                  <Stack spacing={0.5}>
                    <Chip
                      label={beneficiary.is_active ? 'Aktív' : 'Inaktív'}
                      size="small"
                      color={beneficiary.is_active ? 'success' : 'error'}
                      variant="outlined"
                    />
                    {beneficiary.is_frequent && (
                      <Chip label="Gyakori" size="small" color="warning" variant="outlined" />
                    )}
                  </Stack>
                )}
              </TableCell>
              <TableCell align="right">
                {editingId === beneficiary.id ? (
                  <Stack direction="row" justifyContent="flex-end" spacing={1}>
                    <IconButton size="small" onClick={handleSaveEdit} color="success">
                      <CheckIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={handleCancelEdit} color="error">
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                ) : (
                  <Stack direction="row" justifyContent="flex-end" spacing={1}>
                    <IconButton
                      size="small"
                      onClick={() => handleStartEdit(beneficiary)}
                      color="primary"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => onDelete(beneficiary.id)} color="error">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default BeneficiaryTable;
