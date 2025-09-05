import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd

# Initialize Supabase client
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def load_properties() -> list[str]:
    """Load unique properties from both tables, merging 'La Millionare Resort' and 'La Millionaire Luxury Resort' as 'La Millionare Resort'."""
    try:
        res_direct = supabase.table("reservations").select("property_name").execute().data
        res_online = supabase.table("online_reservations").select("property").execute().data
        properties = set(r['property_name'] for r in res_direct if r['property_name']) | set(r['property'] for r in res_online if r['property'])
        # Merge "La Millionare Resort" and "La Millionaire Luxury Resort" as "La Millionare Resort"
        merged_properties = set()
        for prop in properties:
            if prop in ["La Millionare Resort", "La Millionaire Luxury Resort"]:
                merged_properties.add("La Millionare Resort")
            else:
                merged_properties.add(prop)
        return sorted(merged_properties)
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        return []

def normalize_booking(booking: dict, is_online: bool) -> dict:
    """Normalize booking dict to common schema."""
    if is_online:
        payment_status = booking.get('payment_status', '').title()
        if payment_status not in ["Fully Paid", "Partially Paid"]:
            return None
        return {
            'booking_id': booking.get('booking_id'),
            'room_no': booking.get('room_no'),
            'guest_name': booking.get('guest_name'),
            'mobile_no': booking.get('guest_phone'),
            'total_pax': booking.get('total_pax'),
            'check_in': date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None,
            'check_out': date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None,
            'booking_status': booking.get('booking_status'),
            'payment_status': payment_status,
            'remarks': booking.get('remarks')
        }
    else:
        payment_status = booking.get('payment_status', '').title()
        if payment_status not in ["Fully Paid", "Partially Paid"]:
            return None
        return {
            'booking_id': booking.get('booking_id'),
            'room_no': booking.get('room_no'),
            'guest_name': booking.get('guest_name'),
            'mobile_no': booking.get('mobile_no'),
            'total_pax': booking.get('total_pax'),
            'check_in': date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None,
            'check_out': date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None,
            'booking_status': booking.get('booking_status'),
            'payment_status': payment_status,
            'remarks': booking.get('remarks')
        }

def load_combined_bookings(property: str, start_date: date, end_date: date) -> list[dict]:
    """Load bookings overlapping the date range for the property with paid statuses."""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        # Adjust property name for merged case
        query_property = "La Millionare Resort" if property == "La Millionare Resort" else property
        # Fetch direct
        direct = supabase.table("reservations").select("*").eq("property_name", query_property)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"]).execute().data
        # Fetch online
        online = supabase.table("online_reservations").select("*").eq("property", query_property)\
            .lte("check_in", end_str).gt("check_out", start_str)\
            .in_("payment_status", ["Fully Paid", "Partially Paid"]).execute().data
        # Normalize and filter
        normalized = [b for b in [normalize_booking(b, False) for b in direct] + [normalize_booking(b, True) for b in online] if b]
        if len(normalized) < len(direct) + len(online):
            st.warning(f"Skipped {len(direct) + len(online) - len(normalized)} bookings with invalid payment status for {property} from {start_str} to {end_str}")
        return normalized
    except
