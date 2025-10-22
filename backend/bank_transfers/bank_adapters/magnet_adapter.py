"""
MagNet Magyar Közösségi Bank XML statement parser.

Magnet Bank provides XML statements with clean, structured data including:
- All transaction types (AFR, Átutalás, Card payments, Fees)
- Complete counterparty information (IBAN, names)
- Fee breakdown (Jutalék, Illeték)
- Card transaction details
"""

import re
import logging
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import date, datetime

from .base import (
    BankStatementAdapter,
    NormalizedTransaction,
    StatementMetadata,
    BankStatementParseError,
)

logger = logging.getLogger(__name__)


class MagnetBankAdapter(BankStatementAdapter):
    """
    MagNet Magyar Közösségi Bank XML statement parser.

    XML Structure:
    <NetBankXML>
        <FEJLEC> - Header with bank info and document details
        <SzamlaInfo> - Account information
        <EgyenlegInfo> - Balance information
        <Tranzakcio> - Individual transactions
    </NetBankXML>
    """

    BANK_CODE = 'MAGNET'
    BANK_NAME = 'MagNet Magyar Közösségi Bank'
    BANK_BIC = 'MKKB'  # MagNet BIC code

    @classmethod
    def detect(cls, file_bytes: bytes, filename: str) -> bool:
        """Detect MagNet Bank XML by looking for NetBankXML root and bank name."""
        try:
            # Try to parse as XML
            root = ET.fromstring(file_bytes)

            # Check root element
            if root.tag != 'NetBankXML':
                return False

            # Check for FEJLEC/KIBOCSATO/Nev containing "MagNet"
            fejlec = root.find('FEJLEC')
            if fejlec is None:
                return False

            kibocsato = fejlec.find('KIBOCSATO')
            if kibocsato is None:
                return False

            nev = kibocsato.find('Nev')
            if nev is None or nev.text is None:
                return False

            return 'MagNet' in nev.text or 'MAGNET' in nev.text.upper()

        except ET.ParseError as e:
            logger.debug(f"XML parse error during detection: {e}")
            return False
        except Exception as e:
            logger.warning(f"Error detecting MagNet Bank XML: {e}")
            return False

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        """Parse MagNet Bank XML statement."""
        try:
            root = ET.fromstring(file_bytes)

            if root.tag != 'NetBankXML':
                raise BankStatementParseError("Invalid MagNet XML: root element must be NetBankXML")

            # Parse metadata from header
            metadata = self._parse_metadata(root)

            # Parse all transactions
            transactions = self._parse_transactions(root)

            logger.info(f"Successfully parsed {len(transactions)} transactions from MagNet Bank statement")

            return {
                'metadata': metadata,
                'transactions': transactions
            }

        except BankStatementParseError:
            raise
        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}", exc_info=True)
            raise BankStatementParseError(f"Invalid XML format: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse MagNet Bank XML: {e}", exc_info=True)
            raise BankStatementParseError(f"Failed to parse MagNet Bank statement: {str(e)}")

    def _parse_metadata(self, root: ET.Element) -> StatementMetadata:
        """Parse statement header metadata."""

        # Get FEJLEC (header)
        fejlec = root.find('FEJLEC')
        if fejlec is None:
            raise BankStatementParseError("Missing FEJLEC element")

        # Bank information
        kibocsato = fejlec.find('KIBOCSATO')
        bank_name = self._get_text(kibocsato, 'Nev', 'Unknown Bank')

        # Document information
        doc_info = fejlec.find('DokumentumInfo')
        statement_id = self._get_text(doc_info, 'SzamlaID', '')
        period_str = self._get_text(doc_info, 'AlCim', '')  # e.g., "2025-09"

        # Account information
        szamla_info = root.find('SzamlaInfo')
        if szamla_info is None:
            raise BankStatementParseError("Missing SzamlaInfo element")

        account_number = self._get_text(szamla_info, 'Szamlaszam', '')
        account_iban = self._build_iban(account_number)  # Convert to IBAN format

        # Balance information
        egyenleg_info = root.find('EgyenlegInfo')
        if egyenleg_info is None:
            raise BankStatementParseError("Missing EgyenlegInfo element")

        opening_balance_elem = egyenleg_info.find('NyitoEgyenleg')
        opening_balance = self._parse_decimal(opening_balance_elem.text if opening_balance_elem is not None else '0')

        closing_balance_elem = egyenleg_info.find('ZaroEgyenleg')
        closing_balance = self._parse_decimal(closing_balance_elem.text if closing_balance_elem is not None else '0')

        # Parse period dates from AlCim (e.g., "2025-09")
        period_from, period_to = self._parse_period(period_str)

        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=account_number,
            account_iban=account_iban,
            period_from=period_from,
            period_to=period_to,
            statement_number=statement_id,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            raw_metadata={
                'bank_tax_id': self._get_text(kibocsato, 'AdoigazgatasiSzam', ''),
                'bank_address': self._get_text(kibocsato, 'Cim', ''),
                'account_holder': self._get_text(szamla_info, 'Nev', ''),
                'total_debit': self._get_text(egyenleg_info, 'Terheles', '0'),
                'total_credit': self._get_text(egyenleg_info, 'Jovairas', '0'),
                'debit_count': self._get_text(egyenleg_info, 'TerhelesDB', '0'),
                'credit_count': self._get_text(egyenleg_info, 'JovairasDB', '0'),
            }
        )

    def _parse_transactions(self, root: ET.Element) -> List[NormalizedTransaction]:
        """Parse all transaction elements."""
        transactions = []

        for trans_elem in root.findall('Tranzakcio'):
            try:
                transaction = self._parse_transaction(trans_elem)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to parse transaction: {e}", exc_info=True)
                continue

        return transactions

    def _parse_transaction(self, trans: ET.Element) -> Optional[NormalizedTransaction]:
        """Parse a single transaction element."""

        # Basic fields
        nbid = trans.get('NBID', '')
        trans_num = self._get_text(trans, 'Tranzakcioszam', '')
        counterparty = self._get_text(trans, 'Ellenpartner', '')
        counter_iban = self._get_text(trans, 'Ellenszamla', '')

        # Amount and currency
        osszeg_elem = trans.find('Osszeg')
        if osszeg_elem is None:
            logger.warning(f"Transaction {trans_num} missing Osszeg element")
            return None

        amount = self._parse_decimal(osszeg_elem.text or '0')
        currency = osszeg_elem.get('Devizanem', 'HUF')

        # Reference/Közlemény
        reference = self._get_text(trans, 'Kozlemeny', '')

        # Dates
        booking_date_str = self._get_text(trans, 'Terhelesnap', '')
        value_date_str = self._get_text(trans, 'Esedekessegnap', '')

        booking_date = self._parse_magnet_date(booking_date_str)
        value_date = self._parse_magnet_date(value_date_str) or booking_date

        if not booking_date:
            logger.warning(f"Transaction {trans_num} missing date")
            return None

        # Transaction type
        magnet_type = self._get_text(trans, 'Tipus', '')
        transaction_type = self._map_transaction_type(magnet_type)

        # Fee
        fee_elem = trans.find('Jutalekosszeg')
        fee_amount_base = self._parse_decimal(fee_elem.text if fee_elem is not None else '0')

        # Build description
        description = self._build_description(counterparty, reference, magnet_type)
        short_description = f"{magnet_type}: {counterparty}"

        # Initialize transaction
        transaction = NormalizedTransaction(
            transaction_type=transaction_type,
            booking_date=booking_date,
            value_date=value_date,
            amount=amount,
            currency=currency,
            description=description,
            short_description=short_description,
            transaction_id=trans_num,
            reference=reference,
            transaction_type_code=magnet_type,
        )

        # Parse fees from TranzakcioKiegeszito
        kiegeszito = trans.find('TranzakcioKiegeszito')
        if kiegeszito is not None:
            # Check for JutalekKiegeszito (detailed fee)
            jutalek_elem = kiegeszito.find('JutalekKiegeszito')
            if jutalek_elem is not None and jutalek_elem.text:
                detailed_fee = self._parse_decimal(jutalek_elem.text)
                if detailed_fee != Decimal('0'):
                    transaction.fee_amount = abs(detailed_fee)
            elif fee_amount_base != Decimal('0'):
                transaction.fee_amount = abs(fee_amount_base)

            # Store illeték (transaction tax) in raw_data
            illetek_elem = kiegeszito.find('TranzIlletekKiegeszito')
            if illetek_elem is not None and illetek_elem.text:
                transaction.raw_data['transaction_tax'] = illetek_elem.text

            # Parse card transaction details
            kartya_elem = kiegeszito.find('KartyaKiegeszito')
            if kartya_elem is not None:
                self._parse_card_details(kartya_elem, transaction, reference)

            # Parse cost breakdown
            koltseg_elem = kiegeszito.find('KoltsegKiegeszito')
            if koltseg_elem is not None:
                costs = []
                for koltseg in koltseg_elem.findall('Koltseg'):
                    cost_type = koltseg.get('Koltsegnem', '')
                    cost_amount = koltseg.text or '0'
                    costs.append({
                        'type': cost_type,
                        'amount': cost_amount
                    })
                if costs:
                    transaction.raw_data['cost_breakdown'] = costs

        # Determine payer/beneficiary based on amount sign
        if amount < 0:
            # Debit - we are payer
            transaction.payer_name = self._get_text(trans, 'Nev', '')
            transaction.payer_account_number = self._get_text(trans, 'Szamlaszam', '')
            transaction.beneficiary_name = counterparty
            transaction.beneficiary_iban = counter_iban
            if counter_iban:
                transaction.beneficiary_account_number = self._iban_to_account(counter_iban)
        else:
            # Credit - we are beneficiary
            transaction.payer_name = counterparty
            transaction.payer_iban = counter_iban
            if counter_iban:
                transaction.payer_account_number = self._iban_to_account(counter_iban)
            transaction.beneficiary_name = self._get_text(trans, 'Nev', '')
            transaction.beneficiary_account_number = self._get_text(trans, 'Szamlaszam', '')

        # Store raw XML data
        transaction.raw_data['nbid'] = nbid
        transaction.raw_data['xml_type'] = magnet_type

        return transaction

    def _parse_card_details(self, kartya_elem: ET.Element, transaction: NormalizedTransaction, reference: str):
        """Parse card transaction details from KartyaKiegeszito."""

        # Extract card number from reference (Közlemény)
        # Pattern: "558301******7539 Vásárlás..."
        card_match = re.search(r'(\d+\*+\d+)', reference)
        if card_match:
            transaction.card_number = card_match.group(1)

        # Merchant location
        location = self._get_text(kartya_elem, 'ElfogadasHelye', '')
        if location:
            transaction.merchant_location = location

        # Terminal ID contains merchant name
        terminal = self._get_text(kartya_elem, 'TerminalAzonosito', '')
        if terminal:
            # Format: "SIMPLEP*SZERSZAMOK-WEB, 022P5129"
            parts = terminal.split(',')
            if parts:
                merchant_name = parts[0].strip()
                transaction.merchant_name = merchant_name

            # Store full terminal info
            transaction.raw_data['terminal_id'] = terminal

    def _map_transaction_type(self, magnet_type: str) -> str:
        """
        Map MagNet transaction types to our normalized types.

        MagNet types:
        - Átutalás (IB/IG2) - Outgoing transfer
        - Átutalás (IG2) - Incoming transfer
        - AFR jóváírás/terhelés - AFR credit/debit
        - Érkezett bankkártya terhelés/jóváírás - Card debit/credit
        - Költségelszámolás - Cost accounting (fees)
        """
        magnet_lower = magnet_type.lower()

        # Card transactions
        if 'bankkártya' in magnet_lower:
            return 'POS'

        # Transfers
        if 'átutalás' in magnet_lower or 'afr' in magnet_lower:
            return 'TRANSFER'

        # Fees
        if 'költség' in magnet_lower or 'díj' in magnet_lower:
            return 'FEE'

        # Default
        return 'OTHER'

    def _build_description(self, counterparty: str, reference: str, magnet_type: str) -> str:
        """Build full transaction description."""
        parts = [magnet_type]

        if counterparty:
            parts.append(f"Ellenpartner: {counterparty}")

        if reference:
            parts.append(f"Közlemény: {reference}")

        return " | ".join(parts)

    def _build_iban(self, account_number: str) -> str:
        """Convert MagNet account number to IBAN format."""
        if not account_number:
            return ''

        # MagNet account format: 16200151-18581773
        # IBAN format: HU## 1620 0151 1858 1773
        clean = account_number.replace('-', '').replace(' ', '')

        if len(clean) == 16:
            # Format as IBAN (without checksum calculation for now)
            formatted = f"HU{clean[0:4]} {clean[4:8]} {clean[8:12]} {clean[12:16]}"
            return formatted.replace(' ', '')

        return clean

    def _iban_to_account(self, iban: str) -> str:
        """Extract account number from IBAN."""
        if not iban:
            return ''

        # Remove spaces and HU prefix
        clean = iban.replace(' ', '').replace('HU', '')

        # Remove first 2 digits (checksum)
        if len(clean) > 2:
            clean = clean[2:]

        # Format as account number
        if len(clean) >= 16:
            return f"{clean[0:8]}-{clean[8:16]}"

        return clean

    def _parse_period(self, period_str: str) -> tuple[date, date]:
        """
        Parse period string to date range.

        Input: "2025-09"
        Output: (2025-09-01, 2025-09-30)
        """
        if not period_str:
            # Default to current month
            today = date.today()
            return (
                date(today.year, today.month, 1),
                today
            )

        # Parse "YYYY-MM" format
        try:
            parts = period_str.split('-')
            if len(parts) >= 2:
                year = int(parts[0])
                month = int(parts[1])

                # First day of month
                period_from = date(year, month, 1)

                # Last day of month
                if month == 12:
                    period_to = date(year, 12, 31)
                else:
                    next_month = date(year, month + 1, 1)
                    period_to = date(next_month.year, next_month.month, 1)
                    # Go back one day
                    from datetime import timedelta
                    period_to = period_to - timedelta(days=1)

                return (period_from, period_to)
        except Exception as e:
            logger.warning(f"Failed to parse period '{period_str}': {e}")

        # Fallback
        today = date.today()
        return (today, today)

    def _parse_magnet_date(self, date_str: str) -> Optional[date]:
        """
        Parse MagNet date format: "2025.09.02."
        """
        if not date_str:
            return None

        try:
            # Remove trailing dot
            clean = date_str.rstrip('.')
            # Parse YYYY.MM.DD
            return datetime.strptime(clean, '%Y.%m.%d').date()
        except ValueError as e:
            logger.warning(f"Failed to parse MagNet date '{date_str}': {e}")
            return None

    def _parse_decimal(self, value_str: str) -> Decimal:
        """Parse decimal value from string."""
        if not value_str:
            return Decimal('0.00')

        try:
            # MagNet uses dot as decimal separator
            return Decimal(value_str.strip())
        except Exception as e:
            logger.warning(f"Failed to parse decimal '{value_str}': {e}")
            return Decimal('0.00')

    def _get_text(self, parent: Optional[ET.Element], tag: str, default: str = '') -> str:
        """Safely get text from XML element."""
        if parent is None:
            return default

        elem = parent.find(tag)
        if elem is None or elem.text is None:
            return default

        return elem.text.strip()
