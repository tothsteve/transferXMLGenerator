import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  Paper,
  Stack,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
  IconButton
} from '@mui/material';
import {
  Close as CloseIcon,
  CalendarToday as CalendarIcon,
  Group as GroupIcon,
  Payments as PaymentsIcon,
  Description as DocumentIcon
} from '@mui/icons-material';
import { TransferTemplate } from '../../types/api';

interface TemplateViewProps {
  isOpen: boolean;
  onClose: () => void;
  template: TransferTemplate | null;
}

// This would be populated from the template details API
interface TemplateBeneficiaryDetail {
  id: number;
  beneficiary_name: string;
  account_number: string | null | undefined;
  vat_number: string | null | undefined;
  description: string;
  default_amount: string;
  default_remittance_info: string;
}

const TemplateView: React.FC<TemplateViewProps> = ({
  isOpen,
  onClose,
  template,
}) => {
  if (!template) return null;

  // Use real template data from the API
  const templateBeneficiaries: TemplateBeneficiaryDetail[] = template.template_beneficiaries?.map(tb => ({
    id: tb.id,
    beneficiary_name: tb.beneficiary.name,
    account_number: tb.beneficiary.account_number,
    vat_number: tb.beneficiary.vat_number,
    description: tb.beneficiary.description || '',
    default_amount: tb.default_amount?.toString() || '0',
    default_remittance_info: tb.default_remittance || '',
  })) || [];

  const totalAmount = templateBeneficiaries.reduce((sum, b) => 
    sum + (parseFloat(b.default_amount) || 0), 0
  );

  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            Sablon részletei
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3}>
          {/* Template Info */}
          <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <Typography variant="h5" gutterBottom>
                  {template.name}
                </Typography>
                {template.description && (
                  <Typography variant="body2" color="text.secondary">
                    {template.description}
                  </Typography>
                )}
              </Box>
              
              <Box>
                <Stack spacing={2}>
                  <Chip
                    label={template.is_active ? 'Aktív' : 'Inaktív'}
                    color={template.is_active ? 'success' : 'default'}
                    variant="outlined"
                    size="small"
                    sx={{ width: 'fit-content' }}
                  />
                  
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <GroupIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {template.beneficiary_count} kedvezményezett
                    </Typography>
                  </Stack>
                  
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <PaymentsIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {totalAmount.toLocaleString('hu-HU')} HUF összesen
                    </Typography>
                  </Stack>
                  
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <CalendarIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      Létrehozva: {new Date(template.created_at).toLocaleDateString('hu-HU')}
                    </Typography>
                  </Stack>
                  
                  {template.updated_at !== template.created_at && (
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <CalendarIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        Módosítva: {new Date(template.updated_at).toLocaleDateString('hu-HU')}
                      </Typography>
                    </Stack>
                  )}
                </Stack>
              </Box>
            </Box>
          </Paper>

          {/* Beneficiaries */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Kedvezményezettek
            </Typography>
            
            {templateBeneficiaries.length === 0 ? (
              <Paper 
                sx={{ 
                  p: 4, 
                  textAlign: 'center', 
                  border: 2, 
                  borderStyle: 'dashed', 
                  borderColor: 'divider' 
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Nincsenek kedvezményezettek hozzárendelve ehhez a sablonhoz.
                </Typography>
              </Paper>
            ) : (
              <Paper elevation={1}>
                <List>
                  {templateBeneficiaries.map((beneficiary, index) => (
                    <React.Fragment key={beneficiary.id}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'primary.100', color: 'primary.800' }}>
                            <Typography variant="body2" fontWeight={500}>
                              {index + 1}
                            </Typography>
                          </Avatar>
                        </ListItemAvatar>
                        
                        <ListItemText
                          primary={
                            <Typography variant="body1" fontWeight={500}>
                              {beneficiary.beneficiary_name}
                            </Typography>
                          }
                          secondaryTypographyProps={{ component: 'div' }}
                          secondary={
                            <Stack spacing={0.5}>
                              {beneficiary.account_number && (
                                <Typography variant="body2" fontFamily="monospace">
                                  {beneficiary.account_number}
                                </Typography>
                              )}
                              {beneficiary.vat_number && (
                                <Typography variant="body2" sx={{ color: 'info.main', fontWeight: 500 }}>
                                  Adóazonosító: {beneficiary.vat_number}
                                </Typography>
                              )}
                              {!beneficiary.account_number && !beneficiary.vat_number && (
                                <Typography variant="body2" color="text.secondary">
                                  -
                                </Typography>
                              )}
                              {beneficiary.description && (
                                <Typography variant="body2" color="text.secondary">
                                  {beneficiary.description}
                                </Typography>
                              )}
                            </Stack>
                          }
                        />
                        
                        <Box sx={{ textAlign: 'right' }}>
                          <Typography variant="body1" fontWeight={500}>
                            {parseFloat(beneficiary.default_amount).toLocaleString('hu-HU')} HUF
                          </Typography>
                          {beneficiary.default_remittance_info && (
                            <Stack direction="row" alignItems="center" spacing={0.5} justifyContent="flex-end">
                              <DocumentIcon fontSize="small" color="action" />
                              <Typography variant="body2" color="text.secondary">
                                {beneficiary.default_remittance_info}
                              </Typography>
                            </Stack>
                          )}
                        </Box>
                      </ListItem>
                      {index < templateBeneficiaries.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
                
                {/* Summary */}
                <Box sx={{ bgcolor: 'grey.50', p: 2 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body1" fontWeight={500}>
                      Összesen:
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {totalAmount.toLocaleString('hu-HU')} HUF
                    </Typography>
                  </Stack>
                </Box>
              </Paper>
            )}
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Bezárás
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TemplateView;