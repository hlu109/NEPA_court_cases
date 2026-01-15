"""
Merge CourtListener and AdelGlicks datasets by docket numbers.

This script:
- Computes statistics on docket number overlaps between datasets
- Generates match statistics (perfect matches, partial matches, etc.)
- Creates a merged dataset with match indicators
"""

import pandas as pd
import csv
from pathlib import Path
import sys

from utils.config import (
    ADELGLICKS_CLEANED_PATH,
    COURTLISTENER_CLUSTER_CLEANED_PATH,
    INTERMEDIATE_DATA_DIR,
    COURTLISTENER_AG_MATCH_STATS_PATH
)

# TODO: use year_filed as a sanity check after matching (because there might also be error in the year filed data?)

def get_docket_set(row, docket_cols = None):
    """
    Extract a set of non-empty docket numbers from a row.
    
    Args:
        row: DataFrame row
        docket_cols: List of docket column names to check
        
    Returns:
        Set of non-empty docket numbers (normalized: uppercase, stripped)
    """
    dockets = set()

    # CourtListener format 
    if 'docket_numbers_parsed' in row.index:
        parsed = row['docket_numbers_parsed']
        if pd.notna(parsed):
            for docket in str(parsed).split('; '):
                docket = docket.strip().upper()
                if docket and docket != 'NAN':
                    dockets.add(docket)
        return dockets
    
    # AdelGlicks format: docket_no1, docket_no2, docket_no3
    for col in docket_cols:
        if col in row.index:
            docket = row[col]
            if pd.notna(docket) and str(docket).strip() and str(docket).strip().upper() != 'NAN':
                dockets.add(str(docket).strip().upper())
    return dockets


def compute_all_matches(cl_df, ag_df):
    """
    Compute all matches between CourtListener and AdelGlicks cases.
    
    Rules:
    * Restrict matches to cases within the same court.
    * Match using the set of docket numbers.
    
    Args:
        cl_df: CourtListener dataframe with docket_numbers_parsed column
        ag_df: AdelGlicks dataframe with docket_no1, docket_no2, docket_no3
        
    Returns:
        Tuple of (matches list, cl_docket_sets dict, ag_docket_sets dict)
    """    
    # Verify court_id column exists
    if 'court_id' not in cl_df.columns:
        raise ValueError("court_id column not found in CourtListener dataframe")
    if 'court_id' not in ag_df.columns:
        raise ValueError("court_id column not found in AdelGlicks dataframe")
    
    # Extract docket sets for each row
    print("Extracting docket number sets...")
    cl_docket_sets = cl_df.apply(lambda row: get_docket_set(row), axis=1) # pd.Series

    ag_docket_cols = ['docket_no1', 'docket_no2', 'docket_no3']
    ag_docket_sets = ag_df.apply(lambda row: get_docket_set(row, ag_docket_cols), axis=1)
        
    matches = []

    print("Grouping cases by court...")
    cl_courts = cl_df['court_id']
    ag_courts = ag_df['court_id']
    cl_court_to_indices = cl_courts.groupby(cl_courts).groups
    ag_court_to_indices = ag_courts.groupby(ag_courts).groups

    for court_id, cl_indices in cl_court_to_indices.items():
        ag_indices = ag_court_to_indices.get(court_id)
        
        if ag_indices is None:
            continue

        for cl_idx in cl_indices:
            cl_dockets = cl_docket_sets.get(cl_idx, set())
            if not cl_dockets:
                continue

            for ag_idx in ag_indices:
                ag_dockets = ag_docket_sets.get(ag_idx, set())
                if not ag_dockets:
                    continue

                overlap = cl_dockets.intersection(ag_dockets)
                if overlap:
                    matches.append({
                        'cluster_id': cl_df.loc[cl_idx, 'cluster_id'],
                        'adelglicks_id': ag_df.loc[ag_idx, 'id_num'],
                        'cl_docket_count': len(cl_dockets),
                        'ag_docket_count': len(ag_dockets),
                        'overlap_count': len(overlap),
                        'cl_dockets': "; ".join(sorted(cl_dockets)),
                        'ag_dockets': "; ".join(sorted(ag_dockets)),
                        'overlapping_dockets': "; ".join(sorted(overlap)),
                        'is_perfect_match': cl_dockets == ag_dockets,
                        'cl_subset_of_ag': cl_dockets.issubset(ag_dockets),
                        'ag_subset_of_cl': ag_dockets.issubset(cl_dockets),
                    })

    matches_df = pd.DataFrame(matches) if matches else pd.DataFrame()

    # remove duplicates
    matches_df = matches_df.drop_duplicates()

    return matches_df, cl_docket_sets, ag_docket_sets


