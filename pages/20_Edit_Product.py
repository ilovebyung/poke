import streamlit as st
from utils.util import format_price
from utils.database import  get_db_connection 
from utils.style import load_css 

# Page configuration
st.set_page_config(page_title="Manage Product", page_icon="🛠️", layout="wide", initial_sidebar_state="collapsed")


def parse_price(price_str):
    """Convert price string like $5.99 to cents (599)"""
    if not price_str:
        return None
    # Remove $ and spaces
    cleaned = price_str.replace('$', '').replace(' ', '')
    try:
        # Convert to float then to cents
        cents = int(float(cleaned) * 100)
        if cents < 0:
            return None
        return cents
    except ValueError:
        return None

# Category Functions
def get_categories():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM Category ORDER BY description').fetchall()
    conn.close()
    return categories

def insert_category(description, status):
    conn = get_db_connection()
    conn.execute('INSERT INTO Category (description, status) VALUES (?, ?)', (description, status))
    conn.commit()
    conn.close()

def update_category(category_id, description, status):
    conn = get_db_connection()
    conn.execute('UPDATE Category SET description = ?, status = ? WHERE category_id = ?', 
                 (description, status, category_id))
    conn.commit()
    conn.close()

def delete_category(category_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Category WHERE category_id = ?', (category_id,))
    conn.commit()
    conn.close()

# Product Functions
def get_products():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT p.*, c.description as category_name 
        FROM Product p 
        LEFT JOIN Category c ON p.category_id = c.category_id 
        ORDER BY p.description
    ''').fetchall()
    conn.close()
    return products

def insert_product(description, category_id, price, tax, status):
    conn = get_db_connection()
    conn.execute('''INSERT INTO Product (description, category_id, price, tax, status) 
                    VALUES (?, ?, ?, ?, ?)''', 
                 (description, category_id, price, tax, status))
    conn.commit()
    conn.close()

def update_product(product_id, description, category_id, price, tax, status):
    conn = get_db_connection()
    conn.execute('''UPDATE Product 
                    SET description = ?, category_id = ?, price = ?, tax = ?, status = ? 
                    WHERE product_id = ?''', 
                 (description, category_id, price, tax, status, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Product WHERE product_id = ?', (product_id,))
    conn.commit()
    conn.close()

# Modifier Functions
def get_modifiers():
    conn = get_db_connection()
    modifiers = conn.execute('''
        SELECT m.*, p.description as product_name 
        FROM Modifier m 
        LEFT JOIN Product p ON m.product_id = p.product_id 
        ORDER BY m.description
    ''').fetchall()
    conn.close()
    return modifiers

def insert_modifier(description, product_id, price, status):
    conn = get_db_connection()
    conn.execute('''INSERT INTO Modifier (description, product_id, price, status) 
                    VALUES (?, ?, ?, ?)''', 
                 (description, product_id, price, status))
    conn.commit()
    conn.close()

def update_modifier(modifier_id, description, product_id, price, status):
    conn = get_db_connection()
    conn.execute('''UPDATE Modifier 
                    SET description = ?, product_id = ?, price = ?, status = ? 
                    WHERE modifier_id = ?''', 
                 (description, product_id, price, status, modifier_id))
    conn.commit()
    conn.close()

def delete_modifier(modifier_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Modifier WHERE modifier_id = ?', (modifier_id,))
    conn.commit()
    conn.close()

# Main App
def display_dashboard():
    st.subheader("🛍️ Manage Products, Categories, and Modifiers") 
    load_css()
    # Category Management
    with st.expander("📁 Category Management", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Categories")
            categories = get_categories()
            if categories:
                for cat in categories:
                    cols = st.columns([3, 1, 1])
                    status_icon = "✅" if cat['status'] == 1 else "❌"
                    cols[0].write(f"**{cat['description']}** {status_icon}")
                    # cols[0].caption(f"ID: {cat['category_id']}")
                    if cols[1].button("Edit", key=f"edit_cat_{cat['category_id']}"):
                        st.session_state[f"edit_category_{cat['category_id']}"] = True
                    if cols[2].button("Delete", key=f"del_cat_{cat['category_id']}"):
                        delete_category(cat['category_id'])
                        st.rerun()
                    
                    if st.session_state.get(f"edit_category_{cat['category_id']}", False):
                        with st.form(key=f"form_edit_cat_{cat['category_id']}"):
                            new_desc = st.text_input("Description", value=cat['description'])
                            new_status = st.selectbox("Status", options=[1, 0], 
                                                     format_func=lambda x: "Available" if x == 1 else "Not Available",
                                                     index=0 if cat['status'] == 1 else 1)
                            col_a, col_b = st.columns(2)
                            if col_a.form_submit_button("Update"):
                                if new_desc:
                                    update_category(cat['category_id'], new_desc, new_status)
                                    st.session_state[f"edit_category_{cat['category_id']}"] = False
                                    st.success("Category updated!")
                                    st.rerun()
                            if col_b.form_submit_button("Cancel"):
                                st.session_state[f"edit_category_{cat['category_id']}"] = False
                                st.rerun()
            else:
                st.info("No categories found")
        
        with col2:
            st.subheader("Add Category")
            with st.form(key="add_category"):
                cat_desc = st.text_input("Description")
                cat_status = st.selectbox("Status", options=[1, 0], 
                                         format_func=lambda x: "Available" if x == 1 else "Not Available")
                if st.form_submit_button("Add Category"):
                    if cat_desc:
                        insert_category(cat_desc, cat_status)
                        st.success("Category added!")
                        st.rerun()
                    else:
                        st.error("Description is required")
    
    # Product Management
    with st.expander("📦 Product Management"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Products")
            products = get_products()
            if products:
                for prod in products:
                    cols = st.columns([3, 1, 1])
                    status_icon = "✅" if prod['status'] == 1 else "❌"
                    cols[0].write(f"**{prod['description']}** {status_icon}")
                    cols[0].caption(f"Category: {prod['category_name'] or 'None'} | Price: {format_price(prod['price'])} | Tax: {prod['tax']}% ") #| ID: {prod['product_id']}")
                    if cols[1].button("Edit", key=f"edit_prod_{prod['product_id']}"):
                        st.session_state[f"edit_product_{prod['product_id']}"] = True
                    if cols[2].button("Delete", key=f"del_prod_{prod['product_id']}"):
                        delete_product(prod['product_id'])
                        st.rerun()
                    
                    if st.session_state.get(f"edit_product_{prod['product_id']}", False):
                        with st.form(key=f"form_edit_prod_{prod['product_id']}"):
                            new_desc = st.text_input("Description", value=prod['description'])
                            categories = get_categories()
                            cat_options = {cat['category_id']: cat['description'] for cat in categories}
                            selected_cat = st.selectbox("Category", options=[None] + list(cat_options.keys()),
                                                       format_func=lambda x: "None" if x is None else cat_options[x],
                                                       index=0 if prod['category_id'] is None else list(cat_options.keys()).index(prod['category_id']) + 1)
                            new_price = st.text_input("Price (e.g., $5.99)", value=format_price(prod['price']))
                            new_tax = st.number_input("Tax %", value=float(prod['tax']), min_value=0.0, step=0.001,format="%.3f")
                            new_status = st.selectbox("Status", options=[1, 0], 
                                                     format_func=lambda x: "Available" if x == 1 else "Not Available",
                                                     index=0 if prod['status'] == 1 else 1)
                            col_a, col_b = st.columns(2)
                            if col_a.form_submit_button("Update"):
                                price_cents = parse_price(new_price)
                                if new_desc and price_cents is not None:
                                    update_product(prod['product_id'], new_desc, selected_cat, price_cents, new_tax, new_status)
                                    st.session_state[f"edit_product_{prod['product_id']}"] = False
                                    st.success("Product updated!")
                                    st.rerun()
                                else:
                                    st.error("Invalid input. Price must be non-negative.")
                            if col_b.form_submit_button("Cancel"):
                                st.session_state[f"edit_product_{prod['product_id']}"] = False
                                st.rerun()
            else:
                st.info("No products found")
        
        with col2:
            st.subheader("Add Product")
            with st.form(key="add_product"):
                prod_desc = st.text_input("Description")
                categories = get_categories()
                cat_options = {cat['category_id']: cat['description'] for cat in categories}
                selected_cat = st.selectbox("Category", options=[None] + list(cat_options.keys()),
                                           format_func=lambda x: "None" if x is None else cat_options[x])
                prod_price = st.text_input("Price (e.g., $5.99)")
                prod_tax = st.number_input("Tax %", value=float(4.712), min_value=0.0, format="%.3f")
                prod_status = st.selectbox("Status", options=[1, 0], 
                                          format_func=lambda x: "Available" if x == 1 else "Not Available")
                if st.form_submit_button("Add Product"):
                    price_cents = parse_price(prod_price)
                    if prod_desc and price_cents is not None:
                        insert_product(prod_desc, selected_cat, price_cents, prod_tax, prod_status)
                        st.success("Product added!")
                        st.rerun()
                    else:
                        st.error("Invalid input. Description required and price must be non-negative.")
    
    # Modifier Management
    with st.expander("🔧 Modifier Management"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Modifiers")
            modifiers = get_modifiers()
            if modifiers:
                for mod in modifiers:
                    cols = st.columns([3, 1, 1])
                    status_icon = "✅" if mod['status'] == 1 else "❌"
                    cols[0].write(f"**{mod['description']}** {status_icon}")
                    cols[0].caption(f"Product: {mod['product_name'] or 'None'} | Price: {format_price(mod['price'])}") # | ID: {mod['modifier_id']}")
                    if cols[1].button("Edit", key=f"edit_mod_{mod['modifier_id']}"):
                        st.session_state[f"edit_modifier_{mod['modifier_id']}"] = True
                    if cols[2].button("Delete", key=f"del_mod_{mod['modifier_id']}"):
                        delete_modifier(mod['modifier_id'])
                        st.rerun()
                    
                    if st.session_state.get(f"edit_modifier_{mod['modifier_id']}", False):
                        with st.form(key=f"form_edit_mod_{mod['modifier_id']}"):
                            new_desc = st.text_input("Description", value=mod['description'])
                            products = get_products()
                            prod_options = {prod['product_id']: prod['description'] for prod in products}
                            selected_prod = st.selectbox("Product", options=[None] + list(prod_options.keys()),
                                                        format_func=lambda x: "None" if x is None else prod_options[x],
                                                        index=0 if mod['product_id'] is None else list(prod_options.keys()).index(mod['product_id']) + 1)
                            new_price = st.text_input("Price (e.g., $0.50)", value=format_price(mod['price']))
                            new_status = st.selectbox("Status", options=[1, 0], 
                                                     format_func=lambda x: "Available" if x == 1 else "Not Available",
                                                     index=0 if mod['status'] == 1 else 1)
                            col_a, col_b = st.columns(2)
                            if col_a.form_submit_button("Update"):
                                price_cents = parse_price(new_price)
                                if new_desc and price_cents is not None:
                                    update_modifier(mod['modifier_id'], new_desc, selected_prod, price_cents, new_status)
                                    st.session_state[f"edit_modifier_{mod['modifier_id']}"] = False
                                    st.success("Modifier updated!")
                                    st.rerun()
                                else:
                                    st.error("Invalid input. Price must be non-negative.")
                            if col_b.form_submit_button("Cancel"):
                                st.session_state[f"edit_modifier_{mod['modifier_id']}"] = False
                                st.rerun()
            else:
                st.info("No modifiers found")
        
        with col2:
            st.subheader("Add Modifier")
            with st.form(key="add_modifier"):
                mod_desc = st.text_input("Description")
                products = get_products()
                prod_options = {prod['product_id']: prod['description'] for prod in products}
                selected_prod = st.selectbox("Product", options=[None] + list(prod_options.keys()),
                                            format_func=lambda x: "None" if x is None else prod_options[x])
                mod_price = st.text_input("Price (e.g., $0.50)", value="$0.00")
                mod_status = st.selectbox("Status", options=[1, 0], 
                                         format_func=lambda x: "Available" if x == 1 else "Not Available")
                if st.form_submit_button("Add Modifier"):
                    price_cents = parse_price(mod_price)
                    if mod_desc and price_cents is not None:
                        insert_modifier(mod_desc, selected_prod, price_cents, mod_status)
                        st.success("Modifier added!")
                        st.rerun()
                    else:
                        st.error("Invalid input. Description required and price must be non-negative.")

if __name__ == "__main__":
    display_dashboard()