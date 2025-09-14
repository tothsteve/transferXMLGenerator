"""
Template service layer
Handles business logic for transfer template operations
"""
from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import date
from ..models import TransferTemplate, TemplateBeneficiary, BankAccount


class TemplateService:
    """Service for transfer template business logic"""
    
    @staticmethod
    def get_company_templates(company, include_inactive=False):
        """Get templates for a company
        
        Args:
            company: Company instance
            include_inactive: If True, includes inactive templates as well
        """
        queryset = TransferTemplate.objects.filter(company=company)
        
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def create_template(company, **template_data):
        """Create a new transfer template"""
        template_data['company'] = company
        return TransferTemplate.objects.create(**template_data)
    
    @staticmethod
    def add_beneficiary_to_template(template, beneficiary, **beneficiary_data):
        """Add a beneficiary to a template with default values"""
        return TemplateBeneficiary.objects.create(
            template=template,
            beneficiary=beneficiary,
            **beneficiary_data
        )
    
    @staticmethod
    def remove_beneficiary_from_template(template, beneficiary_id):
        """Remove a beneficiary from a template"""
        template_beneficiary = get_object_or_404(
            TemplateBeneficiary,
            template=template,
            beneficiary_id=beneficiary_id
        )
        template_beneficiary.delete()
    
    @staticmethod
    def update_template_beneficiary(template, beneficiary_id, **update_data):
        """Update template beneficiary data"""
        template_beneficiary = get_object_or_404(
            TemplateBeneficiary,
            template=template,
            beneficiary_id=beneficiary_id
        )
        
        for field, value in update_data.items():
            setattr(template_beneficiary, field, value)
        
        template_beneficiary.save()
        return template_beneficiary
    
    @staticmethod
    def load_template_transfers(template, originator_account_id, execution_date):
        """Load template and generate transfer data"""
        originator_account = get_object_or_404(BankAccount, id=originator_account_id)
        
        transfers = []
        today = date.today()
        
        for template_beneficiary in template.template_beneficiaries.filter(is_active=True):
            # Use template's default execution date if available, but ensure it's not in the past
            if template_beneficiary.default_execution_date:
                template_date = template_beneficiary.default_execution_date
                # If template date is in the past, use today's date instead
                if template_date < today:
                    beneficiary_execution_date = today.strftime('%Y-%m-%d')
                else:
                    beneficiary_execution_date = template_date.strftime('%Y-%m-%d')
            else:
                beneficiary_execution_date = execution_date
            
            transfer_data = {
                'originator_account': originator_account.id,
                'beneficiary': template_beneficiary.beneficiary.id,
                'beneficiary_data': {
                    'id': template_beneficiary.beneficiary.id,
                    'name': template_beneficiary.beneficiary.name,
                    'account_number': template_beneficiary.beneficiary.account_number,
                    'vat_number': template_beneficiary.beneficiary.vat_number,
                    'description': template_beneficiary.beneficiary.description,
                    'is_frequent': template_beneficiary.beneficiary.is_frequent,
                    'is_active': template_beneficiary.beneficiary.is_active,
                },
                'amount': template_beneficiary.default_amount or 0,
                'currency': 'HUF',
                'execution_date': beneficiary_execution_date,
                'remittance_info': (
                    template_beneficiary.default_remittance or
                    template_beneficiary.beneficiary.remittance_information or
                    ''
                ),
                'template': template.id
            }
            transfers.append(transfer_data)
        
        return transfers