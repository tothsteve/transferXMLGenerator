"""
Management command to recalculate credit/debit statistics for bank statements.

Usage:
    python manage.py recalculate_statement_stats

This command recalculates:
- credit_count
- debit_count
- total_credits
- total_debits

for all bank statements that have transactions.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q
from bank_transfers.models import BankStatement, BankTransaction


class Command(BaseCommand):
    help = 'Recalculate credit/debit statistics for all bank statements'

    def handle(self, *args, **options):
        """Execute the command."""
        statements = BankStatement.objects.all()
        total_count = statements.count()

        self.stdout.write(f"Found {total_count} bank statements")

        updated_count = 0
        for statement in statements:
            # Calculate statistics
            transaction_stats = BankTransaction.objects.filter(
                bank_statement=statement
            ).aggregate(
                credit_count=Count('id', filter=Q(amount__gt=0)),
                debit_count=Count('id', filter=Q(amount__lt=0)),
                total_credits=Sum('amount', filter=Q(amount__gt=0)),
                total_debits=Sum('amount', filter=Q(amount__lt=0))
            )

            # Update statement
            statement.credit_count = transaction_stats['credit_count'] or 0
            statement.debit_count = transaction_stats['debit_count'] or 0
            statement.total_credits = transaction_stats['total_credits'] or Decimal('0.00')
            statement.total_debits = abs(transaction_stats['total_debits'] or Decimal('0.00'))
            statement.save()

            updated_count += 1

            self.stdout.write(
                f"Updated statement {statement.id}: "
                f"{statement.credit_count} credits, {statement.debit_count} debits"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully recalculated statistics for {updated_count} statements"
            )
        )
