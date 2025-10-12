import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Avatar,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
} from '@mui/material';
import { CheckCircle as CheckCircleIcon, Add as AddIcon } from '@mui/icons-material';
import { PDFProcessingResult } from './PDFImportWizard';

interface TemplateStepProps {
  previewData: PDFProcessingResult;
  onCreateTransfers: () => void;
}

export const TemplateStep: React.FC<TemplateStepProps> = ({ previewData, onCreateTransfers }) => {
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('hu-HU', {
      style: 'currency',
      currency: 'HUF',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Box sx={{ p: { xs: 2, sm: 3 }, textAlign: 'center', maxWidth: '100%', mx: 'auto' }}>
      {/* Success Icon */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <Avatar
          sx={{
            width: { xs: 60, sm: 70 },
            height: { xs: 60, sm: 70 },
            bgcolor: 'success.main',
            fontSize: { xs: 30, sm: 35 },
          }}
        >
          <CheckCircleIcon fontSize="inherit" />
        </Avatar>
      </Box>

      {/* Success Message */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h5"
          component="h2"
          fontWeight="bold"
          gutterBottom
          sx={{ fontSize: { xs: '1.4rem', sm: '1.75rem' } }}
        >
          🎉 Sablon Sikeresen {previewData.template_updated ? 'Frissítve' : 'Létrehozva'}!
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
        >
          A PDF fájlok feldolgozása befejeződött és a sablon készen áll a használatra.
        </Typography>
      </Box>

      {/* Template Summary */}
      <Card elevation={1} sx={{ mb: 3 }}>
        <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography
            variant="subtitle1"
            fontWeight={600}
            gutterBottom
            textAlign="center"
            sx={{ fontSize: { xs: '1rem', sm: '1.1rem' } }}
          >
            📄 Sablon Összefoglaló
          </Typography>

          <Box sx={{ display: { xs: 'block', md: 'flex' }, gap: 4, textAlign: 'left' }}>
            <Box sx={{ flex: 1, mb: { xs: 3, md: 0 } }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Alapadatok
              </Typography>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Sablon neve:
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {previewData.template.name}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Sablon ID:
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    #{previewData.template.id}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Kedvezményezettek:
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {previewData.template.beneficiary_count}
                  </Typography>
                </Box>
              </Stack>
            </Box>

            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Feldolgozás eredménye
              </Typography>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Tranzakciók:
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {previewData.transactions_processed}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Összes összeg:
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {formatCurrency(previewData.total_amount)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Meglévő kedvezményezett:
                  </Typography>
                  <Typography variant="body2" fontWeight={500} color="success.main">
                    {previewData.beneficiaries_matched}
                  </Typography>
                </Box>
                {previewData.beneficiaries_created > 0 && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Új kedvezményezett:
                    </Typography>
                    <Typography variant="body2" fontWeight={500} color="warning.main">
                      {previewData.beneficiaries_created}
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Consolidations Summary */}
      {previewData.consolidations && previewData.consolidations.length > 0 && (
        <Alert severity="warning" sx={{ mb: 4 }}>
          <AlertTitle>🔄 Összevonások</AlertTitle>
          <List dense>
            {previewData.consolidations.map((msg, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.25 }}>
                <ListItemText primary={`• ${msg}`} />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Next Steps */}
      <Alert severity="info" sx={{ mb: 4, textAlign: 'left' }}>
        <AlertTitle>📋 Következő lépések</AlertTitle>
        <List dense>
          <ListItem sx={{ px: 0, py: 1 }}>
            <ListItemIcon>
              <Avatar sx={{ width: 24, height: 24, bgcolor: 'info.main', fontSize: '0.75rem' }}>
                1
              </Avatar>
            </ListItemIcon>
            <ListItemText
              primary="Utalások létrehozása"
              secondary="Használja a sablont azonnali utalás generáláshoz"
            />
          </ListItem>
          <ListItem sx={{ px: 0, py: 1 }}>
            <ListItemIcon>
              <Avatar sx={{ width: 24, height: 24, bgcolor: 'info.main', fontSize: '0.75rem' }}>
                2
              </Avatar>
            </ListItemIcon>
            <ListItemText
              primary="Összegek módosítása"
              secondary="Szükség szerint módosítsa az összegeket és dátumokat"
            />
          </ListItem>
          <ListItem sx={{ px: 0, py: 1 }}>
            <ListItemIcon>
              <Avatar sx={{ width: 24, height: 24, bgcolor: 'info.main', fontSize: '0.75rem' }}>
                3
              </Avatar>
            </ListItemIcon>
            <ListItemText
              primary="Generálás"
              secondary="Töltse le az XML fájlt a banki importhoz"
            />
          </ListItem>
        </List>
      </Alert>

      {/* Action Buttons */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        justifyContent="center"
        sx={{ mb: 4 }}
      >
        <Button
          onClick={onCreateTransfers}
          variant="contained"
          color="success"
          size="large"
          startIcon={<AddIcon />}
        >
          Utalások Létrehozása
        </Button>
      </Stack>

      {/* Tips */}
      <Alert severity="success" sx={{ textAlign: 'left' }}>
        <AlertTitle>💡 Hasznos tippek</AlertTitle>
        <List dense>
          <ListItem sx={{ px: 0, py: 0.25 }}>
            <ListItemText primary="• A sablon újra felhasználható minden hónapban - csak töltse fel az új PDF-eket" />
          </ListItem>
          <ListItem sx={{ px: 0, py: 0.25 }}>
            <ListItemText primary="• A kedvezményezettek automatikusan frissülnek, de az összegek mindig ellenőrizendők" />
          </ListItem>
          <ListItem sx={{ px: 0, py: 0.25 }}>
            <ListItemText primary="• Az XML fájl közvetlenül importálható a legtöbb banki rendszerbe" />
          </ListItem>
          <ListItem sx={{ px: 0, py: 0.25 }}>
            <ListItemText primary="• A sablon később szerkeszthető és kiegészíthető további kedvezményezettekkel" />
          </ListItem>
        </List>
      </Alert>
    </Box>
  );
};
