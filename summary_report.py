import streamlit as st
from datetime import date
import calendar
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Property inventory (reused from inventory.py or similar)
PROPERTY_INVENTORY = {
    "Le Poshe Beach view": {"all": ["101","102","201","202","203","204","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
    "La Millionaire Resort": {"all": ["101","102","103","105","201","202","203","204","205","206","207","208","301","302","303","304","305","306","307","308","401","402","Day Use 1","Day Use 2","Day Use 3","Day Use 4","Day Use 5","No Show"]},
    "Le Poshe Luxury": {"all": ["101","102","201","202","203","204","205","301","302","303","304","305","401","402","403","404","405","501","Day Use 1","Day Use 2","No Show"]},
    "Le Poshe Suite": {"all": ["601","602","603","604","701","702","703","704","801","Day Use 1","Day Use 2","No Show"]},
    "La Paradise Residency": {"all": ["101","102","103","201","202","203","301","302","303","304","Day Use 1","Day Use 2","No Show"]},
    "La Paradise Luxury": {"all": ["101","102","103","201","202","203","Day Use 1","Day Use 2","No Show"]},
    "La Villa Heritage": {"all": ["101","102","103","201","202","203","301","Day Use 1","Day Use 2","No Show"]},
    "Le Pondy Beach Side": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"]},
    "Le Royce Villa": {"all": ["101","102","201","202","Day Use 1","Day Use 2","No Show"]},
    "La Tamara Luxury": {"all": ["101","102","103","104","105","106","201","202","203","204","205","206","301","302","303","304","305","306","401","402","403","404","Day Use 1","Day Use 2","No Show"]},
    "La Antilia Luxury": {"all": ["101","201","202","203","204","301","302","303","304","401","Day Use 1","Day Use 2","No Show"]},
    "La Tamara Suite": {"all": ["101","102","103","104","201","202","203","204","205","206","Day Use 1","Day Use 2","No Show"]},
    "Le Park Resort": {"all": ["111","222","333","444","555","666","Day Use 1","Day Use 2","No Show"]},
    "Villa Shakti": {"all": ["101","102","201","201A","202","203","301","301A","302","303","401","Day Use 1","Day Use 2","No Show"]},
    "Eden Beach Resort": {"all": ["101","102","103","201","202","Day Use 1","Day Use 2","No Show"]}
}

# Helper functions (adapted from inventory.py and monthlyconsolidation.py)
def load_properties() -> List[str]:
    """Load unique properties from reservations and online_reservations tables."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set()
        for r in res_direct + res_online:
            prop = r.get('property_name') or r.get('property')
            if prop:
                properties.add(prop)
        return sorted(properties)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def load_combined_bookings(property_name: str, start_date: date, end_date: date) -> List[Dict]:
    """Load combined direct and online bookings for a property within date range."""
    try:
        direct_bookings = supabase.table("reservations").select("*").eq("property_name", property_name).gte("check_in", str(start_date)).lt("check_out", str(end_date + timedelta(days=1))).execute().data or []
        online_bookings = supabase.table("online_reservations").select("*").eq("property", property_name).gte("check_in", str(start_date)).lt("check_out", str(end_date + timedelta(days=1))).execute().data or []
        combined = direct_bookings + online_bookings
        return combined
    except Exception as e:
        st.error(f"Error loading bookings for {property_name}: {e}")
        return []

def filter_bookings_for_day(bookings: List[Dict], target_date: date) -> List[Dict]:
    """Filter bookings active on the target date."""
    return [b for b in bookings if date.fromisoformat(b["check_in"]) <= target_date < date.fromisoformat(b["check_out"])]

def assign_inventory_numbers(daily_bookings: List[Dict], property_name: str) -> (List[Dict], List[Dict]):
    """Assign inventory numbers (simplified for counting)."""
    assigned = []
    for booking in daily_bookings:
        # Simulate assignment by counting rooms; actual logic can be expanded if needed
        rooms_count = 1  # Placeholder; in real, parse room_no or similar
        booking["inventory_no"] = [f"room_{i}" for i in range(rooms_count)]  # Dummy
        assigned.append(booking)
    return assigned, []  # No overbookings for simplicity

def compute_daily_metrics(bookings: List[Dict], property_name: str, day: date) -> Dict:
    """Compute metrics for a property on a specific day."""
    daily_bookings = filter_bookings_for_day(bookings, day)
    assigned, _ = assign_inventory_numbers(daily_bookings, property_name)
    
    rooms_sold = sum(len(booking.get("inventory_no", [])) for booking in assigned)
    room_charges = sum(booking.get("room_charges", booking.get("booking_amount", 0.0)) for booking in assigned if booking.get("is_primary", True) and date.fromisoformat(booking["check_in"]) == day)
    gst = sum(booking.get("gst", 0.0) for booking in assigned if booking.get("is_primary", True) and date.fromisoformat(booking["check_in"]) == day)
    total = room_charges + gst
    commission = sum(booking.get("commission", booking.get("ota_commission", 0.0)) for booking in assigned if booking.get("is_primary", True) and date.fromisoformat(booking["check_in"]) == day)
    receivable = total - commission  # Simplified; adjust if needed
    tax_deduction = receivable * 0.003  # Assuming 0.3%
    receivable_per_night = receivable / rooms_sold if rooms_sold > 0 else 0.0
    
    return {
        "rooms_sold": rooms_sold,
        "room_charges": room_charges,
        "gst": gst,
        "total": total,
        "commission": commission,
        "tax_deduction": tax_deduction,
        "receivable": receivable,
        "receivable_per_night": receivable_per_night
    }

def generate_report(properties: List[str], month_dates: List[date], bookings: Dict[str, List[Dict]], metric: str) -> pd.DataFrame:
    """Generate a DataFrame for a specific metric."""
    data = []
    property_totals = {prop: 0.0 for prop in properties}
    grand_total = 0.0
    
    for day in month_dates:
        row = {"Date": day.strftime("%Y-%m-%d")}
        day_total = 0.0
        for prop in properties:
            metrics = compute_daily_metrics(bookings.get(prop, []), prop, day)
            value = metrics.get(metric, 0.0)
            row[prop] = value
            day_total += value
            property_totals[prop] += value
        row["Total"] = day_total
        grand_total += day_total
        data.append(row)
    
    # Add total row
    total_row = {"Date": "Total"}
    for prop in properties:
        total_row[prop] = property_totals[prop]
    total_row["Total"] = grand_total
    data.append(total_row)
    
    return pd.DataFrame(data)

def show_summary_report():
    """Display the Summary Report with all sections."""
    st.title("TIE Hotels & Resort Summary Report")
    
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)
    
    properties = load_properties()
    if not properties:
        st.info("No properties available.")
        return
    
    month_dates = [date(year, month, day) for day in range(1, calendar.monthrange(year, month)[1] + 1)]
    start_date = month_dates[0]
    end_date = month_dates[-1]
    
    # Load bookings once
    bookings = {prop: load_combined_bookings(prop, start_date, end_date) for prop in properties}
    
    reports = {
        "rooms_report": ("TIE Hotels & Resort Rooms Report", "rooms_sold"),
        "room_charges_report": ("TIE Hotels & Resort Room Charges Report", "room_charges"),
        "gst_report": ("TIE Hotels & Resort GST Report", "gst"),
        "total_report": ("TIE Hotels & Resort Total Report", "total"),
        "commission_report": ("TIE Hotels & Resort Commission Report", "commission"),
        "tax_deduction_report": ("TIE Hotels & Resort Tax Deduction Report", "tax_deduction"),
        "receivable_report": ("TIE Hotels & Resort Receivable Report", "receivable"),
        "receivable_per_night_report": ("TIE Hotels & Resort Receivable Per Night Report", "receivable_per_night")
    }
    
    for key, (title, metric) in reports.items():
        st.subheader(title)
        df = generate_report(properties, month_dates, bookings, metric)
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    show_summary_report()
