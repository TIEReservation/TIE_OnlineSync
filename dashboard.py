# dashboard.py

import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import pandas as pd  # Ensure this line is present
import altair as alt
from online_reservation import load_online_reservations_from_supabase
from directreservation import load_reservations_from_supabase

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

def get_property_name(booking):
    return booking.get("property") or booking.get("property_name")

@st.cache_data(ttl=300)
def cached_load_all_bookings():
    online = load_online_reservations_from_supabase()
    direct = load_reservations_from_supabase()
    # normalize properties
    for b in online:
        if "property" in b:
            b["property"] = property_mapping.get(b["property"], b["property"])
        b["source"] = "online"
        b["submitted_by"] = "online"
    for b in direct:
        if "property_name" in b:
            b["property_name"] = property_mapping.get(b["property_name"], b["property_name"])
        b["source"] = "direct"
        if "plan_status" in b:
            b["booking_status"] = b["plan_status"]
    return online + direct

def filter_bookings_for_day(bookings, target_date):
    filtered = []
    for b in bookings:
        try:
            check_in = date.fromisoformat(b["check_in"]) if b.get("check_in") else None
            check_out = date.fromisoformat(b["check_out"]) if b.get("check_out") else None
            if check_in and check_out and check_in <= target_date < check_out:
                filtered.append(b)
        except:
            pass
    return filtered

def count_status(properties, target_date, statuses):
    relevant = [b for b in all_bookings if get_property_name(b) in properties]
    active = filter_bookings_for_day(relevant, target_date)
    count = len([b for b in active if b.get("booking_status") in statuses])
    return count

def count_status_person(properties, target_date, statuses, person):
    relevant = [b for b in all_bookings if get_property_name(b) in properties and b.get("submitted_by", "").lower() == person.lower()]
    active = filter_bookings_for_day(relevant, target_date)
    count = len([b for b in active if b.get("booking_status") in statuses])
    return count

teams = {
    "Game Changers": {
        "members": ["Shan", "Barathan", "Anand"],
        "properties": {
            "Le Park Resort": 6,
            "Le Royce Villa": 4,
            "Villa Shakti": 11,
            "Le Poshe Luxury": 18,
            "La Millionaire Resort": 22
        },
        "total_inventory": 61
    },
    "Dream Squad": {
        "members": ["Nandhini", "Thilak", "Prakash"],
        "properties": {
            "Eden Beach Resort": 5,
            "La Paradise Luxury": 6,
            "La Villa Heritage": 7,
            "Le Pondy Beachside": 4,
            "Le Poshe Beach view": 10,
            "Le Poshe Suite": 9
        },
        "total_inventory": 41
    }
}

individuals = {
    "Barath": {"properties": {"La Antilia Luxury": 10}},
    "Rajesh": {"properties": {"La Tamara Luxury": 22}},
    "Bala": {"properties": {"La Tamara Suite": 10}}
}

def show_dashboard():
    st.title("Gamified Reservation Dashboard")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing data...")
        st.rerun()
    
    global all_bookings
    all_bookings = cached_load_all_bookings()
    
    ref_date = st.date_input("Select Reference Date", date(2025, 10, 27))  # Default to current date (08:53 PM IST, Oct 27, 2025)
    dates = [ref_date - timedelta(days=1), ref_date, ref_date + timedelta(days=1), ref_date + timedelta(days=2)]
    date_names = [d.strftime("%Y-%m-%d") for d in dates]  # Yesterday, Today, Tomorrow, Day After Tomorrow
    
    tab1, tab2, tab3 = st.tabs(["Team Competition", "Individual Performance", "Property Performance"])
    
    with tab1:
        st.subheader("Team Competition View")
        
        team_metrics = {}
        for team_name, team_data in teams.items():
            props = list(team_data["properties"].keys())
            total_inv = team_data["total_inventory"]
            metrics = []
            for d in dates:
                sold = count_status(props, d, ["Confirmed"])
                follow = count_status(props, d, ["Follow-up"])
                pend = count_status(props, d, ["Pending"])
                avail = total_inv - sold - follow - pend  # Total unsold includes follow-up and pending
                metrics.append({"sold": sold, "unsold": avail})
            team_metrics[team_name] = {"metrics": metrics, "total_inv": total_inv}
            total_sold = sum(m["sold"] for m in metrics)
            avg_occ = (total_sold / (total_inv * len(dates))) * 100 if total_inv > 0 else 0
            team_metrics[team_name]["avg_occ"] = avg_occ

        # Prepare table data
        table_data = []
        table_data.append(["Game Changers"])  # Row 1
        table_data.append(["Property Names", "Team (Total Inv)"] + [f"{date_names[0]} Sold", f"{date_names[0]} Unsold",
                                                                  f"{date_names[1]} Sold", f"{date_names[1]} Unsold",
                                                                  f"{date_names[2]} Sold", f"{date_names[2]} Unsold",
                                                                  f"{date_names[3]} Sold", f"{date_names[3]} Unsold"])  # Row 2
        for team_name, data in team_metrics.items():
            row = [""] * 2  # Blank for Property Names and Team (Total Inv) in Row 3
            row.extend([m["sold"] for m in data["metrics"]] + [m["unsold"] for m in data["metrics"]])
            table_data.append(row)

        # Convert to DataFrame for display
        df = pd.DataFrame(table_data, columns=["Property Names", "Team (Total Inv)", 
                                              f"{date_names[0]} Sold", f"{date_names[0]} Unsold",
                                              f"{date_names[1]} Sold", f"{date_names[1]} Unsold",
                                              f"{date_names[2]}
