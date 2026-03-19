import streamlit as st
import pandas as pd
from utils.util import format_price, calculate_split_amounts, print_receipt
from utils.database import get_db_connection, get_order_details, get_modifiers_details
from utils.style import load_css 

st.set_page_config(page_title="Checkout", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")
load_css()

def remove_item_from_db(order_id):
    """Helper to remove a specific item from the order in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM Order_Cart 
            WHERE order_id = ?
        """, (order_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error removing item: {e}")
        return False
    finally:
        conn.close()

def settle_order(order_ids, total):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for order_id in order_ids:
            cursor.execute("""
                UPDATE Order_Cart 
                SET order_status = 11, total = ?
                WHERE order_id = ?
            """, (total, order_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error settling order: {e}")
        return False
    finally:
        conn.close()

def handle_calculator_input(value):
    if value == "delete":
        st.session_state.current_input = st.session_state.current_input[:-1]
    elif value == "enter":
        if st.session_state.current_input:
            st.session_state.amount_tendered = int(float(st.session_state.current_input) * 100)
            st.session_state.current_input = ""
    elif value in [".", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
        st.session_state.current_input += value
    elif value.startswith("$"):
        amount = value[1:]
        st.session_state.amount_tendered = int(float(amount) * 100)

def initialize_session_state():
    if 'selected_service_area' not in st.session_state:
        st.session_state.selected_service_area = 0
    if 'amount_tendered' not in st.session_state:
        st.session_state.amount_tendered = 0
    if 'current_input' not in st.session_state:
        st.session_state.current_input = ""
    if 'split_count' not in st.session_state:
        st.session_state.split_count = 1

def show_checkout_page():
    initialize_session_state()

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        order_data = get_order_details()

        if not order_data:
            st.info("No items in cart.")
            if st.button("Return to Order"):
                st.switch_page("pages/10_Order.py")
            return

        orders = {}
        subtotal = 0
        tax_amount = 0

        for row in order_data:
            order_id = row['order_id']
            if order_id not in orders:
                orders[order_id] = []

            if row['product_id']:
                modifiers = get_modifiers_details(row['modifiers'])
                modifier_total_price = sum(mod['price'] for mod in modifiers)
                item_total = (row['product_price'] + modifier_total_price) * row['product_quantity']

                # Tax rate from Product table (e.g. 4.712 means 4.712%)
                try:
                    tax_rate = row['tax'] if row['tax'] is not None else 4.712
                except (KeyError, IndexError):
                    tax_rate = 4.712

                item_tax = item_total * (tax_rate / 100)

                orders[order_id].append({
                    'order_id': order_id,
                    'description': row['product_description'],
                    'quantity': row['product_quantity'],
                    'base_price': row['product_price'],
                    'modifiers': modifiers,
                    'modifier_total': modifier_total_price,
                    'item_total': item_total,
                    'tax_rate': tax_rate,
                    'item_tax': item_tax
                })
                subtotal += item_total
                tax_amount += item_tax

        # --- ITEMS LIST ---
        # hcol1, hcol2, hcol3, hcol4 = st.columns([3, 1, 1, 1])
        # hcol1.write("**Description**")
        # hcol2.write("**Qty**")
        # hcol3.write("**Price**")
        # hcol4.write("**Total**")

        with st.container(height=500, border=True):
            for order_id, items in orders.items():
                hdr_col1, hdr_col2 = st.columns([9, 0.9])
                with hdr_col1:
                    st.subheader(f'Order: {order_id}')
                if hdr_col2.button(" 🗑️ ", key=f"remove_order_{order_id}"):
                    if remove_item_from_db(order_id):
                        st.rerun()

                for idx, item in enumerate(items):
                    icol1, icol2, icol3, icol4 = st.columns([3, 1, 1, 1])

                    with icol1:
                        st.write(f"**{item['description']}**")
                        if item['modifiers']:
                            for mod in item['modifiers']:
                                st.caption(f"└─ {mod['description']} (+{format_price(mod['price'])})")

                    icol2.write(f"{item['quantity']}")
                    icol3.write(format_price(item['base_price'] + item['modifier_total']))
                    icol4.write(format_price(item['item_total']))

        # Payment Summary Section
        display_tax_rate = orders[list(orders.keys())[-1]][-1]['tax_rate']
        balance_due = subtotal + tax_amount

        payment_items = [
            ("Subtotal", subtotal),
            (f"Tax ({display_tax_rate:.3f}%)", tax_amount),
            ("Total", balance_due)
        ]

        for label, amount in payment_items:
            st.markdown(f"""
            <div class="payment-row">
                <span>{label}</span>
                <span>{format_price(amount)}</span>
            </div>
            """, unsafe_allow_html=True)

        # Remaining Balance
        remaining_balance = balance_due - st.session_state.amount_tendered

    with col2:
        with st.container(height=500, border=True):
            st.markdown(f"""
            <div class="balance-header">Remaining Balance</div>
            <div class="balance-amount">{format_price(remaining_balance)}</div>            
            """, unsafe_allow_html=True)

            st.write(f"**Current input:** ${st.session_state.current_input if st.session_state.current_input else '0'}")
            st.markdown("### Number Pad")

            for row in [["7","8","9"], ["4","5","6"], ["1","2","3"]]:
                cols = st.columns(3)
                for i, num in enumerate(row):
                    if cols[i].button(num, key=f"calc_{num}", use_container_width=True):
                        handle_calculator_input(num)
                        st.rerun()

            c1, c2, c3 = st.columns(3)
            if c1.button("0", key="calc_0", use_container_width=True):
                handle_calculator_input("0"); st.rerun()
            if c2.button(".", key="calc_.", use_container_width=True):
                handle_calculator_input("."); st.rerun()
            if c3.button("Del", key="calc_delete", use_container_width=True):
                handle_calculator_input("delete"); st.rerun()

        if st.button("Enter", key="calc_enter", use_container_width=True, type="primary"):
            handle_calculator_input("enter")
            st.rerun()

    with col3:
        with st.container(height=500, border=True):
            st.markdown("### Payment Type")
            st.button("Credit", key="credit", use_container_width=True)
            st.button("Cash", key="cash", use_container_width=True)

            st.markdown("---")
            st.markdown("### Split Evenly")

            sc_minus, sc_count, sc_plus = st.columns([1, 2, 1])

            with sc_minus:
                if st.button("🔻", key="split_minus", help="Decrease count"):
                    if st.session_state.split_count > 1:
                        st.session_state.split_count -= 1
                        st.rerun()

            with sc_count:
                st.markdown(
                    f"<div style='text-align:center; font-weight:bold; font-size:18px;'>{st.session_state.split_count}</div>",
                    unsafe_allow_html=True
                )

            with sc_plus:
                if st.button("🔺", key="split_plus", help="Increase count"):
                    st.session_state.split_count += 1
                    st.rerun()

            if st.session_state.split_count > 1:
                split_amounts = calculate_split_amounts(balance_due, st.session_state.split_count)
                for i, amount in enumerate(split_amounts):
                    st.caption(f"Person {i+1}: {format_price(amount)}")

            st.markdown("---")

        if st.button("Settle", key="settle", use_container_width=True, type="primary"):
            if settle_order(list(orders.keys()), balance_due):
                st.session_state.amount_tendered = 0
                st.session_state.current_input = ""
                st.session_state.split_count = 1
                st.success("Order settled!")
                st.switch_page("pages/10_Order.py")

        if st.button("Print Receipt", key="receipt", use_container_width=True):
            if print_receipt(orders, subtotal, tax_amount):
                st.success("Printing...")

if __name__ == "__main__":
    show_checkout_page()
