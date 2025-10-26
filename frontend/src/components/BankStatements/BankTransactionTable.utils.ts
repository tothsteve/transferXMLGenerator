/**
 * @fileoverview Utility functions for transaction filtering and sorting
 * @module components/BankStatements/BankTransactionTable.utils
 */

import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { getPartnerName } from './BankTransactionTable.helpers';

/**
 * Sortable column identifier.
 *
 * @typedef SortableColumn
 */
export type SortableColumn = 'booking_date' | 'amount' | 'transaction_type';

/**
 * Sort order direction.
 *
 * @typedef SortOrder
 */
export type SortOrder = 'asc' | 'desc';

/**
 * Transaction filter category type.
 * These are simplified categories for UI filtering.
 */
export type TransactionFilterCategory = 'TRANSFER' | 'POS' | 'FEE' | 'INTEREST' | 'CORRECTION' | 'OTHER' | '';

/**
 * Filter configuration for transactions.
 *
 * @interface TransactionFilters
 */
export interface TransactionFilters {
  /** Transaction type filter (category) */
  typeFilter: TransactionFilterCategory;
  /** Match status filter */
  matchFilter: 'matched' | 'unmatched' | '';
  /** Search term for partner name or description */
  searchTerm: string;
}

/**
 * Filter transactions based on multiple criteria.
 *
 * Applies the following filters in sequence:
 * 1. Transaction type (if specified)
 * 2. Match status (if specified)
 * 3. Text search on partner name and description
 *
 * @param transactions - Array of transactions to filter
 * @param filters - Filter configuration object
 * @returns Filtered transaction array
 *
 * @example
 * ```typescript
 * const filtered = filterTransactions(allTransactions, {
 *   typeFilter: 'TRANSFER',
 *   matchFilter: 'unmatched',
 *   searchTerm: 'John',
 * });
 * ```
 */
export const filterTransactions = (
  transactions: BankTransaction[],
  filters: TransactionFilters
): BankTransaction[] => {
  let filtered = [...transactions];

  // Apply type filter with category matching
  if (filters.typeFilter) {
    filtered = filtered.filter((t) => {
      const txType = t.transaction_type;
      const filterCategory = filters.typeFilter;

      // Map filter categories to actual transaction types
      switch (filterCategory) {
        case 'TRANSFER':
          return txType.includes('TRANSFER') || txType.includes('AFR');
        case 'POS':
          return txType.includes('POS') || txType.includes('ATM');
        case 'FEE':
          return txType.includes('FEE') || txType === 'BANK_FEE';
        case 'INTEREST':
          return txType.includes('INTEREST');
        case 'CORRECTION':
          return txType === 'CORRECTION';
        case 'OTHER':
          return txType === 'OTHER';
        default:
          // Unknown filter category
          return false;
      }
    });
  }

  // Apply match status filter
  if (filters.matchFilter === 'matched') {
    filtered = filtered.filter(
      (t) =>
        t.matched_invoice !== null ||
        t.matched_transfer !== null ||
        t.matched_reimbursement !== null
    );
  } else if (filters.matchFilter === 'unmatched') {
    filtered = filtered.filter(
      (t) =>
        t.matched_invoice === null &&
        t.matched_transfer === null &&
        t.matched_reimbursement === null
    );
  }

  // Apply text search filter
  if (filters.searchTerm) {
    const term = filters.searchTerm.toLowerCase();
    filtered = filtered.filter(
      (t) =>
        getPartnerName(t).toLowerCase().includes(term) ||
        (t.description && t.description.toLowerCase().includes(term))
    );
  }

  return filtered;
};

/**
 * Sort transactions by specified column and direction.
 *
 * Supports sorting by:
 * - **booking_date**: Chronological order
 * - **amount**: Numerical order (handles negative values)
 * - **transaction_type**: Alphabetical order
 *
 * @param transactions - Array of transactions to sort (will be modified in place)
 * @param column - Column to sort by
 * @param order - Sort direction (ascending or descending)
 * @returns Sorted transaction array (same reference as input)
 *
 * @example
 * ```typescript
 * const sorted = sortTransactions(
 *   transactions,
 *   'booking_date',
 *   'desc'
 * ); // Most recent first
 * ```
 */
export const sortTransactions = (
  transactions: BankTransaction[],
  column: SortableColumn,
  order: SortOrder
): BankTransaction[] => {
  return transactions.sort((a, b) => {
    let aValue: string | number = '';
    let bValue: string | number = '';

    switch (column) {
      case 'booking_date':
        aValue = a.booking_date;
        bValue = b.booking_date;
        break;
      case 'amount':
        aValue = parseFloat(a.amount);
        bValue = parseFloat(b.amount);
        break;
      case 'transaction_type':
        aValue = a.transaction_type;
        bValue = b.transaction_type;
        break;
    }

    if (aValue < bValue) return order === 'asc' ? -1 : 1;
    if (aValue > bValue) return order === 'asc' ? 1 : -1;
    return 0;
  });
};

/**
 * Process transactions with filtering and sorting.
 *
 * Convenience function that applies both filtering and sorting
 * in a single operation. Memoize the result in the calling component
 * for optimal performance.
 *
 * @param transactions - Original transaction array
 * @param filters - Filter configuration
 * @param sortColumn - Column to sort by
 * @param sortOrder - Sort direction
 * @returns Processed transaction array
 *
 * @example
 * ```typescript
 * const processed = useMemo(
 *   () => processTransactions(transactions, filters, 'booking_date', 'desc'),
 *   [transactions, filters]
 * );
 * ```
 */
export const processTransactions = (
  transactions: BankTransaction[],
  filters: TransactionFilters,
  sortColumn: SortableColumn,
  sortOrder: SortOrder
): BankTransaction[] => {
  if (transactions.length === 0) return [];

  const filtered = filterTransactions(transactions, filters);
  return sortTransactions(filtered, sortColumn, sortOrder);
};
