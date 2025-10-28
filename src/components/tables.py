import pandas as pd
import streamlit as st
from io import BytesIO
from typing import Dict, Any, List
from src.utils.analytics import init_category, get_custom_field, define_pipeline


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
        html += "</tr>"

        # --- Row "Всього дозвонів за день" ---
        total_calls_new = 0
        total_calls_prev = 0
        for category in default_categories:
            stats = categories.get(category, init_category())
            total_calls_new += stats['Нові']['Прогріті'] + stats['Нові']['Не прогріті']
            total_calls_prev += stats['Попередні']['Прогріті'] + stats['Попередні']['Не прогріті']

        html += "<tr style='font-weight:bold;'>"
        html += "<td>Всього дозвонів за день</td>"
        html += f"<td colspan='10'>{total_calls_new + total_calls_prev}</td>"
        html += "</tr>"
        html += "</table>"

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
            pipeline_id = card.get("pipeline_id")
            if pipeline_id is None:
                pipeline_label = "N/A"
            else:
                try:
                    pipeline_label = define_pipeline(int(pipeline_id))
                except (TypeError, ValueError):
                    pipeline_label = "N/A"

            row = {
                "Тип": state,
                "ID": card.get("id"),
                "Назва": card.get("title"),
                "Воронка": pipeline_label or "N/A",
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


def get_managers_excel_download(manager_dict: dict) -> BytesIO:
    """
    Creates an Excel file with tables for all managers (each on a separate sheet).
    Returns BytesIO for transfer to st.download_button.
    """
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        for manager, categories in manager_dict.items():
            default_categories = ["База", "Суміжні", "Алмази", "Діаманти"]
            custom_keys = ["Рефералка", "Зустріч", "Навчання", "Планування"]
            total = {
                "Нові": {"Прогріті": 0, "Не прогріті": 0},
                "Попередні": {"Прогріті": 0, "Не прогріті": 0},
                "Не кваліфіковані": 0,
                "Рефералка": 0,
                "Зустріч": 0,
                "Навчання": 0,
                "Планування": 0,
            }
            export_rows = []
            for category in default_categories:
                stats = categories.get(category, total.copy())
                export_rows.append({
                    "Категорія": category,
                    "Нові - Прогріті": stats['Нові']['Прогріті'],
                    "Нові - Не прогріті": stats['Нові']['Не прогріті'],
                    "Попередні - Прогріті": stats['Попередні']['Прогріті'],
                    "Попередні - Не прогріті": stats['Попередні']['Не прогріті'],
                    "Не кваліфіковані": stats['Не кваліфіковані'],
                    "Рефералка": stats['Рефералка'],
                    "Зустріч": stats['Зустріч'],
                    "Навчання": stats['Навчання'],
                    "Планування": stats['Планування'],
                })
                # Summarizing the results
                for s in ["Нові", "Попередні"]:
                    total[s]["Прогріті"] += stats[s]["Прогріті"]
                    total[s]["Не прогріті"] += stats[s]["Не прогріті"]
                for key in ["Не кваліфіковані", *custom_keys]:
                    total[key] += stats[key]
            # Total rows
            export_rows.append({
                "Категорія": "Всього",
                "Нові - Прогріті": total['Нові']['Прогріті'],
                "Нові - Не прогріті": total['Нові']['Не прогріті'],
                "Попередні - Прогріті": total['Попередні']['Прогріті'],
                "Попередні - Не прогріті": total['Попередні']['Не прогріті'],
                "Не кваліфіковані": total['Не кваліфіковані'],
                "Рефералка": total['Рефералка'],
                "Зустріч": total['Зустріч'],
                "Навчання": total['Навчання'],
                "Планування": total['Планування'],
            })

            # Row "Всього дозвонів за день"
            total_calls_new = 0
            total_calls_prev = 0
            for category in default_categories:
                stats = categories.get(category, init_category())
                total_calls_new += stats['Нові']['Прогріті'] + stats['Нові']['Не прогріті']
                total_calls_prev += stats['Попередні']['Прогріті'] + stats['Попередні']['Не прогріті']

            export_rows.append({
                "Категорія": "Всього дозвонів за день",
                "Нові - Прогріті": "",
                "Нові - Не прогріті": "",
                "Попередні - Прогріті": "",
                "Попередні - Не прогріті": "",
                "Не кваліфіковані": "",
                "Рефералка": "",
                "Зустріч": "",
                "Навчання": "",
                "Планування": total_calls_new + total_calls_prev,
            })

            df = pd.DataFrame(export_rows)
            # Sheet name is the manager's name (up to 31 characters)
            sheet_name = manager[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    excel_buffer.seek(0)
    return excel_buffer