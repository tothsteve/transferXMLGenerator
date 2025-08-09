from django.apps import AppConfig

class BankTransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_transfers'
    verbose_name = 'Bank Utalások'

# bank_transfers/admin.py
from django.contrib import admin
from .models import BankAccount, Beneficiary, Transfer, TransferTemplate, TransferBatch

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_number', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'account_number']

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_number', 'bank_name', 'is_frequent', 'created_at']
    list_filter = ['is_frequent', 'created_at']
    search_fields = ['name', 'account_number', 'bank_name']

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['beneficiary', 'amount', 'currency', 'execution_date', 'created_at']
    list_filter = ['currency', 'execution_date', 'created_at']
    search_fields = ['beneficiary__name', 'remittance_info']
    date_hierarchy = 'execution_date'

@admin.register(TransferTemplate)
class TransferTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']

@admin.register(TransferBatch)
class TransferBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'xml_generated_at']
    filter_horizontal = ['transfers']
