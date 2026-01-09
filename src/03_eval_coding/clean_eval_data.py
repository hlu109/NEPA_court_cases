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


def docket_to_case_crosswalk(CL_data, AG_data, BT_data):
    """ Create a crosswalk spreadsheet for docket numbers to case IDs for each dataset.

        Output: 
            Exports a CSV with columns: docket_number, case_id_courtlistener, case_id_adelglicks, case_id_breakthrough
    """

    # AdelGlicks:
    # extract docket numbers (docket_no1, docket_no2, docket_no3) and id_num
    # id_num may be duplicated. we want the docket number to be the unique index key
    # use pd melt to unpivot the docket number columns into a single column
    AG_crosswalk = AG_data[['id_num', 'docket_no1', 'docket_no2', 'docket_no3']].astype(str)

    AG_crosswalk = AG_crosswalk.melt(
        id_vars=['id_num'],
        value_vars=['docket_no1', 'docket_no2', 'docket_no3'],
        var_name='column_name',
        value_name='docket_num')
    AG_crosswalk = AG_crosswalk.rename(columns={'id_num': 'adelglicks_id'})
    AG_crosswalk = AG_crosswalk[['docket_num', 'adelglicks_id']]
    
    # drop empty docket numbers (which may appear in docket_no2 or docket_no3)
    AG_crosswalk = AG_crosswalk[AG_crosswalk['docket_num'] != 'nan']

    # CourtListener: 
    CL_crosswalk = CL_data[['docket_id', 'docket_no1', 'docket_no2', 'docket_no3', 'docket_no_others', 'opinion_id']].astype(str)
    # TODO: handle multiple opinion ids 
    # actually, it probably makes most sense for the ultimate crosswalk to be directly from docket number to opinion ids 
    CL_crosswalk = CL_crosswalk.rename(columns={'docket_id': 'courtlistener_docket_id'})

    # # check duplicated docket numbers
    # duplicated_dockets = AG_crosswalk[AG_crosswalk.duplicated(
    #     subset=['docket_num'], keep=False)]
    # print("Duplicated docket numbers in AG data:")
    # print(duplicated_dockets.head(20))
    # print("Number of duplicated docket numbers in AG data:",
    #       duplicated_dockets['docket_num'].nunique())

    # merge crosswalk dataframes on docket number
    # TODO
    crosswalk = AG_crosswalk  # placeholder
    print(crosswalk[crosswalk['adelglicks_id']=="436"])

    # export as csv
    crosswalk_out_path = Path("docket_to_case_crosswalk.csv") # TODO: replace with parameter / config 
    crosswalk.to_csv(crosswalk_out_path, index=False)

    print(f"Docket to case crosswalk exported to {crosswalk_out_path}")
    return crosswalk


