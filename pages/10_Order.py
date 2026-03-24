import streamlit as st
from datetime import datetime
from utils.util import format_price
from utils.database import get_db_connection
from utils.style import load_css

# Page layout
st.set_page_config(page_title="Orders", page_icon="🗒", layout="wide", initial_sidebar_state="collapsed")
load_css()

# Initialize session state for cart
if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'order_id' not in st.session_state:
    st.session_state.order_id = None

if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None

# --- Database Sync Logic for CFD ---

def sync_live_cart():
    """
    Flushes the Live_Cart table and inserts the current session's cart items 
    so the Customer Facing Display (CFD) can read it in real-time.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Flush the table for the new state
        cursor.execute("DELETE FROM Live_Cart")
        
        # Insert current cart items
        for item in st.session_state.cart:
            mod_text = ", ".join([m['description'] for m in item['modifiers']]) if item['modifiers'] else ""
            cursor.execute('''
                INSERT INTO Live_Cart (product_name, modifiers_text, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item['product_name'], 
                mod_text, 
                item['quantity'], 
                item['price'], 
                item['price'] * item['quantity']
            ))
        
        conn.commit()
    except Exception as e:
        st.error(f"Error syncing to CFD: {e}")
    finally:
        conn.close()

# --- Data Fetching ---

def get_category():
    """Get all categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id, description FROM category WHERE status = 1 ORDER BY category_id")
    groups = cursor.fetchall()
    conn.close()
    return groups

def get_products(group_id):
    """Get product items for a specific group"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT product_id, description, price 
        FROM Product
        WHERE category_id = ?
        ORDER BY rank
    ''', (group_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_modifiers(product_id):
    """Get modifier groups and their modifiers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            m.modifier_id,
            m.description,
            m.modifier_type_id,
            m.price,
            mt.description as group_description
        FROM Modifier m
        JOIN Modifier_Type mt ON m.modifier_type_id = mt.modifier_type_id
        WHERE m.status = 1
        ORDER BY m.modifier_type_id, m.modifier_id
    ''')
    modifiers = cursor.fetchall()
    conn.close()

    modifier_groups = {}
    for mod_id, description, group_id, price, group_desc in modifiers:
        if group_id not in modifier_groups:
            modifier_groups[group_id] = {
                'group_description': group_desc,
                'modifiers': []
            }
        modifier_groups[group_id]['modifiers'].append({
            'modifier_id': mod_id,
            'description': description,
            'price': price
        })
    return modifier_groups

# --- Cart Logic ---

def add_to_cart(product_id, product_name, price, modifiers):
    """Add item to cart and sync with Live_Cart table"""
    sorted_modifiers = sorted(modifiers, key=lambda x: x['modifier_id']) if modifiers else []

    found = False
    for item in st.session_state.cart:
        item_modifiers = sorted(item['modifiers'], key=lambda x: x['modifier_id']) if item['modifiers'] else []
        if item['product_id'] == product_id and item_modifiers == sorted_modifiers:
            item['quantity'] += 1
            found = True
            break

    if not found:
        modifier_price = sum(mod['price'] for mod in modifiers) if modifiers else 0
        total_price = price + modifier_price
        st.session_state.cart.append({
            'product_id': product_id,
            'product_name': product_name,
            'base_price': price,
            'price': total_price,
            'modifiers': sorted_modifiers,
            'quantity': 1
        })
    
    sync_live_cart() # Update the shared database table

def update_quantity(index, delta):
    """Update quantity of cart item and sync with Live_Cart table"""
    if 0 <= index < len(st.session_state.cart):
        st.session_state.cart[index]['quantity'] += delta
        if st.session_state.cart[index]['quantity'] <= 0:
            st.session_state.cart.pop(index)
    
    sync_live_cart() # Update the shared database table

def calculate_subtotal():
    """Calculate cart subtotal"""
    return sum(item['price'] * item['quantity'] for item in st.session_state.cart)

def create_order():
    """Create order, insert into database, and flush live cart"""
    if not st.session_state.cart:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        subtotal = calculate_subtotal()
        cursor.execute('''
            INSERT INTO Order_Cart (service_area_id, order_status, username, provided_name, note, subtotal, total)
            VALUES (0, 10, ?, ?, ?, ?, ?)
        ''', (st.session_state.get('username'), st.session_state.provided_name, st.session_state.note, subtotal, subtotal))
        
        order_id = cursor.lastrowid
        st.session_state.order_id = order_id

        for item in st.session_state.cart:
            modifier_ids = ','.join(str(mod['modifier_id']) for mod in item['modifiers']) if item['modifiers'] else None
            cursor.execute('''
                INSERT INTO Order_Product (order_id, product_id, modifiers, product_quantity)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], modifier_ids, item['quantity']))

        conn.commit()
        st.session_state.cart = [] # Clear internal cart
        sync_live_cart() # Flush the CFD display table
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error creating order: {e}")
        return False
    finally:
        conn.close()

