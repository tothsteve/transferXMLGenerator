# BASE_TABLES Feature Documentation
## Vertical Slice: Master Data Management System

**Feature Code:** `BASE_TABLES`
**Feature Flag:** ADMIN-only access
**Migration:** `0051_add_base_tables_feature.py`
**Last Updated:** 2025-10-28

## Feature Overview

The BASE_TABLES feature provides master data management functionality for:
- **Suppliers (Beszállítók)**: Partner information with category and type classification
- **Customers (Vevők)**: Customer data with cashflow adjustment tracking
- **Product Prices (CONMED árak)**: Complete product pricing with inventory management

This is a **vertical slice feature** encompassing database schema, REST APIs, frontend components, and business logic for managing time-valid master data records.

---

## Database Schema

### 1. **bank_transfers_supplier**
**Table Comment:** *Company-scoped supplier master data. Stores partner information with validity period management for temporal data tracking.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for supplier record |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company owner of this supplier |
| `partner_name` | VARCHAR(255) | NOT NULL | Legal name of the supplier/partner |
| `category` | VARCHAR(255) | | Supplier category (e.g., "Medical Devices", "IT Services") |
| `type` | VARCHAR(255) | | Supplier type classification (e.g., "Distributor", "Manufacturer") |
| `valid_from` | DATE | NULL | Start date of validity period (NULL = valid from beginning of time) |
| `valid_to` | DATE | NULL | End date of validity period (NULL = valid indefinitely) |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `partner_name` for search functionality
- Index on `category` for category filtering
- Index on `type` for type filtering
- Composite index on `(company_id, valid_from, valid_to)` for validity queries

**Business Rules:**
- `valid_to` must be >= `valid_from` when both are specified
- Record is considered valid when: `(valid_from IS NULL OR valid_from <= today) AND (valid_to IS NULL OR valid_to >= today)`
- Company-scoped isolation enforced at application layer
- Supports temporal queries for historical data analysis

---

### 2. **bank_transfers_customer**
**Table Comment:** *Company-scoped customer master data. Stores customer information with cashflow adjustment days for payment term management and validity tracking.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for customer record |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company owner of this customer |
| `customer_name` | VARCHAR(255) | NOT NULL | Legal name of the customer |
| `cashflow_adjustment` | INTEGER | DEFAULT 0 | Days to adjust cashflow calculations (e.g., payment terms offset) |
| `valid_from` | DATE | NULL | Start date of validity period (NULL = valid from beginning of time) |
| `valid_to` | DATE | NULL | End date of validity period (NULL = valid indefinitely) |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `customer_name` for search functionality
- Index on `cashflow_adjustment` for cashflow analysis
- Composite index on `(company_id, valid_from, valid_to)` for validity queries

**Business Rules:**
- `valid_to` must be >= `valid_from` when both are specified
- `cashflow_adjustment` represents payment term offset in days (negative = early payment, positive = delayed payment)
- Record is considered valid when: `(valid_from IS NULL OR valid_from <= today) AND (valid_to IS NULL OR valid_to >= today)`
- Company-scoped isolation enforced at application layer

---

### 3. **bank_transfers_productprice**
**Table Comment:** *Company-scoped product price master data for CONMED products. Comprehensive pricing information with multi-currency support, markup tracking, unit of measure, and inventory management flags with validity periods.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for product price record |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company owner of this product price |
| `product_value` | VARCHAR(100) | NOT NULL | Product code/SKU (unique identifier for the product) |
| `product_description` | VARCHAR(500) | NOT NULL | Detailed product description |
| `uom` | VARCHAR(50) | | Unit of measure in English (e.g., "piece", "box", "kg") |
| `uom_hun` | VARCHAR(50) | | Unit of measure in Hungarian (e.g., "darab", "doboz", "kg") |
| `purchase_price_usd` | VARCHAR(50) | | Purchase price in USD (stored as string for formatting flexibility) |
| `purchase_price_huf` | VARCHAR(50) | | Purchase price in HUF (stored as string for formatting flexibility) |
| `markup` | VARCHAR(50) | | Markup percentage (e.g., "25%", "1.5x") |
| `sales_price_huf` | VARCHAR(50) | | Sales price in HUF (stored as string for formatting flexibility) |
| `cap_disp` | VARCHAR(100) | | Capital/Disposable classification or additional product categorization |
| `is_inventory_managed` | BOOLEAN | DEFAULT FALSE | Indicates if this product requires inventory tracking |
| `valid_from` | DATE | NULL | Start date of validity period (NULL = valid from beginning of time) |
| `valid_to` | DATE | NULL | End date of validity period (NULL = valid indefinitely) |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `product_value` for product code search
- Index on `product_description` for description search
- Index on `is_inventory_managed` for inventory-tracked product queries
- Composite index on `(company_id, valid_from, valid_to)` for validity queries
- Composite index on `(company_id, product_value)` for product lookup

