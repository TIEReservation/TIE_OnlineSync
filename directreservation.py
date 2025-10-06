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
            "Double Room": ["101", "102", "103", "301", "302", "304"],
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
            "Villa": ["101to102&201to202", "101", "102", "201", "202"]
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"]
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
            "Family Room": ["401&402"]
        }
    }

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

def show_confirmation_dialog(booking_id, is_update=False):
    """Display a confirmation dialog for reservation creation or update."""
    action = "updated" if is_update else "created"
    st.success(f"✅ Reservation {booking_id} {action} successfully!")
    if st.button("View Reservations"):
        st.session_state.current_page = "View Reservations"
        st.rerun()
    if st.button("Edit Another Reservation"):
        st.session_state.current_page = "Edit Reservations"
        st.rerun()

def show_new_reservation_form():
    """Display form for creating new direct reservations."""
    st.title("🏨 New Direct Reservation")
    property_room_map = load_property_room_map()
    properties = list(property_room_map.keys())
    
    with st.form(key="new_reservation_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            property_name = st.selectbox("Property Name", properties)
            room_types = list(property_room_map[property_name].keys())
            room_type = st.selectbox("Room Type", room_types)
            room_numbers = property_room_map[property_name][room_type]
            room_no = st.selectbox("Room No", room_numbers)
        with col2:
            guest_name = st.text_input("Guest Name")
            guest_phone = st.text_input("Mobile No")
            check_in = st.date_input("Check In")
            check_out = st.date_input("Check Out")
        with col3:
            no_of_adults = st.number_input("No of Adults", min_value=0, value=1)
            no_of_children = st.number_input("No of Children", min_value=0, value=0)
            no_of_infant = st.number_input("No of Infant", min_value=0, value=0)
            total_pax = no_of_adults + no_of_children + no_of_infant
            st.text_input("Total Pax", value=total_pax, disabled=True)

        col4, col5, col6 = st.columns(3)
        with col4:
            booking_made_on = st.date_input("Booking Made On", value=date.today())
            booking_confirmed_on = st.date_input("Booking Confirmed On", value=None)
        with col5:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, step=100.0)
            advance_amount = st.number_input("Advance Amount", min_value=0.0, step=100.0)
            balance_amount = total_tariff - advance_amount
            st.text_input("Balance Amount", value=balance_amount, disabled=True)
        with col6:
            mop_options = ["", "Cash", "Card", "UPI", "Bank Transfer", "Other"]
            advance_mop = st.selectbox("Advance MOP", mop_options)
            balance_mop = st.selectbox("Balance MOP", mop_options)

        col7, col8, col9 = st.columns(3)
        with col7:
            booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"])
        with col8:
            payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"])
        with col9:
            plan_status = st.selectbox("Plan Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"])

        remarks = st.text_area("Remarks")
        col10, col11 = st.columns(2)
        with col10:
            submitted_by = st.text_input("Submitted by")
        with col11:
            modified_by = st.text_input("Modified by")

        if st.form_submit_button("📥 Submit Reservation"):
            if not guest_name or not guest_phone or not check_in or not check_out:
                st.error("❌ Please fill in all required fields (Guest Name, Mobile No, Check In, Check Out).")
            elif check_out <= check_in:
                st.error("❌ Check-out date must be after check-in date.")
            else:
                new_reservation = {
                    "property_name": property_name,
                    "booking_id": f"{property_name[:3].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "guest_name": guest_name,
                    "mobile_no": guest_phone,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "no_of_adults": no_of_adults,
                    "no_of_children": no_of_children,
                    "no_of_infant": no_of_infant,
                    "total_pax": total_pax,
                    "room_no": room_no,
                    "room_type": room_type,
                    "booking_made_on": str(booking_made_on),
                    "booking_confirmed_on": str(booking_confirmed_on) if booking_confirmed_on else None,
                    "total_tariff": total_tariff,
                    "advance_amount": advance_amount,
                    "balance_amount": balance_amount,
                    "advance_mop": advance_mop,
                    "balance_mop": balance_mop,
                    "status": booking_status,
                    "payment_status": payment_status,
                    "plan_status": plan_status,
                    "remarks": remarks,
                    "submitted_by": submitted_by,
                    "modified_by": modified_by
                }
                if insert_reservation_in_supabase(new_reservation):
                    st.session_state.reservations.append(new_reservation)
                    show_confirmation_dialog(new_reservation["booking_id"])
                else:
                    st.error("❌ Failed to create reservation")

