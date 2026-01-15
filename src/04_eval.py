"""
Evaluate LLM outcome coding performance on validation/test sets.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

from utils.config import (
    AG_VAL_ASSIGNMENTS_PATH,
    AG_TEST_ASSIGNMENTS_PATH,
    ADELGLICKS_CLEANED_PATH,
    COURTLISTENER_CLUSTER_CLEANED_PATH,
    LLM_OPINION_CODING_PATH,
    INTERMEDIATE_DATA_DIR,
)


OUTCOME_EVAL_DIR = INTERMEDIATE_DATA_DIR / "Outcome Coding Eval"
VAL_EVAL_PATH = OUTCOME_EVAL_DIR / "val_performance.csv"
TEST_EVAL_PATH = OUTCOME_EVAL_DIR / "test_performance.csv"
OUTCOME_PREDICTIONS_DIR = INTERMEDIATE_DATA_DIR / "Outcome Coding Predictions"


def compute_performance(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """
    Compute accuracy and macro-averaged precision/recall/F1.
    """
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
    if df.empty:
        return {
            "n": 0,
            "accuracy": np.nan,
            "macro_precision": np.nan,
            "macro_recall": np.nan,
            "macro_f1": np.nan,
        }

    accuracy = accuracy_score(df["y_true"], df["y_pred"])
    precision, recall, f1, _ = precision_recall_fscore_support(
        df["y_true"], df["y_pred"], average="macro", zero_division=0
    )
    return {
        "n": len(df),
        "accuracy": accuracy,
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(f1),
    }


def plot_confusion_matrix(
    y_true: pd.Series,
    y_pred: pd.Series,
    title: str,
    output_path: str | None = None,
):
    """
    Create and optionally save a confusion matrix figure.
    """
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
    if df.empty:
        return None

    labels = sorted(pd.unique(pd.concat([df["y_true"], pd.Series(["mixed"])])))
    cm = confusion_matrix(df["y_true"], df["y_pred"], labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(6, 6))
    disp.plot(ax=ax, cmap="Blues", colorbar=False, values_format="d")
    ax.set_title(title)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300)
        print(f"Saved confusion matrix to: {output_path}")
    return fig


def evaluate_split(
    assignments_path: str,
    ground_truth_path: str,
    ground_truth_id_col: str,
    assignments_id_col: str,
    split_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Evaluate a split (val or test) and return a metrics dataframe.
    """
    assignments = pd.read_csv(assignments_path, dtype={"cluster_id": str, assignments_id_col: str})
    ground_truth_df = pd.read_csv(ground_truth_path, dtype={"cluster_id": str, ground_truth_id_col: str})
    cl_df = pd.read_csv(COURTLISTENER_CLUSTER_CLEANED_PATH, dtype={"cluster_id": str, "lead_opinion_id": str})
    pred_outcomes_df = pd.read_csv(LLM_OPINION_CODING_PATH, dtype={"opinion_id": str})

    assert "lead_opinion_id" in cl_df.columns, "lead_opinion_id missing from CourtListener cluster metadata"
    assert "opinion_id" in pred_outcomes_df.columns, "opinion_id missing from LLM coded outcomes"
    assert ground_truth_id_col in ground_truth_df.columns, f"Missing ground truth id column: {ground_truth_id_col}"
    assert assignments_id_col in assignments.columns, f"Missing assignments id column: {assignments_id_col}"

    # Join CL to get lead opinion id
    merged = assignments.merge(
        cl_df[["cluster_id", "lead_opinion_id"]],
        on="cluster_id",
        how="left",
    )

    # Join ground truth
    merged = merged.merge(
        ground_truth_df[[ground_truth_id_col,
                         "district_outcome", "disposition"]],
        left_on=assignments_id_col,
        right_on=ground_truth_id_col,
        how="left",
    )

    # Join LLM predictions
    merged = merged.merge(
        pred_outcomes_df[["opinion_id", "district_outcome", "disposition"]],
        left_on="lead_opinion_id",
        right_on="opinion_id",
        how="left",
        suffixes=("_true", "_pred"),
    )

    # Exclude rows with missing predictions from metrics
    missing_pred_mask = merged["district_outcome_pred"].isna(
    ) & merged["disposition_pred"].isna()
    missing_predictions = int(missing_pred_mask.sum())
    eval_df = merged[~missing_pred_mask].copy()

    # Compute metrics
    metrics = []
    for target in ["district_outcome", "disposition"]:
        target_metrics = compute_performance(
            eval_df[f"{target}_true"],
            eval_df[f"{target}_pred"],
        )
        target_metrics["split"] = split_name
        target_metrics["target"] = target
        target_metrics["missing_predictions"] = missing_predictions
        metrics.append(target_metrics)

    metrics_df = pd.DataFrame(metrics)
    return metrics_df, merged


