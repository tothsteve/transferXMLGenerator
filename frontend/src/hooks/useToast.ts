import { useState, useCallback } from 'react';
import { Toast, ToastType } from '../components/UI/Toast';

export const useToast = (): {
  toasts: Toast[];
  addToast: (type: ToastType, title: string, message?: string, duration?: number) => string;
  removeToast: (id: string) => void;
  success: (title: string, message?: string) => string;
  error: (title: string, message?: string) => string;
  warning: (title: string, message?: string) => string;
  info: (title: string, message?: string) => string;
} => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback(
    (type: ToastType, title: string, message?: string, duration?: number): string => {
      const id = Math.random().toString(36).substr(2, 9);
      const toast: Toast = {
        id,
        type,
        title,
        ...(message && { message }),
        duration: duration || (type === 'error' ? 10000 : 5000),
      };

      setToasts((prev) => [...prev, toast]);
      return id;
    },
    []
  );

  const removeToast = useCallback((id: string): void => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const success = useCallback(
    (title: string, message?: string): string => {
      return addToast('success', title, message);
    },
    [addToast]
  );

  const error = useCallback(
    (title: string, message?: string): string => {
      return addToast('error', title, message);
    },
    [addToast]
  );

  const warning = useCallback(
    (title: string, message?: string): string => {
      return addToast('warning', title, message);
    },
    [addToast]
  );

  const info = useCallback(
    (title: string, message?: string): string => {
      return addToast('info', title, message);
    },
    [addToast]
  );

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
  };
};
