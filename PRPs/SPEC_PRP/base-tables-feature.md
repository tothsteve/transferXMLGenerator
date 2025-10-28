# BASE_TABLES Feature Implementation

> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.

## High-Level Objective

Implement a complete feature-gated BASE_TABLES system with 3 master data tables (Suppliers, Customers, Product Prices) that provides CRUD operations, Excel-like filtering, validity period management, and is accessible only to users with ADMIN role. The feature follows vertical slice architecture with complete backend and frontend implementation.

## Mid-Level Objectives

### 1. Backend Feature Flag System
- Add BASE_TABLES feature to FeatureTemplate.FEATURE_CHOICES
- Update CompanyUser.ROLE_PERMISSIONS to grant ADMIN-only access
- Ensure feature flag is enforced at API level via HasFeaturePermission

### 2. Backend Data Models & Migration
- Create 3 Django models: Supplier, Customer, ProductPrice
- Implement CompanyOwnedTimestampedModel base class for multi-tenant isolation
- Add validity period fields (valid_from, valid_to) with is_valid() method
- Create migration with appropriate indexes for performance

### 3. Backend API Layer (Vertical Slice)
- Create 3 serializers with company auto-assignment from request context
- Create 3 ViewSets with feature permission enforcement
- Implement valid_only query parameter (default: true) for validity filtering
- Add search and column-based filtering capabilities
- Register URL routes: /api/suppliers/, /api/customers/, /api/product-prices/

### 4. Frontend Type System & Validation
- Create TypeScript interfaces for all 3 entities
- Add BASE_TABLES to features constant
- Create Zod schemas for form validation and API response parsing
- Ensure strict type safety across all components

### 5. Frontend API Integration & State Management
- Add CRUD API service methods for all 3 entities
- Create React Query hooks with caching and optimistic updates
- Implement valid_only parameter in query hooks with toggle state
- Handle loading, error, and success states

### 6. Frontend UI Components (Vertical Slice)
- Create 3 MUI DataGrid components with Excel-like column filtering
- Implement inline editing via DataGrid processRowUpdate
- Add new record dialog forms with validation
- Add validity toggle switch (default: show valid records only)
- Implement visual validity badges (green/gray)
- Add delete confirmation dialogs

### 7. Frontend Navigation & Routing
- Create new "Alaptáblák" main menu item with feature flag gate
- Add 3 submenu items: Beszállítók, Vevők, CONMED Árak
- Register 3 feature-gated routes in App.tsx
- Use StorageIcon for main menu item

### 8. Documentation & Database Comments
- Update DATABASE_DOCUMENTATION.md with 3 new tables
- Update backend/sql/complete_database_comments_postgresql.sql
- Update backend/sql/complete_database_comments_sqlserver.sql
- Document all fields, indexes, and business logic

## Implementation Notes

### Architecture Principles
- **Vertical Slice**: Each entity (Supplier, Customer, ProductPrice) is a complete vertical slice from database to UI
- **Feature Flag**: All endpoints and UI elements gated by BASE_TABLES feature with ADMIN role requirement
- **Multi-Tenant**: All models inherit from CompanyOwnedTimestampedModel for automatic company scoping
- **Type Safety**: Zod schemas validate all external data (API responses, form inputs)
- **Performance**: Server-side pagination, filtering, and indexes on company_id + validity fields

### Coding Standards
- **Backend**: Follow CLAUDE-PYTHON-BASIC.md (Django REST Framework patterns, service layer separation)
- **Frontend**: Follow CLAUDE-REACT.md (React 19, TypeScript strict mode, Zod validation)
- **Security**: Input validation, XSS prevention, CSRF tokens, feature permission checks

### Dependencies
- **Backend**: Django REST Framework, django-filter for column filtering
- **Frontend**: MUI DataGrid, React Query, Zod, React Hook Form (for dialogs)

### Data Source
- CSV files at: `/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/bank_statement_example/BASE*.csv`
- **Note**: Skip "NEM KELL" column in CONMED árak CSV

