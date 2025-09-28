import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
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
import { 
  validateAndFormatHungarianAccountNumber, 
  formatAccountNumberOnInput 
} from '../../utils/bankAccountValidation';
import { 
  validateBeneficiaryName,
  validateRemittanceInfo,
  normalizeWhitespace
} from '../../utils/stringValidation';

interface BeneficiaryFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Omit<Beneficiary, 'id'>) => Promise<void>;
  beneficiary?: Beneficiary | null;
  isLoading?: boolean;
}

interface FormData {
  name: string;
  account_number?: string;
  vat_number?: string;
  tax_number?: string;
  description?: string;
  remittance_information?: string;
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
  const [accountNumberValue, setAccountNumberValue] = useState(beneficiary?.account_number || '');

  // Update account number value when beneficiary prop changes
  useEffect(() => {
    setAccountNumberValue(beneficiary?.account_number || '');
  }, [beneficiary]);

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
    setError,
    clearErrors,
  } = useForm<FormData>({
    defaultValues: {
      name: beneficiary?.name || '',
      account_number: beneficiary?.account_number || '',
      vat_number: beneficiary?.vat_number || '',
      tax_number: beneficiary?.tax_number || '',
      description: beneficiary?.description || '',
      remittance_information: beneficiary?.remittance_information || '',
      is_frequent: beneficiary?.is_frequent || false,
      is_active: beneficiary?.is_active ?? true,
    },
  });

  const handleFormSubmit = async (data: FormData) => {
    // Validate that at least one identifier is provided
    if (!data.account_number && !data.vat_number && !data.tax_number) {
      setError('account_number', {
        type: 'manual',
        message: 'Meg kell adni a számlaszámot, adóazonosító jelet vagy céges adószámot'
      });
      return;
    }

    // Validate account number if provided
    let formattedAccountNumber: string | undefined;
    if (data.account_number) {
      const validation = validateAndFormatHungarianAccountNumber(data.account_number);
      if (!validation.isValid) {
        setError('account_number', { 
          type: 'manual', 
          message: validation.error || 'Érvénytelen számlaszám' 
        });
        return;
      }
      formattedAccountNumber = validation.formatted;
    }

    // Validate VAT number if provided (10 digits)
    if (data.vat_number) {
      const cleanVat = data.vat_number.replace(/[\s-]/g, '');
      if (!/^\d{10}$/.test(cleanVat)) {
        setError('vat_number', {
          type: 'manual',
          message: 'Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8450782546)'
        });
        return;
      }
    }

    // Validate tax number if provided (8 digits)
    if (data.tax_number) {
      const cleanTax = data.tax_number.replace(/[\s-]/g, '');
      if (!/^\d{8}$/.test(cleanTax)) {
        setError('tax_number', {
          type: 'manual',
          message: 'Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)'
        });
        return;
      }
    }

    // Validate and normalize name
    const nameValidation = validateBeneficiaryName(data.name);
    if (!nameValidation.isValid) {
      setError('name', { 
        type: 'manual', 
        message: nameValidation.error || 'Érvénytelen név' 
      });
      return;
    }

    // Validate and normalize remittance information
    if (data.remittance_information) {
      const remittanceValidation = validateRemittanceInfo(data.remittance_information);
      if (!remittanceValidation.isValid) {
        setError('remittance_information', { 
          type: 'manual', 
          message: remittanceValidation.error || 'Érvénytelen közlemény' 
        });
        return;
      }
    }

    const submitData: Omit<Beneficiary, 'id'> = {
      ...data,
      name: normalizeWhitespace(data.name),
      account_number: formattedAccountNumber,
      vat_number: data.vat_number ? data.vat_number.replace(/[\s-]/g, '') : undefined,
      tax_number: data.tax_number ? data.tax_number.replace(/[\s-]/g, '') : undefined,
      description: data.description || '',
      remittance_information: data.remittance_information ? normalizeWhitespace(data.remittance_information) : ''
    };

    try {
      await onSubmit(submitData);
      reset();
      setAccountNumberValue('');
    } catch (error: any) {
      // Handle backend validation errors
      if (error.response?.status === 400 && error.response?.data) {
        const backendErrors = error.response.data;
        
        // Set field-specific errors from backend
        Object.keys(backendErrors).forEach(field => {
          if (field === 'account_number' || field === 'name' || field === 'description' || field === 'remittance_information') {
            const errorMessage = Array.isArray(backendErrors[field]) 
              ? backendErrors[field][0] 
              : backendErrors[field];
            setError(field as keyof FormData, {
              type: 'manual',
              message: errorMessage
            });
          }
        });
      }
    }
  };

  const handleClose = () => {
    reset();
    setAccountNumberValue('');
    onClose();
  };

  const handleAccountNumberChange = (value: string) => {
    // Format the input in real-time
    const formatted = formatAccountNumberOnInput(value);
    setAccountNumberValue(formatted);
    
    // Clear any existing errors when user starts typing
    if (errors.account_number) {
      clearErrors('account_number');
    }
    
    return formatted;
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
              {...register('name', { 
                required: 'A név megadása kötelező',
                validate: (value) => {
                  const validation = validateBeneficiaryName(value);
                  return validation.isValid || validation.error;
                }
              })}
              error={!!errors.name}
              helperText={errors.name?.message || 'Csak angol betűk, magyar ékezetes betűk, számok és megadott írásjelek használhatók'}
            />

            <Controller
              name="account_number"
              control={control}
              rules={{ 
                validate: (value) => {
                  if (!value) return true; // Optional field now
                  const validation = validateAndFormatHungarianAccountNumber(value);
                  return validation.isValid || validation.error || 'Érvénytelen számlaszám';
                }
              }}
              render={({ field }) => (
                <TextField
                  label="Számlaszám"
                  fullWidth
                  placeholder="12345678-12345678 vagy 12345678-12345678-12345678"
                  value={accountNumberValue}
                  onChange={(e) => {
                    const formatted = handleAccountNumberChange(e.target.value);
                    field.onChange(formatted);
                  }}
                  onBlur={field.onBlur}
                  error={!!errors.account_number}
                  helperText={
                    errors.account_number?.message || 
                    'Magyar számlaszám formátum: 16 vagy 24 számjegy, automatikus formázás'
                  }
                  InputProps={{
                    sx: { fontFamily: 'monospace', letterSpacing: '0.5px' }
                  }}
                />
              )}
            />

            <TextField
              label="Adóazonosító jel"
              fullWidth
              placeholder="8440961790"
              {...register('vat_number', {
                validate: (value) => {
                  if (!value) return true; // Optional field
                  const cleanVat = value.replace(/[\s-]/g, '');
                  if (!/^\d{10}$/.test(cleanVat)) {
                    return 'Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8440961790)';
                  }
                  return true;
                }
              })}
              error={!!errors.vat_number}
              helperText={
                errors.vat_number?.message || 
                'Magyar személyi adóazonosító jel 10 számjegyből áll (alkalmazottak azonosítására)'
              }
              InputProps={{
                sx: { fontFamily: 'monospace', letterSpacing: '0.5px' }
              }}
            />

            <TextField
              label="Céges adószám"
              fullWidth
              placeholder="12345678"
              {...register('tax_number', {
                validate: (value) => {
                  if (!value) return true; // Optional field
                  const cleanTax = value.replace(/[\s-]/g, '');
                  if (!/^\d{8}$/.test(cleanTax)) {
                    return 'Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)';
                  }
                  return true;
                }
              })}
              error={!!errors.tax_number}
              helperText={
                errors.tax_number?.message ||
                'Magyar céges adószám első 8 számjegye (cégek és szervezetek azonosítására)'
              }
              InputProps={{
                sx: { fontFamily: 'monospace', letterSpacing: '0.5px' }
              }}
            />

            <TextField
              label="Leírás"
              fullWidth
              placeholder="Bank neve, szervezet adatai, egyéb információk..."
              {...register('description')}
            />

            <TextField
              label="Közlemény"
              fullWidth
              multiline
              rows={3}
              placeholder="Alapértelmezett közlemény az utalásokhoz..."
              {...register('remittance_information', {
                validate: (value) => {
                  if (!value) return true;
                  const validation = validateRemittanceInfo(value);
                  return validation.isValid || validation.error;
                }
              })}
              error={!!errors.remittance_information}
              helperText={errors.remittance_information?.message || 'Maximum 140 karakter. Csak angol betűk, magyar ékezetes betűk, számok és megadott írásjelek használhatók'}
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