import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Stack,
  Card,
  CardContent,
  Avatar
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { 
  useTemplates, 
  useCreateTemplate, 
  useUpdateTemplate, 
  useDeleteTemplate,
  useLoadTemplate
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
  
  const navigate = useNavigate();

  const { data: templatesData, isLoading, refetch } = useTemplates();
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();
  const deleteMutation = useDeleteTemplate();
  const loadTemplateMutation = useLoadTemplate();

  const templates = templatesData?.results || [];

  const handleCreateTemplate = async (data: TemplateFormData) => {
    try {
      const templateData = {
        name: data.name,
        description: data.description,
        is_active: data.is_active,
      };
      
      await createMutation.mutateAsync(templateData);
      setShowForm(false);
      refetch();
      
      // TODO: Handle beneficiary associations after template creation
      // This would require additional API calls to associate beneficiaries with the template
    } catch (error) {
      console.error('Failed to create template:', error);
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
      
      setShowForm(false);
      setEditingTemplate(null);
      refetch();
      
      // TODO: Handle beneficiary associations update
    } catch (error) {
      console.error('Failed to update template:', error);
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

  const handleLoadTemplate = async (id: number) => {
    try {
      const result = await loadTemplateMutation.mutateAsync(id);
      
      // Navigate to transfers page with the loaded template data
      navigate('/transfers', { 
        state: { 
          templateData: result.data,
          loadedFromTemplate: true 
        } 
      });
    } catch (error) {
      console.error('Failed to load template:', error);
    }
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTemplate(null);
  };

  const handleViewClose = () => {
    setShowView(false);
    setViewingTemplate(null);
  };

  const isFormLoading = createMutation.isPending || updateMutation.isPending;

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
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowForm(true)}
          >
            Új sablon
          </Button>
        </Stack>
      </Box>

      {/* Stats */}
      <Box 
        sx={{ 
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(3, 1fr)'
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

        <Card elevation={1}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Avatar sx={{ bgcolor: 'info.main', width: 40, height: 40 }}>
                <Typography variant="body2" fontWeight="bold" color="white">
                  {templates.reduce((sum, t) => sum + t.beneficiary_count, 0)}
                </Typography>
              </Avatar>
              <Typography variant="body2" color="text.secondary">
                Összes kedvezményezett
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
    </Box>
  );
};

export default TemplateBuilder;