"""
Raiffeisen Bank Zrt. statement parser.

This adapter parses Raiffeisen Bank PDF statements with multi-line transaction format.
Supports all transaction types including transfers, card payments, and interest.
"""

import re
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime

try:
    import PyPDF2
except ImportError:
    raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")

from .base import (
    BankStatementAdapter,
    NormalizedTransaction,
    StatementMetadata,
    BankStatementParseError,
)

logger = logging.getLogger(__name__)


# Character encoding fixes for PDF extraction issues
# Based on actual Raiffeisen Bank PDF extraction
CHAR_FIXES = {
    '£': 'á',
    '©': 'é',
    'é': 'ö',  # PDF uses 'é' (U+00E9) where it should be 'ö'
    'ë': 'ó',
    '›': 'ő',
    '¶': 'Á',
    '½': 'É',
    'Ё': 'á',
    'ï': 'ü',
    'û': 'ű',
}


class RaiffeisenBankAdapter(BankStatementAdapter):
    """
    Raiffeisen Bank Zrt. statement parser.

    Statement format characteristics:
    - Multi-line transaction blocks
    - Transaction ID (Tétel azon.) starts each transaction
    - Dual-date format: Könyvelés (booking) and Értéknap (value date)
    - Amount format: space-separated thousands, comma decimal (e.g., 1.080.000,00)
    - Fees shown as "Előjegyzett díj" within transactions
    - Reference numbers critical for matching
    """

    BANK_CODE = 'RAIFFEISEN'
    BANK_NAME = 'Raiffeisen Bank Zrt.'
    BANK_BIC = 'UBRTHUHB'

    # Transaction type mapping (base types, direction added based on amount)
    # Note: PDF extraction may have encoding issues, use flexible matching
    TRANSACTION_TYPE_MAP = {
        'forint': 'TRANSFER',  # Matches "Forint£tutal£s", "Forint átutalás", etc.
        'elektronikus': 'TRANSFER',  # Matches "Elektronikusforint£tutal£s", etc.
        'bankon': 'TRANSFER',  # Matches "bankon belïli", "bankon belüli", etc.
        'tutal': 'TRANSFER',  # Matches "£tutal£s", "átutalás", etc.
        'rtyatranzakc': 'POS_PURCHASE',  # Matches "K£rtyatranzakcië", "Kártyatranzakció", etc.
        'kamat': 'INTEREST',
        'j': 'BANK_FEE',  # Matches "díj", "jutalék", etc.
    }

    @classmethod
    def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
        """Detect Raiffeisen Bank PDF by looking for bank identifiers."""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            if len(pdf_reader.pages) == 0:
                return False

            first_page_text = pdf_reader.pages[0].extract_text()
            if not first_page_text:
                return False

            # Look for Raiffeisen Bank name and BIC code
            text_upper = first_page_text.upper()
            has_bank_name = 'RAIFFEISEN' in text_upper
            has_bic = 'UBRTHUHB' in first_page_text
            has_statement_header = 'BANKSZ' in text_upper  # BANKSZÁMLAKIVONAT may have encoding issues

            return has_bank_name and has_bic and has_statement_header

        except Exception as e:
            logger.warning(f"Error detecting Raiffeisen Bank PDF: {e}")
            return False

    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Parse Raiffeisen Bank statement PDF."""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))

            # Extract all text from all pages
            full_text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

            if not full_text.strip():
                raise BankStatementParseError("PDF contains no extractable text")

            # Parse metadata from header
            metadata = self._parse_metadata(full_text)

            # Parse all transactions
            transactions = self._parse_transactions(full_text)

            logger.info(f"Successfully parsed {len(transactions)} transactions from Raiffeisen Bank statement")

            return {
                'metadata': metadata,
                'transactions': transactions
            }

        except BankStatementParseError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse Raiffeisen Bank PDF: {e}", exc_info=True)
            raise BankStatementParseError(f"Failed to parse Raiffeisen Bank statement: {str(e)}")

    def _parse_metadata(self, text: str) -> StatementMetadata:
        """Parse statement header metadata."""
        metadata = {}

        # Account number (Pénzforgalmi jelzőszám: 12042847 - 02101027 - 00100008)
        # Note: May appear as "P©nzforgalmi jelzìsz£m" due to encoding
        if m := re.search(r'P©nzforgalmi\s*jelz[^\:]*:\s*([\d\s\-]+)', text):
            account_raw = m.group(1).strip()
            metadata['account_number'] = account_raw.replace(' ', '')

        # IBAN (Nemzetközi bankszámlaszám IBAN: HU83 1204 2847 0210 1027 0010 0008)
        # Note: May appear as "Nemzetkézi banksz£mlasz£m IBAN" due to encoding
        if m := re.search(r'IBAN:\s*(HU[\d\s]+)', text):
            iban_raw = m.group(1)
            iban_clean = ''.join(c for c in iban_raw if c.isalnum())
            if len(iban_clean) == 28 and iban_clean.startswith('HU'):
                metadata['account_iban'] = iban_clean

        # Statement period (Tárgyidőszak: ... - 2025.12.31)
        # Note: May appear as "T£rgyidìszak" due to encoding
        if m := re.search(r'T£rgyid[^\:]*:\s*.*?\s*-\s*([\d.]+)', text):
            metadata['period_to'] = self._parse_date(m.group(1))
            # Period start might be missing, use opening balance date or first transaction date
            metadata['period_from'] = metadata['period_to']  # Will adjust later if needed

        # Statement number (Kivonat sorsz.: 2025/0000001)
        # Note: May appear as "Kivonat sorsz£m" due to encoding
        if m := re.search(r'Kivonat\s*sorsz[^\:]*:\s*([^\n]+)', text):
            metadata['statement_number'] = m.group(1).strip()

        # Opening balance (Utolsó kivonat: 0000.00.00 indicates 0)
        # Note: May appear as "Utolsë kivonat" due to encoding
        metadata['opening_balance'] = Decimal('0.00')
        if m := re.search(r'Utols[ëö]\s*kivonat:\s*([\d.,]+)', text):
            balance_str = m.group(1).strip()
            if balance_str != '0000.00.00':
                metadata['opening_balance'] = self._clean_amount(balance_str)

        # Closing balance (ZÁRÓEGYENLEG: 2.369.738,31)
        # Note: May appear as "Z¶RøEGYENLEG" due to encoding
        if m := re.search(r'Z[¶Á]R[øÓ]EGYENLEG:\s*([\d\s.,\-]+)', text):
            metadata['closing_balance'] = self._clean_amount(m.group(1))

        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=metadata.get('account_number', ''),
            account_iban=metadata.get('account_iban', ''),
            period_from=metadata.get('period_from', date.today()),
            period_to=metadata.get('period_to', date.today()),
            statement_number=metadata.get('statement_number', ''),
            opening_balance=metadata.get('opening_balance', Decimal('0')),
            closing_balance=metadata.get('closing_balance')
        )

    def _parse_transactions(self, text: str) -> List[NormalizedTransaction]:
        """
        Parse all transactions from statement text.

        Strategy:
        1. Find transaction table section (between "Könyvelés" header and summary)
        2. Split into transaction blocks by transaction ID pattern
        3. Parse each multi-line block
        """
        transactions = []

        # Find the transactions section (starts after "Könyvelés" header)
        # Note: PDF extraction may have encoding issues, so use flexible pattern
        # Pattern: Look for "Kényvel©s" (or Könyvelés) and extract until "összes" summary
        section_pattern = r'Kényvel©s.*?T©tel.*?azon\.(.*?)(?:összes|NYITÓ|Záró)'

        section_match = re.search(section_pattern, text, re.DOTALL | re.IGNORECASE)
        if not section_match:
            logger.warning("Could not find transaction section in statement")
            return transactions

        transaction_text = section_match.group(1)

        # Split by transaction ID pattern (10 digits at start of line)
        # Transaction ID pattern: 5365333444 2025.12.05. ...
        tx_blocks = re.split(r'\n(?=\d{10}\s+\d{4}\.\d{2}\.\d{2}\.)', transaction_text)

        for block in tx_blocks:
            block = block.strip()
            if not block or len(block) < 20:
                continue

            try:
                tx = self._parse_transaction_block(block)
                if tx:
                    transactions.append(tx)
            except Exception as e:
                logger.warning(f"Failed to parse transaction block: {e}\nBlock: {block[:200]}")
                continue

        return transactions

    def _parse_transaction_block(self, block: str) -> Optional[NormalizedTransaction]:
        """
        Parse a single multi-line transaction block.

        Format:
        5365333444 2025.12.05. Forint átutalás                    1.080.000,00
                   2025.12.04. Referencia: AFB25L0000262483
                               Átutaló neve: IT Cardigan Kft.
                               ...
        """
        lines = block.split('\n')
        if not lines:
            return None

        # Parse first line: TX_ID DATE TYPE AMOUNT
        first_line = lines[0].strip()

        # Pattern: [TX_ID] [BOOKING_DATE] [TYPE] [DEBIT or CREDIT]
        header_match = re.match(
            r'(\d{10})\s+(\d{4}\.\d{2}\.\d{2}\.)\s+(.*?)\s+([\d\s.,\-]+)$',
            first_line
        )

        if not header_match:
            logger.debug(f"Could not parse transaction header: {first_line}")
            return None

        tx_id = header_match.group(1)
        booking_date_str = header_match.group(2)
        tx_type_raw = header_match.group(3).strip()
        amount_str = header_match.group(4)

        booking_date = self._parse_date(booking_date_str)
        if not booking_date:
            logger.warning(f"Invalid booking date: {booking_date_str}")
            return None

        # Parse amount (determine if debit or credit based on column position or sign)
        amount = self._clean_amount(amount_str)

        # Raiffeisen uses column layout: Terhelés(-) on left, Jóváírás(+) on right
        # If amount was in debit column, it should be negative
        # Check the full line to see if this appears to be in the debit position
        # For simplicity, rely on the amount having a minus sign or being in specific position

        # Parse second line: VALUE_DATE
        value_date = booking_date  # Default to booking date
        if len(lines) > 1:
            second_line = lines[1].strip()
            if value_date_match := re.match(r'(\d{4}\.\d{2}\.\d{2}\.)', second_line):
                value_date = self._parse_date(value_date_match.group(1)) or booking_date

        # Extract details from remaining lines
        details = self._extract_transaction_details('\n'.join(lines[1:]))

        # Determine transaction type (base type + direction)
        base_type = self._map_transaction_type(tx_type_raw)
        transaction_type = self._add_direction_to_type(base_type, amount)

        # Build clean description
        clean_type = self._clean_text(tx_type_raw)
        description = clean_type

        # Add partner name if available
        if details.get('partner_name'):
            partner = self._clean_text(details['partner_name'])
            description = f"{clean_type} - {partner}"
        elif details.get('reference'):
            description = f"{clean_type} - {details['reference']}"

        # Create normalized transaction
        return NormalizedTransaction(
            transaction_type=transaction_type,
            booking_date=booking_date,
            value_date=value_date,
            amount=amount,
            currency='HUF',
            description=description,
            short_description=clean_type,  # Use cleaned text for display

            # Transfer details
            transaction_id=tx_id,
            payment_id=details.get('reference'),
            reference=details.get('kozlemeny'),  # CRITICAL for invoice matching

            # Payer/Beneficiary details (cleaned text)
            payer_name=self._clean_text(details.get('atutalo_neve')) or self._clean_text(details.get('merchant_name')) or None,
            payer_account_number=details.get('atutalo_szamlaszama'),

            beneficiary_name=self._clean_text(details.get('kedvezmenyezett_neve')) or None,
            beneficiary_account_number=details.get('kedvezmenyezett_szamlaszama'),

            # Card details
            card_number=details.get('card_number'),
            merchant_name=details.get('merchant_name'),
            merchant_location=details.get('merchant_location'),

            # Fee
            fee_amount=details.get('fee_amount'),

            # Raw data for debugging
            raw_data={
                'transaction_id': tx_id,
                'raw_type': tx_type_raw,
                'raw_block': block[:500],  # First 500 chars
                **details
            }
        )

    def _extract_transaction_details(self, details_text: str) -> Dict[str, Any]:
        """Extract structured details from transaction detail lines."""
        details = {}

        # Referencia (bank reference number)
        if m := re.search(r'Referencia:\s*([^\n]+)', details_text):
            details['reference'] = self._clean_text(m.group(1).strip())

        # Közlemény (payment reference - CRITICAL for invoice matching)
        # Note: May appear as "Kézlem©ny" due to encoding
        if m := re.search(r'K[ézö]zlem[©é]ny:\s*([^\n]+)', details_text):
            details['kozlemeny'] = self._clean_text(m.group(1).strip())

        # Átutaló details (for incoming transfers)
        # Note: May appear as "¶tutalë" or "¶tutalëneve:" (no spaces) due to encoding
        # Company names may span multiple lines (e.g., "Danubius Expert Consulting Z\nrt.")
        if m := re.search(r'[¶Á]tutal[ëó]\s*neve:\s*(.+?)(?:[¶Á]tutal[ëó]\s*sz[£á]mlasz[£á]ma:|Kedvezm[©é]nyezett|Referencia:|K[ézö]zlem[©é]ny:|$)', details_text, re.DOTALL):
            payer_name = m.group(1).strip()

            # Handle multi-line names: join lines intelligently
            lines = [line.strip() for line in payer_name.split('\n') if line.strip()]
            if len(lines) > 1:
                result = lines[0]
                for line in lines[1:]:
                    # If line starts with lowercase, join without space (word continuation)
                    if line and line[0].islower():
                        result = result + line
                    else:
                        result = result + ' ' + line
                payer_name = result

            # Add spaces to CamelCase names (PyPDF2 already preserves word spacing for all-caps)
            # Handle acronyms: "ITCardigan" -> "IT Cardigan"
            payer_name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', payer_name)
            # Then handle regular camelCase: "DanubiusExpert" -> "Danubius Expert"
            payer_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', payer_name)
            # Clean up double spaces
            payer_name = re.sub(r'\s+', ' ', payer_name).strip()

            # Clean encoding issues
            payer_name = self._clean_text(payer_name)
            # Remove any label text that might be included after cleaning
            payer_name = re.sub(r'^Átutaló\s*neve:\s*', '', payer_name, flags=re.IGNORECASE).strip()
            details['atutalo_neve'] = payer_name
            details['partner_name'] = payer_name  # For display

        if m := re.search(r'Átutaló\s+számlaszáma:\s*([^\n]+)', details_text):
            # Account number might span multiple lines
            account_start = m.end()
            account_text = details_text[account_start:account_start+100]
            if account_match := re.match(r'\s*(HU[\d\s]+)', account_text):
                details['atutalo_szamlaszama'] = self._clean_iban(account_match.group(1))

        # Kedvezményezett details (for outgoing transfers)
        # Note: May appear as "Kedvezm©nyezettneve:" (no spaces) due to encoding
        # Company names may span multiple lines (e.g., "Danubius Expert Consulting Z\nrt.")
        if m := re.search(r'Kedvezm[©é]nyezett\s*neve:\s*(.+?)(?:Kedvezm[©é]nyezett\s*sz[£á]mlasz[£á]ma:|[¶Á]tutal[ëó]|Referencia:|K[ézö]zlem[©é]ny:|Elìjegyzett|$)', details_text, re.DOTALL):
            beneficiary_name = m.group(1).strip()

            # Handle multi-line names: join lines intelligently
            lines = [line.strip() for line in beneficiary_name.split('\n') if line.strip()]
            if len(lines) > 1:
                result = lines[0]
                for line in lines[1:]:
                    # If line starts with lowercase, join without space (word continuation)
                    if line and line[0].islower():
                        result = result + line
                    else:
                        result = result + ' ' + line
                beneficiary_name = result

            # Add spaces to CamelCase names (PyPDF2 already preserves word spacing for all-caps)
            # Handle acronyms: "ITCardigan" -> "IT Cardigan"
            beneficiary_name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', beneficiary_name)
            # Then handle regular camelCase: "DanubiusExpert" -> "Danubius Expert"
            beneficiary_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', beneficiary_name)
            # Clean up double spaces
            beneficiary_name = re.sub(r'\s+', ' ', beneficiary_name).strip()

            # Clean encoding issues
            beneficiary_name = self._clean_text(beneficiary_name)
            # Remove any label text that might be included after cleaning
            beneficiary_name = re.sub(r'^Kedvezményezett\s*neve:\s*', '', beneficiary_name, flags=re.IGNORECASE).strip()
            details['kedvezmenyezett_neve'] = beneficiary_name
            details['partner_name'] = beneficiary_name  # For display

        if m := re.search(r'Kedvezményezett\s+számlaszáma:\s*([^\n]+)', details_text):
            account_start = m.end()
            account_text = details_text[account_start:account_start+100]
            if account_match := re.match(r'\s*(HU[\d\s]+)', account_text):
                details['kedvezmenyezett_szamlaszama'] = self._clean_iban(account_match.group(1))

        # Card transaction details
        # Check for card number pattern (e.g., "402115XXXXXX1446")
        card_number_match = re.search(r'(\d{6}X+\d{4})', details_text)

        if card_number_match:
            # This is a card transaction
            details['card_number'] = card_number_match.group(1)

            # Merchant name: line after "Referencia:"
            # Pattern: "BARIONP BARION.COM/GUE BUDAPEST"
            lines = details_text.split('\n')
            for i, line in enumerate(lines):
                if 'Referencia' in line and i + 1 < len(lines):
                    merchant_line = lines[i + 1].strip()
                    # Skip if it's a card number line or other transaction field
                    if merchant_line and not merchant_line.startswith(('HU', 'Orsz£gkëd', 'Kedvezm', '¶tutal', 'Átutal')) and not re.match(r'\d{6}X+\d{4}', merchant_line):
                        # This is the merchant name
                        details['merchant_name'] = merchant_line
                        # CRITICAL: Also set as reference for UI display (matches Gránit behavior)
                        details['kozlemeny'] = merchant_line
                        break

            # Country code
            if m := re.search(r'Orsz£gkëd:\s*([A-Z]{2})', details_text):
                details['merchant_location'] = m.group(1)

        # Előjegyzett díj (pre-booked fee)
        if m := re.search(r'Előjegyzett\s+díj:\s*([\d\s.,]+)\s*HUF', details_text):
            details['fee_amount'] = self._clean_amount(m.group(1))

        return details

    def _map_transaction_type(self, raw_type: str) -> str:
        """Map Raiffeisen transaction type to base type (without direction)."""
        raw_type_lower = raw_type.lower()

        for key, value in self.TRANSACTION_TYPE_MAP.items():
            if key.lower() in raw_type_lower:
                return value

        # Default to TRANSFER for unknown types
        logger.warning(f"Unknown transaction type: {raw_type}, defaulting to TRANSFER")
        return 'TRANSFER'

    def _add_direction_to_type(self, base_type: str, amount: Decimal) -> str:
        """
        Add direction (CREDIT/DEBIT) to transaction type based on amount sign.

        BankTransaction model requires directional types:
        - TRANSFER → TRANSFER_CREDIT (positive) or TRANSFER_DEBIT (negative)
        - INTEREST → INTEREST_CREDIT (positive) or INTEREST_DEBIT (negative)
        - POS_PURCHASE, ATM_WITHDRAWAL, BANK_FEE → no direction needed
        """
        if base_type == 'TRANSFER':
            return 'TRANSFER_CREDIT' if amount > 0 else 'TRANSFER_DEBIT'
        elif base_type == 'INTEREST':
            return 'INTEREST_CREDIT' if amount > 0 else 'INTEREST_DEBIT'
        elif base_type in ('POS_PURCHASE', 'ATM_WITHDRAWAL', 'BANK_FEE'):
            # These types don't have directional variants
            return base_type
        else:
            # Unknown type, use OTHER
            return 'OTHER'

    def _clean_text(self, text: Optional[str]) -> str:
        """
        Clean text by replacing PDF encoding artifacts with proper Hungarian characters.

        PDF extraction often mangles Hungarian accented characters.
        This function attempts to restore them.
        """
        if not text:
            return ''

        cleaned = text
        for bad_char, good_char in CHAR_FIXES.items():
            cleaned = cleaned.replace(bad_char, good_char)

        return cleaned

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse Raiffeisen date format with trailing dot.

        Raiffeisen format: "2025.12.31." (note the trailing dot)
        """
        if not date_str:
            return None

        # Remove trailing dot if present
        date_str = date_str.strip().rstrip('.')

        # Call parent implementation
        return super()._parse_date(date_str)

    def _clean_amount(self, amount_str: str) -> Decimal:
        """
        Clean Raiffeisen amount format.

        Format: "1.080.000,00" or "-385.000,00" or "8,31"
        - Dots are thousand separators
        - Comma is decimal separator
        - Minus sign for debits
        """
        if not amount_str:
            return Decimal('0.00')

        # Remove spaces
        cleaned = amount_str.strip().replace(' ', '')

        # Handle negative sign
        is_negative = cleaned.startswith('-')
        if is_negative:
            cleaned = cleaned[1:]

        # Replace dots (thousand separator) and comma (decimal separator)
        # Format: 1.080.000,00 -> 1080000.00
        cleaned = cleaned.replace('.', '').replace(',', '.')

        try:
            result = Decimal(cleaned)
            return -result if is_negative else result
        except Exception as e:
            logger.warning(f"Failed to parse amount '{amount_str}': {e}")
            return Decimal('0.00')
