import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Check secrets.toml.")
    st.stop()

@st.cache_data(ttl=300)
def load_reservations_from_supabase():
    """Load direct reservations from Supabase with caching (5min TTL)."""
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def show_new_reservation_form():
    """Display form for new direct reservations."""
    st.title("➕ New Direct Reservation")
    st.write("### Add New Reservation")
    # Placeholder for form logic (assumed unchanged)
    st.write("Form implementation not shown for brevity.")

def show_reservations():
    """Display direct reservations page."""
    st.title("📋 Direct Reservations")
    reservations = load_reservations_from_supabase()
    if not reservations:
        st.info("No direct reservations available.")
        return
    st.write("### Direct Reservations")
    st.dataframe(reservations)

def show_edit_reservations():
    """Display edit direct reservations page."""
    st.title("✏️ Edit Direct Reservations")
    # Placeholder for edit logic (assumed unchanged)
    st.write("Edit implementation not shown for brevity.")

def show_analytics():
    """Display analytics page for Management."""
    st.title("📊 Analytics")
    # Placeholder for analytics logic (assumed unchanged)
    st.write("Analytics implementation not shown for brevity.")
