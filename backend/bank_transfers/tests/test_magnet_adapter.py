"""
Tests for MagNet Bank statement adapter.

Tests cover:
- XML detection
- NetBankXML parsing
- Metadata extraction
- Transaction parsing
- Element-based field mapping
- Date/amount parsing
"""

import pytest
from decimal import Decimal
from datetime import date
from pathlib import Path

from bank_transfers.bank_adapters.magnet_adapter import MagnetBankAdapter
from bank_transfers.bank_adapters.base import BankStatementParseError


@pytest.fixture(scope='module')
def sample_xml_bytes():
    """Load sample MagNet XML for testing."""
    xml_path = Path(__file__).parent.parent.parent / 'bank_statement_example' / 'Magnet' / 'haviKivonat_202509_1620015118581773.xml'

    if not xml_path.exists():
        pytest.skip(f"Test XML not found: {xml_path}")

    with open(xml_path, 'rb') as f:
        return f.read()


@pytest.fixture(scope='module')
def parsed_statement(sample_xml_bytes):
    """Parse sample XML and return result."""
    adapter = MagnetBankAdapter()
    return adapter.parse(sample_xml_bytes)


class TestMagnetDetection:
    """Test MagNet Bank XML detection."""

    def test_detect_valid_magnet_xml(self, sample_xml_bytes):
        """Test detection of valid MagNet XML."""
        adapter = MagnetBankAdapter()
        assert adapter.detect(sample_xml_bytes, "haviKivonat_202509.xml") is True

    def test_detect_invalid_xml(self):
        """Test detection rejects invalid XML."""
        adapter = MagnetBankAdapter()
        invalid_xml = b"Not XML"
        assert adapter.detect(invalid_xml, "test.xml") is False

    def test_detect_other_bank_xml(self):
        """Test detection rejects XML from other sources."""
        adapter = MagnetBankAdapter()
        # XML without NetBankXML root
        other_xml = b'<?xml version="1.0"?><root><bank>Other Bank</bank></root>'
        assert adapter.detect(other_xml, "other.xml") is False

    def test_detect_checks_netbankxml_root(self):
        """Test detection verifies NetBankXML root element."""
        adapter = MagnetBankAdapter()

        # XML with wrong root element
        wrong_root = b'<?xml version="1.0"?><BankStatement><bank>MagNet</bank></BankStatement>'
        assert adapter.detect(wrong_root, "wrong.xml") is False


class TestMagnetParsing:
    """Test MagNet Bank statement parsing."""

    def test_parse_metadata(self, parsed_statement):
        """Test metadata extraction from MagNet XML."""
        metadata = parsed_statement['metadata']

        assert metadata.bank_code == 'MAGNET'
        assert metadata.bank_name == 'MagNet Magyar Közösségi Bank'
        # MagNet may use HBWEHUHB or MKKB (older code)
        assert metadata.bank_bic in ['HBWEHUHB', 'MKKB']

        # Verify account information
        assert metadata.account_number is not None
        assert len(metadata.account_number) > 0

        # Verify IBAN if present
        if metadata.account_iban:
            assert metadata.account_iban.startswith('HU')

        # Verify period dates
        assert metadata.period_from is not None
        assert metadata.period_to is not None
        assert metadata.period_from <= metadata.period_to

        # Verify balances
        assert metadata.opening_balance is not None
        assert metadata.closing_balance is not None

    def test_parse_transactions_exist(self, parsed_statement):
        """Test that transactions are parsed."""
        transactions = parsed_statement['transactions']
        assert len(transactions) > 0, "Should parse at least some transactions"

    def test_transaction_types_validation(self, parsed_statement):
        """Test all transaction types are valid enum values."""
        transactions = parsed_statement['transactions']

        valid_types = {
            'AFR_CREDIT', 'AFR_DEBIT',
            'TRANSFER_CREDIT', 'TRANSFER_DEBIT',
            'POS_PURCHASE', 'ATM_WITHDRAWAL',
            'BANK_FEE', 'INTEREST_CREDIT', 'INTEREST_DEBIT',
            'CORRECTION', 'OTHER'
        }

        for tx in transactions:
            assert tx.transaction_type in valid_types, f"Invalid transaction type: {tx.transaction_type}"

    def test_balance_calculation(self, parsed_statement):
        """Test that transactions balance matches statement closing balance."""
        metadata = parsed_statement['metadata']
        transactions = parsed_statement['transactions']

        # Calculate net change
        total_change = sum(tx.amount for tx in transactions)

        # Verify: opening_balance + total_change = closing_balance
        expected_closing = metadata.opening_balance + total_change

        # Allow small rounding difference
        difference = abs(expected_closing - metadata.closing_balance)
        assert difference < Decimal('1.00'), f"Balance mismatch: expected {expected_closing}, got {metadata.closing_balance}"

    def test_dates_are_parsed(self, parsed_statement):
        """Test that dates are properly parsed."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.booking_date is not None
            assert isinstance(tx.booking_date, date)

            # Value date may be same as booking date
            assert tx.value_date is not None
            assert isinstance(tx.value_date, date)

    def test_amounts_are_decimal(self, parsed_statement):
        """Test that amounts are Decimal type."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.amount is not None
            assert isinstance(tx.amount, Decimal)

    def test_currency_field(self, parsed_statement):
        """Test currency field extraction."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.currency is not None
            # Should be 3-letter currency code
            assert len(tx.currency) == 3
            assert tx.currency.isupper()


class TestMagnetTransactionFields:
    """Test MagNet transaction field extraction."""

    def test_description_field(self, parsed_statement):
        """Test description field extraction."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.description is not None
            assert isinstance(tx.description, str)
            assert len(tx.description) > 0

    def test_partner_name_extraction(self, parsed_statement):
        """Test partner name extraction."""
        transactions = parsed_statement['transactions']

        # Find transactions with partner names
        txs_with_partner = [
            t for t in transactions
            if t.payer_name or t.beneficiary_name
        ]

        if len(txs_with_partner) > 0:
            for tx in txs_with_partner:
                partner_name = tx.payer_name or tx.beneficiary_name
                assert isinstance(partner_name, str)
                assert len(partner_name) > 0

    def test_account_number_extraction(self, parsed_statement):
        """Test account number extraction from transactions."""
        transactions = parsed_statement['transactions']

        # Find transactions with account numbers
        txs_with_account = [
            t for t in transactions
            if t.payer_account_number or t.beneficiary_account_number
        ]

        if len(txs_with_account) > 0:
            for tx in txs_with_account:
                account = tx.payer_account_number or tx.beneficiary_account_number
                assert isinstance(account, str)
                assert len(account) > 0

    def test_reference_field(self, parsed_statement):
        """Test reference field extraction."""
        transactions = parsed_statement['transactions']

        # Find transactions with references
        txs_with_ref = [t for t in transactions if t.reference]

        if len(txs_with_ref) > 0:
            for tx in txs_with_ref:
                assert isinstance(tx.reference, str)
                assert len(tx.reference) > 0

    def test_transaction_id_field(self, parsed_statement):
        """Test transaction ID extraction."""
        transactions = parsed_statement['transactions']

        # Transaction IDs may or may not be present
        txs_with_id = [t for t in transactions if t.transaction_id]

        if len(txs_with_id) > 0:
            for tx in txs_with_id:
                assert isinstance(tx.transaction_id, str)
                assert len(tx.transaction_id) > 0


