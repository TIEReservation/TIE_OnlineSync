import streamlit as st
import pandas as pd

table_data = [
    ["Game Changers"],
    ["Property Names", "Team (Total Inv)", "2025-10-26 Sold", "2025-10-26 Unsold", "2025-10-27 Sold", "2025-10-27 Unsold", "2025-10-28 Sold", "2025-10-28 Unsold", "2025-10-29 Sold", "2025-10-29 Unsold"],
    ["", "", 10, 51, 15, 46, 12, 49, 8, 53]
]
df = pd.DataFrame(table_data[1:], columns=table_data[0])
st.table(df)
