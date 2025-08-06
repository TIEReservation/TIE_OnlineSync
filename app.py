import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="TIE Reservation System - Test",
    layout="wide"
)

st.title("🏢 TIE Reservation System - Test Deployment")
st.success("✅ App is running successfully!")

st.write("If you can see this message, the deployment is working.")

# Simple test functionality
st.header("Basic Functionality Test")

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Enter your name:", "Test User")
with col2:
    date = st.date_input("Select date:", datetime.today())

if st.button("Test Button"):
    st.balloons()
    st.success(f"Hello {name}! Selected date: {date}")

# Test dataframe
st.header("Data Display Test")
test_data = {
    "ID": [1, 2, 3],
    "Name": ["John", "Jane", "Bob"], 
    "Status": ["Active", "Pending", "Complete"]
}
df = pd.DataFrame(test_data)
st.dataframe(df, use_container_width=True)

st.info("This is a minimal test version. If this works, we can add the full functionality.")
