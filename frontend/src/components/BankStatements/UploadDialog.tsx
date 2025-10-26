/**
 * @fileoverview Bank statement file upload dialog with drag-and-drop and multiple file support
 * @module components/BankStatements/UploadDialog
 */

import { useRef, useState, DragEvent } from 'react';
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
  Stack,
  IconButton,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
} from '@mui/icons-material';
import { useUploadBankStatement } from '../../hooks/api';
import { useToastContext } from '../../context/ToastContext';

/**
 * Props for UploadDialog component.
 *
 * @interface UploadDialogProps
 */
interface UploadDialogProps {
  /** Whether dialog is open */
  open: boolean;

  /** Callback when dialog should close */
  onClose: () => void;

  /** Callback when upload succeeds */
  onSuccess: () => void;
}

/**
 * File upload status tracking.
 *
 * @interface FileUploadStatus
 */
interface FileUploadStatus {
  /** The file being uploaded */
  file: File;

  /** Upload status */
  status: 'pending' | 'uploading' | 'success' | 'error';

  /** Error message if upload failed */
  errorMessage?: string;

  /** Number of transactions processed (on success) */
  transactionCount?: number;
}


/**
 * Bank statement file upload dialog component.
 *
 * Features:
 * - Drag-and-drop file upload
 * - Click to select file
 * - File validation (type, size)
 * - Upload progress indication
 * - Supported banks and formats display
 * - Error handling with detailed messages
 *
 * @component
 * @example
 * ```tsx
 * <UploadDialog
 *   open={showDialog}
 *   onClose={() => setShowDialog(false)}
 *   onSuccess={handleSuccess}
 * />
 * ```
 */
