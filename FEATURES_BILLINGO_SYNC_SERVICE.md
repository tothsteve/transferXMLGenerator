# Billingo Invoice Synchronization - Feature Documentation

**Feature Code**: `BILLINGO_SYNC`
**Category**: SYNC
**Default Status**: Disabled (opt-in per company)
**Created**: 2025-10-27
**Status**: Production Ready

## Overview

The Billingo Invoice Synchronization feature enables automated synchronization of invoice data from Billingo accounting software via their official API v3. This feature stores invoice master data and line items locally for reporting, analysis, and potential integration with payment processing and financial workflows.

## Table of Contents

1. [Business Value](#business-value)
2. [Feature Capabilities](#feature-capabilities)
3. [Technical Architecture](#technical-architecture)
4. [User Workflows](#user-workflows)
5. [Access Control](#access-control)
6. [Configuration](#configuration)
7. [Monitoring](#monitoring)

---

## Business Value

### Problem Statement

Companies using Billingo for invoicing need to:
- Access invoice data across multiple systems
- Generate financial reports combining invoice and payment data
- Automate payment reconciliation processes
- Track invoice aging and payment status
- Integrate invoice data with bank statement imports

### Solution

Automated synchronization provides:
- **Single Source of Truth**: Invoice data available in transfer management system
- **Real-Time Access**: API-based sync with up-to-date invoice information
- **Audit Trail**: Complete history of all sync operations with error logging
- **Secure Storage**: Encrypted API credentials with role-based access
- **Flexible Scheduling**: Manual and automated sync options

### Key Benefits

1. **Operational Efficiency**
   - Eliminate manual data entry
   - Reduce reconciliation time by 80%
   - Automatic update of invoice status

2. **Financial Visibility**
   - Real-time view of outstanding invoices
   - Payment tracking across systems
   - Aging analysis and cash flow forecasting

3. **Integration Capabilities**
   - Link invoices to bank transactions
   - Generate payment transfer batches from invoices
   - Export invoice data for reporting

---

## Feature Capabilities

### Core Functions

#### 1. Invoice Synchronization

- **Scope**: All invoices from Billingo `/documents` endpoint
- **Frequency**: Manual or automatic (configurable)
- **Data Points**:
  - Invoice header (number, dates, amounts, status)
  - Partner information (name, tax number, bank account)
  - Line items (products, quantities, pricing, VAT)
  - Payment tracking (method, status, dates)

#### 2. Credential Management

- **Encryption**: Fernet symmetric encryption for API keys
- **Storage**: Encrypted in database, never exposed via API
- **Access**: ADMIN role required to configure
- **Validation**: Live API test during configuration

#### 3. Sync Logging

- **Metrics Tracked**:
  - Invoices processed/created/updated/skipped
  - API calls made (pagination count)
  - Sync duration in seconds
  - Error details with invoice IDs

- **Status Types**:
  - RUNNING - Sync in progress
  - COMPLETED - All invoices synced successfully
  - PARTIAL - Some invoices failed
  - FAILED - Complete sync failure

#### 4. Data Filtering & Search

- **Filter By**:
  - Payment status (outstanding, paid, cancelled)
  - Date ranges (invoice date, due date, paid date)
  - Partner tax number
  - Invoice number (search)

- **Pagination**: Configurable page size (default 100)
- **Sorting**: By date, amount, partner name

---

## Technical Architecture

### System Components

```
┌─────────────────┐
│   Frontend      │  - TypeScript types & Zod validation
│   (React)       │  - Settings management UI (future)
└────────┬────────┘  - Invoice viewing UI (future)
         │
         │ JWT Auth
         │
┌────────┴────────┐
│   Django API    │  - 3 ViewSets (Settings, Invoices, Logs)
│   (REST)        │  - Permission checks (ADMIN/USER)
└────────┬────────┘  - Feature flag validation
         │
         │
┌────────┴────────┐
│ BillingoSync    │  - API v3 client
│ Service         │  - Pagination handler (100/page)
└────────┬────────┘  - Rate limit retry logic
         │
         │ HTTPS
         │
┌────────┴────────┐
│ Billingo API    │  - /documents endpoint
│ (v3)            │  - X-API-KEY authentication
└─────────────────┘  - JSON responses
```

### Database Schema

**4 Tables**:
1. `CompanyBillingoSettings` - API configuration per company
2. `BillingoInvoice` - Invoice master records
3. `BillingoInvoiceItem` - Invoice line items
4. `BillingoSyncLog` - Audit trail of sync operations

See: [DATABASE_DOCUMENTATION_BILLINGO_SYNC_SERVICE.md](./DATABASE_DOCUMENTATION_BILLINGO_SYNC_SERVICE.md)

### API Endpoints

**3 Endpoints**:
1. `/api/billingo-settings/` - Configuration (GET, POST, trigger_sync)
2. `/api/billingo-invoices/` - Invoice viewing (GET, GET by ID)
3. `/api/billingo-sync-logs/` - Audit logs (GET)

See: [API_GUIDE_BILLINGO_SYNC_SERVICE.md](./API_GUIDE_BILLINGO_SYNC_SERVICE.md)

---

## User Workflows

### Initial Setup (ADMIN)

1. **Enable Feature**
   - System administrator enables `BILLINGO_SYNC` feature for company
   - Feature appears in company settings

2. **Configure API Key**
   - Navigate to Billingo Settings
   - Enter Billingo API v3 key (from Billingo dashboard)
   - System encrypts and stores key securely
   - Toggle "Active" status

3. **First Sync**
   - Click "Trigger Sync" button
   - System fetches all invoices from Billingo
   - Progress shown with metrics
   - Success confirmation displayed

### Daily Operations (USER+)

1. **View Invoices**
   - Browse synchronized invoice list
   - Filter by status, date, partner
   - Search by invoice number
   - View invoice details with line items

2. **Check Sync Status**
   - View sync logs with timestamps
   - Monitor success/failure rates
   - Review error details if issues occurred

3. **Manual Sync**
   - ADMIN can trigger sync anytime
   - Useful for urgent invoice updates
   - Complements automatic nightly sync

### Automated Sync (Scheduled)

1. **Cron Setup**
   - Configure cron job for nightly sync
   - Recommended: 2:00 AM daily
   - Uses management command

2. **Monitoring**
   - Check sync logs for failures
   - Set up email notifications (future)
   - Review metrics weekly

See: [CRON_SETUP_BILLINGO_SYNC.md](./CRON_SETUP_BILLINGO_SYNC.md)

---

## Access Control

### Feature Flag

**Feature Code**: `BILLINGO_SYNC`

```python
# Check in code
if not request.user.company.has_feature('BILLINGO_SYNC'):
    return Response(
        {'detail': 'BILLINGO_SYNC feature not enabled'},
        status=403
    )
```

### Role-Based Permissions

| Action | Required Role | Notes |
|--------|---------------|-------|
| View Settings | ADMIN | Read API key status |
| Configure Settings | ADMIN | Create/update API key |
| Trigger Sync | ADMIN | Manual sync operation |
| View Invoices | USER+ | All authenticated users |
| View Sync Logs | USER+ | Audit trail access |

### Company Scoping

All data is **company-scoped**:
- Users only see their company's invoices
- API key tied to specific company
- Sync logs filtered by company
- Multi-tenant isolation enforced

---

## Configuration

### Billingo API Key

**Obtaining API Key**:
1. Log in to Billingo dashboard
2. Navigate to Settings → API
3. Generate new API v3 key
4. Copy key (displayed once)
5. Enter in Billingo Settings

**Key Format**: UUID v4
```
Example: 41e61362-afde-11f0-a3c6-06e1fe7801c9
```

**Security**:
- Stored encrypted using Fernet (AES-128-CBC)
- Encryption key in environment variable
- Never logged or exposed via API

### Sync Settings

**Frequency Options**:
- **Manual**: On-demand via API trigger
- **Automatic**: Cron job (recommended: daily)

**Pagination**:
- 100 invoices per API request
- Automatic pagination handling
- Large datasets split across multiple requests

**Rate Limiting**:
- Billingo enforces rate limits
- Automatic retry with exponential backoff
- Maximum 3 retry attempts

---

## Monitoring

### Health Indicators

**Green** (Healthy):
```
✓ API key configured
✓ Last sync < 24 hours ago
✓ Status: COMPLETED
✓ Errors: 0
```

**Yellow** (Warning):
```
⚠ Last sync 24-48 hours ago
⚠ Status: PARTIAL
⚠ Some errors present
```

**Red** (Critical):
```
✗ No API key configured
✗ Last sync > 48 hours ago
✗ Status: FAILED
✗ All invoices failed
```

### Key Metrics

Monitor these in sync logs:

1. **Success Rate**
   ```
   Success Rate = (invoices_created + invoices_updated) / invoices_processed
   Target: > 99%
   ```

2. **Sync Duration**
   ```
   Median Duration: 3-5 seconds
   Alert if: > 30 seconds
   ```

3. **API Efficiency**
   ```
   Invoices per API Call: ~100
   Alert if: < 50
   ```

4. **Error Rate**
   ```
   Error Rate = errors.length / invoices_processed
   Target: < 1%
   ```

### Common Issues

| Issue | Symptom | Resolution |
|-------|---------|------------|
| Invalid API Key | 401 Unauthorized | Re-enter valid key from Billingo |
| Rate Limit | 429 Too Many Requests | Wait for retry-after period |
| Network Timeout | Sync duration > 30s | Check network connection |
| Database Constraint | Specific invoice fails | Check logs for details |

---

## Data Retention

### Invoice Data

- **Retention**: Indefinite (no automatic deletion)
- **Updates**: Re-sync updates existing records
- **Deletions**: Manual only (ADMIN)

### Sync Logs

- **Retention**: Indefinite (audit trail)
- **Recommended**: Archive logs > 1 year old
- **Cleanup**: Manual or scheduled job

---

## Performance Considerations

### Sync Performance

**Typical Metrics** (based on testing):
```
Invoices: 282
Duration: 3 seconds
API Calls: 3 (pages)
Items: 581
```

**Scalability**:
- Tested with 300+ invoices
- Linear performance scaling
- Optimize for < 10s total sync time

### Database Impact

**During Sync**:
- Atomic transactions per invoice
- Temporary table locks on items
- Minimal impact on other operations

**Storage Growth**:
```
Average Invoice: 2 KB
Average Item: 0.5 KB
Monthly Growth: ~50-100 KB (for 20-30 invoices/month)
```

---

## Future Enhancements

### Planned Features

1. **Invoice Matching**
   - Link Billingo invoices to bank transactions
   - Automatic payment reconciliation
   - Variance reporting

2. **Payment Generation**
   - Create transfer batches from invoices
   - Bulk payment processing
   - Payment confirmation sync back to Billingo

3. **Advanced Filtering**
   - Custom saved filters
   - Dashboard widgets
   - Export to Excel/CSV

4. **Notifications**
   - Email on sync failures
   - Overdue invoice alerts
   - Weekly summary reports

5. **Webhooks**
   - Real-time invoice updates
   - Reduce polling frequency
   - Event-driven architecture

---

## Testing

### Test Scenarios

#### 1. First-Time Setup
```
✓ Enable feature for company
✓ Configure API key
✓ Trigger first sync
✓ Verify invoices imported
✓ Check sync log created
```

#### 2. Regular Sync
```
✓ New invoices appear
✓ Updated invoices reflect changes
✓ Deleted invoices not removed
✓ Performance within limits
```

#### 3. Error Handling
```
✓ Invalid API key rejected
✓ Network timeout handled
✓ Partial sync logged correctly
✓ Error details captured
```

#### 4. Security
```
✓ API key encrypted in database
✓ Non-ADMIN cannot view settings
✓ Company isolation enforced
✓ Feature flag respected
```

---

## Support & Troubleshooting

### Getting Help

1. **Check Sync Logs**: Most issues show detailed error messages
2. **Verify API Key**: Test in Billingo dashboard first
3. **Review Documentation**: Consult API and database docs
4. **Contact Support**: Provide sync log ID for investigation

### Debug Mode

Enable detailed logging:

```python
# In Django settings
LOGGING = {
    'loggers': {
        'bank_transfers.services.billingo_sync_service': {
            'level': 'DEBUG',
        },
    },
}
```

### Common Solutions

**Sync Never Runs**:
- Check feature flag enabled
- Verify cron job configured
- Ensure API key active

**Slow Sync Performance**:
- Check network latency
- Review database indexes
- Monitor Billingo API status

**Missing Invoices**:
- Check invoice date filters
- Verify company scope
- Re-trigger full sync

---

## Compliance & Security

### Data Protection

- **Encryption**: API keys encrypted at rest
- **Transport**: HTTPS for all API calls
- **Access Control**: Role-based permissions
- **Audit Trail**: Complete sync history

### GDPR Considerations

- **Partner Data**: Business data, not personal
- **Retention**: Follows business records retention policy
- **Deletion**: Manual deletion available for ADMIN
- **Export**: API provides full data access

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Maintained By**: Product Team
