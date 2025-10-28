import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Pagination,
  MenuItem,
  InputAdornment,
  CircularProgress,
  Alert,
  Tooltip,
  IconButton,
  Button,
  Menu,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Sync as SyncIcon,
  ArrowDropDown as ArrowDropDownIcon,
} from '@mui/icons-material';
import { useBillingoSpendings, useTriggerBillingoSpendingsSync } from '../../hooks/useBillingo';
import { useToastContext } from '../../context/ToastContext';
import { BillingoSpending } from '../../types/api';

const BillingoSpendings: React.FC = () => {
  const { success: showSuccess, error: showError, warning: showWarning } = useToastContext();

  // Filters
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('all');
  const [paidFilter, setPaidFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Sync menu anchor
  const [syncMenuAnchor, setSyncMenuAnchor] = useState<null | HTMLElement>(null);

  // Query
  const { data, isLoading, error, refetch } = useBillingoSpendings({
    page,
    page_size: pageSize,
    ...(category !== 'all' && { category }),
    ...(paidFilter !== 'all' && { paid: paidFilter }),
    ...(search && { search }),
    ordering: '-invoice_date',
  });

  // Sync mutation
  const syncMutation = useTriggerBillingoSpendingsSync();

  const handleRefresh = () => {
    refetch();
    showSuccess('Adatok frissítve');
  };

  const handleSyncClick = (event: React.MouseEvent<HTMLElement>) => {
    setSyncMenuAnchor(event.currentTarget);
  };

  const handleSyncMenuClose = () => {
    setSyncMenuAnchor(null);
  };

  const handlePartialSync = (): void => {
    handleSyncMenuClose();
    syncMutation.mutate(false, {
      onSuccess: (result) => {
        if (result.spendings_processed === 0) {
          showWarning(
            'Nincs új adat',
            'Nem történt változás a költségekben'
          );
        } else {
          showSuccess(
            'Szinkronizálás sikeres',
            `${result.spendings_processed} költség szinkronizálva (${result.spendings_created} új, ${result.spendings_updated} frissítve)`
          );
        }
        void refetch();
      },
      onError: (err: Error) => {
        showError(
          'Szinkronizálási hiba',
          err.message || 'Ismeretlen hiba történt a szinkronizálás során'
        );
      },
    });
  };

  const handleFullSync = (): void => {
    handleSyncMenuClose();
    syncMutation.mutate(true, {
      onSuccess: (result) => {
        showSuccess(
          'Teljes szinkronizálás sikeres',
          `${result.spendings_processed} költség szinkronizálva (${result.spendings_created} új, ${result.spendings_updated} frissítve)`
        );
        void refetch();
      },
      onError: (err: Error) => {
        showError(
          'Teljes szinkronizálási hiba',
          err.message || 'Ismeretlen hiba történt a teljes szinkronizálás során'
        );
      },
    });
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'HUF',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('hu-HU');
  };

  const getCategoryColor = (category: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    const colors: Record<string, "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"> = {
      service: 'primary',
      stock: 'secondary',
      overheads: 'warning',
      advertisement: 'info',
      development: 'success',
      education_and_training: 'secondary',
      tangible_assets: 'error',
      other: 'default',
    };
    return colors[category] || 'default';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Billingo Költségek
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            startIcon={syncMutation.isPending ? <CircularProgress size={20} /> : <SyncIcon />}
            endIcon={<ArrowDropDownIcon />}
            onClick={handleSyncClick}
            disabled={syncMutation.isPending}
          >
            Szinkronizálás
          </Button>
          <Menu
            anchorEl={syncMenuAnchor}
            open={Boolean(syncMenuAnchor)}
            onClose={handleSyncMenuClose}
          >
            <MenuItem onClick={handlePartialSync}>
              <Stack>
                <Typography variant="body2">Részleges szinkronizálás</Typography>
                <Typography variant="caption" color="text.secondary">
                  Csak új vagy módosult költségek
                </Typography>
              </Stack>
            </MenuItem>
            <MenuItem onClick={handleFullSync}>
              <Stack>
                <Typography variant="body2">Teljes szinkronizálás</Typography>
                <Typography variant="caption" color="text.secondary">
                  Minden költség újraszinkronizálása
                </Typography>
              </Stack>
            </MenuItem>
          </Menu>
          <Tooltip title="Adatok frissítése">
            <IconButton onClick={handleRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center">
          <TextField
            placeholder="Keresés számlaszám, partner alapján..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ flexGrow: 1, minWidth: 250 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            select
            label="Kategória"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            sx={{ minWidth: 200 }}
          >
            <MenuItem value="all">Összes kategória</MenuItem>
            <MenuItem value="service">Szolgáltatás</MenuItem>
            <MenuItem value="stock">Készlet</MenuItem>
            <MenuItem value="overheads">Rezsiköltség</MenuItem>
            <MenuItem value="advertisement">Hirdetés</MenuItem>
            <MenuItem value="development">Fejlesztés</MenuItem>
            <MenuItem value="education_and_training">Oktatás és képzés</MenuItem>
            <MenuItem value="tangible_assets">Tárgyi eszköz</MenuItem>
            <MenuItem value="other">Egyéb</MenuItem>
          </TextField>

          <TextField
            select
            label="Fizetési státusz"
            value={paidFilter}
            onChange={(e) => setPaidFilter(e.target.value)}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="all">Összes</MenuItem>
            <MenuItem value="true">Fizetve</MenuItem>
            <MenuItem value="false">Függőben</MenuItem>
          </TextField>
        </Stack>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Hiba történt az adatok betöltése során: {error.message}
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Data Table */}
      {!isLoading && data && (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Számlaszám</TableCell>
                  <TableCell>Partner</TableCell>
                  <TableCell>Kategória</TableCell>
                  <TableCell>Számla dátuma</TableCell>
                  <TableCell>Esedékesség</TableCell>
                  <TableCell align="right">Összeg</TableCell>
                  <TableCell>Fizetési mód</TableCell>
                  <TableCell align="center">Státusz</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.results.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary" py={3}>
                        Nincs megjeleníthető költség
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  data.results.map((spending: BillingoSpending) => (
                    <TableRow key={spending.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {spending.invoice_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{spending.partner_name}</Typography>
                        {spending.partner_tax_code && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            {spending.partner_tax_code}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={spending.category_display}
                          color={getCategoryColor(spending.category)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(spending.invoice_date)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(spending.due_date)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {formatCurrency(spending.total_gross_local)}
                        </Typography>
                        {spending.currency !== 'HUF' && spending.total_gross != null && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            ({spending.total_gross.toLocaleString()} {spending.currency})
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {spending.payment_method.replace('_', ' ')}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={spending.is_paid ? 'Fizetve' : 'Függőben'}
                          color={spending.is_paid ? 'success' : 'warning'}
                          size="small"
                        />
                        {spending.paid_at && (
                          <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
                            {formatDate(spending.paid_at)}
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {data.count > pageSize && (
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={Math.ceil(data.count / pageSize)}
                page={page}
                onChange={(_, value) => setPage(value)}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          )}

          {/* Summary */}
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Összesen: {data.count} költség
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
};

export default BillingoSpendings;
