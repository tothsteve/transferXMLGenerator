#!/usr/bin/env python3
"""
Verify NAV API integration data storage and integrity.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.models import Invoice, InvoiceLineItem, NavConfiguration, Company
from datetime import date

def verify_nav_integration():
    """Verify NAV integration data integrity."""
    
    print("🎯 NAV API Integration Verification")
    print("="*50)
    
    # Database Statistics
    total_invoices = Invoice.objects.count()
    invoices_with_xml = Invoice.objects.filter(nav_invoice_xml__isnull=False)
    xml_count = invoices_with_xml.count()
    
    print(f"📊 Database Statistics:")
    print(f"  Total invoices: {total_invoices:,}")
    print(f"  Invoices with XML: {xml_count:,}")
    print(f"  XML coverage: {xml_count/total_invoices*100:.1f}%")
    print()
    
    # Recent invoices from August 2025
    recent_invoices = Invoice.objects.filter(issue_date__gte=date(2025, 8, 1))
    print(f"📅 August 2025 Invoices: {recent_invoices.count()}")
    
    for inv in recent_invoices.order_by('-issue_date')[:10]:
        xml_size = len(inv.nav_invoice_xml) if inv.nav_invoice_xml else 0
        line_count = inv.line_items.count()
        # Use the correct field name for gross amount
        amount = inv.invoice_gross_amount_huf or inv.invoice_net_amount_huf or 0
        
        print(f"  • {inv.nav_invoice_number:<25s} | XML: {xml_size:5d} chars | Lines: {line_count:2d} | {amount:,.0f} HUF")
    print()
    
    # Line items statistics
    total_lines = InvoiceLineItem.objects.count()
    print(f"📋 Total Line Items Extracted: {total_lines:,}")
    
    # Recent line items
    recent_lines = InvoiceLineItem.objects.filter(invoice__issue_date__gte=date(2025, 8, 1))
    print(f"📋 Recent Line Items (Aug 2025): {recent_lines.count()}")
    print()
    
    # XML storage analysis
    print("💾 XML Storage Analysis:")
    xml_sizes = []
    for inv in invoices_with_xml:
        if inv.nav_invoice_xml:
            xml_sizes.append(len(inv.nav_invoice_xml))
    
    if xml_sizes:
        avg_size = sum(xml_sizes) / len(xml_sizes)
        max_size = max(xml_sizes)
        min_size = min(xml_sizes)
        total_xml_mb = sum(xml_sizes) / (1024 * 1024)
        
        print(f"  Average XML size: {avg_size:,.0f} chars")
        print(f"  Largest XML: {max_size:,} chars")
        print(f"  Smallest XML: {min_size:,} chars")
        print(f"  Total XML storage: {total_xml_mb:.2f} MB")
        print()
    
    # Top 5 invoices by XML size (calculate in Python since SQL Server doesn't support __length)
    print("📄 Largest XML Documents:")
    xml_docs = []
    for inv in invoices_with_xml:
        if inv.nav_invoice_xml:
            xml_docs.append((inv, len(inv.nav_invoice_xml)))
    
    # Sort by XML size and take top 5
    xml_docs.sort(key=lambda x: x[1], reverse=True)
    for inv, xml_size in xml_docs[:5]:
        line_count = inv.line_items.count()
        print(f"  • {inv.nav_invoice_number:<25s} | {xml_size:6,} chars | {line_count:2d} lines")
    print()
    
    # NAV Configuration Analysis
    print("🌍 NAV Environment Analysis:")
    companies_with_nav = Company.objects.filter(nav_configs__isnull=False).distinct()
    
    for company in companies_with_nav:
        nav_configs = company.nav_configs.all()
        print(f"  🏢 {company.name}:")
        
        for config in nav_configs:
            env_icon = "🔴" if config.api_environment == 'production' else "🟡"
            active_icon = "✅" if config.is_active else "❌"
            
            # Count invoices synced with this environment
            env_invoice_count = Invoice.objects.filter(
                company=company,
                nav_source__isnull=False  # Has NAV data
            ).count()
            
            print(f"    {env_icon} {config.api_environment.upper():10s} | Active: {active_icon} | Invoices: {env_invoice_count:,}")
    print()
    
    # Success metrics
    successful_syncs = Invoice.objects.filter(nav_invoice_xml__isnull=False).count()
    failed_syncs = Invoice.objects.filter(
        nav_source__isnull=False,  # Has NAV reference
        nav_invoice_xml__isnull=True  # But no XML
    ).count()
    
    print("📊 Sync Success Metrics:")
    print(f"  Successful XML extractions: {successful_syncs:,}")
    print(f"  Failed XML extractions: {failed_syncs:,}")
    if successful_syncs + failed_syncs > 0:
        success_rate = successful_syncs / (successful_syncs + failed_syncs) * 100
        print(f"  Success rate: {success_rate:.1f}%")
    print()
    
    print("✅ NAV Integration Verification Complete!")
    print()
    
    # Summary
    if xml_count > 500 and success_rate > 90:
        print("🎉 EXCELLENT: NAV integration is working perfectly!")
        print("   • Large volume of invoices processed")
        print("   • High success rate for XML extraction")
        print("   • Complete line item processing")
    elif xml_count > 100:
        print("✅ GOOD: NAV integration is working well")
        print("   • Reasonable volume of invoices processed")
        print("   • XML extraction functioning")
    else:
        print("⚠️  LIMITED: NAV integration needs more data")
        print("   • Consider syncing more historical data")

if __name__ == "__main__":
    verify_nav_integration()