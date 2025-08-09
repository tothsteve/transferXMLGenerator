import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon } from '@heroicons/react/24/outline';
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
    <div className="lg:pl-72">
      <div className="px-4 py-10 sm:px-6 lg:px-8 lg:py-6">
        <div className="border-b border-gray-200 pb-5">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
                Sablonok
              </h1>
              <p className="mt-2 max-w-4xl text-sm text-gray-500">
                Átutalási sablonok létrehozása és kezelése ismétlődő fizetésekhez
              </p>
            </div>
            <div>
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Új sablon
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-3">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-primary-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">{templates.length}</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Összes sablon
                    </dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {templates.filter(t => t.is_active).length}
                    </span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Aktív sablonok
                    </dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {templates.reduce((sum, t) => sum + t.beneficiary_count, 0)}
                    </span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Összes kedvezményezett
                    </dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Template List */}
        <div className="mt-8">
          <TemplateList
            templates={templates}
            isLoading={isLoading}
            onEdit={handleEditTemplate}
            onDelete={handleDeleteTemplate}
            onView={handleViewTemplate}
            onLoadTemplate={handleLoadTemplate}
          />
        </div>

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
      </div>
    </div>
  );
};

export default TemplateBuilder;