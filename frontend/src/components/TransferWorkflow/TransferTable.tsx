import React, { useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  IconButton,
  TextField,
  Box,
  Stack,
  Chip,
  Avatar,
  Tooltip
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Add as AddIcon,
  CalendarToday as CalendarIcon,
  AccountBalance as CurrencyIcon
} from '@mui/icons-material';
import { Transfer, Beneficiary } from '../../types/api';

interface TransferData extends Omit<Transfer, 'id' | 'is_processed' | 'created_at'> {
  id?: number;
  beneficiary_data?: Beneficiary;
  tempId?: string;
}

interface TransferTableProps {
  transfers: TransferData[];
  onUpdateTransfer: (index: number, transfer: Partial<TransferData>) => void;
  onDeleteTransfer: (index: number) => void;
  onAddTransfer: () => void;
}

const TransferTable: React.FC<TransferTableProps> = ({
  transfers,
  onUpdateTransfer,
  onDeleteTransfer,
  onAddTransfer,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<TransferData>>({});

  const handleStartEdit = (index: number, transfer: TransferData) => {
    setEditingIndex(index);
    setEditData({
      amount: transfer.amount,
      execution_date: transfer.execution_date,
      remittance_info: transfer.remittance_info,
    });
  };

  const handleSaveEdit = () => {
    if (editingIndex !== null) {
      onUpdateTransfer(editingIndex, editData);
      setEditingIndex(null);
      setEditData({});
    }
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditData({});
  };

  const totalAmount = transfers.reduce((sum, transfer) => 
    sum + (parseFloat(transfer.amount) || 0), 0
  );

  if (transfers.length === 0) {
    return (
      <Paper elevation={1}>
        <Box sx={{ p: 6, textAlign: 'center' }}>
          <CurrencyIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Nincsenek átutalások
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Válasszon ki egy sablont vagy adjon hozzá manuálisan átutalásokat.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={onAddTransfer}
          >
            Átutalás hozzáadása
          </Button>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={1}>
      {/* Header */}
      <Box sx={{ px: 3, py: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          Átutalások ({transfers.length})
        </Typography>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={onAddTransfer}
          size="small"
        >
          Hozzáadás
        </Button>
      </Box>

      {/* Table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Kedvezményezett</TableCell>
              <TableCell>Összeg (HUF)</TableCell>
              <TableCell>Teljesítés dátuma</TableCell>
              <TableCell>Közlemény</TableCell>
              <TableCell align="right">Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {transfers.map((transfer, index) => (
              <TableRow key={transfer.id || transfer.tempId || index} hover>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight={500}>
                      {transfer.beneficiary_data?.name || `Kedvezményezett #${transfer.beneficiary}`}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                      {transfer.beneficiary_data?.account_number}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  {editingIndex === index ? (
                    <TextField
                      type="number"
                      size="small"
                      value={editData.amount || ''}
                      onChange={(e) => setEditData({ ...editData, amount: e.target.value })}
                      placeholder="0"
                      sx={{ width: 120 }}
                      InputProps={{ inputProps: { step: 1 } }}
                    />
                  ) : (
                    <Typography variant="body2">
                      {parseFloat(transfer.amount).toLocaleString('hu-HU')} HUF
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {editingIndex === index ? (
                    <TextField
                      type="date"
                      size="small"
                      value={editData.execution_date || ''}
                      onChange={(e) => setEditData({ ...editData, execution_date: e.target.value })}
                      sx={{ width: 150 }}
                    />
                  ) : (
                    <Stack direction="row" alignItems="center" spacing={0.5}>
                      <CalendarIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {new Date(transfer.execution_date).toLocaleDateString('hu-HU')}
                      </Typography>
                    </Stack>
                  )}
                </TableCell>
                <TableCell>
                  {editingIndex === index ? (
                    <TextField
                      size="small"
                      value={editData.remittance_info || ''}
                      onChange={(e) => setEditData({ ...editData, remittance_info: e.target.value })}
                      placeholder="Közlemény..."
                      fullWidth
                    />
                  ) : (
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {transfer.remittance_info || '-'}
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="right">
                  {editingIndex === index ? (
                    <Stack direction="row" justifyContent="flex-end" spacing={0.5}>
                      <Tooltip title="Mentés">
                        <IconButton
                          onClick={handleSaveEdit}
                          size="small"
                          color="success"
                        >
                          <CheckIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Mégse">
                        <IconButton
                          onClick={handleCancelEdit}
                          size="small"
                          color="error"
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  ) : (
                    <Stack direction="row" justifyContent="flex-end" spacing={0.5}>
                      <Tooltip title="Szerkesztés">
                        <IconButton
                          onClick={() => handleStartEdit(index, transfer)}
                          size="small"
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Törlés">
                        <IconButton
                          onClick={() => onDeleteTransfer(index)}
                          size="small"
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Footer with totals */}
      <Box sx={{ px: 3, py: 2, bgcolor: 'grey.50', borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {transfers.length} átutalás összesen
        </Typography>
        <Typography variant="h6" fontWeight="bold">
          Összeg: {totalAmount.toLocaleString('hu-HU')} HUF
        </Typography>
      </Box>
    </Paper>
  );
};

export default TransferTable;