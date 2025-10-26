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
from typing import Dict, List, Any, Optional, Tuple
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
        # Extract components
        fejlec = self._get_required_element(root, 'FEJLEC')
        kibocsato = fejlec.find('KIBOCSATO')
        doc_info = fejlec.find('DokumentumInfo')

        szamla_info = self._get_required_element(root, 'SzamlaInfo')
        egyenleg_info = self._get_required_element(root, 'EgyenlegInfo')

        # Parse components
        statement_id = self._get_text(doc_info, 'SzamlaID', '')
        period_str = self._get_text(doc_info, 'AlCim', '')
        account_number = self._get_text(szamla_info, 'Szamlaszam', '')
        period_from, period_to = self._parse_period(period_str)

        # Parse balances
        opening_balance, closing_balance = self._extract_balances(egyenleg_info)

        # Build metadata object
        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=account_number,
            account_iban=self._build_iban(account_number),
            period_from=period_from,
            period_to=period_to,
            statement_number=statement_id,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            raw_metadata=self._build_raw_metadata(kibocsato, szamla_info, egyenleg_info)
        )

    def _get_required_element(self, parent: ET.Element, tag: str) -> ET.Element:
        """Get required XML element or raise error."""
        element = parent.find(tag)
        if element is None:
            raise BankStatementParseError(f"Missing {tag} element")
        return element

    def _extract_balances(self, egyenleg_info: ET.Element) -> Tuple[Decimal, Decimal]:
        """Extract opening and closing balances from EgyenlegInfo."""
        opening_elem = egyenleg_info.find('NyitoEgyenleg')
        opening = self._parse_decimal(opening_elem.text if opening_elem is not None else '0')

        closing_elem = egyenleg_info.find('ZaroEgyenleg')
        closing = self._parse_decimal(closing_elem.text if closing_elem is not None else '0')

        return opening, closing

    def _build_raw_metadata(
        self,
        kibocsato: Optional[ET.Element],
        szamla_info: ET.Element,
        egyenleg_info: ET.Element
    ) -> Dict[str, str]:
        """Build raw metadata dictionary from XML elements."""
        return {
            'bank_tax_id': self._get_text(kibocsato, 'AdoigazgatasiSzam', ''),
            'bank_address': self._get_text(kibocsato, 'Cim', ''),
            'account_holder': self._get_text(szamla_info, 'Nev', ''),
            'total_debit': self._get_text(egyenleg_info, 'Terheles', '0'),
            'total_credit': self._get_text(egyenleg_info, 'Jovairas', '0'),
            'debit_count': self._get_text(egyenleg_info, 'TerhelesDB', '0'),
            'credit_count': self._get_text(egyenleg_info, 'JovairasDB', '0'),
        }

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
        # Extract basic transaction data
        basic_data = self._extract_basic_transaction_data(trans)
        if not basic_data:
            return None

        # Build base transaction object
        transaction = self._build_magnet_transaction(basic_data)

        # Add optional elements
        self._add_fees_and_taxes(trans, transaction, basic_data['fee_amount_base'])
        self._parse_supplementary_data(trans, transaction, basic_data['reference'])
        self._set_payer_beneficiary(trans, transaction, basic_data)

        # Store raw XML data
        transaction.raw_data['nbid'] = basic_data['nbid']
        transaction.raw_data['xml_type'] = basic_data['magnet_type']

        return transaction

    def _extract_basic_transaction_data(self, trans: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract basic transaction fields from XML element."""
        trans_num = self._get_text(trans, 'Tranzakcioszam', '')

        # Parse amount
        osszeg_elem = trans.find('Osszeg')
        if osszeg_elem is None:
            logger.warning(f"Transaction {trans_num} missing Osszeg element")
            return None

        # Parse dates
        booking_date_str = self._get_text(trans, 'Terhelesnap', '')
        booking_date = self._parse_magnet_date(booking_date_str)
        if not booking_date:
            logger.warning(f"Transaction {trans_num} missing date")
            return None

        value_date_str = self._get_text(trans, 'Esedekessegnap', '')
        value_date = self._parse_magnet_date(value_date_str) or booking_date

        # Extract fee
        fee_elem = trans.find('Jutalekosszeg')
        fee_amount_base = self._parse_decimal(fee_elem.text if fee_elem is not None else '0')

        return {
            'nbid': trans.get('NBID', ''),
            'trans_num': trans_num,
            'counterparty': self._get_text(trans, 'Ellenpartner', ''),
            'counter_iban': self._get_text(trans, 'Ellenszamla', ''),
            'amount': self._parse_decimal(osszeg_elem.text or '0'),
            'currency': osszeg_elem.get('Devizanem', 'HUF'),
            'reference': self._get_text(trans, 'Kozlemeny', ''),
            'booking_date': booking_date,
            'value_date': value_date,
            'magnet_type': self._get_text(trans, 'Tipus', ''),
            'fee_amount_base': fee_amount_base,
        }

    def _build_magnet_transaction(self, data: Dict[str, Any]) -> NormalizedTransaction:
        """Build base NormalizedTransaction from extracted data."""
        transaction_type = self._map_transaction_type(data['magnet_type'], data['amount'])
        description = self._build_description(
            data['counterparty'],
            data['reference'],
            data['magnet_type']
        )
        short_description = f"{data['magnet_type']}: {data['counterparty']}"

        return NormalizedTransaction(
            transaction_type=transaction_type,
            booking_date=data['booking_date'],
            value_date=data['value_date'],
            amount=data['amount'],
            currency=data['currency'],
            description=description,
            short_description=short_description,
            transaction_id=data['trans_num'],
            reference=data['reference'],
            transaction_type_code=data['magnet_type'],
        )

    def _add_fees_and_taxes(
        self,
        trans: ET.Element,
        transaction: NormalizedTransaction,
        fee_amount_base: Decimal
    ) -> None:
        """Add fee and tax information to transaction."""
        kiegeszito = trans.find('TranzakcioKiegeszito')
        if kiegeszito is None:
            if fee_amount_base != Decimal('0'):
                transaction.fee_amount = abs(fee_amount_base)
            return

        # Check for detailed fee
        jutalek_elem = kiegeszito.find('JutalekKiegeszito')
        if jutalek_elem is not None and jutalek_elem.text:
            detailed_fee = self._parse_decimal(jutalek_elem.text)
            if detailed_fee != Decimal('0'):
                transaction.fee_amount = abs(detailed_fee)
        elif fee_amount_base != Decimal('0'):
            transaction.fee_amount = abs(fee_amount_base)

        # Store transaction tax
        illetek_elem = kiegeszito.find('TranzIlletekKiegeszito')
        if illetek_elem is not None and illetek_elem.text:
            transaction.raw_data['transaction_tax'] = illetek_elem.text

    def _parse_supplementary_data(
        self,
        trans: ET.Element,
        transaction: NormalizedTransaction,
        reference: str
    ) -> None:
        """Parse supplementary transaction data (card details, costs)."""
        kiegeszito = trans.find('TranzakcioKiegeszito')
        if kiegeszito is None:
            return

        # Parse card details
        kartya_elem = kiegeszito.find('KartyaKiegeszito')
        if kartya_elem is not None:
            self._parse_card_details(kartya_elem, transaction, reference)

        # Parse cost breakdown
        koltseg_elem = kiegeszito.find('KoltsegKiegeszito')
        if koltseg_elem is not None:
            costs = []
            for koltseg in koltseg_elem.findall('Koltseg'):
                costs.append({
                    'type': koltseg.get('Koltsegnem', ''),
                    'amount': koltseg.text or '0'
                })
            if costs:
                transaction.raw_data['cost_breakdown'] = costs

    def _set_payer_beneficiary(
        self,
        trans: ET.Element,
        transaction: NormalizedTransaction,
        data: Dict[str, Any]
    ) -> None:
        """Set payer and beneficiary based on amount sign."""
        amount = data['amount']
        counterparty = data['counterparty']
        counter_iban = data['counter_iban']

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

    def _map_transaction_type(self, magnet_type: str, amount: Decimal) -> str:
        """
        Map MagNet transaction types to detailed types with direction.

        Uses amount sign to determine direction:
        - Positive amount = CREDIT (incoming)
        - Negative amount = DEBIT (outgoing)

        Returns detailed types matching GRANIT format:
        - AFR_CREDIT / AFR_DEBIT
        - TRANSFER_CREDIT / TRANSFER_DEBIT
        - POS_PURCHASE
        - BANK_FEE
        - OTHER
        """
        magnet_lower = magnet_type.lower()
        is_credit = amount > 0

        # Card transactions (always purchase/debit for MagNet)
        if 'bankkártya' in magnet_lower:
            return 'POS_PURCHASE'

        # AFR transfers (check explicitly for AFR in type name)
        if 'afr' in magnet_lower:
            return 'AFR_CREDIT' if is_credit else 'AFR_DEBIT'

        # Regular transfers
        if 'átutalás' in magnet_lower:
            return 'TRANSFER_CREDIT' if is_credit else 'TRANSFER_DEBIT'

        # Fees (always debit)
        if 'költség' in magnet_lower or 'díj' in magnet_lower:
            return 'BANK_FEE'

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
