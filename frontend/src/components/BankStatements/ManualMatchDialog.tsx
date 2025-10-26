/**
 * @fileoverview Manual transaction-to-invoice matching dialog
 * @module components/BankStatements/ManualMatchDialog
 */

import { ReactElement, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Stack,
  TextField,
  IconButton,
  InputAdornment,
  Alert,
} from '@mui/material';
import {
  Close as CloseIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import {
  useBankTransaction,
  useNAVInvoices,
  useMatchTransactionToInvoice,
  useUnmatchTransaction,
} from '../../hooks/api';
import { useToastContext } from '../../context/ToastContext';
import LoadingSpinner from '../UI/LoadingSpinner';
import TransactionDetailPanel from './TransactionDetailPanel';
import AvailableInvoicesList from './AvailableInvoicesList';

/**
 * Props for ManualMatchDialog component.
 *
 * @interface ManualMatchDialogProps
 */
interface ManualMatchDialogProps {
  /** Whether dialog is open */
  open: boolean;

  /** Callback when dialog should close */
  onClose: () => void;

  /** Transaction ID to match */
  transactionId: number;
}

/**
 * Manual transaction matching dialog component.
 *
 * Features:
 * - Display transaction details
 * - Show suggested invoice matches
 * - Search invoices by number or supplier
 * - Match/unmatch transactions
 *
 * @component
 * @example
 * ```tsx
 * <ManualMatchDialog
 *   open={showDialog}
 *   onClose={() => setShowDialog(false)}
 *   transactionId={123}
 * />
 * ```
 */
const ManualMatchDialog: React.FC<ManualMatchDialogProps> = ({
  open,
  onClose,
  transactionId,
}): ReactElement => {
  const { success: showSuccess, error: showError } = useToastContext();
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch data
  const { data: transaction, isLoading: transactionLoading } = useBankTransaction(transactionId);
  const { data: invoicesData, isLoading: invoicesLoading } = useNAVInvoices({
    search: searchTerm,
    page_size: 50,
  });

  // Mutations
  const matchMutation = useMatchTransactionToInvoice();
  const unmatchMutation = useUnmatchTransaction();

  const invoices = invoicesData?.results ?? [];
  const isMatched = transaction !== undefined &&
    (transaction.matched_invoice !== null || transaction.matched_transfer !== null);

  /**
   * Handle match transaction to invoice.
   *
   * @param invoiceId - NAV invoice ID to match
   */
  const handleMatch = async (invoiceId: number): Promise<void> => {
    try {
      await matchMutation.mutateAsync({ transactionId, invoiceId });
      showSuccess('Sikeres párosítás', 'A tranzakció párosítva lett a számlával');
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ismeretlen hiba történt';
      showError('Párosítási hiba', message);
    }
  };

  /**
   * Handle unmatch transaction.
   */
  const handleUnmatch = async (): Promise<void> => {
    try {
      await unmatchMutation.mutateAsync(transactionId);
      showSuccess('Sikeres törlés', 'A párosítás törölve lett');
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ismeretlen hiba történt';
      showError('Törlési hiba', message);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Tranzakció párosítása</Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {transactionLoading ? (
          <LoadingSpinner />
        ) : transaction !== undefined ? (
          <Stack spacing={3}>
            {/* Transaction Details */}
            <TransactionDetailPanel transaction={transaction} />

            {/* Search */}
            <TextField
              placeholder="Keresés számlaszám vagy szállító neve alapján..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
              fullWidth
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />

            {/* Available Invoices */}
            <AvailableInvoicesList
              invoices={invoices}
              isLoading={invoicesLoading}
              onSelectInvoice={handleMatch}
            />
          </Stack>
        ) : (
          <Alert severity="error">Nem sikerült betölteni a tranzakció adatait</Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        {isMatched && (
          <Button
            variant="outlined"
            color="error"
            onClick={() => void handleUnmatch()}
            disabled={unmatchMutation.isPending}
          >
            Párosítás törlése
          </Button>
        )}
        <Button onClick={onClose} disabled={matchMutation.isPending || unmatchMutation.isPending}>
          Bezárás
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ManualMatchDialog;
