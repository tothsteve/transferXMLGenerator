/**
 * @fileoverview Match details card component for transaction matching information
 * @module components/BankStatements/MatchDetailsCard
 */

import { ReactElement } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  Box,
  Link as MuiLink,
} from '@mui/material';
import {
  CheckCircle as MatchedIcon,
  SwapHoriz as TransferIcon,
  Receipt as InvoiceIcon,
  SwapVert as ReimbursementIcon,
} from '@mui/icons-material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';

/**
 * Props for MatchDetailsCard component.
 *
 * @interface MatchDetailsCardProps
 */
interface MatchDetailsCardProps {
  /** Transaction with match information */
  transaction: BankTransaction;
}

/**
 * Get match method display text in Hungarian.
 *
 * @param method - Match method from backend
 * @returns Hungarian display text
 */
const getMatchMethodLabel = (method: string): string => {
  const methodLabels: Record<string, string> = {
    'TRANSFER_EXACT': 'Átutalás párosítás',
    'REFERENCE_EXACT': 'Hivatkozás szerinti',
    'AMOUNT_IBAN': 'Összeg + IBAN',
    'FUZZY_NAME': 'Név hasonlóság',
    'AMOUNT_DATE_ONLY': 'Csak összeg/dátum',
    'REIMBURSEMENT_PAIR': 'Visszatérítés pár',
    'MANUAL': 'Manuális',
  };
  return methodLabels[method] || method;
};

/**
 * Get confidence badge color based on score.
 *
 * @param confidence - Confidence score as string (0.00 to 1.00)
 * @returns MUI color variant
 */
const getConfidenceColor = (confidence: string): 'success' | 'warning' | 'default' => {
  const score = parseFloat(confidence);
  if (score >= 0.95) return 'success';  // High confidence
  if (score >= 0.70) return 'warning';  // Medium confidence
  return 'default';  // Low confidence
};

/**
 * Get confidence label with percentage.
 *
 * @param confidence - Confidence score as string
 * @returns Formatted label
 */
const getConfidenceLabel = (confidence: string): string => {
  const score = parseFloat(confidence);
  const percent = Math.round(score * 100);

  if (score >= 0.95) return `Magas (${percent}%)`;
  if (score >= 0.70) return `Közepes (${percent}%)`;
  return `Alacsony (${percent}%)`;
};

/**
 * Get payment status badge color.
 *
 * @param status - Payment status
 * @returns MUI color variant
 */
const getPaymentStatusColor = (status: string): 'success' | 'info' | 'warning' | 'default' => {
  const statusColors: Record<string, 'success' | 'info' | 'warning' | 'default'> = {
    'PAID': 'success',
    'PREPARED': 'info',
    'UNPAID': 'warning',
  };
  return statusColors[status] || 'default';
};

/**
 * Get payment status label in Hungarian.
 *
 * @param status - Payment status
 * @returns Hungarian label
 */
const getPaymentStatusLabel = (status: string): string => {
  const statusLabels: Record<string, string> = {
    'PAID': 'Kifizetve',
    'PREPARED': 'Előkészítve',
    'UNPAID': 'Fizetésre vár',
  };
  return statusLabels[status] || status;
};

/**
 * Match details card component.
 *
 * Displays rich information about transaction matching:
 * - Match type (invoice, transfer, reimbursement)
 * - Match method and confidence
 * - Detailed information about matched entity
 * - Match timestamp and notes
 *
 * @component
 * @example
 * ```tsx
 * <MatchDetailsCard transaction={transaction} />
 * ```
 */
