import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  IconButton,
  Box,
  Stack,
  Chip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Close as CloseIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

interface XMLPreviewProps {
  xmlContent: string;
  filename: string;
  onClose: () => void;
  onDownload: () => void;
}

const XMLPreview: React.FC<XMLPreviewProps> = ({ xmlContent, filename, onClose, onDownload }) => {
  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(xmlContent);
      // Success feedback could be handled by a snackbar or toast system
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const formatXML = (xml: string) => {
    // Improved XML formatting with proper indentation
    if (!xml) return [];

    let indentLevel = 0;
    const indentSize = 4; // 4 spaces per indent level

    // Remove existing formatting and add proper line breaks
    const cleaned = xml
      .replace(/>\s*</g, '>\n<') // Add line breaks between tags
      .replace(/^\s+|\s+$/g, ''); // Remove leading/trailing whitespace

    const lines = cleaned.split('\n');
    const result = [];

    for (let i = 0; i < lines.length; i++) {
      const currentLine = lines[i];
      if (!currentLine) continue;
      const line = currentLine.trim();
      if (!line) continue;

      // Adjust indent level BEFORE creating the line
      if (line.startsWith('</')) {
        // Closing tag: decrease indent level first
        indentLevel = Math.max(0, indentLevel - 1);
      }

      // Create formatted line with current indentation
      const spaces = ' '.repeat(indentLevel * indentSize);
      result.push({
        content: line,
        indent: indentLevel * indentSize,
        lineNumber: result.length + 1,
        formattedContent: spaces + line,
      });

      // Adjust indent level AFTER creating the line
      if (
        line.startsWith('<') &&
        !line.startsWith('</') &&
        !line.endsWith('/>') &&
        !line.includes('</')
      ) {
        // Opening tag: increase indent level for next line
        indentLevel++;
      }
    }

    return result;
  };

  const formattedLines = formatXML(xmlContent);

  return (
    <Dialog
      open={true}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: '#1f2937',
          color: '#f9fafb',
        },
      }}
    >
      <DialogTitle sx={{ bgcolor: '#1f2937', color: '#f9fafb', borderBottom: '1px solid #374151' }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Stack direction="row" alignItems="center" spacing={1}>
              <CodeIcon sx={{ color: '#60a5fa' }} />
              <Typography variant="h6" sx={{ color: '#f9fafb' }}>
                XML Előnézet
              </Typography>
            </Stack>
            <Typography variant="body2" sx={{ color: '#9ca3af' }}>
              {filename}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<CopyIcon />}
              onClick={handleCopyToClipboard}
              size="small"
              sx={{
                borderColor: '#4b5563',
                color: '#f9fafb',
                '&:hover': {
                  borderColor: '#6b7280',
                  bgcolor: '#374151',
                },
              }}
            >
              Másolás
            </Button>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={onDownload}
              size="small"
              sx={{
                bgcolor: '#059669',
                '&:hover': {
                  bgcolor: '#047857',
                },
              }}
            >
              Letöltés
            </Button>
            <IconButton
              onClick={onClose}
              edge="end"
              sx={{
                color: '#9ca3af',
                '&:hover': {
                  bgcolor: '#374151',
                  color: '#f9fafb',
                },
              }}
            >
              <CloseIcon />
            </IconButton>
          </Stack>
        </Stack>
      </DialogTitle>

      <DialogContent sx={{ flex: 1, p: 0, overflow: 'hidden', bgcolor: '#1a1a1a' }}>
        <Box
          sx={{
            height: '100%',
            bgcolor: '#1a1a1a',
            color: '#e5e7eb',
            fontFamily:
              '"Fira Code", "JetBrains Mono", "Monaco", "Cascadia Code", "Roboto Mono", monospace',
            fontSize: '0.875rem',
            overflow: 'auto',
            '&::-webkit-scrollbar': {
              width: 8,
              height: 8,
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: '#2d2d2d',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: '#555',
              borderRadius: 4,
              '&:hover': {
                backgroundColor: '#777',
              },
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            {formattedLines.map((line, index) => (
              <Box key={index} sx={{ display: 'flex', minHeight: '1.25em' }}>
                <Box
                  sx={{
                    color: '#6b7280',
                    width: 48,
                    textAlign: 'right',
                    mr: 2,
                    userSelect: 'none',
                    flexShrink: 0,
                    bgcolor: '#262626',
                    px: 1,
                    borderRadius: 0.5,
                    fontSize: '0.8rem',
                  }}
                >
                  {line.lineNumber}
                </Box>
                <Box
                  sx={{
                    flex: 1,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      color: line.content.includes('</')
                        ? '#f87171' // Red for closing tags
                        : line.content.includes('<?xml')
                          ? '#fbbf24' // Yellow for XML declaration
                          : line.content.includes('<') && !line.content.includes('</')
                            ? '#60a5fa' // Blue for opening tags
                            : '#e5e7eb', // Light gray for text content
                      lineHeight: 1.5,
                    }}
                  >
                    {line.formattedContent}
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ bgcolor: '#1f2937', px: 3, py: 2, borderTop: '1px solid #374151' }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ width: '100%' }}
        >
          <Stack direction="row" spacing={2}>
            <Chip
              label={`${formattedLines.length} sor`}
              size="small"
              variant="outlined"
              sx={{
                borderColor: '#4b5563',
                color: '#9ca3af',
                '& .MuiChip-label': {
                  color: '#9ca3af',
                },
              }}
            />
            <Chip
              label={`${new Blob([xmlContent]).size} byte`}
              size="small"
              variant="outlined"
              sx={{
                borderColor: '#4b5563',
                color: '#9ca3af',
                '& .MuiChip-label': {
                  color: '#9ca3af',
                },
              }}
            />
          </Stack>
          <Chip
            label="UTF-8 kódolás"
            size="small"
            variant="outlined"
            sx={{
              borderColor: '#60a5fa',
              color: '#60a5fa',
              '& .MuiChip-label': {
                color: '#60a5fa',
              },
            }}
          />
        </Stack>
      </DialogActions>
    </Dialog>
  );
};

export default XMLPreview;
