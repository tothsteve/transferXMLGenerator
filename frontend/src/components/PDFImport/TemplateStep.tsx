import React from 'react';
import { PDFProcessingResult } from './PDFImportWizard';

interface TemplateStepProps {
  previewData: PDFProcessingResult;
  onViewTemplate: () => void;
  onCreateTransfers: () => void;
}

export const TemplateStep: React.FC<TemplateStepProps> = ({
  previewData,
  onViewTemplate,
  onCreateTransfers,
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
      <div className="max-w-4xl mx-auto text-center space-y-8">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        {/* Success Message */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            🎉 Sablon Sikeresen Létrehozva!
          </h2>
          <p className="text-lg text-gray-600">
            A PDF fájlok feldolgozása befejeződött és a sablon készen áll a használatra.
          </p>
        </div>

        {/* Template Summary */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">📄 Sablon Összefoglaló</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Alapadatok</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Sablon neve:</span>
                  <span className="font-medium">{previewData.template.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sablon ID:</span>
                  <span className="font-medium">#{previewData.template.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Kedvezményezettek:</span>
                  <span className="font-medium">{previewData.template.beneficiary_count}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-700 mb-3">Feldolgozás eredménye</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Tranzakciók:</span>
                  <span className="font-medium">{previewData.transactions_processed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Összes összeg:</span>
                  <span className="font-medium">{formatCurrency(previewData.total_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Meglévő kedvezményezett:</span>
                  <span className="font-medium text-green-600">{previewData.beneficiaries_matched}</span>
                </div>
                {previewData.beneficiaries_created > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Új kedvezményezett:</span>
                    <span className="font-medium text-amber-600">{previewData.beneficiaries_created}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Consolidations Summary */}
        {previewData.consolidations && previewData.consolidations.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <h4 className="font-medium text-amber-800 mb-3">🔄 Összevonások</h4>
            <ul className="text-sm text-amber-700 space-y-1 text-left">
              {previewData.consolidations.map((msg, index) => (
                <li key={index}>• {msg}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Steps */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-medium text-blue-800 mb-3">📋 Következő lépések</h4>
          <div className="text-left space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-blue-800 text-xs font-medium">1</span>
              </div>
              <div>
                <p className="text-blue-700 font-medium">Utalások létrehozása</p>
                <p className="text-blue-600 text-sm">Használja a sablont azonnali utalás generáláshoz</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-blue-800 text-xs font-medium">2</span>
              </div>
              <div>
                <p className="text-blue-700 font-medium">Összegek módosítása</p>
                <p className="text-blue-600 text-sm">Szükség szerint módosítsa az összegeket és dátumokat</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-blue-800 text-xs font-medium">3</span>
              </div>
              <div>
                <p className="text-blue-700 font-medium">XML generálás</p>
                <p className="text-blue-600 text-sm">Töltse le az XML fájlt a banki importhoz</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
          <button
            onClick={onViewTemplate}
            className="px-6 py-3 text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors flex items-center justify-center space-x-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span>Sablon Megtekintése</span>
          </button>
          
          <button
            onClick={onCreateTransfers}
            className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span>Utalások Létrehozása</span>
          </button>
        </div>

        {/* Tips */}
        <div className="text-left bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 className="font-medium text-gray-700 mb-3">💡 Hasznos tippek</h4>
          <ul className="text-sm text-gray-600 space-y-2">
            <li>• A sablon újra felhasználható minden hónapban - csak töltse fel az új PDF-eket</li>
            <li>• A kedvezményezettek automatikusan frissülnek, de az összegek mindig ellenőrizendők</li>
            <li>• Az XML fájl közvetlenül importálható a legtöbb banki rendszerbe</li>
            <li>• A sablon később szerkeszthető és kiegészíthető további kedvezményezettekkel</li>
          </ul>
        </div>
      </div>
    </div>
  );
};