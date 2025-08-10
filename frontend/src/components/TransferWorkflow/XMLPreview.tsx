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
  Paper,
  Divider,
  Chip
} from '@mui/material';
import {
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Close as CloseIcon,
  Code as CodeIcon
} from '@mui/icons-material';

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
      // Success feedback could be handled by a snackbar or toast system
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
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
    <Dialog 
      open={true} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { height: '90vh', display: 'flex', flexDirection: 'column' }
      }}
    >
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Stack direction="row" alignItems="center" spacing={1}>
              <CodeIcon color="primary" />
              <Typography variant="h6">XML Előnézet</Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {filename}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<CopyIcon />}
              onClick={handleCopyToClipboard}
              size="small"
            >
              Másolás
            </Button>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={onDownload}
              size="small"
            >
              Letöltés
            </Button>
            <IconButton onClick={onClose} edge="end">
              <CloseIcon />
            </IconButton>
          </Stack>
        </Stack>
      </DialogTitle>

      <DialogContent sx={{ flex: 1, p: 0, overflow: 'hidden' }}>
        <Paper
          variant="outlined"
          sx={{
            height: '100%',
            bgcolor: 'grey.900',
            color: '#00ff00',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            overflow: 'auto'
          }}
        >
          <Box sx={{ p: 2 }}>
            {formattedLines.map((line, index) => (
              <Box key={index} sx={{ display: 'flex', minHeight: '1.25em' }}>
                <Box
                  sx={{
                    color: 'grey.500',
                    width: 48,
                    textAlign: 'right',
                    mr: 2,
                    userSelect: 'none',
                    flexShrink: 0
                  }}
                >
                  {line.lineNumber}
                </Box>
                <Box
                  sx={{
                    flex: 1,
                    pl: line.indent,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all'
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      color: line.content.includes('</')
                        ? '#ff6b6b'
                        : line.content.includes('<?xml')
                        ? '#ffd93d'
                        : line.content.includes('<') && !line.content.includes('</')
                        ? '#74c0fc'
                        : '#ffffff'
                    }}
                  >
                    {line.content}
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>
      </DialogContent>

      <DialogActions sx={{ bgcolor: 'grey.50', px: 3, py: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ width: '100%' }}>
          <Stack direction="row" spacing={2}>
            <Chip 
              label={`${formattedLines.length} sor`} 
              size="small" 
              variant="outlined" 
            />
            <Chip 
              label={`${new Blob([xmlContent]).size} byte`} 
              size="small" 
              variant="outlined" 
            />
          </Stack>
          <Chip 
            label="UTF-8 kódolás" 
            size="small" 
            color="primary" 
            variant="outlined" 
          />
        </Stack>
      </DialogActions>
    </Dialog>
  );
};

export default XMLPreview;