import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from src.utils.analytics import init_category, get_custom_field


def render_manager_tables(manager_dict: Dict[str, Any]) -> None:
    """
    Displays analytics as HTML tables with a grouped column "Closed from them".
    """
    default_categories = ["База", "Суміжні", "Алмази", "Діаманти"]
    custom_keys = ["Рефералка", "Зустріч", "Навчання", "Планування"]

    for manager, categories in manager_dict.items():
        st.markdown(f"### 👤 {manager}")

        html = """
        <table style='border-collapse:collapse;width:100%;text-align:center;'>
        <tr style='font-weight:bold;'>
            <th rowspan='2'>Category</th>
            <th colspan='2'>New</th>
            <th colspan='2'>Previous</th>
            <th rowspan='2'>Not qualified</th>
            <th colspan='4'>Closed from them:</th>
        </tr>
        <tr style='font-weight:bold;'>
            <th>Warmed up</th><th>Not warmed up</th>
            <th>Warmed up</th><th>Not warmed up</th>
            <th>Referral</th><th>Meeting</th><th>Training</th><th>Planning</th>
        </tr>
        """

        total = init_category()

        for category in default_categories:
            stats = categories.get(category, init_category())

            html += "<tr>"
            html += f"<td>{category}</td>"
            html += f"<td>{stats['Нові']['Прогріті']}</td>"
            html += f"<td>{stats['Нові']['Не прогріті']}</td>"
            html += f"<td>{stats['Попередні']['Прогріті']}</td>"
            html += f"<td>{stats['Попередні']['Не прогріті']}</td>"
            html += f"<td>{stats['Не кваліфіковані']}</td>"
            html += f"<td>{stats['Рефералка']}</td>"
            html += f"<td>{stats['Зустріч']}</td>"
            html += f"<td>{stats['Навчання']}</td>"
            html += f"<td>{stats['Планування']}</td>"
            html += "</tr>"

            # totals
            for s in ["Нові", "Попередні"]:
                total[s]["Прогріті"] += stats[s]["Прогріті"]
                total[s]["Не прогріті"] += stats[s]["Не прогріті"]
            for key in ["Не кваліфіковані", *custom_keys]:
                total[key] += stats[key]

        # totals row
        html += "<tr style='font-weight:bold;'>"
        html += "<td>Total</td>"
        html += f"<td>{total['Нові']['Прогріті']}</td>"
        html += f"<td>{total['Нові']['Не прогріті']}</td>"
        html += f"<td>{total['Попередні']['Прогріті']}</td>"
        html += f"<td>{total['Попередні']['Не прогріті']}</td>"
        html += f"<td>{total['Не кваліфіковані']}</td>"
        html += f"<td>{total['Рефералка']}</td>"
        html += f"<td>{total['Зустріч']}</td>"
        html += f"<td>{total['Навчання']}</td>"
        html += f"<td>{total['Планування']}</td>"
        html += "</tr></table>"

        st.markdown(html, unsafe_allow_html=True)


def create_simple_dataframe(cards: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Create a combined DataFrame from {"Нові": [...], "Попередні": [...]}.
    """
    rows: List[Dict[str, Any]] = []

    for state, card_list in cards.items():
        for card in card_list:
            created = (card.get("created_at") or "")[:10]
            updated = (card.get("updated_at") or "")[:10]
            row = {
                "Type": state,
                "ID": card.get("id"),
                "Title": card.get("title"),
                "Pipeline": card.get("pipeline_id"),
                "Manager": card.get("manager", {}).get("full_name", "N/A"),
                "Warmed up (ready to work)": get_custom_field(card, "ПРОГРІТИЙ (готовий працювати)"),
                "Closed. Meeting KYIV": get_custom_field(card, "Закр. Зустріч КИЇВ"),
                "Closed. Meeting ONLINE": get_custom_field(card, "Закр. Зустріч ONLINE"),
                "Closed. Training RECORDED": get_custom_field(card, "Закр. Навчання В ЗАПИСІ"),
                "Fully qualified": get_custom_field(card, "Кваліфікований повністю"),
                "Created": created,
                "Updated": updated,
            }
            rows.append(row)

    return pd.DataFrame(rows)