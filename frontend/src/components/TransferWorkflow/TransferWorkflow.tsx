import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import { 
  useTemplates, 
  useLoadTemplate, 
  useBulkCreateTransfers, 
  useGenerateXml,
  useDefaultBankAccount
} from '../../hooks/api';
import { Transfer, TransferTemplate, LoadTemplateResponse } from '../../types/api';
import TemplateSelector from './TemplateSelector';
import TransferTable from './TransferTable';
import AddTransferModal from './AddTransferModal';
import XMLPreview from './XMLPreview';

interface TransferData extends Omit<Transfer, 'id' | 'is_processed' | 'created_at'> {
  id?: number;
  tempId?: string;
}

const TransferWorkflow: React.FC = () => {
  const location = useLocation();
  const [selectedTemplate, setSelectedTemplate] = useState<TransferTemplate | null>(null);
  const [transfers, setTransfers] = useState<TransferData[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [xmlPreview, setXmlPreview] = useState<{
    content: string;
    filename: string;
  } | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const { data: templatesData } = useTemplates();
  const { data: defaultAccount } = useDefaultBankAccount();
  const loadTemplateMutation = useLoadTemplate();
  const bulkCreateMutation = useBulkCreateTransfers();
  const generateXmlMutation = useGenerateXml();

  const templates = templatesData?.results || [];

  // Handle template data passed from TemplateBuilder
  useEffect(() => {
    const state = location.state as { 
      templateData?: LoadTemplateResponse; 
      loadedFromTemplate?: boolean 
    } | null;
    
    if (state?.templateData && state.loadedFromTemplate) {
      setSelectedTemplate(state.templateData.template);
      setTransfers(state.templateData.transfers.map((transfer, index) => ({
        ...transfer,
        tempId: `temp-${index}`,
      })));
      
      // Clear the location state to prevent re-loading on refresh
      window.history.replaceState({}, '');
    }
  }, [location.state]);

  const handleLoadTemplate = async (templateId: number) => {
    try {
      const result = await loadTemplateMutation.mutateAsync(templateId);
      setTransfers(result.data.transfers.map((transfer, index) => ({
        ...transfer,
        tempId: `temp-${index}`,
      })));
    } catch (error) {
      console.error('Failed to load template:', error);
    }
  };

  const handleUpdateTransfer = (index: number, updatedData: Partial<TransferData>) => {
    setTransfers(prev => prev.map((transfer, i) => 
      i === index ? { ...transfer, ...updatedData } : transfer
    ));
    setValidationErrors([]);
  };

  const handleDeleteTransfer = (index: number) => {
    setTransfers(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddTransfer = (transferData: TransferData) => {
    setTransfers(prev => [...prev, {
      ...transferData,
      tempId: `temp-${Date.now()}`,
    }]);
    setValidationErrors([]);
  };

  const validateTransfers = (): string[] => {
    const errors: string[] = [];
    
    if (transfers.length === 0) {
      errors.push('Legalább egy átutalást meg kell adni');
    }

    transfers.forEach((transfer, index) => {
      if (!transfer.amount || parseFloat(transfer.amount) <= 0) {
        errors.push(`${index + 1}. átutalás: Érvényes összeget kell megadni`);
      }
      
      if (!transfer.execution_date) {
        errors.push(`${index + 1}. átutalás: Teljesítési dátumot kell megadni`);
      }
      
      if (!transfer.beneficiary) {
        errors.push(`${index + 1}. átutalás: Kedvezményezettet kell választani`);
      }
    });

    return errors;
  };

  const handleGenerateXML = async () => {
    const errors = validateTransfers();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    try {
      // First, bulk create the transfers if they don't have IDs yet
      const transfersToCreate = transfers.filter(t => !t.id);
      let transferIds: number[] = [];

      if (transfersToCreate.length > 0) {
        const bulkResult = await bulkCreateMutation.mutateAsync({
          transfers: transfersToCreate.map(t => ({
            beneficiary: t.beneficiary,
            amount: t.amount,
            currency: t.currency,
            execution_date: t.execution_date,
            remittance_info: t.remittance_info,
          })),
        });
        transferIds = bulkResult.data.map(t => t.id!);
      }

      // Add existing transfer IDs
      const existingIds = transfers.filter(t => t.id).map(t => t.id!);
      const allTransferIds = [...existingIds, ...transferIds];

      // Generate XML
      const xmlResult = await generateXmlMutation.mutateAsync({
        transfer_ids: allTransferIds,
      });

      setXmlPreview({
        content: xmlResult.data.xml_content,
        filename: xmlResult.data.filename,
      });

    } catch (error) {
      console.error('Failed to generate XML:', error);
    }
  };

  const handleDownloadXML = () => {
    if (!xmlPreview) return;

    const blob = new Blob([xmlPreview.content], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = xmlPreview.filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const totalAmount = transfers.reduce((sum, transfer) => 
    sum + (parseFloat(transfer.amount) || 0), 0
  );

  const isGenerating = bulkCreateMutation.isPending || generateXmlMutation.isPending;

  return (
    <div className="lg:pl-72">
      <div className="px-4 py-10 sm:px-6 lg:px-8 lg:py-6">
        <div className="border-b border-gray-200 pb-5">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
                Átutalások
              </h1>
              <p className="mt-2 max-w-4xl text-sm text-gray-500">
                Átutalások létrehozása, szerkesztése és XML generálás bank importáláshoz
              </p>
            </div>
            {transfers.length > 0 && (
              <div className="flex space-x-3">
                <div className="text-right">
                  <div className="text-sm text-gray-500">Összesen</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {totalAmount.toLocaleString('hu-HU')} HUF
                  </div>
                </div>
                <button
                  onClick={handleGenerateXML}
                  disabled={isGenerating || transfers.length === 0}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                  {isGenerating ? 'Generálás...' : 'XML Generálás'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Bank Account Info */}
        {defaultAccount && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <CheckCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-800">
                  Alapértelmezett számla
                </h4>
                <p className="text-sm text-blue-700">
                  {defaultAccount.name} - {defaultAccount.account_number}
                  {defaultAccount.bank_name && ` (${defaultAccount.bank_name})`}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800">
                  Validációs hibák
                </h4>
                <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Template Selector */}
        <div className="mt-8">
          <TemplateSelector
            templates={templates}
            selectedTemplate={selectedTemplate}
            onSelectTemplate={setSelectedTemplate}
            onLoadTemplate={handleLoadTemplate}
            isLoading={loadTemplateMutation.isPending}
          />
        </div>

        {/* Transfer Table */}
        <div className="mt-8">
          <TransferTable
            transfers={transfers}
            onUpdateTransfer={handleUpdateTransfer}
            onDeleteTransfer={handleDeleteTransfer}
            onAddTransfer={() => setShowAddModal(true)}
          />
        </div>

        {/* Workflow Steps */}
        {transfers.length > 0 && (
          <div className="mt-8 bg-gray-50 rounded-lg p-6">
            <h4 className="text-sm font-medium text-gray-900 mb-4">Következő lépések:</h4>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircleIcon className="w-4 h-4 text-green-600" />
                </div>
                <span className="ml-2 text-gray-700">Átutalások összeállítva</span>
              </div>
              <div className="flex items-center">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <PlayIcon className="w-4 h-4 text-blue-600" />
                </div>
                <span className="ml-2 text-gray-700">XML generálás</span>
              </div>
              <div className="flex items-center">
                <div className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center">
                  <DocumentArrowDownIcon className="w-4 h-4 text-gray-500" />
                </div>
                <span className="ml-2 text-gray-500">Letöltés és bank importálás</span>
              </div>
            </div>
          </div>
        )}

        {/* Add Transfer Modal */}
        <AddTransferModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddTransfer}
        />

        {/* XML Preview */}
        {xmlPreview && (
          <XMLPreview
            xmlContent={xmlPreview.content}
            filename={xmlPreview.filename}
            onClose={() => setXmlPreview(null)}
            onDownload={handleDownloadXML}
          />
        )}
      </div>
    </div>
  );
};

export default TransferWorkflow;