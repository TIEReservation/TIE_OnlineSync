# directreservation.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# ----------------------------------------------------------------------
# 1. SUPABASE & SESSION STATE
# ----------------------------------------------------------------------
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}")
    st.stop()

# Session state defaults
if "reservations" not in st.session_state:
    st.session_state.reservations = []
if "role" not in st.session_state:
    st.session_state.role = "User"          # "Management" for admin rights
if "username" not in st.session_state:
    st.session_state.username = "User"

# ----------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ----------------------------------------------------------------------
def load_property_room_map():
    """Full property → room-type → rooms mapping (keep your original data)."""
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
        # ----- (all other properties – paste the rest from your original code) -----
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
        resp = supabase.table("reservations").select("booking_id") \
            .like("booking_id", f"TIE{today}%").execute()
        existing = {r["booking_id"] for r in resp.data}
        seq = 1
        while f"TIE{today}{seq:03d}" in existing:
            seq += 1
        return f"TIE{today}{seq:03d}"
    except Exception as e:
        st.error(f"ID generation error: {e}")
        return None

def check_duplicate_guest(guest_name, mobile_no, room_no,
                         exclude_booking_id=None, mob=None):
    try:
        resp = supabase.table("reservations").select("*").execute()
        for r in resp.data:
            if exclude_booking_id and r["booking_id"] == exclude_booking_id:
                continue
            if (r["guest_name"].lower() == guest_name.lower() and
                r["mobile_no"] == mobile_no and
                r["room_no"] == room_no):
                if mob == "Stay-back" and r["mob"] != "Stay-back":
                    continue
                return True, r["booking_id"]
        return False, None
    except Exception as e:
        st.error(f"Duplicate check error: {e}")
        return False, None

def calculate_days(ci, co):
    if ci and co and co >= ci:
        return max(1, (co - ci).days)
    return 1

def safe_int(v, default=0):
    try:
        return int(v) if v is not None else default
    except Exception:
        return default

def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except Exception:
        return default

# Live update helpers
def update_no_of_days(form_key):
    ci = st.session_state.get(f"{form_key}_checkin")
    co = st.session_state.get(f"{form_key}_checkout")
    st.session_state[f"{form_key}_days"] = calculate_days(ci, co)

def update_tariff_per_day(form_key):
    total = st.session_state.get(f"{form_key}_total_tariff", 0.0)
    days = st.session_state.get(f"{form_key}_days", 1)
    st.session_state[f"{form_key}_tariff_per_day"] = total / max(1, days)

# ----------------------------------------------------------------------
# 3. SUPABASE CRUD
# ----------------------------------------------------------------------
def load_reservations_from_supabase():
    try:
        resp = supabase.table("reservations").select("*").execute()
        out = []
        for r in resp.data:
            out.append({
                "Booking ID": r["booking_id"],
                "Property Name": r.get("property_name") or "",
                "Room No": r.get("room_no") or "",
                "Guest Name": r.get("guest_name") or "",
                "Mobile No": r.get("mobile_no") or "",
                "No of Adults": safe_int(r.get("no_of_adults")),
                "No of Children": safe_int(r.get("no_of_children")),
                "No of Infants": safe_int(r.get("no_of_infants")),
                "Total Pax": safe_int(r.get("total_pax")),
                "Check In": datetime.strptime(r["check_in"], "%Y-%m-%d").date()
                if r.get("check_in") else None,
                "Check Out": datetime.strptime(r["check_out"], "%Y-%m-%d").date()
                if r.get("check_out") else None,
                "No of Days": safe_int(r.get("no_of_days")),
                "Tariff": safe_float(r.get("tariff")),
                "Total Tariff": safe_float(r.get("total_tariff")),
                "Advance Amount": safe_float(r.get("advance_amount")),
                "Balance Amount": safe_float(r.get("balance_amount")),
                "Advance MOP": r.get("advance_mop") or "",
                "Balance MOP": r.get("balance_mop") or "",
                "MOB": r.get("mob") or "",
                "Online Source": r.get("online_source") or "",
                "Invoice No": r.get("invoice_no") or "",
                "Enquiry Date": datetime.strptime(r["enquiry_date"], "%Y-%m-%d").date()
                if r.get("enquiry_date") else None,
                "Booking Date": datetime.strptime(r["booking_date"], "%Y-%m-%d").date()
                if r.get("booking_date") else None,
                "Room Type": r.get("room_type") or "",
                "Breakfast": r.get("breakfast") or "",
                "Booking Status": r.get("plan_status") or "",
                "Submitted By": r.get("submitted_by") or "",
                "Modified By": r.get("modified_by") or "",
                "Modified Comments": r.get("modified_comments") or "",
                "Remarks": r.get("remarks") or "",
                "Payment Status": r.get("payment_status") or "Not Paid"
            })
        return out
    except Exception as e:
        st.error(f"Load error: {e}")
        return []

