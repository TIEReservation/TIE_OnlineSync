import streamlit as st
import pandas as pd
from datetime import datetime
import re
from supabase import create_client, Client
from utils import safe_int, safe_float, get_property_name

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def parse_date(dt_str):
    """Parse date string with or without time."""
    if not dt_str or pd.isna(dt_str):
        return None
    try:
        return datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S").date()
    except ValueError:
        try:
            return datetime.strptime(dt_str, "%d/%m/%Y").date()
        except ValueError:
            return None

def parse_pax(pax_str):
    """Parse pax string to get adults, children, infants."""
    adults = 0
    children = 0
    infants = 0
    if not pax_str or pd.isna(pax_str):
        return adults, children, infants
    # Normalize spaces
    pax_str = re.sub(r'\s*,\s*', ',', pax_str)
    parts = pax_str.split(',')
    for part in parts:
        part = part.strip()
        if 'Adults:' in part:
            try:
                adults += int(part.split('Adults:')[1].strip())
            except ValueError:
                pass
        elif 'Children:' in part:
            try:
                children += int(part.split('Children:')[1].strip())
            except ValueError:
                pass
        elif 'Infant:' in part:
            try:
                infants += int(part.split('Infant:')[1].strip())
            except ValueError:
                pass
    return adults, children, infants

def truncate_string(value, max_length=50):
    """Truncate string to specified length."""
    if not value:
        return value
    return str(value)[:max_length] if len(str(value)) > max_length else str(value)

def insert_online_reservation(reservation):
    """Insert a new online reservation into Supabase."""
    try:
        # Truncate string fields to prevent database errors
        truncated_reservation = reservation.copy()
        
        # List of fields that might have character limits
        string_fields_50 = [
            "property", "booking_id", "guest_name", "guest_phone", "room_no", 
            "room_type", "rate_plans", "booking_source", "segment", "staflexi_status",
            "mode_of_booking", "booking_status", "payment_status", "submitted_by", "modified_by"
        ]
        
        # Truncate to 50 characters for standard fields
        for field in string_fields_50:
            if field in truncated_reservation:
                truncated_reservation[field] = truncate_string(truncated_reservation[field], 50)
        
        # Remarks might have a longer limit, but let's be safe and truncate to 500
        if "remarks" in truncated_reservation:
            truncated_reservation["remarks"] = truncate_string(truncated_reservation["remarks"], 500)
        
        response = supabase.table("online_reservations").insert(truncated_reservation).execute()
        return bool(response.data)
    except Exception as e:
        if '23505' in str(e) and 'duplicate key value' in str(e).lower():
            return False  # Silently skip duplicate booking_id errors
        st.error(f"Error inserting online reservation: {e}")
        return False

