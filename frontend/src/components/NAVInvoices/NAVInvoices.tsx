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
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  SwapHoriz,
  Add as AddIcon,
} from '@mui/icons-material';
import { useToastContext } from '../../context/ToastContext';
import { navInvoicesApi } from '../../services/api';
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
  payment_status: string;
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

const NAVInvoices: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [directionFilter, setDirectionFilter] = useState<string>('');
  const [hideStornoInvoices, setHideStornoInvoices] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [sortField, setSortField] = useState<string>('issue_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [inboundTransferFilter, setInboundTransferFilter] = useState(false);
  
  // Selection states
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);
  
  // Modal states
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoiceDetailsOpen, setInvoiceDetailsOpen] = useState(false);
  const [invoiceLineItems, setInvoiceLineItems] = useState<InvoiceLineItem[]>([]);
  const [invoiceDetailsLoading, setInvoiceDetailsLoading] = useState(false);
  
  const { success: showSuccess, error: showError } = useToastContext();
  const navigate = useNavigate();

  // Load invoices
  const loadInvoices = async () => {
    try {
      setLoading(true);
      
      const params = {
        page: currentPage,
        page_size: 20,
        search: searchTerm || undefined,
        direction: inboundTransferFilter ? 'INBOUND' : (directionFilter || undefined),
        payment_method: inboundTransferFilter ? 'TRANSFER' : undefined,
        ordering: `${sortDirection === 'desc' ? '-' : ''}${sortField}`,
        hide_storno_invoices: hideStornoInvoices,
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

  // Load invoice details with line items
  const loadInvoiceDetails = async (invoiceId: number) => {
    try {
      setInvoiceDetailsLoading(true);
      const response = await navInvoicesApi.getById(invoiceId);
      console.log('Invoice detail response:', response.data); // Debug log
      setSelectedInvoice(response.data);
      setInvoiceLineItems(response.data.line_items || []);
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
  }, [searchTerm, directionFilter, currentPage, sortField, sortDirection, hideStornoInvoices, inboundTransferFilter]);

  const handleViewInvoice = async (invoice: Invoice) => {
    setInvoiceDetailsOpen(true);
    await loadInvoiceDetails(invoice.id);
  };

  const handleCloseInvoiceDetails = () => {
    setInvoiceDetailsOpen(false);
    setSelectedInvoice(null);
    setInvoiceLineItems([]);
    setInvoiceDetailsLoading(false);
  };

  const handleSort = (field: string, direction: 'asc' | 'desc') => {
    setSortField(field);
    setSortDirection(direction);
    setCurrentPage(1); // Reset to first page when sorting
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDirectionFilter('');
    setInboundTransferFilter(false);
    setHideStornoInvoices(true); // Reset to default (hide STORNO invoices)
    setCurrentPage(1);
    setSortField('issue_date');
    setSortDirection('desc');
  };

  const refetch = () => {
    loadInvoices();
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

  // Generate transfers from selected invoices
  const handleGenerateTransfers = () => {
    const selectedInvoiceObjects = invoices.filter(invoice => selectedInvoices.includes(invoice.id));
    
    if (selectedInvoiceObjects.length === 0) {
      showError('Kérjük, válasszon ki legalább egy számlát');
      return;
    }

    // Filter out invoices without required data and collect missing data info
    const validInvoices = [];
    const invalidInvoices = [];
    
    for (const invoice of selectedInvoiceObjects) {
      const hasAccountNumber = invoice.supplier_bank_account_number && invoice.supplier_bank_account_number.trim() !== '';
      const hasAmount = invoice.invoice_gross_amount && invoice.invoice_gross_amount > 0;
      const hasPartnerName = invoice.partner_name && invoice.partner_name.trim() !== '';
      
      if (hasAccountNumber && hasAmount && hasPartnerName) {
        validInvoices.push(invoice);
      } else {
        const missingFields = [];
        if (!hasAccountNumber) missingFields.push('bankszámlaszám');
        if (!hasAmount) missingFields.push('összeg');
        if (!hasPartnerName) missingFields.push('partnernév');
        
        invalidInvoices.push({
          invoice,
          missingFields
        });
      }
    }

    if (validInvoices.length === 0) {
      // Show detailed error about why all invoices were invalid
      const errorDetails = invalidInvoices.map(item => 
        `${item.invoice.nav_invoice_number}: hiányzik ${item.missingFields.join(', ')}`
      ).slice(0, 3); // Show max 3 examples
      
      const errorMessage = `A kiválasztott számlák nem tartalmaznak elegendő adatot az átutalás generálásához:\n${errorDetails.join('\n')}${invalidInvoices.length > 3 ? `\n...és további ${invalidInvoices.length - 3} számla` : ''}`;
      showError(errorMessage);
      return;
    }

    // Create transfer data structure compatible with TransferWorkflow
    const transfersData = validInvoices.map((invoice, index) => ({
      beneficiary_id: null, // Will need to be set manually or matched
      beneficiary_name: invoice.partner_name,
      account_number: invoice.supplier_bank_account_number!,
      amount: Math.floor(invoice.invoice_gross_amount).toString(), // Convert to int as requested
      currency: invoice.currency_code === 'HUF' ? 'HUF' : invoice.currency_code,
      execution_date: invoice.payment_due_date || new Date().toISOString().split('T')[0], // Use payment due date or today
      remittance_info: invoice.nav_invoice_number,
      order: index + 1,
      fromNAVInvoice: true // Flag to indicate this came from NAV invoice
    }));

    // Navigate to transfers with pre-populated data
    navigate('/transfers', { 
      state: { 
        preloadedTransfers: transfersData,
        source: 'nav_invoices'
      } 
    });

    // Show success message with details about skipped invoices
    const successMessage = validInvoices.length === selectedInvoiceObjects.length 
      ? `${validInvoices.length} átutalás előkészítve`
      : `${validInvoices.length} átutalás előkészítve (${invalidInvoices.length} számlát kihagytunk hiányos adatok miatt)`;
    
    showSuccess(successMessage);
  };

  const totalPages = Math.ceil(totalCount / 20);

  // Filter menu state
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const filterMenuOpen = Boolean(filterAnchorEl);

  const handleFilterClick = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterClose = () => {
    setFilterAnchorEl(null);
  };

  const formatAmount = (amount: number, currency: string) => {
    if (currency === 'HUF') {
      return `${amount.toLocaleString('hu-HU', { maximumFractionDigits: 0 })} Ft`;
    }
    return `${amount.toLocaleString('hu-HU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
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
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mt: 1 }}>
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
        </Stack>

        {/* Active filters display - Same pattern as BeneficiaryManager */}
        {(searchTerm || directionFilter || !hideStornoInvoices || inboundTransferFilter) && (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
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

      {/* Action button for selected invoices */}
      {selectedInvoices.length > 0 && (
        <Box sx={{ mb: 1 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleGenerateTransfers}
            sx={{ fontWeight: 'medium' }}
          >
            Eseti utalás generálás ({selectedInvoices.length})
          </Button>
        </Box>
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

      {/* Pagination - Same pattern as BeneficiaryManager */}
      {totalPages > 1 && (
        <Box sx={{ mt: 1, p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Oldal {currentPage} / {totalPages}
          </Typography>
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
          Számla részletei: {selectedInvoice?.nav_invoice_number || 'Betöltés...'}
        </DialogTitle>
        <DialogContent>
          {invoiceDetailsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedInvoice && (
            <Box>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ mb: 3 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Alapadatok
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Irány:</strong> {selectedInvoice.invoice_direction_display}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Kategória:</strong> {selectedInvoice.invoice_category || 'N/A'}
                  </Typography>
                  {selectedInvoice.invoice_operation === 'STORNO' && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Művelet:</strong> <Chip label="Stornó" color="error" size="small" variant="filled" />
                    </Typography>
                  )}
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Pénznem:</strong> {selectedInvoice.currency_code}
                  </Typography>
                  {selectedInvoice.original_invoice_number && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Eredeti szám:</strong> {selectedInvoice.original_invoice_number}
                    </Typography>
                  )}
                </Box>
                
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Partnerek
                  </Typography>
                  {selectedInvoice.supplier_name && (
                    <>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>Eladó:</strong> {selectedInvoice.supplier_name}
                      </Typography>
                      {selectedInvoice.supplier_tax_number && (
                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                          <strong>Eladó adószám:</strong> {selectedInvoice.supplier_tax_number}
                        </Typography>
                      )}
                    </>
                  )}
                  {selectedInvoice.customer_name && (
                    <>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>Vevő:</strong> {selectedInvoice.customer_name}
                      </Typography>
                      {selectedInvoice.customer_tax_number && (
                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                          <strong>Vevő adószám:</strong> {selectedInvoice.customer_tax_number}
                        </Typography>
                      )}
                    </>
                  )}
                </Box>
                
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Összegek
                  </Typography>
                  {selectedInvoice.invoice_net_amount && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Nettó:</strong> {selectedInvoice.invoice_net_amount_formatted}
                    </Typography>
                  )}
                  {selectedInvoice.invoice_vat_amount && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>ÁFA:</strong> {selectedInvoice.invoice_vat_amount_formatted}
                    </Typography>
                  )}
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Bruttó:</strong> {selectedInvoice.invoice_gross_amount_formatted}
                  </Typography>
                </Box>
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ mb: 3 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Dátumok
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Kiállítás:</strong> {selectedInvoice.issue_date_formatted}
                  </Typography>
                  {selectedInvoice.fulfillment_date_formatted && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Teljesítés:</strong> {selectedInvoice.fulfillment_date_formatted}
                    </Typography>
                  )}
                  {selectedInvoice.payment_due_date_formatted && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Fizetési határidő:</strong> {selectedInvoice.payment_due_date_formatted}
                    </Typography>
                  )}
                </Box>

                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Fizetés
                  </Typography>
                  {selectedInvoice.payment_date_formatted && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Fizetés dátuma:</strong> {selectedInvoice.payment_date_formatted}
                    </Typography>
                  )}
                  {selectedInvoice.payment_method && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Fizetési mód:</strong> {selectedInvoice.payment_method}
                    </Typography>
                  )}
                </Box>

                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    NAV adatok
                  </Typography>
                  {selectedInvoice.nav_source && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Forrás:</strong> {selectedInvoice.nav_source}
                    </Typography>
                  )}
                  {selectedInvoice.completion_date && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      <strong>Befejezés:</strong> {selectedInvoice.completion_date}
                    </Typography>
                  )}
                </Box>
              </Stack>

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
                              {item.unit_price ? item.unit_price.toLocaleString('hu-HU') : '-'}
                            </TableCell>
                            <TableCell align="right">
                              {item.line_net_amount.toLocaleString('hu-HU')}
                            </TableCell>
                            <TableCell align="right">
                              {item.vat_rate ? `${item.vat_rate}%` : '-'}
                            </TableCell>
                            <TableCell align="right">
                              {item.line_vat_amount.toLocaleString('hu-HU')}
                            </TableCell>
                            <TableCell align="right">
                              {item.line_gross_amount.toLocaleString('hu-HU')}
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