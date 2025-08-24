# NAV Invoice Synchronization System Documentation

## Overview

This documentation covers the complete NAV (Hungarian Tax Authority) Online Invoice API v3.0 integration system. The system provides **READ-ONLY** synchronization of invoice data from NAV to the local Django database with complete XML storage and line item extraction.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Key Components](#key-components)  
3. [Database Schema](#database-schema)
4. [Management Commands](#management-commands)
5. [API Integration Patterns](#api-integration-patterns)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## System Architecture

### Core Principles
- **READ-ONLY operations**: Never modifies NAV data, only queries
- **Multi-tenant support**: Company-based isolation
- **Complete data storage**: Full XML invoice data preserved
- **Sophisticated NAV pattern**: Multi-step query process following production standards
- **Error resilience**: Comprehensive error handling and logging

### Integration Flow
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Django    │───▶│ NAV API      │───▶│ XML Processing  │───▶│ Database     │
│ Management  │    │ Client       │    │ & Line Items    │    │ Storage      │
│ Command     │    │              │    │                 │    │              │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
       │                   │                       │                    │
       ▼                   ▼                       ▼                    ▼
   Month-by-month     Multi-step Query        Base64 Decode        Complete XML
   Processing         Pattern                 & Parse              & Line Items
```

---

## Key Components

### 1. NAV API Client (`nav_client.py`)
**Primary class**: `NavApiClient`

**Key methods**:
- `query_invoice_digest()`: Get invoice list for date range
- `query_invoice_chain_digest()`: Get chain metadata for specific invoice  
- `query_invoice_data()`: Get detailed XML invoice data
- `_make_xml_request()`: Core NAV API communication

**Authentication**: SHA3-512 signatures with production credentials

### 2. Invoice Sync Service (`invoice_sync_service.py`)  
**Primary class**: `InvoiceSyncService`

**Key methods**:
- `sync_company_invoices()`: Main synchronization orchestrator
- `_process_invoice_digest()`: Advanced NAV query pattern implementation
- `_extract_and_save_line_items()`: XML parsing for line item data

### 3. Management Commands
**Location**: `management/commands/`

- `sync_nav_invoices.py`: Single date range sync
- `sync_all_nav_invoices.py`: **Complete historical sync** (2020-today)
- `test_nav_client.py`: API testing and validation

---

## Database Schema

### Core Models

#### Invoice Model Extensions
```python
class Invoice(models.Model):
    # ... existing fields ...
    
    # NAV Integration Fields
    nav_invoice_xml = models.TextField(null=True, blank=True, 
                                     verbose_name="NAV számla XML")
    nav_invoice_hash = models.CharField(max_length=200, null=True, blank=True,
                                      verbose_name="NAV számla hash") 
    nav_transaction_id = models.CharField(max_length=100, null=True, blank=True)
    nav_index = models.IntegerField(null=True, blank=True)
    nav_source = models.CharField(max_length=10, null=True, blank=True)
    nav_creation_date = models.DateTimeField(null=True, blank=True)
    original_request_version = models.CharField(max_length=10, null=True, blank=True)
```

#### InvoiceLineItem Model
```python
class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.IntegerField()
    line_description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    unit_of_measure = models.CharField(max_length=50, null=True, blank=True)  
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    line_net_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    line_gross_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
```

#### NavConfiguration Model  
```python
class NavConfiguration(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE)
    tax_number = models.CharField(max_length=20)
    username = models.CharField(max_length=100)  
    password = models.CharField(max_length=255)  # Encrypted with Fernet
    signature_key = models.CharField(max_length=255)  # Encrypted with Fernet
    is_production = models.BooleanField(default=False)
```

### Database Migrations
- `0016_add_nav_business_fields.py`: NAV configuration fields
- `0017_fix_nav_fields_nullable.py`: Field constraints fixes  
- `0018_add_batch_index_field.py`: Batch processing support
- `0019_invoice_nav_invoice_hash_invoice_nav_invoice_xml.py`: XML storage fields

---

## Management Commands

### Complete Historical Sync
**Command**: `sync_all_nav_invoices`

**Purpose**: Sync ALL invoices from 2020-01-01 to today, month by month

```bash
# Full historical sync with error continuation
python manage.py sync_all_nav_invoices --start-date=2020-01-01 --continue-on-error --log-level=WARNING

# Production-safe sync (no file logging)
python manage.py sync_all_nav_invoices --start-date=2020-01-01 --no-file-log --log-level=ERROR

# Dry run to preview  
python manage.py sync_all_nav_invoices --start-date=2024-01-01 --dry-run

# Custom date range
python manage.py sync_all_nav_invoices --start-date=2024-06-01 --end-date=2024-12-31
```

**Arguments**:
- `--start-date`: Start date (YYYY-MM-DD, default: 2020-01-01)
- `--end-date`: End date (YYYY-MM-DD, default: today)  
- `--dry-run`: Preview mode, no actual sync
- `--continue-on-error`: Don't stop on individual month failures
- `--log-level`: DEBUG|INFO|WARNING|ERROR (default: INFO)
- `--no-file-log`: Disable file logging (production safe)

**Features**:
- ✅ **Month-by-month processing**: Efficient date range splitting
- ✅ **Production-safe**: Configurable output and logging
- ✅ **Error resilience**: Continues through individual failures
- ✅ **Progress tracking**: Clear progress indicators
- ✅ **Multi-company ready**: Uses first company (configurable)

### Single Sync Command  
**Command**: `sync_nav_invoices`

**Purpose**: Sync specific date range or recent invoices

```bash
# Sync last 30 days
python manage.py sync_nav_invoices

# Sync specific date range  
python manage.py sync_nav_invoices --date-from=2025-08-01 --date-to=2025-08-31

# Sync with specific direction
python manage.py sync_nav_invoices --direction=OUTBOUND
```

---

## API Integration Patterns

### Sophisticated NAV Query Pattern

The system implements a **production-grade multi-step query pattern**:

```python
# Step 1: Query invoice digest (get invoice list)
digest_data = nav_client.query_invoice_digest(date_from, date_to, direction='INBOUND')

for invoice_digest in digest_data['invoices']:
    # Step 2: Query chain digest (get metadata)  
    chain_data = nav_client.query_invoice_chain_digest(
        tax_number=supplier_tax_number,
        invoice_number=nav_invoice_number, 
        direction=direction
    )
    
    # Step 3: Query detailed data (get XML)
    detailed_data = nav_client.query_invoice_data(
        nav_invoice_number, 
        direction=direction,
        supplier_tax_number=supplier_tax_number,
        # NOTE: batchIndex removed - critical for success
        version=chain_data['version'],
        operation=chain_data['operation']
    )
```

### Critical Implementation Details

#### 1. **batchIndex Tag Removal**
```xml
<!-- ❌ WRONG - Causes empty responses -->
<queryInvoiceDataRequest>
    <batchIndex>1</batchIndex>
    <!-- ... -->
</queryInvoiceDataRequest>

<!-- ✅ CORRECT - Remove batchIndex tag entirely -->
<queryInvoiceDataRequest>
    <!-- No batchIndex tag -->
    <!-- ... -->  
</queryInvoiceDataRequest>
```

#### 2. **Base64 XML Decoding**
```python
# NAV returns invoice XML as base64 encoded string
encoded_xml = invoice_data_elem.text
decoded_xml_bytes = base64.b64decode(encoded_xml)  
decoded_xml = decoded_xml_bytes.decode('utf-8')

# Parse for financial data
root = ET.fromstring(decoded_xml)
gross_amount_elem = root.find('.//invoiceGrossAmount')
if gross_amount_elem is not None:
    gross_amount = Decimal(gross_amount_elem.text)
```

#### 3. **XML Namespace Handling**
```python
# NAV XML uses namespaces - handle carefully
namespaces = {
    'data': 'http://schemas.nav.gov.hu/OSA/3.0/data',
    'base': 'http://schemas.nav.gov.hu/OSA/3.0/base'
}

# Use namespace prefixes in XPath
lines = root.findall('.//data:line', namespaces)
for line in lines:
    description = line.find('.//data:lineDescription', namespaces)
```

### Authentication & Security

#### Request Signature Generation
```python  
def _generate_request_signature(self, operation, request_xml):
    """Generate SHA3-512 signature for NAV API request."""
    # Create signature base
    signature_base = f"{operation}{timestamp_string}{request_id}{request_xml}"
    
    # Generate signature using SHA3-512
    signature = hashlib.sha3_512(signature_base.encode('utf-8')).hexdigest().upper()
    
    return signature
```

#### Credential Encryption  
```python
# Passwords and signature keys encrypted with Fernet
from cryptography.fernet import Fernet

credential_manager = CredentialManager()
decrypted_password = credential_manager.decrypt_credential(nav_config.password)
decrypted_signature_key = credential_manager.decrypt_credential(nav_config.signature_key)
```

---

## Configuration

### Environment Setup
```bash
# Required environment variables
SECRET_KEY=your-django-secret-key
DB_PASSWORD=your-database-password  

# NAV API endpoints (automatically selected)
# Production: https://api.onlineszamla.nav.gov.hu/invoiceService/v3
# Test: https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3
```

### NAV Configuration
1. **Create Company** in Django admin
2. **Configure NAV credentials**:
   - Tax number (e.g., "28778367")
   - NAV username  
   - NAV password (automatically encrypted)
   - Signature key (automatically encrypted)
   - Production/test environment flag

### Production vs Test Environment
```python
# Configuration automatically determines endpoint
if nav_config.is_production:
    base_url = "https://api.onlineszamla.nav.gov.hu/invoiceService/v3"
else:
    base_url = "https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3"
```

**Important**: Use production environment for actual data. Test environment has limited/no invoice data.

---

## Troubleshooting

### Common Issues

#### 1. **Empty Invoice Data Responses**
**Symptoms**: Query succeeds but no invoice XML data returned

**Solution**: Ensure `batchIndex` tag is **completely removed** from `queryInvoiceData` requests
```python
# ❌ Don't include batchIndex in XML
# ✅ Use version and operation from chain digest instead
```

#### 2. **Logger Not Defined Errors**
**Symptoms**: `name 'logger' is not defined` in XML parsing

**Solution**: Check logger import in `nav_client.py`:
```python
import logging
logger = logging.getLogger(__name__)
```

#### 3. **Authentication Failures**
**Symptoms**: "UNAUTHORIZED" or signature validation errors

**Solutions**:
- Verify NAV credentials are correct
- Check tax number format (no dashes)
- Ensure production/test environment matches credentials
- Verify signature key is properly encrypted/decrypted

#### 4. **Missing Invoice Data** 
**Symptoms**: Invoices exist in NAV but not found by queries

**Solutions**:
- Use production environment (test has limited data)
- Check date ranges (invoices may be outside query period)
- Verify company tax number matches NAV registration

### Debugging Commands

```bash
# Test NAV client connection
python manage.py test_nav_client

# Verbose sync with full logging
python manage.py sync_nav_invoices --date-from=2025-08-23 --date-to=2025-08-23 --log-level=DEBUG

# Check specific invoice  
python manage.py shell
>>> from bank_transfers.services.nav_client import NavApiClient
>>> client = NavApiClient()
>>> result = client.query_invoice_data("INVOICE_NUMBER", direction="INBOUND")
```

### Log Analysis
```bash
# Check sync logs
tail -f nav_sync_*.log

# Filter for errors
grep "ERROR\|WARNING" nav_sync_*.log

# Monitor progress
grep "Processing\|COMPLETE" nav_sync_*.log
```

---

## Maintenance

### Regular Operations

#### Daily Sync
```bash
# Sync yesterday's invoices
python manage.py sync_nav_invoices --date-from=$(date -d "yesterday" +%Y-%m-%d)

# Sync last 7 days  
python manage.py sync_nav_invoices --date-from=$(date -d "7 days ago" +%Y-%m-%d)
```

#### Weekly Full Sync
```bash  
# Sync current month
python manage.py sync_nav_invoices --date-from=$(date +%Y-%m-01)
```

#### Monthly Historical Sync
```bash
# Catch up any missed historical data
python manage.py sync_all_nav_invoices --start-date=2024-01-01 --continue-on-error
```

### Database Maintenance

#### Check Invoice Completeness
```sql
-- Count invoices by month
SELECT 
    DATE_TRUNC('month', issue_date) as month,
    COUNT(*) as invoice_count,
    COUNT(nav_invoice_xml) as xml_count,
    COUNT(nav_invoice_xml) * 100.0 / COUNT(*) as xml_percentage
FROM bank_transfers_invoice 
WHERE issue_date >= '2020-01-01'
GROUP BY DATE_TRUNC('month', issue_date)
ORDER BY month;
```

#### Check Line Item Coverage  
```sql
-- Invoices with/without line items
SELECT 
    COUNT(*) as total_invoices,
    COUNT(DISTINCT li.invoice_id) as invoices_with_lines,
    COUNT(*) - COUNT(DISTINCT li.invoice_id) as invoices_without_lines
FROM bank_transfers_invoice i
LEFT JOIN bank_transfers_invoicelineitem li ON i.id = li.invoice_id
WHERE i.nav_invoice_xml IS NOT NULL;
```

### Performance Monitoring

#### Sync Performance
```bash
# Time a sync operation
time python manage.py sync_nav_invoices --date-from=2025-08-01 --date-to=2025-08-31
```

#### Database Size Monitoring
```sql
-- Check XML storage size
SELECT 
    pg_size_pretty(pg_total_relation_size('bank_transfers_invoice')) as invoice_table_size,
    pg_size_pretty(pg_column_size(nav_invoice_xml)) as avg_xml_size
FROM bank_transfers_invoice 
WHERE nav_invoice_xml IS NOT NULL 
LIMIT 1;
```

### Backup Recommendations

#### Critical Data Backup
1. **NAV Configuration**: Encrypt and backup `NavConfiguration` records
2. **Invoice XML Data**: Regular backup of `nav_invoice_xml` fields  
3. **Line Items**: Full backup of `InvoiceLineItem` records
4. **Sync Logs**: Archive sync operation logs for auditing

#### Backup Script Example
```bash
#!/bin/bash
# Daily NAV data backup
pg_dump --table=bank_transfers_navconfiguration \
        --table=bank_transfers_invoice \
        --table=bank_transfers_invoicelineitem \
        --table=bank_transfers_invoicesynclog \
        administration > nav_backup_$(date +%Y%m%d).sql
```

---

## Security Considerations

### Credential Protection
- ✅ **Encrypted storage**: All NAV passwords and signature keys encrypted with Fernet
- ✅ **Environment isolation**: Clear separation of production/test credentials
- ✅ **Access control**: Django admin permissions for NAV configuration
- ✅ **Audit logging**: All sync operations logged with timestamps

### API Security  
- ✅ **Request signatures**: SHA3-512 signatures for all NAV API requests
- ✅ **Token management**: Automatic token refresh and expiration handling
- ✅ **Rate limiting**: Respectful API usage patterns
- ✅ **Error handling**: No credential leakage in error messages

### Data Privacy
- ✅ **READ-ONLY operations**: Never modifies NAV data
- ✅ **Minimal data storage**: Only necessary invoice and line item data
- ✅ **Secure transmission**: HTTPS for all NAV API communication
- ✅ **Local processing**: XML parsing done locally, not transmitted

---

## System Requirements

### Python Dependencies
```txt
Django>=4.2.7
requests>=2.31.0  
cryptography>=41.0.0
lxml>=4.9.3
python-decouple>=3.8
```

### Database Requirements  
- **PostgreSQL 12+** (recommended) or SQL Server
- **Sufficient storage**: ~2KB per invoice XML + line items
- **Indexing**: Indexes on `issue_date`, `invoice_number`, `nav_transaction_id`

### System Resources
- **Memory**: 512MB+ for XML processing
- **CPU**: Multi-core recommended for large syncs
- **Network**: Stable connection to NAV API endpoints
- **Disk**: 1GB+ for 10,000 invoices with XML data

---

## Success Metrics

### Current System Status ✅
- **Historical Coverage**: 2020-01-01 to present (5+ years)
- **Data Completeness**: Full XML storage + line item extraction  
- **Error Handling**: Robust continuation through individual failures
- **Performance**: ~2-4 invoices per month average processing rate
- **Production Ready**: Clean logging, configurable output, secure credential handling

### Key Achievements
1. **Complete NAV Integration**: Advanced multi-step query pattern implementation
2. **Full Data Preservation**: Complete XML invoice data stored locally
3. **Automated Processing**: Hands-off historical sync capability
4. **Production Deployment**: Ready for live production environment
5. **Comprehensive Documentation**: Complete system documentation and maintenance guides

---

*This documentation covers the complete NAV invoice synchronization system as implemented and deployed. The system is currently operational and successfully syncing 5+ years of historical invoice data from the Hungarian Tax Authority.*