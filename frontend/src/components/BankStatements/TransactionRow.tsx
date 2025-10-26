/**
 * @fileoverview Transaction table row component with expandable details
 * @module components/BankStatements/TransactionRow
 */

import { ReactElement } from 'react';
import {
  TableRow,
  TableCell,
  IconButton,
  Typography,
  Stack,
  Chip,
  Tooltip,
  Collapse,
} from '@mui/material';
import {
  KeyboardArrowDown as ExpandMoreIcon,
  KeyboardArrowUp as ExpandLessIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';
import {
  isCredit,
  getTransactionTypeIcon,
  getMatchBadge,
  formatAmount,
  getPartnerName,
  getPartnerAccount,
} from './BankTransactionTable.helpers';
import TransactionDetails from './TransactionDetails';

/**
 * Props for TransactionRow component.
 *
 * @interface TransactionRowProps
 */
interface TransactionRowProps {
  /** Transaction data to display */
  transaction: BankTransaction;

  /** Whether the row details are expanded */
  isExpanded: boolean;

  /** Callback when expand/collapse button is clicked */
  onExpand: () => void;

  /** Optional callback when match button is clicked (only for unmatched transactions) */
  onMatch?: (transactionId: number) => void;
}

/**
 * Transaction table row with expandable details panel.
 *
 * Features:
 * - Displays transaction summary (date, type, partner, amount, match status)
 * - Expandable details panel with additional information
 * - Color-coded transaction types (credit=green, debit=red)
 * - Match action button for unmatched transactions
 * - Match confidence indicator with color coding
 *
 * The row automatically formats:
 * - Dates in Hungarian locale (yyyy. MM. dd.)
 * - Amounts with sign and Hungarian number formatting
 * - Partner information based on transaction direction
 *
 * @component
 * @example
 * ```tsx
 * <TransactionRow
 *   transaction={transaction}
 *   isExpanded={expandedId === transaction.id}
 *   onExpand={() => setExpandedId(transaction.id)}
 *   onMatch={(id) => handleMatch(id)}
 * />
 * ```
 */
const TransactionRow: React.FC<TransactionRowProps> = ({
  transaction,
  isExpanded,
  onExpand,
  onMatch,
}): ReactElement => {
  const matchBadge = getMatchBadge(transaction);
  const transactionDate = format(parseISO(transaction.booking_date), 'yyyy. MM. dd.', {
    locale: hu,
  });
  const isMatchedTx = transaction.matched_invoice !== null || transaction.matched_transfer !== null;
  const partnerName = getPartnerName(transaction);
  const partnerAccount = getPartnerAccount(transaction);

  return (
    <>
      {/* Main Row */}
      <TableRow hover sx={{ '& > *': { borderBottom: isExpanded ? 'none' : undefined } }}>
        {/* Expand/Collapse Button */}
        <TableCell>
          <IconButton size="small" onClick={onExpand}>
            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </TableCell>

        {/* Transaction Date */}
        <TableCell>{transactionDate}</TableCell>

        {/* Transaction Type (Credit/Debit) */}
        <TableCell>
          <Stack direction="row" spacing={1} alignItems="center">
            {getTransactionTypeIcon(transaction.amount)}
            <Typography variant="body2">
              {isCredit(transaction.amount) ? 'Jóváírás' : 'Terhelés'}
            </Typography>
          </Stack>
        </TableCell>

        {/* Partner Information */}
        <TableCell>
          <Typography variant="body2" fontWeight="medium">
            {partnerName}
          </Typography>
          {partnerAccount && (
            <Typography variant="caption" color="text.secondary">
              {partnerAccount}
            </Typography>
          )}
        </TableCell>

        {/* Description */}
        <TableCell>
          <Typography variant="body2" color="text.secondary">
            {transaction.description || '-'}
          </Typography>
        </TableCell>

        {/* Amount */}
        <TableCell align="right">
          <Typography
            variant="body2"
            fontWeight="medium"
            color={isCredit(transaction.amount) ? 'success.main' : 'error.main'}
          >
            {formatAmount(transaction.amount)} HUF
          </Typography>
        </TableCell>

        {/* Match Status Badge */}
        <TableCell>
          <Chip icon={matchBadge.icon} label={matchBadge.label} color={matchBadge.color} size="small" />
        </TableCell>

        {/* Actions */}
        <TableCell align="center">
          {!isMatchedTx && onMatch !== undefined && (
            <Tooltip title="Párosítás számához">
              <IconButton
                size="small"
                color="primary"
                onClick={() => onMatch(transaction.id)}
              >
                <LinkIcon />
              </IconButton>
            </Tooltip>
          )}
        </TableCell>
      </TableRow>

      {/* Expanded Details Row */}
      <TableRow>
        <TableCell colSpan={8} sx={{ py: 0 }}>
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <TransactionDetails transaction={transaction} />
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

export default TransactionRow;
