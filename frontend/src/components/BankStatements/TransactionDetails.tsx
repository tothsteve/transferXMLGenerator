/**
 * @fileoverview Transaction expanded details panel component
 * @module components/BankStatements/TransactionDetails
 */

import { ReactElement } from 'react';
import { Box, Typography, Stack } from '@mui/material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';

/**
 * Props for TransactionDetails component.
 *
 * @interface TransactionDetailsProps
 */
interface TransactionDetailsProps {
  /** Transaction data to display details for */
  transaction: BankTransaction;
}

/**
 * Expanded transaction details panel.
 *
 * Displays additional information not shown in the table row:
 * - Full transaction description
 * - Remittance information/reference
 * - Matched invoice ID (if matched)
 * - Matched transfer ID (if matched)
 * - Creation timestamp
 *
 * This component is typically rendered inside a Collapse
 * component below the main transaction row.
 *
 * @component
 * @example
 * ```tsx
 * <Collapse in={isExpanded} timeout="auto" unmountOnExit>
 *   <TransactionDetails transaction={transaction} />
 * </Collapse>
 * ```
 */
const TransactionDetails: React.FC<TransactionDetailsProps> = ({
  transaction,
}): ReactElement => {
  return (
    <Box sx={{ p: 2, bgcolor: 'background.default' }}>
      <Typography variant="subtitle2" gutterBottom>
        Részletek
      </Typography>
      <Stack spacing={1}>
        {/* Description */}
        {transaction.description && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Leírás:
            </Typography>
            <Typography variant="body2">{transaction.description}</Typography>
          </Box>
        )}

        {/* Reference/Remittance Info */}
        {transaction.reference && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Közlemény:
            </Typography>
            <Typography variant="body2">{transaction.reference}</Typography>
          </Box>
        )}

        {/* Matched Invoice */}
        {transaction.matched_invoice !== null && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Párosított számla ID:
            </Typography>
            <Typography variant="body2" color="success.main">
              #{transaction.matched_invoice}
            </Typography>
          </Box>
        )}

        {/* Matched Transfer */}
        {transaction.matched_transfer !== null && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Párosított átutalás ID:
            </Typography>
            <Typography variant="body2" color="success.main">
              #{transaction.matched_transfer}
            </Typography>
          </Box>
        )}

        {/* Created At Timestamp */}
        <Box>
          <Typography variant="caption" color="text.secondary">
            Létrehozva:
          </Typography>
          <Typography variant="body2">
            {format(parseISO(transaction.created_at), 'yyyy. MM. dd. HH:mm', {
              locale: hu,
            })}
          </Typography>
        </Box>
      </Stack>
    </Box>
  );
};

export default TransactionDetails;
