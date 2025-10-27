import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Pagination,
  MenuItem,
  InputAdornment,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Sync as SyncIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useBillingoInvoices, useTriggerBillingoSync, useBillingoInvoice } from '../../hooks/useBillingo';
import { useToastContext } from '../../context/ToastContext';
import { BillingoInvoice } from '../../types/api';

const BillingoInvoices: React.FC = () => {
  const { success: showSuccess, error: showError, warning: showWarning } = useToastContext();

  // Filters
  const [search, setSearch] = useState('');
  const [paymentStatus, setPaymentStatus] = useState<string>('all');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Selected invoice for details
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number>(0);

  // Data validation state
  const [dataIssues, setDataIssues] = useState<string[]>([]);

  // Queries
  const { data, isLoading, error, refetch } = useBillingoInvoices({
    page,
    page_size: pageSize,
    ...(paymentStatus !== 'all' && { payment_status: paymentStatus }),
    ...(search && { search }),
    ordering: '-invoice_date',
  });

  const { data: invoiceDetails, isLoading: isLoadingDetails, error: detailsError } = useBillingoInvoice(selectedInvoiceId);

  // Mutations
  const syncMutation = useTriggerBillingoSync();

  // Data validation effect
  useEffect(() => {
    if (data?.results) {
      const issues: string[] = [];

      // Check for invoices with missing required data
      const invalidInvoices = data.results.filter(inv =>
        !inv.invoice_number || !inv.partner_name || !inv.gross_total_formatted
      );

      if (invalidInvoices.length > 0) {
        issues.push(`${invalidInvoices.length} számla hiányos adatokkal`);
      }

      // Check for invoices with unusual amounts
      const zeroAmountInvoices = data.results.filter(inv =>
        parseFloat(inv.gross_total_formatted?.replace(/\s/g, '') || '0') === 0
      );

      if (zeroAmountInvoices.length > 0) {
        issues.push(`${zeroAmountInvoices.length} számla nulla összeggel`);
      }

      // Check for invoices without dates
      const missingDates = data.results.filter(inv =>
        !inv.invoice_date_formatted || !inv.due_date
      );

      if (missingDates.length > 0) {
        issues.push(`${missingDates.length} számla hiányzó dátummal`);
      }

      setDataIssues(issues);
    }
  }, [data]);

  const handleSync = (): void => {
    syncMutation.mutate(undefined, {
      onSuccess: (result) => {
        if (result.invoices_processed === 0) {
          showWarning(
            'Nincs új adat',
            'Nem történt változás a számlákban'
          );
        } else {
          showSuccess(
            'Szinkronizálás sikeres',
            `${result.invoices_processed} számla szinkronizálva (${result.invoices_created} új, ${result.invoices_updated} frissítve)`
          );
        }
        void refetch();
      },
      onError: (err: Error) => {
        showError(
          'Szinkronizálási hiba',
          err.message || 'Ismeretlen hiba történt a szinkronizálás során'
        );
      },
    });
  };

  const handleRetry = (): void => {
    setDataIssues([]);
    void refetch();
  };

  const getPaymentStatusChip = (invoice: BillingoInvoice): React.ReactElement => {
    const statusConfig: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'default' }> = {
      paid: { label: 'Fizetve', color: 'success' },
      outstanding: { label: 'Függőben', color: 'warning' },
      cancelled: { label: 'Sztornózva', color: 'error' },
    };

    const config = statusConfig[invoice.payment_status] || { label: invoice.payment_status, color: 'default' };
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const totalPages = data ? Math.ceil(data.count / pageSize) : 0;

  // Validation: Check if invoice data is complete
  const isInvoiceDataComplete = (invoice: BillingoInvoice): boolean => {
    return !!(
      invoice.invoice_number &&
      invoice.partner_name &&
      invoice.gross_total_formatted &&
      invoice.invoice_date_formatted &&
      invoice.due_date
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Billingo Számlák</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => void refetch()}
            disabled={isLoading}
          >
            Frissítés
          </Button>
          <Button
            variant="contained"
            startIcon={syncMutation.isPending ? <CircularProgress size={20} /> : <SyncIcon />}
            onClick={handleSync}
            disabled={syncMutation.isPending}
          >
            Szinkronizálás
          </Button>
        </Stack>
      </Stack>

      {/* Data Quality Issues Alert */}
      {dataIssues.length > 0 && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          action={
            <Tooltip title="Újraellenőrzés">
              <IconButton size="small" onClick={handleRetry}>
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          }
        >
          <Typography variant="subtitle2" fontWeight="bold">
            Adatminőségi problémák észlelve:
          </Typography>
          <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
            {dataIssues.map((issue, idx) => (
              <li key={idx}><Typography variant="body2">{issue}</Typography></li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            placeholder="Keresés számlaszám vagy partner alapján..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1); // Reset to first page on search
            }}
            size="small"
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            label="Fizetési státusz"
            value={paymentStatus}
            onChange={(e) => {
              setPaymentStatus(e.target.value);
              setPage(1); // Reset to first page on filter change
            }}
            size="small"
            sx={{ minWidth: 200 }}
          >
            <MenuItem value="all">Összes</MenuItem>
            <MenuItem value="outstanding">Függőben</MenuItem>
            <MenuItem value="paid">Fizetve</MenuItem>
            <MenuItem value="cancelled">Sztornózva</MenuItem>
          </TextField>
        </Stack>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={handleRetry}>
              Újra
            </Button>
          }
        >
          <Typography variant="subtitle2" fontWeight="bold">
            Hiba történt a számlák betöltése során
          </Typography>
          <Typography variant="body2">
            {error.message || 'Ismeretlen hiba történt'}
          </Typography>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box display="flex" justifyContent="center" alignItems="center" p={4}>
          <CircularProgress />
          <Typography ml={2} color="text.secondary">
            Számlák betöltése...
          </Typography>
        </Box>
      )}

      {/* Table */}
      {!isLoading && data && (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Státusz</TableCell>
                  <TableCell>Számlaszám</TableCell>
                  <TableCell>Partner</TableCell>
                  <TableCell>Számla kelte</TableCell>
                  <TableCell>Fizetési határidő</TableCell>
                  <TableCell align="right">Összeg</TableCell>
                  <TableCell>Pénznem</TableCell>
                  <TableCell>Fizetés</TableCell>
                  <TableCell align="center">Tételek</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.results.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Stack alignItems="center" py={4} spacing={2}>
                        <InfoIcon color="disabled" sx={{ fontSize: 48 }} />
                        <Typography color="text.secondary">
                          {search || paymentStatus !== 'all'
                            ? 'Nincs a szűrési feltételeknek megfelelő számla'
                            : 'Nincs megjeleníthető számla'
                          }
                        </Typography>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ) : (
                  data.results.map((invoice) => {
                    const dataComplete = isInvoiceDataComplete(invoice);
                    return (
                      <TableRow
                        key={invoice.id}
                        hover
                        sx={{
                          cursor: 'pointer',
                          bgcolor: !dataComplete ? 'warning.50' : 'inherit'
                        }}
                        onClick={() => setSelectedInvoiceId(invoice.id)}
                      >
                        <TableCell>
                          {dataComplete ? (
                            <Tooltip title="Adatok rendben">
                              <CheckCircleIcon color="success" fontSize="small" />
                            </Tooltip>
                          ) : (
                            <Tooltip title="Hiányos adatok">
                              <WarningIcon color="warning" fontSize="small" />
                            </Tooltip>
                          )}
                        </TableCell>
                        <TableCell>{invoice.invoice_number || '-'}</TableCell>
                        <TableCell>{invoice.partner_name || 'Ismeretlen partner'}</TableCell>
                        <TableCell>{invoice.invoice_date_formatted || '-'}</TableCell>
                        <TableCell>{invoice.due_date || '-'}</TableCell>
                        <TableCell align="right">
                          {invoice.gross_total_formatted || '0'}
                        </TableCell>
                        <TableCell>{invoice.currency || 'HUF'}</TableCell>
                        <TableCell>{getPaymentStatusChip(invoice)}</TableCell>
                        <TableCell align="center">{invoice.item_count || 0}</TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mt={3}>
            <Typography color="text.secondary">
              Összesen: {data.count} számla
              {data.count > 0 && ` (${Math.max(1, (page - 1) * pageSize + 1)} - ${Math.min(page * pageSize, data.count)})`}
            </Typography>
            {totalPages > 1 && (
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, value) => setPage(value)}
                color="primary"
              />
            )}
          </Box>
        </>
      )}

      {/* Invoice Details Modal */}
      <Dialog
        open={selectedInvoiceId > 0}
        onClose={() => setSelectedInvoiceId(0)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Számla részletei
          {invoiceDetails && ` - ${invoiceDetails.invoice_number}`}
        </DialogTitle>
        <DialogContent dividers>
          {detailsError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" fontWeight="bold">
                Hiba a számla részleteinek betöltése során
              </Typography>
              <Typography variant="body2">
                {detailsError.message || 'Ismeretlen hiba történt'}
              </Typography>
            </Alert>
          )}

          {isLoadingDetails && (
            <Box display="flex" justifyContent="center" alignItems="center" p={4}>
              <CircularProgress />
              <Typography ml={2}>Részletek betöltése...</Typography>
            </Box>
          )}

          {invoiceDetails && (
            <Stack spacing={2}>
              {/* Header Info */}
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Partner</Typography>
                <Typography variant="body1">{invoiceDetails.partner_name || 'Ismeretlen'}</Typography>
                {invoiceDetails.partner_tax_number && (
                  <Typography variant="body2" color="text.secondary">
                    Adószám: {invoiceDetails.partner_tax_number}
                  </Typography>
                )}
              </Box>

              <Divider />

              {/* Dates */}
              <Stack direction="row" spacing={4}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Számla kelte</Typography>
                  <Typography variant="body1">
                    {invoiceDetails.invoice_date_formatted || '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Teljesítés dátuma</Typography>
                  <Typography variant="body1">
                    {invoiceDetails.fulfillment_date_formatted || '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Fizetési határidő</Typography>
                  <Typography variant="body1">
                    {invoiceDetails.due_date_formatted || '-'}
                  </Typography>
                </Box>
              </Stack>

              <Divider />

              {/* Line Items */}
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Tételek ({invoiceDetails.items?.length || 0})
                </Typography>
                {(invoiceDetails.items?.length === 0 || invoiceDetails.items === undefined) ? (
                  <Alert severity="info">
                    Nincsenek tételek ehhez a számlához
                  </Alert>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Megnevezés</TableCell>
                          <TableCell align="right">Mennyiség</TableCell>
                          <TableCell align="right">Egységár (nettó)</TableCell>
                          <TableCell align="right">ÁFA %</TableCell>
                          <TableCell align="right">Összeg (bruttó)</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {invoiceDetails.items.map((item, index) => (
                          <TableRow key={index}>
                            <TableCell>{item.name || '-'}</TableCell>
                            <TableCell align="right">
                              {item.quantity || 0} {item.unit || ''}
                            </TableCell>
                            <TableCell align="right">{item.net_unit_price || '0'}</TableCell>
                            <TableCell align="right">{item.vat || 0}%</TableCell>
                            <TableCell align="right">{item.gross_amount || '0'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>

              <Divider />

              {/* Totals */}
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="h6">Összesen</Typography>
                <Typography variant="h6" color="primary">
                  {invoiceDetails.gross_total_formatted || '0'} {invoiceDetails.currency || 'HUF'}
                </Typography>
              </Stack>

              {/* Payment Status */}
              <Box>
                <Typography variant="subtitle2" color="text.secondary" mb={1}>
                  Fizetési státusz
                </Typography>
                {getPaymentStatusChip(invoiceDetails)}
                {invoiceDetails.paid_date && invoiceDetails.paid_date_formatted && (
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Fizetve: {invoiceDetails.paid_date_formatted}
                  </Typography>
                )}
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedInvoiceId(0)}>Bezárás</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BillingoInvoices;