### Validity Period Logic
- Records with valid_from <= today and (valid_to >= today OR valid_to IS NULL) are considered "valid"
- Backend Model method: `is_valid()` returns boolean
- Backend API: `?valid_only=true` (default) filters to valid records only
- Frontend: Toggle switch to show/hide expired records

## Context

### Beginning Context (Files that exist at start)

**Backend:**
- `backend/bank_transfers/models.py` - Contains existing models and FeatureTemplate
- `backend/bank_transfers/base_models.py` - Contains CompanyOwnedTimestampedModel
- `backend/bank_transfers/serializers.py` - Contains existing serializers
- `backend/bank_transfers/api_views.py` - Contains existing ViewSets
- `backend/bank_transfers/permissions.py` - Contains HasFeaturePermission
- `backend/bank_transfers/urls.py` - Contains API router registration
- `backend/DATABASE_DOCUMENTATION.md` - Database schema documentation
- `backend/sql/complete_database_comments_postgresql.sql` - PostgreSQL comments
- `backend/sql/complete_database_comments_sqlserver.sql` - SQL Server comments

**Frontend:**
- `frontend/src/types/features.ts` - Feature flag constants
- `frontend/src/types/` - Type definitions directory
- `frontend/src/schemas/` - Zod schemas directory
- `frontend/src/services/api.ts` - API service with axios
- `frontend/src/hooks/api.ts` - React Query hooks
- `frontend/src/components/Layout/Layout.tsx` - Main navigation menu
- `frontend/src/App.tsx` - Route definitions
- `frontend/src/components/BankStatements/` - Example of existing vertical slice

**Reference Patterns (to mirror):**
- BankStatements feature for vertical slice architecture
- Beneficiary feature for CRUD patterns
- Billingo feature for feature flag usage

### Ending Context (Files that will exist at end)

**Backend (NEW):**
- `backend/bank_transfers/migrations/005X_add_base_tables_feature.py` - Migration for 3 tables + feature flag

**Backend (MODIFIED):**
- `backend/bank_transfers/models.py` - +3 models (Supplier, Customer, ProductPrice), +BASE_TABLES feature
- `backend/bank_transfers/serializers.py` - +3 serializers
- `backend/bank_transfers/api_views.py` - +3 ViewSets
- `backend/bank_transfers/urls.py` - +3 route registrations
- `backend/DATABASE_DOCUMENTATION.md` - +3 table documentation sections
- `backend/sql/complete_database_comments_postgresql.sql` - +3 table comment blocks
- `backend/sql/complete_database_comments_sqlserver.sql` - +3 table comment blocks

**Frontend (NEW):**
- `frontend/src/types/baseTable.types.ts` - TypeScript interfaces
- `frontend/src/schemas/baseTable.schemas.ts` - Zod validation schemas
- `frontend/src/components/BaseTables/Suppliers.tsx` - Suppliers page component
- `frontend/src/components/BaseTables/Customers.tsx` - Customers page component
- `frontend/src/components/BaseTables/ProductPrices.tsx` - Product Prices page component

**Frontend (MODIFIED):**
- `frontend/src/types/features.ts` - +BASE_TABLES constant
- `frontend/src/services/api.ts` - +3 API service sections (suppliers, customers, productPrices)
- `frontend/src/hooks/api.ts` - +6 hooks (3 query, 3 mutation)
- `frontend/src/components/Layout/Layout.tsx` - +main menu + 3 submenus
- `frontend/src/App.tsx` - +3 routes

## Low-Level Tasks

> Ordered from start to finish by dependency logic

---

### 1. Add BASE_TABLES Feature Flag to Backend Models

```
MODIFY backend/bank_transfers/models.py
ADD BASE_TABLES to FeatureTemplate.FEATURE_CHOICES (around line 130-160 where features are defined)
ADD BASE_TABLES to CompanyUser.ROLE_PERMISSIONS['ADMIN'] list (around line 35-45)

Details:
- Feature code: 'BASE_TABLES'
- Feature description: 'Alaptáblák kezelése (Beszállítók, Vevők, CONMED árak)'
- Add to ADMIN permissions only (ADMIN has ['*'] but document explicitly for clarity)
- Follow existing feature naming pattern (uppercase, underscore-separated)
```

