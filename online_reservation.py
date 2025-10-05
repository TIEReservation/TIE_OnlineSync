import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Check secrets.toml.")
    st.stop()

@st.cache_data(ttl=300)
def load_online_reservations_from_supabase():
    """Load online reservations from Supabase with caching (5min TTL)."""
    try:
        response = supabase.table("online_reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def show_online_reservations():
    """Display online reservations page."""
    st.title("🌐 Online Reservations")
    reservations = load_online_reservations_from_supabase()
    if not reservations:
        st.info("No online reservations available.")
        return
    st.write("### Online Reservations")
    st.dataframe(reservations)
