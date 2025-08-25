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
} from '@mui/material';
import {
  Visibility as ViewIcon,
  KeyboardArrowUp as ArrowUpIcon,
  KeyboardArrowDown as ArrowDownIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
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
  payment_status: string;
  is_paid: boolean;
  
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
}

const NAVInvoiceTable: React.FC<NAVInvoiceTableProps> = ({
  invoices,
  isLoading,
  onView,
  onSort,
  sortField,
  sortDirection,
  showStornoColumn = false,
}) => {

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
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: align === 'right' ? 'flex-end' : 'flex-start' }}>
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
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Számlaszám</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Irány</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Partner</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Kiállítás</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Teljesítés</TableCell>
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Fizetési határidő</TableCell>
              <TableCell align="right" sx={{ backgroundColor: 'background.paper' }}>Nettó</TableCell>
              <TableCell align="right" sx={{ backgroundColor: 'background.paper' }}>ÁFA</TableCell>
              <TableCell align="right" sx={{ backgroundColor: 'background.paper' }}>Bruttó</TableCell>
              {showStornoColumn && <TableCell sx={{ backgroundColor: 'background.paper' }}>Sztornó</TableCell>}
              <TableCell sx={{ backgroundColor: 'background.paper' }}>Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.from({ length: 10 }).map((_, index) => (
              <TableRow key={index}>
                {Array.from({ length: showStornoColumn ? 11 : 10 }).map((_, cellIndex) => (
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
            {renderHeaderCell('nav_invoice_number', 'Számlaszám')}
            {renderHeaderCell('invoice_direction', 'Irány')}
            <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'background.paper' }}>Partner</TableCell>
            {renderHeaderCell('issue_date', 'Kiállítás')}
            {renderHeaderCell('fulfillment_date', 'Teljesítés')}
            {renderHeaderCell('payment_due_date', 'Fizetési határidő')}
            {renderHeaderCell('invoice_net_amount', 'Nettó', 'right')}
            {renderHeaderCell('invoice_vat_amount', 'ÁFA', 'right')}
            {renderHeaderCell('invoice_gross_amount', 'Bruttó', 'right')}
            {showStornoColumn && <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'background.paper' }}>Sztornó</TableCell>}
            <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'background.paper' }}>Műveletek</TableCell>
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
              <TableCell>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {invoice.nav_invoice_number}
                </Typography>
              </TableCell>
              <TableCell>
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
              <TableCell align="right">
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {invoice.invoice_net_amount_formatted}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  {invoice.invoice_vat_amount_formatted}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2" sx={{ fontWeight: 'medium', fontSize: '0.8rem' }}>
                  {invoice.invoice_gross_amount_formatted}
                </Typography>
              </TableCell>
              {showStornoColumn && (
                <TableCell>
                  {getStornoIndicator(invoice.invoice_operation)}
                </TableCell>
              )}
              <TableCell onClick={(e) => e.stopPropagation()}>
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