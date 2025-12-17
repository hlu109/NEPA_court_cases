"""
API interaction utilities for CourtListener
"""

import requests
import time
from typing import Dict, List, Optional, Any
from analysis.utils.config import API_KEY, BASE_URL, REQUEST_DELAY, TIMEOUT


def _get_headers(api_key: str = API_KEY) -> Dict[str, str]:
    """ Get request headers with API authentication

        Args:
            api_key: CourtListener API key

        Returns:
            Dictionary of headers
    """
    return {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }


def _make_request(
        endpoint: str, params: Optional[Dict] = None, api_key: str = API_KEY) -> Dict:
    """ Make API request with error handling. 

        Args:
            endpoint: API endpoint (e.g., '/search/')
            params: Query parameters
            api_key: CourtListener API key

        Returns:
            JSON response as dictionary
    """
    # Build URL and avoid double slashes
    url = f"{BASE_URL}{endpoint}"
    if not endpoint.startswith('/'):
        url = f"{BASE_URL}/{endpoint}"

    try:
        response = requests.get(
            url,
            headers=_get_headers(api_key),
            params=params,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {response.text}")
        raise
    except requests.exceptions.Timeout:
        print(f"Request timed out after {TIMEOUT} seconds")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise


def get_search_cases(query: str,
                     result_type: str = 'o',
                     page: int = 1,
                     api_key: str = API_KEY) -> Dict:
    """ Make request to Search API for court cases. 

        Args:
            query: Search query text
            result_type: Type of search. Options:
                * "o": Case law opinion clusters with nested Opinion documents.
                * "r": List of Federal cases (dockets) with up to three nested 
                        documents.
                * "rd": Federal filing documents from PACER.
                * "d": Federal cases (dockets) from PACER.
                * "p": Judges.
                * "oa": Oral argument audio files.
            page: Page number (default 1)
            api_key: CourtListener API key

        Returns:
            Dictionary with search results
    """
    params = {
        'q': query,
        'type': result_type,
        'format': 'json',
        'page': page
    }

    return _make_request('/search/', params, api_key)


def get_opinion_by_id(opinion_id: int, api_key: str = API_KEY) -> Dict:
    """
    Retrieve a specific opinion by ID

    Args:
        opinion_id: Opinion ID number
        api_key: CourtListener API key

    Returns:
        Dictionary with opinion data
    """
    endpoint = f'/opinions/{opinion_id}/'
    params = {'format': 'json'}
    return _make_request(endpoint, params, api_key)


def get_all_results(query: str,
                    max_results: Optional[int] = None,
                    result_type: str = 'o',
                    api_key: str = API_KEY,
                    **kwargs) -> List[Dict]:
    """ Fetch all pages of results for a query. 

        Args:
            query: Search query
            max_results: Maximum number of results to fetch (None = all)
            result_type: Type of search (see get_search_cases() function for options)
            api_key: CourtListener API key
            **kwargs: Additional search parameters (will be added to params)

        Returns:
            List of all results across pages
    """
    all_results = []
    page = 1

    while True:
        print(f"Fetching page {page}...")

        response = get_search_cases(query, result_type=result_type,
                                    page=page, api_key=api_key)
        results = response.get('results', [])
        all_results.extend(results)

        # Check stopping conditions
        if not response.get('next'):
            print(f"Reached end at page {page}")
            break

        if max_results and len(all_results) >= max_results:
            all_results = all_results[:max_results]
            print(f"Reached max_results limit: {max_results}")
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    print(f"Total results fetched: {len(all_results)}")
    return all_results


def download_opinion_pdf(download_url: str, save_path: str) -> bool:
    """ Download opinion PDF from URL.

        Args:
            download_url: URL to PDF
            save_path: Local path to save PDF

        Returns:
            True if successful, False otherwise
    """
    try:
        response = requests.get(download_url, timeout=TIMEOUT)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            f.write(response.content)

        return True

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return False
