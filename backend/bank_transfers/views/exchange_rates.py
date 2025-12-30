"""
Exchange Rate Management ViewSet

This module handles MNB (Magyar Nemzeti Bank) exchange rate operations:
- Rate listing with filtering (currency, date ranges)
- Current and latest rate queries
- Currency conversion to HUF
- Manual sync triggers (ADMIN only)
- Historical rate synchronization
- Sync history and rate history for charts

Domain: MNB Exchange Rate Integration
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import date

from ..models import ExchangeRate, ExchangeRateSyncLog
from ..serializers import (
    ExchangeRateSerializer, ExchangeRateSyncLogSerializer,
    CurrencyConversionSerializer
)
from ..permissions import IsCompanyMember, IsCompanyAdmin
from ..services.exchange_rate_sync_service import ExchangeRateSyncService
from ..schemas.exchange_rate import CurrencyConversionInput, CurrencyConversionOutput


class ExchangeRateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MNB (Magyar Nemzeti Bank) árfolyamok kezelése

    Támogatott funkciók:
    - Árfolyamok listázása szűréssel (currency, date_from, date_to)
    - Aktuális árfolyamok lekérdezése
    - Deviza váltás számítás
    - Árfolyam szinkronizáció MNB API-ról
    - Szinkronizációs előzmények

    Jogosultság: Minden bejelentkezett felhasználó olvashat,
                 de csak ADMIN végezhet szinkronizációt
    """
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['rate_date', 'currency', 'rate']
    ordering = ['-rate_date', 'currency']  # Default: newest first

    def get_queryset(self):
        """
        Szűrési lehetőségek:
        - currency: USD vagy EUR
        - date_from: kezdő dátum (YYYY-MM-DD)
        - date_to: befejező dátum (YYYY-MM-DD)
        """
        queryset = ExchangeRate.objects.all()

        # Currency filter
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency=currency.upper())

        # Date range filters
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(rate_date__gte=date_from)

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(rate_date__lte=date_to)

        return queryset

    @swagger_auto_schema(
        operation_description="Aktuális (mai) árfolyamok lekérdezése USD és EUR valutákra",
        responses={
            200: openapi.Response(
                description="Aktuális árfolyamok",
                examples={
                    'application/json': {
                        'USD': {'rate': '385.5000', 'rate_date': '2025-10-01'},
                        'EUR': {'rate': '410.2500', 'rate_date': '2025-10-01'}
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Aktuális (mai) árfolyamok lekérdezése"""
        today = date.today()
        currencies = ['USD', 'EUR']

        rates_data = {}
        for currency in currencies:
            rate = ExchangeRateSyncService.get_rate_for_date(today, currency)
            if rate:
                rate_obj = ExchangeRate.objects.filter(
                    rate_date=today,
                    currency=currency
                ).first()

                if rate_obj:
                    rates_data[currency] = {
                        'rate': str(rate),
                        'rate_date': rate_obj.rate_date.strftime('%Y-%m-%d')
                    }

        return Response(rates_data)

    @swagger_auto_schema(
        operation_description="Legutóbbi elérhető árfolyamok lekérdezése (ha ma nincs, akkor a legközelebbi korábbi)",
        responses={
            200: openapi.Response(
                description="Legutóbbi árfolyamok",
                examples={
                    'application/json': {
                        'USD': {'rate': '385.5000', 'rate_date': '2025-10-01'},
                        'EUR': {'rate': '410.2500', 'rate_date': '2025-10-01'}
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Legutóbbi elérhető árfolyamok lekérdezése"""
        latest_rates = ExchangeRateSyncService.get_latest_rates(['USD', 'EUR'])

        rates_data = {}
        for currency, (rate, rate_date) in latest_rates.items():
            rates_data[currency] = {
                'rate': str(rate),
                'rate_date': rate_date.strftime('%Y-%m-%d')
            }

        return Response(rates_data)

    @swagger_auto_schema(
        operation_description="Deviza átváltás HUF-ra",
        request_body=CurrencyConversionSerializer,
        responses={
            200: openapi.Response(
                description="Átváltás eredménye",
                examples={
                    'application/json': {
                        'amount': '100.00',
                        'currency': 'USD',
                        'conversion_date': '2025-10-01',
                        'rate': '385.5000',
                        'huf_amount': '38550.00'
                    }
                }
            ),
            400: 'Hiányzó vagy érvénytelen paraméterek',
            404: 'Árfolyam nem található a megadott dátumra'
        }
    )
    @action(detail=False, methods=['post'])
    def convert(self, request):
        """
        Deviza átváltás HUF-ra adott árfolyamon.

        Uses Pydantic for type-safe service layer integration.
        """
        serializer = CurrencyConversionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create Pydantic input from validated data
        try:
            conversion_input = CurrencyConversionInput(
                amount=serializer.validated_data['amount'],
                from_currency=serializer.validated_data['currency'],
                to_currency='HUF',
                rate_date=serializer.validated_data.get('conversion_date')
            )
        except Exception as e:
            return Response(
                {'error': f'Validation error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use Pydantic-based service method
        try:
            service = ExchangeRateSyncService()
            result: CurrencyConversionOutput = service.convert_currency(conversion_input)

            # Return response in original format for backward compatibility
            return Response({
                'amount': str(result.original_amount),
                'currency': result.original_currency,
                'conversion_date': result.rate_date.strftime('%Y-%m-%d'),
                'rate': str(result.exchange_rate),
                'huf_amount': str(result.converted_amount)
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="MNB árfolyamok szinkronizálása (mai napra) - Csak ADMIN",
        responses={
            200: ExchangeRateSyncLogSerializer,
            403: 'Nincs jogosultság',
            500: 'Szinkronizációs hiba'
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsCompanyAdmin])
    def sync_current(self, request):
        """Aktuális árfolyamok szinkronizálása MNB-ről (mai napra)"""
        try:
            service = ExchangeRateSyncService()
            sync_log = service.sync_current_rates()

            serializer = ExchangeRateSyncLogSerializer(sync_log)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': f'Szinkronizációs hiba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Történeti árfolyamok szinkronizálása - Csak ADMIN",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'days_back': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Hány napra visszamenőleg (pl. 730 = 2 év)',
                    default=30
                ),
                'currencies': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Devizák listája (alapértelmezett: USD, EUR)',
                    default=['USD', 'EUR']
                )
            }
        ),
        responses={
            200: ExchangeRateSyncLogSerializer,
            403: 'Nincs jogosultság',
            500: 'Szinkronizációs hiba'
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsCompanyAdmin])
    def sync_historical(self, request):
        """Történeti árfolyamok szinkronizálása (pl. 2 év = 730 nap)"""
        days_back = request.data.get('days_back', 30)
        currencies = request.data.get('currencies', None)

        try:
            service = ExchangeRateSyncService()
            sync_log = service.sync_historical_rates(
                days_back=days_back,
                currencies=currencies
            )

            serializer = ExchangeRateSyncLogSerializer(sync_log)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': f'Szinkronizációs hiba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Szinkronizációs előzmények lekérdezése",
        responses={200: ExchangeRateSyncLogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def sync_history(self, request):
        """Szinkronizációs előzmények listája"""
        sync_logs = ExchangeRateSyncLog.objects.all().order_by('-sync_start_time')[:20]
        serializer = ExchangeRateSyncLogSerializer(sync_logs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Árfolyam történet lekérdezése (grafikonhoz)",
        manual_parameters=[
            openapi.Parameter('currency', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Deviza kód (USD vagy EUR)', required=True),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Napok száma visszamenőleg', default=30)
        ],
        responses={
            200: openapi.Response(
                description="Árfolyam történet",
                examples={
                    'application/json': [
                        {'date': '2025-09-01', 'rate': 385.5},
                        {'date': '2025-09-02', 'rate': 386.1}
                    ]
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Árfolyam történet lekérdezése (grafikonhoz, elemzéshez)"""
        currency = request.query_params.get('currency', 'USD').upper()
        days = int(request.query_params.get('days', 30))

        history_data = ExchangeRateSyncService.get_rate_history(currency, days)
        return Response(history_data)
