import streamlit as st
import streamlit_authenticator 
import yaml
from yaml import SafeLoader
import utils.style as style

# Set page config
st.set_page_config(
    page_title="Home", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="collapsed") # 👈 collapses sidebar by default
st.title("🏠 Welcome to QSR Home ")

# Load configuration first to get user role
with open('.streamlit/credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize authenticator
authenticator = streamlit_authenticator.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Handle login
try:
    authenticator.login()
except Exception as e:
    st.error(e)

# Redirect based on user role
if (st.session_state.get("roles")) == "KDS":
    style.hide_sidebar()
    st.switch_page("./pages/13_KDS.py")
if (st.session_state.get("roles")) == "COD":
    style.hide_sidebar()
    st.switch_page("./pages/14_COD.py")

# Check authentication status
if st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')
elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password') 
elif st.session_state.get('authentication_status'):
    st.title(f'Welcome *{st.session_state.get("username")}*')
    st.subheader("👈 Use the sidebar to navigate")
    # Logout button
    authenticator.logout()




# Add vertical space to push the caption down
for _ in range(10):
    st.write("")
 
# Caption at the bottom
st.caption("Built with ❤️ by BADA") 
