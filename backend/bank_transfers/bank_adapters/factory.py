"""
Bank adapter factory for multi-bank PDF detection and routing.

This factory implements automatic bank detection and adapter selection
for multi-company support with different banks.
"""

from typing import Optional, List, Dict, Any, Type
import logging

from .base import BankStatementAdapter, BankStatementParseError
from .granit_adapter import GranitBankAdapter
from .revolut_adapter import RevolutAdapter
from .magnet_adapter import MagnetBankAdapter
from .kh_adapter import KHBankAdapter
from .raiffeisen_adapter import RaiffeisenBankAdapter

logger = logging.getLogger(__name__)


class BankAdapterFactory:
    """
    Factory for automatic bank detection and adapter selection.

    This factory manages all registered bank adapters and provides
    automatic bank detection based on PDF content analysis.

    Usage:
        # Automatic detection
        adapter = BankAdapterFactory.get_adapter(pdf_bytes, filename)
        result = adapter.parse(pdf_bytes)

        # List supported banks
        banks = BankAdapterFactory.list_supported_banks()
    """

    # Registry of all available bank adapters
    _adapters: List[Type[BankStatementAdapter]] = [
        GranitBankAdapter,
        RevolutAdapter,
        MagnetBankAdapter,
        KHBankAdapter,
        RaiffeisenBankAdapter,
        # Future adapters:
        # OTPBankAdapter,
        # CIBBankAdapter,
        # ErsteBankAdapter,
    ]

    @classmethod
    def get_adapter(
        cls,
        pdf_bytes: bytes,
        filename: str = ""
    ) -> BankStatementAdapter:
        """
        Automatically detect bank and return appropriate adapter instance.

        Iterates through all registered adapters and calls their detect()
        method to find the first matching adapter.

        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename (may contain hints)

        Returns:
            Instantiated adapter for the detected bank

        Raises:
            BankStatementParseError: If no adapter can handle the PDF

        Example:
            try:
                adapter = BankAdapterFactory.get_adapter(pdf_bytes, "statement.pdf")
                result = adapter.parse(pdf_bytes)
            except BankStatementParseError as e:
                print(f"Unsupported bank: {e}")
        """
        logger.info(f"Detecting bank for PDF: {filename}")

        for adapter_class in cls._adapters:
            try:
                if adapter_class.detect(pdf_bytes, filename):
                    logger.info(
                        f"Detected bank: {adapter_class.get_bank_name()} "
                        f"({adapter_class.get_bank_code()})"
                    )
                    return adapter_class()
            except Exception as e:
                # Don't let one adapter's detection error stop others
                logger.warning(
                    f"Error during {adapter_class.__name__}.detect(): {e}"
                )
                continue

        # No adapter could handle this PDF
        raise BankStatementParseError(
            "Unsupported bank statement format. "
            f"Supported banks: {', '.join(cls.get_supported_bank_names())}"
        )

    @classmethod
    def get_adapter_by_bank_code(cls, bank_code: str) -> Optional[BankStatementAdapter]:
        """
        Get adapter instance by bank code.

        Useful for re-parsing existing statements when bank is already known.

        Args:
            bank_code: Bank identifier (e.g., 'GRANIT', 'OTP', 'KH')

        Returns:
            Adapter instance or None if bank code not found

        Example:
            adapter = BankAdapterFactory.get_adapter_by_bank_code('GRANIT')
            if adapter:
                result = adapter.parse(pdf_bytes)
        """
        for adapter_class in cls._adapters:
            try:
                if adapter_class.get_bank_code() == bank_code.upper():
                    return adapter_class()
            except NotImplementedError:
                continue

        logger.warning(f"No adapter found for bank code: {bank_code}")
        return None

    @classmethod
    def list_supported_banks(cls) -> List[Dict[str, str]]:
        """
        Get list of all supported banks with their details.

        Returns:
            List of dictionaries with bank information:
            [
                {
                    'code': 'GRANIT',
                    'name': 'GRÁNIT Bank Nyrt.',
                    'bic': 'GNBAHUHB'
                },
                ...
            ]

        Example:
            banks = BankAdapterFactory.list_supported_banks()
            for bank in banks:
                print(f"{bank['name']} ({bank['code']})")
        """
        banks = []

        for adapter_class in cls._adapters:
            try:
                banks.append({
                    'code': adapter_class.get_bank_code(),
                    'name': adapter_class.get_bank_name(),
                    'bic': adapter_class.get_bank_bic(),
                })
            except NotImplementedError:
                # Skip adapters that don't properly implement required fields
                logger.warning(
                    f"{adapter_class.__name__} does not implement required fields"
                )
                continue

        return banks

    @classmethod
    def get_supported_bank_codes(cls) -> List[str]:
        """
        Get list of supported bank codes.

        Returns:
            List of bank codes (e.g., ['GRANIT', 'OTP', 'KH'])
        """
        return [bank['code'] for bank in cls.list_supported_banks()]

    @classmethod
    def get_supported_bank_names(cls) -> List[str]:
        """
        Get list of supported bank names.

        Returns:
            List of bank names (e.g., ['GRÁNIT Bank Nyrt.', 'OTP Bank Nyrt.'])
        """
        return [bank['name'] for bank in cls.list_supported_banks()]

    @classmethod
    def register_adapter(cls, adapter_class: Type[BankStatementAdapter]) -> None:
        """
        Register a new bank adapter dynamically.

        This allows plugins or custom adapters to be added at runtime.

        Args:
            adapter_class: BankStatementAdapter subclass to register

        Raises:
            ValueError: If adapter doesn't properly implement BankStatementAdapter

        Example:
            class CustomBankAdapter(BankStatementAdapter):
                BANK_CODE = 'CUSTOM'
                BANK_NAME = 'Custom Bank'
                BANK_BIC = 'CUSTBUHB'
                # ... implement detect() and parse()

            BankAdapterFactory.register_adapter(CustomBankAdapter)
        """
        if not issubclass(adapter_class, BankStatementAdapter):
            raise ValueError(
                f"{adapter_class.__name__} must be a subclass of BankStatementAdapter"
            )

        # Validate required class attributes
        try:
            adapter_class.get_bank_code()
            adapter_class.get_bank_name()
            adapter_class.get_bank_bic()
        except NotImplementedError as e:
            raise ValueError(
                f"{adapter_class.__name__} must define BANK_CODE, BANK_NAME, and BANK_BIC"
            ) from e

        # Check for duplicate bank codes
        existing_codes = cls.get_supported_bank_codes()
        new_code = adapter_class.get_bank_code()

        if new_code in existing_codes:
            logger.warning(
                f"Replacing existing adapter for bank code: {new_code}"
            )
            # Remove existing adapter with same code
            cls._adapters = [
                a for a in cls._adapters
                if a.get_bank_code() != new_code
            ]

        cls._adapters.append(adapter_class)
        logger.info(
            f"Registered adapter: {adapter_class.get_bank_name()} ({new_code})"
        )

    @classmethod
    def unregister_adapter(cls, bank_code: str) -> bool:
        """
        Unregister an adapter by bank code.

        Args:
            bank_code: Bank identifier to remove

        Returns:
            True if adapter was found and removed, False otherwise
        """
        original_count = len(cls._adapters)
        cls._adapters = [
            a for a in cls._adapters
            if a.get_bank_code() != bank_code.upper()
        ]

        removed = len(cls._adapters) < original_count
        if removed:
            logger.info(f"Unregistered adapter for bank code: {bank_code}")

        return removed