def run_val_eval(assignments_path: str, ground_truth_path: str, ground_truth_id_col: str, assignments_id_col: str, confusion_matrix_path_prefix: str) -> pd.DataFrame:
    val_metrics, val_merged = evaluate_split(
        assignments_path, ground_truth_path, ground_truth_id_col, assignments_id_col, "val"
    )
    plot_confusion_matrix(val_merged["district_outcome_true"], 
                          val_merged["district_outcome_pred"],
                          title = "District Outcome",
                          output_path = f"{confusion_matrix_path_prefix}_district_outcome.png")
    plot_confusion_matrix(val_merged["disposition_true"], 
                          val_merged["disposition_pred"],
                          title = "Disposition",
                          output_path = f"{confusion_matrix_path_prefix}_disposition.png")
    return val_metrics, val_merged


def run_test_eval(
    assignments_path: str,
    ground_truth_path: str,
    ground_truth_id_col: str,
    assignments_id_col: str,
    confusion_matrix_path_prefix: str,
) -> pd.DataFrame:
    test_metrics, test_merged = evaluate_split(
        assignments_path, ground_truth_path, ground_truth_id_col, assignments_id_col, "test"
    )
    plot_confusion_matrix(test_merged["district_outcome_true"], 
                          test_merged["district_outcome_pred"],
                          title = "District Outcome",
                          output_path = f"{confusion_matrix_path_prefix}_district_outcome.png")
    plot_confusion_matrix(test_merged["disposition_true"], 
                          test_merged["disposition_pred"],
                          title = "Disposition",
                          output_path = f"{confusion_matrix_path_prefix}_disposition.png")
    return test_metrics, test_merged

def main():
    # AdelGlicks val
    val_metrics, val_merged = run_val_eval(
        str(AG_VAL_ASSIGNMENTS_PATH),
        str(ADELGLICKS_CLEANED_PATH),
        "id_num",
        "adelglicks_id",
        str(OUTCOME_EVAL_DIR / "AG_val_confusion_matrix")
    )

    # Save predictions and performance metrics
    OUTCOME_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    OUTCOME_PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    val_metrics.to_csv(VAL_EVAL_PATH, index=False)
    print(f"Saved validation performance to: {VAL_EVAL_PATH}")

    val_pred_path = OUTCOME_PREDICTIONS_DIR / "AG_val_predictions.csv"
    val_merged.to_csv(val_pred_path, index=False)
    print(f"Saved validation predictions to: {val_pred_path}")

    # --------------------------------------------------------------------------
    # # Only run test evaluation once at the very end
    # # AdelGlicks test
    # test_metrics, test_merged = run_test_eval(
    #     str(AG_TEST_ASSIGNMENTS_PATH),
    #     str(ADELGLICKS_CLEANED_PATH),
    #     "id_num",
    #     "adelglicks_id",
    #     str(OUTCOME_EVAL_DIR / "AG_test_confusion_matrix")
    # )

    # # Save predictions and performance metrics
    # test_metrics.to_csv(TEST_EVAL_PATH, index=False)
    # print(f"Saved test performance to: {TEST_EVAL_PATH}")

    # test_pred_path = OUTCOME_PREDICTIONS_DIR / "AG_test_predictions.csv"
    # test_merged.to_csv(test_pred_path, index=False)
    # print(f"Saved test predictions to: {test_pred_path}")


if __name__ == "__main__":
    main()
