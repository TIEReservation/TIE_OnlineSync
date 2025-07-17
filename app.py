import streamlit as st
def check_authentication():
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # If not authenticated, show login page
    if not st.session_state.authenticated:
        st.title("🔐 TIE Reservation System - Organization Login")
        st.write("Please enter the organization password to access the system.")
        
        # Create password input
        password = st.text_input("Enter organization password:", type="password")
        
        # Login button
        if st.button("🔑 Login"):
            # Change "TIE2024" to your desired password
            if password == "TIE2024":
                st.session_state.authenticated = True
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
        
        # Stop the app here if not authenticated
        st.stop()

# Call the authentication check
check_authentication()
import streamlit as st import pandas as pd import psycopg2 from datetime import datetime, date import plotly.express as px import plotly.graph_objects as go from sqlalchemy import create_engine import requests # Page config st.set_page_config( p
