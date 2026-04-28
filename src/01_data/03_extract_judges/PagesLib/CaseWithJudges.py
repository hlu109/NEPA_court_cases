import pandas as pd
from pydantic import BaseModel, Field
from typing import List


class CaseWithJudges(BaseModel):
    judges: List[str] = Field(
        description="List of appellate judge names in panel order."
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
        "judges": _serialize_judges(case.judges),
        "judge_count": len(case.judges),
    }
    df = pd.DataFrame([data])
    return df


def cases_to_dataframe(cases: List[CaseWithJudges]) -> pd.DataFrame:
    """Convert a list of CaseWithJudges objects to a dataframe."""
    data = []
    for case in cases:
        data.append({
            "judges": _serialize_judges(case.judges),
            "judge_count": len(case.judges),
        })
    df = pd.DataFrame(data)
    return df
