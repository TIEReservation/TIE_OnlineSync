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
            "Double Room": ["101", "102", "202", "203", "204"],
            "Standard Room": ["201"],
            "Deluex Double Room Seaview": ["301", "302", "303", "304"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "202", "202"],  # Note: duplicate "202" as per data
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],  # Note: duplicate "404" as per data
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "Deluxe Apartment": ["103&104"],
            "Deluxe Double Room": ["203", "204", "205"],
            "Deluxe Triple Room": ["201", "202"],
            "Deluxe Family Room": ["206"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Park Resort": {
            "Villa with Swimming Pool View": ["555&666", "555", "666"],
            "Villa with Garden View": ["111&222", "111", "222"],
            "Family Villa": ["333&444", "333", "444"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Coromandel Luxury": {
            "King Suite": ["101", "102"],
            "Family Suite": ["103"],
            "Double Room with Balcony": ["201", "202", "203", "204"],
            "Double Room": ["205", "206"],
            "Double Room with Terrace": ["301"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Le Terra": {
            "Luxury Double": ["103", "106"],
            "Deluxe Family suite": ["101", "102", "104", "105"],
            "Standard Double": ["107"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Happymates Forest Retreat": {
            "Entire Villa": ["101", "102"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        }
    }

def load_reservations_from_supabase():
    """Load reservations from Supabase table."""
    try:
        response = supabase.table("reservations").select("*").order("check_in", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

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
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def show_new_reservation_form():
    """Display the new reservation form."""
    st.header("📝 New Direct Reservation")

    property_room_map = load_property_room_map()

    # Property selection
    properties = list(property_room_map.keys())
    selected_property = st.selectbox("Select Property", properties)

    if selected_property:
        room_types = list(property_room_map[selected_property].keys())
        selected_room_type = st.selectbox("Select Room Type", room_types)

        # Room numbers for selected type
        available_rooms = property_room_map[selected_property][selected_room_type]
        selected_room = st.selectbox("Select Room Number", available_rooms)

        # Guest details
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("Guest Name")
        with col2:
            mobile_no = st.text_input("Mobile No")

        # Dates
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check-in Date")
        with col2:
            check_out = st.date_input("Check-out Date")

        # Tariff and payment
        col1, col2 = st.columns(2)
        with col1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0)
        with col2:
            advance_amount = st.number_input("Advance Amount", min_value=0.0)

        # Booking status
        booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled"])

        # Submit
        if st.button("Submit Reservation"):
            if all([guest_name, mobile_no, check_in, check_out, total_tariff]):
                reservation = {
                    "property_name": selected_property,
                    "room_type": selected_room_type,
                    "room_no": selected_room,
                    "guest_name": guest_name,
                    "mobile_no": mobile_no,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "total_tariff": total_tariff,
                    "advance_amount": advance_amount,
                    "booking_status": booking_status,
                    "submitted_by": st.session_state.username
                }
                if insert_reservation_in_supabase(reservation):
                    st.session_state.reservations = load_reservations_from_supabase()
                    st.success("Reservation added successfully!")
                else:
                    st.error("Failed to add reservation.")
            else:
                st.warning("Please fill all required fields.")

def show_reservations():
    """Display the reservations list."""
    st.header("👀 View Reservations")

    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()

    if not st.session_state.reservations:
        st.info("No reservations available.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    st.dataframe(df)

def show_edit_reservations():
    """Display the edit reservations interface."""
    st.header("✏️ Edit Direct Reservations")

    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()

    if not st.session_state.reservations:
        st.info("No reservations available.")
        return

    # Search by booking ID
    search_id = st.text_input("Search by Booking ID")
    filtered_reservations = st.session_state.reservations
    if search_id:
        filtered_reservations = [r for r in st.session_state.reservations if str(r.get("booking_id", "")).startswith(search_id)]

    if not filtered_reservations:
        st.info("No matching reservations found.")
        return

    selected_reservation = st.selectbox("Select Reservation to Edit", filtered_reservations, format_func=lambda x: x.get("guest_name", "Unknown"))

    if selected_reservation:
        # Edit form
        property_room_map = load_property_room_map()
        properties = list(property_room_map.keys())
        selected_property = st.selectbox("Property", properties, index=properties.index(selected_reservation.get("property_name", "")))

        room_types = list(property_room_map[selected_property].keys())
        selected_room_type = st.selectbox("Room Type", room_types, index=room_types.index(selected_reservation.get("room_type", "")))

        available_rooms = property_room_map[selected_property][selected_room_type]
        selected_room = st.selectbox("Room Number", available_rooms, index=available_rooms.index(selected_reservation.get("room_no", "")))

        guest_name = st.text_input("Guest Name", value=selected_reservation.get("guest_name", ""))
        mobile_no = st.text_input("Mobile No", value=selected_reservation.get("mobile_no", ""))

        check_in = st.date_input("Check-in Date", value=datetime.strptime(selected_reservation.get("check_in", ""), "%Y-%m-%d").date())
        check_out = st.date_input("Check-out Date", value=datetime.strptime(selected_reservation.get("check_out", ""), "%Y-%m-%d").date())

        total_tariff = st.number_input("Total Tariff", value=float(selected_reservation.get("total_tariff", 0)))
        advance_amount = st.number_input("Advance Amount", value=float(selected_reservation.get("advance_amount", 0)))

        booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled"], index=["Pending", "Confirmed", "Cancelled"].index(selected_reservation.get("booking_status", "")))

        if st.button("Update Reservation"):
            updated_reservation = {
                "property_name": selected_property,
                "room_type": selected_room_type,
                "room_no": selected_room,
                "guest_name": guest_name,
                "mobile_no": mobile_no,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "total_tariff": total_tariff,
                "advance_amount": advance_amount,
                "booking_status": booking_status,
                "modified_by": st.session_state.username
            }
            booking_id = selected_reservation.get("booking_id")
            if update_reservation_in_supabase(booking_id, updated_reservation):
                st.session_state.reservations = load_reservations_from_supabase()
                st.success("Reservation updated successfully!")
            else:
                st.error("Failed to update reservation.")

        if st.button("Delete Reservation"):
            booking_id = selected_reservation.get("booking_id")
            if delete_reservation_in_supabase(booking_id):
                st.session_state.reservations = load_reservations_from_supabase()
                st.success("Reservation deleted successfully!")
            else:
                st.error("Failed to delete reservation.")

def display_filtered_analysis(df, start_date, end_date, view_mode=False):
    """Display filtered analysis data."""
    filtered_df = df.copy()

    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]

    if view_mode:
        return filtered_df

    st.dataframe(filtered_df)
    return filtered_df

def show_confirmation_dialog(booking_id, is_update=False):
    """Show confirmation dialog."""
    action = "updated" if is_update else "created"
    st.balloons()
    st.info(f"Reservation {booking_id} {action} successfully!")

def show_edit_reservation_form(reservation, edit_index, property_room_map):
    """Render the edit form for a specific reservation."""
    form_key = f"edit_form_{edit_index}"
    st.subheader(f"Edit Reservation: {reservation['Booking ID']}")

    try:
        # Property and Room Type
        properties = list(property_room_map.keys())
        selected_property_idx = properties.index(reservation.get("Property Name", ""))
        selected_property = st.selectbox("Property Name", properties, index=selected_property_idx, key=f"{form_key}_property")

        room_types = list(property_room_map[selected_property].keys())
        selected_room_type_idx = next((i for i, rt in enumerate(room_types) if reservation.get("Room Type") in rt), 0)
        selected_room_type = st.selectbox("Room Type", room_types, index=selected_room_type_idx, key=f"{form_key}_room_type")

        available_rooms = property_room_map[selected_property][selected_room_type]
        selected_room_idx = next((i for i, room in enumerate(available_rooms) if room == reservation.get("Room No")), 0)
        selected_room = st.selectbox("Room No", available_rooms, index=selected_room_idx, key=f"{form_key}_room")

        # Guest Details
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", value=reservation.get("Name", ""), key=f"{form_key}_name")
        with col2:
            mobile_no = st.text_input("Mobile No", value=reservation.get("Mobile No", ""), key=f"{form_key}_mobile")

        # Dates
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check In", value=pd.to_datetime(reservation.get("Check In", date.today())).date(), key=f"{form_key}_check_in")
        with col2:
            check_out = st.date_input("Check Out", value=pd.to_datetime(reservation.get("Check Out", date.today())).date(), key=f"{form_key}_check_out")

        # Tariff and Payment
        col1, col2, col3 = st.columns(3)
        with col1:
            total_tariff = st.number_input("Total Tariff", value=float(reservation.get("Total Tariff", 0)), key=f"{form_key}_tariff")
        with col2:
            advance_amount = st.number_input("Advance Amount", value=float(reservation.get("Advance Amount", 0)), key=f"{form_key}_advance")
        with col3:
            balance_due = total_tariff - advance_amount

        # Mode of Payment
        col1, col2 = st.columns(2)
        with col1:
            advance_mop = st.selectbox("Advance MOP", ["Cash", "UPI", "Card", "Bank Transfer"], index=["Cash", "UPI", "Card", "Bank Transfer"].index(reservation.get("Advance MOP", "Cash")), key=f"{form_key}_advance_mop")
        with col2:
            balance_mop = st.selectbox("Balance MOP", ["Cash", "UPI", "Card", "Bank Transfer"], index=["Cash", "UPI", "Card", "Bank Transfer"].index(reservation.get("Balance MOP", "Cash")), key=f"{form_key}_balance_mop")

        # Status
        col1, col2 = st.columns(2)
        with col1:
            booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Completed", "No Show"].index(reservation.get("Booking Status", "Confirmed")), key=f"{form_key}_status")
        with col2:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Partially Paid", "Fully Paid"], index=["Not Paid", "Partially Paid", "Fully Paid"].index(reservation.get("Payment Status", "Not Paid")), key=f"{form_key}_payment")

        # Online Source
        online_source_options = ["Direct", "Phone", "Email", "Walk-in", "Others"]
        online_source = st.selectbox("Online Source", online_source_options, index=online_source_options.index(reservation.get("Online Source", "Direct")), key=f"{form_key}_online_source")
        custom_online_source = st.text_input("Custom Online Source", value=reservation.get("Custom Online Source", ""), key=f"{form_key}_custom_source") if online_source == "Others" else ""

        # Invoice and Dates
        col1, col2, col3 = st.columns(3)
        with col1:
            invoice_no = st.text_input("Invoice No", value=reservation.get("Invoice No", ""), key=f"{form_key}_invoice")
        with col2:
            enquiry_date = st.date_input("Enquiry Date", value=pd.to_datetime(reservation.get("Enquiry Date", date.today())).date(), key=f"{form_key}_enquiry")
        with col3:
            booking_date = st.date_input("Booking Date", value=pd.to_datetime(reservation.get("Booking Date", date.today())).date(), key=f"{form_key}_booking")

        # Additional Details
        breakfast = st.checkbox("Breakfast Included", value=reservation.get("Breakfast", False), key=f"{form_key}_breakfast")
        remarks = st.text_area("Remarks", value=reservation.get("Remarks", ""), key=f"{form_key}_remarks")

        # Hidden fields
        submitted_by = reservation.get("Submitted By", "")
        modified_by = st.session_state.username
        modified_comments = st.text_area("Modified Comments", value=reservation.get("Modified Comments", ""), key=f"{form_key}_modified_comments")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Update Reservation", key=f"{form_key}_update", use_container_width=True):
                updated_reservation = {
                    "Property Name": selected_property,
                    "Room Type": selected_room_type,
                    "Room No": selected_room,
                    "Name": name,
                    "Mobile No": mobile_no,
                    "Check In": str(check_in),
                    "Check Out": str(check_out),
                    "Total Tariff": total_tariff,
                    "Advance Amount": advance_amount,
                    "Balance Due": balance_due,
                    "Advance MOP": advance_mop,
                    "Balance MOP": balance_mop,
                    "Booking Status": booking_status,
                    "Payment Status": payment_status,
                    "Online Source": custom_online_source if online_source == "Others" else online_source,
                    "Invoice No": invoice_no,
                    "Enquiry Date": str(enquiry_date),
                    "Booking Date": str(booking_date),
                    "Breakfast": breakfast,
                    "Submitted By": submitted_by,
                    "Modified By": modified_by,
                    "Modified Comments": modified_comments,
                    "Remarks": remarks
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

    filtered_df = display_filtered_analysis(df, start_date, end_date, view_mode=True)
    
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
