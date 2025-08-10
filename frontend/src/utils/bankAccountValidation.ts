/**
 * Hungarian Bank Account Number Validation and Formatting Utilities
 * 
 * Hungarian BBAN (Basic Bank Account Number) format:
 * - Bank code: 3 digits
 * - Branch code: 4 digits  
 * - Account number: 16 digits
 * - National checksum: 1 digit
 * - Total: 24 digits (3+4+16+1)
 * 
 * Also supports legacy 16-digit format for backwards compatibility
 */

export interface AccountValidationResult {
  isValid: boolean;
  formatted: string;
  error?: string;
}

/**
 * Validates and formats a Hungarian bank account number
 * @param accountNumber - The input account number (with or without hyphens)
 * @param validateChecksum - Whether to validate checksum (default: true)
 * @returns AccountValidationResult with validation status and formatted number
 */
export const validateAndFormatHungarianAccountNumber = (
  accountNumber: string, 
  validateChecksum: boolean = true
): AccountValidationResult => {
  if (!accountNumber) {
    return {
      isValid: false,
      formatted: '',
      error: 'Számlaszám megadása kötelező'
    };
  }

  // Check if it contains only digits and hyphens
  if (!/^[\d-]+$/.test(accountNumber)) {
    return {
      isValid: false,
      formatted: accountNumber,
      error: 'A számlaszám csak számokat és kötőjeleket tartalmazhat'
    };
  }

  // Remove all non-digit characters for validation
  const digitsOnly = accountNumber.replace(/\D/g, '');

  // Validate length - Hungarian account numbers are 16 or 24 digits
  if (digitsOnly.length !== 16 && digitsOnly.length !== 24) {
    return {
      isValid: false,
      formatted: accountNumber,
      error: 'Magyar számlaszám 16 vagy 24 számjegyből áll'
    };
  }

  // Format based on length
  let formatted: string;
  
  if (digitsOnly.length === 16) {
    // 16 digits: XXXXXXXX-XXXXXXXX
    formatted = `${digitsOnly.slice(0, 8)}-${digitsOnly.slice(8, 16)}`;
  } else if (digitsOnly.length === 24) {
    // 24 digits: XXXXXXXX-XXXXXXXX-XXXXXXXX
    formatted = `${digitsOnly.slice(0, 8)}-${digitsOnly.slice(8, 16)}-${digitsOnly.slice(16, 24)}`;
  } else {
    return {
      isValid: false,
      formatted: accountNumber,
      error: 'Érvénytelen számlaszám formátum'
    };
  }

  // Validate checksum using Hungarian domestic algorithm (if enabled)
  if (validateChecksum && !validateHungarianAccountChecksum(digitsOnly)) {
    return {
      isValid: false,
      formatted,
      error: 'Érvénytelen ellenőrző összeg a számlaszámban'
    };
  }

  return {
    isValid: true,
    formatted,
  };
};

/**
 * Real-time formatter for input fields - formats as user types
 * @param value - Current input value
 * @returns Formatted string for display in input field
 */
export const formatAccountNumberOnInput = (value: string): string => {
  // Remove all non-digit characters
  const digitsOnly = value.replace(/\D/g, '');
  
  // Don't format if empty or too long
  if (!digitsOnly || digitsOnly.length > 24) {
    return digitsOnly;
  }

  // Format based on current length
  if (digitsOnly.length <= 8) {
    return digitsOnly;
  } else if (digitsOnly.length <= 16) {
    return `${digitsOnly.slice(0, 8)}-${digitsOnly.slice(8)}`;
  } else {
    return `${digitsOnly.slice(0, 8)}-${digitsOnly.slice(8, 16)}-${digitsOnly.slice(16)}`;
  }
};

/**
 * Strips formatting from account number for API submission
 * @param accountNumber - Formatted account number
 * @returns Clean number without hyphens
 */
export const cleanAccountNumber = (accountNumber: string): string => {
  return accountNumber.replace(/\D/g, '');
};

/**
 * Validates Hungarian BBAN checksum using the official algorithm
 * @param accountNumber - Clean account number (digits only)
 * @returns True if checksum is valid
 */
export const validateHungarianAccountChecksum = (accountNumber: string): boolean => {
  // Remove any formatting
  const digits = accountNumber.replace(/\D/g, '');
  
  if (digits.length === 16) {
    // Legacy 16-digit format - no specific checksum validation defined
    return true; // Accept for backwards compatibility
  } else if (digits.length === 24) {
    return validateHungarianBBANChecksum(digits);
  }
  
  return false;
};

/**
 * Validates 24-digit Hungarian BBAN checksum
 * Format: BBB-CCCC-AAAAAAAAAAAAAAAA-D
 * Where: BBB=Bank code, CCCC=Branch code, A=Account number (16 digits), D=Checksum digit
 */
