import React from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  ChevronDownIcon, 
  DocumentDuplicateIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import { TransferTemplate } from '../../types/api';

interface TemplateSelectorProps {
  templates: TransferTemplate[];
  selectedTemplate: TransferTemplate | null;
  onSelectTemplate: (template: TransferTemplate) => void;
  onLoadTemplate: (templateId: number) => void;
  isLoading?: boolean;
}

const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  selectedTemplate,
  onSelectTemplate,
  onLoadTemplate,
  isLoading = false,
}) => {
  const activeTemplates = templates.filter(t => t.is_active);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <DocumentDuplicateIcon className="h-6 w-6 text-primary-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Sablon kiválasztása</h3>
        </div>
        {selectedTemplate && (
          <button
            onClick={() => onLoadTemplate(selectedTemplate.id)}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <PlayIcon className="h-4 w-4 mr-1" />
            {isLoading ? 'Betöltés...' : 'Sablon betöltése'}
          </button>
        )}
      </div>

      {activeTemplates.length === 0 ? (
        <div className="text-center py-6 border-2 border-dashed border-gray-300 rounded-lg">
          <DocumentDuplicateIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h4 className="mt-2 text-sm font-medium text-gray-900">Nincsenek aktív sablonok</h4>
          <p className="mt-1 text-sm text-gray-500">
            Hozzon létre egy új sablont a Sablonok menüpontban.
          </p>
        </div>
      ) : (
        <Menu as="div" className="relative inline-block text-left w-full">
          <div>
            <Menu.Button className="inline-flex w-full justify-between items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
              <div className="flex items-center">
                {selectedTemplate ? (
                  <div>
                    <div className="font-medium text-gray-900">{selectedTemplate.name}</div>
                    {selectedTemplate.description && (
                      <div className="text-xs text-gray-500 truncate">{selectedTemplate.description}</div>
                    )}
                  </div>
                ) : (
                  <span>Válasszon sablont...</span>
                )}
              </div>
              <ChevronDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            </Menu.Button>
          </div>
          
          <Transition
            as={Fragment}
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <Menu.Items className="absolute left-0 z-10 mt-2 w-full origin-top-left rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              <div className="py-1">
                {activeTemplates.map((template) => (
                  <Menu.Item key={template.id}>
                    {({ active }) => (
                      <button
                        onClick={() => onSelectTemplate(template)}
                        className={`${
                          active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                        } group flex w-full items-center px-4 py-2 text-sm`}
                      >
                        <div className="flex-1 text-left">
                          <div className="font-medium">{template.name}</div>
                          <div className="text-xs text-gray-500">
                            {template.beneficiary_count} kedvezményezett
                          </div>
                          {template.description && (
                            <div className="text-xs text-gray-400 mt-1 line-clamp-1">
                              {template.description}
                            </div>
                          )}
                        </div>
                        {selectedTemplate?.id === template.id && (
                          <div className="ml-2 h-2 w-2 rounded-full bg-primary-600" />
                        )}
                      </button>
                    )}
                  </Menu.Item>
                ))}
              </div>
            </Menu.Items>
          </Transition>
        </Menu>
      )}

      {selectedTemplate && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Kedvezményezettek:</span>
              <span className="ml-2 text-gray-900">{selectedTemplate.beneficiary_count}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Létrehozva:</span>
              <span className="ml-2 text-gray-900">
                {new Date(selectedTemplate.created_at).toLocaleDateString('hu-HU')}
              </span>
            </div>
          </div>
          {selectedTemplate.description && (
            <div className="mt-2 text-sm text-gray-600">
              {selectedTemplate.description}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TemplateSelector;