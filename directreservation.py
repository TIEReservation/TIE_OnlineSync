import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from utils import safe_int, safe_float, calculate_days, generate_booking_id, check_duplicate_guest

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
            "Deluex Double Room Seaview": ["301", "302", "303", "304"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use" : ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show" : ["No Show"]
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "302", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "201", "202"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Le Park Resort": {
            "Villa with Swimming Pool View": ["555&666", "555", "666"],
            "Villa with Garden View": ["111&222", "111", "222"],
            "Family Retreate Villa": ["333&444", "333", "444"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Villa Shakti": {
            "2BHA Studio Room": ["101&102"],
            "2BHA with Balcony": ["202&203", "302&303"],
            "Family Suite": ["201"],
            "Family Room": ["301"],
            "Terrace Room": ["401"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        },
        "Eden Beach Resort": {
            "Double Room": ["101", "102"],
            "Deluex Room": ["103", "202"],
            "Triple Room": ["201"],
            "Day Use" : ["Day Use 1", "Day Use 2"],
            "No Show" : ["No Show"]
        }
    }

def generate_booking_id():
    """Generate a unique booking ID by checking existing IDs in Supabase."""
    return generate_booking_id(supabase, "reservations")

def insert_reservation_in_supabase(reservation):
    """Insert a new reservation into Supabase."""
    try:
        response = supabase.table("reservations").insert(reservation).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error inserting reservation: {e}")
        return False

def update_reservation_in_supabase(booking_id, updated_reservation):
    """Update a reservation in Supabase."""
    try:
        response = supabase.table("reservations").update(updated_reservation).eq("Booking ID", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("Booking ID", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def load_reservations_from_supabase(properties=None):
    """Load all reservations from Supabase, filtered by properties if provided."""
    try:
        all_data = []
        offset = 0
        limit = 1000
        while True:
            query = supabase.table("reservations").select("*").range(offset, offset + limit - 1)
            if properties:
                query = query.in_("property_name", properties)
            response = query.execute()
            data = response.data if response.data else []
            all_data.extend(data)
            if len(data) < limit:
                break
            offset += limit
        if not all_data:
            st.warning("No reservations found in the database.")
        return all_data
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def show_confirmation_dialog(booking_id, is_update=False):
    """Show a confirmation dialog with a link to view the reservation."""
    action = "updated" if is_update else "created"
    st.markdown(
        f"""
        <div style='background-color: #e6f3ff; padding: 15px; border-radius: 5px;'>
            <p style='margin: 0; font-size: 16px;'>Reservation {booking_id} {action} successfully!</p>
            <a href='?page=View+Reservations&booking_id={booking_id}' target='_self' style='color: #1E90FF; text-decoration: none;'>View Reservation</a>
        </div>
        """,
        unsafe_allow_html=True
    )

def show_new_reservation_form():
    """Display the new reservation form."""
    st.header("📝 New Reservation")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase(st.session_state.properties)
    
    with st.form("new_reservation_form"):
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property Name", sorted(load_property_room_map().keys()), index=0)
            room_types = list(load_property_room_map()[property_name].keys())
            room_type = st.selectbox("Room Type", room_types, index=0)
            room_numbers = load_property_room_map()[property_name][room_type]
            room_no = st.selectbox("Room No", room_numbers, index=0)
        with col2:
            guest_name = st.text_input("Guest Name")
            guest_phone = st.text_input("Guest Phone")
        col3, col4 = st.columns(2)
        with col3:
            check_in = st.date_input("Check In", value=date.today())
            check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1))
        with col4:
            no_of_adults = st.number_input("No of Adults", min_value=0, value=1, step=1)
            no_of_children = st.number_input("No of Children", min_value=0, value=0, step=1)
        col5, col6 = st.columns(2)
        with col5:
            no_of_infant = st.number_input("No of Infant", min_value=0, value=0, step=1)
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.write(f"Total Pax: {total_pax}")
        with col6:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, value=0.0, step=100.0)
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=0.0, step=100.0)
        balance_amount = total_tariff - advance_amount if total_tariff >= advance_amount else 0.0
        st.write(f"Balance Amount: {balance_amount:.2f}")
        col7, col8 = st.columns(2)
        with col7:
            advance_mop_options = ["Cash", "UPI", "Card", "Other"]
            advance_mop = st.selectbox("Advance MOP", advance_mop_options, index=0)
            if advance_mop == "Other":
                custom_advance_mop = st.text_input("Custom Advance MOP")
            else:
                custom_advance_mop = ""
        with col8:
            balance_mop_options = ["Cash", "UPI", "Card", "Other"]
            balance_mop = st.selectbox("Balance MOP", balance_mop_options, index=0)
            if balance_mop == "Other":
                custom_balance_mop = st.text_input("Custom Balance MOP")
            else:
                custom_balance_mop = ""
        col9, col10 = st.columns(2)
        with col9:
            mob_value = st.text_input("MOB")
            online_source_options = ["Booking.com", "Agoda", "Expedia", "Others"]
            online_source = st.selectbox("Online Source", online_source_options, index=0)
            if online_source == "Others":
                custom_online_source = st.text_input("Custom Online Source")
            else:
                custom_online_source = ""
        with col10:
            invoice_no = st.text_input("Invoice No")
            enquiry_date = st.date_input("Enquiry Date", value=date.today())
            booking_date = st.date_input("Booking Date", value=date.today())
        col11, col12 = st.columns(2)
        with col11:
            breakfast = st.checkbox("Breakfast Included")
            booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=0)
        with col12:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=0)
        remarks = st.text_area("Remarks")
        col13, col14 = st.columns(2)
        with col13:
            submitted_by = st.text_input("Submitted By")
        with col14:
            modified_by = st.text_input("Modified By")
            modified_comments = st.text_area("Modified Comments")
        
        if st.session_state.permissions.get("add", False):
            if st.form_submit_button("💾 Save Reservation", use_container_width=True):
                is_duplicate, existing_id = check_duplicate_guest(supabase, "reservations", guest_name, guest_phone, room_no)
                if is_duplicate:
                    st.error(f"Duplicate guest found with Booking ID: {existing_id}. Please check the details.")
                else:
                    booking_id = generate_booking_id()
                    if not booking_id:
                        st.error("Failed to generate Booking ID.")
                        return
                    reservation = {
                        "Property Name": property_name,
                        "Guest Name": guest_name,
                        "Guest Phone": guest_phone,
                        "Check In": str(check_in),
                        "Check Out": str(check_out),
                        "No of Adults": safe_int(no_of_adults),
                        "No of Children": safe_int(no_of_children),
                        "No of Infant": safe_int(no_of_infant),
                        "Total Pax": safe_int(total_pax),
                        "Room No": room_no,
                        "Total Tariff": safe_float(total_tariff),
                        "Advance Amount": safe_float(advance_amount),
                        "Balance Amount": balance_amount,
                        "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                        "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                        "MOB": mob_value,
                        "Online Source": custom_online_source if online_source == "Others" else online_source,
                        "Invoice No": invoice_no,
                        "Enquiry Date": str(enquiry_date),
                        "Booking Date": str(booking_date),
                        "Booking ID": booking_id,
                        "Room Type": room_type if room_type != "Other" else "",
                        "Breakfast": breakfast,
                        "Booking Status": booking_status,
                        "Submitted By": submitted_by,
                        "Modified By": modified_by,
                        "Modified Comments": modified_comments,
                        "Remarks": remarks,
                        "Payment Status": payment_status
                    }
                    if insert_reservation_in_supabase(reservation):
                        st.session_state.reservations.append(reservation)
                        st.success(f"✅ Reservation {booking_id} created successfully!")
                        show_confirmation_dialog(booking_id)
                    else:
                        st.error("❌ Failed to save reservation")
        else:
            st.info("You do not have permission to add reservations.")

