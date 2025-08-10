import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  Stack,
  Pagination,
  Paper,
  Menu,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { 
  useBeneficiaries, 
  useCreateBeneficiary, 
  useUpdateBeneficiary, 
  useDeleteBeneficiary 
} from '../../hooks/api';
import { Beneficiary } from '../../types/api';
import BeneficiaryTable from './BeneficiaryTable';
import BeneficiaryForm from './BeneficiaryForm';
import ExcelImport from './ExcelImport';

const BeneficiaryManager: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showActive, setShowActive] = useState<boolean | undefined>(undefined);
  const [showFrequent, setShowFrequent] = useState<boolean | undefined>(undefined);
  const [currentPage, setCurrentPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [editingBeneficiary, setEditingBeneficiary] = useState<Beneficiary | null>(null);
  const [sortField, setSortField] = useState<string>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const queryParams = {
    search: searchTerm || undefined,
    is_active: showActive,
    is_frequent: showFrequent,
    page: currentPage,
    // Don't send ordering for notes field since we handle it client-side
    ordering: sortField !== 'notes' ? `${sortDirection === 'desc' ? '-' : ''}${sortField}` : undefined,
  };

  const { data: beneficiariesData, isLoading, refetch } = useBeneficiaries(queryParams);
  const createMutation = useCreateBeneficiary();
  const updateMutation = useUpdateBeneficiary();
  const deleteMutation = useDeleteBeneficiary();

  // Get raw beneficiaries and apply client-side sorting for notes if needed
  const rawBeneficiaries = beneficiariesData?.results || [];
  
  // Apply client-side sorting for notes column to handle null values properly
  const beneficiaries = sortField === 'notes' 
    ? [...rawBeneficiaries].sort((a, b) => {
        const aValue = a.notes || '';
        const bValue = b.notes || '';
        
        // Handle null/empty values - put them at the end for ascending, beginning for descending
        if (!aValue && !bValue) return 0;
        if (!aValue) return sortDirection === 'asc' ? 1 : -1;
        if (!bValue) return sortDirection === 'asc' ? -1 : 1;
        
        // Normal string comparison
        const comparison = aValue.localeCompare(bValue);
        return sortDirection === 'desc' ? -comparison : comparison;
      })
    : rawBeneficiaries;
  
  const totalPages = Math.ceil((beneficiariesData?.count || 0) / 20); // Assuming 20 per page

  const handleCreateBeneficiary = async (data: Omit<Beneficiary, 'id'>) => {
    await createMutation.mutateAsync(data);
    setShowForm(false);
    refetch();
  };

  const handleUpdateBeneficiary = async (id: number, data: Partial<Beneficiary>) => {
    await updateMutation.mutateAsync({ id, data });
    refetch();
  };

  const handleDeleteBeneficiary = async (id: number) => {
    if (window.confirm('Biztosan törölni szeretné ezt a kedvezményezettet?')) {
      await deleteMutation.mutateAsync(id);
      refetch();
    }
  };

  const handleEditBeneficiary = (beneficiary: Beneficiary) => {
    setEditingBeneficiary(beneficiary);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingBeneficiary(null);
  };

  const handleImportSuccess = () => {
    refetch();
  };

  const handleSort = (field: string, direction: 'asc' | 'desc') => {
    setSortField(field);
    setSortDirection(direction);
    setCurrentPage(1); // Reset to first page when sorting
  };

  const clearFilters = () => {
    setSearchTerm('');
    setShowActive(undefined);
    setShowFrequent(undefined);
    setCurrentPage(1);
    setSortField('name');
    setSortDirection('asc');
  };

  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const filterMenuOpen = Boolean(filterAnchorEl);

  const handleFilterClick = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterClose = () => {
    setFilterAnchorEl(null);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 3, mb: 4 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={3}>
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
              Kedvezményezettek
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Kedvezményezettek kezelése, hozzáadás, szerkesztés és törlés
            </Typography>
          </Box>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={() => setShowImport(true)}
            >
              Excel importálás
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowForm(true)}
            >
              Új kedvezményezett
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 4 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
          {/* Search */}
          <TextField
            fullWidth
            placeholder="Keresés név vagy számlaszám alapján..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            size="small"
          />

          {/* Filters */}
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={handleFilterClick}
            sx={{ minWidth: 140 }}
          >
            Szűrők
          </Button>
          <Menu
            anchorEl={filterAnchorEl}
            open={filterMenuOpen}
            onClose={handleFilterClose}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={showActive === true}
                    onChange={(e) => setShowActive(e.target.checked ? true : undefined)}
                    size="small"
                  />
                }
                label="Csak aktív kedvezményezettek"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={showFrequent === true}
                    onChange={(e) => setShowFrequent(e.target.checked ? true : undefined)}
                    size="small"
                  />
                }
                label="Csak gyakori kedvezményezettek"
                sx={{ m: 0 }}
              />
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { clearFilters(); handleFilterClose(); }}>
              Szűrők törlése
            </MenuItem>
          </Menu>
        </Stack>

        {/* Active filters display */}
        {(searchTerm || showActive !== undefined || showFrequent !== undefined) && (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            <Typography variant="body2" color="text.secondary">
              Aktív szűrők:
            </Typography>
            {searchTerm && (
              <Chip
                label={`Keresés: ${searchTerm}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
            {showActive === true && (
              <Chip
                label="Aktív"
                size="small"
                color="success"
                variant="outlined"
              />
            )}
            {showFrequent === true && (
              <Chip
                label="Gyakori"
                size="small"
                color="warning"
                variant="outlined"
              />
            )}
          </Stack>
        )}
      </Box>

      {/* Results count */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {beneficiariesData?.count} kedvezményezett találat
      </Typography>

      {/* Table */}
      <Paper elevation={1}>
        <BeneficiaryTable
          beneficiaries={beneficiaries}
          isLoading={isLoading}
          onEdit={handleEditBeneficiary}
          onDelete={handleDeleteBeneficiary}
          onUpdate={handleUpdateBeneficiary}
          onSort={handleSort}
          sortField={sortField}
          sortDirection={sortDirection}
        />
      </Paper>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Oldal {currentPage} / {totalPages}
          </Typography>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(event, page) => setCurrentPage(page)}
            color="primary"
            size="small"
          />
        </Box>
      )}

      {/* Forms */}
      <BeneficiaryForm
        isOpen={showForm}
        onClose={handleFormClose}
        onSubmit={editingBeneficiary ? 
          (data) => handleUpdateBeneficiary(editingBeneficiary.id, data) :
          handleCreateBeneficiary
        }
        beneficiary={editingBeneficiary}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      <ExcelImport
        isOpen={showImport}
        onClose={() => setShowImport(false)}
        onSuccess={handleImportSuccess}
      />
    </Box>
  );
};

export default BeneficiaryManager;