from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Company(models.Model):
    """Cég entitás multi-tenant architektúrához"""
    name = models.CharField(max_length=200, verbose_name="Cég neve")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="Adószám")
    address = models.TextField(blank=True, verbose_name="Cím")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cég"
        verbose_name_plural = "Cégek"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CompanyUser(models.Model):
    """Felhasználó-cég kapcsolat szerepkörrel"""
    ROLE_CHOICES = [
        ('ADMIN', 'Cég adminisztrátor'),
        ('USER', 'Felhasználó'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER', verbose_name="Szerepkör")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cég felhasználó"
        verbose_name_plural = "Cég felhasználók"
        unique_together = ['user', 'company']
        ordering = ['company__name', 'user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.company.name} ({self.role})"

class UserProfile(models.Model):
    """Felhasználói profil kiegészítő adatokkal"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    preferred_language = models.CharField(max_length=10, default='hu', verbose_name="Nyelv")
    timezone = models.CharField(max_length=50, default='Europe/Budapest', verbose_name="Időzóna")
    last_active_company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, 
                                          verbose_name="Utoljára aktív cég")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Felhasználói profil"
        verbose_name_plural = "Felhasználói profilok"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} profil"

class BankAccount(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Számla neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    bank_name = models.CharField(max_length=200, blank=True, verbose_name="Bank neve")
    is_default = models.BooleanField(default=False, verbose_name="Alapértelmezett")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bank számla"
        verbose_name_plural = "Bank számlák"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"
    
    def clean_account_number(self):
        return self.account_number.replace('-', '').replace(' ', '')

class Beneficiary(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='beneficiaries', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Kedvezményezett neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    description = models.CharField(max_length=200, blank=True, verbose_name="Leírás", 
                                 help_text="További információk a kedvezményezettről (bank neve, szervezet adatai, stb.)")
    is_frequent = models.BooleanField(default=False, verbose_name="Gyakori kedvezményezett")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    remittance_information = models.TextField(blank=True, verbose_name="Utalási információ",
                                            help_text="Alapértelmezett fizetési hivatkozások, számlaszámok vagy egyéb tranzakció-specifikus információk")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kedvezményezett"
        verbose_name_plural = "Kedvezményezettek"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_frequent']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"
    
    def clean_account_number(self):
        return self.account_number.replace('-', '').replace(' ', '')

class TransferTemplate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='transfer_templates', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Sablon neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Utalási sablon"
        verbose_name_plural = "Utalási sablonok"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TemplateBeneficiary(models.Model):
    template = models.ForeignKey(TransferTemplate, on_delete=models.CASCADE, related_name='template_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    default_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    default_remittance = models.CharField(max_length=500, blank=True)
    default_execution_date = models.DateField(null=True, blank=True, verbose_name="Alapértelmezett teljesítési dátum")
    order = models.IntegerField(default=0, verbose_name="Sorrend")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Sablon kedvezményezett"
        verbose_name_plural = "Sablon kedvezményezettek"
        ordering = ['order', 'beneficiary__name']
        unique_together = ['template', 'beneficiary']

class Transfer(models.Model):
    CURRENCY_CHOICES = [
        ('HUF', 'HUF'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]
    
    originator_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, verbose_name="Terhelendő számla")
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, verbose_name="Kedvezményezett")
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Összeg")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='HUF', verbose_name="Pénznem")
    execution_date = models.DateField(verbose_name="Teljesítési dátum")
    remittance_info = models.CharField(max_length=500, verbose_name="Közlemény")
    template = models.ForeignKey(TransferTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sablon")
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Átutalások sorrendje XML generáláskor")
    is_processed = models.BooleanField(default=False, verbose_name="Feldolgozva")
    notes = models.TextField(blank=True, verbose_name="Megjegyzések")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Utalás"
        verbose_name_plural = "Utalások"
        ordering = ['order', '-execution_date', '-created_at']
        indexes = [
            models.Index(fields=['execution_date']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.beneficiary.name} - {self.amount} {self.currency}"
    
    @property
    def company(self):
        """Get company from the originator account"""
        return self.originator_account.company

class TransferBatch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='transfer_batches', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Köteg neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    transfers = models.ManyToManyField(Transfer, verbose_name="Utalások")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Összeg")
    used_in_bank = models.BooleanField(default=False, verbose_name="Felhasználva a bankban", help_text="Jelzi, hogy az XML fájl fel lett-e töltve az internetbankba")
    bank_usage_date = models.DateTimeField(null=True, blank=True, verbose_name="Bank felhasználás dátuma")
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Kötegek sorrendje a listázáshoz és letöltéshez")
    created_at = models.DateTimeField(auto_now_add=True)
    xml_generated_at = models.DateTimeField(null=True, blank=True, verbose_name="XML generálás ideje")
    
    class Meta:
        verbose_name = "Utalási köteg"
        verbose_name_plural = "Utalási kötegek"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.transfers.count()} utalás)"
    
    @property
    def xml_filename(self):
        """Generate XML filename based on batch name and date"""
        if self.xml_generated_at:
            date_str = self.xml_generated_at.strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in self.name if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_name = safe_name.replace(' ', '_')
            return f"{safe_name}_{date_str}.xml"
        return f"{self.name.replace(' ', '_')}.xml"


# NAV Online Invoice Synchronization Models

class NavConfiguration(models.Model):
    """
    Company-specific NAV API credentials and synchronization settings.
    
    Key Architecture Notes:
    - Each company has their own NAV API credentials stored encrypted in the database
    - All company credentials are encrypted using the application's master encryption key
    - No company-specific keys are stored in environment variables
    - Multi-tenant architecture with complete data isolation per company
    """
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='nav_config')
    
    # Company-specific NAV credentials
    tax_number = models.CharField(max_length=20, verbose_name="NAV adószám")
    technical_user_login = models.CharField(max_length=100, verbose_name="Technikai felhasználó")
    technical_user_password = models.TextField(verbose_name="Jelszó (titkosítva)")  # Encrypted with MASTER_ENCRYPTION_KEY
    signing_key = models.TextField(verbose_name="Aláíró kulcs (titkosítva)")  # Encrypted with MASTER_ENCRYPTION_KEY
    exchange_key = models.TextField(verbose_name="Csere kulcs (titkosítva)")  # Encrypted with MASTER_ENCRYPTION_KEY
    
    # Company-specific NAV encryption key (for internal company use)
    company_encryption_key = models.TextField(verbose_name="Cég titkosítási kulcs (titkosítva)")  # Encrypted with MASTER_ENCRYPTION_KEY
    
    # Configuration settings
    api_environment = models.CharField(
        max_length=10, 
        choices=[('test', 'Test'), ('production', 'Éles')], 
        default='test',
        verbose_name="API környezet"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    sync_enabled = models.BooleanField(default=False, verbose_name="Szinkronizáció engedélyezett")
    last_sync_timestamp = models.DateTimeField(null=True, blank=True, verbose_name="Utolsó szinkronizáció")
    sync_frequency_hours = models.IntegerField(default=12, verbose_name="Szinkronizáció gyakorisága (óra)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "NAV konfiguráció"
        verbose_name_plural = "NAV konfigurációk"
    
    def __str__(self):
        return f"NAV konfiguráció - {self.company.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate company encryption key if not exists
        if not self.company_encryption_key:
            from .services.credential_manager import CredentialManager
            credential_manager = CredentialManager()
            company_key = credential_manager.generate_company_encryption_key()
            self.company_encryption_key = credential_manager.encrypt_credential(company_key)
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """
    Core invoice data synchronized from NAV API.
    """
    DIRECTION_CHOICES = [
        ('INBOUND', 'Bejövő számla'),
        ('OUTBOUND', 'Kimenő számla'),
    ]
    
    SYNC_STATUS_CHOICES = [
        ('SUCCESS', 'Sikeres'),
        ('PARTIAL', 'Részleges'),
        ('FAILED', 'Sikertelen'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    nav_invoice_number = models.CharField(max_length=100, verbose_name="NAV számlaszám")
    invoice_direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Irány")
    
    # Supplier information
    supplier_name = models.CharField(max_length=200, verbose_name="Szállító neve")
    supplier_tax_number = models.CharField(max_length=20, blank=True, verbose_name="Szállító adószáma")
    
    # Customer information  
    customer_name = models.CharField(max_length=200, verbose_name="Vevő neve")
    customer_tax_number = models.CharField(max_length=20, blank=True, verbose_name="Vevő adószáma")
    
    # Invoice dates
    issue_date = models.DateField(verbose_name="Kiállítás dátuma")
    fulfillment_date = models.DateField(null=True, blank=True, verbose_name="Teljesítés dátuma")
    payment_due_date = models.DateField(null=True, blank=True, verbose_name="Fizetési határidő")
    
    # Financial data
    currency_code = models.CharField(max_length=3, default='HUF', verbose_name="Pénznem")
    invoice_net_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Nettó összeg")
    invoice_vat_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="ÁFA összeg")
    invoice_gross_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Bruttó összeg")
    
    # NAV metadata
    original_request_version = models.CharField(max_length=10, verbose_name="NAV verzió")
    completion_date = models.DateTimeField(null=True, blank=True, verbose_name="NAV feldolgozás dátuma")
    source = models.CharField(max_length=20, default='NAV_SYNC', verbose_name="Forrás")
    nav_transaction_id = models.CharField(max_length=100, blank=True, verbose_name="NAV tranzakció azonosító")
    last_modified_date = models.DateTimeField(verbose_name="Utolsó módosítás (NAV)")
    
    # Sync metadata
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES, default='SUCCESS')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Számla"
        verbose_name_plural = "Számlák"
        ordering = ['-issue_date', '-created_at']
        unique_together = ['company', 'nav_invoice_number', 'invoice_direction']
        indexes = [
            models.Index(fields=['company', 'invoice_direction']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['supplier_tax_number']),
            models.Index(fields=['customer_tax_number']),
            models.Index(fields=['nav_invoice_number']),
        ]
    
    def __str__(self):
        return f"{self.nav_invoice_number} - {self.supplier_name} ({self.invoice_direction})"


class InvoiceLineItem(models.Model):
    """
    Detailed line items for each invoice.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.IntegerField(verbose_name="Sor száma")
    line_description = models.TextField(verbose_name="Megnevezés")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Mennyiség")
    unit_of_measure = models.CharField(max_length=50, blank=True, verbose_name="Mértékegység")
    unit_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, verbose_name="Egységár")
    line_net_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sor nettó összeg")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="ÁFA kulcs (%)")
    line_vat_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sor ÁFA összeg")
    line_gross_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sor bruttó összeg")
    
    # Product classification
    product_code_category = models.CharField(max_length=50, blank=True, verbose_name="Termékkód kategória")
    product_code_value = models.CharField(max_length=100, blank=True, verbose_name="Termékkód érték")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Számla tétel"
        verbose_name_plural = "Számla tételek"
        ordering = ['line_number']
        unique_together = ['invoice', 'line_number']
    
    def __str__(self):
        return f"{self.invoice.nav_invoice_number} - Sor {self.line_number}"


class InvoiceSyncLog(models.Model):
    """
    Audit trail for synchronization operations.
    """
    SYNC_STATUS_CHOICES = [
        ('RUNNING', 'Futás'),
        ('SUCCESS', 'Sikeres'),
        ('PARTIAL_SUCCESS', 'Részlegesen sikeres'),
        ('FAILED', 'Sikertelen'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sync_logs')
    sync_start_time = models.DateTimeField(verbose_name="Szinkronizáció kezdete")
    sync_end_time = models.DateTimeField(null=True, blank=True, verbose_name="Szinkronizáció vége")
    direction_synced = models.CharField(max_length=10, verbose_name="Szinkronizált irány")  # INBOUND, OUTBOUND, BOTH
    
    # Statistics
    invoices_processed = models.IntegerField(default=0, verbose_name="Feldolgozott számlák")
    invoices_created = models.IntegerField(default=0, verbose_name="Létrehozott számlák")
    invoices_updated = models.IntegerField(default=0, verbose_name="Frissített számlák")
    errors_count = models.IntegerField(default=0, verbose_name="Hibák száma")
    
    # Error information
    last_error_message = models.TextField(blank=True, verbose_name="Utolsó hibaüzenet")
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='RUNNING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Szinkronizáció napló"
        verbose_name_plural = "Szinkronizáció naplók"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.name} - {self.sync_start_time.strftime('%Y-%m-%d %H:%M')} ({self.sync_status})"

