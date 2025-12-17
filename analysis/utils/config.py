"""
Configuration file for CourtListener API project
"""

from pathlib import Path


# Directory Structure
BASE_DIR = Path(
    "C:/Users/hl2266/YLS Dropbox/Hannah Lu/Judge Highway NEPA Costs/Code/NEPA_court_cases")
DATA_DIR = BASE_DIR / "data"
METADATA_DIR = DATA_DIR / "metadata"
TEXT_DIR = DATA_DIR / "opinions" / "text"
PDF_DIR = DATA_DIR / "opinions" / "pdf"
LOGS_DIR = DATA_DIR / "logs"

# API Configuration
API_KEY_PATH = BASE_DIR / "secret" / "courtlistener_api_key.txt"
with open(API_KEY_PATH) as f:
    API_KEY = f.read().strip()

BASE_PDF_URL = "https://storage.courtlistener.com"
BASE_API_URL = "https://www.courtlistener.com/api/rest/v3"

# API Settings
RESULTS_PER_PAGE = 20  # TODO: don't think we can specify this?
REQUEST_DELAY = 0.5  # seconds between requests (be nice to the API)
TIMEOUT = 30  # seconds


def setup_directories():
    """Create project directory structure"""
    directories = [
        BASE_DIR,
        DATA_DIR,
        METADATA_DIR,
        TEXT_DIR,
        PDF_DIR,
        LOGS_DIR
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
