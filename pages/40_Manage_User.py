import streamlit as st
import yaml
from yaml.loader import SafeLoader
from utils.style import load_css

# Page configuration
st.set_page_config(page_title="Register User", page_icon="👥", initial_sidebar_state="collapsed")
load_css()

credeintials_file_path = './.streamlit/credentials.yaml'
# Read the credentials file
def load_credentials():
    with open(credeintials_file_path) as file:
        return yaml.load(file, Loader=SafeLoader)

# Save credentials to file
def save_credentials(config):
    with open(credeintials_file_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

# Load config
config = load_credentials()

st.title("User Management System")

# Registration Form
st.subheader("Add New User")

with st.form("add_user_form"):
    username = st.text_input("Username*")
    email = st.text_input("Email*")
    password = st.text_input("Password*")
    first_name = st.text_input("First Name*")
    last_name = st.text_input("Last Name*")
    # roles = st.text_input("Roles", value="viewer")
    roles = st.selectbox(
    "Roles",
    ("cashier", "manager", "admin", "KDS", "COD"),
    )
    
    submit = st.form_submit_button("Add User")
    
    if submit:
        if username and email and password and first_name and last_name:
            # Check if username already exists
            if username in config['credentials']['usernames']:
                st.error(f"Username '{username}' already exists!")
            else:
                # Add new user
                config['credentials']['usernames'][username] = {
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'roles': roles,
                    'failed_login_attempts': 0,
                    'logged_in': False
                }
                
                # Save to file
                save_credentials(config)
                st.success(f"User '{username}' added successfully!")
                st.rerun()
        else:
            st.error("Please fill in all required fields!")

# Display existing users
st.divider()
st.subheader("Existing Users")

if config['credentials']['usernames']:
    for username, details in config['credentials']['usernames'].items():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            with st.expander(f"👤 {username}"):
                st.write(f"**Email:** {details.get('email', 'N/A')}")
                st.write(f"**First Name:** {details.get('first_name', 'N/A')}")
                st.write(f"**Last Name:** {details.get('last_name', 'N/A')}")
                st.write(f"**Password:** {details.get('password', 'N/A')}")
                st.write(f"**Roles:** {details.get('roles', 'N/A')}")
                st.write(f"**Failed Login Attempts:** {details.get('failed_login_attempts', 0)}")
                st.write(f"**Logged In:** {details.get('logged_in', False)}")
        
        with col2:
            if st.button("✏️", key=f"edit_{username}", help=f"Edit {username}"):
                st.session_state.editing_user = username
                st.rerun()
        
        with col3:
            if st.button("🗑️", key=f"delete_{username}", help=f"Delete {username}"):
                del config['credentials']['usernames'][username]
                save_credentials(config)
                st.success(f"User '{username}' deleted!")
                st.rerun()
else:
    st.info("No users registered yet.")

# Update credentials form
if 'editing_user' in st.session_state:
    st.divider()
    st.subheader(f"Update User: {st.session_state.editing_user}")
    
    current_user = config['credentials']['usernames'][st.session_state.editing_user]
    
    with st.form("update_user_form"):
        new_email = st.text_input("Email*", value=current_user.get('email', ''))
        new_password = st.text_input("Password*", value=current_user.get('password', ''))
        new_first_name = st.text_input("First Name*", value=current_user.get('first_name', ''))
        new_last_name = st.text_input("Last Name*", value=current_user.get('last_name', ''))
        # new_roles = st.text_input("Roles", value=current_user.get('roles', 'cashier'))
        new_roles = st.selectbox(
            "Roles",
            ("cashier", "manager", "admin", "KDS", "COD"),
        )

        col1, col2 = st.columns(2)
        with col1:
            update_submit = st.form_submit_button("Update User")
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        if update_submit:
            if new_email and new_password and new_first_name and new_last_name:
                config['credentials']['usernames'][st.session_state.editing_user] = {
                    'email': new_email,
                    'password': new_password,
                    'first_name': new_first_name,
                    'last_name': new_last_name,
                    'roles': new_roles,
                    'failed_login_attempts': current_user.get('failed_login_attempts', 0),
                    'logged_in': current_user.get('logged_in', False)
                }
                save_credentials(config)
                st.success(f"User '{st.session_state.editing_user}' updated successfully!")
                del st.session_state.editing_user
                st.rerun()
            else:
                st.error("Please fill in all required fields!")
        
        if cancel:
            del st.session_state.editing_user
            st.rerun()