def find_cases_with_multiple_matches(matches_df):
    """
    Add indicator columns for CL/AG cases matched to multiple other cases.

    Returns:
        matches_df with two new boolean columns:
        - cl_has_multiple_matches
        - ag_has_multiple_matches
    """
    if matches_df is None or len(matches_df) == 0:
        return matches_df

    cl_counts = matches_df.groupby('cluster_id').size()
    ag_counts = matches_df.groupby('adelglicks_id').size()
    matches_df['cl_has_multiple_matches'] = matches_df['cluster_id'].map(
        cl_counts.gt(1)
    ).fillna(False)
    matches_df['ag_has_multiple_matches'] = matches_df['adelglicks_id'].map(
        ag_counts.gt(1)
    ).fillna(False)

    return matches_df


def compute_match_statistics(cl_df, ag_df, matches_df, cl_docket_sets, ag_docket_sets):
    """
    Compute statistics on docket number matches.
    
    Args:
        cl_df: CourtListener dataframe
        ag_df: AdelGlicks dataframe
        matches_df: DataFrame of matches
        cl_docket_sets: Dictionary mapping CL indices to docket sets
        ag_docket_sets: Dictionary mapping AG indices to docket sets
        
    Returns:
        Dictionary with match statistics
    """
    stats = {}
    
    if len(matches_df) > 0:
        stats['total_matches'] = len(matches_df)
        stats['unique_cl_matched'] = matches_df['cluster_id'].nunique()
        stats['unique_ag_matched'] = matches_df['adelglicks_id'].nunique()
        stats['perfect_matches'] = matches_df['is_perfect_match'].sum()
        stats['cl_subset_of_ag'] = matches_df['cl_subset_of_ag'].sum()
        stats['ag_subset_of_cl'] = matches_df['ag_subset_of_cl'].sum()
        stats['cl_strict_subset_of_ag'] = stats['cl_subset_of_ag'] - stats['perfect_matches']
        stats['ag_strict_subset_of_cl'] = stats['ag_subset_of_cl'] - stats['perfect_matches']
        
        # Multiple match statistics
        cl_match_counts = matches_df.groupby('cluster_id').size()
        ag_match_counts = matches_df.groupby('adelglicks_id').size()
        stats['cl_cases_with_multiple_matches'] = (cl_match_counts > 1).sum()
        stats['ag_cases_with_multiple_matches'] = (ag_match_counts > 1).sum()

        # Perfect matches that also have multiple matches
        cl_perfect_any = matches_df[matches_df['is_perfect_match']].groupby('cluster_id').size()
        ag_perfect_any = matches_df[matches_df['is_perfect_match']].groupby('adelglicks_id').size()
        stats['cl_cases_perfect_and_multiple'] = (
            cl_perfect_any.reindex(cl_match_counts.index, fill_value=0).gt(0)
            & cl_match_counts.gt(1)
        ).sum()
        stats['ag_cases_perfect_and_multiple'] = (
            ag_perfect_any.reindex(ag_match_counts.index, fill_value=0).gt(0)
            & ag_match_counts.gt(1)
        ).sum()
        
        # Overlap count distribution
        stats['overlap_distribution'] = matches_df['overlap_count'].value_counts().to_dict()
        
        # Match quality breakdown
        stats['match_quality'] = {
            'perfect': stats['perfect_matches'],
            'cl_subset': stats['cl_subset_of_ag'],
            'ag_subset': stats['ag_subset_of_cl'],
            'cl_strict_subset': stats['cl_strict_subset_of_ag'],
            'ag_strict_subset': stats['ag_strict_subset_of_cl'],
            'partial': len(matches_df) - stats['perfect_matches']
        }
    else:
        stats['total_matches'] = 0
        stats['unique_cl_matched'] = 0
        stats['unique_ag_matched'] = 0
        stats['perfect_matches'] = 0
        stats['cl_subset_of_ag'] = 0
        stats['ag_subset_of_cl'] = 0
        stats['cl_cases_with_multiple_matches'] = 0
        stats['ag_cases_with_multiple_matches'] = 0
        stats['cl_cases_perfect_and_multiple'] = 0
        stats['ag_cases_perfect_and_multiple'] = 0
        stats['overlap_distribution'] = {}
        stats['match_quality'] = {}
    
    # Overall dataset statistics
    stats['total_cl_cases'] = len(cl_df)
    stats['total_ag_cases'] = len(ag_df)
    stats['cl_cases_with_dockets'] = (cl_docket_sets.apply(len) > 0).sum()
    stats['ag_cases_with_dockets'] = (ag_docket_sets.apply(len) > 0).sum()
    stats['cl_cases_unmatched'] = stats['total_cl_cases'] - stats['unique_cl_matched']
    stats['ag_cases_unmatched'] = stats['total_ag_cases'] - stats['unique_ag_matched']
    
    return stats


