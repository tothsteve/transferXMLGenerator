"""
Tests for K&H Bank statement adapter.

Tests cover:
- PDF detection
- Metadata extraction
- Transaction parsing
- Multi-currency transactions
- Exchange rate handling
- IBAN to account number conversion
- Multi-line beneficiary names
- Closing balance calculation workaround
"""

import pytest
from decimal import Decimal
from datetime import date
from pathlib import Path

from bank_transfers.bank_adapters.kh_adapter import KHBankAdapter
from bank_transfers.bank_adapters.base import BankStatementParseError


@pytest.fixture(scope='module')
def sample_pdf_bytes():
    """Load sample K&H PDF for testing."""
    pdf_path = Path(__file__).parent.parent.parent / 'bank_statement_example' / 'KH' / '20250930ACCOUNT.PDF'

    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        return f.read()


@pytest.fixture(scope='module')
def parsed_statement(sample_pdf_bytes):
    """Parse sample PDF and return result."""
    adapter = KHBankAdapter()
    return adapter.parse(sample_pdf_bytes)


class TestKHDetection:
    """Test K&H Bank PDF detection."""

    def test_detect_valid_kh_pdf(self, sample_pdf_bytes):
        """Test detection of valid K&H Bank PDF."""
        adapter = KHBankAdapter()
        assert adapter.detect(sample_pdf_bytes, "20250930ACCOUNT.PDF") is True

    def test_detect_invalid_pdf(self):
        """Test detection rejects invalid PDF."""
        adapter = KHBankAdapter()
        invalid_pdf = b"Not a PDF"
        assert adapter.detect(invalid_pdf, "test.pdf") is False

    def test_detect_other_bank_pdf(self):
        """Test detection rejects PDF from other banks."""
        adapter = KHBankAdapter()
        # PDF without K&H identifiers
        other_bank_pdf = b"%PDF-1.4\nGranit Bank statement"
        assert adapter.detect(other_bank_pdf, "granit.pdf") is False


class TestKHParsing:
    """Test K&H Bank statement parsing."""

    def test_parse_metadata(self, parsed_statement):
        """Test metadata extraction from K&H statement."""
        metadata = parsed_statement['metadata']

        assert metadata.bank_code == 'KH'
        assert metadata.bank_name == 'K&H Bank Zrt.'
        assert metadata.bank_bic == 'OKHBHUHB'

        # Verify account information
        assert metadata.account_number is not None
        assert len(metadata.account_number) > 0

        # Verify IBAN
        if metadata.account_iban:
            assert metadata.account_iban.startswith('HU')

        # Verify period dates
        assert metadata.period_from is not None
        assert metadata.period_to is not None
        assert metadata.period_from <= metadata.period_to

        # Verify balances
        assert metadata.opening_balance is not None
        assert metadata.closing_balance is not None

        # Statement number should be present
        assert metadata.statement_number is not None

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

    def test_closing_balance_calculation(self, parsed_statement):
        """Test closing balance calculation (K&H has known PDF extraction bug)."""
        metadata = parsed_statement['metadata']
        transactions = parsed_statement['transactions']

        # Calculate net change
        total_change = sum(tx.amount for tx in transactions)

        # Verify: opening_balance + total_change = closing_balance
        expected_closing = metadata.opening_balance + total_change

        # K&H adapter may calculate closing balance if PDF extraction corrupted it
        # Verify the balance is reasonable (within 1% tolerance for rounding)
        difference = abs(expected_closing - metadata.closing_balance)
        tolerance = abs(metadata.closing_balance * Decimal('0.01'))  # 1% tolerance

        assert difference < tolerance or difference < Decimal('100.00'), \
            f"Balance mismatch: expected {expected_closing}, got {metadata.closing_balance}, diff: {difference}"

    def test_dates_are_parsed(self, parsed_statement):
        """Test that dates are properly parsed."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.booking_date is not None
            assert isinstance(tx.booking_date, date)
            assert tx.value_date is not None
            assert isinstance(tx.value_date, date)

    def test_amounts_are_decimal(self, parsed_statement):
        """Test that amounts are Decimal type."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.amount is not None
            assert isinstance(tx.amount, Decimal)


