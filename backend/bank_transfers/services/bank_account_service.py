"""
Bank Account service layer
Handles business logic for bank account operations
"""
from django.db import transaction
from ..models import BankAccount


class BankAccountService:
    """Service for bank account business logic"""
    
    @staticmethod
    def get_default_account(company):
        """Get the default bank account for a company"""
        return BankAccount.objects.filter(
            company=company,
            is_default=True
        ).first()
    
    @staticmethod
    def set_default_account(account):
        """Set an account as default, ensuring only one default per company"""
        with transaction.atomic():
            # Clear existing default for this company
            BankAccount.objects.filter(
                company=account.company,
                is_default=True
            ).update(is_default=False)
            
            # Set this account as default
            account.is_default = True
            account.save()
            
        return account
    
    @staticmethod
    def create_account(company, **account_data):
        """Create a new bank account with proper validation"""
        account_data['company'] = company
        return BankAccount.objects.create(**account_data)
    
    @staticmethod
    def get_company_accounts(company):
        """Get all bank accounts for a company"""
        return BankAccount.objects.filter(company=company)