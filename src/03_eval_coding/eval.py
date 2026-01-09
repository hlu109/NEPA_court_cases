# ------------------------------------------------------------------------------
# Load libraries ---------------------------------------------------------------
# ------------------------------------------------------------------------------
import os
from datetime import datetime
import pandas as pd
import json

import config
from config import write_log
from PagesLib.Case import CaseSimple
from typing import get_args

# ------------------------------------------------------------------------------
# -- Define functions ----------------------------------------------------------
# ------------------------------------------------------------------------------

# TODO: we should pass the config as an argument instead of importing it. also we should move write_log to utils

# TODO: update for court cases
# TODO: import sklearn or something and just use their performance functions 
# could also be nice to have a confusion matrix eventually 
def eval_performance(pred_path, true_path, filter_year_start=1945, filter_year_end=1950, filter_pg=None):
    """
    Evaluate the performance of digitization results. Computes accuracy as well as total and group-wise mileage.

    Args:
        pred_path (str): Path to csv with predicted data.
        true_path (str): Path to spreadsheet with hand-coded ground truth data.
        filter_year_start (int): Only evaluate predictions starting from this year.
        filter_year_end (int): Only evaluate predictions ending in this year (inclusive).
        filter_pg (int): Only evaluate predictions from this page.

    NOTE: filter_year must be the data year, not publication year. 

    Output:
        Returns performance (dict): Dictionary with performance metrics.
        Also logs performance to log file.
    """
    # TODO: the difficult part (and not sure how to resolve it easily automatically) is matching entries because the hand-coded vs generated data may have different number of projects, whether it's because the LLM made something up/missed something or if it was simply a matter of discretion when one entry has multiple projects.
    assert os.path.exists(
        pred_path), f"Predicted data file {pred_path} does not exist."
    assert os.path.exists(
        true_path), f"True data file {true_path} does not exist."

    eval_log_dir = os.path.join(config.output_dir, "performance_evals")

    # Load the predicted and true data
    pred_data = pd.read_csv(pred_path)
    if true_path.endswith(".xlsx"):
        true_data = pd.read_excel(true_path)
    elif true_path.endswith(".csv"):
        true_data = pd.read_csv(true_path)
    else:
        raise ValueError(
            f"Ground truth data file {true_path} must be .xlsx or .csv format.")

    # convert boolean columns to string
    pred_data['New Construction'] = pred_data['New Construction'].astype(
        str).str.upper()
    pred_data['Construction Complete'] = pred_data['Construction Complete'].astype(
        str).str.upper()
    true_data['New Construction'] = true_data['New Construction'].astype(
        str).str.upper()
    true_data['Construction Complete'] = true_data['Construction Complete'].astype(
        str).str.upper()

    # filter by year and page if specified
    true_data = true_data.loc[true_data["Data Year"].between(
        filter_year_start, filter_year_end, inclusive="both")]
    pred_data = pred_data.loc[pred_data["Data Year"].between(
        filter_year_start, filter_year_end, inclusive="both")]
    if filter_pg is not None:
        true_data = true_data.loc[true_data["Page Number"] == filter_pg]
        pred_data = pred_data.loc[pred_data["Page Number"] == filter_pg]

    # verify columnn names are correct in both files
    # (retrieve column names from Entry class description field)
    col_names = [
        Entry.model_fields[vars].description for vars in Entry.model_fields.keys()]
    assert set(col_names).issubset(set(pred_data.columns)
                                   ), f"Predicted data is missing columns: {set(col_names) - set(pred_data.columns)}"
    assert set(col_names).issubset(set(true_data.columns)
                                   ), f"True data is missing columns: {set(col_names) - set(true_data.columns)}"

    # define performance metrics --------------------------
    print("Computing performance metrics...")
    mileage_groups = ["fuel", "new_construction",
                      "construction_complete", "inter_or_intra"]
    mileage_cols = [Entry.model_fields[g].description for g in mileage_groups]
    performance = {
        # "accuracy": {"Data Year": None} | {col: None for col in col_names},
        "accuracy": {col: None for col in col_names},
        "mi_pred_over_true": {
            "Total": None,
            "Data Year": {yr: None for yr in range(filter_year_start, filter_year_end + 1)},
            **{
                col_name: {
                    arg: None for arg in get_args(
                        Entry.model_fields[group].annotation)
                } for (col_name, group) in zip(mileage_cols, mileage_groups)
            },
            "Pipeline Length": {  # by quartile of true distribution?
                "Q1": None,
                "Q2": None,
                "Q3": None,
                "Q4": None,
            },
            "New Complete Natural Gas by Year": {
                yr: None for yr in range(filter_year_start, filter_year_end + 1)
            },
            "New Complete Natural Gas Interstate by Year": {
                yr: None for yr in range(filter_year_start, filter_year_end + 1)
            },
            "New Complete Natural Gas Intrastate by Year": {
                yr: None for yr in range(filter_year_start, filter_year_end + 1)
            },
        },
        "mi_pct_err": {
            "Total": None,
            "Data Year": {yr: None for yr in range(filter_year_start, filter_year_end + 1)},
            **{
                col_name: {
                    arg: None for arg in get_args(
                        Entry.model_fields[group].annotation)
                } for (col_name, group) in zip(mileage_cols, mileage_groups)
            },
            "Pipeline Length": {  # by quartile of true distribution?
                "Q1": None,
                "Q2": None,
                "Q3": None,
                "Q4": None,
            },
            "New Complete Natural Gas by Year": {
                yr: None for yr in range(filter_year_start, filter_year_end + 1)
            },
            "New Complete Natural Gas Interstate by Year": {
                yr: None for yr in range(filter_year_start, filter_year_end + 1)
            },
            "New Complete Natural Gas Intrastate by Year": {
                yr: None for yr in range(filter_year_start, filter_year_end + 1)
            },
        }
    }

    # compute performance metrics -------------------------
    # # compute accuracy for each column
    # for col in performance["accuracy"].keys():
    #     correct = (pred_data[col] == true_data[col]).sum()
    #     total = len(true_data)
    #     performance["accuracy"][col] = correct / total

    # compute mileage error
    # filter out unknown pipeline lengths (-1 and -2)
    true_data_excl_unknown = true_data.loc[
        ~true_data['Pipeline Length'].isin([-1, -2])]
    pred_data_excl_unknown = pred_data.loc[
        ~pred_data['Pipeline Length'].isin([-1, -2])]

    # total mileage
    true_total_mi = true_data_excl_unknown['Pipeline Length'].sum()
    pred_total_mi = pred_data_excl_unknown['Pipeline Length'].sum()
    performance["mi_pct_err"]["Total"] = abs(
        pred_total_mi - true_total_mi) / true_total_mi
    performance["mi_pred_over_true"]["Total"] = (pred_total_mi / true_total_mi)

    # mileage by group
    for col_name, group in zip(mileage_cols, mileage_groups):
        print(f"Computing mileage performance for group: {col_name}")
        for arg in get_args(Entry.model_fields[group].annotation):
            true_mi = true_data_excl_unknown.loc[
                (true_data_excl_unknown[col_name] == arg),
                'Pipeline Length'].sum()
            pred_mi = pred_data_excl_unknown.loc[
                (pred_data_excl_unknown[col_name] == arg),
                'Pipeline Length'].sum()

            if true_mi > 0:
                performance["mi_pct_err"][col_name][arg] = abs(
                    pred_mi - true_mi) / true_mi
                performance["mi_pred_over_true"][col_name][arg] = (
                    pred_mi / true_mi)
            else:
                if pred_mi > 0:
                    performance["mi_pct_err"][col_name][arg] = -999
                    performance["mi_pred_over_true"][col_name][arg] = -999
                else:
                    performance["mi_pct_err"][col_name][arg] = None
                    performance["mi_pred_over_true"][col_name][arg] = None

    # mileage by data year
    # mileage performance by quartile of pipeline distribution
    # TODO

    # mileage for target pipelines
    print("Computing mileage for new complete natural gas pipelines...")
    for yr in range(filter_year_start, filter_year_end + 1):

        # new complete natural gas
        true_pl = true_data_excl_unknown.loc[
            (true_data_excl_unknown["Fuel Type"] == "NATURAL GAS") &
            (true_data_excl_unknown["New Construction"] == "TRUE") &
            (true_data_excl_unknown["Construction Complete"] == "TRUE") & (
                true_data_excl_unknown["Data Year"] == yr)
        ]
        pred_pl = pred_data_excl_unknown.loc[
            (pred_data_excl_unknown["Fuel Type"] == "NATURAL GAS") &
            (pred_data_excl_unknown["New Construction"] == "TRUE") &
            (pred_data_excl_unknown["Construction Complete"] == "TRUE") & (
                pred_data_excl_unknown["Data Year"] == yr)
        ]

        true_mi = true_pl['Pipeline Length'].sum()
        pred_mi = pred_pl['Pipeline Length'].sum()
        performance["mi_pct_err"]["New Complete Natural Gas by Year"][yr] = abs(
            pred_mi - true_mi) / true_mi
        performance["mi_pred_over_true"]["New Complete Natural Gas by Year"][yr] = (
            pred_mi / true_mi)

        # new complete natural gas interstate
        true_pl_inter = true_pl.loc[
            (true_pl["Interstate or Intrastate"] == "INTERSTATE")
        ]
        pred_pl_inter = pred_pl.loc[
            (pred_pl["Interstate or Intrastate"] == "INTERSTATE")
        ]
        true_mi_inter = true_pl_inter['Pipeline Length'].sum()
        pred_mi_inter = pred_pl_inter['Pipeline Length'].sum()
        performance["mi_pct_err"]["New Complete Natural Gas Interstate by Year"][yr] = abs(
            pred_mi_inter - true_mi_inter) / true_mi_inter
        performance["mi_pred_over_true"]["New Complete Natural Gas Interstate by Year"][yr] = (
            pred_mi_inter / true_mi_inter)

        # new complete natural gas intrastate
        true_pl_intra = true_pl.loc[
            (true_pl["Interstate or Intrastate"] == "INTRASTATE")
        ]
        pred_pl_intra = pred_pl.loc[
            (pred_pl["Interstate or Intrastate"] == "INTRASTATE")
        ]
        true_mi_intra = true_pl_intra['Pipeline Length'].sum()
        pred_mi_intra = pred_pl_intra['Pipeline Length'].sum()
        performance["mi_pct_err"]["New Complete Natural Gas Intrastate by Year"][yr] = abs(
            pred_mi_intra - true_mi_intra) / true_mi_intra
        performance["mi_pred_over_true"]["New Complete Natural Gas Intrastate by Year"][yr] = (
            pred_mi_intra / true_mi_intra)

    # Log the evaluation results
    # TODO: create separate folder for performance evaluations and rename the log file something better
    write_log(
        f"Evaluation results for {pred_path} vs {true_path}:\n{json.dumps(performance, indent=4)}", log_dir=eval_log_dir)

    print("Evaluation complete.")

    return performance


if __name__ == "__main__":
    eval_performance()
