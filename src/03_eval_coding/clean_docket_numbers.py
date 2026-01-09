"""
Clean and parse docket numbers from CourtListener data.

This script handles various non-standardized docket number formats and extracts
individual docket numbers into separate columns.
"""

import pandas as pd
import re
from typing import List, Tuple


def parse_docket_numbers(docket_str: str) -> List[str]:
    """
    Extract individual docket numbers from a docket string.

    Handles various formats including:
    - Multiple dockets separated by commas/semicolons
    - Consolidated cases (e.g., "Consolidated with", "C/w")
    - Docket ranges (e.g., "07-1493 to 07-1499")
    - Various prefixes (Civil Action No., Case No., Docket, etc.)
    - Encoding issues (â€" instead of -)

    Args:
        docket_str: Raw docket number string

    Returns:
        List of cleaned individual docket numbers
    """
    if pd.isna(docket_str) or not docket_str.strip():
        return []

    # Fix encoding issues (â€" should be -)
    docket_str = docket_str.replace('â€"', '-')

    # Remove common prefixes to make parsing easier
    prefixes = [
        r'Civil Action No\.\s*',
        r'Civil No\.\s*',
        r'Case No\.\s*',
        r'Docket\s+',
        r'Nos?\.\s*',
        r'Civ\.\s*A\.\s*',
    ]
    for prefix in prefixes:
        docket_str = re.sub(prefix, '', docket_str, flags=re.IGNORECASE)

    # Extract all potential docket numbers before splitting
    dockets = []

    # Handle "Consolidated with" or "C/w" patterns - split these first
    consolidated_pattern = r'(?:Consolidated with|C/w)\s+'
    parts = re.split(consolidated_pattern, docket_str, flags=re.IGNORECASE)

    for part in parts:
        # Split by semicolons (often separates different info)
        # Keep only the first part before semicolon unless it's a docket list
        if ';' in part:
            # Check if the part after semicolon contains docket numbers
            subparts = part.split(';')
            main_part = subparts[0]
            for subpart in subparts[1:]:
                # Only include if it looks like it contains a docket number
                if re.search(r'\d+-\d+', subpart) and not re.search(r'D\.C\.\s*No\.', subpart, re.IGNORECASE):
                    main_part += '; ' + subpart
            part = main_part

        # Handle ranges like "07-1493 to 07-1499"
        range_match = re.search(r'(\d+)-(\d+)\s+to\s+(\d+)-(\d+)', part)
        if range_match:
            prefix1, start, prefix2, end = range_match.groups()
            # Generate the range
            start_num = int(start)
            end_num = int(end)
            for i in range(start_num, end_num + 1):
                dockets.append(f"{prefix1}-{i:04d}")
            # Remove the range from the string to avoid double-counting
            part = re.sub(r'(\d+)-(\d+)\s+to\s+(\d+)-(\d+)', '', part)

        # Split by common separators: comma, semicolon, "and"
        split_pattern = r'[,;]\s*|\s+and\s+'
        items = re.split(split_pattern, part)

        for item in items:
            item = item.strip()
            if not item:
                continue

            # Extract the core docket number (pattern: digits-digits or just numbers)
            # Look for patterns like: 22-1101, 17-cv-1179, 1:17-cv-01871, etc.
            docket_matches = re.findall(
                r'\b\d{1,2}:\d{1,2}-[a-z]{2,3}-\d+\b|'  # 1:17-cv-01871
                r'\b\d{2,4}-\d{4,5}\b|'  # 22-1101, 07-1363
                r'\b\d{2,4}-[a-z]{2,3}-\d+\b',  # 17-cv-1179
                item,
                flags=re.IGNORECASE
            )

            if docket_matches:
                dockets.extend(docket_matches)
            else:
                # If no standard pattern found, try to extract any number-number pattern
                # This handles cases with parenthetical info
                basic_match = re.search(r'(\d{2,4}-\d{4,5})', item)
                if basic_match:
                    dockets.append(basic_match.group(1))

    # Clean up and deduplicate
    cleaned_dockets = []
    seen = set()

    for docket in dockets:
        # Remove any trailing/leading whitespace and parenthetical info
        docket = re.sub(r'\s*\([^)]*\)\s*', '', docket).strip()

        # Normalize the docket number
        docket = docket.strip('.,;')

        if docket and docket not in seen:
            cleaned_dockets.append(docket)
            seen.add(docket)

    return cleaned_dockets


def clean_docket_numbers_dataframe(df: pd.DataFrame, docket_col: str = 'docketNumber') -> pd.DataFrame:
    """
    Process a dataframe to split docket numbers into separate columns.

    Args:
        df: Input dataframe with docket numbers
        docket_col: Name of the column containing docket numbers

    Returns:
        DataFrame with original columns plus docket_1, docket_2, etc.
    """
    # Parse all docket numbers
    df['parsed_dockets'] = df[docket_col].apply(parse_docket_numbers)

    # Find the maximum number of dockets in any row
    max_dockets = df['parsed_dockets'].apply(len).max()

    # Create separate columns for each docket position
    for i in range(max_dockets):
        df[f'docket_{i+1}'] = df['parsed_dockets'].apply(
            lambda x: x[i] if i < len(x) else None
        )

    # Drop the temporary column
    df = df.drop('parsed_dockets', axis=1)

    return df


def main():
    """Main function to clean docket numbers from CourtListener data."""
    # File path
    input_file = "C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Data/Raw/CourtListener NEPA cases/opinions_metadata_20251219_110552.csv"
    output_file = "C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Data/Raw/CourtListener NEPA cases/opinions_metadata_cleaned_dockets.csv"

    # Read the data
    print("Reading data...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows")

    # Clean docket numbers
    print("Cleaning docket numbers...")
    df_cleaned = clean_docket_numbers_dataframe(df)

    # Print some statistics
    docket_cols = [col for col in df_cleaned.columns if col.startswith('docket_')]
    print(f"\nCreated {len(docket_cols)} docket columns")
    print(f"Maximum dockets in a single row: {len(docket_cols)}")

    # Show some examples
    print("\n=== Sample Results ===")
    sample_rows = df_cleaned[df_cleaned['docketNumber'].notna()].head(10)
    for idx, row in sample_rows.iterrows():
        print(f"\nOriginal: {row['docketNumber']}")
        dockets = [row[col] for col in docket_cols if pd.notna(row[col])]
        print(f"Parsed: {dockets}")

    # Save the cleaned data
    print(f"\nSaving to {output_file}...")
    df_cleaned.to_csv(output_file, index=False)
    print("Done!")

    return df_cleaned


if __name__ == "__main__":
    df_cleaned = main()
