import streamlit as st
import pandas as pd
import time
from utils.util import format_price, play_background_audio
from utils.database import get_db_connection 
from utils.style import load_css 
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Kitchen Display System", page_icon="🍳", layout="wide", initial_sidebar_state="collapsed")
load_css()

# Initialize session state
def init_session_state():
    if 'item_states' not in st.session_state:
        st.session_state.item_states = {}
    if 'known_orders' not in st.session_state:
        st.session_state.known_orders = set()

# Get all open orders (order_status = 11)
def get_open_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT 
            oc.order_id,
            oc.note,                   
            oc.order_status,
            oc.created_at
        FROM Order_Cart oc
        INNER JOIN Order_Product op ON oc.order_id = op.order_id
        WHERE oc.order_status = 11
        ORDER BY oc.created_at ASC
    """)
    orders = cursor.fetchall()
    conn.close()
    return orders

# Get modifier names
def get_modifier_names(modifier_ids_str):
    if not modifier_ids_str or modifier_ids_str.strip() == '':
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        modifier_ids = [id.strip() for id in modifier_ids_str.split(',') if id.strip()]
        if not modifier_ids:
            return None
        placeholders = ','.join(['?' for _ in modifier_ids])
        cursor.execute(f"""
            SELECT description
            FROM Modifier
            WHERE modifier_id IN ({placeholders})
            AND status = 1
            ORDER BY modifier_id
        """, modifier_ids)
        modifiers = cursor.fetchall()
        if modifiers:
            return ', '.join([mod['description'] for mod in modifiers])
        return None
    except Exception as e:
        print(f"Error getting modifier names: {e}")
        return None
    finally:
        conn.close()

# Get order items
def get_order_items(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            op.order_id,
            op.product_id,
            op.modifiers,
            pi.description as product_name,
            op.product_quantity
        FROM Order_Product op
        INNER JOIN Order_Cart oc ON op.order_id = oc.order_id
        INNER JOIN Product pi ON op.product_id = pi.product_id
        WHERE op.order_id = ? AND oc.order_status = 11
        ORDER BY pi.description
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()

    processed_items = []
    for item in items:
        item_dict = dict(item)
        item_dict['modifier_names'] = get_modifier_names(item['modifiers'])
        processed_items.append(item_dict)
    return processed_items

# Confirm order
def confirm_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Order_Cart 
            SET order_status = 12 
            WHERE order_id = ?
        """, (order_id,))
        conn.commit()
        keys_to_remove = [key for key in st.session_state.item_states.keys() 
                         if key.startswith(f"{order_id}_")]
        for key in keys_to_remove:
            del st.session_state.item_states[key]
        return True
    except Exception as e:
        st.error(f"Error confirming order: {e}")
        return False
    finally:
        conn.close()

# Create unique item key
def create_item_key(order_id, product_id, modifiers, index):
    modifier_part = modifiers if modifiers else "none"
    return f"{order_id}_{product_id}_{modifier_part}_{index}"

# Display order
def display_order_with_checkboxes(order, items):
    st.subheader(f'Order: {order["order_id"]%100}')
    if order['note'] and str(order['note']).strip():
        st.info(f"📝 Note: {order['note']}")
    all_checked = True
    for i, item in enumerate(items):
        product_display = item['product_name']
        if item['modifier_names']:
            product_display += f" ({item['modifier_names']})"
        product_display += f" x {item['product_quantity']}"
        item_key = create_item_key(order['order_id'], item['product_id'], item['modifiers'], i)
        if item_key not in st.session_state.item_states:
            st.session_state.item_states[item_key] = False
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            is_checked = st.checkbox("", key=f"checkbox_{item_key}", label_visibility="collapsed")
        with col2:
            st.session_state.item_states[item_key] = is_checked
            if is_checked:
                st.markdown(f"~~{product_display}~~")
            else:
                st.write(f"{product_display}")
                all_checked = False
    button_disabled = not all_checked
    button_text = "✓ All Items Ready - Confirm Order" if all_checked else "Confirm Order"
    button_type = "primary" if all_checked else "secondary"
    if all_checked:
        st.markdown("""
        <style>
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #0066CC !important;
            border-color: #0066CC !important;
            color: white !important;
            font-weight: bold !important;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #0052A3 !important;
            border-color: #0052A3 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    if st.button(button_text, key=f"confirm_{order['order_id']}", disabled=button_disabled, use_container_width=True, type=button_type):
        if confirm_order(order['order_id']):
            st.success(f"Order {order['order_id']} confirmed!")
            st.rerun()

# Main KDS page
def show_kds_page():

    init_session_state()
    orders = get_open_orders()

    # Detect new orders
    current_order_ids = {order['order_id'] for order in orders}
    new_orders = current_order_ids - st.session_state.known_orders
    if new_orders:
        # play_background_audio("assets/ding-dong.mp3")
        play_background_audio("ding-dong.mp3")
    st.session_state.known_orders = current_order_ids

    if not orders:
        st.subheader("📋 No pending orders. All caught up! 🎉")
        return

    cols = st.columns(3)
    for i, order in enumerate(orders):
        col_index = i % 3
        with cols[col_index]:
            items = get_order_items(order['order_id'])
            if items:
                display_order_with_checkboxes(order, items)

    st.markdown("---")
    st.write("Last updated:", time.strftime("%Y-%m-%d %H:%M:%S"))

# Run the page
if __name__ == "__main__":
    st_autorefresh(interval=2000, limit=None, key="refresh")
    show_kds_page()
