# Billingo Invoice Synchronization - API Endpoint Documentation

**Feature**: Billingo API v3 Integration
**Base URL**: `http://localhost:8002/api/`
**Authentication**: JWT Bearer Token Required
**Created**: 2025-10-27

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Examples](#requestresponse-examples)
5. [Error Handling](#error-handling)
6. [Testing Guide](#testing-guide)

---

## Overview

The Billingo Invoice Synchronization API provides three main endpoints for managing invoice synchronization from Billingo accounting software:

1. **Settings Management** - Configure API credentials and sync preferences
2. **Invoice Viewing** - Browse synchronized invoices with filtering
3. **Sync Logging** - View audit trail of synchronization operations

All endpoints are **company-scoped** and require appropriate permissions.

---

## Authentication

### Required Headers

```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

### Permission Requirements

| Endpoint | Required Role | Feature Flag |
|----------|--------------|--------------|
| `billingo-settings/*` | **ADMIN** | `BILLINGO_SYNC` |
| `billingo-invoices/*` | USER+ | `BILLINGO_SYNC` |
| `billingo-sync-logs/*` | USER+ | `BILLINGO_SYNC` |

### Getting a Token

```bash
# Login and extract token
export TOKEN=$(curl -s -X POST http://localhost:8002/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"your_username\",\"password\":\"your_password\"}" \
  | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

# Verify token is set
echo "Token: $TOKEN"
```

---

## API Endpoints

### 1. Billingo Settings Management

**Base Path**: `/api/billingo-settings/`

#### GET `/api/billingo-settings/`

List Billingo settings for the current company.

**Response**: `200 OK`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "company": 4,
      "company_name": "IT Cardigan Kft.",
      "has_api_key": true,
      "last_sync_time": "2025-10-27T05:40:24+01:00",
      "last_sync_time_formatted": "2025-10-27 04:40:24",
      "is_active": true,
      "created_at": "2025-10-27T05:36:31+01:00",
      "updated_at": "2025-10-27T05:40:24+01:00"
    }
  ]
}
```

**Notes**:
- **Security**: API key is never exposed (only `has_api_key` boolean)
- **Unique**: Each company can have only one settings record
- Returns empty list if not configured

---

#### POST `/api/billingo-settings/`

Create or update Billingo settings for current company.

**Request Body**:

```json
{
  "api_key_input": "41e61362-afde-11f0-a3c6-06e1fe7801c9",
  "is_active": true
}
```

**Response**: `201 Created` or `200 OK`

```json
{
  "id": 1,
  "company": 4,
  "company_name": "IT Cardigan Kft.",
  "has_api_key": true,
  "last_sync_time": null,
  "last_sync_time_formatted": null,
  "is_active": true,
  "created_at": "2025-10-27T05:36:31+01:00",
  "updated_at": "2025-10-27T05:36:31+01:00"
}
```

**Notes**:
- `api_key_input` is **encrypted** before storage using Fernet symmetric encryption
- API key is never returned in responses
- Updates existing settings if already configured

---

#### POST `/api/billingo-settings/trigger_sync/`

Manually trigger invoice synchronization with Billingo API.

**Request Body**: `{}` (empty JSON object)

**Response**: `200 OK`

```json
{
  "status": "success",
  "invoices_processed": 282,
  "invoices_created": 281,
  "invoices_updated": 1,
  "invoices_skipped": 0,
  "items_extracted": 581,
  "api_calls": 3,
  "duration_seconds": 3,
  "errors": []
}
```

**Process**:
1. Fetches invoices from `https://api.billingo.hu/v3/documents`
2. Paginated requests (100 invoices per page)
3. Creates/updates invoice records atomically
4. Returns detailed sync metrics

**Error Response**: `400 Bad Request`

```json
{
  "status": "error",
  "invoices_processed": 100,
  "invoices_created": 50,
  "invoices_updated": 0,
  "invoices_skipped": 50,
  "items_extracted": 120,
  "api_calls": 1,
  "duration_seconds": 2,
  "errors": [
    {
      "invoice_id": 12345,
      "invoice_number": "INV-2025-100",
      "error": "Database constraint violation"
    }
  ]
}
```

---

### 2. Invoice Viewing

**Base Path**: `/api/billingo-invoices/`

#### GET `/api/billingo-invoices/`

List synchronized invoices with filtering and pagination.

**Query Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | Integer | Page number (1-indexed) | `?page=2` |
| `page_size` | Integer | Results per page (default: 100) | `?page_size=50` |
| `payment_status` | String | Filter by status | `?payment_status=outstanding` |
| `partner_tax_number` | String | Filter by partner | `?partner_tax_number=12345678-2-01` |
| `invoice_date_from` | Date | Min invoice date | `?invoice_date_from=2025-01-01` |
| `invoice_date_to` | Date | Max invoice date | `?invoice_date_to=2025-12-31` |
| `search` | String | Search invoice number | `?search=INV-2025` |

**Response**: `200 OK`

```json
{
  "count": 282,
  "next": "http://localhost:8002/api/billingo-invoices/?page=2&page_size=5",
  "previous": null,
  "results": [
    {
      "id": 111369290,
      "company": 4,
      "company_name": "IT Cardigan Kft.",
      "invoice_number": "INV-2025-244",
      "type": "invoice",
      "payment_status": "outstanding",
      "payment_method": "wire_transfer",
      "gross_total": "19476607.00",
      "gross_total_formatted": "19,476,607.00 HUF",
      "currency": "HUF",
      "invoice_date": "2025-10-22",
      "invoice_date_formatted": "2025-10-22",
      "due_date": "2025-11-21",
      "paid_date": "2025-10-27",
      "partner_name": "GYŐR-MOSON-SOPRON VÁRMEGYEI PETZ ALADÁR EGYETEMI OKTATÓ KÓRHÁZ",
      "partner_tax_number": "15366052-2-08",
      "cancelled": false,
      "item_count": 19,
      "created_at": "2025-10-27T05:40:22+01:00"
    }
  ]
}
```

---

#### GET `/api/billingo-invoices/{id}/`

Retrieve detailed invoice with line items.

**Response**: `200 OK`

```json
{
  "id": 111324303,
  "company": 4,
  "company_name": "IT Cardigan Kft.",
  "invoice_number": "INV-2025-243",
  "type": "invoice",
  "correction_type": "invoice",
  "cancelled": false,
  "block_id": 249951,
  "payment_status": "outstanding",
  "payment_method": "wire_transfer",
  "gross_total": "154842.00",
  "gross_total_formatted": "154,842.00 HUF",
  "currency": "HUF",
  "conversion_rate": "1.000000",
  "invoice_date": "2025-10-22",
  "invoice_date_formatted": "2025-10-22",
  "fulfillment_date": "2025-10-27",
  "due_date": "2025-11-21",
  "due_date_formatted": "2025-11-21",
  "paid_date": "2025-10-27",
  "paid_date_formatted": "2025-10-27",
  "organization_name": "MEDKA Kft.",
  "organization_tax_number": "32560682-2-43",
  "organization_bank_account_number": "10410400-00000190-04894827",
  "organization_bank_account_iban": "HU28104104000000019004894827",
  "organization_swift": "",
  "partner_id": 1843084820,
  "partner_name": "Szegedi Tudományegyetem",
  "partner_tax_number": "19308650-2-06",
  "partner_iban": "",
  "partner_swift": "",
  "partner_account_number": "--",
  "comment": "Lejelentő: TRA/MEDK/2025/7...",
  "online_szamla_status": "done",
  "items": [
    {
      "id": 302,
      "product_id": 18015515,
      "name": "MR004C SEQUENT MENISCAL REPAIR DEVICE, CURVED NEEDLE, 4 IMPLANTS",
      "quantity": "1.00",
      "unit": "db",
      "net_unit_price": "0.00",
      "net_amount": "121923.00",
      "gross_amount": "154842.21",
      "vat": "27%",
      "entitlement": null,
      "created_at": "2025-10-27T05:40:22+01:00",
      "updated_at": "2025-10-27T05:40:22+01:00"
    }
  ],
  "created_at": "2025-10-27T05:40:22+01:00",
  "updated_at": "2025-10-27T05:40:22+01:00",
  "last_modified": "2025-10-27T05:40:22+01:00"
}
```

---

### 3. Sync Logs

**Base Path**: `/api/billingo-sync-logs/`

#### GET `/api/billingo-sync-logs/`

View audit trail of synchronization operations.

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | Integer | Page number |
| `page_size` | Integer | Results per page |
| `sync_type` | String | MANUAL or AUTOMATIC |
| `status` | String | RUNNING, COMPLETED, FAILED, PARTIAL |

**Response**: `200 OK`

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "company": 4,
      "company_name": "IT Cardigan Kft.",
      "sync_type": "MANUAL",
      "sync_type_display": "Kézi",
      "status": "COMPLETED",
      "status_display": "Befejezve",
      "invoices_processed": 282,
      "invoices_created": 281,
      "invoices_updated": 1,
      "invoices_skipped": 0,
      "items_extracted": 581,
      "api_calls_made": 3,
      "sync_duration_seconds": 3,
      "duration_formatted": "3s",
      "started_at": "2025-10-27T05:40:21+01:00",
      "started_at_formatted": "2025-10-27 04:40:21",
      "completed_at": "2025-10-27T05:40:24+01:00",
      "completed_at_formatted": "2025-10-27 04:40:24",
      "errors": "",
      "errors_parsed": []
    }
  ]
}
```

---

## Request/Response Examples

### Complete Workflow Example

```bash
# 1. Login and get token
export TOKEN=$(curl -s -X POST http://localhost:8002/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"tothi\",\"password\":\"Almafa+123\"}" \
  | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

# 2. Configure Billingo settings
read TOKEN < /tmp/clean_token.txt; curl -s -X POST http://localhost:8002/api/billingo-settings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"api_key_input\":\"41e61362-afde-11f0-a3c6-06e1fe7801c9\",\"is_active\":true}"

# 3. Trigger manual sync
read TOKEN < /tmp/clean_token.txt; curl -s -X POST http://localhost:8002/api/billingo-settings/trigger_sync/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}"

# 4. View invoices
read TOKEN < /tmp/clean_token.txt; curl -s -X GET "http://localhost:8002/api/billingo-invoices/?page_size=5" \
  -H "Authorization: Bearer $TOKEN"

# 5. View specific invoice with items
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-invoices/111324303/ \
  -H "Authorization: Bearer $TOKEN"

# 6. Check sync logs
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-sync-logs/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid input data, sync errors |
| `401` | Unauthorized | Missing or invalid JWT token |
| `403` | Forbidden | Insufficient permissions or feature not enabled |
| `404` | Not Found | Invoice/settings not found |
| `500` | Server Error | Database or API connection issues |

### Error Response Format

```json
{
  "detail": "Error message describing the problem",
  "code": "error_code"
}
```

### Permission Error Example

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Feature Not Enabled Error

```json
{
  "detail": "BILLINGO_SYNC feature is not enabled for your company"
}
```

---

## Testing Guide

### 1. Setup Test Environment

```bash
# Save token for reuse
curl -s -X POST http://localhost:8002/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"tothi\",\"password\":\"Almafa+123\"}" \
  -o /tmp/login.json

# Extract and clean token
grep -o '"access":"[^"]*"' /tmp/login.json | cut -d'"' -f4 | tr -d '\n' | tr -d ' ' > /tmp/clean_token.txt
```

### 2. Test Settings Endpoint

```bash
# List settings (should be empty initially)
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-settings/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Create settings
read TOKEN < /tmp/clean_token.txt; curl -s -X POST http://localhost:8002/api/billingo-settings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"api_key_input\":\"YOUR_API_KEY\",\"is_active\":true}" \
  | python3 -m json.tool
```

### 3. Test Sync Endpoint

```bash
# Trigger sync
read TOKEN < /tmp/clean_token.txt; curl -s -X POST http://localhost:8002/api/billingo-settings/trigger_sync/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}" \
  | python3 -m json.tool

# Expected: 200 OK with sync metrics
# Check for: invoices_created > 0, errors = []
```

### 4. Test Invoice Endpoints

```bash
# List all invoices
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-invoices/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Get specific invoice (use ID from list)
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-invoices/111324303/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Filter by status
read TOKEN < /tmp/clean_token.txt; curl -s -X GET "http://localhost:8002/api/billingo-invoices/?payment_status=outstanding" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 5. Test Sync Logs

```bash
# View all logs
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-sync-logs/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Filter by status
read TOKEN < /tmp/clean_token.txt; curl -s -X GET "http://localhost:8002/api/billingo-sync-logs/?status=COMPLETED" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## Rate Limiting

### Billingo API Limits

- **Rate Limit**: 429 status code when limit exceeded
- **Retry-After** header indicates wait time in seconds
- **Automatic Retry**: Service implements exponential backoff (3 retries)

### Recommended Sync Frequency

- **Manual**: On-demand via API
- **Automatic**: Once per day (via cron at night)
- **High-Volume**: Max 4 times per day

---

## Security Best Practices

1. **Never log API keys** - Keys are encrypted in database, never exposed via API
2. **Use HTTPS in production** - Encrypt all traffic
3. **Rotate keys regularly** - Update API keys every 90 days
4. **Monitor sync logs** - Check for unusual activity
5. **Limit access** - Only ADMIN role can configure settings

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Maintained By**: Backend Team