def show_reservations():
    """Display the reservations table with filters."""
    st.header("📋 View Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase(st.session_state.properties)
    
    if not st.session_state.reservations:
        st.info("No reservations available.")
        return
    
    df = pd.DataFrame(st.session_state.reservations)
    
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="filter_start_date")
    with col2:
        end_date = st.date_input("End Date", value=None, key="filter_end_date")
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="filter_status")
    with col4:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].unique()), key="filter_property")
    
    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["Property Name"] == filter_property]
    
    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
        return
    
    display_columns = [
        "Booking ID", "Property Name", "Guest Name", "Check In", "Check Out", 
        "Room No", "Room Type", "Total Tariff", "Advance Amount", "Balance Amount", 
        "Booking Status", "Payment Status"
    ]
    filtered_df["Booking ID"] = filtered_df["Booking ID"].apply(
        lambda x: f'<a href="?page=Edit+Reservations&booking_id={x}" target="_self">{x}</a>'
    )
    st.markdown(filtered_df[display_columns].to_html(escape=False), unsafe_allow_html=True)

def show_edit_reservations():
    """Display edit reservations page."""
    st.header("✏️ Edit Reservations")
    
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase(st.session_state.properties)
    
    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None
    
    df = pd.DataFrame(st.session_state.reservations)
    booking_id_list = df["Booking ID"].tolist()
    selected_booking_id = st.session_state.get('selected_booking_id')
    default_index = booking_id_list.index(selected_booking_id) if selected_booking_id in booking_id_list else 0
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_list, index=default_index, key="edit_booking_id_select")
    
    if selected_booking_id:
        try:
            edit_index = df[df["Booking ID"] == selected_booking_id].index[0]
            st.session_state.edit_index = edit_index
            st.session_state.edit_mode = True
        except IndexError:
            st.error(f"Booking ID {selected_booking_id} not found.")
            return
    
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        edit_index = st.session_state.edit_index
        reservation = st.session_state.reservations[edit_index]
        form_key = f"edit_form_{reservation['Booking ID']}"
        
        try:
            with st.form(form_key):
                col1, col2 = st.columns(2)
                with col1:
                    property_name = st.selectbox("Property Name", sorted(load_property_room_map().keys()), index=sorted(load_property_room_map().keys()).index(reservation["Property Name"]), key=f"{form_key}_property")
                    room_types = list(load_property_room_map()[property_name].keys())
                    room_type = st.selectbox("Room Type", room_types, index=room_types.index(reservation["Room Type"]) if reservation["Room Type"] in room_types else 0, key=f"{form_key}_room_type")
                    room_numbers = load_property_room_map()[property_name][room_type]
                    room_no = st.selectbox("Room No", room_numbers, index=room_numbers.index(reservation["Room No"]) if reservation["Room No"] in room_numbers else 0, key=f"{form_key}_room_no")
                with col2:
                    guest_name = st.text_input("Guest Name", value=reservation["Guest Name"], key=f"{form_key}_guest_name")
                    guest_phone = st.text_input("Guest Phone", value=reservation["Guest Phone"], key=f"{form_key}_guest_phone")
                col3, col4 = st.columns(2)
                with col3:
                    check_in = st.date_input("Check In", value=date.fromisoformat(reservation["Check In"]), key=f"{form_key}_check_in")
                    check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["Check Out"]), key=f"{form_key}_check_out")
                with col4:
                    no_of_adults = st.number_input("No of Adults", min_value=0, value=safe_int(reservation["No of Adults"]), step=1, key=f"{form_key}_adults")
                    no_of_children = st.number_input("No of Children", min_value=0, value=safe_int(reservation["No of Children"]), step=1, key=f"{form_key}_children")
                col5, col6 = st.columns(2)
                with col5:
                    no_of_infant = st.number_input("No of Infant", min_value=0, value=safe_int(reservation["No of Infant"]), step=1, key=f"{form_key}_infant")
                    total_pax = no_of_adults + no_of_children + no_of_infant
                    st.write(f"Total Pax: {total_pax}")
                with col6:
                    total_tariff = st.number_input("Total Tariff", min_value=0.0, value=safe_float(reservation["Total Tariff"]), step=100.0, key=f"{form_key}_tariff")
                    advance_amount = st.number_input("Advance Amount", min_value=0.0, value=safe_float(reservation["Advance Amount"]), step=100.0, key=f"{form_key}_advance")
                balance_amount = total_tariff - advance_amount if total_tariff >= advance_amount else 0.0
                st.write(f"Balance Amount: {balance_amount:.2f}")
                col7, col8 = st.columns(2)
                with col7:
                    advance_mop_options = ["Cash", "UPI", "Card", "Other"]
                    advance_mop = st.selectbox("Advance MOP", advance_mop_options, index=advance_mop_options.index(reservation["Advance MOP"]) if reservation["Advance MOP"] in advance_mop_options else 0, key=f"{form_key}_advance_mop")
                    if advance_mop == "Other":
                        custom_advance_mop = st.text_input("Custom Advance MOP", value=reservation["Advance MOP"] if reservation["Advance MOP"] not in advance_mop_options else "", key=f"{form_key}_custom_advance_mop")
                    else:
                        custom_advance_mop = ""
                with col8:
                    balance_mop_options = ["Cash", "UPI", "Card", "Other"]
                    balance_mop = st.selectbox("Balance MOP", balance_mop_options, index=balance_mop_options.index(reservation["Balance MOP"]) if reservation["Balance MOP"] in balance_mop_options else 0, key=f"{form_key}_balance_mop")
                    if balance_mop == "Other":
                        custom_balance_mop = st.text_input("Custom Balance MOP", value=reservation["Balance MOP"] if reservation["Balance MOP"] not in balance_mop_options else "", key=f"{form_key}_custom_balance_mop")
                    else:
                        custom_balance_mop = ""
                col9, col10 = st.columns(2)
                with col9:
                    mob_value = st.text_input("MOB", value=reservation["MOB"], key=f"{form_key}_mob")
                    online_source_options = ["Booking.com", "Agoda", "Expedia", "Others"]
                    online_source = st.selectbox("Online Source", online_source_options, index=online_source_options.index(reservation["Online Source"]) if reservation["Online Source"] in online_source_options else 0, key=f"{form_key}_online_source")
                    if online_source == "Others":
                        custom_online_source = st.text_input("Custom Online Source", value=reservation["Online Source"] if reservation["Online Source"] not in online_source_options else "", key=f"{form_key}_custom_online_source")
                    else:
                        custom_online_source = ""
                with col10:
                    invoice_no = st.text_input("Invoice No", value=reservation["Invoice No"], key=f"{form_key}_invoice_no")
                    enquiry_date = st.date_input("Enquiry Date", value=date.fromisoformat(reservation["Enquiry Date"]), key=f"{form_key}_enquiry_date")
                    booking_date = st.date_input("Booking Date", value=date.fromisoformat(reservation["Booking Date"]), key=f"{form_key}_booking_date")
                col11, col12 = st.columns(2)
                with col11:
                    breakfast = st.checkbox("Breakfast Included", value=reservation["Breakfast"], key=f"{form_key}_breakfast")
                    booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation["Booking Status"]), key=f"{form_key}_status")
                with col12:
                    payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation["Payment Status"]), key=f"{form_key}_payment_status")
                remarks = st.text_area("Remarks", value=reservation["Remarks"], key=f"{form_key}_remarks")
                col13, col14 = st.columns(2)
                with col13:
                    submitted_by = st.text_input("Submitted By", value=reservation["Submitted By"], key=f"{form_key}_submitted_by")
                with col14:
                    modified_by = st.text_input("Modified By", value=reservation["Modified By"], key=f"{form_key}_modified_by")
                    modified_comments = st.text_area("Modified Comments", value=reservation["Modified Comments"], key=f"{form_key}_modified_comments")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.session_state.permissions.get("edit", False):
                        if st.button("💾 Update Reservation", key=f"{form_key}_update", use_container_width=True):
                            updated_reservation = {
                                "Property Name": property_name,
                                "Guest Name": guest_name,
                                "Guest Phone": guest_phone,
                                "Check In": str(check_in),
                                "Check Out": str(check_out),
                                "No of Adults": safe_int(no_of_adults),
                                "No of Children": safe_int(no_of_children),
                                "No of Infant": safe_int(no_of_infant),
                                "Total Pax": safe_int(total_pax),
                                "Room No": room_no,
                                "Total Tariff": safe_float(total_tariff),
                                "Advance Amount": safe_float(advance_amount),
                                "Balance Amount": balance_amount,
                                "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                                "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                                "MOB": mob_value,
                                "Online Source": custom_online_source if online_source == "Others" else online_source,
                                "Invoice No": invoice_no,
                                "Enquiry Date": str(enquiry_date),
                                "Booking Date": str(booking_date),
                                "Booking ID": reservation["Booking ID"],
                                "Room Type": room_type if room_type != "Other" else "",
                                "Breakfast": breakfast,
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
                    else:
                        st.info("You do not have permission to edit reservations.")
                with col_btn2:
                    if st.session_state.role == "Management" and st.session_state.permissions.get("delete", False):
                        if st.button("🗑️ Delete Reservation", key=f"{form_key}_delete", use_container_width=True):
                            if delete_reservation_in_supabase(reservation["Booking ID"]):
                                st.session_state.reservations.pop(edit_index)
                                st.session_state.edit_mode = False
                                st.session_state.edit_index = None
                                st.success(f"🗑️ Reservation {reservation['Booking ID']} deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete reservation")
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
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="analytics_filter_status")
    with col4:
        filter_check_in_date = st.date_input("Check-in Date", value=None, key="analytics_filter_check_in_date")
    with col5:
        filter_check_out_date = st.date_input("Check-out Date", value=None, key="analytics_filter_check_out_date")
    with col6:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["Property Name"].unique()), key="analytics_filter_property")
    filtered_df = df.copy()
   
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["Booking Status"] == filter_status]
    if filter_check_in_date:
        filtered_df = filtered_df[filtered_df["Check In"] == str(filter_check_in_date)]
    if filter_check_out_date:
        filtered_df = filtered_df[filtered_df["Check Out"] == str(filter_check_out_date)]
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