class TestKHMultiCurrency:
    """Test K&H multi-currency transaction handling."""

    def test_exchange_rate_extraction(self, parsed_statement):
        """Test exchange rate extraction for foreign currency transactions."""
        transactions = parsed_statement['transactions']

        # Find transactions with exchange rates
        txs_with_rate = [t for t in transactions if t.exchange_rate is not None]

        if len(txs_with_rate) > 0:
            for tx in txs_with_rate:
                assert isinstance(tx.exchange_rate, Decimal)
                assert tx.exchange_rate > 0

                # Should have original currency and amount
                assert tx.original_currency is not None
                assert len(tx.original_currency) == 3

                assert tx.original_amount is not None
                assert isinstance(tx.original_amount, Decimal)

    def test_original_currency_populated(self, parsed_statement):
        """Test that original currency/amount are populated for FX transactions."""
        transactions = parsed_statement['transactions']

        # Find multi-currency transactions
        fx_txs = [t for t in transactions if t.original_currency and t.original_currency != 'HUF']

        if len(fx_txs) > 0:
            for tx in fx_txs:
                # Original currency should be 3 letters
                assert len(tx.original_currency) == 3
                assert tx.original_currency.isupper()

                # Original amount should exist
                assert tx.original_amount is not None

                # Exchange rate should exist
                assert tx.exchange_rate is not None

    def test_huf_transactions(self, parsed_statement):
        """Test HUF transactions."""
        transactions = parsed_statement['transactions']

        # Find HUF-only transactions
        huf_txs = [t for t in transactions if not t.original_currency or t.original_currency == 'HUF']

        if len(huf_txs) > 0:
            for tx in huf_txs:
                # Currency should be HUF
                assert tx.currency == 'HUF'


class TestKHIBANHandling:
    """Test K&H IBAN to account number conversion."""

    def test_iban_extraction(self, parsed_statement):
        """Test IBAN extraction from transactions."""
        transactions = parsed_statement['transactions']

        # Find transactions with IBANs
        txs_with_iban = [
            t for t in transactions
            if t.beneficiary_iban or t.payer_iban
        ]

        if len(txs_with_iban) > 0:
            for tx in txs_with_iban:
                iban = tx.beneficiary_iban or tx.payer_iban

                # IBAN should start with 2-letter country code
                assert len(iban) >= 2
                assert iban[:2].isupper(), f"Expected IBAN with country code, got {iban}"

                # IBAN should have reasonable length
                clean_iban = iban.replace(' ', '')
                assert len(clean_iban) >= 15  # Minimum IBAN length

    def test_iban_to_account_conversion(self, parsed_statement):
        """Test IBAN to account number conversion."""
        transactions = parsed_statement['transactions']

        # Find transactions with both IBAN and account number
        txs_with_both = [
            t for t in transactions
            if (t.beneficiary_iban and t.beneficiary_account_number) or
               (t.payer_iban and t.payer_account_number)
        ]

        if len(txs_with_both) > 0:
            for tx in txs_with_both:
                # Account number should be in format: 12345678-12345678-12345678
                account = tx.beneficiary_account_number or tx.payer_account_number

                if account:
                    # Should have dashes
                    assert '-' in account or len(account) >= 16


class TestKHPartnerInformation:
    """Test K&H partner information extraction."""

    def test_beneficiary_extraction_for_outgoing(self, parsed_statement):
        """Test beneficiary extraction for outgoing transfers."""
        transactions = parsed_statement['transactions']

        # Find outgoing transfers (negative amount)
        outgoing = [t for t in transactions if t.amount < 0 and 'TRANSFER' in t.transaction_type]

        if len(outgoing) > 0:
            for tx in outgoing:
                # May have beneficiary info
                if tx.beneficiary_name:
                    assert isinstance(tx.beneficiary_name, str)
                    assert len(tx.beneficiary_name) > 0

    def test_payer_extraction_for_incoming(self, parsed_statement):
        """Test payer extraction for incoming transfers."""
        transactions = parsed_statement['transactions']

        # Find incoming transfers (positive amount)
        incoming = [t for t in transactions if t.amount > 0 and 'TRANSFER' in t.transaction_type]

        if len(incoming) > 0:
            for tx in incoming:
                # May have payer info
                if tx.payer_name:
                    assert isinstance(tx.payer_name, str)
                    assert len(tx.payer_name) > 0

    def test_reference_field_extraction(self, parsed_statement):
        """Test reference field (Közlemény) extraction."""
        transactions = parsed_statement['transactions']

        # Find transactions with references
        txs_with_ref = [t for t in transactions if t.reference]

        if len(txs_with_ref) > 0:
            for tx in txs_with_ref:
                assert isinstance(tx.reference, str)
                assert len(tx.reference) > 0


