import requests
import streamlit as st
from datetime import datetime
from config.settings import WEBHOOK_PROD_URL
from src.utils.analytics import build_manager_category_dict


def process_all_data(api_client, webhook_url: str = WEBHOOK_PROD_URL) -> None:
    """
    Process all data: new leads from webhook + calls from KeyCRM API.
    Saves analytics and cards to Streamlit session_state.
    Args:
        ApiClient (Type): KeyCRM API client class (default: imported ApiClient).
        webhook_url (str): Webhook URL to fetch new leads.
    Returns:
        None
    """
    with st.spinner("Loading all data..."):
        try:
            # Fetch new leads from webhook
            resp = requests.get(webhook_url, timeout=20)
            resp.raise_for_status()
            if not resp.text.strip():
                st.warning("No new leads from webhook")
                webhook_data = []
                card_ids = None
            else:
                webhook_data = resp.json()
                card_ids = list({item['card_id'] for item in webhook_data if 'card_id' in item})

            cards_new = []
            if card_ids:
                    # Include custom fields and managers in card data
                    response_new = api_client.fetch_cards_by_ids(card_ids, include="custom_fields,manager")
                    if not response_new.get('error'):
                        cards_new = response_new.get('data', [])
            else:
                cards_new = []

            # Fetch calls for today
            today = datetime.now().strftime("%Y-%m-%d")
            calls_today = api_client.fetch_all_calls(max_calls=400, date=today, include="")
            lead_ids = [call.get('lead_id') for call in calls_today if call.get('lead_id') is not None]

            # Normalize lead IDs: keep only values convertible to int
            normalized_lead_ids = set()
            for lid in lead_ids:
                if lid is None:
                    continue
                try:
                    # Pass an int directly or convert other values to str first to satisfy type checkers
                    if isinstance(lid, int):
                        normalized_lead_ids.add(lid)
                    else:
                        normalized_lead_ids.add(int(str(lid)))
                except (TypeError, ValueError):
                    continue
            unique_lead_ids = list(normalized_lead_ids)

            cards_by_leads = []
            if unique_lead_ids:
                response_leads = api_client.fetch_cards_by_ids(unique_lead_ids, include="custom_fields,manager")
                if not response_leads.get('error'):
                    cards_by_leads = response_leads.get('data', [])

            # "Нові": cards created today (from webhook and calls)
            cards_calls_new = [card for card in cards_by_leads if card.get('created_at', '')[:10] == today and card.get('manager_id', False)]
            cards_new_final = cards_new + cards_calls_new

            # "Попередні": cards with a call today, but not created today
            cards_calls_final = [card for card in cards_by_leads if card.get('created_at', '')[:10] != today and card.get('manager_id', False)]

            # Remove duplicates (if any)
            new_ids = {card.get('id') for card in cards_new_final}
            cards_calls_final = [card for card in cards_calls_final if card.get('id') not in new_ids]

            filtered_card = {
                "Нові": cards_new_final,
                "Попередні": cards_calls_final
            }

            # Combine all cards into one list
            all_cards = filtered_card["Нові"] + filtered_card["Попередні"]

            # Build analytics dictionary
            manager_dict = build_manager_category_dict(filtered_card)

            # Save to Streamlit session_state
            st.session_state['all_data'] = {
                'cards': all_cards,
                'analytics': manager_dict,
                'count': len(all_cards)
            }

            st.success(f"✅ Received {len(all_cards)} cards")
        except Exception as e:

            st.error(f"❌ Error processing data: {e}")
