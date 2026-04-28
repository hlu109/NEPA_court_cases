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

# TODO: move this to utils
# Define logging function

def write_log(message, log_dir=log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_path = os.path.join(log_dir, f"log_{identifier}.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%H%M:%S")
        file.write(f"[{timestamp}] {message}\n\n")


def log_config(log_dir=log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save text of gemini prompt--------
    with open(prompt_text_path, "r") as file:
        prompt_text = file.read()
    with open(os.path.join(log_dir, f"prompt_text_{identifier}.txt"), "a",
              encoding="utf-8") as file:
        file.write(prompt_text)

    # Save parameter values ----------
    file_path = os.path.join(log_dir, f"log_{identifier}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] \n\n")
        file.write(f"CONFIG PARAMETERS\n\n")
        file.write(f"Input directory: {INPUT_DIR}\n")
        file.write(f"Case IDs filter: {case_ids if case_ids else 'All cases'}\n")
        file.write(f"Prompt text file: {prompt_text_name}\n")
        file.write(f"Gemini model: {gemini_model_id}\n\n")


# ------------------------------------------------------------------------------
# -----------------------------------------------------------------------------
