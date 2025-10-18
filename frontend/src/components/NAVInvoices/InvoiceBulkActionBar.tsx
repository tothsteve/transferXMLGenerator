import React from 'react';
import {
  Paper,
  Typography,
  Stack,
  Button,
  FormControlLabel,
  Checkbox,
  TextField,
} from '@mui/material';
import {
  Add as AddIcon,
  HourglassEmpty as UnpaidIcon,
  Schedule as PreparedIcon,
  CheckCircle as PaidIcon,
} from '@mui/icons-material';

interface InvoiceBulkActionBarProps {
  selectedCount: number;
  onGenerateTransfers: () => void;
  onBulkMarkUnpaid: () => void;
  onBulkMarkPrepared: () => void;
  onBulkMarkPaid: () => void;
  usePaymentDueDate: boolean;
  setUsePaymentDueDate: (value: boolean) => void;
  paymentDate: string;
  setPaymentDate: (value: string) => void;
  isUnpaidPending: boolean;
  isPreparedPending: boolean;
  isPaidPending: boolean;
}

const InvoiceBulkActionBar: React.FC<InvoiceBulkActionBarProps> = ({
  selectedCount,
  onGenerateTransfers,
  onBulkMarkUnpaid,
  onBulkMarkPrepared,
  onBulkMarkPaid,
  usePaymentDueDate,
  setUsePaymentDueDate,
  paymentDate,
  setPaymentDate,
  isUnpaidPending,
  isPreparedPending,
  isPaidPending,
}) => {
  return (
    <Paper elevation={1} sx={{ p: 1, mb: 0.5, backgroundColor: 'action.hover' }}>
      <Typography
        variant="caption"
        sx={{
          mb: 0.5,
          color: 'primary.main',
          fontWeight: 'medium',
          fontSize: '0.75rem',
          display: 'block',
        }}
      >
        Tömeges műveletek ({selectedCount} számla)
      </Typography>

      <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap" useFlexGap>
        <Button
          variant="contained"
          color="primary"
          size="small"
          startIcon={<AddIcon fontSize="small" />}
          onClick={onGenerateTransfers}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
        >
          Utalás generálás
        </Button>

        <Button
          variant="outlined"
          color="warning"
          size="small"
          startIcon={<UnpaidIcon fontSize="small" />}
          onClick={onBulkMarkUnpaid}
          disabled={isUnpaidPending}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
        >
          Fizetésre vár
        </Button>

        <Button
          variant="outlined"
          color="info"
          size="small"
          startIcon={<PreparedIcon fontSize="small" />}
          onClick={onBulkMarkPrepared}
          disabled={isPreparedPending}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
        >
          Előkészítve
        </Button>

        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(usePaymentDueDate)}
              onChange={(e) => setUsePaymentDueDate(e.target.checked)}
              size="small"
              sx={{ '& .MuiSvgIcon-root': { fontSize: 16 } }}
            />
          }
          label="Fizetési határidő"
          sx={{
            fontSize: '0.7rem',
            mx: 0.5,
            '& .MuiFormControlLabel-label': { fontSize: '0.7rem' },
          }}
        />

        {!usePaymentDueDate && (
          <TextField
            label="Dátum"
            type="date"
            value={paymentDate}
            onChange={(e) => setPaymentDate(e.target.value)}
            size="small"
            sx={{
              minWidth: '120px',
              '& .MuiInputBase-input': { fontSize: '0.7rem', py: 0.5 },
              '& .MuiInputLabel-root': { fontSize: '0.7rem' },
            }}
            InputLabelProps={{ shrink: true }}
          />
        )}

        <Button
          variant="outlined"
          color="success"
          size="small"
          startIcon={<PaidIcon fontSize="small" />}
          onClick={onBulkMarkPaid}
          disabled={isPaidPending}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 0.75, minHeight: '28px' }}
        >
          Kifizetve
        </Button>
      </Stack>
    </Paper>
  );
};

export default InvoiceBulkActionBar;
