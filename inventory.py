import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict
import logging

# Configure file-based logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}
reverse_mapping = {}
for variant, canonical in property_mapping.items():
    reverse_mapping.setdefault(canonical, []).append(variant)

# MOP (Mode of Payment) mapping
mop_mapping = {
    "UPI": ["UPI"],
    "Cash": ["Cash"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Agoda": ["Agoda"],
    "NOT PAID": ["Not Paid"],
    "Bank Transfer": ["Bank Transfer"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Card Payment": ["Card"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

# MOB (Mode of Booking) mapping
mob_mapping = {
    "Booking": ["BOOKING"],
    "Direct": ["Direct"],
    "Bkg-Direct": ["Bkg-Direct"],
    "Agoda": ["Agoda"],
    "Go-MMT": ["Goibibo", "MMT", "Go-MMT", "MAKEMYTRIP"],
    "Walk-In": ["Walk-In"],
    "TIE Group": ["TIE Group"],
    "Stayflexi": ["STAYFLEXI_GHA"],
    "Airbnb": ["Airbnb"],
    "Social Media": ["Social Media"],
    "Expedia": ["Expedia"],
    "Cleartrip": ["Cleartrip"],
    "Website": ["Stayflexi Booking Engine"]
}

# Table CSS
TABLE_CSS = """
<style>
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
    max-width: 150px;
    padding: 8px;
    border: 1px solid #ddd;
}
</style>
"""

# Property inventory
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {
        "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"],
        "three_bedroom": ["203", "204"]
    },
    "La Millionaire Resort": {
        "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"],
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

def initialize_property_inventory(properties: List[str]) -> None
