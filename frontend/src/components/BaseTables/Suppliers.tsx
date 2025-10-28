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
  TextField,
  Button,
  IconButton,
  Chip,
  Stack,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { useSuppliers, useCreateSupplier, useUpdateSupplier, useDeleteSupplier, useSupplierCategories, useSupplierTypes } from '../../hooks/api';
import { Supplier } from '../../types/api';
import { useToastContext } from '../../context/ToastContext';
import { useDebounce } from '../../hooks/useDebounce';
import LoadingSpinner from '../UI/LoadingSpinner';

// Compact TextField styling for tables with lots of data
const compactTextFieldSx = {
  '& .MuiInputBase-root': {
    fontSize: '0.75rem', // Smaller font size (12px)
    minHeight: '32px',
  },
  '& .MuiInputBase-input': {
    padding: '6px 8px', // Reduced padding
    fontSize: '0.75rem',
  },
  '& .MuiOutlinedInput-root': {
    '& fieldset': {
      borderColor: 'rgba(0, 0, 0, 0.12)',
    },
  },
};

const Suppliers: React.FC = () => {
  const { success: showSuccess, error: showError} = useToastContext();

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [validOnly, setValidOnly] = useState(true);
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const debouncedCategoryFilter = useDebounce(categoryFilter, 500);
  const debouncedTypeFilter = useDebounce(typeFilter, 500);

  // Editing state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Supplier>>({});
  const [originalSupplierBeforeCopy, setOriginalSupplierBeforeCopy] = useState<Supplier | null>(null);
  const [isCopyMode, setIsCopyMode] = useState(false);

  // API hooks
  const { data, isLoading, refetch } = useSuppliers({
    search: debouncedSearchTerm,
    category: debouncedCategoryFilter,
    type: debouncedTypeFilter,
    valid_only: validOnly,
  });
  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();

  // Fetch categories and types from API
  const { data: categoriesData } = useSupplierCategories();
  const { data: typesData } = useSupplierTypes();

  // Transform API data to dropdown format
  const categories = categoriesData?.results || [];
  const types = typesData?.results || [];

  const handleStartAdd = () => {
    setIsAdding(true);
    setEditForm({ partner_name: '', category: undefined, type: undefined, valid_from: '', valid_to: '' });
  };

  const handleStartEdit = (supplier: Supplier) => {
    setEditingId(supplier.id);
    setEditForm(supplier);
  };

  const handleCancelEdit = async () => {
    // If we have an original supplier that was modified during copy, revert it
    if (originalSupplierBeforeCopy && isCopyMode) {
      try {
        await updateMutation.mutateAsync({
          id: originalSupplierBeforeCopy.id,
          data: {
            ...originalSupplierBeforeCopy,
          } as Partial<Supplier>,
        });
        void refetch();
      } catch (error) {
        showError('Hiba történt az eredeti sor visszaállítása során');
      }
    }

    setOriginalSupplierBeforeCopy(null);
    setIsCopyMode(false);
    setEditingId(null);
    setIsAdding(false);
    setEditForm({});
  };

  const handleSaveNew = async () => {
    if (!editForm.partner_name?.trim()) {
      showError('Partner neve kötelező');
      return;
    }

    try {
      await createMutation.mutateAsync({
        partner_name: editForm.partner_name,
        category: editForm.category || null,
        type: editForm.type || null,
        valid_from: editForm.valid_from || null,
        valid_to: editForm.valid_to || null,
      });
      showSuccess('Beszállító sikeresen létrehozva');
      handleCancelEdit();
      void refetch();
    } catch (error) {
      showError('Hiba történt a létrehozás során');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingId || !editForm.partner_name) return;

    try {
      // Update the original row (close its validity if in copy mode)
      await updateMutation.mutateAsync({
        id: editingId,
        data: {
          partner_name: editForm.partner_name,
          category: editForm.category || null,
          type: editForm.type || null,
          valid_from: editForm.valid_from || null,
          valid_to: editForm.valid_to || null,
        } as Partial<Supplier>,
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
          partner_name: editForm.partner_name,
          category: editForm.category,
          type: editForm.type,
          valid_from: newValidFrom,
          valid_to: '',
        });
        setOriginalSupplierBeforeCopy(null);
        setIsCopyMode(false);
        showSuccess('Előző rekord lezárva. Most szerkessze az új rekordot és mentse el.');
      } else {
        showSuccess('Beszállító sikeresen frissítve');
        await handleCancelEdit();
      }

      void refetch();
    } catch (error) {
      showError('Hiba történt a frissítés során');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Biztosan törölni szeretné ezt a beszállítót?')) return;

    try {
      await deleteMutation.mutateAsync(id);
      showSuccess('Beszállító sikeresen törölve');
      void refetch();
    } catch (error) {
      showError('Hiba történt a törlés során');
    }
  };

  const handleCopyWithNewValidity = (supplier: Supplier) => {
    // Save the original supplier for potential revert
    setOriginalSupplierBeforeCopy({ ...supplier });

    // Calculate suggested valid_to for old row (today)
    const todayIsoString = new Date().toISOString().split('T');
    const suggestedValidTo = todayIsoString[0] || '';

    // Start editing the ORIGINAL row with suggested valid_to
    setEditingId(supplier.id);
    setEditForm({
      ...supplier,
      valid_to: supplier.valid_to || suggestedValidTo,
    });

    // Set copy mode flag
    setIsCopyMode(true);

    showSuccess('Állítsa be az érvényesség végét, majd mentse. Új sor létrehozásra kerül.');
  };

  if (isLoading) return <LoadingSpinner />;

  const suppliers = data?.results || [];

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Beszállítók</Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControlLabel
            control={<Switch checked={validOnly} onChange={(e) => setValidOnly(e.target.checked)} />}
            label="Csak érvényes rekordok"
          />
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleStartAdd} disabled={isAdding}>
            Új beszállító
          </Button>
        </Stack>
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ padding: '8px' }}>
                <TextField
                  size="small"
                  placeholder="Partner neve..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  fullWidth
                  sx={compactTextFieldSx}
                />
              </TableCell>
              <TableCell sx={{ padding: '8px' }}>
                <TextField
                  size="small"
                  placeholder="Kategória..."
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  fullWidth
                  sx={compactTextFieldSx}
                />
              </TableCell>
              <TableCell sx={{ padding: '8px' }}>
                <TextField
                  size="small"
                  placeholder="Típus..."
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  fullWidth
                  sx={compactTextFieldSx}
                />
              </TableCell>
              <TableCell sx={{ padding: '8px', fontSize: '0.75rem' }}>Érvényes tól</TableCell>
              <TableCell sx={{ padding: '8px', fontSize: '0.75rem' }}>Érvényes ig</TableCell>
              <TableCell sx={{ padding: '8px', fontSize: '0.75rem' }}>Állapot</TableCell>
              <TableCell align="right" sx={{ padding: '8px', fontSize: '0.75rem' }}>Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isAdding && (
              <TableRow>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    value={editForm.partner_name || ''}
                    onChange={(e) => setEditForm({ ...editForm, partner_name: e.target.value })}
                    placeholder="Partner neve"
                    fullWidth
                    required
                    sx={compactTextFieldSx}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Select
                    size="small"
                    value={editForm.category || ''}
                    onChange={(e) => setEditForm({ ...editForm, category: e.target.value ? Number(e.target.value) : undefined })}
                    displayEmpty
                    fullWidth
                    sx={{
                      fontSize: '0.75rem',
                      minHeight: '32px',
                      '& .MuiSelect-select': {
                        padding: '6px 8px',
                        fontSize: '0.75rem',
                      },
                    }}
                  >
                    <MenuItem value="" sx={{ fontSize: '0.75rem' }}>
                      <em>Kategória...</em>
                    </MenuItem>
                    {categories.map((cat) => (
                      <MenuItem key={cat.id} value={cat.id} sx={{ fontSize: '0.75rem' }}>
                        {cat.name}
                      </MenuItem>
                    ))}
                  </Select>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <Select
                    size="small"
                    value={editForm.type || ''}
                    onChange={(e) => setEditForm({ ...editForm, type: e.target.value ? Number(e.target.value) : undefined })}
                    displayEmpty
                    fullWidth
                    sx={{
                      fontSize: '0.75rem',
                      minHeight: '32px',
                      '& .MuiSelect-select': {
                        padding: '6px 8px',
                        fontSize: '0.75rem',
                      },
                    }}
                  >
                    <MenuItem value="" sx={{ fontSize: '0.75rem' }}>
                      <em>Típus...</em>
                    </MenuItem>
                    {types.map((type) => (
                      <MenuItem key={type.id} value={type.id} sx={{ fontSize: '0.75rem' }}>
                        {type.name}
                      </MenuItem>
                    ))}
                  </Select>
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    type="date"
                    value={editForm.valid_from || ''}
                    onChange={(e) => setEditForm({ ...editForm, valid_from: e.target.value })}
                    fullWidth
                    sx={compactTextFieldSx}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px' }}>
                  <TextField
                    size="small"
                    type="date"
                    value={editForm.valid_to || ''}
                    onChange={(e) => setEditForm({ ...editForm, valid_to: e.target.value })}
                    fullWidth
                    sx={compactTextFieldSx}
                  />
                </TableCell>
                <TableCell sx={{ padding: '4px 8px', fontSize: '0.75rem' }}>-</TableCell>
                <TableCell align="right" sx={{ padding: '4px 8px' }}>
                  <IconButton size="small" color="primary" onClick={handleSaveNew}>
                    <SaveIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={handleCancelEdit}>
                    <CancelIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            )}
            {suppliers.map((supplier) =>
              editingId === supplier.id ? (
                <TableRow key={supplier.id}>
                  <TableCell>
                    <TextField
                      size="small"
                      value={editForm.partner_name || ''}
                      onChange={(e) => setEditForm({ ...editForm, partner_name: e.target.value })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <Select
                      size="small"
                      value={editForm.category || ''}
                      onChange={(e) => setEditForm({ ...editForm, category: e.target.value ? Number(e.target.value) : undefined })}
                      displayEmpty
                      fullWidth
                      sx={{
                        fontSize: '0.75rem',
                        '& .MuiSelect-select': {
                          padding: '8px',
                          fontSize: '0.875rem',
                        },
                      }}
                    >
                      <MenuItem value="">
                        <em>Kategória...</em>
                      </MenuItem>
                      {categories.map((cat) => (
                        <MenuItem key={cat.id} value={cat.id}>
                          {cat.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Select
                      size="small"
                      value={editForm.type || ''}
                      onChange={(e) => setEditForm({ ...editForm, type: e.target.value ? Number(e.target.value) : undefined })}
                      displayEmpty
                      fullWidth
                      sx={{
                        fontSize: '0.75rem',
                        '& .MuiSelect-select': {
                          padding: '8px',
                          fontSize: '0.875rem',
                        },
                      }}
                    >
                      <MenuItem value="">
                        <em>Típus...</em>
                      </MenuItem>
                      {types.map((type) => (
                        <MenuItem key={type.id} value={type.id}>
                          {type.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="date"
                      value={editForm.valid_from || ''}
                      onChange={(e) => setEditForm({ ...editForm, valid_from: e.target.value })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="date"
                      value={editForm.valid_to || ''}
                      onChange={(e) => setEditForm({ ...editForm, valid_to: e.target.value })}
                      fullWidth
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={supplier.is_valid ? 'Érvényes' : 'Lejárt'} color={supplier.is_valid ? 'success' : 'default'} size="small" />
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
                <TableRow key={supplier.id}>
                  <TableCell>{supplier.partner_name}</TableCell>
                  <TableCell>{supplier.category_name || '-'}</TableCell>
                  <TableCell>{supplier.type_name || '-'}</TableCell>
                  <TableCell>{supplier.valid_from || '-'}</TableCell>
                  <TableCell>{supplier.valid_to || '-'}</TableCell>
                  <TableCell>
                    <Chip label={supplier.is_valid ? 'Érvényes' : 'Lejárt'} color={supplier.is_valid ? 'success' : 'default'} size="small" />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => handleStartEdit(supplier)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" color="primary" onClick={() => handleCopyWithNewValidity(supplier)}>
                      <ContentCopyIcon />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDelete(supplier.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              )
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {suppliers.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">Nincs megjeleníthető beszállító</Typography>
        </Box>
      )}
    </Box>
  );
};

export default Suppliers;
