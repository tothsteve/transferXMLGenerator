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
  Typography,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { Beneficiary } from '../../types/api';
import {
  validateAndFormatHungarianAccountNumber,
  formatAccountNumberOnInput,
} from '../../utils/bankAccountValidation';
import {
  validateBeneficiaryName,
  validateRemittanceInfo,
  normalizeWhitespace,
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

// Type guard for backend validation errors
const hasValidationErrors = (
  error: unknown
): error is { response: { status: number; data: Record<string, string | string[]> } } => {
  if (typeof error !== 'object' || error === null) return false;
  if (!('response' in error)) return false;

  const errorWithResponse = error as { response: unknown };
  if (typeof errorWithResponse.response !== 'object' || errorWithResponse.response === null)
    return false;
  if (!('status' in errorWithResponse.response) || !('data' in errorWithResponse.response))
    return false;

  const response = errorWithResponse.response as { status: unknown; data: unknown };
  return typeof response.status === 'number' && typeof response.data === 'object';
};

const BeneficiaryForm: React.FC<BeneficiaryFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  beneficiary,
  isLoading = false,
}) => {
  const [accountNumberValue, setAccountNumberValue] = useState('');

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
      name: '',
      account_number: '',
      vat_number: '',
      tax_number: '',
      description: '',
      remittance_information: '',
      is_frequent: false,
      is_active: true,
    },
  });

  // Reset form when beneficiary prop changes or dialog opens
  useEffect(() => {
    reset({
      name: beneficiary?.name ?? '',
      account_number: beneficiary?.account_number ?? '',
      vat_number: beneficiary?.vat_number ?? '',
      tax_number: beneficiary?.tax_number ?? '',
      description: beneficiary?.description ?? '',
      remittance_information: beneficiary?.remittance_information ?? '',
      is_frequent: beneficiary?.is_frequent ?? false,
      is_active: beneficiary?.is_active ?? true,
    });
    setAccountNumberValue(beneficiary?.account_number ?? '');
  }, [beneficiary, reset]);

  // Helper: Check if at least one identifier is provided
  const validateIdentifiers = (data: FormData): boolean => {
    const isEmpty = (val: string | undefined): boolean => val === null || val === undefined || val === '';
    if (isEmpty(data.account_number) && isEmpty(data.vat_number) && isEmpty(data.tax_number)) {
      setError('account_number', {
        type: 'manual',
        message: 'Meg kell adni a számlaszámot, adóazonosító jelet vagy céges adószámot',
      });
      return false;
    }
    return true;
  };

  // Helper: Validate and format account number
  const validateAccountNumber = (accountNumber: string | undefined): string | undefined => {
    if (accountNumber === null || accountNumber === undefined || accountNumber === '') {
      return undefined;
    }
    const validation = validateAndFormatHungarianAccountNumber(accountNumber);
    if (!validation.isValid) {
      const errorMsg = validation.error !== null && validation.error !== undefined && validation.error !== ''
        ? validation.error
        : 'Érvénytelen számlaszám';
      setError('account_number', { type: 'manual', message: errorMsg });
      return null as unknown as undefined;
    }
    return validation.formatted;
  };

  // Helper: Validate VAT number
  const validateVatNumber = (vatNumber: string | undefined): boolean => {
    if (vatNumber === null || vatNumber === undefined || vatNumber === '') return true;
    const cleanVat = vatNumber.replace(/[\s-]/g, '');
    if (!/^\d{10}$/.test(cleanVat)) {
      setError('vat_number', {
        type: 'manual',
        message: 'Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8450782546)',
      });
      return false;
    }
    return true;
  };

  // Helper: Validate tax number
  const validateTaxNumber = (taxNumber: string | undefined): boolean => {
    if (taxNumber === null || taxNumber === undefined || taxNumber === '') return true;
    const cleanTax = taxNumber.replace(/[\s-]/g, '');
    if (!/^\d{8}$/.test(cleanTax)) {
      setError('tax_number', {
        type: 'manual',
        message: 'Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)',
      });
      return false;
    }
    return true;
  };

  // Helper: Validate name field
  const validateName = (name: string): boolean => {
    const nameValidation = validateBeneficiaryName(name);
    if (!nameValidation.isValid) {
      const errorMsg = nameValidation.error !== null && nameValidation.error !== undefined && nameValidation.error !== ''
        ? nameValidation.error
        : 'Érvénytelen név';
      setError('name', { type: 'manual', message: errorMsg });
      return false;
    }
    return true;
  };

  // Helper: Validate remittance info
  const validateRemittance = (remittanceInfo: string | undefined): boolean => {
    if (remittanceInfo === null || remittanceInfo === undefined || remittanceInfo === '') return true;
    const remittanceValidation = validateRemittanceInfo(remittanceInfo);
    if (!remittanceValidation.isValid) {
      const errorMsg = remittanceValidation.error !== null && remittanceValidation.error !== undefined && remittanceValidation.error !== ''
        ? remittanceValidation.error
        : 'Érvénytelen közlemény';
      setError('remittance_information', { type: 'manual', message: errorMsg });
      return false;
    }
    return true;
  };

  // Helper: Handle backend errors
  const handleBackendErrors = (error: unknown): void => {
    if (!hasValidationErrors(error) || error.response.status !== 400) return;

    const backendErrors = error.response.data;
    Object.keys(backendErrors).forEach((field) => {
      if (['account_number', 'name', 'description', 'remittance_information'].includes(field)) {
        const fieldErrors = backendErrors[field];
        const errorMessage = Array.isArray(fieldErrors)
          ? (fieldErrors[0] !== null && fieldErrors[0] !== undefined && fieldErrors[0] !== '' ? fieldErrors[0] : 'Validation error')
          : (fieldErrors !== null && fieldErrors !== undefined && fieldErrors !== '' ? fieldErrors : 'Validation error');
        setError(field as keyof FormData, { type: 'manual', message: errorMessage });
      }
    });
  };

  const handleFormSubmit = async (data: FormData): Promise<void> => {
    // Run all validations
    if (!validateIdentifiers(data)) return;

    const formattedAccountNumber = validateAccountNumber(data.account_number);
    if (formattedAccountNumber === null) return;

    if (!validateVatNumber(data.vat_number)) return;
    if (!validateTaxNumber(data.tax_number)) return;
    if (!validateName(data.name)) return;
    if (!validateRemittance(data.remittance_information)) return;

    // Build submit data
    const submitData: Omit<Beneficiary, 'id'> = {
      ...data,
      name: normalizeWhitespace(data.name),
      ...(formattedAccountNumber !== null && formattedAccountNumber !== undefined && formattedAccountNumber !== '' && { account_number: formattedAccountNumber }),
      ...(data.vat_number !== null && data.vat_number !== undefined && data.vat_number !== '' && { vat_number: data.vat_number.replace(/[\s-]/g, '') }),
      ...(data.tax_number !== null && data.tax_number !== undefined && data.tax_number !== '' && { tax_number: data.tax_number.replace(/[\s-]/g, '') }),
      description: data.description !== null && data.description !== undefined && data.description !== '' ? data.description : '',
      remittance_information: data.remittance_information !== null && data.remittance_information !== undefined && data.remittance_information !== ''
        ? normalizeWhitespace(data.remittance_information)
        : '',
    };

    try {
      await onSubmit(submitData);
      reset();
      setAccountNumberValue('');
    } catch (error: unknown) {
      handleBackendErrors(error);
    }
  };

  const handleClose = (): void => {
    reset();
    setAccountNumberValue('');
    onClose();
  };

  const handleAccountNumberChange = (value: string): string => {
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
            {beneficiary !== null && beneficiary !== undefined ? 'Kedvezményezett szerkesztése' : 'Új kedvezményezett'}
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
                },
              })}
              error={!!errors.name}
              helperText={
                errors.name?.message !== null && errors.name?.message !== undefined && errors.name?.message !== '' ? errors.name.message :
                'Csak angol betűk, magyar ékezetes betűk, számok és megadott írásjelek használhatók'
              }
            />

            <Controller
              name="account_number"
              control={control}
              rules={{
                validate: (value) => {
                  if (value === null || value === undefined || value === '') return true; // Optional field now
                  const validation = validateAndFormatHungarianAccountNumber(value);
                  return validation.isValid || (validation.error !== null && validation.error !== undefined && validation.error !== '' ? validation.error : 'Érvénytelen számlaszám');
                },
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
                    errors.account_number?.message !== null && errors.account_number?.message !== undefined && errors.account_number?.message !== '' ? errors.account_number.message :
                    'Magyar számlaszám formátum: 16 vagy 24 számjegy, automatikus formázás'
                  }
                  InputProps={{
                    sx: { fontFamily: 'monospace', letterSpacing: '0.5px' },
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
                  if (value === null || value === undefined || value === '') return true; // Optional field
                  const cleanVat = value.replace(/[\s-]/g, '');
                  if (!/^\d{10}$/.test(cleanVat)) {
                    return 'Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8440961790)';
                  }
                  return true;
                },
              })}
              error={!!errors.vat_number}
              helperText={
                errors.vat_number?.message !== null && errors.vat_number?.message !== undefined && errors.vat_number?.message !== '' ? errors.vat_number.message :
                'Magyar személyi adóazonosító jel 10 számjegyből áll (alkalmazottak azonosítására)'
              }
              InputProps={{
                sx: { fontFamily: 'monospace', letterSpacing: '0.5px' },
              }}
            />

            <TextField
              label="Céges adószám"
              fullWidth
              placeholder="12345678"
              {...register('tax_number', {
                validate: (value) => {
                  if (value === null || value === undefined || value === '') return true; // Optional field
                  const cleanTax = value.replace(/[\s-]/g, '');
                  if (!/^\d{8}$/.test(cleanTax)) {
                    return 'Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)';
                  }
                  return true;
                },
              })}
              error={!!errors.tax_number}
              helperText={
                errors.tax_number?.message !== null && errors.tax_number?.message !== undefined && errors.tax_number?.message !== '' ? errors.tax_number.message :
                'Magyar céges adószám első 8 számjegye (cégek és szervezetek azonosítására)'
              }
              InputProps={{
                sx: { fontFamily: 'monospace', letterSpacing: '0.5px' },
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
                  if (value === null || value === undefined || value === '') return true;
                  const validation = validateRemittanceInfo(value);
                  return validation.isValid || (validation.error !== null && validation.error !== undefined && validation.error !== '' ? validation.error : true);
                },
              })}
              error={!!errors.remittance_information}
              helperText={
                errors.remittance_information?.message !== null && errors.remittance_information?.message !== undefined && errors.remittance_information?.message !== '' ? errors.remittance_information.message :
                'Maximum 140 karakter. Csak angol betűk, magyar ékezetes betűk, számok és megadott írásjelek használhatók'
              }
            />

            <Stack spacing={1}>
              <Controller
                name="is_active"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Checkbox checked={!!field.value} onChange={field.onChange} />}
                    label="Aktív kedvezményezett"
                  />
                )}
              />
              <Controller
                name="is_frequent"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Checkbox checked={!!field.value} onChange={field.onChange} />}
                    label="Gyakori kedvezményezett"
                  />
                )}
              />
            </Stack>
          </Stack>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>Mégse</Button>
          <Button type="submit" variant="contained" disabled={isLoading}>
            {isLoading ? 'Mentés...' : (beneficiary !== null && beneficiary !== undefined ? 'Frissítés' : 'Létrehozás')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default BeneficiaryForm;