def load_online_reservations_from_supabase():
    """Load online reservations from Supabase."""
    try:
        response = supabase.table("online_reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def process_and_sync_excel(uploaded_file):
    """Process the uploaded Excel file and sync to DB."""
    try:
        df = pd.read_excel(uploaded_file, header=0)
        if df.empty:
            st.warning("Uploaded file is empty.")
            return 0, 0
        # Get existing booking_ids
        existing_reservations = load_online_reservations_from_supabase()
        existing_ids = {r["booking_id"] for r in existing_reservations}
        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            property_name = get_property_name(row.get("Property"))
            booking_id = truncate_string(row.get("Booking ID"))
            guest_name = truncate_string(row.get("Guest Name"))
            guest_phone = truncate_string(row.get("Mobile No"))
            check_in = parse_date(row.get("Check In"))
            check_out = parse_date(row.get("Check Out"))
            adults, children, infants = parse_pax(row.get("Pax"))
            total_pax = adults + children + infants
            room_no = truncate_string(row.get("Room No"))
            room_type = truncate_string(row.get("Room Type"))
            rate_plans = truncate_string(row.get("Breakfast"))
            booking_source = truncate_string(row.get("Booking Source"))
            segment = truncate_string(row.get("Segment"))
            staflexi_status = truncate_string(row.get("Staflexi Status"))
            booking_made_on = parse_date(row.get("Booking Made On"))
            booking_confirmed_on = parse_date(row.get("Booking Confirmed On"))
            booking_amount = safe_float(row.get("Total Tariff"))
            total_payment_made = safe_float(row.get("Advance Amount"))
            balance_due = booking_amount - total_payment_made
            advance_mop = truncate_string(row.get("Advance Mop"))
            balance_mop = truncate_string(row.get("Balance Mop"))
            mode_of_booking = truncate_string(row.get("MOB"))
            booking_status = truncate_string(row.get("Booking Status", "Pending"))
            payment_status = truncate_string(row.get("Payment Status", "Not Paid"))
            remarks = truncate_string(row.get("Remarks"), 500)
            submitted_by = truncate_string(row.get("Submitted by"))
            modified_by = truncate_string(row.get("Modified by"))
            total_amount_with_services = safe_float(row.get("Total Amount with Services"))
            ota_gross_amount = safe_float(row.get("OTA Gross Amount"))
            ota_commission = safe_float(row.get("OTA Commission"))
            ota_tax = safe_float(row.get("OTA Tax"))
            ota_net_amount = safe_float(row.get("OTA Net Amount"))
            room_revenue = safe_float(row.get("Room Revenue"))

            reservation = {
                "property": property_name,
                "booking_id": booking_id,
                "booking_made_on": str(booking_made_on) if booking_made_on else None,
                "guest_name": guest_name,
                "guest_phone": guest_phone,
                "check_in": str(check_in) if check_in else None,
                "check_out": str(check_out) if check_out else None,
                "no_of_adults": adults,
                "no_of_children": children,
                "no_of_infant": infants,
                "total_pax": total_pax,
                "room_no": room_no,
                "room_type": room_type,
                "rate_plans": rate_plans,
                "booking_source": booking_source,
                "segment": segment,
                "staflexi_status": staflexi_status,
                "booking_confirmed_on": str(booking_confirmed_on) if booking_confirmed_on else None,
                "booking_amount": booking_amount,
                "total_payment_made": total_payment_made,
                "balance_due": balance_due,
                "advance_mop": advance_mop,
                "balance_mop": balance_mop,
                "mode_of_booking": mode_of_booking,
                "booking_status": booking_status,
                "payment_status": payment_status,
                "remarks": remarks,
                "submitted_by": submitted_by,
                "modified_by": modified_by,
                "total_amount_with_services": total_amount_with_services,
                "ota_gross_amount": ota_gross_amount,
                "ota_commission": ota_commission,
                "ota_tax": ota_tax,
                "ota_net_amount": ota_net_amount,
                "room_revenue": room_revenue
            }
            if reservation["booking_id"] in existing_ids:
                skipped += 1
                continue
            if insert_online_reservation(reservation):
                inserted += 1
                st.session_state.online_reservations.append(reservation)
        return inserted, skipped
    except Exception as e:
        st.error(f"Error processing Excel file: {e}")
        return 0, 0

def show_online_reservations():
    """Display online reservations page with upload and view."""
    st.title("🔥 Online Reservations")
    if 'online_reservations' not in st.session_state:
        st.session_state.online_reservations = load_online_reservations_from_supabase()

    # Upload and Sync section
    st.subheader("Upload and Sync Excel File")
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        if st.button("🔄 Sync to Database"):
            with st.spinner("Processing and syncing..."):
                inserted, skipped = process_and_sync_excel(uploaded_file)
                st.success(f"✅ Synced successfully! Inserted: {inserted}, Skipped (duplicates): {skipped}")
                # Reload to reflect changes, clear cache for other pages
                st.cache_data.clear()  # Added: Clear app-wide cache after data change
                st.session_state.online_reservations = load_online_reservations_from_supabase()  # Added: Fully reload from DB
                st.rerun()  # Added: Rerun to immediately reflect

    # View section
    st.subheader("View Online Reservations")
    if not st.session_state.online_reservations:
        st.info("No online reservations available.")
        return

    df = pd.DataFrame(st.session_state.online_reservations)
    # Enhanced filters
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Start Date (Check-In)", value=None)
    with col2:
        end_date = st.date_input("End Date (Check-In)", value=None)
    with col3:
        filter_status = st.selectbox("Filter by Booking Status", ["All", "Pending", "Confirmed", "Cancelled", "Completed", "No Show"])
    with col4:
        # Get unique properties for filter
        properties = ["All"] + sorted(df["property"].dropna().unique().tolist())
        filter_property = st.selectbox("Filter by Property", properties)

    # Sorting option
    sort_order = st.radio("Sort by Check-In Date", ["Descending (Newest First)", "Ascending (Oldest First)"], index=0)

    filtered_df = df.copy()
    # Apply filters
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["booking_status"] == filter_status]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["property"] == filter_property]

    # Apply sorting
    if sort_order == "Ascending (Oldest First)":
        filtered_df = filtered_df.sort_values(by="check_in", ascending=True)
    else:
        filtered_df = filtered_df.sort_values(by="check_in", ascending=False)

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
    else:
        # Display selected columns
        display_columns = [
            "property", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type",
            "booking_status", "payment_status", "booking_amount", "total_payment_made", "balance_due"
        ]
        st.dataframe(filtered_df[display_columns], use_container_width=True)
