/**
 * @fileoverview Bank statements management component with upload and listing
 * @module components/BankStatements/BankStatements
 */

import { ReactElement, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Stack,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Upload as UploadIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import {
  useBankStatements,
  useDeleteBankStatement,
  useSupportedBanks,
} from '../../hooks/api';
import { BankStatementQueryParams } from '../../schemas/bankStatement.schemas';
import { useToastContext } from '../../context/ToastContext';
import { useDebounce } from '../../hooks/useDebounce';
import BankStatementCard from './BankStatementCard';
import UploadDialog from './UploadDialog';
import LoadingSpinner from '../UI/LoadingSpinner';

/**
 * Main bank statement management interface.
 *
 * Provides functionality for:
 * - Uploading bank statement files (PDF/CSV/XML)
 * - Listing uploaded statements with pagination
 * - Filtering by date range, bank, and status
 * - Viewing transaction details
 * - Deleting statements
 *
 * @component
 * @example
 * ```tsx
 * <BankStatements />
 * ```
 */
const BankStatements = (): ReactElement => {
  const navigate = useNavigate();
  const { success: showSuccess, error: showError } = useToastContext();

  // Local state
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 800); // Increased delay for better performance
  const [bankFilter, setBankFilter] = useState<string>('');
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  // Build query params
  const queryParams: BankStatementQueryParams = {
    page,
    page_size: 20,
    ...(debouncedSearchTerm && { search: debouncedSearchTerm }),
    ...(bankFilter && { bank_code: bankFilter }),
    ordering: '-statement_period_to', // Most recent statement period first
  };

  // React Query hooks
  const { data: statementsData, isLoading, error, refetch } = useBankStatements(queryParams);
  const { data: supportedBanks } = useSupportedBanks();
  const deleteMutation = useDeleteBankStatement();

  // Calculate pagination
  const totalPages =
    statementsData?.count !== undefined && statementsData.count > 0
      ? Math.ceil(statementsData.count / 20)
      : 0;

  /**
   * Handle page change in pagination.
   *
   * @param _event - React change event (unused)
   * @param value - New page number (1-indexed)
   */
  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number): void => {
    setPage(value);
  };

  /**
   * Handle bank filter change.
   *
   * @param event - Select change event
   */
  const handleBankFilterChange = (event: SelectChangeEvent): void => {
    setBankFilter(event.target.value);
    setPage(1); // Reset to first page
  };

  /**
   * Handle search term change with debounce.
   *
   * @param event - Input change event
   */
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setSearchTerm(event.target.value);
    setPage(1);
  };

  /**
   * Clear all filters and reset to initial state.
   */
  const handleClearFilters = (): void => {
    setSearchTerm('');
    setBankFilter('');
    setPage(1);
  };

  /**
   * Handle view transactions button click.
   *
   * Navigates to transaction details page for the statement.
   *
   * @param statementId - Bank statement ID
   */
  const handleViewTransactions = (statementId: number): void => {
    void navigate(`/bank-statements/${statementId}/transactions`);
  };

  /**
   * Handle delete statement with confirmation.
   *
   * @param statementId - Bank statement ID to delete
   */
  const handleDelete = async (statementId: number): Promise<void> => {
    if (!window.confirm('Biztosan törölni szeretné ezt a kivonatot? Ez törli az összes tranzakciót is!')) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(statementId);
      showSuccess('Sikeres törlés', 'A bankkivonat törölve lett');
      void refetch();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ismeretlen hiba történt';
      showError('Törlési hiba', message);
    }
  };

  /**
   * Handle successful upload.
   */
  const handleUploadSuccess = (): void => {
    setShowUploadDialog(false);
    void refetch();
  };

  // Loading state
  if (isLoading && statementsData === undefined) {
    return <LoadingSpinner />;
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="error" variant="h6">
            Hiba történt az adatok betöltése során
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            {error instanceof Error ? error.message : 'Ismeretlen hiba'}
          </Typography>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={() => void refetch()}
            sx={{ mt: 2 }}
          >
            Újrapróbálás
          </Button>
        </Paper>
      </Box>
    );
  }

  const statements = statementsData?.results || [];
  const hasFilters = Boolean(searchTerm || bankFilter);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Bankkivonatok
        </Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setShowUploadDialog(true)}
          size="large"
        >
          Kivonat feltöltése
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
          {/* Search */}
          <TextField
            placeholder="Keresés bank név, számlaszám, kivonatszám vagy fájlnév alapján..."
            value={searchTerm}
            onChange={handleSearchChange}
            size="small"
            sx={{ flexGrow: 1, minWidth: { xs: '100%', md: 300 } }}
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

          {/* Bank Filter */}
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Bank</InputLabel>
            <Select
              value={bankFilter}
              onChange={handleBankFilterChange}
              label="Bank"
            >
              <MenuItem value="">
                <em>Összes bank</em>
              </MenuItem>
              {supportedBanks?.map((bank) => (
                <MenuItem key={bank.code} value={bank.code}>
                  {bank.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Refresh Button */}
          <Tooltip title="Frissítés">
            <IconButton onClick={() => void refetch()} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          {/* Clear Filters */}
          {hasFilters && (
            <Tooltip title="Szűrők törlése">
              <IconButton onClick={handleClearFilters} color="secondary">
                <ClearIcon />
              </IconButton>
            </Tooltip>
          )}
        </Stack>

        {/* Active Filters Display */}
        {hasFilters && (
          <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: 'wrap', gap: 1 }}>
            {searchTerm && (
              <Chip
                label={`Keresés: ${searchTerm}`}
                onDelete={() => {
                  setSearchTerm('');
                  setPage(1);
                }}
                size="small"
              />
            )}
            {bankFilter !== '' && (
              <Chip
                label={`Bank: ${supportedBanks?.find((b) => b.code === bankFilter)?.name ?? bankFilter}`}
                onDelete={() => {
                  setBankFilter('');
                  setPage(1);
                }}
                size="small"
              />
            )}
          </Stack>
        )}
      </Paper>

      {/* Results Count */}
      {statementsData && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Összesen {statementsData.count} kivonat találat
        </Typography>
      )}

      {/* Statements List */}
      {statements.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            {hasFilters ? 'Nincs találat a megadott szűrőkkel' : 'Még nincs feltöltött kivonat'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {hasFilters
              ? 'Próbálja meg módosítani a szűrőket'
              : 'Töltse fel az első bankkivonatot a "Kivonat feltöltése" gombbal'}
          </Typography>
        </Paper>
      ) : (
        <Stack spacing={2}>
          {statements.map((statement) => (
            <BankStatementCard
              key={statement.id}
              statement={statement}
              onViewTransactions={handleViewTransactions}
              onDelete={handleDelete}
              isDeleting={deleteMutation.isPending}
            />
          ))}
        </Stack>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            size="large"
            showFirstButton
            showLastButton
          />
        </Box>
      )}

      {/* Upload Dialog */}
      <UploadDialog
        open={showUploadDialog}
        onClose={() => setShowUploadDialog(false)}
        onSuccess={handleUploadSuccess}
      />
    </Box>
  );
};

export default BankStatements;
