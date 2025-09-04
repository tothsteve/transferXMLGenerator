import React, { useState } from 'react';
import {
  Container,
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
  IconButton,
  Chip,
  Stack,
  Switch,
  FormControlLabel,
  Tooltip,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
  Description as DescriptionIcon,
  SwapHoriz as SwapHorizIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import {
  useBatches,
  useMarkBatchUsedInBank,
  useMarkBatchUnusedInBank,
  useDownloadBatchXml,
  useDeleteBatch,
} from '../../hooks/api';
import { TransferBatch } from '../../types/api';

const BatchManager: React.FC = () => {
  const [downloadingBatchId, setDownloadingBatchId] = useState<number | null>(null);
  const { data: batchesData, isLoading, error } = useBatches();
  const markUsedMutation = useMarkBatchUsedInBank();
  const markUnusedMutation = useMarkBatchUnusedInBank();
  const downloadMutation = useDownloadBatchXml();
  const deleteMutation = useDeleteBatch();

  const batches = batchesData?.results || [];

  const handleUsageToggle = async (batch: TransferBatch) => {
    try {
      if (batch.used_in_bank) {
        await markUnusedMutation.mutateAsync(batch.id);
      } else {
        await markUsedMutation.mutateAsync(batch.id);
      }
    } catch (error) {
      console.error('Error updating batch usage:', error);
    }
  };

  const handleDownload = async (batch: TransferBatch) => {
    try {
      setDownloadingBatchId(batch.id);
      const response = await downloadMutation.mutateAsync(batch.id);
      
      // Determine file type based on batch name
      const isKHExport = batch.name.includes('KH Export');
      const mimeType = isKHExport ? 'text/csv; charset=utf-8' : 'application/xml';
      const fileExtension = isKHExport ? 'csv' : 'xml';
      
      // Create download link
      const blob = new Blob([response.data], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = batch.xml_filename || `batch_${batch.id}.${fileExtension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading file:', error);
    } finally {
      setDownloadingBatchId(null);
    }
  };

  const handleDelete = async (batch: TransferBatch) => {
    if (!window.confirm(`Biztosan törölni szeretnéd a(z) "${batch.name}" köteget? Ez a művelet nem vonható vissza.`)) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(batch.id);
    } catch (error) {
      console.error('Error deleting batch:', error);
      alert('Hiba történt a köteg törlése során.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('hu-HU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatAmount = (amount: string) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'HUF',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">
          Hiba történt a kötegek betöltése során.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
          <DescriptionIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            Kötegek kezelése
          </Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">
          Itt kezelheted a generált kötegeket, letöltheted őket, és jelölheted, hogy fel lettek-e töltve az internetbankba.
        </Typography>
      </Box>

      {batches.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <SwapHorizIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Nincs még generált köteg
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Az első fájl generálás után itt jelennek meg a kötegek.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Köteg neve</strong></TableCell>
                  <TableCell><strong>Utalások száma</strong></TableCell>
                  <TableCell><strong>Összeg</strong></TableCell>
                  <TableCell><strong>Generálás dátuma</strong></TableCell>
                  <TableCell><strong>Bank státusz</strong></TableCell>
                  <TableCell><strong>Felhasználás dátuma</strong></TableCell>
                  <TableCell align="center"><strong>Műveletek</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {batches.map((batch) => (
                  <TableRow key={batch.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {batch.name}
                      </Typography>
                      {batch.description && (
                        <Typography variant="caption" color="text.secondary">
                          {batch.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={`${batch.transfer_count} utalás`} 
                        size="small" 
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {formatAmount(batch.total_amount)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <AccessTimeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {batch.xml_generated_at ? formatDate(batch.xml_generated_at) : 'N/A'}
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={batch.used_in_bank ? <CheckCircleIcon /> : <AccessTimeIcon />}
                        label={batch.used_in_bank ? 'Felhasználva' : 'Várakozik'}
                        color={batch.used_in_bank ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {batch.bank_usage_date ? (
                        <Typography variant="body2" color="success.main">
                          {formatDate(batch.bank_usage_date)}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Tooltip title="Letöltés">
                          <span>
                            <IconButton
                              size="small"
                              onClick={() => handleDownload(batch)}
                              disabled={downloadingBatchId === batch.id}
                              color="primary"
                            >
                              {downloadingBatchId === batch.id ? (
                                <CircularProgress size={20} />
                              ) : (
                                <DownloadIcon />
                              )}
                            </IconButton>
                          </span>
                        </Tooltip>
                        
                        <Tooltip title="Köteg törlése">
                          <span>
                            <IconButton
                              size="small"
                              onClick={() => handleDelete(batch)}
                              disabled={deleteMutation.isPending}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </span>
                        </Tooltip>
                        
                        <Tooltip title={batch.used_in_bank ? 'Nem felhasználtként jelölés' : 'Felhasználtként jelölés'}>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={batch.used_in_bank}
                                onChange={() => handleUsageToggle(batch)}
                                disabled={markUsedMutation.isPending || markUnusedMutation.isPending}
                                size="small"
                              />
                            }
                            label=""
                            sx={{ m: 0 }}
                          />
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      )}
    </Container>
  );
};

export default BatchManager;