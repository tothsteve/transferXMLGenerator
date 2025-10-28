import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Divider,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import {
  Save as SaveIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Sync as SyncIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useBillingoSettings, useSaveBillingoSettings, useTriggerBillingoSync } from '../../hooks/useBillingo';
import { useToastContext } from '../../context/ToastContext';

const BillingoSettings: React.FC = () => {
  const { success: showSuccess, error: showError } = useToastContext();

  const { data: settings, isLoading, error: fetchError } = useBillingoSettings();
  const saveMutation = useSaveBillingoSettings();
  const syncMutation = useTriggerBillingoSync();

  const [apiKey, setApiKey] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (settings) {
      setIsActive(settings.is_active);
      // Don't set API key from server (it's write-only)
      setApiKey('');
    }
  }, [settings]);

  const handleSave = (): void => {
    if (!apiKey.trim() && !settings) {
      showError('API kulcs szükséges', 'Kérjük, adja meg a Billingo API kulcsot');
      return;
    }

    saveMutation.mutate(
      {
        ...(apiKey.trim() && { api_key_input: apiKey.trim() }),
        is_active: isActive,
      },
      {
        onSuccess: () => {
          showSuccess(
            'Beállítások mentve',
            'A Billingo API beállítások sikeresen mentve'
          );
          setApiKey('');
          setHasChanges(false);
        },
        onError: (err: Error) => {
          showError(
            'Mentési hiba',
            err.message || 'Hiba történt a beállítások mentése során'
          );
        },
      }
    );
  };

  const handleApiKeyChange = (value: string): void => {
    setApiKey(value);
    setHasChanges(true);
  };

  const handleIsActiveChange = (checked: boolean): void => {
    setIsActive(checked);
    setHasChanges(true);
  };

  const handleIncrementalSync = (): void => {
    syncMutation.mutate(false, {
      onSuccess: (result) => {
        showSuccess(
          'Szinkronizálás sikeres',
          `${result.invoices_processed} számla feldolgozva (${result.invoices_created} új, ${result.invoices_updated} frissítve)`
        );
      },
      onError: (err: Error) => {
        showError(
          'Szinkronizálási hiba',
          err.message || 'Hiba történt a szinkronizálás során'
        );
      },
    });
  };

  const handleFullSync = (): void => {
    syncMutation.mutate(true, {
      onSuccess: (result) => {
        showSuccess(
          'Teljes szinkronizálás sikeres',
          `${result.invoices_processed} számla feldolgozva (${result.invoices_created} új, ${result.invoices_updated} frissítve)`
        );
      },
      onError: (err: Error) => {
        showError(
          'Szinkronizálási hiba',
          err.message || 'Hiba történt a teljes szinkronizálás során'
        );
      },
    });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={4}>
        <CircularProgress />
        <Typography ml={2} color="text.secondary">
          Beállítások betöltése...
        </Typography>
      </Box>
    );
  }

  if (fetchError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <Typography variant="subtitle2" fontWeight="bold">
            Hiba a beállítások betöltése során
          </Typography>
          <Typography variant="body2">
            {fetchError.message || 'Ismeretlen hiba történt'}
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 800 }}>
      {/* Header */}
      <Stack spacing={1} mb={3}>
        <Typography variant="h4">Billingo Beállítások</Typography>
        <Typography variant="body2" color="text.secondary">
          Konfigurálja a Billingo API kapcsolatot a számlák automatikus szinkronizálásához
        </Typography>
      </Stack>

      {/* Current Status Card */}
      {settings && (
        <Card sx={{ mb: 3, bgcolor: settings.has_api_key ? 'success.50' : 'warning.50' }}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center">
              {settings.has_api_key ? (
                <>
                  <CheckIcon color="success" />
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      API kulcs konfigurálva
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      A Billingo API kapcsolat be van állítva
                    </Typography>
                    {settings.last_sync_time && (
                      <Typography variant="caption" color="text.secondary">
                        Utolsó szinkronizálás: {settings.last_sync_time_formatted}
                      </Typography>
                    )}
                  </Box>
                </>
              ) : (
                <>
                  <WarningIcon color="warning" />
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      API kulcs hiányzik
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Adja meg az API kulcsot a Billingo számlák szinkronizálásához
                    </Typography>
                  </Box>
                </>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Settings Form */}
      <Paper sx={{ p: 3 }}>
        <Stack spacing={3}>
          {/* API Key Field */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <Typography variant="subtitle1" fontWeight="bold">
                Billingo API kulcs
              </Typography>
              {settings?.has_api_key ? (
                <Chip
                  label="Már beállítva"
                  size="small"
                  color="success"
                  variant="outlined"
                  sx={{ fontWeight: 'bold' }}
                />
              ) : (
                <Chip
                  label="Nincs beállítva"
                  size="small"
                  color="warning"
                  variant="outlined"
                  sx={{ fontWeight: 'bold' }}
                />
              )}
            </Stack>

            {settings?.has_api_key && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Az API kulcs biztonsági okokból nem jeleníthető meg.</strong>
                  <br />
                  Ha új kulcsot szeretne beállítani, írja be az új kulcsot az alábbi mezőbe.
                  Ha üresen hagyja, a meglévő kulcs megmarad.
                </Typography>
              </Alert>
            )}

            <TextField
              fullWidth
              type="password"
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder={settings?.has_api_key ? '••••••••••••••••' : 'Adja meg az API kulcsot'}
              label={settings?.has_api_key ? 'Új API kulcs (opcionális)' : 'API kulcs (kötelező)'}
              helperText={
                settings?.has_api_key
                  ? 'Hagyja üresen, ha nem szeretné megváltoztatni az API kulcsot'
                  : 'A Billingo API kulcs a Billingo adminisztrációs felületen található'
              }
              disabled={saveMutation.isPending}
              required={!settings?.has_api_key}
            />
          </Box>

          <Divider />

          {/* Active Switch */}
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={isActive}
                  onChange={(e) => handleIsActiveChange(e.target.checked)}
                  disabled={saveMutation.isPending}
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    Szinkronizálás engedélyezve
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ha aktív, a számlák automatikusan szinkronizálódnak a Billingo rendszerből
                  </Typography>
                </Box>
              }
            />
          </Box>

          <Divider />

          {/* Info Box */}
          <Alert severity="info" icon={<InfoIcon />}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Hogyan szerezze be az API kulcsot?
            </Typography>
            <Typography variant="body2" component="div">
              <ol style={{ margin: 0, paddingLeft: '20px' }}>
                <li>Jelentkezzen be a Billingo fiókjába</li>
                <li>Menjen a Beállítások &gt; API menüpontba</li>
                <li>Hozzon létre egy új API kulcsot vagy használja a meglévőt</li>
                <li>Másolja be a kulcsot ebbe a mezőbe</li>
              </ol>
            </Typography>
          </Alert>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} justifyContent="space-between">
            {/* Sync Buttons */}
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                color="primary"
                startIcon={syncMutation.isPending ? <CircularProgress size={20} /> : <SyncIcon />}
                onClick={handleIncrementalSync}
                disabled={syncMutation.isPending || !settings?.has_api_key}
              >
                Szinkronizálás (utolsó óta)
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                startIcon={syncMutation.isPending ? <CircularProgress size={20} /> : <RefreshIcon />}
                onClick={handleFullSync}
                disabled={syncMutation.isPending || !settings?.has_api_key}
              >
                Teljes szinkronizálás (elejétől)
              </Button>
            </Stack>

            {/* Save Button */}
            <Button
              variant="contained"
              startIcon={saveMutation.isPending ? <CircularProgress size={20} /> : <SaveIcon />}
              onClick={handleSave}
              disabled={saveMutation.isPending || (!hasChanges && !!settings?.has_api_key)}
            >
              Mentés
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
};

export default BillingoSettings;
