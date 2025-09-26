import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Pagination,
  Menu,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Divider,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Select,
  FormControl,
  InputLabel,
  Collapse,
  IconButton,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { startOfMonth, endOfMonth, subMonths, format } from 'date-fns';
import { hu } from 'date-fns/locale';
import { useNavigate } from 'react-router-dom';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  SwapHoriz,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  HourglassEmpty as UnpaidIcon,
  Schedule as PreparedIcon,
  CheckCircle as PaidIcon,
  Clear as ClearIcon,
  AddCircle as AddTrustedIcon,
  Verified as VerifiedIcon,
  TrendingDown as TrendingDownIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useToastContext } from '../../context/ToastContext';
import { navInvoicesApi, trustedPartnersApi, bankAccountsApi } from '../../services/api';
import { useBulkMarkUnpaid, useBulkMarkPrepared, useBulkMarkPaid } from '../../hooks/api';
import NAVInvoiceTable from './NAVInvoiceTable';

interface Invoice {
  id: number;
  nav_invoice_number: string;
  invoice_direction: 'INBOUND' | 'OUTBOUND';
  invoice_direction_display: string;
  partner_name: string;
  partner_tax_number: string;
  
  // Dates
  issue_date: string;
  issue_date_formatted: string;
  fulfillment_date: string | null;
  fulfillment_date_formatted: string | null;
  payment_due_date: string | null;
  payment_due_date_formatted: string | null;
  payment_date: string | null;
  payment_date_formatted: string | null;
  completion_date?: string | null;
  last_modified_date?: string | null;
  
  // Financial
  currency_code: string;
  invoice_net_amount: number;
  invoice_net_amount_formatted: string;
  invoice_vat_amount: number;
  invoice_vat_amount_formatted: string;
  invoice_gross_amount: number;
  invoice_gross_amount_formatted: string;
  
  // Business
  invoice_operation: string | null;
  invoice_category?: string | null;
  invoice_appearance?: string | null;
  payment_method: string | null;
  original_invoice_number: string | null;
  payment_status: {
    status: string;
    label: string;
    icon: string;
    class: string;
  };
  payment_status_date: string | null;
  payment_status_date_formatted: string | null;
  auto_marked_paid: boolean;
  is_overdue: boolean;
  is_paid: boolean;
  
  // System
  sync_status: string;
  created_at: string;
  
  // NAV metadata (available in detail view)
  nav_source?: string | null;
  original_request_version?: string | null;
  
  // Partners (available in detail view)
  supplier_name?: string;
  customer_name?: string;
  supplier_tax_number?: string;
  customer_tax_number?: string;
  supplier_bank_account_number?: string;
  customer_bank_account_number?: string;
  
  // Line items (available in detail view)
  line_items?: InvoiceLineItem[];
}