**Business Rules:**
- `valid_to` must be >= `valid_from` when both are specified
- Prices stored as VARCHAR for formatting flexibility (supports "1,234.56" format, currency symbols, etc.)
- Record is considered valid when: `(valid_from IS NULL OR valid_from <= today) AND (valid_to IS NULL OR valid_to >= today)`
- Company-scoped isolation enforced at application layer
- Product codes (`product_value`) should be unique per company within valid periods (application-level validation)
- `is_inventory_managed` flag enables integration with future inventory management features

**Price Management:**
- Supports historical price tracking through validity periods
- Multiple price records can exist for same product with different validity periods
- Markup calculation: `sales_price_huf = purchase_price_huf × (1 + markup)`
- Multi-currency pricing with USD and HUF support

---

## API Endpoints

### Base URL: `/api/`

### Suppliers API
- **`GET /api/suppliers/`** - List all suppliers with pagination and filtering
  - Query params: `search`, `category`, `type`, `valid_only` (default: true), `ordering`
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`POST /api/suppliers/`** - Create new supplier
  - Body: `{ partner_name, category?, type?, valid_from?, valid_to? }`
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`GET /api/suppliers/{id}/`** - Get supplier details
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`PATCH /api/suppliers/{id}/`** - Update supplier
  - Body: Partial supplier fields
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`DELETE /api/suppliers/{id}/`** - Delete supplier
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

### Customers API
- **`GET /api/customers/`** - List all customers with pagination and filtering
  - Query params: `search`, `valid_only` (default: true), `ordering`
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`POST /api/customers/`** - Create new customer
  - Body: `{ customer_name, cashflow_adjustment?, valid_from?, valid_to? }`
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`GET /api/customers/{id}/`** - Get customer details
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`PATCH /api/customers/{id}/`** - Update customer
  - Body: Partial customer fields
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`DELETE /api/customers/{id}/`** - Delete customer
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

### Product Prices API
- **`GET /api/product-prices/`** - List all product prices with pagination and filtering
  - Query params: `search`, `valid_only` (default: true), `ordering`
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`POST /api/product-prices/`** - Create new product price
  - Body: `{ product_value, product_description, uom?, uom_hun?, purchase_price_usd?, purchase_price_huf?, markup?, sales_price_huf?, cap_disp?, is_inventory_managed?, valid_from?, valid_to? }`
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`GET /api/product-prices/{id}/`** - Get product price details
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`PATCH /api/product-prices/{id}/`** - Update product price
  - Body: Partial product price fields
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

- **`DELETE /api/product-prices/{id}/`** - Delete product price
  - Permission: Requires `BASE_TABLES` feature + ADMIN role

---

## Frontend Components

### Navigation Structure
- **Main Menu:** "Alaptáblák" (Base Tables)
  - **Submenu 1:** "Beszállítók" (Suppliers) → `/base-tables/suppliers`
  - **Submenu 2:** "Vevők" (Customers) → `/base-tables/customers`
  - **Submenu 3:** "CONMED árak" (Product Prices) → `/base-tables/product-prices`

### Component Files
- **`/frontend/src/components/BaseTables/Suppliers.tsx`** - Suppliers management table
- **`/frontend/src/components/BaseTables/Customers.tsx`** - Customers management table
- **`/frontend/src/components/BaseTables/ProductPrices.tsx`** - Product prices management table