const MatchDetailsCard: React.FC<MatchDetailsCardProps> = ({
  transaction,
}): ReactElement | null => {
  // Check if transaction is matched
  const hasMatch = transaction.matched_invoice !== null ||
                   transaction.matched_transfer !== null ||
                   transaction.matched_reimbursement !== null;

  if (!hasMatch) {
    return null;
  }

  const confidence = transaction.match_confidence;
  const method = transaction.match_method;

  return (
    <Card variant="outlined" sx={{ bgcolor: 'success.lighter', borderColor: 'success.main' }}>
      <CardContent>
        <Stack spacing={2}>
          {/* Header with Icon and Title */}
          <Stack direction="row" spacing={1} alignItems="center">
            <MatchedIcon color="success" />
            <Typography variant="subtitle2" fontWeight="bold">
              Párosítás részletei
            </Typography>
          </Stack>

          {/* Match Method and Confidence */}
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip
              label={getMatchMethodLabel(method)}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Chip
              label={getConfidenceLabel(confidence)}
              size="small"
              color={getConfidenceColor(confidence)}
            />
          </Stack>

          {/* Matched Invoice Details */}
          {transaction.matched_invoice !== null && transaction.matched_invoice_details && (
            <Box>
              <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                <InvoiceIcon fontSize="small" color="primary" />
                <Typography variant="body2" fontWeight="medium">
                  Párosított számla
                </Typography>
              </Stack>
              <Stack spacing={0.5} pl={3.5}>
                <Typography variant="body2">
                  <strong>Számlaszám:</strong>{' '}
                  <MuiLink
                    href={`/nav-invoices?invoiceId=${transaction.matched_invoice_details.id}`}
                    underline="hover"
                    color="primary"
                  >
                    {transaction.matched_invoice_details.invoice_number}
                  </MuiLink>
                </Typography>
                <Typography variant="body2">
                  <strong>Szállító:</strong> {transaction.matched_invoice_details.supplier_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Adószám:</strong> {transaction.matched_invoice_details.supplier_tax_number}
                </Typography>
                {transaction.matched_invoice_details.gross_amount && (
                  <Typography variant="body2">
                    <strong>Összeg:</strong>{' '}
                    {new Intl.NumberFormat('hu-HU', {
                      style: 'decimal',
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    }).format(parseFloat(transaction.matched_invoice_details.gross_amount))}{' '}
                    HUF
                  </Typography>
                )}
                <Chip
                  label={getPaymentStatusLabel(transaction.matched_invoice_details.payment_status)}
                  size="small"
                  color={getPaymentStatusColor(transaction.matched_invoice_details.payment_status)}
                  sx={{ width: 'fit-content', mt: 0.5 }}
                />
              </Stack>
            </Box>
          )}

          {/* Matched Transfer Details */}
          {transaction.matched_transfer !== null && (
            <Box>
              <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                <TransferIcon fontSize="small" color="primary" />
                <Typography variant="body2" fontWeight="medium">
                  Párosított átutalás
                </Typography>
              </Stack>
              <Stack spacing={0.5} pl={3.5}>
                <Typography variant="body2">
                  <MuiLink
                    href={`/transfers/${transaction.matched_transfer}`}
                    underline="hover"
                    color="primary"
                  >
                    Átutalás #{transaction.matched_transfer}
                  </MuiLink>
                </Typography>
              </Stack>
            </Box>
          )}

          {/* Matched Reimbursement Details */}
          {transaction.matched_reimbursement !== null && (
            <Box>
              <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                <ReimbursementIcon fontSize="small" color="primary" />
                <Typography variant="body2" fontWeight="medium">
                  Visszatérítés pár
                </Typography>
              </Stack>
              <Stack spacing={0.5} pl={3.5}>
                <Typography variant="body2">
                  Kapcsolódó tranzakció #{transaction.matched_reimbursement}
                </Typography>
              </Stack>
            </Box>
          )}

          {/* Match Timestamp */}
          {transaction.matched_at && (
            <Typography variant="caption" color="text.secondary">
              Párosítva: {format(parseISO(transaction.matched_at), 'yyyy. MM. dd. HH:mm', {
                locale: hu,
              })}
              {transaction.matched_by === null && ' (automatikus)'}
            </Typography>
          )}

          {/* Match Notes (if available) */}
          {transaction.match_notes && (
            <Box sx={{ pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                Párosítás megjegyzés:
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                {transaction.match_notes}
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default MatchDetailsCard;