Validation:
```bash
cd backend
python manage.py shell
from bank_transfers.models import FeatureTemplate, CompanyUser
# Verify BASE_TABLES in FEATURE_CHOICES
print([choice[0] for choice in FeatureTemplate.FEATURE_CHOICES if 'BASE' in choice[0]])
# Expected: ['BASE_TABLES']
```

---

### 2. Create Supplier Model

```
MODIFY backend/bank_transfers/models.py
CREATE Supplier model class inheriting from CompanyOwnedTimestampedModel

Details:
- Field: partner_name (CharField, max_length=255, verbose_name="Partner neve")
- Field: category (CharField, max_length=255, blank=True, verbose_name="Kategória")
- Field: type (CharField, max_length=255, blank=True, verbose_name="Típus")
- Field: valid_from (DateField, null=True, blank=True, verbose_name="Érvényesség kezdete")
- Field: valid_to (DateField, null=True, blank=True, verbose_name="Érvényesség vége")
- Method: is_valid() -> bool - returns True if today is between valid_from and valid_to
- Meta: ordering = ['-id'], verbose_name = "Beszállító", verbose_name_plural = "Beszállítók"
- Meta: indexes on ['company', 'valid_from', 'valid_to']
- __str__: return partner_name
```

Validation:
```bash
cd backend
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

### 3. Create Customer Model

```
MODIFY backend/bank_transfers/models.py
CREATE Customer model class inheriting from CompanyOwnedTimestampedModel

Details:
- Field: customer_name (CharField, max_length=255, verbose_name="Vevő neve")
- Field: cashflow_adjustment (IntegerField, default=0, verbose_name="Cashflow kiigazítás (nap)")
- Field: valid_from (DateField, null=True, blank=True, verbose_name="Érvényesség kezdete")
- Field: valid_to (DateField, null=True, blank=True, verbose_name="Érvényesség vége")
- Method: is_valid() -> bool - returns True if today is between valid_from and valid_to
- Meta: ordering = ['-id'], verbose_name = "Vevő", verbose_name_plural = "Vevők"
- Meta: indexes on ['company', 'valid_from', 'valid_to']
- __str__: return customer_name
```

Validation:
```bash
cd backend
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

### 4. Create ProductPrice Model

```
MODIFY backend/bank_transfers/models.py
CREATE ProductPrice model class inheriting from CompanyOwnedTimestampedModel

Details:
- Field: product_value (CharField, max_length=50, verbose_name="Termék kód")
- Field: product_description (CharField, max_length=500, verbose_name="Termék leírás")
- Field: uom (CharField, max_length=50, blank=True, verbose_name="UOM (EN)")
- Field: uom_hun (CharField, max_length=50, blank=True, verbose_name="UOM (HU)")
- Field: purchase_price_usd (DecimalField, max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Beszerzési ár USD")
- Field: purchase_price_huf (DecimalField, max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Beszerzési ár HUF")
- Field: markup (DecimalField, max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Markup (%)")
- Field: sales_price_huf (DecimalField, max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Eladási ár HUF")
- Field: cap_disp (CharField, max_length=100, blank=True, verbose_name="Cap/Disp")
- Field: is_inventory_managed (BooleanField, default=False, verbose_name="Készletkezelt termék")
- Field: valid_from (DateField, null=True, blank=True, verbose_name="Érvényesség kezdete")
- Field: valid_to (DateField, null=True, blank=True, verbose_name="Érvényesség vége")
- Method: is_valid() -> bool - returns True if today is between valid_from and valid_to
- Meta: ordering = ['-id'], verbose_name = "CONMED ár", verbose_name_plural = "CONMED árak"
- Meta: indexes on ['company', 'valid_from', 'valid_to', 'product_value']
- __str__: return f"{product_value} - {product_description[:50]}"
```