interface InvoiceLineItem {
  id: number;
  line_number: number;
  line_description: string;
  quantity: number | null;
  unit_of_measure: string;
  unit_price: number | null;
  line_net_amount: number;
  vat_rate: number | null;
  line_vat_amount: number;
  line_gross_amount: number;
  product_code_category: string;
  product_code_value: string;
}

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
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [directionFilter, setDirectionFilter] = useState<string>('');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>('');
  const [hideStornoInvoices, setHideStornoInvoices] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [sortField, setSortField] = useState<string>('issue_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [inboundTransferFilter, setInboundTransferFilter] = useState(false);
  
  // Date interval filters
  const [dateFilterType, setDateFilterType] = useState<'issue_date' | 'fulfillment_date' | 'payment_due_date' | ''>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  // Helper functions for date range presets using date-fns
  const getMonthRange = (date: Date) => {
    return {
      from: format(startOfMonth(date), 'yyyy-MM-dd'),
      to: format(endOfMonth(date), 'yyyy-MM-dd')
    };
  };

  const getCurrentMonthRange = () => getMonthRange(new Date());
  
  const getPreviousMonthRange = () => getMonthRange(subMonths(new Date(), 1));

  const getNextMonthRange = () => getMonthRange(new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1));

  // Get current base date from dateFrom field or fallback to current date
  const getCurrentBaseDate = () => {
    if (dateFrom) {
      return new Date(dateFrom + 'T00:00:00');
    }
    return new Date();
  };

  // Apply date range preset
  const applyDatePreset = (preset: 'current' | 'previous' | 'next') => {
    let range;
    if (preset === 'current') {
      range = getCurrentMonthRange();
    } else if (preset === 'previous') {
      range = getPreviousMonthRange();
    } else {
      range = getNextMonthRange();
    }
    setDateFrom(range.from);
    setDateTo(range.to);
  };

  // Navigate to previous/next month based on current selected date
  const navigateMonth = (direction: 'previous' | 'next') => {
    const baseDate = getCurrentBaseDate();
    const targetDate = direction === 'previous' 
      ? subMonths(baseDate, 1)
      : new Date(baseDate.getFullYear(), baseDate.getMonth() + 1, 1);
    
    const range = getMonthRange(targetDate);
    setDateFrom(range.from);
    setDateTo(range.to);
  };

  // Handle date filter type change with automatic date range setting
  const handleDateFilterTypeChange = (value: 'issue_date' | 'fulfillment_date' | 'payment_due_date' | '') => {
    setDateFilterType(value);
    
    if (value !== '') {
      // Set default date range to previous month
      const range = getPreviousMonthRange();
      setDateFrom(range.from);
      setDateTo(range.to);
    } else {
      // Clear dates when no date type is selected
      setDateFrom('');
      setDateTo('');
    }
  };
  
  // Selection states
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);
  
  // Totals collapse state
  const [totalsCollapsed, setTotalsCollapsed] = useState(false);
  
  // Payment date state for bulk update (format: YYYY-MM-DD)
  const [paymentDate, setPaymentDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [usePaymentDueDate, setUsePaymentDueDate] = useState<boolean>(true);
  
  // Modal states
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoiceDetailsOpen, setInvoiceDetailsOpen] = useState(false);
  const [invoiceLineItems, setInvoiceLineItems] = useState<InvoiceLineItem[]>([]);
  const [invoiceDetailsLoading, setInvoiceDetailsLoading] = useState(false);

  // Trusted partner states
  const [isSupplierTrusted, setIsSupplierTrusted] = useState<boolean>(false);
  const [checkingTrustedStatus, setCheckingTrustedStatus] = useState<boolean>(false);
  const [addingTrustedPartner, setAddingTrustedPartner] = useState<boolean>(false);
  
  const { success: showSuccess, error: showError, addToast } = useToastContext();
  const navigate = useNavigate();
  
  // Bulk payment status update hooks
  const bulkMarkUnpaidMutation = useBulkMarkUnpaid();
  const bulkMarkPreparedMutation = useBulkMarkPrepared();
  const bulkMarkPaidMutation = useBulkMarkPaid();

  // Load invoices
  const loadInvoices = async () => {
    try {
      setLoading(true);
      
      const params = {
        page: currentPage,
        page_size: pageSize,
        search: searchTerm || undefined,
        direction: inboundTransferFilter ? 'INBOUND' : (directionFilter || undefined),
        payment_method: inboundTransferFilter ? 'TRANSFER' : undefined,
        payment_status: paymentStatusFilter || undefined,
        ordering: `${sortDirection === 'desc' ? '-' : ''}${sortField}`,
        hide_storno_invoices: hideStornoInvoices,
        // Date interval filters
        ...(dateFilterType === 'issue_date' && dateFrom && { issue_date_from: dateFrom }),
        ...(dateFilterType === 'issue_date' && dateTo && { issue_date_to: dateTo }),
        ...(dateFilterType === 'fulfillment_date' && dateFrom && { fulfillment_date_from: dateFrom }),
        ...(dateFilterType === 'fulfillment_date' && dateTo && { fulfillment_date_to: dateTo }),
        ...(dateFilterType === 'payment_due_date' && dateFrom && { payment_due_date_from: dateFrom }),
        ...(dateFilterType === 'payment_due_date' && dateTo && { payment_due_date_to: dateTo }),
      };

      const response = await navInvoicesApi.getAll(params);
      console.log('API Response:', response.data); // Debug log
      
      // Handle both paginated and non-paginated responses
      if (Array.isArray(response.data)) {
        // Non-paginated response (direct array)
        setInvoices(response.data);
        setTotalCount(response.data.length);
      } else if (response.data.results) {
        // Paginated response with results array
        setInvoices(response.data.results);
        setTotalCount(response.data.count || 0);
      } else {
        // Fallback
        setInvoices([]);
        setTotalCount(0);
      }
    } catch (error) {
      console.error('Error loading invoices:', error);
      showError('Hiba a számlák betöltése során');
    } finally {
      setLoading(false);
    }
  };

  // Check if supplier is already a trusted partner
  const checkSupplierTrustedStatus = async (supplierTaxNumber: string) => {
    if (!supplierTaxNumber) {
      setIsSupplierTrusted(false);
      return;
    }

    try {
      setCheckingTrustedStatus(true);
      const response = await trustedPartnersApi.getAll({
        search: supplierTaxNumber,
        is_active: true
      });

      // Check if any trusted partner matches this tax number
      const isTrusted = response.data?.results?.some(partner =>
        partner.tax_number === supplierTaxNumber
      ) || false;

      setIsSupplierTrusted(isTrusted);
    } catch (error) {
      console.error('Error checking trusted partner status:', error);
      setIsSupplierTrusted(false);
    } finally {
      setCheckingTrustedStatus(false);
    }
  };

  // Load invoice details with line items
  const loadInvoiceDetails = async (invoiceId: number) => {
    try {
      setInvoiceDetailsLoading(true);
      const response = await navInvoicesApi.getById(invoiceId);
      console.log('Invoice detail response:', response.data); // Debug log
      setSelectedInvoice(response.data);
      setInvoiceLineItems(response.data.line_items || []);

      // Check trusted partner status for supplier
      if (response.data.supplier_tax_number) {
        await checkSupplierTrustedStatus(response.data.supplier_tax_number);
      } else {
        setIsSupplierTrusted(false);
      }
    } catch (error) {
      console.error('Error loading invoice details:', error);
      showError('Hiba a számla részletek betöltése során');
    } finally {
      setInvoiceDetailsLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
    // Clear selections when filters or page change
    setSelectedInvoices([]);
  }, [searchTerm, directionFilter, paymentStatusFilter, currentPage, pageSize, sortField, sortDirection, hideStornoInvoices, inboundTransferFilter, dateFilterType, dateFrom, dateTo]);

  const handleViewInvoice = async (invoice: Invoice) => {
    setInvoiceDetailsOpen(true);
    await loadInvoiceDetails(invoice.id);
  };

  // Track if we need to refresh the invoice list when closing the detail dialog
  const [shouldRefreshOnClose, setShouldRefreshOnClose] = useState<boolean>(false);

  const handleCloseInvoiceDetails = () => {
    setInvoiceDetailsOpen(false);
    setSelectedInvoice(null);
    setInvoiceLineItems([]);
    setInvoiceDetailsLoading(false);
    setIsSupplierTrusted(false);
    setCheckingTrustedStatus(false);
    setAddingTrustedPartner(false);

    // Refresh the invoice list if changes were made (preserving filters)
    if (shouldRefreshOnClose) {
      loadInvoices();
      setShouldRefreshOnClose(false);
    }
  };

  // Add supplier as trusted partner
  const handleAddTrustedPartner = async () => {
    if (!selectedInvoice || !selectedInvoice.supplier_name || !selectedInvoice.supplier_tax_number) {
      showError('Hiányzó szállító adatok a partner hozzáadásához');
      return;
    }

    try {
      setAddingTrustedPartner(true);

      const trustedPartnerData = {
        partner_name: selectedInvoice.supplier_name,
        tax_number: selectedInvoice.supplier_tax_number,
        is_active: true,
        auto_pay: true
      };

      // Add trusted partner
      await trustedPartnersApi.create(trustedPartnerData);
      setIsSupplierTrusted(true);
      setShouldRefreshOnClose(true); // Mark that we need to refresh the list

      // Auto-mark invoice as PAID if it's currently UNPAID
      if (selectedInvoice.payment_status.status === 'UNPAID') {
        try {
          await bulkMarkPaidMutation.mutateAsync({
            invoice_ids: [selectedInvoice.id],
            payment_date: new Date().toISOString().split('T')[0] // Today's date
          });

          // Update the invoice in state to reflect the new payment status
          setSelectedInvoice(prev => prev ? {
            ...prev,
            payment_status: {
              status: 'PAID',
              label: 'Kifizetve',
              icon: 'CheckCircle',
              class: 'success'
            },
            payment_status_date: new Date().toISOString().split('T')[0],
            payment_status_date_formatted: new Date().toLocaleDateString('hu-HU'),
            is_paid: true
          } : null);

          showSuccess(`${selectedInvoice.supplier_name} hozzáadva a megbízható partnerekhez és a számla megjelölve kifizetettként`);
        } catch (paymentError) {
          console.error('Error marking invoice as paid:', paymentError);
          showSuccess(`${selectedInvoice.supplier_name} hozzáadva a megbízható partnerekhez (fizetési állapot frissítése sikertelen)`);
        }
      } else {
        showSuccess(`${selectedInvoice.supplier_name} hozzáadva a megbízható partnerekhez`);
      }

    } catch (error: any) {
      console.error('Error adding trusted partner:', error);
      if (error?.response?.data?.non_field_errors?.[0]) {
        showError(error.response.data.non_field_errors[0]);
      } else if (error?.response?.data?.tax_number?.[0]) {
        showError(`Adószám hiba: ${error.response.data.tax_number[0]}`);
      } else {
        showError('Hiba a megbízható partner hozzáadása során');
      }
    } finally {
      setAddingTrustedPartner(false);
    }
  };

  const handleSort = (field: string, direction: 'asc' | 'desc') => {
    setSortField(field);
    setSortDirection(direction);
    setCurrentPage(1); // Reset to first page when sorting
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDirectionFilter('');
    setPaymentStatusFilter('');
    setInboundTransferFilter(false);
    setHideStornoInvoices(true); // Reset to default (hide STORNO invoices)
    handleDateFilterTypeChange(''); // Use the handler to properly clear dates
    setCurrentPage(1);
    setSortField('issue_date');
    setSortDirection('desc');
  };

  const refetch = () => {
    loadInvoices();
  };

  // Calculate totals for selected or filtered invoices
  const calculateTotals = (): InvoiceTotals | null => {
    let invoicesToCalculate: Invoice[] = [];
    
    // If there are selected invoices, calculate totals for selected only
    if (selectedInvoices.length > 0) {
      invoicesToCalculate = invoices.filter(invoice => selectedInvoices.includes(invoice.id));
    } else {
      // If no selection but there are filters active, calculate totals for all visible invoices
      const hasActiveFilters = searchTerm || directionFilter || paymentStatusFilter || !hideStornoInvoices || inboundTransferFilter || dateFilterType;
      if (hasActiveFilters) {
        invoicesToCalculate = invoices;
      }
    }

    // Initialize totals structure
    const totals = {
      inbound: { net: 0, vat: 0, gross: 0, count: 0 },
      outbound: { net: 0, vat: 0, gross: 0, count: 0 },
      total: { net: 0, vat: 0, gross: 0, count: 0 }
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
  const formatAmount = (amount: number, currency: string) => {
    if (currency === 'HUF') {
      return `${formatNumber(amount)} Ft`;
    }
    return `${formatNumber(amount)} ${currency}`;
  };

  const handlePageSizeChange = (event: any) => {
    setPageSize(event.target.value);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  // Selection handlers
  const handleSelectInvoice = (invoiceId: number, selected: boolean) => {
    if (selected) {
      setSelectedInvoices(prev => [...prev, invoiceId]);
    } else {
      setSelectedInvoices(prev => prev.filter(id => id !== invoiceId));
    }
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedInvoices(invoices.map(invoice => invoice.id));
    } else {
      setSelectedInvoices([]);
    }
  };

  // Generate transfers from selected invoices using new API with tax number fallback
  const handleGenerateTransfers = async () => {
    if (selectedInvoices.length === 0) {
      showError('Kérjük, válasszon ki legalább egy számlát');
      return;
    }

    try {
      // Get default bank account for originator
      const defaultAccountResponse = await bankAccountsApi.getDefault();
      const originatorAccountId = defaultAccountResponse.data.id;

      if (!originatorAccountId) {
        showError('Nincs beállítva alapértelmezett bankszámla. Kérjük, állítson be egyet a beállítások menüben.');
        return;
      }

      // Call the new generate_transfers endpoint with tax number fallback
      const requestData = {
        invoice_ids: selectedInvoices,
        originator_account_id: originatorAccountId,
        execution_date: new Date().toISOString().split('T')[0], // Today as default execution date
      };

      showSuccess('Átutalások generálása folyamatban...');

      const response = await navInvoicesApi.generateTransfers(requestData);
      const { transfers, transfer_count, errors, warnings, message } = response.data;

      // Show detailed feedback about the generation process
      if (errors.length > 0) {
        const errorMessage = `Hibák:\n${errors.slice(0, 3).join('\n')}${errors.length > 3 ? `\n...és további ${errors.length - 3} hiba` : ''}`;
        showError(errorMessage);
      }

      if (warnings.length > 0) {
        const warningMessage = `Figyelmeztetések:\n${warnings.slice(0, 3).join('\n')}${warnings.length > 3 ? `\n...és további ${warnings.length - 3} figyelmeztetés` : ''}`;
        // Use addToast with longer duration (12 seconds) for detailed warning messages
        addToast('warning', 'Figyelmeztetések', warningMessage, 12000);
      }

      if (transfer_count > 0) {
        // Use addToast with longer duration (8 seconds) so the message stays visible longer
        addToast('success', `${transfer_count} átutalás sikeresen létrehozva`, '', 8000);

        // Navigate to transfers page to show the created transfers
        navigate('/transfers', {
          state: {
            source: 'nav_invoices_generated',
            transfers: transfers, // Pass the created transfers data
            message: `${transfer_count} átutalás létrehozva NAV számlákból`
          }
        });
      } else {
        showError('Nem sikerült átutalást létrehozni a kiválasztott számlákból');
      }

      // Clear selections
      setSelectedInvoices([]);

    } catch (error: any) {
      console.error('Error generating transfers:', error);
      console.log('Error details:', {
        status: error?.response?.status,
        data: error?.response?.data,
        message: error?.message
      });

      if (error?.response?.status === 401) {
        showError('Nincs jogosultság az átutalások generálásához. Kérjük jelentkezzen be újra.');
      } else if (error?.response?.status === 403) {
        showError('Nincs engedély az átutalások generálásához');
      } else if (error?.response?.data?.error) {
        showError(error.response.data.error);
      } else if (error?.response?.data?.errors) {
        const errorMessage = `Hibák:\n${error.response.data.errors.slice(0, 3).join('\n')}`;
        showError(errorMessage);
      } else if (error?.response?.data?.detail) {
        showError(`API hiba: ${error.response.data.detail}`);
      } else {
        showError(`Hiba történt az átutalások generálásakor: ${error?.message || 'Ismeretlen hiba'}`);
      }
    }
  };

  // Bulk payment status update handlers
  const handleBulkMarkUnpaid = async () => {
    if (selectedInvoices.length === 0) return;
    
    try {
      await bulkMarkUnpaidMutation.mutateAsync(selectedInvoices);
      showSuccess(`${selectedInvoices.length} számla megjelölve "Fizetésre vár" státuszként`);
      setSelectedInvoices([]);
      await loadInvoices(); // Refresh the list
    } catch (error: any) {
      showError(error?.response?.data?.error || 'Hiba történt a státusz frissítésekor');
    }
  };

  const handleBulkMarkPrepared = async () => {
    if (selectedInvoices.length === 0) return;
    
    try {
      await bulkMarkPreparedMutation.mutateAsync(selectedInvoices);
      showSuccess(`${selectedInvoices.length} számla megjelölve "Előkészítve" státuszként`);
      setSelectedInvoices([]);
      await loadInvoices(); // Refresh the list
    } catch (error: any) {
      showError(error?.response?.data?.error || 'Hiba történt a státusz frissítésekor');
    }
  };

  const handleBulkMarkPaid = async () => {
    if (selectedInvoices.length === 0) return;
    
    try {
      let requestData;
      
      if (usePaymentDueDate) {
        // Option 2: Use individual payment_due_date for each invoice
        const selectedInvoiceObjects = invoices.filter(invoice => selectedInvoices.includes(invoice.id));
        requestData = {
          invoices: selectedInvoiceObjects.map(invoice => ({
            invoice_id: invoice.id,
            payment_date: invoice.payment_due_date || new Date().toISOString().split('T')[0]
          }))
        };
      } else {
        // Option 1: Use single custom date for all invoices
        requestData = {
          invoice_ids: selectedInvoices,
          payment_date: paymentDate || undefined
        };
      }
      
      await bulkMarkPaidMutation.mutateAsync(requestData);
      showSuccess(`${selectedInvoices.length} számla megjelölve "Kifizetve" státuszként`);
      setSelectedInvoices([]);
      await loadInvoices(); // Refresh the list
    } catch (error: any) {
      showError(error?.response?.data?.error || 'Hiba történt a státusz frissítésekor');
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  // Filter menu state
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const filterMenuOpen = Boolean(filterAnchorEl);

  const handleFilterClick = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterClose = () => {
    setFilterAnchorEl(null);
  };

  return (
    <Box sx={{ p: { xs: 0.5, sm: 0.5, md: 1 }, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header - Same pattern as BeneficiaryManager */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 1, mb: 1 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={2}>
          <Box>
            <Typography variant="h5" component="h1" fontWeight="bold" sx={{ mb: 0.5 }}>
              NAV Számlák
            </Typography>
            <Typography variant="body2" color="text.secondary">
              NAV-ból szinkronizált számlák megtekintése és keresése
            </Typography>
          </Box>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={refetch}
              disabled={loading}
            >
              Frissítés
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Search and Filters - Same pattern as BeneficiaryManager */}
      <Box sx={{ mb: 1 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 1 }}>
          {/* Search */}
          <TextField
            fullWidth
            placeholder="Keresés számlaszám, név vagy adószám alapján..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            size="small"
          />

          {/* Filters */}
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={handleFilterClick}
            sx={{ minWidth: 140 }}
          >
            Szűrők
          </Button>
          <Menu
            anchorEl={filterAnchorEl}
            open={filterMenuOpen}
            onClose={handleFilterClose}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(directionFilter === 'INBOUND')}
                    onChange={(e) => setDirectionFilter(e.target.checked ? 'INBOUND' : '')}
                    size="small"
                  />
                }
                label="Csak bejövő számlák"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(directionFilter === 'OUTBOUND')}
                    onChange={(e) => setDirectionFilter(e.target.checked ? 'OUTBOUND' : '')}
                    size="small"
                  />
                }
                label="Csak kimenő számlák"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <Divider />
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(paymentStatusFilter === 'UNPAID')}
                    onChange={(e) => setPaymentStatusFilter(e.target.checked ? 'UNPAID' : '')}
                    size="small"
                  />
                }
                label="Csak fizetésre váró"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(paymentStatusFilter === 'PREPARED')}
                    onChange={(e) => setPaymentStatusFilter(e.target.checked ? 'PREPARED' : '')}
                    size="small"
                  />
                }
                label="Csak előkészített"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(paymentStatusFilter === 'PAID')}
                    onChange={(e) => setPaymentStatusFilter(e.target.checked ? 'PAID' : '')}
                    size="small"
                  />
                }
                label="Csak kifizetett"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <Divider />
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={hideStornoInvoices}
                    onChange={(e) => setHideStornoInvoices(e.target.checked)}
                    size="small"
                  />
                }
                label="Sztornózott számlák elrejtése"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { clearFilters(); handleFilterClose(); }}>
              Szűrők törlése
            </MenuItem>
          </Menu>
        </Stack>

        {/* Quick Filter Buttons */}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 1 }}>
          <Button
            variant={inboundTransferFilter ? "contained" : "outlined"}
            color="primary"
            size="small"
            onClick={() => {
              setInboundTransferFilter(!inboundTransferFilter);
              // Clear other direction filters when this is active
              if (!inboundTransferFilter) {
                setDirectionFilter('');
              }
            }}
            startIcon={<SwapHoriz />}
          >
            Bejövő átutalások
          </Button>

          {/* Date Interval Filter */}
          <Stack direction="row" spacing={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Dátum típus</InputLabel>
              <Select
                value={dateFilterType}
                label="Dátum típus"
                onChange={(e) => handleDateFilterTypeChange(e.target.value as 'issue_date' | 'fulfillment_date' | 'payment_due_date' | '')}
              >
                <MenuItem value="">Nincs</MenuItem>
                <MenuItem value="issue_date">Kiállítás</MenuItem>
                <MenuItem value="fulfillment_date">Teljesítés</MenuItem>
                <MenuItem value="payment_due_date">Fizetési határidő</MenuItem>
              </Select>
            </FormControl>
            
            {dateFilterType && (
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={hu}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <TextField
                    label="Dátum-tól"
                    type="date"
                    size="small"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{ minWidth: 140 }}
                  />
                  <TextField
                    label="Dátum-ig"
                    type="date"
                    size="small"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{ minWidth: 140 }}
                  />
                  
                  {/* Month Navigation Stepper */}
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <IconButton
                      size="small"
                      onClick={() => navigateMonth('previous')}
                      sx={{ 
                        border: '1px solid',
                        borderColor: 'primary.main',
                        borderRadius: 1,
                        '&:hover': { bgcolor: 'primary.50' }
                      }}
                    >
                      <ChevronLeftIcon fontSize="small" />
                    </IconButton>
                    
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => applyDatePreset('current')}
                      sx={{ 
                        whiteSpace: 'nowrap', 
                        fontSize: '0.75rem',
                        minWidth: '90px',
                        py: 0.5
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
                        '&:hover': { bgcolor: 'primary.50' }
                      }}
                    >
                      <ChevronRightIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                </Stack>
              </LocalizationProvider>
            )}
          </Stack>
        </Stack>

        {/* Active filters display - Same pattern as BeneficiaryManager */}
        {(searchTerm || directionFilter || paymentStatusFilter || !hideStornoInvoices || inboundTransferFilter || dateFilterType) && (
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
                label={paymentStatusFilter === 'UNPAID' ? 'Fizetésre vár' : 
                       paymentStatusFilter === 'PREPARED' ? 'Előkészítve' : 
                       'Kifizetve'}
                size="small"
                color="info"
                variant="outlined"
              />
            )}
            {inboundTransferFilter && (
              <Chip
                label="Bejövő átutalások"
                size="small"
                color="primary"
                variant="outlined"
              />
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
                  dateFilterType === 'issue_date' ? 'Kiállítás' : 
                  dateFilterType === 'fulfillment_date' ? 'Teljesítés' : 
                  'Fizetési határidő'
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
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              sx={{ ml: 1 }}
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
        <Paper 
          elevation={2} 
          sx={{ 
            p: 2, 
            mb: 1, 
            bgcolor: 'primary.50',
            border: '1px solid',
            borderColor: 'primary.200'
          }}
        >
          <Stack spacing={2}>
            {/* Header with collapse button */}
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                {selectedInvoices.length > 0 
                  ? `${selectedInvoices.length} kiválasztott számla összesen:`
                  : `${totals.total.count} szűrt számla összesen:`
                }
              </Typography>
              <IconButton
                size="small"
                onClick={() => setTotalsCollapsed(!totalsCollapsed)}
                sx={{ ml: 1 }}
              >
                {totalsCollapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
              </IconButton>
            </Stack>
            
            {/* Collapsible direction-specific totals - Compact Table Design */}
            <Collapse in={!totalsCollapsed}>
              <Box sx={{ 
                border: '1px solid', 
                borderColor: 'divider', 
                borderRadius: 1, 
                overflow: 'hidden',
                mt: 1
              }}>
                {/* Table Header */}
                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: '120px 1fr 1fr 1fr', 
                  gap: 1,
                  bgcolor: 'grey.50',
                  p: 1,
                  borderBottom: '1px solid',
                  borderBottomColor: 'divider'
                }}>
                  <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                    Irány
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center' }}>
                    Nettó
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center' }}>
                    ÁFA
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.75rem', textAlign: 'center' }}>
                    Bruttó
                  </Typography>
                </Box>
                
                {/* Outbound Row */}
                {totals.outbound.count > 0 && (
                  <Box sx={{ 
                    display: 'grid', 
                    gridTemplateColumns: '120px 1fr 1fr 1fr', 
                    gap: 1,
                    p: 1,
                    borderBottom: totals.inbound.count > 0 ? '1px solid' : 'none',
                    borderBottomColor: 'divider',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}>
                    <Typography variant="body2" color="primary.main" sx={{ fontSize: '0.75rem', fontWeight: 'medium' }}>
                      Kimenő ({totals.outbound.count})
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', textAlign: 'center', color: 'success.main', fontWeight: 'medium' }}>
                      {formatAmount(totals.outbound.net, 'HUF')}
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', textAlign: 'center', color: 'warning.main', fontWeight: 'medium' }}>
                      {formatAmount(totals.outbound.vat, 'HUF')}
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', textAlign: 'center', color: 'primary.main', fontWeight: 'bold' }}>
                      {formatAmount(totals.outbound.gross, 'HUF')}
                    </Typography>
                  </Box>
                )}
                
                {/* Inbound Row */}
                {totals.inbound.count > 0 && (
                  <Box sx={{ 
                    display: 'grid', 
                    gridTemplateColumns: '120px 1fr 1fr 1fr', 
                    gap: 1,
                    p: 1,
                    '&:hover': { bgcolor: 'action.hover' }
                  }}>
                    <Typography variant="body2" color="secondary.main" sx={{ fontSize: '0.75rem', fontWeight: 'medium' }}>
                      Bejövő ({totals.inbound.count})
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', textAlign: 'center', color: 'success.main', fontWeight: 'medium' }}>
                      {formatAmount(totals.inbound.net, 'HUF')}
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', textAlign: 'center', color: 'warning.main', fontWeight: 'medium' }}>
                      {formatAmount(totals.inbound.vat, 'HUF')}
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', textAlign: 'center', color: 'secondary.main', fontWeight: 'bold' }}>
                      {formatAmount(totals.inbound.gross, 'HUF')}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Collapse>
          </Stack>
        </Paper>
      )}

      {/* Action buttons for selected invoices */}
      {selectedInvoices.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 1, backgroundColor: 'action.hover' }}>
          <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'primary.main', fontWeight: 'medium' }}>
            Tömeges műveletek ({selectedInvoices.length} számla kiválasztva)
          </Typography>
          
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
            {/* Generate transfers button */}
            <Button
              variant="contained"
              color="primary"
              size="small"
              startIcon={<AddIcon />}
              onClick={handleGenerateTransfers}
            >
              Eseti utalás generálás
            </Button>
            
            {/* Payment status buttons */}
            <Button
              variant="outlined"
              color="warning"
              size="small"
              startIcon={<UnpaidIcon />}
              onClick={handleBulkMarkUnpaid}
              disabled={bulkMarkUnpaidMutation.isPending}
            >
              {bulkMarkUnpaidMutation.isPending ? 'Frissítés...' : 'Fizetésre vár'}
            </Button>
            
            <Button
              variant="outlined"
              color="info"
              size="small"
              startIcon={<PreparedIcon />}
              onClick={handleBulkMarkPrepared}
              disabled={bulkMarkPreparedMutation.isPending}
            >
              {bulkMarkPreparedMutation.isPending ? 'Frissítés...' : 'Előkészítve'}
            </Button>
            
            <Stack direction="column" spacing={1}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={usePaymentDueDate}
                    onChange={(e) => setUsePaymentDueDate(e.target.checked)}
                    size="small"
                  />
                }
                label="Fizetési határidőre állítás"
                sx={{ fontSize: '0.875rem' }}
              />
              
              <Stack direction="row" spacing={1} alignItems="center">
                {!usePaymentDueDate && (
                  <TextField
                    label="Fizetés dátuma"
                    type="date"
                    value={paymentDate}
                    onChange={(e) => setPaymentDate(e.target.value)}
                    size="small"
                    sx={{ minWidth: '150px' }}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                )}
                
                <Button
                  variant="outlined"
                  color="success"
                  size="small"
                  startIcon={<PaidIcon />}
                  onClick={handleBulkMarkPaid}
                  disabled={bulkMarkPaidMutation.isPending}
                >
                  {bulkMarkPaidMutation.isPending ? 'Frissítés...' : 'Kifizetve'}
                </Button>
                
                {usePaymentDueDate && (
                  <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', maxWidth: '200px' }}>
                    Minden számla saját fizetési határidejével lesz megjelölve
                  </Typography>
                )}
              </Stack>
            </Stack>
          </Stack>
        </Paper>
      )}

      {/* Table - Same pattern as BeneficiaryManager */}
      <Paper elevation={1} sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
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
        <Box sx={{ mt: 1, p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
            onChange={(event, page) => setCurrentPage(page)}
            color="primary"
            size="small"
          />
        </Box>
      )}

      {/* Invoice Details Dialog */}
      <Dialog
        open={invoiceDetailsOpen}
        onClose={handleCloseInvoiceDetails}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
            <Typography variant="h6" component="span">
              Számla részletei: {selectedInvoice?.nav_invoice_number || 'Betöltés...'}
            </Typography>
            {selectedInvoice && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                {/* Direction Badge - same style as in the list */}
                <Chip
                  label={selectedInvoice.invoice_direction_display}
                  color={selectedInvoice.invoice_direction === 'INBOUND' ? 'secondary' : 'primary'}
                  size="small"
                  variant="outlined"
                  icon={selectedInvoice.invoice_direction === 'INBOUND' ? <TrendingDownIcon /> : <TrendingUpIcon />}
                />
                {selectedInvoice.invoice_operation === 'STORNO' && (
                  <Chip label="Stornó" color="error" size="small" variant="filled" sx={{ height: 24, fontSize: '0.75rem' }} />
                )}
              </Box>
            )}
          </Box>
        </DialogTitle>
        <DialogContent>
          {invoiceDetailsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedInvoice && (
            <Box>

              {/* Compact Partners Section - Clean two-column like invoice */}
              <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                {/* Supplier Column */}
                {selectedInvoice.supplier_name && (
                  <Box sx={{ flex: 1, borderRight: selectedInvoice.customer_name ? '1px solid #e0e0e0' : 'none', pr: selectedInvoice.customer_name ? 2 : 0 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      Eladó: {selectedInvoice.supplier_name}
                    </Typography>
                    {selectedInvoice.supplier_tax_number && (
                      <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                        Magyar adószám: {selectedInvoice.supplier_tax_number}
                      </Typography>
                    )}
                    {selectedInvoice.supplier_bank_account_number && (
                      <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                        Bankszámlaszám: {selectedInvoice.supplier_bank_account_number}
                      </Typography>
                    )}

                    {/* Trusted Partner Status - Compact */}
                    <Box sx={{ mt: 1 }}>
                      {checkingTrustedStatus ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CircularProgress size={14} />
                          <Typography variant="caption" color="text.secondary">
                            Ellenőrzés...
                          </Typography>
                        </Box>
                      ) : isSupplierTrusted ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <VerifiedIcon color="success" fontSize="small" />
                          <Typography variant="caption" color="success.main" sx={{ fontWeight: 'medium' }}>
                            Megbízható partner
                          </Typography>
                        </Box>
                      ) : selectedInvoice.supplier_tax_number && (
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<AddTrustedIcon />}
                          onClick={handleAddTrustedPartner}
                          disabled={addingTrustedPartner}
                          sx={{ fontSize: '0.75rem', py: 0.5, px: 1 }}
                        >
                          {addingTrustedPartner ? 'Hozzáadás...' : 'Megbízható partner'}
                        </Button>
                      )}
                    </Box>
                  </Box>
                )}

                {/* Customer Column */}
                {selectedInvoice.customer_name && (
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      Vevő: {selectedInvoice.customer_name}
                    </Typography>
                    {selectedInvoice.customer_tax_number && (
                      <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                        Magyar adószám: {selectedInvoice.customer_tax_number}
                      </Typography>
                    )}
                    {selectedInvoice.customer_bank_account_number && (
                      <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                        Bankszámlaszám: {selectedInvoice.customer_bank_account_number}
                      </Typography>
                    )}
                  </Box>
                )}
              </Stack>

              {/* Compact Details Row - Essential dates only */}
              <Box sx={{ borderTop: '1px solid #e0e0e0', pt: 1.5, mb: 2 }}>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                    Teljesítés: {selectedInvoice.fulfillment_date_formatted || selectedInvoice.issue_date_formatted}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                    Keltezés: {selectedInvoice.issue_date_formatted}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                    Fizetési határidő: {selectedInvoice.payment_due_date_formatted || 'N/A'}
                  </Typography>
                  {selectedInvoice.original_invoice_number && (
                    <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                      Eredeti szám: {selectedInvoice.original_invoice_number}
                    </Typography>
                  )}
                </Stack>
              </Box>

              {/* Compact Summary Section */}
              <Box sx={{ backgroundColor: '#f9f9f9', p: 1.5, borderRadius: 1, mb: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Számla összesítő:
                </Typography>

                <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
                  <Stack spacing={0.5} sx={{ flex: 1 }}>
                    {selectedInvoice.invoice_net_amount && (
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Számla nettó értéke</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {formatNumber(selectedInvoice.invoice_net_amount)} Ft
                        </Typography>
                      </Stack>
                    )}
                    {selectedInvoice.invoice_vat_amount && (
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="body2">Áfa összege</Typography>
                        <Typography variant="body2">
                          {formatNumber(selectedInvoice.invoice_vat_amount)} Ft
                        </Typography>
                      </Stack>
                    )}
                    <Stack direction="row" justifyContent="space-between" sx={{ borderTop: '1px solid #ddd', pt: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Számla bruttó végösszege</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatNumber(selectedInvoice.invoice_gross_amount)} Ft
                      </Typography>
                    </Stack>
                  </Stack>
                </Stack>

              </Box>

              <Box>
                <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                  Számla tételek
                </Typography>
                {invoiceLineItems.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Sor</TableCell>
                          <TableCell>Megnevezés</TableCell>
                          <TableCell align="right">Mennyiség</TableCell>
                          <TableCell align="right">Egységár</TableCell>
                          <TableCell align="right">Nettó</TableCell>
                          <TableCell align="right">ÁFA %</TableCell>
                          <TableCell align="right">ÁFA összeg</TableCell>
                          <TableCell align="right">Bruttó</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {invoiceLineItems.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell>{item.line_number}</TableCell>
                            <TableCell>{item.line_description}</TableCell>
                            <TableCell align="right">
                              {item.quantity ? `${item.quantity} ${item.unit_of_measure}` : '-'}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(item.unit_price)}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(item.line_net_amount)}
                            </TableCell>
                            <TableCell align="right">
                              {item.vat_rate ? `${formatNumber(item.vat_rate)}%` : '-'}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(item.line_vat_amount)}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(item.line_gross_amount)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">Nincsenek részletes tételek</Alert>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseInvoiceDetails}>Bezárás</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NAVInvoices;