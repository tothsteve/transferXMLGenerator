"""
Bank Account service layer
Handles business logic for bank account operations
"""
from typing import Optional, Any
from django.db import transaction
from django.db.models import QuerySet
from ..models import BankAccount, Company


class BankAccountService:
    """Service for bank account business logic"""

    @staticmethod
    def get_default_account(company: Company) -> Optional[BankAccount]:
        """
        Get the default bank account for a company.

        Args:
            company: Company instance to get default account for

        Returns:
            Default BankAccount instance or None if no default is set
        """
        return BankAccount.objects.filter(
            company=company,
            is_default=True
        ).first()

    @staticmethod
    def set_default_account(account: BankAccount) -> BankAccount:
        """
        Set an account as default, ensuring only one default per company.

        Args:
            account: BankAccount instance to set as default

        Returns:
            Updated BankAccount instance with is_default=True
        """
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
    def create_account(company: Company, **account_data: Any) -> BankAccount:
        """
        Create a new bank account with proper validation.

        Args:
            company: Company instance to create account for
            **account_data: Additional account fields (name, account_number, etc.)

        Returns:
            Created BankAccount instance
        """
        account_data['company'] = company
        return BankAccount.objects.create(**account_data)

    @staticmethod
    def get_company_accounts(company: Company) -> QuerySet[BankAccount]:
        """
        Get all bank accounts for a company.

        Args:
            company: Company instance to get accounts for

        Returns:
            QuerySet of BankAccount instances for the company
        """
        return BankAccount.objects.filter(company=company)