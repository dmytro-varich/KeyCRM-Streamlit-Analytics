from typing import List, Dict, Any, Optional, Tuple


def define_category(pipeline_id: int) -> Optional[str]:
    """
    Returns category name based on pipeline ID.
    Args:
        pipeline_id (int): Pipeline ID.
    Returns:
        str or None: Category name ('Алмази', 'Діаманти', 'Не Алмази') or None if not found.
    """
    if pipeline_id in [1, 4, 7, 10, 13]:
        return "Алмази"
    elif pipeline_id in [2, 5, 8, 11, 14]:
        return "Діаманти"
    elif pipeline_id in [0, 3, 6, 9, 12, 15, 16]:
        return "Не Алмази"
    return None


def build_manager_category_dict(cards: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    Builds a summary dictionary by manager and category.
    Args:
        cards (dict): {"Нові": [...], "Попередні": [...]}
    Returns:
        dict: Nested analytics by manager and category.
    """
    result: Dict[str, Any] = {}
    custom_keys: List[str] = [
        "Закр. Зустріч КИЇВ",
        "Закр. Навчання В ЗАПИСІ",
        "Закр. Зустріч ONLINE"
    ]
    not_qualified_status_ids = {341, 386, 396, 435}
    hot_status_ids = {344, 437, 398}

    for state, card_list in cards.items():
        for card in card_list:
            manager = card.get('manager', {})
            status_id = card.get('status_id')
            manager_key = f"{manager.get('first_name', 'N/A')} {manager.get('last_name', 'N/A')}"
            pipeline_id = card.get('pipeline_id')
            if not isinstance(pipeline_id, int):
                continue
            category = define_category(pipeline_id)
            if not category:
                continue
            profession_priority = category

            custom_fields = card.get('custom_fields', [])
            hot_contact = False
            kvalifikovanyi = False
            custom_values = {key: False for key in custom_keys}
            for field in custom_fields:
                if field.get('name') == 'ПРОГРІТИЙ (готовий працювати)':
                    hot_contact = field.get('value', False)
                if field.get('name') == "Кваліфікований повністю":
                    kvalifikovanyi = field.get('value', False)
                if field.get('name') in custom_keys:
                    custom_values[field.get('name')] = field.get('value', False)
            prog = "Прогріті" if hot_contact or status_id in hot_status_ids else "Не прогріті"

            # Initialize structure for manager/category if not exists
            if manager_key not in result:
                result[manager_key] = {}
            if profession_priority not in result[manager_key]:
                result[manager_key][profession_priority] = {
                    "Нові": {"Прогріті": 0, "Не прогріті": 0},
                    "Попередні": {"Прогріті": 0, "Не прогріті": 0},
                    "Не квалифіковані": 0
                }
                for key in custom_keys:
                    result[manager_key][profession_priority][key] = 0

            # Increment counts for Нові/Попередні
            result[manager_key][profession_priority][state][prog] += 1
            # Increment counts for custom fields
            for key in custom_keys:
                if custom_values[key]:
                    result[manager_key][profession_priority][key] += 1

            # Logic for "Не квалифіковані"
            if not kvalifikovanyi or (status_id in not_qualified_status_ids):
                result[manager_key][profession_priority]["Не квалифіковані"] += 1

    return result