# --- UI Components ---

@st.dialog("Customize Your Order")
def show_modifier_dialog():
    if not st.session_state.selected_product:
        return

    product      = st.session_state.selected_product
    product_id   = product['product_id']
    product_name = product['product_name']
    price        = product['price']

    st.write(f"**{product_name}**")
    st.write(f"Base Price: {format_price(price)}")
    st.divider()

    modifier_groups = get_modifiers(product_id)

    if modifier_groups:
        for type_id, group_data in modifier_groups.items():
            group_desc = group_data['group_description'] or "Modifiers"
            modifiers  = group_data['modifiers']

            with st.expander(f"**{group_desc}**", expanded=True):
                for modifier in modifiers:
                    mod_price = f" (+{format_price(modifier['price'])})" if modifier['price'] > 0 else ""
                    st.checkbox(
                        f"{modifier['description']}{mod_price}",
                        key=f"dialog_check_{product_id}_{modifier['modifier_id']}"
                    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'):
            st.session_state.selected_product = None
            st.rerun()
    with col2:
        if st.button("Add to Menu", type="primary", width='stretch'):
            selected_modifiers = []
            if modifier_groups:
                for type_id, group_data in modifier_groups.items():
                    for modifier in group_data['modifiers']:
                        key = f"dialog_check_{product_id}_{modifier['modifier_id']}"
                        if st.session_state.get(key, False):
                            selected_modifiers.append(modifier)

            add_to_cart(product_id, product_name, price, selected_modifiers)
            st.session_state.selected_product = None
            st.rerun()

def show_order_page():
    col_cart, col_menu = st.columns([1, 2])

    # Left column – Cart
    with col_cart:
        with st.container(height=420, border=True):

            st.markdown("""
                <style>
                div[data-testid="stTabs"] div[data-testid="stButton"] button {
                    height: 110px;
                    white-space: pre-wrap;
                    line-height: 1.4;
                }
                </style>
            """, unsafe_allow_html=True)

            if st.session_state.cart:
                for i, item in enumerate(st.session_state.cart):
                    with st.container():
                        cart_col1, cart_col2, cart_col3 = st.columns([3, 3, 2])
                        with cart_col1:
                            st.write(f"**{item['product_name']}**")
                            if item['modifiers']:
                                for mod in item['modifiers']:
                                    mp = f" (+{format_price(mod['price'])})" if mod['price'] > 0 else ""
                                    st.caption(f"• {mod['description']}{mp}")
                        with cart_col2:
                            d_col, q_col, i_col = st.columns([1, 0.4, 1])
                            if d_col.button(" 🔻 ", key=f"dec_{i}"):
                                update_quantity(i, -1)
                                st.rerun()
                            q_col.markdown(f"<div style='text-align:center;'>{item['quantity']}</div>", unsafe_allow_html=True)
                            if i_col.button(" 🔺 ", key=f"inc_{i}"):
                                update_quantity(i, 1)
                                st.rerun()
                        with cart_col3:
                            st.write(format_price(item['price'] * item['quantity']))
                        st.divider()
            else:
                st.info("Menu is empty")

        if 'provided_name' not in st.session_state: st.session_state.provided_name = ''
        if 'note' not in st.session_state: st.session_state.note = ''

        c1, c2 = st.columns([1, 3])
        st.session_state.provided_name = c1.text_input("Name? 👋", value=st.session_state.provided_name)
        st.session_state.note = c2.text_input("Special request? 👋", value=st.session_state.note)

        st.write(f"Subtotal: {format_price(calculate_subtotal())}")

        if st.button("Checkout", type="primary", width='stretch', disabled=(not st.session_state.cart)):
            if create_order():
                st.success("Order created!")
                st.switch_page("pages/12_Checkout.py")

    # Right column – Menu
    with col_menu:
        with st.container(height=600, border=True):
            category = get_category()
            if category:
                tabs = st.tabs([group[1] for group in category])
                for i, (group_id, group_name) in enumerate(category):
                    with tabs[i]:
                        product_items = get_products(group_id)
                        cols = st.columns(3)
                        for idx, (p_id, p_name, p_price) in enumerate(product_items):
                            with cols[idx % 3]:
                                if st.button(f"{p_name}\n{format_price(p_price)}", key=f"btn_{p_id}", width='stretch'):
                                    st.session_state.selected_product = {'product_id': p_id, 'product_name': p_name, 'price': p_price}
                                    if group_id == 1:
                                        show_modifier_dialog()
                                    else:
                                        add_to_cart(p_id, p_name, p_price, [])
                                        st.rerun()

if __name__ == "__main__":
    show_order_page()