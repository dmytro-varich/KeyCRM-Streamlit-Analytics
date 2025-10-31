import requests
from typing import Any, Dict, List, Optional

def get_n8n_webhook_data(webhook_url: str) -> Optional[List[Dict[str, Any]]]:
    try:
        response = requests.get(webhook_url, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from n8n webhook: {e}")
        return None