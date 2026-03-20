import streamlit as st
import pandas as pd
from utils.util import format_price
from utils.database import get_db_connection
from utils.style import load_css
from streamlit_autorefresh import st_autorefresh

def get_live_cart_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, modifiers_text, quantity, unit_price, total_price FROM Live_Cart")
    rows = cursor.fetchall()
    conn.close()
    return rows

def display_cfd():
    st.set_page_config(page_title="Customer Display", page_icon="🗒", layout="wide")
    load_css()

    rows = get_live_cart_data()
    
    if not rows:
        st.info("Welcome! Please start your order.")
        return

    table_data = []
    subtotal = 0
    
    for row in rows:
        name, mods, qty, unit_p, total_p = row
        description = name
        if mods:
            description += f"\n  └─ {mods}"
            
        table_data.append({
            "Item": description,
            "Qty": qty,
            "Price": format_price(total_p)
        })
        subtotal += total_p

    # Calculations
    tax_rate = 4.712
    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount

    st.subheader("Current Order")
    df = pd.DataFrame(table_data)
    st.table(df) # Static table looks better for customers

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Subtotal", format_price(subtotal))
    c2.metric(f"Tax ({tax_rate}%)", format_price(tax_amount))
    c3.subheader(f"Total: {format_price(total)}")

if __name__ == "__main__":
    # Refresh every 1 second to make it feel "live"
    st_autorefresh(interval=1000, key="cfd_refresh")
    display_cfd()