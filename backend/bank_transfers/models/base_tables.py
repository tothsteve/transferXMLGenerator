"""
Base tables models.

This module contains models for base reference data including suppliers,
customers, and product pricing data imported from CSV files.
"""
from django.db import models
from datetime import date
from ..base_models import CompanyOwnedTimestampedModel


class SupplierCategory(CompanyOwnedTimestampedModel):
    """
    Beszállító kategória (Supplier Category) alaptábla - cost categories for suppliers.
    Multi-tenant isolated.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Kategória neve",
        help_text="Cost category name"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="Megjelenítési sorrend",
        help_text="Display order (lower numbers appear first)"
    )

    class Meta:
        verbose_name = "Beszállító kategória"
        verbose_name_plural = "Beszállító kategóriák"
        ordering = ['display_order', 'name']
        unique_together = [['company', 'name']]
        indexes = [
            models.Index(fields=['company', 'display_order']),
        ]

    def __str__(self):
        return self.name


class SupplierType(CompanyOwnedTimestampedModel):
    """
    Beszállító típus (Supplier Type) alaptábla - cost subcategories for suppliers.
    Multi-tenant isolated.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Típus neve",
        help_text="Cost subcategory name"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="Megjelenítési sorrend",
        help_text="Display order (lower numbers appear first)"
    )

    class Meta:
        verbose_name = "Beszállító típus"
        verbose_name_plural = "Beszállító típusok"
        ordering = ['display_order', 'name']
        unique_together = [['company', 'name']]
        indexes = [
            models.Index(fields=['company', 'display_order']),
        ]

    def __str__(self):
        return self.name


class Supplier(CompanyOwnedTimestampedModel):
    """
    Beszállító (Supplier) alaptábla - partner adatok kategóriával és típussal.
    Multi-tenant isolated, validity period managed.
    """
    partner_name = models.CharField(
        max_length=255,
        verbose_name="Partner neve"
    )
    category = models.ForeignKey(
        SupplierCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategória",
        help_text="Cost category",
        related_name='suppliers'
    )
    type = models.ForeignKey(
        SupplierType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Típus",
        help_text="Cost subcategory",
        related_name='suppliers'
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség kezdete",
        help_text="Start date of validity period"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség vége",
        help_text="End date of validity period (null = no expiry)"
    )

    class Meta:
        verbose_name = "Beszállító"
        verbose_name_plural = "Beszállítók"
        ordering = ['-id']
        indexes = [
            models.Index(fields=['company', 'valid_from', 'valid_to']),
            models.Index(fields=['partner_name']),
        ]

    def __str__(self):
        return self.partner_name

    def is_valid(self):
        """
        Check if this supplier record is currently valid.
        Valid means: today >= valid_from AND (valid_to is null OR today <= valid_to)
        """
        today = date.today()

        # If valid_from is set and today is before it, not valid
        if self.valid_from and today < self.valid_from:
            return False

        # If valid_to is set and today is after it, not valid
        if self.valid_to and today > self.valid_to:
            return False

        # Otherwise, it's valid
        return True


class Customer(CompanyOwnedTimestampedModel):
    """
    Vevő (Customer) alaptábla - customer data with cashflow adjustment.
    Multi-tenant isolated, validity period managed.
    """
    customer_name = models.CharField(
        max_length=255,
        verbose_name="Vevő neve"
    )
    cashflow_adjustment = models.IntegerField(
        default=0,
        verbose_name="Cashflow kiigazítás (nap)",
        help_text="Number of days to adjust cashflow calculations (can be negative)"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség kezdete",
        help_text="Start date of validity period"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség vége",
        help_text="End date of validity period (null = no expiry)"
    )

    class Meta:
        verbose_name = "Vevő"
        verbose_name_plural = "Vevők"
        ordering = ['-id']
        indexes = [
            models.Index(fields=['company', 'valid_from', 'valid_to']),
            models.Index(fields=['customer_name']),
        ]

    def __str__(self):
        return self.customer_name

    def is_valid(self):
        """
        Check if this customer record is currently valid.
        Valid means: today >= valid_from AND (valid_to is null OR today <= valid_to)
        """
        today = date.today()

        # If valid_from is set and today is before it, not valid
        if self.valid_from and today < self.valid_from:
            return False

        # If valid_to is set and today is after it, not valid
        if self.valid_to and today > self.valid_to:
            return False

        # Otherwise, it's valid
        return True


class ProductPrice(CompanyOwnedTimestampedModel):
    """
    CONMED árak (Product Pricing) alaptábla - product pricing data with USD/HUF prices and markup.
    Multi-tenant isolated, validity period managed.
    """
    product_value = models.CharField(
        max_length=50,
        verbose_name="Termék kód",
        help_text="Product code/identifier"
    )
    product_description = models.CharField(
        max_length=500,
        verbose_name="Termék leírás",
        help_text="Product description"
    )
    uom = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="UOM (EN)",
        help_text="Unit of measure in English (e.g., 'EA')"
    )
    uom_hun = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="UOM (HU)",
        help_text="Unit of measure in Hungarian (e.g., 'db')"
    )
    purchase_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Beszerzési ár USD",
        help_text="Purchase price in USD"
    )
    purchase_price_huf = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Beszerzési ár HUF",
        help_text="Purchase price in HUF"
    )
    markup = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Markup (%)",
        help_text="Markup percentage"
    )
    sales_price_huf = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Eladási ár HUF",
        help_text="Sales price in HUF"
    )
    cap_disp = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cap/Disp",
        help_text="Capital or Disposable classification"
    )
    is_inventory_managed = models.BooleanField(
        default=False,
        verbose_name="Készletkezelt termék",
        help_text="Whether this product is inventory-managed (Készletkezelt termék = 'y')"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség kezdete",
        help_text="Start date of validity period"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség vége",
        help_text="End date of validity period (null = no expiry)"
    )

    class Meta:
        verbose_name = "CONMED ár"
        verbose_name_plural = "CONMED árak"
        ordering = ['-id']
        indexes = [
            models.Index(fields=['company', 'valid_from', 'valid_to']),
            models.Index(fields=['product_value']),
            models.Index(fields=['company', 'product_value']),
        ]

    def __str__(self):
        return f"{self.product_value} - {self.product_description[:50]}"

    def is_valid(self):
        """
        Check if this product price record is currently valid.
        Valid means: today >= valid_from AND (valid_to is null OR today <= valid_to)
        """
        today = date.today()

        # If valid_from is set and today is before it, not valid
        if self.valid_from and today < self.valid_from:
            return False

        # If valid_to is set and today is after it, not valid
        if self.valid_to and today > self.valid_to:
            return False

        # Otherwise, it's valid
        return True

