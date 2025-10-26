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
            <th rowspan='2'>Категорія</th>
            <th colspan='2'>Нові</th>
            <th colspan='2'>Попередні</th>
            <th rowspan='2'>Не кваліфіковані</th>
            <th colspan='4'>З них закрито:</th>
        </tr>
        <tr style='font-weight:bold;'>
            <th>Прогріті</th><th>Не прогріті</th>
            <th>Прогріті</th><th>Не прогріті</th>
            <th>Рефералка</th><th>Зустріч</th><th>Навчання</th><th>Планування</th>
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
        html += "<td>Всього</td>"
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
                "Тип": state,
                "ID": card.get("id"),
                "Назва": card.get("title"),
                "Воронка": card.get("pipeline_id"),
                "Менеджер": card.get("manager", {}).get("full_name", "N/A"),
                "Прогрітий (готовий працювати)": get_custom_field(card, "ПРОГРІТИЙ (готовий працювати)"),
                "Закр. Зустріч КИЇВ": get_custom_field(card, "Закр. Зустріч КИЇВ"),
                "Закр. Зустріч ONLINE": get_custom_field(card, "Закр. Зустріч ONLINE"),
                "Закр. Навчання В ЗАПИСІ": get_custom_field(card, "Закр. Навчання В ЗАПИСІ"),
                "Кваліфікований повністю": get_custom_field(card, "Кваліфікований повністю"),
                "Створено": created,
                "Оновлено": updated,
            }
            rows.append(row)

    return pd.DataFrame(rows)