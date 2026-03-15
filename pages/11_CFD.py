import streamlit as st
import pandas as pd
from utils.util import format_price
from utils.database import get_order_details, get_modifiers_details
from streamlit_autorefresh import st_autorefresh

def display_order_summary():
    # Fetch order data from the database
    order_data = get_order_details()
    
    if not order_data:
        st.warning("No active order found.")
        return

    # Data structures to hold processed information
    orders = {}
    subtotal = 0
    
    # Process order data with modifiers as seen in 12_Checkout.py
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
            
            orders[order_id].append({
                'description': row['product_description'],
                'quantity': row['product_quantity'],
                'base_price': row['product_price'],
                'modifiers': modifiers,
                'modifier_total': modifier_total_price,
                'item_total': item_total
            })
            
            subtotal += item_total

    # --- EXTRACTED SECTION START ---
    
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
                "Price": format_price(item['base_price'] + item['modifier_total']),
                "Total": format_price(item['item_total'])
            })

    # Create and display the DataFrame as a table
    # if table_data:  # Only if we have data
    #     df = pd.DataFrame(table_data)
    #     if not df.empty:
    #         st.table(df.set_index(df.columns[0]))
    #         st.markdown(f"**Subtotal: {format_price(subtotal)}**")
    #     else:
    #         st.info("No items to display in the order.")
    # else:
    #     st.info("No items to display in the order.")


    if table_data:  # Only if we have data
        df = pd.DataFrame(table_data)
        st.table(df.set_index(df.columns[0]))  
        st.markdown(f"**Subtotal: {format_price(subtotal)}**")
    else:
        st.info("No items to display in the order.")

if __name__ == "__main__":
    st_autorefresh(interval=1000, limit=None, key="refresh")
    display_order_summary()