def show_reservations():
    """Display direct reservations with filters."""
    st.title("📋 View Direct Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()

    if not st.session_state.reservations:
        st.info("No reservations available.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Start Date (Check-In)", value=None)
    with col2:
        end_date = st.date_input("End Date (Check-In)", value=None)
    with col3:
        filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"])
    with col4:
        filter_property = st.selectbox("Filter by Property", ["All"] + sorted(df["property_name"].unique()))

    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["check_in"]) <= pd.to_datetime(end_date)]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == filter_status]
    if filter_property != "All":
        filtered_df = filtered_df[filtered_df["property_name"] == filter_property]

    if filtered_df.empty:
        st.warning("No reservations match the selected filters.")
    else:
        display_columns = [
            "property_name", "booking_id", "guest_name", "check_in", "check_out",
            "room_no", "room_type", "status", "payment_status", "total_tariff",
            "advance_amount", "balance_amount"
        ]
        st.dataframe(filtered_df[display_columns], use_container_width=True)

def show_edit_reservations(selected_booking_id=None):
    """Display edit direct reservations page."""
    st.title("✏️ Edit Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()

    if not st.session_state.reservations:
        st.info("No reservations available to edit.")
        return

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_index = None

    df = pd.DataFrame(st.session_state.reservations)
    booking_id_list = df["booking_id"].tolist()
    default_index = booking_id_list.index(selected_booking_id) if selected_booking_id in booking_id_list else 0
    selected_booking_id = st.selectbox("Select Booking ID", booking_id_list, index=default_index)

    if selected_booking_id:
        edit_index = df[df["booking_id"] == selected_booking_id].index[0]
        reservation = st.session_state.reservations[edit_index]
        st.session_state.edit_mode = True
        st.session_state.edit_index = edit_index

    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        reservation = st.session_state.reservations[st.session_state.edit_index]
        st.subheader(f"Editing Reservation: {reservation['booking_id']}")
        property_room_map = load_property_room_map()
        properties = list(property_room_map.keys())
        
        with st.form(key=f"edit_reservation_form_{reservation['booking_id']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                property_name = st.selectbox("Property Name", properties, index=properties.index(reservation["property_name"]) if reservation["property_name"] in properties else 0)
                room_types = list(property_room_map[property_name].keys())
                room_type = st.selectbox("Room Type", room_types, index=room_types.index(reservation["room_type"]) if reservation["room_type"] in room_types else 0)
                room_numbers = property_room_map[property_name][room_type]
                room_no = st.selectbox("Room No", room_numbers, index=room_numbers.index(reservation["room_no"]) if reservation["room_no"] in room_numbers else 0)
            with col2:
                guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
                guest_phone = st.text_input("Mobile No", value=reservation.get("mobile_no", ""))
                check_in = st.date_input("Check In", value=date.fromisoformat(reservation["check_in"]) if reservation.get("check_in") else None)
                check_out = st.date_input("Check Out", value=date.fromisoformat(reservation["check_out"]) if reservation.get("check_out") else None)
            with col3:
                no_of_adults = st.number_input("No of Adults", value=reservation.get("no_of_adults", 0), min_value=0)
                no_of_children = st.number_input("No of Children", value=reservation.get("no_of_children", 0), min_value=0)
                no_of_infant = st.number_input("No of Infant", value=reservation.get("no_of_infant", 0), min_value=0)
                total_pax = no_of_adults + no_of_children + no_of_infant
                st.text_input("Total Pax", value=total_pax, disabled=True)

            col4, col5, col6 = st.columns(3)
            with col4:
                booking_made_on = st.date_input("Booking Made On", value=date.fromisoformat(reservation["booking_made_on"]) if reservation.get("booking_made_on") else None)
                booking_confirmed_on = st.date_input("Booking Confirmed On", value=date.fromisoformat(reservation["booking_confirmed_on"]) if reservation.get("booking_confirmed_on") else None)
            with col5:
                total_tariff = st.number_input("Total Tariff", value=reservation.get("total_tariff", 0.0))
                advance_amount = st.number_input("Advance Amount", value=reservation.get("advance_amount", 0.0))
                balance_amount = total_tariff - advance_amount
                st.text_input("Balance Amount", value=balance_amount, disabled=True)
            with col6:
                mop_options = ["", "Cash", "Card", "UPI", "Bank Transfer", "Other"]
                advance_mop = st.selectbox("Advance MOP", mop_options, index=mop_options.index(reservation.get("advance_mop", "")) if reservation.get("advance_mop") in mop_options else 0)
                balance_mop = st.selectbox("Balance MOP", mop_options, index=mop_options.index(reservation.get("balance_mop", "")) if reservation.get("balance_mop") in mop_options else 0)

            col7, col8, col9 = st.columns(3)
            with col7:
                booking_status = st.selectbox("Booking Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation.get("status", "Pending")))
            with col8:
                payment_status = st.selectbox("Payment Status", ["Not Paid", "Fully Paid", "Partially Paid"], index=["Not Paid", "Fully Paid", "Partially Paid"].index(reservation.get("payment_status", "Not Paid")))
            with col9:
                plan_status = st.selectbox("Plan Status", ["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Pending", "Confirmed", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation.get("plan_status", "Pending")))

            remarks = st.text_area("Remarks", value=reservation.get("remarks", ""))
            col10, col11 = st.columns(2)
            with col10:
                submitted_by = st.text_input("Submitted by", value=reservation.get("submitted_by", ""))
            with col11:
                modified_by = st.text_input("Modified by", value=reservation.get("modified_by", ""))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("💾 Update Reservation"):
                    updated_reservation = {
                        "property_name": property_name,
                        "guest_name": guest_name,
                        "mobile_no": guest_phone,
                        "check_in": str(check_in) if check_in else None,
                        "check_out": str(check_out) if check_out else None,
                        "no_of_adults": no_of_adults,
                        "no_of_children": no_of_children,
                        "no_of_infant": no_of_infant,
                        "total_pax": total_pax,
                        "room_no": room_no,
                        "room_type": room_type,
                        "booking_made_on": str(booking_made_on) if booking_made_on else None,
                        "booking_confirmed_on": str(booking_confirmed_on) if booking_confirmed_on else None,
                        "total_tariff": total_tariff,
                        "advance_amount": advance_amount,
                        "balance_amount": balance_amount,
                        "advance_mop": advance_mop,
                        "balance_mop": balance_mop,
                        "status": booking_status,
                        "payment_status": payment_status,
                        "plan_status": plan_status,
                        "remarks": remarks,
                        "submitted_by": submitted_by,
                        "modified_by": modified_by
                    }
                    if update_reservation_in_supabase(reservation["booking_id"], updated_reservation):
                        st.session_state.reservations[st.session_state.edit_index] = {**reservation, **updated_reservation, "booking_id": reservation["booking_id"]}
                        st.session_state.edit_mode = False
                        st.session_state.edit_index = None
                        st.query_params.clear()
                        show_confirmation_dialog(reservation["booking_id"], is_update=True)
                    else:
                        st.error("❌ Failed to update reservation")
            with col_btn2:
                if st.session_state.role == "Management":
                    if st.form_submit_button("🗑️ Delete Reservation"):
                        if delete_reservation_in_supabase(reservation["booking_id"]):
                            st.session_state.reservations.pop(st.session_state.edit_index)
                            st.session_state.edit_mode = False
                            st.session_state.edit_index = None
                            st.success(f"🗑️ Reservation {reservation['booking_id']} deleted successfully!")
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
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], key="analytics_filter_status")
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
        filtered_df = filtered_df[filtered_df["status"] == filter_status]
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
