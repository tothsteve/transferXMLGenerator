import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { useForm } from 'react-hook-form';
import { 
  XMarkIcon,
  MagnifyingGlassIcon,
  UserIcon
} from '@heroicons/react/24/outline';
import { useBeneficiaries } from '../../hooks/api';
import { Beneficiary } from '../../types/api';

interface AddTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (transferData: {
    beneficiary: number;
    beneficiary_data: Beneficiary;
    amount: string;
    execution_date: string;
    remittance_info: string;
    currency: 'HUF' | 'EUR' | 'USD';
  }) => void;
}

interface FormData {
  amount: string;
  execution_date: string;
  remittance_info: string;
  currency: 'HUF' | 'EUR' | 'USD';
}

const AddTransferModal: React.FC<AddTransferModalProps> = ({
  isOpen,
  onClose,
  onAdd,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBeneficiary, setSelectedBeneficiary] = useState<Beneficiary | null>(null);
  const [showBeneficiaryPicker, setShowBeneficiaryPicker] = useState(true);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      amount: '',
      execution_date: new Date().toISOString().split('T')[0],
      remittance_info: '',
      currency: 'HUF',
    },
  });

  const { data: beneficiariesData } = useBeneficiaries({
    search: searchTerm,
    is_active: true,
  });

  const availableBeneficiaries = beneficiariesData?.results || [];

  const handleFormSubmit = (data: FormData) => {
    if (!selectedBeneficiary) return;

    onAdd({
      beneficiary: selectedBeneficiary.id,
      beneficiary_data: selectedBeneficiary,
      amount: data.amount,
      execution_date: data.execution_date,
      remittance_info: data.remittance_info,
      currency: data.currency,
    });

    handleClose();
  };

  const handleClose = () => {
    reset();
    setSelectedBeneficiary(null);
    setSearchTerm('');
    setShowBeneficiaryPicker(true);
    onClose();
  };

  const handleBeneficiarySelect = (beneficiary: Beneficiary) => {
    setSelectedBeneficiary(beneficiary);
    setShowBeneficiaryPicker(false);
    setSearchTerm('');
  };

  const handleChangeBeneficiary = () => {
    setSelectedBeneficiary(null);
    setShowBeneficiaryPicker(true);
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex justify-between items-center mb-6">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Új átutalás hozzáadása
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {showBeneficiaryPicker ? (
                  /* Beneficiary Selection */
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Kedvezményezett kiválasztása
                      </label>
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

                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {availableBeneficiaries.length === 0 ? (
                        <div className="text-center py-6 text-gray-500">
                          <UserIcon className="mx-auto h-8 w-8 mb-2" />
                          <p className="text-sm">Nincsenek találatok</p>
                        </div>
                      ) : (
                        availableBeneficiaries.map((beneficiary) => (
                          <button
                            key={beneficiary.id}
                            type="button"
                            onClick={() => handleBeneficiarySelect(beneficiary)}
                            className="w-full text-left p-3 hover:bg-gray-50 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <div className="font-medium text-gray-900">{beneficiary.name}</div>
                            <div className="text-sm text-gray-500 font-mono">{beneficiary.account_number}</div>
                            {beneficiary.bank_name && (
                              <div className="text-xs text-gray-400">{beneficiary.bank_name}</div>
                            )}
                          </button>
                        ))
                      )}
                    </div>
                  </div>
                ) : (
                  /* Transfer Form */
                  <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
                    {/* Selected Beneficiary */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium text-gray-900">{selectedBeneficiary?.name}</div>
                          <div className="text-sm text-gray-500 font-mono">{selectedBeneficiary?.account_number}</div>
                          {selectedBeneficiary?.bank_name && (
                            <div className="text-xs text-gray-400">{selectedBeneficiary.bank_name}</div>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={handleChangeBeneficiary}
                          className="text-sm text-primary-600 hover:text-primary-800"
                        >
                          Változtatás
                        </button>
                      </div>
                    </div>

                    {/* Amount */}
                    <div>
                      <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                        Összeg *
                      </label>
                      <div className="mt-1 relative rounded-md shadow-sm">
                        <input
                          type="number"
                          step="1"
                          min="0"
                          {...register('amount', { 
                            required: 'Az összeg megadása kötelező',
                            min: { value: 1, message: 'Az összegnek pozitívnak kell lennie' }
                          })}
                          className="block w-full pr-16 border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                          placeholder="0"
                        />
                        <div className="absolute inset-y-0 right-0 flex items-center">
                          <select
                            {...register('currency')}
                            className="h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                          >
                            <option value="HUF">HUF</option>
                            <option value="EUR">EUR</option>
                            <option value="USD">USD</option>
                          </select>
                        </div>
                      </div>
                      {errors.amount && (
                        <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
                      )}
                    </div>

                    {/* Execution Date */}
                    <div>
                      <label htmlFor="execution_date" className="block text-sm font-medium text-gray-700">
                        Teljesítés dátuma *
                      </label>
                      <input
                        type="date"
                        {...register('execution_date', { required: 'A teljesítés dátuma kötelező' })}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                      {errors.execution_date && (
                        <p className="mt-1 text-sm text-red-600">{errors.execution_date.message}</p>
                      )}
                    </div>

                    {/* Remittance Info */}
                    <div>
                      <label htmlFor="remittance_info" className="block text-sm font-medium text-gray-700">
                        Közlemény
                      </label>
                      <input
                        type="text"
                        {...register('remittance_info')}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        placeholder="Fizetési közlemény..."
                      />
                    </div>

                    <div className="flex justify-end space-x-3 pt-4">
                      <button
                        type="button"
                        onClick={handleClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        Mégse
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        Hozzáadás
                      </button>
                    </div>
                  </form>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default AddTransferModal;