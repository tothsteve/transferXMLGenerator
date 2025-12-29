"""
Base Tables ViewSets

This module handles base table operations for suppliers, customers, and product prices:
- Supplier categories and types management
- Supplier master data with validity dates
- Customer master data with cashflow adjustments
- Product price management (CONMED catalog)
- Filtering by validity, category, and inventory management status

Domain: Base Tables Management (Suppliers, Customers, Products)
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django.db import models
from datetime import date

from ..models import SupplierCategory, SupplierType, Supplier, Customer, ProductPrice
from ..serializers import (
    SupplierCategorySerializer, SupplierTypeSerializer, SupplierSerializer,
    CustomerSerializer, ProductPriceSerializer
)
from ..permissions import IsCompanyMember, RequireBaseTables


class SupplierCategoryViewSet(viewsets.ModelViewSet):
    """
    Beszállító kategóriák (Supplier Categories) kezelése

    Cost category management for suppliers.

    Támogatott szűrések:
    - search: name alapján keresés

    Rendezés:
    - display_order, name, created_at (default: display_order)

    Hozzáférés: BASE_TABLES feature required
    """
    serializer_class = SupplierCategorySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBaseTables]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order']

    def get_queryset(self):
        """Csak a cég kategóriái"""
        company = getattr(self.request, 'company', None)
        if not company:
            return SupplierCategory.objects.none()
        return SupplierCategory.objects.filter(company=company)

    def perform_create(self, serializer):
        """Assign company and auto-increment display_order on creation"""
        # Get max display_order for this company, default to -1 if no items exist
        max_order = SupplierCategory.objects.filter(
            company=self.request.company
        ).aggregate(max_order=models.Max('display_order'))['max_order'] or -1

        # Set display_order to max + 1 if not provided
        if 'display_order' not in serializer.validated_data:
            serializer.save(company=self.request.company, display_order=max_order + 1)
        else:
            serializer.save(company=self.request.company)


class SupplierTypeViewSet(viewsets.ModelViewSet):
    """
    Beszállító típusok (Supplier Types) kezelése

    Cost subcategory management for suppliers.

    Támogatott szűrések:
    - search: name alapján keresés

    Rendezés:
    - display_order, name, created_at (default: display_order)

    Hozzáférés: BASE_TABLES feature required
    """
    serializer_class = SupplierTypeSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBaseTables]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order']

    def get_queryset(self):
        """Csak a cég típusai"""
        company = getattr(self.request, 'company', None)
        if not company:
            return SupplierType.objects.none()
        return SupplierType.objects.filter(company=company)

    def perform_create(self, serializer):
        """Assign company and auto-increment display_order on creation"""
        # Get max display_order for this company, default to -1 if no items exist
        max_order = SupplierType.objects.filter(
            company=self.request.company
        ).aggregate(max_order=models.Max('display_order'))['max_order'] or -1

        # Set display_order to max + 1 if not provided
        if 'display_order' not in serializer.validated_data:
            serializer.save(company=self.request.company, display_order=max_order + 1)
        else:
            serializer.save(company=self.request.company)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    Beszállítók (Suppliers) kezelése

    Támogatott szűrések:
    - valid_only: true/false - csak érvényes rekordok (default: true)
    - search: partner_name, category, type alapján keresés
    - category: kategória alapján szűrés
    - type: típus alapján szűrés
    - valid_from: érvényesség kezdete >= (YYYY-MM-DD)
    - valid_to: érvényesség vége <= (YYYY-MM-DD)

    Rendezés:
    - partner_name, category, type, valid_from, valid_to, created_at

    Hozzáférés: ADMIN only
    """
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBaseTables]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['partner_name', 'category__name', 'type__name']
    ordering_fields = ['partner_name', 'category', 'type', 'valid_from', 'valid_to', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Csak a cég beszállítói"""
        company = getattr(self.request, 'company', None)
        if not company:
            return Supplier.objects.none()

        queryset = Supplier.objects.filter(company=company)

        # Filter by valid_only (default: true)
        valid_only = self.request.query_params.get('valid_only', 'true').lower() == 'true'
        if valid_only:
            today = date.today()
            queryset = queryset.filter(
                models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=today),
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=today)
            )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name__icontains=category)

        # Filter by type
        supplier_type = self.request.query_params.get('type')
        if supplier_type:
            queryset = queryset.filter(type__name__icontains=supplier_type)

        # Filter by valid_from date
        valid_from = self.request.query_params.get('valid_from')
        if valid_from:
            queryset = queryset.filter(valid_from__gte=valid_from)

        # Filter by valid_to date
        valid_to = self.request.query_params.get('valid_to')
        if valid_to:
            queryset = queryset.filter(valid_to__lte=valid_to)

        return queryset

    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Vevők (Customers) kezelése

    Támogatott szűrések:
    - valid_only: true/false - csak érvényes rekordok (default: true)
    - search: customer_name alapján keresés
    - valid_from: érvényesség kezdete >= (YYYY-MM-DD)
    - valid_to: érvényesség vége <= (YYYY-MM-DD)

    Rendezés:
    - customer_name, cashflow_adjustment, valid_from, valid_to, created_at

    Hozzáférés: ADMIN only
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBaseTables]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name']
    ordering_fields = ['customer_name', 'cashflow_adjustment', 'valid_from', 'valid_to', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Csak a cég vevői"""
        company = getattr(self.request, 'company', None)
        if not company:
            return Customer.objects.none()

        queryset = Customer.objects.filter(company=company)

        # Filter by valid_only (default: true)
        valid_only = self.request.query_params.get('valid_only', 'true').lower() == 'true'
        if valid_only:
            today = date.today()
            queryset = queryset.filter(
                models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=today),
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=today)
            )

        # Filter by valid_from date
        valid_from = self.request.query_params.get('valid_from')
        if valid_from:
            queryset = queryset.filter(valid_from__gte=valid_from)

        # Filter by valid_to date
        valid_to = self.request.query_params.get('valid_to')
        if valid_to:
            queryset = queryset.filter(valid_to__lte=valid_to)

        return queryset

    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)


