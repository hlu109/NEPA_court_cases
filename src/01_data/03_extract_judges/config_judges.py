import os
from datetime import datetime
from PagesLib.CaseWithJudges import CaseWithJudges
from utils.config import DATA_ROOT_DIR, CODE_DIR


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
INPUT_DIR = DATA_ROOT_DIR / "Raw" / "CourtListener opinion download" / "opinions_20251219_110552"


# Define your output file base name (no file extension)
OUTPUT_FILE_BASE_NAME = INPUT_DIR.name
print(f"Output file base name set to: {OUTPUT_FILE_BASE_NAME}")

# SET OUTPUT PATH  -------------------------------------------------------------
OUTPUT_DIR = DATA_ROOT_DIR / "Intermediate"

gemini_dir = OUTPUT_DIR / "gemini_output"
log_dir = OUTPUT_DIR / "gemini_logs"

# SET GEMINI PROMPT ------------------------------------------------------------
# Indicate the file name for the prompt to use
prompt_text_name = "judge_prompt.txt"
prompt_text_path = CODE_DIR / "src" / "01_data" / "03_extract_judges" / "prompts" / prompt_text_name

# Set Case Schema -----------------------------------
page_schema = CaseWithJudges

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
identifier = "judges_" + timestamp
OUTPUT_FILE_NAME = OUTPUT_FILE_BASE_NAME + "_" + identifier + ".csv"

# folder for intermediate results
results_dir = gemini_dir / (OUTPUT_FILE_BASE_NAME + "_" + identifier)
temp_dir = results_dir / "temp"

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
