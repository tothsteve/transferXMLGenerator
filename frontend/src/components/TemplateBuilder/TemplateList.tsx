import React from 'react';
import { 
  PencilIcon, 
  TrashIcon, 
  PlayIcon,
  EyeIcon,
  CalendarIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { TransferTemplate } from '../../types/api';

interface TemplateListProps {
  templates: TransferTemplate[];
  isLoading: boolean;
  onEdit: (template: TransferTemplate) => void;
  onDelete: (id: number) => void;
  onView: (template: TransferTemplate) => void;
  onLoadTemplate: (id: number) => void;
}

const TemplateList: React.FC<TemplateListProps> = ({
  templates,
  isLoading,
  onEdit,
  onDelete,
  onView,
  onLoadTemplate,
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
              <div className="mt-4 flex space-x-2">
                <div className="h-8 bg-gray-200 rounded w-20"></div>
                <div className="h-8 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto h-12 w-12 text-gray-400">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="mt-2 text-sm font-medium text-gray-900">Nincsenek sablonok</h3>
        <p className="mt-1 text-sm text-gray-500">
          Kezdjen el egy új sablon létrehozásával.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {templates.map((template) => (
        <div key={template.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-medium text-gray-900 truncate">
                  {template.name}
                </h3>
                {template.description && (
                  <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                    {template.description}
                  </p>
                )}
              </div>
              <div className="ml-2 flex-shrink-0">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  template.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {template.is_active ? 'Aktív' : 'Inaktív'}
                </span>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center text-sm text-gray-500">
                <UserGroupIcon className="h-4 w-4 mr-2" />
                <span>{template.beneficiary_count} kedvezményezett</span>
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

            <div className="mt-6 flex space-x-2">
              <button
                onClick={() => onLoadTemplate(template.id)}
                className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlayIcon className="h-4 w-4 mr-1" />
                Betöltés
              </button>
              <div className="flex space-x-1">
                <button
                  onClick={() => onView(template)}
                  className="inline-flex items-center px-2 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  title="Megtekintés"
                >
                  <EyeIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => onEdit(template)}
                  className="inline-flex items-center px-2 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  title="Szerkesztés"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => onDelete(template.id)}
                  className="inline-flex items-center px-2 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-red-600 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  title="Törlés"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TemplateList;