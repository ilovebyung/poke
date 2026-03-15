import streamlit as st
import pandas as pd
import time
from utils.util import format_price
from utils.database import  get_db_connection 
from utils.style import load_css 
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Customer-Facing Display",page_icon="🍳",layout="wide",initial_sidebar_state="collapsed")
load_css()

# Get orders by status
def get_orders_by_status(status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT 
            oc.order_id,
            oc.service_area_id,
            oc.order_status,
            oc.provided_name,
            oc.created_at
        FROM Order_Cart oc
        INNER JOIN Order_Product op ON oc.order_id = op.order_id
        WHERE oc.order_status = ? 
        ORDER BY oc.created_at ASC
    """, (status,))
    
    orders = cursor.fetchall()
    conn.close()
    return orders

# Get order items for a specific order
def get_order_items(order_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            op.order_id,
            op.product_id,
            pi.description as product_name,
            op.product_quantity
        FROM Order_Product op
        INNER JOIN Order_Cart oc ON op.order_id = oc.order_id
        INNER JOIN Product pi ON op.product_id = pi.product_id
        WHERE op.order_id = ? AND oc.order_status = ? 
        ORDER BY pi.description
    """, (order_id, status))
    
    items = cursor.fetchall()
    conn.close()
    return items

# Display orders in a column
def display_orders_column(orders, status, title):
    st.subheader(title)
    
    if not orders:
        st.info("No orders at this stage")
        return
    
    # Create sub-columns for better organization (2 per main column)
    sub_cols = st.columns(2)
    
    for i, order in enumerate(orders):
        col_index = i % 2
        
        with sub_cols[col_index]:
            # Get items for this order
            items = get_order_items(order['order_id'],status)
            
            if items:  # Only display if order has items
                with st.container():
                    st.markdown(f"### Order: {order['order_id']%100} &nbsp; {order['provided_name']}")
                    
                    # Display items
                    # for item in items:
                        # product_display = item['product_name']

                        # st.write(f"• {product_display} x {item['product_quantity']}")
                    

# Main CFD page
def show_cod_page():
    
    # Create two main columns
    left_col, right_col = st.columns(2)
    
    # Left column: In Preparation (status 12 confirmed)
    with left_col:
        st.markdown("### 🍳 In Preparation")
        prep_orders = get_orders_by_status(11)
        display_orders_column(prep_orders, 11, "")
    
    # Right column: Ready for Pickup (status 13 delivered)
    with right_col:
        st.markdown("### 🛍️ Ready for Pickup")
        ready_orders = get_orders_by_status(12)
        display_orders_column(ready_orders, 12, "")
    
    # Footer with last updated time
    st.markdown("---")
    st.write("Last updated:", time.strftime("%Y-%m-%d %H:%M:%S"))     

# Run the page
if __name__ == "__main__":
    # Uncomment to enable auto-refresh every 10 seconds
    st_autorefresh(interval=2000, limit=None, key="refresh")
    show_cod_page()