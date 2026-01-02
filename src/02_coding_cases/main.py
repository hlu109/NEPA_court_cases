# ------------------------------------------------------------------------------
# Load libraries ---------------------------------------------------------------
# ------------------------------------------------------------------------------
from google import genai
import os
from datetime import datetime
import pandas as pd

# Load the user-defined files -----

import config
from config import write_log
import digitizer 
from eval import eval_performance

# Note: API requires an API key, saved in secret/GEMINI_API_KEY.txt


def main():
    # TODO: pass in config here instead of importing?
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
    config.log_config()

    print(f"Using task prompt in {config.prompt_text_name}")
    print(f"Saving output in {config.results_dir}")

    # Create a client -----------------------------------------

    # get API key
    with open("secret/GEMINI_API_KEY.txt", "r", encoding="utf-8") as file:
        api_key = file.read()
        print("Successfully loaded API key")

    client = genai.Client(api_key=api_key,
                          #   http_options={'api_version': 'v1'}
                          )
    print("Successfully loaded Gemini AI client with API key")

    # Read in the structured prompt
    with open(config.prompt_text_path, "r", encoding="utf-8") as file:
        task = file.read()

    # Defined .csv outfile path
    outpath = os.path.join(config.results_dir, config.OUTPUT_FILE_NAME)
    print(f"Outpath set to: {outpath}")

    # Run digitizer process ------------------------------------------
    df = digitizer.process_cases(client,
                                 input_dir=config.INPUT_DIR,
                                 data_struct=config.page_schema,
                                 prompt_text=task,
                                 model_id=config.gemini_model_id,
                                 outfile_path=outpath,
                                 intermediate_dir=config.temp_dir,
                                 case_ids=config.case_ids if hasattr(config, 'case_ids') else None,
                                 debug=False)
    write_log("PROCESS COMPLETE")
    print("\n Digitizing task complete !! ")

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------


if __name__ == "__main__":
    main()
