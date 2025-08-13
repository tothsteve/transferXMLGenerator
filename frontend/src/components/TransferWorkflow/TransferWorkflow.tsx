import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Paper,
  Stepper,
  Step,
  StepLabel,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import {
  Download as DownloadIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayIcon
} from '@mui/icons-material';
import { 
  useTemplates, 
  useLoadTemplate, 
  useBulkCreateTransfers, 
  useGenerateXml,
  useDefaultBankAccount,
  useBeneficiaries
} from '../../hooks/api';
import { Transfer, TransferTemplate, LoadTemplateResponse, Beneficiary } from '../../types/api';
import TemplateSelector from './TemplateSelector';
import TransferTable from './TransferTable';
import AddTransferModal from './AddTransferModal';
import XMLPreview from './XMLPreview';

interface TransferData extends Omit<Transfer, 'id' | 'is_processed' | 'created_at'> {
  id?: number;
  tempId?: string;
  beneficiary_data?: Beneficiary;
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
  const { data: beneficiariesData } = useBeneficiaries();
  const loadTemplateMutation = useLoadTemplate();
  const bulkCreateMutation = useBulkCreateTransfers();
  const generateXmlMutation = useGenerateXml();

  const templates = templatesData?.results || [];
  const beneficiaries = beneficiariesData?.results || [];

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
    if (!defaultAccount) {
      console.error('No default account available for template loading');
      return;
    }

