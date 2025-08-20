import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  Stack,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  IconButton,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Close as CloseIcon,
  Search as SearchIcon,
  Person as PersonIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { useBeneficiaries } from '../../hooks/api';
import { Beneficiary } from '../../types/api';

interface AddTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (transferData: {
    beneficiary: number;
    beneficiary_data: Beneficiary;
    amount: string;
    execution_date: string;
    remittance_info: string;
    currency: 'HUF' | 'EUR' | 'USD';
  }) => void;
}

interface FormData {
  amount: string;
  execution_date: string;
  remittance_info: string;
  currency: 'HUF' | 'EUR' | 'USD';
}

const AddTransferModal: React.FC<AddTransferModalProps> = ({
  isOpen,
  onClose,
  onAdd,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBeneficiary, setSelectedBeneficiary] = useState<Beneficiary | null>(null);
  const [showBeneficiaryPicker, setShowBeneficiaryPicker] = useState(true);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      amount: '',
      execution_date: new Date().toISOString().split('T')[0],
      remittance_info: '',
      currency: 'HUF',
    },
  });

  const { data: beneficiariesData } = useBeneficiaries({
    search: searchTerm,
    is_active: true,
  });

  const availableBeneficiaries = beneficiariesData?.results || [];

  // Auto-fill remittance info when beneficiary is selected
  useEffect(() => {
    if (selectedBeneficiary && selectedBeneficiary.remittance_information) {
      setValue('remittance_info', selectedBeneficiary.remittance_information);
    }
  }, [selectedBeneficiary, setValue]);

  const handleFormSubmit = (data: FormData) => {
    if (!selectedBeneficiary) return;

    onAdd({
      beneficiary: selectedBeneficiary.id,
      beneficiary_data: selectedBeneficiary,
      amount: data.amount,
      execution_date: data.execution_date,
      remittance_info: data.remittance_info,
      currency: data.currency,
    });

    handleClose();
  };

  const handleClose = () => {
    reset();
    setSelectedBeneficiary(null);
    setSearchTerm('');
    setShowBeneficiaryPicker(true);
    onClose();
  };

  const handleBeneficiarySelect = (beneficiary: Beneficiary) => {
    setSelectedBeneficiary(beneficiary);
    setShowBeneficiaryPicker(false);
    setSearchTerm('');
  };

  const handleChangeBeneficiary = () => {
    setSelectedBeneficiary(null);
    setShowBeneficiaryPicker(true);
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            Új átutalás hozzáadása
          </Typography>
          <IconButton onClick={handleClose} edge="end">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent dividers>

        {showBeneficiaryPicker ? (
          /* Beneficiary Selection */
          <Stack spacing={2}>
            <Typography variant="subtitle1" fontWeight={500}>
              Kedvezményezett kiválasztása
            </Typography>
            <TextField
              fullWidth
              placeholder="Keresés név vagy számlaszám alapján..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />

            <Box sx={{ maxHeight: 320, overflowY: 'auto' }}>
              {availableBeneficiaries.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <PersonIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Nincsenek találatok
                  </Typography>
                </Box>
              ) : (
                <List disablePadding>
                  {availableBeneficiaries.map((beneficiary) => (
                    <ListItem key={beneficiary.id} disablePadding>
                      <ListItemButton
                        onClick={() => handleBeneficiarySelect(beneficiary)}
                        sx={{ 
                          border: 1, 
                          borderColor: 'divider', 
                          borderRadius: 1, 
                          mb: 1,
                          '&:hover': {
                            bgcolor: 'action.hover'
                          }
                        }}
                      >
                        <ListItemText
                          primary={
                            <Typography variant="body2" fontWeight={500}>
                              {beneficiary.name}
                            </Typography>
                          }
                          secondary={
                            <Box component="span">
                              <Typography variant="caption" component="span" sx={{ fontFamily: 'monospace', display: 'block' }}>
                                {beneficiary.account_number}
                              </Typography>
                              {beneficiary.description && (
                                <Typography variant="caption" component="span" color="text.secondary" sx={{ display: 'block' }}>
                                  {beneficiary.description}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </Stack>
        ) : (
          /* Transfer Form */
          <form onSubmit={handleSubmit(handleFormSubmit)}>
            <Stack spacing={3}>
              {/* Selected Beneficiary */}
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="body2" fontWeight={500}>
                      {selectedBeneficiary?.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                      {selectedBeneficiary?.account_number}
                    </Typography>
                    {selectedBeneficiary?.description && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {selectedBeneficiary.description}
                      </Typography>
                    )}
                  </Box>
                  <Button
                    size="small"
                    onClick={handleChangeBeneficiary}
                    startIcon={<EditIcon />}
                  >
                    Változtatás
                  </Button>
                </Stack>
              </Paper>

              {/* Amount */}
              <Stack direction="row" spacing={1} alignItems="flex-start">
                <TextField
                  fullWidth
                  label="Összeg *"
                  type="number"
                  {...register('amount', { 
                    required: 'Az összeg megadása kötelező',
                    min: { value: 1, message: 'Az összegnek pozitívnak kell lennie' }
                  })}
                  error={!!errors.amount}
                  helperText={errors.amount?.message}
                  InputProps={{ 
                    inputProps: { step: 1, min: 0 }
                  }}
                  placeholder="0"
                />
                <FormControl sx={{ minWidth: 80 }}>
                  <InputLabel>Pénznem</InputLabel>
                  <Select
                    {...register('currency')}
                    label="Pénznem"
                    defaultValue="HUF"
                  >
                    <MenuItem value="HUF">HUF</MenuItem>
                    <MenuItem value="EUR">EUR</MenuItem>
                    <MenuItem value="USD">USD</MenuItem>
                  </Select>
                </FormControl>
              </Stack>

              {/* Execution Date */}
              <TextField
                fullWidth
                label="Teljesítés dátuma *"
                type="date"
                {...register('execution_date', { required: 'A teljesítés dátuma kötelező' })}
                error={!!errors.execution_date}
                helperText={errors.execution_date?.message}
                InputLabelProps={{ shrink: true }}
              />

              {/* Remittance Info */}
              <TextField
                fullWidth
                label="Közlemény"
                {...register('remittance_info')}
                placeholder="Fizetési közlemény..."
                multiline
                rows={2}
              />
            </Stack>
          </form>
        )}
      </DialogContent>

      {!showBeneficiaryPicker && (
        <DialogActions>
          <Button onClick={handleClose}>
            Mégse
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSubmit(handleFormSubmit)}
            disabled={!selectedBeneficiary}
          >
            Hozzáadás
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
};

export default AddTransferModal;