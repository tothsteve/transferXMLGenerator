import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  Stack,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  IconButton,
  InputAdornment,
  Chip,
  CircularProgress,
  Checkbox,
} from '@mui/material';
import {
  Close as CloseIcon,
  Search as SearchIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import { NAVInvoice } from '../../types/api';

/**
 * Props for the InvoiceSelectionModal component
 */
interface InvoiceSelectionModalProps {
  /** Whether the modal is currently open */
  isOpen: boolean;
  /** Callback when modal is closed */
  onClose: () => void;
  /**
   * Callback when invoices are selected for transfer generation
   * @param invoiceIds - Array of selected NAV invoice IDs
   * @returns Promise that resolves when transfers are generated
   */
  onSelect: (invoiceIds: number[]) => Promise<void>;
}

/**
 * Invoice Selection Modal Component
 *
 * Modal dialog for selecting NAV invoices to generate bank transfers.
 * Displays a searchable, filterable list of INBOUND invoices from the NAV system.
 *
 * **Features:**
 * - Search by invoice number or partner name
 * - Multi-select with checkboxes
 * - Filter to show only unpaid/pending invoices
 * - Visual payment status indicators
 * - Disabled state for already paid invoices
 * - Batch transfer generation from selected invoices
 *
 * **Business Logic:**
 * - Only shows INBOUND direction invoices (invoices to pay)
 * - Hides STORNO invoices by default
 * - Limits results to 50 invoices for performance
 * - Disables paid invoices from selection
 * - Generates one transfer per selected invoice with:
 *   - Amount from invoice gross amount
 *   - Partner info from invoice supplier
 *   - Payment due date as execution date
 *
 * @component
 */
const InvoiceSelectionModal: React.FC<InvoiceSelectionModalProps> = ({
  isOpen,
  onClose,
  onSelect,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  // Note: useNAVInvoices doesn't support enabled flag, so we need to modify it
  // For now, let's use a manual fetch approach
  const [invoices, setInvoices] = useState<NAVInvoice[]>([]);
  const [isFetching, setIsFetching] = useState(false);

  // Fetch invoices when modal opens
  React.useEffect(() => {
    if (isOpen) {
      const fetchInvoices = async (): Promise<void> => {
        setIsFetching(true);
        try {
          const { navInvoicesApi } = await import('../../services/api');
          const response = await navInvoicesApi.getAll({
            search: searchTerm,
            direction: 'INBOUND',
            page_size: 50,
            hide_storno_invoices: true,
          });
          setInvoices(response.data.results);
        } catch (error) {
          console.error('Failed to fetch NAV invoices:', error);
          setInvoices([]);
        } finally {
          setIsFetching(false);
        }
      };
      fetchInvoices();
    }
  }, [isOpen, searchTerm]);

  const availableInvoices = invoices;

  const handleClose = (): void => {
    setSearchTerm('');
    setSelectedInvoices([]);
    setInvoices([]);
    onClose();
  };

  const handleToggleInvoice = (invoiceId: number): void => {
    setSelectedInvoices((prev) =>
      prev.includes(invoiceId) ? prev.filter((id) => id !== invoiceId) : [...prev, invoiceId]
    );
  };

  const handleGenerateTransfers = async (): Promise<void> => {
    if (selectedInvoices.length === 0) return;

    setLoading(true);
    try {
      await onSelect(selectedInvoices);
      handleClose();
    } catch (error) {
      console.error('Failed to generate transfers from invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">NAV számla kiválasztása</Typography>
          <IconButton onClick={handleClose} edge="end" disabled={loading}>
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent dividers>
        <Stack spacing={2}>
          <TextField
            fullWidth
            placeholder="Keresés számla száma vagy partner alapján..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            disabled={loading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
            {isFetching ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : availableInvoices.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <ReceiptIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Nincsenek bejövő számlák
                </Typography>
              </Box>
            ) : (
              <List disablePadding>
                {availableInvoices.map((invoice) => (
                  <ListItem key={invoice.id} disablePadding>
                    <ListItemButton
                      onClick={() => handleToggleInvoice(invoice.id)}
                      disabled={loading || invoice.payment_status.status === 'PAID'}
                      sx={{
                        border: 1,
                        borderColor: selectedInvoices.includes(invoice.id)
                          ? 'primary.main'
                          : 'divider',
                        borderRadius: 1,
                        mb: 1,
                        bgcolor: selectedInvoices.includes(invoice.id)
                          ? 'primary.50'
                          : 'transparent',
                        '&:hover': {
                          bgcolor: selectedInvoices.includes(invoice.id)
                            ? 'primary.100'
                            : 'action.hover',
                        },
                      }}
                    >
                      <Checkbox
                        checked={selectedInvoices.includes(invoice.id)}
                        disabled={loading || invoice.payment_status.status === 'PAID'}
                        sx={{ mr: 1 }}
                      />
                      <ListItemText
                        primary={
                          <Box>
                            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                              <Typography variant="body2" fontWeight={500}>
                                {invoice.nav_invoice_number}
                              </Typography>
                              <Chip
                                label={invoice.payment_status.label}
                                size="small"
                                sx={{
                                  height: 20,
                                  fontSize: '0.65rem',
                                  bgcolor:
                                    invoice.payment_status.class === 'overdue'
                                      ? 'error.light'
                                      : invoice.payment_status.class === 'paid'
                                        ? 'success.light'
                                        : invoice.payment_status.class === 'prepared'
                                          ? 'info.light'
                                          : 'warning.light',
                                  color:
                                    invoice.payment_status.class === 'overdue'
                                      ? 'error.dark'
                                      : invoice.payment_status.class === 'paid'
                                        ? 'success.dark'
                                        : invoice.payment_status.class === 'prepared'
                                          ? 'info.dark'
                                          : 'warning.dark',
                                }}
                              />
                            </Stack>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {invoice.partner_name}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="primary"
                              fontWeight={600}
                              component="span"
                            >
                              {invoice.invoice_gross_amount_formatted}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" component="span">
                              {' • Esedékes: '}
                              {invoice.payment_due_date_formatted || 'N/A'}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions>
        <Box sx={{ flex: 1, pl: 2 }}>
          {selectedInvoices.length > 0 && (
            <Typography variant="body2" color="text.secondary">
              {selectedInvoices.length} számla kiválasztva
            </Typography>
          )}
        </Box>
        <Button onClick={handleClose} disabled={loading}>
          Mégse
        </Button>
        <Button
          variant="contained"
          onClick={handleGenerateTransfers}
          disabled={loading || selectedInvoices.length === 0}
        >
          {loading ? 'Generálás...' : 'Átutalás generálás'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InvoiceSelectionModal;
