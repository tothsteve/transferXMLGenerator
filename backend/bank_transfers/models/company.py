"""
Company and user management models.

This module contains models for multi-tenant company architecture,
user-company relationships with role-based permissions, and feature management.
"""
from django.db import models
from django.contrib.auth.models import User
from ..base_models import TimestampedModel, ActiveModel, TimestampedActiveModel


class Company(TimestampedActiveModel):
    """Cég entitás multi-tenant architektúrához"""
    name = models.CharField(max_length=200, verbose_name="Cég neve")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="Adószám")

    class Meta:
        verbose_name = "Cég"
        verbose_name_plural = "Cégek"
        ordering = ['name']

    def __str__(self):
        return self.name


class CompanyUser(ActiveModel):
    """
    Felhasználó-cég kapcsolat szerepkörrel és feature-alapú jogosultságokkal.
    Combines user roles with feature-level permissions for granular access control.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Cég adminisztrátor'),
        ('FINANCIAL', 'Pénzügyi munkatárs'),
        ('ACCOUNTANT', 'Könyvelő'),
        ('USER', 'Alapfelhasználó'),
    ]

    # Define role-based feature permissions
    ROLE_PERMISSIONS = {
        'ADMIN': ['*'],  # All features - admin has unrestricted access
        'FINANCIAL': [
            'BENEFICIARY_MANAGEMENT',
            'TRANSFER_MANAGEMENT',
            'BATCH_MANAGEMENT',
            'EXPORT_XML_SEPA',
            'EXPORT_CSV_KH',
            'EXPENSE_TRACKING',
        ],
        'ACCOUNTANT': [
            'NAV_SYNC',
            'INVOICE_MANAGEMENT',
            'EXPENSE_TRACKING',
            'REPORTING',
            'BENEFICIARY_MANAGEMENT',
            'TRANSFER_MANAGEMENT',
            'MULTI_CURRENCY',
        ],
        'USER': [
            'BENEFICIARY_VIEW',
            'TRANSFER_VIEW',
            'BATCH_VIEW',
        ],
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='USER', verbose_name="Szerepkör")
    joined_at = models.DateTimeField(auto_now_add=True)

    # Additional permission fields
    custom_permissions = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Egyedi jogosultságok",
        help_text="JSON array of additional feature codes this user can access beyond their role"
    )
    permission_restrictions = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Jogosultság korlátozások",
        help_text="JSON array of feature codes this user is explicitly denied access to"
    )

    class Meta:
        verbose_name = "Cég felhasználó"
        verbose_name_plural = "Cég felhasználók"
        unique_together = ['user', 'company']
        ordering = ['company__name', 'user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['company', 'role']),
            models.Index(fields=['user', 'company']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.company.name} ({self.role})"

    def get_allowed_features(self):
        """
        Get all feature codes this user is allowed to access.
        Combines role permissions with custom permissions and restrictions.
        """
        # Start with role-based permissions
        role_perms = self.ROLE_PERMISSIONS.get(self.role, [])

        # Admin gets everything
        if '*' in role_perms:
            return ['*']

        allowed_features = set(role_perms)

        # Add custom permissions
        if self.custom_permissions:
            allowed_features.update(self.custom_permissions)

        # Remove explicit restrictions
        if self.permission_restrictions:
            allowed_features -= set(self.permission_restrictions)

        return list(allowed_features)

    def can_access_feature(self, feature_code):
        """
        Check if this user can access a specific feature.

        Args:
            feature_code: String feature code to check

        Returns:
            Boolean indicating access permission
        """
        allowed_features = self.get_allowed_features()

        # Admin access
        if '*' in allowed_features:
            return True

        # Direct feature access
        if feature_code in allowed_features:
            return True

        # Check for wildcard permissions (e.g., 'EXPORT_*' for all export features)
        for perm in allowed_features:
            if perm.endswith('*') and feature_code.startswith(perm[:-1]):
                return True

        return False


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


class FeatureTemplate(TimestampedModel):
    """
    Template definitions for available features that can be enabled per company.
    Defines the catalog of features available across the system.
    """
    FEATURE_CATEGORIES = [
        ('EXPORT', 'Export Features'),
        ('SYNC', 'Synchronization Features'),
        ('TRACKING', 'Tracking & Management Features'),
        ('REPORTING', 'Reporting Features'),
        ('INTEGRATION', 'Integration Features'),
        ('GENERAL', 'General Features'),
    ]

    feature_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Feature kód",
        help_text="Unique identifier for the feature (e.g., 'EXPORT_XML_SEPA')"
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name="Megjelenített név",
        help_text="Human-readable name shown in UI"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Leírás",
        help_text="Detailed description of what this feature enables"
    )
    category = models.CharField(
        max_length=20,
        choices=FEATURE_CATEGORIES,
        default='GENERAL',
        verbose_name="Kategória"
    )
    default_enabled = models.BooleanField(
        default=False,
        verbose_name="Alapértelmezetten engedélyezett",
        help_text="Whether this feature should be enabled for new companies"
    )
    config_schema = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Konfigurációs séma",
        help_text="JSON schema for feature-specific configuration validation"
    )
    is_system_critical = models.BooleanField(
        default=False,
        verbose_name="Rendszerkritikus",
        help_text="Critical features that cannot be disabled"
    )

    class Meta:
        verbose_name = "Feature sablon"
        verbose_name_plural = "Feature sablonok"
        ordering = ['category', 'display_name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['feature_code']),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.feature_code})"


class CompanyFeature(TimestampedModel):
    """
    Company-specific feature enablement and configuration.
    Controls which features are active for each company.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name="Cég"
    )
    feature_template = models.ForeignKey(
        FeatureTemplate,
        on_delete=models.CASCADE,
        related_name='company_instances',
        verbose_name="Feature sablon"
    )
    is_enabled = models.BooleanField(
        default=False,
        verbose_name="Engedélyezett",
        help_text="Whether this feature is active for the company"
    )
    config_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Konfigurációs adatok",
        help_text="Company-specific configuration for this feature"
    )
    enabled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Engedélyezve ekkor",
        help_text="When this feature was first enabled"
    )
    enabled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enabled_features',
        verbose_name="Engedélyezte"
    )

    class Meta:
        verbose_name = "Cég feature"
        verbose_name_plural = "Cég feature-ök"
        unique_together = ['company', 'feature_template']
        ordering = ['company__name', 'feature_template__category', 'feature_template__display_name']
        indexes = [
            models.Index(fields=['company', 'is_enabled']),
            models.Index(fields=['feature_template', 'is_enabled']),
        ]

    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{self.company.name} - {self.feature_template.display_name} {status}"

    def save(self, *args, **kwargs):
        # Set enabled_at timestamp when feature is first enabled
        if self.is_enabled and not self.enabled_at:
            from django.utils import timezone
            self.enabled_at = timezone.now()
        # Clear enabled_at if feature is disabled
        elif not self.is_enabled and self.enabled_at:
            self.enabled_at = None

        super().save(*args, **kwargs)

    @property
    def feature_code(self):
        """Convenience property to access feature code"""
        return self.feature_template.feature_code


