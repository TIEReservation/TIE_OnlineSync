# directreservation.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

def load_property_room_map():
    """
    Loads the property to room type to room numbers mapping based on provided data.
    Keys and values are kept as-is from the user's input, including typos and combined rooms.
    Returns a nested dictionary: {"Property": {"Room Type": ["Room No", ...], ...}, ...}
    """
    return {
        "Le Poshe Beachview": {
            "Deluex Room": ["101", "102", "202", "203", "204"],
            "Standard Room": ["201"],
            "Deluex Double Room Seaview": ["301", "302", "303", "304"]
        },
        "La Millionare Resort": {
            "Deluex Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303", "402"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308", "401"]
        },
        "Le Poshe Luxury": {
            "Two Bedroom Appartment": ["101&102", "101", "102"],
            "Two Bedroom Appartment with Balcony": ["201&202", "301&302", "401&402"],
            "Three Bedroom Appartment": ["203to205", "303to305", "403to405"],
            "Double with Terrace": ["501"],
            "Double Room": ["D1", "D2", "D3", "D4", "D5"]
        },
        "Le Poshe Suite": {
            "Two Bedroom Suite": ["601&602", "603&604", "703&704"],
            "King Suite with Balcony": ["701&702"],
            "Double Room with Terrace": ["801"],
            "One Bedroom": ["602", "702", "604", "704"]
        },
        "La Paradise Residency": {
            "Deluxe Double Room": ["101", "102", "103", "301", "304"],
            "Deluxe Family Suite": ["201", "203"],
            "Deluxe Triple Room": ["202", "303"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "Singleroom", "TwoRooms", "ThreeRooms"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "102", "202"]
        },
        "La Tamara Luxury": {
            "Three Bedroom Villa": ["101to103", "104to106", "104", "105", "106", "201to203", "204to206", "204", "205", "206", "301to303", "304to306", "304", "305", "306"],
            "Superior Villa": ["401to404"],
            "Standard Double Room": ["101", "103", "201", "203", "301", "303"],
            "Standard Triple Room": ["102", "202", "302"],
            "Deluxe Double Room": ["402", "404"],
            "Deluxe Quadruple Room": ["401"],
            "Deluxe Triple Room": ["403"]
        },
        "La Antilia": {
            "Deluex Suite": ["101"],
            "Deluex Double": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite with Tarrace": ["404"]
        },
        "La Tamara Suite": {
            "Deluxe Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"]
        },
        "Le Park Resort": {
            "Villa with Swimming Pool View": ["555&666", "555", "666"],
            "Villa with Garden View": ["111&222", "111", "222"],
            "Family Retreate Villa": ["333&444", "333", "444"]
        },
        "Villa Shakti": {
            "Two Bedroom Villa": ["101&102"],
            "Two Bedroom with Balcony": ["202&203", "302&303"],
            "Family Suite": ["201"],
            "Family Room": ["301"],
            "Terrace Room": ["401"]
        },
        "Eden Beach Resort": {
            "Double Room": ["101", "102"],
            "Deluex Double Room": ["103", "202"],
            "Triple Room with Balcony": ["201"]
        }
    }

def generate_booking_id():
    """Generate a unique booking ID by checking existing IDs in Supabase."""
    try:
        today = datetime.now().strftime('%Y%m%d')
        response = supabase.table("reservations").select("booking_id").like("booking_id", f"TIE{today}%").execute()
        existing_ids = [record["booking_id"] for record in response.data]
        sequence = 1
        while f"TIE{today}{sequence:03d}" in existing_ids:
            sequence += 1
        return f"TIE{today}{sequence:03d}"
    except Exception as e:
        st.error(f"Error generating booking ID: {e}")
        return None

