"""
Banking Serializers Module

This module contains serializers for core banking operations including:
- Bank accounts and beneficiaries
- Transfer templates and template beneficiaries
- Individual transfers and transfer batches
- Bulk transfer operations and Excel imports
- XML/CSV export generation
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import (
    BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, Company
)
from ..validators import validate_hungarian_account_number
from ..string_validation import validate_beneficiary_name, validate_remittance_info, normalize_whitespace, sanitize_export_string


class BankAccountSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = BankAccount
        fields = ['id', 'name', 'account_number', 'bank_name', 'is_default', 'company_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

    def validate_account_number(self, value):
        """Validate and format Hungarian bank account number using shared validator"""
        return validate_hungarian_account_number(value)

class BeneficiarySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'account_number', 'vat_number', 'tax_number', 'description',
            'is_frequent', 'is_active', 'remittance_information',
            'company_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

    def validate_account_number(self, value):
        """Validate and format Hungarian bank account number using shared validator"""
        return validate_hungarian_account_number(value)

    def validate_name(self, value):
        """Sanitize beneficiary name for XML/CSV export"""
        if not value or not value.strip():
            raise serializers.ValidationError("A kedvezményezett neve kötelező.")

        # Sanitize invalid characters and normalize whitespace
        sanitized = sanitize_export_string(value)
        return normalize_whitespace(sanitized)

    def validate_remittance_information(self, value):
        """Sanitize remittance information for XML/CSV export"""
        if not value:
            return value

        # Sanitize invalid characters and normalize whitespace
        sanitized = sanitize_export_string(value)
        return normalize_whitespace(sanitized)

    def validate_vat_number(self, value):
        """Validate Hungarian VAT number format"""
        if not value:
            return value

        # Clean the VAT number (remove spaces and dashes)
        clean_vat = value.replace(' ', '').replace('-', '')

        # Validate format
        if not clean_vat.isdigit() or len(clean_vat) != 10:
            raise serializers.ValidationError(
                "Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8440961790)"
            )

        # Return the cleaned VAT number
        return clean_vat

    def validate_tax_number(self, value):
        """Validate Hungarian company tax number format"""
        if not value:
            return value

        # Clean the tax number (remove spaces and dashes)
        clean_tax = value.replace(' ', '').replace('-', '')

        # Validate format: exactly 8 digits
        if not clean_tax.isdigit() or len(clean_tax) != 8:
            raise serializers.ValidationError(
                "Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)"
            )

        # Return the cleaned tax number
        return clean_tax

    def validate(self, data):
        """Validate that at least one identifier is provided"""
        account_number = data.get('account_number')
        vat_number = data.get('vat_number')
        tax_number = data.get('tax_number')

        if not account_number and not vat_number and not tax_number:
            raise serializers.ValidationError(
                "Meg kell adni a számlaszámot, adóazonosító jelet vagy céges adószámot"
            )

        return data

class TemplateBeneficiarySerializer(serializers.ModelSerializer):
    beneficiary = BeneficiarySerializer(read_only=True)
    beneficiary_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TemplateBeneficiary
        fields = [
            'id', 'beneficiary', 'beneficiary_id',
            'default_amount', 'default_remittance', 'default_execution_date',
            'order', 'is_active'
        ]

class TransferTemplateSerializer(serializers.ModelSerializer):
    template_beneficiaries = TemplateBeneficiarySerializer(many=True, read_only=True)
    beneficiary_count = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = TransferTemplate
        fields = [
            'id', 'name', 'description', 'is_active',
            'template_beneficiaries', 'beneficiary_count', 'company_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

    def get_beneficiary_count(self, obj):
        return obj.template_beneficiaries.filter(is_active=True).count()

class TransferSerializer(serializers.ModelSerializer):
    beneficiary = BeneficiarySerializer(read_only=True)
    beneficiary_id = serializers.IntegerField(write_only=True)
    originator_account = BankAccountSerializer(read_only=True)
    originator_account_id = serializers.IntegerField(write_only=True)
    nav_invoice_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Transfer
        fields = [
            'id', 'originator_account', 'originator_account_id',
            'beneficiary', 'beneficiary_id', 'amount', 'currency',
            'execution_date', 'remittance_info', 'template', 'nav_invoice', 'nav_invoice_id',
            'order', 'is_processed', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_remittance_info(self, value):
        """Sanitize remittance info for XML/CSV export"""
        if not value:
            return value

        # Sanitize invalid characters and normalize whitespace
        sanitized = sanitize_export_string(value)
        return normalize_whitespace(sanitized)

    def validate_beneficiary_id(self, value):
        """Validate that beneficiary has account number for transfer creation"""
        try:
            beneficiary = Beneficiary.objects.get(id=value)
            if not beneficiary.account_number:
                raise serializers.ValidationError(
                    f"Kedvezményezett '{beneficiary.name}' rendelkezik adóazonosító jellel ({beneficiary.vat_number}), "
                    f"de nincs bankszámlaszáma. Kérem adja meg a bankszámlaszámot az utalás létrehozása előtt."
                )
            return value
        except Beneficiary.DoesNotExist:
            raise serializers.ValidationError("A kedvezményezett nem található.")

class TransferBatchSerializer(serializers.ModelSerializer):
    transfers = TransferSerializer(many=True, read_only=True)
    transfer_count = serializers.SerializerMethodField()
    filename = serializers.ReadOnlyField()
    xml_filename = serializers.ReadOnlyField()  # Keep for backwards compatibility
    company_name = serializers.CharField(source='company.name', read_only=True)
    batch_format_display = serializers.CharField(source='get_batch_format_display', read_only=True)

    class Meta:
        model = TransferBatch
        fields = [
            'id', 'name', 'description', 'transfers',
            'total_amount', 'transfer_count', 'order',
            'used_in_bank', 'bank_usage_date', 'batch_format', 'batch_format_display',
            'filename', 'xml_filename', 'company_name', 'created_at', 'xml_generated_at'
        ]
        read_only_fields = ['created_at', 'xml_generated_at', 'total_amount', 'filename', 'xml_filename', 'company', 'company_name', 'batch_format_display']

    def get_transfer_count(self, obj):
        return obj.transfers.count()

# Transfer creation for template loading
class TransferCreateFromTemplateSerializer(serializers.Serializer):
    template_id = serializers.IntegerField()
    originator_account_id = serializers.IntegerField()
    execution_date = serializers.DateField()

class BulkTransferSerializer(serializers.Serializer):
    transfers = TransferSerializer(many=True)
    batch_name = serializers.CharField(max_length=200, required=False)

# Excel import serializer
class ExcelImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    import_type = serializers.ChoiceField(choices=[
        ('beneficiaries', 'Kedvezményezettek'),
        ('transfers', 'Utalások')
    ], default='beneficiaries')

# XML generation serializer
class XMLGenerateSerializer(serializers.Serializer):
    transfer_ids = serializers.ListField(child=serializers.IntegerField())
    batch_name = serializers.CharField(max_length=200, required=False)
