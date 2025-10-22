"""
K&H Bank statement parser - PDF FORMAT.

K&H provides detailed PDF bank statements with structured transaction data.
This adapter parses multi-line transaction blocks using regex patterns.

Supported transaction types:
- TRANSFER: Forint/SEPA/Nemzetközi átutalás
- FEE: Bank fees and transaction charges
- INTEREST: Interest (Kamat)
"""

import re
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import date

import pdfplumber

from .base import (
    BankStatementAdapter,
    NormalizedTransaction,
    StatementMetadata,
    BankStatementParseError,
)

logger = logging.getLogger(__name__)


class KHBankAdapter(BankStatementAdapter):
    """
    K&H Bank PDF statement parser.

    PDF Structure:
    - Page 1: Cover page with legal text
    - Page 2+: Transaction pages with header and table
    - Last page: Transaction summary with opening/closing balances

    Transaction Format (multi-line):
    2025.09.03 2025.09.03 Azonnali Forint átutalás bankon kívül - 212 309
    Ref.: BNK25246BJHLCKHJ Szla.:
    HU60117200012248254300000000, ITMAN Számítástechnikai
    Szolgáltató Kft. Közl.: SZA00456/2025 Hiv.:
    00000000000000000000000000000000053
    """

    BANK_CODE = 'KH'
    BANK_NAME = 'K&H Bank Zrt.'
    BANK_BIC = 'OKHBHUHB'  # K&H Bank BIC code

    @classmethod
    def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
        """
        Detect if this is a K&H Bank PDF statement.

        Looks for:
        - "K&H Bank Zrt." in header
        - "BANKSZÁMLAKIVONAT" text
        - Account number pattern "10410400-..."
        """
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                if len(pdf.pages) < 2:
                    return False

                # Check first two pages for K&H identifiers
                for page in pdf.pages[:2]:
                    text = page.extract_text()
                    if not text:
                        continue

                    # Look for K&H Bank and statement identifier
                    if ('K&H Bank Zrt.' in text or 'K&H Bank' in text) and \
                       'BANKSZÁMLAKIVONAT' in text:
                        return True

                return False
        except Exception as e:
            logger.debug(f"Failed to detect K&H Bank PDF: {e}")
            return False

    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Parse K&H Bank PDF statement."""
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                # Extract metadata from header (page 2)
                metadata = self._parse_metadata(pdf)

                # Extract all transactions from all pages
                transactions = self._parse_transactions(pdf)

                logger.info(f"Successfully parsed {len(transactions)} transactions from K&H Bank statement")

                return {
                    'metadata': metadata,
                    'transactions': transactions
                }

        except BankStatementParseError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse K&H Bank PDF: {e}", exc_info=True)
            raise BankStatementParseError(f"Failed to parse K&H Bank statement: {str(e)}")

    def _parse_metadata(self, pdf: pdfplumber.PDF) -> StatementMetadata:
        """
        Extract statement metadata from PDF header.

        Header format (page 2):
        Készítés dátuma: 2025.09.30
        Időszak: 2025.08.30-2025.09.30
        Kivonat sorszám: 3/2025
        Számlatulajdonos neve: MEDKA Technologies Korlátolt Felelősségű Társaság
        Számlaszám: 10410400-00000190-04894827
        Nemzetközi számlaszám (IBAN):HU28 1041 0400 0000 0190 0489 4827
        """
        if len(pdf.pages) < 2:
            raise BankStatementParseError("PDF has less than 2 pages")

        # Extract from page 2 (first actual statement page)
        text = pdf.pages[1].extract_text()

        # Account number
        account_match = re.search(r'Számlaszám:\s*([\d-]+)', text)
        if not account_match:
            raise BankStatementParseError("Could not find account number")
        account_number = self._clean_account_number(account_match.group(1))

        # IBAN
        iban_match = re.search(r'Nemzetközi számlaszám \(IBAN\):\s*(HU\d{2}[\d\s]+)', text)
        account_iban = self._clean_iban(iban_match.group(1)) if iban_match else ''

        # Statement period
        period_match = re.search(r'Időszak:\s*(\d{4}\.\d{2}\.\d{2})-(\d{4}\.\d{2}\.\d{2})', text)
        if not period_match:
            raise BankStatementParseError("Could not find statement period")

        period_from = self._parse_date(period_match.group(1))
        period_to = self._parse_date(period_match.group(2))

        # Statement number
        statement_match = re.search(r'Kivonat sorszám:\s*(\S+)', text)
        statement_number = statement_match.group(1) if statement_match else ''

        # Opening/Closing balances (from last page)
        last_page_text = pdf.pages[-1].extract_text()

        opening_match = re.search(r'Könyvelt nyitóegyenleg:\s*([\d\s-]+)', last_page_text)
        if not opening_match:
            raise BankStatementParseError("Could not find opening balance")
        opening_balance = self._clean_amount(opening_match.group(1))

        closing_match = re.search(r'Könyvelt záróegyenleg:\s*([\d\s-]+)', last_page_text)
        if not closing_match:
            raise BankStatementParseError("Could not find closing balance")

        # K&H PDFs often have corrupted closing balance due to PDF layout issues
        # Try to extract, but if it looks wrong, calculate from totals
        closing_str = closing_match.group(1).strip()
        closing_balance = self._clean_amount(closing_str)

        # Validate closing balance - if unreasonable, calculate from totals
        if abs(closing_balance) > 100000000 or abs(closing_balance) < 100:  # Outside reasonable range
            logger.warning(f"Closing balance looks corrupted: {closing_balance}, calculating from totals")

            # Try to extract credit and debit totals
            credit_match = re.search(r'Jóváírás összesen:\s*([\d\s]+)', last_page_text)
            debit_match = re.search(r'Terhelés összesen:\s*-?\s*([\d\s]+)', last_page_text)

            if credit_match and debit_match:
                total_credits = self._clean_amount(credit_match.group(1))
                total_debits = -abs(self._clean_amount(debit_match.group(1)))  # Make negative
                closing_balance = opening_balance + total_credits + total_debits
                logger.info(f"Calculated closing balance: {opening_balance} + {total_credits} + {total_debits} = {closing_balance}")

        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=account_number,
            account_iban=account_iban,
            period_from=period_from,
            period_to=period_to,
            statement_number=statement_number,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            raw_metadata={
                'pdf_pages': len(pdf.pages),
            }
        )

    def _parse_transactions(self, pdf: pdfplumber.PDF) -> List[NormalizedTransaction]:
        """
        Parse all transactions from PDF pages.

        Transaction format (multi-line):
        könyvelés értéknap tranzakció típus terhelés jóváírás
        dátuma tranzakció adatai
        2025.09.03 2025.09.03 Azonnali Forint átutalás bankon kívül - 212 309
        Ref.: BNK25246BJHLCKHJ Szla.:
        HU60117200012248254300000000, ITMAN Számítástechnikai
        Szolgáltató Kft. Közl.: SZA00456/2025 Hiv.:
        00000000000000000000000000000000053
        """
        transactions = []

        # Extract text from all pages except first (cover page)
        for page_num, page in enumerate(pdf.pages[1:], start=2):
            text = page.extract_text()
            if not text:
                continue

            # Split into lines
            lines = text.split('\n')

            # Find transaction blocks (lines starting with date pattern)
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Check if line starts with date (transaction start)
                if re.match(r'^\d{4}\.\d{2}\.\d{2}', line):
                    # Collect this transaction and all following lines until next transaction
                    trans_lines = [line]
                    i += 1

                    # Collect continuation lines
                    while i < len(lines):
                        next_line = lines[i].strip()
                        # Stop if we hit next transaction or balance summary
                        if re.match(r'^\d{4}\.\d{2}\.\d{2}', next_line) or \
                           'Könyvelt nyitóegyenleg' in next_line or \
                           'Jóváírás összesen' in next_line:
                            break
                        if next_line:  # Skip empty lines
                            trans_lines.append(next_line)
                        i += 1

                    # Parse this transaction block
                    try:
                        transaction = self._parse_transaction_block(trans_lines)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"Failed to parse transaction on page {page_num}: {e}")
                        continue
                else:
                    i += 1

        return transactions

    def _parse_transaction_block(self, lines: List[str]) -> Optional[NormalizedTransaction]:
        """
        Parse a single transaction block.

        First line format:
        2025.09.03 2025.09.03 Azonnali Forint átutalás bankon kívül - 212 309

        Pattern: booking_date value_date transaction_type [- debit | credit]
        """
        if not lines:
            return None

        first_line = lines[0]
        full_text = ' '.join(lines)

        # Parse first line: dates, type, amount
        # Pattern: YYYY.MM.DD YYYY.MM.DD Type [- Amount | Amount]
        match = re.match(
            r'^(\d{4}\.\d{2}\.\d{2})\s+(\d{4}\.\d{2}\.\d{2})\s+(.+?)\s+(-\s*[\d\s]+|[\d\s]+)$',
            first_line
        )

        if not match:
            logger.warning(f"Could not parse transaction first line: {first_line}")
            return None

        booking_date = self._parse_date(match.group(1))
        value_date = self._parse_date(match.group(2))
        transaction_type_text = match.group(3).strip()
        amount_str = match.group(4).strip()

        if not booking_date or not value_date:
            return None

        # Parse amount (negative sign means debit)
        amount = self._clean_amount(amount_str)

        # Currency (K&H statements are HUF by default)
        currency = 'HUF'

        # Check for foreign currency in text
        if 'EUR' in full_text:
            # Extract original amount for SEPA/foreign transactions
            orig_match = re.search(r'Eredeti összeg:\s*([\d\s.,]+)\s+EUR', full_text)
            if orig_match:
                # This is a multi-currency transaction
                pass  # We'll handle this below

        # Map transaction type
        transaction_type = self._map_transaction_type(transaction_type_text)

        # Build description
        description = transaction_type_text

        # Create transaction
        transaction = NormalizedTransaction(
            transaction_type=transaction_type,
            booking_date=booking_date,
            value_date=value_date,
            amount=amount,
            currency=currency,
            description=description,
            short_description=transaction_type_text[:200],
            transaction_type_code=transaction_type_text,
        )

        # Extract additional fields from continuation lines
        self._extract_transaction_details(full_text, transaction)

        # Store raw data
        transaction.raw_data = {
            'lines': lines,
            'full_text': full_text,
        }

        return transaction

    def _extract_transaction_details(self, text: str, transaction: NormalizedTransaction):
        """
        Extract additional transaction details from text.

        Possible fields:
        - Ref.: BNK25246BJHLCKHJ (transaction ID)
        - Szla.: HU60117200012248254300000000, ITMAN Kft. (beneficiary IBAN and name)
        - Közl.: SZA00456/2025 (reference/memo)
        - Hiv.: 00000000000000000000000000000000053 (payment ID)
        - Tr. azon.: PI25247JKZVDQWRF (transaction reference)
        - Árf.: 395.33 HUF/EUR (exchange rate)
        - Eredeti összeg: 14100.00 EUR (original amount in foreign currency)
        """
        # Transaction ID
        ref_match = re.search(r'Ref\.:\s*(\S+)', text)
        if ref_match:
            transaction.transaction_id = ref_match.group(1)

        # Beneficiary/Payer IBAN and name
        # Pattern: Szla.: HU... Name (may be multi-line)
        # Extract everything between IBAN and next keyword (Közl/Hiv/Tr/Árf)
        szla_match = re.search(r'Szla\.:\s*([A-Z]{2}\d+[\d\s]*)[,\s]+(.*?)(?=\s+(?:Közl\.|Hiv\.|Tr\. azon\.|Árf\.|$))', text, re.DOTALL)
        if szla_match:
            iban = self._clean_iban(szla_match.group(1))
            # Name may span multiple lines - clean it up
            name_raw = szla_match.group(2).strip()
            # Remove newlines and extra spaces
            name = ' '.join(name_raw.split()).rstrip(',')

            # Determine payer/beneficiary based on amount
            if transaction.amount < 0:
                # Outgoing - we are payer
                transaction.beneficiary_iban = iban
                transaction.beneficiary_name = name
                # Try to extract account number from IBAN
                if iban.startswith('HU'):
                    transaction.beneficiary_account_number = self._iban_to_account(iban)
            else:
                # Incoming - we are beneficiary
                transaction.payer_iban = iban
                transaction.payer_name = name
                if iban.startswith('HU'):
                    transaction.payer_account_number = self._iban_to_account(iban)

        # Reference (Közlemény)
        kozl_match = re.search(r'Közl\.:\s*([^Hiv:Tr\.Árf:]+)', text)
        if kozl_match:
            transaction.reference = kozl_match.group(1).strip()

        # Payment ID (Hivatkozási szám)
        hiv_match = re.search(r'Hiv\.:\s*(\d+)', text)
        if hiv_match:
            transaction.payment_id = hiv_match.group(1)

        # Transaction reference
        tr_match = re.search(r'Tr\. azon\.:\s*(\S+)', text)
        if tr_match:
            transaction.partner_id = tr_match.group(1)

        # Exchange rate and original amount (for foreign currency transactions)
        arf_match = re.search(r'Árf\.:\s*([\d.,]+)\s+HUF/(\w+)', text)
        if arf_match:
            rate_str = arf_match.group(1).replace(',', '.')
            orig_currency = arf_match.group(2)
            try:
                transaction.exchange_rate = Decimal(rate_str)
            except:
                pass

            # Extract original amount
            orig_match = re.search(r'Eredeti összeg:\s*([\d\s.,]+)\s+' + orig_currency, text)
            if orig_match:
                orig_amount_str = orig_match.group(1).replace(',', '.').replace(' ', '')
                try:
                    orig_amount = Decimal(orig_amount_str)
                    # Keep sign from HUF amount
                    if transaction.amount < 0:
                        orig_amount = -abs(orig_amount)
                    else:
                        orig_amount = abs(orig_amount)

                    transaction.original_amount = orig_amount
                    transaction.original_currency = orig_currency
                except:
                    pass

    def _map_transaction_type(self, type_text: str) -> str:
        """
        Map K&H transaction types to normalized types.

        K&H types:
        - "Forint átutalás..." → TRANSFER
        - "Azonnali Forint átutalás..." → TRANSFER
        - "SEPA átutalás..." → TRANSFER
        - "Nemzetközi átutalás..." → TRANSFER
        - "...díj..." → FEE
        - "Kamat" → INTEREST
        - "Számlavezetési díj" → FEE
        - "Könyvelési díj" → FEE
        """
        type_lower = type_text.lower()

        # Fees
        if 'díj' in type_lower or 'költség' in type_lower:
            return 'FEE'

        # Interest
        if 'kamat' in type_lower:
            return 'INTEREST'

        # Transfers
        if 'átutalás' in type_lower or 'sepa' in type_lower or 'nemzetközi' in type_lower:
            return 'TRANSFER'

        return 'OTHER'

    def _iban_to_account(self, iban: str) -> str:
        """
        Convert Hungarian IBAN to account number format.

        HU28 1041 0400 0000 0190 0489 4827
        →
        10410400-00000190-04894827

        Format: HU + 2 check digits + 3 bank code + 4 branch + 16 account
        Account number: 8 digits + dash + 8 digits + dash + 8 digits
        """
        # Remove HU prefix and spaces
        iban_clean = iban.replace('HU', '').replace(' ', '')

        if len(iban_clean) < 26:
            return ''

        # Skip check digits (2) and bank code (3+4=7)
        # Extract account number part (remaining 16 digits)
        account_part = iban_clean[9:]  # Skip first 9 chars (2 check + 7 bank)

        if len(account_part) >= 24:
            # Format: 8-8-8
            return f'{account_part[0:8]}-{account_part[8:16]}-{account_part[16:24]}'

        return ''
