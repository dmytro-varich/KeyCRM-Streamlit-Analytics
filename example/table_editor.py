# import pandas as pd
# import streamlit as st

# df = pd.DataFrame(
#     [
#         {"command": "st.selectbox", "rating": None, "is_widget": True},
#         {"command": "st.balloons", "rating": 5, "is_widget": False},
#         {"command": "st.time_input", "rating": 3, "is_widget": True},
#     ]
# )
# edited_df = st.data_editor(df)

# favorite_command = edited_df.loc[edited_df["rating"].idxmax()]["command"]
# st.markdown(f"Your favorite command is **{favorite_command}** 🎈")

import streamlit as st
import pandas as pd

key = "demo_table"

# 1. Инициализация только один раз
if key not in st.session_state:
    st.session_state[key] = pd.DataFrame([
        {"Опис": "Київ", "URL": "https://"},
        {"Опис": "Львів", "URL": "https://"}
    ])

# 2. Форма предотвращает промежуточные ререндеры
with st.form("table_form"):
    st.subheader("💎 Діаманти")
    edited = st.data_editor(st.session_state[key], key=key + "_editor")
    submitted = st.form_submit_button("💾 Зберегти")

# 3. Обновляем state и сохраняем
if submitted:
    st.session_state[key] = edited
    st.success("✅ Збережено без миготіння!")