Validation:
```bash
cd backend
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

### 5. Create Database Migration

```
CREATE backend/bank_transfers/migrations/005X_add_base_tables_feature.py
Using Django makemigrations command

Details:
- Run: python manage.py makemigrations -n add_base_tables_feature
- Migration should create 3 tables: bank_transfers_supplier, bank_transfers_customer, bank_transfers_productprice
- Verify indexes are created on company_id, valid_from, valid_to fields
- Apply migration: python manage.py migrate
```

Validation:
```bash
cd backend
python manage.py makemigrations -n add_base_tables_feature
python manage.py migrate
python manage.py showmigrations bank_transfers | grep add_base_tables
# Expected: [X] 005X_add_base_tables_feature
```

---

### 6. Create Supplier Serializer

```
MODIFY backend/bank_transfers/serializers.py
CREATE SupplierSerializer class inheriting from serializers.ModelSerializer

Details:
- Meta.model = Supplier
- Meta.fields = ['id', 'company', 'partner_name', 'category', 'type', 'valid_from', 'valid_to', 'created_at', 'updated_at']
- Meta.read_only_fields = ['id', 'company', 'created_at', 'updated_at']
- Override create() to auto-assign company from self.context['request'].user.active_company
- Override update() to preserve company (cannot be changed)
- Add validation: partner_name is required
```

Validation:
```bash
cd backend
python manage.py shell
from bank_transfers.serializers import SupplierSerializer
# Verify serializer imports without error
print(SupplierSerializer.Meta.fields)
# Expected: list of field names
```

---

### 7. Create Customer Serializer

```
MODIFY backend/bank_transfers/serializers.py
CREATE CustomerSerializer class inheriting from serializers.ModelSerializer

Details:
- Meta.model = Customer
- Meta.fields = ['id', 'company', 'customer_name', 'cashflow_adjustment', 'valid_from', 'valid_to', 'created_at', 'updated_at']
- Meta.read_only_fields = ['id', 'company', 'created_at', 'updated_at']
- Override create() to auto-assign company from self.context['request'].user.active_company
- Override update() to preserve company (cannot be changed)
- Add validation: customer_name is required
```

Validation:
```bash
cd backend
python manage.py shell
from bank_transfers.serializers import CustomerSerializer
# Verify serializer imports without error
print(CustomerSerializer.Meta.fields)
# Expected: list of field names
```

---

### 8. Create ProductPrice Serializer

```
MODIFY backend/bank_transfers/serializers.py
CREATE ProductPriceSerializer class inheriting from serializers.ModelSerializer

Details:
- Meta.model = ProductPrice
- Meta.fields = ['id', 'company', 'product_value', 'product_description', 'uom', 'uom_hun', 'purchase_price_usd', 'purchase_price_huf', 'markup', 'sales_price_huf', 'cap_disp', 'is_inventory_managed', 'valid_from', 'valid_to', 'created_at', 'updated_at']
- Meta.read_only_fields = ['id', 'company', 'created_at', 'updated_at']
- Override create() to auto-assign company from self.context['request'].user.active_company
- Override update() to preserve company (cannot be changed)
- Add validation: product_value and product_description are required
```

Validation:
```bash
cd backend
python manage.py shell
from bank_transfers.serializers import ProductPriceSerializer
# Verify serializer imports without error
print(ProductPriceSerializer.Meta.fields)
# Expected: list of field names
```

---

### 9. Create Supplier ViewSet

```
MODIFY backend/bank_transfers/api_views.py
CREATE SupplierViewSet class inheriting from viewsets.ModelViewSet

Details:
- serializer_class = SupplierSerializer
- permission_classes = [IsAuthenticated, HasFeaturePermission]
- feature_required = 'BASE_TABLES'
- filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
- filterset_fields = ['partner_name', 'category', 'type', 'valid_from', 'valid_to']
- search_fields = ['partner_name', 'category', 'type']
- ordering_fields = ['id', 'partner_name', 'valid_from', 'valid_to']
- ordering = ['-id']
- Override get_queryset() to:
  1. Filter by company: Supplier.objects.filter(company=request.user.active_company)
  2. Handle valid_only parameter: if request.query_params.get('valid_only', 'true') == 'true', filter by is_valid()
  3. Return queryset
