"""
Django management command to import base tables from CSV files.

Supports three CSV types:
1. Suppliers (with categories and types in two-phase import)
2. Customers
3. Product Prices

Usage:
    # Import suppliers
    python manage.py import_base_tables --company-id=4 --csv-type=suppliers --csv-path=/path/to/suppliers.csv

    # Import customers
    python manage.py import_base_tables --company-id=4 --csv-type=customers --csv-path=/path/to/customers.csv

    # Import product prices
    python manage.py import_base_tables --company-id=4 --csv-type=prices --csv-path=/path/to/prices.csv
"""

import csv
import logging
import time
from pathlib import Path
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from bank_transfers.models import (
    Company, Supplier, SupplierCategory, SupplierType,
    Customer, ProductPrice
)

logger = logging.getLogger(__name__)


def detect_delimiter(file_path, sample_size=5):
    """
    Automatically detect CSV delimiter (comma or tab).
    Reads first few lines and uses csv.Sniffer to detect delimiter.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read first few lines for detection
        sample = ''.join([f.readline() for _ in range(sample_size)])

        try:
            # Use csv.Sniffer to detect delimiter
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            return delimiter
        except csv.Error:
            # Fallback: count commas vs tabs in first line
            first_line = sample.split('\n')[0]
            comma_count = first_line.count(',')
            tab_count = first_line.count('\t')

            if tab_count > comma_count:
                return '\t'
            else:
                return ','


class Command(BaseCommand):
    help = 'Import base tables (suppliers, customers, product prices) from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            required=True,
            help='Company ID to import data for (required)'
        )
        parser.add_argument(
            '--csv-type',
            type=str,
            required=True,
            choices=['suppliers', 'customers', 'prices'],
            help='Type of CSV to import (suppliers, customers, or prices)'
        )
        parser.add_argument(
            '--csv-path',
            type=str,
            required=True,
            help='Full path to CSV file (required)'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        csv_type = options['csv_type']
        csv_path = options['csv_path']

        # Validate company
        try:
            company = Company.objects.get(id=company_id, is_active=True)
        except Company.DoesNotExist:
            raise CommandError(f'❌ Company with ID {company_id} not found or inactive')

        # Validate CSV path
        full_path = Path(csv_path)
        if not full_path.exists():
            raise CommandError(f'❌ CSV file not found: {full_path}')

        # Detect delimiter (CSV or TSV)
        delimiter = detect_delimiter(full_path)
        delimiter_name = 'TAB' if delimiter == '\t' else 'COMMA'

        self.stdout.write("=" * 80)
        self.stdout.write(f"📊 Importing {csv_type} from CSV/TSV")
        self.stdout.write(f"🏢 Company: {company.name} (ID: {company.id})")
        self.stdout.write(f"📁 File: {full_path}")
        self.stdout.write(f"🔍 Detected delimiter: {delimiter_name}")
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # Route to appropriate import method
        if csv_type == 'suppliers':
            result = self.import_suppliers(company, full_path, delimiter)
        elif csv_type == 'customers':
            result = self.import_customers(company, full_path, delimiter)
        elif csv_type == 'prices':
            result = self.import_product_prices(company, full_path, delimiter)

        # Print summary
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS('✅ Import completed successfully!'))
        self.stdout.write("")

        if csv_type == 'suppliers':
            self.stdout.write(f"  Phase 1 - Categories & Types:")
            self.stdout.write(f"    Categories created: {result['categories_created']}")
            self.stdout.write(f"    Types created: {result['types_created']}")
            self.stdout.write(f"  Phase 2 - Suppliers:")
            self.stdout.write(f"    Suppliers created: {result['suppliers_created']}")
            self.stdout.write(f"    Suppliers updated: {result['suppliers_updated']}")
            self.stdout.write(f"    Rows skipped: {result['rows_skipped']}")
        elif csv_type == 'customers':
            self.stdout.write(f"  Customers created: {result['created']}")
            self.stdout.write(f"  Customers updated: {result['updated']}")
            self.stdout.write(f"  Rows skipped: {result['skipped']}")
        elif csv_type == 'prices':
            self.stdout.write(f"  Product prices created: {result['created']}")
            self.stdout.write(f"  Product prices updated: {result['updated']}")
            self.stdout.write(f"  Rows skipped: {result['skipped']}")
            self.stdout.write(f"  Batches processed: {result['batches']}")

        self.stdout.write("=" * 80)

    @transaction.atomic
    def import_suppliers(self, company, csv_path, delimiter=','):
        """
        Two-phase import for suppliers:
        1. Extract and create all unique categories and types first
        2. Import suppliers with FK links
        """

        # Phase 1: Extract unique categories and types from CSV
        self.stdout.write("📊 Phase 1: Extracting categories and types...")

        categories_dict = OrderedDict()  # Preserve order of first appearance
        types_dict = OrderedDict()

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
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
            reader = csv.DictReader(f, delimiter=delimiter)

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
                            valid_from_date = datetime.strptime(valid_from, '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(
                                f'⚠️  Row {row_num}: Invalid valid_from date format: {valid_from}'
                            ))

                    if valid_to:
                        try:
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

    @transaction.atomic
    def import_customers(self, company, csv_path, delimiter=','):
        """Import customers from CSV."""
        created = 0
        updated = 0
        skipped = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                try:
                    customer_name = row['Customer name'].strip()
                    cashflow_adjustment = row.get('Cashflow adjustment', '0').strip() or '0'
                    valid_from = row.get('Validf_from', '').strip() or None
                    valid_to = row.get('Valid_to', '').strip() or None

                    if not customer_name:
                        self.stdout.write(self.style.WARNING(f'⚠️  Row {row_num}: Empty customer name, skipping'))
                        skipped += 1
                        continue

                    # Parse cashflow adjustment
                    try:
                        cashflow_adj = int(cashflow_adjustment)
                    except ValueError:
                        cashflow_adj = 0

                    # Parse dates (format: 2024/06/30)
                    valid_from_date = None
                    valid_to_date = None

                    if valid_from:
                        try:
                            valid_from_date = datetime.strptime(valid_from, '%Y/%m/%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(
                                f'⚠️  Row {row_num}: Invalid valid_from date format: {valid_from}'
                            ))

                    if valid_to:
                        try:
                            valid_to_date = datetime.strptime(valid_to, '%Y/%m/%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(
                                f'⚠️  Row {row_num}: Invalid valid_to date format: {valid_to}'
                            ))

                    # Create or update customer
                    customer, is_created = Customer.objects.update_or_create(
                        company=company,
                        customer_name=customer_name,
                        defaults={
                            'cashflow_adjustment': cashflow_adj,
                            'valid_from': valid_from_date,
                            'valid_to': valid_to_date,
                        }
                    )

                    if is_created:
                        created += 1
                        self.stdout.write(f"  ✅ {customer_name[:60]:60} | Cashflow adj: {cashflow_adj:>3}")
                    else:
                        updated += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Row {row_num}: Error - {str(e)}'))
                    logger.error(f"Error importing customer row {row_num}: {e}", exc_info=True)
                    skipped += 1

        return {'created': created, 'updated': updated, 'skipped': skipped}

    def import_product_prices(self, company, csv_path, delimiter=','):
        """
        Import product prices from CSV with batch processing and connection management.
        Handles large datasets (5000+ rows) by committing every 50 records with 1s delay.
        """
        created = 0
        updated = 0
        skipped = 0
        batch_count = 0
        BATCH_SIZE = 50  # Commit every 50 records, then close connection and sleep 1s

        # Helper function to clean currency values
        # Handles both US format ($1,234.56) and European format (1 234,56 Ft)
        def clean_currency(value):
            if not value:
                return None
            # Remove currency symbols and trim
            cleaned = value.replace('$', '').replace('Ft', '').strip()
            # Remove both regular spaces AND non-breaking spaces (U+00A0) - European thousands separator
            cleaned = cleaned.replace(' ', '').replace('\xa0', '')
            # Convert comma to period (European decimal separator)
            cleaned = cleaned.replace(',', '.')
            try:
                return str(Decimal(cleaned))
            except:
                return None

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                try:
                    product_value = row['Product Value'].strip()
                    product_description = row['Product Description'].strip()
                    uom = row.get('UOM', '').strip() or None
                    uom_hun = row.get('UOM_HUN', '').strip() or None
                    purchase_price_usd = row.get(' PURCHASE PRICE USD ', '').strip()
                    purchase_price_huf = row.get(' PURCHASE PRICE HUF ', '').strip()
                    markup = row.get(' MARKUP', '').strip()
                    sales_price_huf = row.get(' SALES PRICE HUF', '').strip()
                    cap_disp = row.get('Cap/Disp', '').strip() or None
                    is_inventory = row.get('Készletkezelt termék', '').strip().lower() == 'y'
                    valid_from = row.get('Valid from', '').strip() or None
                    valid_to = row.get('Valid to', '').strip() or None

                    if not product_value:
                        skipped += 1
                        continue

                    purchase_usd = clean_currency(purchase_price_usd)
                    purchase_huf = clean_currency(purchase_price_huf)
                    markup_val = clean_currency(markup)
                    sales_huf = clean_currency(sales_price_huf)

                    # Parse dates (format: 2024/06/30)
                    valid_from_date = None
                    valid_to_date = None

                    if valid_from:
                        try:
                            valid_from_date = datetime.strptime(valid_from, '%Y/%m/%d').date()
                        except ValueError:
                            pass

                    if valid_to:
                        try:
                            valid_to_date = datetime.strptime(valid_to, '%Y/%m/%d').date()
                        except ValueError:
                            pass

                    # Create or update product price (no transaction wrapper for better connection management)
                    _, is_created = ProductPrice.objects.update_or_create(
                        company=company,
                        product_value=product_value,
                        defaults={
                            'product_description': product_description,
                            'uom': uom,
                            'uom_hun': uom_hun,
                            'purchase_price_usd': purchase_usd,
                            'purchase_price_huf': purchase_huf,
                            'markup': markup_val,
                            'sales_price_huf': sales_huf,
                            'cap_disp': cap_disp,
                            'is_inventory_managed': is_inventory,
                            'valid_from': valid_from_date,
                            'valid_to': valid_to_date,
                        }
                    )

                    if is_created:
                        created += 1
                    else:
                        updated += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Row {row_num}: {str(e)[:100]}'))
                    logger.error(f"Error importing product price row {row_num}: {e}", exc_info=True)
                    skipped += 1
                    continue

                # Batch processing: Commit, close connection, and sleep every BATCH_SIZE records
                if row_num % BATCH_SIZE == 0:
                    batch_count += 1
                    transaction.commit()  # Commit the batch
                    connection.close()  # Close connection
                    self.stdout.write(f"  📦 Batch {batch_count}: Processed {row_num} records ({created} created, {updated} updated)")
                    time.sleep(1)  # 1 second delay before next batch

        # Final summary
        self.stdout.write(f"  ✅ Total: {created + updated} product prices processed")
        return {'created': created, 'updated': updated, 'skipped': skipped, 'batches': batch_count}
