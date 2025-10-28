"""
Django management command to import suppliers from CSV with FK relationships.

Two-phase import:
1. Extract and create all unique categories and types first
2. Import suppliers and link to created categories/types

Usage:
    python manage.py import_suppliers --company-id=4
"""

import csv
import logging
from pathlib import Path
from collections import OrderedDict
from django.core.management.base import BaseCommand
from django.db import transaction
from bank_transfers.models import Company, Supplier, SupplierCategory, SupplierType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import suppliers from CSV file with category and type as foreign keys (two-phase)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to import suppliers for (required)'
        )
        parser.add_argument(
            '--csv-path',
            type=str,
            default='bank_statement_example/BASE table - Beszallitok.csv',
            help='Path to CSV file relative to backend directory'
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        csv_path = options.get('csv_path')

        if not company_id:
            self.stdout.write(self.style.ERROR('❌ --company-id is required'))
            return

        try:
            company = Company.objects.get(id=company_id, is_active=True)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Company with ID {company_id} not found or inactive'))
            return

        # Construct full path
        from django.conf import settings
        base_dir = Path(settings.BASE_DIR)
        full_path = base_dir / csv_path

        if not full_path.exists():
            self.stdout.write(self.style.ERROR(f'❌ CSV file not found: {full_path}'))
            return

        self.stdout.write(f"📁 Importing suppliers from: {full_path}")
        self.stdout.write(f"🏢 Company: {company.name}")
        self.stdout.write("")

        # Import the data in two phases
        result = self.import_suppliers_two_phase(company, full_path)

        # Print summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f'✅ Import completed successfully!'))
        self.stdout.write(f"  Phase 1 - Categories & Types:")
        self.stdout.write(f"    Categories created: {result['categories_created']}")
        self.stdout.write(f"    Types created: {result['types_created']}")
        self.stdout.write(f"  Phase 2 - Suppliers:")
        self.stdout.write(f"    Suppliers created: {result['suppliers_created']}")
        self.stdout.write(f"    Suppliers updated: {result['suppliers_updated']}")
        self.stdout.write(f"    Rows skipped: {result['rows_skipped']}")

    @transaction.atomic
    def import_suppliers_two_phase(self, company, csv_path):
        """
        Two-phase import:
        1. Extract unique categories/types and create them
        2. Import suppliers with FK links
        """

        # Phase 1: Extract unique categories and types from CSV
        self.stdout.write("📊 Phase 1: Extracting categories and types...")

        categories_dict = OrderedDict()  # Preserve order of first appearance
        types_dict = OrderedDict()

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category_name = row['Category'].strip()
                type_name = row['Type'].strip()

                if category_name and category_name not in categories_dict:
                    categories_dict[category_name] = len(categories_dict)

                if type_name and type_name not in types_dict:
                    types_dict[type_name] = len(types_dict)

        self.stdout.write(f"  Found {len(categories_dict)} unique categories")
        self.stdout.write(f"  Found {len(types_dict)} unique types")
        self.stdout.write("")

        # Create SupplierCategory records
        self.stdout.write("🏷️  Creating categories...")
        categories_created = 0
        category_lookup = {}  # Map name -> SupplierCategory instance

        for cat_name, display_order in categories_dict.items():
            category, created = SupplierCategory.objects.get_or_create(
                company=company,
                name=cat_name,
                defaults={'display_order': display_order}
            )
            category_lookup[cat_name] = category
            if created:
                categories_created += 1
                self.stdout.write(f"  ✨ {display_order}. {cat_name}")

        self.stdout.write("")

        # Create SupplierType records
        self.stdout.write("🔖 Creating types...")
        types_created = 0
        type_lookup = {}  # Map name -> SupplierType instance

        for type_name, display_order in types_dict.items():
            supplier_type, created = SupplierType.objects.get_or_create(
                company=company,
                name=type_name,
                defaults={'display_order': display_order}
            )
            type_lookup[type_name] = supplier_type
            if created:
                types_created += 1
                self.stdout.write(f"  ✨ {display_order}. {type_name}")

        self.stdout.write("")
        self.stdout.write("👥 Phase 2: Creating suppliers with FK links...")

        # Phase 2: Import suppliers and link to categories/types
        suppliers_created = 0
        suppliers_updated = 0
        rows_skipped = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                try:
                    partner_name = row['Partner neve'].strip()
                    category_name = row['Category'].strip()
                    type_name = row['Type'].strip()
                    valid_from = row.get('Valid_from', '').strip() or None
                    valid_to = row.get('Valid_to', '').strip() or None

                    if not partner_name:
                        self.stdout.write(self.style.WARNING(f'⚠️  Row {row_num}: Empty partner name, skipping'))
                        rows_skipped += 1
                        continue

                    # Get category FK (or None)
                    category = category_lookup.get(category_name) if category_name else None

                    # Get type FK (or None)
                    supplier_type = type_lookup.get(type_name) if type_name else None

                    # Parse dates
                    valid_from_date = None
                    valid_to_date = None

                    if valid_from:
                        try:
                            from datetime import datetime
                            valid_from_date = datetime.strptime(valid_from, '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(
                                f'⚠️  Row {row_num}: Invalid valid_from date format: {valid_from}'
                            ))

                    if valid_to:
                        try:
                            from datetime import datetime
                            valid_to_date = datetime.strptime(valid_to, '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(
                                f'⚠️  Row {row_num}: Invalid valid_to date format: {valid_to}'
                            ))

                    # Create or update supplier
                    supplier, created = Supplier.objects.update_or_create(
                        company=company,
                        partner_name=partner_name,
                        defaults={
                            'category': category,
                            'type': supplier_type,
                            'valid_from': valid_from_date,
                            'valid_to': valid_to_date,
                        }
                    )

                    if created:
                        suppliers_created += 1
                        cat_display = category.name if category else 'None'
                        type_display = supplier_type.name if supplier_type else 'None'
                        self.stdout.write(f"  ✅ {partner_name[:50]:50} | {cat_display[:25]:25} | {type_display}")
                    else:
                        suppliers_updated += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Row {row_num}: Error - {str(e)}'))
                    logger.error(f"Error importing row {row_num}: {e}", exc_info=True)
                    rows_skipped += 1

        return {
            'categories_created': categories_created,
            'types_created': types_created,
            'suppliers_created': suppliers_created,
            'suppliers_updated': suppliers_updated,
            'rows_skipped': rows_skipped
        }
