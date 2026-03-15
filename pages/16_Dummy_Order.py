import streamlit as st
from utils.database import get_db_connection
from utils.style import load_css
from utils.util import format_price

# Helper function
def check_and_format_total(value):
    if isinstance(value, int):
        # Convert cents to dollars and cents
        return f"${value / 100:.2f}"
    else:
        return "Invalid input: must be an integer"
    
# Page configuration
st.set_page_config(
    page_title="Dummy Order",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)
load_css()

# Get username from session state
username = st.session_state.get("username", "guest")

# Inputs
st.subheader("Enter details:")
note = st.text_area("Item Description", max_chars=40)
total = st.number_input("Total (in cents)", min_value=0)

# Display formatted value
st.write("Formatted Total:", check_and_format_total(total))


# Submit button
if st.button("Place Order"):
    if not username or not total or not note:
        st.error("Username, Total, and Note are required.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert into Order_Cart
        cursor.execute(
            """
            INSERT INTO Order_Cart (service_area_id, order_status, username, total, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                1,   # dummy service_area_id
                33,  # 33 (dummy order delivered)
                username,
                total,
                note
            )
        )
        conn.commit()
        conn.close()

        st.success(f"Order placed successfully! Total: {format_price(total)}")
