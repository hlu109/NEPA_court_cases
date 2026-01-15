"""
Clean and standardize AdelGlicks dataset.

This script:
- Standardizes docket numbers in AdelGlicks raw data
- Saves cleaned data to Intermediate/Cleaned Datasets/AdelGlicks.csv
"""

import pandas as pd
import csv
from pathlib import Path
import sys

from utils.docket_utils import normalize_dash_characters
from utils.config import ADELGLICKS_RAW_PATH, ADELGLICKS_SHEET_NAME, ADELGLICKS_CLEANED_PATH



def clean_adelglicks_dockets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize docket numbers in AdelGlicks dataframe. 

    (This function only normalizes the dash characters because the docket numbers already appear pretty consistent and clean.)

    Args:
        df: Input dataframe with docket_no1, docket_no2, docket_no3 columns

    Returns:
        DataFrame with standardized docket numbers.
    """
    df = df.copy()

    # Standardize docket number columns
    for col in ['docket_no1', 'docket_no2', 'docket_no3']:
        if col in df.columns:
            # convert docket numbers to strings but prevent nan's from being converted to strings that say "nan"
            df[col] = df[col].fillna('').astype(str) 

            # Normalize dash characters for consistency with CourtListener data
            df[col] = df[col].apply(
                lambda x: normalize_dash_characters(x) if pd.notna(x) else x)

            # Strip whitespace
            df[col] = df[col].str.strip() if df[col].notna().any() else df[col]

            # Convert any letters to upper case
            df[col] = df[col].str.upper()

    return df


def clean_adelglicks_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the coding of case outcomes. 
    """
    df = df.copy()
    # strip whitespace and standardize to lowercase
    df['decision'] = df['decision'].str.strip().str.lower()
    df['rev_aff'] = df['rev_aff'].str.strip().str.lower()

    df['district_outcome'] = df['decision'].map({
        'aff_def': 'defendant',
        'rev_def': 'defendant',
        'aff_pl': 'plaintiff',
        'rev_pl': 'plaintiff',
    })
    df['disposition'] = df['rev_aff'].map({
        'aff': 'affirm',
        'rev': 'reverse',
    })


    # TODO: handle mixed outcomes, which are not coded in rev_aff
    # if decision is mixed, granted, denied, or dismissed, then set district_outcome and disposition to na for now 
    df.loc[df['decision'].isin(['mixed', 'granted', 'denied', 'dismissed']), 'district_outcome'] = None
    df.loc[df['decision'].isin(['mixed', 'granted', 'denied', 'dismissed']), 'disposition'] = None

    # TODO: handle unclear coding for district outcome - e.g., granted, denied, mixed, dismissed - will need to manually check these 
    
    print("Unmapped district outcomes:")
    print(df['district_outcome'].isna().sum())
    print("Unmapped dispositions:")
    print(df['disposition'].isna().sum())
    print("Total cases in AG data:", df.shape[0])

    return df

def clean_adelglicks_data(adelglicks_raw_path: str, sheet_name: str, 
                          output_path: str) -> pd.DataFrame:
    """
    Clean and standardize AdelGlicks dataset.
    
    Args:
        adelglicks_raw_path: Path to raw AdelGlicks Excel file
        sheet_name: Name of the sheet to read from Excel file
        output_path: Path to save cleaned CSV file
        
    Returns:
        Cleaned DataFrame
    """
    print(f"Loading AdelGlicks data from {adelglicks_raw_path}...")
    df = pd.read_excel(adelglicks_raw_path, sheet_name=sheet_name)
    
    # Standardize docket numbers
    print("Standardizing docket numbers...")
    df = clean_adelglicks_dockets(df)
    
    # Harmonize other variables (year, court/circuit, lead agency)
    # year_filed is already present
    print("Harmonizing other variables...")
    
    df['court_id'] = df['circuit'].map({
        'DC Circuit': 'cadc',
        'First Circuit': 'ca1',
        'Second Circuit': 'ca2',
        'Third Circuit': 'ca3',
        'Fourth Circuit': 'ca4',
        'Fifth Circuit': 'ca5',
        'Sixth Circuit': 'ca6',
        'Seventh Circuit': 'ca7',
        'Eighth Circuit': 'ca8',
        'Ninth Circuit': 'ca9',
        'Tenth Circuit': 'ca10',
        'Eleventh Circuit': 'ca11',
        'Federal Circuit': 'cafc',
    })
    df['lead_agency'] = df['agency']
    # print("Lead agencies found:")
    # print(df['lead_agency'].unique())

    df = clean_adelglicks_outcomes(df)
    
    # Save cleaned data
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"\nSaved cleaned data to {output_path}")
    
    return df


def main():
    clean_adelglicks_data(
        adelglicks_raw_path=str(ADELGLICKS_RAW_PATH),
        sheet_name=ADELGLICKS_SHEET_NAME,
        output_path=str(ADELGLICKS_CLEANED_PATH)
    )

if __name__ == "__main__":
    main()

