import React, { useState } from 'react';
import { 
  PencilIcon, 
  TrashIcon, 
  CheckIcon, 
  XMarkIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import { Beneficiary } from '../../types/api';

interface BeneficiaryTableProps {
  beneficiaries: Beneficiary[];
  isLoading: boolean;
  onEdit: (beneficiary: Beneficiary) => void;
  onDelete: (id: number) => void;
  onUpdate: (id: number, data: Partial<Beneficiary>) => void;
  onSort: (field: string, direction: 'asc' | 'desc') => void;
  sortField?: string;
  sortDirection?: 'asc' | 'desc';
}

const BeneficiaryTable: React.FC<BeneficiaryTableProps> = ({
  beneficiaries,
  isLoading,
  onEdit,
  onDelete,
  onUpdate,
  onSort,
  sortField,
  sortDirection,
}) => {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<Beneficiary>>({});

  const handleStartEdit = (beneficiary: Beneficiary) => {
    setEditingId(beneficiary.id);
    setEditData({
      name: beneficiary.name,
      account_number: beneficiary.account_number,
      notes: beneficiary.notes,
      is_frequent: beneficiary.is_frequent,
      is_active: beneficiary.is_active,
    });
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      // Toggle direction
      const newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(field, newDirection);
    } else {
      // New field, start with ascending
      onSort(field, 'asc');
    }
  };

  const SortableHeader: React.FC<{ field: string; children: React.ReactNode }> = ({ field, children }) => (
    <th 
      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center space-x-1">
        <span>{children}</span>
        {sortField === field && (
          sortDirection === 'asc' ? 
            <ChevronUpIcon className="h-4 w-4" /> : 
            <ChevronDownIcon className="h-4 w-4" />
        )}
      </div>
    </th>
  );

  const handleSaveEdit = () => {
    if (editingId && editData) {
      onUpdate(editingId, editData);
      setEditingId(null);
      setEditData({});
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditData({});
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
          <div className="divide-y divide-gray-200">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="px-6 py-4">
                <div className="flex space-x-4">
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (beneficiaries.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6 text-center">
        <p className="text-gray-500">Nincsenek kedvezményezettek</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <SortableHeader field="name">Név</SortableHeader>
            <SortableHeader field="notes">Megjegyzés</SortableHeader>
            <SortableHeader field="account_number">Számlaszám</SortableHeader>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Állapot
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Műveletek
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {beneficiaries.map((beneficiary) => (
            <tr key={beneficiary.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                {editingId === beneficiary.id ? (
                  <input
                    type="text"
                    value={editData.name || ''}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                ) : (
                  <div className="flex items-center">
                    <div className="text-sm font-medium text-gray-900">
                      {beneficiary.name}
                    </div>
                    {beneficiary.is_frequent && (
                      <StarSolidIcon className="h-4 w-4 text-yellow-400 ml-2" />
                    )}
                  </div>
                )}
              </td>
              <td className="px-6 py-4">
                {editingId === beneficiary.id ? (
                  <textarea
                    value={editData.notes || ''}
                    onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm resize-none"
                    rows={2}
                    placeholder="Megjegyzés..."
                  />
                ) : (
                  <div className="text-sm text-gray-500 max-w-xs">
                    {beneficiary.notes || '-'}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {editingId === beneficiary.id ? (
                  <input
                    type="text"
                    value={editData.account_number || ''}
                    onChange={(e) => setEditData({ ...editData, account_number: e.target.value })}
                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                ) : (
                  <div className="text-sm text-gray-900 font-mono">
                    {beneficiary.account_number}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {editingId === beneficiary.id ? (
                  <div className="flex flex-col space-y-1">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={editData.is_active || false}
                        onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })}
                        className="mr-1"
                      />
                      <span className="text-xs">Aktív</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={editData.is_frequent || false}
                        onChange={(e) => setEditData({ ...editData, is_frequent: e.target.checked })}
                        className="mr-1"
                      />
                      <span className="text-xs">Gyakori</span>
                    </label>
                  </div>
                ) : (
                  <div className="flex flex-col space-y-1">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      beneficiary.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {beneficiary.is_active ? 'Aktív' : 'Inaktív'}
                    </span>
                    {beneficiary.is_frequent && (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        Gyakori
                      </span>
                    )}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                {editingId === beneficiary.id ? (
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={handleSaveEdit}
                      className="text-green-600 hover:text-green-900 p-1"
                    >
                      <CheckIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="text-red-600 hover:text-red-900 p-1"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => handleStartEdit(beneficiary)}
                      className="text-primary-600 hover:text-primary-900 p-1"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onDelete(beneficiary.id)}
                      className="text-red-600 hover:text-red-900 p-1"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BeneficiaryTable;