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
} from '@mui/material';
import { Grid } from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useToast } from '../../hooks/useToast';
import { apiClient as api } from '../../services/api';
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
  payment_method: string | null;
  original_invoice_number: string | null;
  payment_status: string;
  is_paid: boolean;
  
  // System
  sync_status: string;
  created_at: string;
  
  // Additional fields for detail view
  supplier_name?: string;
  customer_name?: string;
  supplier_tax_number?: string;
  customer_tax_number?: string;
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
  const [directionFilter, setDirectionFilter] = useState<string | undefined>(undefined);
  const [currencyFilter, setCurrencyFilter] = useState<string | undefined>(undefined);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [sortField, setSortField] = useState<string>('issue_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  
  // Modal states
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoiceDetailsOpen, setInvoiceDetailsOpen] = useState(false);
  const [invoiceLineItems, setInvoiceLineItems] = useState<InvoiceLineItem[]>([]);
  
  const { success: showSuccess, error: showError } = useToast();

  const queryParams = {
    search: searchTerm || undefined,
    direction: directionFilter,
    currency: currencyFilter,
    page: currentPage,
    ordering: `${sortDirection === 'desc' ? '-' : ''}${sortField}`,
  };

  // Load invoices
  const loadInvoices = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      // Add pagination
      params.append('page', currentPage.toString());
      params.append('page_size', '20');
      
      // Add filters
      if (searchTerm) params.append('search', searchTerm);
      if (directionFilter) params.append('direction', directionFilter);
      if (currencyFilter) params.append('currency', currencyFilter);
      
      // Add sorting
      const ordering = `${sortDirection === 'desc' ? '-' : ''}${sortField}`;
      params.append('ordering', ordering);

      const response = await api.get(`/api/nav/invoices/?${params}`);
      setInvoices(response.data.results || []);
      setTotalCount(response.data.count || 0);
    } catch (error) {
      console.error('Error loading invoices:', error);
      showError('Hiba a számlák betöltése során');
    } finally {
      setLoading(false);
    }
  };

  // Load invoice line items for detail view
  const loadInvoiceLineItems = async (invoiceId: number) => {
    try {
      const response = await api.get(`/api/nav/invoices/${invoiceId}/line_items/`);
      setInvoiceLineItems(response.data);
    } catch (error) {
      console.error('Error loading invoice line items:', error);
      showError('Hiba a számla tételek betöltése során');
    }
  };

  useEffect(() => {
    loadInvoices();
  }, [searchTerm, directionFilter, currencyFilter, currentPage, sortField, sortDirection]);

  const handleViewInvoice = async (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setInvoiceDetailsOpen(true);
    await loadInvoiceLineItems(invoice.id);
  };

  const handleCloseInvoiceDetails = () => {
    setInvoiceDetailsOpen(false);
    setSelectedInvoice(null);
    setInvoiceLineItems([]);
  };

  const handleSort = (field: string, direction: 'asc' | 'desc') => {
    setSortField(field);
    setSortDirection(direction);
    setCurrentPage(1); // Reset to first page when sorting
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDirectionFilter(undefined);
    setCurrencyFilter(undefined);
    setCurrentPage(1);
    setSortField('issue_date');
    setSortDirection('desc');
  };

  const refetch = () => {
    loadInvoices();
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
                    checked={directionFilter === 'INBOUND'}
                    onChange={(e) => setDirectionFilter(e.target.checked ? 'INBOUND' : undefined)}
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
                    checked={directionFilter === 'OUTBOUND'}
                    onChange={(e) => setDirectionFilter(e.target.checked ? 'OUTBOUND' : undefined)}
                    size="small"
                  />
                }
                label="Csak kimenő számlák"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={currencyFilter === 'HUF'}
                    onChange={(e) => setCurrencyFilter(e.target.checked ? 'HUF' : undefined)}
                    size="small"
                  />
                }
                label="Csak HUF számlák"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { clearFilters(); handleFilterClose(); }}>
              Szűrők törlése
            </MenuItem>
          </Menu>
        </Stack>

        {/* Active filters display - Same pattern as BeneficiaryManager */}
        {(searchTerm || directionFilter || currencyFilter) && (
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
            {currencyFilter && (
              <Chip
                label={`Pénznem: ${currencyFilter}`}
                size="small"
                color="warning"
                variant="outlined"
              />
            )}
          </Stack>
        )}
      </Box>

      {/* Results count - Same pattern as BeneficiaryManager */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
        {totalCount} számla találat
      </Typography>

      {/* Table - Same pattern as BeneficiaryManager */}
      <Paper elevation={1} sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <NAVInvoiceTable
          invoices={invoices}
          isLoading={loading}
          onView={handleViewInvoice}
          onSort={handleSort}
          sortField={sortField}
          sortDirection={sortDirection}
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
          Számla részletei: {selectedInvoice?.nav_invoice_number}
        </DialogTitle>
        <DialogContent>
          {selectedInvoice && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                  Alapadatok
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Irány:</strong> {selectedInvoice.invoice_direction_display}
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Partner:</strong> {selectedInvoice.partner_name}
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Kiállítás dátuma:</strong> {selectedInvoice.issue_date_formatted}
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Pénznem:</strong> {selectedInvoice.currency_code}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                  Összegek
                </Typography>
                {selectedInvoice.invoice_net_amount && (
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Nettó összeg:</strong> {formatAmount(selectedInvoice.invoice_net_amount, selectedInvoice.currency_code)}
                  </Typography>
                )}
                {selectedInvoice.invoice_vat_amount && (
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>ÁFA összeg:</strong> {formatAmount(selectedInvoice.invoice_vat_amount, selectedInvoice.currency_code)}
                  </Typography>
                )}
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Bruttó összeg:</strong> {formatAmount(selectedInvoice.invoice_gross_amount, selectedInvoice.currency_code)}
                </Typography>
              </Grid>

              <Grid item xs={12}>
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
              </Grid>
            </Grid>
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