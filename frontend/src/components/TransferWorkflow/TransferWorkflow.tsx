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
  useBulkUpdateTransfers,
  useGenerateXml,
  useGenerateKHExport,
  useDefaultBankAccount,
  useBeneficiaries,
  useCreateBeneficiary
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
  const { data: beneficiariesData, isLoading: beneficiariesLoading } = useBeneficiaries({ page: 1 });
  const loadTemplateMutation = useLoadTemplate();
  const bulkCreateMutation = useBulkCreateTransfers();
  const bulkUpdateMutation = useBulkUpdateTransfers();
  const generateXmlMutation = useGenerateXml();
  const generateKHExportMutation = useGenerateKHExport();
  const createBeneficiaryMutation = useCreateBeneficiary();

  const templates = templatesData?.results || [];
  const beneficiaries = beneficiariesData?.results || [];

  // Handle preloaded transfers from NAV invoices
  useEffect(() => {
    const state = location.state as any;
    if (state?.preloadedTransfers && state?.source === 'nav_invoices') {
      console.log('Loading preloaded transfers from NAV invoices:', state.preloadedTransfers);
      
      // Convert preloaded data to TransferData format
      const convertedTransfers: TransferData[] = state.preloadedTransfers.map((transfer: any, index: number) => ({
        tempId: `nav_${index}`,
        beneficiary: transfer.beneficiary_id, // null initially
        beneficiary_data: transfer.beneficiary_id ? undefined : {
          id: 0,
          name: transfer.beneficiary_name,
          account_number: transfer.account_number,
          description: `From NAV: ${transfer.remittance_info}`,
          remittance_information: transfer.remittance_info,
          is_frequent: false,
          is_active: true,
        },
        amount: transfer.amount,
        currency: transfer.currency as 'HUF' | 'EUR' | 'USD',
        execution_date: transfer.execution_date,
        remittance_info: transfer.remittance_info,
        order: transfer.order,
        is_processed: false,
      }));

      setTransfers(convertedTransfers);
      // Clear the location state so it doesn't reload on refresh
      window.history.replaceState({}, document.title);
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

  // Handle template data passed from TemplateBuilder or preloaded transfers from NAV
  useEffect(() => {
    const state = location.state as { 
      templateData?: LoadTemplateResponse; 
      loadedFromTemplate?: boolean;
      templateId?: number;
      loadFromTemplate?: boolean;
      preloadedTransfers?: any[];
      source?: string;
    } | null;
    
    // Handle direct template data (from previous workflow)
    if (state?.templateData && state.loadedFromTemplate) {
      setSelectedTemplate(state.templateData.template);
      setTransfers(state.templateData.transfers.map((transfer, index) => ({
        ...transfer,
        tempId: `temp-${index}`,
      })));
      
      // Clear the location state to prevent re-loading on refresh
      window.history.replaceState({}, '');
    }
    // Handle template ID from TemplateBuilder "Betöltés" button
    else if (state?.templateId && state.loadFromTemplate && templates.length > 0 && defaultAccount) {
      const template = templates.find(t => t.id === state.templateId);
      if (template) {
        console.log('Auto-loading template from TemplateBuilder:', template);
        setSelectedTemplate(template);
        handleLoadTemplate(state.templateId);
      }
      
      // Clear the location state to prevent re-loading on refresh
      window.history.replaceState({}, '');
    }
    // Handle preloaded transfers from NAV invoices
    else if (state?.preloadedTransfers && state.source === 'nav_invoices' && defaultAccount) {
      console.log('Loading preloaded transfers from NAV invoices:', state.preloadedTransfers);
      
      const navTransfers = state.preloadedTransfers.map((transfer, index) => ({
        ...transfer,
        tempId: `nav-${index}`,
        originator_account: defaultAccount.id,
        // Keep beneficiary_id as null initially - will be resolved before saving
      }));
      
      setTransfers(navTransfers);
      
      // Clear the location state to prevent re-loading on refresh
      window.history.replaceState({}, '');
    }
  }, [location.state, templates, defaultAccount]);

  // Handle template parameter from URL (e.g., /transfers?template=123)
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const templateIdParam = searchParams.get('template');
    
    if (templateIdParam && templates.length > 0 && defaultAccount && !selectedTemplate) {
      const templateId = parseInt(templateIdParam, 10);
      const template = templates.find(t => t.id === templateId);
      
      if (template) {
        console.log('Auto-loading template from URL parameter:', template);
        setSelectedTemplate(template);
        handleLoadTemplate(templateId);
        
        // Remove the template parameter from URL to clean it up
        searchParams.delete('template');
        const newUrl = `${location.pathname}${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
        window.history.replaceState({}, '', newUrl);
      }
    }
  }, [location.search, templates, defaultAccount, selectedTemplate]);

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
        // For NAV transfers, check if we have beneficiary_name and account_number
        if (!(transfer as any).beneficiary_name || !(transfer as any).account_number) {
          errors.push(`${index + 1}. átutalás: Kedvezményezettet kell választani`);
        }
      }
    });

    return errors;
  };

  // Helper function to resolve beneficiaries for NAV transfers
  const resolveBeneficiariesForTransfers = async (transfersToProcess: TransferData[]) => {
    const resolvedTransfers = [...transfersToProcess];
    
    for (let i = 0; i < resolvedTransfers.length; i++) {
      const transfer = resolvedTransfers[i] as any;
      
      // Skip if beneficiary is already set
      if (transfer.beneficiary) continue;
      
      // Skip if we don't have the required NAV transfer data
      if (!transfer.beneficiary_name || !transfer.account_number) continue;
      
      console.log(`Resolving beneficiary for NAV transfer: ${transfer.beneficiary_name}`);
      
      // Try to find existing beneficiary by account number (most reliable match)
      let matchingBeneficiary = beneficiaries.find(b => 
        b.account_number === transfer.account_number && b.is_active
      );
      
      // If not found by account number, try to find by name
      if (!matchingBeneficiary) {
        matchingBeneficiary = beneficiaries.find(b => 
          b.name.toLowerCase() === transfer.beneficiary_name!.toLowerCase() && b.is_active
        );
      }
      
      if (matchingBeneficiary) {
        // Use existing beneficiary
        resolvedTransfers[i] = {
          ...transfer,
          beneficiary: matchingBeneficiary.id,
        };
        console.log(`Matched existing beneficiary for ${transfer.beneficiary_name}:`, matchingBeneficiary);
      } else {
        // Create new beneficiary
        try {
          console.log(`Creating new beneficiary for NAV transfer: ${transfer.beneficiary_name}`);
          const newBeneficiary = await createBeneficiaryMutation.mutateAsync({
            name: transfer.beneficiary_name!,
            account_number: transfer.account_number!,
            description: 'NAV számla alapján automatikusan létrehozva',
            is_active: true,
            is_frequent: false,
            remittance_information: '',
          });
          
          resolvedTransfers[i] = {
            ...transfer,
            beneficiary: newBeneficiary.data.id,
          };
          console.log(`Created new beneficiary for ${transfer.beneficiary_name}:`, newBeneficiary.data);
        } catch (error) {
          console.error(`Failed to create beneficiary for ${transfer.beneficiary_name}:`, error);
          throw new Error(`Nem sikerült létrehozni a kedvezményezettet: ${transfer.beneficiary_name}`);
        }
      }
    }
    
    return resolvedTransfers;
  };

  const handleSaveTransfers = async (): Promise<false | number[]> => {
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
      // First, resolve beneficiaries for any NAV transfers
      console.log('Resolving beneficiaries for NAV transfers if needed...');
      const resolvedTransfers = await resolveBeneficiariesForTransfers(transfers);
      
      // Update the transfers state with resolved beneficiaries
      setTransfers(resolvedTransfers);
      
      // Separate transfers into create and update groups
      const transfersToCreate = resolvedTransfers.filter(t => !t.id);
      const transfersToUpdate = resolvedTransfers.filter(t => t.id);
      
      console.log('Transfers to create:', transfersToCreate.length);
      console.log('Transfers to update:', transfersToUpdate.length);
      
      // Collect all transfer IDs that will be available after saving
      const allTransferIds: number[] = [];
      
      // Step 1: Create new transfers
      let createdTransfers: any[] = [];
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
        
        console.log('Sending create payload to backend:', { transfers: transfersPayload });
        
        const bulkResult = await bulkCreateMutation.mutateAsync({
          transfers: transfersPayload,
        });
        
        console.log('Bulk create response:', bulkResult);
        
        // Handle the response structure - check if it's wrapped or direct array
        const responseData: any = bulkResult.data;
        createdTransfers = Array.isArray(responseData) 
          ? responseData 
          : responseData?.transfers || responseData?.results || [];
        
        console.log('Created transfers:', createdTransfers);
        
        // Add created transfer IDs
        createdTransfers.forEach(transfer => {
          if (transfer.id) {
            allTransferIds.push(transfer.id);
          }
        });
      }
      
      // Step 2: Update existing transfers with current order and modifications
      if (transfersToUpdate.length > 0) {
        console.log('Updating transfers:', transfersToUpdate);
        
        const updatePayloads = transfersToUpdate.map(t => ({
          id: t.id!,
          data: {
            beneficiary: t.beneficiary,
            amount: parseFloat(t.amount).toFixed(2),
            currency: t.currency,
            execution_date: t.execution_date,
            remittance_info: t.remittance_info,
            order: transfers.indexOf(t), // Update order based on current UI position
          }
        }));
        
        console.log('Sending update payloads to backend:', updatePayloads);
        
        await bulkUpdateMutation.mutateAsync(updatePayloads);
        console.log('Bulk updates completed');
        
        // Add existing transfer IDs (they already exist)
        transfersToUpdate.forEach(t => {
          if (t.id) {
            allTransferIds.push(t.id);
          }
        });
      }
      
      // Step 3: Update state with newly created transfers (for UI consistency)
      if (createdTransfers.length > 0) {
        const newTransfers = createdTransfers.map((createdTransfer: any, index: number) => ({
          ...transfersToCreate[index],
          id: createdTransfer.id,
        }));
        
        // Update the transfers state with the created transfer IDs
        setTransfers(prev => prev.map(t => {
          if (!t.id) {
            // Find the corresponding created transfer
            const matchingCreated = newTransfers.find(nt => 
              nt.beneficiary === t.beneficiary && 
              nt.amount === t.amount &&
              nt.execution_date === t.execution_date
            );
            return matchingCreated || t;
          }
          return t;
        }));
      }
      
      console.log('All transfers saved successfully');
      console.log('Transfer IDs for XML generation:', allTransferIds);
      return allTransferIds;
      
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
    // First, ensure all transfers are saved and get their IDs
    const transferIds = await handleSaveTransfers();
    if (!transferIds) return;

    try {
      console.log('Transfer IDs for XML generation:', transferIds);
      
      if (transferIds.length === 0) {
        setValidationErrors(['Nincsenek mentett átutalások a generáláshoz.']);
        return;
      }
      
      // Use the returned transfer IDs directly instead of reading from state
      console.log('Calling XML generation with IDs:', transferIds);
      
      // Generate batch name with current date and time
      const now = new Date();
      const batchName = `Átutalás ${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      const xmlResult = await generateXmlMutation.mutateAsync({
        transfer_ids: transferIds,
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
                          'Hiba történt a generálás során.';
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

  const handleGenerateKHExport = async () => {
    // First, ensure all transfers are saved and get their IDs
    const transferIds = await handleSaveTransfers();
    if (!transferIds) return;

    try {
      console.log('Transfer IDs for KH export:', transferIds);
      
      if (transferIds.length === 0) {
        setValidationErrors(['Nincsenek mentett átutalások a KH export generálásához.']);
        return;
      }
      
      // Check if more than 40 transfers (KH Bank limit)
      if (transferIds.length > 40) {
        setValidationErrors([`KH Bank maximum 40 átutalást támogat, de ${transferIds.length} átutalás található.`]);
        return;
      }
      
      // Use the returned transfer IDs directly instead of reading from state
      console.log('Calling KH export generation with IDs:', transferIds);
      
      // Generate batch name with current date and time
      const now = new Date();
      const batchName = `KH Export ${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      const khResult = await generateKHExportMutation.mutateAsync({
        transfer_ids: transferIds,
        batch_name: batchName,
      });
      
      console.log('KH export result:', khResult);
      
      // Automatically download the file with proper ISO-8859-2 encoding
      let blob;
      if (khResult.data.content_encoding === 'base64') {
        // Decode base64 content to get ISO-8859-2 encoded bytes
        const binaryString = atob(khResult.data.content);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        blob = new Blob([bytes], { type: 'text/csv' });
      } else {
        // Fallback for non-base64 content
        blob = new Blob([khResult.data.content], { type: 'text/csv; charset=utf-8' });
      }
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = khResult.data.filename;
      link.click();
      URL.revokeObjectURL(url);
      
      setValidationErrors([]);
      console.log(`KH Bank export sikeresen generálva: ${khResult.data.transfer_count} átutalás, ${parseFloat(khResult.data.total_amount).toLocaleString('hu-HU')} HUF`);
      
    } catch (error: any) {
      console.error('KH export generation failed:', error);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.detail || 
                          'Hiba történt a KH export generálása során.';
      setValidationErrors([errorMessage]);
    }
  };

  const totalAmount = transfers.reduce((sum, transfer) => 
    sum + (parseFloat(transfer.amount) || 0), 0
  );

  const isGenerating = bulkCreateMutation.isPending || bulkUpdateMutation.isPending || generateXmlMutation.isPending || generateKHExportMutation.isPending;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 3, mb: 4 }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
            Átutalások
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Átutalások létrehozása, szerkesztése és generálás bank importáláshoz
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
                {bulkCreateMutation.isPending ? 'Új átutalások mentése...' : 
                 bulkUpdateMutation.isPending ? 'Változások mentése...' :
                 generateXmlMutation.isPending ? 'Generálás...' : 
                 'Generálás'}
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<DownloadIcon />}
                onClick={handleGenerateKHExport}
                disabled={isGenerating || transfers.length === 0}
                sx={{ 
                  minWidth: 160,
                  background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
                  boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 6px 16px rgba(25, 118, 210, 0.4)',
                  }
                }}
              >
                {generateKHExportMutation.isPending ? 'KH Export...' : 'KH Bank Export'}
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
                Generálás
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