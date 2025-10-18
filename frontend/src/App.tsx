import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout/Layout';
import ErrorBoundary from './components/UI/ErrorBoundary';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import customTheme from './theme/customTheme';

// Type guard for error objects with response status
function hasResponseStatus(error: unknown): error is { response: { status: number } } {
  if (typeof error !== 'object' || error === null) return false;
  if (!('response' in error)) return false;

  const errorWithResponse = error as { response: unknown };
  if (typeof errorWithResponse.response !== 'object' || errorWithResponse.response === null) return false;
  if (!('status' in errorWithResponse.response)) return false;

  const response = errorWithResponse.response as { status: unknown };
  return typeof response.status === 'number';
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: unknown) => {
        // Don't retry on 4xx errors
        if (hasResponseStatus(error) && error.response.status >= 400 && error.response.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
    },
    mutations: {
      retry: (failureCount, error: unknown) => {
        // Don't retry mutations on client errors
        if (hasResponseStatus(error) && error.response.status >= 400 && error.response.status < 500) {
          return false;
        }
        return failureCount < 1;
      },
    },
  },
});

function App(): React.ReactElement {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={customTheme}>
        <CssBaseline />
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <ToastProvider>
              <Router>
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              </Router>
            </ToastProvider>
          </QueryClientProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
