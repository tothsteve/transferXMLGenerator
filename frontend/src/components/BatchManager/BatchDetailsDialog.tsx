import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
  IconButton,
  Divider,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  AccountBalance as AccountBalanceIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
  AttachMoney as AttachMoneyIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { TransferBatch } from '../../types/api';

interface BatchDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  batch: TransferBatch | null;
  isLoading?: boolean;
}

const BatchDetailsDialog: React.FC<BatchDetailsDialogProps> = ({
  open,
  onClose,
  batch,
  isLoading = false,
}) => {

  const formatAmount = (amount: string) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'HUF',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('hu-HU');
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('hu-HU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <DescriptionIcon color="primary" />
            <Box>
              <Typography variant="h5" component="div">
                {batch?.name || 'Betöltés...'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Köteg részletei
              </Typography>
            </Box>
          </Stack>
          <IconButton onClick={onClose} size="large">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent dividers>
        {isLoading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress />
          </Box>
        ) : batch ? (
          <>
            {/* Batch Summary */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Összesítő adatok
                </Typography>
            <Stack direction="row" spacing={4} flexWrap="wrap">
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Utalások száma
                </Typography>
                <Chip 
                  label={`${batch.transfer_count} utalás`}
                  color="primary"
                  variant="outlined"
                />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Teljes összeg
                </Typography>
                <Typography variant="h6" color="primary">
                  {formatAmount(batch.total_amount)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Formátum
                </Typography>
                <Chip 
                  label={batch.batch_format_display?.replace('SEPA XML', 'XML') || batch.batch_format || 'XML'}
                  size="small"
                  color="info"
                />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Generálás dátuma
                </Typography>
                <Typography variant="body1">
                  {batch.xml_generated_at ? formatDateTime(batch.xml_generated_at) : 'N/A'}
                </Typography>
              </Box>
            </Stack>
            
            {batch.description && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Leírás
                </Typography>
                <Typography variant="body1">
                  {batch.description}
                </Typography>
              </>
            )}
          </CardContent>
        </Card>

        {/* Transfer Details */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Utalások részletei ({batch.transfers?.length || 0})
            </Typography>
            
            {batch.transfers && batch.transfers.length > 0 ? (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Kedvezményezett</strong></TableCell>
                      <TableCell><strong>Számla</strong></TableCell>
                      <TableCell align="right"><strong>Összeg</strong></TableCell>
                      <TableCell><strong>Teljesítés</strong></TableCell>
                      <TableCell><strong>Közlemény</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {batch.transfers.map((transfer, index) => (
                      <TableRow key={transfer.id} hover>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <PersonIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            <Typography variant="body2">
                              {transfer.beneficiary?.name || 'Ismeretlen kedvezményezett'}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <AccountBalanceIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            <Typography variant="body2" fontFamily="monospace">
                              {transfer.beneficiary?.account_number || 'N/A'}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="medium">
                            {formatAmount(transfer.amount)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <CalendarIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            <Typography variant="body2">
                              {formatDate(transfer.execution_date)}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              maxWidth: 200, 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                            title={transfer.remittance_info}
                          >
                            {transfer.remittance_info || '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box 
                sx={{ 
                  textAlign: 'center', 
                  py: 4,
                  color: 'text.secondary' 
                }}
              >
                <Typography variant="body2">
                  Nincsenek utalások ebben a kötegben
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
          </>
        ) : (
          <Box 
            sx={{ 
              textAlign: 'center', 
              py: 4,
              color: 'text.secondary' 
            }}
          >
            <Typography variant="body2">
              Hiba történt az adatok betöltése során
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Bezárás
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BatchDetailsDialog;