### Component Features
**All 3 tables include:**
- Excel-like column header filtering with debounced search (500ms delay)
- Inline row editing with save/cancel actions
- Add new record functionality with seamless inline form
- Valid/Expired record toggle (default: show only valid records)
- CRUD operations with optimistic updates via React Query
- Responsive Material-UI design with sticky headers
- Loading states and error handling with toast notifications
- Company-scoped data isolation (automatic via JWT context)

---

## Backend Implementation

### Django Models
**Location:** `/backend/bank_transfers/models.py` (lines 2265-2502)

**Base Class:** All 3 models extend `CompanyOwnedTimestampedModel` for:
- Automatic company association
- Automatic timestamp management (`created_at`, `updated_at`)
- Company-scoped query methods

**Key Model Methods:**
```python
def is_valid(self) -> bool:
    """Check if record is currently valid based on validity period."""
    today = date.today()
    if self.valid_from and today < self.valid_from:
        return False
    if self.valid_to and today > self.valid_to:
        return False
    return True
```

### Serializers
**Location:** `/backend/bank_transfers/serializers.py` (lines 1567-1698)

**Features:**
- Automatic company assignment on create
- `is_valid` computed field
- Validity period validation (valid_to >= valid_from)
- Company name inclusion for display purposes
- Read-only fields: `id`, `company`, `company_name`, `created_at`, `updated_at`

### ViewSets
**Location:** `/backend/bank_transfers/api_views.py` (lines 2428-2616)

**Features:**
- `RequireBaseTables` permission class (ADMIN-only + feature check)
- `valid_only` query parameter filter (default: true)
- Server-side search with `SearchFilter` on relevant fields
- Server-side ordering with `OrderingFilter`
- Company-scoped querysets (automatic isolation)
- Automatic company assignment on create via `perform_create()`

### Permissions
**Location:** `/backend/bank_transfers/permissions.py` (lines 503-545)

**Permission Logic:**
```python
class RequireBaseTables(FeatureBasedPermission):
    required_features = ['BASE_TABLES']

    def has_permission(self, request, view):
        # 1. Check company context exists
        # 2. Check user has ADMIN role
        # 3. Check BASE_TABLES feature is enabled for company
        # 4. Check user has BASE_TABLES in allowed features
        return user_role == 'ADMIN' and feature_enabled
```

---

## Frontend Implementation

### TypeScript Types
**Location:** `/frontend/src/types/api.ts` (lines 347-397)

**Interfaces:**
- `Supplier` - 12 fields including validity tracking
- `Customer` - 9 fields including cashflow_adjustment
- `ProductPrice` - 16 fields including pricing, UOM, and inventory flag

### Zod Validation Schemas
**Location:** `/frontend/src/schemas/baseTables.schemas.ts`

**Schemas:**
- `SupplierSchema` - Runtime validation for supplier data
- `CustomerSchema` - Runtime validation for customer data
- `ProductPriceSchema` - Runtime validation for product price data
- `ApiResponseSchema` wrapper for paginated responses

### API Service Layer
**Location:** `/frontend/src/services/api.ts` (lines 524-725)

**Service Objects:**
- `suppliersApi` - CRUD methods with Zod validation
- `customersApi` - CRUD methods with Zod validation
- `productPricesApi` - CRUD methods with Zod validation

**Methods per service:**
- `getAll(params?)` - List with filtering
- `getById(id)` - Single record retrieval
- `create(data)` - Create new record
- `update(id, data)` - Update existing record
- `delete(id)` - Delete record

### React Query Hooks
**Location:** `/frontend/src/hooks/api.ts` (lines 1012-1252)

**Hooks per entity (15 total):**
- `useSuppliers(params?)` - Query for supplier list
- `useSupplier(id)` - Query for single supplier
- `useCreateSupplier()` - Mutation for creating supplier
- `useUpdateSupplier()` - Mutation for updating supplier
- `useDeleteSupplier()` - Mutation for deleting supplier
- _(Same pattern for Customers and ProductPrices)_

**Features:**
- Automatic caching and invalidation
- Optimistic updates
- Error handling with retries
- Loading and error states
- Zod validation on responses

---

## Testing & Usage

