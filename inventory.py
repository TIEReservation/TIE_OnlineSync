import streamlit as st
from supabase import create_client, Client

try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Check secrets.toml.")
    st.stop()

@st.cache_data(ttl=300)
def load_inventory_from_supabase():
    """Load inventory data from Supabase with caching (5min TTL)."""
    try:
        response = supabase.table("inventory").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        return []

def show_daily_status():
    """Display daily status page."""
    st.title("📅 Daily Status")
    inventory = load_inventory_from_supabase()
    if not inventory:
        st.info("No inventory data available.")
        return
    st.write("### Daily Inventory Status")
    st.dataframe(inventory)
