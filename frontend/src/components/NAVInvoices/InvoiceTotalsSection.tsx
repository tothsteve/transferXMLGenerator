import React from 'react';
import {
  Paper,
  Stack,
  Typography,
  IconButton,
  Collapse,
  Box,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

interface InvoiceTotals {
  inbound: {
    net: number;
    vat: number;
    gross: number;
    count: number;
  };
  outbound: {
    net: number;
    vat: number;
    gross: number;
    count: number;
  };
  total: {
    net: number;
    vat: number;
    gross: number;
    count: number;
  };
}

interface InvoiceTotalsSectionProps {
  totals: InvoiceTotals | null;
  selectedCount: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
  formatAmount: (amount: number, currency: string) => string;
}

const InvoiceTotalsSection: React.FC<InvoiceTotalsSectionProps> = ({
  totals,
  selectedCount,
  collapsed,
  onToggleCollapse,
  formatAmount,
}) => {
  if (totals === null) {
    return null;
  }

  return (
    <Paper
      elevation={1}
      sx={{
        p: 1,
        mb: 0.5,
        bgcolor: 'primary.50',
        border: '1px solid',
        borderColor: 'primary.200',
      }}
    >
      <Stack spacing={0.5}>
        {/* Header with collapse button */}
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ minHeight: '24px' }}
        >
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontSize: '0.7rem', fontWeight: 'medium' }}
          >
            {selectedCount > 0
              ? `${selectedCount} kiválasztott számla összesen:`
              : `${totals.total.count} szűrt számla összesen:`}
          </Typography>
          <IconButton
            size="small"
            onClick={onToggleCollapse}
            sx={{ p: 0.25, '& .MuiSvgIcon-root': { fontSize: 16 } }}
          >
            {collapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
          </IconButton>
        </Stack>

        {/* Collapsible direction-specific totals - Compact Table Design */}
        <Collapse in={!collapsed}>
          <Box
            sx={{
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              overflow: 'hidden',
              mt: 0.5,
            }}
          >
            {/* Table Header */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: '100px 1fr 1fr 1fr',
                gap: 0.5,
                bgcolor: 'grey.50',
                p: 0.5,
                borderBottom: '1px solid',
                borderBottomColor: 'divider',
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.65rem' }}>
                Irány
              </Typography>
              <Typography
                variant="caption"
                sx={{ fontWeight: 'bold', fontSize: '0.65rem', textAlign: 'center' }}
              >
                Nettó
              </Typography>
              <Typography
                variant="caption"
                sx={{ fontWeight: 'bold', fontSize: '0.65rem', textAlign: 'center' }}
              >
                ÁFA
              </Typography>
              <Typography
                variant="caption"
                sx={{ fontWeight: 'bold', fontSize: '0.65rem', textAlign: 'center' }}
              >
                Bruttó
              </Typography>
            </Box>

            {/* Outbound Row */}
            {totals.outbound.count > 0 && (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '100px 1fr 1fr 1fr',
                  gap: 0.5,
                  p: 0.5,
                  borderBottom: totals.inbound.count > 0 ? '1px solid' : 'none',
                  borderBottomColor: 'divider',
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              >
                <Typography
                  variant="caption"
                  color="primary.main"
                  sx={{ fontSize: '0.65rem', fontWeight: 'medium' }}
                >
                  Kimenő ({totals.outbound.count})
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    textAlign: 'center',
                    color: 'success.main',
                    fontWeight: 'medium',
                  }}
                >
                  {formatAmount(totals.outbound.net, 'HUF')}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    textAlign: 'center',
                    color: 'warning.main',
                    fontWeight: 'medium',
                  }}
                >
                  {formatAmount(totals.outbound.vat, 'HUF')}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    textAlign: 'center',
                    color: 'primary.main',
                    fontWeight: 'bold',
                  }}
                >
                  {formatAmount(totals.outbound.gross, 'HUF')}
                </Typography>
              </Box>
            )}

            {/* Inbound Row */}
            {totals.inbound.count > 0 && (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '100px 1fr 1fr 1fr',
                  gap: 0.5,
                  p: 0.5,
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              >
                <Typography
                  variant="caption"
                  color="secondary.main"
                  sx={{ fontSize: '0.65rem', fontWeight: 'medium' }}
                >
                  Bejövő ({totals.inbound.count})
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    textAlign: 'center',
                    color: 'success.main',
                    fontWeight: 'medium',
                  }}
                >
                  {formatAmount(totals.inbound.net, 'HUF')}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    textAlign: 'center',
                    color: 'warning.main',
                    fontWeight: 'medium',
                  }}
                >
                  {formatAmount(totals.inbound.vat, 'HUF')}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.65rem',
                    textAlign: 'center',
                    color: 'secondary.main',
                    fontWeight: 'bold',
                  }}
                >
                  {formatAmount(totals.inbound.gross, 'HUF')}
                </Typography>
              </Box>
            )}
          </Box>
        </Collapse>
      </Stack>
    </Paper>
  );
};

export default InvoiceTotalsSection;
