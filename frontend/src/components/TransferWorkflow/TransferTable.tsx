import React, { useState } from 'react';
import { 
  PencilIcon, 
  TrashIcon, 
  CheckIcon, 
  XMarkIcon,
  PlusIcon,
  CalendarIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';
import { Transfer, Beneficiary } from '../../types/api';

interface TransferData extends Omit<Transfer, 'id' | 'is_processed' | 'created_at'> {
  id?: number;
  beneficiary_data?: Beneficiary;
  tempId?: string;
}

interface TransferTableProps {
  transfers: TransferData[];
  onUpdateTransfer: (index: number, transfer: Partial<TransferData>) => void;
  onDeleteTransfer: (index: number) => void;
  onAddTransfer: () => void;
}

const TransferTable: React.FC<TransferTableProps> = ({
  transfers,
  onUpdateTransfer,
  onDeleteTransfer,
  onAddTransfer,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<TransferData>>({});

  const handleStartEdit = (index: number, transfer: TransferData) => {
    setEditingIndex(index);
    setEditData({
      amount: transfer.amount,
      execution_date: transfer.execution_date,
      remittance_info: transfer.remittance_info,
    });
  };

  const handleSaveEdit = () => {
    if (editingIndex !== null) {
      onUpdateTransfer(editingIndex, editData);
      setEditingIndex(null);
      setEditData({});
    }
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditData({});
  };

  const totalAmount = transfers.reduce((sum, transfer) => 
    sum + (parseFloat(transfer.amount) || 0), 0
  );

  if (transfers.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-8 text-center">
          <CurrencyDollarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Nincsenek átutalások</h3>
          <p className="mt-1 text-sm text-gray-500">
            Válasszon ki egy sablont vagy adjon hozzá manuálisan átutalásokat.
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={onAddTransfer}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Átutalás hozzáadása
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          Átutalások ({transfers.length})
        </h3>
        <button
          onClick={onAddTransfer}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Hozzáadás
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Kedvezményezett
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Összeg (HUF)
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Teljesítés dátuma
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Közlemény
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Műveletek
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transfers.map((transfer, index) => (
              <tr key={transfer.id || transfer.tempId || index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {transfer.beneficiary_data?.name || `Kedvezményezett #${transfer.beneficiary}`}
                      </div>
                      <div className="text-sm text-gray-500 font-mono">
                        {transfer.beneficiary_data?.account_number}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {editingIndex === index ? (
                    <input
                      type="number"
                      step="1"
                      value={editData.amount || ''}
                      onChange={(e) => setEditData({ ...editData, amount: e.target.value })}
                      className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                      placeholder="0"
                    />
                  ) : (
                    <div className="text-sm text-gray-900">
                      {parseFloat(transfer.amount).toLocaleString('hu-HU')} HUF
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {editingIndex === index ? (
                    <input
                      type="date"
                      value={editData.execution_date || ''}
                      onChange={(e) => setEditData({ ...editData, execution_date: e.target.value })}
                      className="w-36 px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  ) : (
                    <div className="flex items-center text-sm text-gray-900">
                      <CalendarIcon className="h-4 w-4 mr-1 text-gray-400" />
                      {new Date(transfer.execution_date).toLocaleDateString('hu-HU')}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingIndex === index ? (
                    <input
                      type="text"
                      value={editData.remittance_info || ''}
                      onChange={(e) => setEditData({ ...editData, remittance_info: e.target.value })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      placeholder="Közlemény..."
                    />
                  ) : (
                    <div className="text-sm text-gray-900 max-w-xs truncate">
                      {transfer.remittance_info || '-'}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {editingIndex === index ? (
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={handleSaveEdit}
                        className="text-green-600 hover:text-green-900 p-1"
                        title="Mentés"
                      >
                        <CheckIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="text-red-600 hover:text-red-900 p-1"
                        title="Mégse"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => handleStartEdit(index, transfer)}
                        className="text-primary-600 hover:text-primary-900 p-1"
                        title="Szerkesztés"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteTransfer(index)}
                        className="text-red-600 hover:text-red-900 p-1"
                        title="Törlés"
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

      {/* Footer with totals */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {transfers.length} átutalás összesen
          </div>
          <div className="text-lg font-semibold text-gray-900">
            Összeg: {totalAmount.toLocaleString('hu-HU')} HUF
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransferTable;