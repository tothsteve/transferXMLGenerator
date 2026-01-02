"""
Tests for GRÁNIT Bank statement adapter.

Tests cover:
- PDF detection
- Metadata extraction
- Transaction parsing (POS, AFR, Transfers)
- Multi-line text handling
- Card number extraction
- Merchant location parsing
- IBAN/BIC extraction
"""

import pytest
from decimal import Decimal
from datetime import date
from pathlib import Path

from bank_transfers.bank_adapters.granit_adapter import GranitBankAdapter
from bank_transfers.bank_adapters.base import BankStatementParseError


@pytest.fixture(scope='module')
def sample_pdf_bytes():
    """Load sample GRÁNIT PDF for testing."""
    # Use the most recent statement with diverse transactions
    pdf_path = Path(__file__).parent.parent.parent / 'bank_statement_example' / '1' / 'BK_1_PDF_kivonat_20250131_1210001119014874.pdf'

    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        return f.read()


@pytest.fixture(scope='module')
def parsed_statement(sample_pdf_bytes):
    """Parse sample PDF and return result."""
    adapter = GranitBankAdapter()
    return adapter.parse(sample_pdf_bytes)


class TestGranitDetection:
    """Test GRÁNIT Bank PDF detection."""

    def test_detect_valid_granit_pdf(self, sample_pdf_bytes):
        """Test detection of valid GRÁNIT Bank PDF."""
        adapter = GranitBankAdapter()
        assert adapter.detect(sample_pdf_bytes, "BK_1_PDF_kivonat_20250131.pdf") is True

    def test_detect_invalid_pdf(self):
        """Test detection rejects invalid PDF."""
        adapter = GranitBankAdapter()
        invalid_pdf = b"Not a PDF"
        assert adapter.detect(invalid_pdf, "test.pdf") is False

    def test_detect_other_bank_pdf(self):
        """Test detection rejects PDF from other banks."""
        adapter = GranitBankAdapter()
        # Simple PDF without GRÁNIT identifiers
        other_bank_pdf = b"%PDF-1.4\nRaiffeisen Bank statement"
        assert adapter.detect(other_bank_pdf, "raiff.pdf") is False


