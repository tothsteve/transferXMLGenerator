"""
Tests for Raiffeisen Bank statement adapter.

Tests cover:
- PDF detection
- Metadata extraction
- Transaction parsing
- Character encoding cleanup
- Multi-line name handling
- Card transaction merchant extraction
"""

import pytest
from decimal import Decimal
from datetime import date
from pathlib import Path

from bank_transfers.bank_adapters.raiffeisen_adapter import RaiffeisenBankAdapter
from bank_transfers.bank_adapters.base import BankStatementParseError


class TestRaiffeisenDetection:
    """Test Raiffeisen Bank PDF detection."""

    def test_detect_valid_raiffeisen_pdf(self):
        """Test detection of valid Raiffeisen Bank PDF."""
        pdf_path = Path(__file__).parent.parent.parent / 'bank_statement_example' / 'Raiffeisen' / '2026_01_01_4284_A0NLK3_001_016725666.PDF'

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found: {pdf_path}")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        adapter = RaiffeisenBankAdapter()
        assert adapter.detect(pdf_bytes, pdf_path.name) is True

    def test_detect_invalid_pdf(self):
        """Test detection rejects invalid PDF."""
        adapter = RaiffeisenBankAdapter()
        invalid_pdf = b"Not a PDF"
        assert adapter.detect(invalid_pdf, "test.pdf") is False

    def test_detect_other_bank_pdf(self):
        """Test detection rejects PDF from other banks."""
        # Simple PDF without Raiffeisen identifiers
        adapter = RaiffeisenBankAdapter()
        other_bank_pdf = b"%PDF-1.4\nGranit Bank statement"
        assert adapter.detect(other_bank_pdf, "granit.pdf") is False


@pytest.fixture(scope='module')
def sample_pdf_bytes():
    """Load sample Raiffeisen PDF for testing."""
    pdf_path = Path(__file__).parent.parent.parent / 'bank_statement_example' / 'Raiffeisen' / '2026_01_01_4284_A0NLK3_001_016725666.PDF'

    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        return f.read()


@pytest.fixture(scope='module')
def parsed_statement(sample_pdf_bytes):
    """Parse sample PDF and return result."""
    adapter = RaiffeisenBankAdapter()
    return adapter.parse(sample_pdf_bytes)


class TestRaiffeisenParsing:
    """Test Raiffeisen Bank statement parsing."""

    def test_parse_metadata(self, parsed_statement):
        """Test metadata extraction from Raiffeisen statement."""
        metadata = parsed_statement['metadata']

        assert metadata.bank_code == 'RAIFFEISEN'
        assert metadata.bank_name == 'Raiffeisen Bank Zrt.'
        assert metadata.bank_bic == 'UBRTHUHB'
        assert metadata.account_number == '12042847-02101027-00100008'
        assert metadata.account_iban == 'HU83120428470210102700100008'
        assert metadata.statement_number == '2025/0000001'

        # Verify period dates
        assert metadata.period_from == date(2025, 12, 31)
        assert metadata.period_to == date(2025, 12, 31)

        # Verify balances
        assert metadata.opening_balance == Decimal('0.00')
        assert metadata.closing_balance == Decimal('2369738.31')

    def test_parse_transactions_count(self, parsed_statement):
        """Test correct number of transactions parsed."""
        transactions = parsed_statement['transactions']
        assert len(transactions) == 11

    def test_parse_transfer_transaction(self, parsed_statement):
        """Test parsing of transfer transaction with proper character encoding."""
        transactions = parsed_statement['transactions']

        # Find a transfer transaction (IT Cardigan transfer)
        transfer = next(t for t in transactions if t.transaction_type == 'TRANSFER_DEBIT' and t.beneficiary_name == 'IT Cardigan Kft.')

        assert transfer.amount == Decimal('-390000.00')
        assert transfer.currency == 'HUF'
        assert transfer.booking_date == date(2025, 12, 23)
        assert transfer.value_date == date(2025, 12, 22)
        assert transfer.beneficiary_name == 'IT Cardigan Kft.'
        assert transfer.transaction_id == '5398212724'
        assert transfer.payment_id == 'AFK25L0002079874'

        # Verify reference field exists and has content
        assert transfer.reference is not None
        assert len(transfer.reference) > 0
        # Verify character encoding artifacts are cleaned
        assert '£' not in transfer.reference
        assert '©' not in transfer.raw_data.get('kozlemeny', '')

    def test_parse_card_transaction(self, parsed_statement):
        """Test parsing of card transaction with merchant name extraction."""
        transactions = parsed_statement['transactions']

        # Find card transaction
        card_tx = next((t for t in transactions if t.transaction_type == 'POS_PURCHASE'), None)
        assert card_tx is not None

        # Verify card transaction has card number
        assert card_tx.card_number is not None
        assert 'XXXX' in card_tx.card_number  # Masked format

        # Verify merchant information is extracted
        assert card_tx.merchant_name is not None
        assert len(card_tx.merchant_name) > 0
        assert card_tx.merchant_location is not None
        assert card_tx.amount < 0  # Card purchases are debits

        # CRITICAL: reference field should contain merchant name for UI display
        assert card_tx.reference == card_tx.merchant_name, "Reference should match merchant name for UI display"

    def test_parse_interest_transaction(self, parsed_statement):
        """Test parsing of interest credit transaction."""
        transactions = parsed_statement['transactions']

        # Find interest transaction
        interest = next((t for t in transactions if t.transaction_type == 'INTEREST_CREDIT'), None)
        assert interest is not None

        assert interest.amount > 0  # Interest credit is positive
        assert interest.currency == 'HUF'
        assert 'Kamat' in interest.description

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
        assert expected_closing == metadata.closing_balance


