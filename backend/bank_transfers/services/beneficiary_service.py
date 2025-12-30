"""
Beneficiary service layer
Handles business logic for beneficiary operations
"""
from typing import Optional, Dict, Any, Tuple
from django.db.models import Q, QuerySet
from ..models import Beneficiary, Company


class BeneficiaryService:
    """Service for beneficiary business logic"""

    @staticmethod
    def get_company_beneficiaries(
        company: Company,
        filters: Optional[Dict[str, Any]] = None
    ) -> QuerySet[Beneficiary]:
        """
        Get beneficiaries for a company with optional filters.

        Args:
            company: Company instance to get beneficiaries for
            filters: Optional dict of filter parameters (is_active, is_frequent, search, etc.)

        Returns:
            QuerySet of filtered Beneficiary instances
        """
        queryset = Beneficiary.objects.filter(company=company)
        
        if filters:
            # Apply active filter
            if filters.get('is_active') is not None:
                queryset = queryset.filter(is_active=filters['is_active'])
            
            # Apply frequent filter
            if filters.get('is_frequent') is not None:
                queryset = queryset.filter(is_frequent=filters['is_frequent'])
            
            # Apply search filter - search in name, account_number, vat_number, tax_number, and description
            search = filters.get('search')
            if search:
                search_q = Q(name__icontains=search) | Q(description__icontains=search)

                # Add account number search if present
                if 'account_number__icontains' not in str(search_q):
                    search_q |= Q(account_number__icontains=search)

                # Add VAT number search if present
                search_q |= Q(vat_number__icontains=search)

                # Add tax number search if present
                search_q |= Q(tax_number__icontains=search)

                queryset = queryset.filter(search_q)
            
            # Apply VAT number filter
            vat_number = filters.get('vat_number')
            if vat_number:
                queryset = queryset.filter(vat_number__icontains=vat_number)
            
            # Apply has_vat_number filter (true/false)
            has_vat_number = filters.get('has_vat_number')
            if has_vat_number is not None:
                if has_vat_number:
                    queryset = queryset.exclude(vat_number__isnull=True).exclude(vat_number='')
                else:
                    queryset = queryset.filter(Q(vat_number__isnull=True) | Q(vat_number=''))
            
            # Apply has_account_number filter (true/false)
            has_account_number = filters.get('has_account_number')
            if has_account_number is not None:
                if has_account_number:
                    queryset = queryset.exclude(account_number__isnull=True).exclude(account_number='')
                else:
                    queryset = queryset.filter(Q(account_number__isnull=True) | Q(account_number=''))

            # Apply tax number search if present
            tax_number = filters.get('tax_number')
            if tax_number:
                queryset = queryset.filter(tax_number__icontains=tax_number)

        return queryset
    
    @staticmethod
    def get_frequent_beneficiaries(company: Company) -> QuerySet[Beneficiary]:
        """
        Get frequent and active beneficiaries for a company.

        Args:
            company: Company instance to get beneficiaries for

        Returns:
            QuerySet of frequent and active Beneficiary instances
        """
        return Beneficiary.objects.filter(
            company=company,
            is_frequent=True,
            is_active=True
        )

    @staticmethod
    def create_beneficiary(company: Company, **beneficiary_data: Any) -> Beneficiary:
        """
        Create a new beneficiary with proper validation.

        Args:
            company: Company instance to create beneficiary for
            **beneficiary_data: Additional beneficiary fields (name, account_number, etc.)

        Returns:
            Created Beneficiary instance
        """
        beneficiary_data['company'] = company
        return Beneficiary.objects.create(**beneficiary_data)

    @staticmethod
    def toggle_frequent_status(beneficiary: Beneficiary) -> Beneficiary:
        """
        Toggle the frequent status of a beneficiary.

        Args:
            beneficiary: Beneficiary instance to toggle

        Returns:
            Updated Beneficiary instance
        """
        beneficiary.is_frequent = not beneficiary.is_frequent
        beneficiary.save()
        return beneficiary

    @staticmethod
    def find_or_create_from_excel_data(
        company: Company,
        name: str,
        account_number: str,
        **extra_data: Any
    ) -> Tuple[Beneficiary, bool]:
        """
        Find existing beneficiary or create new one from Excel import data.

        Args:
            company: Company instance to create beneficiary for
            name: Beneficiary name
            account_number: Bank account number
            **extra_data: Additional beneficiary fields

        Returns:
            Tuple of (Beneficiary instance, created boolean)
        """
        defaults = {
            'description': extra_data.get('description', ''),
            'is_active': True,
            'remittance_information': extra_data.get('remittance_information', ''),
            **extra_data
        }
        
        beneficiary, created = Beneficiary.objects.get_or_create(
            name=name,
            account_number=account_number,
            company=company,
            defaults=defaults
        )
        
        return beneficiary, created

    @staticmethod
    def find_beneficiary_by_tax_number(
        company: Company,
        supplier_tax_number: str
    ) -> Optional[Beneficiary]:
        """
        Find beneficiary by 8-digit tax number for transfer fallback.

        Args:
            company: Company instance
            supplier_tax_number: Tax number from NAV invoice (can be 8-13 digits)

        Returns:
            Beneficiary instance with account_number, or None if not found
        """
        if not supplier_tax_number or len(supplier_tax_number) < 8:
            return None

        # Extract base 8-digit tax number (normalize first by removing non-digits)
        normalized = ''.join(filter(str.isdigit, supplier_tax_number))
        base_tax = normalized[:8] if len(normalized) >= 8 else normalized

        if len(base_tax) != 8:
            return None

        # Find beneficiary with matching tax number and account number
        return Beneficiary.objects.filter(
            company=company,
            tax_number=base_tax,
            account_number__isnull=False,
            is_active=True
        ).exclude(account_number='').first()