import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import calendar
import pandas as pd
from typing import Any, List, Dict

# ... (Previous code unchanged: Supabase initialization, TABLE_CSS, PROPERTY_INVENTORY, etc.)

def normalize_booking(booking: Dict, is_online: bool) -> Dict:
    """Normalize booking dict to common schema."""
    # Sanitize inputs to prevent f-string and HTML issues
    booking_id = sanitize_string(booking.get('booking_id'))
    payment_status = sanitize_string(booking.get('payment_status')).title()
    booking_status = sanitize_string(booking.get('booking_status')).title()
    
    # Check payment status
    if payment_status not in ["Fully Paid", "Partially Paid"]:
        st.warning(f"Skipping booking {booking_id} with invalid payment status: {payment_status}")
        return None
    
    # Check booking status
    if booking_status not in ["Completed", "Confirmed"]:
        st.warning(f"Skipping booking {booking_id} with invalid booking status: {booking_status}")
        return None
    
    try:
        normalized = {
            'booking_id': booking_id,
            'room_no': sanitize_string(booking.get('room_no')),
            'guest_name': sanitize_string(booking.get('guest_name')),
            'mobile_no': sanitize_string(booking.get('guest_phone') if is_online else booking.get('mobile_no')),
            'total_pax': booking.get('total_pax'),
            'check_in': date.fromisoformat(booking.get('check_in')) if booking.get('check_in') else None,
            'check_out': date.fromisoformat(booking.get('check_out')) if booking.get('check_out') else None,
            'booking_status': booking_status,
            'payment_status': payment_status,
            'remarks': sanitize_string(booking.get('remarks')),
            'type': 'online' if is_online else 'direct'
        }
        if not normalized['check_in'] or not normalized['check_out']:
            st.warning(f"Skipping booking {booking_id} with missing check-in/check-out dates")
            return None
        return normalized
    except Exception as e:
        st.error(f"Error normalizing booking {booking_id}: {sanitize_string(e)}")
        return None

# ... (Rest of the code unchanged: load_combined_bookings, filter_bookings_for_day, etc.)
