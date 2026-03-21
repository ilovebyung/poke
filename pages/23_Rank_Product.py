import streamlit as st
import sqlite3
import pandas as pd
from utils.database import get_db_connection 
from utils.style import load_css 

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Product Rank Manager", page_icon="🏆", layout="wide")
load_css()

# ── DB helpers ────────────────────────────────────────────────────────────────
def load_products(category_id):
    conn = get_db_connection()
    q = """
        SELECT p.product_id, p.description, c.description as category,
               p.price, p.rank, p.status
        FROM Product p
        LEFT JOIN Category c ON p.category_id = c.category_id
        WHERE p.category_id = ?
        ORDER BY p.rank ASC, p.product_id ASC
    """
    df = pd.read_sql_query(q, conn, params=(category_id,))
    conn.close()
    return df

def load_categories():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT category_id, description FROM Category", conn)
    conn.close()
    return df

def bulk_update_ranks(updates: list[tuple]):
    """updates: list of (rank, product_id)"""
    conn = get_db_connection()
    conn.executemany("UPDATE Product SET rank = ? WHERE product_id = ?", updates)
    conn.commit()
    conn.close()


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🏆 Product Rank Manager")

categories = load_categories()
cat_options = dict(zip(categories["description"], categories["category_id"]))

col_filter, col_spacer = st.columns([2, 4])
with col_filter:
    selected_cat_name = st.selectbox("Filter by Category", list(cat_options.keys()))

selected_cat_id = cat_options[selected_cat_name]
products = load_products(selected_cat_id)

if products.empty:
    st.info("No products found.")
    st.stop()

st.divider()

# ── Reorder ───────────────────────────────────────────────────────────────────
st.markdown("#### Reorder products — assign sequential ranks 1, 2, 3 …")
st.caption("Use the ↑ ↓ buttons to reorder, then save.")

if "order" not in st.session_state or st.session_state.get("order_cat") != selected_cat_name:
    st.session_state.order = list(products["product_id"])
    st.session_state.order_cat = selected_cat_name

order = st.session_state.order
id_to_row = products.set_index("product_id")

for idx, pid in enumerate(order):
    row = id_to_row.loc[pid]
    c1, c2, c3, c4 = st.columns([0.5, 3, 1, 1])
    with c1:
        st.markdown(f"<div style='font-family:Syne;font-size:1.4rem;font-weight:800;color:#f5c518;padding-top:8px'>#{idx+1}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='padding-top:10px;font-size:0.95rem'>{row['description']}<br><span style='color:#888;font-size:0.75rem'>{row['category']} · ${row['price']/100:.2f}</span></div>", unsafe_allow_html=True)
    with c3:
        if idx > 0:
            if st.button("▲ Up", key=f"up_{pid}"):
                order[idx], order[idx-1] = order[idx-1], order[idx]
                st.rerun()
    with c4:
        if idx < len(order) - 1:
            if st.button("▼ Down", key=f"dn_{pid}"):
                order[idx], order[idx+1] = order[idx+1], order[idx]
                st.rerun()

st.divider()
if st.button("💾 Save Ranks", width='stretch'):
    updates = [(rank+1, pid) for rank, pid in enumerate(order)]
    bulk_update_ranks(updates)
    st.success("✅ Ranks saved!")
    del st.session_state["order"]
    st.rerun()