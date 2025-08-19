#!/usr/bin/env python
"""
Database migration script from SQL Server to PostgreSQL for Railway deployment.

This script helps migrate data from the current SQL Server database to PostgreSQL.
Run this script before deploying to Railway.

Requirements:
1. Have both databases accessible (SQL Server and PostgreSQL)
2. Install required packages: pip install pyodbc psycopg2-binary
3. Set environment variables for both databases

Usage:
python migrate_to_postgresql.py --export-only  # Export data only
python migrate_to_postgresql.py --import-only  # Import data only
python migrate_to_postgresql.py               # Full migration
"""

import os
import json
import argparse
from datetime import datetime
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
import django
django.setup()

from django.core.management import execute_from_command_line
from bank_transfers.models import BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch


class DatabaseMigrator:
    def __init__(self):
        self.data_dir = 'migration_data'
        os.makedirs(self.data_dir, exist_ok=True)
        
    def export_data(self):
        """Export data from SQL Server to JSON files"""
        print("🔄 Exporting data from SQL Server...")
        
        # Export Bank Accounts
        bank_accounts = list(BankAccount.objects.all().values())
        self.save_json('bank_accounts.json', bank_accounts)
        print(f"   ✅ Exported {len(bank_accounts)} bank accounts")
        
        # Export Beneficiaries
        beneficiaries = list(Beneficiary.objects.all().values())
        self.save_json('beneficiaries.json', beneficiaries)
        print(f"   ✅ Exported {len(beneficiaries)} beneficiaries")
        
        # Export Transfer Templates
        templates = list(TransferTemplate.objects.all().values())
        self.save_json('transfer_templates.json', templates)
        print(f"   ✅ Exported {len(templates)} transfer templates")
        
        # Export Template Beneficiaries
        template_beneficiaries = list(TemplateBeneficiary.objects.all().values())
        self.save_json('template_beneficiaries.json', template_beneficiaries)
        print(f"   ✅ Exported {len(template_beneficiaries)} template beneficiaries")
        
        # Export Transfers
        transfers = list(Transfer.objects.all().values())
        self.save_json('transfers.json', transfers)
        print(f"   ✅ Exported {len(transfers)} transfers")
        
        # Export Transfer Batches
        batches = list(TransferBatch.objects.all().values())
        self.save_json('transfer_batches.json', batches)
        print(f"   ✅ Exported {len(batches)} transfer batches")
        
        print("✅ Data export completed!")
        
    def import_data(self):
        """Import data from JSON files to PostgreSQL"""
        print("🔄 Importing data to PostgreSQL...")
        
        # Clear existing data (optional - comment out to preserve existing data)
        print("   ⚠️  Clearing existing data...")
        TransferBatch.objects.all().delete()
        Transfer.objects.all().delete()
        TemplateBeneficiary.objects.all().delete()
        TransferTemplate.objects.all().delete()
        Beneficiary.objects.all().delete()
        BankAccount.objects.all().delete()
        
        # Import Bank Accounts
        bank_accounts = self.load_json('bank_accounts.json')
        for account_data in bank_accounts:
            BankAccount.objects.create(**self.clean_data(account_data))
        print(f"   ✅ Imported {len(bank_accounts)} bank accounts")
        
        # Import Beneficiaries
        beneficiaries = self.load_json('beneficiaries.json')
        for beneficiary_data in beneficiaries:
            Beneficiary.objects.create(**self.clean_data(beneficiary_data))
        print(f"   ✅ Imported {len(beneficiaries)} beneficiaries")
        
        # Import Transfer Templates
        templates = self.load_json('transfer_templates.json')
        for template_data in templates:
            TransferTemplate.objects.create(**self.clean_data(template_data))
        print(f"   ✅ Imported {len(templates)} transfer templates")
        
        # Import Template Beneficiaries
        template_beneficiaries = self.load_json('template_beneficiaries.json')
        for tb_data in template_beneficiaries:
            clean_data = self.clean_data(tb_data)
            # Handle foreign keys
            clean_data['template_id'] = clean_data.pop('template')
            clean_data['beneficiary_id'] = clean_data.pop('beneficiary')
            TemplateBeneficiary.objects.create(**clean_data)
        print(f"   ✅ Imported {len(template_beneficiaries)} template beneficiaries")
        
        # Import Transfers
        transfers = self.load_json('transfers.json')
        for transfer_data in transfers:
            clean_data = self.clean_data(transfer_data)
            # Handle foreign keys
            clean_data['originator_account_id'] = clean_data.pop('originator_account')
            clean_data['beneficiary_id'] = clean_data.pop('beneficiary')
            if clean_data.get('template'):
                clean_data['template_id'] = clean_data.pop('template')
            Transfer.objects.create(**clean_data)
        print(f"   ✅ Imported {len(transfers)} transfers")
        
        # Import Transfer Batches
        batches = self.load_json('transfer_batches.json')
        for batch_data in batches:
            clean_data = self.clean_data(batch_data)
            # Create batch without transfers first
            transfers_data = clean_data.pop('transfers', [])
            batch = TransferBatch.objects.create(**clean_data)
            # Add transfers to batch if any
            if transfers_data:
                batch.transfers.set(transfers_data)
        print(f"   ✅ Imported {len(batches)} transfer batches")
        
        print("✅ Data import completed!")
    
    def save_json(self, filename, data):
        """Save data to JSON file with datetime/decimal handling"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=self.json_serializer, ensure_ascii=False)
    
    def load_json(self, filename):
        """Load data from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            print(f"   ⚠️  File {filename} not found, skipping...")
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def json_serializer(self, obj):
        """JSON serializer for datetime and decimal objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def clean_data(self, data):
        """Clean data for PostgreSQL import"""
        cleaned = {}
        for key, value in data.items():
            if key == 'id':
                continue  # Skip ID, let PostgreSQL auto-generate
            if isinstance(value, str) and value.endswith('+00:00'):
                # Convert datetime strings back to datetime objects
                from django.utils.dateparse import parse_datetime
                cleaned[key] = parse_datetime(value)
            else:
                cleaned[key] = value
        return cleaned


def main():
    parser = argparse.ArgumentParser(description='Migrate database from SQL Server to PostgreSQL')
    parser.add_argument('--export-only', action='store_true', help='Export data only')
    parser.add_argument('--import-only', action='store_true', help='Import data only')
    args = parser.parse_args()
    
    migrator = DatabaseMigrator()
    
    if args.export_only:
        migrator.export_data()
    elif args.import_only:
        migrator.import_data()
    else:
        # Full migration
        print("🚀 Starting full database migration...")
        migrator.export_data()
        print("\n📋 Data exported. Now switch to PostgreSQL settings and run:")
        print("   python migrate_to_postgresql.py --import-only")


if __name__ == '__main__':
    main()