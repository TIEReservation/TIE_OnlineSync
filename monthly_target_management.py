import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from log import log_activity

# Monthly Target Management using the existing `monthly_targets` table.
# Assumes `st.session_state.supabase_client` is available and the table has columns:
# id (uuid), property_name (text), year (int), month (int), target (numeric),
# created_at, updated_at
# A UNIQUE constraint on (property_name, year, month) is required for upsert, e.g.:
#   ALTER TABLE monthly_targets
#   ADD CONSTRAINT monthly_targets_prop_year_month_key UNIQUE (property_name, year, month);

TABLE_NAME = "monthly_targets"

PROPERTIES = [
    "Le Park Resort",
    "La Tamara Luxury",
    "Le Poshe Luxury",
    "Le Poshe Suite",
    "Eden Beach Resort",
    "La Antilia Luxury",
    "La Coromandel Luxury",
    "La Tamara Suite",
    "Villa Shakti",
    "La Paradise Luxury",
    "La Villa Heritage",
    "La Paradise Residency",
    "Le Royce Villa",
]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def fetch_targets(supabase):
    try:
        resp = (
            supabase.table(TABLE_NAME)
            .select("id, property_name, year, month, target, created_at, updated_at")
            .order("year", desc=True)
            .order("month", desc=True)
            .execute()
        )
        return resp.data if resp and hasattr(resp, "data") and resp.data else []
    except Exception as e:
        st.error(f"Failed to fetch monthly targets: {e}")
        return []


def upsert_target(supabase, property_name, year, month, target, user):
    """Insert or update a single property's target."""
    try:
        payload = {
            "property_name": property_name,
            "year": int(year),
            "month": int(month),
            "target": float(target),
            "updated_at": _now_iso(),
        }
        resp = (
            supabase.table(TABLE_NAME)
            .upsert(payload, on_conflict="property_name,year,month")
            .execute()
        )
        log_activity(supabase, user, f"Upserted monthly target for {property_name} {year}-{month}: {target}")
        return resp
    except Exception as e:
        st.error(f"Failed to save target: {e}")
        return None


def upsert_targets_bulk(supabase, targets_by_property, year, month, user):
    """Insert or update targets for many properties in one call."""
    try:
        now = _now_iso()
        payload = [
            {
                "property_name": prop,
                "year": int(year),
                "month": int(month),
                "target": float(value),
                "updated_at": now,
            }
            for prop, value in targets_by_property.items()
        ]
        resp = (
            supabase.table(TABLE_NAME)
            .upsert(payload, on_conflict="property_name,year,month")
            .execute()
        )
        log_activity(
            supabase,
            user,
            f"Saved monthly targets for {year}-{month} ({len(payload)} properties)",
        )
        return resp
    except Exception as e:
        st.error(f"Failed to save targets: {e}")
        return None


def delete_target(supabase, row_id, user):
    try:
        resp = supabase.table(TABLE_NAME).delete().eq("id", row_id).execute()
        log_activity(supabase, user, f"Deleted monthly target id={row_id}")
        return resp
    except Exception as e:
        st.error(f"Failed to delete target: {e}")
        return None


def _clear_target_inputs():
    """Remove cached number_input values so the form re-reads from the database."""
    for k in [k for k in st.session_state.keys() if str(k).startswith("target_")]:
        del st.session_state[k]


