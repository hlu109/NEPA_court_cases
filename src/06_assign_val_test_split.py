"""
Assign validation/test split for matched CourtListener-AdelGlicks cases.
"""

import pandas as pd
import numpy as np

from utils.config import (
    COURTLISTENER_AG_MATCHING_PATH,
    COURTLISTENER_AG_MATCHING_SPLIT_PATH,
    OUTCOME_ASSIGNMENTS_DIR,
    AG_VAL_ASSIGNMENTS_PATH,
    AG_TEST_ASSIGNMENTS_PATH,
)


def assign_val_test_split(
    matches_df: pd.DataFrame,
    seed: int = 42,
    split_col: str = "dataset_split",
) -> pd.DataFrame:
    """
    Assign 50/50 validation/test split for AdelGLicks cases that were perfectly matched to CourtListener cases and have case outcomes coded. Assignments are random and stratified by court.

    Args:
        matches_df: DataFrame from CourtListener_AdelGlicks_matching.csv
        seed: Random seed for reproducibility
        split_col: Column name for dataset split assignment

    Returns:
        DataFrame with split assignments in split_col.
    """
    required_cols = {"is_perfect_match", "AG_has_outcome", "court_id"}
    missing = required_cols - set(matches_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = matches_df.copy()
    df[split_col] = ""

    eligible_mask = df["is_perfect_match"].astype(bool) & df["AG_has_outcome"].astype(bool)
    eligible_df = df[eligible_mask]

    rng = np.random.default_rng(seed)
    val_indices = []
    test_indices = []
    leftovers = []


    for _, group in eligible_df.groupby(["court_id"]):
        group_indices = group.index.to_numpy()
        rng.shuffle(group_indices)
        split_point = len(group_indices) // 2
        val_indices.extend(group_indices[:split_point])
        test_indices.extend(group_indices[split_point:split_point * 2])
        if len(group_indices) % 2 == 1:
            leftovers.append(group_indices[-1])

    # Randomize leftover order, then distribute to keep overall counts balanced
    leftovers = np.array(leftovers)
    rng.shuffle(leftovers)
    for idx in leftovers:
        if len(val_indices) <= len(test_indices):
            val_indices.append(idx)
        else:
            test_indices.append(idx)

    df.loc[val_indices, split_col] = "val"
    df.loc[test_indices, split_col] = "test"

    print(f"Eligible rows for split: {len(eligible_df)}")
    print(f"Validation rows: {len(val_indices)}")
    print(f"Test rows: {len(test_indices)}")

    return df


def main():
    matches_df = pd.read_csv(COURTLISTENER_AG_MATCHING_PATH)
    matches_df = assign_val_test_split(matches_df)

    # Save outputs
    COURTLISTENER_AG_MATCHING_SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    matches_df.to_csv(COURTLISTENER_AG_MATCHING_SPLIT_PATH, index=False)
    print(f"\nSaved split data to: {COURTLISTENER_AG_MATCHING_SPLIT_PATH}")

    # Also save the val and test sets in their own files (as a permanent identification so we don't accidentally touch or change the test set)
    OUTCOME_ASSIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    val_df = matches_df[matches_df["dataset_split"] == "val"].copy()
    test_df = matches_df[matches_df["dataset_split"] == "test"].copy()
    val_df.to_csv(AG_VAL_ASSIGNMENTS_PATH, index=False)
    test_df.to_csv(AG_TEST_ASSIGNMENTS_PATH, index=False)

    print(f"Saved val subset to: {AG_VAL_ASSIGNMENTS_PATH}")
    print(f"Saved test subset to: {AG_TEST_ASSIGNMENTS_PATH}")


if __name__ == "__main__":
    main()

