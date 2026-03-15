import streamlit as st
import pandas as pd
import time
from utils.util import format_price
from utils.database import  get_db_connection 
from utils.style import load_css 
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Delivery Confirm System",page_icon="🥡",layout="wide",initial_sidebar_state="collapsed")
load_css()

# Get all confirmed orders (order_status = 12)
def get_open_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT 
            oc.order_id,
            --oc.service_area_id,
            oc.order_status,
            oc.created_at
        FROM Order_Cart oc
        INNER JOIN Order_Product op ON oc.order_id = op.order_id
        WHERE oc.order_status = 12
        ORDER BY oc.created_at ASC
    """)
    
    orders = cursor.fetchall()
    conn.close()
    return orders

# Get order items for a specific order
def get_order_items(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            op.order_id,
            op.product_id,
            pi.description as product_name,
            op.product_quantity,
            oc.provided_name
        FROM Order_Product op
        INNER JOIN Order_Cart oc ON op.order_id = oc.order_id
        INNER JOIN Product pi ON op.product_id = pi.product_id
        WHERE op.order_id = ? AND oc.order_status = 12
        ORDER BY pi.description
    """, (order_id,))
    
    items = cursor.fetchall()
    conn.close()
    return items

# Confirm delivery (set order_status to 13)
def confirm_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Order_Cart 
            SET order_status = 13 
            WHERE order_id = ?
        """, (order_id,))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error confirming order: {e}")
        return False
    finally:
        conn.close()

# Display order with simple list
def display_order(order, items):
    st.subheader(f'Order: {order["order_id"]}')
    
    for item in items:
        product_display = item['product_name']

        product_display += f" x {item['product_quantity']}"
        
        st.write(f"• {product_display}  &nbsp; {item['provided_name']}")


        # st.markdown(f"### Order: {order['order_id']} &nbsp; {order['provided_name']}")
    
    # Show confirm button
    if st.button("Confirm Delivery", key=f"confirm_{order['order_id']}", use_container_width=True):
        if confirm_order(order['order_id']):
            st.success(f"Order {order['order_id']} confirmed!")
            st.rerun()

# Main Delivery page
def show_delivery_page():

    # Get open orders
    orders = get_open_orders()
    
    if not orders:
        st.subheader("""
                📋 No pending orders. All caught up! 🎉
            """)
        return
    
    # Display orders in three columns
    cols = st.columns(3)
    
    for i, order in enumerate(orders):
        col_index = i % 3
        
        with cols[col_index]:
            # Get items for this order
            items = get_order_items(order['order_id'])
            
            if items:  # Only display if order has items
                display_order(order, items)
    
    st.write("Last updated:", time.strftime("%Y-%m-%d %H:%M:%S"))    

# Run the page
if __name__ == "__main__":
    # Note: The st_autorefresh function is set to refresh the page every 10 seconds to keep the KDS updated.
    st_autorefresh(interval=10 * 1000, limit=None, key="refresh")
    show_delivery_page()