    try {
      // Use today's date as default execution date
      const today = new Date().toISOString().split('T')[0];
      
      const result = await loadTemplateMutation.mutateAsync({
        templateId,
        data: {
          template_id: templateId,
          originator_account_id: defaultAccount.id,
          execution_date: today,
        }
      });
      
      console.log('Template loading response:', result.data);
      console.log('Loaded transfers:', result.data.transfers);
      
      // Enrich transfers with beneficiary data
      const enrichedTransfers = result.data.transfers.map((transfer: any, index: number) => {
        const beneficiaryData = beneficiaries.find(b => b.id === transfer.beneficiary);
        console.log(`Transfer ${index}: beneficiary ID ${transfer.beneficiary}, found data:`, beneficiaryData);
        
        return {
          ...transfer,
          tempId: `temp-${index}`,
          beneficiary_data: beneficiaryData,
        };
      });
      
      console.log('Enriched transfers:', enrichedTransfers);
      setTransfers(enrichedTransfers);
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

  const handleReorderTransfers = (reorderedTransfers: TransferData[]) => {
    setTransfers(reorderedTransfers);
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

  const handleSaveTransfers = async () => {
    const errors = validateTransfers();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return false;
    }

    if (!defaultAccount) {
      setValidationErrors(['Nem található alapértelmezett számla az átutalások mentéséhez.']);
      return false;
    }

    try {
      // Create all transfers that don't have IDs yet
      const transfersToCreate = transfers.filter(t => !t.id);
      
      if (transfersToCreate.length > 0) {
        console.log('Creating transfers:', transfersToCreate);
        
        const transfersPayload = transfersToCreate.map((t, index) => ({
          originator_account_id: defaultAccount!.id,
          beneficiary_id: t.beneficiary,
          amount: parseFloat(t.amount).toFixed(2),
          currency: t.currency,
          execution_date: t.execution_date,
          remittance_info: t.remittance_info,
          order: transfers.indexOf(t), // Preserve the order from the UI
        }));
        
        console.log('Sending payload to backend:', { transfers: transfersPayload });
        
        const bulkResult = await bulkCreateMutation.mutateAsync({
          transfers: transfersPayload,
        });
        
        console.log('Bulk create response:', bulkResult);
        console.log('Response data:', bulkResult.data);
        
        // Handle the response structure - check if it's wrapped or direct array
        const responseData: any = bulkResult.data;
        const createdTransfers = Array.isArray(responseData) 
          ? responseData 
          : responseData?.transfers || responseData?.results || [];
        
        console.log('Created transfers:', createdTransfers);
        
        // Update the transfers state with the created transfer IDs
        const newTransfers = createdTransfers.map((createdTransfer: any, index: number) => ({
          ...transfersToCreate[index],
          id: createdTransfer.id,
        }));
        
        // Replace the unsaved transfers with saved ones
        setTransfers(prev => [
          ...prev.filter(t => t.id), // Keep existing saved transfers
          ...newTransfers // Add newly saved transfers
        ]);
      }
      
      return true;
    } catch (error: any) {
      console.error('Failed to save transfers:', error);
      console.error('Error response:', error.response?.data);
      
      // Handle validation errors from backend
      let errorMessages: string[] = [];
      
      if (error.response?.data?.transfers) {
        // Backend returned field-specific errors for each transfer
        const transferErrors = error.response.data.transfers;
        transferErrors.forEach((transferError: any, index: number) => {
          if (transferError) {
            Object.keys(transferError).forEach(field => {
              const fieldErrors = transferError[field];
              if (Array.isArray(fieldErrors)) {
                fieldErrors.forEach(err => {
                  errorMessages.push(`${index + 1}. átutalás - ${field}: ${err}`);
                });
              }
            });
          }
        });
      }
      
      if (errorMessages.length === 0) {
        const errorMessage = error.response?.data?.detail || 
                            error.response?.data?.message || 
                            'Hiba történt az átutalások mentése során.';
        errorMessages = [errorMessage];
      }
      
      setValidationErrors(errorMessages);
      return false;
    }
  };

  const handleGenerateXML = async () => {
    // First, ensure all transfers are saved
    const saveSuccess = await handleSaveTransfers();
    if (!saveSuccess) return;

    try {
      // Get all transfer IDs (now all should have IDs)
      const allTransferIds = transfers
        .filter(t => t.id)
        .map(t => t.id!);

      console.log('Current transfers state:', transfers);
      console.log('Transfer IDs for XML generation:', allTransferIds);

      if (allTransferIds.length === 0) {
        setValidationErrors(['Nincsenek mentett átutalások az XML generáláshoz.']);
        return;
      }

      // Generate XML from saved transfers
      console.log('Calling XML generation with IDs:', allTransferIds);
      
      // Generate batch name with current date and time
      const now = new Date();
      const batchName = `Átutalás ${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      const xmlResult = await generateXmlMutation.mutateAsync({
        transfer_ids: allTransferIds,
        batch_name: batchName,
      });

      console.log('XML generation response:', xmlResult);
      console.log('XML content:', xmlResult.data);

      setXmlPreview({
        content: xmlResult.data.xml,
        filename: `transfers_${new Date().toISOString().split('T')[0]}.xml`,
      });

    } catch (error: any) {
      console.error('Failed to generate XML:', error);
      console.error('Error response:', error.response?.data);
      
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          'Hiba történt az XML generálása során.';
      setValidationErrors([errorMessage]);
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
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 3, mb: 4 }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
            Átutalások
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Átutalások létrehozása, szerkesztése és XML generálás bank importáláshoz
          </Typography>
        </Box>
      </Box>

      {/* Bank Account Info */}
      {defaultAccount && (
        <Alert severity="info" icon={<CheckCircleIcon />} sx={{ mb: 3 }}>
          <AlertTitle>Alapértelmezett számla</AlertTitle>
          <Typography variant="body2">
            {defaultAccount.name} - {defaultAccount.account_number}
            {defaultAccount.bank_name && ` (${defaultAccount.bank_name})`}
          </Typography>
        </Alert>
      )}

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert severity="error" icon={<WarningIcon />} sx={{ mb: 3 }}>
          <AlertTitle>Validációs hibák</AlertTitle>
          <List dense sx={{ pt: 1 }}>
            {validationErrors.map((error, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.25 }}>
                <ListItemText primary={`• ${error}`} />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Template Selector */}
      <Box sx={{ mb: 4 }}>
        <TemplateSelector
          templates={templates}
          selectedTemplate={selectedTemplate}
          onSelectTemplate={setSelectedTemplate}
          onLoadTemplate={handleLoadTemplate}
          isLoading={loadTemplateMutation.isPending}
        />
      </Box>

      {/* Action Buttons and Total Amount */}
      {transfers.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Stack 
            direction={{ xs: 'column', sm: 'row' }} 
            justifyContent="space-between" 
            alignItems={{ xs: 'stretch', sm: 'center' }} 
            spacing={3}
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: 3,
            }}
          >
            <Box sx={{ textAlign: { xs: 'center', sm: 'left' } }}>
              <Typography variant="body2" color="text.secondary">
                Összesen
              </Typography>
              <Typography variant="h5" fontWeight="bold" sx={{ color: 'success.dark' }}>
                {totalAmount.toLocaleString('hu-HU')} HUF
              </Typography>
            </Box>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button
                variant="outlined"
                color="primary"
                onClick={handleSaveTransfers}
                disabled={isGenerating || transfers.length === 0}
                sx={{ 
                  minWidth: 160,
                  borderWidth: 2,
                  '&:hover': { borderWidth: 2 }
                }}
              >
                {bulkCreateMutation.isPending ? 'Mentés...' : 'Átutalások mentése'}
              </Button>
              <Button
                variant="contained"
                color="success"
                startIcon={<DownloadIcon />}
                onClick={handleGenerateXML}
                disabled={isGenerating || transfers.length === 0}
                sx={{ 
                  minWidth: 160,
                  background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
                  boxShadow: '0 4px 12px rgba(5, 150, 105, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #047857 0%, #059669 100%)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 6px 16px rgba(5, 150, 105, 0.4)',
                  }
                }}
              >
                {isGenerating ? 'Generálás...' : 'XML Generálás'}
              </Button>
            </Stack>
          </Stack>
        </Box>
      )}

      {/* Transfer Table */}
      <Box sx={{ mb: 4 }}>
        <TransferTable
          transfers={transfers}
          onUpdateTransfer={handleUpdateTransfer}
          onDeleteTransfer={handleDeleteTransfer}
          onAddTransfer={() => setShowAddModal(true)}
          onReorderTransfers={handleReorderTransfers}
        />
      </Box>

      {/* Workflow Steps */}
      {transfers.length > 0 && (
        <Paper sx={{ p: 3, bgcolor: 'grey.50', mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Következő lépések:
          </Typography>
          <Stepper orientation="horizontal" sx={{ pt: 2 }}>
            <Step completed>
              <StepLabel icon={<CheckCircleIcon sx={{ color: 'success.main' }} />}>
                Átutalások összeállítva
              </StepLabel>
            </Step>
            <Step active={!xmlPreview}>
              <StepLabel icon={<PlayIcon sx={{ color: xmlPreview ? 'success.main' : 'primary.main' }} />}>
                XML generálás
              </StepLabel>
            </Step>
            <Step>
              <StepLabel icon={<DownloadIcon sx={{ color: 'text.disabled' }} />}>
                Letöltés és bank importálás
              </StepLabel>
            </Step>
          </Stepper>
        </Paper>
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
    </Box>
  );
};

export default TransferWorkflow;