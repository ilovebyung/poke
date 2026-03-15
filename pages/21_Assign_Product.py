import streamlit as st
import pandas as pd
from utils.database import get_db_connection
from utils.style import load_css

# ── Session state ─────────────────────────────────────────────────────────────
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_categories():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM Category WHERE status = 1 ORDER BY description", conn)
    conn.close()
    return df

def get_unassigned_products():
    """Products not yet linked to any category."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM Product WHERE (category_id IS NULL) AND status = 1 ORDER BY description",
        conn
    )
    conn.close()
    return df

def get_assigned_products(category_id):
    """Products linked to the given category."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM Product WHERE category_id = ? AND status = 1 ORDER BY description",
        conn, params=(category_id,)
    )
    conn.close()
    return df

def assign_product(product_id, category_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE Product SET category_id = ? WHERE product_id = ?",
        (category_id, product_id)
    )
    conn.commit()
    conn.close()

def unassign_product(product_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE Product SET category_id = NULL WHERE product_id = ?",
        (product_id,)
    )
    conn.commit()
    conn.close()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Category Product Assignment",
    page_icon="🥪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_css()

st.subheader("Assign Products to Category")

# ── Layout ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.subheader("🗂️ Categories")
    categories = get_categories()

    if categories.empty:
        st.info("No categories found.")
    else:
        for _, category in categories.iterrows():
            if st.button(
                f"**{category['description']}**",
                key=f"cat_{category['category_id']}",
                use_container_width=True,
                type="primary" if st.session_state.selected_category == category['category_id'] else "secondary"
            ):
                st.session_state.selected_category = category['category_id']
                st.rerun()

with col2:
    st.subheader("🥪 Unassigned Products")
    unassigned = get_unassigned_products()

    if unassigned.empty:
        st.info("No unassigned products available.")
    else:
        for _, product in unassigned.iterrows():
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{product['description']}**")
                st.caption(f"${product['price']/100:.2f}")
            with col_b:
                if st.session_state.selected_category:
                    if st.button("➡️", key=f"assign_{product['product_id']}"):
                        assign_product(product['product_id'], st.session_state.selected_category)
                        st.success(f"Assigned {product['description']}")
                        st.rerun()
                else:
                    st.caption("—")

with col3:
    st.subheader("✅ Assigned Products")

    if st.session_state.selected_category:
        selected_cat = categories[categories['category_id'] == st.session_state.selected_category].iloc[0]
        st.info(f"Selected: **{selected_cat['description']}**")

        assigned = get_assigned_products(st.session_state.selected_category)

        if assigned.empty:
            st.warning("No products assigned to this category.")
        else:
            for _, product in assigned.iterrows():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**{product['description']}**")
                    st.caption(f"${product['price']/100:.2f}")
                with col_b:
                    if st.button("❌", key=f"remove_{product['product_id']}"):
                        unassign_product(product['product_id'])
                        st.success(f"Removed {product['description']}")
                        st.rerun()
    else:
        st.info("👈 Select a category to view assigned products")