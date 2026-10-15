import streamlit as st
import pandas as pd
from datetime import datetime
from log import log_activity

# Simple UI for Monthly Target Management using existing `monthly_targets` table
# Assumes `st.session_state.supabase_client` is available and that table exists with columns:
# id (uuid), property_name (text), year (int), month (int), target (numeric), created_at, updated_at

TABLE_NAME = "monthly_targets"


def fetch_targets(supabase):
    try:
        resp = supabase.table(TABLE_NAME).select("id, property_name, year, month, target, created_at, updated_at").order("year", desc=True).order("month", desc=True).execute()
        return resp.data if resp and hasattr(resp, "data") else []
    except Exception as e:
        st.error(f"Failed to fetch monthly targets: {e}")
        return []


def upsert_target(supabase, property_name, year, month, target, user):
    try:
        payload = {
            "property_name": property_name,
            "year": int(year),
            "month": int(month),
            "target": float(target),
            "updated_at": datetime.utcnow().isoformat()
        }
        # Use upsert to insert or update the unique (property_name, year, month) row
        resp = supabase.table(TABLE_NAME).upsert(payload, on_conflict=["property_name", "year", "month"]).execute()
        log_activity(supabase, user, f"Upserted monthly target for {property_name} {year}-{month}: {target}")
        return resp
    except Exception as e:
        st.error(f"Failed to save target: {e}")
        return None


def delete_target(supabase, row_id, user):
    try:
        resp = supabase.table(TABLE_NAME).delete().eq("id", row_id).execute()
        log_activity(supabase, user, f"Deleted monthly target id={row_id}")
        return resp
    except Exception as e:
        st.error(f"Failed to delete target: {e}")
        return None


def show_monthly_target_management():
    # Ensure supabase client is available in session state
    supabase = st.session_state.get("supabase_client")
    if not supabase:
        st.error("Supabase client not available in session state. Please reload the app.")
        return

    st.header("Monthly Target Management")

    user = st.session_state.get("username", "Unknown")

    # Fetch existing targets
    targets = fetch_targets(supabase)
    df = pd.DataFrame(targets)

    # Filters
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        properties = sorted(df["property_name"].unique().tolist()) if not df.empty and "property_name" in df.columns else []
        properties = properties or ["Le Poshe Beachview", "La Millionaire Resort", "La Poshe Luxury"]
        prop_filter = st.selectbox("Property", options=["All"] + properties, index=0)
    with col2:
        years = sorted(df["year"].unique().tolist(), reverse=True) if not df.empty and "year" in df.columns else [datetime.utcnow().year]
        year_filter = st.selectbox("Year", options=["All"] + years, index=0)
    with col3:
        months = list(range(1, 13))
        month_filter = st.selectbox("Month", options=["All"] + months, index=0)

    filtered = df.copy()
    if not filtered.empty:
        if prop_filter != "All":
            filtered = filtered[filtered["property_name"] == prop_filter]
        if year_filter != "All":
            filtered = filtered[filtered["year"] == int(year_filter)]
        if month_filter != "All":
            filtered = filtered[filtered["month"] == int(month_filter)]

    st.subheader("Existing Targets")
    if filtered.empty:
        st.info("No monthly targets found for the selected filters.")
    else:
        # Show user-friendly table
        display_df = filtered[["id", "property_name", "year", "month", "target", "updated_at"]].copy()
        display_df = display_df.rename(columns={"property_name": "Property", "year": "Year", "month": "Month", "target": "Target", "updated_at": "Last Updated", "id": "ID"})
        st.dataframe(display_df.reset_index(drop=True))

        # Provide Delete buttons per row
        st.write("---")
        st.subheader("Manage Existing Targets")
        for idx, row in display_df.iterrows():
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.write(f"**{row['Property']} — {int(row['Year'])}-{int(row['Month'])}**")
                st.write(f"Target: {row['Target']}")
                st.write(f"Last updated: {row['Last Updated']}")
            with cols[1]:
                if st.button(f"Edit-{row['ID']}", key=f"edit_{row['ID']}"):
                    # Pre-fill form by setting session state
                    st.session_state['mtm_edit_id'] = row['ID']
                    st.session_state['mtm_edit_property'] = row['Property']
                    st.session_state['mtm_edit_year'] = int(row['Year'])
                    st.session_state['mtm_edit_month'] = int(row['Month'])
                    st.session_state['mtm_edit_target'] = float(row['Target'])
                    st.experimental_rerun()
            with cols[2]:
                if st.button(f"Delete-{row['ID']}", key=f"delete_{row['ID']}"):
                    confirm = st.confirm(f"Are you sure you want to delete target for {row['Property']} {row['Year']}-{row['Month']}?") if hasattr(st, 'confirm') else True
                    if confirm:
                        delete_target(supabase, row['ID'], user)
                        st.success("Deleted target")
                        st.experimental_rerun()

    st.write("---")
    st.subheader("Create / Update Target")

    # If editing an existing row, prefill
    edit_id = st.session_state.get('mtm_edit_id')
    default_property = st.session_state.get('mtm_edit_property', None)
    default_year = st.session_state.get('mtm_edit_year', datetime.utcnow().year)
    default_month = st.session_state.get('mtm_edit_month', datetime.utcnow().month)
    default_target = st.session_state.get('mtm_edit_target', 0.0)

    with st.form("monthly_target_form"):
        property_name = st.text_input("Property Name", value=default_property or "")
        year = st.number_input("Year", min_value=2000, max_value=2100, value=int(default_year))
        month = st.selectbox("Month", options=list(range(1, 13)), index=(int(default_month) - 1))
        target = st.number_input("Target (numeric)", min_value=0.0, format="%.2f", value=float(default_target))
        submitted = st.form_submit_button("Save Target")
        if submitted:
            if not property_name:
                st.error("Property name is required")
            else:
                upsert_target(supabase, property_name.strip(), int(year), int(month), target, user)
                st.success("Target saved")
                # clear edit session state
                for k in ["mtm_edit_id", "mtm_edit_property", "mtm_edit_year", "mtm_edit_month", "mtm_edit_target"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.experimental_rerun()


# If run as module directly (for local testing), show the UI
if __name__ == "__main__":
    show_monthly_target_management()
