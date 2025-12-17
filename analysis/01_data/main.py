"""
Main workflow to download CourtListener cases. 
"""

import sys
from pathlib import Path
from time import time
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.utils import config
from analysis.utils.api_utils import get_all_results
from analysis.utils.storage_utils import save_complete_dataset
from analysis.utils.data_utils import flatten_metadata


def search_and_download(query: str,
                        max_results: int = 100,
                        # court: str = None,
                        download_pdfs: bool = True):
    """ Search cases, save metadata, and download opinions.

        Args:
            query: Search query
            max_results: Maximum number of results to fetch
            court: Optional court code filter
            download_pdfs: Whether to download PDFs

        Outputs:
            Returns dataFrame with flattened metadata. 
            Also saves metadata files and downloads opinions locally.
    """
    print(f"Query: {query}")
    print(f"Max results: {max_results}")
    # if court:
    #     print(f"Court: {court}")
    # print(f"{'='*60}\n")

    # Search and collect results
    print("Searching for opinions...")
    results = get_all_results(
        query=query,
        max_results=max_results,
        # court=court,
    )

    print(f"Found {len(results)} opinions.")

    # Save complete dataset
    print("Saving metadata and downloading opinions...")
    saved_files = save_complete_dataset(results, download_opinions=True)

    print("Data saved:")
    for file_type, path in saved_files.items():
        print(f"  - {file_type}: {path}")

    # Return flattened DataFrame for immediate analysis
    df = flatten_metadata(results)
    return df


if __name__ == "__main__":
    # add timer to see how long script takes
    script_start_time = time.time()

    config.setup_directories()

    df = search_and_download(
        query="\"National Environmental Policy Act\"",
        max_results=20,
        download_pdfs=True
    )

    print(
        f"Total script runtime: {time.time() - script_start_time:.2f} seconds")
