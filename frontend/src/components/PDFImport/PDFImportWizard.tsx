import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../hooks/useToast';
import { TransferTemplate } from '../../types/api';
import { UploadStep } from './UploadStep';
import { ReviewStep } from './ReviewStep';
import { TemplateStep } from './TemplateStep';
import { ProgressIndicator } from './ProgressIndicator';
import axios from 'axios';

interface PDFImportWizardProps {
  onComplete?: (template: TransferTemplate) => void;
}

export interface PDFProcessingResult {
  template: {
    id: number;
    name: string;
    beneficiary_count: number;
  };
  transactions_processed: number;
  beneficiaries_matched: number;
  beneficiaries_created: number;
  consolidations: string[];
  template_created: boolean;
  template_updated: boolean;
  preview: Array<{
    beneficiary_id: number | null;
    beneficiary_name: string;
    account_number: string;
    amount: number;
    remittance_info: string;
    execution_date: string;
    created_beneficiary: boolean;
  }>;
  total_amount: number;
}

export const PDFImportWizard: React.FC<PDFImportWizardProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [templateName, setTemplateName] = useState('');
  const [processing, setProcessing] = useState(false);
  const [previewData, setPreviewData] = useState<PDFProcessingResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const handleFilesSelected = (files: File[]) => {
    setSelectedFiles(files);
    setErrorMessage(null);
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
  };

  const handleProcessFiles = async () => {
    if (selectedFiles.length === 0) {
      setErrorMessage('Válasszon legalább egy PDF fájlt');
      return;
    }

    console.log('Starting PDF processing with files:', selectedFiles.map(f => f.name));
    setProcessing(true);
    setErrorMessage(null);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        console.log('Adding file to FormData:', file.name, file.size, file.type);
        formData.append('pdf_files', file);
      });

      if (templateName.trim()) {
        formData.append('template_name', templateName.trim());
        console.log('Template name:', templateName.trim());
      }

      console.log('Making API request to http://localhost:8000/api/templates/process_pdf/');
      const response = await axios.post('http://localhost:8000/api/templates/process_pdf/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('Success result:', response.data);
      setPreviewData(response.data);
      setCurrentStep(2);
      success('PDF fájlok sikeresen feldolgozva!');
    } catch (err: any) {
      console.error('PDF processing error:', err);
      if (err.response?.data) {
        const errorData = err.response.data;
        setErrorMessage(errorData.details || errorData.error || 'Hiba a PDF feldolgozás során');
      } else if (err.message) {
        setErrorMessage(`Hálózati hiba: ${err.message}`);
      } else {
        setErrorMessage('Váratlan hiba történt. Kérjük, próbálja újra.');
      }
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirmTemplate = () => {
    if (!previewData) return;
    
    setCurrentStep(3);
    
    // Show different success message based on whether template was created or updated
    if (previewData.template_updated) {
      success(`Sablon frissítve: ${previewData.template.name}`);
    } else {
      success(`Sablon létrehozva: ${previewData.template.name}`);
    }
    
    // Navigate to transfer workflow with the template
    setTimeout(() => {
      navigate(`/transfers?template=${previewData.template.id}`);
      if (onComplete) {
        onComplete(previewData.template as any);
      }
    }, 1500);
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCancel = () => {
    navigate('/templates');
  };

  const steps = [
    { number: 1, title: 'PDF Feltöltés', description: 'Fájlok kiválasztása' },
    { number: 2, title: 'Adatok Áttekintése', description: 'Tranzakciók ellenőrzése' },
    { number: 3, title: 'Sablon Kezelés', description: 'Létrehozás vagy frissítés' }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          PDF Importálás
        </h1>
        <p className="text-gray-600">
          Töltse fel a NAV adó és fizetési PDF fájljait automatikus sablon létrehozásához vagy meglévő sablon frissítéséhez
        </p>
      </div>

      {/* Progress Indicator */}
      <ProgressIndicator 
        steps={steps} 
        currentStep={currentStep} 
        className="mb-8"
      />

      {/* Error Display */}
      {errorMessage && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="text-red-400 mt-0.5">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="text-red-800 font-medium">Hiba</h3>
              <p className="text-red-700 text-sm mt-1">{errorMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 min-h-[500px]">
        {currentStep === 1 && (
          <UploadStep
            selectedFiles={selectedFiles}
            templateName={templateName}
            processing={processing}
            onFilesSelected={handleFilesSelected}
            onRemoveFile={handleRemoveFile}
            onTemplateNameChange={setTemplateName}
            onProcessFiles={handleProcessFiles}
            onCancel={handleCancel}
          />
        )}

        {currentStep === 2 && previewData && (
          <ReviewStep
            previewData={previewData}
            onBack={handleBack}
            onConfirm={handleConfirmTemplate}
          />
        )}

        {currentStep === 3 && previewData && (
          <TemplateStep
            previewData={previewData}
            onViewTemplate={() => navigate(`/templates/${previewData.template.id}`)}
            onCreateTransfers={() => navigate(`/transfers?template=${previewData.template.id}`)}
          />
        )}
      </div>
    </div>
  );
};