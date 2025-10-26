/**
 * @fileoverview Transaction table header component with sortable columns
 * @module components/BankStatements/TransactionTableHeader
 */

import { ReactElement } from 'react';
import { TableHead, TableRow, TableCell, TableSortLabel } from '@mui/material';
import { SortableColumn, SortOrder } from './BankTransactionTable.utils';

/**
 * Props for TransactionTableHeader component.
 *
 * @interface TransactionTableHeaderProps
 */
interface TransactionTableHeaderProps {
  /** Currently active sort column */
  sortColumn: SortableColumn;

  /** Current sort direction */
  sortOrder: SortOrder;

  /** Callback when a column header is clicked */
  onSort: (column: SortableColumn) => void;
}

/**
 * Table header with sortable columns.
 *
 * Displays column headers for the transaction table with sorting capability:
 * - Date (booking_date)
 * - Type (transaction_type)
 * - Partner (not sortable)
 * - Description (not sortable)
 * - Amount
 * - Match status (not sortable)
 * - Actions (not sortable)
 *
 * Clicking a sortable column toggles between ascending and descending order.
 *
 * @component
 * @example
 * ```tsx
 * <TransactionTableHeader
 *   sortColumn={sortColumn}
 *   sortOrder={sortOrder}
 *   onSort={(column) => handleSort(column)}
 * />
 * ```
 */
const TransactionTableHeader: React.FC<TransactionTableHeaderProps> = ({
  sortColumn,
  sortOrder,
  onSort,
}): ReactElement => {
  return (
    <TableHead>
      <TableRow>
        <TableCell width={50} />
        <TableCell>
          <TableSortLabel
            active={sortColumn === 'booking_date'}
            direction={sortColumn === 'booking_date' ? sortOrder : 'asc'}
            onClick={() => onSort('booking_date')}
          >
            Dátum
          </TableSortLabel>
        </TableCell>
        <TableCell>
          <TableSortLabel
            active={sortColumn === 'transaction_type'}
            direction={sortColumn === 'transaction_type' ? sortOrder : 'asc'}
            onClick={() => onSort('transaction_type')}
          >
            Típus
          </TableSortLabel>
        </TableCell>
        <TableCell>Partner</TableCell>
        <TableCell>Leírás</TableCell>
        <TableCell align="right">
          <TableSortLabel
            active={sortColumn === 'amount'}
            direction={sortColumn === 'amount' ? sortOrder : 'asc'}
            onClick={() => onSort('amount')}
          >
            Összeg
          </TableSortLabel>
        </TableCell>
        <TableCell>Párosítás</TableCell>
        <TableCell align="center">Műveletek</TableCell>
      </TableRow>
    </TableHead>
  );
};

export default TransactionTableHeader;
