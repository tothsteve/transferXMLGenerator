import React, { useRef, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  CloudArrowUpIcon, 
  XMarkIcon, 
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { useUploadExcel } from '../../hooks/api';

interface ExcelImportProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ExcelImport: React.FC<ExcelImportProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<{
    imported_count: number;
    errors: string[];
  } | null>(null);

  const uploadMutation = useUploadExcel();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await uploadMutation.mutateAsync(selectedFile);
      setUploadResult(result.data);
      
      if (result.data.errors.length === 0 && onSuccess) {
        setTimeout(() => {
          onSuccess();
          handleClose();
        }, 2000);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setUploadResult(null);
    uploadMutation.reset();
    onClose();
  };

  const downloadTemplate = () => {
    // Create a sample Excel template
    const csvContent = `Megjegyzés,Kedvezményezett neve,Számlaszám,Összeg,Teljesítés dátuma,Közlemény
Példa,Teszt Kft.,12345678-12345678-12345678,100000,2025-01-15,Számla 2025-001
,Másik Cég Kft.,98765432-98765432-98765432,,,`;
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'kedvezményezettek_sablon.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex justify-between items-center mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Excel importálás
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Template download */}
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-start">
                      <DocumentArrowDownIcon className="h-5 w-5 text-blue-400 mt-0.5" />
                      <div className="ml-3">
                        <h4 className="text-sm font-medium text-blue-800">
                          Excel sablon letöltése
                        </h4>
                        <p className="text-sm text-blue-700 mt-1">
                          Töltse le a sablon fájlt a helyes formátum megtekintéséhez.
                        </p>
                        <button
                          onClick={downloadTemplate}
                          className="mt-2 text-sm text-blue-600 hover:text-blue-800 underline"
                        >
                          Sablon letöltése
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* File selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Excel fájl kiválasztása
                    </label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                      <div className="space-y-1 text-center">
                        <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <div className="flex text-sm text-gray-600">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                          >
                            <span>Fájl kiválasztása</span>
                            <input
                              id="file-upload"
                              ref={fileInputRef}
                              type="file"
                              className="sr-only"
                              accept=".xlsx,.xls,.csv"
                              onChange={handleFileSelect}
                            />
                          </label>
                          <p className="pl-1">vagy húzza ide</p>
                        </div>
                        <p className="text-xs text-gray-500">
                          XLSX, XLS, CSV fájlok (max. 10MB)
                        </p>
                      </div>
                    </div>
                    
                    {selectedFile && (
                      <div className="mt-2 text-sm text-gray-600">
                        Kiválasztott fájl: <span className="font-medium">{selectedFile.name}</span>
                      </div>
                    )}
                  </div>

                  {/* Upload result */}
                  {uploadResult && (
                    <div className={`p-4 rounded-lg ${
                      uploadResult.errors.length > 0 ? 'bg-yellow-50' : 'bg-green-50'
                    }`}>
                      <div className="flex items-start">
                        {uploadResult.errors.length > 0 ? (
                          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5" />
                        ) : (
                          <CheckCircleIcon className="h-5 w-5 text-green-400 mt-0.5" />
                        )}
                        <div className="ml-3">
                          <h4 className={`text-sm font-medium ${
                            uploadResult.errors.length > 0 ? 'text-yellow-800' : 'text-green-800'
                          }`}>
                            Import eredmény
                          </h4>
                          <div className={`text-sm mt-1 ${
                            uploadResult.errors.length > 0 ? 'text-yellow-700' : 'text-green-700'
                          }`}>
                            <p>Importált kedvezményezettek: {uploadResult.imported_count}</p>
                            
                            {uploadResult.errors.length > 0 && (
                              <div className="mt-2">
                                <p className="font-medium">Hibák:</p>
                                <ul className="list-disc list-inside space-y-1">
                                  {uploadResult.errors.map((error, index) => (
                                    <li key={index}>{error}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Expected format info */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Várt fájl formátum (3. sortól kezdve):
                    </h4>
                    <ul className="text-xs text-gray-700 space-y-1">
                      <li><strong>A oszlop:</strong> Megjegyzés (opcionális)</li>
                      <li><strong>B oszlop:</strong> Kedvezményezett neve (kötelező)</li>
                      <li><strong>C oszlop:</strong> Számlaszám (kötelező)</li>
                      <li><strong>D oszlop:</strong> Összeg (opcionális)</li>
                      <li><strong>E oszlop:</strong> Teljesítés dátuma (opcionális)</li>
                      <li><strong>F oszlop:</strong> Közlemény (opcionális)</li>
                    </ul>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-6">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    Bezárás
                  </button>
                  <button
                    type="button"
                    onClick={handleUpload}
                    disabled={!selectedFile || uploadMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {uploadMutation.isPending ? 'Importálás...' : 'Importálás'}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default ExcelImport;