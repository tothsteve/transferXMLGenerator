import React, { useRef, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Paper,
  Alert,
  AlertTitle,
  List,
  ListItem,
  Stack,
  IconButton,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Close as CloseIcon,
  Download as DownloadIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useUploadExcel } from '../../hooks/api';

interface ExcelImportProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ExcelImport: React.FC<ExcelImportProps> = ({ isOpen, onClose, onSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<{
    imported_count: number;
    errors: string[];
  } | null>(null);

  const uploadMutation = useUploadExcel();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadResult(null);
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (!selectedFile) return;

    try {
      const result = await uploadMutation.mutateAsync(selectedFile);
      setUploadResult(result);

      if (result.errors?.length === 0 && onSuccess) {
        setTimeout(() => {
          onSuccess();
          handleClose();
        }, 2000);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleClose = (): void => {
    setSelectedFile(null);
    setUploadResult(null);
    uploadMutation.reset();
    onClose();
  };

  const downloadTemplate = (): void => {
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
    <Dialog open={isOpen} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Excel importálás</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3}>
          {/* Template download */}
          <Alert severity="info" icon={<DownloadIcon />}>
            <AlertTitle>Excel sablon letöltése</AlertTitle>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Töltse le a sablon fájlt a helyes formátum megtekintéséhez.
            </Typography>
            <Button size="small" onClick={downloadTemplate} sx={{ textTransform: 'none' }}>
              Sablon letöltése
            </Button>
          </Alert>

          {/* File selection */}
          <Box>
            <Typography variant="body2" fontWeight={500} gutterBottom>
              Excel fájl kiválasztása
            </Typography>
            <Paper
              sx={{
                border: 2,
                borderStyle: 'dashed',
                borderColor: 'divider',
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <Stack spacing={2} alignItems="center">
                <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
                <Box>
                  <Typography
                    variant="body2"
                    color="primary"
                    component="span"
                    sx={{ fontWeight: 500 }}
                  >
                    Fájl kiválasztása
                  </Typography>
                  <Typography variant="body2" color="text.secondary" component="span">
                    {' '}
                    vagy húzza ide
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  XLSX, XLS, CSV fájlok (max. 10MB)
                </Typography>
                <input
                  ref={fileInputRef}
                  type="file"
                  style={{ display: 'none' }}
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileSelect}
                />
              </Stack>
            </Paper>

            {selectedFile && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Kiválasztott fájl:{' '}
                <Typography component="span" fontWeight={500}>
                  {selectedFile.name}
                </Typography>
              </Typography>
            )}
          </Box>

          {/* Upload result */}
          {uploadResult && (
            <Alert
              severity={uploadResult.errors?.length > 0 ? 'warning' : 'success'}
              icon={uploadResult.errors?.length > 0 ? <WarningIcon /> : <CheckCircleIcon />}
            >
              <AlertTitle>Import eredmény</AlertTitle>
              <Typography variant="body2" gutterBottom>
                Importált kedvezményezettek: {uploadResult.imported_count}
              </Typography>

              {uploadResult.errors?.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" fontWeight={500} gutterBottom>
                    Hibák:
                  </Typography>
                  <List dense sx={{ pt: 0 }}>
                    {uploadResult.errors?.map((error, index) => (
                      <ListItem key={index} sx={{ px: 0, py: 0.25 }}>
                        <Typography variant="body2">• {error}</Typography>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Alert>
          )}

          {/* Expected format info */}
          <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
            <Typography variant="body2" fontWeight={500} gutterBottom>
              Várt fájl formátum (3. sortól kezdve):
            </Typography>
            <List dense sx={{ pt: 1 }}>
              <ListItem sx={{ px: 0, py: 0.25 }}>
                <Typography variant="caption">
                  <strong>A oszlop:</strong> Megjegyzés (opcionális)
                </Typography>
              </ListItem>
              <ListItem sx={{ px: 0, py: 0.25 }}>
                <Typography variant="caption">
                  <strong>B oszlop:</strong> Kedvezményezett neve (kötelező)
                </Typography>
              </ListItem>
              <ListItem sx={{ px: 0, py: 0.25 }}>
                <Typography variant="caption">
                  <strong>C oszlop:</strong> Számlaszám (kötelező)
                </Typography>
              </ListItem>
              <ListItem sx={{ px: 0, py: 0.25 }}>
                <Typography variant="caption">
                  <strong>D oszlop:</strong> Összeg (opcionális)
                </Typography>
              </ListItem>
              <ListItem sx={{ px: 0, py: 0.25 }}>
                <Typography variant="caption">
                  <strong>E oszlop:</strong> Teljesítés dátuma (opcionális)
                </Typography>
              </ListItem>
              <ListItem sx={{ px: 0, py: 0.25 }}>
                <Typography variant="caption">
                  <strong>F oszlop:</strong> Közlemény (opcionális)
                </Typography>
              </ListItem>
            </List>
          </Paper>
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Bezárás</Button>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!selectedFile || uploadMutation.isPending}
        >
          {uploadMutation.isPending ? 'Importálás...' : 'Importálás'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExcelImport;
