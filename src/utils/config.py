"""
Configuration file for CourtListener API project
"""

from pathlib import Path
from datetime import datetime

################################################################################
# SET CODE LOCATION -----------------------------------------------------------

# loc = "yale_server"
loc = "local"

if loc == "local":
    BASE_DIR = Path(
        "C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Code/NEPA_court_cases")
elif loc == "yale_server":
    BASE_DIR = Path(
        "/home/hl2266/project_pi_zdl3/hl2266/code/NEPA_court_cases")
else:
    raise ValueError("Invalid location specified")

################################################################################
# DATA DIRECTORY --------------------------------------------------------------


# Data directory structure (separate from code directory)
if loc == "local":
    DATA_ROOT_DIR = Path(
        "C:/Users/hl2266/YLS Dropbox/Hannah Lu/NEPA Court Cases/Data/")
elif loc == "yale_server":
    pass # TODO: update 
else:
    raise ValueError("Invalid location specified")

# Raw and Intermediate data directories
RAW_DATA_DIR = DATA_ROOT_DIR / "Raw"
INTERMEDIATE_DATA_DIR = DATA_ROOT_DIR / "Intermediate"

# Raw data file paths
ADELGLICKS_RAW_PATH = RAW_DATA_DIR / "nepa_judicial/data/NEPA Lit Circuit WL Sample-Combo Supp-Coded Final 2001-15 2.7.24.xlsx"
ADELGLICKS_SHEET_NAME = "NEPA Circuit Data"
COURTLISTENER_METADATA_DIR = RAW_DATA_DIR / "CourtListener metadata"

# Output paths for cleaned datasets
CLEANED_DATASETS_DIR = INTERMEDIATE_DATA_DIR / "Cleaned Datasets"
ADELGLICKS_CLEANED_PATH = CLEANED_DATASETS_DIR / "AdelGlicks.csv"
COURTLISTENER_CLUSTER_CLEANED_PATH = CLEANED_DATASETS_DIR / "CourtListener/cluster_metadata.csv"
COURTLISTENER_AG_MATCH_STATS_PATH = INTERMEDIATE_DATA_DIR / "CL_AG_match_stats.txt"
COURTLISTENER_AG_MATCHING_PATH = INTERMEDIATE_DATA_DIR / "CL_AG_matching.csv"
COURTLISTENER_AG_MATCHING_SPLIT_PATH = INTERMEDIATE_DATA_DIR / "CL_AG_matched_val_test_assignments.csv"
OUTCOME_ASSIGNMENTS_DIR = INTERMEDIATE_DATA_DIR / "Outcome Coding Assignments"
AG_VAL_ASSIGNMENTS_PATH = OUTCOME_ASSIGNMENTS_DIR / "AG_val.csv"
AG_TEST_ASSIGNMENTS_PATH = OUTCOME_ASSIGNMENTS_DIR / "AG_test.csv"
CL_TRAIN_ASSIGNMENTS_PATH = OUTCOME_ASSIGNMENTS_DIR / "CL_train.csv"
OUTCOME_PREDICTIONS_DIR = INTERMEDIATE_DATA_DIR / "Outcome Coding Predictions"
CL_TRAIN_PREDICTIONS_PATH = OUTCOME_PREDICTIONS_DIR / "CL_train_predictions.csv"
LLM_OPINION_CODING_RAW_PATH = INTERMEDIATE_DATA_DIR / "gemini_output/opinions_20251219_110552_coding_20260102_165440/opinions_20251219_110552_coding_20260102_165440.csv"
LLM_OPINION_CODING_PATH = INTERMEDIATE_DATA_DIR / "gemini_output/opinions_20251219_110552_coding_20260102_165440/opinions_20251219_110552_coding_20260102_165440_district_flipped.csv"

################################################################################

# Set global timestamp for use as file/run identifier
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

################################################################################
# COURTLISTENER SETUP  --------------------------------------------------------

# CourtListener download structure 
DATA_DIR = BASE_DIR / "data" # TODO: we need to get rid of this variable and move courtlistener stuff to the actual data dir outside this git repository

RUN_DIR = DATA_DIR / f"run_{RUN_TIMESTAMP}"
CURR_OPINIONS_DIR = RUN_DIR / "opinions"


# API Configuration
API_KEY_PATH = BASE_DIR / "secret" / "COURTLISTENER_API_KEY.txt"
with open(API_KEY_PATH) as f:
    API_KEY = f.read().strip()

BASE_PDF_URL = "https://storage.courtlistener.com"
BASE_API_URL = "https://www.courtlistener.com/api/rest/v4"

# API Settings
REQUEST_DELAY = 0.5  # seconds between requests (be nice to the API)
TIMEOUT = 60  # seconds
RETRY_WAIT_TIME = 5  # seconds to wait before retrying on retryable errors
MAX_RETRIES = 3  # maximum number of retries for 502 and 429 errors


################################################################################

def setup_directories():
    """Create project directory structure"""
    directories = [
        BASE_DIR,
        DATA_DIR,
        RUN_DIR,
        CURR_OPINIONS_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Initialize global logger
    from src.utils.logger import Logger, set_logger
    logger = Logger(log_dir=RUN_DIR)
    set_logger(logger)
    logger.info("Logger initialized", run_dir=str(RUN_DIR))
