"""
Download opinions from a CSV file

This script allows you to download opinion HTML/PDFs based on a CSV file
containing opinion IDs. It will skip opinions that have already been downloaded.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import config
from src.utils.courtlistener_utils import download_opinions_from_csv


def main(csv_path: str,
         opinion_id_column: str = 'opinion_id',
         use_existing_run_dir: Optional[str] = None,
         check_existing_downloads_dir: Optional[str] = None):
    """
    Download opinions from CSV file

    Args:
        csv_path: Path to CSV file containing opinion IDs
        opinion_id_column: Name of column with opinion IDs (default: 'opinion_id')
        use_existing_run_dir: Add downloads to this existing run directory (e.g., 'data/run_20250109_120000')
                             If None, creates new run_TIMESTAMP directory
        check_existing_downloads_dir: Directory to check for existing downloads to skip
                                      (typically 'data/run_XXXXX/opinions' from a previous run)
    """
    script_start_time = datetime.now()

    config.setup_directories()

    # Determine output directory
    if use_existing_run_dir:
        output_dir = Path(use_existing_run_dir) / "opinions"
        print(f"Adding downloads to existing run directory: {use_existing_run_dir}")
    else:
        # Create new run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = config.DATA_DIR / f"run_{timestamp}" / "opinions"
        print(f"Creating new run directory: {output_dir.parent}")

    # Convert existing downloads path if provided
    existing_path = Path(check_existing_downloads_dir) if check_existing_downloads_dir else None

    print(f"CSV file: {csv_path}")
    print(f"Opinion ID column: {opinion_id_column}")
    print(f"Output directory: {output_dir}")
    print(f"Check for existing downloads in: {existing_path or 'None'}")
    print(f"{'='*60}\n")

    download_opinions_from_csv(
        csv_path=csv_path,
        opinion_id_column=opinion_id_column,
        output_dir=output_dir,
        existing_downloads_dir=existing_path
    )

    print(f"\nTotal script runtime: {datetime.now() - script_start_time}")


if __name__ == "__main__":
    # Example usage - customize these parameters

    # Download to a NEW run directory
    main(
        csv_path="data/run_20250109_120000/cluster_opinion_crosswalk.csv",  # TODO: update 
        opinion_id_column='opinion_id',
        use_existing_run_dir=None, # TODO: get rid of this for sake of transparency
        check_existing_downloads_dir="data/run_20250109_120000/opinions",  # optional - skip already-downloaded
    )