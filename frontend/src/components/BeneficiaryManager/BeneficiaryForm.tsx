import React from 'react';
import { useForm } from 'react-hook-form';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  Stack,
  IconButton,
  Typography
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { Beneficiary } from '../../types/api';

interface BeneficiaryFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Omit<Beneficiary, 'id'>) => void;
  beneficiary?: Beneficiary | null;
  isLoading?: boolean;
}

interface FormData {
  name: string;
  account_number: string;
  bank_name?: string;
  notes?: string;
  is_frequent: boolean;
  is_active: boolean;
}

const BeneficiaryForm: React.FC<BeneficiaryFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  beneficiary,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      name: beneficiary?.name || '',
      account_number: beneficiary?.account_number || '',
      bank_name: beneficiary?.bank_name || '',
      notes: beneficiary?.notes || '',
      is_frequent: beneficiary?.is_frequent || false,
      is_active: beneficiary?.is_active ?? true,
    },
  });

  const handleFormSubmit = (data: FormData) => {
    const submitData: Omit<Beneficiary, 'id'> = {
      ...data,
      bank_name: data.bank_name || '',
      notes: data.notes || ''
    };
    onSubmit(submitData);
    reset();
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {beneficiary ? 'Kedvezményezett szerkesztése' : 'Új kedvezményezett'}
          </Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>

      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent>
          <Stack spacing={3}>
            <TextField
              label="Név *"
              fullWidth
              {...register('name', { required: 'A név megadása kötelező' })}
              error={!!errors.name}
              helperText={errors.name?.message}
            />

            <TextField
              label="Számlaszám *"
              fullWidth
              placeholder="12345678-12345678"
              {...register('account_number', { 
                required: 'A számlaszám megadása kötelező',
                pattern: {
                  value: /^[\d-]+$/,
                  message: 'Érvénytelen számlaszám formátum'
                }
              })}
              error={!!errors.account_number}
              helperText={errors.account_number?.message}
              InputProps={{
                sx: { fontFamily: 'monospace' }
              }}
            />

            <TextField
              label="Bank neve"
              fullWidth
              {...register('bank_name')}
            />

            <TextField
              label="Megjegyzés"
              fullWidth
              multiline
              rows={3}
              placeholder="Megjegyzés a kedvezményezettel kapcsolatban..."
              {...register('notes')}
            />

            <Stack spacing={1}>
              <FormControlLabel
                control={<Checkbox {...register('is_active')} />}
                label="Aktív kedvezményezett"
              />
              <FormControlLabel
                control={<Checkbox {...register('is_frequent')} />}
                label="Gyakori kedvezményezett"
              />
            </Stack>
          </Stack>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>
            Mégse
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={isLoading}
          >
            {isLoading ? 'Mentés...' : (beneficiary ? 'Frissítés' : 'Létrehozás')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default BeneficiaryForm;