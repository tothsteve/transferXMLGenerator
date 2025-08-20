import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Alert,
  AlertTitle,
  Paper,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { useToast } from '../../hooks/useToast';
import { TransferTemplate } from '../../types/api';
import { UploadStep } from './UploadStep';
import { ReviewStep } from './ReviewStep';
import { TemplateStep } from './TemplateStep';
import { apiClient } from '../../services/api';

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
  const { success } = useToast();

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

      console.log('Making API request to /templates/process_pdf/');
      const response = await apiClient.post('/templates/process_pdf/', formData, {
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

  const handleConfirmTemplate = async () => {
    if (!previewData) return;
    
    try {
      // Verify the template actually exists in the database
      const response = await apiClient.get(`/templates/${previewData.template.id}/`);
      
      if (response.data) {
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
            onComplete(response.data);
          }
        }, 1500);
      }
    } catch (error: any) {
      console.error('Template verification failed:', error);
      setErrorMessage(`Hiba: A sablon nem található az adatbázisban. ${error.response?.data?.detail || error.message}`);
    }
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
    <Box sx={{ p: { xs: 2, sm: 3 }, maxWidth: '100%', mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 2, mb: 3 }}>
        <Typography variant="h5" component="h1" fontWeight="bold" gutterBottom>
          PDF Importálás
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
          Töltse fel a NAV adó és fizetési PDF fájljait automatikus sablon létrehozásához vagy meglévő sablon frissítéséhez
        </Typography>
      </Box>

      {/* Progress Stepper */}
      <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: { xs: 2, sm: 3 }, mb: 3, border: 1, borderColor: 'grey.200' }}>
        <Stepper activeStep={currentStep - 1} sx={{ width: '100%' }} orientation="horizontal">
          {steps.map((step) => (
            <Step key={step.number}>
              <StepLabel>
                <Typography variant="body2" fontWeight={600} sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {step.title}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', md: 'block' } }}>
                  {step.description}
                </Typography>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Error Display */}
      {errorMessage && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Hiba</AlertTitle>
          {errorMessage}
        </Alert>
      )}

      {/* Step Content */}
      <Paper elevation={1} sx={{ minHeight: { xs: 400, sm: 500 } }}>
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
      </Paper>
    </Box>
  );
};