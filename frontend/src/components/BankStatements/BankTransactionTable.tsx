/**
 * @fileoverview Bank transaction table with sorting, filtering, and matching
 * @module components/BankStatements/BankTransactionTable
 */

import { ReactElement, useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
  SelectChangeEvent,
} from '@mui/material';
import { useBankTransactions } from '../../hooks/api';
import { BankStatementId, BankTransaction } from '../../schemas/bankStatement.schemas';
import LoadingSpinner from '../UI/LoadingSpinner';
import TransactionFilters from './TransactionFilters';
import TransactionRow from './TransactionRow';
import TransactionTableHeader from './TransactionTableHeader';
import { processTransactions, SortableColumn, SortOrder, TransactionFilterCategory } from './BankTransactionTable.utils';

/**
 * Props for BankTransactionTable component.
 *
 * @interface BankTransactionTableProps
 */
interface BankTransactionTableProps {
  /** Bank statement ID to fetch transactions for */
  statementId: BankStatementId;

  /** Optional callback when user clicks match button on a transaction */
  onMatchTransaction?: (transactionId: number) => void;
}

/**
 * Bank transaction table component with comprehensive filtering and sorting.
 *
 * Features:
 * - **Sortable columns**: Date, amount, and transaction type
 * - **Multi-criteria filtering**: By type, match status, and text search
 * - **Row expansion**: Click to view detailed transaction information
 * - **Match actions**: One-click matching for unmatched transactions
 * - **Color coding**: Visual distinction between credits and debits
 * - **Responsive design**: Mobile-friendly layout and controls
 *
 * The table automatically fetches transaction data from the API based on
 * the provided statement ID and applies client-side filtering and sorting
 * for optimal performance.
 *
 * @component
 * @example
 * ```tsx
 * <BankTransactionTable
 *   statementId={123}
 *   onMatchTransaction={(id) => openMatchDialog(id)}
 * />
 * ```
 */
const BankTransactionTable: React.FC<BankTransactionTableProps> = ({
  statementId,
  onMatchTransaction,
}): ReactElement => {
  // UI state
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [sortColumn, setSortColumn] = useState<SortableColumn>('booking_date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Filter state
  const [typeFilter, setTypeFilter] = useState<TransactionFilterCategory>('');
  const [matchFilter, setMatchFilter] = useState<'matched' | 'unmatched' | ''>('');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch transactions from API
  const { data: transactionsData, isLoading, error } = useBankTransactions(statementId);
  const transactions = useMemo(
    () => transactionsData?.results ?? [],
    [transactionsData?.results]
  );

  /**
   * Handle sort column change with direction toggle.
   *
   * If clicking the same column, toggles between ascending and descending.
   * If clicking a new column, sets it as active with ascending order.
   *
   * @param column - Column to sort by
   */
  const handleSort = (column: SortableColumn): void => {
    if (sortColumn === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortOrder('asc');
    }
  };

  /**
   * Handle row expansion toggle.
   *
   * Expands the clicked row or collapses it if already expanded.
   * Only one row can be expanded at a time.
   *
   * @param transactionId - Transaction ID to expand/collapse
   */
  const handleRowExpand = (transactionId: number): void => {
    setExpandedRow(expandedRow === transactionId ? null : transactionId);
  };

  /**
   * Handle successful match action (approve/unmatch/rematch).
   *
   * Closes the expanded row so the user can re-expand to see updated state.
   */
  const handleActionSuccess = (): void => {
    setExpandedRow(null);
  };

  /**
   * Memoized filtered and sorted transaction list.
   *
   * Uses utility functions to apply filtering and sorting operations.
   * The computation is memoized to avoid unnecessary recalculations
   * when unrelated state changes.
   */
  const processedTransactions = useMemo(
    () =>
      processTransactions(
        transactions,
        { typeFilter, matchFilter, searchTerm },
        sortColumn,
        sortOrder
      ),
    [transactions, typeFilter, matchFilter, searchTerm, sortColumn, sortOrder]
  );

  // Loading state
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Error state
  if (error !== null && error !== undefined) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error" variant="h6">
          Hiba történt a tranzakciók betöltése során
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {error instanceof Error ? error.message : 'Ismeretlen hiba'}
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Filters Panel */}
      <TransactionFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        typeFilter={typeFilter}
        onTypeFilterChange={(e: SelectChangeEvent) => setTypeFilter(e.target.value as TransactionFilterCategory)}
        matchFilter={matchFilter}
        onMatchFilterChange={(e: SelectChangeEvent) =>
          setMatchFilter(e.target.value as 'matched' | 'unmatched' | '')
        }
        totalCount={transactions.length}
        filteredCount={processedTransactions.length}
      />

      {/* Transaction Table */}
      <TableContainer component={Paper}>
        <Table>
          <TransactionTableHeader
            sortColumn={sortColumn}
            sortOrder={sortOrder}
            onSort={handleSort}
          />
          <TableBody>
            {processedTransactions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    Nincs megjeleníthető tranzakció
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              processedTransactions.map((transaction: BankTransaction) => (
                <TransactionRow
                  key={transaction.id}
                  transaction={transaction}
                  isExpanded={expandedRow === transaction.id}
                  onExpand={() => handleRowExpand(transaction.id)}
                  onActionSuccess={handleActionSuccess}
                  {...(onMatchTransaction !== undefined && { onMatch: onMatchTransaction })}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default BankTransactionTable;
