"""
Exchange rate models.

This module contains models for MNB (Magyar Nemzeti Bank) exchange rate
synchronization and currency conversion tracking.
"""
from django.db import models
from ..base_models import TimestampedModel
from .company import Company


class ExchangeRate(TimestampedModel):
    """
    MNB (Magyar Nemzeti Bank) official exchange rates for foreign currencies to HUF.
    Supports historical data and multiple daily synchronizations.

    The MNB publishes official exchange rates daily, typically updated around 11:45 AM.
    This model stores historical rates for accurate currency conversions.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    rate_date = models.DateField(verbose_name="Árfolyam dátuma", db_index=True)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        verbose_name="Deviza kód",
        help_text="Currency code (USD or EUR)"
    )
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        verbose_name="Árfolyam (HUF)",
        help_text="Exchange rate: 1 unit of currency = X HUF"
    )
    unit = models.IntegerField(
        default=1,
        verbose_name="Egység",
        help_text="Number of currency units this rate applies to (typically 1)"
    )

    # Sync metadata
    sync_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Szinkronizálva",
        help_text="When this rate was fetched from MNB"
    )
    source = models.CharField(
        max_length=20,
        default='MNB',
        verbose_name="Forrás",
        help_text="Data source (always MNB for official rates)"
    )

    class Meta:
        verbose_name = "Árfolyam"
        verbose_name_plural = "Árfolyamok"
        ordering = ['-rate_date', 'currency']
        unique_together = ['rate_date', 'currency']
        indexes = [
            models.Index(fields=['rate_date', 'currency']),
            models.Index(fields=['-rate_date']),
            models.Index(fields=['currency']),
        ]

    def __str__(self):
        return f"{self.currency} - {self.rate_date}: {self.rate:.4f} HUF"

    def convert_to_huf(self, amount):
        """
        Convert foreign currency amount to HUF using this exchange rate.

        Args:
            amount: Decimal amount in foreign currency

        Returns:
            Decimal amount in HUF
        """
        from decimal import Decimal
        return (Decimal(str(amount)) * self.rate) / self.unit


class ExchangeRateSyncLog(TimestampedModel):
    """
    Audit trail for MNB exchange rate synchronization operations.
    Tracks success, failures, and statistics for each sync run.
    """
    SYNC_STATUS_CHOICES = [
        ('RUNNING', 'Futás'),
        ('SUCCESS', 'Sikeres'),
        ('PARTIAL_SUCCESS', 'Részlegesen sikeres'),
        ('FAILED', 'Sikertelen'),
    ]

    sync_start_time = models.DateTimeField(verbose_name="Szinkronizáció kezdete")
    sync_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Szinkronizáció vége"
    )

    # Sync parameters
    currencies_synced = models.CharField(
        max_length=50,
        verbose_name="Szinkronizált devizák",
        help_text="Comma-separated currency codes (e.g., 'USD,EUR')"
    )
    date_range_start = models.DateField(verbose_name="Dátum tartomány kezdete")
    date_range_end = models.DateField(verbose_name="Dátum tartomány vége")

    # Statistics
    rates_created = models.IntegerField(
        default=0,
        verbose_name="Létrehozott árfolyamok",
        help_text="Number of new exchange rates created"
    )
    rates_updated = models.IntegerField(
        default=0,
        verbose_name="Frissített árfolyamok",
        help_text="Number of existing exchange rates updated"
    )

    # Status and errors
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='RUNNING',
        verbose_name="Szinkronizáció státusza"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Hibaüzenet",
        help_text="Error details if sync failed"
    )

    class Meta:
        verbose_name = "Árfolyam szinkronizáció napló"
        verbose_name_plural = "Árfolyam szinkronizáció naplók"
        ordering = ['-sync_start_time']
        indexes = [
            models.Index(fields=['-sync_start_time']),
            models.Index(fields=['sync_status']),
        ]

    def __str__(self):
        return f"MNB Sync - {self.sync_start_time.strftime('%Y-%m-%d %H:%M')} ({self.sync_status})"

    @property
    def duration_seconds(self):
        """Calculate sync duration in seconds"""
        if self.sync_end_time:
            delta = self.sync_end_time - self.sync_start_time
            return delta.total_seconds()
        return None

    @property
    def total_rates_processed(self):
        """Total number of rates processed (created + updated)"""
        return self.rates_created + self.rates_updated


# =============================================================================
# Bank Statement Import Models
# =============================================================================

