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
  const [showActive, setShowActive] = useState<boolean | undefined>();
  const [showFrequent, setShowFrequent] = useState<boolean | undefined>();
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
    page_size: 20, // Force pagination with 20 items per page
    // Send all sorting to backend for proper cross-page sorting
    ordering: `${sortDirection === 'desc' ? '-' : ''}${sortField}`,
  };

  const { data: beneficiariesData, isLoading, refetch } = useBeneficiaries(queryParams);
  const createMutation = useCreateBeneficiary();
  const updateMutation = useUpdateBeneficiary();
  const deleteMutation = useDeleteBeneficiary();

  // All sorting handled by backend for proper cross-page sorting
  const beneficiaries = beneficiariesData?.results || [];
  
  // Calculate pagination based on our forced page size
  const pageSize = 20;
  const totalPages = Math.ceil((beneficiariesData?.count || 0) / pageSize);

  const handleCreateBeneficiary = async (data: Omit<Beneficiary, 'id'>) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
      refetch();
    } catch (error: any) {
      // Error will be handled by the form component through React Hook Form
      throw error;
    }
  };

  const handleUpdateBeneficiary = async (id: number, data: Partial<Beneficiary>) => {
    try {
      await updateMutation.mutateAsync({ id, data });
      refetch();
    } catch (error: any) {
      // Error will be handled by the calling component
      throw error;
    }
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
    // Force refetch to ensure fresh data
    setTimeout(() => refetch(), 100);
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
    <Box sx={{ p: { xs: 0.5, sm: 0.5, md: 1 }, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 1, mb: 1 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={2}>
          <Box>
            <Typography variant="h5" component="h1" fontWeight="bold" sx={{ mb: 0.5 }}>
              Kedvezményezettek
            </Typography>
            <Typography variant="body2" color="text.secondary">
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
      <Box sx={{ mb: 1 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 1 }}>
          {/* Search */}
          <TextField
            fullWidth
            placeholder="Keresés név, számlaszám, adóazonosító jel vagy leírás alapján..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1); // Reset to first page when searching
            }}
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
                    onChange={(e) => {
                      setShowActive(e.target.checked ? true : undefined);
                      setCurrentPage(1);
                    }}
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
                    onChange={(e) => {
                      setShowFrequent(e.target.checked ? true : undefined);
                      setCurrentPage(1);
                    }}
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
      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
        {beneficiariesData?.count} kedvezményezett találat
      </Typography>

      {/* Table */}
      <Paper elevation={1} sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
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
        <Box sx={{ mt: 1, p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Oldal {currentPage} / {totalPages}
          </Typography>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(_event, page) => setCurrentPage(page)}
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