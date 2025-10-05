import streamlit as st
from supabase import create_client, Client

try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Check secrets.toml.")
    st.stop()

@st.cache_data(ttl=300)
def load_dms_data_from_supabase():
    """Load DMS data from Supabase with caching (5min TTL)."""
    try:
        response = supabase.table("dms").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading DMS data: {e}")
        return []

def show_dms():
    """Display daily management status page."""
    st.title("📊 Daily Management Status")
    dms_data = load_dms_data_from_supabase()
    if not dms_data:
        st.info("No DMS data available.")
        return
    st.write("### Daily Management Status")
    st.dataframe(dms_data)
