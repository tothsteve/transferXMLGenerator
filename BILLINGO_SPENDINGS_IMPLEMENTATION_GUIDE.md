# Billingo Spendings Feature - Implementation Guide

This guide provides step-by-step implementation instructions for the Billingo Spendings sync feature.

## Status
✅ **CompanyBillingoSettings Updated** - Added `last_billingo_spending_sync_date` field
⏳ **Remaining Steps** - Follow this guide to complete the implementation

---

## Step 1: Add BillingoSpending Model (READY TO COPY)

Add this model to `/backend/bank_transfers/models.py` after `BillingoSyncLog` class (around line 2260):

```python
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
        ('other', 'Egyéb'),
        ('overheads', 'Rezsiköltség'),
        ('service', 'Szolgáltatás'),
        ('stock', 'Készlet'),
        ('tangible_assets', 'Tárgyi eszköz'),
    ]
    category = models.CharField(
        max_length=20,
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
        verbose_name="Partner IBAN"
    )
    partner_account_number = models.CharField(
        max_length=100,
        blank=True,
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
```

---

## Step 2: Create Database Migration

Run these commands:

```bash
cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend
python manage.py makemigrations bank_transfers -n add_billingo_spending
python manage.py migrate
```

---

## Step 3: Create Sync Service

Create `/backend/bank_transfers/services/billingo_spending_sync_service.py`:

This file is too large to include here. Key points:
- Copy pattern from `billingo_sync_service.py`
- Replace "invoices" with "spendings"
- API endpoint: `GET /spendings`
- Handle SpendingPartner nested object extraction
- Update `last_billingo_spending_sync_date` after sync

---

## Step 4: Add Serializers

Add to `/backend/bank_transfers/serializers.py` (after BillingoInvoice serializers, around line 1700):

```python
class BillingoSpendingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for spending list view"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = BillingoSpending
        fields = [
            'id', 'company', 'company_name', 'invoice_number', 'partner_name',
            'partner_tax_code', 'category', 'category_display', 'invoice_date',
            'due_date', 'paid_at', 'is_paid', 'total_gross_local', 'currency',
            'payment_method', 'is_created_by_nav'
        ]
        read_only_fields = fields


class BillingoSpendingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for spending detail view"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = BillingoSpending
        fields = '__all__'
        read_only_fields = [
            'id', 'company', 'organization_id', 'created_at', 'updated_at'
        ]
```

---

## Step 5: Add API ViewSet

Add to `/backend/bank_transfers/api_views.py` (after BillingoInvoiceViewSet, around line 2400):

```python
class BillingoSpendingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Billingo költségek megtekintése

    Szinkronizált költségek lekérdezése Billingo-ból.
    Csak olvasható - a költségek az API szinkronizálással frissülnek.

    Szűrések:
    - category: kategória (advertisement, development, stb.)
    - paid: true/false - kifizetett költségek
    - partner_tax_code: partner adószáma
    - invoice_number: számlaszám keresés
    - from_date: számla dátuma >= (YYYY-MM-DD)
    - to_date: számla dátuma <= (YYYY-MM-DD)
    - payment_method: fizetési mód
    """
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBillingoSync]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'partner_name', 'partner_tax_code', 'comment']
    ordering_fields = ['invoice_date', 'due_date', 'total_gross_local']
    ordering = ['-invoice_date']

    def get_queryset(self):
        """Csak a cég költségei"""
        company = getattr(self.request, 'company', None)
        if not company:
            return BillingoSpending.objects.none()

        queryset = BillingoSpending.objects.filter(company=company)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by paid status
        paid = self.request.query_params.get('paid')
        if paid is not None:
            if paid.lower() == 'true':
                queryset = queryset.filter(paid_at__isnull=False)
            else:
                queryset = queryset.filter(paid_at__isnull=True)

        # Filter by partner tax code
        partner_tax_code = self.request.query_params.get('partner_tax_code')
        if partner_tax_code:
            queryset = queryset.filter(partner_tax_code=partner_tax_code)

        # Filter by invoice number
        invoice_number = self.request.query_params.get('invoice_number')
        if invoice_number:
            queryset = queryset.filter(invoice_number__icontains=invoice_number)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(invoice_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(invoice_date__lte=to_date)

        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset

    def get_serializer_class(self):
        """Use list serializer for list view, detail for retrieve"""
        if self.action == 'list':
            return BillingoSpendingListSerializer
        return BillingoSpendingDetailSerializer
```

---

