"""
Data processing, storage, and file I/O utilities
"""

import json
import csv
import time
import pandas as pd
import warnings 
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from analysis.utils.config import METADATA_DIR, LOGS_DIR, REQUEST_DELAY, BASE_PDF_URL, CURR_OPINIONS_DIR, RUN_TIMESTAMP
from analysis.utils.api_utils import get_opinion_by_id, get_cluster_by_id, download_opinion_pdf


def save_metadata_csv(results: List[Dict],
                      filename: Optional[str] = None) -> str:
    """
    Save metadata to CSV file

    Args:
        results: List of opinion dictionaries
        filename: Optional custom filename (will auto-generate if None)

    Returns:
        Path to saved file
    """
    if not filename:
        filename = f"opinions_metadata_{RUN_TIMESTAMP}.csv"

    filepath = METADATA_DIR / filename

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not results:
        print("Warning: No results to save")
        return str(filepath)

    # Convert to flattened structure 
    df = flatten_metadata(results)

    # Write CSV
    df.to_csv(filepath, index=False, quoting=csv.QUOTE_NONNUMERIC)

    print(f"Saved {len(results)} records to: {filepath}")
    return str(filepath)


def save_metadata_json(results: List[Dict],
                       filename: Optional[str] = None) -> str:
    """
    Save metadata to JSON file (preserves nested structures)

    Args:
        results: List of opinion dictionaries
        filename: Optional custom filename

    Returns:
        Path to saved file
    """
    if not filename:
        filename = f"opinions_metadata_{RUN_TIMESTAMP}.json"

    filepath = METADATA_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(results)} records to: {filepath}")
    return str(filepath)


def load_metadata_json(filename: str) -> List[Dict]:
    """
    Load metadata from JSON file

    Args:
        filename: Name of JSON file in metadata directory

    Returns:
        List of opinion dictionaries
    """
    filepath = METADATA_DIR / filename

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_opinion_text(opinion_id: int, text: str, save_path) -> str:
    """
    Save opinion text to file

    Args:
        opinion_id: Opinion ID
        text: HTML text content

    Returns:
        Path to saved file
    """
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(text)

    return str(save_path)


class DownloadLogger:
    """Logger for tracking download progress and errors"""

    def __init__(self, log_filename: Optional[str] = None):
        if not log_filename:
            log_filename = f"download_log_{RUN_TIMESTAMP}.txt"

        self.log_path = LOGS_DIR / log_filename
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.successful = 0
        self.failed = 0
        self.errors = []

    def log_success(self, opinion_id: int, message: str = ""):
        """Log successful download"""
        self.successful += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] SUCCESS: Opinion {opinion_id}"
        if message:
            log_entry += f" - {message}"

        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def log_failure(self, opinion_id: int, error: str):
        """Log failed download"""
        self.failed += 1
        self.errors.append((opinion_id, error))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] FAILED: Opinion {opinion_id} - {error}"

        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def print_summary(self):
        """Print download summary"""
        print("\n" + "="*50)
        print("DOWNLOAD SUMMARY")
        print("="*50)
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Total: {self.successful + self.failed}")
        print(f"Log saved to: {self.log_path}")

        if self.errors:
            print(f"\nFirst 5 errors:")
            for opinion_id, error in self.errors[:5]:
                print(f"  - Opinion {opinion_id}: {error}")


def download_all_opinions(metadata: List[Dict],
                          download_pdfs: bool = True) -> DownloadLogger:
    """
    Download text and PDFs for all opinions in metadata

    Args:
        metadata: List of opinion metadata dictionaries
        download_pdfs: Whether to download PDFs (default True)

    Returns:
        DownloadLogger with results
    """
    logger = DownloadLogger()

    print(f"Starting download of {len(metadata)} opinions...")
    print(f"PDF download: {'enabled' if download_pdfs else 'disabled'}")
    print(f"Saving to: {CURR_OPINIONS_DIR}")

    # print(len(metadata))

    # for metadata in results:

    for i, item in enumerate(metadata, 1):
        # print(item)
        opinion_id = item.get('opinions')[0].get('id')

        if not opinion_id:
            print(f"Skipping item {i}: no opinion ID found")
            continue

        print(f"[{i}/{len(metadata)}] Downloading opinion {opinion_id}...")

        # Create opinion-specific directory
        opinion_dir = CURR_OPINIONS_DIR / f"opinion_{opinion_id}"
        opinion_dir.mkdir(parents=True, exist_ok=True)
        print("opinion directory created:", opinion_dir)

        try:
            # Get full opinion data
            opinion_data = get_opinion_by_id(opinion_id)

            # Save text (via HTML with citations field, which is recommended over plain text)
            if opinion_data.get('html_with_citations'):
                text = opinion_data['html_with_citations']
                if text == "":
                    warnings.warn(f"Empty 'html_with_citations' for opinion {opinion_id}")
                html_path = opinion_dir / f"opinion_{opinion_id}.html"

                save_opinion_text(opinion_id, text, html_path)

            # Save PDF if requested
            if download_pdfs:
                # get pdf url from results pdf_local_path or pdf_harvard_path
                pdf_url = ""
                if item.get('pdf_local_path'):
                    pdf_url = f"{BASE_PDF_URL}/{item.get('pdf_local_path')}"
                elif item.get('pdf_harvard_path'):
                    # if there is no local pdf path, then check if the case was hosted on harvard's system 
                    pdf_url = f"{BASE_PDF_URL}/{item['pdf_harvard_path']}"
                else:
                    warnings.warn(f"no local pdf path found and no harvard pdf path found for opinion {opinion_id}, skipping pdf download")
                    logger.log_success(opinion_id, "Text saved but no PDF available")
                
                if pdf_url != "":
                    print(pdf_url)
                    pdf_path = opinion_dir / f"opinion_{opinion_id}.pdf"
                    if download_opinion_pdf(pdf_url, pdf_path):
                        logger.log_success(opinion_id, "Text and PDF saved")
                    else:
                        logger.log_success(opinion_id, "Text saved (PDF failed)")
            else:
                logger.log_success(opinion_id, "Text saved")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            logger.log_failure(opinion_id, str(e))
            print(f"  Error: {e}")

    logger.print_summary()
    return logger


