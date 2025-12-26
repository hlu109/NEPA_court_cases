"""
API interaction utilities for CourtListener
"""

import requests
import time
from typing import Dict, List, Optional, Any
from src.utils.config import API_KEY, BASE_API_URL, REQUEST_DELAY, TIMEOUT


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
        endpoint: str, params: Optional[Dict] = None, 
        full_url: Optional[str] = None,
        api_key: str = API_KEY
        ) -> Dict:
    """ Make API request with error handling. 

        Args:
            endpoint: API endpoint (e.g., '/search/')
            params: Query parameters
            api_key: CourtListener API key
            full_url: Optional full URL to use instead of constructing from endpoint

        Returns:
            JSON response as dictionary
    """
    # Use full URL if provided, otherwise build from endpoint
    if full_url:
        url = full_url
    else:
        # Build URL and avoid double slashes
        url = f"{BASE_API_URL}{endpoint}"
        if not endpoint.startswith('/'):
            url = f"{BASE_API_URL}/{endpoint}"

    try:
        response = requests.get(
            url,
            headers=_get_headers(api_key),
            params=params if not full_url else None,  # Don't use params with full_url
            timeout=TIMEOUT
        )
        # print("Request URL:", response.url)
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
                     api_key: str = API_KEY,
                     highlight: Optional[str] = None,
                     court: Optional[str] = None) -> Dict:
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
            api_key: CourtListener API key
            highlight: Optional highlight parameter for search results. 
                Use "on" or "all" to enable highlighting of search terms in results.
            court: Optional court code filter (e.g., 'ca9', 'ca2')

        Returns:
            Dictionary with search results
    """
    params = {
        'q': query,
        'type': result_type,
        'format': 'json'
    }
    if highlight is not None:
        params['highlight'] = highlight
    
    if court is not None:
        params['court'] = court

    return _make_request('/search/', params=params, api_key=api_key)


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
    return _make_request(endpoint=endpoint, params=params, api_key=api_key)

def get_cluster_by_id(cluster_id: int, api_key: str = API_KEY) -> Dict:
    """
    Retrieve a specific cluster by ID

    Args:
        cluster_id: Cluster ID number
        api_key: CourtListener API key

    Returns:
        Dictionary with cluster data
    """
    endpoint = f'/clusters/{cluster_id}/'
    params = {'format': 'json'}
    return _make_request(endpoint=endpoint, params=params, api_key=api_key)

def get_all_results(query: str,
                    max_results: Optional[int] = None,
                    result_type: str = 'o',
                    api_key: str = API_KEY,
                    highlight: Optional[str] = None,
                    court: Optional[str] = None,
                    **kwargs) -> List[Dict]:
    """ Fetch all pages of results for a query. 

        Args:
            query: Search query
            max_results: Maximum number of results to fetch (None = all)
            result_type: Type of search (see get_search_cases() function for options)
            api_key: CourtListener API key
            highlight: Optional highlight parameter for search results.
                Use "on" to enable highlighting of search terms in result snippet.
            court: Optional court code filter (e.g., 'ca9', 'ca2')
            **kwargs: Additional search parameters (will be added to params)

        Returns:
            List of all results across pages
    """
    all_results = []
    page = 1
    next_url = None

    while True:
        print(f"Fetching page {page}...")

        # Use next_url if available, otherwise make initial request
        if next_url is not None:
            response = _make_request(endpoint='', params=None, api_key=api_key, full_url=next_url)
        else:
            response = get_search_cases(query, result_type=result_type,
                                        api_key=api_key, highlight=highlight,
                                        court=court)
        results = response.get('results', [])
        all_results.extend(results)

        # Check stopping conditions
        next_url = response.get('next')
        if not next_url:
            print(f"Reached end at page {page}")
            break

        if max_results and len(all_results) >= max_results:
            all_results = all_results[:max_results]
            print(f"Reached max_results limit: {max_results}")
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    print(f"Total results fetched: {len(all_results)}")

    # add a column to check if html_with_citations is populated; if local_path pdf link is available; if harvard pdf link is available 
    for result in all_results:
        opinion_metadata = result.get('opinions', [{}])[0]
        opinion_id = opinion_metadata.get('id')
        cluster_id = result.get('cluster_id')
        opinion = get_opinion_by_id(opinion_id, api_key)
        cluster = get_cluster_by_id(cluster_id, api_key)

        result['has_html_with_citations'] = bool(opinion.get('html_with_citations')) & (opinion.get('html_with_citations') != "")
        result['pdf_local_path'] = opinion.get('local_path') 
        result['pdf_harvard_path'] = cluster.get('filepath_pdf_harvard') 

    return all_results


def download_opinion_pdf(download_url: str, save_path: str) -> bool:
    """ Download opinion PDF from URL.

        Args:
            download_url: URL to PDF
            save_path: Local path to save PDF

        Returns:
            True if successful, False otherwise
    """
    # TODO: replace download url with local url from CourListener API response
    try:
        response = requests.get(download_url, timeout=TIMEOUT)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"PDF saved to {save_path}")

        return True

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return False
