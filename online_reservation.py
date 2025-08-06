import requests
       from config import STAYFLEXI_API_TOKEN, STAYFLEXI_API_BASE_URL
       from datetime import datetime

       def fetch_bookings(hotel_id, date, is_today=True):
           """
           Fetch bookings for a specific hotel from Stayflexi API.
           
           Args:
               hotel_id (str): The ID of the property (e.g., '31550').
               date (str): Date for bookings (format: 'YYYY-MM-DD' or 'Wed Aug 06 2025').
               is_today (bool): Whether to fetch today's data (default: True).
           
           Returns:
               dict: Booking details in JSON format (CHECKINS, NEW_BOOKINGS, etc.).
           
           Raises:
               requests.exceptions.HTTPError: If the API request fails.
           """
           headers = {"Authorization": f"Bearer {STAYFLEXI_API_TOKEN}"}
           # Format date if provided as YYYY-MM-DD
           try:
               date_obj = datetime.strptime(date, "%Y-%m-%d")
               formatted_date = date_obj.strftime("%a %b %d %Y")
           except ValueError:
               formatted_date = date  # Use as-is if already in 'Wed Aug 06 2025' format
           
           params = {
               "date": formatted_date,
               "is_today": str(is_today).lower(),
               "hotel_id": hotel_id,
               "hotelId": hotel_id  # Include both as per the request
           }
           url = f"{STAYFLEXI_API_BASE_URL}/api/v2/reports/generateDashDataLite/"
           try:
               response = requests.get(url, headers=headers, params=params)
               response.raise_for_status()
               return response.json()
           except requests.exceptions.HTTPError as e:
               print(f"Error fetching bookings for hotel {hotel_id}: {e}")
               return {}
           except requests.exceptions.RequestException as e:
               print(f"Network error while fetching bookings: {e}")
               return {}

       def get_all_properties_bookings(date, is_today=True):
           """
           Fetch bookings for all active properties.
           
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
           return all_bookings
