import React, { Component, ReactNode } from 'react';
import { Alert, AlertTitle, Box, Typography, Button, Card, CardContent } from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            minHeight: '100vh',
            bgcolor: 'background.default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
          }}
        >
          <Card sx={{ maxWidth: 500, width: '100%' }}>
            <CardContent sx={{ textAlign: 'center', p: 4 }}>
              <WarningIcon 
                sx={{ 
                  fontSize: 60, 
                  color: 'error.main', 
                  mb: 2 
                }} 
              />
              
              <Typography variant="h5" component="h2" gutterBottom>
                Alkalmazás hiba történt
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Váratlan hiba történt az alkalmazásban. Kérjük, frissítse az oldalt vagy próbálja újra később.
              </Typography>

              {this.state.error && (
                <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                  <AlertTitle>Technikai részletek</AlertTitle>
                  <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                    {this.state.error.toString()}
                  </Typography>
                </Alert>
              )}

              <Button
                variant="contained"
                onClick={() => window.location.reload()}
                fullWidth
                size="large"
              >
                Oldal újratöltése
              </Button>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;