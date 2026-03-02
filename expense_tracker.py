import streamlit as st
import supabase

# Initialize Supabase client
url = 'your_supabase_url'
key = 'your_supabase_anon_key'
supabase_client = supabase.create_client(url, key)

# Streamlit configuration
def main():
    st.title('Editable Expense Tracker')

    # Field definitions
    fields = ['Sl No', 'Expense made Date', 'Person who made expense', 'Particulars', 'Property Name', 'Other comments', 'Submitted by']
    data = []

    # Role-based access
    roles = ['Management', 'Accounts Team']
    user_role = st.selectbox('Select Your Role', roles)

    if user_role in roles:
        # Add new entry
        if st.button('Add Entry'):
            new_entry = {}
            for field in fields:
                new_entry[field] = st.text_input(f'Enter {field}')
            data.append(new_entry)

            # Insert data to Supabase
            supabase_client.table('expenses').insert(new_entry).execute()

        # Display entries
        st.write('Current Entries:')
        st.write(data)
    else:
        st.warning('You do not have access to this expense tracker.')

if __name__ == '__main__':
    main()