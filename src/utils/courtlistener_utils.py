"""
CourtListener Data Utilities 
"""

import json
import csv
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from src.utils.config import METADATA_DIR, TEXT_DIR, PDF_DIR, LOGS_DIR, REQUEST_DELAY, BASE_PDF_URL
from src.utils.api_utils import get_opinion_by_id, download_opinion_pdf



def get_timestamp() -> str:
    """Get current timestamp string for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


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
        filename = f"opinions_metadata_{get_timestamp()}.csv"

    filepath = METADATA_DIR / filename

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not results:
        print("Warning: No results to save")
        return str(filepath)

    # Get all unique keys across all results
    all_keys = set()
    for result in results:
        all_keys.update(result.keys())

    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
        writer.writeheader()

        for result in results:
            # Convert lists/dicts to JSON strings for CSV compatibility
            row = {}
            for key, value in result.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = value
            writer.writerow(row)

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
        filename = f"opinions_metadata_{get_timestamp()}.json"

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


def save_opinion_text(opinion_id: int, text: str) -> str:
    """
    Save opinion text to file

    Args:
        opinion_id: Opinion ID
        text: Plain text content

    Returns:
        Path to saved file
    """
    filename = f"opinion_{opinion_id}.txt"
    filepath = TEXT_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

    return str(filepath)


class DownloadLogger:
    """Logger for tracking download progress and errors"""

    def __init__(self, log_filename: Optional[str] = None):
        if not log_filename:
            log_filename = f"download_log_{get_timestamp()}.txt"

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

    # print(len(metadata))

    # for metadata in results:

    for i, item in enumerate(metadata, 1):
        # print(item)
        opinion_id = item.get('opinions')[0].get('id')

        if not opinion_id:
            print(f"Skipping item {i}: no opinion ID found")
            continue

        print(f"[{i}/{len(metadata)}] Downloading opinion {opinion_id}...")

        try:
            # Get full opinion data
            opinion_data = get_opinion_by_id(opinion_id)

            # Save plain text
            if opinion_data.get('plain_text'):
                save_opinion_text(opinion_id, opinion_data['plain_text'])

            # Save PDF if requested
            if download_pdfs and opinion_data.get('download_url'):
                pdf_url = f"{BASE_PDF_URL}/{opinion_data['local_path']}"
                print(pdf_url)
                if download_opinion_pdf(pdf_url, PDF_DIR / f"opinion_{opinion_id}.pdf"):
                    logger.log_success(opinion_id, "Text and PDF saved")
                else:
                    logger.log_success(opinion_id, "Text saved (PDF failed)")
            else:
                logger.log_success(opinion_id, "Text saved")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            logger.log_failure(opinion_id, str(e))
            print(f"  ✗ Error: {e}")

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

        # Handle nested 'opinions' field if it exists
        if 'opinions' in item and isinstance(item['opinions'], dict):
            opinion = item['opinions'][0]  # assuming first opinion
            # TODO: add handling for if there are 0 or multiple opinions

            # Extract key opinion fields
            flat_item['opinion_id'] = opinion.get('id')
            flat_item['author_id'] = opinion.get('author_id')
            flat_item['download_url'] = opinion.get('download_url')
            flat_item['local_path'] = opinion.get('local_path')


            # Convert lists to comma-separated strings or counts
            if 'joined_by_ids' in opinion and opinion['joined_by_ids']:
                flat_item['joined_by_ids'] = ','.join(
                    map(str, opinion['joined_by_ids']))
                flat_item['num_joined_by'] = len(opinion['joined_by_ids'])

            if 'cites' in opinion and opinion['cites']:
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

    # Convert date columns to datetime
    date_columns = ['date_filed', 'dateFiled']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df

