import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Switch,
  FormControlLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Tooltip,
  InputAdornment,
} from '@mui/material';
import {
  Edit,
  Delete,
  Add,
  Search,
  CheckCircle,
  Cancel,
  PersonAdd,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { trustedPartnersApi } from '../../services/api';
import { TrustedPartner, AvailablePartner } from '../../types/api';
import AddPartnerDialog from './AddPartnerDialog';

const TrustedPartners: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingPartner, setEditingPartner] = useState<TrustedPartner | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  // Fetch trusted partners
  const { data: partnersResponse, isLoading, error } = useQuery({
    queryKey: ['trustedPartners', { page: page + 1, page_size: rowsPerPage, search: searchTerm }],
    queryFn: () => trustedPartnersApi.getAll({ 
      page: page + 1, 
      page_size: rowsPerPage,
      search: searchTerm || undefined,
      ordering: '-created_at'
    }),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => trustedPartnersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trustedPartners'] });
      setDeleteConfirmId(null);
    },
  });

  // Toggle active status mutation
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => 
      trustedPartnersApi.partialUpdate(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trustedPartners'] });
    },
  });

  // Toggle auto-pay mutation
  const toggleAutoPayMutation = useMutation({
    mutationFn: ({ id, auto_pay }: { id: number; auto_pay: boolean }) => 
      trustedPartnersApi.partialUpdate(id, { auto_pay }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trustedPartners'] });
    },
  });

  const partners = partnersResponse?.data?.results || [];
  const totalCount = partnersResponse?.data?.count || 0;

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const handleDelete = (id: number) => {
    setDeleteConfirmId(id);
  };

  const confirmDelete = () => {
    if (deleteConfirmId) {
      deleteMutation.mutate(deleteConfirmId);
    }
  };

  const handleToggleActive = (partner: TrustedPartner) => {
    toggleActiveMutation.mutate({ id: partner.id, is_active: !partner.is_active });
  };

  const handleToggleAutoPay = (partner: TrustedPartner) => {
    toggleAutoPayMutation.mutate({ id: partner.id, auto_pay: !partner.auto_pay });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Hiba történt a megbízható partnerek betöltésekor.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="600">
          Megbízható Partnerek
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setIsAddDialogOpen(true)}
        >
          Partner hozzáadása
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        A megbízható partnerektől érkező számlák automatikusan kifizetve lesznek a NAV szinkronizáció során.
      </Typography>

      <Paper elevation={2} sx={{ width: '100%', overflow: 'hidden' }}>
        {/* Search */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <TextField
            placeholder="Keresés név vagy adószám alapján..."
            value={searchTerm}
            onChange={handleSearchChange}
            size="small"
            sx={{ minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Partner neve</TableCell>
                <TableCell>Adószám</TableCell>
                <TableCell align="center">Aktív</TableCell>
                <TableCell align="center">Automatikus fizetés</TableCell>
                <TableCell align="center">Számlák száma</TableCell>
                <TableCell>Utolsó számla</TableCell>
                <TableCell align="center">Műveletek</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {partners.map((partner) => (
                <TableRow key={partner.id} hover>
                  <TableCell>
                    <Typography variant="subtitle2" fontWeight="600">
                      {partner.partner_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {partner.tax_number}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Switch
                      checked={partner.is_active ?? false}
                      onChange={() => handleToggleActive(partner)}
                      color="primary"
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Switch
                      checked={partner.auto_pay ?? false}
                      onChange={() => handleToggleAutoPay(partner)}
                      color="success"
                      size="small"
                      disabled={!(partner.is_active ?? false)}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={partner.invoice_count}
                      size="small"
                      color={partner.invoice_count > 0 ? 'primary' : 'default'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {partner.last_invoice_date_formatted || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="Törlés">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(partner.id)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
              {partners.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      {searchTerm ? 'Nincs találat a keresésre.' : 'Még nincsenek megbízható partnerek hozzáadva.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={totalCount}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Sorok száma oldalanként:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
        />
      </Paper>

      {/* Add Partner Dialog */}
      <AddPartnerDialog
        open={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['trustedPartners'] });
          setIsAddDialogOpen(false);
        }}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
      >
        <DialogTitle>Partner törlése</DialogTitle>
        <DialogContent>
          <Typography>
            Biztosan törölni szeretnéd ezt a megbízható partnert? Ez a művelet nem vonható vissza.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmId(null)}>
            Mégse
          </Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
            startIcon={deleteMutation.isPending ? <CircularProgress size={16} /> : <Delete />}
          >
            {deleteMutation.isPending ? 'Törlés...' : 'Törlés'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TrustedPartners;