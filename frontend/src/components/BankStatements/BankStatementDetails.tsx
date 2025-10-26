/**
 * @fileoverview Bank statement details page with transaction table
 * @module components/BankStatements/BankStatementDetails
 */

import { ReactElement, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Chip,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  AccountBalance as BankIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useBankStatement } from '../../hooks/api';
import { BankStatementIdSchema, BankStatement } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';
import LoadingSpinner from '../UI/LoadingSpinner';
import BankTransactionTable from './BankTransactionTable';
import ManualMatchDialog from './ManualMatchDialog';

/**
 * Get status badge configuration based on statement status.
 *
 * @param status - Bank statement status
 * @returns Status badge properties
 */
const getStatusBadge = (
  status: BankStatement['status']
): { color: 'default' | 'primary' | 'success' | 'error'; icon: ReactElement; label: string } => {
  switch (status) {
    case 'UPLOADED':
      return {
        color: 'default',
        icon: <UploadIcon fontSize="small" />,
        label: 'Feltöltve',
      };
    case 'PARSING':
      return {
        color: 'primary',
        icon: <HourglassIcon fontSize="small" />,
        label: 'Feldolgozás...',
      };
    case 'PARSED':
      return {
        color: 'success',
        icon: <CheckCircleIcon fontSize="small" />,
        label: 'Feldolgozva',
      };
    case 'ERROR':
      return {
        color: 'error',
        icon: <ErrorIcon fontSize="small" />,
        label: 'Hiba',
      };
    default:
      return {
        color: 'default',
        icon: <HourglassIcon fontSize="small" />,
        label: status,
      };
  }
};

/**
 * Format currency amount.
 *
 * @param amount - Amount as decimal string
 * @returns Formatted amount
 */
