"""
Billingo integration models.

This module contains models for Billingo accounting system integration,
including invoice synchronization, spending tracking, and document management.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from ..base_models import TimestampedModel
from .company import Company


class CompanyBillingoSettings(TimestampedModel):
    """
    Billingo API configuration for invoice synchronization.
    One configuration per company (company-scoped).
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_settings',
        verbose_name="Cég"
    )
    api_key = models.CharField(
        max_length=255,
        verbose_name="API kulcs (titkosított)",
        help_text="Titkosított Billingo API kulcs (X-API-KEY header)"
    )
    last_sync_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Utolsó szinkronizálás",
        help_text="Utolsó sikeres szinkronizálás időpontja"
    )
    last_billingo_invoice_sync_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Utolsó Billingo számla szinkronizálás dátuma",
        help_text="Az utolsó szinkronizált Billingo számla módosítási dátuma (Billingo API last_modified_date filter)"
    )
    last_billingo_spending_sync_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Utolsó Billingo költség szinkronizálás dátuma",
        help_text="Az utolsó szinkronizált Billingo költség módosítási dátuma"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktív",
        help_text="Engedélyezi/tiltja a szinkronizálást ennél a cégnél"
    )

    class Meta:
        verbose_name = "Billingo beállítás"
        verbose_name_plural = "Billingo beállítások"
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company'],
                name='unique_billingo_settings_per_company'
            )
        ]

    def __str__(self):
        return f"Billingo beállítások - {self.company.name}"


class BillingoInvoice(TimestampedModel):
    """
    Billingo invoice/document record from /documents API endpoint.
    Company-scoped for multi-tenant isolation.
    """
    # Billingo ID is the primary key (BigInteger from API response)
    id = models.BigIntegerField(primary_key=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_invoices',
        verbose_name="Cég"
    )

    # Invoice identification
    invoice_number = models.CharField(
        max_length=50,
        verbose_name="Számlaszám"
    )
    type = models.CharField(
        max_length=30,
        verbose_name="Típus",
        help_text="invoice, receipt, proforma, stb."
    )
    correction_type = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Helyesbítés típusa"
    )
    cancelled = models.BooleanField(
        default=False,
        verbose_name="Sztornózott"
    )
    block_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Billingo blokk ID"
    )

    # Payment information
    payment_status = models.CharField(
        max_length=30,
        verbose_name="Fizetési státusz",
        help_text="paid, unpaid, overdue, stb."
    )
    payment_method = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Fizetési mód",
        help_text="wire_transfer, cash, stb."
    )

    # Financial data
    gross_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg"
    )
    net_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Nettó összeg"
    )
    currency = models.CharField(
        max_length=5,
        verbose_name="Deviza"
    )
    conversion_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1,
        verbose_name="Átváltási árfolyam"
    )

    # Dates
    invoice_date = models.DateField(
        verbose_name="Számla kelte"
    )
    fulfillment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Teljesítés dátuma"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fizetési határidő"
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Kiegyenlítés dátuma"
    )

    # Organization (our company information from Billingo)
    organization_name = models.CharField(
        max_length=255,
        verbose_name="Saját cég neve"
    )
    organization_tax_number = models.CharField(
        max_length=50,
        verbose_name="Saját adószám"
    )
    organization_bank_account_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Saját bankszámlaszám"
    )
    organization_bank_account_iban = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Saját IBAN"
    )
    organization_swift = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Saját SWIFT/BIC"
    )

    # Partner (customer/supplier information)
    partner_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Partner Billingo ID"
    )
    partner_name = models.CharField(
        max_length=255,
        verbose_name="Partner neve"
    )
    partner_tax_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Partner adószáma"
    )
    partner_iban = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Partner IBAN"
    )
    partner_swift = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Partner SWIFT/BIC"
    )
    partner_account_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Partner számlaszáma"
    )

    # Additional metadata
    comment = models.TextField(
        blank=True,
        verbose_name="Megjegyzés"
    )
    online_szamla_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Online Számla státusz"
    )

    # Audit fields (last_modified in addition to created_at/updated_at from TimestampedModel)
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name="Utoljára módosítva"
    )

    class Meta:
        verbose_name = "Billingo számla"
        verbose_name_plural = "Billingo számlák"
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['company', 'invoice_date']),
            models.Index(fields=['company', 'payment_status']),
            models.Index(fields=['company', 'partner_tax_number']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.partner_name}"


class BillingoRelatedDocument(TimestampedModel):
    """
    Related documents for Billingo invoices (corrections, credit notes, etc.).
    Stores document relationships from the Billingo API related_documents array.
    """
    invoice = models.ForeignKey(
        BillingoInvoice,
        on_delete=models.CASCADE,
        related_name='related_documents',
        verbose_name="Számla"
    )
    related_invoice_id = models.BigIntegerField(
        verbose_name="Kapcsolódó számla ID",
        help_text="Billingo invoice ID of the related document"
    )
    related_invoice_number = models.CharField(
        max_length=100,
        verbose_name="Kapcsolódó számlaszám",
        help_text="Invoice number of the related document"
    )

    class Meta:
        verbose_name = "Kapcsolódó Billingo dokumentum"
        verbose_name_plural = "Kapcsolódó Billingo dokumentumok"
        ordering = ['related_invoice_number']
        indexes = [
            models.Index(fields=['invoice', 'related_invoice_id']),
            models.Index(fields=['related_invoice_id']),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} → {self.related_invoice_number}"


