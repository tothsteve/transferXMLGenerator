import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  XMarkIcon, 
  PlusIcon, 
  TrashIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { TransferTemplate, Beneficiary, TemplateBeneficiary } from '../../types/api';
import { useBeneficiaries } from '../../hooks/api';

interface TemplateFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TemplateFormData) => void;
  template?: TransferTemplate | null;
  isLoading?: boolean;
}

interface TemplateFormData {
  name: string;
  description: string;
  is_active: boolean;
  beneficiaries: {
    beneficiary_id: number;
    default_amount: string;
    default_remittance_info: string;
  }[];
}

interface BeneficiarySelection {
  beneficiary_id: number;
  beneficiary_name: string;
  account_number: string;
  default_amount: string;
  default_remittance_info: string;
}

const TemplateForm: React.FC<TemplateFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  template,
  isLoading = false,
}) => {
  const [selectedBeneficiaries, setSelectedBeneficiaries] = useState<BeneficiarySelection[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showBeneficiaryPicker, setShowBeneficiaryPicker] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Omit<TemplateFormData, 'beneficiaries'>>({
    defaultValues: {
      name: template?.name || '',
      description: template?.description || '',
      is_active: template?.is_active ?? true,
    },
  });

  const { data: beneficiariesData } = useBeneficiaries({
    search: searchTerm,
    is_active: true,
  });

  const availableBeneficiaries = beneficiariesData?.results || [];
  const selectedBeneficiaryIds = new Set(selectedBeneficiaries.map(b => b.beneficiary_id));

  useEffect(() => {
    if (template) {
      // TODO: Load template beneficiaries when we have that endpoint
      setSelectedBeneficiaries([]);
    }
  }, [template]);

  const handleFormSubmit = (data: Omit<TemplateFormData, 'beneficiaries'>) => {
    const formData: TemplateFormData = {
      ...data,
      beneficiaries: selectedBeneficiaries.map(b => ({
        beneficiary_id: b.beneficiary_id,
        default_amount: b.default_amount,
        default_remittance_info: b.default_remittance_info,
      })),
    };
    onSubmit(formData);
  };

  const handleClose = () => {
    reset();
    setSelectedBeneficiaries([]);
    setSearchTerm('');
    setShowBeneficiaryPicker(false);
    onClose();
  };

  const addBeneficiary = (beneficiary: Beneficiary) => {
    if (!selectedBeneficiaryIds.has(beneficiary.id)) {
      setSelectedBeneficiaries(prev => [...prev, {
        beneficiary_id: beneficiary.id,
        beneficiary_name: beneficiary.name,
        account_number: beneficiary.account_number,
        default_amount: '',
        default_remittance_info: '',
      }]);
    }
    setShowBeneficiaryPicker(false);
    setSearchTerm('');
  };

  const removeBeneficiary = (beneficiaryId: number) => {
    setSelectedBeneficiaries(prev => 
      prev.filter(b => b.beneficiary_id !== beneficiaryId)
    );
  };

  const updateBeneficiary = (beneficiaryId: number, field: 'default_amount' | 'default_remittance_info', value: string) => {
    setSelectedBeneficiaries(prev => 
      prev.map(b => 
        b.beneficiary_id === beneficiaryId 
          ? { ...b, [field]: value }
          : b
      )
    );
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
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex justify-between items-center mb-6">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    {template ? 'Sablon szerkesztése' : 'Új sablon létrehozása'}
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
                  {/* Basic Template Info */}
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                        Sablon neve *
                      </label>
                      <input
                        type="text"
                        {...register('name', { required: 'A sablon neve kötelező' })}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        placeholder="pl. Havi bérszámfejtés"
                      />
                      {errors.name && (
                        <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                      )}
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('is_active')}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                        Aktív sablon
                      </label>
                    </div>
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                      Leírás
                    </label>
                    <textarea
                      {...register('description')}
                      rows={3}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                      placeholder="Sablon leírása..."
                    />
                  </div>

                  {/* Beneficiaries Section */}
                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <label className="block text-sm font-medium text-gray-700">
                        Kedvezményezettek ({selectedBeneficiaries.length})
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowBeneficiaryPicker(true)}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        <PlusIcon className="h-4 w-4 mr-1" />
                        Hozzáadás
                      </button>
                    </div>

                    {/* Beneficiary Picker Modal */}
                    {showBeneficiaryPicker && (
                      <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                          <div className="flex justify-between items-center mb-4">
                            <h4 className="text-lg font-medium">Kedvezményezett kiválasztása</h4>
                            <button
                              onClick={() => setShowBeneficiaryPicker(false)}
                              className="text-gray-400 hover:text-gray-600"
                            >
                              <XMarkIcon className="h-5 w-5" />
                            </button>
                          </div>

                          <div className="relative mb-4">
                            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <input
                              type="text"
                              placeholder="Keresés..."
                              value={searchTerm}
                              onChange={(e) => setSearchTerm(e.target.value)}
                              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                            />
                          </div>

                          <div className="max-h-64 overflow-y-auto space-y-2">
                            {availableBeneficiaries
                              .filter(b => !selectedBeneficiaryIds.has(b.id))
                              .map(beneficiary => (
                                <button
                                  key={beneficiary.id}
                                  type="button"
                                  onClick={() => addBeneficiary(beneficiary)}
                                  className="w-full text-left p-3 hover:bg-gray-50 border border-gray-200 rounded-md"
                                >
                                  <div className="font-medium text-gray-900">{beneficiary.name}</div>
                                  <div className="text-sm text-gray-500 font-mono">{beneficiary.account_number}</div>
                                </button>
                              ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Selected Beneficiaries */}
                    {selectedBeneficiaries.length === 0 ? (
                      <div className="text-center py-6 border-2 border-dashed border-gray-300 rounded-lg">
                        <p className="text-sm text-gray-500">
                          Nincs kiválasztott kedvezményezett. Kattintson a "Hozzáadás" gombra.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4 max-h-64 overflow-y-auto">
                        {selectedBeneficiaries.map(beneficiary => (
                          <div key={beneficiary.beneficiary_id} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-gray-900">{beneficiary.beneficiary_name}</div>
                              <div className="text-sm text-gray-500 font-mono">{beneficiary.account_number}</div>
                              
                              <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
                                <div>
                                  <label className="block text-xs font-medium text-gray-700">
                                    Alapértelmezett összeg (HUF)
                                  </label>
                                  <input
                                    type="number"
                                    value={beneficiary.default_amount}
                                    onChange={(e) => updateBeneficiary(beneficiary.beneficiary_id, 'default_amount', e.target.value)}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                                    placeholder="0"
                                  />
                                </div>
                                <div>
                                  <label className="block text-xs font-medium text-gray-700">
                                    Alapértelmezett közlemény
                                  </label>
                                  <input
                                    type="text"
                                    value={beneficiary.default_remittance_info}
                                    onChange={(e) => updateBeneficiary(beneficiary.beneficiary_id, 'default_remittance_info', e.target.value)}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                                    placeholder="Közlemény..."
                                  />
                                </div>
                              </div>
                            </div>
                            
                            <button
                              type="button"
                              onClick={() => removeBeneficiary(beneficiary.beneficiary_id)}
                              className="text-red-400 hover:text-red-600"
                            >
                              <TrashIcon className="h-5 w-5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end space-x-3 pt-6">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      Mégse
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading || selectedBeneficiaries.length === 0}
                      className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? 'Mentés...' : (template ? 'Frissítés' : 'Létrehozás')}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default TemplateForm;