import pandas as pd
from pydantic import BaseModel, Field, StringConstraints
from typing import List, Dict, Optional, Union, Literal, Any, Annotated


# class CaseSimpleGemini(BaseModel):
#     """Partial case data structure for fields to be extracted by Gemini."""
#     disposition: Literal["affirm", "reverse", "mixed"] = Field(
#         description="Case disposition")
#     district_outcome: Literal["plaintiff", "defendant", "mixed"] = Field(
#         description="Outcome from lower district court case")


class CaseSimple(BaseModel):
    # opinion_id: str = Field(description="Opinion ID")
    disposition: Literal["affirm", "reverse", "mixed", "UNK"] = Field(
        description="Case disposition")
    district_outcome: Literal["plaintiff", "defendant", "mixed", "UNK"] = Field(
        description="Outcome from lower district court case")
    
    # TODO: extract judge? 
    
    def save_json(self, file_path: str):
        """Save the case information to a JSON file."""
        with open(file_path, "w") as f:
            f.write(self.model_dump_json(indent=4))

# convert Case to a DataFrame
def case_to_dataframe(case: CaseSimple) -> pd.DataFrame:
    """ Convert a Case object to a DataFrame."""
    data = {
        # "Opinion ID": case.opinion_id,
        "disposition": case.disposition,
        "district_outcome": case.district_outcome
    }
    df = pd.DataFrame([data])
    return df

def cases_to_dataframe(cases: List[CaseSimple]) -> pd.DataFrame:
    """ Convert a list of Case objects to a DataFrame."""
    data = []
    for case in cases: 
        data.append({
            # "Opinion ID": case.opinion_id,
            "disposition": case.disposition,
            "district_outcome": case.district_outcome
        })

    df = pd.DataFrame(data)
    return df
