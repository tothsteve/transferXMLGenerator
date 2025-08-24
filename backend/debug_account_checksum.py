#!/usr/bin/env python3
"""
Debug script to test Hungarian account number checksum validation.
"""

from bank_transfers.hungarian_account_validator import validate_and_format_hungarian_account_number

def debug_account_number(account_number):
    """Debug a specific account number"""
    print(f"Testing account number: {account_number}")
    print(f"Length: {len(account_number)}")
    
    # Extract components
    if len(account_number) == 24:
        bank_code = account_number[0:3]
        branch_code = account_number[3:7]
        account_part = account_number[7:23]
        checksum_digit = int(account_number[23:24])
        
        print(f"Bank code: {bank_code}")
        print(f"Branch code: {branch_code}")
        print(f"Account part: {account_part}")
        print(f"Checksum digit: {checksum_digit}")
        
        # Calculate checksum manually
        total = 0
        weights = [9, 7, 3, 1]
        
        for i in range(16):
            digit = int(account_part[i])
            weight = weights[i % 4]
            total += digit * weight
            print(f"Position {i:2d}: digit {digit} × weight {weight} = {digit * weight:2d}, running total: {total}")
        
        calculated_checksum = (10 - (total % 10)) % 10
        print(f"\nTotal sum: {total}")
        print(f"Sum mod 10: {total % 10}")
        print(f"Calculated checksum: (10 - {total % 10}) mod 10 = {calculated_checksum}")
        print(f"Expected checksum: {checksum_digit}")
        print(f"Checksum valid: {calculated_checksum == checksum_digit}")
    
    # Test with validation function
    result = validate_and_format_hungarian_account_number(account_number)
    print(f"\nValidation result:")
    print(f"Valid: {result.is_valid}")
    print(f"Formatted: {result.formatted}")
    if result.error:
        print(f"Error: {result.error}")

if __name__ == "__main__":
    # Test the user's new 25-digit account number
    account_number = "1210001111409520000000000"
    print(f"Testing 25-digit account: {account_number} (Length: {len(account_number)})")
    debug_account_number(account_number)
    
    # Test the original 24-digit that worked
    print(f"\n{'='*50}")
    print("Testing original 24-digit account:")
    original_account = "121000111140952000000000"
    print(f"Original: {original_account} (Length: {len(original_account)})")
    debug_account_number(original_account)
    
    # Test what should be the correct version
    print(f"\n{'='*50}")
    print("Testing corrected 24-digit account:")
    corrected_account = "121000111140952000000000"
    print(f"Corrected: {corrected_account} (Length: {len(corrected_account)})")
    debug_account_number(corrected_account)