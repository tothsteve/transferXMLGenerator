/**
 * @fileoverview Transaction expanded details panel component
 * @module components/BankStatements/TransactionDetails
 */

import { ReactElement, useState } from 'react';
import { Box, Typography, Stack, Button, Alert } from '@mui/material';
import { Category as CategoryIcon } from '@mui/icons-material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import MatchDetailsCard from './MatchDetailsCard';
import CategoryDialog, { CategoryFormData } from './CategoryDialog';
import { otherCostsApi } from '../../services/api';

/**
 * Props for TransactionDetails component.
 *
 * @interface TransactionDetailsProps
 */
interface TransactionDetailsProps {
  /** Transaction data to display details for */
  transaction: BankTransaction;
  /** Optional callback after successful match action */
  onActionSuccess?: () => void;
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
  onActionSuccess,
}): ReactElement => {
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Check if transaction can be categorized
  const isMatched = transaction.matched_invoice !== null ||
                    transaction.matched_transfer !== null ||
                    transaction.matched_reimbursement !== null ||
                    (transaction.is_batch_match && transaction.matched_invoices_details && transaction.matched_invoices_details.length > 0) ||
                    transaction.has_other_cost === true ||
                    transaction.match_method === 'SYSTEM_AUTO_CATEGORIZED' ||
                    transaction.match_method === 'LEARNED_PATTERN';

  // Mutation for creating OtherCost
  const createOtherCostMutation = useMutation({
    mutationFn: async (formData: CategoryFormData) => {
      const tags = formData.tags
        ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
        : [];

      // Note: company and created_by are set by backend in perform_create()
      return otherCostsApi.create({
        bank_transaction: transaction.id,
        category: formData.category,
        amount: Math.abs(parseFloat(transaction.amount)).toString(),
        currency: transaction.currency,
        date: transaction.value_date,
        description: formData.description || transaction.description,
        notes: formData.notes,
        tags: tags,
        // company and created_by will be set automatically by the backend
      } as any); // Type assertion needed because OtherCost type includes these fields
    },
    onSuccess: () => {
      setCategoryDialogOpen(false);
      setError(null);
      // Invalidate queries to refresh transaction list
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] });
      queryClient.invalidateQueries({ queryKey: ['bankStatements'] });
      if (onActionSuccess) {
        onActionSuccess();
      }
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Hiba történt a kategorizálás során');
    },
  });

  const handleCategorize = async (formData: CategoryFormData) => {
    // Prevent double-submit - check if mutation is already in progress
    if (createOtherCostMutation.isPending) {
      return;
    }
    await createOtherCostMutation.mutateAsync(formData);
  };

  return (
    <Box sx={{ p: 2, bgcolor: 'background.default' }}>
      <Typography variant="subtitle2" gutterBottom>
        Részletek
      </Typography>
      <Stack spacing={2}>
        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Match Details Card (if matched) */}
        <MatchDetailsCard
          transaction={transaction}
          {...(onActionSuccess && { onActionSuccess })}
        />

        {/* Transaction Details */}
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

          {/* Transaction ID */}
          {transaction.transaction_id && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Tranzakció azonosító:
              </Typography>
              <Typography variant="body2" fontFamily="monospace">
                {transaction.transaction_id}
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

        {/* Categorize Button (only for unmatched transactions) */}
        {!isMatched && (
          <Box sx={{ pt: 1 }}>
            <Button
              variant="outlined"
              startIcon={<CategoryIcon />}
              onClick={() => setCategoryDialogOpen(true)}
              fullWidth
            >
              Kategorizálás
            </Button>
          </Box>
        )}
      </Stack>

      {/* Category Dialog */}
      <CategoryDialog
        open={categoryDialogOpen}
        transaction={transaction}
        onClose={() => setCategoryDialogOpen(false)}
        onSubmit={handleCategorize}
        isSubmitting={createOtherCostMutation.isPending}
      />
    </Box>
  );
};

export default TransactionDetails;
