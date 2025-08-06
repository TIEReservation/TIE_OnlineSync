import streamlit as st
import requests
import pandas as pd
from config import STAYFLEXI_API_TOKEN, STAYFLEXI_API_BASE_URL
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def fetch_bookings(hotel_id, date, is_today=True):
    """
    Fetch bookings for a specific hotel from Stayflexi API.
    
    Args:
        hotel_id (str): The ID of the property (e.g., '31550').
        date (str): Date for bookings (format: 'YYYY-MM-DD' or 'Wed Aug 06 2025').
        is_today (bool): Whether to fetch today's data (default: True).
    
    Returns:
        dict: Booking details in JSON format (CHECKINS, NEW_BOOKINGS, etc.).
    """
    headers = {"Authorization": f"Bearer {STAYFLEXI_API_TOKEN}"}
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%a %b %d %Y")
    except ValueError:
        formatted_date = date
    
    params = {
        "date": formatted_date,
        "is_today": str(is_today).lower(),
        "hotel_id": hotel_id,
        "hotelId": hotel_id
    }
    url = f"{STAYFLEXI_API_BASE_URL}/api/v2/reports/generateDashDataLite/"
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Error fetching bookings for hotel {hotel_id}: {e}")
        return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Network error while fetching bookings: {e}")
        return {}

def save_online_reservation(reservation, hotel_id, status):
    """
    Save a single reservation to the online_reservations table.
    
    Args:
        reservation (dict): Booking details from Stayflexi API.
        hotel_id (str): Property ID.
        status (str): Status of the booking (e.g., 'CHECKINS', 'NEW_BOOKINGS', 'CANCELLED').
    """
    try:
        supabase_reservation = {
            "reservation_id": reservation.get("reservation_id", "N/A"),
            "hotel_id": hotel_id,
            "guest_name": reservation.get("user_name", "N/A"),
            "check_in": reservation.get("check_in"),
            "check_out": reservation.get("check_out"),
            "room_type": reservation.get("room_type", "N/A"),
            "booking_source": reservation.get("booking_source", "N/A"),
            "reservation_amount": float(reservation.get("reservation_amount", 0)),
            "status": status,
            "cancel_date": reservation.get("cancel_date") if status in ["CANCELLED", "TODAY_CANCELLED"] else None
        }
        response = supabase.table("online_reservations").insert(supabase_reservation).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error saving online reservation {reservation.get('reservation_id', 'N/A')}: {e}")
        return False

def get_all_properties_bookings(date, is_today=True):
    """
    Fetch and save bookings for all active properties.
    
    Args:
        date (str): Date for bookings (format: 'YYYY-MM-DD' or 'Wed Aug 06 2025').
        is_today (bool): Whether to fetch today's data (default: True).
    
    Returns:
        dict: Dictionary with hotelId as key and booking details as value.
    """
    active_hotel_ids = [
        "27704", "27706", "27707", "27709", "27710", "27711", "27719",
        "27720", "27721", "27722", "27723", "27724", "30357", "31550", "32470"
    ]
    all_bookings = {}
    for hotel_id in active_hotel_ids:
        bookings = fetch_bookings(hotel_id, date, is_today)
        all_bookings[hotel_id] = bookings
        # Save bookings to Supabase
        for status in ["CHECKINS", "NEW_BOOKINGS", "CANCELLED", "TODAY_CANCELLED"]:
            for booking in bookings.get(status, []):
                save_online_reservation(booking, hotel_id, status)
    return all_bookings

def load_online_reservations_from_supabase(date, is_today=True):
    """
    Load online reservations from Supabase for the given date.
    
    Args:
        date (str): Date for bookings (format: 'YYYY-MM-DD').
        is_today (bool): Whether to filter for today's data.
    
    Returns:
        list: List of reservation dictionaries.
    """
    try:
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
        query = supabase.table("online_reservations").select("*")
        if is_today:
            query = query.eq("check_in", formatted_date)
        response = query.execute()
        reservations = []
        for record in response.data:
            reservation = {
                "Reservation ID": record["reservation_id"],
                "Hotel ID": record["hotel_id"],
                "Guest Name": record["guest_name"],
                "Check In": datetime.strptime(record["check_in"], "%Y-%m-%d").date() if record["check_in"] else None,
                "Check Out": datetime.strptime(record["check_out"], "%Y-%m-%d").date() if record["check_out"] else None,
                "Room Type": record["room_type"],
                "Booking Source": record["booking_source"],
                "Reservation Amount": float(record["reservation_amount"]),
                "Status": record["status"],
                "Cancel Date": datetime.strptime(record["cancel_date"], "%Y-%m-%d").date() if record["cancel_date"] else None
            }
            reservations.append(reservation)
        return reservations
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

def show_online_reservations():
    """
    Display online reservations from Stayflexi API in Streamlit.
    """
    st.header("📡 Online Reservations")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        date = st.date_input("Select Date", value=datetime.today(), key="online_reservations_date")
    with col2:
        is_today = st.checkbox("Show Today's Bookings", value=True, key="online_reservations_is_today")
    
    if date:
        formatted_date = date.strftime("%Y-%m-%d")
        # Fetch and save bookings
        bookings = get_all_properties_bookings(formatted_date, is_today)
        # Load from Supabase for display
        reservations = load_online_reservations_from_supabase(formatted_date, is_today)
        
        if not reservations:
            st.info("No online reservations found for the selected date.")
            return
        
        df = pd.DataFrame(reservations)
        properties = df["Hotel ID"].unique()
        
        for hotel_id in properties:
            with st.expander(f"Property ID: {hotel_id}"):
                property_df = df[df["Hotel ID"] == hotel_id]
                tabs = st.tabs(["Check-ins", "New Bookings", "Cancelled"])
                
                with tabs[0]:
                    checkin_df = property_df[property_df["Status"] == "CHECKINS"]
                    if not checkin_df.empty:
                        st.dataframe(
                            checkin_df[["Reservation ID", "Guest Name", "Check In", "Check Out", "Room Type", "Booking Source", "Reservation Amount"]],
                            use_container_width=True
                        )
                    else:
                        st.write("No check-ins found.")
                
                with tabs[1]:
                    new_df = property_df[property_df["Status"] == "NEW_BOOKINGS"]
                    if not new_df.empty:
                        st.dataframe(
                            new_df[["Reservation ID", "Guest Name", "Check In", "Check Out", "Room Type", "Booking Source", "Reservation Amount"]],
                            use_container_width=True
                        )
                    else:
                        st.write("No new bookings found.")
                
                with tabs[2]:
                    cancelled_df = property_df[property_df["Status"].isin(["CANCELLED", "TODAY_CANCELLED"])]
                    if not cancelled_df.empty:
                        st.dataframe(
                            cancelled_df[["Reservation ID", "Guest Name", "Check In", "Check Out", "Room Type", "Booking Source", "Cancel Date"]],
                            use_container_width=True
                        )
                    else:
                        st.write("No cancelled bookings found.")
