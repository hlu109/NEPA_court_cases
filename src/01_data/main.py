"""
Main workflow to download CourtListener cases. 
"""

# TODO: handle HTTP Error: 429 Client Error: Too Many Requests for url somewhere with a reattempt 
# parse error message: eg {"detail":"Request was throttled. Expected available in 275 seconds."} 
# also retry request for 502 errors 

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd

# Add project root to Python path to allow imports from src.utils
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.courtlistener_utils import save_complete_dataset, get_all_results
from src.utils import config


def search_and_download(query: str,
                        max_results: Optional[int] = None,
                        result_type: str = "o",
                        court: Optional[str] = None,
                        highlight: Optional[str] = None,
                        download_opinions: bool = False):
    """ Search cases, save metadata/crosswalks, and optionally download opinion documents.

        Args:
            query: Search query
            max_results: Maximum number of results to fetch
            result_type: Type of search (see get_search_cases() function for options)
            court: Optional court code filter (e.g., 'ca9', 'ca2')
            highlight: Optional highlight parameter for search results
            download_opinions: Whether to download opinion files (both HTML and PDFs)

        Outputs:
            Creates directory: data/run_{timestamp}/

            Files saved in run directory:
            - cluster_metadata.csv: Cluster-level metadata
            - cluster_opinion_crosswalk.csv: Cluster→Opinion mapping with opinion types
            - cluster_docket_crosswalk.csv: Cluster→Docket mapping with docket numbers
            - opinion_metadata.csv: Individual opinion metadata
            - docket_metadata.csv: Individual docket metadata
            - complete_metadata.json: Complete JSON backup with nested structures
            - log.txt: Log file of activity and errors
            - opinions/: Directory with opinion HTML/PDFs (if download_opinions=True)
              - opinion_{id}/: Subdirectories for each opinion
                - opinion_{id}.html
                - opinion_{id}.pdf

            Returns dictionary of saved file paths.
    """
    logger = get_logger()

    logger.info("Starting API data pull")
    logger.info(f"Run directory: {config.RUN_DIR}")
    logger.info(f"Query: {query}")
    logger.info(f"Max results: {max_results}")
    if court:
        logger.info(f"Court: {court}")
    logger.info(f"Download opinions: {download_opinions}")

    try:
        # Search and collect results
        logger.info("=" * 60)
        logger.info("Pulling opinion clusters from Search API...")
        results = get_all_results(query=query,
                                  max_results=max_results,
                                  result_type=result_type,
                                  highlight=highlight,
                                  court=court)

        logger.info(f"Found {len(results)} opinion clusters.")

        saved_files = save_complete_dataset(results,
                                            download_opinions=download_opinions)

        logger.info("All saved files:")
        for file_type, path in saved_files.items():
            logger.info(f"  - {file_type}: {path}")

        return saved_files

    except Exception as e:
        logger.critical("Error in search_and_download()",
                        exception=e,
                        query=query,
                        max_results=max_results,
                        result_type=result_type,
                        download_opinions=download_opinions)
        raise


if __name__ == "__main__":
    script_start_time = datetime.now()

    try:
        config.setup_directories()
        logger = get_logger()
        logger.info("="*60)
        logger.info("NEPA CourtListener Data Pull")
        logger.info("="*60)

        saved_files = search_and_download(
            query="\"National Environmental Policy Act\"",
            result_type="o",
            highlight="on",
            court="(ca1 OR ca2 OR ca3 OR ca4 OR ca5 OR ca6 OR ca7 OR ca8 OR ca9 OR ca10 OR ca11 OR cadc OR cafc OR scotus)",
            # max_results=3229,
            # max_results=5,
            max_results=None,
            download_opinions=False
        )

        runtime = datetime.now() - script_start_time
        logger.info(f"Total script runtime: {runtime}")
        logger.print_summary()

    except KeyboardInterrupt:
        logger = get_logger()
        logger.critical("Script interrupted by user")
        logger.print_summary()
        raise
    except Exception as e:
        logger = get_logger()
        logger.critical("Fatal error in main script", exception=e)
        logger.print_summary()
        raise
