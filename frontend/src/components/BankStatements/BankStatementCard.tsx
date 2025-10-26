/**
 * @fileoverview Bank statement summary card component
 * @module components/BankStatements/BankStatementCard
 */

import { ReactElement } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  Stack,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
  Upload as UploadIcon,
  AccountBalance as BankIcon,
} from '@mui/icons-material';
import { BankStatement, BankStatementId } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';

/**
 * Props for BankStatementCard component.
 *
 * @interface BankStatementCardProps
 */
interface BankStatementCardProps {
  /** Bank statement data to display */
  statement: BankStatement;

  /** Callback when user clicks "View Transactions" button */
  onViewTransactions: (statementId: BankStatementId) => void;

  /** Callback when user clicks delete button */
  onDelete: (statementId: BankStatementId) => void;

  /** Whether deletion is in progress @default false */
  isDeleting?: boolean;
}

/**
 * Get status badge configuration based on statement status.
 *
 * @param status - Bank statement status
 * @returns Status badge properties (color, icon, label)
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
 * Format currency amount with HUF suffix.
 *
 * @param amount - Amount as decimal string
 * @returns Formatted amount (e.g., "1,234,567 HUF")
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
 * Bank statement summary card component.
 *
 * Displays key information about a bank statement including:
 * - Bank name and logo
 * - Account number and period
 * - Transaction count and match statistics
 * - Status badge
 * - Opening/closing balance
 *
 * @component
 * @example
 * ```tsx
 * <BankStatementCard
 *   statement={statement}
 *   onViewTransactions={(id) => navigate(`/statements/${id}`)}
 *   onDelete={(id) => handleDelete(id)}
 * />
 * ```
 */
const BankStatementCard: React.FC<BankStatementCardProps> = ({
  statement,
  onViewTransactions,
  onDelete,
  isDeleting = false,
}) => {
  const statusBadge = getStatusBadge(statement.status);

  // Calculate match percentage
  const matchRate =
    statement.total_transactions > 0
      ? Math.round((statement.matched_count / statement.total_transactions) * 100)
      : 0;

  // Format dates
  const periodFrom = format(parseISO(statement.statement_period_from), 'yyyy. MM. dd.', {
    locale: hu,
  });
  const periodTo = format(parseISO(statement.statement_period_to), 'yyyy. MM. dd.', { locale: hu });

  // Format upload date
  const uploadedAt = format(parseISO(statement.uploaded_at), 'yyyy. MM. dd. HH:mm', {
    locale: hu,
  });

  return (
    <Card
      sx={{
        position: 'relative',
        opacity: isDeleting ? 0.5 : 1,
        pointerEvents: isDeleting ? 'none' : 'auto',
      }}
    >
      {/* Loading indicator for parsing status */}
      {statement.status === 'PARSING' && (
        <LinearProgress sx={{ position: 'absolute', top: 0, left: 0, right: 0 }} />
      )}

      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Stack spacing={1.5}>
          {/* Header: Compact Table-like Layout */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr 1fr',
                gap: 2,
                alignItems: 'start',
                flex: 1
              }}
            >
              {/* Bank Name with Icon */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BankIcon color="primary" sx={{ fontSize: 28 }} />
                <Typography variant="h6" component="div" sx={{ whiteSpace: 'nowrap', fontSize: '1.1rem' }}>
                  {statement.bank_name}
                </Typography>
              </Box>

              {/* Account Number Column */}
              <Box>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.25 }}>
                  Számlaszám
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {statement.account_number}
                </Typography>
                {statement.account_iban && (
                  <Typography variant="caption" color="text.secondary">
                    ({statement.account_iban})
                  </Typography>
                )}
              </Box>

              {/* Period Column */}
              <Box>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.25 }}>
                  Időszak
                </Typography>
                <Typography variant="body2">
                  {periodFrom} – {periodTo}
                </Typography>
                {statement.statement_number && (
                  <Typography variant="caption" color="text.secondary">
                    Kivonat: {statement.statement_number}
                  </Typography>
                )}
              </Box>
            </Box>

            {/* Status Chip */}
            <Chip
              icon={statusBadge.icon}
              label={statusBadge.label}
              color={statusBadge.color}
              size="small"
            />
          </Box>

          {/* Statistics - Compact Row */}
          <Box
            sx={{
              display: 'flex',
              gap: 3,
              p: 1.5,
              bgcolor: 'background.default',
              borderRadius: 1,
              flexWrap: 'wrap',
            }}
          >
            {/* Transactions */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.25 }}>
                Tranzakciók
              </Typography>
              <Typography variant="body1" fontWeight="medium" component="span">
                {statement.total_transactions}
              </Typography>
              <Typography variant="caption" color="text.secondary" component="span" sx={{ ml: 0.5 }}>
                ({statement.credit_count} jóváírás • {statement.debit_count} terhelés)
              </Typography>
            </Box>

            {/* Match Rate */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.25 }}>
                Párosítva
              </Typography>
              <Typography variant="body1" fontWeight="medium" component="span">
                {statement.matched_count} / {statement.total_transactions}
              </Typography>
              <Typography
                variant="caption"
                component="span"
                sx={{ ml: 0.5 }}
                color={matchRate >= 70 ? 'success.main' : 'warning.main'}
              >
                ({matchRate}%)
              </Typography>
            </Box>

            {/* Balances */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.25 }}>
                Nyitó egyenleg
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {formatCurrency(statement.opening_balance)} HUF
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.25 }}>
                Záró egyenleg
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {formatCurrency(statement.closing_balance)} HUF
              </Typography>
            </Box>
          </Box>

          {/* File Information */}
          <Box>
            <Typography variant="caption" color="text.secondary">
              Fájl: {statement.file_name} • {(statement.file_size / 1024).toFixed(0)} KB •
              Feltöltve: {uploadedAt}
            </Typography>
          </Box>

          {/* Error Message */}
          {statement.status === 'ERROR' && statement.parse_error !== null && statement.parse_error !== '' && (
            <Box
              sx={{
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

          {/* Warnings */}
          {statement.parse_warnings && statement.parse_warnings.length > 0 && (
            <Box
              sx={{
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
        </Stack>
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pt: 0, pb: 1.5 }}>
        <Button
          variant="contained"
          startIcon={<ViewIcon />}
          onClick={() => onViewTransactions(statement.id)}
          disabled={statement.status !== 'PARSED' || isDeleting}
          size="small"
        >
          Tranzakciók megtekintése
        </Button>

        <Tooltip title="Kivonat törlése">
          <IconButton
            color="error"
            onClick={() => onDelete(statement.id)}
            disabled={isDeleting}
            size="small"
          >
            <DeleteIcon />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );
};

export default BankStatementCard;
