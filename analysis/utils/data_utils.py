"""
Data processing and transformation utilities
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime


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

