import pandas as pd
from pydantic import BaseModel, Field
from typing import Any, Dict, List


class CaseWithJudges(BaseModel):
    panel_judges: List[str] = Field(
        description="List of all appellate judge names on the panel, in panel order."
    )
    opinion_authors: List[str] = Field(
        description="List of judge name(s) who authored this specific opinion (majority, concurrence, or dissent)."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, # constructs new empty dict by default
        description="Flexible metadata fields added during processing."
    )

    def save_json(self, file_path: str):
        """Save the case information to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=4))


def _serialize_judges(judges: List[str]) -> str:
    if not judges:
        return ""
    return "; ".join(judge for judge in judges if judge)


def case_to_dataframe(case: CaseWithJudges) -> pd.DataFrame:
    """Convert a CaseWithJudges object to a dataframe."""
    data = {
        "panel_judges": _serialize_judges(case.panel_judges),
        "panel_judge_count": len(case.panel_judges),
        "opinion_authors": _serialize_judges(case.opinion_authors),
        "opinion_author_count": len(case.opinion_authors),
    }
    data.update(case.metadata) # appends dictionary of metadatax
    df = pd.DataFrame([data])
    return df


def cases_to_dataframe(cases: List[CaseWithJudges]) -> pd.DataFrame:
    """Convert a list of CaseWithJudges objects to a dataframe."""
    data = []
    for case in cases:
        row = {
            "panel_judges": _serialize_judges(case.panel_judges),
            "panel_judge_count": len(case.panel_judges),
            "opinion_authors": _serialize_judges(case.opinion_authors),
            "opinion_author_count": len(case.opinion_authors),
        }
        row.update(case.metadata) # appends dictionary of metadata
        data.append(row)
    df = pd.DataFrame(data)
    return df
