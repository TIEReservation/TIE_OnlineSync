import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client

try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Check Streamlit secrets.")
    st.stop()

if "reservations" not in st.session_state:
    st.session_state.reservations = []
if "username" not in st.session_state:
    st.session_state.username = "Admin"

def load_property_room_map():
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
            "Villa": ["101to102&201to202", "101", "102", "202", "202"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "La Tamara Luxury": {
            "3BHA": ["101to103", "101", "102", "103", "104to106", "104", "105", "106",
                     "201to203", "201", "202", "203", "204to206", "204", "205", "206",
                     "301to303", "301", "302", "303", "304to306", "304", "305", "306"],
            "4BHA": ["401to404", "401", "402", "403", "404"],
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
            "Family Retreate Villa": ["333&444", "333", "444"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Villa Shakti": {
            "2BHA Studio Room": ["101&102"],
            "2BHA with Balcony": ["202&203", "302&303"],
            "Family Suite": ["201"],
            "Family Room": ["301"],
            "Terrace Room": ["401"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        },
        "Eden Beach Resort": {
            "Double Room": ["101", "102"],
            "Deluex Room": ["103", "202"],
            "Triple Room": ["201"],
            "Day Use": ["Day Use 1", "Day Use 2"],
            "No Show": ["No Show"],
            "Others": []
        }
    }

def generate_booking_id():
    try:
        today = datetime.now().strftime("%Y%m%d")
        resp = supabase.table("reservations").select("booking_id").like("booking_id", f"TIE{today}%").execute()
        existing = [r["booking_id"] for r in resp.data]
        seq = 1
        while f"TIE{today}{seq:03d}" in existing:
            seq += 1
        return f"TIE{today}{seq:03d}"
    except Exception as e:
        st.error(f"Error generating booking ID: {e}")
        return None

def check_duplicate_guest(guest_name, mobile_no, room_no, exclude_booking_id=None, mob=None):
    try:
        resp = supabase.table("reservations").select("*").execute()
        for r in resp.data:
            if exclude_booking_id and r["booking_id"] == exclude_booking_id:
                continue
            if (r["guest_name"].lower() == guest_name.lower()
                    and r["mobile_no"] == mobile_no
                    and r["room_no"] == room_no):
                if mob == "Stay-back" and r["mob"] != "Stay-back":
                    continue
                return True, r["booking_id"]
        return False, None
    except Exception as e:
        st.error(f"Error checking duplicate guest: {e}")
        return False, None

def calculate_days(check_in, check_out):
    if check_in and check_out and check_out >= check_in:
        return max(1, (check_out - check_in).days)
    return 0

def safe_int(v, default=0):
    try:
        return int(v) if v is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (ValueError, TypeError):
        return default

def _update_derived(form_key: str):
    ci = st.session_state.get(f"{form_key}_checkin")
    co = st.session_state.get(f"{form_key}_checkout")
    days = calculate_days(ci, co) if ci and co else 0
    st.session_state[f"{form_key}_no_of_days"] = days
    a = safe_int(st.session_state.get(f"{form_key}_adults"))
    c = safe_int(st.session_state.get(f"{form_key}_children"))
    i = safe_int(st.session_state.get(f"{form_key}_infants"))
    st.session_state[f"{form_key}_total_pax"] = a + c + i
    total = safe_float(st.session_state.get(f"{form_key}_total_tariff"))
    adv = safe_float(st.session_state.get(f"{form_key}_advance"))
    st.session_state[f"{form_key}_balance_amount"] = max(0.0, total - adv)

def load_reservations_from_supabase():
    try:
        resp = supabase.table("reservations").select("*").execute()
        out = []
        for r in resp.data:
            out.append({
                "Booking ID": r["booking_id"],
                "Property Name": r.get("property_name", ""),
                "Room No": r.get("room_no", ""),
                "Guest Name": r.get("guest_name", ""),
                "Mobile No": r.get("mobile_no", ""),
                "No of Adults": safe_int(r.get("no_of_adults")),
                "No of Children": safe_int(r.get("no_of_children")),
                "No of Infants": safe_int(r.get("no_of_infants")),
                "Total Pax": safe_int(r.get("total_pax")),
                "Check In": datetime.strptime(r["check_in"], "%Y-%m-%d").date() if r.get("check_in") else None,
                "Check Out": datetime.strptime(r["check_out"], "%Y-%m-%d").date() if r.get("check_out") else None,
                "No of Days": safe_int(r.get("no_of_days")),
                "Tariff": safe_float(r.get("tariff")),
                "Total Tariff": safe_float(r.get("total_tariff")),
                "Advance Amount": safe_float(r.get("advance_amount")),
                "Balance Amount": safe_float(r.get("balance_amount")),
                "Advance MOP": r.get("advance_mop", ""),
                "Balance MOP": r.get("balance_mop", ""),
                "MOB": r.get("mob", ""),
                "Online Source": r.get("online_source", ""),
                "Invoice No": r.get("invoice_no", ""),
                "Enquiry Date": datetime.strptime(r["enquiry_date"], "%Y-%m-%d").date() if r.get("enquiry_date") else None,
                "Booking Date": datetime.strptime(r["booking_date"], "%Y-%m-%d").date() if r.get("booking_date") else None,
                "Room Type": r.get("room_type", ""),
                "Breakfast": r.get("breakfast", ""),
                "Booking Status": r.get("plan_status", ""),
                "Submitted By": r.get("submitted_by", ""),
                "Modified By": r.get("modified_by", ""),
                "Modified Comments": r.get("modified_comments", ""),
                "Remarks": r.get("remarks", ""),
                "Payment Status": r.get("payment_status", "Not Paid")
            })
        return out
    except Exception as e:
        st.error(f"Error loading reservations: {e}")
        return []

def save_reservation_to_supabase(res):
    try:
        payload = {
            "booking_id": res["Booking ID"],
            "property_name": res["Property Name"],
            "room_no": res["Room No"],
            "guest_name": res["Guest Name"],
            "mobile_no": res["Mobile No"],
            "no_of_adults": res["No of Adults"],
            "no_of_children": res["No of Children"],
            "no_of_infants": res["No of Infants"],
            "total_pax": res["Total Pax"],
            "check_in": res["Check In"].strftime("%Y-%m-%d") if res["Check In"] else None,
            "check_out": res["Check Out"].strftime("%Y-%m-%d") if res["Check Out"] else None,
            "no_of_days": res["No of Days"],
            "tariff": res["Tariff"],
            "total_tariff": res["Total Tariff"],
            "advance_amount": res["Advance Amount"],
            "balance_amount": res["Balance Amount"],
            "advance_mop": res["Advance MOP"],
            "balance_mop": res["Balance MOP"],
            "mob": res["MOB"],
            "online_source": res["Online Source"],
            "invoice_no": res["Invoice No"],
            "enquiry_date": res["Enquiry Date"].strftime("%Y-%m-%d") if res["Enquiry Date"] else None,
            "booking_date": res["Booking Date"].strftime("%Y-%m-%d") if res["Booking Date"] else None,
            "room_type": res["Room Type"],
            "breakfast": res["Breakfast"],
            "plan_status": res["Booking Status"],
            "submitted_by": res["Submitted By"],
            "modified_by": res["Modified By"],
            "modified_comments": res["Modified Comments"],
            "remarks": res["Remarks"],
            "payment_status": res["Payment Status"]
        }
        resp = supabase.table("reservations").insert(payload).execute()
        if resp.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Error saving reservation: {e}")
        return False

def update_reservation_in_supabase(booking_id, upd):
    try:
        payload = {
            "booking_id": upd["Booking ID"],
            "property_name": upd["Property Name"],
            "room_no": upd["Room No"],
            "guest_name": upd["Guest Name"],
            "mobile_no": upd["Mobile No"],
            "no_of_adults": upd["No of Adults"],
            "no_of_children": upd["No of Children"],
            "no_of_infants": upd["No of Infants"],
            "total_pax": upd["Total Pax"],
            "check_in": upd["Check In"].strftime("%Y-%m-%d") if upd["Check In"] else None,
            "check_out": upd["Check Out"].strftime("%Y-%m-%d") if upd["Check Out"] else None,
            "no_of_days": upd["No of Days"],
            "tariff": upd["Tariff"],
            "total_tariff": upd["Total Tariff"],
            "advance_amount": upd["Advance Amount"],
            "balance_amount": upd["Balance Amount"],
            "advance_mop": upd["Advance MOP"],
            "balance_mop": upd["Balance MOP"],
            "mob": upd["MOB"],
            "online_source": upd["Online Source"],
            "invoice_no": upd["Invoice No"],
            "enquiry_date": upd["Enquiry Date"].strftime("%Y-%m-%d") if upd["Enquiry Date"] else None,
            "booking_date": upd["Booking Date"].strftime("%Y-%m-%d") if upd["Booking Date"] else None,
            "room_type": upd["Room Type"],
            "breakfast": upd["Breakfast"],
            "plan_status": upd["Booking Status"],
            "submitted_by": upd["Submitted By"],
            "modified_by": upd["Modified By"],
            "modified_comments": upd["Modified Comments"],
            "remarks": upd["Remarks"],
            "payment_status": upd["Payment Status"]
        }
        resp = supabase.table("reservations").update(payload).eq("booking_id", booking_id).execute()
        if resp.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Error updating reservation: {e}")
        return False

def delete_reservation_in_supabase(booking_id):
    try:
        resp = supabase.table("reservations").delete().eq("booking_id", booking_id).execute()
        if resp.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting reservation: {e}")
        return False

@st.dialog("Reservation Confirmation")
def show_confirmation_dialog(booking_id, is_update=False):
    msg = "Reservation Updated!" if is_update else "Reservation Confirmed!"
    st.markdown(f"**{msg}**\n\nBooking ID: {booking_id}")
    if st.button("Confirm", use_container_width=True):
        st.rerun()

def show_new_reservation_form():
    st.header("Direct Reservations")
    form_key = "new_reservation"
    prop_map = load_property_room_map()
    for suf in ("_no_of_days", "_total_pax", "_balance_amount"):
        if f"{form_key}{suf}" not in st.session_state:
            st.session_state[f"{form_key}{suf}"] = 0

    c1, c2, c3 = st.columns(3)
    with c1:
        property_name = st.selectbox("Property Name", sorted(prop_map.keys()), key=f"{form_key}_property")
    with c2:
        guest_name = st.text_input("Guest Name", key=f"{form_key}_guest")
    with c3:
        mobile_no = st.text_input("Mobile No", key=f"{form_key}_mobile")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        enquiry_date = st.date_input("Enquiry Date", value=date.today(), key=f"{form_key}_enquiry")
    with r2c2:
        check_in = st.date_input("Check In", value=date.today(), key=f"{form_key}_checkin", on_change=lambda: _update_derived(form_key))
    with r2c3:
        check_out = st.date_input("Check Out", value=date.today() + timedelta(days=1), key=f"{form_key}_checkout", on_change=lambda: _update_derived(form_key))
    with r2c4:
        st.metric("No of Days", value=st.session_state[f"{form_key}_no_of_days"])

    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    with r3c1:
        adults = st.number_input("No of Adults", min_value=0, value=1, key=f"{form_key}_adults", on_change=lambda: _update_derived(form_key))
    with r3c2:
        children = st.number_input("No of Children", min_value=0, key=f"{form_key}_children", on_change=lambda: _update_derived(form_key))
    with r3c3:
        infants = st.number_input("No of Infants", min_value=0, key=f"{form_key}_infants", on_change=lambda: _update_derived(form_key))
    with r3c4:
        breakfast = st.selectbox("Breakfast", ["CP", "EP"], key=f"{form_key}_breakfast")

    r4c1, r4c2, r4c3, r4c4 = st.columns(4)
    with r4c1:
        st.metric("Total Pax", value=st.session_state[f"{form_key}_total_pax"])
    with r4c2:
        mob = st.selectbox("MOB", ["Direct", "Online", "Agent", "Walk-in", "Phone", "Website", "Booking-Drt", "Social Media", "Stay-back", "TIE-Group", "Others"], key=f"{form_key}_mob")
        custom_mob = st.text_input("Custom MOB", key=f"{form_key}_custom_mob") if mob == "Others" else None
    with r4c3:
        room_types = list(prop_map[property_name].keys())
        room_type = st.selectbox("Room Type", room_types, key=f"{form_key}_room_type")
    with r4c4:
        if room_type == "Others":
            room_no = st.text_input("Room No", key=f"{form_key}_room_no")
            if not room_no.strip():
                st.warning("Room No required for 'Others'")
        else:
            suggestions = [r for r in prop_map[property_name].get(room_type, []) if r.strip()]
            room_no = st.text_input("Room No", key=f"{form_key}_room_no")
            if suggestions:
                st.caption(f"Suggestions: {', '.join(suggestions)}")

    r5c1, r5c2, r5c3, r5c4 = st.columns(4)
    with r5c1:
        total_tariff = st.number_input("Total Tariff", min_value=0.0, step=100.0, key=f"{form_key}_total_tariff", on_change=lambda: _update_derived(form_key))
    with r5c2:
        days = st.session_state[f"{form_key}_no_of_days"]
        st.text_input("Tariff (per day)", value=f"₹{total_tariff / max(1, days):.2f}", disabled=True)
    with r5c3:
        advance_amount = st.number_input("Advance Amount", min_value=0.0, step=100.0, key=f"{form_key}_advance", on_change=lambda: _update_derived(form_key))
    with r5c4:
        advance_mop = st.selectbox("Advance MOP", [" ", "Cash", "Card", "UPI", "Bank Transfer", "ClearTrip", "TIE Management", "Booking.com", "Pending", "Other"], key=f"{form_key}_advmop")
        custom_advance_mop = st.text_input("Custom Advance MOP", key=f"{form_key}_custom_advmop") if advance_mop == "Other" else None

    r6c1, r6c2 = st.columns(2)
    with r6c1:
        st.metric("Balance Amount", value=f"₹{st.session_state[f'{form_key}_balance_amount']:.2f}")
    with r6c2:
        balance_mop = st.selectbox("Balance MOP", [" ", "Pending", "Cash", "Card", "UPI", "Bank Transfer", "Other"], key=f"{form_key}_balmop")
        custom_balance_mop = st.text_input("Custom Balance MOP", key=f"{form_key}_custom_balmop") if balance_mop == "Other" else None

    r7c1, r7c2, r7c3 = st.columns(3)
    with r7c1:
        booking_date = st.date_input("Booking Date", value=date.today(), key=f"{form_key}_booking")
    with r7c2:
        invoice_no = st.text_input("Invoice No", key=f"{form_key}_invoice")
    with r7c3:
        booking_status = st.selectbox("Booking Status", ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"], index=1, key=f"{form_key}_status")

    remarks = st.text_area("Remarks", key=f"{form_key}_remarks")

    rc9_1, rc9_2 = st.columns(2)
    with rc9_1:
        payment_status = st.selectbox("Payment Status", ["Fully Paid", "Partially Paid", "Not Paid"], index=2, key=f"{form_key}_payment_status")
    with rc9_2:
        submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""), disabled=True)

    if mob == "Online":
        online_source = st.selectbox("Online Source", ["Booking.com", "Agoda Prepaid", "Agoda Booking.com", "Expedia", "MMT", "Cleartrip", "Others"], key=f"{form_key}_online_source")
        custom_online_source = st.text_input("Custom Online Source", key=f"{form_key}_custom_online_source") if online_source == "Others" else None
    else:
        online_source = custom_online_source = None

    if st.button("Save Reservation", use_container_width=True):
        if not room_no.strip():
            st.error("Room No is required")
        elif not all([property_name, guest_name, mobile_no]):
            st.error("Fill all required fields")
        elif check_out < check_in:
            st.error("Check-out must be after check-in")
        else:
            mob_val = custom_mob if mob == "Others" else mob
            dup, dup_id = check_duplicate_guest(guest_name, mobile_no, room_no.strip(), mob=mob_val)
            if dup:
                st.error(f"Duplicate! Booking ID: {dup_id}")
            else:
                booking_id = generate_booking_id()
                if not booking_id:
                    st.error("Failed to generate ID")
                    return

                res = {
                    "Booking ID": booking_id,
                    "Property Name": property_name,
                    "Room No": room_no.strip(),
                    "Guest Name": guest_name,
                    "Mobile No": mobile_no,
                    "No of Adults": safe_int(adults),
                    "No of Children": safe_int(children),
                    "No of Infants": safe_int(infants),
                    "Total Pax": st.session_state[f"{form_key}_total_pax"],
                    "Check In": check_in,
                    "Check Out": check_out,
                    "No of Days": st.session_state[f"{form_key}_no_of_days"],
                    "Tariff": total_tariff / max(1, st.session_state[f"{form_key}_no_of_days"]),
                    "Total Tariff": total_tariff,
                    "Advance Amount": advance_amount,
                    "Balance Amount": st.session_state[f"{form_key}_balance_amount"],
                    "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                    "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                    "MOB": mob_val,
                    "Online Source": custom_online_source if online_source == "Others" else online_source,
                    "Invoice No": invoice_no,
                    "Enquiry Date": enquiry_date,
                    "Booking Date": booking_date,
                    "Room Type": room_type,
                    "Breakfast": breakfast,
                    "Booking Status": booking_status,
                    "Submitted By": submitted_by,
                    "Modified By": "",
                    "Modified Comments": "",
                    "Remarks": remarks,
                    "Payment Status": payment_status
                }

                if save_reservation_to_supabase(res):
                    show_confirmation_dialog(booking_id)

def show_edit_reservations():
    if not st.session_state.reservations:
        st.info("No reservations to edit.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    display_cols = ["Booking ID", "Property Name", "Guest Name", "Room No", "Check In", "Check Out", "Total Tariff", "Booking Status"]
    selected = st.dataframe(df[display_cols], use_container_width=True, on_select="rerun")

    if selected and selected["selection"]["rows"]:
        idx = selected["selection"]["rows"][0]
        res = st.session_state.reservations[idx]
        form_key = f"edit_{res['Booking ID']}"

        for suf in ("_no_of_days", "_total_pax", "_balance_amount"):
            key = f"{form_key}{suf}"
            if key not in st.session_state:
                st.session_state[key] = res.get(
                    {"_no_of_days": "No of Days", "_total_pax": "Total Pax", "_balance_amount": "Balance Amount"}[suf],
                    0
                )

        prop_map = load_property_room_map()

        c1, c2, c3 = st.columns(3)
        with c1:
            property_name = st.selectbox("Property Name", sorted(prop_map.keys()), index=sorted(prop_map.keys()).index(res["Property Name"]), key=f"{form_key}_property")
        with c2:
            guest_name = st.text_input("Guest Name", value=res["Guest Name"], key=f"{form_key}_guest")
        with c3:
            mobile_no = st.text_input("Mobile No", value=res["Mobile No"], key=f"{form_key}_mobile")

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        with r2c1:
            enquiry_date = st.date_input("Enquiry Date", value=res["Enquiry Date"], key=f"{form_key}_enquiry")
        with r2c2:
            check_in = st.date_input("Check In", value=res["Check In"], key=f"{form_key}_checkin", on_change=lambda: _update_derived(form_key))
        with r2c3:
            check_out = st.date_input("Check Out", value=res["Check Out"], key=f"{form_key}_checkout", on_change=lambda: _update_derived(form_key))
        with r2c4:
            st.metric("No of Days", value=st.session_state[f"{form_key}_no_of_days"])

        r3c1, r3c2, r3c3, r3c4 = st.columns(4)
        with r3c1:
            adults = st.number_input("No of Adults", min_value=0, value=res["No of Adults"], key=f"{form_key}_adults", on_change=lambda: _update_derived(form_key))
        with r3c2:
            children = st.number_input("No of Children", min_value=0, value=res["No of Children"], key=f"{form_key}_children", on_change=lambda: _update_derived(form_key))
        with r3c3:
            infants = st.number_input("No of Infants", min_value=0, value=res["No of Infants"], key=f"{form_key}_infants", on_change=lambda: _update_derived(form_key))
        with r3c4:
            breakfast = st.selectbox("Breakfast", ["CP", "EP"], index=["CP", "EP"].index(res["Breakfast"]), key=f"{form_key}_breakfast")

        r4c1, r4c2, r4c3, r4c4 = st.columns(4)
        with r4c1:
            st.metric("Total Pax", value=st.session_state[f"{form_key}_total_pax"])
        with r4c2:
            mob_opts = ["Direct", "Online", "Agent", "Walk-in", "Phone", "Website", "Booking-Drt", "Social Media", "Stay-back", "TIE-Group", "Others"]
            mob_idx = mob_opts.index(res["MOB"]) if res["MOB"] in mob_opts else -1
            mob = st.selectbox("MOB", mob_opts, index=mob_idx, key=f"{form_key}_mob")
            custom_mob = st.text_input("Custom MOB", value=res["MOB"] if mob_idx == -1 else "", key=f"{form_key}_custom_mob") if mob == "Others" else None
        with r4c3:
            room_types = list(prop_map[property_name].keys())
            room_type = st.selectbox("Room Type", room_types, index=room_types.index(res["Room Type"]), key=f"{form_key}_room_type")
        with r4c4:
            if room_type == "Others":
                room_no = st.text_input("Room No", value=res["Room No"], key=f"{form_key}_room_no")
            else:
                suggestions = [r for r in prop_map[property_name].get(room_type, []) if r.strip()]
                room_no = st.text_input("Room No", value=res["Room No"], key=f"{form_key}_room_no")
                if suggestions:
                    st.caption(f"Suggestions: {', '.join(suggestions)}")

        r5c1, r5c2, r5c3, r5c4 = st.columns(4)
        with r5c1:
            total_tariff = st.number_input("Total Tariff", min_value=0.0, value=res["Total Tariff"], step=100.0, key=f"{form_key}_total_tariff", on_change=lambda: _update_derived(form_key))
        with r5c2:
            days = st.session_state[f"{form_key}_no_of_days"]
            st.text_input("Tariff (per day)", value=f"₹{total_tariff / max(1, days):.2f}", disabled=True)
        with r5c3:
            advance_amount = st.number_input("Advance Amount", min_value=0.0, value=res["Advance Amount"], step=100.0, key=f"{form_key}_advance", on_change=lambda: _update_derived(form_key))
        with r5c4:
            adv_opts = [" ", "Cash", "Card", "UPI", "Bank Transfer", "ClearTrip", "TIE Management", "Booking.com", "Pending", "Other"]
            adv_idx = adv_opts.index(res["Advance MOP"]) if res["Advance MOP"] in adv_opts else -1
            advance_mop = st.selectbox("Advance MOP", adv_opts, index=adv_idx, key=f"{form_key}_advmop")
            custom_advance_mop = st.text_input("Custom Advance MOP", value=res["Advance MOP"] if adv_idx == -1 else "", key=f"{form_key}_custom_advmop") if advance_mop == "Other" else None

        r6c1, r6c2 = st.columns(2)
        with r6c1:
            st.metric("Balance Amount", value=f"₹{st.session_state[f'{form_key}_balance_amount']:.2f}")
        with r6c2:
            bal_opts = [" ", "Pending", "Cash", "Card", "UPI", "Bank Transfer", "Other"]
            bal_idx = bal_opts.index(res["Balance MOP"]) if res["Balance MOP"] in bal_opts else 0
            balance_mop = st.selectbox("Balance MOP", bal_opts, index=bal_idx, key=f"{form_key}_balmop")
            custom_balance_mop = st.text_input("Custom Balance MOP", value=res["Balance MOP"] if bal_idx == len(bal_opts)-1 else "", key=f"{form_key}_custom_balmop") if balance_mop == "Other" else None

        r7c1, r7c2, r7c3 = st.columns(3)
        with r7c1:
            booking_date = st.date_input("Booking Date", value=res["Booking Date"], key=f"{form_key}_booking")
        with r7c2:
            invoice_no = st.text_input("Invoice No", value=res["Invoice No"], key=f"{form_key}_invoice")
        with r7c3:
            status_opts = ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"]
            status_idx = status_opts.index(res["Booking Status"]) if res["Booking Status"] in status_opts else 1
            booking_status = st.selectbox("Booking Status", status_opts, index=status_idx, key=f"{form_key}_status")

        remarks = st.text_area("Remarks", value=res["Remarks"], key=f"{form_key}_remarks")

        rc9_1, rc9_2 = st.columns(2)
        with rc9_1:
            pay_opts = ["Fully Paid", "Partially Paid", "Not Paid"]
            pay_idx = pay_opts.index(res["Payment Status"]) if res["Payment Status"] in pay_opts else 2
            payment_status = st.selectbox("Payment Status", pay_opts, index=pay_idx, key=f"{form_key}_payment_status")
        with rc9_2:
            st.text_input("Submitted By", value=res["Submitted By"], disabled=True)

        if mob == "Online":
            src_opts = ["Booking.com", "Agoda Prepaid", "Agoda Booking.com", "Expedia", "MMT", "Cleartrip", "Others"]
            src_idx = src_opts.index(res["Online Source"]) if res["Online Source"] in src_opts else -1
            online_source = st.selectbox("Online Source", src_opts, index=src_idx, key=f"{form_key}_online_source")
            custom_online_source = st.text_input("Custom Online Source", value=res["Online Source"] if src_idx == -1 else "", key=f"{form_key}_custom_online_source") if online_source == "Others" else None
        else:
            online_source = custom_online_source = None

        rc10_1, rc10_2 = st.columns(2)
        with rc10_1:
            modified_by = st.text_input("Modified By", value=st.session_state.get("username", ""), key=f"{form_key}_modified_by")
        with rc10_2:
            modified_comments = st.text_area("Modified Comments", key=f"{form_key}_modified_comments")

        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("Save Changes", use_container_width=True):
                if not room_no.strip():
                    st.error("Room No required")
                elif check_out < check_in:
                    st.error("Check-out must be after check-in")
                else:
                    mob_val = custom_mob if mob == "Others" else mob
                    dup, dup_id = check_duplicate_guest(guest_name, mobile_no, room_no.strip(), exclude_booking_id=res["Booking ID"], mob=mob_val)
                    if dup:
                        st.error(f"Duplicate! Booking ID: {dup_id}")
                    else:
                        updated = {
                            "Booking ID": res["Booking ID"],
                            "Property Name": property_name,
                            "Room No": room_no.strip(),
                            "Guest Name": guest_name,
                            "Mobile No": mobile_no,
                            "No of Adults": safe_int(adults),
                            "No of Children": safe_int(children),
                            "No of Infants": safe_int(infants),
                            "Total Pax": st.session_state[f"{form_key}_total_pax"],
                            "Check In": check_in,
                            "Check Out": check_out,
                            "No of Days": st.session_state[f"{form_key}_no_of_days"],
                            "Tariff": total_tariff / max(1, st.session_state[f"{form_key}_no_of_days"]),
                            "Total Tariff": total_tariff,
                            "Advance Amount": advance_amount,
                            "Balance Amount": st.session_state[f"{form_key}_balance_amount"],
                            "Advance MOP": custom_advance_mop if advance_mop == "Other" else advance_mop,
                            "Balance MOP": custom_balance_mop if balance_mop == "Other" else balance_mop,
                            "MOB": mob_val,
                            "Online Source": custom_online_source if online_source == "Others" else online_source,
                            "Invoice No": invoice_no,
                            "Enquiry Date": enquiry_date,
                            "Booking Date": booking_date,
                            "Room Type": room_type,
                            "Breakfast": breakfast,
                            "Booking Status": booking_status,
                            "Submitted By": res["Submitted By"],
                            "Modified By": modified_by,
                            "Modified Comments": modified_comments,
                            "Remarks": remarks,
                            "Payment Status": payment_status
                        }
                        if update_reservation_in_supabase(res["Booking ID"], updated):
                            show_confirmation_dialog(res["Booking ID"], is_update=True)

        with col_del:
            if st.button("Delete", type="secondary", use_container_width=True):
                if delete_reservation_in_supabase(res["Booking ID"]):
                    st.success(f"Deleted {res['Booking ID']}")
                    st.rerun()

def show_online_reservations():
    st.header("Online Reservations")
    st.info("Online reservation module not implemented yet.")

def show_edit_online_reservations():
    st.header("Edit Online Reservations")
    st.info("Edit online reservation module not implemented yet.")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "New Direct Reservation",
    "Edit Direct Reservations",
    "Online Reservations",
    "Edit Online Reservations"
])

if page == "New Direct Reservation":
    show_new_reservation_form()
elif page == "Edit Direct Reservations":
    show_edit_reservations()
elif page == "Online Reservations":
    show_online_reservations()
elif page == "Edit Online Reservations":
    show_edit_online_reservations()
