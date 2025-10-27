# Billingo Invoice Synchronization Service - Complete Documentation

**Status**: ✅ Production Ready
**Version**: 1.0
**Created**: 2025-10-27
**Last Updated**: 2025-10-27

---

## 🎯 Quick Start

### What is this?

The Billingo Invoice Synchronization Service automatically imports invoice data from Billingo accounting software into your transfer management system, enabling unified financial reporting and payment processing.

### Key Features

- ✅ **Automated Sync** - Scheduled daily imports via cron
- ✅ **282 Invoices Tested** - Successfully synced in production
- ✅ **Secure Storage** - Fernet-encrypted API keys
- ✅ **Complete Audit Trail** - Detailed sync logs with metrics
- ✅ **Multi-Company Support** - Company-scoped data isolation
- ✅ **Feature Flag Controlled** - Opt-in per company

---

## 📚 Documentation Index

This service includes comprehensive documentation split into focused, standalone files:

### 1. [Database Schema Documentation](./DATABASE_DOCUMENTATION_BILLINGO_SYNC_SERVICE.md)

**What's Inside**:
- 4 database tables with complete field descriptions
- Indexes and constraints
- Sample SQL queries
- Security considerations
- Migration history

**Use When**:
- Understanding the data model
- Writing custom queries
- Troubleshooting database issues
- Planning integrations

### 2. [API Endpoint Documentation](./API_GUIDE_BILLINGO_SYNC_SERVICE.md)

**What's Inside**:
- 3 REST API endpoints
- Request/response examples
- Authentication guide
- Error handling
- Complete curl testing workflow

**Use When**:
- Integrating with the API
- Testing endpoints manually
- Debugging API issues
- Building frontend UI

### 3. [Feature Documentation](./FEATURES_BILLINGO_SYNC_SERVICE.md)

**What's Inside**:
- Business value and use cases
- Feature capabilities
- Technical architecture
- User workflows (ADMIN and USER)
- Access control and permissions
- Monitoring and health checks

**Use When**:
- Understanding business requirements
- Training users
- Planning feature enhancements
- Troubleshooting workflows

### 4. [Cron Setup Guide](./CRON_SETUP_BILLINGO_SYNC.md)

**What's Inside**:
- **Railway.app Production** - APScheduler automatic setup (recommended)
- Traditional cron configuration for Linux/macOS/VPS
- Schedule recommendations
- Testing procedures
- Monitoring and logs
- Troubleshooting common issues

**Use When**:
- Setting up automated sync
- Deploying to Railway production (automatic)
- Deploying to VPS/local (manual cron)
- Debugging scheduling issues
- Configuring notifications

---

## 🚀 Implementation Summary

### Backend (Django)

**Models** (4):
```
├── CompanyBillingoSettings  (API configuration)
├── BillingoInvoice          (Invoice master data)
├── BillingoInvoiceItem      (Invoice line items)
└── BillingoSyncLog          (Audit trail)
```

**Services** (1):
```
└── BillingoSyncService
    ├── sync_all_companies()
    ├── sync_company()
    ├── _fetch_documents_page()  (pagination)
    └── _process_invoice()       (atomic transactions)
```

**Management Command** (1):
```bash
python manage.py sync_billingo_invoices [--company-id X] [--verbose]
```

**API Endpoints** (3):
```
GET    /api/billingo-settings/              # List settings
POST   /api/billingo-settings/              # Create/update
POST   /api/billingo-settings/trigger_sync/ # Manual sync

GET    /api/billingo-invoices/              # List invoices
GET    /api/billingo-invoices/{id}/         # Invoice detail

GET    /api/billingo-sync-logs/             # Sync history
```

**Migrations** (3):
```
0046_add_billingo_models.py       # Create tables
0047_add_billingo_sync_feature.py # Add feature flag
0048_allow_null_entitlement.py    # Bug fix
```

### Frontend (React + TypeScript)

**TypeScript Types** (7):
```typescript
BillingoInvoiceItem
BillingoInvoice
BillingoInvoiceDetail
CompanyBillingoSettings
CompanyBillingoSettingsInput
BillingoSyncLog
BillingoSyncTriggerResponse
```

**Zod Schemas** (7):
```typescript
BillingoInvoiceItemSchema
BillingoInvoiceSchema
BillingoInvoiceDetailSchema
CompanyBillingoSettingsSchema
CompanyBillingoSettingsInputSchema
BillingoSyncLogSchema
BillingoSyncTriggerResponseSchema
```

**Files Modified**:
```
frontend/src/types/api.ts         (+125 lines)
frontend/src/schemas/api.schemas.ts (+140 lines)
```

