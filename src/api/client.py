
import requests
from typing import Optional, Dict, Any, List
from config.settings import API_BASE_URL, KEYCRM_API_KEY, TIMEOUT, API_CARDS_ENDPOINT

class ApiClient:
    """
    KeyCRM API client for working with cards, calls, and pipelines.
    """
    def __init__(self) -> None:
        """
        Initialize KeyCRM API client.
        Args:
            api_key (str, optional): API key for authentication. If None, uses key from settings.
        """
        self.base_url: str = API_BASE_URL
        self.api_key: str = KEYCRM_API_KEY
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def fetch_cards_by_ids(self, card_ids: List[int], include: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch cards by a list of IDs.
        Args:
            card_ids (List[int]): List of card IDs to fetch.
            include (str, optional): Include string for related fields (e.g. 'contact.client,products').
        Returns:
            dict: {"error": bool, "data": list}
        """
        results: List[Dict[str, Any]] = []
        try:
            for card_id in card_ids:
                query_params: Dict[str, Any] = {}
                if include:
                    query_params['include'] = include
                url: str = f"{self.base_url}{API_CARDS_ENDPOINT}/{card_id}"
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=query_params,
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                card_data = response.json()

                if 'data' in card_data:
                    results.append(card_data['data'])
                else:
                    results.append(card_data)
            return {"error": False, "data": results}
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": f"Error fetching cards by IDs: {str(e)}",
                "data": []
            }
    
    def fetch_calls(
        self,
        limit: int = 15,
        page: int = 1,
        include: str = "",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch a list of calls with pagination and filtering support.
        Args:
            limit (int): Number of calls per page.
            page (int): Page number.
            include (str): Include string for related fields.
            filters (dict, optional): Additional filters for API.
        Returns:
            dict: API response with call data.
        """
        url: str = f"{self.base_url}/calls"
        params: Dict[str, Any] = {
            "limit": limit,
            "page": page
        }
        if include:
            params["include"] = include
        if filters:
            for key, value in filters.items():
                params[f"filter[{key}]"] = value

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": f"Error fetching calls: {str(e)}",
                "data": []
            }

    def fetch_all_calls(
        self,
        date: Optional[str],
        filters: Optional[Dict[str, Any]] = None,
        max_calls: int = 500,
        include: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Fetch all calls with pagination and date filtering.
        Args:
            date (str, optional): Date in 'YYYY-MM-DD' format for filtering calls.
            filters (dict, optional): Additional filters for API.
            max_calls (int): Maximum number of calls to fetch.
            include (str): Include string for related fields (manager, service, lead, client).
        Returns:
            list: List of calls for the specified date.
        """
        all_calls: List[Dict[str, Any]] = []
        page: int = 1
        limit: int = 50  # Maximum for KeyCRM API according to docs

        # If date is provided, create filters for the range
        if date:
            if filters is None:
                filters = {}
            # Filter by range: from start to end of day
            filters['created_between'] = f"{date} 00:00:00, {date} 23:59:59"

        while len(all_calls) < max_calls:
            response = self.fetch_calls(
                limit=limit,
                page=page,
                include=include,
                filters=filters
            )

            if response.get('error'):
                print(f"Error on page {page}: {response.get('message')}")
                break

            data = response.get('data', [])
            if not data:
                break

            if date:
                filtered_data = [
                    call for call in data
                    if call.get('created_at', '')[:10] == date
                ]
                all_calls.extend(filtered_data)
            else:
                all_calls.extend(data)

            # Check if there are more pages
            current_page = response.get('current_page', page)
            total = response.get('total', 0)
            per_page = response.get('per_page', limit)
            last_page = (total + per_page - 1) // per_page  # Calculate last page

            if current_page >= last_page or len(all_calls) >= max_calls:
                break

            page += 1

        return all_calls[:max_calls]  # Trim to max_calls just in case

    def fetch_pipeline_statuses(self, pipeline_id: int) -> Dict[str, Any]:
        """
        Fetch statuses for a given pipeline_id.
        Args:
            pipeline_id (int): ID of the pipeline.
        Returns:
            dict: API response with statuses.
        """
        url: str = f"{self.base_url}/pipelines/{pipeline_id}/statuses"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": f"Error fetching statuses for pipeline {pipeline_id}: {str(e)}",
                "data": []
            }