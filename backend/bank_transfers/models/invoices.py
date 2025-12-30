"""
NAV invoice integration models.

This module contains models for NAV API configuration, invoice synchronization,
trusted partners, and invoice-transaction matching for automatic payment tracking.
"""
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from ..base_models import TimestampedModel
from .company import Company


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
    
    # Payment status tracking fields
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Fizetésre vár'),
        ('PREPARED', 'Előkészítve'),
        ('PAID', 'Kifizetve'),
    ]
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='UNPAID',
        verbose_name="Fizetési állapot",
        help_text="A számla aktuális fizetési státusza"
    )
    payment_status_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Fizetési állapot dátuma",
        help_text="A számla kifizetésének dátuma (PAID státusz esetén)"
    )
    auto_marked_paid = models.BooleanField(
        default=False,
        verbose_name="Automatikusan jelölve",
        help_text="Igaz, ha automatikusan lett megjelölve fizetettként köteg feldolgozáskor"
    )
    
    # Bank account information (extracted from XML)
    supplier_bank_account_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Szállító bankszámlaszáma")
    customer_bank_account_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Vevő bankszámlaszáma")
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
    
    # Payment tracking
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Fizetésre vár'),
        ('PREPARED', 'Előkészítve'),
        ('PAID', 'Kifizetve'),
    ]
    payment_status = models.CharField(
        max_length=10, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='UNPAID', 
        verbose_name="Fizetési állapot"
    )
    
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
    
    @property
    def is_paid(self):
        """
        Returns True if the invoice is marked as paid.
        """
        return self.payment_status == 'PAID'

    def mark_as_paid(self, payment_date=None, auto_marked=False):
        """Mark invoice as paid"""
        from django.utils import timezone
        self.payment_status = 'PAID'
        self.payment_status_date = payment_date or timezone.now().date()
        self.auto_marked_paid = auto_marked
        self.save()
    
    def mark_as_prepared(self, prepared_date=None):
        """Mark invoice as prepared (transfer created)"""
        from django.utils import timezone
        self.payment_status = 'PREPARED'
        self.payment_status_date = prepared_date or timezone.now().date()
        self.auto_marked_paid = False
        self.save()
        
    def mark_as_unpaid(self):
        """Mark invoice as unpaid (undo payment)"""
        self.payment_status = 'UNPAID'
        self.payment_status_date = None
        self.auto_marked_paid = False
        self.save()
    
    def is_overdue(self):
        """Check if invoice is overdue (unpaid and past due date)"""
        if self.payment_status != 'UNPAID':
            return False
        
        if not self.payment_due_date:
            return False
            
        from django.utils import timezone
        today = timezone.now().date()
        return self.payment_due_date < today
    
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


class BankTransactionInvoiceMatch(models.Model):
    """
    Intermediate model for ManyToMany relationship between BankTransaction and Invoice.

    Stores per-invoice match metadata (confidence, method, notes) for both single
    and batch invoice matching. Replaces the deprecated matched_invoice ForeignKey.

    Business Logic:
    - Used for BOTH single and batch invoice matching
    - match_method = 'BATCH_INVOICES' for automatic batch matches
    - match_method = 'MANUAL_BATCH' for user-created batch matches
    - match_confidence = 1.00 for all manual matches

    Performance:
    - Unique index on (transaction, invoice) prevents duplicate matches
    - Index on invoice_id for reverse lookups (all transactions for an invoice)
    """
    transaction = models.ForeignKey(
        'BankTransaction',
        on_delete=models.CASCADE,
        related_name='invoice_matches',
        verbose_name='Bank tranzakció',
        help_text='The bank transaction that was matched'
    )
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='transaction_matches',
        verbose_name='NAV számla',
        help_text='The NAV invoice that was matched'
    )
    match_confidence = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Párosítás megbízhatósága',
        help_text='Match confidence score (0.00-1.00)'
    )
    match_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Párosítási módszer',
        help_text='Matching method used (BATCH_INVOICES, MANUAL_BATCH, etc.)',
        choices=[
            ('REFERENCE_EXACT', 'Reference Exact Match'),
            ('AMOUNT_IBAN', 'Amount + IBAN Match'),
            ('BATCH_INVOICES', 'Batch Invoice Match'),
            ('FUZZY_NAME', 'Fuzzy Name Match'),
            ('AMOUNT_DATE_ONLY', 'Amount + Date Only'),
            ('MANUAL', 'Manual Single Match'),
            ('MANUAL_BATCH', 'Manual Batch Match'),
        ]
    )
    matched_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Párosítás időpontja',
        help_text='When the match was created'
    )
    matched_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Párosította',
        help_text='User who created manual match (NULL for automatic)'
    )
    match_notes = models.TextField(
        blank=True,
        verbose_name='Párosítási megjegyzések',
        help_text='Detailed match information for audit trail'
    )

    class Meta:
        db_table = 'bank_transfers_banktransactioninvoicematch'
        verbose_name = 'Tranzakció-számla párosítás'
        verbose_name_plural = 'Tranzakció-számla párosítások'
        unique_together = [['transaction', 'invoice']]
        indexes = [
            models.Index(fields=['transaction', 'invoice'], name='idx_tx_invoice_match'),
            models.Index(fields=['invoice'], name='idx_invoice_matches'),
        ]
        ordering = ['transaction', 'invoice']

    def __str__(self):
        return f"Transaction {self.transaction.id} → Invoice {self.invoice.nav_invoice_number} ({self.match_confidence})"


# Company Feature Management Models

class TrustedPartner(TimestampedModel):
    """
    Trusted partners for automatic payment processing.
    When invoices are received from these partners, they are automatically marked as PAID.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='trusted_partners')
    partner_name = models.CharField(max_length=200, verbose_name="Partner neve")
    tax_number = models.CharField(max_length=20, verbose_name="Adószám")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    auto_pay = models.BooleanField(default=True, verbose_name="Automatikus fizetés")
    notes = models.TextField(blank=True, verbose_name="Megjegyzések")
    
    # Statistics
    invoice_count = models.IntegerField(default=0, verbose_name="Számlák száma")
    last_invoice_date = models.DateField(null=True, blank=True, verbose_name="Utolsó számla dátuma")
    
    class Meta:
        verbose_name = "Megbízható partner"
        verbose_name_plural = "Megbízható partnerek"
        ordering = ['partner_name']
        unique_together = ['company', 'tax_number']
        indexes = [
            models.Index(fields=['company', 'tax_number']),
            models.Index(fields=['is_active', 'auto_pay']),
        ]
    
    def __str__(self):
        return f"{self.partner_name} ({self.tax_number})"
    
    def update_statistics(self):
        """Update invoice count and last invoice date from NAV invoices"""
        from django.db.models import Count, Max
        
        # Count invoices from this partner
        stats = Invoice.objects.filter(
            company=self.company,
            supplier_tax_number=self.tax_number
        ).aggregate(
            count=Count('id'),
            last_date=Max('issue_date')
        )
        
        self.invoice_count = stats['count'] or 0
        self.last_invoice_date = stats['last_date']
        self.save(update_fields=['invoice_count', 'last_invoice_date'])


# MNB Exchange Rate Models
