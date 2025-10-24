# (Full code from the provided document, with additions)

def load_reservations_from_supabase():
    """Load all online reservations from Supabase without limit."""
    try:
        all_data = []
        offset = 0
        limit = 1000  # Supabase default max rows per request
        while True:
            response = supabase.table("online_reservations").select("*").range(offset, offset + limit - 1).execute()
            data = response.data if response.data else []
            all_data.extend(data)
            if len(data) < limit:  # If fewer rows than limit, we've reached the end
                break
            offset += limit
            if st.session_state.properties:
                all_data = [r for r in all_data if r["property"] in st.session_state.properties]
        if not all_data:
            st.warning("No online reservations found in the database.")
        return all_data
    except Exception as e:
        st.error(f"Error loading online reservations: {e}")
        return []

# In show_new_reservation_form, check permissions for add
if st.session_state.permissions["add"]:
    # Save button
else:
    st.warning("You do not have permission to add reservations.")

# In show_edit_reservations, check permissions for edit and delete
if st.session_state.permissions["edit"]:
    # Update button
else:
    st.warning("You do not have permission to edit reservations.")

if st.session_state.permissions["delete"]:
    # Delete button
else:
    st.warning("You do not have permission to delete reservations.")

# (Rest of the code remains the same to maintain look and functionality)
