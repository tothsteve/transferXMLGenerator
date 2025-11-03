"""
Management command to check net_total values in Billingo invoices.
"""
from django.core.management.base import BaseCommand
from bank_transfers.models import BillingoInvoice


class Command(BaseCommand):
    help = 'Check net_total values in Billingo invoices'

    def handle(self, *args, **options):
        invoices = BillingoInvoice.objects.all()[:10]

        self.stdout.write(f"\nTotal invoices: {BillingoInvoice.objects.count()}\n")
        self.stdout.write(f"Invoices with net_total: {BillingoInvoice.objects.filter(net_total__isnull=False).count()}\n")
        self.stdout.write(f"Invoices without net_total: {BillingoInvoice.objects.filter(net_total__isnull=True).count()}\n\n")

        self.stdout.write("Sample invoices:\n")
        for inv in invoices:
            self.stdout.write(
                f"ID: {inv.id}, Invoice: {inv.invoice_number}, "
                f"Gross: {inv.gross_total}, Net: {inv.net_total}"
            )