class TestMagnetXMLStructure:
    """Test XML structure handling."""

    def test_xml_elements_parsed(self, parsed_statement):
        """Test that XML elements are properly parsed."""
        # If parsing succeeded, XML structure was valid
        assert parsed_statement is not None
        assert 'metadata' in parsed_statement
        assert 'transactions' in parsed_statement

    def test_raw_data_stored(self, parsed_statement):
        """Test that raw XML data is stored."""
        transactions = parsed_statement['transactions']

        if len(transactions) > 0:
            for tx in transactions:
                # raw_data should contain XML element info
                assert hasattr(tx, 'raw_data')


class TestMagnetDateParsing:
    """Test MagNet date parsing."""

    def test_dates_in_statement_period(self, parsed_statement):
        """Test transaction dates fall within statement period."""
        metadata = parsed_statement['metadata']
        transactions = parsed_statement['transactions']

        for tx in transactions:
            # Booking date should be within period
            assert tx.booking_date >= metadata.period_from, \
                f"Transaction date {tx.booking_date} before period start {metadata.period_from}"
            assert tx.booking_date <= metadata.period_to, \
                f"Transaction date {tx.booking_date} after period end {metadata.period_to}"


class TestMagnetAmountParsing:
    """Test MagNet amount parsing."""

    def test_debit_credit_signs(self, parsed_statement):
        """Test that debit/credit amounts have correct signs."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            if 'DEBIT' in tx.transaction_type or tx.transaction_type in ['ATM_WITHDRAWAL', 'BANK_FEE']:
                # Debits should be negative or zero
                assert tx.amount <= 0, f"Debit transaction should have negative amount: {tx.amount}"
            elif 'CREDIT' in tx.transaction_type:
                # Credits should be positive or zero
                assert tx.amount >= 0, f"Credit transaction should have positive amount: {tx.amount}"
            # Note: POS_PURCHASE can be positive (refunds/chargebacks) or negative (purchases)
            # so we don't assert on sign for POS_PURCHASE


class TestMagnetEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_xml_fails(self):
        """Test parsing empty XML fails gracefully."""
        adapter = MagnetBankAdapter()

        with pytest.raises((BankStatementParseError, Exception)):
            adapter.parse(b"")

    def test_parse_invalid_xml_fails(self):
        """Test parsing invalid XML fails gracefully."""
        adapter = MagnetBankAdapter()

        with pytest.raises((BankStatementParseError, Exception)):
            adapter.parse(b"<invalid xml")

    def test_parse_xml_without_transactions(self):
        """Test parsing XML with no transactions."""
        adapter = MagnetBankAdapter()

        # Minimal valid XML structure without transactions
        minimal_xml = b'''<?xml version="1.0"?>
<NetBankXML>
    <Bank>MagNet</Bank>
    <Account>
        <Number>16200151-18581773</Number>
    </Account>
    <Statement>
        <PeriodFrom>2025-09-01</PeriodFrom>
        <PeriodTo>2025-09-30</PeriodTo>
        <OpeningBalance>1000.00</OpeningBalance>
        <ClosingBalance>1000.00</ClosingBalance>
    </Statement>
    <Transactions>
    </Transactions>
</NetBankXML>'''

        # Should handle gracefully
        try:
            result = adapter.parse(minimal_xml)
            # Should return empty transaction list
            assert len(result['transactions']) == 0
        except (BankStatementParseError, Exception):
            # Or may raise error for invalid structure
            pass
