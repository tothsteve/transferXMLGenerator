import React from 'react';
import { Alert, AlertTitle, IconButton, Fade } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastProps {
  toast: Toast;
  onClose: (id: string) => void;
}

const ToastComponent: React.FC<ToastProps> = ({ toast, onClose }) => {
  React.useEffect(() => {
    const timer = setTimeout(() => {
      onClose(toast.id);
    }, toast.duration || 5000);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onClose]);

  return (
    <Fade in timeout={300}>
      <Alert
        severity={toast.type}
        onClose={() => onClose(toast.id)}
        action={
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={() => onClose(toast.id)}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        }
        sx={{
          mb: 1,
          maxWidth: toast.message && toast.message.length > 100 ? '600px' : '400px',
          '& .MuiAlert-message': {
            width: '100%',
            whiteSpace: 'pre-line',
          },
        }}
      >
        <AlertTitle sx={{ fontWeight: 600 }}>{toast.title}</AlertTitle>
        {toast.message && toast.message}
      </Alert>
    </Fade>
  );
};

export default ToastComponent;