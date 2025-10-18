import React, { createContext, useContext, ReactNode } from 'react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/UI/ToastContainer';
import { ToastType } from '../components/UI/Toast';

interface ToastContextValue {
  success: (title: string, message?: string) => string;
  error: (title: string, message?: string) => string;
  warning: (title: string, message?: string) => string;
  info: (title: string, message?: string) => string;
  addToast: (type: ToastType, title: string, message?: string, duration?: number) => string;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const useToastContext = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const { toasts, removeToast, success, error, warning, info, addToast } = useToast();

  // Listen for global toast events
  React.useEffect(() => {
    const handleToastEvent = (event: CustomEvent): void => {
      const { type, title, message, duration } = event.detail;
      addToast(type, title, message, duration);
    };

    window.addEventListener('toast' as any, handleToastEvent);
    return (): void => window.removeEventListener('toast' as any, handleToastEvent);
  }, [addToast]);

  const value: ToastContextValue = {
    success,
    error,
    warning,
    info,
    addToast,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
};
