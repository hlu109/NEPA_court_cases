import os
from datetime import datetime
from PagesLib.Case import CaseSimple
from pathlib import Path

# TODO: merge this config with the main config in utils/config.py

# ------------------------------------------------------------------------------
# SET PARAMETERS ---------------------------------------------------------------
# ------------------------------------------------------------------------------


# Set API Parameters -------------------------------------------
# Define the model you are going to use (flash is free with 1,500 requests per day)
# gemini_model_id = "gemini-2.0-flash"
# gemini_model_id = "gemini-2.5-flash"
gemini_model_id = "gemini-2.5-pro"
# gemini_model_id = "gemini-3-flash-preview"
# gemini_model_id = "gemini-3-pro-preview"


# Set File Paths -------------------------------------------
# Define the input directory containing opinion_XXX folders
# Each folder should contain opinion_XXX.html file

BASE_DATA_DIR = Path("C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Data/")
BASE_CODE_DIR = Path("C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Code/NEPA_court_cases/")
INPUT_DIR = BASE_DATA_DIR / "Raw/CourtListener NEPA cases/opinions_20251219_110552"


# Define your output file base name (no file extension)
# redo this since input dir is now a Path object
OUTPUT_FILE_BASE_NAME = INPUT_DIR.name
print(f"Output file base name set to: {OUTPUT_FILE_BASE_NAME}")

# SET OUTPUT PATH  -------------------------------------------------------------
OUTPUT_DIR = BASE_DATA_DIR / "Intermediate/"

gemini_dir = OUTPUT_DIR / "gemini_output"
log_dir = OUTPUT_DIR / "gemini_logs"

# SET GEMINI PROMPT ------------------------------------------------------------
# Indicate the file name for the prompt to use
prompt_text_name = "case_prompt_simple.txt"
prompt_text_path = BASE_CODE_DIR / "src" / "02_coding_cases" / "prompts" / prompt_text_name

# Set Case Schema -----------------------------------
page_schema = CaseSimple

# Case Parameters -------------------------------------------
# Case filtering (optional) - if None, processes all cases in INPUT_DIR
# Example: ["10033657", "1027273"] to process specific cases
case_ids = None
# case_ids = ["5738", "2471"]

# ------------------------------------------------------------------------------
# END OF SET PARAMETERS --------------------------------------------------------
# ------------------------------------------------------------------------------

# save each execution with a separate file suffix --- to ensure nothing is over-written
# TODO: refactor to use the generate timestamp function already in utils
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
identifier = "coding_" + timestamp
OUTPUT_FILE_NAME = OUTPUT_FILE_BASE_NAME + "_" + identifier + ".csv"

# folder for intermediate results
results_dir = gemini_dir / (OUTPUT_FILE_BASE_NAME + "_" + identifier)
temp_dir = results_dir / "temp"


# ------------------------------------------------------------------------------
# -----------------------------------------------------------------------------
