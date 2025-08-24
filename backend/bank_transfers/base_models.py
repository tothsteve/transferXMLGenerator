"""
Abstract base models for common fields and functionality
"""
from django.db import models


class TimestampedModel(models.Model):
    """
    Abstract base model that provides timestamps for creation and modification
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Létrehozva")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Módosítva")
    
    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """
    Abstract base model that provides an active/inactive status field
    """
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    
    class Meta:
        abstract = True


class TimestampedActiveModel(TimestampedModel, ActiveModel):
    """
    Abstract base model that combines timestamps and active status
    """
    class Meta:
        abstract = True


class CompanyOwnedModel(models.Model):
    """
    Abstract base model for models that belong to a company
    """
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        verbose_name="Cég",
        help_text="A modell tulajdonosa"
    )
    
    class Meta:
        abstract = True


class CompanyOwnedTimestampedModel(CompanyOwnedModel, TimestampedModel):
    """
    Abstract base model that combines company ownership and timestamps
    """
    class Meta:
        abstract = True


class CompanyOwnedTimestampedActiveModel(CompanyOwnedModel, TimestampedActiveModel):
    """
    Abstract base model that combines company ownership, timestamps, and active status
    """
    class Meta:
        abstract = True