---

## ✅ Testing Results

### Production Test (2025-10-27)

**Company**: IT Cardigan Kft. (ID: 4)
**API Key**: Configured and encrypted
**Result**: ✅ SUCCESS

```
Invoices Processed: 282
Invoices Created:   281
Invoices Updated:   1
Invoices Skipped:   0
Line Items:         581
API Calls:          3 (3 pages × 100 invoices)
Duration:           3 seconds
Errors:             0
```

### API Endpoints Verified

- ✅ POST `/api/billingo-settings/` - Settings created
- ✅ POST `/api/billingo-settings/trigger_sync/` - Sync triggered
- ✅ GET `/api/billingo-invoices/` - 282 invoices listed
- ✅ GET `/api/billingo-invoices/111324303/` - Detail view works
- ✅ GET `/api/billingo-sync-logs/` - 2 sync logs recorded

### Bug Fixes Applied

**Issue**: `entitlement` field NULL constraint
**Solution**: Migration 0048 - Allow NULL values
**Status**: ✅ Fixed and deployed

---

## 🔧 Quick Reference

### Enable Feature for Company

```python
python manage.py shell

from bank_transfers.models import Company, FeatureTemplate
company = Company.objects.get(id=4)
feature = FeatureTemplate.objects.get(feature_code='BILLINGO_SYNC')
company.enable_feature(feature)
```

### Configure API Key

```bash
# Via curl
read TOKEN < /tmp/clean_token.txt; curl -s -X POST http://localhost:8002/api/billingo-settings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"api_key_input\":\"YOUR_API_KEY\",\"is_active\":true}"
```

### Trigger Manual Sync

```bash
# Via management command
python manage.py sync_billingo_invoices --company-id 4 --verbose

# Via API
read TOKEN < /tmp/clean_token.txt; curl -s -X POST http://localhost:8002/api/billingo-settings/trigger_sync/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}"
```

### Check Sync Status

```python
from bank_transfers.models import BillingoSyncLog

# Last sync
log = BillingoSyncLog.objects.filter(company_id=4).order_by('-started_at').first()
print(f"Status: {log.status}")
print(f"Invoices: {log.invoices_processed}")
print(f"Duration: {log.sync_duration_seconds}s")
print(f"Errors: {len(log.errors_parsed)}")
```

### Setup Automated Sync

**Railway.app Production (Automatic)**:
```
✅ Already configured! Scheduler starts automatically when deployed to Railway.
   - Schedule: Daily at 2:00 AM
   - File: backend/bank_transfers/apps.py (APScheduler)
   - No setup required
```

**Traditional Cron (Linux/macOS/VPS)**:
```bash
crontab -e

# Add this line:
0 2 * * * cd /path/to/backend && python manage.py sync_billingo_invoices >> /var/log/billingo_sync.log 2>&1
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Actions                         │
└───────┬──────────────────────────────────────────────┬──────┘
        │                                               │
        │ Manual Trigger (API)              Automated (Cron)
        │                                               │
┌───────┴────────┐                           ┌─────────┴───────┐
│  Django API    │                           │  Management     │
│  ViewSet       │                           │  Command        │
└───────┬────────┘                           └─────────┬───────┘
        │                                               │
        └─────────────────┬───────────────────────────┘
                          │
                ┌─────────┴──────────┐
                │  BillingoSync      │
                │  Service           │
                └─────────┬──────────┘
                          │
                ┌─────────┴──────────┐
                │  Billingo API v3   │
                │  (HTTPS)           │
                └─────────┬──────────┘
                          │
                ┌─────────┴──────────┐
                │  Local Database    │
                │  - Invoices        │
                │  - Items           │
                │  - Logs            │
                └────────────────────┘
```

---

## 🔐 Security Features

1. **API Key Encryption**
   - Fernet symmetric encryption (AES-128-CBC)
   - Key stored in environment variable
   - Never exposed via API responses

2. **Role-Based Access**
   - ADMIN: Configure settings, trigger sync
   - USER+: View invoices and logs
   - Company-scoped data isolation

3. **Feature Flag Control**
   - Must be enabled per company
   - Prevents unauthorized access
   - Easy enable/disable

4. **Audit Trail**
   - All sync operations logged
   - Detailed error tracking
   - Timestamp and metrics recorded

---

## 🎯 Common Use Cases

### 1. First-Time Setup

**Who**: System Administrator (ADMIN role)

**Steps**:
1. Enable `BILLINGO_SYNC` feature for company
2. Configure Billingo API key in settings
3. Trigger first manual sync
4. Verify invoices imported correctly
5. Set up automated nightly cron job