def save_reservation_to_supabase(res):
    try:
        data = {k.lower().replace(" ", "_"): v for k, v in res.items()}
        # convert dates
        for f in ["check_in", "check_out", "enquiry_date", "booking_date"]:
            if isinstance(data.get(f), date):
                data[f] = data[f].strftime("%Y-%m-%d")
        resp = supabase.table("reservations").insert(data).execute()
        if resp.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def update_reservation_in_supabase(bid, res):
    try:
        data = {k.lower().replace(" ", "_"): v for k, v in res.items()}
        for f in ["check_in", "check_out", "enquiry_date", "booking_date"]:
            if isinstance(data.get(f), date):
                data[f] = data[f].strftime("%Y-%m-%d")
        resp = supabase.table("reservations").update(data).eq("booking_id", bid).execute()
        if resp.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Update error: {e}")
        return False

def delete_reservation_in_supabase(bid):
    try:
        resp = supabase.table("reservations").delete().eq("booking_id", bid).execute()
        if resp.data:
            st.session_state.reservations = load_reservations_from_supabase()
            return True
        return False
    except Exception as e:
        st.error(f"Delete error: {e}")
        return False

# ----------------------------------------------------------------------
# 4. NEW RESERVATION FORM
# ----------------------------------------------------------------------
def show_new_reservation_form():
    st.header("New Direct Reservation")
    form_key = "new_res"
    pmap = load_property_room_map()

    # defaults
    if f"{form_key}_property" not in st.session_state:
        st.session_state[f"{form_key}_property"] = sorted(pmap.keys())[0]
    if f"{form_key}_days" not in st.session_state:
        st.session_state[f"{form_key}_days"] = 1

    # ---------- ROW 1 ----------
    c1, c2, c3 = st.columns(3)
    with c1:
        property = st.selectbox(
            "Property", sorted(pmap.keys()),
            key=f"{form_key}_property",
            on_change=lambda: st.session_state.update({f"{form_key}_room_type": ""})
        )
    with c2:
        guest = st.text_input("Guest Name", key=f"{form_key}_guest")
    with c3:
        mobile = st.text_input("Mobile No", key=f"{form_key}_mobile")

    # ---------- ROW 2 ----------
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        enquiry = st.date_input("Enquiry Date", value=date.today(), key=f"{form_key}_enquiry")
    with r2c2:
        check_in = st.date_input(
            "Check In", value=date.today(),
            key=f"{form_key}_checkin",
            on_change=lambda: update_no_of_days(form_key)
        )
    with r2c3:
        check_out = st.date_input(
            "Check Out", value=date.today() + timedelta(days=1),
            key=f"{form_key}_checkout",
            on_change=lambda: update_no_of_days(form_key)
        )
    with r2c4:
        days = st.session_state[f"{form_key}_days"]
        st.text_input("No of Days", value=days, disabled=True)

    # ---------- ROW 3 ----------
    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    with r3c1:
        adults = st.number_input("Adults", min_value=0, value=1, key=f"{form_key}_adults")
    with r3c2:
        children = st.number_input("Children", min_value=0, value=0, key=f"{form_key}_children")
    with r3c3:
        infants = st.number_input("Infants", min_value=0, value=0, key=f"{form_key}_infants")
    with r3c4:
        breakfast = st.selectbox("Breakfast", ["CP", "EP"], key=f"{form_key}_breakfast")

    # ---------- ROW 4 ----------
    r4c1, r4c2, r4c3, r4c4 = st.columns(4)
    with r4c1:
        total_pax = safe_int(adults) + safe_int(children) + safe_int(infants)
        st.text_input("Total Pax", value=total_pax, disabled=True)
    with r4c2:
        mob = st.selectbox(
            "MOB", [
                "Direct", "Online", "Agent", "Walk-in", "Phone",
                "Website", "Booking-Drt", "Social Media",
                "Stay-back", "TIE-Group", "Others"
            ],
            key=f"{form_key}_mob"
        )
        custom_mob = st.text_input("Custom MOB", key=f"{form_key}_custom_mob") if mob == "Others" else None
    with r4c3:
        rtypes = list(pmap[property].keys())
        room_type = st.selectbox("Room Type", rtypes, key=f"{form_key}_room_type")
    with r4c4:
        if room_type == "Others":
            room_no = st.text_input("Room No (custom)", key=f"{form_key}_room_no")
        else:
            suggestions = pmap[property].get(room_type, [])
            room_no = st.text_input(
                "Room No", placeholder="Enter or pick",
                key=f"{form_key}_room_no"
            )
            if suggestions:
                st.caption(f"Suggestions: {', '.join(suggestions)}")

    # ---------- ROW 5 ----------
    r5c1, r5c2, r5c3, r5c4 = st.columns(4)
    with r5c1:
        total_tariff = st.number_input(
            "Total Tariff", min_value=0.0, step=100.0,
            key=f"{form_key}_total_tariff",
            on_change=lambda: update_tariff_per_day(form_key)
        )
    with r5c2:
        tpd = st.session_state.get(f"{form_key}_tariff_per_day", 0.0)
        st.text_input("Tariff / day", value=f"₹{tpd:,.2f}", disabled=True)
    with r5c3:
        advance = st.number_input("Advance Amount", min_value=0.0, step=100.0, key=f"{form_key}_advance")
    with r5c4:
        adv_mop = st.selectbox(
            "Advance MOP", [" ", "Cash", "Card", "UPI", "Bank Transfer",
                           "ClearTrip", "TIE Management", "Booking.com",
                           "Pending", "Other"],
            key=f"{form_key}_advmop"
        )
        custom_adv_mop = st.text_input("Custom MOP", key=f"{form_key}_custom_advmop") if adv_mop == "Other" else None

    # ---------- ROW 6 ----------
    r6c1, r6c2 = st.columns(2)
    with r6c1:
        balance = max(0.0, total_tariff - safe_float(advance))
        st.text_input("Balance", value=f"₹{balance:,.2f}", disabled=True)
    with r6c2:
        bal_mop = st.selectbox(
            "Balance MOP", [" ", "Pending", "Cash", "Card", "UPI",
                           "Bank Transfer", "Other"],
            key=f"{form_key}_balmop"
        )
        custom_bal_mop = st.text_input("Custom Balance MOP", key=f"{form_key}_custom_balmop") if bal_mop == "Other" else None

    # ---------- ROW 7 ----------
    r7c1, r7c2, r7c3 = st.columns(3)
    with r7c1:
        booking_date = st.date_input("Booking Date", value=date.today(), key=f"{form_key}_booking")
    with r7c2:
        invoice = st.text_input("Invoice No", key=f"{form_key}_invoice")
    with r7c3:
        status = st.selectbox(
            "Booking Status", ["Confirmed", "Pending", "Cancelled",
                               "Completed", "No Show"],
            index=1, key=f"{form_key}_status"
        )

    # ---------- ROW 8 ----------
    remarks = st.text_area("Remarks", key=f"{form_key}_remarks")

    # ---------- ROW 9 ----------
    r9c1, r9c2 = st.columns(2)
    with r9c1:
        pay_status = st.selectbox(
            "Payment Status", ["Fully Paid", "Partially Paid", "Not Paid"],
            index=2, key=f"{form_key}_paystatus"
        )
    with r9c2:
        submitted = st.text_input(
            "Submitted By", value=st.session_state.username,
            disabled=True, key=f"{form_key}_submitted"
        )

    # ---------- ONLINE SOURCE ----------
    online_source = None
    custom_online = None
    if mob == "Online":
        src = st.selectbox(
            "Online Source", [
                "Booking.com", "Agoda Prepaid", "Agoda Booking.com",
                "Expedia", "MMT", "Cleartrip", "Others"
            ],
            key=f"{form_key}_online_src"
        )
        if src == "Others":
            custom_online = st.text_input("Custom Online Source", key=f"{form_key}_custom_online")
        else:
            online_source = src

    # ---------- SAVE ----------
    if st.button("Save Reservation", use_container_width=True):
        if not all([property, guest, mobile, room_no]):
            st.error("Fill all required fields")
        elif check_out < check_in:
            st.error("Check-out must be after Check-in")
        else:
            mob_val = custom_mob if mob == "Others" else mob
            dup, dup_id = check_duplicate_guest(guest, mobile, room_no.strip(), mob=mob_val)
            if dup:
                st.error(f"Guest already exists – Booking ID: {dup_id}")
            else:
                bid = generate_booking_id()
                if not bid:
                    st.error("Could not generate Booking ID")
                    return

                res = {
                    "Booking ID": bid,
                    "Property Name": property,
                    "Room No": room_no.strip(),
                    "Guest Name": guest,
                    "Mobile No": mobile,
                    "No of Adults": safe_int(adults),
                    "No of Children": safe_int(children),
                    "No of Infants": safe_int(infants),
                    "Total Pax": total_pax,
                    "Check In": check_in,
                    "Check Out": check_out,
                    "No of Days": days,
                    "Tariff": tpd,
                    "Total Tariff": safe_float(total_tariff),
                    "Advance Amount": safe_float(advance),
                    "Balance Amount": balance,
                    "Advance MOP": custom_adv_mop if adv_mop == "Other" else adv_mop,
                    "Balance MOP": custom_bal_mop if bal_mop == "Other" else bal_mop,
                    "MOB": mob_val,
                    "Online Source": custom_online if online_source == "Others" else online_source,
                    "Invoice No": invoice,
                    "Enquiry Date": enquiry,
                    "Booking Date": booking_date,
                    "Room Type": room_type,
                    "Breakfast": breakfast,
                    "Booking Status": status,
                    "Submitted By": submitted,
                    "Modified By": "",
                    "Modified Comments": "",
                    "Remarks": remarks,
                    "Payment Status": pay_status
                }
                if save_reservation_to_supabase(res):
                    st.success(f"Reservation {bid} saved!")
                    st.balloons()
                else:
                    st.error("Failed to save")

