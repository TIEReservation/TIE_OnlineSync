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

def insert_online_reservation(reservation):
    """Insert a new online reservation into Supabase."""
    try:
        response = supabase.table("online_reservations").insert(reservation).execute()
        return bool(response.data)
    except Exception as e:
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
            hotel_id = str(safe_int(row.get("hotel id", "")))
            property_name = get_property_name(hotel_id)
            if property_name == "Unknown Property":
                property_name = str(row.get("hotel name", "")).split("-")[0].strip() if row.get("hotel name") else ""
            booking_id = str(row.get("booking id", ""))
            if not booking_id:
                continue  # Skip if no booking_id
            if booking_id in existing_ids:
                skipped += 1
                continue
            booking_made_on = parse_date(row.get("booking_made_on"))
            guest_name = str(row.get("customer_name", ""))
            guest_phone = str(row.get("customer_phone", ""))
            check_in = parse_date(row.get("checkin"))
            check_out = parse_date(row.get("checkout"))
            pax_str = str(row.get("pax", ""))
            no_of_adults, no_of_children, no_of_infant = parse_pax(pax_str)
            total_pax = no_of_adults + no_of_children + no_of_infant
            room_no = str(row.get("room ids", ""))
            room_type = str(row.get("room types", ""))
            rate_plans = str(row.get("rate_plans", ""))
            booking_source = str(row.get("booking_source", ""))
            segment = str(row.get("segment", ""))
            staflexi_status = str(row.get("status", ""))
            booking_Confirmed_on = None  # Editable, default None
            booking_amount = safe_float(row.get("booking_amount"))
            total_payment_made = safe_float(row.get("Total Payment Made"))
            balance_due = safe_float(row.get("balance_due"))
            mode_of_booking = ""  # Editable, default empty
            booking_status = staflexi_status.capitalize()  # Map to standard, e.g., "Confirmed"
            if "cancel" in booking_status.lower():
                booking_status = "Cancelled"
            elif "confirm" in booking_status.lower():
                booking_status = "Confirmed"
            # Compute payment_status
            if total_payment_made >= booking_amount:
                payment_status = "Fully Paid"
            elif total_payment_made > 0:
                payment_status = "Partially Paid"
            else:
                payment_status = "Not Paid"
            remarks = str(row.get("special_requests", ""))  # Or ota_special_requests
            submitted_by = ""  # Editable
            modified_by = ""  # Editable
            total_amount_with_services = safe_float(row.get("total_amount_with_services"))
            ota_gross_amount = safe_float(row.get("ota_gross_amount"))
            ota_commission = safe_float(row.get("ota_commission"))
            ota_tax = safe_float(row.get("ota_tax"))
            ota_net_amount = safe_float(row.get("ota_net_amount"))
            room_revenue = safe_float(row.get("room_revenue"))
            reservation = {
                "property": property_name,
                "booking_id": booking_id,
                "booking_made_on": str(booking_made_on) if booking_made_on else None,
                "guest_name": guest_name,
                "guest_phone": guest_phone,
                "check_in": str(check_in) if check_in else None,
                "check_out": str(check_out) if check_out else None,
                "no_of_adults": no_of_adults,
                "no_of_children": no_of_children,
                "no_of_infant": no_of_infant,
                "total_pax": total_pax,
                "room_no": room_no,
                "room_type": room_type,
                "rate_plans": rate_plans,
                "booking_source": booking_source,
                "segment": segment,
                "staflexi_status": staflexi_status,
                "booking_Confirmed_on": booking_Confirmed_on,
                "booking_amount": booking_amount,
                "total_payment_made": total_payment_made,
                "balance_due": balance_due,
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
            if insert_online_reservation(reservation):
                inserted += 1
                st.session_state.online_reservations.append(reservation)
        return inserted, skipped
    except Exception as e:
        st.error(f"Error processing Excel file: {e}")
        return 0, 0

def show_online_reservations():
    """Display online reservations page with upload and view."""
    st.title("📥 Online Reservations")
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
                # Reload to reflect changes
                st.session_state.online_reservations = load_online_reservations_from_supabase()

    # View section
    st.subheader("View Online Reservations")
    if not st.session_state.online_reservations:
        st.info("No online reservations available.")
        return

    df = pd.DataFrame(st.session_state.online_reservations)
    # Basic filters (can expand similar to direct reservations)
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date (Check-In)", value=None)
    with col2:
        end_date = st.date_input("End Date (Check-In)", value=None)
    with col3:
        filter_status = st.selectbox("Filter by Booking Status", ["All", "Pending", "Confirmed", "Cancelled", "Completed", "No Show"])

    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["booking_status"] == filter_status]

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
    else:
        # Display selected columns
        display_columns = [
            "property", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type",
            "booking_status", "payment_status", "booking_amount", "total_payment_made", "balance_due"
        ]
        st.dataframe(filtered_df[display_columns], use_container_width=True)
