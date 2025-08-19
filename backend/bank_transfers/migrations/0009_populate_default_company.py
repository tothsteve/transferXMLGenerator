# Generated data migration to populate default company

from django.db import migrations


def create_default_company(apps, schema_editor):
    """Create a default company and assign all existing data to it"""
    Company = apps.get_model('bank_transfers', 'Company')
    BankAccount = apps.get_model('bank_transfers', 'BankAccount')
    Beneficiary = apps.get_model('bank_transfers', 'Beneficiary')
    TransferTemplate = apps.get_model('bank_transfers', 'TransferTemplate')
    TransferBatch = apps.get_model('bank_transfers', 'TransferBatch')
    
    # Create default company
    default_company, created = Company.objects.get_or_create(
        tax_id='00000000-0-00',
        defaults={
            'name': 'Main Company',
            'address': '',
            'phone': '',
            'email': '',
            'is_active': True,
        }
    )
    
    # Assign all existing records to the default company
    BankAccount.objects.filter(company__isnull=True).update(company=default_company)
    Beneficiary.objects.filter(company__isnull=True).update(company=default_company)
    TransferBatch.objects.filter(company__isnull=True).update(company=default_company)
    
    # Handle TransferTemplate with duplicate names by updating one by one
    for template in TransferTemplate.objects.filter(company__isnull=True):
        template.company = default_company
        # Check if this would create a duplicate
        existing = TransferTemplate.objects.filter(
            company=default_company, 
            name=template.name
        ).exclude(id=template.id).first()
        
        if existing:
            # Rename to avoid duplicate
            base_name = template.name
            counter = 1
            while TransferTemplate.objects.filter(
                company=default_company, 
                name=f"{base_name} ({counter})"
            ).exists():
                counter += 1
            template.name = f"{base_name} ({counter})"
        
        template.save()


def reverse_default_company(apps, schema_editor):
    """Remove the default company assignment"""
    Company = apps.get_model('bank_transfers', 'Company')
    
    # Delete the default company (this will cascade)
    Company.objects.filter(tax_id='00000000-0-00').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bank_transfers', '0008_company_bankaccount_bank_name_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_company, reverse_default_company),
    ]