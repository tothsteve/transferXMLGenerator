"""
Base Tables Serializers Module

This module contains serializers for base tables (alaptáblák) management:
- Supplier categories and types for cost categorization
- Supplier records with validity periods
- Customer records with cashflow adjustments
- Product prices with USD/HUF support and validity periods

These tables are manually imported via CSV and support temporal data with valid_from/valid_to.
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import (
    SupplierCategory, SupplierType, Supplier, Customer, ProductPrice
)


class SupplierCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for SupplierCategory (Beszállító kategória) model.

    Provides CRUD operations for supplier cost categories.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = SupplierCategory
        fields = [
            'id', 'company', 'company_name', 'name', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate category name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A kategória neve kötelező.")
        return value.strip()


class SupplierTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for SupplierType (Beszállító típus) model.

    Provides CRUD operations for supplier cost subcategories.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = SupplierType
        fields = [
            'id', 'company', 'company_name', 'name', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate type name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A típus neve kötelező.")
        return value.strip()


class SupplierSerializer(serializers.ModelSerializer):
    """
    Serializer for Supplier (Beszállító) model.

    Provides CRUD operations with company auto-assignment and validity period support.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    type_name = serializers.CharField(source='type.name', read_only=True, allow_null=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'company', 'company_name', 'partner_name',
            'category', 'category_name', 'type', 'type_name',
            'valid_from', 'valid_to', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'category_name', 'type_name', 'created_at', 'updated_at']

    def get_is_valid(self, obj):
        """Check if supplier record is currently valid"""
        return obj.is_valid()

    def validate_partner_name(self, value):
        """Validate partner name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A partner neve kötelező.")
        return value.strip()

    def validate(self, data):
        """Validate validity period"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({
                'valid_to': 'Az érvényesség vége nem lehet korábbi, mint a kezdete.'
            })

        return data


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer (Vevő) model.

    Provides CRUD operations with company auto-assignment and cashflow adjustment support.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'company', 'company_name', 'customer_name', 'cashflow_adjustment',
            'valid_from', 'valid_to', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def get_is_valid(self, obj):
        """Check if customer record is currently valid"""
        return obj.is_valid()

    def validate_customer_name(self, value):
        """Validate customer name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A vevő neve kötelező.")
        return value.strip()

    def validate(self, data):
        """Validate validity period"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({
                'valid_to': 'Az érvényesség vége nem lehet korábbi, mint a kezdete.'
            })

        return data


class ProductPriceSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductPrice (CONMED árak) model.

    Provides CRUD operations for product pricing with USD/HUF support and validity periods.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = ProductPrice
        fields = [
            'id', 'company', 'company_name',
            'product_value', 'product_description',
            'uom', 'uom_hun',
            'purchase_price_usd', 'purchase_price_huf',
            'markup', 'sales_price_huf',
            'cap_disp', 'is_inventory_managed',
            'valid_from', 'valid_to', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def get_is_valid(self, obj):
        """Check if product price record is currently valid"""
        return obj.is_valid()

    def validate_product_value(self, value):
        """Validate product code is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A termék kód kötelező.")
        return value.strip()

    def validate_product_description(self, value):
        """Validate product description is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A termék leírás kötelező.")
        return value.strip()

    def validate(self, data):
        """Validate validity period and pricing logic"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({
                'valid_to': 'Az érvényesség vége nem lehet korábbi, mint a kezdete.'
            })

        return data