### Backend Testing
```bash
# Check models and migrations
python manage.py check
python manage.py makemigrations --dry-run

# Test API endpoints
curl -X GET http://localhost:8002/api/suppliers/ \
  -H "Authorization: Bearer <token>"

# Create supplier
curl -X POST http://localhost:8002/api/suppliers/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"partner_name": "Test Supplier", "category": "Medical"}'
```

### Frontend Testing
```bash
# Start development server
cd frontend
npx react-scripts start

# Navigate to:
# http://localhost:3000/base-tables/suppliers
# http://localhost:3000/base-tables/customers
# http://localhost:3000/base-tables/product-prices
```

---

## Feature Flag Management

### Enabling BASE_TABLES Feature
**Backend:** Feature template created automatically via migration 0051

**Django Admin:**
1. Navigate to **CompanyFeature** admin
2. Select target company
3. Enable **BASE_TABLES** feature template
4. Save

**API Method:**
```python
from bank_transfers.models import CompanyFeature, FeatureTemplate

# Enable for company
template = FeatureTemplate.objects.get(feature_code='BASE_TABLES')
CompanyFeature.objects.create(
    company=company,
    feature_template=template,
    is_enabled=True
)
```

### Permission Check Flow
1. **User Authentication:** JWT token validation
2. **Company Context:** Extract active company from token
3. **Feature Check:** Verify BASE_TABLES enabled for company
4. **Role Check:** Verify user has ADMIN role for company
5. **Permission Grant:** Allow access if all checks pass

---

## Migration Details

**Migration File:** `0051_add_base_tables_feature.py`

**Operations:**
1. Create `bank_transfers_supplier` table
2. Create `bank_transfers_customer` table
3. Create `bank_transfers_productprice` table
4. Create `BASE_TABLES` feature template with:
   - `feature_code`: "BASE_TABLES"
   - `display_name`: "Alaptáblák kezelése"
   - `description`: "Beszállítók, Vevők és CONMED árak alaptáblák kezelése (ADMIN jogosultság szükséges)"
   - `category`: "GENERAL"
   - `default_enabled`: False
   - `is_system_critical`: False

---

## Integration Points

### Current Integrations
- **Authentication System:** JWT-based company context
- **Permission System:** Feature flags + role-based access control
- **Multi-Company Architecture:** Complete data isolation

### Future Integration Opportunities
1. **NAV Invoice Matching:** Link suppliers to NAV invoice partners
2. **Transfer Beneficiaries:** Auto-populate beneficiaries from suppliers
3. **Inventory Management:** Use ProductPrice.is_inventory_managed flag
4. **Cashflow Forecasting:** Use Customer.cashflow_adjustment for predictions
5. **Pricing History:** Temporal queries for price change analysis
6. **Bulk Import/Export:** Excel import for mass data updates

---

## Known Limitations

1. **Search Performance:** Full-text search may be slow on large datasets (consider PostgreSQL full-text search)
2. **Price Calculations:** Stored as strings (no automatic markup calculation)
3. **Duplicate Prevention:** No unique constraint on product_value per company (application-level validation only)
4. **Audit Trail:** No change history tracking (consider django-simple-history)
5. **Bulk Operations:** No bulk create/update/delete endpoints

---

## Future Enhancements

### Phase 2 Features
- [ ] Bulk import from Excel/CSV
- [ ] Export to Excel/CSV
- [ ] Advanced filtering (date ranges, multi-select categories)
- [ ] Audit trail with django-simple-history
- [ ] Duplicate detection and merge functionality

### Phase 3 Features
- [ ] Price calculation automation (auto-compute sales price from markup)
- [ ] Integration with NAV invoice system
- [ ] Integration with beneficiary management
- [ ] Inventory tracking integration
- [ ] Advanced reporting and analytics

---

## Documentation Files

This vertical slice documentation should be read in conjunction with:
- `/DATABASE_DOCUMENTATION.md` - Complete database schema reference
- `/FEATURES.md` - All feature implementations
- `/API_GUIDE.md` - Complete API documentation
- `/frontend/CLAUDE-REACT.md` - React development guidelines
- `/backend/CLAUDE-PYTHON-BASIC.md` - Django development guidelines
