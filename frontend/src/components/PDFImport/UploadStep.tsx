import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface UploadStepProps {
  selectedFiles: File[];
  templateName: string;
  processing: boolean;
  onFilesSelected: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onTemplateNameChange: (name: string) => void;
  onProcessFiles: () => void;
  onCancel: () => void;
}

export const UploadStep: React.FC<UploadStepProps> = ({
  selectedFiles,
  templateName,
  processing,
  onFilesSelected,
  onRemoveFile,
  onTemplateNameChange,
  onProcessFiles,
  onCancel,
}) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter only PDF files and combine with existing files
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    const newFiles = [...selectedFiles, ...pdfFiles];
    onFilesSelected(newFiles);
  }, [selectedFiles, onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true,
    maxFiles: 10,
    maxSize: 50 * 1024 * 1024, // 50MB max file size
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            PDF Fájlok Feltöltése
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Töltse fel a havi NAV adó és fizetési PDF fájljait. A rendszer automatikusan 
            felismeri a formátumokat és létrehozza a megfelelő sablont.
          </p>
        </div>

        {/* Template Name Input */}
        <div className="max-w-md mx-auto">
          <label htmlFor="templateName" className="block text-sm font-medium text-gray-700 mb-2">
            Sablon neve (opcionális)
          </label>
          <input
            type="text"
            id="templateName"
            value={templateName}
            onChange={(e) => onTemplateNameChange(e.target.value)}
            placeholder="pl. Havi Fizetések 2025-07"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Ha üresen hagyja, automatikusan generálunk nevet
          </p>
        </div>

        {/* Drag & Drop Zone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200 ${
            isDragActive
              ? 'border-blue-400 bg-blue-50 ring-2 ring-blue-200'
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <div className="space-y-4">
            <div className="text-gray-400">
              <svg
                className="mx-auto h-8 w-8"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            {isDragActive ? (
              <div>
                <p className="text-blue-600 font-medium">Engedje el a fájlokat itt...</p>
                <p className="text-blue-500 text-sm">PDF fájlok támogatottak</p>
              </div>
            ) : (
              <div>
                <p className="text-gray-600">
                  <span className="text-blue-600 font-medium cursor-pointer hover:underline">
                    Kattintson a fájlok kiválasztásához
                  </span>{' '}
                  vagy húzza ide őket
                </p>
                <p className="text-sm text-gray-500">
                  PDF fájlok, maximum 10 fájl, fájlonként max. 50MB
                </p>
              </div>
            )}
          </div>
        </div>

        {/* File Rejections */}
        {fileRejections.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="text-red-800 font-medium mb-2">Nem sikerült feltölteni:</h4>
            <ul className="text-red-700 text-sm space-y-1">
              {fileRejections.map(({ file, errors }, index) => (
                <li key={index}>
                  <strong>{file.name}</strong>: {errors.map(e => e.message).join(', ')}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Kiválasztott fájlok ({selectedFiles.length})</h3>
            <div className="space-y-2">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-red-500">
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{file.name}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => onRemoveFile(index)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                    disabled={processing}
                  >
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Supported Formats Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-blue-800 font-medium mb-2">📄 Támogatott PDF formátumok:</h4>
          <ul className="text-blue-700 text-sm space-y-1">
            <li>• <strong>NAV adó és járulék befizetési PDF-ek</strong> - Automatikus NAV kedvezményezett felismerés</li>
            <li>• <strong>Banki utalás / fizetési lista PDF-ek</strong> - Alkalmazott fizetések és bérleti díjak</li>
            <li>• <strong>Többféle formátum együtt</strong> - Egy sablonba egyesíti az összes tranzakciót</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between pt-6">
          <button
            onClick={onCancel}
            className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            disabled={processing}
          >
            Mégse
          </button>
          <button
            onClick={onProcessFiles}
            disabled={selectedFiles.length === 0 || processing}
            className="px-8 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {processing && (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            )}
            <span>{processing ? 'PDF-ek feldolgozása...' : 'PDF-ek feldolgozása'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};