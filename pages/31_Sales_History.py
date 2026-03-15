import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from utils.util import format_price, format_timestamp
from utils.database import get_db_connection
from utils.style import load_css

# Page configuration
st.set_page_config(page_title="Sales Summary Report", page_icon="📑", layout="wide")
load_css()

def get_summary_data(start_date, end_date):
    """Get summary statistics for the selected date range"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        # Get total revenue separately to avoid duplication from JOIN
        revenue_query = """
        SELECT SUM(total) as total_revenue
        FROM Order_History
        WHERE DATE(timestamp) BETWEEN ? AND ? AND order_status = 13
        """
        revenue_result = conn.execute(revenue_query, (start_date, end_date)).fetchone()
        total_revenue = revenue_result[0] or 0
        
        # Get other statistics
        query = """
        SELECT 
            COUNT(DISTINCT oh.order_id) as total_orders,
            COUNT(DISTINCT op.product_id) as unique_products,
            SUM(op.product_quantity) as total_quantity
        FROM Order_History oh
        LEFT JOIN Order_Product op ON oh.order_id = op.order_id
        WHERE DATE(oh.timestamp) BETWEEN ? AND ? AND oh.order_status = 13
        """
        
        result = conn.execute(query, (start_date, end_date)).fetchone()
        return {
            'total_orders': result[0] or 0,
            'unique_products': result[1] or 0,
            'total_quantity': result[2] or 0,
            'total_revenue': total_revenue
        }
        
    except sqlite3.Error as e:
        st.error(f"Database query error: {e}")
        return {}
    finally:
        conn.close()


def get_sales_summary_data(start_date, end_date):
    """Get sales summary grouped by product"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            p.product_id,
            p.description as product_description,
            SUM(op.product_quantity) as total_quantity,
            p.price as unit_price,
            p.tax as unit_tax,
            SUM(op.product_quantity * p.price) as subtotal,
            SUM(op.product_quantity * p.tax) as total_tax,
            SUM(op.product_quantity * (p.price + p.tax)) as total_amount,
            COUNT(DISTINCT oh.order_id) as order_count
        FROM Order_History oh
        INNER JOIN Order_Product op ON oh.order_id = op.order_id
        INNER JOIN Product p ON op.product_id = p.product_id
        WHERE DATE(oh.timestamp) BETWEEN ? AND ? AND oh.order_status = 13
        GROUP BY p.product_id, p.description, p.price, p.tax
        ORDER BY total_quantity DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        return df
        
    except sqlite3.Error as e:
        st.error(f"Database query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


# Sidebar for date selection
st.sidebar.header("📅 Date Selection")

# Date range selection
date_option = st.sidebar.radio(
    "Select date range:",
    ["Single Day", "Last 7 Days", "Last 30 Days"]
)

today = date.today()

if date_option == "Single Day":
    selected_date = st.sidebar.date_input(
        "Select date:",
        value=today,
        max_value=today
    )
    start_date = end_date = selected_date
      
elif date_option == "Last 7 Days":
    start_date = today - timedelta(days=7)
    end_date = today
    
elif date_option == "Last 30 Days":
    start_date = today - timedelta(days=30)
    end_date = today

# Display selected date range
if start_date == end_date:
    st.sidebar.info(f"Selected: {start_date}")
else:
    st.sidebar.info(f"Selected: {start_date} to {end_date}")

# Main content
if st.sidebar.button("Refresh Data", type="primary"):
    st.cache_data.clear()

# Get and display summary statistics
st.subheader("Sales Summary Statistics")
summary = get_summary_data(start_date, end_date)

if summary:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Orders", summary['total_orders'])
    with col2:
        st.metric("Unique Products", summary['unique_products'])
    with col3:
        st.metric("Total Quantity", summary['total_quantity'])
    with col4:
        st.metric("Total Revenue", format_price(summary['total_revenue']))

# Get sales summary data
st.subheader("Product Sales Summary")
df = get_sales_summary_data(start_date, end_date)

if df.empty:
    st.info("No sales found for the selected date range.")
else:
    # Format the data for display
    display_df = df.copy()
    
    # Format price columns
    if 'unit_price' in display_df.columns:
        display_df['unit_price'] = display_df['unit_price'].apply(format_price)
    if 'unit_tax' in display_df.columns:
        display_df['unit_tax'] = display_df['unit_tax'].apply(format_price)
    if 'subtotal' in display_df.columns:
        display_df['subtotal'] = display_df['subtotal'].apply(format_price)
    if 'total_tax' in display_df.columns:
        display_df['total_tax'] = display_df['total_tax'].apply(format_price)
    if 'total_amount' in display_df.columns:
        display_df['total_amount'] = display_df['total_amount'].apply(format_price)
    
    # Rename columns for better display
    column_mapping = {
        'product_id': 'Product ID',
        'product_description': 'Product Description',
        'total_quantity': 'Total Quantity',
        'unit_price': 'Unit Price',
        'unit_tax': 'Unit Tax',
        'subtotal': 'Subtotal',
        'total_tax': 'Total Tax',
        'total_amount': 'Total Amount',
        'order_count': 'Order Count'
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    # Display options
    items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=1)

    # Show detailed view with pagination
    total_rows = len(display_df)
    
    if total_rows > items_per_page:
        page_num = st.number_input(
            f"Page (showing {items_per_page} of {total_rows} records)",
            min_value=1,
            max_value=(total_rows - 1) // items_per_page + 1,
            value=1
        )
        start_idx = (page_num - 1) * items_per_page
        end_idx = start_idx + items_per_page
        display_df = display_df.iloc[start_idx:end_idx]
    
    # Display the data editor
    edited_df = st.data_editor(
        display_df,
        width='stretch',
        hide_index=True,
        disabled=True,
        num_rows="dynamic",
        column_config={
            "Product ID": st.column_config.NumberColumn("Product ID", width="small"),
            "Product Description": st.column_config.TextColumn("Product Description", width="large"),
            "Total Quantity": st.column_config.NumberColumn("Total Quantity", width="small"),
            "Unit Price": st.column_config.TextColumn("Unit Price", width="small"),
            "Unit Tax": st.column_config.TextColumn("Unit Tax", width="small"),
            "Subtotal": st.column_config.TextColumn("Subtotal", width="medium"),
            "Total Tax": st.column_config.TextColumn("Total Tax", width="small"),
            "Total Amount": st.column_config.TextColumn("Total Amount", width="medium"),
            "Order Count": st.column_config.NumberColumn("Order Count", width="small")
        }
    )
    
    # Show record count
    st.info(f"Showing {len(display_df)} of {total_rows} records")
    
