/**
 * @fileoverview Transaction filtering panel component
 * @module components/BankStatements/TransactionFilters
 */

import { ReactElement } from 'react';
import {
  Paper,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Typography,
  SelectChangeEvent,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { TransactionFilterCategory } from './BankTransactionTable.utils';

/**
 * Props for TransactionFilters component.
 *
 * @interface TransactionFiltersProps
 */
interface TransactionFiltersProps {
  /** Current search term value */
  searchTerm: string;

  /** Callback when search term changes */
  onSearchChange: (value: string) => void;

  /** Current transaction type filter value */
  typeFilter: TransactionFilterCategory;

  /** Callback when type filter changes */
  onTypeFilterChange: (event: SelectChangeEvent) => void;

  /** Current match status filter value */
  matchFilter: 'matched' | 'unmatched' | '';

  /** Callback when match filter changes */
  onMatchFilterChange: (event: SelectChangeEvent) => void;

  /** Total number of transactions (before filtering) */
  totalCount: number;

  /** Number of transactions after filtering */
  filteredCount: number;
}

/**
 * Transaction filtering panel with search and dropdown filters.
 *
 * Features:
 * - Text search by partner name or transaction description
 * - Filter by transaction type (TRANSFER, POS, FEE, etc.)
 * - Filter by match status (matched, unmatched, or all)
 * - Real-time results count display
 * - Responsive layout (stacks vertically on mobile)
 *
 * The component displays a summary showing how many transactions
 * match the current filter criteria out of the total.
 *
 * @component
 * @example
 * ```tsx
 * <TransactionFilters
 *   searchTerm={searchTerm}
 *   onSearchChange={(value) => setSearchTerm(value)}
 *   typeFilter={typeFilter}
 *   onTypeFilterChange={(e) => setTypeFilter(e.target.value)}
 *   matchFilter={matchFilter}
 *   onMatchFilterChange={(e) => setMatchFilter(e.target.value)}
 *   totalCount={100}
 *   filteredCount={45}
 * />
 * ```
 */
const TransactionFilters: React.FC<TransactionFiltersProps> = ({
  searchTerm,
  onSearchChange,
  typeFilter,
  onTypeFilterChange,
  matchFilter,
  onMatchFilterChange,
  totalCount,
  filteredCount,
}): ReactElement => {
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        {/* Search Input */}
        <TextField
          placeholder="Keresés partner neve vagy leírás alapján..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          size="small"
          sx={{ flexGrow: 1 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            },
          }}
        />

        {/* Transaction Type Filter */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Típus</InputLabel>
          <Select value={typeFilter} onChange={onTypeFilterChange} label="Típus">
            <MenuItem value="">
              <em>Minden típus</em>
            </MenuItem>
            <MenuItem value="TRANSFER">Átutalás</MenuItem>
            <MenuItem value="POS">Kártyás fizetés</MenuItem>
            <MenuItem value="FEE">Díj</MenuItem>
            <MenuItem value="INTEREST">Kamat</MenuItem>
            <MenuItem value="CORRECTION">Korrekció</MenuItem>
            <MenuItem value="OTHER">Egyéb</MenuItem>
          </Select>
        </FormControl>

        {/* Match Status Filter */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Párosítás</InputLabel>
          <Select value={matchFilter} onChange={onMatchFilterChange} label="Párosítás">
            <MenuItem value="">
              <em>Minden</em>
            </MenuItem>
            <MenuItem value="matched">Párosítva</MenuItem>
            <MenuItem value="unmatched">Párosítatlan</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {/* Results Count Summary */}
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        {filteredCount} tranzakció
        {filteredCount !== totalCount && ` (${totalCount}-ból szűrve)`}
      </Typography>
    </Paper>
  );
};

export default TransactionFilters;
