import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Button,
  IconButton,
  Chip,
  Stack,
  FormControlLabel,
  Switch,
  Checkbox,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { useProductPrices, useCreateProductPrice, useUpdateProductPrice, useDeleteProductPrice } from '../../hooks/api';
import { ProductPrice } from '../../types/api';
import { useToastContext } from '../../context/ToastContext';
import { useDebounce } from '../../hooks/useDebounce';
import LoadingSpinner from '../UI/LoadingSpinner';

const ProductPrices: React.FC = () => {
  const { success: showSuccess, error: showError } = useToastContext();

  const [searchTerm, setSearchTerm] = useState('');
  const [validOnly, setValidOnly] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [editForm, setEditForm] = useState<Partial<ProductPrice>>({});
  const [originalPriceBeforeCopy, setOriginalPriceBeforeCopy] = useState<ProductPrice | null>(null);
  const [isCopyMode, setIsCopyMode] = useState(false);

  const { data, isLoading, refetch } = useProductPrices({
    search: debouncedSearchTerm,
    valid_only: validOnly,
    page: page + 1,
    page_size: rowsPerPage,
  });
  const createMutation = useCreateProductPrice();
  const updateMutation = useUpdateProductPrice();
  const deleteMutation = useDeleteProductPrice();

  const handleStartAdd = () => {
    setIsAdding(true);
    setEditForm({
      product_value: '',
      product_description: '',
      is_inventory_managed: true,  // Default: készletkezelt = true
      uom: 'EA',                    // Default: UOM(EN) = EA
      uom_hun: 'db',                // Default: UOM(HU) = db
      purchase_price_usd: '',
      purchase_price_huf: '',       // Default: null (empty)
      markup: '',
      sales_price_huf: '',          // Default: null (empty)
      cap_disp: '',
      valid_from: '',
      valid_to: '',
    });
  };

  const handleCancelEdit = async () => {
    // If we have an original price that was modified during copy, revert it
    if (originalPriceBeforeCopy && isCopyMode) {
      try {
        await updateMutation.mutateAsync({
          id: originalPriceBeforeCopy.id,
          data: {
            ...originalPriceBeforeCopy,
          } as Partial<ProductPrice>,
        });
        void refetch();
      } catch (error) {
        showError('Hiba történt az eredeti sor visszaállítása során');
      }
    }

    setOriginalPriceBeforeCopy(null);
    setIsCopyMode(false);
    setEditingId(null);
    setIsAdding(false);
    setEditForm({});
  };

  const handleSaveNew = async () => {
    if (!editForm.product_value?.trim() || !editForm.product_description?.trim()) {
      showError('Termék kód és leírás kötelező');
      return;
    }

    try {
      await createMutation.mutateAsync({
        product_value: editForm.product_value,
        product_description: editForm.product_description,
        uom: editForm.uom || null,
        uom_hun: editForm.uom_hun || null,
        purchase_price_usd: editForm.purchase_price_usd || null,
        purchase_price_huf: editForm.purchase_price_huf || null,
        markup: editForm.markup || null,
        sales_price_huf: editForm.sales_price_huf || null,
        cap_disp: editForm.cap_disp || null,
        is_inventory_managed: editForm.is_inventory_managed || false,
        valid_from: editForm.valid_from || null,
        valid_to: editForm.valid_to || null,
      });
      showSuccess('Termék ár sikeresen létrehozva');
      setOriginalPriceBeforeCopy(null); // Clear backup on successful save
      handleCancelEdit();
      void refetch();
    } catch (error) {
      showError('Hiba történt a létrehozás során');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingId || !editForm.product_value || !editForm.product_description || editForm.is_inventory_managed === undefined) return;

    try {
      // Update the original row (close its validity)
      await updateMutation.mutateAsync({
        id: editingId,
        data: {
          product_value: editForm.product_value,
          product_description: editForm.product_description,
          uom: editForm.uom || null,
          uom_hun: editForm.uom_hun || null,
          purchase_price_usd: editForm.purchase_price_usd || null,
          purchase_price_huf: editForm.purchase_price_huf || null,
          markup: editForm.markup || null,
          sales_price_huf: editForm.sales_price_huf || null,
          cap_disp: editForm.cap_disp || null,
          is_inventory_managed: editForm.is_inventory_managed,
          valid_from: editForm.valid_from || null,
          valid_to: editForm.valid_to || null,
        } as Partial<ProductPrice>,
      });

      // If in copy mode, open new add form with copied data
      if (isCopyMode && editForm.valid_to) {
        const validToDate = new Date(editForm.valid_to);
        validToDate.setDate(validToDate.getDate() + 1);
        const isoString = validToDate.toISOString().split('T');
        const newValidFrom = isoString[0] || '';

        setEditingId(null);
        setIsAdding(true);
        setEditForm({
          product_value: editForm.product_value,
          product_description: editForm.product_description,
          uom: editForm.uom,
          uom_hun: editForm.uom_hun,
          purchase_price_usd: editForm.purchase_price_usd,
          purchase_price_huf: editForm.purchase_price_huf,
          markup: editForm.markup,
          sales_price_huf: editForm.sales_price_huf,
          cap_disp: editForm.cap_disp,
          is_inventory_managed: editForm.is_inventory_managed,
          valid_from: newValidFrom,
          valid_to: '',
        });
        setOriginalPriceBeforeCopy(null);
        setIsCopyMode(false);
        showSuccess('Előző ár lezárva. Most szerkessze az új árat és mentse el.');
      } else {
        showSuccess('Termék ár sikeresen frissítve');
        setEditingId(null);
        setIsAdding(false);
        setEditForm({});
        setOriginalPriceBeforeCopy(null);
        setIsCopyMode(false);
      }

      void refetch();
    } catch (error) {
      showError('Hiba történt a frissítés során');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Biztosan törölni szeretné ezt a termék árat?')) return;

    try {
      await deleteMutation.mutateAsync(id);
      showSuccess('Termék ár sikeresen törölve');
      void refetch();
    } catch (error) {
      showError('Hiba történt a törlés során');
    }
  };

  const handleCopyWithNewValidity = (price: ProductPrice) => {
    // Save the original price for potential revert
    setOriginalPriceBeforeCopy({ ...price });

    // Calculate suggested valid_to for old row (today)
    const todayIsoString = new Date().toISOString().split('T');
    const suggestedValidTo = todayIsoString[0] || '';

    // Start editing the ORIGINAL row with suggested valid_to
    // User can modify this before confirming
    setEditingId(price.id);
    setEditForm({
      ...price,
      valid_to: price.valid_to || suggestedValidTo, // Suggest today if no valid_to
    });

    // Set copy mode flag
    setIsCopyMode(true);

    showSuccess('Állítsa be az érvényesség végét, majd mentse. Új sor létrehozásra kerül.');
  };

  const handleChangePage = (_event: unknown, newPage: number): void => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (): void => {
    setPage(0);
  };

  if (isLoading) return <LoadingSpinner />;

  const prices = data?.results || [];
  const totalCount = data?.count || 0;

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">CONMED árak</Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControlLabel
            control={<Switch checked={validOnly} onChange={(e) => setValidOnly(e.target.checked)} />}
            label="Csak érvényes rekordok"
          />
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleStartAdd} disabled={isAdding}>
            Új termék ár
          </Button>
        </Stack>
      </Stack>

      <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 250px)' }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ minWidth: 120 }}>
                <TextField
                  size="small"
                  placeholder="Termék kód/leírás..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    handleSearchChange();
                  }}
                  fullWidth
                />
              </TableCell>
              <TableCell sx={{ minWidth: 200 }}>Leírás</TableCell>
              <TableCell>UOM (EN)</TableCell>
              <TableCell>UOM (HU)</TableCell>
              <TableCell>Beszer. ár USD</TableCell>
              <TableCell>Beszer. ár HUF</TableCell>
              <TableCell>Felár %</TableCell>
              <TableCell>Eladási ár HUF</TableCell>
              <TableCell>Cap/Disp</TableCell>
              <TableCell>Készlet</TableCell>
              <TableCell>Érvényes tól</TableCell>
              <TableCell>Érvényes ig</TableCell>
              <TableCell>Állapot</TableCell>
              <TableCell align="right">Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isAdding && (
              <TableRow>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.product_value || ''}
                    onChange={(e) => setEditForm({ ...editForm, product_value: e.target.value })}
                    placeholder="Kód"
                    required
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.product_description || ''}
                    onChange={(e) => setEditForm({ ...editForm, product_description: e.target.value })}
                    placeholder="Leírás"
                    required
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.uom || ''}
                    onChange={(e) => setEditForm({ ...editForm, uom: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.uom_hun || ''}
                    onChange={(e) => setEditForm({ ...editForm, uom_hun: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.purchase_price_usd || ''}
                    onChange={(e) => setEditForm({ ...editForm, purchase_price_usd: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.purchase_price_huf || ''}
                    onChange={(e) => setEditForm({ ...editForm, purchase_price_huf: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.markup || ''}
                    onChange={(e) => setEditForm({ ...editForm, markup: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.sales_price_huf || ''}
                    onChange={(e) => setEditForm({ ...editForm, sales_price_huf: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={editForm.cap_disp || ''}
                    onChange={(e) => setEditForm({ ...editForm, cap_disp: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <Checkbox
                    checked={editForm.is_inventory_managed || false}
                    onChange={(e) => setEditForm({ ...editForm, is_inventory_managed: e.target.checked })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="date"
                    value={editForm.valid_from || ''}
                    onChange={(e) => setEditForm({ ...editForm, valid_from: e.target.value })}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="date"
                    value={editForm.valid_to || ''}
                    onChange={(e) => setEditForm({ ...editForm, valid_to: e.target.value })}
                  />
                </TableCell>
                <TableCell>-</TableCell>
                <TableCell align="right">
                  <IconButton size="small" color="primary" onClick={handleSaveNew}>
                    <SaveIcon />
                  </IconButton>
                  <IconButton size="small" onClick={handleCancelEdit}>
                    <CancelIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            )}
            {prices.map((price) =>
              editingId === price.id ? (
                <TableRow key={price.id}>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.product_value || ''}
                      onChange={(e) => setEditForm({ ...editForm, product_value: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.product_description || ''}
                      onChange={(e) => setEditForm({ ...editForm, product_description: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.uom || ''}
                      onChange={(e) => setEditForm({ ...editForm, uom: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.uom_hun || ''}
                      onChange={(e) => setEditForm({ ...editForm, uom_hun: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.purchase_price_usd || ''}
                      onChange={(e) => setEditForm({ ...editForm, purchase_price_usd: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.purchase_price_huf || ''}
                      onChange={(e) => setEditForm({ ...editForm, purchase_price_huf: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.markup || ''}
                      onChange={(e) => setEditForm({ ...editForm, markup: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.sales_price_huf || ''}
                      onChange={(e) => setEditForm({ ...editForm, sales_price_huf: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.cap_disp || ''}
                      onChange={(e) => setEditForm({ ...editForm, cap_disp: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <Checkbox
                      checked={editForm.is_inventory_managed || false}
                      onChange={(e) => setEditForm({ ...editForm, is_inventory_managed: e.target.checked })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="date"
                      value={editForm.valid_from || ''}
                      onChange={(e) => setEditForm({ ...editForm, valid_from: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="date"
                      value={editForm.valid_to || ''}
                      onChange={(e) => setEditForm({ ...editForm, valid_to: e.target.value })}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={price.is_valid ? 'Érvényes' : 'Lejárt'} color={price.is_valid ? 'success' : 'default'} size="small" />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" color="primary" onClick={handleSaveEdit}>
                      <SaveIcon />
                    </IconButton>
                    <IconButton size="small" onClick={handleCancelEdit}>
                      <CancelIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ) : (
                <TableRow key={price.id}>
                  <TableCell>{price.product_value}</TableCell>
                  <TableCell>{price.product_description}</TableCell>
                  <TableCell>{price.uom || '-'}</TableCell>
                  <TableCell>{price.uom_hun || '-'}</TableCell>
                  <TableCell>{price.purchase_price_usd ? `$${price.purchase_price_usd}` : '-'}</TableCell>
                  <TableCell>{price.purchase_price_huf ? `${price.purchase_price_huf} Ft` : '-'}</TableCell>
                  <TableCell>{price.markup || '-'}</TableCell>
                  <TableCell>{price.sales_price_huf ? `${price.sales_price_huf} Ft` : '-'}</TableCell>
                  <TableCell>{price.cap_disp || '-'}</TableCell>
                  <TableCell>{price.is_inventory_managed ? '✓' : '-'}</TableCell>
                  <TableCell>{price.valid_from || '-'}</TableCell>
                  <TableCell>{price.valid_to || '-'}</TableCell>
                  <TableCell>
                    <Chip label={price.is_valid ? 'Érvényes' : 'Lejárt'} color={price.is_valid ? 'success' : 'default'} size="small" />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => { setEditingId(price.id); setEditForm(price); }}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" color="primary" onClick={() => handleCopyWithNewValidity(price)}>
                      <ContentCopyIcon />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDelete(price.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              )
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={totalCount}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[10, 25, 50, 100]}
        labelRowsPerPage="Sorok száma:"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
      />

      {prices.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">Nincs megjeleníthető termék ár</Typography>
        </Box>
      )}
    </Box>
  );
};

export default ProductPrices;
