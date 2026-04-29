# ------------------------------------------------------------------------------
# Load libraries ---------------------------------------------------------------
# ------------------------------------------------------------------------------
from google import genai
import os
import sys
from pathlib import Path

# Add project root to Python path to allow imports from src.utils
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import config_judges as config
from PagesLib.CaseWithJudges import case_to_dataframe
from utils.gemini_digitizer import process_cases
from utils.gemini_logging import write_log, log_config

# Note: API requires an API key, saved in secret/GEMINI_API_KEY.txt


def main():
    # --------------------------------------------------------------------------
    # -- Execution -------------------------------------------------------------
    # --------------------------------------------------------------------------

    # Create output directory
    if not os.path.exists(config.gemini_dir):
        os.makedirs(config.gemini_dir)
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)
    if not os.path.exists(config.results_dir):
        os.makedirs(config.results_dir)
    if not os.path.exists(config.temp_dir):
        os.makedirs(config.temp_dir)

    # Log parameters used -----------------------------------------
    log_config(
        prompt_text_path=config.prompt_text_path,
        gemini_model_id=config.gemini_model_id,
        identifier=config.identifier,
        log_dir=config.log_dir,
        input_dir=config.INPUT_DIR,
        case_ids=config.case_ids,
    )

    print(f"Using task prompt in {config.prompt_text_name}")
    print(f"Saving output in {config.results_dir}")

    # Create a client -----------------------------------------
    # get API key
    with open("secret/GEMINI_API_KEY.txt", "r", encoding="utf-8") as file:
        api_key = file.read()
        print("Successfully loaded API key")

    client = genai.Client(api_key=api_key)
    print("Successfully loaded Gemini AI client with API key")

    # Read in the structured prompt
    with open(config.prompt_text_path, "r", encoding="utf-8") as file:
        task = file.read()

    # Defined .csv outfile path
    outpath = os.path.join(config.results_dir, config.OUTPUT_FILE_NAME)
    print(f"Outpath set to: {outpath}")

    # Run digitizer process ------------------------------------------
    process_cases(client,
                  input_dir=config.INPUT_DIR,
                  data_struct=config.page_schema,
                  prompt_text=task,
                  model_id=config.gemini_model_id,
                  outfile_path=outpath,
                  intermediate_dir=config.temp_dir,
                  to_dataframe_fn=case_to_dataframe,
                  file_extension="pdf",
                  case_ids=config.case_ids if hasattr(config, 'case_ids') else None,
                  log_dir=config.log_dir,
                  identifier=config.identifier,
                  debug=False)
    write_log("PROCESS COMPLETE", config.log_dir, config.identifier)
    print("\n Digitizing task complete !! ")


if __name__ == "__main__":
    main()
