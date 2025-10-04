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
import { useNAVInvoices } from '../../hooks/api';
import { NAVInvoice } from '../../types/api';

interface InvoiceSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (invoiceIds: number[]) => Promise<void>;
}

const InvoiceSelectionModal: React.FC<InvoiceSelectionModalProps> = ({
  isOpen,
  onClose,
  onSelect,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  const { data: invoicesData, isLoading } = useNAVInvoices({
    search: searchTerm,
    direction: 'INBOUND',
    page_size: 50,
    hide_storno_invoices: true,
  });

  const availableInvoices = invoicesData?.results || [];

  const handleClose = () => {
    setSearchTerm('');
    setSelectedInvoices([]);
    onClose();
  };

  const handleToggleInvoice = (invoiceId: number) => {
    setSelectedInvoices(prev =>
      prev.includes(invoiceId)
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    );
  };

  const handleGenerateTransfers = async () => {
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
          <Typography variant="h6">
            NAV számla kiválasztása
          </Typography>
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
            {isLoading ? (
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
                        borderColor: selectedInvoices.includes(invoice.id) ? 'primary.main' : 'divider',
                        borderRadius: 1,
                        mb: 1,
                        bgcolor: selectedInvoices.includes(invoice.id) ? 'primary.50' : 'transparent',
                        '&:hover': {
                          bgcolor: selectedInvoices.includes(invoice.id) ? 'primary.100' : 'action.hover'
                        }
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
                                  bgcolor: invoice.payment_status.class === 'overdue' ? 'error.light' :
                                           invoice.payment_status.class === 'paid' ? 'success.light' :
                                           invoice.payment_status.class === 'prepared' ? 'info.light' : 'warning.light',
                                  color: invoice.payment_status.class === 'overdue' ? 'error.dark' :
                                         invoice.payment_status.class === 'paid' ? 'success.dark' :
                                         invoice.payment_status.class === 'prepared' ? 'info.dark' : 'warning.dark',
                                }}
                              />
                            </Stack>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {invoice.partner_name}
                            </Typography>
                            <Typography variant="caption" color="primary" fontWeight={600} component="span">
                              {invoice.invoice_gross_amount_formatted}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" component="span">
                              {' • Esedékes: '}{invoice.payment_due_date_formatted || 'N/A'}
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
