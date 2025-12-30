"""
Hungarian-specific validators.

Contains validation logic for Hungarian financial identifiers including
bank account numbers, tax numbers, and other local formats.
"""

from rest_framework import serializers
from ..hungarian_account_validator import validate_and_format_hungarian_account_number


def validate_hungarian_account_number(value: str) -> str:
    """
    Validate and format Hungarian bank account number.

    This validator ensures the account number follows Hungarian banking
    standards and returns a consistently formatted version.

    Args:
        value: Account number string (may contain spaces or dashes)

    Returns:
        Formatted account number in standard format

    Raises:
        serializers.ValidationError: If validation fails

    Example:
        >>> validate_hungarian_account_number("12345678-12345678-12345678")
        "12345678-12345678-12345678"
    """
    if not value:
        raise serializers.ValidationError("Számlaszám megadása kötelező")

    validation = validate_and_format_hungarian_account_number(value)
    if not validation.is_valid:
        raise serializers.ValidationError(
            validation.error or "Érvénytelen számlaszám formátum"
        )

    # Return the formatted account number for consistent storage
    return validation.formatted