class CompanyFeatureManager:
    """
    Business logic manager for company feature operations.
    Provides high-level methods for feature management.
    """

    @staticmethod
    def initialize_company_features(company, user=None):
        """
        Initialize default features for a new company based on FeatureTemplate defaults.

        Args:
            company: Company instance
            user: User who is initializing the features (optional)

        Returns:
            List of CompanyFeature instances created
        """
        default_features = FeatureTemplate.objects.filter(default_enabled=True)
        created_features = []

        for template in default_features:
            feature, created = CompanyFeature.objects.get_or_create(
                company=company,
                feature_template=template,
                defaults={
                    'is_enabled': True,
                    'enabled_by': user,
                }
            )
            if created:
                created_features.append(feature)

        return created_features

    @staticmethod
    def is_feature_enabled(company, feature_code):
        """
        Check if a specific feature is enabled for a company.

        Args:
            company: Company instance or ID
            feature_code: String feature code (e.g., 'EXPORT_XML_SEPA')

        Returns:
            Boolean indicating if feature is enabled
        """
        try:
            feature = CompanyFeature.objects.select_related('feature_template').get(
                company=company,
                feature_template__feature_code=feature_code
            )
            return feature.is_enabled
        except CompanyFeature.DoesNotExist:
            return False

    @staticmethod
    def get_company_features(company, category=None, enabled_only=False):
        """
        Get features for a company with optional filtering.

        Args:
            company: Company instance or ID
            category: Filter by feature category (optional)
            enabled_only: If True, only return enabled features

        Returns:
            QuerySet of CompanyFeature instances
        """
        queryset = CompanyFeature.objects.select_related(
            'feature_template'
        ).filter(company=company)

        if category:
            queryset = queryset.filter(feature_template__category=category)

        if enabled_only:
            queryset = queryset.filter(is_enabled=True)

        return queryset.order_by('feature_template__category', 'feature_template__display_name')

    @staticmethod
    def toggle_feature(company, feature_code, user=None):
        """
        Toggle a feature on/off for a company.

        Args:
            company: Company instance
            feature_code: String feature code
            user: User performing the action (optional)

        Returns:
            Tuple (CompanyFeature instance, was_enabled_after_toggle)
        """
        try:
            feature = CompanyFeature.objects.select_related('feature_template').get(
                company=company,
                feature_template__feature_code=feature_code
            )

            # Check if feature is system critical and cannot be disabled
            if feature.is_enabled and feature.feature_template.is_system_critical:
                raise ValueError(f"Cannot disable system critical feature: {feature_code}")

            feature.is_enabled = not feature.is_enabled
            if feature.is_enabled and user:
                feature.enabled_by = user

            feature.save()
            return feature, feature.is_enabled

        except CompanyFeature.DoesNotExist:
            # Feature doesn't exist, create it as enabled
            template = FeatureTemplate.objects.get(feature_code=feature_code)
            feature = CompanyFeature.objects.create(
                company=company,
                feature_template=template,
                is_enabled=True,
                enabled_by=user
            )
            return feature, True
