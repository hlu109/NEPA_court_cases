"""
Clean CourtListener cluster metadata and map to lead opinions.

This script:
- Standardizes docket numbers 
- Maps each cluster to its lead opinion 
- Saves cleaned data to Intermediate/Cleaned Datasets/CourtListener/cluster_metadata.csv
"""

import pandas as pd
import csv
from pathlib import Path
import sys
import re
from typing import List

from utils.docket_utils import normalize_dash_characters
from utils.config import COURTLISTENER_METADATA_DIR, COURTLISTENER_CLUSTER_CLEANED_PATH


def find_lead_opinion(cluster_id: int, opinion_df: pd.DataFrame) -> str:
    """
    Find the lead opinion ID for a given cluster.
    
    Prefer identifying lead opinions in the following order: 
    * 020lead 
    * 025plurality
    * 015unanimous
    * 010combined (fallback when CourtListener can't identify a specific opinion type or opinion contains multiple types)
    
    Args:
        cluster_id: Cluster ID to find lead opinion for
        opinion_df: DataFrame with opinion metadata (must have cluster_id and opinion_type columns)
        
    Returns:
        Lead opinion ID (string), or empty string if not found
    """
    cluster_opinions = opinion_df[opinion_df['cluster_id'] == cluster_id]
    if cluster_opinions.empty:
        return ''
    
    # Look for lead opinions
    lead_opinion = cluster_opinions[cluster_opinions['opinion_type'] == '020lead']
    if not lead_opinion.empty:
        return lead_opinion.iloc[0]['opinion_id'] # return the first '020lead' opinion id
    plurality_opinion = cluster_opinions[cluster_opinions['opinion_type'] == '025plurality']
    if not plurality_opinion.empty:
        return plurality_opinion.iloc[0]['opinion_id'] # return the first '025plurality' opinion id

    unanimous_opinion = cluster_opinions[cluster_opinions['opinion_type'] == '015unanimous']
    if not unanimous_opinion.empty:
        return unanimous_opinion.iloc[0]['opinion_id'] # return the first '015unanimous' opinion id
    
    combined_opinion = cluster_opinions[cluster_opinions['opinion_type'] == '010combined']
    if not combined_opinion.empty:
        return combined_opinion.iloc[0]['opinion_id'] # return the first '010combined' opinion id
    
    # If no lead opinion found
    return ''


def map_clusters_to_lead_opinions(cluster_df: pd.DataFrame, 
                                   opinion_df: pd.DataFrame) -> pd.DataFrame:
    """
    Map each cluster to its lead opinion ID.
    
    Args:
        cluster_df: DataFrame with cluster metadata (must have cluster_id column)
        opinion_df: DataFrame with opinion metadata (must have cluster_id, opinion_id, and opinion_type columns)
        
    Returns:
        Cluster DataFrame with added lead_opinion_id column
    """
    print("\nMapping clusters to lead opinions...")
    cluster_df = cluster_df.copy()
    
    if 'cluster_id' not in cluster_df.columns:
        raise ValueError("Cluster dataframe must have 'cluster_id' column.")
    
    # Check for required columns in opinion_df
    if 'cluster_id' not in opinion_df.columns:
        raise ValueError("Opinion dataframe must have 'cluster_id' column")
    if 'opinion_id' not in opinion_df.columns:
        raise ValueError("Opinion dataframe must have 'opinion_id' column")
    if 'opinion_type' not in opinion_df.columns:
        raise ValueError("Opinion dataframe must have 'opinion_type' column")
        
    # Map each cluster to its lead opinion
    cluster_df['lead_opinion_id'] = cluster_df['cluster_id'].apply(
        lambda cid: find_lead_opinion(cid, opinion_df)
    )
    
    # Report statistics
    mapped_count = cluster_df['lead_opinion_id'].notna().sum()
    print(f"  Mapped {mapped_count} clusters ({mapped_count/len(cluster_df)*100:.1f}%) to lead opinions")
    print(f"  {len(cluster_df) - mapped_count} clusters without lead opinions")
    
    return cluster_df