const formatCurrency = (amount: string): string => {
  const num = parseFloat(amount);
  return new Intl.NumberFormat('hu-HU', {
    style: 'decimal',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
};

/**
 * Bank statement details page component.
 *
 * Displays:
 * - Bank statement header information
 * - Account and period details
 * - Transaction statistics
 * - Full transaction table with filtering and sorting
 * - Manual matching capability
 *
 * @component
 * @example
 * ```tsx
 * // Accessed via route: /bank-statements/:id/transactions
 * <BankStatementDetails />
 * ```
 */
const BankStatementDetails = (): ReactElement => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [matchDialogOpen, setMatchDialogOpen] = useState(false);
  const [selectedTransactionId, setSelectedTransactionId] = useState<number | null>(null);

  // Validate and parse statement ID
  const statementId = BankStatementIdSchema.safeParse(Number(id));

  // Fetch statement details
  const { data: statement, isLoading, error } = useBankStatement(
    statementId.success ? statementId.data : 0
  );

  /**
   * Handle navigation back to statements list.
   */
  const handleBack = (): void => {
    void navigate('/bank-statements');
  };

  /**
   * Handle match transaction button click.
   *
   * @param transactionId - Transaction ID to match
   */
  const handleMatchTransaction = (transactionId: number): void => {
    setSelectedTransactionId(transactionId);
    setMatchDialogOpen(true);
  };

  /**
   * Handle match dialog close.
   */
  const handleMatchDialogClose = (): void => {
    setMatchDialogOpen(false);
    setSelectedTransactionId(null);
  };

  // Invalid ID
  if (!statementId.success) {
    return (
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="error" variant="h6">
            Érvénytelen kivonat azonosító
          </Typography>
          <Button
            variant="contained"
            startIcon={<BackIcon />}
            onClick={handleBack}
            sx={{ mt: 2 }}
          >
            Vissza a kivonatokhoz
          </Button>
        </Paper>
      </Box>
    );
  }

  // Loading state
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Error state
  if (error || !statement) {
    return (
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="error" variant="h6">
            Hiba történt a kivonat betöltése során
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            {error instanceof Error ? error.message : 'Ismeretlen hiba'}
          </Typography>
          <Button
            variant="contained"
            startIcon={<BackIcon />}
            onClick={handleBack}
            sx={{ mt: 2 }}
          >
            Vissza a kivonatokhoz
          </Button>
        </Paper>
      </Box>
    );
  }

  const statusBadge = getStatusBadge(statement.status);
  const matchRate =
    statement.total_transactions > 0
      ? Math.round((statement.matched_count / statement.total_transactions) * 100)
      : 0;

  const periodFrom = format(parseISO(statement.statement_period_from), 'yyyy. MM. dd.', {
    locale: hu,
  });
  const periodTo = format(parseISO(statement.statement_period_to), 'yyyy. MM. dd.', { locale: hu });

  return (
    <Box sx={{ p: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link
          component="button"
          variant="body2"
          onClick={handleBack}
          sx={{ cursor: 'pointer', textDecoration: 'none' }}
        >
          Bankkivonatok
        </Link>
        <Typography variant="body2" color="text.primary">
          {statement.bank_name} - {statement.account_number}
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Bankkivonat részletei
        </Typography>
        <Button variant="outlined" startIcon={<BackIcon />} onClick={handleBack}>
          Vissza
        </Button>
      </Stack>

      {/* Statement Summary */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
          {/* Bank Information */}
          <Box sx={{ flex: 1 }}>
            <Stack spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BankIcon color="primary" sx={{ fontSize: 32 }} />
                <Box>
                  <Typography variant="h6">{statement.bank_name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {statement.bank_code} • {statement.bank_bic}
                  </Typography>
                </Box>
                <Chip
                  icon={statusBadge.icon}
                  label={statusBadge.label}
                  color={statusBadge.color}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Számlaszám
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {statement.account_number}
                </Typography>
                {statement.account_iban && (
                  <Typography variant="caption" color="text.secondary">
                    IBAN: {statement.account_iban}
                  </Typography>
                )}
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Időszak
                </Typography>
                <Typography variant="body1">
                  {periodFrom} – {periodTo}
                </Typography>
                {statement.statement_number && (
                  <Typography variant="caption" color="text.secondary">
                    Kivonat szám: {statement.statement_number}
                  </Typography>
                )}
              </Box>
            </Stack>
          </Box>

          {/* Statistics */}
          <Box sx={{ flex: 1 }}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={2}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Összes tranzakció
                  </Typography>
                  <Typography variant="h4">{statement.total_transactions}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {statement.credit_count} jóváírás • {statement.debit_count} terhelés
                  </Typography>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Párosítva
                  </Typography>
                  <Typography variant="h4">
                    {statement.matched_count} / {statement.total_transactions}
                  </Typography>
                  <Typography variant="caption" color={matchRate >= 70 ? 'success.main' : 'warning.main'}>
                    {matchRate}% találat
                  </Typography>
                </Paper>
              </Stack>

              <Stack direction="row" spacing={2}>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Nyitó egyenleg
                  </Typography>
                  <Typography variant="h6">{formatCurrency(statement.opening_balance)} HUF</Typography>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Záró egyenleg
                  </Typography>
                  <Typography variant="h6">{formatCurrency(statement.closing_balance)} HUF</Typography>
                </Paper>
              </Stack>
            </Stack>
          </Box>
        </Stack>

        {/* Error/Warning Messages */}
        {statement.status === 'ERROR' && statement.parse_error !== null && statement.parse_error !== '' && (
          <Box
            sx={{
              mt: 2,
              p: 2,
              bgcolor: 'error.light',
              color: 'error.contrastText',
              borderRadius: 1,
            }}
          >
            <Typography variant="body2" fontWeight="medium">
              Feldolgozási hiba:
            </Typography>
            <Typography variant="body2">{statement.parse_error}</Typography>
          </Box>
        )}

        {statement.parse_warnings && statement.parse_warnings.length > 0 && (
          <Box
            sx={{
              mt: 2,
              p: 2,
              bgcolor: 'warning.light',
              borderRadius: 1,
            }}
          >
            <Typography variant="body2" fontWeight="medium">
              Figyelmeztetések:
            </Typography>
            {statement.parse_warnings.map((warning, index) => (
              <Typography key={index} variant="body2">
                • {warning}
              </Typography>
            ))}
          </Box>
        )}
      </Paper>

      {/* Transactions Table */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4, mb: 2 }}>
        Tranzakciók
      </Typography>
      <BankTransactionTable
        statementId={statement.id}
        onMatchTransaction={handleMatchTransaction}
      />

      {/* Manual Match Dialog */}
      {selectedTransactionId !== null && (
        <ManualMatchDialog
          open={matchDialogOpen}
          onClose={handleMatchDialogClose}
          transactionId={selectedTransactionId}
        />
      )}
    </Box>
  );
};

export default BankStatementDetails;
