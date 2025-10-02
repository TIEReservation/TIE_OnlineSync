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
        "Le Poshe Beach view": {
            "Double Room": ["101", "102", "202", "203", "204"],
            "Standard Room": ["201"],
            "Deluex Double Room Seaview": ["301", "302", "303", "304"]
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"]
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"]
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"]
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "202", "202"]  # Note: duplicate "202" as per data
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"]  # Note: duplicate "404" as per data
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"]
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
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
            "2BHA Studio Room": ["101&102"],
            "2BHA with Balcony": ["202&203", "302&303"],
            "Family Suite": ["201"],
            "Family Room": ["301"],
            "Terrace Room": ["401"]
        },
        "Eden Beach Resort": {
            "Double Room": ["101", "102"],
            "Deluex Room": ["103", "202"],
            "Triple Room": ["201"]
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

def insert_reservation_in_supabase(reservation):
    """Insert a new reservation into Supabase."""
    try:
        response = supabase.table("reservations").insert(reservation).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error inserting reservation: {e}")
        return False

def update_reservation_in_supabase(booking_id, updated_reservation):
    """Update an existing reservation in Supabase."""
    try:
        response = supabase.table("reservations").update(updated_reservation).eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating reservation: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation: {e}")
        return False

def load_reservations_from_supabase():
    """Load reservations from Supabase."""
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def show_new_reservation_form():
    """Display form for adding new direct reservations."""
    st.subheader("New Reservation")
    property_room_map = load_property_room_map()
    
    with st.form("new_reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property Name", list(property_room_map.keys()))
        with col2:
            room_types = list(property_room_map[property_name].keys()) + ["Other"]
            room_type = st.selectbox("Room Type", room_types)
        
        col1, col2 = st.columns(2)
        with col1:
            custom_room_type = st.text_input("Custom Room Type", value="", disabled=room_type != "Other")
        with col2:
            room_numbers = property_room_map[property_name][room_type] if room_type != "Other" else []
            room_no = st.selectbox("Room No", room_numbers) if room_numbers else st.text_input("Room No")
        
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name")
        with col2:
            mobile_no = st.text_input("Mobile No")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            adults = st.number_input("No of Adults", min_value=0, value=0)
        with col2:
            children = st.number_input("No of Children", min_value=0, value=0)
        with col3:
            infants = st.number_input("No of Infants", min_value=0, value=0)
        with col4:
            total_pax = adults + children + infants
            st.text_input("Total Pax", value=total_pax, disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", min_value=date.today())
        with col2:
            check_out = st.date_input("Check Out", min_value=check_in if check_in else date.today())
        
        no_of_days = calculate_days(check_in, check_out)
        st.text_input("No of Days", value=no_of_days, disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            tariff = st.number_input("Tariff per Night", min_value=0.0, step=100.0)
        with col2:
            total_tariff = tariff * no_of_days
            st.text_input("Total Tariff", value=total_tariff, disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, step=100.0)
        with col2:
            balance_amount = total_tariff - advance_amount
            st.text_input("Balance Amount", value=balance_amount, disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            advance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Other"]
            advance_mop = st.selectbox("Advance MOP", advance_mop_options)
        with col2:
            custom_advance_mop = st.text_input("Custom Advance MOP", value="", disabled=advance_mop != "Other")
        
        col1, col2 = st.columns(2)
        with col1:
            balance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Other"]
            balance_mop = st.selectbox("Balance MOP", balance_mop_options)
        with col2:
            custom_balance_mop = st.text_input("Custom Balance MOP", value="", disabled=balance_mop != "Other")
        
        col1, col2 = st.columns(2)
        with col1:
            mob_options = ["Direct", "Online", "Stay-back"]
            mob_value = st.selectbox("MOB", mob_options)
        with col2:
            online_source_options = ["Booking.com", "Expedia", "Agoda", "Others"]
            online_source = st.selectbox("Online Source", online_source_options, disabled=mob_value != "Online")
            custom_online_source = st.text_input("Custom Online Source", value="", disabled=online_source != "Others" or mob_value != "Online")
        
        col1, col2 = st.columns(2)
        with col1:
            invoice_no = st.text_input("Invoice No")
        with col2:
            enquiry_date = st.date_input("Enquiry Date", value=None)
        
        booking_date = st.date_input("Booking Date", value=date.today())
        
        col1, col2 = st.columns(2)
        with col1:
            breakfast = st.selectbox("Breakfast", ["Yes", "No"])
        with col2:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"])
        
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted By")
        with col2:
            modified_by = st.text_input("Modified By")
        
        modified_comments = st.text_area("Modified Comments")
        remarks = st.text_area("Remarks")
        
        payment_status = "Fully Paid" if advance_amount >= total_tariff else "Partially Paid" if advance_amount > 0 else "Not Paid"
        
        if st.form_submit_button("Submit Reservation", use_container_width=True):
            is_duplicate, duplicate_id = check_duplicate_guest(guest_name, mobile_no, room_no, mob=mob_value)
            if is_duplicate:
                st.error(f"Duplicate guest found with Booking ID: {duplicate_id}. Please check the details.")
            else:
                booking_id = generate_booking_id()
                if booking_id:
                    reservation = {
                        "booking_id": booking_id,
                        "property_name": property_name,
                        "room_no": room_no,
                        "guest_name": guest_name,
                        "mobile_no": mobile_no,
                        "no_of_adults": safe_int(adults),
                        "no_of_children": safe_int(children),
                        "no_of_infants": safe_int(infants),
                        "total_pax": total_pax,
                        "check_in": str(check_in) if check_in else None,
                        "check_out": str(check_out) if check_out else None,
                        "no_of_days": no_of_days,
                        "tariff": safe_float(tariff),
                        "total_tariff": safe_float(total_tariff),
                        "advance_amount": safe_float(advance_amount),
                        "balance_amount": balance_amount,
                        "advance_mop": custom_advance_mop if advance_mop == "Other" else advance_mop,
                        "balance_mop": custom_balance_mop if balance_mop == "Other" else balance_mop,
                        "mob": mob_value,
                        "online_source": custom_online_source if online_source == "Others" else online_source,
                        "invoice_no": invoice_no,
                        "enquiry_date": str(enquiry_date) if enquiry_date else None,
                        "booking_date": str(booking_date) if booking_date else None,
                        "room_type": custom_room_type if room_type == "Other" else room_type,
                        "breakfast": breakfast,
                        "booking_status": booking_status,
                        "submitted_by": submitted_by,
                        "modified_by": modified_by,
                        "modified_comments": modified_comments,
                        "remarks": remarks,
                        "payment_status": payment_status
                    }
                    if insert_reservation_in_supabase(reservation):
                        st.session_state.reservations.append(reservation)
                        st.success(f"✅ Reservation {booking_id} created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create reservation")

def show_edit_reservations():
    """Display edit reservations page."""
    st.title("✏️ Edit Direct Reservations")
    
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    
    if not st.session_state.reservations:
        st.info("No direct reservations available to edit.")
        return

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None

    df = pd.DataFrame(st.session_state.reservations)
    display_columns = ["property_name", "booking_id", "guest_name", "check_in", "check_out", "room_no", "room_type", "booking_status"]
    
    st.subheader("Select Reservation to Edit")
    
    # Handle query parameters for pre-selecting booking ID
    booking_ids = df["booking_id"].tolist()
    query_params = st.query_params
    default_index = 0
    if query_params.get("booking_id") and query_params["booking_id"][0] in booking_ids:
        default_index = booking_ids.index(query_params["booking_id"][0])
    
    selected_booking_id = st.selectbox("Select Booking ID", booking_ids, index=default_index)
    
    if selected_booking_id:
        edit_index = df[df["booking_id"] == selected_booking_id].index[0]
        reservation = st.session_state.reservations[edit_index]
        st.session_state.edit_index = edit_index
        st.session_state.edit_mode = True

    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        
        st.subheader(f"Editing Reservation: {reservation['booking_id']}")
        
        property_room_map = load_property_room_map()
        
        # Row 1: Property Name, Booking ID, Booking Date
        col1, col2, col3 = st.columns(3)
        with col1:
            property_name = st.selectbox("Property Name", list(property_room_map.keys()), index=list(property_room_map.keys()).index(reservation.get("property_name", "")) if reservation.get("property_name") in property_room_map else 0)
        with col2:
            booking_id = st.text_input("Booking ID", value=reservation.get("booking_id", ""), disabled=True)
        with col3:
            booking_date = st.date_input("Booking Date", value=date.fromisoformat(reservation.get("booking_date")) if reservation.get("booking_date") else None)

        # Row 2: Room Type, Room No, Guest Name
        col1, col2, col3 = st.columns(3)
        with col1:
            room_types = list(property_room_map[property_name].keys()) + ["Other"]
            room_type = st.selectbox("Room Type", room_types, index=room_types.index(reservation.get("room_type", "")) if reservation.get("room_type") in room_types else len(room_types)-1)
        with col2:
            room_numbers = property_room_map[property_name][room_type] if room_type != "Other" else []
            room_no = st.selectbox("Room No", room_numbers, index=room_numbers.index(reservation.get("room_no", "")) if reservation.get("room_no") in room_numbers else 0) if room_numbers else st.text_input("Room No", value=reservation.get("room_no", ""))
        with col3:
            guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))

        # Row 3: Mobile No, Check In, Check Out
        col1, col2, col3 = st.columns(3)
        with col1:
            mobile_no = st.text_input("Mobile No", value=reservation.get("mobile_no", ""))
        with col2:
            check_in = st.date_input("Check In", value=date.fromisoformat(reservation.get("check_in")) if reservation.get("check_in") else None)
        with col3:
            check_out = st.date_input("Check Out", value=date.fromisoformat(reservation.get("check_out")) if reservation.get("check_out") else None)

        # Row 4: No of Adults, No of Children, No of Infants, Total Pax
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            adults = st.number_input("No of Adults", value=safe_int(reservation.get("no_of_adults", 0)), min_value=0)
        with col2:
            children = st.number_input("No of Children", value=safe_int(reservation.get("no_of_children", 0)), min_value=0)
        with col3:
            infants = st.number_input("No of Infants", value=safe_int(reservation.get("no_of_infants", 0)), min_value=0)
        with col4:
            total_pax = adults + children + infants
            st.text_input("Total Pax", value=total_pax, disabled=True)

        # Row 5: Tariff, Total Tariff, Advance Amount
        col1, col2, col3 = st.columns(3)
        with col1:
            tariff = st.number_input("Tariff per Night", value=safe_float(reservation.get("tariff", 0.0)), min_value=0.0)
        with col2:
            no_of_days = calculate_days(check_in, check_out)
            total_tariff = tariff * no_of_days
            st.text_input("Total Tariff", value=total_tariff, disabled=True)
        with col3:
            advance_amount = st.number_input("Advance Amount", value=safe_float(reservation.get("advance_amount", 0.0)), min_value=0.0)

        # Row 6: Balance Amount, Advance MOP, Balance MOP
        col1, col2, col3 = st.columns(3)
        with col1:
            balance_amount = total_tariff - advance_amount
            st.text_input("Balance Amount", value=balance_amount, disabled=True)
        with col2:
            advance_mop_options = ["Cash", "Card", "UPI", "Bank Transfer", "Other"]
            advance_mop = st.selectbox("Advance MOP", advance_mop_options, index=advance_mop_options.index(reservation.get("advance_mop", "")) if reservation.get("advance_mop") in advance_mop_options else len(advance_mop_options)-1)
        with col3:
            custom_advance_mop = st.text_input("Custom Advance MOP", value=reservation.get("advance_mop", "") if advance_mop == "Other" else "", disabled=advance_mop != "Other")

        # Row 7: MOB, Online Source, Invoice No
        col1, col2, col3 = st.columns(3)
        with col1:
            mob_options = ["Direct", "Online", "Stay-back"]
            mob_value = st.selectbox("MOB", mob_options, index=mob_options.index(reservation.get("mob", "")) if reservation.get("mob") in mob_options else 0)
        with col2:
            online_source_options = ["Booking.com", "Expedia", "Agoda", "Others"]
            online_source = st.selectbox("Online Source", online_source_options, index=online_source_options.index(reservation.get("online_source", "")) if reservation.get("online_source") in online_source_options else len(online_source_options)-1, disabled=mob_value != "Online")
            custom_online_source = st.text_input("Custom Online Source", value=reservation.get("online_source", "") if online_source == "Others" else "", disabled=online_source != "Others" or mob_value != "Online")
        with col3:
            invoice_no = st.text_input("Invoice No", value=reservation.get("invoice_no", ""))

        # Row 8: Enquiry Date, Breakfast, Booking Status
        col1, col2, col3 = st.columns(3)
        with col1:
            enquiry_date = st.date_input("Enquiry Date", value=date.fromisoformat(reservation.get("enquiry_date")) if reservation.get("enquiry_date") else None)
        with col2:
            breakfast = st.selectbox("Breakfast", ["Yes", "No"], index=["Yes", "No"].index(reservation.get("breakfast", "No")))
        with col3:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Completed", "No Show"].index(reservation.get("booking_status", "Pending")))

        # Row 9: Submitted By, Modified By
        col1, col2 = st.columns(2)
        with col1:
            submitted_by = st.text_input("Submitted By", value=reservation.get("submitted_by", ""))
        with col2:
            modified_by = st.text_input("Modified By", value=reservation.get("modified_by", ""))

        # Row 10: Modified Comments, Remarks
        modified_comments = st.text_area("Modified Comments", value=reservation.get("modified_comments", ""))
        remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))

        payment_status = "Fully Paid" if advance_amount >= total_tariff else "Partially Paid" if advance_amount > 0 else "Not Paid"

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Update Reservation", use_container_width=True):
                updated_reservation = {
                    "property_name": property_name,
                    "booking_id": booking_id,
                    "room_no": room_no,
                    "guest_name": guest_name,
                    "mobile_no": mobile_no,
                    "no_of_adults": safe_int(adults),
                    "no_of_children": safe_int(children),
                    "no_of_infants": safe_int(infants),
                    "total_pax": total_pax,
                    "check_in": str(check_in) if check_in else None,
                    "check_out": str(check_out) if check_out else None,
                    "no_of_days": no_of_days,
                    "tariff": safe_float(tariff),
                    "total_tariff": safe_float(total_tariff),
                    "advance_amount": safe_float(advance_amount),
                    "balance_amount": balance_amount,
                    "advance_mop": custom_advance_mop if advance_mop == "Other" else advance_mop,
                    "balance_mop": custom_balance_mop if balance_mop == "Other" else balance_mop,
                    "mob": mob_value,
                    "online_source": custom_online_source if online_source == "Others" else online_source,
                    "invoice_no": invoice_no,
                    "enquiry_date": str(enquiry_date) if enquiry_date else None,
                    "booking_date": str(booking_date) if booking_date else None,
                    "room_type": custom_room_type if room_type == "Other" else room_type,
                    "breakfast": breakfast,
                    "booking_status": booking_status,
                    "submitted_by": submitted_by,
                    "modified_by": modified_by,
                    "modified_comments": modified_comments,
                    "remarks": remarks,
                    "payment_status": payment_status
                }
                if update_reservation_in_supabase(reservation["booking_id"], updated_reservation):
                    st.session_state.reservations[edit_index] = {**reservation, **updated_reservation}
                    st.session_state.edit_mode = False
                    st.session_state.edit_index = None
                    st.success(f"✅ Reservation {reservation['booking_id']} updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update reservation")
        with col_btn2:
            if st.session_state.role == "Management":
                if st.button("🗑️ Delete Reservation", use_container_width=True):
                    if delete_reservation_in_supabase(reservation["booking_id"]):
                        st.session_state.reservations.pop(edit_index)
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.success(f"🗑️ Reservation {reservation['booking_id']} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete reservation")

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
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["property_name"].unique()), key="analytics_filter_property")

    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["booking_status"] == filter_status]
    if filter_check_in_date:
        filtered_df = filtered_df[filtered_df["check_in"] == str(filter_check_in_date)]
    if filter_check_out_date:
        filtered_df = filtered_df[filtered_df["check_out"] == str(filter_check_out_date)]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["property_name"] == filter_property]

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        property_counts = filtered_df["property_name"].value_counts().reset_index()
        property_counts.columns = ["property_name", "Reservation Count"]
        fig_pie = px.pie(
            property_counts,
            values="Reservation Count",
            names="property_name",
            title="Reservation Distribution by Property",
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="analytics_pie_chart")
    with col2:
        revenue_by_property = filtered_df.groupby("property_name")["total_tariff"].sum().reset_index()
        fig_bar = px.bar(
            revenue_by_property,
            x="property_name",
            y="total_tariff",
            title="Total Revenue by Property",
            height=400,
            labels={"total_tariff": "Revenue (₹)"}
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="analytics_bar_chart")
