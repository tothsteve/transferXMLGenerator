/**
 * @fileoverview Match action buttons for transaction match management
 * @module components/BankStatements/MatchActionButtons
 */

import { ReactElement, useState } from 'react';
import {
  Button,
  Stack,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as UnmatchIcon,
  Refresh as RematchIcon,
} from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { bankTransactionApi } from '../../services/bankTransaction.api';
import { BankTransaction } from '../../schemas/bankStatement.schemas';

/**
 * Props for MatchActionButtons component.
 *
 * @interface MatchActionButtonsProps
 */
interface MatchActionButtonsProps {
  /** Transaction with match information */
  transaction: BankTransaction;
  /** Callback after successful action (optional) */
  onSuccess?: () => void;
}

/**
 * Match action buttons component.
 *
 * Provides buttons for:
 * - Approve Match (upgrade confidence to 1.00)
 * - Unmatch (remove match)
 * - Rematch (re-run automatic matching)
 *
 * @component
 * @example
 * ```tsx
 * <MatchActionButtons transaction={transaction} onSuccess={handleRefresh} />
 * ```
 */
const MatchActionButtons: React.FC<MatchActionButtonsProps> = ({
  transaction,
  onSuccess,
}): ReactElement => {
  const queryClient = useQueryClient();
  const [unmatchDialogOpen, setUnmatchDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const confidence = parseFloat(transaction.match_confidence);
  const isMatched =
    transaction.matched_invoice !== null ||
    transaction.matched_transfer !== null ||
    transaction.matched_reimbursement !== null ||
    (transaction.is_batch_match &&
      transaction.matched_invoices_details &&
      transaction.matched_invoices_details.length > 0);

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Approve match mutation
  const approveMutation = useMutation({
    mutationFn: () => bankTransactionApi.approveMatch(transaction.id),
    onSuccess: (data) => {
      showSnackbar(
        `Párosítás jóváhagyva! (${data.previous_confidence} → ${data.new_confidence})`,
        'success'
      );
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['bankStatements'] });
      onSuccess?.();
    },
    onError: (error: any) => {
      showSnackbar(
        `Jóváhagyás sikertelen: ${error.response?.data?.error || error.message}`,
        'error'
      );
    },
  });

  // Unmatch mutation
  const unmatchMutation = useMutation({
    mutationFn: () => bankTransactionApi.unmatch(transaction.id),
    onSuccess: (data) => {
      showSnackbar(
        `Párosítás törölve! (${data.invoices_unmatched} számla)`,
        'success'
      );
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['bankStatements'] });
      setUnmatchDialogOpen(false);
      onSuccess?.();
    },
    onError: (error: any) => {
      showSnackbar(
        `Törlés sikertelen: ${error.response?.data?.error || error.message}`,
        'error'
      );
    },
  });

  // Rematch mutation
  const rematchMutation = useMutation({
    mutationFn: () => bankTransactionApi.rematch(transaction.id),
    onSuccess: (data) => {
      if (data.matched) {
        showSnackbar(
          `Újra párosítva! Módszer: ${data.method}, Megbízhatóság: ${
            data.confidence ? Math.round(parseFloat(data.confidence) * 100) : 0
          }%`,
          'success'
        );
      } else {
        showSnackbar('Nem található megfelelő párosítás', 'error');
      }
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['bankStatements'] });
      onSuccess?.();
    },
    onError: (error: any) => {
      showSnackbar(
        `Újra párosítás sikertelen: ${error.response?.data?.error || error.message}`,
        'error'
      );
    },
  });

  const handleApprove = () => {
    approveMutation.mutate();
  };

  const handleUnmatch = () => {
    setUnmatchDialogOpen(true);
  };

  const handleConfirmUnmatch = () => {
    unmatchMutation.mutate();
  };

  const handleRematch = () => {
    rematchMutation.mutate();
  };

  const isLoading =
    approveMutation.isPending ||
    unmatchMutation.isPending ||
    rematchMutation.isPending;

  return (
    <>
      <Stack direction="row" spacing={1} flexWrap="wrap">
        {/* Approve button - only show if confidence < 1.00 */}
        {isMatched && confidence < 1.0 && (
          <Button
            variant="contained"
            color="success"
            size="small"
            startIcon={
              approveMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <ApproveIcon />
              )
            }
            onClick={handleApprove}
            disabled={isLoading}
          >
            Jóváhagyás
          </Button>
        )}

        {/* Unmatch button - show for all matched transactions */}
        {isMatched && (
          <Button
            variant="outlined"
            color="error"
            size="small"
            startIcon={
              unmatchMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <UnmatchIcon />
              )
            }
            onClick={handleUnmatch}
            disabled={isLoading}
          >
            Párosítás törlése
          </Button>
        )}

        {/* Rematch button - show for low confidence or unmatched */}
        {(!isMatched || confidence < 0.9) && (
          <Button
            variant="outlined"
            color="primary"
            size="small"
            startIcon={
              rematchMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <RematchIcon />
              )
            }
            onClick={handleRematch}
            disabled={isLoading}
          >
            Újra párosítás
          </Button>
        )}
      </Stack>

      {/* Unmatch confirmation dialog */}
      <Dialog
        open={unmatchDialogOpen}
        onClose={() => !unmatchMutation.isPending && setUnmatchDialogOpen(false)}
      >
        <DialogTitle>Párosítás törlése</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Biztosan törölni szeretné ezt a párosítást?
            {transaction.is_batch_match &&
              transaction.matched_invoices_details && (
                <>
                  {' '}
                  Ez egy tömeges párosítás{' '}
                  <strong>
                    {transaction.matched_invoices_details.length} számlával
                  </strong>
                  .
                </>
              )}
          </DialogContentText>
          <DialogContentText sx={{ mt: 1, color: 'warning.main' }}>
            A törlés után manuálisan kell újra párosítania a tranzakciót, vagy
            használhatja az "Újra párosítás" funkciót.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setUnmatchDialogOpen(false)}
            disabled={unmatchMutation.isPending}
          >
            Mégse
          </Button>
          <Button
            onClick={handleConfirmUnmatch}
            color="error"
            variant="contained"
            disabled={unmatchMutation.isPending}
            startIcon={
              unmatchMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : undefined
            }
          >
            Törlés
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default MatchActionButtons;