# ----------------------------------------------------------------------
# 5. VIEW RESERVATIONS (filterable table)
# ----------------------------------------------------------------------
def show_reservations():
    st.header("View Reservations")
    if not st.session_state.reservations:
        st.info("No reservations yet.")
        return

    df = pd.DataFrame(st.session_state.reservations)

    # ---- filters ----
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        start = st.date_input("Check-In From", value=None, key="v_start")
    with fcol2:
        end = st.date_input("Check-In To", value=None, key="v_end")
    with fcol3:
        status = st.selectbox(
            "Status", ["All"] + sorted(df["Booking Status"].unique()),
            key="v_status"
        )
    with fcol4:
        prop = st.selectbox(
            "Property", ["All"] + sorted(df["Property Name"].unique()),
            key="v_prop"
        )

    filt = df.copy()
    if start:
        filt = filt[filt["Check In"] >= start]
    if end:
        filt = filt[filt["Check In"] <= end]
    if status != "All":
        filt = filt[filt["Booking Status"] == status]
    if prop != "All":
        filt = filt[filt["Property Name"] == prop]

    st.dataframe(
        filt[[
            "Booking ID", "Guest Name", "Mobile No", "Property Name",
            "Room No", "Check In", "Check Out", "No of Days",
            "Total Tariff", "Booking Status", "Payment Status"
        ]],
        use_container_width=True
    )

