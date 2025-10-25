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
            "Deluex Double Room Seaview": ["301", "302", "303", "304"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Millionaire Resort": {
            "Double Room": ["101", "102", "103", "105"],
            "Deluex Double Room with Balcony": ["205", "304", "305"],
            "Deluex Triple Room with Balcony": ["201", "202", "203", "204", "301", "302", "303"],
            "Deluex Family Room with Balcony": ["206", "207", "208", "306", "307", "308"],
            "Deluex Triple Room": ["402"],
            "Deluex Family Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2", "Day Use 3", "Day Use 5"],
            "No Show": ["No Show"]
        },
        "Le Poshe Luxury": {
            "2BHA Appartment": ["101&102", "101", "102"],
            "2BHA Appartment with Balcony": ["201&202", "201", "202", "301&302", "301", "302", "401&402", "401", "402"],
            "3BHA Appartment": ["203to205", "203", "204", "205", "303to305", "303", "304", "305", "403to405", "403", "404", "405"],
            "Double Room with Private Terrace": ["501"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "Le Poshe Suite": {
            "2BHA Appartment": ["601&602", "601", "602", "603", "604", "703", "704"],
            "2BHA Appartment with Balcony": ["701&702", "701", "702"],
            "Double Room with Terrace": ["801"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Paradise Residency": {
            "Double Room": ["101", "102", "103", "301", "302", "304"],
            "Family Room": ["201", "203"],
            "Triple Room": ["202", "303"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Paradise Luxury": {
            "3BHA Appartment": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Villa Heritage": {
            "Double Room": ["101", "102", "103"],
            "4BHA Appartment": ["201to203&301", "201", "202", "203", "301"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "Le Pondy Beach Side": {
            "Villa": ["101to104", "101", "102", "103", "104"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "Le Royce Villa": {
            "Villa": ["101to102&201to202", "101", "102", "201", "202"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "201to203", "201", "202", "203"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        }
    }

@st.cache_data
def load_reservations_from_supabase():
    """Load all reservations from Supabase."""
    try:
        response = supabase.table("reservations").select("*").execute()
        data = response.data if response.data else []
        if not data:
            st.warning("No reservations found in the database.")
        return data
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def show_new_reservation_form():
    """Display and handle the new reservation form."""
    st.subheader("📝 New Reservation Form")
    
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()

    # Set submitted_by from session state
    submitted_by = st.session_state.username if 'username' in st.session_state else "Unknown"
    st.write(f"Submitted By: {submitted_by}")

    with st.form("new_reservation_form"):
        # Form fields
        property_name = st.selectbox("Property Name", list(load_property_room_map().keys()))
        check_in = st.date_input("Check-in Date", value=date.today())
        check_out = st.date_input("Check-out Date", value=date.today() + timedelta(days=1))
        room_type = st.selectbox("Room Type", list(load_property_room_map().get(property_name, {}).keys()))
        room_no = st.selectbox("Room No.", load_property_room_map().get(property_name, {}).get(room_type, []))
        guest_name = st.text_input("Guest Name")
        guest_phone = st.text_input("Guest Phone")
        no_of_adults = st.number_input("No. of Adults", min_value=1, value=1)
        no_of_children = st.number_input("No. of Children", min_value=0, value=0)
        no_of_infant = st.number_input("No. of Infants", min_value=0, value=0)
        total_pax = no_of_adults + no_of_children + no_of_infant
        st.write(f"Total Pax: {total_pax}")
        booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"])
        total_tariff = st.number_input("Total Tariff (₹)", min_value=0.0, value=0.0)

        if st.form_submit_button("Submit Reservation"):
            new_reservation = {
                "property_name": property_name,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "room_type": room_type,
                "room_no": room_no,
                "guest_name": guest_name,
                "guest_phone": guest_phone,
                "no_of_adults": no_of_adults,
                "no_of_children": no_of_children,
                "no_of_infant": no_of_infant,
                "total_pax": total_pax,
                "booking_status": booking_status,
                "total_tariff": total_tariff,
                "submitted_by": submitted_by,
                "modified_by": submitted_by  # Initially same as submitted_by
            }
            try:
                response = supabase.table("reservations").insert(new_reservation).execute()
                if response.data:
                    st.session_state.reservations.append(new_reservation)
                    st.success(f"✅ Reservation for {guest_name} added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add reservation.")
            except Exception as e:
                st.error(f"❌ Error adding reservation: {e}")

def show_reservations():
    """Display all reservations."""
    st.subheader("👀 View Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    if not st.session_state.reservations:
        st.warning("No reservations available.")
        return
    df = pd.DataFrame(st.session_state.reservations)
    st.dataframe(df)

def show_edit_reservations():
    """Edit existing reservations."""
    st.subheader("✏️ Edit Reservations")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
    if not st.session_state.reservations:
        st.warning("No reservations available to edit.")
        return

    selected_index = st.selectbox("Select Reservation to Edit", range(len(st.session_state.reservations)))
    reservation = st.session_state.reservations[selected_index]

    modified_by = st.session_state.username if 'username' in st.session_state else "Unknown"
    st.write(f"Modified By: {modified_by}")

    with st.form("edit_reservation_form"):
        property_name = st.selectbox("Property Name", list(load_property_room_map().keys()), index=list(load_property_room_map().keys()).index(reservation["property_name"]) if reservation["property_name"] in load_property_room_map() else 0)
        check_in = st.date_input("Check-in Date", value=date.fromisoformat(reservation["check_in"]) if reservation.get("check_in") else date.today())
        check_out = st.date_input("Check-out Date", value=date.fromisoformat(reservation["check_out"]) if reservation.get("check_out") else date.today())
        room_type = st.selectbox("Room Type", list(load_property_room_map().get(property_name, {}).keys()), index=list(load_property_room_map().get(property_name, {}).keys()).index(reservation["room_type"]) if reservation["room_type"] in load_property_room_map().get(property_name, {}) else 0)
        room_no = st.selectbox("Room No.", load_property_room_map().get(property_name, {}).get(room_type, []), index=load_property_room_map().get(property_name, {}).get(room_type, []).index(reservation["room_no"]) if reservation["room_no"] in load_property_room_map().get(property_name, {}).get(room_type, []) else 0)
        guest_name = st.text_input("Guest Name", value=reservation.get("guest_name", ""))
        guest_phone = st.text_input("Guest Phone", value=reservation.get("guest_phone", ""))
        no_of_adults = st.number_input("No. of Adults", min_value=1, value=reservation.get("no_of_adults", 1))
        no_of_children = st.number_input("No. of Children", min_value=0, value=reservation.get("no_of_children", 0))
        no_of_infant = st.number_input("No. of Infants", min_value=0, value=reservation.get("no_of_infant", 0))
        total_pax = no_of_adults + no_of_children + no_of_infant
        st.write(f"Total Pax: {total_pax}")
        booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"], index=["Confirmed", "Pending", "Cancelled", "Follow-up", "Completed", "No Show"].index(reservation.get("booking_status", "Confirmed")))
        total_tariff = st.number_input("Total Tariff (₹)", min_value=0.0, value=float(reservation.get("total_tariff", 0.0)))

        if st.form_submit_button("Save Changes"):
            updated_reservation = {
                "property_name": property_name,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "room_type": room_type,
                "room_no": room_no,
                "guest_name": guest_name,
                "guest_phone": guest_phone,
                "no_of_adults": no_of_adults,
                "no_of_children": no_of_children,
                "no_of_infant": no_of_infant,
                "total_pax": total_pax,
                "booking_status": booking_status,
                "total_tariff": total_tariff,
                "modified_by": modified_by
            }
            try:
                response = supabase.table("reservations").update(updated_reservation).eq("property_name", reservation["property_name"]).eq("check_in", reservation["check_in"]).eq("guest_name", reservation["guest_name"]).execute()
                if response.data:
                    st.session_state.reservations[selected_index] = {**reservation, **updated_reservation}
                    st.success(f"✅ Reservation for {guest_name} updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update reservation.")
            except Exception as e:
                st.error(f"❌ Error updating reservation: {e}")

def show_analytics():
    """Display analytics dashboard."""
    st.subheader("📊 Analytics Dashboard")
    if 'reservations' not in st.session_state:
        st.session_state.reservations = load_reservations_from_supabase()
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
    filtered_df = df if start_date is None and end_date is None else df[(df["check_in"] >= str(start_date)) & (df["check_out"] <= str(end_date))] if start_date and end_date else df
   
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