```

Validation:
```bash
cd backend
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

### 10. Create Customer ViewSet

```
MODIFY backend/bank_transfers/api_views.py
CREATE CustomerViewSet class inheriting from viewsets.ModelViewSet

Details:
- serializer_class = CustomerSerializer
- permission_classes = [IsAuthenticated, HasFeaturePermission]
- feature_required = 'BASE_TABLES'
- filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
- filterset_fields = ['customer_name', 'cashflow_adjustment', 'valid_from', 'valid_to']
- search_fields = ['customer_name']
- ordering_fields = ['id', 'customer_name', 'valid_from', 'valid_to']
- ordering = ['-id']
- Override get_queryset() to:
  1. Filter by company: Customer.objects.filter(company=request.user.active_company)
  2. Handle valid_only parameter: if request.query_params.get('valid_only', 'true') == 'true', filter by is_valid()
  3. Return queryset
```

Validation:
```bash
cd backend
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

### 11. Create ProductPrice ViewSet

```
MODIFY backend/bank_transfers/api_views.py
CREATE ProductPriceViewSet class inheriting from viewsets.ModelViewSet

Details:
- serializer_class = ProductPriceSerializer
- permission_classes = [IsAuthenticated, HasFeaturePermission]
- feature_required = 'BASE_TABLES'
- filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
- filterset_fields = ['product_value', 'product_description', 'cap_disp', 'is_inventory_managed', 'valid_from', 'valid_to']
- search_fields = ['product_value', 'product_description']
- ordering_fields = ['id', 'product_value', 'valid_from', 'valid_to']
- ordering = ['-id']
- Override get_queryset() to:
  1. Filter by company: ProductPrice.objects.filter(company=request.user.active_company)
  2. Handle valid_only parameter: if request.query_params.get('valid_only', 'true') == 'true', filter by is_valid()
  3. Return queryset
```

Validation:
```bash
cd backend
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

### 12. Register API Routes

```
MODIFY backend/bank_transfers/urls.py
ADD 3 router registrations for the new ViewSets

Details:
- router.register(r'suppliers', SupplierViewSet, basename='supplier')
- router.register(r'customers', CustomerViewSet, basename='customer')
- router.register(r'product-prices', ProductPriceViewSet, basename='productprice')
- Ensure imports are added at top: from .api_views import SupplierViewSet, CustomerViewSet, ProductPriceViewSet
```

Validation:
```bash
cd backend
python manage.py show_urls | grep -E '(supplier|customer|product-price)'
# Expected: API endpoints listed for all 3 resources
```

---

### 13. Add BASE_TABLES to Frontend Features Constant

```
MODIFY frontend/src/types/features.ts
ADD BASE_TABLES constant to FEATURES object

Details:
- Add line: BASE_TABLES: 'BASE_TABLES',
- Ensure type inference works correctly
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 14. Create Frontend TypeScript Types

```
CREATE frontend/src/types/baseTable.types.ts
CREATE TypeScript interfaces for Supplier, Customer, ProductPrice

Details:
- Export interface Supplier with fields matching backend model
- Export interface Customer with fields matching backend model
- Export interface ProductPrice with fields matching backend model
- Export type BaseTableListResponse<T> = { count: number; next: string | null; previous: string | null; results: T[] }
- Use proper types: string for CharField, number for IntegerField, string for DateField, boolean for BooleanField
- All date fields nullable: valid_from?: string | null
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 15. Create Frontend Zod Schemas

```
CREATE frontend/src/schemas/baseTable.schemas.ts
CREATE Zod validation schemas for all 3 entities

Details:
- Import { z } from 'zod'
- SupplierSchema = z.object({ id: z.number(), partner_name: z.string().min(1), category: z.string(), type: z.string(), valid_from: z.string().nullable(), valid_to: z.string().nullable(), ... })
- CustomerSchema = z.object({ ... })
- ProductPriceSchema = z.object({ ... })
- Export type inference: export type SupplierType = z.infer<typeof SupplierSchema>
- Create list response schemas: SupplierListResponseSchema, CustomerListResponseSchema, ProductPriceListResponseSchema
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 16. Add API Service Methods for Suppliers

```
MODIFY frontend/src/services/api.ts
ADD suppliers API service section