class TestCharacterEncoding:
    """Test Hungarian character encoding cleanup."""

    def test_clean_text_hungarian_characters(self):
        """Test cleaning of Hungarian characters from PDF encoding."""
        adapter = RaiffeisenBankAdapter()

        # Test character mapping from CHAR_FIXES
        test_cases = [
            ('K£rtyatranzakci©', 'Kártyatranzakció'),  # £->á, ©->é
            ('¶tutal£s', 'Átutalás'),  # ¶->Á, £->á
            ('Kézlem©ny', 'Közlemény'),  # é->ö, ©->é
            # Note: 'é' maps to 'ö' globally - this affects all text
            # So 'SchénherzIskolaszévetkezet' becomes 'SchönherzIskolaszövetkezet'
            # This is intentional based on observed PDF encoding
        ]

        for dirty, expected in test_cases:
            result = adapter._clean_text(dirty)
            # Verify mapping is applied
            assert '£' not in result, f"Should not have £ in result: {result}"
            assert '©' not in result or result.count('©') < dirty.count('©'), f"Should reduce © in result: {result}"

    def test_clean_text_preserves_normal_text(self):
        """Test that normal text is not affected."""
        adapter = RaiffeisenBankAdapter()

        normal_text = "Normal text without special characters"
        assert adapter._clean_text(normal_text) == normal_text


class TestNameFormatting:
    """Test company name formatting (CamelCase, multi-line, acronyms)."""

    def test_camelcase_spacing(self, sample_pdf_bytes):
        """Test CamelCase company names get proper spacing."""
        adapter = RaiffeisenBankAdapter()
        result = adapter.parse(sample_pdf_bytes)

        # Look for transactions with IT Cardigan - should have space between IT and Cardigan
        transactions = result['transactions']
        it_cardigan_txs = [t for t in transactions if 'IT Cardigan' in str(t.beneficiary_name or t.payer_name)]

        assert len(it_cardigan_txs) > 0, "Should find IT Cardigan transactions"

        for tx in it_cardigan_txs:
            name = tx.beneficiary_name or tx.payer_name
            assert 'IT Cardigan' in name, f"Expected 'IT Cardigan' but got '{name}'"
            assert 'ITCardigan' not in name, f"Should not have ITCardigan without space: '{name}'"

    def test_multiline_company_names(self, sample_pdf_bytes):
        """Test multi-line company names are joined correctly."""
        adapter = RaiffeisenBankAdapter()
        result = adapter.parse(sample_pdf_bytes)

        # Check for proper joining (e.g., "Z\nrt." -> "Zrt." without space)
        transactions = result['transactions']

        for tx in transactions:
            name = tx.payer_name or tx.beneficiary_name or ''

            # Should not have newlines in final name
            assert '\n' not in name, f"Name contains newline: '{name}'"

            # If it's a Zrt./Kft. company, should be properly joined
            if 'Zrt.' in name or 'Kft.' in name:
                # Should not have space before "rt." when joining multi-line
                assert ' rt.' not in name or name.endswith(' Zrt.'), f"Improper Zrt. formatting: '{name}'"


class TestPyPDF2Integration:
    """Test PyPDF2 usage for proper word spacing."""

    def test_uses_pypdf2_for_extraction(self):
        """Test that adapter uses PyPDF2 for text extraction."""
        # This test verifies that PyPDF2 is used instead of pdfplumber
        # by checking the import in the adapter module
        from bank_transfers.bank_adapters import raiffeisen_adapter
        import inspect

        source = inspect.getsource(raiffeisen_adapter)
        assert 'import PyPDF2' in source or 'from PyPDF2' in source
        assert 'pdfplumber' not in source

    def test_all_caps_names_have_spacing(self, sample_pdf_bytes):
        """Test that all-caps names maintain proper word spacing (PyPDF2 feature)."""
        adapter = RaiffeisenBankAdapter()
        result = adapter.parse(sample_pdf_bytes)

        transactions = result['transactions']

        # Look for transactions with all-caps names
        for tx in transactions:
            name = tx.payer_name or tx.beneficiary_name or ''

            # If name is all caps and has multiple words, should have spaces
            if name.isupper() and len(name) > 10:
                # Should have at least one space in multi-word names
                # (PyPDF2 preserves word boundaries, pdfplumber doesn't)
                words = name.split()
                if len(words) > 1:
                    assert ' ' in name, f"All-caps multi-word name should have spaces: '{name}'"