class BillingoInvoiceItem(TimestampedModel):
    """
    Line items for Billingo invoices.
    Represents individual products/services on the invoice.
    """
    invoice = models.ForeignKey(
        BillingoInvoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Számla"
    )
    product_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Termék ID"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Megnevezés"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Mennyiség"
    )
    unit = models.CharField(
        max_length=20,
        verbose_name="Mértékegység",
        help_text="PIECE, HOUR, LITER, stb."
    )
    net_unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Nettó egységár"
    )
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Nettó összeg"
    )
    gross_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg"
    )
    vat = models.CharField(
        max_length=10,
        verbose_name="ÁFA kulcs",
        help_text="27%, 5%, 0%, stb."
    )
    entitlement = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ÁFA jogcím"
    )

    class Meta:
        verbose_name = "Billingo számla tétel"
        verbose_name_plural = "Billingo számla tételek"
        ordering = ['invoice', 'id']
        indexes = [
            models.Index(fields=['invoice']),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.name}"


class BillingoSyncLog(TimestampedModel):
    """
    Audit log for Billingo invoice synchronization operations.
    """
    STATUS_CHOICES = [
        ('RUNNING', 'Fut'),
        ('COMPLETED', 'Befejezve'),
        ('FAILED', 'Sikertelen'),
        ('PARTIAL', 'Részben sikeres'),
    ]

    SYNC_TYPE_CHOICES = [
        ('MANUAL', 'Kézi'),
        ('AUTOMATIC', 'Automatikus'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_sync_logs',
        verbose_name="Cég"
    )
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        verbose_name="Szinkronizálás típusa"
    )

    # Sync metrics
    invoices_processed = models.IntegerField(
        default=0,
        verbose_name="Feldolgozott számlák"
    )
    invoices_created = models.IntegerField(
        default=0,
        verbose_name="Létrehozott számlák"
    )
    invoices_updated = models.IntegerField(
        default=0,
        verbose_name="Frissített számlák"
    )
    invoices_skipped = models.IntegerField(
        default=0,
        verbose_name="Kihagyott számlák"
    )
    items_extracted = models.IntegerField(
        default=0,
        verbose_name="Kivont tételek száma"
    )

    # Performance metrics
    sync_duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Szinkronizálás időtartama (mp)"
    )
    api_calls_made = models.IntegerField(
        default=0,
        verbose_name="API hívások száma"
    )

    # Error tracking
    errors = models.TextField(
        blank=True,
        verbose_name="Hibák (JSON)",
        help_text="JSON array of errors"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='RUNNING',
        verbose_name="Státusz"
    )

    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Indítva"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Befejezve"
    )

    class Meta:
        verbose_name = "Billingo szinkronizálási napló"
        verbose_name_plural = "Billingo szinkronizálási naplók"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['company', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['sync_type']),
        ]

    def __str__(self):
        return f"Billingo szinkronizálás - {self.company.name} - {self.started_at}"


class BillingoSpending(TimestampedModel):
    """
    Billingo spending record from /spendings API endpoint.
    Company-scoped for multi-tenant isolation.
    Represents expenses/costs from suppliers.
    """
    # Billingo ID is the primary key (BigInteger from API response)
    id = models.BigIntegerField(primary_key=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_spendings',
        verbose_name="Cég"
    )

    organization_id = models.IntegerField(
        verbose_name="Billingo szervezet ID"
    )

    # Spending category
    CATEGORY_CHOICES = [
        ('advertisement', 'Hirdetés'),
        ('development', 'Fejlesztés'),
        ('education_and_training', 'Oktatás és képzés'),
        ('other', 'Egyéb'),
        ('overheads', 'Rezsiköltség'),
        ('service', 'Szolgáltatás'),
        ('stock', 'Készlet'),
        ('tangible_assets', 'Tárgyi eszköz'),
    ]
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        verbose_name="Kategória"
    )

    # Payment tracking
    paid_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Kiegyenlítés dátuma"
    )

    # Financial data
    fulfillment_date = models.DateField(
        verbose_name="Teljesítés dátuma"
    )
    invoice_number = models.CharField(
        max_length=100,
        verbose_name="Számla/Bizonylat száma"
    )
    currency = models.CharField(
        max_length=3,
        default='HUF',
        verbose_name="Deviza"
    )
    conversion_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1,
        verbose_name="Átváltási árfolyam"
    )
    total_gross = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg"
    )
    total_gross_local = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg (HUF)"
    )
    total_vat_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="ÁFA összeg"
    )
    total_vat_amount_local = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="ÁFA összeg (HUF)"
    )

    # Dates
    invoice_date = models.DateField(
        verbose_name="Számla kelte"
    )
    due_date = models.DateField(
        verbose_name="Fizetési határidő"
    )

    # Payment method
    payment_method = models.CharField(
        max_length=30,
        verbose_name="Fizetési mód",
        help_text="wire_transfer, cash, card, stb."
    )

    # Partner information
    partner_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Partner ID"
    )
    partner_name = models.CharField(
        max_length=255,
        verbose_name="Partner neve"
    )
    partner_tax_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Partner adószáma"
    )
    partner_address = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Partner címe",
        help_text="Full address object from API"
    )
    partner_iban = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Partner IBAN"
    )
    partner_account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Partner bankszámla"
    )

    # Additional information
    comment = models.TextField(
        blank=True,
        verbose_name="Megjegyzés"
    )
    is_created_by_nav = models.BooleanField(
        default=False,
        verbose_name="NAV által létrehozva",
        help_text="True if spending was created from NAV import"
    )

    class Meta:
        verbose_name = "Billingo költség"
        verbose_name_plural = "Billingo költségek"
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['company', 'invoice_date']),
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'paid_at']),
            models.Index(fields=['partner_tax_code']),
            models.Index(fields=['invoice_number']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.partner_name} ({self.total_gross_local} HUF)"

    @property
    def is_paid(self):
        """Check if spending has been paid"""
        return self.paid_at is not None


# BASE Tables (Alaptáblák) - Master Data Management

