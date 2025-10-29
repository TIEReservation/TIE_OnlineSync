import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(filename='dashboard.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Property synonym mapping (from inventory.py)
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

# Property inventory mapping (from inventory.py)
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

def get_total_inventory(property_name):
    """Calculate total inventory excluding Day Use and No Show rooms."""
    inventory = PROPERTY_INVENTORY.get(property_name, {"all": []})["all"]
    return len([inv for inv in inventory if not inv.startswith(("Day Use", "No Show"))])

def sanitize_string(value, default="Unknown"):
    """Convert value to string, handling None and non-string types."""
    return str(value).strip() if value is not None else default

def safe_int(value, default=0):
    """Safely convert value to int."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def normalize_booking(booking, is_online):
    """Normalize booking dict to common schema."""
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
        if days < 0:
            return None
        if days == 0:
            days = 1
        
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
    """Load all bookings for the date range."""
    all_bookings = []
    
    try:
        # Load online reservations
        online_response = supabase.table("online_reservations").select("*").gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute()
        for b in (online_response.data or []):
            normalized = normalize_booking(b, True)
            if normalized:
                all_bookings.append(normalized)
        
        # Load direct reservations
        direct_response = supabase.table("reservations").select("*").gte("check_in", str(start_date)).lte("check_out", str(end_date)).execute()
        for b in (direct_response.data or []):
            normalized = normalize_booking(b, False)
            if normalized:
                all_bookings.append(normalized)
        
        logging.info(f"Loaded {len(all_bookings)} bookings for date range {start_date} to {end_date}")
        return all_bookings
    except Exception as e:
        st.error(f"Error loading bookings: {e}")
        logging.error(f"Error loading bookings: {e}")
        return []

def filter_bookings_for_day(bookings, target_date):
    """Filter bookings that are active on the target date."""
    filtered = []
    for b in bookings:
        try:
            check_in = date.fromisoformat(b["check_in"])
            check_out = date.fromisoformat(b["check_out"])
            
            # Booking is active if target_date >= check_in and target_date < check_out
            if target_date >= check_in and target_date < check_out:
                filtered.append(b)
        except Exception as e:
            logging.warning(f"Error filtering booking {b.get('booking_id', 'Unknown')}: {e}")
    
    return filtered

def count_rooms_sold(bookings, property_name):
    """Count total rooms sold for a property on a specific date."""
    rooms_sold = 0
    inventory = PROPERTY_INVENTORY.get(property_name, {"all": []})["all"]
    inventory_lower = [i.lower() for i in inventory]
    
    for b in bookings:
        if b["property"] != property_name:
            continue
        
        room_no = b.get('room_no', '').strip()
        inventory_no = [r.strip().title() for r in room_no.split(',') if r.strip()]
        
        if not inventory_no:
            continue
        
        # Validate rooms
        valid = all(r.lower() in inventory_lower for r in inventory_no)
        if valid:
            rooms_sold += len(inventory_no)
    
    return rooms_sold

def get_dashboard_data():
    """Fetch dashboard data for yesterday, today, tomorrow, and day after tomorrow."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    
    dates = [yesterday, today, tomorrow, day_after_tomorrow]
    
    # Load bookings for the entire range
    start_date = yesterday
    end_date = day_after_tomorrow
    all_bookings = load_bookings_for_date_range(start_date, end_date)
    
    # Get all properties
    properties = sorted(PROPERTY_INVENTORY.keys())
    
    # Build dashboard data
    dashboard_data = []
    
    for prop in properties:
        total_inventory = get_total_inventory(prop)
        row = {
            "Property Name": prop,
            "Total Inventory": total_inventory
        }
        
        for target_date in dates:
            date_str = target_date.strftime('%Y-%m-%d')
            daily_bookings = filter_bookings_for_day(all_bookings, target_date)
            rooms_sold = count_rooms_sold(daily_bookings, prop)
            rooms_unsold = total_inventory - rooms_sold
            
            row[f"{date_str} Sold"] = rooms_sold
            row[f"{date_str} Unsold"] = rooms_unsold
        
        dashboard_data.append(row)
    
    return dashboard_data, dates

def show_dashboard():
    """Display the dashboard with real inventory data."""
    st.title("🎯 Game Changers Dashboard")
    
    # Add refresh button
    if st.button("🔄 Refresh Dashboard Data"):
        st.cache_data.clear()
        st.rerun()
    
    try:
        dashboard_data, dates = get_dashboard_data()
        
        if not dashboard_data:
            st.info("No data available.")
            return
        
        # Create DataFrame
        df = pd.DataFrame(dashboard_data)
        
        # Calculate totals row
        totals = {"Property Name": "TOTAL", "Total Inventory": df["Total Inventory"].sum()}
        for target_date in dates:
            date_str = target_date.strftime('%Y-%m-%d')
            totals[f"{date_str} Sold"] = df[f"{date_str} Sold"].sum()
            totals[f"{date_str} Unsold"] = df[f"{date_str} Unsold"].sum()
        
        # Add totals row
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
        
        # Format date columns for display
        yesterday_str = dates[0].strftime('%b %d')
        today_str = dates[1].strftime('%b %d')
        tomorrow_str = dates[2].strftime('%b %d')
        day_after_str = dates[3].strftime('%b %d')
        
        # Rename columns for better display
        display_df = df.copy()
        display_df.columns = [
            "Property Name",
            "Total Inv",
            f"{yesterday_str} Sold",
            f"{yesterday_str} Unsold",
            f"{today_str} Sold",
            f"{today_str} Unsold",
            f"{tomorrow_str} Sold",
            f"{tomorrow_str} Unsold",
            f"{day_after_str} Sold",
            f"{day_after_str} Unsold"
        ]
        
        # Display header info
        st.markdown(f"### 📊 Dashboard for {yesterday_str} to {day_after_str}")
        st.markdown("---")
        
        # Style the dataframe
        def highlight_totals(row):
            if row["Property Name"] == "TOTAL":
                return ['background-color: #e6f3ff; font-weight: bold'] * len(row)
            return [''] * len(row)
        
        styled_df = display_df.style.apply(highlight_totals, axis=1)
        
        # Display table
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Display summary metrics
        st.markdown("---")
        st.subheader("📈 Summary Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label=f"{yesterday_str} Occupancy",
                value=f"{totals[dates[0].strftime('%Y-%m-%d') + ' Sold']} / {totals['Total Inventory']}"
            )
        
        with col2:
            st.metric(
                label=f"{today_str} Occupancy",
                value=f"{totals[dates[1].strftime('%Y-%m-%d') + ' Sold']} / {totals['Total Inventory']}"
            )
        
        with col3:
            st.metric(
                label=f"{tomorrow_str} Occupancy",
                value=f"{totals[dates[2].strftime('%Y-%m-%d') + ' Sold']} / {totals['Total Inventory']}"
            )
        
        with col4:
            st.metric(
                label=f"{day_after_str} Occupancy",
                value=f"{totals[dates[3].strftime('%Y-%m-%d') + ' Sold']} / {totals['Total Inventory']}"
            )
        
    except Exception as e:
        st.error(f"Error generating dashboard: {e}")
        logging.error(f"Dashboard error: {e}")

if __name__ == "__main__":
    show_dashboard()
