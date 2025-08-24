"""
Beneficiary service layer
Handles business logic for beneficiary operations
"""
from django.db.models import Q
from ..models import Beneficiary


class BeneficiaryService:
    """Service for beneficiary business logic"""
    
    @staticmethod
    def get_company_beneficiaries(company, filters=None):
        """Get beneficiaries for a company with optional filters"""
        queryset = Beneficiary.objects.filter(company=company)
        
        if filters:
            # Apply active filter
            if filters.get('is_active') is not None:
                queryset = queryset.filter(is_active=filters['is_active'])
            
            # Apply frequent filter
            if filters.get('is_frequent') is not None:
                queryset = queryset.filter(is_frequent=filters['is_frequent'])
            
            # Apply search filter - search in name, account_number, and description
            search = filters.get('search')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(account_number__icontains=search) |
                    Q(description__icontains=search)
                )
        
        return queryset
    
    @staticmethod
    def get_frequent_beneficiaries(company):
        """Get frequent and active beneficiaries for a company"""
        return Beneficiary.objects.filter(
            company=company,
            is_frequent=True,
            is_active=True
        )
    
    @staticmethod
    def create_beneficiary(company, **beneficiary_data):
        """Create a new beneficiary with proper validation"""
        beneficiary_data['company'] = company
        return Beneficiary.objects.create(**beneficiary_data)
    
    @staticmethod
    def toggle_frequent_status(beneficiary):
        """Toggle the frequent status of a beneficiary"""
        beneficiary.is_frequent = not beneficiary.is_frequent
        beneficiary.save()
        return beneficiary
    
    @staticmethod
    def find_or_create_from_excel_data(company, name, account_number, **extra_data):
        """Find existing beneficiary or create new one from Excel import data"""
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