Details:
- Create suppliers object with methods:
  - getAll(params?: { page?: number; page_size?: number; valid_only?: boolean; search?: string }): Promise<BaseTableListResponse<Supplier>>
  - getById(id: number): Promise<Supplier>
  - create(data: Omit<Supplier, 'id' | 'created_at' | 'updated_at' | 'company'>): Promise<Supplier>
  - update(id: number, data: Partial<Supplier>): Promise<Supplier>
  - delete(id: number): Promise<void>
- Parse responses with SupplierSchema and SupplierListResponseSchema
- Export suppliers object from api object
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 17. Add API Service Methods for Customers

```
MODIFY frontend/src/services/api.ts
ADD customers API service section

Details:
- MIRROR task 16 pattern for customers
- Create customers object with same method structure
- Use CustomerSchema for parsing
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 18. Add API Service Methods for Product Prices

```
MODIFY frontend/src/services/api.ts
ADD productPrices API service section

Details:
- MIRROR task 16 pattern for product prices
- Create productPrices object with same method structure
- Use ProductPriceSchema for parsing
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 19. Create React Query Hooks for Suppliers

```
MODIFY frontend/src/hooks/api.ts
CREATE useSuppliers and useSupplierMutations hooks

Details:
- useSuppliers(params) hook using useQuery:
  - queryKey: ['suppliers', params]
  - queryFn: () => api.suppliers.getAll(params)
  - Enable staleTime, cacheTime
- useCreateSupplier() mutation with invalidateQueries(['suppliers'])
- useUpdateSupplier() mutation with invalidateQueries(['suppliers'])
- useDeleteSupplier() mutation with invalidateQueries(['suppliers'])
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 20. Create React Query Hooks for Customers

```
MODIFY frontend/src/hooks/api.ts
CREATE useCustomers and useCustomerMutations hooks

Details:
- MIRROR task 19 pattern for customers
- Use api.customers methods
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 21. Create React Query Hooks for Product Prices

```
MODIFY frontend/src/hooks/api.ts
CREATE useProductPrices and useProductPriceMutations hooks

Details:
- MIRROR task 19 pattern for product prices
- Use api.productPrices methods
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 22. Create Suppliers Component

```
CREATE frontend/src/components/BaseTables/Suppliers.tsx
CREATE React component with MUI DataGrid

Details:
- Import MUI DataGrid, Button, Switch, Dialog, TextField, etc.
- State: page, pageSize, search, validOnly (default: true)
- Use useSuppliers({ page, page_size: pageSize, valid_only: validOnly, search })
- MUI DataGrid columns: id, partner_name, category, type, valid_from, valid_to, actions (edit/delete)
- DataGrid props: rows, columns, pagination, pageSize, onPageChange, onPageSizeChange, loading
- Top bar: Search TextField, "Érvényes rekordok" Switch (validOnly state), "Új beszállító" Button
- Add Dialog for creating new supplier with React Hook Form + Zod validation
- Inline editing via processRowUpdate calling updateSupplier mutation
- Delete confirmation dialog
- Visual validity badge: green chip "Érvényes" if is_valid(), gray chip "Lejárt" otherwise
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
npm run build
# Expected: Build succeeds without errors
```

---

### 23. Create Customers Component

```
CREATE frontend/src/components/BaseTables/Customers.tsx
CREATE React component with MUI DataGrid

Details:
- MIRROR task 22 pattern for customers
- Columns: id, customer_name, cashflow_adjustment, valid_from, valid_to, actions
- Top bar: Search, validity toggle, "Új vevő" button
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
npm run build
# Expected: Build succeeds without errors
```

---

### 24. Create Product Prices Component

```
CREATE frontend/src/components/BaseTables/ProductPrices.tsx
CREATE React component with MUI DataGrid