## Step 6: Add Sync Trigger to BillingoSettingsViewSet

Add this action to `BillingoSettingsViewSet` in `/backend/bank_transfers/api_views.py`:

```python
@action(detail=False, methods=['post'])
def trigger_spending_sync(self, request):
    """
    Trigger manual Billingo spending sync for current company.

    POST /api/billingo-settings/trigger_spending_sync/
    Body: { "full_sync": true|false }  (optional, defaults to false)
    """
    from .services.billingo_spending_sync_service import BillingoSpendingSyncService, BillingoAPIError

    company = request.company

    # Check if Billingo settings exist
    try:
        settings = CompanyBillingoSettings.objects.get(company=company)
    except CompanyBillingoSettings.DoesNotExist:
        return Response(
            {'error': 'Nincs Billingo beállítás konfigurálva ennél a cégnél'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not settings.is_active:
        return Response(
            {'error': 'Billingo szinkronizálás le van tiltva ennél a cégnél'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get full_sync parameter
    full_sync = request.data.get('full_sync', False)

    # Trigger sync
    try:
        service = BillingoSpendingSyncService()
        result = service.sync_company(company, sync_type='MANUAL', full_sync=full_sync)

        return Response({
            'status': 'success',
            'spendings_processed': result['spendings_processed'],
            'spendings_created': result['spendings_created'],
            'spendings_updated': result['spendings_updated'],
            'spendings_skipped': result['spendings_skipped'],
            'api_calls': result['api_calls'],
            'duration_seconds': result['duration_seconds'],
            'errors': result.get('errors', [])
        })

    except BillingoAPIError as e:
        logger.error(f"Billingo spending sync failed for company {company.id}: {str(e)}")
        return Response(
            {'error': f'Billingo szinkronizálás hiba: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error during Billingo spending sync: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Váratlan hiba történt: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## Step 7: Register Routes

Add to `/backend/bank_transfers/urls.py`:

```python
router.register(r'billingo-spendings', views.BillingoSpendingViewSet, basename='billingo-spending')
```

---

## Frontend Implementation

### Step 8: TypeScript Types

Add to `/frontend/src/types/api.ts`:

```typescript
export interface BillingoSpending {
  id: number;
  company: number;
  company_name?: string;
  organization_id: number;
  category: 'advertisement' | 'development' | 'other' | 'overheads' | 'service' | 'stock' | 'tangible_assets';
  category_display?: string;
  paid_at: string | null;
  fulfillment_date: string;
  invoice_number: string;
  currency: string;
  conversion_rate: number;
  total_gross: number;
  total_gross_local: number;
  total_vat_amount: number;
  total_vat_amount_local: number;
  invoice_date: string;
  due_date: string;
  payment_method: string;
  partner_id?: number | null;
  partner_name: string;
  partner_tax_code: string;
  partner_address?: object | null;
  partner_iban?: string;
  partner_account_number?: string;
  comment?: string;
  is_created_by_nav: boolean;
  is_paid?: boolean;
  created_at: string;
  updated_at: string;
}
```

### Step 9: API Services & React Query Hooks

See separate implementation files for:
- `/frontend/src/services/api.ts` - Add spending API functions
- `/frontend/src/hooks/api.ts` - Add React Query hooks

### Step 10: React Component

Create `/frontend/src/components/Billingo/BillingoSpendings.tsx`
- Follow pattern from `BillingoInvoices.tsx`
- Table with columns: Invoice Number, Partner, Category, Date, Amount, Payment Status
- Filters for category, date range, paid status
- Sync button
- Export functionality

### Step 11: Navigation

Add to `/frontend/src/components/Layout/Sidebar.tsx`:
```typescript
{ name: 'Költségek', href: '/billingo/spendings' },
```

Add to `/frontend/src/components/Layout/Layout.tsx`:
```typescript
<Route path="/billingo/spendings" element={<BillingoSpendings />} />
```

---

## Testing Checklist

1. ✅ Verify model added correctly
2. ✅ Run migrations successfully
3. ⏳ Test sync service with Billingo API
4. ⏳ Verify API endpoints work
5. ⏳ Test frontend display
6. ⏳ Test filters and search
7. ⏳ Test sync button
8. ⏳ Verify company-scoped data isolation

---

## Notes

- Pattern closely mirrors BillingoInvoice implementation
- Replace "invoices" with "spendings" throughout
- API endpoint: `/spendings` instead of `/documents`
- Partner data comes from nested SpendingPartner object
- Category is enum (7 choices) vs invoice type field
