"""
Main workflow to download CourtListener cases. 
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.utils import config
from analysis.utils.api_utils import get_all_results
from analysis.utils.storage_utils import save_complete_dataset
from analysis.utils.data_utils import flatten_metadata


def search_and_download(query: str,
                        max_results: Optional[int] = None,
                        result_type: str = "o",
                        court: Optional[str] = None,
                        highlight: Optional[str] = None,
                        download_pdfs: bool = True):
    """ Search cases, save metadata, and download opinions.

        Args:
            query: Search query
            max_results: Maximum number of results to fetch
            result_type: Type of search (see get_search_cases() function for options)
            court: Optional court code filter (e.g., 'ca9', 'ca2')
            highlight: Optional highlight parameter for search results
            download_pdfs: Whether to download PDFs

        Outputs:
            Returns dataFrame with flattened metadata. 
            Also saves metadata files and downloads opinions locally.
    """
    print(f"Query: {query}")
    print(f"Max results: {max_results}")
    if court:
        print(f"Court: {court}")
    print(f"{'='*60}\n")

    # Search and collect results
    print("Searching for opinions...")
    results = get_all_results(
        query=query,
        max_results=max_results,
        result_type=result_type,
        highlight=highlight,
        court=court
    )

    print(f"Found {len(results)} opinions.")

    # Save complete dataset
    print("Saving metadata and downloading opinions...")
    saved_files = save_complete_dataset(results, download_opinions=download_pdfs)

    print("Data saved:")
    for file_type, path in saved_files.items():
        print(f"  - {file_type}: {path}")

    # Return flattened DataFrame for immediate analysis
    df = flatten_metadata(results)
    return df


if __name__ == "__main__":
    # add timer to see how long script takes
    script_start_time = datetime.now()

    config.setup_directories()

    df = search_and_download(
        query="\"National Environmental Policy Act\"",
        result_type="o",
        highlight="on",
        court="(ca1 OR ca2 OR ca3 OR ca4 OR ca5 OR ca6 OR ca7 OR ca8 OR ca9 OR ca10 OR ca11 OR cadc OR cafc OR scotus)",
        max_results=3229, # 3229
        download_pdfs=True
    )
    # TODO: update to download pdfs in batches 

    print(
        f"Total script runtime: {datetime.now() - script_start_time}")
