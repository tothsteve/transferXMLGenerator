import React, { ReactNode } from 'react';
import { useAuth } from '../../hooks/useAuth';
import AuthPage from './AuthPage';
import { Box, CircularProgress, Typography } from '@mui/material';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAdmin?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requireAdmin = false }) => {
  const { state } = useAuth();

  // Show loading spinner while checking authentication
  if (state.isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        flexDirection="column"
      >
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Betöltés...
        </Typography>
      </Box>
    );
  }

  // If not authenticated, show auth page
  if (!state.isAuthenticated) {
    return <AuthPage />;
  }

  // If admin required but user is not admin
  if (requireAdmin && state.currentCompany?.user_role !== 'ADMIN') {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        flexDirection="column"
      >
        <Typography variant="h4" color="error" gutterBottom>
          Hozzáférés megtagadva
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Ehhez a funkcióhoz adminisztrátori jogosultság szükséges.
        </Typography>
      </Box>
    );
  }

  // If no company selected
  if (!state.currentCompany) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        flexDirection="column"
      >
        <Typography variant="h4" gutterBottom>
          Nincs aktív cég
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Kérjük válasszon céget a folytatáshoz.
        </Typography>
      </Box>
    );
  }

  // User is authenticated and has proper permissions
  return <>{children}</>;
};

export default ProtectedRoute;