const validateHungarianBBANChecksum = (digits: string): boolean => {
  try {
    if (digits.length !== 24) {
      return false;
    }

    // Extract components according to BBAN specification
    // const bankCode = digits.substring(0, 3);      // 3 digits
    // const branchCode = digits.substring(3, 7);    // 4 digits 
    const accountNumber = digits.substring(7, 23); // 16 digits
    const checksumDigit = parseInt(digits.substring(23, 24)); // 1 digit

    // Apply checksum algorithm to the 16-digit account number
    let sum = 0;
    const weights = [9, 7, 3, 1]; // Repeating pattern
    
    for (let i = 0; i < 16; i++) {
      const digit = parseInt(accountNumber[i]);
      const weight = weights[i % 4]; // Cycle through [9, 7, 3, 1]
      sum += digit * weight;
    }

    // Calculate expected checksum: (10 - (sum mod 10)) mod 10
    const calculatedChecksum = (10 - (sum % 10)) % 10;
    
    return calculatedChecksum === checksumDigit;
  } catch (error) {
    return false;
  }
};

/**
 * Validates account number format without formatting
 * @param accountNumber - Account number to validate
 * @returns True if valid Hungarian account number format
 */
export const isValidHungarianAccountNumber = (accountNumber: string): boolean => {
  const result = validateAndFormatHungarianAccountNumber(accountNumber);
  return result.isValid;
};

/**
 * Calculates the correct checksum digit for a Hungarian BBAN
 * @param bankCode - 3-digit bank code
 * @param branchCode - 4-digit branch code  
 * @param accountNumber - 16-digit account number
 * @returns The calculated checksum digit (0-9)
 */
export const calculateHungarianBBANChecksum = (
  bankCode: string, 
  branchCode: string, 
  accountNumber: string
): number => {
  if (accountNumber.length !== 16) {
    throw new Error('Account number must be exactly 16 digits');
  }

  let sum = 0;
  const weights = [9, 7, 3, 1]; // Repeating pattern
  
  for (let i = 0; i < 16; i++) {
    const digit = parseInt(accountNumber[i]);
    const weight = weights[i % 4]; // Cycle through [9, 7, 3, 1]
    sum += digit * weight;
  }

  // Calculate checksum: (10 - (sum mod 10)) mod 10
  const checksum = (10 - (sum % 10)) % 10;
  return checksum;
};

/**
 * Generates a valid Hungarian BBAN with correct checksum
 * @param bankCode - 3-digit bank code
 * @param branchCode - 4-digit branch code
 * @param accountNumber - 16-digit account number
 * @returns Complete 24-digit BBAN with correct checksum
 */
export const generateValidHungarianBBAN = (
  bankCode: string, 
  branchCode: string, 
  accountNumber: string
): string => {
  if (bankCode.length !== 3 || !/^\d{3}$/.test(bankCode)) {
    throw new Error('Bank code must be exactly 3 digits');
  }
  if (branchCode.length !== 4 || !/^\d{4}$/.test(branchCode)) {
    throw new Error('Branch code must be exactly 4 digits');
  }
  if (accountNumber.length !== 16 || !/^\d{16}$/.test(accountNumber)) {
    throw new Error('Account number must be exactly 16 digits');
  }

  const checksum = calculateHungarianBBANChecksum(bankCode, branchCode, accountNumber);
  return bankCode + branchCode + accountNumber + checksum.toString();
};

/**
 * Common Hungarian bank account number examples for testing
 * Note: 24-digit examples include correct BBAN checksums
 */
export const EXAMPLE_ACCOUNT_NUMBERS = {
  // Test examples for format validation (16-digit legacy format)
  format16: '1177342500989949', // Should format to: 11773425-00989949
  formatted16: '11773425-00989949',
  
  // Valid 24-digit BBAN with correct checksums
  validBBAN: '117734212345678901234566', // Bank:117, Branch:7342, Account:1234567890123456, Checksum:6
  validBBAN2: '103200012345678901234566', // Bank:103, Branch:2000, Account:1234567890123456, Checksum:6 (same account = same checksum)
  
  // Format examples (may have incorrect checksums)
  format24: '121000111901487412345678', // Should format to: 12100011-19014874-12345678
  formatted24: '12100011-19014874-12345678',
  
  // Invalid examples
  invalid: '123456789', // Too short
  invalidChars: '1177-3425-ABCD-9949', // Contains letters
  invalidChecksum: '117734212345678901234567', // Wrong checksum (should be 6, not 7)
  
  // Known Hungarian bank prefixes for testing structure
  otpBank: '117', // OTP Bank (3-digit code)
  nav: '103', // Hungarian Treasury (NAV) (3-digit code)
  kAndH: '104', // K&H Bank (3-digit code)
  erste: '116', // Erste Bank (3-digit code)
  magyar: '103', // MKB Bank (3-digit code)
};