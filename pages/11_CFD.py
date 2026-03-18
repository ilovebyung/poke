import streamlit as st
import pandas as pd
from utils.util import format_price
from utils.database import get_order_details, get_modifiers_details
from utils.style import load_css
from streamlit_autorefresh import st_autorefresh

def display_order_summary():
    st.set_page_config(page_title="CFD", page_icon="🗒", layout="wide", initial_sidebar_state="collapsed")
    load_css()

    # Fetch order data from the database
    order_data = get_order_details()

    if not order_data:
        st.warning("No active order found.")
        return

    # Data structures to hold processed information
    orders = {}
    subtotal = 0
    tax_amount = 0

    # Process order data with modifiers
    for row in order_data:
        order_id = row['order_id']
        if order_id not in orders:
            orders[order_id] = []

        if row['product_id']:
            # Get modifiers for this specific product
            modifiers = get_modifiers_details(row['modifiers'])

            # Calculate total modifier price
            modifier_total_price = sum(mod['price'] for mod in modifiers)

            # Item total = (product price + all modifier prices) * quantity
            item_total = (row['product_price'] + modifier_total_price) * row['product_quantity']

            # Tax rate from Product table (stored as a percentage, e.g. 4.712 means 4.712%)
            try:
                tax_rate = row['tax'] if row['tax'] is not None else 4.712
            except (KeyError, IndexError):
                tax_rate = 4.712
            item_tax = item_total * (tax_rate / 100)

            orders[order_id].append({
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

    # Total = Subtotal + Tax
    total = subtotal + tax_amount

    # Display the Order IDs
    st.subheader(f'Order: {", ".join(str(k) for k in orders.keys())}')

    # Prepare detailed table data for the UI
    table_data = []

    for order_id, items in orders.items():
        for item in items:
            description = item['description']

            # Append modifier details to the description string if they exist
            if item['modifiers']:
                modifier_text = ", ".join([
                    f"{mod['description']} (+{format_price(mod['price'])})"
                    for mod in item['modifiers']
                ])
                description += f"\n  └─ {modifier_text}"

            table_data.append({
                "Description": description,
                "Quantity": item['quantity'],
                "Unit Price": format_price(item['base_price'] + item['modifier_total']),
                "Price": format_price(item['item_total'])
            })

    if table_data:
        df = pd.DataFrame(table_data)
        with st.container(height=500, border=True):
            st.table(df.set_index(df.columns[0]))

        # Summary: Subtotal → Tax → Total
        display_tax_rate = orders[list(orders.keys())[-1]][-1]['tax_rate']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Subtotal: {format_price(subtotal)}**")
        with col2:
            st.markdown(f"**Tax ({display_tax_rate:.3f}%): {format_price(tax_amount)}**")
        with col3:
            st.markdown(f"**Total: {format_price(total)}**")
    else:
        st.info("No items to display in the order.")

if __name__ == "__main__":
    st_autorefresh(interval=1000, limit=None, key="refresh")
    display_order_summary()