def check_duplicate_guest(guest_name, mobile_no, room_no, exclude_booking_id=None, mob=None):
    """Check for duplicate guest based on name, mobile number, and room number, allowing 'Stay-back' if MOB differs."""
    try:
        response = supabase.table("reservations").select("*").execute()
        for reservation in response.data:
            if exclude_booking_id and reservation["booking_id"] == exclude_booking_id:
                continue
            if (reservation["guest_name"].lower() == guest_name.lower() and
                    reservation["mobile_no"] == mobile_no and
                    reservation["room_no"] == room_no):
                if mob == "Stay-back" and reservation["mob"] != "Stay-back":
                    continue
                return True, reservation["booking_id"]
        return False, None
    except Exception as e:
        st.error(f"Error checking duplicate guest: {e}")
        return False, None

def calculate_days(check_in, check_out):
    """Calculate the number of days between check-in and check-out dates."""
    if check_in and check_out and check_out >= check_in:
        delta = check_out - check_in
        return max(1, delta.days)
    return 0

def safe_int(value, default=0):
    """Safely convert value to int, return default if conversion fails."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float, return default if conversion fails."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def parse_date(dt_str):
    """Parse date string with or without time."""
    if not dt_str or pd.isna(dt_str):
        return None
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def load_reservations_from_supabase():
    """Load reservations from Supabase, handling potential None values."""
    try:
        response = supabase.table("reservations").select("*").execute()
        reservations = []
        for record in response.data:
            reservation = {
                "Booking ID": record["booking_id"],
                "Property Name": record["property_name"] or "",
                "Room No": record["room_no"] or "",
                "Guest Name": record["guest_name"] or "",
                "Mobile No": record["mobile_no"] or "",
                "No of Adults": safe_int(record["no_of_adults"]),
                "No of Children": safe_int(record["no_of_children"]),
                "No of Infants": safe_int(record["no_of_infants"]),
                "Total Pax": safe_int(record["total_pax"]) if "total_pax" in record else (safe_int(record["no_of_adults"]) + safe_int(record["no_of_children"]) + safe_int(record["no_of_infants"])),
                "Check In": parse_date(record["check_in"]) if record["check_in"] else None,
                "Check Out": parse_date(record["check_out"]) if record["check_out"] else None,
                "No of Days": safe_int(record["no_of_days"]),
                "Tariff": safe_float(record["tariff"]),
                "Total Tariff": safe_float(record["total_tariff"]),
                "Advance Amount": safe_float(record["advance_amount"]),
                "Balance Amount": safe_float(record["balance_amount"]),
                "Advance MOP": record["advance_mop"] or "",
                "Balance MOP": record["balance_mop"] or "",
                "MOB": record["mob"] or "",
                "Online Source": record["online_source"] or "",
                "Invoice No": record["invoice_no"] or "",
                "Enquiry Date": parse_date(record["enquiry_date"]) if record["enquiry_date"] else None,
                "Booking Date": parse_date(record["booking_date"]) if record["booking_date"] else None,
                "Room Type": record["room_type"] or "",
                "Breakfast": record["breakfast"] or "",
                "Booking Status": record["booking_status"] or "",
                "Submitted By": record["submitted_by"] or "",
                "Modified By": record["modified_by"] or "",
                "Modified Comments": record["modified_comments"] or "",
                "Remarks": record["remarks"] or "",
                "Payment Status": record["payment_status"] or ""
            }
            reservations.append(reservation)
        return reservations
    except Exception as e:
        st.error(f"Error loading reservations from Supabase: {e}")
        return []

# Placeholder for truncated functions (assuming they exist elsewhere or can be stubbed)
def update_reservation_in_supabase(booking_id, updated_reservation):
    st.error("update_reservation_in_supabase not implemented in this snippet.")
    return False

def delete_reservation_in_supabase(booking_id):
    st.error("delete_reservation_in_supabase not implemented in this snippet.")
    return False

def show_confirmation_dialog(booking_id, is_update=False):
    st.error("show_confirmation_dialog not implemented in this snippet.")

def display_filtered_analysis(df, start_date, end_date, view_mode=False):
    st.error("display_filtered_analysis not implemented in this snippet.")
    return df.copy()

def show_new_reservation_form():
    st.error("show_new_reservation_form not implemented in this snippet.")

def show_reservations():
    st.error("show_reservations not implemented in this snippet.")

def show_edit_reservations():
    st.error("show_edit_reservations not implemented in this snippet.")
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        form_key = f"edit_form_{edit_index}"
        
        st.subheader(f"Editing Reservation: {reservation['Booking ID']}")
        
        # Row 1: Property Name, Room No, Guest Name, Mobile No
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            property_name = st.selectbox("Property Name", options=sorted(load_property_room_map().keys()), index=sorted(load_property_room_map().keys()).index(reservation["Property Name"]) if reservation["Property Name"] in load_property_room_map() else 0, key=f"{form_key}_property")
        with col2:
            room_options = load_property_room_map().get(property_name, {}).get(reservation["Room Type"], [])
            room_no = st.selectbox("Room No", options=room_options, index=room_options.index(reservation["Room No"]) if reservation["Room No"] in room_options else 0, key=f"{form_key}_room")
        with col3:
            guest_name = st.text_input("Guest Name", value=reservation["Guest Name"], key=f"{form_key}_guest")
        with col4:
            mobile_no = st.text_input("Mobile No", value=reservation["Mobile No"], key=f"{form_key}_mobile")

        # Row 2: No of Adults, No of Children, No of Infants, Total Pax
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            adults = st.number_input("No of Adults", value=safe_int(reservation["No of Adults"]), min_value=0, key=f"{form_key}_adults")
        with col2:
            children = st.number_input("No of Children", value=safe_int(reservation["No of Children"]), min_value=0, key=f"{form_key}_children")
        with col3:
            infants = st.number_input("No of Infants", value=safe_int(reservation["No of Infants"]), min_value=0, key=f"{form_key}_infants")
        with col4:
            total_pax = adults + children + infants
            st.text_input("Total Pax", value=total_pax, disabled=True, key=f"{form_key}_total_pax")

        # Row 3: Check In, Check Out, No of Days
        col1, col2, col3 = st.columns(3)
        with col1:
            check_in = st.date_input("Check In", value=reservation["Check In"] if reservation["Check In"] else date.today(), key=f"{form_key}_check_in")
        with col2:
            check_out = st.date_input("Check Out", value=reservation["Check Out"] if reservation["Check Out"] else date.today() + timedelta(days=1), key=f"{form_key}_check_out")
        with col3:
            no_of_days = calculate_days(check_in, check_out)
            st.text_input("No of Days", value=no_of_days, disabled=True, key=f"{form_key}_days")

        # Row 4: Tariff, Total Tariff, Advance Amount
        col1, col2, col3 = st.columns(3)
        with col1:
            tariff = st.number_input("Tariff", value=safe_float(reservation["Tariff"]), min_value=0.0, key=f"{form_key}_tariff")
        with col2:
            total_tariff = tariff * no_of_days
            st.text_input("Total Tariff", value=total_tariff, disabled=True, key=f"{form_key}_total_tariff")
        with col3:
            advance_amount = st.number_input("Advance Amount", value=safe_float(reservation["Advance Amount"]), min_value=0.0, key=f"{form_key}_advance")

        # Row 5: Balance Amount, Advance MOP, Balance MOP
        col1, col2, col3 = st.columns(3)
        with col1:
            balance_amount = total_tariff - advance_amount
            st.text_input("Balance Amount", value=balance_amount, disabled=True, key=f"{form_key}_balance")
        with col2:
            advance_mop_options = ["Cash", "Card", "UPI", "Other"]
            advance_mop = st.selectbox("Advance MOP", options=advance_mop_options, index=advance_mop_options.index(reservation["Advance MOP"]) if reservation["Advance MOP"] in advance_mop_options else 0, key=f"{form_key}_advance_mop")
            custom_advance_mop = st.text_input("Custom Advance MOP", value=reservation["Advance MOP"] if advance_mop == "Other" else "", key=f"{form_key}_custom_advance_mop", disabled=advance_mop != "Other")
        with col3:
            balance_mop_options = ["Cash", "Card", "UPI", "Other"]
            balance_mop = st.selectbox("Balance MOP", options=balance_mop_options, index=balance_mop_options.index(reservation["Balance MOP"]) if reservation["Balance MOP"] in balance_mop_options else 0, key=f"{form_key}_balance_mop")
            custom_balance_mop = st.text_input("Custom Balance MOP", value=reservation["Balance MOP"] if balance_mop == "Other" else "", key=f"{form_key}_custom_balance_mop", disabled=balance_mop != "Other")

        # Row 6: MOB, Online Source, Invoice No
        col1, col2, col3 = st.columns(3)
        with col1:
            mob_options = ["Walk-in", "Corporate", "Stay-back", "Others"]
            mob = st.selectbox("MOB", options=mob_options, index=mob_options.index(reservation["MOB"]) if reservation["MOB"] in mob_options else 0, key=f"{form_key}_mob")
            custom_mob = st.text_input("Custom MOB", value=reservation["MOB"] if mob == "Others" else "", key=f"{form_key}_custom_mob", disabled=mob != "Others")
        with col2:
            online_source_options = ["Website", "OTA", "Travel Agent", "Others"]
            online_source = st.selectbox("Online Source", options=online_source_options, index=online_source_options.index(reservation["Online Source"]) if reservation["Online Source"] in online_source_options else 0, key=f"{form_key}_online_source")
            custom_online_source = st.text_input("Custom Online Source", value=reservation["Online Source"] if online_source == "Others" else "", key=f"{form_key}_custom_online_source", disabled=online_source != "Others")
        with col3:
            invoice_no = st.text_input("Invoice No", value=reservation["Invoice No"], key=f"{form_key}_invoice")

        # Row 7: Enquiry Date, Booking Date
        col1, col2 = st.columns(2)
        with col1:
            enquiry_date = st.date_input("Enquiry Date", value=reservation["Enquiry Date"] if reservation["Enquiry Date"] else None, key=f"{form_key}_enquiry")
        with col2:
            booking_date = st.date_input("Booking Date", value=reservation["Booking Date"] if reservation["Booking Date"] else date.today(), key=f"{form_key}_booking")

        # Row 8: Room Type, Breakfast
        col1, col2 = st.columns(2)
        with col1:
            room_type_options = list(load_property_room_map().get(property_name, {}).keys()) + ["Other"]
            room_type = st.selectbox("Room Type", options=room_type_options, index=room_type_options.index(reservation["Room Type"]) if reservation["Room Type"] in room_type_options else 0, key=f"{form_key}_room_type")
            custom_room_type = st.text_input("Custom Room Type", value=reservation["Room Type"] if room_type == "Other" else "", key=f"{form_key}_custom_room_type", disabled=room_type != "Other")
        with col2:
            breakfast = st.checkbox("Breakfast", value=reservation["Breakfast"] == "Yes", key=f"{form_key}_breakfast")

        # Row 9: Booking Status
        col1 = st.columns(1)[0]
        with col1:
            booking_status_options = ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"]
            booking_status = st.selectbox("Booking Status", options=booking_status_options, index=booking_status_options.index(reservation["Booking Status"]) if reservation["Booking Status"] in booking_status_options else 0, key=f"{form_key}_status")

        # Row 10: Submitted By, Modified By, Modified Comments
        col1, col2, col3 = st.columns(3)
        with col1:
            submitted_by = st.text_input("Submitted By", value=reservation["Submitted By"], key=f"{form_key}_submitted")
        with col2:
            modified_by = st.text_input("Modified By", value=reservation["Modified By"], key=f"{form_key}_modified")
        with col3:
            modified_comments = st.text_input("Modified Comments", value=reservation["Modified Comments"], key=f"{form_key}_modified_comments")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Save Reservation", key=f"{form_key}_update", use_container_width=True):
                if not all([property_name, room_no, guest_name, mobile_no]):
                    st.error("❌ Please fill in all required fields")
                elif check_out < check_in:
                    st.error("❌ Check-out date must be on or after check-in")
                elif no_of_days < 0:
                    st.error("❌ Number of days cannot be negative")
                else:
                    mob_value = custom_mob if mob == "Others" else mob
                    is_duplicate, existing_booking_id = check_duplicate_guest(guest_name, mobile_no, room_no, exclude_booking_id=reservation["Booking ID"], mob=mob_value)
                    if is_duplicate:
                        st.error(f"❌ Guest already exists! Booking ID: {existing_booking_id}")
                    else:
                        updated_reservation = {
                            "Property Name": property_name,
                            "Room No": room_no,
                            "Guest Name": guest_name,
                            "Mobile No": mobile_no,
                            "No of Adults": safe_int(adults),
                            "No of Children": safe_int(children),
                            "No of Infants": safe_int(infants),
                            "Total Pax": total_pax,
                            "Check In": check_in,
                            "Check Out": check_out,
                            "No of Days": no_of_days,
                            "Tariff": safe_float(tariff),
                            "Total Tariff": safe_float(total_tariff),
                            "Advance Amount": safe_float(advance_amount),
                            "Balance Amount": balance_amount,
                            "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                            "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                            "MOB": mob_value,
                            "Online Source": custom_online_source if online_source == "Others" else online_source,
                            "Invoice No": invoice_no,
                            "Enquiry Date": enquiry_date,
                            "Booking Date": booking_date,
                            "Booking ID": reservation["Booking ID"],
                            "Room Type": custom_room_type if room_type == "Other" else room_type,
                            "Breakfast": "Yes" if breakfast else "No",
                            "Booking Status": booking_status,
                            "Submitted By": submitted_by,
                            "Modified By": modified_by,
                            "Modified Comments": modified_comments,
                            "Remarks": remarks,
                            "Payment Status": payment_status
                        }
                        if update_reservation_in_supabase(reservation["Booking ID"], updated_reservation):
                            st.session_state.reservations[edit_index] = updated_reservation
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"✅ Reservation {reservation['Booking ID']} updated successfully!")
                            show_confirmation_dialog(reservation["Booking ID"], is_update=True)
                        else:
                            st.error("❌ Failed to update reservation")
        with col_btn2:
            if st.session_state.role == "Management":
                if st.button("🗑️ Delete Reservation", key=f"{form_key}_delete", use_container_width=True):
                    if delete_reservation_in_supabase(reservation["Booking ID"]):
                        st.session_state.reservations.pop(edit_index)
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")
        # End of show_edit_reservations function
    except Exception as e:
        st.error(f"Error rendering edit form: {e}")

def show_analytics():
    """Display analytics dashboard for Management users."""
    if st.session_state.role != "Management":
        st.error("❌ Access Denied: Analytics is available only for Management users.")
        return

    st.header("📊 Analytics Dashboard")
    if not st.session_state.reservations:
        st.info("No reservations available for analysis.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    
    st.subheader("Filters")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="analytics_filter_start_date", help="Filter by Check In date range (optional)")
    with col2:
        end_date = st.date_input("End Date", value=None, key="analytics_filter_end_date", help="Filter by Check In date range (optional)")
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Completed", "No Show"], key="analytics_filter_status")
    with col4:
        filter_check_in_date = st.date_input("Check-in Date", value=None, key="analytics_filter_check_in_date")
    with col5:
        filter_check_out_date = st.date_input("Check-out Date", value=None, key="analytics_filter_check_out_date")
    with col6:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].unique()), key="analytics_filter_property")

    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
    if filter_check_in_date:
        filtered_df = filtered_df[filtered_df["Check In"] == filter_check_in_date]
    if filter_check_out_date:
        filtered_df = filtered_df[filtered_df["Check Out"] == filter_check_out_date]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        property_counts = filtered_df["Property Name"].value_counts().reset_index()
        property_counts.columns = ["Property Name", "Reservation Count"]
        fig_pie = px.pie(
            property_counts,
            values="Reservation Count",
            names="Property Name",
            title="Reservation Distribution by Property",
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="analytics_pie_chart")
    with col2:
        revenue_by_property = filtered_df.groupby("Property Name")["Total Tariff"].sum().reset_index()
        fig_bar = px.bar(
            revenue_by_property,
            x="Property Name",
            y="Total Tariff",
            title="Total Revenue by Property",
            height=400,
            labels={"Total Tariff": "Revenue (₹)"}
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="analytics_bar_chart")