class ProductPriceViewSet(viewsets.ModelViewSet):
    """
    CONMED árak (Product Prices) kezelése

    Támogatott szűrések:
    - valid_only: true/false - csak érvényes rekordok (default: true)
    - search: product_value, product_description alapján keresés
    - is_inventory_managed: true/false - készletkezelt termékek
    - valid_from: érvényesség kezdete >= (YYYY-MM-DD)
    - valid_to: érvényesség vége <= (YYYY-MM-DD)

    Rendezés:
    - product_value, product_description, purchase_price_usd, purchase_price_huf,
      sales_price_huf, valid_from, valid_to, created_at

    Hozzáférés: ADMIN only
    """
    serializer_class = ProductPriceSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBaseTables]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product_value', 'product_description']
    ordering_fields = ['product_value', 'product_description', 'purchase_price_usd', 'purchase_price_huf', 'sales_price_huf', 'valid_from', 'valid_to', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Csak a cég termékárai"""
        company = getattr(self.request, 'company', None)
        if not company:
            return ProductPrice.objects.none()

        queryset = ProductPrice.objects.filter(company=company)

        # Filter by valid_only (default: true)
        valid_only = self.request.query_params.get('valid_only', 'true').lower() == 'true'
        if valid_only:
            today = date.today()
            queryset = queryset.filter(
                models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=today),
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=today)
            )

        # Filter by is_inventory_managed
        is_inventory_managed = self.request.query_params.get('is_inventory_managed')
        if is_inventory_managed is not None:
            is_managed = is_inventory_managed.lower() == 'true'
            queryset = queryset.filter(is_inventory_managed=is_managed)

        # Filter by valid_from date
        valid_from = self.request.query_params.get('valid_from')
        if valid_from:
            queryset = queryset.filter(valid_from__gte=valid_from)

        # Filter by valid_to date
        valid_to = self.request.query_params.get('valid_to')
        if valid_to:
            queryset = queryset.filter(valid_to__lte=valid_to)

        return queryset

    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)
