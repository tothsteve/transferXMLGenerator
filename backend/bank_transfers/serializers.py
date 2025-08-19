from rest_framework import serializers
from .models import BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, Company

class BankAccountSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = ['id', 'name', 'account_number', 'bank_name', 'is_default', 'company_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

class BeneficiarySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'account_number', 'description', 
            'is_frequent', 'is_active', 'remittance_information', 
            'company_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

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
    
    class Meta:
        model = Transfer
        fields = [
            'id', 'originator_account', 'originator_account_id',
            'beneficiary', 'beneficiary_id', 'amount', 'currency',
            'execution_date', 'remittance_info', 'template', 'order',
            'is_processed', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TransferBatchSerializer(serializers.ModelSerializer):
    transfers = TransferSerializer(many=True, read_only=True)
    transfer_count = serializers.SerializerMethodField()
    xml_filename = serializers.ReadOnlyField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = TransferBatch
        fields = [
            'id', 'name', 'description', 'transfers',
            'total_amount', 'transfer_count', 'order',
            'used_in_bank', 'bank_usage_date', 'xml_filename',
            'company_name', 'created_at', 'xml_generated_at'
        ]
        read_only_fields = ['created_at', 'xml_generated_at', 'total_amount', 'xml_filename', 'company', 'company_name']
    
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