**Docs**: [Cron Setup Guide](./CRON_SETUP_BILLINGO_SYNC.md)

### 2. Daily Operations

**Who**: Financial Staff (USER+ role)

**Actions**:
- View synchronized invoice list
- Search for specific invoices
- Check payment status
- Review invoice details and line items
- Export data for reporting

**Docs**: [Feature Documentation](./FEATURES_BILLINGO_SYNC_SERVICE.md)

### 3. Troubleshooting

**Who**: Developer/Support

**Scenarios**:
- Sync failures
- Missing invoices
- API authentication errors
- Performance issues

**Docs**: [API Guide](./API_GUIDE_BILLINGO_SYNC_SERVICE.md), [Database Documentation](./DATABASE_DOCUMENTATION_BILLINGO_SYNC_SERVICE.md)

### 4. Integration Development

**Who**: Frontend/Backend Developers

**Tasks**:
- Build invoice viewing UI
- Create payment matching features
- Generate reports
- Export invoice data

**Docs**: [API Guide](./API_GUIDE_BILLINGO_SYNC_SERVICE.md), [Database Documentation](./DATABASE_DOCUMENTATION_BILLINGO_SYNC_SERVICE.md)

---

## 📈 Performance Metrics

### Tested Configuration

```
Dataset Size:     282 invoices
Line Items:       581 items
API Calls:        3 (100 invoices per page)
Total Duration:   3 seconds
Success Rate:     100%
```

### Scalability Estimates

| Invoices | API Calls | Est. Duration | Memory Usage |
|----------|-----------|---------------|--------------|
| 100      | 1         | ~1s           | ~50 MB       |
| 500      | 5         | ~5s           | ~100 MB      |
| 1000     | 10        | ~10s          | ~150 MB      |
| 5000     | 50        | ~50s          | ~300 MB      |

**Recommendation**: For >1000 invoices, consider splitting sync across multiple cron jobs per company.

---

## 🔄 Migration Path

### From Manual Entry

1. Export existing invoice data from Billingo
2. Enable `BILLINGO_SYNC` feature
3. Configure API key
4. Run initial sync
5. Validate data completeness
6. Switch to automated sync

### From Other Systems

1. Map data fields to Billingo schema
2. Migrate historical data (if needed)
3. Set up Billingo as primary source
4. Configure sync service
5. Decommission old system

---

## 🆘 Support & Help

### Documentation

- 📖 [Database Schema](./DATABASE_DOCUMENTATION_BILLINGO_SYNC_SERVICE.md)
- 🔌 [API Endpoints](./API_GUIDE_BILLINGO_SYNC_SERVICE.md)
- ⚙️ [Feature Guide](./FEATURES_BILLINGO_SYNC_SERVICE.md)
- ⏰ [Cron Setup](./CRON_SETUP_BILLINGO_SYNC.md)

### Quick Links

- **Billingo API Docs**: https://billingo.hu/api/v3
- **Billingo Dashboard**: https://app.billingo.hu
- **Billingo Support**: support@billingo.hu

### Internal Contacts

- **Implementation**: Backend Team
- **API Issues**: DevOps Team
- **Feature Requests**: Product Team
- **User Training**: Support Team

---

## 📝 Change Log

### Version 1.0 (2025-10-27)

**Initial Release** - Production Ready

✅ **Backend**:
- 4 database models created
- 3 migrations applied
- BillingoSyncService implemented
- Management command created
- 3 API endpoints registered
- Feature flag added

✅ **Frontend**:
- 7 TypeScript types defined
- 7 Zod schemas created
- TypeScript compilation verified

✅ **Testing**:
- 282 invoices synced successfully
- All API endpoints verified
- NULL constraint bug fixed

✅ **Documentation**:
- Database schema documented
- API endpoints documented
- Feature capabilities documented
- Cron setup guide created

---

## 🚀 Future Roadmap

### Phase 2: Payment Integration

- Link Billingo invoices to bank transactions
- Auto-generate payment transfers from invoices
- Mark invoices as paid in Billingo

### Phase 3: Advanced Features

- Real-time webhooks (replace polling)
- Custom dashboard widgets
- Excel/CSV export
- Advanced filtering and search

### Phase 4: Reporting

- Aging analysis reports
- Cash flow forecasting
- Payment reconciliation reports
- Financial analytics

---

## ✨ Credits

**Developed By**: Backend Team
**Tested By**: IT Cardigan Kft.
**Documentation**: Complete
**Status**: ✅ Production Ready

---

**Last Updated**: 2025-10-27
**Document Version**: 1.0
