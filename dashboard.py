# dashboard.py

import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import pandas as pd  # Explicitly included
import altair as alt
from online_reservation import load_online_reservations_from_supabase
from directreservation import load_reservations_from_supabase

# Initialize Supabase client
try:
    supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except KeyError as e:
    st.error(f"Missing Supabase secret: {e}. Please check Streamlit Cloud secrets configuration.")
    st.stop()

# Property synonym mapping
property_mapping = {
    "La Millionaire Luxury Resort": "La Millionaire Resort",
    "Le Poshe Beach View": "Le Poshe Beach view",
    "Le Poshe Beach view": "Le Poshe Beach view",
    "Le Poshe Beach VIEW": "Le Poshe Beach view",
    "Millionaire": "La Millionaire Resort",
}

def get_property_name(booking):
    return booking.get("property") or booking.get("property_name")

@st.cache_data(ttl=300)
def cached_load_all_bookings():
    online = load_online_reservations_from_supabase()
    direct = load_reservations_from_supabase()
    # normalize properties
    for b in online:
        if "property" in b:
            b["property"] = property_mapping.get(b["property"], b["property"])
        b["source"] = "online"
        b["submitted_by"] = "online"
    for b in direct:
        if "property_name" in b:
            b["property_name"] = property_mapping.get(b["property_name"], b["property_name"])
        b["source"] = "direct"
        if "plan_status" in b:
            b["booking_status"] = b["plan_status"]
    return online + direct

def filter_bookings_for_day(bookings, target_date):
    filtered = []
    for b in bookings:
        try:
            check_in = date.fromisoformat(b["check_in"]) if b.get("check_in") else None
            check_out = date.fromisoformat(b["check_out"]) if b.get("check_out") else None
            if check_in and check_out and check_in <= target_date < check_out:
                filtered.append(b)
        except:
            pass
    return filtered

def count_status(properties, target_date, statuses):
    relevant = [b for b in all_bookings if get_property_name(b) in properties]
    active = filter_bookings_for_day(relevant, target_date)
    count = len([b for b in active if b.get("booking_status") in statuses])
    return count

def count_status_person(properties, target_date, statuses, person):
    relevant = [b for b in all_bookings if get_property_name(b) in properties and b.get("submitted_by", "").lower() == person.lower()]
    active = filter_bookings_for_day(relevant, target_date)
    count = len([b for b in active if b.get("booking_status") in statuses])
    return count

teams = {
    "Game Changers": {
        "members": ["Shan", "Barathan", "Anand"],
        "properties": {
            "Le Park Resort": 6,
            "Le Royce Villa": 4,
            "Villa Shakti": 11,
            "Le Poshe Luxury": 18,
            "La Millionaire Resort": 22
        },
        "total_inventory": 61
    },
    "Dream Squad": {
        "members": ["Nandhini", "Thilak", "Prakash"],
        "properties": {
            "Eden Beach Resort": 5,
            "La Paradise Luxury": 6,
            "La Villa Heritage": 7,
            "Le Pondy Beachside": 4,
            "Le Poshe Beach view": 10,
            "Le Poshe Suite": 9
        },
        "total_inventory": 41
    }
}

individuals = {
    "Barath": {"properties": {"La Antilia Luxury": 10}},
    "Rajesh": {"properties": {"La Tamara Luxury": 22}},
    "Bala": {"properties": {"La Tamara Suite": 10}}
}

