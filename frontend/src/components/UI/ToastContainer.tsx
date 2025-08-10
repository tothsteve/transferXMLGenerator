import React from 'react';
import { Box, Stack } from '@mui/material';
import ToastComponent, { Toast } from './Toast';

interface ToastContainerProps {
  toasts: Toast[];
  onClose: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        zIndex: 1400,
        maxWidth: 400,
        width: '100%',
        pointerEvents: 'none',
      }}
    >
      <Stack spacing={1}>
        {toasts.map((toast) => (
          <Box key={toast.id} sx={{ pointerEvents: 'auto' }}>
            <ToastComponent toast={toast} onClose={onClose} />
          </Box>
        ))}
      </Stack>
    </Box>
  );
};

export default ToastContainer;