def main(courtlistener_metadata_path: str, coded_opinions_path: str,
         adelglicks_raw_path: str, AG_sheet_name: str,
         breakthrough_raw_path: str, output_dir: str):
    """ Main function to clean and harmonize appellate NEPA case datasets."""

    CL_data = pd.read_csv(courtlistener_metadata_path)
    AG_data = pd.read_excel(adelglicks_raw_path, sheet_name=AG_sheet_name)

    BT_data = pd.read_csv(breakthrough_raw_path)

    # clean and harmonize docket numbers ---------------------------------------

    # CourtListener ---
    CL_data['docket_num_clean'] = CL_data['docketNumber']

    # Fix encoding issues (â€" should be -)
    CL_data['docket_num_clean'] = CL_data['docket_num_clean'].str.replace(
        'â€"', '-', regex=True)

    # remove "Consolidated with " or "C/w" text
    CL_data['docket_num_clean'] = CL_data['docket_num_clean'].str.replace(
        r" Consolidated with\s*", ", ", regex=True)
    CL_data['docket_num_clean'] = CL_data['docket_num_clean'].str.replace(
        r" C/w\s*", ", ", regex=True)

    # Remove common prefixes to make parsing easier
    prefixes = [
        r'Civil Action No\.\s*',
        r'Civil No\.\s*',
        r'Case No\.\s*',
        r'Docket\s*',
        r'Docket No\.\s*',
        r'No\.\s*',
        r'Nos\.\s*',
        r'Civ\.\s*A\.\s*',
    ]
    for prefix in prefixes:
        CL_data['docket_num_clean'] = CL_data['docket_num_clean'].str.replace(
            prefix, '', regex=True)

    # if there are multiple docket numbers, parse into multiple columns using delimeters "," ";" "&" "and" ", and". we keep the first 3 unique docket numbers and then put all remaining ones in a single extra column
    CL_data[['docket_no1', 'docket_no2', 'docket_no3',
             'docket_no_others']] = CL_data['docket_num_clean'].str.split(
                 r"\s*[,;&]\s*|\s*[,\s*]?and\s*", expand=True, n=3)
    # trim whitespace
    for col in ['docket_no1', 'docket_no2', 'docket_no3', 'docket_no_others']:
        CL_data[col] = CL_data[col].str.strip()

    CL_data = CL_data.drop(columns=['docket_num_clean'])

    # Adelman & Glicksman ---
    # nothing to change - already in the format docket_no1, docket_no2, etc.

    # Breakthrough Institute ---
    # TODO

    # harmonize outcome coding terms -------------------------------------------

    # CourtListener ---
    # already coded correctly

    # Adelman & Glicksman ---
    AG_data['district_outcome'] = AG_data['decision'].map({
        'aff_def':
        'defendant',
        'rev_def':
        'defendant',
        'aff_pl':
        'plaintiff',
        'rev_pl':
        'plaintiff',
    })

    AG_data['disposition'] = AG_data['rev_aff'].map({
        'aff': 'affirm',
        'rev': 'reverse',
    })

    # count how many unmapped values remain
    print("Unmapped district outcomes:")
    print(AG_data['district_outcome'].isna().sum())
    print("Unmapped dispositions:")
    print(AG_data['disposition'].isna().sum())
    print("Total cases in AG data:", AG_data.shape[0])

    # handle mixed outcomes, which are not coded in rev_aff

    # handle unclear coding for district outcome - e.g., granted, denied, mixed, dismissed

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

    # harmonize other variables ------------------------------------------------
    # harmonize values for year, court/circuit, lead agency

    # CourtListener ---
    CL_data['year_filed'] = pd.to_datetime(CL_data['dateFiled']).dt.year
    # court_id is already present
    # at the moment we don't have the metadata on federal agencies involved

    # Adelman & Glicksman ---
    # year_filed is already present
    print(AG_data['circuit'].unique())
    AG_data['court_id'] = AG_data['circuit'].map({
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
    AG_data['lead_agency'] = AG_data['agency']
    print(AG_data['lead_agency'].unique())

    # Breakthrough Institute ---

    # merge coded opinions with CourtListener metadata -------------------------
    # TODO

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


if __name__ == "__main__":
    data_dir = Path(
        "C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Data/")
    raw_dir = data_dir / "Raw/"
    intermed_dir = data_dir / "Intermediate/"

    CL_data, AG_data, BT_data = load_data(
        courtlistener_metadata_path=raw_dir /
        "CourtListener NEPA cases/opinions_metadata_20251219_110552.csv",
        adelglicks_raw_path=raw_dir /
        "nepa_judicial/data/NEPA Lit Circuit WL Sample-Combo Supp-Coded Final 2001-15 2.7.24.xlsx",
        AG_sheet_name="NEPA Circuit Data",
        breakthrough_raw_path=raw_dir /
        "Breakthrough_NEPA_Cases_2013_2022.csv")

    crosswalk = docket_to_case_crosswalk(CL_data, AG_data, BT_data)

    # main(
    #     courtlistener_metadata_path=raw_dir /
    #     "CourtListener NEPA cases/opinions_metadata_20251219_110552.csv",
    #     coded_opinions_path=None,
    #     adelglicks_raw_path=raw_dir /
    #     "nepa_judicial/data/NEPA Lit Circuit WL Sample-Combo Supp-Coded Final 2001-15 2.7.24.xlsx",
    #     AG_sheet_name="NEPA Circuit Data",
    #     breakthrough_raw_path=raw_dir /
    #     "Breakthrough_NEPA_Cases_2013_2022.csv",
    #     output_dir=intermed_dir / "eval_data/")

    # val_test_split()