const UploadDialog: React.FC<UploadDialogProps> = ({ open, onClose, onSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isUploadingRef = useRef(false);
  const { success: showSuccess, error: showError } = useToastContext();

  // Local state
  const [fileStatuses, setFileStatuses] = useState<FileUploadStatus[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragFileCount, setDragFileCount] = useState(0);

  // React Query hooks
  const uploadMutation = useUploadBankStatement();

  /**
   * Validate file type and size.
   *
   * @param file - File to validate
   * @returns Error message if invalid, null if valid
   */
  const validateFile = (file: File): string | null => {
    // Check file type
    const allowedExtensions = ['pdf', 'csv', 'xml', 'xls', 'xlsx'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext === undefined || ext === '' || !allowedExtensions.includes(ext)) {
      return `Nem támogatott fájltípus. Csak ${allowedExtensions.join(', ').toUpperCase()} fájlok engedélyezettek.`;
    }

    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return 'A fájl túl nagy. Maximális méret: 50 MB';
    }

    return null;
  };

  /**
   * Handle file selection from input or drop.
   *
   * @param files - Selected files (one or more)
   */
  const handleFileSelect = (files: FileList | File[]): void => {
    const fileArray = Array.from(files);
    const validFiles: FileUploadStatus[] = [];

    for (const file of fileArray) {
      const error = validateFile(file);
      if (error !== null) {
        showError('Érvénytelen fájl', `${file.name}: ${error}`);
        continue;
      }

      validFiles.push({
        file,
        status: 'pending',
      });
    }

    if (validFiles.length > 0) {
      setFileStatuses((prev) => [...prev, ...validFiles]);
    }
  };

  /**
   * Handle file input change event.
   *
   * @param event - Input change event
   */
  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const files = event.target.files;
    if (files !== null && files.length > 0) {
      handleFileSelect(files);
    }
    // Reset input so same file can be selected again
    event.target.value = '';
  };

  /**
   * Handle drag over event.
   *
   * @param event - Drag event
   */
  const handleDragOver = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setIsDragging(true);

    // Detect number of files being dragged
    const fileCount = event.dataTransfer.items?.length ?? event.dataTransfer.files?.length ?? 0;
    setDragFileCount(fileCount);
  };

  /**
   * Handle drag leave event.
   */
  const handleDragLeave = (): void => {
    setIsDragging(false);
    setDragFileCount(0);
  };

  /**
   * Handle file drop event.
   *
   * @param event - Drop event
   */
  const handleDrop = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setIsDragging(false);
    setDragFileCount(0);

    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  };

  /**
   * Handle upload button click - processes all pending files sequentially.
   *
   * Uses a boolean ref lock to prevent double submission (React.StrictMode can cause double invocation).
   * The isUploadingRef is checked and set synchronously at function start to ensure atomicity.
   *
   * Each file is uploaded sequentially with status updates for success/error.
   */
  const handleUpload = async (): Promise<void> => {
    console.log('[DEBUG] handleUpload called, isUploading:', isUploadingRef.current);

    // Double-guard: ref check AND immediate state update
    if (isUploadingRef.current) {
      console.log('[DEBUG] BLOCKED - already uploading');
      return;
    }

    // Set ref AND update all pending files to uploading IMMEDIATELY (synchronous state update)
    console.log('[DEBUG] Setting isUploadingRef to true');
    isUploadingRef.current = true;
    const pendingFiles = fileStatuses.filter((f) => f.status === 'pending');

    console.log('[DEBUG] Pending files count:', pendingFiles.length);

    if (pendingFiles.length === 0) {
      console.log('[DEBUG] No pending files, resetting');
      isUploadingRef.current = false;
      return;
    }

    // Mark ALL files as uploading immediately to prevent double-click
    console.log('[DEBUG] Marking all files as uploading');
    setFileStatuses((prev) =>
      prev.map((f) => (f.status === 'pending' ? { ...f, status: 'uploading' } : f))
    );

    try {
      let successCount = 0;
      let errorCount = 0;

      for (const fileStatus of pendingFiles) {
        console.log('[DEBUG] Uploading file:', fileStatus.file.name);
        try {
          const result = await uploadMutation.mutateAsync(fileStatus.file);
          console.log('[DEBUG] Upload success:', fileStatus.file.name);

          // Update status to success
          setFileStatuses((prev) =>
            prev.map((f) =>
              f.file === fileStatus.file
                ? {
                    ...f,
                    status: 'success',
                    transactionCount: result.total_transactions,
                  }
                : f
            )
          );
          successCount++;
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Ismeretlen hiba';

          // Update status to error
          setFileStatuses((prev) =>
            prev.map((f) =>
              f.file === fileStatus.file
                ? { ...f, status: 'error', errorMessage: message }
                : f
            )
          );
          errorCount++;
        }
      }

      // Show summary toast
      if (successCount > 0 && errorCount === 0) {
        showSuccess(
          'Sikeres feltöltés',
          `${successCount} kivonat sikeresen feltöltve.`
        );
        onSuccess();
        setTimeout(handleClose, 1500); // Auto-close after success
      } else if (successCount > 0 && errorCount > 0) {
        showSuccess(
          'Részben sikeres',
          `${successCount} sikeres, ${errorCount} sikertelen feltöltés.`
        );
        onSuccess();
      } else if (errorCount > 0) {
        showError(
          'Feltöltési hiba',
          `Minden feltöltés sikertelen (${errorCount} fájl).`
        );
      }
    } finally {
      console.log('[DEBUG] Upload complete, resetting isUploadingRef');
      isUploadingRef.current = false;
    }
  };

  /**
   * Handle dialog close.
   *
   * Resets state and calls onClose callback.
   */
  const handleClose = (): void => {
    // Only reset if not currently uploading
    if (!isUploadingRef.current) {
      setFileStatuses([]);
      setIsDragging(false);
      setDragFileCount(0);
      uploadMutation.reset();
    }
    onClose();
  };

  /**
   * Remove a file from the upload list.
   *
   * @param file - File to remove
   */
  const handleRemoveFile = (file: File): void => {
    setFileStatuses((prev) => prev.filter((f) => f.file !== file));
  };

  /**
   * Open file picker.
   */
  const handleBrowseClick = (): void => {
    fileInputRef.current?.click();
  };

  // Compute upload button state
  const pendingCount = fileStatuses.filter((f) => f.status === 'pending').length;
  const isUploading = fileStatuses.some((f) => f.status === 'uploading');

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        Bankkivonat feltöltése
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Stack spacing={3}>
          {/* Drag and Drop Area */}
          <Paper
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            sx={{
              p: 4,
              border: '2px dashed',
              borderColor: isDragging ? 'primary.main' : 'divider',
              bgcolor: isDragging ? 'action.hover' : 'background.default',
              cursor: 'pointer',
              transition: 'all 0.2s',
              textAlign: 'center',
              '&:hover': {
                bgcolor: 'action.hover',
                borderColor: 'primary.main',
              },
            }}
            onClick={handleBrowseClick}
          >
            <CloudUploadIcon
              sx={{
                fontSize: 64,
                color: isDragging ? 'primary.main' : 'text.secondary',
                mb: 2,
              }}
            />
            <Typography variant="h6" gutterBottom>
              {isDragging
                ? `Engedje el ${dragFileCount > 0 ? `a ${dragFileCount} fájlt` : 'a fájlokat'} ide`
                : 'Húzza ide a fájlokat'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {isDragging
                ? `${dragFileCount} fájl kiválasztva`
                : 'vagy kattintson a fájlok kiválasztásához (több fájl is választható)'}
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Chip label="PDF" size="small" sx={{ mx: 0.5 }} />
              <Chip label="CSV" size="small" sx={{ mx: 0.5 }} />
              <Chip label="XML" size="small" sx={{ mx: 0.5 }} />
              <Chip label="XLS" size="small" sx={{ mx: 0.5 }} />
            </Box>
          </Paper>

          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.csv,.xml,.xls,.xlsx"
            onChange={handleFileInputChange}
            multiple
            style={{ display: 'none' }}
          />

          {/* Selected Files List */}
          {fileStatuses.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Kiválasztott fájlok ({fileStatuses.length})
              </Typography>
              <List dense>
                {fileStatuses.map((fileStatus, index) => {
                  const statusIcon = (() => {
                    switch (fileStatus.status) {
                      case 'pending':
                        return <HourglassIcon color="action" />;
                      case 'uploading':
                        return <LinearProgress sx={{ width: 24 }} />;
                      case 'success':
                        return <CheckCircleIcon color="success" />;
                      case 'error':
                        return <ErrorIcon color="error" />;
                      default:
                        return null;
                    }
                  })();

                  return (
                    <ListItem
                      key={index}
                      secondaryAction={
                        fileStatus.status === 'pending' ? (
                          <IconButton
                            edge="end"
                            size="small"
                            onClick={() => handleRemoveFile(fileStatus.file)}
                            aria-label="Fájl eltávolítása"
                          >
                            <CloseIcon fontSize="small" />
                          </IconButton>
                        ) : null
                      }
                    >
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        {statusIcon}
                      </ListItemIcon>
                      <ListItemText
                        primary={fileStatus.file.name}
                        secondary={(() => {
                          const sizeKB = (fileStatus.file.size / 1024).toFixed(0);

                          if (fileStatus.status === 'success' && fileStatus.transactionCount !== undefined) {
                            return `${sizeKB} KB • ${fileStatus.transactionCount} tranzakció feldolgozva`;
                          }

                          if (fileStatus.status === 'error' && fileStatus.errorMessage !== undefined) {
                            return `${sizeKB} KB • Hiba: ${fileStatus.errorMessage}`;
                          }

                          if (fileStatus.status === 'uploading') {
                            return `${sizeKB} KB • Feltöltés folyamatban...`;
                          }

                          return `${sizeKB} KB`;
                        })()}
                        primaryTypographyProps={{
                          sx: {
                            ...(fileStatus.status === 'error' ? { color: 'error.main' } : {}),
                            ...(fileStatus.status === 'success' ? { color: 'success.main' } : {}),
                          },
                        }}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </Box>
          )}

          {/* Info Alert */}
          <Alert severity="info">
            <AlertTitle>Tudnivalók</AlertTitle>
            <Typography variant="body2">
              • A kivonat automatikusan feldolgozásra kerül feltöltés után
              <br />
              • A rendszer automatikusan felismeri a bank típusát
              <br />
              • A tranzakciók automatikusan párosításra kerülnek a NAV számlákkal
              <br />• Maximum 50 MB méretű fájl tölthető fel
            </Typography>
          </Alert>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={handleClose} disabled={isUploading}>
          {isUploading ? 'Bezárás' : 'Mégse'}
        </Button>
        <Button
          variant="contained"
          onClick={() => void handleUpload()}
          disabled={pendingCount === 0 || isUploading}
          startIcon={<CloudUploadIcon />}
        >
          {isUploading
            ? `Feltöltés... (${fileStatuses.filter((f) => f.status === 'uploading').length}/${pendingCount + fileStatuses.filter((f) => f.status === 'uploading').length})`
            : `Feltöltés (${pendingCount})`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UploadDialog;
