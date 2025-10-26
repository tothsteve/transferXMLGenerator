/**
 * @fileoverview Available invoices list for manual transaction matching
 * @module components/BankStatements/AvailableInvoicesList
 */

import { ReactElement } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
  Alert,
  Divider,
} from '@mui/material';
import { NAVInvoice } from '../../types/api';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';
import LoadingSpinner from '../UI/LoadingSpinner';

/**
 * Props for AvailableInvoicesList component.
 *
 * @interface AvailableInvoicesListProps
 */
interface AvailableInvoicesListProps {
  /** List of available invoices */
  invoices: NAVInvoice[];

  /** Whether invoices are loading */
  isLoading: boolean;

  /** Callback when an invoice is selected for matching */
  onSelectInvoice: (invoiceId: number) => void;
}

/**
 * Format currency with Hungarian locale.
 *
 * @param amount - Amount as decimal string
 * @returns Formatted currency
 */
const formatCurrency = (amount: string): string => {
  const num = parseFloat(amount);
  return new Intl.NumberFormat('hu-HU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
};

/**
 * Available invoices list component.
 *
 * Displays a scrollable list of available invoices that can be
 * matched to the current transaction. Each invoice shows the
 * invoice number, supplier, amount, and due date.
 *
 * @component
 * @example
 * ```tsx
 * <AvailableInvoicesList
 *   invoices={invoices}
 *   isLoading={loading}
 *   onSelectInvoice={(id) => handleMatch(id)}
 * />
 * ```
 */
const AvailableInvoicesList: React.FC<AvailableInvoicesListProps> = ({
  invoices,
  isLoading,
  onSelectInvoice,
}): ReactElement => {
  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (invoices.length === 0) {
    return (
      <Alert severity="info">
        Nincs elérhető számla
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Elérhető számlák (Fizetetlen)
      </Typography>
      <List sx={{ maxHeight: 300, overflow: 'auto', border: 1, borderColor: 'divider' }}>
        {invoices.map((invoice) => (
          <ListItem key={invoice.id} disablePadding>
            <ListItemButton onClick={() => onSelectInvoice(invoice.id)}>
              <ListItemText
                primary={
                  <Typography variant="body2" fontWeight="medium">
                    {invoice.nav_invoice_number}
                  </Typography>
                }
                secondary={
                  <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Szállító: {invoice.supplier_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Összeg: {formatCurrency(String(invoice.invoice_gross_amount))} HUF •
                      Határidő:{' '}
                      {invoice.payment_due_date !== null
                        ? format(parseISO(invoice.payment_due_date), 'yyyy. MM. dd.', {
                            locale: hu,
                          })
                        : 'N/A'}
                    </Typography>
                  </Stack>
                }
              />
            </ListItemButton>
            <Divider />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default AvailableInvoicesList;
