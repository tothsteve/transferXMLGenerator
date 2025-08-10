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
  FormControlLabel
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  KeyboardArrowUp as ArrowUpIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { Beneficiary } from '../../types/api';

interface BeneficiaryTableProps {
  beneficiaries: Beneficiary[];
  isLoading: boolean;
  onEdit: (beneficiary: Beneficiary) => void;
  onDelete: (id: number) => void;
  onUpdate: (id: number, data: Partial<Beneficiary>) => void;
  onSort: (field: string, direction: 'asc' | 'desc') => void;
  sortField?: string;
  sortDirection?: 'asc' | 'desc';
}

const BeneficiaryTable: React.FC<BeneficiaryTableProps> = ({
  beneficiaries,
  isLoading,
  onEdit,
  onDelete,
  onUpdate,
  onSort,
  sortField,
  sortDirection,
}) => {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<Beneficiary>>({});

  const handleStartEdit = (beneficiary: Beneficiary) => {
    setEditingId(beneficiary.id);
    setEditData({
      name: beneficiary.name,
      account_number: beneficiary.account_number,
      notes: beneficiary.notes,
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

  const SortableHeader: React.FC<{ field: string; children: React.ReactNode }> = ({ field, children }) => (
    <TableCell 
      sx={{ 
        cursor: 'pointer',
        '&:hover': { backgroundColor: 'action.hover' },
        fontWeight: 600
      }}
      onClick={() => handleSort(field)}
    >
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <Typography variant="body2" fontWeight="inherit">
          {children}
        </Typography>
        {sortField === field && (
          sortDirection === 'asc' ? 
            <ArrowUpIcon fontSize="small" /> : 
            <ArrowDownIcon fontSize="small" />
        )}
      </Stack>
    </TableCell>
  );

  const handleSaveEdit = () => {
    if (editingId && editData) {
      onUpdate(editingId, editData);
      setEditingId(null);
      setEditData({});
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditData({});
  };

  if (isLoading) {
    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Név</TableCell>
              <TableCell>Megjegyzés</TableCell>
              <TableCell>Számlaszám</TableCell>
              <TableCell>Állapot</TableCell>
              <TableCell align="right">Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...Array(5)].map((_, i) => (
              <TableRow key={i}>
                <TableCell><Skeleton variant="text" width="80%" /></TableCell>
                <TableCell><Skeleton variant="text" width="60%" /></TableCell>
                <TableCell><Skeleton variant="text" width="90%" /></TableCell>
                <TableCell><Skeleton variant="text" width="60%" /></TableCell>
                <TableCell><Skeleton variant="text" width="40%" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  if (beneficiaries.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Nincsenek kedvezményezettek
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <SortableHeader field="name">Név</SortableHeader>
            <SortableHeader field="notes">Megjegyzés</SortableHeader>
            <SortableHeader field="account_number">Számlaszám</SortableHeader>
            <TableCell sx={{ fontWeight: 600 }}>
              <Typography variant="body2" fontWeight="inherit">
                Állapot
              </Typography>
            </TableCell>
            <TableCell align="right" sx={{ fontWeight: 600 }}>
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
                    multiline
                    rows={2}
                    value={editData.notes || ''}
                    onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
                    placeholder="Megjegyzés..."
                    fullWidth
                  />
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 200 }}>
                    {beneficiary.notes || '-'}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <TextField
                    size="small"
                    value={editData.account_number || ''}
                    onChange={(e) => setEditData({ ...editData, account_number: e.target.value })}
                    fullWidth
                  />
                ) : (
                  <Typography variant="body2" fontFamily="monospace">
                    {beneficiary.account_number}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {editingId === beneficiary.id ? (
                  <Stack spacing={0.5}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          size="small"
                          checked={editData.is_active || false}
                          onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })}
                        />
                      }
                      label={<Typography variant="caption">Aktív</Typography>}
                      sx={{ m: 0 }}
                    />
                    <FormControlLabel
                      control={
                        <Checkbox
                          size="small"
                          checked={editData.is_frequent || false}
                          onChange={(e) => setEditData({ ...editData, is_frequent: e.target.checked })}
                        />
                      }
                      label={<Typography variant="caption">Gyakori</Typography>}
                      sx={{ m: 0 }}
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
                      <Chip
                        label="Gyakori"
                        size="small"
                        color="warning"
                        variant="outlined"
                      />
                    )}
                  </Stack>
                )}
              </TableCell>
              <TableCell align="right">
                {editingId === beneficiary.id ? (
                  <Stack direction="row" justifyContent="flex-end" spacing={1}>
                    <IconButton
                      size="small"
                      onClick={handleSaveEdit}
                      color="success"
                    >
                      <CheckIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={handleCancelEdit}
                      color="error"
                    >
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
                    <IconButton
                      size="small"
                      onClick={() => onDelete(beneficiary.id)}
                      color="error"
                    >
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