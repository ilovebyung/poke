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
    """Get modifier groups and their modifiers.

    - category_id == 1 : fetch modifiers scoped to that category (category-wide modifiers).
    - Otherwise        : fetch modifiers scoped to the specific product.
    """
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

    # Organize modifiers by Modifier_Type
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

def add_to_cart(product_id, product_name, price, modifiers):
    """Add item to cart or update quantity if already exists"""
    sorted_modifiers = sorted(modifiers, key=lambda x: x['modifier_id']) if modifiers else []

    for item in st.session_state.cart:
        item_modifiers = sorted(item['modifiers'], key=lambda x: x['modifier_id']) if item['modifiers'] else []
        if item['product_id'] == product_id and item_modifiers == sorted_modifiers:
            item['quantity'] += 1
            return

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

def update_quantity(index, delta):
    """Update quantity of cart item"""
    if 0 <= index < len(st.session_state.cart):
        st.session_state.cart[index]['quantity'] += delta
        if st.session_state.cart[index]['quantity'] <= 0:
            st.session_state.cart.pop(index)

def calculate_subtotal():
    """Calculate cart subtotal"""
    return sum(item['price'] * item['quantity'] for item in st.session_state.cart)

def create_order():
    """Create order and insert into database"""
    if not st.session_state.cart:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        subtotal = sum(item['price'] * item['quantity'] for item in st.session_state.cart)

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
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error creating order: {e}")
        return False
    finally:
        conn.close()


@st.dialog("Customize Your Order")
def show_modifier_dialog():
    """
    Dialog — shown when a category_is == 1 item is tapped.
    Modifiers are grouped by Modifier_Type using st.expander.
    Each modifier is rendered as a checkbox (multiple selections allowed).
    """
    if 'selected_product' not in st.session_state or not st.session_state.selected_product:
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

    # ── Footer ────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.selected_product = None
            st.rerun()
    with col2:
        if st.button("Add to Menu", type="primary", use_container_width=True):
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
        # st.subheader("Orders")

        with st.container(height=400, border=True):
            if st.session_state.cart:
                for i, item in enumerate(st.session_state.cart):
                    with st.container():
                        cart_col1, cart_col2, cart_col3 = st.columns([3, 2, 2])

                        with cart_col1:
                            st.write(f"**{item['product_name']}**")
                            st.caption(f"Base: {format_price(item['base_price'])}")
                            if item['modifiers']:
                                for modifier in item['modifiers']:
                                    mp = f" (+{format_price(modifier['price'])})" if modifier['price'] > 0 else ""
                                    st.caption(f"• {modifier['description']}{mp}")

                        with cart_col2:
                            dec_col, qty_col, inc_col = st.columns([1, 0.4, 1])

                            with dec_col:
                                if st.button(" ➖ ", key=f"dec_{i}", help="Decrease quantity"):
                                    update_quantity(i, -1)
                                    st.rerun()

                            with qty_col:
                                st.markdown(
                                    f"<div style='text-align:center; font-size:16px;'>{item['quantity']}</div>",
                                    unsafe_allow_html=True
                                )

                            with inc_col:
                                if st.button(" ➕ ", key=f"inc_{i}", help="Increase quantity"):
                                    update_quantity(i, 1)
                                    st.rerun()

                        with cart_col3:
                            st.write(format_price(item['price'] * item['quantity']))

                        st.divider()
            else:
                st.info("Menu is empty")

        if 'provided_name' not in st.session_state:
            st.session_state.provided_name = ''
            st.session_state.note = ''

        col1, col2 = st.columns([1, 3])
        with col1:
            st.session_state.provided_name = st.text_input("Name? 👋")
        with col2:
            st.session_state.note = st.text_input("Special request? 👋")

        subtotal = calculate_subtotal()
        st.subheader(f"Subtotal: {format_price(subtotal)}")

        checkout_disabled = len(st.session_state.cart) == 0
        if st.button("Checkout", type="primary", use_container_width=True, disabled=checkout_disabled):
            if create_order():
                st.success("Order created successfully!")
                st.session_state.cart = []
                st.switch_page("pages/12_Checkout.py")

    # Right column – Menu
    with col_menu:
        # st.subheader("Menu")

        with st.container(height=600, border=True):  

            st.markdown("""
                <style>
                div[data-testid="stTabs"] div[data-testid="stButton"] button {
                    height: 120px;
                    white-space: pre-wrap;
                    line-height: 1.4;
                }
                </style>
            """, unsafe_allow_html=True)

            category = get_category()

            if category:
                group_names = [group[1] for group in category]
                tabs = st.tabs(group_names)

                for i, (group_id, group_name) in enumerate(category):
                    with tabs[i]:
                        product_items = get_products(group_id)
                        cols = st.columns(3)
                        for idx, (product_id, product_name, price) in enumerate(product_items):
                            with cols[idx % 3]:
                                if st.button(
                                    f"{product_name}\n{format_price(price)}",
                                    key=f"menu_btn_{product_id}",
                                    use_container_width=True
                                ):
                                    st.session_state.selected_product = {
                                        'product_id':   product_id,
                                        'product_name': product_name,
                                        'price':        price,
                                        'category_id':  group_id
                                    }
                                    if group_id == 1:
                                        show_modifier_dialog()
                                    else:
                                        add_to_cart(product_id, product_name, price, [])
                                        st.session_state.selected_product = None
                                        st.rerun()


# Run the page
if __name__ == "__main__":
    show_order_page()