"""
GRÁNIT Bank Nyrt. statement parser.

Parses PDF bank statements from GRÁNIT Bank, extracting:
- Statement metadata (account, period, balances)
- ALL transaction types (AFR transfers, POS purchases, fees, interest)
- Complete transaction details (IBAN, payment ID, reference, amounts)
"""

import re
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import date

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

    Handles multi-page PDF statements with various transaction types:
    - AFR jóváírás/terhelés (Instant payments) - multi-line format
    - POS vásárlás (Card purchases) - multi-line format
    - Előjegyzett jutalék (Bank fees) - single line
    - Kamat (Interest) - single line
    - Other transaction types
    """

    BANK_CODE = 'GRANIT'
    BANK_NAME = 'GRÁNIT Bank Nyrt.'
    BANK_BIC = 'GNBAHUHB'

    @classmethod
    def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
        """
        Detect GRÁNIT Bank PDF by looking for bank identifiers.

        Checks for:
        - "GRÁNIT Bank" text in first page
        - BIC code "GNBAHUHB"
        """
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
        """
        Parse GRÁNIT Bank statement PDF.

        Returns:
            {
                'metadata': StatementMetadata,
                'transactions': List[NormalizedTransaction]
            }
        """
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

                # Parse ALL transactions
                transactions = self._parse_all_transactions(full_text)

                return {
                    'metadata': metadata,
                    'transactions': transactions
                }

        except Exception as e:
            if isinstance(e, BankStatementParseError):
                raise
            raise BankStatementParseError(f"Failed to parse GRÁNIT Bank PDF: {str(e)}")

    def _parse_metadata(self, text: str) -> StatementMetadata:
        """
        Extract statement metadata from PDF header.

        Looks for:
        - Számlaszám: 12100011-19014874
        - IBAN szám: HU62 1210 0011 1901 4874 0000 0000
        - Könyvelés dátuma: 2025.01.01 - 2025.01.31
        - Kivonatszám/számla sorszáma: 1/2025
        - Utolsó kivonat egyenlege: 845 898
        """
        metadata_dict = {}

        # Account number
        if m := re.search(r'Számlaszám:\s*([0-9\-]+)', text):
            metadata_dict['account_number'] = self._clean_account_number(m.group(1))
        else:
            raise BankStatementParseError("Could not find account number (Számlaszám)")

        # IBAN
        if m := re.search(r'IBAN szám:\s*([A-Z0-9\s]+)', text):
            metadata_dict['account_iban'] = self._clean_iban(m.group(1))
        else:
            metadata_dict['account_iban'] = ""

        # Statement period
        if m := re.search(r'Könyvelés dátuma:\s*([0-9.]+)\s*-\s*([0-9.]+)', text):
            period_from = self._parse_date(m.group(1))
            period_to = self._parse_date(m.group(2))
            if not period_from or not period_to:
                raise BankStatementParseError("Could not parse statement period dates")
            metadata_dict['period_from'] = period_from
            metadata_dict['period_to'] = period_to
        else:
            raise BankStatementParseError("Could not find statement period (Könyvelés dátuma)")

        # Statement number
        if m := re.search(r'Kivonatszám/számla sorszáma:\s*([^\n]+)', text):
            metadata_dict['statement_number'] = m.group(1).strip()
        else:
            metadata_dict['statement_number'] = ""

        # Opening balance
        if m := re.search(r'Utolsó kivonat egyenlege:\s*([\d\s]+)', text):
            metadata_dict['opening_balance'] = self._clean_amount(m.group(1))
        else:
            metadata_dict['opening_balance'] = Decimal('0.00')

        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=metadata_dict['account_number'],
            account_iban=metadata_dict['account_iban'],
            period_from=metadata_dict['period_from'],
            period_to=metadata_dict['period_to'],
            statement_number=metadata_dict['statement_number'],
            opening_balance=metadata_dict['opening_balance'],
            closing_balance=None,  # Not always present in GRÁNIT statements
            raw_metadata=metadata_dict
        )

    def _parse_all_transactions(self, text: str) -> List[NormalizedTransaction]:
        """
        Parse ALL transaction types from statement.

        Strategy:
        1. Split text into lines
        2. State machine to detect transaction boundaries
        3. Multi-line parsing for complex transactions (AFR, POS)
        4. Single-line parsing for simple transactions (fees, interest)
        5. Classify each transaction by type
        """
        transactions = []
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check for AFR transfer (multi-line)
            if 'AFR' in line and ('jóváírás' in line or 'terhelés' in line):
                try:
                    txn, lines_consumed = self._parse_afr_transfer(lines, i)
                    if txn:
                        transactions.append(txn)
                    i += lines_consumed
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse AFR transaction at line {i}: {e}")
                    i += 1
                    continue

            # Check for POS purchase (multi-line)
            if 'POS vásárlás' in line:
                try:
                    txn, lines_consumed = self._parse_pos_purchase(lines, i)
                    if txn:
                        transactions.append(txn)
                    i += lines_consumed
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse POS transaction at line {i}: {e}")
                    i += 1
                    continue

            # Check for bank fee (single-line or multi-line)
            if 'jutalék' in line.lower() or 'költség' in line.lower():
                try:
                    txn = self._parse_bank_fee(line)
                    if txn:
                        transactions.append(txn)
                except Exception as e:
                    logger.warning(f"Failed to parse fee at line {i}: {e}")
                i += 1
                continue

            # Check for interest
            if 'kamat' in line.lower():
                try:
                    txn = self._parse_interest(line)
                    if txn:
                        transactions.append(txn)
                except Exception as e:
                    logger.warning(f"Failed to parse interest at line {i}: {e}")
                i += 1
                continue

            # Check for regular transfer
            if 'átutalás' in line.lower():
                try:
                    txn, lines_consumed = self._parse_transfer(lines, i)
                    if txn:
                        transactions.append(txn)
                        i += lines_consumed
                        continue
                except Exception as e:
                    logger.warning(f"Failed to parse transfer at line {i}: {e}")
                    i += 1
                    continue

            i += 1

        logger.info(f"Parsed {len(transactions)} transactions from GRÁNIT Bank statement")
        return transactions

    def _parse_afr_transfer(self, lines: List[str], start_idx: int) -> Tuple[Optional[NormalizedTransaction], int]:
        """
        Parse AFR transfer (multi-line format).

        Format:
        Line 0: 2025.04.01 AFR jóváírás bankon kívül                    4 675 505
        Line 1: 2025.04.01 Értéknap: 2025.04.01, Fizetési azonosító: J0057M8Y6XGLKAAC
        Line 2: Partnerek közti egyedi azonosító: NOTPROVIDED
        Line 3: Tranzakció azonosító: J0057M8Y6XGLKAAC
        Line 4: Fizető fél: DANUBIUS EXPERT ZRT.
        Line 5: Fizető fél IBAN: HU62116000060000000078175381
        Line 6: Kedvezményezett IBAN: HU62121000111901487400000000
        Line 7: Kedvezményezett neve: IT Cardigan Kft.
        Line 8: Nem strukturált közlemény: ITC-2025-6
        Line 9: AFR elszámolás időpontja: 2025.04.01 09.42.36
        Line 10: Fizető fél BIC: GIBAHUHB, GNBAHUHB, RTP eredeti összeg: 4675505
        """
        first_line = lines[start_idx].strip()

        # Extract date and amount from first line
        # Pattern: "2025.01.13 AFR jóváírás bankon kívül 10 260"
        match = re.match(r'^([\d.]+)\s+(AFR\s+(?:jóváírás|terhelés)[^\d\-]*)([\d\s\-,]+)$', first_line)
        if not match:
            return None, 1

        booking_date = self._parse_date(match.group(1))
        description = match.group(2).strip()
        amount = self._clean_amount(match.group(3))

        # Determine transaction type
        if 'jóváírás' in description:
            txn_type = 'AFR_CREDIT'
        else:
            txn_type = 'AFR_DEBIT'

        # Collect next 15 lines for metadata
        metadata = {
            'booking_date': booking_date,
            'description': description,
        }

        lines_to_scan = min(15, len(lines) - start_idx - 1)
        for offset in range(1, lines_to_scan + 1):
            line = lines[start_idx + offset].strip()

            # Value date
            if m := re.search(r'Értéknap:\s*([\d.]+)', line):
                metadata['value_date'] = self._parse_date(m.group(1))

            # Payment ID
            if m := re.search(r'Fizetési azonosító:\s*(\S+)', line):
                metadata['payment_id'] = m.group(1)

            # Transaction ID
            if m := re.search(r'Tranzakció azonosító:\s*(\S+)', line):
                metadata['transaction_id'] = m.group(1)

            # Payer name
            if m := re.search(r'Fizető fél:\s*([^\n]+)', line):
                if 'IBAN' not in m.group(1):  # Avoid capturing IBAN line
                    metadata['payer_name'] = m.group(1).strip()

            # Payer IBAN
            if m := re.search(r'Fizető fél IBAN:\s*([A-Z0-9\s]+)', line):
                metadata['payer_iban'] = self._clean_iban(m.group(1))

            # Beneficiary name
            if m := re.search(r'Kedvezményezett neve:\s*([^\n]+)', line):
                metadata['beneficiary_name'] = m.group(1).strip()

            # Beneficiary IBAN
            if m := re.search(r'Kedvezményezett IBAN:\s*([A-Z0-9\s]+)', line):
                metadata['beneficiary_iban'] = self._clean_iban(m.group(1))

            # Reference (CRITICAL for matching)
            if m := re.search(r'Nem strukturált közlemény:\s*([^\n]+)', line):
                metadata['reference'] = m.group(1).strip()

            # BIC
            if m := re.search(r'Fizető fél BIC:\s*([A-Z,\s]+)', line):
                bic_str = m.group(1).strip()
                # Take first BIC code
                if ',' in bic_str:
                    metadata['payer_bic'] = bic_str.split(',')[0].strip()
                else:
                    metadata['payer_bic'] = bic_str

            # Stop if we hit next transaction
            if re.match(r'^\d{4}\.\d{2}\.\d{2}', line):
                break

        # Create normalized transaction
        txn = NormalizedTransaction(
            transaction_type=txn_type,
            booking_date=metadata.get('booking_date') or booking_date,
            value_date=metadata.get('value_date') or booking_date,
            amount=amount,
            currency='HUF',
            description=description,
            short_description=f"AFR {'jóváírás' if txn_type == 'AFR_CREDIT' else 'terhelés'}",
            payment_id=metadata.get('payment_id'),
            transaction_id=metadata.get('transaction_id'),
            payer_name=metadata.get('payer_name'),
            payer_iban=metadata.get('payer_iban'),
            payer_bic=metadata.get('payer_bic'),
            beneficiary_name=metadata.get('beneficiary_name'),
            beneficiary_iban=metadata.get('beneficiary_iban'),
            reference=metadata.get('reference'),
            raw_data=metadata
        )

        return txn, lines_to_scan + 1

    def _parse_pos_purchase(self, lines: List[str], start_idx: int) -> Tuple[Optional[NormalizedTransaction], int]:
        """
        Parse POS purchase (multi-line format).

        Format:
        Line 0: 2025.01.02 POS vásárlás tranzakció belföld Időpont: 2024.12.30 22:41 -29 508
        Line 1: 2025.01.02 Kártya: 558644******5059 Hely: OHU3124B:OMV 1907
        Line 2: BANK
        """
        first_line = lines[start_idx].strip()

        # Extract date and amount
        match = re.match(r'^([\d.]+)\s+POS vásárlás[^\d\-]*([\d\s\-,]+)$', first_line)
        if not match:
            return None, 1

        booking_date = self._parse_date(match.group(1))
        amount = self._clean_amount(match.group(2))

        metadata = {
            'booking_date': booking_date,
            'description': first_line,
        }

        # Check next 2-3 lines for card info
        lines_to_scan = min(3, len(lines) - start_idx - 1)
        for offset in range(1, lines_to_scan + 1):
            line = lines[start_idx + offset].strip()

            # Card number
            if m := re.search(r'Kártya:\s*([0-9*]+)', line):
                metadata['card_number'] = m.group(1)

            # Merchant location/name
            if m := re.search(r'Hely:\s*([^\n]+)', line):
                location = m.group(1).strip()
                # Parse location code and name
                if ':' in location:
                    parts = location.split(':', 1)
                    metadata['merchant_location'] = parts[0].strip()
                    metadata['merchant_name'] = parts[1].strip()
                else:
                    metadata['merchant_name'] = location

            # Stop if we hit next transaction
            if re.match(r'^\d{4}\.\d{2}\.\d{2}', line) and 'Kártya' not in line:
                break

        txn = NormalizedTransaction(
            transaction_type='POS_PURCHASE',
            booking_date=booking_date,
            value_date=booking_date,
            amount=amount,
            currency='HUF',
            description=first_line,
            short_description="POS vásárlás",
            card_number=metadata.get('card_number'),
            merchant_name=metadata.get('merchant_name'),
            merchant_location=metadata.get('merchant_location'),
            raw_data=metadata
        )

        return txn, lines_to_scan + 1

    def _parse_bank_fee(self, line: str) -> Optional[NormalizedTransaction]:
        """
        Parse bank fee (single-line).

        Format: "2025.04.01         Előjegyzett jutalék:                                      -664"
        """
        # Extract date and amount
        match = re.match(r'^([\d.]+)\s+.*(?:jutalék|költség)[^\d\-]*([\d\s\-,]+)$', line, re.IGNORECASE)
        if not match:
            return None

        booking_date = self._parse_date(match.group(1))
        amount = self._clean_amount(match.group(2))

        return NormalizedTransaction(
            transaction_type='BANK_FEE',
            booking_date=booking_date,
            value_date=booking_date,
            amount=amount,
            currency='HUF',
            description=line.strip(),
            short_description="Banki költség",
            raw_data={'original_line': line}
        )

    def _parse_interest(self, line: str) -> Optional[NormalizedTransaction]:
        """Parse interest charge/credit (single-line)"""
        match = re.match(r'^([\d.]+)\s+.*kamat[^\d\-]*([\d\s\-,]+)$', line, re.IGNORECASE)
        if not match:
            return None

        booking_date = self._parse_date(match.group(1))
        amount = self._clean_amount(match.group(2))

        # Determine if credit or debit
        txn_type = 'INTEREST_CREDIT' if amount > 0 else 'INTEREST_DEBIT'

        return NormalizedTransaction(
            transaction_type=txn_type,
            booking_date=booking_date,
            value_date=booking_date,
            amount=amount,
            currency='HUF',
            description=line.strip(),
            short_description="Kamat",
            raw_data={'original_line': line}
        )

    def _parse_transfer(self, lines: List[str], start_idx: int) -> Tuple[Optional[NormalizedTransaction], int]:
        """Parse regular bank transfer (may be multi-line)"""
        first_line = lines[start_idx].strip()

        match = re.match(r'^([\d.]+)\s+.*átutalás[^\d\-]*([\d\s\-,]+)$', first_line, re.IGNORECASE)
        if not match:
            return None, 1

        booking_date = self._parse_date(match.group(1))
        amount = self._clean_amount(match.group(2))

        # Determine type
        if 'jóváírás' in first_line.lower() or amount > 0:
            txn_type = 'TRANSFER_CREDIT'
        else:
            txn_type = 'TRANSFER_DEBIT'

        # Scan next few lines for additional info
        metadata = {'description': first_line}
        lines_to_scan = min(5, len(lines) - start_idx - 1)

        for offset in range(1, lines_to_scan + 1):
            line = lines[start_idx + offset].strip()

            # Look for common patterns
            if 'Értéknap:' in line:
                if m := re.search(r'Értéknap:\s*([\d.]+)', line):
                    metadata['value_date'] = self._parse_date(m.group(1))

            if 'Fizető fél:' in line:
                if m := re.search(r'Fizető fél:\s*([^\n]+)', line):
                    metadata['payer_name'] = m.group(1).strip()

            # Stop if next transaction
            if re.match(r'^\d{4}\.\d{2}\.\d{2}', line):
                break

        txn = NormalizedTransaction(
            transaction_type=txn_type,
            booking_date=booking_date,
            value_date=metadata.get('value_date') or booking_date,
            amount=amount,
            currency='HUF',
            description=first_line,
            short_description="Átutalás",
            payer_name=metadata.get('payer_name'),
            raw_data=metadata
        )

        return txn, lines_to_scan + 1