def parse_courtlistener_docket_string(docket_str: str) -> List[str]:
    """
    Extract individual docket numbers from a CourtListener docket string.

    This function is specifically designed for parsing CourtListener docket numbers.
    Handles various formats including:
    - Multiple dockets separated by commas/semicolons
    - Consolidated cases (e.g., "Consolidated with", "C/w")
    - Docket ranges (e.g., "07-1493 to 07-1499")
    - Various prefixes (Civil Action No., Case No., Docket, etc.)
    - Encoding issues and dash character variants

    Args:
        docket_str: Raw CourtListener docket number string

    Returns:
        List of cleaned individual docket numbers with normalized dash characters
    """
    if pd.isna(docket_str) or not str(docket_str).strip():
        return []

    docket_str = str(docket_str)

    # Normalize dash characters first
    docket_str = normalize_dash_characters(docket_str)

    # Remove common prefixes
    prefixes = [
        r'Civil Action No\.\s*',
        r'Civil No\.\s*',
        r'Case No\.\s*',
        r'Docket\s+',
        r'Docket No\.\s*',
        r'DOCKETS \s+',
        r'Nos?\.\s*',
        r'Civ\.\s*A\.\s*',
    ]
    for prefix in prefixes:
        docket_str = re.sub(prefix, '', docket_str, flags=re.IGNORECASE)

    # Handle "Consolidated with" or "C/w" patterns
    consolidated_pattern = r'(?:Consolidated with|C/w)\s+'
    docket_str = re.sub(consolidated_pattern, ', ',
                        docket_str, flags=re.IGNORECASE)

    # Extract all potential docket numbers
    dockets = []

    # Handle ranges like "07-1493 to 07-1499"
    # TODO: handle edge case where there are multiple ranges. e.g. "Nos. 07-1363, 07-1437, 07-1493 to 07-1499, 08-1105 to 08-1107"
    range_match = re.search(r'(\d+)-(\d+)\s+to\s+(\d+)-(\d+)', docket_str)
    if range_match:
        prefix1, start, prefix2, end = range_match.groups()
        # Generate the range
        start_num = int(start)
        end_num = int(end)
        for i in range(start_num, end_num + 1):
            dockets.append(f"{prefix1}-{i:04d}")
        # Remove the range from the string to avoid double-counting
        docket_str = re.sub(r'(\d+)-(\d+)\s+to\s+(\d+)-(\d+)', '', docket_str)

    # Split by common separators: comma, semicolon, ampersand, "and"
    split_pattern = r'\s*[,;&]\s*|\s+and\s+|\s*,\s*and\s*'
    dockets.extend(re.split(split_pattern, docket_str))

    # Convert any letters to upper case
    docket_str = docket_str.upper()

    # not sure if we need/want the below - may be excessive
    # # Extract the core docket number (pattern: digits-digits or just numbers)
    # # Look for patterns like: 22-1101, 17-cv-1179, 1:17-cv-01871, etc.
    # docket_matches = re.findall(
    #     r'\b\d{1,2}:\d{1,2}-[a-z]{2,3}-\d+\b|'  # 1:17-cv-01871
    #     r'\b\d{2,4}-\d{4,5}\b|'  # 22-1101, 07-1363
    #     r'\b\d{2,4}-[a-z]{2,3}-\d+\b',  # 17-cv-1179
    #     item,
    #     flags=re.IGNORECASE
    # )

    # if docket_matches:
    #     dockets.extend(docket_matches)
    # else:
    #     # If no standard pattern found, try to extract any number-number pattern
    #     # This handles cases with parenthetical info
    #     basic_match = re.search(r'(\d{2,4}-\d{4,5})', item)
    #     if basic_match:
    #         dockets.append(basic_match.group(1))

    # Clean up and deduplicate
    cleaned_dockets = []
    seen = set()

    for docket in dockets:
        # Remove any trailing/leading whitespace, parenthetical info, and punctuation characters
        docket = re.sub(r'\s*\([^)]*\)\s*', '', docket).strip()
        docket = docket.strip('.,;')

        if docket and docket not in seen:
            cleaned_dockets.append(docket)
            seen.add(docket)

    # sort cleaned dockets alphabetically
    cleaned_dockets.sort()
    return cleaned_dockets