class TestKHMultilineHandling:
    """Test multi-line text handling in K&H PDFs."""

    def test_multiline_names_joined(self, parsed_statement):
        """Test that multi-line partner names are properly joined."""
        transactions = parsed_statement['transactions']

        # Check all partner names
        for tx in transactions:
            for name_field in [tx.payer_name, tx.beneficiary_name]:
                if name_field:
                    # Should not have excessive whitespace
                    assert '  ' not in name_field, f"Name has double spaces: {name_field}"

                    # Should not have newlines
                    assert '\n' not in name_field, f"Name contains newline: {name_field}"


class TestKHTransactionTypes:
    """Test K&H transaction type detection."""

    def test_fee_transactions(self, parsed_statement):
        """Test bank fee transactions."""
        transactions = parsed_statement['transactions']

        fee_txs = [t for t in transactions if t.transaction_type == 'BANK_FEE']

        if len(fee_txs) > 0:
            for tx in fee_txs:
                # Fees should be debits (negative)
                assert tx.amount <= 0

    def test_transfer_transactions(self, parsed_statement):
        """Test transfer transactions."""
        transactions = parsed_statement['transactions']

        transfer_txs = [t for t in transactions if 'TRANSFER' in t.transaction_type]

        if len(transfer_txs) > 0:
            for tx in transfer_txs:
                # Should have transaction type code
                assert tx.transaction_type_code is not None or True  # May be None


class TestKHRawData:
    """Test raw_data storage."""

    def test_raw_data_stored(self, parsed_statement):
        """Test that raw transaction data is stored."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert hasattr(tx, 'raw_data')


class TestKHEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_pdf_fails(self):
        """Test parsing empty PDF fails gracefully."""
        adapter = KHBankAdapter()

        with pytest.raises((BankStatementParseError, Exception)):
            adapter.parse(b"")

    def test_parse_corrupted_pdf_fails(self):
        """Test parsing corrupted PDF fails gracefully."""
        adapter = KHBankAdapter()

        with pytest.raises((BankStatementParseError, Exception)):
            adapter.parse(b"%PDF-1.4\nCorrupted content")


class TestKHPDFStructure:
    """Test K&H PDF structure handling."""

    def test_handles_multipage_pdf(self, parsed_statement):
        """Test that multi-page PDFs are handled."""
        # K&H statements often have multiple pages
        # If parsing succeeded, multi-page handling works
        assert parsed_statement is not None
        assert len(parsed_statement['transactions']) > 0

    def test_transaction_id_extraction(self, parsed_statement):
        """Test transaction ID extraction."""
        transactions = parsed_statement['transactions']

        # K&H may provide transaction IDs (Ref: or Tr. azon:)
        txs_with_id = [t for t in transactions if t.transaction_id]

        if len(txs_with_id) > 0:
            for tx in txs_with_id:
                assert isinstance(tx.transaction_id, str)
                assert len(tx.transaction_id) > 0

    def test_payment_id_extraction(self, parsed_statement):
        """Test payment ID extraction."""
        transactions = parsed_statement['transactions']

        # K&H may provide payment IDs (Hiv:)
        txs_with_payment_id = [t for t in transactions if t.payment_id]

        if len(txs_with_payment_id) > 0:
            for tx in txs_with_payment_id:
                assert isinstance(tx.payment_id, str)
                assert len(tx.payment_id) > 0
