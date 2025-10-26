/**
 * @fileoverview Transaction detail panel for manual matching dialog
 * @module components/BankStatements/TransactionDetailPanel
 */

import { ReactElement } from 'react';
import { Paper, Typography, Stack, Box, Alert } from '@mui/material';
import { TrendingUp as CreditIcon, TrendingDown as DebitIcon } from '@mui/icons-material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';

/**
 * Props for TransactionDetailPanel component.
 *
 * @interface TransactionDetailPanelProps
 */
interface TransactionDetailPanelProps {
  /** Transaction to display */
  transaction: BankTransaction;
}

/**
 * Format currency amount with Hungarian locale.
 *
 * @param amount - Amount as decimal string
 * @returns Formatted currency string
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
 * Check if transaction is a credit (incoming).
 *
 * @param amount - Transaction amount string
 * @returns True if credit, false if debit
 */
const isCredit = (amount: string): boolean => parseFloat(amount) > 0;

/**
 * Get partner name based on transaction direction.
 *
 * @param transaction - Bank transaction
 * @returns Partner name
 */
const getPartnerName = (transaction: BankTransaction): string => {
  return isCredit(transaction.amount)
    ? transaction.payer_name || '-'
    : transaction.beneficiary_name || '-';
};

/**
 * Transaction detail panel component.
 *
 * Displays key transaction information including date, type, amount,
 * partner, description, and current match status.
 *
 * @component
 * @example
 * ```tsx
 * <TransactionDetailPanel transaction={transaction} />
 * ```
 */
const TransactionDetailPanel: React.FC<TransactionDetailPanelProps> = ({
  transaction,
}): ReactElement => {
  const credit = isCredit(transaction.amount);
  const isMatched = transaction.matched_invoice !== null || transaction.matched_transfer !== null;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        Tranzakció részletei
      </Typography>
      <Stack spacing={1}>
        {/* Date */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            Dátum:
          </Typography>
          <Typography variant="body2">
            {format(parseISO(transaction.booking_date), 'yyyy. MM. dd.', { locale: hu })}
          </Typography>
        </Box>

        {/* Type (Credit/Debit) */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            Típus:
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            {credit ? (
              <CreditIcon color="success" fontSize="small" />
            ) : (
              <DebitIcon color="error" fontSize="small" />
            )}
            <Typography variant="body2">{credit ? 'Jóváírás' : 'Terhelés'}</Typography>
          </Stack>
        </Box>

        {/* Amount */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            Összeg:
          </Typography>
          <Typography
            variant="body2"
            fontWeight="medium"
            color={credit ? 'success.main' : 'error.main'}
          >
            {formatCurrency(transaction.amount)} HUF
          </Typography>
        </Box>

        {/* Partner */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            Partner:
          </Typography>
          <Typography variant="body2">{getPartnerName(transaction)}</Typography>
        </Box>

        {/* Description */}
        {transaction.description !== null && transaction.description !== '' && (
          <Box>
            <Typography variant="body2" color="text.secondary">
              Leírás:
            </Typography>
            <Typography variant="body2">{transaction.description}</Typography>
          </Box>
        )}

        {/* Current Match Status */}
        {isMatched && (
          <Alert severity="info" sx={{ mt: 1 }}>
            Jelenlegi párosítás:{' '}
            <strong>
              {transaction.matched_invoice !== null
                ? `Számla #${transaction.matched_invoice}`
                : `Átutalás #${transaction.matched_transfer ?? ''}`}
            </strong>
          </Alert>
        )}
      </Stack>
    </Paper>
  );
};

export default TransactionDetailPanel;
