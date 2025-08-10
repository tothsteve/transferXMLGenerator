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
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 3, mb: 4 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={3}>
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
              Átutalások
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Átutalások létrehozása, szerkesztése és XML generálás bank importáláshoz
            </Typography>
          </Box>
          {transfers.length > 0 && (
            <Stack direction="row" alignItems="center" spacing={2}>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body2" color="text.secondary">
                  Összesen
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {totalAmount.toLocaleString('hu-HU')} HUF
                </Typography>
              </Box>
              <Button
                variant="contained"
                color="success"
                startIcon={<DownloadIcon />}
                onClick={handleGenerateXML}
                disabled={isGenerating || transfers.length === 0}
              >
                {isGenerating ? 'Generálás...' : 'XML Generálás'}
              </Button>
            </Stack>
          )}
        </Stack>
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

      {/* Transfer Table */}
      <Box sx={{ mb: 4 }}>
        <TransferTable
          transfers={transfers}
          onUpdateTransfer={handleUpdateTransfer}
          onDeleteTransfer={handleDeleteTransfer}
          onAddTransfer={() => setShowAddModal(true)}
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