# ----------------------------------------------------------------------
# 6. EDIT RESERVATIONS
# ----------------------------------------------------------------------
def show_edit_reservations():
    st.header("Edit / Delete Reservations")
    if not st.session_state.reservations:
        st.info("No data to edit.")
        return

    df = pd.DataFrame(st.session_state.reservations)
    bid = st.selectbox("Select Booking ID", df["Booking ID"].tolist(), key="edit_bid")
    rec = df[df["Booking ID"] == bid].iloc[0].to_dict()

    form_key = f"edit_{bid}"
    pmap = load_property_room_map()

    # defaults
    if f"{form_key}_property" not in st.session_state:
        st.session_state[f"{form_key}_property"] = rec["Property Name"]
    if f"{form_key}_days" not in st.session_state:
        st.session_state[f"{form_key}_days"] = rec["No of Days"]

    # ----- ROW 1 -----
    c1, c2, c3 = st.columns(3)
    with c1:
        prop = st.selectbox(
            "Property", sorted(pmap.keys()),
            index=sorted(pmap.keys()).index(st.session_state[f"{form_key}_property"]),
            key=f"{form_key}_property"
        )
    with c2:
        guest = st.text_input("Guest Name", value=rec["Guest Name"], key=f"{form_key}_guest")
    with c3:
        mobile = st.text_input("Mobile No", value=rec["Mobile No"], key=f"{form_key}_mobile")

    # ----- ROW 2 -----
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        enquiry = st.date_input(
            "Enquiry Date", value=rec["Enquiry Date"] or date.today(),
            key=f"{form_key}_enquiry"
        )
    with r2c2:
        ci = st.date_input(
            "Check In", value=rec["Check In"],
            key=f"{form_key}_checkin",
            on_change=lambda: update_no_of_days(form_key)
        )
    with r2c3:
        co = st.date_input(
            "Check Out", value=rec["Check Out"],
            key=f"{form_key}_checkout",
            on_change=lambda: update_no_of_days(form_key)
        )
    with r2c4:
        days = st.session_state[f"{form_key}_days"]
        st.text_input("No of Days", value=days, disabled=True)

    # ----- ROW 3 -----
    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    with r3c1:
        adults = st.number_input("Adults", min_value=0, value=rec["No of Adults"], key=f"{form_key}_adults")
    with r3c2:
        children = st.number_input("Children", min_value=0, value=rec["No of Children"], key=f"{form_key}_children")
    with r3c3:
        infants = st.number_input("Infants", min_value=0, value=rec["No of Infants"], key=f"{form_key}_infants")
    with r3c4:
        breakfast = st.selectbox(
            "Breakfast", ["CP", "EP"],
            index=["CP", "EP"].index(rec["Breakfast"]),
            key=f"{form_key}_breakfast"
        )

    # ----- ROW 4 -----
    r4c1, r4c2, r4c3, r4c4 = st.columns(4)
    with r4c1:
        total_pax = safe_int(adults) + safe_int(children) + safe_int(infants)
        st.text_input("Total Pax", value=total_pax, disabled=True)
    with r4c2:
        mob_opts = ["Direct", "Online", "Agent", "Walk-in", "Phone",
                    "Website", "Booking-Drt", "Social Media",
                    "Stay-back", "TIE-Group", "Others"]
        mob_idx = mob_opts.index(rec["MOB"]) if rec["MOB"] in mob_opts else len(mob_opts)-1
        mob = st.selectbox("MOB", mob_opts, index=mob_idx, key=f"{form_key}_mob")
        custom_mob = st.text_input("Custom MOB", value=rec["MOB"] if mob_idx == len(mob_opts)-1 else "", key=f"{form_key}_custom_mob") if mob == "Others" else None
    with r4c3:
        rtypes = list(pmap[prop].keys())
        rt_idx = rtypes.index(rec["Room Type"]) if rec["Room Type"] in rtypes else 0
        room_type = st.selectbox("Room Type", rtypes, index=rt_idx, key=f"{form_key}_room_type")
    with r4c4:
        if room_type == "Others":
            room_no = st.text_input("Room No (custom)", value=rec["Room No"], key=f"{form_key}_room_no")
        else:
            suggestions = pmap[prop].get(room_type, [])
            room_no = st.text_input(
                "Room No", value=rec["Room No"],
                key=f"{form_key}_room_no"
            )
            if suggestions:
                st.caption(f"Suggestions: {', '.join(suggestions)}")

    # ----- ROW 5 -----
    r5c1, r5c2, r5c3, r5c4 = st.columns(4)
    with r5c1:
        total_tariff = st.number_input(
            "Total Tariff", min_value=0.0, step=100.0,
            value=rec["Total Tariff"],
            key=f"{form_key}_total_tariff",
            on_change=lambda: update_tariff_per_day(form_key)
        )
    with r5c2:
        tpd = st.session_state.get(f"{form_key}_tariff_per_day", rec["Tariff"])
        st.text_input("Tariff / day", value=f"₹{tpd:,.2f}", disabled=True)
    with r5c3:
        advance = st.number_input(
            "Advance Amount", min_value=0.0, step=100.0,
            value=rec["Advance Amount"], key=f"{form_key}_advance"
        )
    with r5c4:
        adv_opts = ["Cash", "Card", "UPI", "Bank Transfer",
                    "ClearTrip", "TIE Management", "Booking.com",
                    "Pending", "Other"]
        adv_idx = adv_opts.index(rec["Advance MOP"]) if rec["Advance MOP"] in adv_opts else len(adv_opts)-1
        adv_mop = st.selectbox("Advance MOP", adv_opts, index=adv_idx, key=f"{form_key}_advmop")
        custom_adv_mop = st.text_input("Custom MOP", value=rec["Advance MOP"] if adv_idx == len(adv_opts)-1 else "", key=f"{form_key}_custom_advmop") if adv_mop == "Other" else None

    # ----- ROW 6 -----
    r6c1, r6c2 = st.columns(2)
    with r6c1:
        balance = max(0.0, total_tariff - safe_float(advance))
        st.text_input("Balance", value=f"₹{balance:,.2f}", disabled=True)
    with r6c2:
        bal_opts = ["Pending", "Cash", "Card", "UPI", "Bank Transfer", "Other"]
        bal_idx = bal_opts.index(rec["Balance MOP"]) if rec["Balance MOP"] in bal_opts else 0
        bal_mop = st.selectbox("Balance MOP", bal_opts, index=bal_idx, key=f"{form_key}_balmop")
        custom_bal_mop = st.text_input("Custom Balance MOP", value=rec["Balance MOP"] if bal_idx == len(bal_opts)-1 else "", key=f"{form_key}_custom_balmop") if bal_mop == "Other" else None

    # ----- ROW 7 -----
    r7c1, r7c2, r7c3 = st.columns(3)
    with r7c1:
        booking_date = st.date_input("Booking Date", value=rec["Booking Date"], key=f"{form_key}_booking")
    with r7c2:
        invoice = st.text_input("Invoice No", value=rec["Invoice No"], key=f"{form_key}_invoice")
    with r7c3:
        status_opts = ["Confirmed", "Pending", "Cancelled", "Completed", "No Show"]
        status_idx = status_opts.index(rec["Booking Status"])
        status = st.selectbox("Booking Status", status_opts, index=status_idx, key=f"{form_key}_status")

    # ----- ROW 8 -----
    remarks = st.text_area("Remarks", value=rec["Remarks"], key=f"{form_key}_remarks")

    # ----- ROW 9 -----
    r9c1, r9c2 = st.columns(2)
    with r9c1:
        pay_opts = ["Fully Paid", "Partially Paid", "Not Paid"]
        pay_idx = pay_opts.index(rec["Payment Status"])
        pay_status = st.selectbox("Payment Status", pay_opts, index=pay_idx, key=f"{form_key}_paystatus")
    with r9c2:
        modified_by = st.text_input("Modified By", value=st.session_state.username, key=f"{form_key}_modby")

    # ----- SAVE / DELETE -----
    col_save, col_del = st.columns([1, 1])
    with col_save:
        if st.button("Update Reservation", use_container_width=True):
            if not all([prop, guest, mobile, room_no]):
                st.error("Required fields missing")
            elif co < ci:
                st.error("Check-out must be after Check-in")
            else:
                mob_val = custom_mob if mob == "Others" else mob
                dup, dup_id = check_duplicate_guest(
                    guest, mobile, room_no.strip(),
                    exclude_booking_id=bid, mob=mob_val
                )
                if dup:
                    st.error(f"Guest conflict – Booking ID: {dup_id}")
                else:
                    updated = {
                        "Booking ID": bid,
                        "Property Name": prop,
                        "Room No": room_no.strip(),
                        "Guest Name": guest,
                        "Mobile No": mobile,
                        "No of Adults": safe_int(adults),
                        "No of Children": safe_int(children),
                        "No of Infants": safe_int(infants),
                        "Total Pax": total_pax,
                        "Check In": ci,
                        "Check Out": co,
                        "No of Days": days,
                        "Tariff": tpd,
                        "Total Tariff": safe_float(total_tariff),
                        "Advance Amount": safe_float(advance),
                        "Balance Amount": balance,
                        "Advance MOP": custom_adv_mop if adv_mop == "Other" else adv_mop,
                        "Balance MOP": custom_bal_mop if bal_mop == "Other" else bal_mop,
                        "MOB": mob_val,
                        "Online Source": rec["Online Source"],   # keep existing or add logic
                        "Invoice No": invoice,
                        "Enquiry Date": enquiry,
                        "Booking Date": booking_date,
                        "Room Type": room_type,
                        "Breakfast": breakfast,
                        "Booking Status": status,
                        "Submitted By": rec["Submitted By"],
                        "Modified By": modified_by,
                        "Modified Comments": rec["Modified Comments"],
                        "Remarks": remarks,
                        "Payment Status": pay_status
                    }
                    if update_reservation_in_supabase(bid, updated):
                        st.success(f"Updated {bid}")
                        st.balloons()
                    else:
                        st.error("Update failed")
    with col_del:
        if st.session_state.role == "Management":
            if st.button("Delete Reservation", use_container_width=True, type="primary"):
                if delete_reservation_in_supabase(bid):
                    st.success(f"Deleted {bid}")
                    st.rerun()
                else:
                    st.error("Delete failed")

# ----------------------------------------------------------------------
# 7. EXPORTED NAMES (so `app.py` can import them cleanly)
# ----------------------------------------------------------------------
__all__ = [
    "show_new_reservation_form",
    "show_reservations",
    "show_edit_reservations"
]
