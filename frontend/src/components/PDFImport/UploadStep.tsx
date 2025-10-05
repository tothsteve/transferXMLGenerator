import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  PictureAsPdf as PdfIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

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
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      // Filter only PDF files and combine with existing files
      const pdfFiles = acceptedFiles.filter((file) => file.type === 'application/pdf');
      const newFiles = [...selectedFiles, ...pdfFiles];
      onFilesSelected(newFiles);
    },
    [selectedFiles, onFilesSelected]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
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
    <Box sx={{ p: { xs: 2, sm: 3 }, maxWidth: '100%', mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h6" component="h2" fontWeight="bold" gutterBottom>
          PDF Fájlok Feltöltése
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ maxWidth: 600, mx: 'auto', display: { xs: 'none', sm: 'block' } }}
        >
          Töltse fel a havi NAV adó és fizetési PDF fájljait. A rendszer automatikusan felismeri a
          formátumokat és létrehozza a megfelelő sablont.
        </Typography>
      </Box>

      {/* Template Name Input */}
      <Box sx={{ maxWidth: 500, mx: 'auto', mb: 3 }}>
        <TextField
          fullWidth
          label="Sablon neve (opcionális)"
          value={templateName}
          onChange={(e) => onTemplateNameChange(e.target.value)}
          placeholder="pl. Havi Fizetések 2025-07"
          helperText="Ha üresen hagyja, automatikusan generálunk nevet"
          variant="outlined"
          size="small"
        />
      </Box>

      {/* Drag & Drop Zone */}
      <Paper
        {...getRootProps()}
        elevation={0}
        sx={{
          border: 2,
          borderStyle: 'dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          bgcolor: isDragActive ? 'primary.50' : 'grey.50',
          p: { xs: 3, sm: 4 },
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          mb: 3,
          '&:hover': {
            borderColor: 'grey.400',
            bgcolor: 'grey.100',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon
          sx={{
            fontSize: { xs: 32, sm: 40 },
            color: isDragActive ? 'primary.main' : 'grey.400',
            mb: 1,
          }}
        />
        {isDragActive ? (
          <Box>
            <Typography variant="body1" color="primary" gutterBottom fontWeight={600}>
              Engedje el a fájlokat itt...
            </Typography>
            <Typography variant="body2" color="primary">
              PDF fájlok támogatottak
            </Typography>
          </Box>
        ) : (
          <Box>
            <Typography
              variant="body1"
              gutterBottom
              sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
            >
              <Box
                component="span"
                color="primary.main"
                sx={{ textDecoration: 'underline', fontWeight: 600 }}
              >
                Kattintson a fájlok kiválasztásához
              </Box>
              <Box component="span" sx={{ display: { xs: 'block', sm: 'inline' } }}>
                {' '}
                vagy húzza ide őket
              </Box>
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
            >
              PDF fájlok, max. 10 fájl, fájlonként max. 50MB
            </Typography>
          </Box>
        )}
      </Paper>

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Nem sikerült feltölteni:</AlertTitle>
          <List dense>
            {fileRejections.map(({ file, errors }, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.25 }}>
                <ListItemText
                  primary={`${file.name}: ${errors.map((e) => e.message).join(', ')}`}
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom fontWeight={600}>
            Kiválasztott fájlok ({selectedFiles.length})
          </Typography>
          <Paper elevation={1}>
            <List dense>
              {selectedFiles.map((file, index) => (
                <ListItem key={index} divider={index < selectedFiles.length - 1} sx={{ py: 1 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <PdfIcon color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2" fontWeight={500}>
                        {file.name}
                      </Typography>
                    }
                    secondary={
                      <Typography variant="caption" color="text.secondary">
                        {formatFileSize(file.size)}
                      </Typography>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => onRemoveFile(index)}
                      disabled={processing}
                      color="error"
                      size="small"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {/* Supported Formats Info */}
      <Alert severity="info" sx={{ mb: 3, display: { xs: 'none', md: 'flex' } }}>
        <AlertTitle sx={{ fontSize: '0.9rem' }}>Támogatott PDF formátumok</AlertTitle>
        <Box component="ul" sx={{ m: 0, pl: 1, fontSize: '0.8rem', '& li': { mb: 0.5 } }}>
          <li>NAV adó és járulék befizetési PDF-ek - Automatikus NAV kedvezményezett felismerés</li>
          <li>Banki utalás / fizetési lista PDF-ek - Alkalmazott fizetések és bérleti díjak</li>
          <li>Többféle formátum együtt - Egy sablonba egyesíti az összes tranzakciót</li>
        </Box>
      </Alert>

      {/* Action Buttons */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          pt: 1,
          gap: 2,
          flexDirection: { xs: 'column', sm: 'row' },
        }}
      >
        <Button
          onClick={onCancel}
          variant="outlined"
          disabled={processing}
          size="medium"
          sx={{ width: { xs: '100%', sm: 'auto' } }}
        >
          Mégse
        </Button>
        <Button
          onClick={onProcessFiles}
          disabled={selectedFiles.length === 0 || processing}
          variant="contained"
          size="medium"
          startIcon={processing ? <CircularProgress size={20} /> : <CheckCircleIcon />}
          sx={{ width: { xs: '100%', sm: 'auto' }, minWidth: { sm: 180 } }}
        >
          {processing ? 'PDF-ek feldolgozása...' : 'PDF-ek feldolgozása'}
        </Button>
      </Box>
    </Box>
  );
};
