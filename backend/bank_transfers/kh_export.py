"""
KH Bank Text Export Generator
Generates .HUF.csv files for KH Bank import according to "IV. Egyszerűsített forintátutalás" format
"""

from typing import List
from datetime import datetime
from .models import Transfer, BankAccount


class KHBankExporter:
    """Generate KH Bank import files in .HUF.csv format"""
    
    def __init__(self):
        self.max_transfers = 40  # KH Bank limit
    
    def generate_kh_export(self, transfers: List[Transfer]) -> str:
        """
        Generate KH Bank .HUF.csv file content from transfers
        
        Args:
            transfers: List of Transfer objects to export
            
        Returns:
            String content of the .HUF.csv file
            
        Raises:
            ValueError: If more than 40 transfers or validation fails
        """
        if len(transfers) > self.max_transfers:
            raise ValueError(f"KH Bank format supports maximum {self.max_transfers} transfers, got {len(transfers)}")
        
        if not transfers:
            raise ValueError("No transfers provided for export")
        
        # Get default originator account
        default_account = transfers[0].originator_account
        
        # Build CSV content
        lines = []
        
        # Header row (field names - not imported by bank)
        header = [
            "Forrás számlaszám",
            "Partner számlaszáma", 
            "Partner neve",
            "Átutalandó összeg",
            "Átutalandó deviza",
            "Közlemény",
            "Átutalás egyedi azonosítója",
            "Értéknap"
        ]
        lines.append(";".join(header))
        
        # Data rows
        for i, transfer in enumerate(transfers, 1):
            # Validate transfer
            self._validate_transfer(transfer)
            
            # Clean and format account numbers (remove dashes, spaces)
            source_account = self._clean_account_number(transfer.originator_account.account_number)
            partner_account = self._clean_account_number(transfer.beneficiary.account_number)
            
            # Format amount as integer (remove decimals, no thousands separator)
            amount = int(transfer.amount)
            
            # Format execution date as YYYY.MM.DD
            execution_date = transfer.execution_date.strftime('%Y.%m.%d')
            
            # Clean text fields (ensure proper character encoding)
            partner_name = self._clean_text_field(transfer.beneficiary.name, 70)
            remittance = self._clean_text_field(transfer.remittance_info, 140)
            
            # Generate unique ID (optional) - use transfer ID or sequential number
            unique_id = str(transfer.id) if transfer.id else str(i)
            
            # Apply KH Bank field padding requirements
            partner_name_padded = partner_name.ljust(70)                    # Right pad with spaces to 70
            amount_padded = str(amount).zfill(18)                          # Left pad with zeros to 18
            remittance_padded = remittance.ljust(140)                      # Right pad with spaces to 140
            unique_id_padded = unique_id.zfill(35)                         # Left pad with zeros to 35
            
            # Build row
            row = [
                source_account,           # Forrás számlaszám (28)
                partner_account,          # Partner számlaszáma (28)  
                partner_name_padded,      # Partner neve (70) - right padded
                amount_padded,            # Átutalandó összeg (18) - left padded with zeros
                "HUF",                    # Átutalandó deviza (3)
                remittance_padded,        # Közlemény (140) - right padded
                unique_id_padded,         # Átutalás egyedi azonosítója (35) - left padded with zeros
                execution_date            # Értéknap (10)
            ]
            
            lines.append(";".join(row))
        
        return "\n".join(lines)
    
    def generate_kh_export_encoded(self, transfers: List[Transfer]) -> bytes:
        """
        Generate KH Bank .HUF.csv file content with ISO-8859-2 encoding
        
        Args:
            transfers: List of Transfer objects to export
            
        Returns:
            Bytes content with ISO-8859-2 encoding for KH Bank
        """
        # Generate the CSV content as string
        content = self.generate_kh_export(transfers)
        
        # Encode to ISO-8859-2 (Latin-2) for Hungarian bank compatibility
        try:
            encoded_content = content.encode('iso-8859-2')
            return encoded_content
        except UnicodeEncodeError as e:
            # If encoding fails, log problematic characters and use replacement
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"KH export encoding warning: {str(e)}")
            encoded_content = content.encode('iso-8859-2', errors='replace')
            return encoded_content
    
    def _validate_transfer(self, transfer: Transfer):
        """Validate transfer for KH Bank export requirements"""
        # Check currency is HUF
        if transfer.currency != 'HUF':
            raise ValueError(f"KH Bank format only supports HUF currency, got {transfer.currency}")
        
        # Check amount is positive
        if transfer.amount <= 0:
            raise ValueError(f"Amount must be positive, got {transfer.amount}")
        
        # Check beneficiary name exists
        if not transfer.beneficiary.name or not transfer.beneficiary.name.strip():
            raise ValueError("Beneficiary name is required")
        
        # Check account numbers exist
        if not transfer.beneficiary.account_number or not transfer.beneficiary.account_number.strip():
            raise ValueError("Beneficiary account number is required")
            
        if not transfer.originator_account.account_number or not transfer.originator_account.account_number.strip():
            raise ValueError("Originator account number is required")
    
    def _clean_account_number(self, account_number: str) -> str:
        """
        Clean account number for KH Bank format
        Remove dashes, spaces, and other separators
        """
        if not account_number:
            return ""
        
        # Remove all separators and whitespace
        cleaned = account_number.replace('-', '').replace(' ', '').replace('_', '')
        
        # Ensure it's not longer than 28 characters
        if len(cleaned) > 28:
            cleaned = cleaned[:28]
        
        return cleaned
    
    def _clean_text_field(self, text: str, max_length: int) -> str:
        """
        Clean text field according to KH Bank character restrictions
        
        Allowed characters:
        - English alphabet (upper and lower case)
        - Hungarian accented characters: áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý
        - Numbers
        - Special characters: space, tab, newline, ,-.,!?_:()+@;=<>~%*$#&/§
        """
        if not text:
            return ""
        
        # Define allowed characters (based on PDF spec)
        allowed_chars = set()
        
        # English alphabet
        allowed_chars.update('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        
        # Hungarian accented characters
        allowed_chars.update('áéíóúöüÁÉÍÓÚÖÜőŐűŰÄßäý')
        
        # Numbers
        allowed_chars.update('0123456789')
        
        # Special characters (based on PDF)
        allowed_chars.update(' \t\n,-.,!?_:()+@;=<>~%*$#&/§')
        
        # Filter out disallowed characters
        cleaned = ''.join(char for char in text if char in allowed_chars)
        
        # Truncate to max length
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned
    
    def get_filename(self, batch_name: str = None) -> str:
        """Generate filename for KH Bank export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if batch_name:
            # Clean batch name for filename
            safe_name = "".join(c for c in batch_name if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_name = safe_name.replace(' ', '_')
            return f"{safe_name}_KH_{timestamp}.HUF.csv"
        else:
            return f"KH_export_{timestamp}.HUF.csv"