# NEPA Court Cases

A project for downloading and analyzing court cases related to the National Environmental Policy Act (NEPA) from CourtListener.

## Project Structure

```
NEPA_court_cases/
├── analysis/
│   ├── 01_data/              # Data collection scripts
│   │   └── main.py           # Main download script
│   ├── 02_analysis/          # Analysis scripts
│   └── utils/                # Utility modules
│       ├── api_utils.py      # CourtListener API functions
│       ├── config.py         # Configuration and paths
│       ├── data_utils.py     # Data processing utilities
│       └── storage_utils.py  # File storage utilities
├── data/
│   ├── opinions/             # Downloaded opinion files
│   │   └── run_YYYYMMDD_HHMMSS/  # Timestamped run directories
│   │       └── opinion_ID/       # Individual opinion folders
│   │           ├── opinion_ID.txt
│   │           └── opinion_ID.pdf
│   ├── metadata/             # Opinion metadata (CSV/JSON)
│   └── logs/                 # Download logs
└── secret/
    └── courtlistener_api_key.txt  # API key (not in git)
```

## File Organization

Each time you run `main.py`, a new timestamped directory is created under `data/opinions/`. Within that directory, each opinion gets its own folder containing all associated files (text and PDF).

Example:
```
data/opinions/run_20251218_150652/
  ├── opinion_1027273/
  │   ├── opinion_1027273.txt
  │   └── opinion_1027273.pdf
  └── opinion_1034773/
      ├── opinion_1034773.txt
      └── opinion_1034773.pdf
```

## Usage

### Running the Main Download Script

```bash
python analysis/01_data/main.py
```

This will:
1. Create a new timestamped run directory
2. Search for NEPA-related opinions on CourtListener
3. Download opinion metadata, text, and PDFs
4. Save logs and return a flattened DataFrame

### Configuration

Edit `analysis/utils/config.py` to set:
- Base directory paths
- API settings (timeout, delay between requests)
- Search parameters

### API Key

You need a CourtListener API key stored in `secret/courtlistener_api_key.txt`.