def show_monthly_target_management():
    # Ensure supabase client is available in session state
    supabase = st.session_state.get("supabase_client")
    if not supabase:
        st.error("Supabase client not available in session state. Please reload the app.")
        return

    st.header("Monthly Target Management")

    user = st.session_state.get("username", "Unknown")
    now = datetime.now(timezone.utc)

    # Defaults for the Year / Month widgets (set before the widgets are created)
    st.session_state.setdefault("mtm_year", now.year)
    st.session_state.setdefault("mtm_month", now.month)

    # Fetch existing targets
    targets = fetch_targets(supabase)
    df = pd.DataFrame(targets)

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        db_properties = (
            df["property_name"].unique().tolist()
            if not df.empty and "property_name" in df.columns
            else []
        )
        properties = sorted(set(PROPERTIES) | set(db_properties))
        prop_filter = st.selectbox("Property", options=["All"] + properties, index=0)
    with col2:
        years = (
            sorted(df["year"].unique().tolist(), reverse=True)
            if not df.empty and "year" in df.columns
            else [now.year]
        )
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

    # ------------------------------------------------------------------
    # Existing targets
    # ------------------------------------------------------------------
    st.subheader("Existing Targets")
    if filtered.empty:
        st.info("No monthly targets found for the selected filters.")
    else:
        display_df = filtered[
            ["id", "property_name", "year", "month", "target", "updated_at"]
        ].copy()
        display_df = display_df.rename(
            columns={
                "property_name": "Property",
                "year": "Year",
                "month": "Month",
                "target": "Target",
                "updated_at": "Last Updated",
                "id": "ID",
            }
        )
        st.dataframe(display_df.reset_index(drop=True))

        st.write("---")
        st.subheader("Manage Existing Targets")

        pending_delete = st.session_state.get("mtm_pending_delete")

        for _, row in display_df.iterrows():
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.write(f"**{row['Property']} — {int(row['Year'])}-{int(row['Month'])}**")
                st.write(f"Target: {row['Target']}")
                st.write(f"Last updated: {row['Last Updated']}")

            with cols[1]:
                if st.button("Edit", key=f"edit_{row['ID']}"):
                    # Jump the form below to this row's year/month
                    st.session_state["mtm_year"] = int(row["Year"])
                    st.session_state["mtm_month"] = int(row["Month"])
                    st.session_state.pop("mtm_pending_delete", None)
                    st.rerun()

            with cols[2]:
                if pending_delete == row["ID"]:
                    st.warning("Delete this target?")
                    if st.button("Yes, delete", key=f"confirm_delete_{row['ID']}"):
                        delete_target(supabase, row["ID"], user)
                        st.session_state.pop("mtm_pending_delete", None)
                        _clear_target_inputs()
                        st.success("Deleted target")
                        st.rerun()
                    if st.button("Cancel", key=f"cancel_delete_{row['ID']}"):
                        st.session_state.pop("mtm_pending_delete", None)
                        st.rerun()
                else:
                    if st.button("Delete", key=f"delete_{row['ID']}"):
                        st.session_state["mtm_pending_delete"] = row["ID"]
                        st.rerun()

    # ------------------------------------------------------------------
    # Create / update targets for all properties
    # ------------------------------------------------------------------
    st.write("---")
    st.subheader("Create / Update Targets")

    col_y, col_m = st.columns(2)
    with col_y:
        year = st.number_input("Year", min_value=2000, max_value=2100, step=1, key="mtm_year")
    with col_m:
        month = st.selectbox("Month", options=list(range(1, 13)), key="mtm_month")

    # Existing targets for the selected year/month, used to pre-fill the boxes
    existing = {}
    if not df.empty:
        match = df[(df["year"] == int(year)) & (df["month"] == int(month))]
        existing = dict(zip(match["property_name"], match["target"]))

    with st.form("monthly_target_form"):
        st.caption(
            "Enter a target for each property. Properties with no saved target "
            "and a value of 0 are skipped."
        )
        values = {}
        for prop in PROPERTIES:
            values[prop] = st.number_input(
                prop,
                min_value=0.0,
                format="%.2f",
                value=float(existing.get(prop, 0.0)),
                key=f"target_{prop}_{int(year)}_{int(month)}",
            )
        submitted = st.form_submit_button("Save Targets")

    if submitted:
        # Save properties with a value > 0, plus properties that already have a
        # saved target (so an existing target can be updated, even back to 0).
        to_save = {p: v for p, v in values.items() if v > 0 or p in existing}
        if not to_save:
            st.error("Enter a target for at least one property")
        else:
            if upsert_targets_bulk(supabase, to_save, int(year), int(month), user):
                st.success(f"Saved targets for {len(to_save)} properties")
                st.rerun()


# If run as module directly (for local testing), show the UI
if __name__ == "__main__":
    show_monthly_target_management()
