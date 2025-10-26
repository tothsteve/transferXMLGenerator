import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Pagination,
  MenuItem,
  InputAdornment,
  Select,
  SelectChangeEvent,
  FormControl,
  InputLabel,
  IconButton,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { hu } from 'date-fns/locale';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  SwapHoriz,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useToastContext } from '../../context/ToastContext';
import { useBulkMarkUnpaid, useBulkMarkPrepared, useBulkMarkPaid } from '../../hooks/api';
import NAVInvoiceTable from './NAVInvoiceTable';
import InvoiceFilterMenu from './InvoiceFilterMenu';
import InvoiceBulkActionBar from './InvoiceBulkActionBar';
import InvoiceTotalsSection from './InvoiceTotalsSection';
import InvoiceDetailsModal from './InvoiceDetailsModal';
import { useInvoiceFilters } from '../../hooks/useInvoiceFilters';
import { useInvoiceData, Invoice } from '../../hooks/useInvoiceData';
import { useInvoiceDetails } from '../../hooks/useInvoiceDetails';
import { useInvoiceSelection } from '../../hooks/useInvoiceSelection';

interface InvoiceTotals {
  inbound: {
    net: number;
    vat: number;
    gross: number;
    count: number;
  };
  outbound: {
    net: number;
    vat: number;
    gross: number;
    count: number;
  };
  total: {
    net: number;
    vat: number;
    gross: number;
    count: number;
  };
}

