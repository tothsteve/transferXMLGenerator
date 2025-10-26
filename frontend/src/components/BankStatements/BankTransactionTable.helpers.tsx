/**
 * @fileoverview Helper functions for bank transaction table operations
 * @module components/BankStatements/BankTransactionTable.helpers
 */

import { ReactElement } from 'react';
import {
  TrendingUp as CreditIcon,
  TrendingDown as DebitIcon,
  CheckCircle as MatchedIcon,
  Cancel as UnmatchedIcon,
} from '@mui/icons-material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';

/**
 * Check if transaction amount represents a credit (incoming money).
 *
 * Determines transaction direction based on amount sign:
 * - Positive amount = Credit (money in)
 * - Negative amount = Debit (money out)
 *
 * @param amount - Transaction amount as decimal string (e.g., "1000.50" or "-250.00")
 * @returns True if credit (positive), false if debit (negative)
 *
 * @example
 * ```typescript
 * isCredit("1000.50");  // true
 * isCredit("-250.00");  // false
 * isCredit("0.00");     // false
 * ```
 */
export const isCredit = (amount: string): boolean => {
  return parseFloat(amount) > 0;
};

/**
 * Get transaction direction icon with appropriate color.
 *
 * Returns a Material-UI icon component styled for the transaction direction:
 * - Credit (positive): Green trending up icon
 * - Debit (negative): Red trending down icon
 *
 * @param amount - Transaction amount as decimal string
 * @returns React icon element with color styling
 *
 * @example
 * ```tsx
 * <Stack direction="row" spacing={1}>
 *   {getTransactionTypeIcon(transaction.amount)}
 *   <Typography>{isCredit(transaction.amount) ? 'Jóváírás' : 'Terhelés'}</Typography>
 * </Stack>
 * ```
 */
export const getTransactionTypeIcon = (amount: string): ReactElement => {
  return isCredit(amount) ? (
    <CreditIcon color="success" />
  ) : (
    <DebitIcon color="error" />
  );
};

/**
 * Match badge configuration for transaction display.
 *
 * @interface MatchBadge
 */
interface MatchBadge {
  /** Icon element to display */
  icon: ReactElement;
  /** Text label for badge */
  label: string;
  /** Badge color variant */
  color: 'success' | 'default' | 'warning';
}

/**
 * Get match status badge configuration based on transaction state.
 *
 * Determines badge appearance based on matching status and confidence:
 * - Unmatched: Gray badge with cancel icon
 * - High confidence (≥90%): Green badge with check icon
 * - Low confidence (<90%): Orange badge with check icon
 *
 * @param transaction - Bank transaction object
 * @returns Badge configuration object
 *
 * @example
 * ```tsx
 * const badge = getMatchBadge(transaction);
 * <Chip
 *   icon={badge.icon}
 *   label={badge.label}
 *   color={badge.color}
 *   size="small"
 * />
 * ```
 */
export const getMatchBadge = (transaction: BankTransaction): MatchBadge => {
  const isMatched = transaction.matched_invoice !== null || transaction.matched_transfer !== null;

  if (!isMatched) {
    return {
      icon: <UnmatchedIcon fontSize="small" />,
      label: 'Nincs párosítva',
      color: 'default',
    };
  }

  const confidence = parseFloat(transaction.match_confidence) * 100;

  if (confidence >= 90) {
    return {
      icon: <MatchedIcon fontSize="small" />,
      label: `Párosítva (${Math.round(confidence)}%)`,
      color: 'success',
    };
  }

  return {
    icon: <MatchedIcon fontSize="small" />,
    label: `Párosítva (${Math.round(confidence)}%)`,
    color: 'warning',
  };
};

/**
 * Format currency amount with sign and Hungarian locale formatting.
 *
 * Formats decimal amounts for display with:
 * - Hungarian number formatting (space as thousands separator)
 * - 2 decimal places
 * - Sign prefix (+ for positive, - for negative)
 *
 * @param amount - Amount as decimal string (e.g., "1000.50" or "-250.00")
 * @returns Formatted amount with sign (e.g., "+1 000,50" or "-250,00")
 *
 * @example
 * ```typescript
 * formatAmount("1000.50");   // "+1 000,50"
 * formatAmount("-250.00");   // "-250,00"
 * formatAmount("0.00");      // "-0,00"
 * ```
 */
export const formatAmount = (amount: string): string => {
  const num = parseFloat(amount);
  const formatted = new Intl.NumberFormat('hu-HU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(num));

  return num > 0 ? `+${formatted}` : `-${formatted}`;
};

/**
 * Extract partner name from transaction based on direction.
 *
 * Determines which party is the "partner" based on transaction direction:
 * - Credit (positive amount): Partner is the payer (who sent money)
 * - Debit (negative amount): Partner is the beneficiary (who received money)
 *
 * @param transaction - Bank transaction object
 * @returns Partner name or "-" if not available
 *
 * @example
 * ```typescript
 * // For incoming payment
 * getPartnerName({ amount: "1000.00", payer_name: "John Doe", ... });
 * // Returns: "John Doe"
 *
 * // For outgoing payment
 * getPartnerName({ amount: "-500.00", beneficiary_name: "ACME Corp", ... });
 * // Returns: "ACME Corp"
 * ```
 */
export const getPartnerName = (transaction: BankTransaction): string => {
  const amount = parseFloat(transaction.amount);
  // If credit (positive), partner is payer; if debit (negative), partner is beneficiary
  return amount > 0
    ? transaction.payer_name || '-'
    : transaction.beneficiary_name || '-';
};

/**
 * Extract partner account number from transaction based on direction.
 *
 * Retrieves the appropriate account number based on transaction direction:
 * - Credit: Returns payer's account (account_number or IBAN)
 * - Debit: Returns beneficiary's account (account_number or IBAN)
 *
 * Prefers account_number over IBAN if both are available.
 *
 * @param transaction - Bank transaction object
 * @returns Partner account number or empty string if not available
 *
 * @example
 * ```typescript
 * // For incoming payment
 * getPartnerAccount({
 *   amount: "1000.00",
 *   payer_account_number: "12345678-12345678",
 *   ...
 * });
 * // Returns: "12345678-12345678"
 *
 * // For outgoing payment with IBAN fallback
 * getPartnerAccount({
 *   amount: "-500.00",
 *   beneficiary_account_number: "",
 *   beneficiary_iban: "HU42 1234 5678 ...",
 *   ...
 * });
 * // Returns: "HU42 1234 5678 ..."
 * ```
 */
export const getPartnerAccount = (transaction: BankTransaction): string => {
  const amount = parseFloat(transaction.amount);
  return amount > 0
    ? transaction.payer_account_number || transaction.payer_iban
    : transaction.beneficiary_account_number || transaction.beneficiary_iban;
};
