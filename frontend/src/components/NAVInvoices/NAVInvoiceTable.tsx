import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Typography,
  Skeleton,
  Box,
  Tooltip,
  Checkbox,
} from '@mui/material';
import PaymentStatusBadge from '../PaymentStatusBadge';
import {
  Visibility as ViewIcon,
  KeyboardArrowUp as ArrowUpIcon,
  KeyboardArrowDown as ArrowDownIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  SwapHoriz as TransferIcon,
  CreditCard as CardIcon,
  Receipt as ReceiptIcon,
  AttachMoney as CashIcon,
  CheckCircle as PaidIcon,
  Schedule as UnpaidIcon,
  Warning as OverdueIcon,
  Assignment as PreparedIcon,
} from '@mui/icons-material';

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
  invoice_category?: string | null;
  
  // System
  sync_status: string;
  created_at: string;
}

interface NAVInvoiceTableProps {
  invoices: Invoice[];
  isLoading: boolean;
  onView: (invoice: Invoice) => void;
  onSort: (field: string, direction: 'asc' | 'desc') => void;
  sortField?: string;
  sortDirection?: 'asc' | 'desc';
  showStornoColumn?: boolean; // Show Sztornó column when STORNO invoices are visible
  // Selection functionality
  selectedInvoices?: number[];
  onSelectInvoice?: (invoiceId: number, selected: boolean) => void;
  onSelectAll?: (selected: boolean) => void;
}

// Consistent number formatting function - ensures spaces as thousand separators
const formatNumber = (value: number | string | null): string => {
  if (value === null || value === undefined || value === '') return '-';

  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '-';

  // Use Hungarian locale which uses spaces as thousand separators
  return num.toLocaleString('hu-HU', { maximumFractionDigits: 2 }).replace(/,00$/, '');
};

