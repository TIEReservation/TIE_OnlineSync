import streamlit as st
from datetime import date
import calendar
import pandas as pd
from inventory import load_combined_bookings, filter_bookings_for_day, assign_inventory_numbers, load_properties, PROPERTY_INVENTORY
from typing import List, Dict

def generate_month_dates(year: int, month: int) -> List[date]:
    """Generate list of dates for the given month."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, num_days + 1)]

def compute_daily_totals(bookings: Dict[str, List[Dict]], properties: List[str], day: date) -> Dict:
    """Compute daily totals across all properties for the given day."""
    total_rooms = 0
    total_room_charges = 0.0
    total_gst = 0.0
    total_commission = 0.0
    total_receivable = 0.0
    total_per_night = 0.0

    for prop in properties:
        daily_bookings = filter_bookings_for_day(bookings.get(prop, []), day)
        assigned, _ = assign_inventory_numbers(daily_bookings, prop)
        for booking in assigned:
            rooms = len(booking.get("inventory_no", []))
            total_rooms += rooms
            if booking.get("is_primary", False) and booking.get("target_date") == date.fromisoformat(booking["check_in"]):
                total_room_charges += booking.get("room_charges", 0.0)
                total_gst += booking.get("gst", 0.0)
                total_commission += booking.get("commission", 0.0)
                total_receivable += booking.get("receivable", 0.0)
                total_per_night += booking.get("per_night", 0.0) * rooms

    total_tax_deduction = total_receivable * 0.003  # Assuming 0.3% as per previous example
    total_total = total_room_charges + total_gst

    return {
        "room_count": total_rooms,
        "room_charges": total_room_charges,
        "gst": total_gst,
        "total": total_total,
        "commission": total_commission,
        "tax_deduction": total_tax_deduction,
        "receivable": total_receivable,
        "per_night_receivable": total_per_night
    }

def show_monthly_consolidation():
    """Display the Monthly Consolidated Report for all properties."""
    st.title("📊 Monthly Consolidation")
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5, key="monthly_year")
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1, key="monthly_month")
    
    properties = load_properties()
    if not properties:
        st.info("No properties available.")
        return

    month_dates = generate_month_dates(year, month)
    start_date = month_dates[0]
    end_date = month_dates[-1]

    # Cache bookings for all properties
    bookings = {prop: load_combined_bookings(prop, start_date, end_date) for prop in properties}

    # Prepare table data
    columns = [
        "Particulars", "Room Count", "Room Charges", "GST", "Total",
        "Commission", "Tax Deduction", "Receivable", "Per Night Receivable"
    ]
    table_data = []

    for day in month_dates:
        daily_totals = compute_daily_totals(bookings, properties, day)
        table_data.append({
            "Particulars": f"Day {day.day}",
            "Room Count": daily_totals["room_count"],
            "Room Charges": f"{daily_totals['room_charges']:.2f}",
            "GST": f"{daily_totals['gst']:.2f}",
            "Total": f"{daily_totals['total']:.2f}",
            "Commission": f"{daily_totals['commission']:.2f}",
            "Tax Deduction": f"{daily_totals['tax_deduction']:.2f}",
            "Receivable": f"{daily_totals['receivable']:.2f}",
            "Per Night Receivable": f"{daily_totals['per_night_receivable']:.2f}"
        })

    df = pd.DataFrame(table_data, columns=columns)
    st.dataframe(df, use_container_width=True)
