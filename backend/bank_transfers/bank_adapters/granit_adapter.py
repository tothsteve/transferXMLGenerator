"""
GRÁNIT Bank Nyrt. statement parser - REWRITTEN FOR COMPLETE TRANSACTION EXTRACTION.

This version correctly parses ALL transactions including:
- POS purchases (with card details)
- AFR transfers (with full IBAN/BIC)
- Átutalás (IG2/IB/IG2) transfers (with full IBAN/BIC)
- Bank fees (associated with transactions)
- Interest, corrections, etc.
"""

import re
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime

try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber is required for PDF parsing. Install with: pip install pdfplumber")

from .base import (
    BankStatementAdapter,
    NormalizedTransaction,
    StatementMetadata,
    BankStatementParseError,
)

logger = logging.getLogger(__name__)


class GranitBankAdapter(BankStatementAdapter):
    """
    GRÁNIT Bank Nyrt. statement parser.

    Strategy: Parse transactions as multi-line blocks that start with a date.
    Each transaction block continues until the next date line is found.
    """

    BANK_CODE = 'GRANIT'
    BANK_NAME = 'GRÁNIT Bank Nyrt.'
    BANK_BIC = 'GNBAHUHB'

    @classmethod
    def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
        """Detect GRÁNIT Bank PDF by looking for bank identifiers."""
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                if not pdf.pages:
                    return False

                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text:
                    return False

                return ('GRÁNIT Bank' in first_page_text or 'GRANIT Bank' in first_page_text) and \
                       'GNBAHUHB' in first_page_text
        except Exception as e:
            logger.warning(f"Error detecting GRÁNIT Bank PDF: {e}")
            return False

    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Parse GRÁNIT Bank statement PDF."""
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                # Extract all text from all pages
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

                if not full_text.strip():
                    raise BankStatementParseError("PDF contains no extractable text")

                # Parse metadata from header
                metadata = self._parse_metadata(full_text)

                # Parse ALL transactions using new multi-line block approach
                transactions = self._parse_transactions_multiline(full_text)

                logger.info(f"Successfully parsed {len(transactions)} transactions from GRÁNIT Bank statement")

                return {
                    'metadata': metadata,
                    'transactions': transactions
                }

        except BankStatementParseError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse GRÁNIT Bank PDF: {e}", exc_info=True)
            raise BankStatementParseError(f"Failed to parse GRÁNIT Bank statement: {str(e)}")

    def _parse_metadata(self, text: str) -> StatementMetadata:
        """Parse statement header metadata."""
        metadata = {}

        # Account number
        if m := re.search(r'Számlaszám:\s*([\d\-]+)', text):
            metadata['account_number'] = m.group(1)

        # IBAN - capture HU + digits, then clean to exactly 28 chars
        if m := re.search(r'IBAN\s+szám[:\s]+(HU[\d\s\n]+)', text):
            # Extract only HU + 26 digits (28 chars total)
            iban_raw = m.group(1)
            iban_clean = ''.join(c for c in iban_raw if c.isalnum())  # Remove spaces/newlines
            if len(iban_clean) == 28 and iban_clean.startswith('HU'):
                metadata['account_iban'] = iban_clean

        # Statement period
        if m := re.search(r'Könyvelés dátuma:\s*([\d.]+)\s*-\s*([\d.]+)', text):
            metadata['period_from'] = self._parse_date(m.group(1))
            metadata['period_to'] = self._parse_date(m.group(2))

        # Statement number
        if m := re.search(r'Kivonatszám/számla sorszáma:\s*([^\n]+)', text):
            metadata['statement_number'] = m.group(1).strip()

        # Opening balance
        if m := re.search(r'Utolsó kivonat egyenlege:\s*([\d\s\-,]+)', text):
            metadata['opening_balance'] = self._clean_amount(m.group(1))

        # Closing balance (may not be present)
        if m := re.search(r'Záró egyenleg:\s*([\d\s\-,]+)', text):
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

    def _parse_transactions_multiline(self, text: str) -> List[NormalizedTransaction]:
        """
        Parse ALL transactions using multi-line block approach.

        Strategy:
        1. Find all lines that start with a date AND end with an amount (transaction headers)
        2. For each transaction header, collect all subsequent lines until the next transaction header
        3. Parse the complete multi-line block as one transaction
        4. Extract all available fields from the block

        Key insight: Lines like "2025.01.14 Előjegyzett jutalék: -723" are detail lines,
        not new transactions. Only lines ending with amounts are transaction headers.
        """
        transactions = []

        # Stop parsing at the summary/invoice section
        # Keywords that indicate end of transaction list
        end_markers = ['SZÁMLÁZOTT TÉTELEK', 'Üzenetek:', 'Üzenetek vége']

        # Find where transactions end
        end_pos = len(text)
        for marker in end_markers:
            pos = text.find(marker)
            if pos != -1:
                end_pos = min(end_pos, pos)

        # Only parse transaction section
        transaction_section = text[:end_pos]
        lines = transaction_section.split('\n')

        # Find all transaction start indices (lines with date + space-separated amount at end)
        # Format: "2025.01.14 Description... -361 250" or "2025.01.14 Description... 10 260"
        # NOT: "2025.01.14 Előjegyzett jutalék: -723" (detail line, no space in amount)
        transaction_starts = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Must start with date
            if not re.match(r'^2025\.\d{2}\.\d{2}\s+', line_stripped):
                continue

            # Check if line ends with space-separated amount (e.g., "-361 250" or "10 260")
            # Transaction amounts in GRÁNIT statements have spaces for thousands separator
            # Detail lines like "Előjegyzett jutalék: -723" don't have spaces in the amount
            if re.search(r'\s[\d\-]+\s\d{3}$', line_stripped):  # Space-separated thousands
                transaction_starts.append(i)
            elif re.search(r'\s[\d\-]+$', line_stripped):  # Could be small amount without thousands
                # Further validation: must have meaningful description (not just metadata)
                # Skip lines like "Előjegyzett jutalék:", "Beérkezés dátuma:", etc.
                if not re.search(r'(jutalék|Beérkezés|Előjegyzett|Eredeti|Értéknap|Kártya):', line_stripped):
                    transaction_starts.append(i)

        logger.info(f"Found {len(transaction_starts)} transaction headers (lines with amounts)")

        # Parse each transaction block
        for idx, start_i in enumerate(transaction_starts):
            # Determine end of this transaction block
            if idx + 1 < len(transaction_starts):
                end_i = transaction_starts[idx + 1]
            else:
                end_i = len(lines)

            # Extract multi-line block for this transaction
            block_lines = lines[start_i:end_i]
            block_text = '\n'.join(block_lines)

            # Parse the transaction block
            try:
                txn = self._parse_transaction_block(block_lines, block_text)
                if txn:
                    transactions.append(txn)
            except Exception as e:
                logger.warning(f"Failed to parse transaction block starting at line {start_i}: {e}")
                continue

        return transactions

    def _parse_transaction_block(self, block_lines: List[str], block_text: str) -> Optional[NormalizedTransaction]:
        """
        Parse a complete transaction block (all lines from one date to the next).

        Returns a NormalizedTransaction with ALL extracted fields.
        """
        if not block_lines:
            return None

        first_line = block_lines[0].strip()

        # Extract booking date and main description from first line
        date_match = re.match(r'^([\d.]+)\s+(.+?)\s+([\d\s\-,]+)$', first_line)
        if not date_match:
            logger.warning(f"Could not parse first line: {first_line}")
            return None

        booking_date = self._parse_date(date_match.group(1))
        main_desc = date_match.group(2).strip()
        amount = self._clean_amount(date_match.group(3))

        # Determine transaction type and extract fields
        txn_type, fields = self._classify_and_extract(main_desc, block_text, amount)

        # Build transaction
        return NormalizedTransaction(
            transaction_type=txn_type,
            booking_date=booking_date,
            value_date=fields.get('value_date', booking_date),
            amount=amount,
            currency=fields.get('currency', 'HUF'),
            description=fields.get('description', main_desc),
            short_description=fields.get('short_description', main_desc[:50]),

            # AFR/Transfer fields
            payment_id=fields.get('payment_id', ''),
            transaction_id=fields.get('transaction_id', ''),
            payer_name=fields.get('payer_name', ''),
            payer_iban=fields.get('payer_iban', ''),
            payer_account_number=fields.get('payer_account_number', ''),
            payer_bic=fields.get('payer_bic', ''),
            beneficiary_name=fields.get('beneficiary_name', ''),
            beneficiary_iban=fields.get('beneficiary_iban', ''),
            beneficiary_account_number=fields.get('beneficiary_account_number', ''),
            beneficiary_bic=fields.get('beneficiary_bic', ''),
            reference=fields.get('reference', ''),
            partner_id=fields.get('partner_id', ''),
            transaction_type_code=fields.get('transaction_type_code', ''),
            fee_amount=fields.get('fee_amount'),

            # POS fields
            card_number=fields.get('card_number', ''),
            merchant_name=fields.get('merchant_name', ''),
            merchant_location=fields.get('merchant_location', ''),

            # Raw data for debugging (always include block_text)
            raw_data={
                'block_text': block_text,
                'main_desc': main_desc,
                **fields
            }
        )

    def _classify_and_extract(self, main_desc: str, block_text: str, amount: Decimal) -> Tuple[str, Dict[str, Any]]:
        """
        Classify transaction type and extract all relevant fields from block.

        Returns: (transaction_type, fields_dict)
        """
        fields = {}

        # === POS Purchase ===
        if 'POS vásárlás' in main_desc:
            fields['short_description'] = 'POS vásárlás'

            # Extract card number
            if m := re.search(r'Kártya:\s*([\d*]+)', block_text):
                fields['card_number'] = m.group(1)

            # Extract merchant
            # Pattern: Hely: 00227731:AMZN Mktp DE*MK1FV4U15BANK
            # Capture everything after "Hely:" until newline
            if m := re.search(r'Hely:\s*([^\n]+)', block_text):
                merchant_full = m.group(1).strip()

                # Check if there's a colon with NO space after it (location code:merchant format)
                # e.g., "00227731:AMZN Mktp DE*MK1FV4U15BANK"
                if ':' in merchant_full and not merchant_full.split(':', 1)[1].startswith(' '):
                    parts = merchant_full.split(':', 1)
                    location_code = parts[0].strip()
                    merchant_name = parts[1].strip() if len(parts) > 1 else ''

                    # Store full value as merchant_location
                    fields['merchant_location'] = merchant_full
                    # Extract merchant name (after colon)
                    if merchant_name:
                        fields['merchant_name'] = merchant_name
                        # Use merchant name as reference for better matching
                        fields['reference'] = merchant_name
                else:
                    # Simple format, just store as-is
                    fields['merchant_location'] = merchant_full

            return 'POS_PURCHASE', fields

        # === AFR Credit ===
        elif 'AFR jóváírás' in main_desc or 'AFR jóváírás' in block_text:
            fields['short_description'] = 'AFR jóváírás'
            self._extract_transfer_fields(block_text, fields)
            return 'AFR_CREDIT', fields

        # === AFR Debit ===
        elif 'AFR terhelés' in main_desc or 'AFR terhelés' in block_text:
            fields['short_description'] = 'AFR terhelés'
            self._extract_transfer_fields(block_text, fields)
            return 'AFR_DEBIT', fields

        # === Regular Transfer ===
        elif 'Átutalás' in main_desc or 'átutalás' in main_desc.lower():
            if amount > 0:
                fields['short_description'] = 'Átutalás jóváírás'
                self._extract_transfer_fields(block_text, fields)
                return 'TRANSFER_CREDIT', fields
            else:
                fields['short_description'] = 'Átutalás terhelés'
                self._extract_transfer_fields(block_text, fields)
                return 'TRANSFER_DEBIT', fields

        # === Bank Fee ===
        elif 'jutalék' in main_desc.lower() or 'költség' in main_desc.lower() or 'díj' in main_desc.lower():
            fields['short_description'] = 'Banki költség'
            return 'BANK_FEE', fields

        # === Interest ===
        elif 'kamat' in main_desc.lower():
            fields['short_description'] = 'Kamat'
            if amount > 0:
                return 'INTEREST_CREDIT', fields
            else:
                return 'INTEREST_DEBIT', fields

        # === Default ===
        else:
            fields['short_description'] = main_desc[:50]
            return 'OTHER', fields

    def _extract_transfer_fields(self, block_text: str, fields: Dict[str, Any]):
        """Extract all transfer-related fields from multi-line block."""

        # Value date
        if m := re.search(r'Értéknap:\s*([\d.]+)', block_text):
            fields['value_date'] = self._parse_date(m.group(1))

        # Payment ID
        if m := re.search(r'Fizetési azonosító:\s*([A-Z0-9]+)', block_text):
            fields['payment_id'] = m.group(1)

        # Transaction ID
        if m := re.search(r'Tranzakció azonosító:\s*([A-Z0-9]+)', block_text):
            fields['transaction_id'] = m.group(1)

        # Partner ID
        if m := re.search(r'Partnerek közti .*?azonosító:\s*([^\n]+)', block_text):
            fields['partner_id'] = m.group(1).strip()

        # Transaction type code
        if m := re.search(r'Tranzakció típus:\s*([\d\-]+)', block_text):
            fields['transaction_type_code'] = m.group(1)

        # Fee amount
        if m := re.search(r'Előjegyzett jutalék:\s*([\d\s\-,]+)', block_text):
            fields['fee_amount'] = self._clean_amount(m.group(1))

        # Payer extraction - handles multiple formats:
        # Format 1: "Fizető fél: Uri-Zanyi Gázkészülék- és Klímaszerelő..." (may wrap across lines)
        # Format 2: "Fizető fél: HU62116000060000000078175381, DANUBIUS EXPERT ZRT."
        # Format 3: "Fizető fél: HU12304000010000000071947848\nUri-Zanyi Gáz..." (IBAN on line 1, name on line 2+)

        # Check for Format 2: IBAN followed by comma and name on same line
        if m := re.search(r'Fizető fél:\s*(HU\d{26})\s*,\s*([^\n]+)', block_text):
            fields['payer_iban'] = m.group(1)
            fields['payer_name'] = m.group(2).strip()
        # Check for Format 3: IBAN on line 1, name on subsequent lines
        elif m := re.search(r'Fizető fél:\s*(HU\d{26})\s*\n(.+?)(?:,\s*Fizető fél BIC:|\nFizető fél BIC:|$)', block_text, re.DOTALL):
            fields['payer_iban'] = m.group(1)
            # Extract and clean multi-line name
            name_text = m.group(2).strip()

            # Handle case where name is on one line followed by ", Fizető fél BIC:"
            # Example: "ALLIANZ HUNGÁRIA ÖNKÉNTES KÖLCSÖNÖS, Fizető fél BIC: UBRTHUHB"
            if ', Fizető fél BIC:' in name_text:
                # Extract everything before the comma
                payer_name = name_text.split(', Fizető fél BIC:')[0].strip()
                fields['payer_name'] = payer_name
            else:
                # Multi-line name - original logic
                lines = name_text.split('\n')
                name_lines = []
                for line in lines:
                    line = line.strip()
                    # Stop if we hit another field or footer information
                    if any(keyword in line for keyword in ['Fizető fél BIC:', 'Kedvezményezett', 'Azonosító:', 'Tranzakció', 'Közlemény', 'BIC:', 'Értéknap', 'Számlaszám:', 'Devizanem:', 'Takarékinfo']):
                        break
                    if line:
                        name_lines.append(line)
                # Join lines - handle words split across lines
                payer_name = ''
                for i, line in enumerate(name_lines):
                    if i == 0:
                        payer_name = line
                    else:
                        # Check if word is split mid-word (next line starts with lowercase)
                        if line and line[0].islower():
                            # Mid-word split: join without space (e.g., "Tár" + "saság" -> "Társaság")
                            payer_name = payer_name + line
                        else:
                            # Normal multi-word name: join with space
                            payer_name = payer_name + ' ' + line
                fields['payer_name'] = payer_name
        # Check for Format 1: Name only (no IBAN) - may span multiple lines
        elif m := re.search(r'Fizető fél:\s*(.+?)(?:\nFizető fél IBAN:|$)', block_text, re.DOTALL):
            potential_payer = m.group(1).strip()
            # Only treat as name if it's NOT an IBAN (already handled by Format 3 above)
            if not re.match(r'^HU\d{26}', potential_payer):
                # Stop at any other field that might follow
                if '\n' in potential_payer:
                    # Take only lines that are part of the name (before next field)
                    lines = potential_payer.split('\n')
                    name_lines = []
                    for line in lines:
                        line = line.strip()
                        # Stop if we hit another field or footer information
                        if any(keyword in line for keyword in ['Kedvezményezett', 'Azonosító:', 'Tranzakció', 'Közlemény', 'BIC:', 'Értéknap', 'Számlaszám:', 'Devizanem:', 'Takarékinfo']):
                            break
                        if line:
                            name_lines.append(line)
                    # Join lines - handle words split across lines
                    payer_name = ''
                    for i, line in enumerate(name_lines):
                        if i == 0:
                            payer_name = line
                        else:
                            # Check if word is split mid-word (next line starts with lowercase)
                            # or if previous line ends with hyphen (hyphenated word split)
                            if payer_name.endswith('-'):
                                # Hyphenated split: remove hyphen and join
                                payer_name = payer_name[:-1] + line
                            elif line and line[0].islower():
                                # Mid-word split: join without space
                                # e.g., "Fel" + "elősségű" -> "Felelősségű"
                                payer_name = payer_name + line
                            else:
                                # Normal multi-word name: join with space
                                payer_name = payer_name + ' ' + line
                else:
                    payer_name = potential_payer

                fields['payer_name'] = payer_name

        # Payer IBAN (separate line) - HU + exactly 26 digits
        if m := re.search(r'Fizető fél IBAN:\s*(HU\d{26})', block_text):
            fields['payer_iban'] = m.group(1)

        # Payer BIC
        if m := re.search(r'Fizető fél BIC:\s*([A-Z0-9]+)', block_text):
            fields['payer_bic'] = m.group(1)

        # Beneficiary name
        if m := re.search(r'Kedvezményezett:\s*([^,\n]+)', block_text):
            fields['beneficiary_name'] = m.group(1).strip()

        # Kedvezményezett neve (alternative format)
        if m := re.search(r'Kedvezményezett neve:\s*([^\n]+)', block_text):
            fields['beneficiary_name'] = m.group(1).strip()

        # Beneficiary IBAN - HU + exactly 26 digits
        if m := re.search(r'Kedvezményezett IBAN:\s*(HU\d{26})', block_text):
            fields['beneficiary_iban'] = m.group(1)

        # Beneficiary BIC
        if m := re.search(r'Kedvezményezett BIC:\s*([A-Z0-9]+)', block_text):
            fields['beneficiary_bic'] = m.group(1)

        # Azonosító (could be beneficiary IBAN on separate line) - HU + exactly 26 digits
        if 'beneficiary_iban' not in fields:
            if m := re.search(r'Azonosító:\s*(HU\d{26})', block_text):
                fields['beneficiary_iban'] = m.group(1)

        # Reference (Közlemény) - with fallback to Nem strukturált közlemény
        if m := re.search(r'Közlemény:\s*([^\n]+)', block_text):
            fields['reference'] = m.group(1).strip()
        elif m := re.search(r'Nem strukturált közlemény:\s*([^\n]+)', block_text):
            fields['reference'] = m.group(1).strip()

    def _parse_date(self, date_str: str) -> date:
        """Parse Hungarian date format: 2025.01.15"""
        try:
            return datetime.strptime(date_str.strip(), '%Y.%m.%d').date()
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return date.today()

    def _clean_amount(self, amount_str: str) -> Decimal:
        """Convert Hungarian number format to Decimal."""
        cleaned = amount_str.replace(' ', '').replace(',', '.')
        cleaned = re.sub(r'[^\d.\-]', '', cleaned)
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')

    @classmethod
    def get_bank_code(cls) -> str:
        return cls.BANK_CODE

    @classmethod
    def get_bank_name(cls) -> str:
        return cls.BANK_NAME

    @classmethod
    def get_bank_bic(cls) -> str:
        return cls.BANK_BIC
