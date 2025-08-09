import React, { useState } from 'react';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  FunnelIcon, 
  DocumentArrowUpIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { Menu } from '@headlessui/react';
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

  return (
    <div className="lg:pl-72">
      <div className="px-4 py-10 sm:px-6 lg:px-8 lg:py-6">
        <div className="border-b border-gray-200 pb-5">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
                Kedvezményezettek
              </h1>
              <p className="mt-2 max-w-4xl text-sm text-gray-500">
                Kedvezményezettek kezelése, hozzáadás, szerkesztés és törlés
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowImport(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
                Excel importálás
              </button>
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Új kedvezményezett
              </button>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mt-8 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Keresés név vagy számlaszám alapján..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex space-x-2">
              <Menu as="div" className="relative inline-block text-left">
                <Menu.Button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                  <FunnelIcon className="h-4 w-4 mr-2" />
                  Szűrők
                </Menu.Button>
                <Menu.Items className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                  <div className="py-1">
                    <Menu.Item>
                      <div className="px-4 py-2 text-sm text-gray-700">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={showActive === true}
                            onChange={(e) => setShowActive(e.target.checked ? true : undefined)}
                            className="mr-2"
                          />
                          Csak aktív kedvezményezettek
                        </label>
                      </div>
                    </Menu.Item>
                    <Menu.Item>
                      <div className="px-4 py-2 text-sm text-gray-700">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={showFrequent === true}
                            onChange={(e) => setShowFrequent(e.target.checked ? true : undefined)}
                            className="mr-2"
                          />
                          Csak gyakori kedvezményezettek
                        </label>
                      </div>
                    </Menu.Item>
                    <div className="border-t border-gray-100">
                      <Menu.Item>
                        <button
                          onClick={clearFilters}
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                        >
                          Szűrők törlése
                        </button>
                      </Menu.Item>
                    </div>
                  </div>
                </Menu.Items>
              </Menu>
            </div>
          </div>

          {/* Active filters display */}
          {(searchTerm || showActive !== undefined || showFrequent !== undefined) && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Aktív szűrők:</span>
              {searchTerm && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                  Keresés: {searchTerm}
                </span>
              )}
              {showActive === true && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Aktív
                </span>
              )}
              {showFrequent === true && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Gyakori
                </span>
              )}
            </div>
          )}
        </div>

        {/* Results count */}
        <div className="mt-6 text-sm text-gray-700">
          {beneficiariesData?.count} kedvezményezett találat
        </div>

        {/* Table */}
        <div className="mt-4">
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
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Oldal {currentPage} / {totalPages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRightIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
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
      </div>
    </div>
  );
};

export default BeneficiaryManager;