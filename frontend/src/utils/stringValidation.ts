/**
 * Validation utilities for XML/CSV export string fields
 * 
 * Allowed characters for XML/CSV export:
 * - English alphabet (a-z, A-Z)
 * - Hungarian accented characters: áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý
 * - Numbers (0-9)
 * - Special characters: space, tab, newline, -.,!?_:()+@;=<>~%*$#&/§
 */

// Define allowed characters for XML/CSV export
const ALLOWED_ENGLISH_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
const ALLOWED_HUNGARIAN_ACCENTS = 'áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý';
const ALLOWED_NUMBERS = '0123456789';
const ALLOWED_SPECIAL_CHARS = ' \t\n-.,!?_:()+@;=<>~%*$#&/§';

// Combined allowed character set
const ALLOWED_CHARS = ALLOWED_ENGLISH_LETTERS + ALLOWED_HUNGARIAN_ACCENTS + ALLOWED_NUMBERS + ALLOWED_SPECIAL_CHARS;

// Create regex pattern for allowed characters
const ALLOWED_CHARS_REGEX = new RegExp(`^[${ALLOWED_CHARS.replace(/[[\]\\-]/g, '\\$&')}]*$`);

/**
 * Validates if a string contains only allowed characters for XML/CSV export
 * @param value - String to validate
 * @returns Object with isValid boolean and error message if invalid
 */
export const validateExportString = (value: string): { isValid: boolean; error?: string } => {
  if (!value) {
    return { isValid: true }; // Empty strings are valid
  }

  if (!ALLOWED_CHARS_REGEX.test(value)) {
    return {
      isValid: false,
      error: 'Csak angol betűk, magyar ékezetes betűk (áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý), számok és a következő írásjelek engedélyezettek: -.,!?_:()+@;=<>~%*$#&/§'
    };
  }

  return { isValid: true };
};

/**
 * Sanitizes a string by removing invalid characters for XML/CSV export
 * @param value - String to sanitize
 * @returns Sanitized string with only allowed characters
 */
export const sanitizeExportString = (value: string): string => {
  if (!value) return '';
  
  return value
    .split('')
    .filter(char => ALLOWED_CHARS.includes(char))
    .join('');
};

/**
 * Removes extra whitespace from a string (trims and removes multiple spaces/tabs/newlines)
 * @param value - String to clean
 * @returns String with normalized whitespace
 */
export const normalizeWhitespace = (value: string): string => {
  if (!value) return '';
  
  return value
    .trim() // Remove leading/trailing whitespace
    .replace(/\s+/g, ' '); // Replace multiple whitespace with single space
};

/**
 * Validates and sanitizes a string for XML/CSV export
 * Combines validation, sanitization, and whitespace normalization
 * @param value - String to process
 * @returns Object with processed string and validation result
 */
export const validateAndSanitizeExportString = (value: string): { 
  value: string; 
  isValid: boolean; 
  error?: string;
  wasModified: boolean;
} => {
  if (!value) {
    return { value: '', isValid: true, wasModified: false };
  }

  const originalValue = value;
  
  // First normalize whitespace
  let processedValue = normalizeWhitespace(value);
  
  // Then sanitize by removing invalid characters
  const sanitizedValue = sanitizeExportString(processedValue);
  
  // Check if the original value was valid
  const validation = validateExportString(originalValue);
  const wasModified = originalValue !== sanitizedValue;
  
  return {
    value: sanitizedValue,
    isValid: validation.isValid,
    error: validation.error,
    wasModified
  };
};

/**
 * Validates name field specifically for beneficiaries
 * @param name - Beneficiary name to validate
 * @returns Validation result object
 */
export const validateBeneficiaryName = (name: string): { isValid: boolean; error?: string } => {
  if (!name || name.trim().length === 0) {
    return { isValid: false, error: 'A név megadása kötelező' };
  }

  if (name.trim().length < 2) {
    return { isValid: false, error: 'A név legalább 2 karakter hosszú kell legyen' };
  }

  if (name.trim().length > 100) {
    return { isValid: false, error: 'A név maximum 100 karakter lehet' };
  }

  return validateExportString(name);
};

/**
 * Validates remittance information field
 * @param remittanceInfo - Remittance information to validate
 * @returns Validation result object
 */
export const validateRemittanceInfo = (remittanceInfo: string): { isValid: boolean; error?: string } => {
  if (!remittanceInfo) {
    return { isValid: true }; // Optional field
  }

  if (remittanceInfo.length > 140) {
    return { isValid: false, error: 'A közlemény maximum 140 karakter lehet' };
  }

  return validateExportString(remittanceInfo);
};