def show_dashboard():
    st.title("Gamified Reservation Dashboard")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing data...")
        st.rerun()
    
    global all_bookings
    all_bookings = cached_load_all_bookings()
    
    ref_date = st.date_input("Select Reference Date", date(2025, 10, 27))  # Default to current date (08:08 PM IST, Oct 27, 2025)
    dates = [ref_date - timedelta(days=1), ref_date, ref_date + timedelta(days=1), ref_date + timedelta(days=2)]
    date_names = [d.strftime("%Y-%m-%d") for d in dates]  # Use actual dates: Yesterday, Today, Tomorrow, Day After Tomorrow
    
    tab1, tab2, tab3 = st.tabs(["Team Competition", "Individual Performance", "Property Performance"])
    
    with tab1:
        st.subheader("Team Competition View")
        
        team_metrics = {}
        for team_name, team_data in teams.items():
            props = list(team_data["properties"].keys())
            total_inv = team_data["total_inventory"]
            metrics = []
            for d in dates:
                sold = count_status(props, d, ["Confirmed"])
                follow = count_status(props, d, ["Follow-up"])
                pend = count_status(props, d, ["Pending"])
                avail = total_inv - sold - follow - pend
                metrics.append({"sold": sold, "follow": follow, "pend": pend, "avail": avail})
            team_metrics[team_name] = {"metrics": metrics, "total_inv": total_inv}
            total_sold = sum(m["sold"] for m in metrics)
            avg_occ = (total_sold / (total_inv * len(dates))) * 100 if total_inv > 0 else 0
            team_metrics[team_name]["avg_occ"] = avg_occ
        
        cols = st.columns([1] + [3] * len(dates))
        cols[0].write("**Team (Total Inv)**")
        for i, name in enumerate(date_names):
            cols[i+1].write(f"**{name}**")
        
        for team_name, data in team_metrics.items():
            cols = st.columns([1] + [3] * len(dates))
            cols[0].write(f"{team_name} ({data['total_inv']})")
            for i, m in enumerate(data["metrics"]):
                with cols[i+1]:
                    st.write(f"Sold: {m['sold']}")
                    st.write(f"Follow-up: {m['follow']}")
                    chart_data = pd.DataFrame({
                        "Status": ["Sold", "Follow-up", "Available"],
                        "Count": [m['sold'], m['follow'], m['avail'] + m['pend']]
                    })
                    pie = alt.Chart(chart_data).mark_arc().encode(
                        theta="Count:Q",
                        color=alt.Color("Status:N", scale=alt.Scale(domain=["Sold", "Follow-up", "Available"], range=["green", "orange", "red"])),
                        tooltip=["Status", "Count"]
                    ).properties(width=150, height=150)
                    st.altair_chart(pie, use_container_width=True)
        
        st.subheader("Team Leaderboard")
        sorted_teams = sorted(team_metrics.items(), key=lambda x: x[1]["avg_occ"], reverse=True)
        for rank, (name, data) in enumerate(sorted_teams, 1):
            st.write(f"{rank}. {name} - Avg Occupancy: {data['avg_occ']:.2f}%")
    
    with tab2:
        st.subheader("Individual Performance")
        
        members = []
        for team, tdata in teams.items():
            for mem in tdata["members"]:
                members.append({"name": mem, "team": team, "properties": tdata["properties"], "total_inv": sum(tdata["properties"].values())})
        for name, idata in individuals.items():
            members.append({"name": name, "team": "Individual", "properties": idata["properties"], "total_inv": sum(idata["properties"].values())})
        
        individual_metrics = {}
        for mem in members:
            props_dict = mem["properties"]
            props = list(props_dict.keys())
            total_sold = 0
            total_follow = 0
            prop_details = {}
            for p in props:
                sold_p = 0
                follow_p = 0
                for d in dates:
                    sold_d = count_status_person([p], d, ["Confirmed"], mem["name"])
                    follow_d = count_status_person([p], d, ["Follow-up"], mem["name"])
                    sold_p += sold_d
                    follow_p += follow_d
                prop_details[p] = {"sold": sold_p, "follow": follow_p}
                total_sold += sold_p
                total_follow += follow_p
            conv_rate = (total_sold / (total_sold + total_follow)) * 100 if (total_sold + total_follow) > 0 else 0
            individual_metrics[mem["name"]] = {"total_sold": total_sold, "total_follow": total_follow, "conv_rate": conv_rate, "prop_details": prop_details, "team": mem["team"]}
        
        st.subheader("Individual Leaderboard")
        sorted_inds = sorted(individual_metrics.items(), key=lambda x: x[1]["total_sold"], reverse=True)
        for rank, (name, data) in enumerate(sorted_inds, 1):
            st.write(f"{rank}. {name} ({data['team']}) - Sold Room-Nights: {data['total_sold']}, Conversion Rate: {data['conv_rate']:.2f}%")
        
        selected_member = st.selectbox("Select Member for Details", list(individual_metrics.keys()))
        if selected_member:
            data = individual_metrics[selected_member]
            st.write(f"**Name:** {selected_member}")
            st.write(f"**Team:** {data['team']}")
            st.write(f"**Total Confirmed Room-Nights (over 4 days):** {data['total_sold']}")
            st.write(f"**Total Follow-ups (over 4 days):** {data['total_follow']}")
            st.write("**Properties Assigned and Performance:**")
            for p, pd in data["prop_details"].items():
                st.write(f"- {p} ({mem['properties'][p]} inventories): Confirmed {pd['sold']}, Follow-ups {pd['follow']}")
    
    with tab3:
        st.subheader("Property Performance")
        
        all_props = {}
        for team, tdata in teams.items():
            all_props.update(tdata["properties"])
        for idata in individuals.values():
            all_props.update(idata["properties"])
        
        prop_metrics = {}
        for p, inv in all_props.items():
            metrics = []
            for d in dates:
                sold = count_status([p], d, ["Confirmed"])
                follow = count_status([p], d, ["Follow-up"])
                pend = count_status([p], d, ["Pending"])
                avail = inv - sold - follow - pend
                occ = (sold / inv * 100) if inv > 0 else 0
                metrics.append({"sold": sold, "occ": occ, "follow": follow, "pend": pend, "avail": avail})
            avg_occ = sum(m["occ"] for m in metrics) / len(metrics)
            total_sold = sum(m["sold"] for m in metrics)
            prop_metrics[p] = {"avg_occ": avg_occ, "total_sold": total_sold, "inv": inv, "metrics": metrics}
        
        df = pd.DataFrame([{"Property": p, "Inventory": d["inv"], "Total Sold Room-Nights (4 days)": d["total_sold"], "Avg Occupancy %": f"{d['avg_occ']:.2f}"} for p, d in prop_metrics.items()])
        st.dataframe(df)
        
        bar = alt.Chart(df).mark_bar().encode(
            x="Property",
            y="Avg Occupancy %:Q",
            tooltip=["Property", "Avg Occupancy %", "Inventory"]
        ).properties(width=700)
        st.altair_chart(bar)
        
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Property Data", csv, "property_performance.csv", "text/csv")
