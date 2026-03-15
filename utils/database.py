import sqlite3
import streamlit as st
import pandas as pd
from datetime import date, datetime

# Adapter: Python date → ISO 8601 string
def adapt_date_iso(val):
    return val.isoformat()

# Converter: ISO 8601 string → Python date
def convert_date(val):
    return date.fromisoformat(val.decode())

# Register them
sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_converter("date", convert_date)

# Connect with type detection enabled
def get_db_connection():
    conn = sqlite3.connect('pos.database', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def get_table_data(table_name):
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY {table_name}_id ", conn)
            return df
    except Exception as e:
        st.error(f"Error fetching data from Table {table_name}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def add_item(table_name, item_value):
    """Inserts a new item into the specified generic table."""
    column_name = table_name
    try:
        with get_db_connection() as conn:
            conn.execute(f"INSERT INTO {table_name} ({column_name}) VALUES (?)", (item_value,))
            conn.commit()
            st.success(f"Added new {table_name}: **{item_value}**")
    except sqlite3.IntegrityError:
        st.warning(f"Error: {item_value} already exists in {table_name}.")
    except Exception as e:
        st.error(f"Failed to add {table_name}. Error: {e}")
        
def update_row(table_name, row_id_col, row_data):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{col} = ?" for col in row_data.keys() if col != row_id_col])
            values = [row_data[col] for col in row_data.keys() if col != row_id_col]
            values.append(row_data[row_id_col])
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {row_id_col} = ?", values)
            conn.commit()
    except Exception as e:
        st.error(f"Error updating row in Table {table_name}: {e}")

def delete_row(table_name, row_id_col, row_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE {row_id_col} = ?", (row_id,))
    except Exception as e:
        st.error(f"Error deleting row in Table {table_name}: {e}")

# Get order details with modifiers
def get_order_details():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get orders with products and their modifiers
    cursor.execute("""
        SELECT 
            oc.order_id,
            oc.subtotal,
            op.product_id,
            op.modifiers,
            pi.description as product_description,
            op.product_quantity,
            pi.price as product_price
        FROM Order_Cart oc
        LEFT JOIN Order_Product op ON oc.order_id = op.order_id
        LEFT JOIN Product pi ON op.product_id = pi.product_id
        WHERE oc.order_status = 10
        ORDER BY oc.order_id, pi.description
    """)
    
    results = cursor.fetchall()
    conn.close()
    return results

# Get modifier details for a list of modifier IDs
def get_modifiers_details(modifier_ids_str):
    """
    Parse modifier IDs string and fetch their details
    modifier_ids_str: "12,15,18" format
    Returns: list of dicts with modifier info
    """
    if not modifier_ids_str:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    modifier_ids = modifier_ids_str.split(',')
    placeholders = ','.join(['?' for _ in modifier_ids])
    
    cursor.execute(f"""
        SELECT 
            modifier_id,
            description,
            price
        FROM Modifier
        WHERE modifier_id IN ({placeholders})
        AND status = 1
    """, modifier_ids)
    
    modifiers = cursor.fetchall()
    conn.close()
    
    return [dict(mod) for mod in modifiers]
