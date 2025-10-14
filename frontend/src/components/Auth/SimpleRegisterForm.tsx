import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Link,
  Container,
} from '@mui/material';
import { useAuth, RegisterData } from '../../contexts/AuthContext';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

const SimpleRegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { state, register, clearError } = useAuth();
  const [formData, setFormData] = useState<RegisterData>({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    company_name: '',
    company_tax_id: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (state.error !== null && state.error !== '') {
      clearError();
    }
  };

  const validateForm = (): string | null => {
    if (!formData.username.trim()) return 'Felhasználónév kötelező';
    if (!formData.email.trim()) return 'E-mail cím kötelező';
    if (!formData.first_name.trim()) return 'Keresztnév kötelező';
    if (!formData.last_name.trim()) return 'Vezetéknév kötelező';
    if (!formData.company_name.trim()) return 'Cég neve kötelező';
    if (!formData.company_tax_id.trim()) return 'Adószám kötelező';
    if (formData.password.length < 8)
      return 'A jelszónak legalább 8 karakter hosszúnak kell lennie';
    if (formData.password !== formData.password_confirm) return 'A jelszavak nem egyeznek';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    const error = validateForm();
    if (error !== null && error !== '') {
      clearError();
      return;
    }

    try {
      await register(formData);
    } catch (error) {
      // Error is handled by the context
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Paper elevation={6} sx={{ p: 4, mt: 8, borderRadius: 2 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          {/* Logo */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              mb: 3,
            }}
          >
            <img
              src="/logo192.png"
              alt="ITCardigan Logo"
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                border: '2px solid #e0e0e0',
              }}
            />
            <Box>
              <Typography component="h1" variant="h4" fontWeight="bold" color="primary">
                Transfer
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Generator
              </Typography>
            </Box>
          </Box>

          <Typography component="h2" variant="h5" gutterBottom>
            Regisztráció
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
            Hozzon létre új fiókot és céget
          </Typography>

          {state.error !== null && state.error !== '' && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {state.error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Felhasználói adatok
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                required
                fullWidth
                id="first_name"
                label="Keresztnév"
                name="first_name"
                autoComplete="given-name"
                value={formData.first_name}
                onChange={handleChange}
              />
              <TextField
                required
                fullWidth
                id="last_name"
                label="Vezetéknév"
                name="last_name"
                autoComplete="family-name"
                value={formData.last_name}
                onChange={handleChange}
              />
            </Box>

            <TextField
              required
              fullWidth
              id="email"
              label="E-mail cím"
              name="email"
              autoComplete="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              sx={{ mb: 2 }}
            />

            <TextField
              required
              fullWidth
              id="username"
              label="Felhasználónév"
              name="username"
              autoComplete="username"
              value={formData.username}
              onChange={handleChange}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                required
                fullWidth
                id="password"
                label="Jelszó"
                name="password"
                type="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
              />
              <TextField
                required
                fullWidth
                id="password_confirm"
                label="Jelszó megerősítése"
                name="password_confirm"
                type="password"
                autoComplete="new-password"
                value={formData.password_confirm}
                onChange={handleChange}
              />
            </Box>

            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
              Céginformációk
            </Typography>

            <TextField
              required
              fullWidth
              id="company_name"
              label="Cégnév"
              name="company_name"
              value={formData.company_name}
              onChange={handleChange}
              sx={{ mb: 2 }}
            />

            <TextField
              required
              fullWidth
              id="company_tax_id"
              label="Adószám"
              name="company_tax_id"
              placeholder="12345678-1-23"
              value={formData.company_tax_id}
              onChange={handleChange}
              sx={{ mb: 3 }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={state.isLoading}
              sx={{ mt: 3, mb: 2, py: 1.5 }}
            >
              {state.isLoading ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Regisztráció...
                </>
              ) : (
                'Regisztráció'
              )}
            </Button>

            <Box textAlign="center">
              <Link
                component="button"
                variant="body2"
                onClick={(e) => {
                  e.preventDefault();
                  onSwitchToLogin();
                }}
              >
                Már van fiókja? Jelentkezzen be!
              </Link>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default SimpleRegisterForm;
