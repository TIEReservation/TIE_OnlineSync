import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

# Reuse the same Supabase credentials as app.py
SUPABASE_URL = "https://oxbrezracnmazucnnqox.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94YnJlenJhY25tYXp1Y25ucW94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjUxMTgsImV4cCI6MjA2OTM0MTExOH0.nqBK2ZxntesLY9qYClpoFPVnXOW10KrzF-UI_DKjbKo"

@st.cache_resource
def get_expense_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def display_expense_tracker():
    supabase = get_expense_supabase()

    st.header("💰 Expense Tracker")
    st.markdown("---")

    # --- Add New Expense Form ---
    st.subheader("Add New Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input("Expense Date", value=date.today())
            person = st.text_input("Person Who Made Expense")
            particulars = st.text_input("Particulars")
        with col2:
            property_name = st.selectbox("Property Name", [
                "Le Poshe Beachview", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
                "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
                "Le Royce Villa", "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
                "Le Park Resort", "Villa Shakti", "Eden Beach Resort", "La Coromandel Luxury",
                "Le Terra", "Happymates Forest Retreat", "Other"
            ])
            amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
            other_comments = st.text_area("Other Comments", height=68)

        submitted_by = st.text_input("Submitted By", value=st.session_state.get("username", ""))

        submit = st.form_submit_button("➕ Add Expense")
        if submit:
            if not person or not particulars:
                st.error("Please fill in at least 'Person' and 'Particulars'.")
            else:
                new_row = {
                    "expense_date": str(expense_date),
                    "person": person,
                    "particulars": particulars,
                    "property_name": property_name,
                    "amount": amount,
                    "other_comments": other_comments,
                    "submitted_by": submitted_by,
                }
                try:
                    supabase.table("expenses").insert(new_row).execute()
                    st.success("✅ Expense added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save expense: {e}")

    st.markdown("---")

    # --- View Expenses ---
    st.subheader("All Expenses")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_property = st.selectbox("Filter by Property", ["All"] + [
            "Le Poshe Beachview", "La Millionaire Resort", "Le Poshe Luxury", "Le Poshe Suite",
            "La Paradise Residency", "La Paradise Luxury", "La Villa Heritage", "Le Pondy Beach Side",
            "Le Royce Villa", "La Tamara Luxury", "La Antilia Luxury", "La Tamara Suite",
            "Le Park Resort", "Villa Shakti", "Eden Beach Resort", "La Coromandel Luxury",
            "Le Terra", "Happymates Forest Retreat", "Other"
        ], key="filter_property")
    with col2:
        filter_from = st.date_input("From Date", value=date(date.today().year, date.today().month, 1), key="filter_from")
    with col3:
        filter_to = st.date_input("To Date", value=date.today(), key="filter_to")

    try:
        query = supabase.table("expenses").select("*").order("expense_date", desc=True)
        result = query.execute()
        data = result.data if result.data else []

        if data:
            df = pd.DataFrame(data)

            # Apply filters
            df["expense_date"] = pd.to_datetime(df["expense_date"]).dt.date
            df = df[(df["expense_date"] >= filter_from) & (df["expense_date"] <= filter_to)]
            if filter_property != "All":
                df = df[df["property_name"] == filter_property]

            # Display columns in friendly order
            display_cols = ["id", "expense_date", "person", "particulars", "property_name", "amount", "other_comments", "submitted_by"]
            display_cols = [c for c in display_cols if c in df.columns]
            df = df[display_cols]

            # Summary
            total = df["amount"].sum() if "amount" in df.columns else 0
            st.metric("Total Expenses (filtered)", f"₹ {total:,.2f}")

            st.dataframe(df, use_container_width=True, hide_index=True)

            # Download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download as CSV", csv, "expenses.csv", "text/csv")
        else:
            st.info("No expenses found. Add your first expense above!")

    except Exception as e:
        st.error(f"Failed to load expenses: {e}")

    st.markdown("---")

    # --- Delete Expense ---
    if st.session_state.get("role") in ["Management", "Admin"]:
        st.subheader("🗑️ Delete an Expense")
        try:
            result = supabase.table("expenses").select("id, expense_date, person, particulars, amount").order("expense_date", desc=True).execute()
            deletable = result.data if result.data else []
            if deletable:
                options = {f"#{r['id']} | {r['expense_date']} | {r['person']} | {r['particulars']} | ₹{r['amount']}": r["id"] for r in deletable}
                selected_label = st.selectbox("Select Expense to Delete", list(options.keys()))
                if st.button("🗑️ Delete Selected Expense"):
                    expense_id = options[selected_label]
                    supabase.table("expenses").delete().eq("id", expense_id).execute()
                    st.success("Expense deleted.")
                    st.rerun()
        except Exception as e:
            st.error(f"Could not load expenses for deletion: {e}")
