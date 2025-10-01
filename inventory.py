import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict # Type hints for function signatures

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

# Table CSS for non-wrapping, scrollable table
TABLE_CSS = """
<style>
/* Styles for non-wrapping, scrollable table in daily status */
.custom-scrollable-table {
    overflow-x: auto;
    max-width: 100%;
    min-width: 800px;
}
.custom-scrollable-table table {
    table-layout: auto;
    border-collapse: collapse;
}
.custom-scrollable-table td, .custom-scrollable-table th {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 300px;
    padding: 8px;
    border: 1px solid #ddd;
}
</style>
"""

# Property inventory mapping
PROPERTY_INVENTORY = {
    "Le Poshe Beach View": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "No Show"],
        "three_bedroom": ["203", "204", "205"]
    },
    "Le Poshe Luxury": {
        "all": ["101", "102", "201", "202", "203", "204", "205", "301", "302", "303", "304", "305", "401", "402", "403", "404", "405", "501", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205"]
    },
    "Le Poshe Suite": {
        "all": ["601", "602", "603", "604", "701", "702", "703", "704", "801", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Paradise Residency": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "La Paradise Luxury": {
        "all": ["101", "102", "103", "201", "202", "203", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "La Villa Heritage": {
        "all": ["101", "102", "103", "201", "202", "203", "301", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "Le Pondy Beach Side": {
        "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Le Royce Villa": {
        "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "La Tamara Luxury": {
        "all": ["101", "102", "103", "104", "105", "106", "201", "202", "203", "204", "205", "206", "301", "302", "303", "304", "305", "306", "401", "402", "403", "404", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205", "206"]
    },
    "La Antilia Luxury": {
        "all": ["101", "201", "202", "203", "204", "301", "302", "303", "304", "401", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Tamara Suite": {
        "all": ["101", "102", "103", "104", "201", "202", "203", "204", "205", "206", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204", "205", "206"]
    },
    "Le Park Resort": {
        "all": ["111", "222", "333", "444", "555", "666", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    },
    "Villa Shakti": {
        "all": ["101", "102", "201", "201A", "202", "203", "301", "301A", "302", "303", "401", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203"]
    },
    "Eden Beach Resort": {
        "all": ["101", "102", "103", "201", "202", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": []
    }
}

def initialize_property_inventory(properties: List[str]) -> None:
    """Add missing properties to PROPERTY_INVENTORY with fallback inventory."""
    fallback = {"all": ["Unknown"], "three_bedroom": []}
    for prop in properties:
        if prop not in PROPERTY_INVENTORY:
            PROPERTY_INVENTORY[prop] = fallback
            st.warning(f"Added fallback inventory for unknown property: {prop}")

def format_booking_id(booking: Dict) -> str:
    """Format booking ID as a clickable hyperlink."""
    booking_id = sanitize_string(booking.get('booking_id'))
    return f'<a target="_blank" href="/?edit_type={booking["type"]}&booking_id={booking_id}">{booking_id}</a>'

def load_properties() -> List[str]:
    """Load unique properties from reservations and online_reservations tables."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set()
        for r in res_direct:
            prop = r['property_name']
            if prop:
                canonical = property_mapping.get(prop, prop)
                properties.add(canonical)
        for r in res_online:
            prop = r['property']
            if prop:
                canonical = property_mapping.get(prop, prop)
                properties.add(canonical)
        properties = sorted(properties)
        initialize_property_inventory(properties)
        return properties
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def sanitize_string(value: Any, default: str = "Unknown") -> str:
    """Convert value to string, handling None and non-string types."""
    return str(value) if value is not None else default

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    """Normalize booking dict to common schema."""
    # Sanitize inputs to prevent f-string and HTML issues
    booking_id = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status
