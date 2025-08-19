"""
Hungarian Bank Account Number Validation and Formatting Utilities

Hungarian BBAN (Basic Bank Account Number) format:
- Bank code: 3 digits
- Branch code: 4 digits  
- Account number: 16 digits
- National checksum: 1 digit
- Total: 24 digits (3+4+16+1)

Also supports legacy 16-digit format for backwards compatibility
"""

import re
from typing import Dict, Union


class AccountValidationResult:
    """Result of account validation"""
    def __init__(self, is_valid: bool, formatted: str, error: str = None):
        self.is_valid = is_valid
        self.formatted = formatted
        self.error = error


def validate_and_format_hungarian_account_number(
    account_number: str, 
    validate_checksum: bool = True
) -> AccountValidationResult:
    """
    Validates and formats a Hungarian bank account number
    
    Args:
        account_number: The input account number (with or without hyphens)
        validate_checksum: Whether to validate checksum (default: True)
        
    Returns:
        AccountValidationResult with validation status and formatted number
    """
    if not account_number:
        return AccountValidationResult(
            is_valid=False,
            formatted='',
            error='Számlaszám megadása kötelező'
        )

    # Check if it contains only digits and hyphens
    if not re.match(r'^[\d-]+$', account_number):
        return AccountValidationResult(
            is_valid=False,
            formatted=account_number,
            error='A számlaszám csak számokat és kötőjeleket tartalmazhat'
        )

    # Remove all non-digit characters for validation
    digits_only = re.sub(r'\D', '', account_number)

    # Validate length - Hungarian account numbers are 16 or 24 digits
    if len(digits_only) not in [16, 24]:
        return AccountValidationResult(
            is_valid=False,
            formatted=account_number,
            error='Magyar számlaszám 16 vagy 24 számjegyből áll'
        )

    # Format based on length
    if len(digits_only) == 16:
        # 16 digits: XXXXXXXX-XXXXXXXX
        formatted = f"{digits_only[:8]}-{digits_only[8:16]}"
    elif len(digits_only) == 24:
        # 24 digits: XXXXXXXX-XXXXXXXX-XXXXXXXX
        formatted = f"{digits_only[:8]}-{digits_only[8:16]}-{digits_only[16:24]}"
    else:
        return AccountValidationResult(
            is_valid=False,
            formatted=account_number,
            error='Érvénytelen számlaszám formátum'
        )

    # Validate checksum using Hungarian domestic algorithm (if enabled)
    if validate_checksum and not validate_hungarian_account_checksum(digits_only):
        return AccountValidationResult(
            is_valid=False,
            formatted=formatted,
            error='Érvénytelen ellenőrző összeg a számlaszámban'
        )

    return AccountValidationResult(
        is_valid=True,
        formatted=formatted
    )


def clean_account_number(account_number: str) -> str:
    """
    Strips formatting from account number for API submission
    
    Args:
        account_number: Formatted account number
        
    Returns:
        Clean number without hyphens
    """
    return re.sub(r'\D', '', account_number)


def validate_hungarian_account_checksum(account_number: str) -> bool:
    """
    Validates Hungarian BBAN checksum using the official algorithm
    
    Args:
        account_number: Clean account number (digits only)
        
    Returns:
        True if checksum is valid
    """
    # Remove any formatting
    digits = re.sub(r'\D', '', account_number)
    
    if len(digits) == 16:
        # Legacy 16-digit format - no specific checksum validation defined
        return True  # Accept for backwards compatibility
    elif len(digits) == 24:
        return validate_hungarian_bban_checksum(digits)
    
    return False


def validate_hungarian_bban_checksum(digits: str) -> bool:
    """
    Validates 24-digit Hungarian BBAN checksum
    Format: BBB-CCCC-AAAAAAAAAAAAAAAA-D
    Where: BBB=Bank code, CCCC=Branch code, A=Account number (16 digits), D=Checksum digit
    """
    try:
        if len(digits) != 24:
            return False

        # Extract components according to BBAN specification
        # bank_code = digits[0:3]      # 3 digits
        # branch_code = digits[3:7]    # 4 digits 
        account_number = digits[7:23]  # 16 digits
        checksum_digit = int(digits[23:24])  # 1 digit

        # Apply checksum algorithm to the 16-digit account number
        total = 0
        weights = [9, 7, 3, 1]  # Repeating pattern
        
        for i in range(16):
            digit = int(account_number[i])
            weight = weights[i % 4]  # Cycle through [9, 7, 3, 1]
            total += digit * weight

        # Calculate expected checksum: (10 - (sum mod 10)) mod 10
        calculated_checksum = (10 - (total % 10)) % 10
        
        return calculated_checksum == checksum_digit
    except (ValueError, IndexError):
        return False


def calculate_hungarian_bban_checksum(bank_code: str, branch_code: str, account_number: str) -> int:
    """
    Calculates the correct checksum digit for a Hungarian BBAN
    
    Args:
        bank_code: 3-digit bank code
        branch_code: 4-digit branch code  
        account_number: 16-digit account number
        
    Returns:
        The calculated checksum digit (0-9)
    """
    if len(account_number) != 16:
        raise ValueError('Account number must be exactly 16 digits')

    total = 0
    weights = [9, 7, 3, 1]  # Repeating pattern
    
    for i in range(16):
        digit = int(account_number[i])
        weight = weights[i % 4]  # Cycle through [9, 7, 3, 1]
        total += digit * weight

    # Calculate checksum: (10 - (sum mod 10)) mod 10
    checksum = (10 - (total % 10)) % 10
    return checksum


def is_valid_hungarian_account_number(account_number: str) -> bool:
    """
    Validates account number format without formatting
    
    Args:
        account_number: Account number to validate
        
    Returns:
        True if valid Hungarian account number format
    """
    result = validate_and_format_hungarian_account_number(account_number)
    return result.is_valid


def format_account_number_for_display(account_number: str) -> str:
    """
    Formats account number for display with proper Hungarian formatting
    
    Args:
        account_number: Raw account number
        
    Returns:
        Properly formatted account number (8-8 or 8-8-8 format)
    """
    result = validate_and_format_hungarian_account_number(account_number, validate_checksum=False)
    return result.formatted if result.is_valid else account_number


# Example account numbers for testing
EXAMPLE_ACCOUNT_NUMBERS = {
    # Test examples for format validation (16-digit legacy format)
    'format16': '1177342500989949',  # Should format to: 11773425-00989949
    'formatted16': '11773425-00989949',
    
    # Valid 24-digit BBAN with correct checksums
    'valid_bban': '117734212345678901234566',  # Bank:117, Branch:7342, Account:1234567890123456, Checksum:6
    'valid_bban2': '103200012345678901234566',  # Bank:103, Branch:2000, Account:1234567890123456, Checksum:6
    
    # Format examples (may have incorrect checksums)
    'format24': '121000111901487412345678',  # Should format to: 12100011-19014874-12345678
    'formatted24': '12100011-19014874-12345678',
    
    # Known Hungarian bank prefixes for testing structure
    'otp_bank': '117',  # OTP Bank (3-digit code)
    'nav': '103',  # Hungarian Treasury (NAV) (3-digit code)
    'nav_account': '10032000-06055950',  # Common NAV account format
}