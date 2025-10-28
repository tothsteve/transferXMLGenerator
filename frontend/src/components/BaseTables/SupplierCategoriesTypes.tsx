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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import {
  useSupplierCategories,
  useCreateSupplierCategory,
  useUpdateSupplierCategory,
  useDeleteSupplierCategory,
  useSupplierTypes,
  useCreateSupplierType,
  useUpdateSupplierType,
  useDeleteSupplierType,
} from '../../hooks/api';
import { SupplierCategory, SupplierType } from '../../types/api';
import { useToastContext } from '../../context/ToastContext';
import LoadingSpinner from '../UI/LoadingSpinner';

/**
 * SupplierCategoriesTypes Component
 *
 * Manages supplier categories and types in a dual-panel layout.
 * Provides CRUD operations for both entities.
 */
const SupplierCategoriesTypes: React.FC = () => {
  const { success: showSuccess, error: showError } = useToastContext();

  // Categories state
  const { data: categoriesData, isLoading: categoriesLoading, refetch: refetchCategories } = useSupplierCategories();
  const createCategoryMutation = useCreateSupplierCategory();
  const updateCategoryMutation = useUpdateSupplierCategory();
  const deleteCategoryMutation = useDeleteSupplierCategory();
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [categoryForm, setCategoryForm] = useState<Partial<SupplierCategory>>({ name: '', display_order: 0 });

  // Types state
  const { data: typesData, isLoading: typesLoading, refetch: refetchTypes } = useSupplierTypes();
  const createTypeMutation = useCreateSupplierType();
  const updateTypeMutation = useUpdateSupplierType();
  const deleteTypeMutation = useDeleteSupplierType();
  const [editingTypeId, setEditingTypeId] = useState<number | null>(null);
  const [isAddingType, setIsAddingType] = useState(false);
  const [typeForm, setTypeForm] = useState<Partial<SupplierType>>({ name: '', display_order: 0 });

  const categories = categoriesData?.results || [];
  const types = typesData?.results || [];

  // Category handlers
  const handleStartAddCategory = () => {
    setIsAddingCategory(true);
    setCategoryForm({ name: '', display_order: 0 });
  };

  const handleStartEditCategory = (category: SupplierCategory) => {
    setEditingCategoryId(category.id);
    setCategoryForm(category);
  };

  const handleCancelCategoryEdit = () => {
    setEditingCategoryId(null);
    setIsAddingCategory(false);
    setCategoryForm({ name: '', display_order: 0 });
  };

  const handleSaveCategory = async () => {
    try {
      if (isAddingCategory) {
        // Don't send display_order when creating - let backend auto-assign
        await createCategoryMutation.mutateAsync({
          name: categoryForm.name || '',
        });
        showSuccess('Kategória sikeresen létrehozva');
      } else if (editingCategoryId) {
        await updateCategoryMutation.mutateAsync({
          id: editingCategoryId,
          data: categoryForm,
        });
        showSuccess('Kategória sikeresen frissítve');
      }
      handleCancelCategoryEdit();
      void refetchCategories();
    } catch (error) {
      showError('Hiba történt a kategória mentése során');
    }
  };

  const handleDeleteCategory = async (id: number) => {
    if (!window.confirm('Biztosan törölni szeretné ezt a kategóriát?')) {
      return;
    }
    try {
      await deleteCategoryMutation.mutateAsync(id);
      showSuccess('Kategória sikeresen törölve');
      void refetchCategories();
    } catch (error) {
      showError('Hiba történt a kategória törlése során');
    }
  };

  // Type handlers
  const handleStartAddType = () => {
    setIsAddingType(true);
    setTypeForm({ name: '', display_order: 0 });
  };

  const handleStartEditType = (type: SupplierType) => {
    setEditingTypeId(type.id);
    setTypeForm(type);
  };

  const handleCancelTypeEdit = () => {
    setEditingTypeId(null);
    setIsAddingType(false);
    setTypeForm({ name: '', display_order: 0 });
  };

  const handleSaveType = async () => {
    try {
      if (isAddingType) {
        // Don't send display_order when creating - let backend auto-assign
        await createTypeMutation.mutateAsync({
          name: typeForm.name || '',
        });
        showSuccess('Típus sikeresen létrehozva');
      } else if (editingTypeId) {
        await updateTypeMutation.mutateAsync({
          id: editingTypeId,
          data: typeForm,
        });
        showSuccess('Típus sikeresen frissítve');
      }
      handleCancelTypeEdit();
      void refetchTypes();
    } catch (error) {
      showError('Hiba történt a típus mentése során');
    }
  };

  const handleDeleteType = async (id: number) => {
    if (!window.confirm('Biztosan törölni szeretné ezt a típust?')) {
      return;
    }
    try {
      await deleteTypeMutation.mutateAsync(id);
      showSuccess('Típus sikeresen törölve');
      void refetchTypes();
    } catch (error) {
      showError('Hiba történt a típus törlése során');
    }
  };

  if (categoriesLoading || typesLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Beszállító Kategóriák és Típusok
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Kezeld a beszállító kategóriákat és típusokat. Ezek az értékek a Beszállítók képernyőn választhatók ki.
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Categories Panel */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Kategóriák ({categories.length})</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleStartAddCategory}
                disabled={isAddingCategory}
              >
                Új Kategória
              </Button>
            </Box>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell width="80">Sorrend</TableCell>
                    <TableCell>Név</TableCell>
                    <TableCell width="120" align="right">Műveletek</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {isAddingCategory && (
                    <TableRow>
                      <TableCell>
                        <TextField
                          type="number"
                          value={categoryForm.display_order || 0}
                          onChange={(e) => setCategoryForm({ ...categoryForm, display_order: parseInt(e.target.value) || 0 })}
                          size="small"
                          fullWidth
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={categoryForm.name || ''}
                          onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                          size="small"
                          fullWidth
                          placeholder="Kategória neve"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={handleSaveCategory} color="primary">
                          <SaveIcon />
                        </IconButton>
                        <IconButton size="small" onClick={handleCancelCategoryEdit}>
                          <CancelIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  )}
                  {categories.map((category) => (
                    <TableRow key={category.id}>
                      {editingCategoryId === category.id ? (
                        <>
                          <TableCell>
                            <TextField
                              type="number"
                              value={categoryForm.display_order || 0}
                              onChange={(e) => setCategoryForm({ ...categoryForm, display_order: parseInt(e.target.value) || 0 })}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              value={categoryForm.name || ''}
                              onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell align="right">
                            <IconButton size="small" onClick={handleSaveCategory} color="primary">
                              <SaveIcon />
                            </IconButton>
                            <IconButton size="small" onClick={handleCancelCategoryEdit}>
                              <CancelIcon />
                            </IconButton>
                          </TableCell>
                        </>
                      ) : (
                        <>
                          <TableCell>{category.display_order}</TableCell>
                          <TableCell>{category.name}</TableCell>
                          <TableCell align="right">
                            <IconButton size="small" onClick={() => handleStartEditCategory(category)}>
                              <EditIcon />
                            </IconButton>
                            <IconButton size="small" onClick={() => handleDeleteCategory(category.id)} color="error">
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>

        {/* Types Panel */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Típusok ({types.length})</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleStartAddType}
                disabled={isAddingType}
              >
                Új Típus
              </Button>
            </Box>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell width="80">Sorrend</TableCell>
                    <TableCell>Név</TableCell>
                    <TableCell width="120" align="right">Műveletek</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {isAddingType && (
                    <TableRow>
                      <TableCell>
                        <TextField
                          type="number"
                          value={typeForm.display_order || 0}
                          onChange={(e) => setTypeForm({ ...typeForm, display_order: parseInt(e.target.value) || 0 })}
                          size="small"
                          fullWidth
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={typeForm.name || ''}
                          onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
                          size="small"
                          fullWidth
                          placeholder="Típus neve"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={handleSaveType} color="primary">
                          <SaveIcon />
                        </IconButton>
                        <IconButton size="small" onClick={handleCancelTypeEdit}>
                          <CancelIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  )}
                  {types.map((type) => (
                    <TableRow key={type.id}>
                      {editingTypeId === type.id ? (
                        <>
                          <TableCell>
                            <TextField
                              type="number"
                              value={typeForm.display_order || 0}
                              onChange={(e) => setTypeForm({ ...typeForm, display_order: parseInt(e.target.value) || 0 })}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              value={typeForm.name || ''}
                              onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell align="right">
                            <IconButton size="small" onClick={handleSaveType} color="primary">
                              <SaveIcon />
                            </IconButton>
                            <IconButton size="small" onClick={handleCancelTypeEdit}>
                              <CancelIcon />
                            </IconButton>
                          </TableCell>
                        </>
                      ) : (
                        <>
                          <TableCell>{type.display_order}</TableCell>
                          <TableCell>{type.name}</TableCell>
                          <TableCell align="right">
                            <IconButton size="small" onClick={() => handleStartEditType(type)}>
                              <EditIcon />
                            </IconButton>
                            <IconButton size="small" onClick={() => handleDeleteType(type.id)} color="error">
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default SupplierCategoriesTypes;
