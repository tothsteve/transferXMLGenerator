"""
Transfer service layer
Handles business logic for transfer and batch operations
"""
from django.db import transaction, models
from django.utils import timezone
from ..models import Transfer, TransferBatch
from ..utils import generate_xml
from ..kh_export import KHBankExporter


class TransferService:
    """Service for transfer business logic"""
    
    @staticmethod
    def get_company_transfers(company, filters=None):
        """Get transfers for a company with optional filters"""
        queryset = Transfer.objects.select_related('beneficiary', 'originator_account').filter(
            originator_account__company=company
        )
        
        if filters:
            # Apply processed filter
            if filters.get('is_processed') is not None:
                queryset = queryset.filter(is_processed=filters['is_processed'])
            
            # Apply template filter
            if filters.get('template_id'):
                queryset = queryset.filter(template_id=filters['template_id'])
            
            # Apply date range filters
            if filters.get('execution_date_from'):
                queryset = queryset.filter(execution_date__gte=filters['execution_date_from'])
            
            if filters.get('execution_date_to'):
                queryset = queryset.filter(execution_date__lte=filters['execution_date_to'])
        
        return queryset
    
    @staticmethod
    def bulk_create_transfers(transfers_data, batch_name=None):
        """Create multiple transfers in a transaction with optional batch"""
        with transaction.atomic():
            transfers = []
            nav_invoices_to_update = []
            
            for transfer_data in transfers_data:
                # Handle nested data properly - if transfer_data contains instances, get the data
                if hasattr(transfer_data, '__dict__'):
                    # If it's a dict-like object, use it directly
                    data_dict = transfer_data
                else:
                    data_dict = transfer_data
                
                # Debug: Log nav_invoice data
                nav_invoice_value = data_dict.get('nav_invoice')
                if nav_invoice_value:
                    print(f"Creating transfer with nav_invoice: {nav_invoice_value}")
                
                transfer = Transfer.objects.create(**data_dict)
                transfers.append(transfer)
                
                # Track NAV invoices that need status update
                if transfer.nav_invoice_id:
                    print(f"Transfer {transfer.id} linked to NAV invoice {transfer.nav_invoice_id}")
                    nav_invoices_to_update.append(transfer.nav_invoice_id)
            
            # Update linked NAV invoices to PREPARED status
            if nav_invoices_to_update:
                from ..models import Invoice
                from django.utils import timezone
                
                invoices = Invoice.objects.filter(
                    id__in=nav_invoices_to_update,
                    payment_status='UNPAID'  # Only update if currently unpaid
                )
                
                for invoice in invoices:
                    invoice.mark_as_prepared()
            
            # Create batch if name provided
            batch = None
            if batch_name and transfers:
                batch = TransferBatch.objects.create(name=batch_name)
                batch.transfers.set(transfers)
                batch.total_amount = sum(t.amount for t in transfers)
                batch.save()
            
            return transfers, batch
    
    @staticmethod
    def generate_xml_from_transfers(transfer_ids, batch_name=None):
        """Generate XML from transfer IDs and optionally create batch"""
        transfers = Transfer.objects.filter(id__in=transfer_ids).select_related(
            'beneficiary', 'originator_account'
        ).order_by('order', 'execution_date')
        
        if not transfers:
            raise ValueError("No transfers found")
        
        # Generate XML
        xml_content = generate_xml(transfers)
        
        # Create batch if name provided
        batch = None
        if batch_name:
            max_order = TransferBatch.objects.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            
            # Get company from first transfer's originator account
            company = transfers.first().originator_account.company
            
            batch = TransferBatch.objects.create(
                name=batch_name,
                company=company,
                xml_generated_at=timezone.now(),
                total_amount=sum(t.amount for t in transfers),
                order=max_order + 1
            )
            batch.transfers.set(transfers)
        
        # Mark transfers as processed
        transfers.update(is_processed=True)
        
        # Return serializable batch data
        batch_data = None
        if batch:
            batch_data = {
                'id': batch.id,
                'name': batch.name,
                'total_amount': str(batch.total_amount),
                'transfer_count': batch.transfers.count(),
                'xml_generated_at': batch.xml_generated_at.isoformat() if batch.xml_generated_at else None
            }
        
        return {
            'xml': xml_content,
            'transfer_count': len(transfers),
            'total_amount': str(sum(t.amount for t in transfers)),
            'batch': batch_data
        }
    
    @staticmethod
    def generate_kh_export_from_transfers(transfer_ids, batch_name=None):
        """Generate KH Bank export from transfer IDs"""
        transfers = Transfer.objects.filter(id__in=transfer_ids).select_related(
            'beneficiary', 'originator_account'
        ).order_by('order', 'execution_date')
        
        if not transfers:
            raise ValueError("No transfers found")
        
        # Generate KH Bank export with ISO-8859-2 encoding (required by bank)
        import base64
        exporter = KHBankExporter()
        kh_content_bytes = exporter.generate_kh_export_encoded(transfers)  # Get ISO-8859-2 encoded bytes
        kh_content_base64 = base64.b64encode(kh_content_bytes).decode('ascii')  # Base64 for JSON transport
        filename = exporter.get_filename(batch_name)
        
        # Create batch if name provided
        batch = None
        if batch_name:
            max_order = TransferBatch.objects.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            
            # Get company from first transfer's originator account
            company = transfers.first().originator_account.company
            
            batch = TransferBatch.objects.create(
                name=f"{batch_name} (KH Export)",
                company=company,
                xml_generated_at=timezone.now(),
                total_amount=sum(t.amount for t in transfers),
                order=max_order + 1,
                batch_format='KH_CSV'
            )
            batch.transfers.set(transfers)
        
        # Mark transfers as processed
        transfers.update(is_processed=True)
        
        # Return serializable batch data
        batch_data = None
        if batch:
            batch_data = {
                'id': batch.id,
                'name': batch.name,
                'total_amount': str(batch.total_amount),
                'transfer_count': batch.transfers.count(),
                'xml_generated_at': batch.xml_generated_at.isoformat() if batch.xml_generated_at else None
            }
        
        return {
            'content': kh_content_base64,
            'filename': filename,
            'encoding': 'iso-8859-2',  # Required by Hungarian bank
            'content_encoding': 'base64',  # Content is base64 encoded
            'transfer_count': len(transfers),
            'total_amount': str(sum(t.amount for t in transfers)),
            'batch': batch_data
        }


