import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
} from '@mui/material';
import { Save, AccountBalance, People } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bankAccountsApi } from '../../services/api';
import { TrustedPartners } from '../TrustedPartners';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps): React.ReactElement {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState({
    account_number: '',
    name: '',
    bank_name: '',
    is_default: true,
  });
  const [isEditing, setIsEditing] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const queryClient = useQueryClient();

  // Fetch default bank account
  const {
    data: defaultAccount,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['bankAccount', 'default'],
    queryFn: () => bankAccountsApi.getDefault(),
    retry: false,
  });

  // Mutation for creating/updating bank account
  const saveBankAccountMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      console.log('🚀 saveBankAccountMutation called with data:', data);
      console.log('🔍 Current isEditing state:', isEditing);
      console.log('📍 Stack trace:', new Error().stack);

      // CRITICAL SAFEGUARD: Don't allow mutation if not in editing mode
      if (!isEditing) {
        console.log('🚫 BLOCKING MUTATION - not in editing mode');
        throw new Error('Cannot save when not in editing mode');
      }

      if (defaultAccount?.data?.id) {
        // Update existing account
        console.log('📝 Updating existing account:', defaultAccount.data.id);
        return bankAccountsApi.update(defaultAccount.data.id, data);
      } else {
        // Create new account
        console.log('🆕 Creating new account');
        return bankAccountsApi.create(data);
      }
    },
    onSuccess: (response) => {
      console.log('✅ saveBankAccountMutation onSuccess called');
      console.log('📦 Response:', response);
      console.log('🔍 Current isEditing state in onSuccess:', isEditing);

      // Update form data with the response to prevent flicker
      if (response?.data) {
        setFormData({
          account_number: response.data.account_number || '',
          name: response.data.name || '',
          bank_name: response.data.bank_name || '',
          is_default: response.data.is_default || true,
        });
      }

      setSuccessMessage('Alapértelmezett bank számla beállításai mentve!');
      setIsEditing(false);

      // Invalidate and refetch default account
      queryClient.invalidateQueries({ queryKey: ['bankAccount', 'default'] });

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    },
    onError: (error: unknown) => {
      console.error('Error saving bank account:', error);
      setSuccessMessage('Hiba történt a mentés során. Kérlek próbáld újra!');

      // Clear error message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);
    },
  });

  // Update form when default account is loaded (but NEVER while editing)
  useEffect(() => {
    console.log('🔍 Settings useEffect triggered:', {
      hasData: !!defaultAccount?.data,
      isEditing,
      accountNumber: defaultAccount?.data?.account_number,
    });

    // CRITICAL: Never update form data while editing - this was causing the race condition
    if (isEditing) {
      console.log('⏸️ Skipping form update - currently editing');
      return; // Exit early if editing - do not touch form data
    }

    if (defaultAccount?.data) {
      console.log('📝 Updating form data from API response');
      // Only update on initial load or after successful save (when not editing)
      setFormData({
        account_number: defaultAccount.data.account_number || '',
        name: defaultAccount.data.name || '',
        bank_name: defaultAccount.data.bank_name || '',
        is_default: defaultAccount.data.is_default || true,
      });
    }
  }, [defaultAccount?.data, isEditing]);

  const handleInputChange =
    (field: string) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
      setFormData((prev) => ({
        ...prev,
        [field]: event.target.value,
      }));
    };

  const handleSubmit = (event: React.FormEvent): void => {
    event.preventDefault();
    console.log('📝 handleSubmit called, isEditing:', isEditing);

    // CRITICAL: Only allow submission if we're actually in editing mode
    if (!isEditing) {
      console.log('🚫 Prevented submission - not in editing mode');
      return;
    }

    console.log('✅ Proceeding with mutation');
    saveBankAccountMutation.mutate(formData);
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number): void => {
    setTabValue(newValue);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        Beállítások
      </Typography>

      <Paper elevation={2}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} sx={{ px: 3 }}>
            <Tab
              icon={<AccountBalance />}
              label="Bank számla"
              sx={{ textTransform: 'none', fontWeight: 600 }}
            />
            <Tab
              icon={<People />}
              label="Automatikusan Fizetettnek Jelölt Partnerek"
              sx={{ textTransform: 'none', fontWeight: 600 }}
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {successMessage && (
            <Alert severity={successMessage.includes('Hiba') ? 'error' : 'success'} sx={{ mb: 3 }}>
              {successMessage}
            </Alert>
          )}

          {error && (
            <Alert severity="info" sx={{ mb: 3 }}>
              Nincs beállított alapértelmezett bank számla. Hozz létre egyet alább.
            </Alert>
          )}

          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Alapértelmezett Bank Számla
              </Typography>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Ez a számla lesz automatikusan kiválasztva új utalások létrehozásakor.
            </Typography>

            {/* Edit Button - Outside form to prevent auto-submit */}
            {!isEditing && (
              <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
                <Button
                  type="button"
                  variant="contained"
                  startIcon={<AccountBalance />}
                  onClick={() => {
                    console.log('🔧 Edit button clicked, setting isEditing to true');
                    setIsEditing(true);
                  }}
                >
                  Szerkesztés
                </Button>
              </Box>
            )}

            <form onSubmit={handleSubmit}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                  gap: 3,
                  mb: 3,
                }}
              >
                <TextField
                  label="Számlaszám"
                  value={formData.account_number}
                  onChange={handleInputChange('account_number')}
                  disabled={!isEditing}
                  required
                  placeholder="1234567890123456"
                  helperText="16 számjegyű számlaszám"
                />

                <TextField
                  label="Számla neve"
                  value={formData.name}
                  onChange={handleInputChange('name')}
                  disabled={!isEditing}
                  required
                  placeholder="Főszámla"
                />

                <TextField
                  label="Bank neve"
                  value={formData.bank_name}
                  onChange={handleInputChange('bank_name')}
                  disabled={!isEditing}
                  required
                  placeholder="OTP Bank"
                  sx={{ gridColumn: { md: '1 / -1' } }}
                />
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_default}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, is_default: e.target.checked }))
                    }
                    disabled={!isEditing}
                  />
                }
                label="Alapértelmezett számla"
              />

              {/* Form Buttons - Only shown when editing */}
              {isEditing && (
                <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={
                      saveBankAccountMutation.isPending ? <CircularProgress size={20} /> : <Save />
                    }
                    color="primary"
                    disabled={saveBankAccountMutation.isPending}
                  >
                    {saveBankAccountMutation.isPending ? 'Mentés...' : 'Mentés'}
                  </Button>
                  <Button
                    type="button"
                    variant="outlined"
                    onClick={() => {
                      setIsEditing(false);
                      // Reset form to original values
                      if (defaultAccount?.data) {
                        setFormData({
                          account_number: defaultAccount.data.account_number || '',
                          name: defaultAccount.data.name || '',
                          bank_name: defaultAccount.data.bank_name || '',
                          is_default: defaultAccount.data.is_default || true,
                        });
                      }
                    }}
                  >
                    Mégse
                  </Button>
                </Box>
              )}
            </form>

            {!defaultAccount?.data && !error && (
              <Alert severity="warning" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  <strong>Nincs alapértelmezett bank számla beállítva.</strong>
                  <br />
                  Kérlek add meg a számla adatait a fenti űrlapon keresztül.
                </Typography>
              </Alert>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ p: 3 }}>
            <TrustedPartners />
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Settings;
