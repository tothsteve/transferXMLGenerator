import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Stack,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Add as AddIcon,
  AttachMoney as AttachMoneyIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { PDFProcessingResult } from './PDFImportWizard';

interface ReviewStepProps {
  previewData: PDFProcessingResult;
  onBack: () => void;
  onConfirm: () => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({ previewData, onBack, onConfirm }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'HUF',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Box sx={{ p: { xs: 2, sm: 3 }, maxWidth: '100%', mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h6" component="h2" fontWeight="bold" gutterBottom>
          Adatok Áttekintése
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ display: { xs: 'none', sm: 'block' } }}
        >
          {previewData.template_updated
            ? 'Ellenőrizze a kinyert tranzakciókat és erősítse meg a sablon frissítését'
            : 'Ellenőrizze a kinyert tranzakciókat és erősítse meg a sablon létrehozását'}
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: 'repeat(2, 1fr)',
            sm: 'repeat(4, 1fr)',
          },
          gap: { xs: 1.5, sm: 2 },
          mb: 3,
        }}
      >
        <Card elevation={1}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2 }, '&:last-child': { pb: { xs: 1.5, sm: 2 } } }}>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              alignItems="center"
              spacing={{ xs: 1, sm: 2 }}
              textAlign={{ xs: 'center', sm: 'left' }}
            >
              <Avatar
                sx={{
                  bgcolor: 'primary.main',
                  width: { xs: 32, sm: 40 },
                  height: { xs: 32, sm: 40 },
                }}
              >
                <DescriptionIcon fontSize="small" />
              </Avatar>
              <Box>
                <Typography
                  variant="h5"
                  fontWeight="bold"
                  color="primary"
                  sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                >
                  {previewData.transactions_processed}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Tranzakció
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Card elevation={1}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2 }, '&:last-child': { pb: { xs: 1.5, sm: 2 } } }}>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              alignItems="center"
              spacing={{ xs: 1, sm: 2 }}
              textAlign={{ xs: 'center', sm: 'left' }}
            >
              <Avatar
                sx={{
                  bgcolor: 'success.main',
                  width: { xs: 32, sm: 40 },
                  height: { xs: 32, sm: 40 },
                }}
              >
                <CheckCircleIcon fontSize="small" />
              </Avatar>
              <Box>
                <Typography
                  variant="h5"
                  fontWeight="bold"
                  color="success.main"
                  sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                >
                  {previewData.beneficiaries_matched}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Meglévő
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Card elevation={1}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2 }, '&:last-child': { pb: { xs: 1.5, sm: 2 } } }}>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              alignItems="center"
              spacing={{ xs: 1, sm: 2 }}
              textAlign={{ xs: 'center', sm: 'left' }}
            >
              <Avatar
                sx={{
                  bgcolor: 'warning.main',
                  width: { xs: 32, sm: 40 },
                  height: { xs: 32, sm: 40 },
                }}
              >
                <AddIcon fontSize="small" />
              </Avatar>
              <Box>
                <Typography
                  variant="h5"
                  fontWeight="bold"
                  color="warning.main"
                  sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                >
                  {previewData.beneficiaries_created}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Új
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Card elevation={1}>
          <CardContent sx={{ p: { xs: 1.5, sm: 2 }, '&:last-child': { pb: { xs: 1.5, sm: 2 } } }}>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              alignItems="center"
              spacing={{ xs: 1, sm: 2 }}
              textAlign={{ xs: 'center', sm: 'left' }}
            >
              <Avatar
                sx={{
                  bgcolor: 'secondary.main',
                  width: { xs: 32, sm: 40 },
                  height: { xs: 32, sm: 40 },
                }}
              >
                <AttachMoneyIcon fontSize="small" />
              </Avatar>
              <Box>
                <Typography
                  variant="h6"
                  fontWeight="bold"
                  color="secondary.main"
                  sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                >
                  {formatCurrency(previewData.total_amount)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Összesen
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Box>

      {/* Template Info */}
      <Alert
        severity={previewData.template_updated ? 'info' : 'success'}
        sx={{ mb: 4 }}
        icon={previewData.template_updated ? <InfoIcon /> : <DescriptionIcon />}
      >
        <AlertTitle>
          {previewData.template_updated ? 'Frissítendő sablon' : 'Létrehozandó sablon'}
        </AlertTitle>
        <Typography variant="body2" component="div">
          <strong>Név:</strong> {previewData.template.name}
        </Typography>
        <Typography variant="body2" component="div">
          <strong>Kedvezményezettek száma:</strong> {previewData.template.beneficiary_count}
        </Typography>
        {previewData.template_updated && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            A rendszer észlelte, hogy már létezik sablon ugyanezekkel a kedvezményezettekkel. Az
            összegek és közlemények frissítésre kerülnek az új értékekkel.
          </Typography>
        )}
      </Alert>

      {/* Consolidation Alerts */}
      {previewData.consolidations && previewData.consolidations.length > 0 && (
        <Alert severity="warning" sx={{ mb: 4 }} icon={<WarningIcon />}>
          <AlertTitle>Tranzakciók összevonása</AlertTitle>
          <List dense>
            {previewData.consolidations.map((msg, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.25 }}>
                <ListItemText primary={`• ${msg}`} />
              </ListItem>
            ))}
          </List>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Az azonos kedvezményezetthez tartozó tranzakciók automatikusan összevonásra kerültek.
          </Typography>
        </Alert>
      )}

      {/* Transaction Table */}
      <Paper elevation={1} sx={{ mb: 3 }}>
        <Box sx={{ p: { xs: 2, sm: 3 }, borderBottom: 1, borderColor: 'divider' }}>
          <Typography
            variant="h6"
            fontWeight={600}
            sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}
          >
            Kinyert Tranzakciók
          </Typography>
        </Box>
        <TableContainer sx={{ overflowX: 'auto' }}>
          <Table
            sx={{
              tableLayout: { xs: 'auto', sm: 'fixed' },
              minWidth: { xs: 650, sm: '100%' },
            }}
            size="small"
          >
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: { sm: '25%' }, fontWeight: 600, fontSize: '0.8rem' }}>
                  Kedvezményezett
                </TableCell>
                <TableCell sx={{ width: { sm: '22%' }, fontWeight: 600, fontSize: '0.8rem' }}>
                  Számlaszám
                </TableCell>
                <TableCell
                  align="right"
                  sx={{ width: { sm: '15%' }, fontWeight: 600, fontSize: '0.8rem' }}
                >
                  Összeg
                </TableCell>
                <TableCell sx={{ width: { sm: '25%' }, fontWeight: 600, fontSize: '0.8rem' }}>
                  Közlemény
                </TableCell>
                <TableCell
                  align="center"
                  sx={{ width: { sm: '13%' }, fontWeight: 600, fontSize: '0.8rem' }}
                >
                  Állapot
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {previewData.preview.map((transaction, index) => (
                <TableRow
                  key={index}
                  hover
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell sx={{ py: 1.5 }}>
                    <Typography variant="body2" fontWeight={500} sx={{ fontSize: '0.85rem' }}>
                      {transaction.beneficiary_name}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.7rem',
                        wordBreak: 'break-all',
                        lineHeight: 1.2,
                      }}
                    >
                      {transaction.account_number}
                    </Typography>
                  </TableCell>
                  <TableCell align="right" sx={{ py: 1.5 }}>
                    <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.85rem' }}>
                      {formatCurrency(transaction.amount)}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '0.8rem',
                      }}
                      title={transaction.remittance_info || '-'}
                    >
                      {transaction.remittance_info || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center" sx={{ py: 1.5 }}>
                    {transaction.beneficiary_id ? (
                      <Chip
                        label="Meglévő"
                        color="success"
                        size="small"
                        sx={{
                          fontSize: '0.7rem',
                          height: 20,
                          '& .MuiChip-label': { px: 1 },
                          '& .MuiChip-icon': { fontSize: 12 },
                        }}
                        icon={<CheckCircleIcon />}
                      />
                    ) : (
                      <Chip
                        label="Új"
                        color="warning"
                        size="small"
                        sx={{
                          fontSize: '0.7rem',
                          height: 20,
                          '& .MuiChip-label': { px: 1 },
                          '& .MuiChip-icon': { fontSize: 12 },
                        }}
                        icon={<AddIcon />}
                      />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Info Box */}
      <Alert
        severity="info"
        sx={{ mb: 3, display: { xs: 'none', md: 'flex' } }}
        icon={<InfoIcon />}
      >
        <AlertTitle sx={{ mb: 1, fontSize: '0.9rem' }}>Tudnivalók</AlertTitle>
        <Box component="ul" sx={{ m: 0, pl: 1, fontSize: '0.8rem', '& li': { mb: 0.5 } }}>
          {previewData.template_updated ? (
            <>
              <li>A meglévő sablon összegei és közleményei frissülnek az új PDF adatokkal</li>
              <li>A kedvezményezettek listája változatlan marad</li>
              <li>A frissítés után közvetlenül használhatja az utalások generálásához</li>
            </>
          ) : (
            <>
              <li>A sablon létrehozása után közvetlenül használhatja az utalások generálásához</li>
              <li>A meglévő kedvezményezettek nem kerülnek duplikálásra</li>
              <li>Az összegek és közlemények módosíthatók az utalás létrehozásakor</li>
            </>
          )}
        </Box>
      </Alert>

      {/* Action Buttons */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          pt: 1,
          gap: 2,
          flexDirection: { xs: 'column', sm: 'row' },
        }}
      >
        <Button
          onClick={onBack}
          variant="outlined"
          size="medium"
          sx={{ width: { xs: '100%', sm: 'auto' } }}
        >
          ← Vissza
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          size="medium"
          color={previewData.template_updated ? 'primary' : 'success'}
          startIcon={<CheckCircleIcon />}
          sx={{ width: { xs: '100%', sm: 'auto' }, minWidth: { sm: 200 } }}
        >
          {previewData.template_updated ? 'Jóváhagyás és Folytatás' : 'Jóváhagyás és Folytatás'}
        </Button>
      </Box>
    </Box>
  );
};