class TransferBatchService:
    """Service for transfer batch business logic"""
    
    @staticmethod
    def get_company_batches(company):
        """Get transfer batches for a company"""
        return TransferBatch.objects.filter(company=company)
    
    @staticmethod
    def regenerate_xml_for_batch(batch):
        """Regenerate XML content for a batch"""
        transfers = batch.transfers.select_related(
            'beneficiary', 'originator_account'
        ).order_by('order', 'execution_date')
        
        if not transfers:
            raise ValueError("No transfers in batch")
        
        return generate_xml(transfers)
    
    @staticmethod
    def mark_batch_as_used(batch):
        """Mark batch as used in bank and auto-mark linked NAV invoices as paid"""
        batch.used_in_bank = True
        batch.bank_usage_date = timezone.now()
        batch.save()
        
        # Auto-mark linked NAV invoices as paid
        updated_invoices = []
        
        try:
            with transaction.atomic():
                # Get all transfers in this batch that have linked NAV invoices
                transfers_with_invoices = batch.transfers.filter(
                    nav_invoice__isnull=False
                ).select_related('nav_invoice')
                
                for transfer in transfers_with_invoices:
                    invoice = transfer.nav_invoice
                    # Only auto-mark unpaid and prepared invoices (skip already paid invoices)
                    if invoice.payment_status in ['UNPAID', 'PREPARED']:
                        invoice.mark_as_paid(
                            payment_date=batch.bank_usage_date.date() if batch.bank_usage_date else timezone.now().date(),
                            auto_marked=True
                        )
                        updated_invoices.append(invoice)
                        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update NAV invoices for batch {batch.id}: {e}")
        
        return batch
    
    @staticmethod
    def mark_batch_as_unused(batch):
        """Mark batch as unused in bank"""
        batch.used_in_bank = False
        batch.bank_usage_date = None
        batch.save()
        return batch