def save_complete_dataset(results: List[Dict],
                          download_opinions: bool = True) -> Dict[str, str]:
    """
    Save complete dataset: metadata + opinion text/PDFs

    Args:
        results: List of opinion metadata
        download_opinions: Whether to download full opinion text/PDFs

    Returns:
        Dictionary with paths to saved files
    """
    saved_files = {}

    # Save metadata in both formats
    saved_files['csv'] = save_metadata_csv(results)
    saved_files['json'] = save_metadata_json(results)

    # Download opinions if requested
    if download_opinions:
        logger = download_all_opinions(results)
        saved_files['log'] = str(logger.log_path)
        saved_files['run_dir'] = str(CURR_OPINIONS_DIR)

    return saved_files


def flatten_metadata(results: List[Dict]) -> pd.DataFrame:
    """
    Flatten nested metadata structures for easier analysis

    Args:
        results: List of opinion dictionaries from API

    Returns:
        Pandas DataFrame with flattened data
    """
    flattened = []

    for item in results:
        flat_item = {}

        # Copy simple fields
        for key, value in item.items():
            if not isinstance(value, (dict, list)):
                flat_item[key] = value

        # Flatten all the columns that are lists
        if 'citation' in item and isinstance(item['citation'], list):
            flat_item['citation'] = '; '.join(item['citation'])
        if 'non_participating_judge_ids' in item and isinstance(item['non_participating_judge_ids'], list):
            flat_item['non_participating_judge_ids'] = '; '.join(
                map(str, item['non_participating_judge_ids']))
        if 'panel_ids' in item and isinstance(item['panel_ids'], list):
            flat_item['panel_ids'] = '; '.join(
                map(str, item['panel_ids']))
        if 'panel_names' in item and isinstance(item['panel_names'], list):
            flat_item['panel_names'] = '; '.join(item['panel_names'])
        if 'sibling_ids' in item and isinstance(item['sibling_ids'], list):
            flat_item['sibling_ids'] = '; '.join(
                map(str, item['sibling_ids']))


        # Flatten the "meta" field which is a dictionary 
        if 'meta' in item and isinstance(item['meta'], dict):
            for meta_key, meta_value in item['meta'].items():
                if meta_key == 'score' and isinstance(meta_value, dict):
                    for score_key, score_value in meta_value.items():
                        flat_item[f"meta_score_{score_key}"] = score_value
                else:
                    flat_item[f"meta_{meta_key}"] = meta_value
                    # parse meta_score which is another nested dict 


        # Handle nested 'opinions' field if it exists, which is a list of dicts 
        # TODO: add handling for if there are multiple opinions
        opinion = None
        if 'opinions' in item and isinstance(item['opinions'], list):
            if len(item['opinions']) > 1:
                warnings.warn(f"Found multiple 'opinions' field for case {item.get('absolute_url')}")
            opinion = item['opinions'][0]  # assuming first opinion
        elif 'opinion' in item:
            print("Found 'opinion' field of class:", type(item['opinion']))
            if isinstance(item['opinion'], dict):
                opinion = item['opinion']  # TODO check, but it seemed like there was a different data structure here if you only pulled the first page of results
        if opinion is not None:
            # Extract key opinion fields
            flat_item['opinion_id'] = opinion.get('id')
            flat_item['author_id'] = opinion.get('author_id')
            flat_item['pdf_original_path'] = opinion.get('download_url')
            # flat_item['pdf_local_path'] = opinion.get('local_path') # already handled when retrieving results
            flat_item['per_curiam'] = opinion.get('per_curiam')
            flat_item['snippet'] = opinion.get('snippet')
            flat_item['opinion_type'] = opinion.get('type')

            # Flatten lists
            if 'joined_by_ids' in opinion and opinion['joined_by_ids']:
                flat_item['joined_by_ids'] = '; '.join(
                    map(str, opinion['joined_by_ids']))
                flat_item['num_joined_by'] = len(opinion['joined_by_ids'])

            if 'cites' in opinion and opinion['cites']:
                flat_item['cites'] = '; '.join(
                    map(str, opinion['cites']))
                flat_item['num_citations'] = len(opinion['cites'])
            else:
                flat_item['num_citations'] = 0

        # Handle 'cluster' field if it exists
        if 'cluster' in item and isinstance(item['cluster'], dict):
            cluster = item['cluster']
            flat_item['cluster_id'] = cluster.get('id')
            flat_item['case_name'] = cluster.get('case_name')
            flat_item['date_filed'] = cluster.get('date_filed')

        flattened.append(flat_item)

    df = pd.DataFrame(flattened)
    df = df.reindex(sorted(df.columns), axis=1) # rearrange columns in alphabetical order

    # Convert date columns to datetime
    date_columns = ['date_filed', 'dateFiled']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df