Details:
- MIRROR task 22 pattern for product prices
- Columns: id, product_value, product_description, uom, uom_hun, purchase_price_usd, purchase_price_huf, markup, sales_price_huf, cap_disp, is_inventory_managed, valid_from, valid_to, actions
- Top bar: Search, validity toggle, "Új termék ár" button
- DataGrid: Set columnVisibilityModel to hide some columns by default (show toggle)
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
npm run build
# Expected: Build succeeds without errors
```

---

### 25. Add Navigation Menu Structure

```
MODIFY frontend/src/components/Layout/Layout.tsx
ADD Alaptáblák main menu item with 3 submenus

Details:
- Import StorageIcon from @mui/icons-material
- Import FEATURES from types/features
- Add feature check: {hasFeature(FEATURES.BASE_TABLES) && (...)}
- Add state: openMenus.baseTables (boolean)
- ListItemButton: "Alaptáblák" with StorageIcon, onClick toggles openMenus.baseTables
- Collapse with 3 ListItemButton children (pl: 4):
  - "Beszállítók" → navigate('/suppliers')
  - "Vevők" → navigate('/customers')
  - "CONMED Árak" → navigate('/product-prices')
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
```

---

### 26. Add Routes

```
MODIFY frontend/src/App.tsx
ADD 3 feature-gated routes

Details:
- Import Suppliers, Customers, ProductPrices components
- Import FEATURES from types/features
- Add conditional routes inside feature check:
  {hasFeature(FEATURES.BASE_TABLES) && (
    <>
      <Route path="/suppliers" element={<Suppliers />} />
      <Route path="/customers" element={<Customers />} />
      <Route path="/product-prices" element={<ProductPrices />} />
    </>
  )}
```

Validation:
```bash
cd frontend
npx tsc --noEmit
# Expected: No TypeScript errors
npm run build
# Expected: Build succeeds without errors
```

---

### 27. Update DATABASE_DOCUMENTATION.md

```
MODIFY /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/DATABASE_DOCUMENTATION.md
ADD 3 new table documentation sections

Details:
- Add "## BASE Tables (BASE_TABLES Feature)" section
- Document bank_transfers_supplier table with all columns
- Document bank_transfers_customer table with all columns
- Document bank_transfers_productprice table with all columns
- Include field descriptions, types, constraints, indexes
- Document is_valid() business logic
- Include relationships (company foreign key)
```

Validation:
```bash
# Manual review of documentation completeness
cat /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/DATABASE_DOCUMENTATION.md | grep -A 20 "BASE Tables"
# Expected: Complete table documentation
```

---

### 28. Update PostgreSQL Database Comments Script

```
MODIFY /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/sql/complete_database_comments_postgresql.sql
ADD COMMENT statements for 3 new tables

Details:
- Add COMMENT ON TABLE bank_transfers_supplier IS '...'
- Add COMMENT ON COLUMN for all supplier columns
- MIRROR pattern for customer table
- MIRROR pattern for productprice table
- Include business logic explanations in comments
```

Validation:
```bash
# Manual review - check SQL syntax
cat /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/sql/complete_database_comments_postgresql.sql | grep -A 5 "supplier"
# Expected: Valid PostgreSQL COMMENT statements
```

---

### 29. Update SQL Server Database Comments Script

```
MODIFY /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/sql/complete_database_comments_sqlserver.sql
ADD extended properties for 3 new tables

Details:
- Use SQL Server EXEC sp_addextendedproperty syntax
- Add table descriptions for supplier, customer, productprice
- Add column descriptions for all fields
- MIRROR pattern from PostgreSQL script but using SQL Server syntax
```

Validation:
```bash
# Manual review - check SQL syntax
cat /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/sql/complete_database_comments_sqlserver.sql | grep -A 5 "supplier"
# Expected: Valid SQL Server extended property statements
```

---

### 30. End-to-End Integration Test

```
VALIDATE entire feature stack

