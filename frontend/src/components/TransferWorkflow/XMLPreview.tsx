import React from 'react';
import { 
  DocumentArrowDownIcon,
  ClipboardDocumentIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface XMLPreviewProps {
  xmlContent: string;
  filename: string;
  onClose: () => void;
  onDownload: () => void;
}

const XMLPreview: React.FC<XMLPreviewProps> = ({
  xmlContent,
  filename,
  onClose,
  onDownload,
}) => {
  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(xmlContent);
      // Success feedback would be handled by parent component
      window.dispatchEvent(new CustomEvent('toast', {
        detail: { type: 'success', title: 'XML tartalma vágólapra másolva' }
      }));
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      window.dispatchEvent(new CustomEvent('toast', {
        detail: { type: 'error', title: 'Másolás sikertelen', message: 'Próbálja meg manuálisan kijelölni és másolni a tartalmat' }
      }));
    }
  };

  const formatXML = (xml: string) => {
    // Simple XML formatting for display
    const formatted = xml
      .replace(/></g, '>\n<')
      .replace(/^\s*\n/gm, '')
      .split('\n')
      .map((line, index) => {
        const indentLevel = (line.match(/<\//g) || []).length > 0 ? 
          Math.max(0, (line.match(/</g) || []).length - 1) : 
          (line.match(/</g) || []).length;
        
        return {
          content: line.trim(),
          indent: Math.max(0, indentLevel - 1) * 2,
          lineNumber: index + 1
        };
      })
      .filter(line => line.content.length > 0);

    return formatted;
  };

  const formattedLines = formatXML(xmlContent);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-full flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">XML Előnézet</h3>
            <p className="text-sm text-gray-500">{filename}</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleCopyToClipboard}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              title="Másolás vágólapra"
            >
              <ClipboardDocumentIcon className="h-4 w-4 mr-2" />
              Másolás
            </button>
            <button
              onClick={onDownload}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Letöltés
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* XML Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-auto bg-gray-900 text-green-400 font-mono text-sm">
            <div className="p-4">
              {formattedLines.map((line, index) => (
                <div key={index} className="flex">
                  <div className="text-gray-500 w-12 text-right mr-4 select-none">
                    {line.lineNumber}
                  </div>
                  <div 
                    className="flex-1"
                    style={{ paddingLeft: `${line.indent * 8}px` }}
                  >
                    <span className="whitespace-pre-wrap">
                      {line.content.includes('</') ? (
                        <span className="text-red-400">{line.content}</span>
                      ) : line.content.includes('<?xml') ? (
                        <span className="text-yellow-400">{line.content}</span>
                      ) : line.content.includes('<') && !line.content.includes('</') ? (
                        <span className="text-blue-400">{line.content}</span>
                      ) : (
                        <span className="text-white">{line.content}</span>
                      )}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <div>
              {formattedLines.length} sor • {new Blob([xmlContent]).size} byte
            </div>
            <div>
              UTF-8 kódolás
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default XMLPreview;