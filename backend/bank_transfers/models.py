from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from .base_models import (
    TimestampedModel, ActiveModel, TimestampedActiveModel,
    CompanyOwnedModel, CompanyOwnedTimestampedModel, CompanyOwnedTimestampedActiveModel
)

class Company(TimestampedActiveModel):
    """Cég entitás multi-tenant architektúrához"""
    name = models.CharField(max_length=200, verbose_name="Cég neve")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="Adószám")
    address = models.TextField(blank=True, verbose_name="Cím")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    
    class Meta:
        verbose_name = "Cég"
        verbose_name_plural = "Cégek"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CompanyUser(ActiveModel):
    """Felhasználó-cég kapcsolat szerepkörrel"""
    ROLE_CHOICES = [
        ('ADMIN', 'Cég adminisztrátor'),
        ('USER', 'Felhasználó'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER', verbose_name="Szerepkör")
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cég felhasználó"
        verbose_name_plural = "Cég felhasználók"
        unique_together = ['user', 'company']
        ordering = ['company__name', 'user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.company.name} ({self.role})"

class UserProfile(TimestampedModel):
    """Felhasználói profil kiegészítő adatokkal"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    preferred_language = models.CharField(max_length=10, default='hu', verbose_name="Nyelv")
    timezone = models.CharField(max_length=50, default='Europe/Budapest', verbose_name="Időzóna")
    last_active_company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, 
                                          verbose_name="Utoljára aktív cég")
    
    class Meta:
        verbose_name = "Felhasználói profil"
        verbose_name_plural = "Felhasználói profilok"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} profil"

class BankAccount(CompanyOwnedTimestampedModel):
    name = models.CharField(max_length=200, verbose_name="Számla neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    bank_name = models.CharField(max_length=200, blank=True, verbose_name="Bank neve")
    is_default = models.BooleanField(default=False, verbose_name="Alapértelmezett")
    
    class Meta:
        verbose_name = "Bank számla"
        verbose_name_plural = "Bank számlák"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"
    
    def clean_account_number(self):
        return self.account_number.replace('-', '').replace(' ', '')

class Beneficiary(CompanyOwnedTimestampedActiveModel):
    name = models.CharField(max_length=200, verbose_name="Kedvezményezett neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    description = models.CharField(max_length=200, blank=True, verbose_name="Leírás", 
                                 help_text="További információk a kedvezményezettről (bank neve, szervezet adatai, stb.)")
    is_frequent = models.BooleanField(default=False, verbose_name="Gyakori kedvezményezett")
    remittance_information = models.TextField(blank=True, verbose_name="Utalási információ",
                                            help_text="Alapértelmezett fizetési hivatkozások, számlaszámok vagy egyéb tranzakció-specifikus információk")
    
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

class TransferTemplate(CompanyOwnedTimestampedActiveModel):
    name = models.CharField(max_length=200, verbose_name="Sablon neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    
    class Meta:
        verbose_name = "Utalási sablon"
        verbose_name_plural = "Utalási sablonok"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TemplateBeneficiary(ActiveModel):
    template = models.ForeignKey(TransferTemplate, on_delete=models.CASCADE, related_name='template_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    default_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    default_remittance = models.CharField(max_length=500, blank=True)
    default_execution_date = models.DateField(null=True, blank=True, verbose_name="Alapértelmezett teljesítési dátum")
    order = models.IntegerField(default=0, verbose_name="Sorrend")
    
    class Meta:
        verbose_name = "Sablon kedvezményezett"
        verbose_name_plural = "Sablon kedvezményezettek"
        ordering = ['order', 'beneficiary__name']
        unique_together = ['template', 'beneficiary']

class Transfer(TimestampedModel):
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

class TransferBatch(CompanyOwnedTimestampedModel):
    BATCH_FORMAT_CHOICES = [
        ('XML', 'SEPA XML'),
        ('KH_CSV', 'KH Bank CSV'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Köteg neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    transfers = models.ManyToManyField(Transfer, verbose_name="Utalások")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Összeg")
    used_in_bank = models.BooleanField(default=False, verbose_name="Felhasználva a bankban", help_text="Jelzi, hogy a fájl fel lett-e töltve az internetbankba")
    bank_usage_date = models.DateTimeField(null=True, blank=True, verbose_name="Bank felhasználás dátuma")
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Kötegek sorrendje a listázáshoz és letöltéshez")
    xml_generated_at = models.DateTimeField(null=True, blank=True, verbose_name="Fájl generálás ideje")
    batch_format = models.CharField(max_length=10, choices=BATCH_FORMAT_CHOICES, default='XML', verbose_name="Fájlformátum")
    
    class Meta:
        verbose_name = "Utalási köteg"
        verbose_name_plural = "Utalási kötegek"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.transfers.count()} utalás)"
    
    @property
    def filename(self):
        """Generate filename based on batch format, name and date"""
        if self.xml_generated_at:
            date_str = self.xml_generated_at.strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in self.name if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            if self.batch_format == 'KH_CSV':
                return f"{safe_name}_{date_str}.HUF.CSV"
            else:
                return f"{safe_name}_{date_str}.xml"
        else:
            safe_name = self.name.replace(' ', '_')
            if self.batch_format == 'KH_CSV':
                return f"{safe_name}.HUF.CSV"
            else:
                return f"{safe_name}.xml"
    
    @property
    def xml_filename(self):
        """Legacy property for backwards compatibility"""
        return self.filename


# NAV Online Invoice Synchronization Models

class NavConfigurationManager(models.Manager):
    """Enhanced manager for NavConfiguration with environment-aware queries."""
    
    def for_company_and_environment(self, company, environment='production'):
        """
        Get NAV configuration for a company and specific environment.
        
        Args:
            company: Company instance or ID
            environment: 'production' or 'test'
            
        Returns:
            NavConfiguration instance or None
        """
        if isinstance(company, int):
            company_id = company
        else:
            company_id = company.id
            
        return self.filter(
            company_id=company_id,
            api_environment=environment,
            is_active=True
        ).first()
    
    def get_active_config(self, company, prefer_production=True):
        """
        Get the best available NAV configuration for a company.
        
        Args:
            company: Company instance or ID
            prefer_production: If True, prefer production over test
            
        Returns:
            NavConfiguration instance or None
            
        Logic:
        - If prefer_production=True: production first, fallback to test
        - If prefer_production=False: test first, fallback to production
        """
        primary_env = 'production' if prefer_production else 'test'
        fallback_env = 'test' if prefer_production else 'production'
        
        # Try primary environment first
        config = self.for_company_and_environment(company, primary_env)
        if config:
            return config
            
        # Fallback to secondary environment
        return self.for_company_and_environment(company, fallback_env)


class NavConfiguration(models.Model):
    """
    Company-specific NAV API credentials and synchronization settings.
    
    Production Multi-Company Architecture:
    - Each company can have MULTIPLE NAV configurations (test + production)
    - Environment selection happens at runtime via configuration lookup
    - All credentials encrypted with master key, no environment variables needed
    - Complete data isolation per company with shared application logic
    
    Usage Examples:
    - Company A: Test config only (for development/staging)
    - Company B: Production config only (live operations)
    - Company C: Both test AND production (full development lifecycle)
    """
    
    objects = NavConfigurationManager()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='nav_configs')
    
    # Company-specific NAV credentials
    tax_number = models.CharField(max_length=20, verbose_name="NAV adószám")
    technical_user_login = models.CharField(max_length=100, verbose_name="Technikai felhasználó", default='')
    technical_user_password = models.TextField(verbose_name="Technikai felhasználó jelszó", default='')  # Will be encrypted on save
    signing_key = models.TextField(verbose_name="Aláíró kulcs", default='')  # Will be encrypted on save
    exchange_key = models.TextField(verbose_name="Csere kulcs", default='')  # Will be encrypted on save
    
    # Company-specific NAV encryption key (for internal company use)
    company_encryption_key = models.TextField(verbose_name="Cég titkosítási kulcs", blank=True)  # Auto-generated and encrypted
    
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
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        
        # Check if this is a new instance or if credential fields have changed
        if self.pk is None:
            # New instance - encrypt all credential fields
            if self.technical_user_password and not self._is_encrypted(self.technical_user_password):
                self.technical_user_password = credential_manager.encrypt_credential(self.technical_user_password)
            if self.signing_key and not self._is_encrypted(self.signing_key):
                self.signing_key = credential_manager.encrypt_credential(self.signing_key)
            if self.exchange_key and not self._is_encrypted(self.exchange_key):
                self.exchange_key = credential_manager.encrypt_credential(self.exchange_key)
        else:
            # Existing instance - only encrypt if values have changed and are not already encrypted
            original = NavConfiguration.objects.get(pk=self.pk)
            
            if self.technical_user_password != original.technical_user_password and not self._is_encrypted(self.technical_user_password):
                self.technical_user_password = credential_manager.encrypt_credential(self.technical_user_password)
            if self.signing_key != original.signing_key and not self._is_encrypted(self.signing_key):
                self.signing_key = credential_manager.encrypt_credential(self.signing_key)
            if self.exchange_key != original.exchange_key and not self._is_encrypted(self.exchange_key):
                self.exchange_key = credential_manager.encrypt_credential(self.exchange_key)
        
        # Auto-generate company encryption key if not exists
        if not self.company_encryption_key:
            company_key = credential_manager.generate_company_encryption_key()
            self.company_encryption_key = credential_manager.encrypt_credential(company_key)
        
        super().save(*args, **kwargs)
    
    def _is_encrypted(self, value):
        """Check if a value is already encrypted (simple heuristic)"""
        if not value:
            return True
        # Encrypted values are typically base64-encoded and much longer
        return len(value) > 100 and '=' in value
    
    def get_decrypted_password(self):
        """Get decrypted technical user password"""
        if not self.technical_user_password:
            return ""
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        return credential_manager.decrypt_credential(self.technical_user_password)
    
    def get_decrypted_signing_key(self):
        """Get decrypted signing key"""
        if not self.signing_key:
            return ""
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        return credential_manager.decrypt_credential(self.signing_key)
    
    def get_decrypted_exchange_key(self):
        """Get decrypted exchange key"""
        if not self.exchange_key:
            return ""
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        return credential_manager.decrypt_credential(self.exchange_key)
    


class Invoice(TimestampedModel):
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
    
    # Additional NAV business fields
    invoice_operation = models.CharField(max_length=20, null=True, blank=True, verbose_name="Számla művelet (CREATE/STORNO/MODIFY)")
    invoice_category = models.CharField(max_length=20, null=True, blank=True, verbose_name="Számla kategória (NORMAL/SIMPLIFIED)")
    payment_method = models.CharField(max_length=20, null=True, blank=True, verbose_name="Fizetési mód (TRANSFER/CASH/CARD)")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Fizetési dátum")
    invoice_appearance = models.CharField(max_length=20, null=True, blank=True, verbose_name="Számla megjelenés (PAPER/ELECTRONIC)")
    nav_source = models.CharField(max_length=10, null=True, blank=True, verbose_name="NAV forrás (OSZ/XML)")
    completeness_indicator = models.BooleanField(null=True, blank=True, verbose_name="Teljesség jelző")
    modification_index = models.IntegerField(null=True, blank=True, verbose_name="Módosítási index")
    original_invoice_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Eredeti számla száma (storno esetén)")
    
    # STORNO relationship - ForeignKey to the original invoice that this STORNO cancels
    storno_of = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='storno_invoices',
        verbose_name="Eredeti számla (amit ez a storno érvénytelenít)",
        help_text="A STORNO számla által érvénytelenített eredeti számla"
    )
    
    invoice_index = models.IntegerField(null=True, blank=True, verbose_name="Számla index")
    batch_index = models.IntegerField(null=True, blank=True, verbose_name="Köteg index")
    nav_creation_date = models.DateTimeField(null=True, blank=True, verbose_name="NAV létrehozási dátum")
    
    # HUF amounts for foreign currency invoices
    invoice_net_amount_huf = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Nettó összeg (HUF)")
    invoice_vat_amount_huf = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="ÁFA összeg (HUF)")
    invoice_gross_amount_huf = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Bruttó összeg (HUF)")
    
    # XML Data Storage
    nav_invoice_xml = models.TextField(null=True, blank=True, verbose_name="NAV számla XML")
    nav_invoice_hash = models.CharField(max_length=200, null=True, blank=True, verbose_name="NAV számla hash")
    
    # Sync metadata
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES, default='SUCCESS')
    
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
    
    @property
    def is_active(self):
        """
        Invoice is active if:
        1. It's not a STORNO invoice itself
        2. It hasn't been canceled by a STORNO invoice
        """
        if self.invoice_operation == 'STORNO':
            return False
        
        # Check if this invoice has been storno'd
        return not self.storno_invoices.exists()
    
    def __str__(self):
        return f"{self.nav_invoice_number} - {self.supplier_name} ({self.invoice_direction})"


class InvoiceLineItem(TimestampedModel):
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
    
    class Meta:
        verbose_name = "Számla tétel"
        verbose_name_plural = "Számla tételek"
        ordering = ['line_number']
        unique_together = ['invoice', 'line_number']
    
    def __str__(self):
        return f"{self.invoice.nav_invoice_number} - Sor {self.line_number}"


class InvoiceSyncLog(TimestampedModel):
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
    
    class Meta:
        verbose_name = "Szinkronizáció napló"
        verbose_name_plural = "Szinkronizáció naplók"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.name} - {self.sync_start_time.strftime('%Y-%m-%d %H:%M')} ({self.sync_status})"

