import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  InputAdornment,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { Add, Search, PersonAdd, ArrowUpward, ArrowDownward } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { trustedPartnersApi } from '../../services/api';
import { TrustedPartner, AvailablePartner } from '../../types/api';
import { hasResponseData } from '../../utils/errorTypeGuards';

interface AddPartnerDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps): React.ReactElement {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`partner-tabpanel-${index}`}
      aria-labelledby={`partner-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

const AddPartnerDialog: React.FC<AddPartnerDialogProps> = ({ open, onClose, onSuccess }) => {
  const [tabValue, setTabValue] = useState(0);
  const [manualFormData, setManualFormData] = useState({
    partner_name: '',
    tax_number: '',
    is_active: true,
    auto_pay: true,
  });
  const [availablePartnersPage, setAvailablePartnersPage] = useState(0);
  const [availablePartnersRowsPerPage, setAvailablePartnersRowsPerPage] = useState(10);
  const [availablePartnersSearch, setAvailablePartnersSearch] = useState('');
  const [availablePartnersOrdering, setAvailablePartnersOrdering] = useState('-last_invoice_date');
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const queryClient = useQueryClient();

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      setTabValue(0);
      setManualFormData({
        partner_name: '',
        tax_number: '',
        is_active: true,
        auto_pay: true,
      });
      setError('');
      setSuccessMessage('');
      setAvailablePartnersPage(0);
      setAvailablePartnersSearch('');
    }
  }, [open]);

  // Fetch available partners from invoices
  const { data: availablePartnersResponse, isLoading: availablePartnersLoading } = useQuery({
    queryKey: [
      'availablePartners',
      {
        page: availablePartnersPage + 1,
        page_size: availablePartnersRowsPerPage,
        search: availablePartnersSearch,
      },
    ],
    queryFn: () =>
      trustedPartnersApi.getAvailablePartners({
        page: availablePartnersPage + 1,
        page_size: availablePartnersRowsPerPage,
        ...(availablePartnersSearch && { search: availablePartnersSearch }),
      }),
    enabled: open && tabValue === 1, // Only fetch when dialog is open and on "From Invoices" tab
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (
      data: Omit<
        TrustedPartner,
        'id' | 'invoice_count' | 'last_invoice_date' | 'created_at' | 'updated_at'
      >
    ) => trustedPartnersApi.create(data),
    onSuccess: (response) => {
      // Show success message
      setSuccessMessage(`Partner "${response.data.partner_name}" sikeresen hozzáadva!`);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);

      // Reset manual form if on manual tab
      if (tabValue === 0) {
        setManualFormData({
          partner_name: '',
          tax_number: '',
          is_active: true,
          auto_pay: true,
        });
      }

      // Invalidate queries to refresh both trusted partners and available partners lists
      void queryClient.invalidateQueries({ queryKey: ['trustedPartners'] });
      void queryClient.invalidateQueries({ queryKey: ['availablePartners'] });

      // Call onSuccess for parent component
      onSuccess();

      // Do NOT close dialog - user can continue adding partners
    },
    onError: (error: unknown) => {
      if (hasResponseData(error)) {
        if (error.response.data.partner_name && Array.isArray(error.response.data.partner_name)) {
          const errorMsg = error.response.data.partner_name[0];
          setError(typeof errorMsg === 'string' ? errorMsg : 'Hiba történt a partner mentésekor');
        } else if (error.response.data.tax_number && Array.isArray(error.response.data.tax_number)) {
          const errorMsg = error.response.data.tax_number[0];
          setError(typeof errorMsg === 'string' ? errorMsg : 'Hiba történt a partner mentésekor');
        } else if (error.response.data.non_field_errors && Array.isArray(error.response.data.non_field_errors)) {
          const errorMsg = error.response.data.non_field_errors[0];
          setError(typeof errorMsg === 'string' ? errorMsg : 'Hiba történt a partner mentésekor');
        } else {
          setError('Hiba történt a partner mentésekor. Kérlek próbáld újra!');
        }
      } else {
        setError('Hiba történt a partner mentésekor. Kérlek próbáld újra!');
      }
    },
  });

  const availablePartners = availablePartnersResponse?.data?.results || [];
  const availablePartnersCount = availablePartnersResponse?.data?.count || 0;

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number): void => {
    setTabValue(newValue);
    setError('');
    setSuccessMessage('');
  };

  const handleManualInputChange =
    (field: keyof typeof manualFormData) =>
    (event: React.ChangeEvent<HTMLInputElement>): void => {
      setManualFormData((prev) => ({
        ...prev,
        [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value,
      }));
      setError('');
    };

  const handleManualSubmit = (): void => {
    if (!manualFormData.partner_name.trim()) {
      setError('Partner neve kötelező mező.');
      return;
    }
    if (!manualFormData.tax_number.trim()) {
      setError('Adószám kötelező mező.');
      return;
    }

    createMutation.mutate(manualFormData);
  };

  const handleAddFromInvoices = (availablePartner: AvailablePartner): void => {
    createMutation.mutate({
      partner_name: availablePartner.partner_name,
      tax_number: availablePartner.tax_number,
      is_active: true,
      auto_pay: true,
    });
  };

  const handleAvailablePartnersPageChange = (_event: unknown, newPage: number): void => {
    setAvailablePartnersPage(newPage);
  };

  const handleAvailablePartnersRowsPerPageChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ): void => {
    setAvailablePartnersRowsPerPage(parseInt(event.target.value, 10));
    setAvailablePartnersPage(0);
  };

  const handleAvailablePartnersSearchChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setAvailablePartnersSearch(event.target.value);
    setAvailablePartnersPage(0);
  };

  const handleSort = (field: string): void => {
    const isCurrentlyAsc = availablePartnersOrdering === field;
    const newOrdering = isCurrentlyAsc ? `-${field}` : field;
    setAvailablePartnersOrdering(newOrdering);
    setAvailablePartnersPage(0);
  };

  const getSortIcon = (field: string): React.ReactElement | null => {
    if (availablePartnersOrdering === field) {
      return <ArrowUpward sx={{ fontSize: 16 }} />;
    } else if (availablePartnersOrdering === `-${field}`) {
      return <ArrowDownward sx={{ fontSize: 16 }} />;
    }
    return null;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h6" fontWeight="600">
          Automatikusan Fizetett Partner Hozzáadása
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Válassz módszert a partner hozzáadásához
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Kézi bevitel" />
            <Tab label="NAV számláktól" />
          </Tabs>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
            {error}
          </Alert>
        )}

        {successMessage && (
          <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
            {successMessage}
          </Alert>
        )}

        {/* Manual Input Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'grid', gap: 2, mt: 1 }}>
            <TextField
              label="Partner neve"
              value={manualFormData.partner_name}
              onChange={handleManualInputChange('partner_name')}
              required
              fullWidth
              placeholder="pl. ITCardigan Kft."
            />

            <TextField
              label="Adószám"
              value={manualFormData.tax_number}
              onChange={handleManualInputChange('tax_number')}
              required
              fullWidth
              placeholder="pl. 12345678-2-44"
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={manualFormData.is_active}
                    onChange={handleManualInputChange('is_active')}
                  />
                }
                label="Aktív"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={manualFormData.auto_pay}
                    onChange={handleManualInputChange('auto_pay')}
                    disabled={!manualFormData.is_active}
                  />
                }
                label="Automatikus fizetés"
              />
            </Box>
          </Box>
        </TabPanel>

        {/* From Invoices Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            NAV számláiból származó partnerek, akik még nincsenek hozzáadva az Automatikusan
            Fizetettnek jelölt Partnerekhez.
          </Typography>

          <TextField
            placeholder="Keresés név vagy adószám alapján..."
            value={availablePartnersSearch}
            onChange={handleAvailablePartnersSearchChange}
            size="small"
            sx={{ mb: 2, minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />

          {availablePartnersLoading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>
                        <Button
                          variant="text"
                          size="small"
                          onClick={() => handleSort('partner_name')}
                          endIcon={getSortIcon('partner_name')}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            color: 'text.primary',
                            '&:hover': { backgroundColor: 'transparent' },
                          }}
                        >
                          Partner neve
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="text"
                          size="small"
                          onClick={() => handleSort('tax_number')}
                          endIcon={getSortIcon('tax_number')}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            color: 'text.primary',
                            '&:hover': { backgroundColor: 'transparent' },
                          }}
                        >
                          Adószám
                        </Button>
                      </TableCell>
                      <TableCell align="center">
                        <Button
                          variant="text"
                          size="small"
                          onClick={() => handleSort('invoice_count')}
                          endIcon={getSortIcon('invoice_count')}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            color: 'text.primary',
                            '&:hover': { backgroundColor: 'transparent' },
                          }}
                        >
                          Számlák száma
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="text"
                          size="small"
                          onClick={() => handleSort('last_invoice_date')}
                          endIcon={getSortIcon('last_invoice_date')}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            color: 'text.primary',
                            '&:hover': { backgroundColor: 'transparent' },
                          }}
                        >
                          Utolsó számla
                        </Button>
                      </TableCell>
                      <TableCell align="center">Művelet</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {availablePartners.map((partner, index) => (
                      <TableRow key={`${partner.tax_number}-${index}`} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight="500">
                            {partner.partner_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {partner.tax_number}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={partner.invoice_count}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {partner.last_invoice_date || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => handleAddFromInvoices(partner)}
                            color="primary"
                            disabled={createMutation.isPending}
                          >
                            <PersonAdd />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    {availablePartners.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                          <Typography variant="body2" color="text.secondary">
                            {availablePartnersSearch
                              ? 'Nincs találat a keresésre.'
                              : 'Nincsenek elérhető partnerek.'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {availablePartners.length > 0 && (
                <TablePagination
                  rowsPerPageOptions={[5, 10, 25]}
                  component="div"
                  count={availablePartnersCount}
                  rowsPerPage={availablePartnersRowsPerPage}
                  page={availablePartnersPage}
                  onPageChange={handleAvailablePartnersPageChange}
                  onRowsPerPageChange={handleAvailablePartnersRowsPerPageChange}
                  labelRowsPerPage="Sorok száma:"
                  labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
                />
              )}
            </>
          )}
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={createMutation.isPending}>
          Bezárás
        </Button>
        {tabValue === 0 && (
          <Button
            onClick={handleManualSubmit}
            variant="contained"
            disabled={createMutation.isPending}
            startIcon={createMutation.isPending ? <CircularProgress size={16} /> : <Add />}
          >
            {createMutation.isPending ? 'Hozzáadás...' : 'Hozzáadás'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AddPartnerDialog;
