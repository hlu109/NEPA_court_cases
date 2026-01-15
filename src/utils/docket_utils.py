"""
Utility functions for cleaning and parsing docket numbers.
"""

import pandas as pd


def normalize_dash_characters(text: str) -> str:
    """
    Normalize all dash/hyphen variants (en dash, em dash, figure dash, minus 
    sign, encoding issues, etc.) to a standard hyphen-minus (-) for consistency
    across datasets.

    Args:
        text: String that may contain various dash characters

    Returns:
        String with all dash characters normalized to standard hyphen
    """
    if pd.isna(text):
        return text

    text = str(text)

    # Common dash/hyphen variants to normalize:
    dash_variants = [
        '–',  # En dash (U+2013)
        '—',  # Em dash (U+2014)
        '‒',  # Figure dash (U+2012)
        '−',  # Minus sign (U+2212)
        '‑',  # Non-breaking hyphen (U+2011)
        'â€"',  # Encoding corruption (Windows-1252)
    ]

    for dash in dash_variants:
        text = text.replace(dash, '-')

    return text