const NAVInvoiceTable: React.FC<NAVInvoiceTableProps> = ({
  invoices,
  isLoading,
  onView,
  onSort,
  sortField,
  sortDirection,
  showStornoColumn = false,
  selectedInvoices = [],
  onSelectInvoice,
  onSelectAll,
}) => {
  // Helper functions for checkbox selection
  const safeSelectedInvoices = selectedInvoices || [];
  const selectedCount = safeSelectedInvoices.length;
  const totalCount = invoices.length;
  
  const isAllSelected = Boolean(totalCount > 0 && selectedCount === totalCount);
  const isIndeterminate = Boolean(selectedCount > 0 && selectedCount < totalCount);

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (onSelectAll) {
      onSelectAll(event.target.checked);
    }
  };

  const handleSelectInvoice = (invoiceId: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
    event.stopPropagation(); // Prevent row click when checking checkbox
    if (onSelectInvoice) {
      onSelectInvoice(invoiceId, event.target.checked);
    }
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      // Toggle direction
      const newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(field, newDirection);
    } else {
      // New field, start with descending for dates and amounts, ascending for text
      const newDirection = ['issue_date', 'invoice_gross_amount'].includes(field) ? 'desc' : 'asc';
      onSort(field, newDirection);
    }
  };

  const formatAmount = (amount: number, currency: string) => {
    if (currency === 'HUF') {
      return `${amount.toLocaleString('hu-HU', { maximumFractionDigits: 0 })} Ft`;
    }
    return `${amount.toLocaleString('hu-HU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
  };

  const getDirectionChip = (direction: string, display: string) => (
    <Chip
      label={display}
      color={direction === 'OUTBOUND' ? 'primary' : 'secondary'}
      size="small"
      icon={direction === 'OUTBOUND' ? <TrendingUpIcon /> : <TrendingDownIcon />}
      variant="outlined"
    />
  );

  const getSortIcon = (field: string) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ArrowUpIcon fontSize="small" /> : <ArrowDownIcon fontSize="small" />;
  };

  const renderHeaderCell = (field: string, label: string, align: 'left' | 'right' | 'center' = 'left') => (
    <TableCell
      align={align}
      sx={{ 
        cursor: 'pointer',
        userSelect: 'none',
        '&:hover': { backgroundColor: 'action.hover' },
        fontWeight: 'bold',
        backgroundColor: sortField === field ? 'action.selected' : 'background.paper'
      }}
      onClick={() => handleSort(field)}
    >
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: align === 'right' ? 'flex-end' : align === 'center' ? 'center' : 'flex-start' 
      }}>
        {label}
        {getSortIcon(field)}
      </Box>
    </TableCell>
  );

  const getStornoIndicator = (operation: string | null) => {
    // Show "Igen" for STORNO invoices, empty for others
    if (operation === 'STORNO') {
      return (
        <Chip
          label="Igen"
          color="error"
          size="small"
          variant="filled"
        />
      );
    }
    return null;
  };

  const getPaymentMethodIcon = (paymentMethod: string | null, invoiceCategory?: string | null) => {
    // Show Receipt icon for SIMPLIFIED invoices when payment_method is null
    if (!paymentMethod && invoiceCategory?.toUpperCase() === 'SIMPLIFIED') {
      return (
        <Tooltip title="Egyszerűsített">
          <ReceiptIcon color="success" fontSize="small" />
        </Tooltip>
      );
    }
    
    // Show Card icon for NORMAL invoices when payment_method is null
    if (!paymentMethod && invoiceCategory?.toUpperCase() === 'NORMAL') {
      return (
        <Tooltip title="Bankkártya (feltételezett)">
          <CardIcon color="secondary" fontSize="small" />
        </Tooltip>
      );
    }
    
    if (!paymentMethod) return '-';
    
    const method = paymentMethod.toUpperCase().trim();
    
    switch (method) {
      case 'TRANSFER':
        return (
          <Tooltip title="Átutalás">
            <TransferIcon color="primary" fontSize="small" />
          </Tooltip>
        );
      case 'CARD':
        return (
          <Tooltip title="Kártya">
            <CardIcon color="secondary" fontSize="small" />
          </Tooltip>
        );
      case 'CASH':
        return (
          <Tooltip title="Készpénz">
            <CashIcon color="warning" fontSize="small" />
          </Tooltip>
        );
      default:
        console.log('Unknown payment method:', paymentMethod); // Debug log
        return (
          <Tooltip title={paymentMethod}>
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
              {paymentMethod}
            </Typography>
          </Tooltip>
        );
    }
  };



  if (isLoading) {
    return (
      <TableContainer sx={{ flexGrow: 1 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow sx={{
              '& .MuiTableCell-head': {
                backgroundColor: 'background.paper',
                borderBottom: '2px solid',
                borderBottomColor: 'divider',
              }
            }}>
              <TableCell sx={{ backgroundColor: 'background.paper', width: '60px' }}>
                <Checkbox disabled />
              </TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Számlaszám</TableCell>
              <TableCell align="center" sx={{ backgroundColor: 'background.paper' }}>Irány</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Partner</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Kiállítás</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Teljesítés</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Fizetési határidő</TableCell>
              <TableCell align="center" sx={{ backgroundColor: 'background.paper' }}>Fizetési mód</TableCell>
              <TableCell align="center" sx={{ backgroundColor: 'background.paper' }}>Fizetési állapot</TableCell>
              <TableCell align="right" sx={{ backgroundColor: 'background.paper' }}>Nettó</TableCell>
              <TableCell align="right" sx={{ backgroundColor: 'background.paper' }}>ÁFA</TableCell>
              <TableCell align="right" sx={{ backgroundColor: 'background.paper' }}>Bruttó</TableCell>
              {showStornoColumn && <TableCell sx={{ backgroundColor: 'background.paper' }}>Sztornó</TableCell>}
              <TableCell align="center" sx={{ backgroundColor: 'background.paper' }}>Részletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.from({ length: 10 }).map((_, index) => (
              <TableRow key={index}>
                {Array.from({ length: showStornoColumn ? 14 : 13 }).map((_, cellIndex) => (
                  <TableCell key={cellIndex}><Skeleton /></TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  if (invoices.length === 0) {
    return (
      <Box 
        sx={{ 
          flexGrow: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 8
        }}
      >
        <Typography variant="h6" color="text.secondary">
          Nincsenek számlák a megadott szűrők alapján
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer sx={{ flexGrow: 1 }}>
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow sx={{
            '& .MuiTableCell-head': {
              backgroundColor: 'background.paper',
              borderBottom: '2px solid',
              borderBottomColor: 'divider',
            }
          }}>
            <TableCell sx={{ width: '60px', backgroundColor: 'background.paper' }}>
              {onSelectAll && (
                <Checkbox
                  checked={isAllSelected}
                  indeterminate={isIndeterminate}
                  onChange={handleSelectAll}
                />
              )}
            </TableCell>
            {renderHeaderCell('nav_invoice_number', 'Számlaszám')}
            {renderHeaderCell('invoice_direction', 'Irány', 'center')}
            <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'background.paper' }}>Partner</TableCell>
            {renderHeaderCell('issue_date', 'Kiállítás')}
            {renderHeaderCell('fulfillment_date', 'Teljesítés')}
            {renderHeaderCell('payment_due_date', 'Fizetési határidő')}
            {renderHeaderCell('payment_status', 'Fizetési állapot', 'center')}
            {renderHeaderCell('payment_method', 'Fizetési mód', 'center')}
            {renderHeaderCell('invoice_net_amount', 'Nettó', 'right')}
            {renderHeaderCell('invoice_vat_amount', 'ÁFA', 'right')}
            {renderHeaderCell('invoice_gross_amount', 'Bruttó', 'right')}
            {showStornoColumn && <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'background.paper' }}>Sztornó</TableCell>}
            <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: 'background.paper' }}>Részletek</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {invoices.map((invoice) => (
            <TableRow 
              key={invoice.id} 
              hover
              sx={{ 
                '&:hover': { 
                  backgroundColor: 'action.hover',
                  cursor: 'pointer' 
                }
              }}
              onClick={() => onView(invoice)}
            >
              <TableCell sx={{ width: '60px' }} onClick={(e) => e.stopPropagation()}>
                {onSelectInvoice && (
                  <Checkbox
                    checked={Boolean(safeSelectedInvoices.includes(invoice.id))}
                    onChange={handleSelectInvoice(invoice.id)}
                  />
                )}
              </TableCell>
              <TableCell>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {invoice.nav_invoice_number}
                </Typography>
              </TableCell>
              <TableCell align="center">
                {getDirectionChip(invoice.invoice_direction, invoice.invoice_direction_display)}
              </TableCell>
              <TableCell>
                <Box>
                  <Typography variant="body2" sx={{ 
                    maxWidth: 150, 
                    overflow: 'hidden', 
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontSize: '0.8rem'
                  }}>
                    {invoice.partner_name}
                  </Typography>
                  {invoice.partner_tax_number && (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {invoice.partner_tax_number}
                    </Typography>
                  )}
                </Box>
              </TableCell>
              <TableCell>
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {invoice.issue_date_formatted}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {invoice.fulfillment_date_formatted || '-'}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {invoice.payment_due_date_formatted || '-'}
                </Typography>
              </TableCell>
              <TableCell align="center">
                <PaymentStatusBadge 
                  paymentStatus={invoice.payment_status}
                  paymentStatusDate={invoice.payment_status_date_formatted || undefined}
                  size="small"
                  compact={true}
                  isOverdue={invoice.is_overdue}
                />
              </TableCell>
              <TableCell align="center">
                {getPaymentMethodIcon(invoice.payment_method, invoice.invoice_category)}
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {formatNumber(invoice.invoice_net_amount)} Ft
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {formatNumber(invoice.invoice_vat_amount)} Ft
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2" sx={{ fontWeight: 'medium', fontSize: '0.8rem' }}>
                  {formatNumber(invoice.invoice_gross_amount)} Ft
                </Typography>
              </TableCell>
              {showStornoColumn && (
                <TableCell>
                  {getStornoIndicator(invoice.invoice_operation)}
                </TableCell>
              )}
              <TableCell align="center" onClick={(e) => e.stopPropagation()}>
                <Tooltip title="Számla részletei és tételek">
                  <IconButton
                    onClick={() => onView(invoice)}
                    size="small"
                    color="primary"
                  >
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default NAVInvoiceTable;