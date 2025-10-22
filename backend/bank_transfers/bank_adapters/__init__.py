"""
Bank statement adapter system for multi-bank PDF parsing.

This module provides an abstract adapter interface and factory pattern
for parsing bank statements from different Hungarian banks.
"""

from .base import (
    BankStatementAdapter,
    NormalizedTransaction,
    StatementMetadata,
    BankStatementParseError,
)
from .factory import BankAdapterFactory
from .granit_adapter import GranitBankAdapter
from .revolut_adapter import RevolutAdapter
from .magnet_adapter import MagnetBankAdapter
from .kh_adapter import KHBankAdapter

__all__ = [
    'BankStatementAdapter',
    'NormalizedTransaction',
    'StatementMetadata',
    'BankStatementParseError',
    'BankAdapterFactory',
    'GranitBankAdapter',
    'RevolutAdapter',
    'MagnetBankAdapter',
    'KHBankAdapter',
]
