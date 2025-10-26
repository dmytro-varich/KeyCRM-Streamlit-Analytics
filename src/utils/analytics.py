from typing import List, Dict, Any, Optional


def define_category(pipeline_id: int) -> Optional[str]:
    """
    Returns category name based on pipeline ID.
    """
    if pipeline_id in [1, 4, 7, 10, 13]:
        return "База"
    elif pipeline_id in [16, 17]:
        return "Суміжні"
    elif pipeline_id in [2, 5, 8, 11, 14]:
        return "Алмази"
    elif pipeline_id in [3, 6, 9, 12, 15]:
        return "Діаманти"
    return None


def get_custom_field(card, field_name, default=False):
    """
    Universally retrieves the value of a custom field by name.
    Works with types: switcher, select, text, etc.
    """
    custom_fields = card.get("custom_fields", [])
    if not isinstance(custom_fields, list):
        return default

    for field in custom_fields:
        if field.get("name") == field_name:
            value = field.get("value", default)
            # Если значение — список (например, select)
            if isinstance(value, list):
                return value[0] if value else default
            return value
    return default


def init_category() -> Dict[str, Any]:
    """Initializes the category structure for a manager."""
    return {
        "Нові": {"Прогріті": 0, "Не прогріті": 0},
        "Попередні": {"Прогріті": 0, "Не прогріті": 0},
        "Не кваліфіковані": 0,
        "Рефералка": 0,
        "Зустріч": 0,
        "Навчання": 0,
        "Планування": 0
    }


def build_manager_category_dict(cards: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    Builds analytics by managers and funnel categories.
    cards = {"Нові": [...], "Попередні": [...]}
    """
    result: Dict[str, Any] = {}

    meeting_fields = {"Закр. Зустріч КИЇВ", "Закр. Зустріч ONLINE"}
    training_field = "Закр. Навчання В ЗАПИСІ"
    not_qualified_status_ids = {326, 341, 386, 396, 435, 425, 534, 524, 361, 450, 411}
    plan_status_ids = {365, 414, 452}

    for state, card_list in cards.items():
        for card in card_list:
            manager = card.get("manager", {})
            manager_key = f"{manager.get('first_name', 'N/A')} {manager.get('last_name', 'N/A')}".strip()

            pipeline_id = card.get("pipeline_id")
            if not isinstance(pipeline_id, int):
                continue

            category = define_category(pipeline_id)
            if not category:
                continue

            # --- reading custom fields ---
            custom_fields = card.get("custom_fields", [])
            hot_contact = False             # warmed up (ready to work)
            kvalifikovanyi = False          # fully qualified
            referral = False               # referral
            meeting = False                # meeting
            training = False               # training

            for field in custom_fields:
                name = field.get("name")
                value = field.get("value")

                if name == "ПРОГРІТИЙ (готовий працювати)":
                    hot_contact = bool(value)
                elif name == "Кваліфікований повністю":
                    kvalifikovanyi = bool(value)
                elif name == "Рефералка":
                    referral = bool(value)
                elif name in meeting_fields:
                    meeting = bool(value)
                elif name == training_field:
                    training = bool(value)

            prog_state = "Прогріті" if hot_contact else "Не прогріті"

            # --- initialization of nested structures ---
            if manager_key not in result:
                result[manager_key] = {}
            if category not in result[manager_key]:
                result[manager_key][category] = init_category()

            # --- increments ---
            result[manager_key][category][state][prog_state] += 1
            if referral:
                result[manager_key][category]["Рефералка"] += 1
            if meeting:
                result[manager_key][category]["Зустріч"] += 1
            if training:
                result[manager_key][category]["Навчання"] += 1

            status_id = card.get("status_id")
            # Planning
            if status_id in plan_status_ids:
                result[manager_key][category]["Планування"] += 1

            # Not qualified
            if (not kvalifikovanyi) or (status_id in not_qualified_status_ids):
                result[manager_key][category]["Не кваліфіковані"] += 1

    return result