const NAVInvoices: React.FC = () => {
  // Toast and navigation
  const { success: showSuccess, error: showError, addToast } = useToastContext();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Track if invoice modal was opened via URL parameter for back navigation
  const openedViaUrlParam = useRef<boolean>(false);

  // Bulk payment status update mutations
  const bulkMarkUnpaidMutation = useBulkMarkUnpaid();
  const bulkMarkPreparedMutation = useBulkMarkPrepared();
  const bulkMarkPaidMutation = useBulkMarkPaid();

  // Adapter functions to match hook interface signatures
  const adaptedAddToast = (type: string, title: string, message: string, duration?: number): void => {
    addToast(type as 'success' | 'error' | 'warning' | 'info', title, message, duration);
  };

  const adaptedBulkMarkUnpaidMutation = {
    mutateAsync: async (invoiceIds: number[]): Promise<void> => {
      await bulkMarkUnpaidMutation.mutateAsync(invoiceIds);
    },
    isPending: bulkMarkUnpaidMutation.isPending,
  };

  const adaptedBulkMarkPreparedMutation = {
    mutateAsync: async (invoiceIds: number[]): Promise<void> => {
      await bulkMarkPreparedMutation.mutateAsync(invoiceIds);
    },
    isPending: bulkMarkPreparedMutation.isPending,
  };

  const adaptedBulkMarkPaidMutation = {
    mutateAsync: async (data: unknown): Promise<void> => {
      await bulkMarkPaidMutation.mutateAsync(data as { invoice_ids?: number[]; payment_date?: string; invoices?: { invoice_id: number; payment_date: string }[] });
    },
    isPending: bulkMarkPaidMutation.isPending,
  };

  // Local state (pagination, UI)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortField, setSortField] = useState<string>('issue_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [totalsCollapsed, setTotalsCollapsed] = useState(false);

  // Custom Hook 1: Filters
  const {
    searchTerm,
    setSearchTerm,
    directionFilter,
    setDirectionFilter,
    paymentStatusFilter,
    setPaymentStatusFilter,
    hideStornoInvoices,
    setHideStornoInvoices,
    inboundTransferFilter,
    setInboundTransferFilter,
    dateFilterType,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    filterAnchorEl,
    handleDateFilterTypeChange,
    applyDatePreset,
    navigateMonth,
    clearFilters,
    buildInvoiceQueryParams,
    handleFilterClick,
    handleFilterClose,
    filterMenuOpen,
  } = useInvoiceFilters();

  // Temporary selection state for useInvoiceData (cleared on filter changes)
  const [_tempSelectedInvoices, setTempSelectedInvoices] = useState<number[]>([]);

  // Build query params for data loading
  const queryParams = buildInvoiceQueryParams(currentPage, pageSize, sortField, sortDirection);

  // Custom Hook 2: Data Loading
  const { invoices, loading, totalCount, refetch } = useInvoiceData({
    queryParams,
    showError,
    setSelectedInvoices: setTempSelectedInvoices,
  });

  // Custom Hook 3: Details Modal
  const {
    selectedInvoice,
    invoiceDetailsOpen,
    invoiceLineItems,
    invoiceDetailsLoading,
    isSupplierTrusted,
    checkingTrustedStatus,
    addingTrustedPartner,
    handleViewInvoice,
    handleViewInvoiceById,
    handleCloseInvoiceDetails,
    handleAddTrustedPartner,
  } = useInvoiceDetails({
    refetch,
    showSuccess,
    showError,
    bulkMarkPaidMutation: adaptedBulkMarkPaidMutation,
  });

  // Custom Hook 4: Selection & Bulk Operations
  const {
    selectedInvoices,
    paymentDate,
    setPaymentDate,
    usePaymentDueDate,
    setUsePaymentDueDate,
    handleSelectInvoice,
    handleSelectAll,
    handleBulkMarkUnpaid,
    handleBulkMarkPrepared,
    handleBulkMarkPaid,
    handleGenerateTransfers,
  } = useInvoiceSelection({
    invoices,
    refetch,
    showSuccess,
    showError,
    addToast: adaptedAddToast,
    navigate,
    bulkMarkUnpaidMutation: adaptedBulkMarkUnpaidMutation,
    bulkMarkPreparedMutation: adaptedBulkMarkPreparedMutation,
    bulkMarkPaidMutation: adaptedBulkMarkPaidMutation,
  });

  // Handle deep linking: Check for invoiceId parameter in URL
  useEffect(() => {
    const invoiceIdParam = searchParams.get('invoiceId');
    if (invoiceIdParam) {
      const invoiceId = parseInt(invoiceIdParam, 10);
      if (!isNaN(invoiceId)) {
        // Mark that we opened via URL parameter for back navigation
        openedViaUrlParam.current = true;
        // Open invoice modal automatically
        void handleViewInvoiceById(invoiceId);
      }
    }
    // Only run on mount when URL parameter changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get('invoiceId')]);

  // Custom close handler that navigates back if opened via URL parameter
  const handleCloseInvoiceDetailsWithNavigation = (): void => {
    // Close the modal first
    handleCloseInvoiceDetails();

    // If modal was opened via URL parameter, navigate back to previous page
    if (openedViaUrlParam.current) {
      openedViaUrlParam.current = false; // Reset the flag
      navigate(-1); // Go back to the previous page (bank transactions)
    }
  };

  // Local formatting and calculation functions
  const handleSort = (field: string, direction: 'asc' | 'desc'): void => {
    setSortField(field);
    setSortDirection(direction);
    setCurrentPage(1);
  };

  // Calculate totals for selected or filtered invoices
  const calculateTotals = (): InvoiceTotals | null => {
    let invoicesToCalculate: Invoice[] = [];

    // If there are selected invoices, calculate totals for selected only
    if (selectedInvoices.length > 0) {
      invoicesToCalculate = invoices.filter((invoice) => selectedInvoices.includes(invoice.id));
    } else {
      // If no selection but there are filters active, calculate totals for all visible invoices
      const hasActiveFilters =
        (searchTerm !== null && searchTerm !== undefined && searchTerm !== '') ||
        (directionFilter !== null && directionFilter !== undefined && directionFilter !== '') ||
        (paymentStatusFilter !== null && paymentStatusFilter !== undefined && paymentStatusFilter !== '') ||
        !hideStornoInvoices ||
        inboundTransferFilter ||
        (dateFilterType !== null && dateFilterType !== undefined && dateFilterType !== '');
      if (hasActiveFilters) {
        invoicesToCalculate = invoices;
      }
    }

    // Initialize totals structure
    const totals = {
      inbound: { net: 0, vat: 0, gross: 0, count: 0 },
      outbound: { net: 0, vat: 0, gross: 0, count: 0 },
      total: { net: 0, vat: 0, gross: 0, count: 0 },
    };

    // Calculate sums by direction
    invoicesToCalculate.forEach((invoice) => {
      const net = Number(invoice.invoice_net_amount) || 0;
      const vat = Number(invoice.invoice_vat_amount) || 0;
      const gross = Number(invoice.invoice_gross_amount) || 0;

      if (invoice.invoice_direction === 'INBOUND') {
        totals.inbound.net += net;
        totals.inbound.vat += vat;
        totals.inbound.gross += gross;
        totals.inbound.count += 1;
      } else if (invoice.invoice_direction === 'OUTBOUND') {
        totals.outbound.net += net;
        totals.outbound.vat += vat;
        totals.outbound.gross += gross;
        totals.outbound.count += 1;
      }

      // Add to total regardless of direction
      totals.total.net += net;
      totals.total.vat += vat;
      totals.total.gross += gross;
      totals.total.count += 1;
    });

    return totals.total.count > 0 ? totals : null;
  };

  const totals = calculateTotals();

  // Consistent number formatting function - ensures spaces as thousand separators
  const formatNumber = (value: number | string | null): string => {
    if (value === null || value === undefined || value === '') return '-';

    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '-';

    // Use Hungarian locale which uses spaces as thousand separators
    return num.toLocaleString('hu-HU', { maximumFractionDigits: 2 }).replace(/,00$/, '');
  };

  // Format amount helper function
  const formatAmount = (amount: number, currency: string): string => {
    if (currency === 'HUF') {
      return `${formatNumber(amount)} Ft`;
    }
    return `${formatNumber(amount)} ${currency}`;
  };

  const handlePageSizeChange = (event: SelectChangeEvent<number>): void => {
    setPageSize(Number(event.target.value));
    setCurrentPage(1);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <Box
      sx={{
        p: { xs: 0.5, sm: 0.5, md: 1 },
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header - Same pattern as BeneficiaryManager */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 1, mb: 1 }}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={2}
        >
          <Box>
            <Typography variant="h5" component="h1" fontWeight="bold" sx={{ mb: 0.5 }}>
              NAV Számlák
            </Typography>
            <Typography variant="body2" color="text.secondary">
              NAV-ból szinkronizált számlák megtekintése és keresése
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon fontSize="small" />}
              onClick={refetch}
              disabled={loading}
              size="small"
              sx={{ fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
            >
              Frissítés
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Search and Filters - Same pattern as BeneficiaryManager */}
      <Box sx={{ mb: 1 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 1 }}>
          {/* Search */}
          <TextField
            fullWidth
            placeholder="Keresés számlaszám, név vagy adószám alapján..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
            size="small"
            sx={{ '& .MuiInputBase-input': { fontSize: '0.8rem' } }}
          />

          {/* Filters */}
          <Button
            variant="outlined"
            startIcon={<FilterIcon fontSize="small" />}
            onClick={handleFilterClick}
            size="small"
            sx={{ minWidth: 120, fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
          >
            Szűrők
          </Button>
          <InvoiceFilterMenu
            anchorEl={filterAnchorEl}
            open={filterMenuOpen}
            onClose={handleFilterClose}
            directionFilter={directionFilter}
            setDirectionFilter={setDirectionFilter}
            paymentStatusFilter={paymentStatusFilter}
            setPaymentStatusFilter={setPaymentStatusFilter}
            hideStornoInvoices={hideStornoInvoices}
            setHideStornoInvoices={setHideStornoInvoices}
            clearFilters={clearFilters}
          />
        </Stack>

        {/* Quick Filter Buttons */}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mt: 0.5 }}>
          <Button
            variant={inboundTransferFilter ? 'contained' : 'outlined'}
            color="primary"
            size="small"
            onClick={() => {
              setInboundTransferFilter(!inboundTransferFilter);
              // Clear other direction filters when this is active
              if (!inboundTransferFilter) {
                setDirectionFilter('');
              }
            }}
            startIcon={<SwapHoriz fontSize="small" />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
          >
            Bejövő átutalások
          </Button>

          {/* Date Interval Filter */}
          <Stack direction="row" spacing={0.5} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel sx={{ fontSize: '0.8rem' }}>Dátum típus</InputLabel>
              <Select
                value={dateFilterType}
                label="Dátum típus"
                onChange={(e) =>
                  handleDateFilterTypeChange(
                    e.target.value as 'issue_date' | 'fulfillment_date' | 'payment_due_date' | ''
                  )
                }
                sx={{ fontSize: '0.8rem' }}
              >
                <MenuItem value="" sx={{ fontSize: '0.8rem' }}>
                  Nincs
                </MenuItem>
                <MenuItem value="issue_date" sx={{ fontSize: '0.8rem' }}>
                  Kiállítás
                </MenuItem>
                <MenuItem value="fulfillment_date" sx={{ fontSize: '0.8rem' }}>
                  Teljesítés
                </MenuItem>
                <MenuItem value="payment_due_date" sx={{ fontSize: '0.8rem' }}>
                  Fizetési határidő
                </MenuItem>
              </Select>
            </FormControl>

            {dateFilterType && (
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={hu}>
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <TextField
                    label="Dátum-tól"
                    type="date"
                    size="small"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{
                      minWidth: 120,
                      '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                      '& .MuiInputBase-input': { fontSize: '0.8rem' },
                    }}
                  />
                  <TextField
                    label="Dátum-ig"
                    type="date"
                    size="small"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{
                      minWidth: 120,
                      '& .MuiInputLabel-root': { fontSize: '0.8rem' },
                      '& .MuiInputBase-input': { fontSize: '0.8rem' },
                    }}
                  />

                  {/* Month Navigation Stepper */}
                  <Stack direction="row" spacing={0.25} alignItems="center">
                    <IconButton
                      size="small"
                      onClick={() => navigateMonth('previous')}
                      sx={{
                        border: '1px solid',
                        borderColor: 'primary.main',
                        borderRadius: 1,
                        p: 0.25,
                        '&:hover': { bgcolor: 'primary.50' },
                        '& .MuiSvgIcon-root': { fontSize: 16 },
                      }}
                    >
                      <ChevronLeftIcon />
                    </IconButton>

                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => applyDatePreset('current')}
                      sx={{
                        whiteSpace: 'nowrap',
                        fontSize: '0.7rem',
                        minWidth: '80px',
                        py: 0.25,
                        px: 0.75,
                        minHeight: '28px',
                      }}
                    >
                      Aktuális hónap
                    </Button>

                    <IconButton
                      size="small"
                      onClick={() => navigateMonth('next')}
                      sx={{
                        border: '1px solid',
                        borderColor: 'primary.main',
                        borderRadius: 1,
                        p: 0.25,
                        '&:hover': { bgcolor: 'primary.50' },
                        '& .MuiSvgIcon-root': { fontSize: 16 },
                      }}
                    >
                      <ChevronRightIcon />
                    </IconButton>
                  </Stack>
                </Stack>
              </LocalizationProvider>
            )}
          </Stack>
        </Stack>

        {/* Active filters display - Same pattern as BeneficiaryManager */}
        {(searchTerm ||
          directionFilter ||
          paymentStatusFilter ||
          !hideStornoInvoices ||
          inboundTransferFilter ||
          dateFilterType) && (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Aktív szűrők:
            </Typography>
            {searchTerm && (
              <Chip
                label={`Keresés: ${searchTerm}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
            {directionFilter && (
              <Chip
                label={directionFilter === 'INBOUND' ? 'Bejövő' : 'Kimenő'}
                size="small"
                color="success"
                variant="outlined"
              />
            )}
            {paymentStatusFilter && (
              <Chip
                label={
                  paymentStatusFilter === 'UNPAID'
                    ? 'Fizetésre vár'
                    : paymentStatusFilter === 'PREPARED'
                      ? 'Előkészítve'
                      : 'Kifizetve'
                }
                size="small"
                color="info"
                variant="outlined"
              />
            )}
            {inboundTransferFilter && (
              <Chip label="Bejövő átutalások" size="small" color="primary" variant="outlined" />
            )}
            {!hideStornoInvoices && (
              <Chip
                label="Sztornózott számlák láthatóak"
                size="small"
                color="error"
                variant="outlined"
              />
            )}
            {dateFilterType && (dateFrom || dateTo) && (
              <Chip
                label={`${
                  dateFilterType === 'issue_date'
                    ? 'Kiállítás'
                    : dateFilterType === 'fulfillment_date'
                      ? 'Teljesítés'
                      : 'Fizetési határidő'
                }: ${
                  dateFrom && dateTo
                    ? `${dateFrom} - ${dateTo}`
                    : dateFrom
                      ? `${dateFrom}-tól`
                      : `${dateTo}-ig`
                }`}
                size="small"
                color="secondary"
                variant="outlined"
              />
            )}
            <Button
              variant="outlined"
              size="small"
              startIcon={<ClearIcon fontSize="small" />}
              onClick={clearFilters}
              sx={{ ml: 0.5, fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
            >
              Összes szűrő törlése
            </Button>
          </Stack>
        )}
      </Box>

      {/* Results count - Same pattern as BeneficiaryManager */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
        <Typography variant="body2" color="text.secondary">
          {totalCount} számla találat
        </Typography>
        {selectedInvoices.length > 0 && (
          <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'medium' }}>
            {selectedInvoices.length} kijelölve
          </Typography>
        )}
      </Stack>

      {/* Totals Summary Card */}
      {totals && (
        <InvoiceTotalsSection
          totals={totals}
          selectedCount={selectedInvoices.length}
          collapsed={totalsCollapsed}
          onToggleCollapse={() => setTotalsCollapsed(!totalsCollapsed)}
          formatAmount={formatAmount}
        />
      )}

      {/* Action buttons for selected invoices */}
      {selectedInvoices.length > 0 && (
        <InvoiceBulkActionBar
          selectedCount={selectedInvoices.length}
          onGenerateTransfers={handleGenerateTransfers}
          onBulkMarkUnpaid={handleBulkMarkUnpaid}
          onBulkMarkPrepared={handleBulkMarkPrepared}
          onBulkMarkPaid={handleBulkMarkPaid}
          usePaymentDueDate={usePaymentDueDate}
          setUsePaymentDueDate={setUsePaymentDueDate}
          paymentDate={paymentDate}
          setPaymentDate={setPaymentDate}
          isUnpaidPending={bulkMarkUnpaidMutation.isPending}
          isPreparedPending={bulkMarkPreparedMutation.isPending}
          isPaidPending={bulkMarkPaidMutation.isPending}
        />
      )}

      {/* Table - Same pattern as BeneficiaryManager */}
      <Paper
        elevation={1}
        sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
      >
        <NAVInvoiceTable
          invoices={invoices}
          isLoading={loading}
          onView={handleViewInvoice}
          onSort={handleSort}
          sortField={sortField}
          sortDirection={sortDirection}
          showStornoColumn={!hideStornoInvoices}
          selectedInvoices={selectedInvoices}
          onSelectInvoice={handleSelectInvoice}
          onSelectAll={handleSelectAll}
        />
      </Paper>

      {/* Pagination with Page Size Selector */}
      {totalPages > 1 && (
        <Box
          sx={{
            mt: 1,
            p: 1,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Stack direction="row" spacing={2} alignItems="center">
            <Typography variant="body2" color="text.secondary">
              Oldal {currentPage} / {totalPages}
            </Typography>
            <FormControl size="small" sx={{ minWidth: '80px' }}>
              <InputLabel id="page-size-select-label">Méret</InputLabel>
              <Select
                labelId="page-size-select-label"
                value={pageSize}
                label="Méret"
                onChange={handlePageSizeChange}
                size="small"
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={20}>20</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
                <MenuItem value={200}>200</MenuItem>
                <MenuItem value={500}>500</MenuItem>
              </Select>
            </FormControl>
            <Typography variant="body2" color="text.secondary">
              elemek oldalanként
            </Typography>
          </Stack>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(_event, page) => setCurrentPage(page)}
            color="primary"
            size="small"
          />
        </Box>
      )}

      {/* Invoice Details Dialog */}
      <InvoiceDetailsModal
        open={invoiceDetailsOpen}
        onClose={handleCloseInvoiceDetailsWithNavigation}
        invoice={selectedInvoice}
        lineItems={invoiceLineItems}
        loading={invoiceDetailsLoading}
        isSupplierTrusted={isSupplierTrusted}
        checkingTrustedStatus={checkingTrustedStatus}
        addingTrustedPartner={addingTrustedPartner}
        onAddTrustedPartner={handleAddTrustedPartner}
        formatNumber={formatNumber}
      />
    </Box>
  );
};

export default NAVInvoices;
