"""
String validation utilities for XML/CSV export fields

Allowed characters for XML/CSV export:
- English alphabet (a-z, A-Z)
- Hungarian accented characters: áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý  
- Numbers (0-9)
- Special characters: space, tab, newline, -.,!?_:()+@;=<>~%*$#&/§
"""

import re
from typing import Dict, Any

# Define allowed characters for XML/CSV export
ALLOWED_ENGLISH_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
ALLOWED_HUNGARIAN_ACCENTS = 'áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý'
ALLOWED_NUMBERS = '0123456789'
ALLOWED_SPECIAL_CHARS = ' \t\n-.,!?_:()+@;=<>~%*$#&/§'

# Combined allowed character set
ALLOWED_CHARS = ALLOWED_ENGLISH_LETTERS + ALLOWED_HUNGARIAN_ACCENTS + ALLOWED_NUMBERS + ALLOWED_SPECIAL_CHARS

# Create regex pattern for allowed characters (escape special regex characters)
ALLOWED_CHARS_ESCAPED = re.escape(ALLOWED_CHARS).replace('\\-', '-').replace('\\]', ']').replace('\\[', '[')
ALLOWED_CHARS_REGEX = re.compile(f'^[{ALLOWED_CHARS_ESCAPED}]*$')


def validate_export_string(value: str) -> Dict[str, Any]:
    """
    Validates if a string contains only allowed characters for XML/CSV export
    
    Args:
        value: String to validate
        
    Returns:
        Dict with 'is_valid' boolean and 'error' message if invalid
    """
    if not value:
        return {'is_valid': True}
    
    if not ALLOWED_CHARS_REGEX.match(value):
        return {
            'is_valid': False,
            'error': 'Csak angol betűk, magyar ékezetes betűk (áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý), számok és a következő írásjelek engedélyezettek: -.,!?_:()+@;=<>~%*$#&/§'
        }
    
    return {'is_valid': True}


def sanitize_export_string(value: str) -> str:
    """
    Sanitizes a string by removing invalid characters for XML/CSV export
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string with only allowed characters
    """
    if not value:
        return ''
    
    return ''.join(char for char in value if char in ALLOWED_CHARS)


def normalize_whitespace(value: str) -> str:
    """
    Removes extra whitespace from a string (trims and removes multiple spaces/tabs/newlines)
    
    Args:
        value: String to clean
        
    Returns:
        String with normalized whitespace
    """
    if not value:
        return ''
    
    # Replace multiple whitespace with single space and trim
    return re.sub(r'\s+', ' ', value.strip())


def validate_beneficiary_name(name: str) -> Dict[str, Any]:
    """
    Validates name field specifically for beneficiaries
    
    Args:
        name: Beneficiary name to validate
        
    Returns:
        Validation result dict
    """
    if not name or not name.strip():
        return {'is_valid': False, 'error': 'A kedvezményezett neve kötelező'}
    
    if len(name.strip()) < 2:
        return {'is_valid': False, 'error': 'A kedvezményezett neve legalább 2 karakter hosszú kell legyen'}
    
    if len(name.strip()) > 100:
        return {'is_valid': False, 'error': 'A kedvezményezett neve maximum 100 karakter lehet'}
    
    return validate_export_string(name)


def validate_remittance_info(remittance_info: str) -> Dict[str, Any]:
    """
    Validates remittance information field
    
    Args:
        remittance_info: Remittance information to validate
        
    Returns:
        Validation result dict
    """
    if not remittance_info:
        return {'is_valid': True}  # Optional field
    
    if len(remittance_info) > 140:
        return {'is_valid': False, 'error': 'A közlemény maximum 140 karakter lehet'}
    
    return validate_export_string(remittance_info)


def validate_and_normalize_string_field(value: str, field_name: str = None) -> Dict[str, Any]:
    """
    Validates and normalizes a string field for XML/CSV export
    
    Args:
        value: String to process
        field_name: Optional field name for specific validation rules
        
    Returns:
        Dict with processed string and validation result
    """
    if not value:
        return {'value': '', 'is_valid': True, 'was_modified': False}
    
    original_value = value
    
    # Normalize whitespace first
    processed_value = normalize_whitespace(value)
    
    # Apply field-specific validation
    if field_name == 'name':
        validation = validate_beneficiary_name(processed_value)
    elif field_name == 'remittance_information':
        validation = validate_remittance_info(processed_value)
    else:
        validation = validate_export_string(processed_value)
    
    # Sanitize if needed (remove invalid characters)
    if not validation['is_valid']:
        sanitized_value = sanitize_export_string(processed_value)
        processed_value = sanitized_value
    
    was_modified = original_value != processed_value
    
    return {
        'value': processed_value,
        'is_valid': validation['is_valid'],
        'error': validation.get('error'),
        'was_modified': was_modified
    }