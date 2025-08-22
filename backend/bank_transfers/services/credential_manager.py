from cryptography.fernet import Fernet
from django.conf import settings


class CredentialManager:
    """
    Manages encryption and decryption of company-specific NAV credentials.
    
    Uses the application's MASTER_ENCRYPTION_KEY to encrypt/decrypt all
    company credentials stored in the database.
    """
    
    def __init__(self):
        # Use the master encryption key for all company credentials
        self.cipher_suite = Fernet(settings.MASTER_ENCRYPTION_KEY.encode())
    
    def encrypt_credential(self, value):
        """Encrypt a credential value for database storage"""
        if not value:
            return ""
        return self.cipher_suite.encrypt(value.encode()).decode()
    
    def decrypt_credential(self, encrypted_value):
        """Decrypt a credential value from database storage"""
        if not encrypted_value:
            return ""
        return self.cipher_suite.decrypt(encrypted_value.encode()).decode()
    
    def generate_company_encryption_key(self):
        """Generate a new encryption key for a company's NAV credentials"""
        return Fernet.generate_key().decode()