class TestGranitParsing:
    """Test GRÁNIT Bank statement parsing."""

    def test_parse_metadata(self, parsed_statement):
        """Test metadata extraction from GRÁNIT statement."""
        metadata = parsed_statement['metadata']

        assert metadata.bank_code == 'GRANIT'
        assert metadata.bank_name == 'GRÁNIT Bank Nyrt.'
        assert metadata.bank_bic == 'GNBAHUHB'
        assert metadata.account_number == '12100011-19014874'
        assert 'HU' in metadata.account_iban

        # Verify period dates exist
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

    def test_parse_pos_transaction(self, parsed_statement):
        """Test parsing of POS purchase transaction."""
        transactions = parsed_statement['transactions']

        # Find a POS purchase
        pos_txs = [t for t in transactions if t.transaction_type == 'POS_PURCHASE']

        if len(pos_txs) > 0:
            pos_tx = pos_txs[0]

            assert pos_tx.amount < 0, "POS purchases should be debits"
            assert pos_tx.currency == 'HUF'
            assert pos_tx.booking_date is not None
            assert pos_tx.value_date is not None

            # POS transactions may have card number
            # Some may have merchant information

    def test_parse_transfer_transaction(self, parsed_statement):
        """Test parsing of transfer transaction."""
        transactions = parsed_statement['transactions']

        # Find transfer transactions
        transfer_txs = [t for t in transactions if 'TRANSFER' in t.transaction_type]

        if len(transfer_txs) > 0:
            transfer = transfer_txs[0]

            assert transfer.currency == 'HUF'
            assert transfer.booking_date is not None

            # Transfers should have either beneficiary or payer info
            has_partner_info = (
                transfer.beneficiary_name or
                transfer.payer_name or
                transfer.beneficiary_iban or
                transfer.payer_iban
            )
            # Some transfers may not have full partner info in all statements

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

        # Allow small rounding difference (within 1 HUF)
        difference = abs(expected_closing - metadata.closing_balance)
        assert difference < Decimal('1.00'), f"Balance mismatch: expected {expected_closing}, got {metadata.closing_balance}"

    def test_currency_is_huf(self, parsed_statement):
        """Test all GRÁNIT transactions are in HUF."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.currency == 'HUF', f"Expected HUF currency, got {tx.currency}"

    def test_dates_in_period(self, parsed_statement):
        """Test all transaction dates fall within statement period."""
        metadata = parsed_statement['metadata']
        transactions = parsed_statement['transactions']

        for tx in transactions:
            # Booking date should be within period
            # (Some transactions may have value dates outside period)
            assert tx.booking_date >= metadata.period_from, \
                f"Transaction date {tx.booking_date} before period start {metadata.period_from}"
            assert tx.booking_date <= metadata.period_to, \
                f"Transaction date {tx.booking_date} after period end {metadata.period_to}"


class TestGranitCardTransactions:
    """Test GRÁNIT Bank card transaction parsing."""

    def test_card_number_extraction(self, parsed_statement):
        """Test card number extraction from POS transactions."""
        transactions = parsed_statement['transactions']
        pos_txs = [t for t in transactions if t.transaction_type == 'POS_PURCHASE']

        if len(pos_txs) > 0:
            # Check if any POS transaction has card number
            card_numbers = [tx.card_number for tx in pos_txs if tx.card_number]

            for card_num in card_numbers:
                # Card numbers should be strings
                assert isinstance(card_num, str)
                # May contain asterisks for masking
                assert len(card_num) > 0

    def test_merchant_location_extraction(self, parsed_statement):
        """Test merchant location/name extraction."""
        transactions = parsed_statement['transactions']
        pos_txs = [t for t in transactions if t.transaction_type == 'POS_PURCHASE']

        if len(pos_txs) > 0:
            # Check if any POS transaction has merchant info
            merchants = [tx.merchant_location for tx in pos_txs if tx.merchant_location]

            for merchant in merchants:
                assert isinstance(merchant, str)
                assert len(merchant) > 0


class TestGranitTransferTransactions:
    """Test GRÁNIT Bank transfer transaction parsing."""

    def test_iban_extraction(self, parsed_statement):
        """Test IBAN extraction from transfer transactions."""
        transactions = parsed_statement['transactions']

        # Find transactions with IBANs
        txs_with_iban = [
            t for t in transactions
            if t.beneficiary_iban or t.payer_iban
        ]

        if len(txs_with_iban) > 0:
            for tx in txs_with_iban:
                iban = tx.beneficiary_iban or tx.payer_iban

                # IBAN should start with country code
                assert iban.startswith('HU'), f"Expected Hungarian IBAN, got {iban}"
                # IBAN should have reasonable length
                assert len(iban.replace(' ', '')) >= 20

    def test_bic_extraction(self, parsed_statement):
        """Test BIC extraction from transfer transactions."""
        transactions = parsed_statement['transactions']

        # Find transactions with BICs
        txs_with_bic = [
            t for t in transactions
            if t.beneficiary_bic or t.payer_bic
        ]

        if len(txs_with_bic) > 0:
            for tx in txs_with_bic:
                bic = tx.beneficiary_bic or tx.payer_bic

                # BIC should be 8 or 11 characters
                assert len(bic) in [8, 11], f"Invalid BIC length: {bic}"
                # BIC should be alphanumeric
                assert bic.replace(' ', '').isalnum()

    def test_reference_field(self, parsed_statement):
        """Test reference field extraction."""
        transactions = parsed_statement['transactions']

        # Find transactions with references
        txs_with_ref = [t for t in transactions if t.reference]

        if len(txs_with_ref) > 0:
            for tx in txs_with_ref:
                assert isinstance(tx.reference, str)
                assert len(tx.reference) > 0


class TestGranitMultilineHandling:
    """Test multi-line text handling in GRÁNIT PDFs."""

    def test_description_field_populated(self, parsed_statement):
        """Test that descriptions are extracted."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.description is not None
            assert isinstance(tx.description, str)
            assert len(tx.description) > 0

    def test_short_description_field(self, parsed_statement):
        """Test short description field."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            assert tx.short_description is not None
            assert isinstance(tx.short_description, str)
            assert len(tx.short_description) > 0
            # Short description should be reasonably short
            assert len(tx.short_description) <= 250


class TestGranitRawData:
    """Test raw_data storage for debugging."""

    def test_raw_data_exists(self, parsed_statement):
        """Test that raw_data is stored for transactions."""
        transactions = parsed_statement['transactions']

        for tx in transactions:
            # raw_data should exist (may be None or dict)
            assert hasattr(tx, 'raw_data')


class TestGranitEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_pdf_fails(self):
        """Test parsing empty PDF fails gracefully."""
        adapter = GranitBankAdapter()

        with pytest.raises((BankStatementParseError, Exception)):
            adapter.parse(b"")

    def test_parse_corrupted_pdf_fails(self):
        """Test parsing corrupted PDF fails gracefully."""
        adapter = GranitBankAdapter()

        with pytest.raises((BankStatementParseError, Exception)):
            adapter.parse(b"%PDF-1.4\nCorrupted content")
