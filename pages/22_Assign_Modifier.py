import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_db_connection 
from utils.style import load_css

# Initialize session state
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None
if 'dragged_modifier' not in st.session_state:
    st.session_state.dragged_modifier = None

# Fetch products
def get_products():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM Product WHERE status = 1", conn)
    conn.close()
    return df

# Fetch modifiers
def get_modifiers(product_id=None):
    conn = get_db_connection()
    if product_id:
        query = f"SELECT * FROM Modifier WHERE product_id = {product_id} AND status = 1 ORDER BY description"
    else:
        # query = "SELECT * FROM Modifier WHERE product_id IS NULL AND status = 1 ORDER BY description"
        query = "SELECT * FROM Modifier WHERE status = 1 GROUP BY description ORDER BY description"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Assign modifier to product by creating a new row
def assign_modifier(modifier_id, product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the original modifier details
    cursor.execute("SELECT description, price FROM Modifier WHERE modifier_id = ?", (modifier_id,))
    modifier = cursor.fetchone()
    
    if modifier:
        description, price = modifier
        # Insert a new modifier row with the product_id
        cursor.execute(
            "INSERT INTO Modifier (description, product_id, price, status) VALUES (?, ?, ?, 1)",
            (description, product_id, price)
        )
        conn.commit()
    
    conn.close()

# Delete assigned modifier
def delete_modifier(modifier_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Modifier WHERE modifier_id = ?", (modifier_id,))
    conn.commit()
    conn.close()

# Main app
st.set_page_config(
    page_title="Assign Modifier to Product",  
    page_icon="🧂", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Page layout
load_css()

st.subheader("Assign Modifiers") 

# Layout
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.subheader("🥪 Products")
    products = get_products()
    
    for _, product in products.iterrows():
        product_key = f"product_{product['product_id']}"
        
        if st.button(
            f"**{product['description']}**",
            key=product_key,
            use_container_width=True,
            type="primary" if st.session_state.selected_product == product['product_id'] else "secondary"
        ):
            st.session_state.selected_product = product['product_id']
            st.rerun()

with col2:
    st.subheader("🧂 Available Modifiers")
    unassigned_modifiers = get_modifiers(product_id=None)
    
    if len(unassigned_modifiers) == 0:
        st.info("No unassigned modifiers available")
    else:
        for _, modifier in unassigned_modifiers.iterrows():
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{modifier['description']}**")
            with col_b:
                if st.session_state.selected_product:
                    if st.button("➡️", key=f"assign_{modifier['modifier_id']}"):
                        assign_modifier(modifier['modifier_id'], st.session_state.selected_product)
                        st.success(f"Assigned {modifier['description']}")
                        st.rerun()

with col3:
    st.subheader("✅ Assigned Modifiers")
    
    if st.session_state.selected_product:
        selected_product = products[products['product_id'] == st.session_state.selected_product].iloc[0]
        st.info(f"Selected: **{selected_product['description']}**")
        
        assigned_modifiers = get_modifiers(product_id=st.session_state.selected_product)
        
        if len(assigned_modifiers) == 0:
            st.warning("No modifiers assigned to this product")
        else:
            for _, modifier in assigned_modifiers.iterrows():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**{modifier['description']}**")
                with col_b:
                    if st.button("❌", key=f"remove_{modifier['modifier_id']}"):
                        delete_modifier(modifier['modifier_id'])
                        st.success(f"Removed {modifier['description']}")
                        st.rerun()
    else:
        st.info("👈 Select a product to view assigned modifiers")