import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
import logging

# === CONFIG ===
logging.basicConfig(
    filename='dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    supabase: Client = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# === PROPERTY MAPPING & INVENTORY ===
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}

PROPERTY_INVENTORY = {
    "Le Poshe Beach view": { "all": ["101", "102", "201", "202", "203", "204", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204"] },
    "La Millionaire Resort": { "all": ["101", "102", "103", "105", "201", "202", "203", "204", "205", "206", "207", "208", "301", "302", "303", "304", "305", "306", "307", "308", "401", "402", "Day Use 1", "Day Use 2", "Day Use 3", "Day Use 4", "Day Use 5", "No Show"], "three_bedroom": ["203", "204", "205"] },
    "Le Poshe Luxury": { "all": ["101", "102", "201", "202", "203", "204", "205", "301", "302", "303", "304", "305", "401", "402", "403", "404", "405", "501", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204", "205"] },
    "Le Poshe Suite": { "all": ["601", "602", "603", "604", "701", "702", "703", "704", "801", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": [] },
    "La Paradise Residency": { "all": ["101", "102", "103", "201", "202", "203", "301", "302", "303", "304", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"] },
    "La Paradise Luxury": { "all": ["101", "102", "103", "201", "202", "203", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"] },
    "La Villa Heritage": { "all": ["101", "102", "103", "201", "202", "203", "301", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"] },
    "Le Pondy Beach Side": { "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": [] },  # ← ADDED
    "Le Royce Villa": { "all": ["101", "102", "201", "202", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": [] },
    "La Tamara Luxury": { "all": ["101", "102", "103", "104", "105", "106", "201", "202", "203", "204", "205", "206", "301", "302", "303", "304", "305", "306", "401", "402", "403", "404", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204", "205", "206"] },
    "La Antilia Luxury": { "all": ["101", "201", "202", "203", "204", "301", "302", "303", "304", "401", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204"] },
    "La Tamara Suite": { "all": ["101", "102", "103", "104", "201", "202", "203", "204", "205", "206", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203", "204", "205", "206"] },
    "Le Park Resort": { "all": ["111", "222", "333", "444", "555", "666", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": [] },
    "Villa Shakti": { "all": ["101", "102", "201", "201A", "202", "203", "301", "301A", "302", "303", "401", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": ["203"] },
    "Eden Beach Resort": { "all": ["101", "102", "103", "201", "202", "Day Use 1", "Day Use 2", "No Show"], "three_bedroom": [] }
}

# === TIE TEAMS ===
GAME_CHANGERS = ["La Millionaire Resort", "Le Park Resort", "Le Poshe Luxury", "Villa Shakti", "Le Royce Villa"]
DREAM_SQUAD = [
    "Eden Beach Resort",
    "La Paradise Luxury",
    "La Paradise Residency",
    "Le Pondy Beach Side",  # ← ADDED & SORTED
    "Le Poshe Suite",
    "Le Poshe Beach view",
    "La Villa Heritage"
]
INDIVIDUAL_WARRIORS = ["La Antilia Luxury", "La Tamara Suite", "La Tamara Luxury", "Le Poshe Beach view"]

# === HELPER FUNCTIONS ===
def get_total_inventory(property_name):
    inventory = PROPERTY_INVENTORY.get(property_name, {"all": []})["all"]
    return len([inv for inv in inventory if not inv.startswith(("Day Use", "No Show"))])

def sanitize_string(value, default="Unknown"):
    return str(value).strip() if value is not None else default

def normalize_booking(booking, is_online):
    booking_id = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status')).title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        return None
    try:
        check_in = date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None
        check_out = date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None
        if not check_in or not check_out:
            return None
        days = (check_out - check_in).days
        if days <= 0: days = 1
        property_name = sanitize_string(booking.get('property', booking.get('property_name', '')))
        property_name = property_mapping.get(property_name, property_name)
        room_no = sanitize_string(booking.get('room_no', '')).title()
        return {
            "property": property_name,
            "booking_id": booking_id,
            "check_in": str(check_in),
            "check_out": str(check_out),
            "days": days,
            "room_no": room_no,
            "payment_status": payment_status
        }
    except Exception as e:
        logging.warning(f"Error normalizing booking {booking_id}: {e}")
        return None

def load_bookings_for_date_range(start_date, end_date):
    all_bookings = []
    try:
        online_response = supabase.table("online_reservations").select("*") \
            .gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute()
        for b in (online_response.data or []):
            norm = normalize_booking(b, True)
            if norm: all_bookings.append(norm)
        direct_response = supabase.table("reservations").select("*") \
            .gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute()
        for b in (direct_response.data or []):
            norm = normalize_booking(b, False)
            if norm: all_bookings.append(norm)
        logging.info(f"Loaded {len(all_bookings)} bookings for {start_date} to {end_date}")
        return all_bookings
    except Exception as e:
        st.error(f"Error loading bookings: {e}")
        logging.error(f"Error loading bookings: {e}")
        return []

def filter_bookings_for_day(bookings, target_date):
    return [b for b in bookings if date.fromisoformat(b["check_in"]) <= target_date < date.fromisoformat(b["check_out"])]

def count_rooms_sold(bookings, property_name):
    inventory = PROPERTY_INVENTORY.get(property_name, {"all": []})["all"]
    inventory_lower = [i.lower() for i in inventory]
    rooms_sold = 0
    for b in bookings:
        if b["property"] != property_name: continue
        rooms = [r.strip().title() for r in b.get('room_no', '').split(',') if r.strip()]
        if all(r.lower() in inventory_lower for r in rooms):
            rooms_sold += len(rooms)
    return rooms_sold

def get_dashboard_data():
    today = date.today()
    dates = [today - timedelta(days=1), today, today + timedelta(days=1), today + timedelta(days=2)]
    all_bookings = load_bookings_for_date_range(dates[0], dates[3])
    properties = sorted(PROPERTY_INVENTORY.keys())
    data = []
    for prop in properties:
        total_inv = get_total_inventory(prop)
        row = {"Property Name": prop, "Total Inventory": total_inv}
        for d in dates:
            d_str = d.strftime('%Y-%m-%d')
            sold = count_rooms_sold(filter_bookings_for_day(all_bookings, d), prop)
            row[f"{d_str} Sold"] = sold
        data.append(row)
    return data, dates, all_bookings

# === COLOR-CODED % (HTML) ===
def colored_percent_html(occ):
    if occ > 70:
        return f'<span style="color:#10b981; font-weight:bold;">{occ}%</span>'
    elif occ > 50:
        return f'