Details:
- Backend: Start Django server, verify endpoints accessible
- Test: curl -H "Authorization: Bearer <token>" http://localhost:8002/api/suppliers/?valid_only=true
- Expected: JSON response with pagination
- Frontend: Start React app, login as ADMIN user
- Navigate: Click Alaptáblák → Beszállítók
- Expected: DataGrid loads with columns, validity toggle works
- Create: Click "Új beszállító", fill form, submit
- Expected: New record appears in table, API call succeeds
- Edit: Double-click cell, edit value, press Enter
- Expected: Update mutation succeeds, optimistic update works
- Delete: Click delete icon, confirm
- Expected: Record deleted, table refreshes
- Validity toggle: Turn off "Érvényes rekordok"
- Expected: Expired records now visible with gray badge
- Repeat for Customers and Product Prices
```

Validation:
```bash
# Backend
cd backend
python manage.py runserver 8002

# Frontend (separate terminal)
cd frontend
npm start

# Manual testing checklist:
# [ ] Login as ADMIN user
# [ ] Alaptáblák menu visible
# [ ] All 3 submenus clickable
# [ ] Suppliers CRUD works
# [ ] Customers CRUD works
# [ ] Product Prices CRUD works
# [ ] Validity toggle filters correctly
# [ ] Search filters work
# [ ] Column filters work (MUI DataGrid built-in)
# [ ] Pagination works
# [ ] Inline editing works
# [ ] Delete confirmation works
# [ ] Visual validity badges display correctly
```

---

## Implementation Strategy

### Dependency Order
1. **Backend Foundation** (Tasks 1-5): Feature flag + models + migration - must complete before any API work
2. **Backend API Layer** (Tasks 6-12): Serializers + ViewSets + routes - requires models to exist
3. **Frontend Types** (Tasks 13-15): Feature constant + interfaces + schemas - independent of backend completion
4. **Frontend API Integration** (Tasks 16-21): API service + React Query hooks - requires backend API running for testing
5. **Frontend UI** (Tasks 22-26): Components + navigation + routes - requires API hooks completed
6. **Documentation** (Tasks 27-29): Database docs - can be done in parallel with frontend work
7. **Integration Testing** (Task 30): End-to-end validation - final step after all code complete

### Rollback Strategy
- If migration fails: Run `python manage.py migrate bank_transfers <previous_migration_number>`
- If API breaks: Feature flag allows disabling via CompanyFeature.is_active = False
- If frontend crashes: Remove routes and menu items, deploy without BaseTables components
- Database rollback: Keep backup before migration, restore if needed

### Progressive Enhancement
- Phase 1: Implement Supplier entity end-to-end (model → API → UI) as proof of concept
- Phase 2: Mirror pattern for Customer entity
- Phase 3: Mirror pattern for ProductPrice entity (most complex, save for last)
- Phase 4: Add Excel-like filtering enhancements
- Phase 5: Add CSV import functionality (future enhancement, not in current scope)

### Risk Mitigation
- **Risk**: Feature permission not enforced → **Mitigation**: HasFeaturePermission used on all ViewSets
- **Risk**: Company isolation broken → **Mitigation**: All models inherit CompanyOwnedTimestampedModel, get_queryset filters by company
- **Risk**: Invalid date logic → **Mitigation**: is_valid() method with explicit null handling
- **Risk**: Frontend type mismatches → **Mitigation**: Zod schemas parse all API responses
- **Risk**: Performance issues with large datasets → **Mitigation**: Indexes on company_id + validity dates, server-side pagination

## Success Criteria

- [ ] All 30 low-level tasks completed and validated
- [ ] Backend tests pass (if tests exist for other features, add for BASE_TABLES)
- [ ] Frontend builds without TypeScript errors
- [ ] Feature only accessible to ADMIN users (403 for others)
- [ ] All CRUD operations work for all 3 entities
- [ ] Validity filtering works correctly (default shows valid only)
- [ ] Excel-like column filtering functional
- [ ] Inline editing functional
- [ ] All 3 documentation files updated and synchronized
- [ ] Manual testing checklist (Task 30) passes completely
