import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Stack,
  Card,
  CardContent,
  Avatar,
  Alert,
  Snackbar,
  FormControlLabel,
  Switch
} from '@mui/material';
import { Add as AddIcon, VisibilityOff as InactiveIcon } from '@mui/icons-material';
import { 
  useTemplates, 
  useCreateTemplate, 
  useUpdateTemplate, 
  useDeleteTemplate,
  useAddTemplateBeneficiary,
  useRemoveTemplateBeneficiary,
  useUpdateTemplateBeneficiary
} from '../../hooks/api';
import { TransferTemplate } from '../../types/api';
import TemplateList from './TemplateList';
import TemplateForm from './TemplateForm';
import TemplateView from './TemplateView';

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

const TemplateBuilder: React.FC = () => {
  const [showForm, setShowForm] = useState(false);
  const [showView, setShowView] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<TransferTemplate | null>(null);
  const [viewingTemplate, setViewingTemplate] = useState<TransferTemplate | null>(null);
  const [showInactive, setShowInactive] = useState(false);
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const navigate = useNavigate();

  const { data: templatesData, isLoading, refetch } = useTemplates(showInactive);
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();
  const deleteMutation = useDeleteTemplate();
  const addBeneficiaryMutation = useAddTemplateBeneficiary();
  const removeBeneficiaryMutation = useRemoveTemplateBeneficiary();
  const updateBeneficiaryMutation = useUpdateTemplateBeneficiary();

  const templates = templatesData?.results || [];

  const showNotification = (message: string, severity: 'success' | 'error' | 'info' | 'warning' = 'success') => {
    setNotification({ open: true, message, severity });
  };

  const hideNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  const handleCreateTemplate = async (data: TemplateFormData) => {
    try {
      console.log('Creating template with data:', data);
      
      const templateData = {
        name: data.name,
        description: data.description,
        is_active: data.is_active,
      };
      
      const result = await createMutation.mutateAsync(templateData);
      console.log('Template created successfully:', result);
      
      const createdTemplate = result.data;
      
      // Add beneficiaries to the template if any were selected
      if (data.beneficiaries && data.beneficiaries.length > 0) {
        console.log('Adding beneficiaries to template:', data.beneficiaries);
        
        for (let i = 0; i < data.beneficiaries.length; i++) {
          const beneficiary = data.beneficiaries[i];
          try {
            await addBeneficiaryMutation.mutateAsync({
              templateId: createdTemplate.id,
              data: {
                beneficiary_id: beneficiary.beneficiary_id,
                default_amount: beneficiary.default_amount ? parseFloat(beneficiary.default_amount) : undefined,
                default_remittance: beneficiary.default_remittance_info || undefined,
                order: i,
                is_active: true,
              }
            });
          } catch (beneficiaryError) {
            console.error(`Failed to add beneficiary ${beneficiary.beneficiary_id}:`, beneficiaryError);
            showNotification(`Figyelem: Nem sikerült hozzáadni minden kedvezményezettet a sablonhoz.`, 'warning');
          }
        }
      }
      
      setShowForm(false);
      refetch();
      showNotification(`Sablon "${data.name}" sikeresen létrehozva!`, 'success');
      
    } catch (error) {
      console.error('Failed to create template:', error);
      showNotification('Hiba történt a sablon létrehozása során.', 'error');
    }
  };

  const handleUpdateTemplate = async (data: TemplateFormData) => {
    if (!editingTemplate) return;
    
    try {
      const templateData = {
        name: data.name,
        description: data.description,
        is_active: data.is_active,
      };
      
      await updateMutation.mutateAsync({
        id: editingTemplate.id,
        data: templateData,
      });
      
      // Handle beneficiary associations update when editing templates
      const currentBeneficiaryIds = new Set(
        editingTemplate.template_beneficiaries?.map(tb => tb.beneficiary.id) || []
      );
      const newBeneficiaryIds = new Set(
        data.beneficiaries.map(b => b.beneficiary_id)
      );
      
      // Remove beneficiaries that are no longer selected
      for (const currentBeneficiaryId of Array.from(currentBeneficiaryIds)) {
        if (!newBeneficiaryIds.has(currentBeneficiaryId)) {
          try {
            await removeBeneficiaryMutation.mutateAsync({
              templateId: editingTemplate.id,
              beneficiaryId: currentBeneficiaryId
            });
          } catch (error) {
            console.error(`Failed to remove beneficiary ${currentBeneficiaryId}:`, error);
          }
        }
      }
      
      // Handle beneficiaries (add new ones and update existing ones)
      for (let i = 0; i < data.beneficiaries.length; i++) {
        const beneficiary = data.beneficiaries[i];
        
        if (!currentBeneficiaryIds.has(beneficiary.beneficiary_id)) {
          // Add new beneficiaries
          try {
            await addBeneficiaryMutation.mutateAsync({
              templateId: editingTemplate.id,
              data: {
                beneficiary_id: beneficiary.beneficiary_id,
                default_amount: beneficiary.default_amount ? parseFloat(beneficiary.default_amount) : undefined,
                default_remittance: beneficiary.default_remittance_info || undefined,
                order: i,
                is_active: true,
              }
            });
          } catch (error) {
            console.error(`Failed to add beneficiary ${beneficiary.beneficiary_id}:`, error);
          }
        } else {
          // Update existing beneficiaries (order, amount, remittance info)
          try {
            await updateBeneficiaryMutation.mutateAsync({
              templateId: editingTemplate.id,
              data: {
                beneficiary_id: beneficiary.beneficiary_id,
                default_amount: beneficiary.default_amount ? parseFloat(beneficiary.default_amount) : undefined,
                default_remittance: beneficiary.default_remittance_info || undefined,
                order: i,
                is_active: true,
              }
            });
          } catch (error) {
            console.error(`Failed to update beneficiary ${beneficiary.beneficiary_id}:`, error);
          }
        }
      }
      
      setShowForm(false);
      setEditingTemplate(null);
      refetch();
      showNotification(`Sablon "${data.name}" sikeresen frissítve!`, 'success');
    } catch (error) {
      console.error('Failed to update template:', error);
      showNotification('Hiba történt a sablon frissítése során.', 'error');
    }
  };

  const handleDeleteTemplate = async (id: number) => {
    if (window.confirm('Biztosan törölni szeretné ezt a sablont?')) {
      try {
        await deleteMutation.mutateAsync(id);
        refetch();
      } catch (error) {
        console.error('Failed to delete template:', error);
      }
    }
  };

  const handleEditTemplate = (template: TransferTemplate) => {
    setEditingTemplate(template);
    setShowForm(true);
  };

  const handleViewTemplate = (template: TransferTemplate) => {
    setViewingTemplate(template);
    setShowView(true);
  };

  const handleLoadTemplate = (id: number) => {
    // Navigate to transfers page with template ID - let TransferWorkflow handle the loading
    navigate('/transfers', { 
      state: { 
        templateId: id,
        loadFromTemplate: true 
      } 
    });
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTemplate(null);
  };

  const handleViewClose = () => {
    setShowView(false);
    setViewingTemplate(null);
  };

  const isFormLoading = createMutation.isPending || updateMutation.isPending || addBeneficiaryMutation.isPending || removeBeneficiaryMutation.isPending;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 3, mb: 4 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={3}>
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
              Sablonok
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Átutalási sablonok létrehozása és kezelése ismétlődő fizetésekhez
            </Typography>
          </Box>
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControlLabel
              control={
                <Switch
                  checked={showInactive}
                  onChange={(e) => setShowInactive(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Stack direction="row" alignItems="center" spacing={1}>
                  <InactiveIcon sx={{ fontSize: 16 }} />
                  <Typography variant="body2">
                    Inaktív sablonok
                  </Typography>
                </Stack>
              }
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowForm(true)}
            >
              Új sablon
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Stats */}
      <Box 
        sx={{ 
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: showInactive ? 'repeat(4, 1fr)' : 'repeat(3, 1fr)'
          },
          gap: 3,
          mb: 4
        }}
      >
        <Card elevation={1}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>
                <Typography variant="body2" fontWeight="bold" color="white">
                  {templates.length}
                </Typography>
              </Avatar>
              <Typography variant="body2" color="text.secondary">
                Összes sablon
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        <Card elevation={1}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Avatar sx={{ bgcolor: 'success.main', width: 40, height: 40 }}>
                <Typography variant="body2" fontWeight="bold" color="white">
                  {templates.filter(t => t.is_active).length}
                </Typography>
              </Avatar>
              <Typography variant="body2" color="text.secondary">
                Aktív sablonok
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        {showInactive && (
          <Card elevation={1}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'warning.main', width: 40, height: 40 }}>
                  <Typography variant="body2" fontWeight="bold" color="white">
                    {templates.filter(t => !t.is_active).length}
                  </Typography>
                </Avatar>
                <Typography variant="body2" color="text.secondary">
                  Inaktív sablonok
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        )}

        <Card elevation={1}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Avatar sx={{ bgcolor: 'info.main', width: 40, height: 40 }}>
                <Typography variant="body2" fontWeight="bold" color="white">
                  {templates.reduce((sum, t) => sum + (showInactive || t.is_active ? t.beneficiary_count : 0), 0)}
                </Typography>
              </Avatar>
              <Typography variant="body2" color="text.secondary">
                Kedvezményezettek
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Box>

      {/* Template List */}
      <TemplateList
        templates={templates}
        isLoading={isLoading}
        onEdit={handleEditTemplate}
        onDelete={handleDeleteTemplate}
        onView={handleViewTemplate}
        onLoadTemplate={handleLoadTemplate}
      />

      {/* Template Form Modal */}
      <TemplateForm
        isOpen={showForm}
        onClose={handleFormClose}
        onSubmit={editingTemplate ? handleUpdateTemplate : handleCreateTemplate}
        template={editingTemplate}
        isLoading={isFormLoading}
      />

      {/* Template View Modal */}
      <TemplateView
        isOpen={showView}
        onClose={handleViewClose}
        template={viewingTemplate}
      />

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={hideNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={hideNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default TemplateBuilder;