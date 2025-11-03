"""
Management command to populate net_total for existing Billingo invoices.

Since net_total was added later, this command calculates it from:
1. The invoice items (sum of net_amount)
2. Or if no items, estimate as gross_total / 1.27 (assuming 27% VAT)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from bank_transfers.models import BillingoInvoice


class Command(BaseCommand):
    help = 'Populate net_total for existing Billingo invoices from their items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        invoices_without_net_total = BillingoInvoice.objects.filter(net_total__isnull=True)
        total_count = invoices_without_net_total.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('All invoices already have net_total populated!'))
            return

        self.stdout.write(f"\nFound {total_count} invoices without net_total\n")

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        updated_count = 0
        estimated_count = 0

        with transaction.atomic():
            for invoice in invoices_without_net_total:
                # Calculate net_total from items
                items = invoice.items.all()

                if items.exists():
                    # Sum net_amount from all items
                    net_total = sum(item.net_amount for item in items)
                    if dry_run:
                        self.stdout.write(
                            f"Would set {invoice.invoice_number}: net_total = {net_total} "
                            f"(from {items.count()} items)"
                        )
                    else:
                        invoice.net_total = net_total
                        invoice.save(update_fields=['net_total'])
                    updated_count += 1
                else:
                    # No items - estimate from gross_total
                    # Assuming 27% VAT (most common in Hungary)
                    estimated_net = invoice.gross_total / Decimal('1.27')
                    if dry_run:
                        self.stdout.write(
                            f"Would estimate {invoice.invoice_number}: net_total = {estimated_net:.2f} "
                            f"(from gross {invoice.gross_total})"
                        )
                    else:
                        invoice.net_total = estimated_net
                        invoice.save(update_fields=['net_total'])
                    estimated_count += 1

            if dry_run:
                self.stdout.write('\n' + self.style.WARNING('DRY RUN - Rolling back transaction'))
                transaction.set_rollback(True)

        if not dry_run:
            self.stdout.write('\n' + self.style.SUCCESS(
                f'Successfully populated net_total for {updated_count + estimated_count} invoices\n'
                f'  - {updated_count} calculated from items\n'
                f'  - {estimated_count} estimated from gross_total\n'
            ))
        else:
            self.stdout.write('\n' + self.style.WARNING(
                f'Would populate net_total for {updated_count + estimated_count} invoices\n'
                f'  - {updated_count} from items\n'
                f'  - {estimated_count} estimated\n'
                f'\nRun without --dry-run to apply changes'
            ))
