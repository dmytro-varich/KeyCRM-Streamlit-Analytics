import streamlit as st
from copy import deepcopy
from collections import defaultdict
from typing import List, Dict, Tuple, Any
from src.utils.time_utils import get_kyiv_date, get_today_date_kyiv
from src.utils.analytics import build_manager_category_dict
from config.settings import plan_sent_status_ids, plan_promised_status_ids


def _merge_values(a: Any, b: Any) -> Any:
    """Recursively combines a and b: for dict - recursively, for int - sums, otherwise takes b."""
    if isinstance(a, dict) and isinstance(b, dict):
        res: Dict[Any, Any] = {}
        for key in set(a.keys()) | set(b.keys()):
            if key in a and key in b:
                res[key] = _merge_values(a[key], b[key])
            elif key in a:
                res[key] = deepcopy(a[key])
            else:
                res[key] = deepcopy(b[key])
        return res
    if isinstance(a, int) and isinstance(b, int):
        return a + b
    # если один из них отсутствует или типы разные — возвращаем deepcopy(b) если b задан, иначе deepcopy(a)
    return deepcopy(b) if b is not None else deepcopy(a)


def merge_manager_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge any number of manager dictionaries into one.
    Each argument is expected to be a dict: {manager_name: {category: stats_dict, ...}, ...}.
    Numeric values are summed, nested dicts are merged recursively via _merge_values.
    """
    merged: Dict[str, Any] = {}
    for d in dicts:
        if not d:
            continue
        for manager, data in d.items():
            if manager in merged:
                merged[manager] = _merge_values(merged[manager], data)
            else:
                merged[manager] = deepcopy(data)
    return merged


def process_all_data(api_client, all_cards: List[Dict[str, Any]], base_cards: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any], Dict[str, int]]:
    """
    Processes all cards and classifies them as New or Previous
    for 'Base' (not Diamonds) and 'Target' (Diamonds, Diamenty, Sumizhnyky).
    """

    # --- Get previous state ---
    prev_cards_by_id = {
        card["id"]: card for card in base_cards if not card.get("is_finished", False)
    }

    all_cards = [card for card in all_cards if not card.get("is_finished", False)]

    # --- Get today's calls ---
    today_date = get_today_date_kyiv()
    calls_today = api_client.fetch_all_calls(max_calls=400, date=today_date, include="")

    called_card_ids = {
        call["lead_id"]
        for call in calls_today
        if call["lead_id"]
        and get_kyiv_date(call["created_at"]) == str(today_date)
        and call["state"] in ["completed"]
    }

    # --- Set up pipeline IDs ---
    base_pipelines = [1, 3, 16, 20, 31]                                 # Not Diamonds ("Base")
    target_pipelines = [2, 4, 15, 19, 32, 22, 24, 26, 30, 33, 46, 18]   # Almazy / Diamenty / Sumizhnyky

    new_cards = []
    previous_cards = []
    previous_cards_no_calls = []

    # Total calls for the card
    calls_total = defaultdict(int)

    # Manager ID to Name mapping
    manager_id_key_map: Dict[int, str] = {}

    # --- Main loop over cards ---
    for card in all_cards:
        card_id = card["id"]
        pipeline_id = card.get("pipeline_id")
        status_id = card.get("status_id")
        manager_id = card.get("manager_id")
        manager = card.get("manager", None)

        # Skip if no manager
        if manager_id is None:
            continue

        if manager:
            manager_key = manager['full_name']
            manager_id_key_map[manager_id] = manager_key
        else:
            manager_key = manager_id_key_map.get(manager_id)
            if manager_key is None:
                continue

        # if card['title'] and card['title'] == 'test999':
        #     st.json(card)

        card_created_kyiv = get_kyiv_date(card.get("created_at", ""))
        card_updated_kyiv = get_kyiv_date(card.get("updated_at", ""))

        # --- If the card already existed before ---
        if card_id in prev_cards_by_id:
            prev_card = prev_cards_by_id[card_id]
            prev_pipeline = prev_card["pipeline_id"]
            prev_manager_id = prev_card.get("manager_id")
            prev_status_id = prev_card.get("status_id")

            # ▪ Target: New (moved to target today)
            if prev_pipeline != pipeline_id and pipeline_id in target_pipelines and prev_pipeline in base_pipelines:
                new_cards.append(card)

            # ▪ Target: Previous (already in target, manager exists, there was a call)
            elif (
                prev_pipeline == pipeline_id
                and pipeline_id in target_pipelines
                and card_id in called_card_ids
            ):
                previous_cards.append(card)
                calls_total[manager_key] += 1

            # ▪ Base: New (manager appeared today and there was a call)
            elif (
                pipeline_id in base_pipelines
                and prev_manager_id is None
                and manager_id is not None
                and card_updated_kyiv == str(today_date)
                and card_id in called_card_ids
            ):
                new_cards.append(card)
                calls_total[manager_key] += 1

            # ▪ Base: Previous (manager already existed, there was a call)
            elif (
                pipeline_id in base_pipelines
                and prev_manager_id is not None
                and manager_id is not None
                and card_id in called_card_ids
            ):
                previous_cards.append(card)
                calls_total[manager_key] += 1

            # ▪ Diamonds: Previous (card moved to plans status, there wasn't a call)
            elif (
                pipeline_id in target_pipelines
                and prev_pipeline == pipeline_id
                and status_id in plan_sent_status_ids.union(plan_promised_status_ids)
                and card_id not in called_card_ids
                and prev_status_id != status_id
                and manager_id is not None
            ): 
                manager_key = manager_id_key_map.get(manager_id) or f"ID:{manager_id}"
                # Ensure manager dict exists before writing full_name
                # if not isinstance(card.get("manager"), dict):
                #     card["manager"] = {"full_name": manager_key}
                # else:
                #     card["manager"]["full_name"] = manager_key
                previous_cards_no_calls.append(card)
                
        # --- If the card is new (was not in previous_hidden_cards) ---
        else:
            # ▪ Target: New (created today and manager exists)
            if (
                pipeline_id in target_pipelines
                and card_created_kyiv == str(today_date)
                and manager_id is not None
            ):
                new_cards.append(card)

            # ▪ Base: New (manager appeared immediately and there was a call)
            elif (
                pipeline_id in base_pipelines
                and manager_id is not None
                and card_id in called_card_ids
                and card_created_kyiv == str(today_date)
            ):
                new_cards.append(card)
                calls_total[manager_key] += 1

    filtered_all_cards = {
        "Нові": new_cards,
        "Попередні": previous_cards + previous_cards_no_calls
    }

    manager_dict = build_manager_category_dict(filtered_all_cards)

    return (filtered_all_cards, manager_dict, calls_total)
