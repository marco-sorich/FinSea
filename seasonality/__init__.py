"""
Seasonality package to check and varify financial symbols for seasonality behaviour.

Modules:
--------
    analyzer
    Performs the anayzis and returns some pandas dataframes with results.
"""

__all__ = ['.analyzer']

from .analyzer import Analyzer  # noqa: F401
from .views.view import Views  # noqa: F401
