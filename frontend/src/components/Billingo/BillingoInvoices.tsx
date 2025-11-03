import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  MenuItem,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Tooltip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridSortModel, GridRowParams, GridFilterModel } from '@mui/x-data-grid';
import { useBillingoInvoices, useTriggerBillingoSync, useBillingoInvoice } from '../../hooks/useBillingo';
import { useToastContext } from '../../context/ToastContext';
import { BillingoInvoice } from '../../types/api';

const BillingoInvoices: React.FC = () => {
  const { success: showSuccess, error: showError, warning: showWarning } = useToastContext();

  // Column-specific filters with operators
  // String filters
  const [invoiceNumberFilter, setInvoiceNumberFilter] = useState('');
  const [invoiceNumberOperator, setInvoiceNumberOperator] = useState('contains');
  const [partnerNameFilter, setPartnerNameFilter] = useState('');
  const [partnerNameOperator, setPartnerNameOperator] = useState('contains');
  const [typeFilter, setTypeFilter] = useState('');
  const [typeOperator, setTypeOperator] = useState('contains');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState('');
  const [paymentStatusOperator, setPaymentStatusOperator] = useState('equals');

  // Boolean filter
  const [cancelledFilter, setCancelledFilter] = useState('');
  const [cancelledOperator, setCancelledOperator] = useState('is');

  // Date filters
  const [invoiceDateFilter, setInvoiceDateFilter] = useState('');
  const [invoiceDateOperator, setInvoiceDateOperator] = useState('is');
  const [dueDateFilter, setDueDateFilter] = useState('');
  const [dueDateOperator, setDueDateOperator] = useState('is');

  // Numeric filters
  const [grossTotalFilter, setGrossTotalFilter] = useState('');
  const [grossTotalOperator, setGrossTotalOperator] = useState('=');
  const [netTotalFilter, setNetTotalFilter] = useState('');
  const [netTotalOperator, setNetTotalOperator] = useState('=');

  // Related documents filter (hide invoices with related documents - corrections, storno, etc.)
  const [hideRelatedInvoices, setHideRelatedInvoices] = useState(true);

  // Legacy filters (kept for backward compatibility)
  const [invoiceDateFromFilter, setInvoiceDateFromFilter] = useState('');
  const [invoiceDateToFilter, setInvoiceDateToFilter] = useState('');
  const [dueDateFromFilter, setDueDateFromFilter] = useState('');
  const [dueDateToFilter, setDueDateToFilter] = useState('');
  const [paymentStatus, setPaymentStatus] = useState<string>('all');

  const [page, setPage] = useState(0); // DataGrid uses 0-based indexing
  const [pageSize, setPageSize] = useState(20);

  // Sorting
  const [sortModel, setSortModel] = useState<GridSortModel>([
    { field: 'invoice_date', sort: 'desc' }
  ]);

  // DataGrid filter model
  const [filterModel, setFilterModel] = useState<GridFilterModel>({ items: [] });

  // Selected invoice for details
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number>(0);

  // Data validation state
  const [dataIssues, setDataIssues] = useState<string[]>([]);

  // Map frontend field names to backend field names for sorting
  const mapFieldNameToBackend = (fieldName: string): string => {
    const fieldMap: Record<string, string> = {
      'invoice_date_formatted': 'invoice_date',
      'gross_total_formatted': 'gross_total',
    };
    return fieldMap[fieldName] || fieldName;
  };

  // Queries
  const frontendOrderField = sortModel[0]?.field || 'invoice_date';
  const orderField = mapFieldNameToBackend(frontendOrderField);
  const orderDirection = sortModel[0]?.sort || 'desc';

  // Memoize query params to ensure stable reference for React Query
  const queryParams = useMemo(() => ({
    page: page + 1, // Convert back to 1-based for backend
    page_size: pageSize,
    // String filters with operators
    ...(invoiceNumberFilter && {
      invoice_number: invoiceNumberFilter,
      invoice_number_operator: invoiceNumberOperator
    }),
    ...(partnerNameFilter && {
      partner_name: partnerNameFilter,
      partner_name_operator: partnerNameOperator
    }),
    ...(typeFilter && {
      type: typeFilter,
      type_operator: typeOperator
    }),
    ...(paymentStatusFilter && {
      payment_status: paymentStatusFilter,
      payment_status_operator: paymentStatusOperator
    }),
    // Boolean filter
    ...(cancelledFilter && {
      cancelled: cancelledFilter,
      cancelled_operator: cancelledOperator
    }),
    // Date filters with operators
    ...(invoiceDateFilter && {
      invoice_date: invoiceDateFilter,
      invoice_date_operator: invoiceDateOperator
    }),
    ...(dueDateFilter && {
      due_date: dueDateFilter,
      due_date_operator: dueDateOperator
    }),
    // Numeric filters with operators
    ...(grossTotalFilter && {
      gross_total: grossTotalFilter,
      gross_total_operator: grossTotalOperator
    }),
    ...(netTotalFilter && {
      net_total: netTotalFilter,
      net_total_operator: netTotalOperator
    }),
    // Related documents filter
    hide_related_invoices: hideRelatedInvoices,
    // Legacy filters (for backward compatibility)
    ...(paymentStatus !== 'all' && { payment_status: paymentStatus }),
    ...(invoiceDateFromFilter && { from_date: invoiceDateFromFilter }),
    ...(invoiceDateToFilter && { to_date: invoiceDateToFilter }),
    ...(dueDateFromFilter && { due_date_from: dueDateFromFilter }),
    ...(dueDateToFilter && { due_date_to: dueDateToFilter }),
    ordering: `${orderDirection === 'desc' ? '-' : ''}${orderField}`,
  }), [
    page, pageSize,
    invoiceNumberFilter, invoiceNumberOperator,
    partnerNameFilter, partnerNameOperator,
    typeFilter, typeOperator,
    paymentStatusFilter, paymentStatusOperator,
    cancelledFilter, cancelledOperator,
    invoiceDateFilter, invoiceDateOperator,
    dueDateFilter, dueDateOperator,
    grossTotalFilter, grossTotalOperator,
    netTotalFilter, netTotalOperator,
    hideRelatedInvoices,
    paymentStatus, invoiceDateFromFilter, invoiceDateToFilter,
    dueDateFromFilter, dueDateToFilter,
    orderField, orderDirection
  ]);

  const { data, isLoading, error, refetch } = useBillingoInvoices(queryParams);

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
    syncMutation.mutate(false, {
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

  const handleFullSync = (): void => {
    syncMutation.mutate(true, {
      onSuccess: (result) => {
        showSuccess(
          'Teljes szinkronizálás sikeres',
          `${result.invoices_processed} számla szinkronizálva (${result.invoices_created} új, ${result.invoices_updated} frissítve)`
        );
        void refetch();
      },
      onError: (err: Error) => {
        showError(
          'Teljes szinkronizálási hiba',
          err.message || 'Ismeretlen hiba történt a teljes szinkronizálás során'
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

  // Define DataGrid columns
  const columns: GridColDef[] = [
    {
      field: 'type',
      headerName: 'Típus',
      width: 120,
      filterable: true,
    },
    {
      field: 'invoice_number',
      headerName: 'Számlaszám',
      width: 180,
      filterable: true,
    },
    {
      field: 'partner_name',
      headerName: 'Partner',
      width: 250,
      filterable: true,
    },
    {
      field: 'invoice_date_formatted',
      headerName: 'Számla kelte',
      width: 150,
      filterable: true,
      type: 'date',
      valueGetter: (_value, row) => {
        const invoice = row as BillingoInvoice;
        return invoice.invoice_date_formatted ? new Date(invoice.invoice_date_formatted) : null;
      },
    },
    {
      field: 'due_date',
      headerName: 'Fizetési határidő',
      width: 150,
      filterable: true,
      type: 'date',
      valueGetter: (_value, row) => {
        const invoice = row as BillingoInvoice;
        return invoice.due_date ? new Date(invoice.due_date) : null;
      },
    },
    {
      field: 'gross_total_formatted',
      headerName: 'Bruttó',
      width: 150,
      align: 'right',
      headerAlign: 'right',
      filterable: true,
    },
    {
      field: 'net_total',
      headerName: 'Nettó',
      width: 150,
      align: 'right',
      headerAlign: 'right',
      filterable: true,
      renderCell: (params) => {
        const invoice = params.row as BillingoInvoice;
        const gross = parseFloat(invoice.gross_total_formatted?.replace(/[^\d.-]/g, '') || '0');
        const net = gross / 1.27;
        return `${net.toLocaleString('hu-HU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${invoice.currency || 'HUF'}`;
      },
    },
    {
      field: 'currency',
      headerName: 'Pénznem',
      width: 100,
      sortable: false,
      filterable: false,
    },
    {
      field: 'payment_status',
      headerName: 'Fizetés',
      width: 130,
      filterable: true,
      renderCell: (params) => {
        return getPaymentStatusChip(params.row as BillingoInvoice);
      },
    },
    {
      field: 'cancelled',
      headerName: 'Sztornó',
      width: 100,
      filterable: true,
      type: 'boolean',
      renderCell: (params) => {
        const invoice = params.row as BillingoInvoice;
        return invoice.cancelled ? (
          <Chip label="Sztornó" color="error" size="small" />
        ) : null;
      },
    },
    {
      field: 'item_count',
      headerName: 'Tételek',
      width: 100,
      align: 'center',
      headerAlign: 'center',
      sortable: false,
      filterable: false,
      renderCell: (params) => (params.row as BillingoInvoice).item_count || 0,
    },
    {
      field: 'related_documents_count',
      headerName: 'Kapcsolódó dok.',
      width: 140,
      align: 'center',
      headerAlign: 'center',
      sortable: false,
      filterable: false,
      renderCell: (params) => {
        const count = (params.row as BillingoInvoice).related_documents_count || 0;
        return count > 0 ? (
          <Chip label={count} color="warning" size="small" />
        ) : (
          '—'
        );
      },
    },
  ];

  // Calculate totals for current page
  const calculateTotals = () => {
    if (!data?.results) return { gross: 0, net: 0, count: 0 };

    const gross = data.results.reduce((sum, invoice) => {
      const value = parseFloat(invoice.gross_total_formatted?.replace(/[^\d.-]/g, '') || '0');
      return sum + value;
    }, 0);

    const net = data.results.reduce((sum, invoice) => {
      const value = parseFloat(invoice.gross_total_formatted?.replace(/[^\d.-]/g, '') || '0');
      return sum + (value / 1.27);
    }, 0);

    return { gross, net, count: data.results.length };
  };

  const totals = calculateTotals();

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
            variant="outlined"
            color="primary"
            startIcon={syncMutation.isPending ? <CircularProgress size={20} /> : <SyncIcon />}
            onClick={handleSync}
            disabled={syncMutation.isPending}
          >
            Szinkronizálás (utolsó óta)
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={syncMutation.isPending ? <CircularProgress size={20} /> : <RefreshIcon />}
            onClick={handleFullSync}
            disabled={syncMutation.isPending}
          >
            Teljes szinkronizálás
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

      {/* Column Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom fontWeight="bold">
          Szűrők
        </Typography>
        <Stack spacing={2}>
          {/* Row 1: Text filters */}
          <Stack direction="row" spacing={2}>
            <TextField
              label="Számlaszám"
              placeholder="Keresés számlaszámra..."
              value={invoiceNumberFilter}
              onChange={(e) => {
                setInvoiceNumberFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              sx={{ flexGrow: 1 }}
            />
            <TextField
              label="Partner név"
              placeholder="Keresés partnerre..."
              value={partnerNameFilter}
              onChange={(e) => {
                setPartnerNameFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              sx={{ flexGrow: 1 }}
            />
            <TextField
              select
              label="Fizetési státusz"
              value={paymentStatus}
              onChange={(e) => {
                setPaymentStatus(e.target.value);
                setPage(0);
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

          {/* Row 2: Date filters */}
          <Stack direction="row" spacing={2}>
            <TextField
              label="Számla kelte (tól)"
              type="date"
              value={invoiceDateFromFilter}
              onChange={(e) => {
                setInvoiceDateFromFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              InputLabelProps={{ shrink: true }}
              sx={{ flexGrow: 1 }}
            />
            <TextField
              label="Számla kelte (ig)"
              type="date"
              value={invoiceDateToFilter}
              onChange={(e) => {
                setInvoiceDateToFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              InputLabelProps={{ shrink: true }}
              sx={{ flexGrow: 1 }}
            />
            <TextField
              label="Fizetési határidő (tól)"
              type="date"
              value={dueDateFromFilter}
              onChange={(e) => {
                setDueDateFromFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              InputLabelProps={{ shrink: true }}
              sx={{ flexGrow: 1 }}
            />
            <TextField
              label="Fizetési határidő (ig)"
              type="date"
              value={dueDateToFilter}
              onChange={(e) => {
                setDueDateToFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              InputLabelProps={{ shrink: true }}
              sx={{ flexGrow: 1 }}
            />
          </Stack>

          {/* Related Documents Filter */}
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControlLabel
              control={
                <Checkbox
                  checked={hideRelatedInvoices}
                  onChange={(e) => {
                    setHideRelatedInvoices(e.target.checked);
                    setPage(0);
                  }}
                />
              }
              label="Kapcsolódó dokumentumok elrejtése (sztornó, helyesbítés)"
            />
            {!hideRelatedInvoices && (
              <Chip
                label="Kapcsolódó dokumentumok láthatóak"
                color="warning"
                size="small"
                variant="outlined"
              />
            )}
          </Stack>

          {/* Clear Filters Button */}
          <Stack direction="row" justifyContent="flex-end">
            <Button
              size="small"
              onClick={() => {
                setInvoiceNumberFilter('');
                setPartnerNameFilter('');
                setInvoiceDateFromFilter('');
                setInvoiceDateToFilter('');
                setDueDateFromFilter('');
                setDueDateToFilter('');
                setPaymentStatus('all');
                setHideRelatedInvoices(true);
                setPage(0);
              }}
            >
              Szűrők törlése
            </Button>
          </Stack>
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

      {/* DataGrid */}
      <Paper sx={{ height: 700, width: '100%' }}>
        <DataGrid
          rows={data?.results || []}
          columns={columns}
          paginationMode="server"
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={(model) => {
            setPage(model.page);
            setPageSize(model.pageSize);
          }}
          pageSizeOptions={[10, 20, 50, 100]}
          rowCount={data?.count || 0}
          loading={isLoading}
          sortingMode="server"
          sortModel={sortModel}
          onSortModelChange={(newSortModel) => setSortModel(newSortModel)}
          filterMode="server"
          filterModel={filterModel}
          onFilterModelChange={(newFilterModel) => {
            setFilterModel(newFilterModel);
            // Convert DataGrid filter to our backend format
            const filters = newFilterModel.items[0];

            // Helper to convert Date object or ISO datetime string to YYYY-MM-DD
            const formatDateForBackend = (value: string | Date | null | undefined): string => {
              if (!value) return '';

              // If it's a Date object, format it to YYYY-MM-DD
              if (value instanceof Date) {
                const year = value.getFullYear();
                const month = String(value.getMonth() + 1).padStart(2, '0');
                const day = String(value.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
              }

              // If it's an ISO datetime string, extract just the date part
              if (typeof value === 'string' && value.includes('T')) {
                return value.split('T')[0] ?? value;
              }

              return String(value);
            };

            if (filters) {
              switch (filters.field) {
                // String filters
                case 'invoice_number':
                  setInvoiceNumberFilter(filters.value || '');
                  setInvoiceNumberOperator(filters.operator || 'contains');
                  break;
                case 'partner_name':
                  setPartnerNameFilter(filters.value || '');
                  setPartnerNameOperator(filters.operator || 'contains');
                  break;
                case 'type':
                  setTypeFilter(filters.value || '');
                  setTypeOperator(filters.operator || 'contains');
                  break;
                case 'payment_status':
                  setPaymentStatusFilter(filters.value || '');
                  setPaymentStatusOperator(filters.operator || 'equals');
                  break;
                // Boolean filter
                case 'cancelled':
                  setCancelledFilter(filters.value || '');
                  setCancelledOperator(filters.operator || 'is');
                  break;
                // Date filters - convert ISO datetime to date only
                case 'invoice_date_formatted':
                case 'invoice_date':
                  setInvoiceDateFilter(formatDateForBackend(filters.value));
                  setInvoiceDateOperator(filters.operator || 'is');
                  break;
                case 'due_date':
                  setDueDateFilter(formatDateForBackend(filters.value));
                  setDueDateOperator(filters.operator || 'is');
                  break;
                // Numeric filters
                case 'gross_total_formatted':
                case 'gross_total':
                  setGrossTotalFilter(filters.value || '');
                  setGrossTotalOperator(filters.operator || '=');
                  break;
                case 'net_total':
                  setNetTotalFilter(filters.value || '');
                  setNetTotalOperator(filters.operator || '=');
                  break;
              }
            }
            setPage(0);
          }}
          onRowClick={(params: GridRowParams) => {
            setSelectedInvoiceId((params.row as BillingoInvoice).id);
          }}
          sx={{
            '& .MuiDataGrid-row': {
              cursor: 'pointer',
            },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Totals Summary */}
      {data && data.results.length > 0 && (
        <Paper sx={{ p: 2, mt: 2, bgcolor: 'primary.50' }}>
          <Stack direction="row" spacing={4} justifyContent="flex-end" alignItems="center">
            <Typography variant="subtitle1" fontWeight="bold">
              Összesen ({totals.count} számla):
            </Typography>
            <Typography variant="subtitle1" fontWeight="bold">
              Bruttó: {totals.gross.toLocaleString('hu-HU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} HUF
            </Typography>
            <Typography variant="subtitle1" fontWeight="bold">
              Nettó: {totals.net.toLocaleString('hu-HU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} HUF
            </Typography>
          </Stack>
        </Paper>
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

              {/* Related Documents */}
              {invoiceDetails.related_documents && invoiceDetails.related_documents.length > 0 && (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Kapcsolódó dokumentumok ({invoiceDetails.related_documents.length})
                    </Typography>
                    <Alert severity="warning" sx={{ mb: 1 }}>
                      Ez a számla kapcsolódik más dokumentumokhoz (pl. helyesbítés, sztornó)
                    </Alert>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Számlaszám</TableCell>
                            <TableCell>Billingo ID</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {invoiceDetails.related_documents.map((relDoc) => (
                            <TableRow key={relDoc.id}>
                              <TableCell>
                                <Typography variant="body2" fontWeight="bold">
                                  {relDoc.related_invoice_number}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2" color="text.secondary">
                                  {relDoc.related_invoice_id}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                </>
              )}

              <Divider />

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
