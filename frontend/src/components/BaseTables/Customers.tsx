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
  TextField,
  Button,
  IconButton,
  Chip,
  Stack,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { useCustomers, useCreateCustomer, useUpdateCustomer, useDeleteCustomer } from '../../hooks/api';
import { Customer } from '../../types/api';
import { useToastContext } from '../../context/ToastContext';
import { useDebounce } from '../../hooks/useDebounce';
import LoadingSpinner from '../UI/LoadingSpinner';

const Customers: React.FC = () => {
  const { success: showSuccess, error: showError } = useToastContext();

  const [searchTerm, setSearchTerm] = useState('');
  const [validOnly, setValidOnly] = useState(true);
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Customer>>({});
  const [originalCustomerBeforeCopy, setOriginalCustomerBeforeCopy] = useState<Customer | null>(null);
  const [isCopyMode, setIsCopyMode] = useState(false);

  const { data, isLoading, refetch } = useCustomers({
    search: debouncedSearchTerm,
    valid_only: validOnly,
  });
  const createMutation = useCreateCustomer();
  const updateMutation = useUpdateCustomer();
  const deleteMutation = useDeleteCustomer();

  const handleStartAdd = () => {
    setIsAdding(true);
    setEditForm({ customer_name: '', cashflow_adjustment: 0, valid_from: '', valid_to: '' });
  };

  const handleCancelEdit = async () => {
    // If we have an original customer that was modified during copy, revert it
    if (originalCustomerBeforeCopy && isCopyMode) {
      try {
        await updateMutation.mutateAsync({
          id: originalCustomerBeforeCopy.id,
          data: {
            ...originalCustomerBeforeCopy,
          } as Partial<Customer>,
        });
        void refetch();
      } catch (error) {
        showError('Hiba történt az eredeti sor visszaállítása során');
      }
    }

    setOriginalCustomerBeforeCopy(null);
    setIsCopyMode(false);
    setEditingId(null);
    setIsAdding(false);
    setEditForm({});
  };

  const handleSaveNew = async () => {
    if (!editForm.customer_name?.trim()) {
      showError('Vevő neve kötelező');
      return;
    }

    try {
      await createMutation.mutateAsync({
        customer_name: editForm.customer_name,
        cashflow_adjustment: editForm.cashflow_adjustment || 0,
        valid_from: editForm.valid_from || null,
        valid_to: editForm.valid_to || null,
      });
      showSuccess('Vevő sikeresen létrehozva');
      handleCancelEdit();
      void refetch();
    } catch (error) {
      showError('Hiba történt a létrehozás során');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingId || !editForm.customer_name || editForm.cashflow_adjustment === undefined) return;

    try {
      // Update the original row (close its validity if in copy mode)
      await updateMutation.mutateAsync({
        id: editingId,
        data: {
          customer_name: editForm.customer_name,
          cashflow_adjustment: editForm.cashflow_adjustment,
          valid_from: editForm.valid_from || null,
          valid_to: editForm.valid_to || null,
        } as Partial<Customer>,
      });

      // If in copy mode, open new add form with copied data
      if (isCopyMode && editForm.valid_to) {
        const validToDate = new Date(editForm.valid_to);
        validToDate.setDate(validToDate.getDate() + 1);
        const isoString = validToDate.toISOString().split('T');
        const newValidFrom = isoString[0] || '';

        setEditingId(null);
        setIsAdding(true);
        setEditForm({
          customer_name: editForm.customer_name,
          cashflow_adjustment: editForm.cashflow_adjustment,
          valid_from: newValidFrom,
          valid_to: '',
        });
        setOriginalCustomerBeforeCopy(null);
        setIsCopyMode(false);
        showSuccess('Előző rekord lezárva. Most szerkessze az új rekordot és mentse el.');
      } else {
        showSuccess('Vevő sikeresen frissítve');
        await handleCancelEdit();
      }

      void refetch();
    } catch (error) {
      showError('Hiba történt a frissítés során');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Biztosan törölni szeretné ezt a vevőt?')) return;

    try {
      await deleteMutation.mutateAsync(id);
      showSuccess('Vevő sikeresen törölve');
      void refetch();
    } catch (error) {
      showError('Hiba történt a törlés során');
    }
  };

  const handleCopyWithNewValidity = (customer: Customer) => {
    // Save the original customer for potential revert
    setOriginalCustomerBeforeCopy({ ...customer });

    // Calculate suggested valid_to for old row (today)
    const todayIsoString = new Date().toISOString().split('T');
    const suggestedValidTo = todayIsoString[0] || '';

    // Start editing the ORIGINAL row with suggested valid_to
    setEditingId(customer.id);
    setEditForm({
      ...customer,
      valid_to: customer.valid_to || suggestedValidTo,
    });

    // Set copy mode flag
    setIsCopyMode(true);

    showSuccess('Állítsa be az érvényesség végét, majd mentse. Új sor létrehozásra kerül.');
  };

  if (isLoading) return <LoadingSpinner />;

  const customers = data?.results || [];

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Vevők</Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControlLabel
            control={<Switch checked={validOnly} onChange={(e) => setValidOnly(e.target.checked)} />}
            label="Csak érvényes rekordok"
          />
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleStartAdd} disabled={isAdding}>
            Új vevő
          </Button>
        </Stack>
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <TextField
                  size="small"
                  placeholder="Vevő neve..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  fullWidth
                />
              </TableCell>
              <TableCell>Cashflow kiigazítás (nap)</TableCell>
              <TableCell>Érvényes tól</TableCell>
              <TableCell>Érvényes ig</TableCell>
              <TableCell>Állapot</TableCell>
              <TableCell align="right">Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isAdding && (
              <TableRow>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.customer_name || ''}
                    onChange={(e) => setEditForm({ ...editForm, customer_name: e.target.value })}
                    placeholder="Vevő neve"
                    fullWidth
                    required
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="number"
                    value={editForm.cashflow_adjustment || 0}
                    onChange={(e) => setEditForm({ ...editForm, cashflow_adjustment: parseInt(e.target.value) })}
                    fullWidth
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="date"
                    value={editForm.valid_from || ''}
                    onChange={(e) => setEditForm({ ...editForm, valid_from: e.target.value })}
                    fullWidth
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="date"
                    value={editForm.valid_to || ''}
                    onChange={(e) => setEditForm({ ...editForm, valid_to: e.target.value })}
                    fullWidth
                  />
                </TableCell>
                <TableCell>-</TableCell>
                <TableCell align="right">
                  <IconButton size="small" color="primary" onClick={handleSaveNew}>
                    <SaveIcon />
                  </IconButton>
                  <IconButton size="small" onClick={handleCancelEdit}>
                    <CancelIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            )}
            {customers.map((customer) =>
              editingId === customer.id ? (
                <TableRow key={customer.id}>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.customer_name || ''}
                      onChange={(e) => setEditForm({ ...editForm, customer_name: e.target.value })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={editForm.cashflow_adjustment || 0}
                      onChange={(e) => setEditForm({ ...editForm, cashflow_adjustment: parseInt(e.target.value) })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="date"
                      value={editForm.valid_from || ''}
                      onChange={(e) => setEditForm({ ...editForm, valid_from: e.target.value })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="date"
                      value={editForm.valid_to || ''}
                      onChange={(e) => setEditForm({ ...editForm, valid_to: e.target.value })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={customer.is_valid ? 'Érvényes' : 'Lejárt'} color={customer.is_valid ? 'success' : 'default'} size="small" />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" color="primary" onClick={handleSaveEdit}>
                      <SaveIcon />
                    </IconButton>
                    <IconButton size="small" onClick={handleCancelEdit}>
                      <CancelIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ) : (
                <TableRow key={customer.id}>
                  <TableCell>{customer.customer_name}</TableCell>
                  <TableCell>{customer.cashflow_adjustment}</TableCell>
                  <TableCell>{customer.valid_from || '-'}</TableCell>
                  <TableCell>{customer.valid_to || '-'}</TableCell>
                  <TableCell>
                    <Chip label={customer.is_valid ? 'Érvényes' : 'Lejárt'} color={customer.is_valid ? 'success' : 'default'} size="small" />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => { setEditingId(customer.id); setEditForm(customer); }}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" color="primary" onClick={() => handleCopyWithNewValidity(customer)}>
                      <ContentCopyIcon />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDelete(customer.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              )
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {customers.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">Nincs megjeleníthető vevő</Typography>
        </Box>
      )}
    </Box>
  );
};

export default Customers;
