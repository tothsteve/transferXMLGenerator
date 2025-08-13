import React from 'react';
import { PDFProcessingResult } from './PDFImportWizard';

interface ReviewStepProps {
  previewData: PDFProcessingResult;
  onBack: () => void;
  onConfirm: () => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  previewData,
  onBack,
  onConfirm,
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'HUF',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Adatok Áttekintése
          </h2>
          <p className="text-gray-600">
            {previewData.template_updated 
              ? 'Ellenőrizze a kinyert tranzakciókat és erősítse meg a sablon frissítését'
              : 'Ellenőrizze a kinyert tranzakciókat és erősítse meg a sablon létrehozását'
            }
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="text-blue-600">
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-2xl font-bold text-blue-900">{previewData.transactions_processed}</p>
                <p className="text-blue-700 text-sm">Tranzakció</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="text-green-600">
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-2xl font-bold text-green-900">{previewData.beneficiaries_matched}</p>
                <p className="text-green-700 text-sm">Meglévő kedvezményezett</p>
              </div>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="text-amber-600">
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-2xl font-bold text-amber-900">{previewData.beneficiaries_created}</p>
                <p className="text-amber-700 text-sm">Új kedvezményezett</p>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="text-purple-600">
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-2xl font-bold text-purple-900">{formatCurrency(previewData.total_amount)}</p>
                <p className="text-purple-700 text-sm">Összes összeg</p>
              </div>
            </div>
          </div>
        </div>

        {/* Template Info */}
        <div className={`border rounded-lg p-6 ${previewData.template_updated 
          ? 'bg-blue-50 border-blue-200' 
          : 'bg-gray-50 border-gray-200'
        }`}>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {previewData.template_updated 
              ? '🔄 Frissítendő sablon' 
              : '📄 Létrehozandó sablon'
            }
          </h3>
          <p className="text-gray-700">
            <strong>Név:</strong> {previewData.template.name}
          </p>
          <p className="text-gray-700">
            <strong>Kedvezményezettek száma:</strong> {previewData.template.beneficiary_count}
          </p>
          {previewData.template_updated && (
            <div className="mt-3 p-3 bg-blue-100 border border-blue-200 rounded">
              <p className="text-sm text-blue-800">
                ✅ A rendszer észlelte, hogy már létezik sablon ugyanezekkel a kedvezményezettekkel. 
                Az összegek és közlemények frissítésre kerülnek az új értékekkel.
              </p>
            </div>
          )}
        </div>

        {/* Consolidation Alerts */}
        {previewData.consolidations && previewData.consolidations.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <div className="text-amber-500 mt-0.5">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-medium text-amber-800 mb-2">🔄 Tranzakciók összevonása</h3>
                <ul className="space-y-1 text-sm text-amber-700">
                  {previewData.consolidations.map((msg, index) => (
                    <li key={index}>• {msg}</li>
                  ))}
                </ul>
                <p className="text-xs text-amber-600 mt-2">
                  Az azonos kedvezményezetthez tartozó tranzakciók automatikusan összevonásra kerültek.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Transaction Table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900">Kinyert Tranzakciók</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Kedvezményezett
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Számlaszám
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Összeg
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Közlemény
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Állapot
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {previewData.preview.map((transaction, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">
                        {transaction.beneficiary_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {transaction.account_number.length > 20
                        ? `${transaction.account_number.substring(0, 8)}...${transaction.account_number.substring(transaction.account_number.length - 8)}`
                        : transaction.account_number
                      }
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                      {formatCurrency(transaction.amount)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {transaction.remittance_info || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {transaction.beneficiary_id ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓ Meglévő
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                          + Új
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <div className="text-blue-500 mt-0.5">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-blue-800 mb-1">ℹ️ Tudnivalók</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                {previewData.template_updated ? (
                  <>
                    <li>• A meglévő sablon összegei és közleményei frissülnek az új PDF adatokkal</li>
                    <li>• A kedvezményezettek listája változatlan marad</li>
                    <li>• A frissítés után közvetlenül használhatja az utalások generálásához</li>
                    <li>• Az eredeti sablon neve és beállításai megmaradnak</li>
                  </>
                ) : (
                  <>
                    <li>• A sablon létrehozása után közvetlenül használhatja az utalások generálásához</li>
                    <li>• A meglévő kedvezményezettek nem kerülnek duplikálásra</li>
                    <li>• Az összegek és közlemények módosíthatók az utalás létrehozásakor</li>
                    <li>• A sablon később bármikor frissíthető újabb PDF-ekkel</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between pt-6">
          <button
            onClick={onBack}
            className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            ← Vissza
          </button>
          <button
            onClick={onConfirm}
            className={`px-8 py-2 text-white rounded-lg transition-colors flex items-center space-x-2 ${
              previewData.template_updated
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{previewData.template_updated ? 'Sablon Frissítése' : 'Sablon Létrehozása'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};