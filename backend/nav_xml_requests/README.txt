NAV API XML Requests Overview
========================================

1. tokenExchange - Get authentication token
2. queryInvoiceDigest (INBOUND) - Get invoice list for incoming invoices
3. queryInvoiceDigest (OUTBOUND) - Get invoice list for outgoing invoices
4. queryInvoiceChainDigest - Get chain metadata for specific invoice
5. queryInvoiceData - Get detailed invoice data (batch index 1)
6. queryInvoiceData - Get detailed invoice data (batch index 2)

All requests use NAV API v3.0 specification.
Authentication: SHA3-512 signatures with technical user credentials.
Environment: Production NAV API endpoint.