def clean_courtlistener_dockets(
        df: pd.DataFrame,
        docket_col: str = 'docketNumber',
        max_columns: int = 5) -> pd.DataFrame:
    """
    Process a CourtListener dataframe to split docket numbers into separate columns.


    Args:
        df: Input CourtListener dataframe with docket numbers
        docket_col: Name of the column containing docket numbers (default: 'docketNumber')
        max_columns: Maximum number of docket columns to create (default: 5)

    Returns:
        DataFrame with original columns plus docket_no1, docket_no2, ..., docket_no{max_columns}, 
        and docket_no_others for overflow
    """
    print("\nCleaning docket numbers...")
    df = df.copy()

    # Parse all docket numbers (using CourtListener-specific parser)
    df['docket_numbers_parsed'] = df[docket_col].apply(
        parse_courtlistener_docket_string)

    # Expand out the first X docket numbers in separate columns
    for i in range(max_columns):
        col_name = f'docket_no{i+1}'
        df[col_name] = df['docket_numbers_parsed'].apply(
            lambda x: x[i] if i < len(x) else None
        )

    # Clean up columns
    df['docket_numbers_parsed'] = df['docket_numbers_parsed'].apply(
        lambda x: '; '.join(x) if isinstance(x, list) else x
    )
    df = df.rename(columns={'docketNumber': 'docket_numbers_raw'})

    return df


def clean_cluster_metadata(cluster_metadata_path: str, 
                           opinion_metadata_path: str,
                           output_path: str) -> pd.DataFrame:
    """
    Clean CourtListener cluster metadata and link to lead opinions.
    
    Args:
        cluster_metadata_path: Path to raw cluster metadata CSV
        opinion_metadata_path: Path to opinion metadata CSV
        output_path: Path to save cleaned cluster metadata CSV
        
    Returns:
        Cleaned DataFrame with docket numbers split and lead_opinion_id added
    """
    print(f"Loading cluster metadata from {cluster_metadata_path}...")
    cluster_df = pd.read_csv(cluster_metadata_path)
    
    print(f"\nLoading opinion metadata from {opinion_metadata_path}...")
    opinion_df = pd.read_csv(opinion_metadata_path)
    
    # Clean docket numbers
    cluster_df = clean_courtlistener_dockets(
        cluster_df, max_columns=5)
    
    # Harmonize other variables (year, court/circuit, lead agency)
    print("\nHarmonizing other variables...")
    assert 'dateFiled' in cluster_df.columns
    cluster_df['year_filed'] = pd.to_datetime(cluster_df['dateFiled']).dt.year
    # court_id is already in standardized form
    # at the moment we don't have the metadata on federal agencies involved
    
    # Map to lead opinions
    cluster_df = map_clusters_to_lead_opinions(cluster_df, opinion_df)

    # Re-sort column variables alphabetically 
    cluster_df = cluster_df.reindex(sorted(cluster_df.columns), axis=1)
    
    # Save cleaned data
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cluster_df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"\nSaved cleaned cluster metadata to {output_path}")
    
    return cluster_df


def main():
    # Find the most recent run directory
    # TODO: maybe move to separate function or pass as parameter 
    run_dirs = sorted([d for d in COURTLISTENER_METADATA_DIR.iterdir() if d.is_dir() and d.name.startswith('run_')])
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {COURTLISTENER_METADATA_DIR}")
    
    latest_run_dir = run_dirs[-1]
    print(f"Using run directory: {latest_run_dir.name}")
    
    cluster_metadata_path = latest_run_dir / "cluster_metadata.csv"
    opinion_metadata_path = latest_run_dir / "opinion_metadata.csv"
    
    # Clean the data
    clean_cluster_metadata(
        cluster_metadata_path=str(cluster_metadata_path),
        opinion_metadata_path=str(opinion_metadata_path),
        output_path=str(COURTLISTENER_CLUSTER_CLEANED_PATH)
    )
    
    print("Done!")


if __name__ == "__main__":
    main()

