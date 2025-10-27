import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# Booking source dropdown options
BOOKING_SOURCES = [
    "Booking", "Direct", "Bkg-Direct", "Agoda", "Go-MMT", "Walk-In",
    "TIE Group", "Stayflexi", "Airbnb", "Social Media", "Expedia",
    "Cleartrip", "Website"
]

# MOP (Mode of Payment) options - same as online reservations
MOP_OPTIONS = [
    "","UPI", "Cash", "Go-MMT", "Agoda", "Not Paid", "Bank Transfer", 
    "Card Payment", "Expedia", "Cleartrip", "Website", "AIRBNB"
]

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
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106", "201to203", "201", "202", "203", "204to206", "204", "205", "206", "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Antilia Luxury": {
            "Deluex Suite Room": ["101"],
            "Deluex Double Room": ["203", "204", "303", "304"],
            "Family Room": ["201", "202", "301", "302"],
            "Deluex suite Room with Tarrace": ["404"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"]
        },
        "La Tamara Suite": {
            "Two Bedroom apartment": ["101&102"],
            "De...(truncated 28041 characters)...select("*").order("checkIn", desc=True).execute()
        if not response.data:
            st.warning("No reservations found in Supabase.")
            return []
        
        # Transform Supabase camelCase to title case for UI consistency
        transformed_data = []
        for record in response.data:
            transformed_record = {
                "Property Name": record.get("propertyName", ""),
                "Booking ID": record.get("bookingId", ""),
                "Guest Name": record.get("guestName", ""),
                "Guest Phone": record.get("guestPhone", ""),
                "Check In": record.get("checkIn", ""),
                "Check Out": record.get("checkOut", ""),
                "Room No": record.get("roomNo", ""),
                "Room Type": record.get("roomType", ""),
                "No of Adults": record.get("noOfAdults", 0),
                "No of Children": record.get("noOfChildren", 0),
                "No of Infants": record.get("noOfInfants", 0),
                "Rate Plans": record.get("ratePlans", ""),
                "Booking Source": record.get("bookingSource", ""),
                "Total Tariff": record.get("totalTariff", 0.0),
                "Advance Payment": record.get("advancePayment", 0.0),
                "Balance": record.get("balance", 0.0),
                "Advance MOP": record.get("advanceMop", "Not Paid"),
                "Balance MOP": record.get("balanceMop", "Not Paid"),
                "Booking Status": record.get("bookingStatus", "Pending"),
                "Payment Status": record.get("paymentStatus", "Not Paid"),
                "Submitted By": record.get("submittedBy", ""),
                "Modified By": record.get("modifiedBy", ""),
                "Modified Comments": record.get("modifiedComments", ""),
                "Remarks": record.get("remarks", "")
            }
            transformed_data.append(transformed_record)
        return transformed_data
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

# Added generate_booking_id function from old logic, corrected to use "bookingId"
def generate_booking_id():
    """
    Generate a unique booking ID by checking existing IDs in Supabase.
    """
    try:
        today = datetime.now().strftime('%Y%m%d')
        response = supabase.table("reservations").select("bookingId").like("bookingId", f"TIE{today}%").execute()
        existing_ids = [record["bookingId"] for record in response.data]
        sequence = 1
        while f"TIE{today}{sequence:03d}" in existing_ids:
            sequence += 1
        return f"TIE{today}{sequence:03d}"
    except Exception as e:
        st.error(f"Error generating booking ID: {e}")
        return None

# Added insert_reservation_in_supabase if missing, modeled after update
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
        # Transform to camelCase for Supabase
        supabase_reservation = {
            "propertyName": updated_reservation["propertyName"],
            "bookingId": updated_reservation["bookingId"],
            "guestName": updated_reservation["guestName"],
            "guestPhone": updated_reservation["guestPhone"],
            "checkIn": updated_reservation["checkIn"],
            "checkOut": updated_reservation["checkOut"],
            "roomNo": updated_reservation["roomNo"],
            "roomType": updated_reservation["roomType"],
            "noOfAdults": updated_reservation["noOfAdults"],
            "noOfChildren": updated_reservation["noOfChildren"],
            "noOfInfants": updated_reservation["noOfInfants"],
            "ratePlans": updated_reservation["ratePlans"],
            "bookingSource": updated_reservation["bookingSource"],
            "totalTariff": updated_reservation["totalTariff"],
            "advancePayment": updated_reservation["advancePayment"],
            "balance": updated_reservation["balance"],
            "advanceMop": updated_reservation["advanceMop"],
            "balanceMop": updated_reservation["balanceMop"],
            "bookingStatus": updated_reservation["bookingStatus"],
            "paymentStatus": updated_reservation["paymentStatus"],
            "submittedBy": updated_reservation["submittedBy"],
            "modifiedBy": updated_reservation["modifiedBy"],
            "modifiedComments": updated_reservation["modifiedComments"],
            "remarks": updated_reservation["remarks"]
        }
        response = supabase.table("reservations").update(supabase_reservation).eq("bookingId", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating reservation {booking_id}: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    """Delete a reservation from Supabase."""
    try:
        response = supabase.table("reservations").delete().eq("bookingId", booking_id).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting reservation {booking_id}: {e}")
        return False

def display_filtered_analysis(df, start_date, end_date, view_mode=True):
    """Helper function to filter dataframe for analytics or view."""
    filtered_df = df.copy()
    try:
        if start_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df["Check In"]) <= pd.to_datetime(end_date)]
    except Exception as e:
        st.error(f"Error filtering data: {e}")
    return filtered_df
