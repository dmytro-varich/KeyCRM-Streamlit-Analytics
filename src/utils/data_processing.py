import streamlit as st
from typing import List, Dict, Tuple, Any
from src.utils.file_utils import load_json_file
from src.utils.time_utils import get_kyiv_date, today_date
from src.utils.analytics import build_manager_category_dict

def process_all_data(api_client, all_cards: List[Dict[str, Any]], base_cards: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """
    Processes all cards and classifies them as New or Previous
    for 'Base' (not Diamonds) and 'Target' (Diamonds, Diamenty, Sumizhnyky).
    """

    # --- Get previous state ---
    previous_hidden_cards = base_cards
    prev_cards_by_id = {
        card["id"]: card for card in previous_hidden_cards if not card.get("is_finished", False)
    }

    # --- Get today's calls ---
    calls_today = api_client.fetch_all_calls(max_calls=400, date=today_date, include="")
    called_card_ids = {
        call["lead_id"]
        for call in calls_today
        if call.get("lead_id")
        and get_kyiv_date(call.get("created_at", "")) == str(today_date)
        # and call.get("state") in ["completed"]
    }

    # --- Set up pipeline IDs ---
    base_pipelines = [1, 4, 7, 10, 13]                               # Not Diamonds ("Base")
    target_pipelines = [2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 16, 17]    # Diamonds / Diamenty / Sumizhnyky

    new_cards = []
    previous_cards = []

    # --- Main loop over cards ---

    for card in all_cards:
        card_id = card["id"]
        pipeline_id = card.get("pipeline_id")
        manager_id = card.get("manager_id")

    # Skip if no manager
        if manager_id is None:
            continue

        card_created_kyiv = get_kyiv_date(card.get("created_at", ""))
        card_updated_kyiv = get_kyiv_date(card.get("updated_at", ""))

    # --- If the card already existed before ---
        if card_id in prev_cards_by_id:
            prev_card = prev_cards_by_id[card_id]
            prev_pipeline = prev_card["pipeline_id"]
            prev_manager_id = prev_card.get("manager_id")

            # ▪ Target: New (moved to target today)
            if prev_pipeline != pipeline_id and pipeline_id in target_pipelines:
                new_cards.append(card)

            # ▪ Target: Previous (already in target, manager exists, there was a call)
            elif (
                prev_pipeline == pipeline_id
                and pipeline_id in target_pipelines
                and card_id in called_card_ids
            ):
                previous_cards.append(card)

            # ▪ Base: New (manager appeared today and there was a call)
            elif (
                pipeline_id in base_pipelines
                and prev_manager_id is None
                and manager_id is not None
                and card_updated_kyiv == str(today_date)
                and card_id in called_card_ids
            ):
                new_cards.append(card)

            # ▪ Base: Previous (manager already existed, there was a call)
            elif (
                pipeline_id in base_pipelines
                and prev_manager_id is not None
                and manager_id is not None
                and card_id in called_card_ids
            ):
                previous_cards.append(card)

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

    filtered_all_cards = {
        "Нові": new_cards,
        "Попередні": previous_cards
    }

    manager_dict = build_manager_category_dict(filtered_all_cards)

    return (filtered_all_cards, manager_dict)
