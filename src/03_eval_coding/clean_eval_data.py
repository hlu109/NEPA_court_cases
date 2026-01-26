""" Clean and harmonize coding across CourtListener, Adelman & Glicksman, and
    Breakthrough datasets of appellate NEPA cases.
"""

import csv
import json
import pandas as pd
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.courtlistener_utils import flatten_metadata


def load_data(courtlistener_metadata_path: str, adelglicks_raw_path: str,
              AG_sheet_name: str, breakthrough_raw_path: str):
    """ Load raw data from each dataset.

        Output:
            tuple containing three dataframes: (CL_data, AG_data, BT_data)
    """
    CL_data = pd.read_csv(courtlistener_metadata_path)
    AG_data = pd.read_excel(adelglicks_raw_path, sheet_name=AG_sheet_name)
    BT_data = pd.read_csv(breakthrough_raw_path)

    return CL_data, AG_data, BT_data


def main(courtlistener_metadata_path: str, coded_opinions_path: str,
         adelglicks_raw_path: str, AG_sheet_name: str,
         breakthrough_raw_path: str, output_dir: str):
    """ Main function to clean and harmonize appellate NEPA case datasets."""

    CL_data = pd.read_csv(courtlistener_metadata_path)
    AG_data = pd.read_excel(adelglicks_raw_path, sheet_name=AG_sheet_name)

    BT_data = pd.read_csv(breakthrough_raw_path)


    # harmonize outcome coding terms -------------------------------------------



    # Breakthrough Institute ---
    # TODO
    print(BT_data['Prev Agency on NEPA claim'].unique())
    print(BT_data['Prevailing party\non all claims (District only)'].unique())
    print(BT_data['Case Disposition'].unique())

    # TODO: which do we want - prevailing on NEPA claim or prevailing overall?
    BT_data['district_outcome'] = BT_data['Prev Agency on NEPA claim'].map({
        'Agency':
        'defendant',
        'Challenger':
        'plaintiff',
        'N/A':
        'UNK',
    })

    # if Case Disposition is Judgement for Defendant and district_outcome is defendant,
    # then disposition is affirm; if district_outcome is plaintiff, then disposition is reverse
    BT_data['disposition'] = BT_data.apply(
        lambda row: 'affirm'
        if (row['Case Disposition'] == 'Judgement for Defendant' and row[
            'district_outcome'] == 'defendant') else
        ('reverse' if (row['Case Disposition'] == 'Judgement for Defendant' and
                       row['district_outcome'] == 'plaintiff') else
         ('reverse' if (row['Case Disposition'] == 'Judgement for Plaintiff'
                        and row['district_outcome'] == 'plaintiff') else
          ('affirm'
           if (row['Case Disposition'] == 'Judgement for Plaintiff' and row[
               'district_outcome'] == 'defendant') else 'UNK'))),
        axis=1)

    # count how many unmapped values remain
    print("Unmapped district outcomes:")
    print(BT_data['district_outcome'].isna().sum())
    print("Unmapped dispositions:")
    print(
        (BT_data['disposition'] == "UNK").sum())  # check == UNK instead of na

    # handle mixed outcomes, which are not coded in rev_aff

    # handle unclear coding for district outcome - e.g., granted, denied, mixed, dismissed


    # export cleaned data ------------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    CL_out_path = Path(output_dir) / "courtlistener_metadata_clean.csv"
    AG_out_path = Path(output_dir) / "adelman_glicksman_clean.csv"
    BT_out_path = Path(output_dir) / "breakthrough_metadata_clean.csv"

    CL_data.to_csv(CL_out_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    AG_data.to_csv(AG_out_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    BT_data.to_csv(BT_out_path, index=False, quoting=csv.QUOTE_NONNUMERIC)


def val_test_split(in_path: str, out_path_prefix: str):
    """ Split evaluation data into validation and test sets based on docket 
        IDs and exports as two csvs. 
    
        Implements stratified sampling by year and court.

        Args:
            in_path: path to cleaned evaluation csv data
            out_path_prefix: prefix for output csvs; will save as 
                {out_path_prefix}_val.csv and {out_path_prefix}_test.csv
    """
    pass