def format_statistics(stats):
    """Format match statistics in a readable format."""
    lines = []
    lines.append("\n" + "="*60)
    lines.append("DOCKET NUMBER MATCH STATISTICS")
    lines.append("="*60)
    
    lines.append("\nDataset Overview:")
    lines.append(f"  CourtListener cases: {stats['total_cl_cases']}")
    lines.append(f"  AdelGlicks cases: {stats['total_ag_cases']}")
    
    lines.append("\nMatch Overview:")
    lines.append(f"  Total matches found: {stats['total_matches']}")
    lines.append(f"  Unique CourtListener cases matched: {stats['unique_cl_matched']}")
    lines.append(f"  Unique AdelGlicks cases matched: {stats['unique_ag_matched']}")
    lines.append(f"  CourtListener cases unmatched: {stats['cl_cases_unmatched']}")
    lines.append(f"  AdelGlicks cases unmatched: {stats['ag_cases_unmatched']}")
    
    if stats['total_matches'] > 0:
        lines.append("\nMultiple Match Statistics:")
        lines.append(f"  CL cases with multiple matches: {stats['cl_cases_with_multiple_matches']}")
        lines.append(f"  AG cases with multiple matches: {stats['ag_cases_with_multiple_matches']}")
        lines.append(f"  CL cases perfect + multiple: {stats['cl_cases_perfect_and_multiple']}")
        lines.append(f"  AG cases perfect + multiple: {stats['ag_cases_perfect_and_multiple']}")
        
        lines.append("\nMatch Quality:")
        lines.append(f"  Perfect matches (identical docket sets): {stats['match_quality'].get('perfect', 0)}")
        lines.append(f"  CL strict subset of AG (all CL dockets in AG): {stats['match_quality'].get('cl_strict_subset', 0)}")
        lines.append(f"  AG strict subset of CL (all AG dockets in CL): {stats['match_quality'].get('ag_strict_subset', 0)}")
        lines.append(f"  Partial matches (some overlap): {stats['match_quality'].get('partial', 0)}")
        
        lines.append("\nOverlap Count Distribution:")
        for overlap_count, match_count in sorted(stats['overlap_distribution'].items()):
            lines.append(f"  {overlap_count} docket(s) overlap: {match_count} matches")

    return "\n".join(lines)


def print_statistics(stats):
    """Print match statistics in a readable format."""
    output = format_statistics(stats)
    print(output)
    return output


def main():
    # Load cleaned datasets
    cl_df = pd.read_csv(COURTLISTENER_CLUSTER_CLEANED_PATH)
    ag_df = pd.read_csv(ADELGLICKS_CLEANED_PATH)
    
    # Compute all matches
    matches_df, cl_docket_sets, ag_docket_sets = compute_all_matches(cl_df, ag_df)
    matches_df = find_cases_with_multiple_matches(matches_df)
    
    # # Create detailed merge with all cases
    # detailed_df = create_detailed_merge(cl_df, ag_df, matches_df, cl_docket_sets, ag_docket_sets)
    
    # Compute statistics
    stats = compute_match_statistics(cl_df, ag_df, matches_df, cl_docket_sets, ag_docket_sets)
    
    # Print statistics and save to text file
    stats_output = print_statistics(stats)
    COURTLISTENER_AG_MATCH_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    COURTLISTENER_AG_MATCH_STATS_PATH.write_text(stats_output, encoding="utf-8")
    
    
    # Save match data to CSV
    output_path = INTERMEDIATE_DATA_DIR / "CourtListener_AdelGlicks_matching.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    matches_df.to_csv(output_path, index=False)
    print(f"\nSaved matching data to: {output_path}")


if __name__ == "__main__":
    main()

