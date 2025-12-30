"""
Exchange Rate Serializers Module

This module contains serializers for MNB (Magyar Nemzeti Bank) exchange rate integration:
- Exchange rate models with formatted display
- Exchange rate sync logs and history
- Current rates endpoint for USD/EUR
- Currency conversion functionality

Exchange rates are synced daily from MNB official API.
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import ExchangeRate, ExchangeRateSyncLog


class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    Serializer for ExchangeRate model.
    Provides exchange rate data with formatted output.
    """
    rate_display = serializers.SerializerMethodField()
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)

    class Meta:
        model = ExchangeRate
        fields = [
            'id',
            'rate_date',
            'currency',
            'currency_display',
            'rate',
            'rate_display',
            'unit',
            'sync_date',
            'source',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'sync_date',
            'created_at',
            'updated_at'
        ]

    def get_rate_display(self, obj):
        """Format rate with 4 decimal places for display"""
        return f"{obj.rate:.4f} HUF"


class ExchangeRateSyncLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ExchangeRateSyncLog model.
    Provides sync history and statistics.
    """
    duration_seconds = serializers.ReadOnlyField()
    total_rates_processed = serializers.ReadOnlyField()
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)

    class Meta:
        model = ExchangeRateSyncLog
        fields = [
            'id',
            'sync_start_time',
            'sync_end_time',
            'duration_seconds',
            'currencies_synced',
            'date_range_start',
            'date_range_end',
            'rates_created',
            'rates_updated',
            'total_rates_processed',
            'sync_status',
            'sync_status_display',
            'error_message',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'sync_start_time',
            'sync_end_time',
            'duration_seconds',
            'total_rates_processed',
            'created_at'
        ]


class ExchangeRateListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for exchange rate lists.
    Used for compact API responses.
    """
    class Meta:
        model = ExchangeRate
        fields = [
            'rate_date',
            'currency',
            'rate',
            'sync_date'
        ]


class CurrentRatesSerializer(serializers.Serializer):
    """
    Serializer for current exchange rates endpoint response.
    """
    USD = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True)
    EUR = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True)
    last_sync = serializers.DateTimeField(allow_null=True)
    rate_date = serializers.DateField(allow_null=True)


class ExchangeRateHistorySerializer(serializers.Serializer):
    """
    Serializer for exchange rate history endpoint response.
    Used for charting and analysis.
    """
    date = serializers.DateField()
    rate = serializers.DecimalField(max_digits=12, decimal_places=6)


class CurrencyConversionSerializer(serializers.Serializer):
    """
    Serializer for currency conversion requests and responses.
    """
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    currency = serializers.ChoiceField(choices=['USD', 'EUR'], required=True)
    conversion_date = serializers.DateField(required=False, allow_null=True)

    # Response fields
    huf_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    exchange_rate = serializers.DecimalField(max_digits=12, decimal_places=6, read_only=True)
    rate_date = serializers.DateField(read_only=True)
