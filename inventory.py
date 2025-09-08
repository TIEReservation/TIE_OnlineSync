import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def load_properties() -> list[str]:
    """Load unique properties from both tables without merging variations."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set(r['property_name'] for r in res_direct if r['property_name']) | set(r['property'] for r in res_online if r['property'])
        return sorted(properties)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def normalize_booking(booking: dict, is_online: bool) -> dict:
    """Normalize booking dict to common schema."""
    payment_status = booking.get('payment_status', '').title()
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        st.warning(f"Skipping booking {booking.get('booking_id')} with invalid payment status: {payment_status}")
        return None
    try:
        normalized = {
            'booking_id': booking.get('booking_id'),
            'room_no': booking.get('room_no'),
            'guest_name': booking.get('guest_name'),
            'mobile_no': booking.get('guest_phone') if is_online else booking.get('mobile_no'),
            'total_pax': booking.get('total_pax'),
            'check_in': date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None,
            'check_out': date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None,
            'booking_status': booking.get('booking_status'),
            'payment_status': payment_status,
            'remarks': booking.get('remarks')
        }
        if not normalized['check_in'] or not normalized['check_out']:
            st.warning(f"Skipping booking {booking.get('booking_id')} with missing check-in/check-out dates")
            return None
        return normalized
    except Exception as e:
        st.error(f"Error normalizing booking {booking.get('booking_id')}: {e}")
        return None

def load_combined_bookings(property: str, start_date: date, end_date: date) -> list[dict]:
    """Load bookings overlapping the date range for the property with paid statuses."""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        # Fetch direct bookings
        direct = supabase.table("reservations").select("*").eq("property_name", property)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"]).execute().data
        st.info(f"Fetched {len(direct)} direct bookings for {property} from {start_str} to {end_str}")
        # Fetch online bookings
        online = supabase.table("online_reservations").select("*").eq("property", property)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"]).execute().data
        st.info(f"Fetched {len(online)} online bookings for {property} from {start_str} to {end_str}")
        # Normalize and filter
        normalized = [b for b in [normalize_booking(b, False) for b in direct] + [normalize_booking(b, True) for b in online] if b]
        if len(normalized) < len(direct) + len(online):
            st.warning(f"Skipped {len(direct) + len(online) - len(normalized)} bookings with invalid data for {property}")
        return normalized
    except Exception as e:
        st.error(f"Error loading bookings for {property}: {e}")
        return []

def filter_bookings_for_day(bookings: list[dict], day: date) -> list[dict]:
    """Filter bookings active on the given day."""
    return [b for b in bookings if b['check_in'] and b['check_out'] and b['check_in'] <= day < b['check_out']]

def generate_month_dates(year: int, month: int) -> list[date]:
    """Generate all dates in the month."""
    _, num_days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, num_days + 1)]

@st.cache_data
def cached_load_properties():
    return load_properties()

@st.cache_data
def cached_load_bookings(property, start_date, end_date):
    return load_combined_bookings(property, start_date, end_date)

def show_daily_status():
    """Main function to display daily status screen."""
    st.title("📅 Daily Status")

    # Cache-clearing button
    if st.button("🔄 Refresh Property List"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing properties...")
        st.rerun()

    # Year and Month selection
    current_year = date.today().year
    year = st.selectbox("Select Year", list(range(current_year - 5, current_year + 6)), index=5)
    month = st.selectbox("Select Month", list(range(1, 13)), index=date.today().month - 1)

    properties = cached_load_properties()
    if not properties:
        st.info("No properties available.")
        return

    # List properties
    st.subheader("Properties")
    for prop in properties:
        with st.expander(f"{prop}"):
            month_dates = generate_month_dates(year, month)
            start_date = month_dates[0]
            end_date = month_dates[-1] + timedelta(days=1)  # For exclusive check_out
            bookings = cached_load_bookings(prop, start_date, end_date - timedelta(days=1))
            st.info(f"Total bookings for {prop}: {len(bookings)}")

            for day in month_dates:
                daily_bookings = filter_bookings_for_day(bookings, day)
                if daily_bookings:
                    # Build DataFrame
                    df_data = []
                    for b in daily_bookings:
                        days = (b['check_out'] - b['check_in']).days if b['check_in'] and b['check_out'] else 0
                        df_data.append({
                            'Room No': b['room_no'],
                            'Booking ID': b['booking_id'],
                            'Guest Name': b['guest_name'],
                            'Mobile No': b['mobile_no'],
                            'Total Pax': b['total_pax'],
                            'Check-in Date': b['check_in'],
                            'Check-out Date': b['check_out'],
                            'Days': days,
                            'Booking Status': b['booking_status'],
                            'Payment Status': b['payment_status'],
                            'Remarks': b['remarks']
                        })
                    df = pd.DataFrame(df_data).sort_values('Room No')
                    df['Inventory No'] = range(len(df))  # Sequential index
                    df = df[['Inventory No', 'Room No', 'Booking ID', 'Guest Name', 'Mobile No', 'Total Pax',
                             'Check-in Date', 'Check-out Date', 'Days', 'Booking Status', 'Payment Status', 'Remarks']]
                    st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.subheader(f"{prop} - {day.strftime('%B %d, %Y')}")
                    st.info("No active bookings on this day.")
