import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  XMarkIcon,
  CalendarIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { TransferTemplate } from '../../types/api';

interface TemplateViewProps {
  isOpen: boolean;
  onClose: () => void;
  template: TransferTemplate | null;
}

// This would be populated from the template details API
interface TemplateBeneficiaryDetail {
  id: number;
  beneficiary_name: string;
  account_number: string;
  bank_name: string;
  default_amount: string;
  default_remittance_info: string;
}

const TemplateView: React.FC<TemplateViewProps> = ({
  isOpen,
  onClose,
  template,
}) => {
  if (!template) return null;

  // Mock data - in real implementation, this would come from API
  const templateBeneficiaries: TemplateBeneficiaryDetail[] = [
    {
      id: 1,
      beneficiary_name: 'Teszt Alkalmazott',
      account_number: '12345678-12345678',
      bank_name: 'Test Bank',
      default_amount: '350000',
      default_remittance_info: 'Havi bér - január',
    },
    {
      id: 2,
      beneficiary_name: 'Másik Alkalmazott', 
      account_number: '87654321-87654321',
      bank_name: 'Másik Bank',
      default_amount: '420000',
      default_remittance_info: 'Havi bér - január',
    },
  ];

  const totalAmount = templateBeneficiaries.reduce((sum, b) => 
    sum + (parseFloat(b.default_amount) || 0), 0
  );

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
                    Sablon részletei
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Template Info */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                      <div>
                        <h4 className="text-lg font-medium text-gray-900 mb-4">{template.name}</h4>
                        {template.description && (
                          <p className="text-sm text-gray-600">{template.description}</p>
                        )}
                      </div>
                      
                      <div className="space-y-3">
                        <div className="flex items-center text-sm">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            template.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {template.is_active ? 'Aktív' : 'Inaktív'}
                          </span>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-500">
                          <UserGroupIcon className="h-4 w-4 mr-2" />
                          <span>{template.beneficiary_count} kedvezményezett</span>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-500">
                          <CurrencyDollarIcon className="h-4 w-4 mr-2" />
                          <span>{totalAmount.toLocaleString('hu-HU')} HUF összesen</span>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-500">
                          <CalendarIcon className="h-4 w-4 mr-2" />
                          <span>
                            Létrehozva: {new Date(template.created_at).toLocaleDateString('hu-HU')}
                          </span>
                        </div>
                        
                        {template.updated_at !== template.created_at && (
                          <div className="flex items-center text-sm text-gray-500">
                            <CalendarIcon className="h-4 w-4 mr-2" />
                            <span>
                              Módosítva: {new Date(template.updated_at).toLocaleDateString('hu-HU')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Beneficiaries */}
                  <div>
                    <h5 className="text-sm font-medium text-gray-900 mb-4">Kedvezményezettek</h5>
                    
                    {templateBeneficiaries.length === 0 ? (
                      <div className="text-center py-6 border-2 border-dashed border-gray-300 rounded-lg">
                        <p className="text-sm text-gray-500">
                          Nincsenek kedvezményezettek hozzárendelve ehhez a sablonhoz.
                        </p>
                      </div>
                    ) : (
                      <div className="bg-white shadow overflow-hidden sm:rounded-md">
                        <ul className="divide-y divide-gray-200">
                          {templateBeneficiaries.map((beneficiary, index) => (
                            <li key={beneficiary.id} className="px-6 py-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center">
                                  <div className="flex-shrink-0">
                                    <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                                      <span className="text-sm font-medium text-primary-800">
                                        {index + 1}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="ml-4">
                                    <div className="text-sm font-medium text-gray-900">
                                      {beneficiary.beneficiary_name}
                                    </div>
                                    <div className="text-sm text-gray-500 font-mono">
                                      {beneficiary.account_number}
                                    </div>
                                    {beneficiary.bank_name && (
                                      <div className="text-sm text-gray-500">
                                        {beneficiary.bank_name}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                
                                <div className="text-right">
                                  <div className="text-sm font-medium text-gray-900">
                                    {parseFloat(beneficiary.default_amount).toLocaleString('hu-HU')} HUF
                                  </div>
                                  {beneficiary.default_remittance_info && (
                                    <div className="text-sm text-gray-500 flex items-center">
                                      <DocumentTextIcon className="h-3 w-3 mr-1" />
                                      {beneficiary.default_remittance_info}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </li>
                          ))}
                        </ul>
                        
                        {/* Summary */}
                        <div className="bg-gray-50 px-6 py-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-900">Összesen:</span>
                            <span className="text-sm font-bold text-gray-900">
                              {totalAmount.toLocaleString('hu-HU')} HUF
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex justify-end pt-6">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    Bezárás
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default TemplateView;